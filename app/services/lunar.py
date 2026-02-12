"""
Lunar tracking service for moon position compositing
"""
import asyncio
import logging
import cv2
import numpy as np
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class LunarService:
    """Service for capturing and compositing moon positions"""
    
    def __init__(self, camera_manager, settings):
        self.camera = camera_manager
        self.settings = settings
        self.is_running = False
        self.task = None
        self.detection_count = 0
        
        # Setup storage
        self.base_path = Path(settings.storage.base_path) / "lunar"
        self.raw_path = self.base_path / "raw"
        self.raw_path.mkdir(parents=True, exist_ok=True)
        
        self.composite_path = self.base_path / "composite.jpg"
        self.composite_image = None
        
    async def start(self):
        """Start lunar service"""
        self.is_running = True
        
        # Load existing composite if available
        if self.composite_path.exists():
            self.composite_image = cv2.imread(str(self.composite_path))
            logger.info("Loaded existing lunar composite")
        
        self.task = asyncio.create_task(self._capture_loop())
        logger.info("Lunar service started")
        
    async def stop(self):
        """Stop lunar service"""
        self.is_running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        logger.info("Lunar service stopped")
        
    async def _capture_loop(self):
        """Main capture loop"""
        while self.is_running:
            try:
                if self._is_nighttime():
                    await self._detect_and_capture_moon()
                else:
                    logger.debug("Outside nighttime hours, skipping moon detection")
                    
                await asyncio.sleep(self.settings.lunar.detection_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in lunar capture: {e}")
                await asyncio.sleep(5)
                
    def _is_nighttime(self) -> bool:
        """Check if current time is nighttime"""
        if not self.settings.lunar.nighttime_only:
            return True
            
        # Simple nighttime check: 8 PM to 6 AM
        current_hour = datetime.now().hour
        return current_hour >= 20 or current_hour <= 6
        
    async def _detect_and_capture_moon(self):
        """Detect moon in frame and capture if found"""
        frame = self.camera.get_frame()
        if frame is None:
            return
            
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Find bright areas (moon should be bright against dark sky)
        _, thresh = cv2.threshold(
            gray,
            self.settings.lunar.brightness_threshold,
            255,
            cv2.THRESH_BINARY
        )
        
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (9, 9), 2)
        
        # Find circles (potential moon)
        circles = cv2.HoughCircles(
            blurred,
            cv2.HOUGH_GRADIENT,
            dp=1,
            minDist=100,
            param1=50,
            param2=30,
            minRadius=self.settings.lunar.min_radius,
            maxRadius=self.settings.lunar.max_radius
        )
        
        if circles is not None and len(circles[0]) > 0:
            # Take the brightest circle
            circles = np.uint16(np.around(circles))
            best_circle = None
            max_brightness = 0
            
            for circle in circles[0]:
                x, y, r = circle
                mask = np.zeros_like(gray)
                cv2.circle(mask, (x, y), r, 255, -1)
                mean_brightness = cv2.mean(gray, mask=mask)[0]
                
                if mean_brightness > max_brightness:
                    max_brightness = mean_brightness
                    best_circle = (x, y, r)
                    
            if best_circle:
                await self._capture_moon(frame, best_circle)
                
    async def _capture_moon(self, frame, circle_info):
        """Capture moon and update composite"""
        x, y, r = circle_info
        
        # Save raw capture
        now = datetime.now()
        filename = now.strftime("%Y-%m-%d_%H-%M-%S.jpg")
        filepath = self.raw_path / filename
        
        # Draw circle on frame for debugging
        debug_frame = frame.copy()
        cv2.circle(debug_frame, (x, y), r, (0, 255, 255), 2)
        cv2.imwrite(str(filepath), debug_frame)
        
        self.detection_count += 1
        logger.info(f"Moon detected and captured: {filename} at ({x}, {y}) radius {r}")
        
        # Update composite
        await self._update_composite(frame, circle_info)
        
    async def _update_composite(self, frame, circle_info):
        """Update composite image with new moon position"""
        if self.composite_image is None:
            # Initialize composite with first frame (darkened)
            self.composite_image = (frame * 0.2).astype(np.uint8)
        
        # Extract moon region
        x, y, r = circle_info
        mask = np.zeros(frame.shape[:2], dtype=np.uint8)
        cv2.circle(mask, (x, y), r, 255, -1)
        
        # Blend moon into composite using maximum intensity
        moon_region = cv2.bitwise_and(frame, frame, mask=mask)
        
        # Use maximum pixel values to accumulate moon trails
        self.composite_image = np.maximum(self.composite_image, moon_region)
        
        # Save composite
        cv2.imwrite(str(self.composite_path), self.composite_image)
        logger.debug("Lunar composite image updated")
        
    def get_stats(self) -> dict:
        """Get service statistics"""
        return {
            "enabled": self.settings.lunar.enabled,
            "is_running": self.is_running,
            "detection_count": self.detection_count,
            "interval": self.settings.lunar.detection_interval,
            "composite_exists": self.composite_path.exists(),
            "storage_path": str(self.base_path)
        }
        
    def get_composite_path(self) -> Path:
        """Get path to composite image"""
        return self.composite_path
