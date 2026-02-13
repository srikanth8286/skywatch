"""
Solargraph service for tracking and compositing sun positions
"""
import asyncio
import logging
import cv2
import numpy as np
from pathlib import Path
from datetime import datetime, time
from astral import LocationInfo
from astral.sun import sun

logger = logging.getLogger(__name__)


class SolargraphService:
    """Service for capturing and compositing sun positions"""
    
    def __init__(self, camera_manager, settings):
        self.camera = camera_manager
        self.settings = settings
        self.is_running = False
        self.task = None
        self.detection_count = 0
        
        # Setup storage
        self.base_path = Path(settings.storage.base_path) / "solargraph"
        self.raw_path = self.base_path / "raw"
        self.raw_path.mkdir(parents=True, exist_ok=True)
        
        self.composite_path = self.base_path / "composite.jpg"
        self.composite_image = None
        
        # Setup location for sunrise/sunset
        if settings.solargraph.latitude != 0 or settings.solargraph.longitude != 0:
            self.location = LocationInfo(
                latitude=settings.solargraph.latitude,
                longitude=settings.solargraph.longitude
            )
        else:
            self.location = None
            
    async def start(self):
        """Start solargraph service"""
        self.is_running = True
        
        # Load existing composite if available
        if self.composite_path.exists():
            self.composite_image = cv2.imread(str(self.composite_path))
            logger.info("Loaded existing solargraph composite")
        
        self.task = asyncio.create_task(self._capture_loop())
        logger.info("Solargraph service started")
        
    async def stop(self):
        """Stop solargraph service"""
        self.is_running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        logger.info("Solargraph service stopped")
        
    async def _capture_loop(self):
        """Main capture loop"""
        while self.is_running:
            try:
                if self._is_daytime():
                    await self._detect_and_capture_sun()
                else:
                    logger.debug("Outside daylight hours, skipping sun detection")
                    
                await asyncio.sleep(self.settings.solargraph.detection_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in solargraph capture: {e}")
                await asyncio.sleep(5)
                
    def _is_daytime(self) -> bool:
        """Check if current time is during daylight hours"""
        if not self.settings.solargraph.daytime_only:
            return True
            
        if self.location is None:
            # If no location set, assume daytime from 6 AM to 8 PM
            current_hour = datetime.now().hour
            return 6 <= current_hour <= 20
            
        try:
            s = sun(self.location.observer, date=datetime.now())
            now = datetime.now().time()
            sunrise = s["sunrise"].time()
            sunset = s["sunset"].time()
            return sunrise <= now <= sunset
        except Exception as e:
            logger.error(f"Error calculating daylight hours: {e}")
            return True
            
    async def _detect_and_capture_sun(self):
        """Detect sun in frame and capture if found"""
        frame = self.camera.get_frame()
        if frame is None:
            return
            
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (9, 9), 2)
        
        # Find circles (potential sun) with stricter parameters
        circles = cv2.HoughCircles(
            blurred,
            cv2.HOUGH_GRADIENT,
            dp=1,
            minDist=200,  # Increased - sun should be alone in the sky
            param1=100,    # Increased - stricter edge detection
            param2=50,     # Increased - stricter circle detection
            minRadius=self.settings.solargraph.min_radius,
            maxRadius=self.settings.solargraph.max_radius
        )
        
        if circles is not None and len(circles[0]) > 0:
            # Take the brightest circle that meets sun criteria
            circles = np.uint16(np.around(circles))
            best_circle = None
            max_score = 0
            
            for circle in circles[0]:
                x, y, r = circle
                
                # Validate this could be the sun
                if not self._validate_sun_candidate(gray, x, y, r):
                    continue
                
                # Calculate mask for this circle
                mask = np.zeros_like(gray)
                cv2.circle(mask, (x, y), r, 255, -1)
                mean_brightness = cv2.mean(gray, mask=mask)[0]
                
                # Score based on brightness and size
                # Sun should be very bright and reasonably sized
                score = mean_brightness * (r / self.settings.solargraph.max_radius)
                
                if score > max_score and mean_brightness > self.settings.solargraph.brightness_threshold:
                    max_score = score
                    best_circle = (x, y, r)
                    
            if best_circle:
                await self._capture_sun(frame, best_circle)
    
    def _validate_sun_candidate(self, gray, x, y, r) -> bool:
        """Validate if a circle could be the sun"""
        h, w = gray.shape
        
        # Sun shouldn't be at the very edge of the frame
        margin = 50
        if x < margin or x > w - margin or y < margin or y > h - margin:
            return False
        
        # Check if the circle area is uniformly bright (not just a small bright spot)
        mask = np.zeros_like(gray)
        cv2.circle(mask, (x, y), r, 255, -1)
        
        # Get pixel values in the circle
        circle_pixels = gray[mask > 0]
        if len(circle_pixels) == 0:
            return False
        
        mean_brightness = np.mean(circle_pixels)
        std_brightness = np.std(circle_pixels)
        
        # Sun should be very bright
        if mean_brightness < self.settings.solargraph.brightness_threshold:
            return False
        
        # Sun should be relatively uniform (not a random bright spot)
        # Low standard deviation means uniform brightness
        if std_brightness > 50:  # Too much variation
            return False
        
        # Check the area around the circle - sun should have a glow/gradient
        outer_mask = np.zeros_like(gray)
        cv2.circle(outer_mask, (x, y), int(r * 1.5), 255, -1)
        cv2.circle(outer_mask, (x, y), r, 0, -1)  # Remove inner circle
        
        outer_pixels = gray[outer_mask > 0]
        if len(outer_pixels) > 0:
            outer_brightness = np.mean(outer_pixels)
            # There should be a significant drop in brightness outside the sun
            if mean_brightness - outer_brightness < 30:
                return False
        
        return True
                
    async def _capture_sun(self, frame, circle_info):
        """Capture sun and update composite"""
        x, y, r = circle_info
        
        # Save raw capture
        now = datetime.now()
        filename = now.strftime("%Y-%m-%d_%H-%M-%S.jpg")
        filepath = self.raw_path / filename
        
        # Draw circle on frame for debugging
        debug_frame = frame.copy()
        cv2.circle(debug_frame, (x, y), r, (0, 255, 0), 2)
        cv2.imwrite(str(filepath), debug_frame)
        
        self.detection_count += 1
        logger.info(f"Sun detected and captured: {filename} at ({x}, {y}) radius {r}")
        
        # Update composite
        await self._update_composite(frame, circle_info)
        
    async def _update_composite(self, frame, circle_info):
        """Update composite image with new sun position"""
        if self.composite_image is None:
            # Initialize composite with first frame (darkened)
            self.composite_image = (frame * 0.3).astype(np.uint8)
        
        # Extract sun region
        x, y, r = circle_info
        mask = np.zeros(frame.shape[:2], dtype=np.uint8)
        cv2.circle(mask, (x, y), r, 255, -1)
        
        # Blend sun into composite using maximum intensity
        sun_region = cv2.bitwise_and(frame, frame, mask=mask)
        
        # Use maximum pixel values to accumulate sun trails
        self.composite_image = np.maximum(self.composite_image, sun_region)
        
        # Save composite
        cv2.imwrite(str(self.composite_path), self.composite_image)
        logger.debug("Composite image updated")
        
    def get_stats(self) -> dict:
        """Get service statistics"""
        return {
            "enabled": self.settings.solargraph.enabled,
            "is_running": self.is_running,
            "detection_count": self.detection_count,
            "interval": self.settings.solargraph.detection_interval,
            "composite_exists": self.composite_path.exists(),
            "storage_path": str(self.base_path)
        }
        
    def get_composite_path(self) -> Path:
        """Get path to composite image"""
        return self.composite_path
    
    def reset_composite(self):
        """Reset/clear the composite image"""
        self.composite_image = None
        if self.composite_path.exists():
            self.composite_path.unlink()
        self.detection_count = 0
        logger.info("Solargraph composite reset")
