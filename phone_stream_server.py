#!/usr/bin/env python3
"""
Phone Stream Server - Use phone's processing power for object detection
"""

import socket
import threading
import cv2
import numpy as np
import json
import base64
from flask import Flask, request, jsonify
import logging

# Disable Flask logs for cleaner output
log = logging.getLogger("werkzeug")
log.setLevel(logging.ERROR)

app = Flask(__name__)


class PhoneStreamServer:
    """Server to receive detection results from phone"""

    def __init__(self, port=5000):
        self.port = port
        self.latest_detections = []
        self.latest_frame = None
        self.frame_count = 0

    def start_server(self):
        """Start the Flask server"""
        print(f"📱 Starting phone stream server on port {self.port}")
        print("📋 Phone Setup Instructions:")
        print("   1. Install 'IP Webcam' or similar app on your phone")
        print("   2. Connect phone to same WiFi as laptop")
        print("   3. Start IP camera on phone")
        print("   4. Note the phone's IP address")
        print("   5. Run: python phone_client.py --phone-ip YOUR_PHONE_IP")
        print()
        app.run(host="0.0.0.0", port=self.port, debug=False)

    @app.route("/detections", methods=["POST"])
    def receive_detections():
        """Receive detection results from phone"""
        try:
            data = request.json
            self.latest_detections = data.get("detections", [])
            self.frame_count += 1

            if self.frame_count % 30 == 0:
                print(
                    f"📱 Received {len(self.latest_detections)} detections from phone"
                )

            return jsonify({"status": "success"})
        except Exception as e:
            print(f"Error receiving detections: {e}")
            return jsonify({"status": "error", "message": str(e)})

    @app.route("/frame", methods=["POST"])
    def receive_frame():
        """Receive processed frame from phone"""
        try:
            data = request.json
            frame_data = data.get("frame", "")

            # Decode base64 frame
            frame_bytes = base64.b64decode(frame_data)
            frame_array = np.frombuffer(frame_bytes, dtype=np.uint8)
            self.latest_frame = cv2.imdecode(frame_array, cv2.IMREAD_COLOR)

            return jsonify({"status": "success"})
        except Exception as e:
            print(f"Error receiving frame: {e}")
            return jsonify({"status": "error", "message": str(e)})

    def get_latest_detections(self):
        """Get latest detections from phone"""
        return self.latest_detections

    def get_latest_frame(self):
        """Get latest processed frame from phone"""
        return self.latest_frame


class PhoneDetector:
    """Detector that uses phone processing"""

    def __init__(self, phone_ip, phone_port=8080):
        self.phone_ip = phone_ip
        self.phone_port = phone_port
        self.server = PhoneStreamServer()
        self.cap = None

        # Start server in background
        server_thread = threading.Thread(target=self.server.start_server)
        server_thread.daemon = True
        server_thread.start()

        print(f"📱 Connecting to phone at {phone_ip}:{phone_port}")
        self._setup_phone_stream()

    def _setup_phone_stream(self):
        """Setup connection to phone camera stream"""
        try:
            # Common IP webcam URLs
            possible_urls = [
                f"http://{self.phone_ip}:{self.phone_port}/video",
                f"http://{self.phone_ip}:{self.phone_port}/videofeed",
                f"http://{self.phone_ip}:{self.phone_port}/cam/1/stream",
            ]

            for url in possible_urls:
                print(f"Trying: {url}")
                cap = cv2.VideoCapture(url)
                if cap.isOpened():
                    self.cap = cap
                    print(f"✅ Connected to phone camera: {url}")
                    return

            print("❌ Could not connect to phone camera")
            print("Make sure IP Webcam app is running on your phone")

        except Exception as e:
            print(f"Error connecting to phone: {e}")

    def get_frame(self):
        """Get frame from phone camera"""
        if self.cap is None:
            return None

        ret, frame = self.cap.read()
        if ret:
            return frame
        return None

    def detect_objects(self, frame):
        """Get detection results from phone processing"""
        return self.server.get_latest_detections()

    def categorize_objects(self, detections):
        """Categorize detections (same as regular detector)"""
        from detection import OfflineDetector

        dummy_detector = OfflineDetector()
        return dummy_detector.categorize_objects(detections)


def create_phone_client_script():
    """Create a Python script for phone-side processing"""
    phone_script = '''#!/usr/bin/env python3
"""
Phone Client - Run object detection on phone and send results to laptop
Install on phone using Termux or similar Python environment
"""

import cv2
import requests
import json
import base64
import time
import argparse
from ultralytics import YOLO

class PhoneClient:
    def __init__(self, laptop_ip, phone_camera_url="0"):
        self.laptop_ip = laptop_ip
        self.laptop_url = f"http://{laptop_ip}:5000"
        self.phone_camera_url = phone_camera_url
        
        # Load lightweight YOLO model
        print("📱 Loading YOLO model on phone...")
        self.model = YOLO("yolo11n.pt")  # Download if needed
        
        # Setup camera
        if phone_camera_url == "0":
            self.cap = cv2.VideoCapture(0)  # Phone camera
        else:
            self.cap = cv2.VideoCapture(phone_camera_url)
        
        print(f"📱 Phone client ready, sending to {self.laptop_url}")
    
    def run(self):
        """Run detection and streaming"""
        frame_count = 0
        
        while True:
            ret, frame = self.cap.read()
            if not ret:
                continue
                
            frame_count += 1
            
            # Run detection on phone
            results = self.model.predict(frame, verbose=False, imgsz=320)
            
            # Convert results to standard format
            detections = []
            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for box in boxes:
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        conf = box.conf[0].cpu().numpy()
                        cls = int(box.cls[0].cpu().numpy())
                        
                        if conf > 0.3:
                            detections.append({
                                "class_id": cls,
                                "confidence": float(conf),
                                "bbox": [int(x1), int(y1), int(x2), int(y2)],
                                "center": [int((x1+x2)/2), int((y1+y2)/2)],
                                "area": int((x2-x1)*(y2-y1))
                            })
            
            # Send detections to laptop
            try:
                response = requests.post(
                    f"{self.laptop_url}/detections",
                    json={"detections": detections},
                    timeout=0.1
                )
            except:
                pass  # Continue even if laptop connection fails
            
            # Send frame every 10 frames
            if frame_count % 10 == 0:
                try:
                    _, buffer = cv2.imencode('.jpg', frame)
                    frame_b64 = base64.b64encode(buffer).decode()
                    
                    requests.post(
                        f"{self.laptop_url}/frame",
                        json={"frame": frame_b64},
                        timeout=0.1
                    )
                except:
                    pass
            
            # FPS control
            time.sleep(0.01)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--laptop-ip", required=True, help="Laptop IP address")
    parser.add_argument("--camera", default="0", help="Phone camera (0 for default)")
    args = parser.parse_args()
    
    client = PhoneClient(args.laptop_ip, args.camera)
    client.run()
'''

    with open("phone_client.py", "w") as f:
        f.write(phone_script)

    print("📱 Created phone_client.py")
    print("📋 Setup instructions:")
    print("   1. Install Termux on Android or similar Python app")
    print("   2. Install: pip install ultralytics opencv-python requests")
    print("   3. Copy phone_client.py to your phone")
    print("   4. Find your laptop IP: ipconfig (Windows) or ifconfig (Linux)")
    print("   5. Run on phone: python phone_client.py --laptop-ip YOUR_LAPTOP_IP")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--create-client", action="store_true", help="Create phone client script"
    )
    parser.add_argument("--phone-ip", help="Phone IP address for direct connection")

    args = parser.parse_args()

    if args.create_client:
        create_phone_client_script()
    elif args.phone_ip:
        # Test phone detector
        detector = PhoneDetector(args.phone_ip)

        print("📱 Testing phone detection...")
        while True:
            frame = detector.get_frame()
            if frame is not None:
                detections = detector.detect_objects(frame)

                # Draw detections
                for det in detections:
                    bbox = det["bbox"]
                    cv2.rectangle(
                        frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), (0, 255, 0), 2
                    )

                cv2.imshow("Phone Detection", frame)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break

        cv2.destroyAllWindows()
    else:
        # Start server only
        server = PhoneStreamServer()
        server.start_server()
