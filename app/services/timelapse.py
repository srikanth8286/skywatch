"""
Timelapse capture service with incremental video compilation
"""
import asyncio
import logging
import cv2
from pathlib import Path
from datetime import datetime
import numpy as np
import tempfile
import shutil
from concurrent.futures import ThreadPoolExecutor

# Shared thread pool for blocking I/O (cv2.imwrite, file ops)
_io_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="timelapse-io")

logger = logging.getLogger(__name__)


class TimelapseService:
    """Service for capturing timelapse images and compiling to video"""
    
    def __init__(self, camera_manager, settings):
        self.camera = camera_manager
        self.settings = settings
        self.is_running = False
        self.task = None
        self.capture_count = 0
        self.daily_frame_count = 0
        
        # Frame buffer for incremental compilation
        self.frame_buffer = []
        self.buffer_size = 20  # Compile every 20 frames
        
        # Setup storage
        self.base_path = Path(settings.storage.base_path) / "timelapse"
        self.temp_frames_path = self.base_path / "temp"
        self.temp_frames_path.mkdir(parents=True, exist_ok=True)
        
        self.current_date = None
        self.current_video_path = None
        
    async def start(self):
        """Start timelapse service"""
        self.is_running = True
        self.task = asyncio.create_task(self._capture_loop())
        logger.info("Timelapse service started")
        
    async def stop(self):
        """Stop timelapse service"""
        self.is_running = False
        
        # Compile any remaining frames before stopping
        if self.frame_buffer:
            logger.info("Compiling remaining frames before shutdown...")
            await self._compile_buffer()
        
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        logger.info("Timelapse service stopped")
    
    def update_settings(self, new_settings):
        """Update settings without restart"""
        old_interval = self.settings.timelapse.interval
        self.settings = new_settings
        if old_interval != new_settings.timelapse.interval:
            logger.info(f"Timelapse interval updated: {old_interval}s -> {new_settings.timelapse.interval}s")
        
    async def _capture_loop(self):
        """Main capture loop"""
        while self.is_running:
            try:
                await self._capture_frame()
                await asyncio.sleep(self.settings.timelapse.interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in timelapse capture: {e}")
                await asyncio.sleep(5)
                
    async def _capture_frame(self):
        """Capture a single frame and add to buffer"""
        frame = self.camera.get_frame()
        if frame is None:
            logger.warning("No frame available for timelapse")
            return
        
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        
        # Check if we've moved to a new day
        if self.current_date != date_str:
            # Flush any remaining frames from previous day
            if self.frame_buffer:
                await self._compile_buffer()
            
            self.current_date = date_str
            self.current_video_path = self.base_path / f"{date_str}.mp4"
            self.daily_frame_count = 0
            logger.info(f"Started new timelapse for {date_str}")
        
        # Save frame to temp buffer
        filename = now.strftime("%Y-%m-%d_%H-%M-%S.jpg")
        temp_path = self.temp_frames_path / filename
        
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), self.settings.timelapse.quality]
        try:
            loop = asyncio.get_running_loop()
            success = await loop.run_in_executor(
                _io_executor, cv2.imwrite, str(temp_path), frame, encode_param
            )
        except Exception as e:
            logger.error(f"Failed to write frame {filename}: {e}", exc_info=True)
            return
        
        if success:
            self.frame_buffer.append(str(temp_path))
            self.capture_count += 1
            self.daily_frame_count += 1
            logger.info(f"Timelapse frame captured: {filename} (#{self.capture_count})")
            
            # Compile buffer when it reaches threshold
            if len(self.frame_buffer) >= self.buffer_size:
                await self._compile_buffer()
        else:
            logger.error(f"Failed to save timelapse frame: {filename}")
    
    async def _compile_buffer(self):
        """Compile buffered frames into video segment and append to daily video"""
        if not self.frame_buffer:
            return
        
        list_file = None
        temp_segment = None
        
        try:
            fps = self.settings.timelapse.video_fps
            
            # Create temporary segment
            temp_segment = self.temp_frames_path / f"segment_{datetime.now().strftime('%H%M%S')}.mp4"
            
            # Create file list for ffmpeg
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                list_file = f.name
                for frame_path in self.frame_buffer:
                    if not Path(frame_path).exists():
                        logger.warning(f"Frame missing: {frame_path}")
                        continue
                    f.write(f"file '{frame_path}'\n")
                    f.write(f"duration {1.0/fps}\n")
                # Duplicate last frame
                if self.frame_buffer:
                    f.write(f"file '{self.frame_buffer[-1]}'\n")
            
            # Compile segment using async subprocess (non-blocking)
            cmd = [
                'ffmpeg', '-y', '-loglevel', 'error',
                '-f', 'concat', '-safe', '0', '-i', list_file,
                '-vf', f'fps={fps}',
                '-pix_fmt', 'yuv420p',
                '-c:v', 'libx264',
                '-preset', 'ultrafast',  # Fast encoding for real-time
                '-crf', '23',
                str(temp_segment)
            ]
            
            try:
                proc = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                _, stderr = await asyncio.wait_for(proc.communicate(), timeout=60)
                
                if proc.returncode != 0:
                    logger.error(f"Failed to compile segment: {stderr.decode()}")
                    return
            except asyncio.TimeoutError:
                logger.error("FFmpeg segment compilation timed out")
                try:
                    proc.kill()
                except Exception:
                    pass
                return
            
            # Append to daily video or create new
            if self.current_video_path.exists():
                # Append to existing video
                await self._append_to_video(temp_segment)
            else:
                # First segment of the day - just rename it
                shutil.move(str(temp_segment), str(self.current_video_path))
                logger.info(f"Created daily video: {self.current_video_path.name}")
            
            # Clean up temp segment if it still exists
            if temp_segment and temp_segment.exists():
                temp_segment.unlink()
            
            # Delete processed frames
            for frame_path in self.frame_buffer:
                try:
                    Path(frame_path).unlink()
                except Exception as e:
                    logger.warning(f"Failed to delete temp frame {frame_path}: {e}")
            
            logger.info(f"Compiled {len(self.frame_buffer)} frames into video segment")
            self.frame_buffer = []
            
        except Exception as e:
            logger.error(f"Error compiling buffer: {e}", exc_info=True)
        finally:
            # Clean up list file
            if list_file and Path(list_file).exists():
                try:
                    Path(list_file).unlink()
                except Exception as e:
                    logger.warning(f"Failed to delete list file: {e}")
    
    async def _append_to_video(self, segment_path: Path):
        """Append video segment to daily video (non-blocking)"""
        concat_file = None
        try:
            # Create concat list
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                concat_file = f.name
                f.write(f"file '{self.current_video_path.absolute()}'\n")
                f.write(f"file '{segment_path.absolute()}'\n")
            
            # Create temp output
            temp_output = self.current_video_path.with_suffix('.tmp.mp4')
            
            # Concatenate videos using async subprocess
            cmd = [
                'ffmpeg', '-y', '-loglevel', 'error',
                '-f', 'concat', '-safe', '0', '-i', concat_file,
                '-c', 'copy',  # Copy without re-encoding (fast)
                str(temp_output)
            ]
            
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            _, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)
            
            if proc.returncode == 0:
                shutil.move(str(temp_output), str(self.current_video_path))
                logger.info("Appended segment to daily video")
            else:
                logger.error(f"Failed to append segment: {stderr.decode()}")
                if temp_output.exists():
                    temp_output.unlink()
                    
        except asyncio.TimeoutError:
            logger.error("FFmpeg append timed out")
            try:
                proc.kill()
            except Exception:
                pass
        except Exception as e:
            logger.error(f"Error appending to video: {e}")
        finally:
            if concat_file and Path(concat_file).exists():
                try:
                    Path(concat_file).unlink()
                except Exception:
                    pass
            
    def get_stats(self) -> dict:
        """Get service statistics"""
        return {
            "enabled": self.settings.timelapse.enabled,
            "is_running": self.is_running,
            "capture_count": self.capture_count,
            "daily_frame_count": self.daily_frame_count,
            "buffer_size": len(self.frame_buffer),
            "interval": self.settings.timelapse.interval,
            "storage_path": str(self.base_path),
            "current_video": str(self.current_video_path) if self.current_video_path else None
        }
        
    def get_available_dates(self) -> list:
        """Get list of dates with compiled timelapse videos or current day"""
        dates = set()
        
        # Add current date (even if video not compiled yet)
        from datetime import datetime
        today = datetime.now().strftime('%Y-%m-%d')
        dates.add(today)
        
        # Add dates from existing MP4 files
        if self.base_path.exists():
            for video_file in sorted(self.base_path.glob("*.mp4"), reverse=True):
                if video_file.stem != "temp":  # Skip temp files
                    dates.add(video_file.stem)
        
        return sorted(list(dates), reverse=True)
        
    def get_video_path(self, date: str) -> Path:
        """Get path to compiled video for a specific date"""
        return self.base_path / f"{date}.mp4"
    
    def get_frames_for_date(self, date: str) -> list:
        """Get video info for a specific date (for backward compatibility)"""
        video_path = self.get_video_path(date)
        if video_path.exists():
            return [{
                "type": "video",
                "path": str(video_path.relative_to(self.base_path.parent)),
                "filename": video_path.name
            }]
        return []
