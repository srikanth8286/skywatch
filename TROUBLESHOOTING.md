# Troubleshooting Guide

Common issues and solutions for SkyWatch.

## Camera Connection Issues

### Problem: "Camera not available" or "No frame available"

**Solutions:**
1. Verify RTSP URL is correct:
   ```bash
   # Test with VLC or ffmpeg
   ffplay rtsp://admin:password@192.168.1.205:554/stream
   # or
   ffmpeg -i rtsp://admin:password@192.168.1.205:554/stream -frames:v 1 test.jpg
   ```

2. Check network connectivity:
   ```bash
   ping 192.168.1.205
   ```

3. Verify camera credentials and port

4. Check firewall settings:
   ```bash
   sudo ufw allow 554
   sudo ufw allow 8080
   ```

5. Try different RTSP paths (common variations):
   - `/tcp/av0_0`
   - `/stream`
   - `/live`
   - `/ch0`
   - `/Streaming/Channels/101`

### Problem: Stream keeps disconnecting

**Solutions:**
1. Increase `reconnect_interval` in config.yaml
2. Check camera's maximum connection limit
3. Reduce frame resolution:
   ```yaml
   camera:
     frame_width: 1280
     frame_height: 720
   ```
4. Check network stability

## Installation Issues

### Problem: `pip install` fails for opencv-python

**Solutions:**
1. Install system dependencies first:
   ```bash
   # Ubuntu/Debian
   sudo apt-get update
   sudo apt-get install python3-opencv libgl1-mesa-glx libglib2.0-0
   
   # macOS
   brew install opencv
   ```

2. Try opencv-python-headless:
   ```bash
   pip uninstall opencv-python
   pip install opencv-python-headless
   ```

### Problem: Permission denied on storage directory

**Solutions:**
```bash
# Make storage directory writable
chmod 755 storage
# or run with sudo (not recommended)
# or change base_path to user directory in config.yaml
```

## Web Interface Issues

### Problem: Cannot access web interface

**Solutions:**
1. Check if server is running:
   ```bash
   ps aux | grep python.*main.py
   ```

2. Verify port is not in use:
   ```bash
   netstat -tuln | grep 8080
   # or
   sudo lsof -i :8080
   ```

3. Check firewall:
   ```bash
   sudo ufw allow 8080
   ```

4. Try accessing from localhost first:
   ```
   http://localhost:8080
   ```

5. Check server logs for errors

### Problem: Live stream not loading

**Solutions:**
1. Check browser console for errors (F12)
2. Verify camera is connected (check Status tab)
3. Try different browser
4. Disable browser extensions
5. Check CORS settings in config if accessing from different domain

## Performance Issues

### Problem: High CPU usage

**Solutions:**
1. Reduce frame resolution
2. Disable unused services:
   ```yaml
   motion:
     enabled: false
   solargraph:
     enabled: false
   ```
3. Increase capture intervals
4. Lower JPEG quality:
   ```yaml
   advanced:
     jpeg_quality_live: 75
   ```

### Problem: Storage filling up quickly

**Solutions:**
1. Reduce capture frequency
2. Lower JPEG quality
3. Setup automatic cleanup script:
   ```bash
   # Delete timelapse frames older than 30 days
   find storage/timelapse -type f -mtime +30 -delete
   ```
4. Enable daily video compilation and delete frames:
   ```yaml
   timelapse:
     daily_video: true
   ```

## Solargraph Issues

### Problem: Sun not being detected

**Solutions:**
1. Lower brightness threshold:
   ```yaml
   solargraph:
     brightness_threshold: 150
   ```

2. Adjust detection radius:
   ```yaml
   solargraph:
     min_radius: 5
     max_radius: 150
   ```

3. Check camera is aimed at sky
4. Verify daytime_only is configured correctly
5. Set correct latitude/longitude

### Problem: False sun detections

**Solutions:**
1. Increase brightness threshold:
   ```yaml
   solargraph:
     brightness_threshold: 220
   ```
2. Narrow radius range
3. Check for reflections or bright objects in frame

## Motion Detection Issues

### Problem: Too many false detections

**Solutions:**
1. Reduce sensitivity:
   ```yaml
   motion:
     sensitivity: 40  # Higher = less sensitive
   ```

2. Increase minimum area:
   ```yaml
   motion:
     min_area: 1000
   ```

3. Increase cooldown:
   ```yaml
   motion:
     cooldown: 10
   ```

### Problem: Missing detections

**Solutions:**
1. Increase sensitivity:
   ```yaml
   motion:
     sensitivity: 15
   ```

2. Decrease minimum area:
   ```yaml
   motion:
     min_area: 200
   ```

3. Ensure good contrast and lighting

## Docker Issues

### Problem: Container fails to start

**Solutions:**
1. Check logs:
   ```bash
   docker-compose logs skywatch
   ```

2. Verify config.yaml exists and is valid

3. Check volume mounts:
   ```bash
   docker-compose down
   docker-compose up
   ```

4. Rebuild container:
   ```bash
   docker-compose build --no-cache
   docker-compose up
   ```

### Problem: Cannot access camera from Docker

**Solutions:**
1. Use host network mode:
   ```yaml
   # In docker-compose.yml
   network_mode: "host"
   ```

2. Or specify camera IP directly (not localhost)

## System Service Issues

### Problem: Service fails to start

**Solutions:**
1. Check service status:
   ```bash
   sudo systemctl status skywatch
   journalctl -u skywatch -n 50
   ```

2. Verify paths in skywatch.service are correct
3. Check permissions
4. Ensure virtual environment is properly set up

## Log Analysis

Enable debug logging for more information:
```yaml
advanced:
  log_level: "DEBUG"
```

View logs:
```bash
# If running directly
python main.py

# If running as service
sudo journalctl -u skywatch -f

# If using Docker
docker-compose logs -f
```

## Still Having Issues?

1. Check GitHub issues: https://github.com/srikanth8286/skywatch/issues
2. Open a new issue with:
   - Detailed description
   - Steps to reproduce
   - Logs (with sensitive info removed)
   - System information (OS, Python version, camera model)
   - Configuration (with credentials removed)

## Getting Help

- GitHub Issues: For bugs and feature requests
- GitHub Discussions: For questions and community help
- Include log output and system info when asking for help
