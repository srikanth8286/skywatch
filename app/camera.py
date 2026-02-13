"""
Camera manager for handling RTSP stream
"""
import asyncio
import logging
import cv2
import numpy as np
from typing import Optional, List, Callable
from datetime import datetime
import threading
import time

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
        self.last_frame_time: Optional[datetime] = None
        
        # Dedicated capture thread — keeps OpenCV completely off the event loop
        self._capture_thread: Optional[threading.Thread] = None
        
    async def start(self):
        """Start camera capture in a dedicated thread"""
        self.is_running = True
        self._capture_thread = threading.Thread(
            target=self._capture_thread_main,
            name="camera-capture",
            daemon=True,
        )
        self._capture_thread.start()
        logger.info(f"Camera manager started for {self.rtsp_url}")
        
    async def stop(self):
        """Stop camera capture"""
        self.is_running = False
        if self._capture_thread and self._capture_thread.is_alive():
            self._capture_thread.join(timeout=5.0)
        if self.cap:
            try:
                self.cap.release()
            except Exception:
                pass
        logger.info("Camera manager stopped")
    
    # ── Dedicated capture thread (runs entirely outside asyncio) ──────────
    
    def _capture_thread_main(self):
        """
        Main capture loop running in its own OS thread.
        All OpenCV calls happen here — never on the asyncio event loop.
        """
        consecutive_failures = 0
        max_failures = 10
        
        while self.is_running:
            try:
                # Connect if needed
                if not self.cap or not self.cap.isOpened():
                    self._connect_sync()
                    if not self.cap or not self.cap.isOpened():
                        time.sleep(self.reconnect_interval)
                        continue
                    consecutive_failures = 0
                
                ret, frame = self.cap.read()
                
                if ret and frame is not None:
                    with self.frame_lock:
                        self.current_frame = frame  # No copy — we own this reference
                        self.frame_count += 1
                        self.last_frame_time = datetime.now()
                    consecutive_failures = 0
                else:
                    consecutive_failures += 1
                    if consecutive_failures >= max_failures:
                        logger.warning(f"Failed to read frame {consecutive_failures} times, reconnecting...")
                        self._reconnect_sync()
                        consecutive_failures = 0
                    else:
                        time.sleep(0.05)
                    continue
                
                # Throttle to ~15 FPS — sufficient for all services, much lower CPU
                time.sleep(0.066)
                
            except Exception as e:
                logger.error(f"Error in capture thread: {e}", exc_info=True)
                consecutive_failures += 1
                if consecutive_failures >= max_failures:
                    time.sleep(self.reconnect_interval)
                    consecutive_failures = 0
                else:
                    time.sleep(0.5)
    
    def _connect_sync(self):
        """Connect to RTSP stream (called from capture thread only)"""
        try:
            logger.info(f"Connecting to camera: {self.rtsp_url}")
            
            # Release any existing capture
            if self.cap:
                try:
                    self.cap.release()
                except Exception:
                    pass
            
            # Try GStreamer first, fallback to default
            gst_pipeline = (
                f"rtspsrc location={self.rtsp_url} latency=0 ! "
                "rtph264depay ! h264parse ! avdec_h264 ! "
                "videoconvert ! appsink"
            )
            cap = cv2.VideoCapture(gst_pipeline, cv2.CAP_GSTREAMER)
            
            if not cap.isOpened():
                logger.info("GStreamer failed, trying default backend...")
                cap = cv2.VideoCapture(self.rtsp_url)
            
            if cap.isOpened():
                # Minimal buffer to avoid stale frames
                cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                
                # Verify with a test read
                ret, frame = cap.read()
                if ret and frame is not None:
                    logger.info(f"Camera connected - frame size: {frame.shape}")
                    with self.frame_lock:
                        self.current_frame = frame
                        self.frame_count += 1
                        self.last_frame_time = datetime.now()
                    self.cap = cap
                else:
                    logger.warning("Camera opened but cannot read frames")
                    cap.release()
                    self.cap = None
            else:
                logger.error("Failed to connect to camera - check RTSP URL")
                self.cap = None
        except Exception as e:
            logger.error(f"Exception during camera connection: {e}", exc_info=True)
            self.cap = None
    
    def _reconnect_sync(self):
        """Reconnect to camera (called from capture thread only)"""
        if self.cap:
            try:
                self.cap.release()
            except Exception:
                pass
            self.cap = None
        time.sleep(self.reconnect_interval)
        self._connect_sync()
        
    def get_frame(self) -> Optional[np.ndarray]:
        """Get current frame (thread-safe). Returns a copy."""
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
            
    async def update_rtsp_url(self, new_url: str):
        """Update RTSP URL and reconnect"""
        logger.info(f"Updating RTSP URL to {new_url}")
        self.rtsp_url = new_url
        # Release current capture — the thread will auto-reconnect with the new URL
        if self.cap:
            try:
                self.cap.release()
            except Exception:
                pass
            self.cap = None
        
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
