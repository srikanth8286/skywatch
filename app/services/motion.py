"""
Motion detection service for capturing wildlife/events
"""
import asyncio
import logging
import cv2
import numpy as np
from pathlib import Path
from datetime import datetime
import time

logger = logging.getLogger(__name__)


class MotionDetectionService:
    """Service for detecting motion and capturing burst images"""
    
    def __init__(self, camera_manager, settings):
        self.camera = camera_manager
        self.settings = settings
        self.is_running = False
        self.task = None
        self.detection_count = 0
        
        # Motion detection state
        self.previous_frame = None
        self.last_detection_time = 0
        
        # Setup storage
        self.base_path = Path(settings.storage.base_path) / "motion"
        self.base_path.mkdir(parents=True, exist_ok=True)
        
    async def start(self):
        """Start motion detection service"""
        self.is_running = True
        self.task = asyncio.create_task(self._detection_loop())
        logger.info("Motion detection service started")
        
    async def stop(self):
        """Stop motion detection service"""
        self.is_running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        logger.info("Motion detection service stopped")
        
    async def _detection_loop(self):
        """Main detection loop"""
        while self.is_running:
            try:
                await self._detect_motion()
                await asyncio.sleep(0.1)  # Check 10 times per second
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in motion detection: {e}")
                await asyncio.sleep(1)
                
    async def _detect_motion(self):
        """Detect motion in current frame"""
        frame = self.camera.get_frame()
        if frame is None:
            return
            
        # Convert to grayscale and blur
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)
        
        # Initialize previous frame
        if self.previous_frame is None:
            self.previous_frame = gray
            return
            
        # Compute difference
        frame_delta = cv2.absdiff(self.previous_frame, gray)
        thresh = cv2.threshold(frame_delta, self.settings.motion.sensitivity, 255, cv2.THRESH_BINARY)[1]
        
        # Dilate to fill in holes
        thresh = cv2.dilate(thresh, None, iterations=2)
        
        # Find contours
        contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Check for significant motion
        motion_detected = False
        for contour in contours:
            if cv2.contourArea(contour) >= self.settings.motion.min_area:
                motion_detected = True
                break
                
        if motion_detected:
            current_time = time.time()
            if current_time - self.last_detection_time >= self.settings.motion.cooldown:
                await self._capture_burst(frame)
                self.last_detection_time = current_time
                
        # Update previous frame
        self.previous_frame = gray
        
    async def _capture_burst(self, trigger_frame):
        """Capture burst of images when motion detected"""
        now = datetime.now()
        event_dir = self.base_path / now.strftime("%Y-%m-%d_%H-%M-%S")
        event_dir.mkdir(parents=True, exist_ok=True)
        
        self.detection_count += 1
        logger.info(f"Motion detected! Capturing burst to {event_dir.name}")
        
        # Save trigger frame
        cv2.imwrite(str(event_dir / "trigger.jpg"), trigger_frame)
        
        # Capture burst
        frame_interval = 1.0 / self.settings.motion.burst_fps
        for i in range(self.settings.motion.burst_count):
            frame = self.camera.get_frame()
            if frame is not None:
                filename = f"burst_{i:03d}.jpg"
                cv2.imwrite(str(event_dir / filename), frame)
            await asyncio.sleep(frame_interval)
            
        logger.info(f"Burst capture complete: {self.settings.motion.burst_count} frames")
        
    def get_stats(self) -> dict:
        """Get service statistics"""
        return {
            "enabled": self.settings.motion.enabled,
            "is_running": self.is_running,
            "detection_count": self.detection_count,
            "sensitivity": self.settings.motion.sensitivity,
            "storage_path": str(self.base_path)
        }
        
    def get_recent_events(self, limit: int = 20) -> list:
        """Get list of recent motion events"""
        events = []
        if self.base_path.exists():
            event_dirs = sorted(self.base_path.iterdir(), reverse=True)
            for event_dir in event_dirs[:limit]:
                if event_dir.is_dir():
                    frame_count = len(list(event_dir.glob("burst_*.jpg")))
                    events.append({
                        "timestamp": event_dir.name,
                        "path": str(event_dir.relative_to(self.base_path)),
                        "frame_count": frame_count
                    })
        return events
