"""
Settings management module for SkyWatch
Handles reading and updating configuration
"""
import yaml
from pathlib import Path
from typing import Dict, Any
from pydantic import BaseModel, Field


class CameraSettings(BaseModel):
    rtsp_url: str = Field(..., description="Camera RTSP URL")
    reconnect_interval: int = Field(5, ge=1, le=60)
    frame_width: int = Field(1920, ge=640)
    frame_height: int = Field(1080, ge=480)


class StorageSettings(BaseModel):
    base_path: str
    nas_enabled: bool = False
    nas_path: str = ""
    retention_days: int = Field(30, ge=1, le=365, description="Days to keep data")


class TimelapseSettings(BaseModel):
    enabled: bool = True
    interval: int = Field(60, ge=1, le=3600, description="Seconds between frames")
    quality: int = Field(90, ge=1, le=100)
    daily_video: bool = True
    video_fps: int = Field(24, ge=1, le=60)


class SolargraphSettings(BaseModel):
    enabled: bool = True
    detection_interval: int = Field(30, ge=10, le=300)
    brightness_threshold: int = Field(200, ge=0, le=255)
    min_radius: int = Field(10, ge=5, le=50)
    max_radius: int = Field(100, ge=50, le=200)
    daytime_only: bool = True
    latitude: float = Field(0.0, ge=-90, le=90)
    longitude: float = Field(0.0, ge=-180, le=180)


class LunarSettings(BaseModel):
    enabled: bool = True
    detection_interval: int = Field(60, ge=10, le=300)
    brightness_threshold: int = Field(150, ge=0, le=255)
    min_radius: int = Field(15, ge=5, le=50)
    max_radius: int = Field(150, ge=50, le=300)
    nighttime_only: bool = True


class MotionSettings(BaseModel):
    enabled: bool = True
    sensitivity: int = Field(25, ge=0, le=100, description="0=most sensitive, 100=least")
    min_area: int = Field(500, ge=100, le=10000)
    burst_count: int = Field(10, ge=1, le=100)
    burst_fps: int = Field(10, ge=1, le=30)
    cooldown: int = Field(5, ge=0, le=60)


class ServerSettings(BaseModel):
    host: str = "0.0.0.0"
    port: int = Field(8080, ge=1024, le=65535)
    cors_origins: list = ["*"]


class AdvancedSettings(BaseModel):
    max_frame_queue: int = Field(30, ge=10, le=100)
    jpeg_quality_live: int = Field(85, ge=1, le=100)
    log_level: str = "INFO"


class AllSettings(BaseModel):
    camera: CameraSettings
    storage: StorageSettings
    timelapse: TimelapseSettings
    solargraph: SolargraphSettings
    lunar: LunarSettings
    motion: MotionSettings
    server: ServerSettings
    advanced: AdvancedSettings


CONFIG_FILE = Path("config.yaml")


def load_settings() -> Dict[str, Any]:
    """Load settings from config.yaml"""
    if not CONFIG_FILE.exists():
        raise FileNotFoundError("config.yaml not found")
    
    with open(CONFIG_FILE, 'r') as f:
        return yaml.safe_load(f)


def save_settings(settings: Dict[str, Any]) -> bool:
    """Save settings to config.yaml"""
    try:
        # Backup current config
        backup_file = Path("config.yaml.backup")
        if CONFIG_FILE.exists():
            import shutil
            shutil.copy(CONFIG_FILE, backup_file)
        
        # Write new settings
        with open(CONFIG_FILE, 'w') as f:
            yaml.dump(settings, f, default_flow_style=False, sort_keys=False)
        
        return True
    except Exception as e:
        print(f"Error saving settings: {e}")
        # Restore backup if save failed
        if backup_file.exists():
            import shutil
            shutil.copy(backup_file, CONFIG_FILE)
        return False


def validate_settings(settings: Dict[str, Any]) -> tuple[bool, str]:
    """Validate settings before saving"""
    try:
        AllSettings(**settings)
        return True, "Settings are valid"
    except Exception as e:
        return False, str(e)
