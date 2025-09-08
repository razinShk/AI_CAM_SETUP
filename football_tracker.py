"""
Football Tracker - Main Entry Point
Simplified version for laptop testing with webcam
"""

import cv2
import argparse
import time
import os
from datetime import datetime
import numpy as np

# Import our modules
from detection import FootballDetector, OfflineDetector
from tracking import MultiObjectTracker
from config import MODELS


class FootballTrackerApp:
    """Main football tracker application"""

    def __init__(
        self, model="yolo11n", confidence=0.5, offline=False, record=None, verbose=False
    ):
        self.model_name = model
        self.confidence = confidence
        self.offline = offline
        self.record_path = record
        self.verbose = verbose

        # Initialize components
        self.detector = OfflineDetector() if offline else FootballDetector()
        self.tracker = MultiObjectTracker()
        self.writer = None

        # Camera
        self.cap = None
        self.running = False

        # Recording
        self.recording = record is not None

    def initialize_camera(self):
        """Initialize camera"""
        try:
            self.cap = cv2.VideoCapture(0)  # Use default webcam

            if not self.cap.isOpened():
                print("❌ Error: Could not open camera")
                return False

            # Set camera properties
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            self.cap.set(cv2.CAP_PROP_FPS, 30)

            print("✅ Camera initialized successfully")
            return True

        except Exception as e:
            print(f"❌ Camera initialization failed: {e}")
            return False

    def setup_recording(self):
        """Setup video recording"""
        if not self.recording:
            return True

        try:
            # Get frame size
            ret, frame = self.cap.read()
            if not ret:
                return False

            height, width = frame.shape[:2]

            # Setup video writer
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            fps = 30

            self.writer = cv2.VideoWriter(
                self.record_path, fourcc, fps, (width, height)
            )

            if not self.writer.isOpened():
                print(f"❌ Error: Could not create video file {self.record_path}")
                return False

            print(f"✅ Recording to: {self.record_path}")
            return True

        except Exception as e:
            print(f"❌ Recording setup failed: {e}")
            return False

    def draw_detections(self, frame, detections):
        """Draw detection boxes and labels"""
        for detection in detections:
            x, y, w, h, conf, class_id = detection

            # Draw bounding box
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

            # Draw label
            label = f"Object {class_id}: {conf:.2f}"
            cv2.putText(
                frame, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2
            )

        return frame

    def draw_tracking(self, frame, tracked_objects):
        """Draw tracking information"""
        for object_id, centroid in tracked_objects.items():
            # Draw centroid
            cv2.circle(frame, centroid, 5, (255, 0, 0), -1)

            # Draw object ID
            cv2.putText(
                frame,
                f"ID: {object_id}",
                (centroid[0] - 10, centroid[1] - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 0, 0),
                2,
            )

        return frame

    def run(self):
        """Main tracking loop"""
        print("🏆 Football Tracker Starting...")
        print(f"Model: {self.model_name}")
        print(f"Confidence: {self.confidence}")
        print(f"Offline mode: {self.offline}")
        print(f"Recording: {self.recording}")

        # Initialize camera
        if not self.initialize_camera():
            return False

        # Setup recording
        if self.recording and not self.setup_recording():
            return False

        self.running = True
        frame_count = 0
        start_time = time.time()

        print("🎬 Starting tracking... Press 'q' to quit")

        try:
            while self.running:
                ret, frame = self.cap.read()
                if not ret:
                    print("❌ Failed to read frame")
                    break

                frame_count += 1

                # Run detection
                detections = self.detector.detect(frame)

                # Convert detections to rectangles for tracking
                rects = []
                for detection in detections:
                    if len(detection) >= 6:  # Check if detection has enough values
                        x, y, w, h, conf, class_id = detection
                        if conf >= self.confidence:
                            rects.append((x, y, w, h))

                # Update tracking
                tracked_objects = self.tracker.update(rects)

                # Draw results
                frame = self.draw_detections(frame, detections)
                frame = self.draw_tracking(frame, tracked_objects)

                # Add info overlay
                elapsed = time.time() - start_time
                fps = frame_count / elapsed if elapsed > 0 else 0

                info_text = f"FPS: {fps:.1f} | Objects: {len(tracked_objects)} | Frame: {frame_count}"
                cv2.putText(
                    frame,
                    info_text,
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (255, 255, 255),
                    2,
                )

                # Show frame
                cv2.imshow("Football Tracker", frame)

                # Record frame
                if self.recording and self.writer:
                    self.writer.write(frame)

                # Check for quit
                key = cv2.waitKey(1) & 0xFF
                if key == ord("q"):
                    break

                # Print progress every 100 frames
                if self.verbose and frame_count % 100 == 0:
                    print(f"Processed {frame_count} frames, FPS: {fps:.1f}")

        except KeyboardInterrupt:
            print("\n🛑 Stopping tracker...")

        finally:
            self.cleanup()

        return True

    def cleanup(self):
        """Clean up resources"""
        self.running = False

        if self.writer:
            self.writer.release()
            print(f"✅ Video saved: {self.record_path}")

        if self.cap:
            self.cap.release()

        cv2.destroyAllWindows()
        print("✅ Cleanup completed")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Football Tracker")
    parser.add_argument(
        "--model",
        default="yolo11n",
        choices=["yolo11n", "yolov8n"],
        help="Model to use for detection",
    )
    parser.add_argument(
        "--confidence",
        type=float,
        default=0.5,
        help="Confidence threshold for detections",
    )
    parser.add_argument(
        "--offline", action="store_true", help="Run in offline mode (no camera)"
    )
    parser.add_argument("--record", type=str, help="Record video to specified file")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")

    args = parser.parse_args()

    # Create and run tracker
    tracker = FootballTrackerApp(
        model=args.model,
        confidence=args.confidence,
        offline=args.offline,
        record=args.record,
        verbose=args.verbose,
    )

    success = tracker.run()

    if success:
        print("✅ Tracker completed successfully")
    else:
        print("❌ Tracker failed")
        exit(1)


if __name__ == "__main__":
    main()
