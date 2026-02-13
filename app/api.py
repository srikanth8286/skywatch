"""
FastAPI routes for SkyWatch
"""
from fastapi import APIRouter, HTTPException, Response, Request
from fastapi.responses import StreamingResponse, FileResponse, JSONResponse
import cv2
import numpy as np
from pathlib import Path
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/status")
async def get_status(request: Request):
    """Get system status"""
    camera = request.app.state.camera_manager
    services = request.app.state.services
    
    service_stats = {}
    for service in services:
        name = service.__class__.__name__.replace("Service", "").lower()
        service_stats[name] = service.get_stats()
    
    return {
        "status": "running",
        "camera": camera.get_stats() if camera else None,
        "services": service_stats,
        "timestamp": datetime.now().isoformat()
    }


@router.get("/stream")
async def video_stream(request: Request):
    """Live MJPEG stream"""
    camera = request.app.state.camera_manager
    if not camera:
        raise HTTPException(status_code=503, detail="Camera not available")
    
    async def generate():
        from app.config import settings
        try:
            while True:
                # Check if client disconnected
                if await request.is_disconnected():
                    break
                    
                frame = camera.get_frame()
                if frame is not None:
                    try:
                        # Encode frame as JPEG
                        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), settings.advanced.jpeg_quality_live]
                        _, buffer = cv2.imencode('.jpg', frame, encode_param)
                        frame_bytes = buffer.tobytes()
                        
                        yield (b'--frame\r\n'
                               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                    except Exception as e:
                        logger.error(f"Error encoding frame: {e}")
                        await asyncio.sleep(0.1)
                        continue
                
                await asyncio.sleep(0.033)  # ~30 FPS
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Stream error: {e}", exc_info=True)
    
    return StreamingResponse(
        generate(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )


@router.get("/snapshot")
async def get_snapshot(request: Request):
    """Get current frame as JPEG"""
    camera = request.app.state.camera_manager
    if not camera:
        raise HTTPException(status_code=503, detail="Camera not available")
    
    frame = camera.get_frame()
    if frame is None:
        raise HTTPException(status_code=503, detail="No frame available")
    
    _, buffer = cv2.imencode('.jpg', frame)
    return Response(content=buffer.tobytes(), media_type="image/jpeg")


@router.get("/timelapse/dates")
async def get_timelapse_dates(request: Request):
    """Get available timelapse dates"""
    services = request.app.state.services
    for service in services:
        if service.__class__.__name__ == "TimelapseService":
            return {"dates": service.get_available_dates()}
    raise HTTPException(status_code=404, detail="Timelapse service not found")


@router.get("/timelapse/frames/{date}")
async def get_timelapse_frames(date: str, request: Request):
    """Get video info for a specific date"""
    services = request.app.state.services
    for service in services:
        if service.__class__.__name__ == "TimelapseService":
            video_path = service.get_video_path(date)
            if video_path.exists():
                return {
                    "date": date,
                    "type": "video",
                    "path": str(video_path.name),
                    "exists": True
                }
            else:
                return {
                    "date": date,
                    "type": "video",
                    "exists": False,
                    "message": "Video not yet created or no frames captured for this date"
                }
    raise HTTPException(status_code=404, detail="Timelapse service not found")


@router.get("/timelapse/video/{date}")
async def get_timelapse_video(date: str, request: Request):
    """Stream timelapse video file directly"""
    from app.config import settings
    services = request.app.state.services
    
    timelapse_service = None
    for service in services:
        if service.__class__.__name__ == "TimelapseService":
            timelapse_service = service
            break
    
    if not timelapse_service:
        raise HTTPException(status_code=404, detail="Timelapse service not found")
    
    video_path = timelapse_service.get_video_path(date)
    if not video_path.exists():
        raise HTTPException(status_code=404, detail=f"No video found for {date}")
    
    return FileResponse(
        video_path,
        media_type="video/mp4",
        headers={"Accept-Ranges": "bytes"}
    )


@router.get("/timelapse/play/{date}")
async def play_timelapse_legacy(date: str, speed: int = 24, request: Request = None):
    """Legacy MJPEG stream endpoint - redirects to video"""
    return {"message": "Use /timelapse/video/{date} for video playback"}


@router.get("/timelapse/download/{date}")
async def download_timelapse_video(date: str, fps: int = 24, request: Request = None):
    """Compile and download timelapse as MP4 video"""
    from app.config import settings
    import tempfile
    import subprocess
    
    services = request.app.state.services
    
    timelapse_service = None
    for service in services:
        if service.__class__.__name__ == "TimelapseService":
            timelapse_service = service
            break
    
    if not timelapse_service:
        raise HTTPException(status_code=404, detail="Timelapse service not found")
    
    frames = timelapse_service.get_frames_for_date(date)
    if not frames:
        raise HTTPException(status_code=404, detail="No frames found for date")
    
    # Check if compiled video already exists
    base_path = Path(settings.storage.base_path) / "timelapse"
    video_path = base_path / f"timelapse_{date}.mp4"
    
    if not video_path.exists():
        # Compile video using ffmpeg
        try:
            # Create temporary file list
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                list_file = f.name
                for frame_info in frames:
                    frame_path = base_path / frame_info["path"]
                    if frame_path.exists():
                        # FFmpeg concat requires duration for each file
                        f.write(f"file '{frame_path.absolute()}'\n")
                        f.write(f"duration {1.0/fps}\n")
                # Duplicate last frame to ensure it shows
                if frames:
                    last_frame = base_path / frames[-1]["path"]
                    if last_frame.exists():
                        f.write(f"file '{last_frame.absolute()}'\n")
            
            # Compile video with ffmpeg
            cmd = [
                'ffmpeg', '-y',
                '-f', 'concat',
                '-safe', '0',
                '-i', list_file,
                '-vf', f'fps={fps}',
                '-pix_fmt', 'yuv420p',
                '-c:v', 'libx264',
                '-preset', 'medium',
                '-crf', '23',
                str(video_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            # Clean up temp file
            Path(list_file).unlink()
            
            if result.returncode != 0:
                raise HTTPException(status_code=500, detail=f"Video compilation failed: {result.stderr}")
                
        except FileNotFoundError:
            raise HTTPException(status_code=500, detail="ffmpeg not installed. Please install ffmpeg to compile videos.")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error compiling video: {str(e)}")
    
    return FileResponse(
        video_path,
        media_type="video/mp4",
        filename=f"skywatch_timelapse_{date}.mp4"
    )


@router.get("/solargraph/composite")
async def get_solargraph_composite(request: Request):
    """Get solargraph composite image"""
    services = request.app.state.services
    for service in services:
        if service.__class__.__name__ == "SolargraphService":
            composite_path = service.get_composite_path()
            if composite_path.exists():
                return FileResponse(composite_path)
            else:
                raise HTTPException(status_code=404, detail="Composite not yet created")
    raise HTTPException(status_code=404, detail="Solargraph service not found")


@router.post("/solargraph/reset")
async def reset_solargraph(request: Request):
    """Reset/clear the solargraph composite"""
    services = request.app.state.services
    for service in services:
        if service.__class__.__name__ == "SolargraphService":
            service.reset_composite()
            return {"message": "Solargraph composite reset successfully"}
    raise HTTPException(status_code=404, detail="Solargraph service not found")


@router.get("/lunar/composite")
async def get_lunar_composite(request: Request):
    """Get lunar composite image"""
    services = request.app.state.services
    for service in services:
        if service.__class__.__name__ == "LunarService":
            composite_path = service.get_composite_path()
            if composite_path.exists():
                return FileResponse(composite_path)
            else:
                raise HTTPException(status_code=404, detail="Composite not yet created")
    raise HTTPException(status_code=404, detail="Lunar service not found")


@router.post("/lunar/reset")
async def reset_lunar(request: Request):
    """Reset/clear the lunar composite"""
    services = request.app.state.services
    for service in services:
        if service.__class__.__name__ == "LunarService":
            service.reset_composite()
            return {"message": "Lunar composite reset successfully"}
    raise HTTPException(status_code=404, detail="Lunar service not found")


@router.get("/motion/events")
async def get_motion_events(limit: int = 20, request: Request = None):
    """Get recent motion detection events"""
    services = request.app.state.services
    for service in services:
        if service.__class__.__name__ == "MotionDetectionService":
            events = service.get_recent_events(limit)
            return {"events": events, "count": len(events)}
    raise HTTPException(status_code=404, detail="Motion detection service not found")


@router.get("/storage/{path:path}")
async def get_storage_file(path: str):
    """Serve files from storage"""
    from app.config import settings
    file_path = Path(settings.storage.base_path) / path
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    if not file_path.is_file():
        raise HTTPException(status_code=400, detail="Not a file")
    
    return FileResponse(file_path)


@router.get("/settings")
async def get_settings():
    """Get current settings"""
    from app.settings import load_settings
    import copy
    try:
        settings = load_settings()
        # Create a deep copy to avoid modifying the original
        settings_copy = copy.deepcopy(settings)
        
        # Remove sensitive data from response
        if 'camera' in settings_copy and 'rtsp_url' in settings_copy['camera']:
            # Mask password in RTSP URL
            url = settings_copy['camera']['rtsp_url']
            if '@' in url and '://' in url:
                protocol = url.split('://')[0]
                rest = url.split('://')[1]
                if '@' in rest:
                    creds, location = rest.split('@', 1)
                    if ':' in creds:
                        user = creds.split(':')[0]
                        settings_copy['camera']['rtsp_url'] = f"{protocol}://{user}:****@{location}"
        return settings_copy
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/settings")
async def update_settings(settings: Dict[str, Any], request: Request):
    """Update settings and apply changes immediately without restart"""
    from app.settings import save_settings, validate_settings
    from app.config import reload_config
    
    # Check if password was corrupted (contains ****)
    if 'camera' in settings and 'rtsp_url' in settings['camera']:
        if '****' in settings['camera']['rtsp_url']:
            raise HTTPException(status_code=400, detail="Cannot save settings with masked password. Please re-enter the full RTSP URL.")
    
    # Validate settings
    valid, message = validate_settings(settings)
    if not valid:
        raise HTTPException(status_code=400, detail=f"Invalid settings: {message}")
    
    # Save settings to file
    success = save_settings(settings)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to save settings")
    
    # Reload global settings object
    new_settings = reload_config()
    
    # Apply camera URL changes immediately
    if 'camera' in settings and 'rtsp_url' in settings['camera']:
        camera_manager = request.app.state.camera_manager
        new_url = settings['camera']['rtsp_url']
        await camera_manager.update_rtsp_url(new_url)
    
    # Update services with new settings
    for service in request.app.state.services:
        if hasattr(service, 'update_settings'):
            service.update_settings(new_settings)
        
    return {
        "success": True,
        "message": "Settings applied immediately. No restart required.",
        "restart_required": False
    }


@router.post("/settings/restart")
async def restart_application():
    """Trigger application restart"""
    import os
    import signal
    
    # Send signal to restart (handled by systemd or supervisor)
    # For now, just return a message
    return {
        "message": "Please restart SkyWatch manually to apply new settings",
        "command": "systemctl restart skywatch  # or restart the process manually"
    }

