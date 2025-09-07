"""
Main Football Tracking Application
Real-time football player and ball tracking using Raspberry Pi AI Camera (IMX500)
"""

import cv2
import numpy as np
import argparse
import time
import logging
from datetime import datetime
import os

from detection import FootballDetector, OfflineDetector
from tracking import MultiObjectTracker
from config import CAMERA, RECORDING, MODELS, OBJECT_CATEGORIES


class ObjectTrackingApp:
    """
    Main application class for multi-object tracking
    """

    def __init__(
        self,
        model_name="yolo11n",
        use_offline=False,
        record_output=None,
        demo_mode=False,
        camera_index=None,
        fast_mode=False,
        phone_display=False,
    ):
        """
        Initialize the object tracking application

        Args:
            model_name (str): AI model to use ('yolo11n' or 'yolov8n')
            use_offline (bool): Use offline detector for testing
            record_output (str): Output file path for recording
            demo_mode (bool): Enable demo mode with mock objects
            camera_index (int): Camera index to use
            fast_mode (bool): Enable fast mode optimizations for higher FPS
        """
        self.model_name = model_name
        self.use_offline = use_offline
        self.record_output = record_output
        self.demo_mode = demo_mode
        self.camera_index = camera_index
        self.fast_mode = fast_mode
        self.phone_display = phone_display

        # Initialize components
        self.detector = None
        self.tracker = MultiObjectTracker()
        self.video_writer = None
        self.phone_server = None

        # FPS optimization variables
        self.frame_skip_counter = 0
        self.frame_skip_rate = 2 if fast_mode else 1  # Process every Nth frame
        self.last_detections = []

        # State variables
        self.is_running = False
        self.is_recording = False
        self.frame_count = 0
        self.fps_counter = 0
        self.fps_start_time = time.time()
        self.current_fps = 0

        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
        self.logger = logging.getLogger(__name__)

        if self.fast_mode:
            self.logger.info("🚀 Fast mode enabled - optimizing for maximum FPS")

        if self.phone_display:
            self.logger.info("📱 Phone display enabled - starting display server")
            self._initialize_phone_display()

        self._initialize_detector()

    def _initialize_phone_display(self):
        """Initialize phone display server"""
        try:
            from phone_display_app import PhoneDisplayServer
            import threading
            import socket

            self.phone_server = PhoneDisplayServer()

            # Start server in background thread
            def start_server():
                from phone_display_app import app

                # Get local IP
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                try:
                    s.connect(("8.8.8.8", 80))
                    local_ip = s.getsockname()[0]
                    print(f"📱 Phone Display URL: http://{local_ip}:5001")
                    print("📱 Open this URL on your phone browser")
                except:
                    print("📱 Phone display starting on port 5001")
                finally:
                    s.close()

                app.run(host="0.0.0.0", port=5001, debug=False, use_reloader=False)

            server_thread = threading.Thread(target=start_server)
            server_thread.daemon = True
            server_thread.start()

        except Exception as e:
            self.logger.error(f"Failed to initialize phone display: {e}")
            self.phone_server = None

    def _initialize_detector(self):
        """Initialize the appropriate detector"""
        try:
            if self.use_offline:
                self.logger.info("Initializing offline detector for testing")
                self.detector = OfflineDetector(camera_index=self.camera_index)

                # Enable demo mode if requested
                if hasattr(self, "demo_mode") and self.demo_mode:
                    self.detector.enable_demo_mode()
                    self.logger.info("Demo mode enabled - showing mock objects")
            else:
                self.logger.info(f"Initializing IMX500 detector with {self.model_name}")
                self.detector = FootballDetector(self.model_name)

        except Exception as e:
            self.logger.error(f"Failed to initialize detector: {e}")
            self.logger.info("Falling back to offline detector")
            self.detector = OfflineDetector()
            self.use_offline = True

    def _setup_video_writer(self, frame_shape):
        """Setup video writer for recording"""
        if not self.record_output:
            return

        try:
            height, width = frame_shape[:2]
            fourcc = cv2.VideoWriter_fourcc(*RECORDING["codec"])

            self.video_writer = cv2.VideoWriter(
                self.record_output, fourcc, RECORDING["fps"], (width, height)
            )

            self.is_recording = True
            self.logger.info(f"Started recording to {self.record_output}")

        except Exception as e:
            self.logger.error(f"Failed to setup video writer: {e}")

    def _calculate_fps(self):
        """Calculate current FPS"""
        self.fps_counter += 1

        if self.fps_counter >= 30:  # Update FPS every 30 frames
            current_time = time.time()
            self.current_fps = self.fps_counter / (current_time - self.fps_start_time)
            self.fps_counter = 0
            self.fps_start_time = current_time

    def _draw_ui_overlay(self, frame):
        """Draw UI overlay with controls and information"""
        height, width = frame.shape[:2]

        # Create semi-transparent overlay
        overlay = frame.copy()

        # Top bar
        cv2.rectangle(overlay, (0, 0), (width, 60), (0, 0, 0), -1)

        # Bottom bar for controls
        cv2.rectangle(overlay, (0, height - 60), (width, height), (0, 0, 0), -1)

        # Blend overlay
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)

        # Top bar text
        title = f"Object Tracker - Model: {self.model_name.upper()}"
        if self.use_offline:
            title += " (OFFLINE MODE)"

        cv2.putText(
            frame, title, (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2
        )
        cv2.putText(
            frame,
            f"FPS: {self.current_fps:.1f}",
            (width - 120, 25),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            2,
        )

        # Recording indicator
        if self.is_recording:
            cv2.circle(frame, (width - 30, 35), 8, (0, 0, 255), -1)
            cv2.putText(
                frame,
                "REC",
                (width - 60, 25),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 0, 255),
                2,
            )

        # Bottom bar controls
        controls_text = "Controls: Q-Quit | R-Reset Tracking | S-Screenshot"
        if self.record_output:
            controls_text += " | Recording Enabled"

        cv2.putText(
            frame,
            controls_text,
            (10, height - 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 255, 255),
            1,
        )

    def _save_screenshot(self, frame):
        """Save current frame as screenshot"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"object_tracking_screenshot_{timestamp}.jpg"

        try:
            cv2.imwrite(filename, frame)
            self.logger.info(f"Screenshot saved: {filename}")
        except Exception as e:
            self.logger.error(f"Failed to save screenshot: {e}")

    def start(self):
        """Start the object tracking application"""
        self.logger.info("Starting object tracking application")

        try:
            # Start detector
            if not self.use_offline:
                self.detector.start()

            self.is_running = True
            self.fps_start_time = time.time()

            # Main loop
            self._main_loop()

        except KeyboardInterrupt:
            self.logger.info("Application interrupted by user")
        except Exception as e:
            self.logger.error(f"Application error: {e}")
        finally:
            self.stop()

    def _main_loop(self):
        """Main processing loop"""
        # Create window
        cv2.namedWindow("Object Tracker", cv2.WINDOW_AUTOSIZE)

        while self.is_running:
            start_time = time.time()

            # Get frame and detections with optional frame skipping
            if self.use_offline:
                # For offline mode, detector handles frame acquisition
                frame = self.detector.get_frame()

                # Frame skipping optimization for fast mode
                self.frame_skip_counter += 1
                should_process = (self.frame_skip_counter % self.frame_skip_rate) == 0

                if should_process:
                    # Get detections - either real or demo
                    if self.demo_mode and hasattr(self.detector, "get_demo_detections"):
                        detections = self.detector.get_demo_detections(frame)
                    else:
                        detections = self.detector.detect_objects(frame)

                    # Cache detections for skipped frames
                    self.last_detections = detections
                else:
                    # Use cached detections for skipped frames
                    detections = self.last_detections
            else:
                frame, detections = self.detector.get_detections()

            if frame is None:
                continue

            # Setup video writer on first frame
            if self.video_writer is None and self.record_output:
                self._setup_video_writer(frame.shape)

            # Categorize detections by object type
            if hasattr(self.detector, "categorize_objects"):
                categorized_detections = self.detector.categorize_objects(detections)
            else:
                # Manual categorization for offline detector
                categorized_detections = {}
                for category in OBJECT_CATEGORIES.keys():
                    categorized_detections[category] = []

                for det in detections:
                    class_id = det["class_id"]

                    # Find which category this class belongs to
                    object_category = "other"  # default
                    for category, class_ids in OBJECT_CATEGORIES.items():
                        if class_id in class_ids:
                            object_category = category
                            break

                    # Add category info to detection
                    det["category"] = object_category
                    categorized_detections[object_category].append(det)

            # Update tracking
            tracking_results = self.tracker.update(categorized_detections)

            # Draw tracking information
            frame_with_tracking = self.tracker.draw_tracking_info(
                frame, tracking_results
            )

            # Draw UI overlay
            self._draw_ui_overlay(frame_with_tracking)

            # Record frame if enabled
            if self.is_recording and self.video_writer:
                self.video_writer.write(frame_with_tracking)

            # Update phone display if enabled
            if self.phone_server:
                self.phone_server.update_frame(frame_with_tracking, detections)

            # Display frame
            cv2.imshow("Object Tracker", frame_with_tracking)

            # Handle keyboard input
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break
            elif key == ord("r"):
                self.tracker.reset()
                self.logger.info("Tracking reset")
            elif key == ord("s"):
                self._save_screenshot(frame_with_tracking)

            # Update counters
            self.frame_count += 1
            self._calculate_fps()

            # Optional: Control frame rate
            processing_time = time.time() - start_time
            target_time = 1.0 / CAMERA["framerate"]
            if processing_time < target_time:
                time.sleep(target_time - processing_time)

        cv2.destroyAllWindows()

    def _get_mock_frame(self):
        """Create a mock frame for testing offline detector"""
        # Create a simple frame for testing
        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        # Add some visual elements to simulate a football field
        # Green background (grass)
        frame[:, :] = (34, 139, 34)  # Forest green in BGR

        # White lines (field markings)
        cv2.line(frame, (320, 0), (320, 480), (255, 255, 255), 2)  # Center line
        cv2.rectangle(frame, (50, 50), (590, 430), (255, 255, 255), 2)  # Field boundary

        # Center circle
        cv2.circle(frame, (320, 240), 50, (255, 255, 255), 2)

        return frame

    def stop(self):
        """Stop the application and cleanup resources"""
        self.logger.info("Stopping object tracking application")

        self.is_running = False

        # Stop detector
        if self.detector and not self.use_offline:
            self.detector.stop()

        # Close video writer
        if self.video_writer:
            self.video_writer.release()
            self.is_recording = False
            self.logger.info("Recording stopped")

        # Final statistics
        self.logger.info(f"Total frames processed: {self.frame_count}")
        if self.current_fps > 0:
            self.logger.info(f"Average FPS: {self.current_fps:.2f}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Multi-Object Tracking with Raspberry Pi AI Camera"
    )

    parser.add_argument(
        "--model",
        choices=["yolo11n", "yolov8n"],
        default="yolo11n",
        help="AI model to use for detection",
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Use offline detector for testing without IMX500",
    )
    parser.add_argument(
        "--record", type=str, default=None, help="Output file path for video recording"
    )
    parser.add_argument(
        "--confidence",
        type=float,
        default=0.5,
        help="Confidence threshold for detections",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Enable demo mode with mock objects for demonstration",
    )
    parser.add_argument(
        "--camera",
        type=int,
        default=None,
        help="Camera index to use (0=built-in, 1+=external/phone camera)",
    )
    parser.add_argument(
        "--fast",
        action="store_true",
        help="Enable fast mode for maximum FPS (trades some accuracy for speed)",
    )
    parser.add_argument(
        "--phone-display",
        action="store_true",
        help="Enable phone display - show results on phone browser",
    )

    args = parser.parse_args()

    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Update confidence threshold in config
    if args.confidence:
        for model_config in MODELS.values():
            model_config["confidence_threshold"] = args.confidence

    # Create and start application
    app = ObjectTrackingApp(
        model_name=args.model,
        use_offline=args.offline,
        record_output=args.record,
        demo_mode=args.demo,
        camera_index=args.camera,
        fast_mode=args.fast,
        phone_display=args.phone_display,
    )

    try:
        app.start()
    except Exception as e:
        logging.error(f"Application failed: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
