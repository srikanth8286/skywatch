"""
FastAPI routes for SkyWatch
"""
from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import StreamingResponse, FileResponse
import cv2
import numpy as np
from pathlib import Path
import asyncio
from datetime import datetime
import main

router = APIRouter()


@router.get("/status")
async def get_status():
    """Get system status"""
    camera = main.get_camera_manager()
    services = main.get_services()
    
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
async def video_stream():
    """Live MJPEG stream"""
    camera = main.get_camera_manager()
    if not camera:
        raise HTTPException(status_code=503, detail="Camera not available")
    
    async def generate():
        from app.config import settings
        while True:
            frame = camera.get_frame()
            if frame is not None:
                # Encode frame as JPEG
                encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), settings.advanced.jpeg_quality_live]
                _, buffer = cv2.imencode('.jpg', frame, encode_param)
                frame_bytes = buffer.tobytes()
                
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            
            await asyncio.sleep(0.033)  # ~30 FPS
    
    return StreamingResponse(
        generate(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )


@router.get("/snapshot")
async def get_snapshot():
    """Get current frame as JPEG"""
    camera = main.get_camera_manager()
    if not camera:
        raise HTTPException(status_code=503, detail="Camera not available")
    
    frame = camera.get_frame()
    if frame is None:
        raise HTTPException(status_code=503, detail="No frame available")
    
    _, buffer = cv2.imencode('.jpg', frame)
    return Response(content=buffer.tobytes(), media_type="image/jpeg")


@router.get("/timelapse/dates")
async def get_timelapse_dates():
    """Get available timelapse dates"""
    services = main.get_services()
    for service in services:
        if service.__class__.__name__ == "TimelapseService":
            return {"dates": service.get_available_dates()}
    raise HTTPException(status_code=404, detail="Timelapse service not found")


@router.get("/timelapse/frames/{date}")
async def get_timelapse_frames(date: str):
    """Get frames for a specific date"""
    services = main.get_services()
    for service in services:
        if service.__class__.__name__ == "TimelapseService":
            frames = service.get_frames_for_date(date)
            return {"date": date, "frames": frames, "count": len(frames)}
    raise HTTPException(status_code=404, detail="Timelapse service not found")


@router.get("/timelapse/play/{date}")
async def play_timelapse(date: str, speed: int = 24):
    """Stream timelapse for a date range as video"""
    from app.config import settings
    services = main.get_services()
    
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
    
    async def generate():
        base_path = Path(settings.storage.base_path) / "timelapse"
        for frame_info in frames:
            frame_path = base_path / frame_info["path"]
            if frame_path.exists():
                with open(frame_path, 'rb') as f:
                    frame_bytes = f.read()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            
            # Adjust speed (lower value = faster playback)
            await asyncio.sleep(1.0 / speed)
    
    return StreamingResponse(
        generate(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )


@router.get("/solargraph/composite")
async def get_solargraph_composite():
    """Get solargraph composite image"""
    services = main.get_services()
    for service in services:
        if service.__class__.__name__ == "SolargraphService":
            composite_path = service.get_composite_path()
            if composite_path.exists():
                return FileResponse(composite_path)
            else:
                raise HTTPException(status_code=404, detail="Composite not yet created")
    raise HTTPException(status_code=404, detail="Solargraph service not found")


@router.get("/lunar/composite")
async def get_lunar_composite():
    """Get lunar composite image"""
    services = main.get_services()
    for service in services:
        if service.__class__.__name__ == "LunarService":
            composite_path = service.get_composite_path()
            if composite_path.exists():
                return FileResponse(composite_path)
            else:
                raise HTTPException(status_code=404, detail="Composite not yet created")
    raise HTTPException(status_code=404, detail="Lunar service not found")


@router.get("/motion/events")
async def get_motion_events(limit: int = 20):
    """Get recent motion detection events"""
    services = main.get_services()
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
