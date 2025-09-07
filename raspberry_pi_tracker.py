#!/usr/bin/env python3
"""
Raspberry Pi AI Camera Object Tracker
Optimized for Raspberry Pi 5 with IMX500 AI Camera

This setup leverages the IMX500's onboard AI processing capabilities,
minimizing CPU load on the Raspberry Pi 5 while providing real-time object tracking.
"""

import cv2
import numpy as np
import time
import logging
import argparse
from datetime import datetime
import threading
import json
import os

# Raspberry Pi specific imports
try:
    from picamera2 import Picamera2
    from libcamera import controls

    PICAMERA2_AVAILABLE = True
except ImportError:
    print(
        "❌ picamera2 not available. This script requires Raspberry Pi with picamera2."
    )
    print("Install with: sudo apt install -y python3-picamera2")
    exit(1)

from config import MODELS, CAMERA, RECORDING, OBJECT_CATEGORIES, CATEGORY_COLORS
from tracking import MultiObjectTracker


class RaspberryPiAIDetector:
    """
    AI detector optimized for Raspberry Pi 5 with IMX500 AI Camera
    All AI processing happens on the camera's dedicated neural processor
    """

    def __init__(self, model_name="yolo11n", enable_preview=True):
        """
        Initialize the Raspberry Pi AI detector

        Args:
            model_name: AI model to use ('yolo11n', 'yolov8n', etc.)
            enable_preview: Enable camera preview window
        """
        self.model_name = model_name
        self.enable_preview = enable_preview
        self.camera = None
        self.is_running = False
        self.frame_count = 0
        self.fps_start_time = time.time()

        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
        self.logger = logging.getLogger(__name__)

        # Initialize camera with AI model
        self._setup_ai_camera()
        self._load_ai_model()

    def _setup_ai_camera(self):
        """Setup Raspberry Pi camera with IMX500 AI capabilities"""
        try:
            self.camera = Picamera2()

            # Configure camera for optimal AI performance
            # The IMX500 processes AI inference directly on the camera
            config = self.camera.create_preview_configuration(
                main={"size": CAMERA["resolution"], "format": "RGB888"},
                lores={
                    "size": (640, 640),  # AI processing resolution
                    "format": "RGB888",
                },
                display="main" if self.enable_preview else None,
                controls={
                    "FrameRate": CAMERA["framerate"],
                    "ExposureTime": 10000,  # Auto-exposure for better detection
                    "AnalogueGain": 1.0,
                    "DigitalGain": 1.0,
                },
            )

            # Apply configuration
            self.camera.configure(config)
            self.logger.info(
                f"✅ Raspberry Pi camera configured: {CAMERA['resolution']}"
            )

            # Set camera controls for optimal AI performance
            self.camera.set_controls(
                {
                    "AfMode": controls.AfModeEnum.Auto,
                    "AeEnable": True,
                    "AwbEnable": True,
                }
            )

        except Exception as e:
            self.logger.error(f"❌ Failed to setup camera: {e}")
            raise

    def _load_ai_model(self):
        """Load AI model onto the IMX500 camera"""
        try:
            model_config = MODELS.get(self.model_name)
            if not model_config:
                raise ValueError(f"Model {self.model_name} not found in config")

            model_path = model_config["path"]

            # Check if model file exists
            if not os.path.exists(model_path):
                self.logger.error(f"❌ Model file not found: {model_path}")
                self.logger.info(
                    "📥 Download models using: https://github.com/raspberrypi/imx500-models"
                )
                raise FileNotFoundError(f"Model file not found: {model_path}")

            # Load model onto IMX500 camera
            self.camera.set_controls({"rpi.imx500.model_file": model_path})

            self.logger.info(f"✅ AI model loaded on IMX500: {model_path}")
            self.logger.info(
                f"🧠 AI processing will happen on camera's neural processor"
            )

        except Exception as e:
            self.logger.error(f"❌ Failed to load AI model: {e}")
            raise

    def start(self):
        """Start the camera and AI inference"""
        try:
            self.camera.start()
            self.is_running = True
            self.logger.info("🚀 Raspberry Pi AI camera started")
            self.logger.info("🧠 AI inference running on IMX500 neural processor")

        except Exception as e:
            self.logger.error(f"❌ Failed to start camera: {e}")
            raise

    def stop(self):
        """Stop the camera and AI inference"""
        if self.camera and self.is_running:
            self.camera.stop()
            self.is_running = False
            self.logger.info("⏹️ Raspberry Pi AI camera stopped")

    def get_ai_detections(self):
        """
        Get AI detection results from IMX500 camera
        This method has minimal CPU overhead as AI processing is done on camera
        """
        if not self.is_running:
            return None, []

        try:
            # Capture frame with AI inference results
            # The IMX500 automatically runs AI inference and returns results
            request = self.camera.capture_request()

            # Get the main frame
            frame = request.make_array("main")

            # Get AI inference results from camera metadata
            metadata = request.get_metadata()
            inference_results = metadata.get("rpi.imx500.results", {})

            # Release the request (important for memory management)
            request.release()

            # Process AI results into standard detection format
            detections = self._process_ai_results(inference_results, frame.shape)

            self.frame_count += 1

            return frame, detections

        except Exception as e:
            self.logger.error(f"❌ Error getting AI detections: {e}")
            return None, []

    def _process_ai_results(self, inference_results, frame_shape):
        """
        Process AI inference results from IMX500 into standard detection format

        Args:
            inference_results: Raw results from IMX500 AI inference
            frame_shape: Shape of the captured frame

        Returns:
            list: Processed detections in standard format
        """
        detections = []

        try:
            # Parse inference results based on model output format
            if "detections" in inference_results:
                raw_detections = inference_results["detections"]

                for detection in raw_detections:
                    # Extract detection data
                    class_id = int(detection.get("class_id", -1))
                    confidence = float(detection.get("confidence", 0.0))
                    bbox = detection.get("bbox", [0, 0, 0, 0])

                    # Filter by confidence threshold
                    model_config = MODELS[self.model_name]
                    if confidence < model_config["confidence_threshold"]:
                        continue

                    # Convert coordinates if needed
                    h, w = frame_shape[:2]
                    if model_config.get("bbox_normalization", False):
                        # Convert normalized coordinates to pixel coordinates
                        x1, y1, x2, y2 = bbox
                        x1, x2 = int(x1 * w), int(x2 * w)
                        y1, y2 = int(y1 * h), int(y2 * h)
                    else:
                        x1, y1, x2, y2 = [int(coord) for coord in bbox]

                    # Create detection object
                    det = {
                        "class_id": class_id,
                        "class_name": self._get_class_name(class_id),
                        "confidence": confidence,
                        "bbox": [x1, y1, x2, y2],
                        "center": [(x1 + x2) // 2, (y1 + y2) // 2],
                        "area": (x2 - x1) * (y2 - y1),
                    }

                    detections.append(det)

        except Exception as e:
            self.logger.error(f"❌ Error processing AI results: {e}")

        return detections

    def _get_class_name(self, class_id):
        """Get class name from class ID"""
        try:
            from config import COCO_CLASSES

            if 0 <= class_id < len(COCO_CLASSES):
                return COCO_CLASSES[class_id]
            return "unknown"
        except:
            return "unknown"

    def categorize_detections(self, detections):
        """Categorize detections by object type"""
        categorized = {}
        for category in OBJECT_CATEGORIES.keys():
            categorized[category] = []

        for detection in detections:
            class_id = detection["class_id"]

            # Find category
            object_category = "other"
            for category, class_ids in OBJECT_CATEGORIES.items():
                if class_id in class_ids:
                    object_category = category
                    break

            detection["category"] = object_category
            categorized[object_category].append(detection)

        return categorized

    def get_fps(self):
        """Calculate current FPS"""
        if self.frame_count == 0:
            return 0.0

        elapsed = time.time() - self.fps_start_time
        return self.frame_count / elapsed if elapsed > 0 else 0.0


class RaspberryPiTracker:
    """
    Complete object tracking application for Raspberry Pi 5 with IMX500 AI Camera
    Optimized for minimal CPU usage on Pi while leveraging camera's AI capabilities
    """

    def __init__(self, model_name="yolo11n", record_output=None, enable_preview=True):
        """
        Initialize Raspberry Pi tracker

        Args:
            model_name: AI model to use
            record_output: Video recording file path
            enable_preview: Show camera preview
        """
        self.model_name = model_name
        self.record_output = record_output
        self.enable_preview = enable_preview

        # Initialize components
        self.detector = RaspberryPiAIDetector(model_name, enable_preview)
        self.tracker = MultiObjectTracker()
        self.video_writer = None

        # State variables
        self.is_running = False
        self.frame_count = 0
        self.start_time = time.time()

        # Setup logging
        self.logger = logging.getLogger(__name__)

    def start(self):
        """Start the tracking application"""
        try:
            self.logger.info("🚀 Starting Raspberry Pi AI object tracker")
            self.logger.info(f"📷 Model: {self.model_name}")
            self.logger.info(f"🧠 AI processing: IMX500 neural processor")
            self.logger.info(f"💻 Pi CPU load: Minimal (tracking only)")

            # Start detector
            self.detector.start()
            self.is_running = True

            # Run main tracking loop
            self._main_loop()

        except KeyboardInterrupt:
            self.logger.info("⏹️ Interrupted by user")
        except Exception as e:
            self.logger.error(f"❌ Application error: {e}")
        finally:
            self.stop()

    def _main_loop(self):
        """Main tracking loop optimized for Raspberry Pi"""
        self.logger.info("🔄 Starting main tracking loop")

        while self.is_running:
            # Get frame and AI detections from camera
            frame, detections = self.detector.get_ai_detections()

            if frame is None:
                continue

            # Setup video writer on first frame
            if self.video_writer is None and self.record_output:
                self._setup_video_writer(frame.shape)

            # Categorize detections
            categorized_detections = self.detector.categorize_detections(detections)

            # Update tracking (minimal CPU load)
            tracking_results = self.tracker.update(categorized_detections)

            # Draw tracking information
            frame_with_tracking = self.tracker.draw_tracking_info(
                frame, tracking_results
            )

            # Add performance overlay
            self._draw_performance_overlay(frame_with_tracking)

            # Record frame if enabled
            if self.video_writer:
                self.video_writer.write(frame_with_tracking)

            # Display frame (if preview enabled)
            if self.enable_preview:
                cv2.imshow("Raspberry Pi AI Object Tracker", frame_with_tracking)

                # Handle keyboard input
                key = cv2.waitKey(1) & 0xFF
                if key == ord("q"):
                    break
                elif key == ord("r"):
                    self.tracker.reset()
                    self.logger.info("🔄 Tracking reset")
                elif key == ord("s"):
                    self._save_screenshot(frame_with_tracking)

            self.frame_count += 1

            # Log performance every 100 frames
            if self.frame_count % 100 == 0:
                fps = self.detector.get_fps()
                self.logger.info(f"📊 FPS: {fps:.1f}, Objects: {len(detections)}")

        if self.enable_preview:
            cv2.destroyAllWindows()

    def _setup_video_writer(self, frame_shape):
        """Setup video recording"""
        try:
            h, w = frame_shape[:2]
            fourcc = cv2.VideoWriter_fourcc(*RECORDING["codec"])
            self.video_writer = cv2.VideoWriter(
                self.record_output, fourcc, RECORDING["fps"], (w, h)
            )
            self.logger.info(f"📹 Recording to: {self.record_output}")
        except Exception as e:
            self.logger.error(f"❌ Failed to setup recording: {e}")

    def _draw_performance_overlay(self, frame):
        """Draw performance information overlay"""
        # FPS and model info
        fps = self.detector.get_fps()
        cv2.putText(
            frame,
            f"FPS: {fps:.1f}",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2,
        )
        cv2.putText(
            frame,
            f"Model: {self.model_name}",
            (10, 60),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 255, 255),
            1,
        )
        cv2.putText(
            frame,
            "AI: IMX500",
            (10, 80),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 255, 255),
            1,
        )

    def _save_screenshot(self, frame):
        """Save screenshot with timestamp"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"pi_tracking_{timestamp}.jpg"
        cv2.imwrite(filename, frame)
        self.logger.info(f"📸 Screenshot saved: {filename}")

    def stop(self):
        """Stop the tracking application"""
        self.logger.info("⏹️ Stopping Raspberry Pi tracker")
        self.is_running = False

        if self.detector:
            self.detector.stop()

        if self.video_writer:
            self.video_writer.release()
            self.logger.info("📹 Recording saved")

        # Final statistics
        if self.frame_count > 0:
            elapsed = time.time() - self.start_time
            avg_fps = self.frame_count / elapsed
            self.logger.info(
                f"📊 Final stats: {self.frame_count} frames, {avg_fps:.2f} FPS"
            )


def main():
    """Main entry point for Raspberry Pi AI tracker"""
    parser = argparse.ArgumentParser(
        description="Raspberry Pi AI Object Tracker - Optimized for IMX500"
    )

    parser.add_argument(
        "--model",
        choices=list(MODELS.keys()),
        default="yolo11n",
        help="AI model to use for detection",
    )
    parser.add_argument("--record", type=str, help="Output video file for recording")
    parser.add_argument(
        "--no-preview",
        action="store_true",
        help="Disable camera preview (for headless operation)",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )

    args = parser.parse_args()

    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Create and start tracker
    tracker = RaspberryPiTracker(
        model_name=args.model,
        record_output=args.record,
        enable_preview=not args.no_preview,
    )

    try:
        tracker.start()
    except Exception as e:
        logging.error(f"❌ Tracker failed: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
