"""
Camera manager for handling RTSP stream
"""
import asyncio
import logging
import cv2
import numpy as np
from typing import Optional, List, Callable
from datetime import datetime
from queue import Queue, Full
import threading

logger = logging.getLogger(__name__)


class CameraManager:
    """Manages RTSP camera connection and frame distribution"""
    
    def __init__(self, rtsp_url: str, reconnect_interval: int = 5):
        self.rtsp_url = rtsp_url
        self.reconnect_interval = reconnect_interval
        self.cap: Optional[cv2.VideoCapture] = None
        self.is_running = False
        self.current_frame: Optional[np.ndarray] = None
        self.frame_lock = threading.Lock()
        self.subscribers: List[Callable] = []
        self.frame_count = 0
        self.last_frame_time = None
        
    async def start(self):
        """Start camera capture"""
        self.is_running = True
        asyncio.create_task(self._capture_loop())
        logger.info(f"Camera manager started for {self.rtsp_url}")
        
    async def stop(self):
        """Stop camera capture"""
        self.is_running = False
        if self.cap:
            self.cap.release()
        logger.info("Camera manager stopped")
        
    async def _capture_loop(self):
        """Main capture loop running in background"""
        consecutive_failures = 0
        max_failures = 10
        
        while self.is_running:
            try:
                if not self.cap or not self.cap.isOpened():
                    await self._connect()
                    if not self.cap or not self.cap.isOpened():
                        # Connection failed, wait before retry
                        await asyncio.sleep(self.reconnect_interval)
                        continue
                    consecutive_failures = 0
                
                if self.cap and self.cap.isOpened():
                    ret, frame = self.cap.read()
                    
                    if ret and frame is not None:
                        with self.frame_lock:
                            self.current_frame = frame.copy()
                            self.frame_count += 1
                            self.last_frame_time = datetime.now()
                        consecutive_failures = 0
                        
                        # Notify subscribers
                        for subscriber in self.subscribers:
                            try:
                                subscriber(frame.copy())
                            except Exception as e:
                                logger.error(f"Error in subscriber: {e}", exc_info=True)
                    else:
                        consecutive_failures += 1
                        if consecutive_failures >= max_failures:
                            logger.warning(f"Failed to read frame {consecutive_failures} times, reconnecting...")
                            await self._reconnect()
                            consecutive_failures = 0
                
                await asyncio.sleep(0.01)  # ~100 FPS max
                
            except Exception as e:
                logger.error(f"Error in capture loop: {e}", exc_info=True)
                consecutive_failures += 1
                if consecutive_failures >= max_failures:
                    await asyncio.sleep(self.reconnect_interval)
                    consecutive_failures = 0
                else:
                    await asyncio.sleep(0.1)
                
    async def _connect(self):
        """Connect to RTSP stream with timeout"""
        try:
            logger.info(f"Connecting to camera: {self.rtsp_url}")
            
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            try:
                # Create VideoCapture with specific options
                def create_capture():
                    cap = cv2.VideoCapture(self.rtsp_url)
                    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                    return cap
                
                self.cap = await asyncio.wait_for(
                    loop.run_in_executor(None, create_capture),
                    timeout=15.0  # 15 second timeout
                )
            except asyncio.TimeoutError:
                logger.error("Camera connection timed out after 15 seconds - camera may be offline or URL incorrect")
                self.cap = None
                return
            
            if self.cap and self.cap.isOpened():
                logger.info("Camera connected successfully")
                # Test read a frame to verify it's actually working
                ret, frame = self.cap.read()
                if ret and frame is not None:
                    logger.info(f"Camera verified - frame size: {frame.shape}")
                else:
                    logger.warning("Camera opened but cannot read frames")
            else:
                logger.error("Failed to connect to camera - check RTSP URL and camera availability")
                self.cap = None
        except Exception as e:
            logger.error(f"Exception during camera connection: {e}", exc_info=True)
            self.cap = None
            
    async def _reconnect(self):
        """Reconnect to camera"""
        if self.cap:
            self.cap.release()
        await asyncio.sleep(self.reconnect_interval)
        await self._connect()
        
    def get_frame(self) -> Optional[np.ndarray]:
        """Get current frame (thread-safe)"""
        with self.frame_lock:
            if self.current_frame is not None:
                return self.current_frame.copy()
        return None
        
    def subscribe(self, callback: Callable):
        """Subscribe to frame updates"""
        self.subscribers.append(callback)
        logger.debug(f"Subscriber added. Total subscribers: {len(self.subscribers)}")
        
    def unsubscribe(self, callback: Callable):
        """Unsubscribe from frame updates"""
        if callback in self.subscribers:
            self.subscribers.remove(callback)
            logger.debug(f"Subscriber removed. Total subscribers: {len(self.subscribers)}")
            
    def get_stats(self) -> dict:
        """Get camera statistics"""
        is_connected = self.cap is not None and self.cap.isOpened()
        return {
            "is_connected": is_connected,
            "status_message": "Connected and streaming" if is_connected else "Camera unavailable - check connection and RTSP URL",
            "frame_count": self.frame_count,
            "last_frame_time": self.last_frame_time.isoformat() if self.last_frame_time else None,
            "subscribers": len(self.subscribers)
        }
