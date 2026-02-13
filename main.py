"""
SkyWatch - Smart Camera Capture System
Main application entry point
"""
import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.camera import CameraManager
from app.api import router
from app.services.timelapse import TimelapseService
from app.services.solargraph import SolargraphService
from app.services.lunar import LunarService
from app.services.motion import MotionDetectionService

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.advanced.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    
    logger.info("Starting SkyWatch...")
    
    # Initialize camera
    camera_manager = CameraManager(settings.camera.rtsp_url)
    await camera_manager.start()
    
    # Store in app state
    app.state.camera_manager = camera_manager
    app.state.services = []
    app.state._tasks = []  # Track background tasks for error handling
    
    # Initialize and start services
    if settings.timelapse.enabled:
        timelapse_service = TimelapseService(camera_manager, settings)
        app.state.services.append(timelapse_service)
        await timelapse_service.start()
        logger.info("Timelapse service started")
    
    if settings.solargraph.enabled:
        solargraph_service = SolargraphService(camera_manager, settings)
        app.state.services.append(solargraph_service)
        await solargraph_service.start()
        logger.info("Solargraph service started")
    
    if settings.lunar.enabled:
        lunar_service = LunarService(camera_manager, settings)
        app.state.services.append(lunar_service)
        await lunar_service.start()
        logger.info("Lunar service started")
    
    if settings.motion.enabled:
        motion_service = MotionDetectionService(camera_manager, settings)
        app.state.services.append(motion_service)
        await motion_service.start()
        logger.info("Motion detection service started")
    
    # Set up a global exception handler for unhandled task errors
    loop = asyncio.get_running_loop()
    loop.set_exception_handler(_handle_task_exception)
    
    logger.info(f"SkyWatch is ready! Access at http://localhost:{settings.server.port}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down SkyWatch...")
    for service in app.state.services:
        try:
            await service.stop()
        except Exception as e:
            logger.error(f"Error stopping service: {e}")
    if app.state.camera_manager:
        try:
            await app.state.camera_manager.stop()
        except Exception as e:
            logger.error(f"Error stopping camera: {e}")
    logger.info("SkyWatch stopped")


def _handle_task_exception(loop, context):
    """Global handler for unhandled asyncio task exceptions"""
    exception = context.get("exception")
    message = context.get("message", "")
    if exception:
        logger.error(f"Unhandled async exception: {exception} - {message}", exc_info=exception)
    else:
        logger.error(f"Unhandled async error: {message}")


# Create FastAPI app
app = FastAPI(
    title="SkyWatch",
    description="Smart Camera Capture System for Timelapses, Solargraphs, and Motion Detection",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.server.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api")

# Mount static files (frontend)
app.mount("/", StaticFiles(directory="app/static", html=True), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.server.host,
        port=settings.server.port,
        reload=False,
        log_level=settings.advanced.log_level.lower()
    )
