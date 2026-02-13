"""
Configuration management for SkyWatch
"""
import yaml
from pathlib import Path
from pydantic import BaseModel
from typing import List


class CameraSettings(BaseModel):
    rtsp_url: str
    reconnect_interval: int = 5
    frame_width: int = 1920
    frame_height: int = 1080


class StorageSettings(BaseModel):
    base_path: str = "/storage"
    nas_enabled: bool = False
    nas_path: str = ""
    retention_days: int = 30


class TimelapseSettings(BaseModel):
    enabled: bool = True
    interval: int = 60
    quality: int = 90
    daily_video: bool = True
    video_fps: int = 24


class SolargraphSettings(BaseModel):
    enabled: bool = True
    detection_interval: int = 30
    brightness_threshold: int = 200
    min_radius: int = 10
    max_radius: int = 100
    daytime_only: bool = True
    latitude: float = 0.0
    longitude: float = 0.0


class LunarSettings(BaseModel):
    enabled: bool = True
    detection_interval: int = 60
    brightness_threshold: int = 150
    min_radius: int = 15
    max_radius: int = 150
    nighttime_only: bool = True


class MotionSettings(BaseModel):
    enabled: bool = True
    sensitivity: int = 25
    min_area: int = 500
    burst_count: int = 10
    burst_fps: int = 10
    cooldown: int = 5


class ServerSettings(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8080
    cors_origins: List[str] = ["*"]


class AdvancedSettings(BaseModel):
    max_frame_queue: int = 30
    jpeg_quality_live: int = 85
    log_level: str = "INFO"


class Settings(BaseModel):
    camera: CameraSettings
    storage: StorageSettings
    timelapse: TimelapseSettings
    solargraph: SolargraphSettings
    lunar: LunarSettings
    motion: MotionSettings
    server: ServerSettings
    advanced: AdvancedSettings


def load_config(config_path: str = "config.yaml") -> Settings:
    """Load configuration from YAML file"""
    config_file = Path(config_path)
    
    # Try local config first
    local_config = Path("config.local.yaml")
    if local_config.exists():
        config_file = local_config
    
    if not config_file.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_file}")
    
    with open(config_file, 'r') as f:
        config_data = yaml.safe_load(f)
    
    return Settings(**config_data)


def reload_config():
    """Reload configuration from file and update global settings"""
    global settings
    settings = load_config()
    return settings


# Global settings instance
settings = load_config()
