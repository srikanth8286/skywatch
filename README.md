# 🌤️ SkyWatch

**Smart Camera Capture System for Timelapses, Solargraphs, Lunar Tracking, and Motion Detection**

SkyWatch is a powerful, open-source web application that transforms your RTSP camera into an intelligent capture system. Perfect for astronomical photography, wildlife monitoring, and long-term environmental observation.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)

## ✨ Features

### 🎥 Live View
- Real-time MJPEG stream from your RTSP camera
- Accessible from any device on your network
- Take instant snapshots

### ⏱️ Timelapse Capture
- Automatic capture at configurable intervals (default: 1 frame/minute)
- Daily organization of captured frames
- Date range playback with adjustable speed (1x - 60x)
- Automatic daily video compilation

### ☀️ Solargraph
- Intelligent sun detection and tracking
- Automatic exposure compensation
- Composite image generation showing sun's path across the sky
- Daylight-only operation with sunrise/sunset awareness
- Perfect for creating stunning solargraph images

### 🌙 Lunar Tracking
- Moon position detection and tracking
- Nighttime composite generation
- Captures the moon's journey across the night sky

### 🐦 Motion Detection
- Real-time motion detection
- Burst capture mode (captures multiple frames when motion detected)
- Perfect for wildlife photography (hummingbirds, birds, etc.)
- Configurable sensitivity and cooldown periods
- Separate storage for each motion event

### 🎨 Advanced Features
- Multiple concurrent capture modes (all can run simultaneously)
- NAS storage support
- Responsive web interface (mobile & desktop)
- Real-time statistics and monitoring
- RESTful API for custom integrations
- Docker support for easy deployment

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- RTSP camera or stream
- Linux/macOS/Windows

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/srikanth8286/skywatch.git
   cd skywatch
   ```

2. **Run the installation script:**
   ```bash
   chmod +x install.sh
   ./install.sh
   ```

3. **Configure your camera:**
   Edit `config.local.yaml` with your camera's RTSP URL:
   ```yaml
   camera:
     rtsp_url: "rtsp://username:password@camera-ip:port/stream"
   ```

4. **Set your location (for solargraph):**
   ```yaml
   solargraph:
     latitude: 40.7128   # Your latitude
     longitude: -74.0060 # Your longitude
   ```

5. **Start SkyWatch:**
   ```bash
   ./start.sh
   ```

6. **Access the web interface:**
   Open your browser to `http://localhost:8080`

## 🐳 Docker Deployment

For easier deployment, use Docker:

```bash
# Build and run with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

## 📁 Project Structure

```
skywatch/
├── app/
│   ├── __init__.py
│   ├── api.py              # FastAPI routes
│   ├── camera.py           # RTSP stream handler
│   ├── config.py           # Configuration management
│   ├── services/
│   │   ├── timelapse.py    # Timelapse capture
│   │   ├── solargraph.py   # Sun tracking
│   │   ├── lunar.py        # Moon tracking
│   │   └── motion.py       # Motion detection
│   └── static/
│       ├── index.html      # Web interface
│       ├── styles.css      # Styling
│       └── script.js       # Frontend logic
├── storage/                # Captured images (auto-created)
│   ├── timelapse/
│   ├── solargraph/
│   ├── lunar/
│   └── motion/
├── config.yaml             # Default configuration
├── main.py                 # Application entry point
├── requirements.txt        # Python dependencies
├── Dockerfile
├── docker-compose.yml
└── README.md
```

## ⚙️ Configuration

SkyWatch is highly configurable. Edit `config.yaml` or create `config.local.yaml`:

### Camera Settings
```yaml
camera:
  rtsp_url: "rtsp://admin:password@192.168.1.100:554/stream"
  reconnect_interval: 5
  frame_width: 1920
  frame_height: 1080
```

### Timelapse Settings
```yaml
timelapse:
  enabled: true
  interval: 60          # seconds between captures
  quality: 90           # JPEG quality (1-100)
  daily_video: true     # Compile daily videos
  video_fps: 24         # Video framerate
```

### Solargraph Settings
```yaml
solargraph:
  enabled: true
  detection_interval: 30        # seconds between detection attempts
  brightness_threshold: 200     # 0-255
  daytime_only: true
  latitude: 40.7128
  longitude: -74.0060
```

### Motion Detection Settings
```yaml
motion:
  enabled: true
  sensitivity: 25       # 0-100 (lower = more sensitive)
  min_area: 500        # minimum motion area in pixels
  burst_count: 10      # frames to capture
  burst_fps: 10        # capture rate
  cooldown: 5          # seconds before next detection
```

### Storage Settings
```yaml
storage:
  base_path: "/storage"
  nas_enabled: false
  nas_path: "//nas-ip/skywatch"  # For NAS storage
```

## 🖥️ Web Interface

### Live View Tab
- Real-time camera feed
- Take instant snapshots

### Timelapse Tab
- Select date range
- Adjust playback speed
- View compiled timelapses

### Solargraph Tab
- View sun trail composite
- Real-time updates as sun is detected

### Lunar Tab
- View moon trail composite
- Track lunar path across nights

### Motion Tab
- Browse motion detection events
- View captured bursts
- Click to see full-resolution images

### Status Tab
- System health monitoring
- Capture statistics
- Service status

## 🔌 API Endpoints

SkyWatch provides a RESTful API:

- `GET /api/status` - System status and statistics
- `GET /api/stream` - Live MJPEG stream
- `GET /api/snapshot` - Current frame as JPEG
- `GET /api/timelapse/dates` - Available timelapse dates
- `GET /api/timelapse/frames/{date}` - Frames for specific date
- `GET /api/timelapse/play/{date}?speed=24` - Playback timelapse
- `GET /api/solargraph/composite` - Solargraph composite image
- `GET /api/lunar/composite` - Lunar composite image
- `GET /api/motion/events` - Recent motion events
- `GET /api/storage/{path}` - Access stored files

## 🛠️ System Service (Linux)

To run SkyWatch as a system service:

1. Edit `skywatch.service` with your paths and username
2. Copy to systemd:
   ```bash
   sudo cp skywatch.service /etc/systemd/system/
   ```
3. Enable and start:
   ```bash
   sudo systemctl enable skywatch
   sudo systemctl start skywatch
   ```
4. Check status:
   ```bash
   sudo systemctl status skywatch
   ```

## 📊 Storage Requirements

Approximate storage usage:
- **Timelapse** (1 frame/min, 1920x1080): ~2GB/day
- **Solargraph** (raw captures): ~100MB/day
- **Lunar** (raw captures): ~50MB/day
- **Motion** (per event): ~5-20MB

## 🎯 Use Cases

### Astronomical Photography
- Create stunning solargraphs showing the sun's path
- Track lunar phases and movements
- Long-term sky observation

### Wildlife Monitoring
- Capture hummingbirds at feeders
- Monitor bird behavior
- Wildlife activity tracking

### Environmental Observation
- Weather pattern documentation
- Plant growth timelapses
- Seasonal changes

### Security & Monitoring
- Motion-activated recording
- Long-term property monitoring
- Event detection and logging

## 🤝 Contributing

Contributions are welcome! Please feel free to submit pull requests.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- Computer vision powered by [OpenCV](https://opencv.org/)
- Astronomical calculations using [Astral](https://astral.readthedocs.io/)

## 💬 Support

For issues, questions, or suggestions, please open an issue on GitHub.

## 🗺️ Roadmap

- [ ] AI-powered object classification
- [ ] Multi-camera support
- [ ] Cloud storage integration
- [ ] Mobile app
- [ ] Advanced video compilation options
- [ ] Weather overlay integration
- [ ] Email/notification alerts
- [ ] Time-lapse video effects

---

Made with ❤️ for astronomy, photography, and nature enthusiasts
