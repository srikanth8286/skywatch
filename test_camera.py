#!/usr/bin/env python3
import cv2
import sys

url = "rtsp://admin:osprey%401234@192.168.1.205:10554/tcp/av0_0"
print(f"Testing camera connection to: {url}")
print("This may take up to 30 seconds...")

cap = cv2.VideoCapture(url)

if cap.isOpened():
    print("✓ Camera opened successfully")
    ret, frame = cap.read()
    if ret and frame is not None:
        print(f"✓ Frame read successfully - size: {frame.shape}")
        print("✓ Camera is working!")
    else:
        print("✗ Camera opened but cannot read frames")
        sys.exit(1)
    cap.release()
else:
    print("✗ Failed to open camera")
    sys.exit(1)
