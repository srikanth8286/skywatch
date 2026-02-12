# Example Configuration

This is an example configuration file with common use cases.

## Basic Setup (Minimal Configuration)

```yaml
camera:
  rtsp_url: "rtsp://admin:password@192.168.1.205:554/stream"

storage:
  base_path: "./storage"

timelapse:
  enabled: true
  interval: 60

solargraph:
  enabled: false

lunar:
  enabled: false

motion:
  enabled: false

server:
  host: "0.0.0.0"
  port: 8080
```

## Hummingbird Monitoring

```yaml
camera:
  rtsp_url: "rtsp://admin:password@192.168.1.205:554/stream"

storage:
  base_path: "./storage"

timelapse:
  enabled: true
  interval: 300  # Every 5 minutes

motion:
  enabled: true
  sensitivity: 15      # More sensitive for small birds
  min_area: 200       # Smaller minimum area
  burst_count: 20     # More frames
  burst_fps: 15       # Higher FPS for action
  cooldown: 2         # Shorter cooldown

solargraph:
  enabled: false

lunar:
  enabled: false
```

## Astronomy Observation (Solargraph + Lunar)

```yaml
camera:
  rtsp_url: "rtsp://admin:password@192.168.1.205:554/stream"

storage:
  base_path: "/mnt/nas/skywatch"  # NAS storage
  nas_enabled: true

timelapse:
  enabled: true
  interval: 180  # Every 3 minutes
  daily_video: true

solargraph:
  enabled: true
  detection_interval: 30
  latitude: 40.7128      # New York
  longitude: -74.0060
  daytime_only: true

lunar:
  enabled: true
  detection_interval: 60
  nighttime_only: true

motion:
  enabled: false
```

## Security/Wildlife Monitoring (24/7)

```yaml
camera:
  rtsp_url: "rtsp://admin:password@192.168.1.205:554/stream"

storage:
  base_path: "./storage"

timelapse:
  enabled: true
  interval: 120  # Every 2 minutes

motion:
  enabled: true
  sensitivity: 30
  min_area: 1000
  burst_count: 15
  burst_fps: 10
  cooldown: 10

solargraph:
  enabled: false

lunar:
  enabled: false
```

## Weather Documentation

```yaml
camera:
  rtsp_url: "rtsp://admin:password@192.168.1.205:554/stream"

storage:
  base_path: "./storage"

timelapse:
  enabled: true
  interval: 60       # 1 frame per minute
  daily_video: true
  video_fps: 30      # Smoother playback

solargraph:
  enabled: true
  detection_interval: 60
  latitude: YOUR_LAT
  longitude: YOUR_LON

lunar:
  enabled: false

motion:
  enabled: false
```

## All Features Enabled (Maximum Capture)

```yaml
camera:
  rtsp_url: "rtsp://admin:password@192.168.1.205:554/stream"
  frame_width: 1920
  frame_height: 1080

storage:
  base_path: "/storage"

timelapse:
  enabled: true
  interval: 60
  quality: 95
  daily_video: true
  video_fps: 24

solargraph:
  enabled: true
  detection_interval: 30
  brightness_threshold: 200
  latitude: YOUR_LATITUDE
  longitude: YOUR_LONGITUDE
  daytime_only: true

lunar:
  enabled: true
  detection_interval: 60
  brightness_threshold: 150
  nighttime_only: true

motion:
  enabled: true
  sensitivity: 25
  min_area: 500
  burst_count: 10
  burst_fps: 10
  cooldown: 5

server:
  host: "0.0.0.0"
  port: 8080

advanced:
  max_frame_queue: 30
  jpeg_quality_live: 85
  log_level: "INFO"
```

## Performance Tips

### For Raspberry Pi or Low-Power Devices
```yaml
camera:
  frame_width: 1280
  frame_height: 720

timelapse:
  quality: 80

advanced:
  jpeg_quality_live: 75
  max_frame_queue: 10
```

### For High-Performance Servers
```yaml
camera:
  frame_width: 3840
  frame_height: 2160

timelapse:
  quality: 95

advanced:
  jpeg_quality_live: 90
  max_frame_queue: 60
```

## NAS Storage Setup

### SMB/CIFS (Windows Share)
```bash
# Mount NAS
sudo mkdir -p /mnt/nas/skywatch
sudo mount -t cifs //192.168.1.100/skywatch /mnt/nas/skywatch -o username=user,password=pass

# Then in config.yaml:
storage:
  base_path: "/mnt/nas/skywatch"
  nas_enabled: true
```

### NFS
```bash
# Mount NAS
sudo mkdir -p /mnt/nas/skywatch
sudo mount -t nfs 192.168.1.100:/export/skywatch /mnt/nas/skywatch

# Then in config.yaml:
storage:
  base_path: "/mnt/nas/skywatch"
  nas_enabled: true
```
