"""
Timelapse capture service
"""
import asyncio
import logging
import cv2
from pathlib import Path
from datetime import datetime
import numpy as np

logger = logging.getLogger(__name__)


class TimelapseService:
    """Service for capturing timelapse images"""
    
    def __init__(self, camera_manager, settings):
        self.camera = camera_manager
        self.settings = settings
        self.is_running = False
        self.task = None
        self.capture_count = 0
        
        # Setup storage
        self.base_path = Path(settings.storage.base_path) / "timelapse"
        self.base_path.mkdir(parents=True, exist_ok=True)
        
    async def start(self):
        """Start timelapse service"""
        self.is_running = True
        self.task = asyncio.create_task(self._capture_loop())
        logger.info("Timelapse service started")
        
    async def stop(self):
        """Stop timelapse service"""
        self.is_running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        logger.info("Timelapse service stopped")
        
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
        """Capture a single frame"""
        frame = self.camera.get_frame()
        if frame is None:
            logger.warning("No frame available for timelapse")
            return
            
        # Get current date for daily organization
        now = datetime.now()
        date_dir = self.base_path / now.strftime("%Y-%m-%d") / "frames"
        date_dir.mkdir(parents=True, exist_ok=True)
        
        # Save frame
        filename = now.strftime("%Y-%m-%d_%H-%M-%S.jpg")
        filepath = date_dir / filename
        
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), self.settings.timelapse.quality]
        success = cv2.imwrite(str(filepath), frame, encode_param)
        
        if success:
            self.capture_count += 1
            logger.info(f"Timelapse frame captured: {filename} (#{self.capture_count})")
        else:
            logger.error(f"Failed to save timelapse frame: {filename}")
            
    def get_stats(self) -> dict:
        """Get service statistics"""
        return {
            "enabled": self.settings.timelapse.enabled,
            "is_running": self.is_running,
            "capture_count": self.capture_count,
            "interval": self.settings.timelapse.interval,
            "storage_path": str(self.base_path)
        }
        
    def get_available_dates(self) -> list:
        """Get list of dates with captured timelapses"""
        dates = []
        if self.base_path.exists():
            for date_dir in sorted(self.base_path.iterdir(), reverse=True):
                if date_dir.is_dir() and (date_dir / "frames").exists():
                    dates.append(date_dir.name)
        return dates
        
    def get_frames_for_date(self, date: str) -> list:
        """Get list of frames for a specific date"""
        date_dir = self.base_path / date / "frames"
        if not date_dir.exists():
            return []
            
        frames = []
        for frame_file in sorted(date_dir.glob("*.jpg")):
            frames.append({
                "filename": frame_file.name,
                "path": str(frame_file.relative_to(self.base_path)),
                "timestamp": frame_file.stem.replace("_", " ")
            })
        return frames
