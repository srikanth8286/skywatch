#!/usr/bin/env python3
import cv2
import sys

# Try different URL formats
urls = [
    "rtsp://admin:osprey@1234@192.168.1.205:10554/tcp/av0_0",
    "rtsp://admin:osprey@1234@192.168.1.205:10554/av0_0",
    "rtsp://admin:osprey@1234@192.168.1.205:554/tcp/av0_0",
    "rtsp://admin:osprey@1234@192.168.1.205:554/av0_0",
    "rtsp://admin:osprey@1234@192.168.1.205:10554/stream1",
    "rtsp://admin:osprey@1234@192.168.1.205:10554/",
]

for url in urls:
    print(f"\nTrying: {url.replace('osprey@1234', '****')}")
    try:
        cap = cv2.VideoCapture(url)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret and frame is not None:
                print(f"✓ SUCCESS! Frame size: {frame.shape}")
                print(f"Working URL: {url.replace('osprey@1234', '****')}")
                cap.release()
                sys.exit(0)
            else:
                print("  Opened but no frames")
        else:
            print("  Failed to open")
        cap.release()
    except Exception as e:
        print(f"  Error: {e}")

print("\n✗ None of the URL formats worked")
sys.exit(1)
