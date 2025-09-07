"""
Raspberry Pi Camera Server for Football Tracking
Runs on each Raspberry Pi to control camera and communicate with main server
"""

from flask import Flask, request, jsonify
import threading
import time
import os
import cv2
import numpy as np
from picamera2 import Picamera2
from picamera2.encoders import H264Encoder
from picamera2.outputs import FileOutput
import requests
import json
from datetime import datetime
import subprocess
import signal
import sys
from pathlib import Path

# Import your existing tracking modules
from football_tracker import FootballTracker
from config import MODELS

app = Flask(__name__)


class CameraServer:
    def __init__(self):
        self.picam2 = None
        self.tracker = None
        self.recording = False
        self.current_session_id = None
        self.recording_path = None
        self.encoder = None
        self.output = None
        self.tracking_thread = None
        self.main_server_url = os.environ.get(
            "MAIN_SERVER_URL", "http://your-main-server.com"
        )
        self.camera_id = os.environ.get("CAMERA_ID", "default")

        # Initialize camera
        self.init_camera()

        # Register with main server
        self.register_with_server()

    def init_camera(self):
        """Initialize the Raspberry Pi camera"""
        try:
            self.picam2 = Picamera2()

            # Configure camera for both preview and recording
            config = self.picam2.create_video_configuration(
                main={"size": (1920, 1080), "format": "RGB888"},
                lores={"size": (640, 480), "format": "YUV420"},
            )
            self.picam2.configure(config)

            # Initialize tracker with IMX500 AI camera
            self.tracker = FootballTracker(
                model_name="yolo11n",  # Use the fastest model for real-time
                confidence_threshold=0.5,
                use_imx500=True,
            )

            print("Camera initialized successfully")

        except Exception as e:
            print(f"Failed to initialize camera: {e}")
            self.picam2 = None

    def register_with_server(self):
        """Register this camera with the main server"""
        try:
            response = requests.post(
                f"{self.main_server_url}/api/camera/register",
                json={
                    "camera_id": self.camera_id,
                    "ip_address": self.get_local_ip(),
                    "status": "online",
                    "capabilities": ["recording", "ai_tracking", "live_stream"],
                },
                timeout=10,
            )

            if response.status_code == 200:
                print("Successfully registered with main server")
            else:
                print(f"Failed to register: {response.text}")

        except Exception as e:
            print(f"Could not connect to main server: {e}")

    def get_local_ip(self):
        """Get local IP address"""
        import socket

        try:
            # Connect to a remote address to determine local IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"

    def start_recording(self, session_id, output_path=None):
        """Start recording with AI tracking"""
        if self.recording:
            return {"error": "Already recording"}

        if not self.picam2:
            return {"error": "Camera not initialized"}

        try:
            # Generate output path if not provided
            if not output_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = f"recordings/session_{session_id}_{timestamp}.mp4"

            # Ensure directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # Start camera
            self.picam2.start()

            # Set up H264 encoder for recording
            self.encoder = H264Encoder(bitrate=10000000)  # 10Mbps
            self.output = FileOutput(output_path)

            # Start recording
            self.picam2.start_encoder(self.encoder, self.output)

            # Start AI tracking in separate thread
            self.current_session_id = session_id
            self.recording_path = output_path
            self.recording = True

            self.tracking_thread = threading.Thread(target=self.run_tracking)
            self.tracking_thread.daemon = True
            self.tracking_thread.start()

            print(f"Started recording session {session_id} to {output_path}")

            return {
                "success": True,
                "session_id": session_id,
                "recording_path": output_path,
                "message": "Recording started with AI tracking",
            }

        except Exception as e:
            self.recording = False
            return {"error": f"Failed to start recording: {str(e)}"}

    def stop_recording(self):
        """Stop recording"""
        if not self.recording:
            return {"error": "Not currently recording"}

        try:
            # Stop recording
            self.recording = False

            if self.encoder and self.picam2:
                self.picam2.stop_encoder()
                self.picam2.stop()

            # Wait for tracking thread to finish
            if self.tracking_thread:
                self.tracking_thread.join(timeout=5)

            recording_path = self.recording_path
            session_id = self.current_session_id

            # Reset state
            self.current_session_id = None
            self.recording_path = None
            self.encoder = None
            self.output = None

            print(f"Stopped recording session {session_id}")

            # Notify main server that recording is complete
            self.notify_recording_complete(session_id, recording_path)

            return {
                "success": True,
                "session_id": session_id,
                "recording_path": recording_path,
                "message": "Recording stopped",
            }

        except Exception as e:
            return {"error": f"Failed to stop recording: {str(e)}"}

    def run_tracking(self):
        """Run AI tracking while recording"""
        try:
            frame_count = 0
            tracking_data = []

            while self.recording and self.picam2:
                # Capture frame for AI processing
                frame = self.picam2.capture_array("lores")

                if frame is not None:
                    # Convert YUV to RGB for processing
                    if len(frame.shape) == 3 and frame.shape[2] == 1:
                        # Convert YUV420 to RGB
                        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_YUV2RGB_I420)
                    else:
                        frame_rgb = frame

                    # Run AI detection and tracking
                    detections = self.tracker.process_frame(frame_rgb)

                    # Store tracking data with timestamp
                    timestamp = time.time()
                    tracking_data.append(
                        {
                            "frame": frame_count,
                            "timestamp": timestamp,
                            "detections": detections,
                        }
                    )

                    frame_count += 1

                    # Save tracking data every 100 frames
                    if frame_count % 100 == 0:
                        self.save_tracking_data(tracking_data[-100:])

                time.sleep(0.033)  # ~30 FPS processing

            # Save final tracking data
            if tracking_data:
                self.save_tracking_data(tracking_data)

        except Exception as e:
            print(f"Tracking error: {e}")

    def save_tracking_data(self, data):
        """Save tracking data to file"""
        if not self.current_session_id:
            return

        tracking_file = f"tracking_data/session_{self.current_session_id}_tracking.json"
        os.makedirs(os.path.dirname(tracking_file), exist_ok=True)

        # Append to existing file or create new
        existing_data = []
        if os.path.exists(tracking_file):
            try:
                with open(tracking_file, "r") as f:
                    existing_data = json.load(f)
            except:
                existing_data = []

        existing_data.extend(data)

        with open(tracking_file, "w") as f:
            json.dump(existing_data, f)

    def notify_recording_complete(self, session_id, recording_path):
        """Notify main server that recording is complete"""
        try:
            requests.post(
                f"{self.main_server_url}/api/camera/recording_complete",
                json={
                    "session_id": session_id,
                    "recording_path": recording_path,
                    "camera_id": self.camera_id,
                },
                timeout=10,
            )
        except Exception as e:
            print(f"Failed to notify server: {e}")

    def get_status(self):
        """Get current camera status"""
        return {
            "camera_id": self.camera_id,
            "status": "online" if self.picam2 else "error",
            "recording": self.recording,
            "current_session": self.current_session_id,
            "ai_tracking": True,
            "model": "yolo11n",
            "resolution": "1920x1080",
            "fps": 30,
        }

    def capture_screenshot(self):
        """Capture a screenshot"""
        if not self.picam2:
            return {"error": "Camera not initialized"}

        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_path = f"screenshots/screenshot_{timestamp}.jpg"
            os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)

            # Capture high-resolution image
            self.picam2.capture_file(screenshot_path)

            return {
                "success": True,
                "screenshot_path": screenshot_path,
                "timestamp": timestamp,
            }

        except Exception as e:
            return {"error": f"Failed to capture screenshot: {str(e)}"}


# Global camera server instance
camera_server = CameraServer()


# API Routes
@app.route("/api/status", methods=["GET"])
def get_status():
    """Get camera status"""
    return jsonify(camera_server.get_status())


@app.route("/api/start_recording", methods=["POST"])
def start_recording():
    """Start recording"""
    data = request.get_json() or {}
    session_id = data.get("session_id")
    output_path = data.get("output_path")

    if not session_id:
        return jsonify({"error": "session_id is required"}), 400

    result = camera_server.start_recording(session_id, output_path)

    if "error" in result:
        return jsonify(result), 500

    return jsonify(result)


@app.route("/api/stop_recording", methods=["POST"])
def stop_recording():
    """Stop recording"""
    result = camera_server.stop_recording()

    if "error" in result:
        return jsonify(result), 500

    return jsonify(result)


@app.route("/api/screenshot", methods=["POST"])
def capture_screenshot():
    """Capture screenshot"""
    result = camera_server.capture_screenshot()

    if "error" in result:
        return jsonify(result), 500

    return jsonify(result)


@app.route("/api/live_stream", methods=["GET"])
def live_stream():
    """Get live stream URL (for future implementation)"""
    return jsonify(
        {
            "stream_url": f"http://{camera_server.get_local_ip()}:8000/stream",
            "format": "mjpeg",
            "resolution": "640x480",
        }
    )


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})


def signal_handler(sig, frame):
    """Handle shutdown gracefully"""
    print("\nShutting down camera server...")

    if camera_server.recording:
        print("Stopping recording...")
        camera_server.stop_recording()

    if camera_server.picam2:
        try:
            camera_server.picam2.stop()
            camera_server.picam2.close()
        except:
            pass

    sys.exit(0)


if __name__ == "__main__":
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    print("Starting Football Tracking Camera Server...")
    print(f"Camera ID: {camera_server.camera_id}")
    print(f"Local IP: {camera_server.get_local_ip()}")

    # Create necessary directories
    os.makedirs("recordings", exist_ok=True)
    os.makedirs("screenshots", exist_ok=True)
    os.makedirs("tracking_data", exist_ok=True)

    # Start Flask server
    app.run(host="0.0.0.0", port=5000, debug=False)
