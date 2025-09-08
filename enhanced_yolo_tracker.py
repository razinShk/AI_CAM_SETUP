import cv2
import numpy as np
from ultralytics import YOLO
from tracking import MultiObjectTracker
import time
from datetime import datetime
import threading


class EnhancedYOLOTracker:
    def __init__(self):
        # Load YOLO model
        print("Loading YOLO model...")
        self.model = YOLO("yolo11n.pt")
        print("✅ YOLO model loaded successfully")

        # Initialize tracker
        self.tracker = MultiObjectTracker()

        # COCO class names
        self.class_names = [
            "person",
            "bicycle",
            "car",
            "motorcycle",
            "airplane",
            "bus",
            "train",
            "truck",
            "boat",
            "traffic light",
            "fire hydrant",
            "stop sign",
            "parking meter",
            "bench",
            "bird",
            "cat",
            "dog",
            "horse",
            "sheep",
            "cow",
            "elephant",
            "bear",
            "zebra",
            "giraffe",
            "backpack",
            "umbrella",
            "handbag",
            "tie",
            "suitcase",
            "frisbee",
            "skis",
            "snowboard",
            "sports ball",
            "kite",
            "baseball bat",
            "baseball glove",
            "skateboard",
            "surfboard",
            "tennis racket",
            "bottle",
            "wine glass",
            "cup",
            "fork",
            "knife",
            "spoon",
            "bowl",
            "banana",
            "apple",
            "sandwich",
            "orange",
            "broccoli",
            "carrot",
            "hot dog",
            "pizza",
            "donut",
            "cake",
            "chair",
            "couch",
            "potted plant",
            "bed",
            "dining table",
            "toilet",
            "tv",
            "laptop",
            "mouse",
            "remote",
            "keyboard",
            "cell phone",
            "microwave",
            "oven",
            "toaster",
            "sink",
            "refrigerator",
            "book",
            "clock",
            "vase",
            "scissors",
            "teddy bear",
            "hair drier",
            "toothbrush",
        ]

        # Camera and recording
        self.cap = None
        self.writer = None
        self.recording = False
        self.recording_thread = None

        # Zoom functionality
        self.zoom_factor = 1.0
        self.target_objects = []
        self.zoom_speed = 0.05
        self.min_zoom = 0.5
        self.max_zoom = 3.0

        # UI state
        self.running = False
        self.frame_count = 0
        self.start_time = time.time()

    def initialize_camera(self):
        """Initialize camera"""
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            print("❌ Could not open camera")
            return False

        # Set camera properties
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        self.cap.set(cv2.CAP_PROP_FPS, 30)

        print("✅ Camera initialized successfully")
        return True

    def start_recording(self):
        """Start video recording"""
        if self.recording:
            return False

        try:
            # Get frame size
            ret, frame = self.cap.read()
            if not ret:
                return False

            height, width = frame.shape[:2]

            # Create filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"recording_{timestamp}.mp4"

            # Setup video writer
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            fps = 30
            self.writer = cv2.VideoWriter(filename, fourcc, fps, (width, height))

            if not self.writer.isOpened():
                print(f"❌ Error: Could not create video file {filename}")
                return False

            self.recording = True
            print(f"✅ Recording started: {filename}")
            return True

        except Exception as e:
            print(f"❌ Recording start failed: {e}")
            return False

    def stop_recording(self):
        """Stop video recording"""
        if not self.recording:
            return False

        self.recording = False
        if self.writer:
            self.writer.release()
            self.writer = None
            print("✅ Recording stopped")
            return True
        return False

    def apply_zoom(self, frame, target_objects):
        """Apply zoom based on detected objects"""
        if not target_objects:
            # No objects, gradually zoom out
            self.zoom_factor = max(self.min_zoom, self.zoom_factor - self.zoom_speed)
        else:
            # Objects detected, zoom in
            self.zoom_factor = min(self.max_zoom, self.zoom_factor + self.zoom_speed)

        # Apply zoom
        if self.zoom_factor != 1.0:
            h, w = frame.shape[:2]
            center_x, center_y = w // 2, h // 2

            # Calculate new dimensions
            new_w = int(w / self.zoom_factor)
            new_h = int(h / self.zoom_factor)

            # Calculate crop region
            x1 = max(0, center_x - new_w // 2)
            y1 = max(0, center_y - new_h // 2)
            x2 = min(w, x1 + new_w)
            y2 = min(h, y1 + new_h)

            # Crop and resize
            cropped = frame[y1:y2, x1:x2]
            if cropped.size > 0:
                frame = cv2.resize(cropped, (w, h))

        return frame

    def draw_ui(self, frame):
        """Draw user interface"""
        h, w = frame.shape[:2]

        # Draw control panel
        panel_height = 80
        panel = np.zeros((panel_height, w, 3), dtype=np.uint8)
        panel[:] = (50, 50, 50)  # Dark gray background

        # Add panel to frame
        frame[:panel_height] = panel

        # Draw buttons
        button_width = 120
        button_height = 40
        button_y = 20

        # Start/Stop button
        if not self.recording:
            button_color = (0, 255, 0)  # Green
            button_text = "START"
        else:
            button_color = (0, 0, 255)  # Red
            button_text = "STOP"

        cv2.rectangle(
            frame,
            (20, button_y),
            (20 + button_width, button_y + button_height),
            button_color,
            -1,
        )
        cv2.putText(
            frame,
            button_text,
            (35, button_y + 25),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2,
        )

        # Recording indicator
        if self.recording:
            cv2.circle(frame, (w - 30, 30), 10, (0, 0, 255), -1)
            cv2.putText(
                frame,
                "REC",
                (w - 80, 35),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 0, 255),
                2,
            )

        # Zoom indicator
        zoom_text = f"Zoom: {self.zoom_factor:.1f}x"
        cv2.putText(
            frame,
            zoom_text,
            (200, button_y + 25),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            2,
        )

        # FPS and object count
        elapsed = time.time() - self.start_time
        fps = self.frame_count / elapsed if elapsed > 0 else 0
        info_text = f"FPS: {fps:.1f} | Objects: {len(self.target_objects)}"
        cv2.putText(
            frame,
            info_text,
            (400, button_y + 25),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            2,
        )

        # Instructions
        cv2.putText(
            frame,
            "Click START to record, STOP to stop, 'q' to quit",
            (20, h - 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 255, 255),
            1,
        )

        return frame

    def handle_mouse_click(self, event, x, y, flags, param):
        """Handle mouse clicks for button interaction"""
        if event == cv2.EVENT_LBUTTONDOWN:
            # Check if click is on START/STOP button
            if 20 <= x <= 140 and 20 <= y <= 60:
                if not self.recording:
                    self.start_recording()
                else:
                    self.stop_recording()

    def run(self):
        """Main tracking loop"""
        if not self.initialize_camera():
            return False

        print("🎬 Enhanced YOLO Tracker Starting...")
        print("Controls:")
        print("- Click START button to begin recording")
        print("- Click STOP button to stop recording")
        print("- Press 'q' to quit")

        # Create window and set mouse callback
        cv2.namedWindow("Enhanced YOLO Tracker", cv2.WINDOW_AUTOSIZE)
        cv2.setMouseCallback("Enhanced YOLO Tracker", self.handle_mouse_click)

        self.running = True

        try:
            while self.running:
                ret, frame = self.cap.read()
                if not ret:
                    break

                self.frame_count += 1

                # Run YOLO detection
                results = self.model(frame, verbose=False)

                # Process detections
                rects = []
                detections = []
                self.target_objects = []

                for result in results:
                    boxes = result.boxes
                    if boxes is not None:
                        for box in boxes:
                            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                            conf = box.conf[0].cpu().numpy()
                            cls = int(box.cls[0].cpu().numpy())

                            if conf > 0.5:
                                x, y, w, h = (
                                    int(x1),
                                    int(y1),
                                    int(x2 - x1),
                                    int(y2 - y1),
                                )
                                rects.append((x, y, w, h))
                                detections.append((x, y, w, h, conf, cls))
                                self.target_objects.append((x, y, w, h, conf, cls))

                # Update tracking
                tracked_objects = self.tracker.update(rects)

                # Apply zoom based on objects
                frame = self.apply_zoom(frame, self.target_objects)

                # Draw detections
                for detection in detections:
                    x, y, w, h, conf, cls = detection
                    object_name = (
                        self.class_names[cls]
                        if cls < len(self.class_names)
                        else f"Class {cls}"
                    )

                    # Draw bounding box
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

                    # Draw label
                    label = f"{object_name}: {conf:.2f}"
                    cv2.putText(
                        frame,
                        label,
                        (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        (0, 255, 0),
                        2,
                    )

                # Draw tracking IDs
                for object_id, centroid in tracked_objects.items():
                    cv2.circle(frame, centroid, 5, (255, 0, 0), -1)
                    cv2.putText(
                        frame,
                        f"ID: {object_id}",
                        (centroid[0] - 10, centroid[1] - 10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        (255, 0, 0),
                        2,
                    )

                # Draw UI
                frame = self.draw_ui(frame)

                # Record frame if recording
                if self.recording and self.writer:
                    self.writer.write(frame)

                # Show frame
                cv2.imshow("Enhanced YOLO Tracker", frame)

                # Check for quit
                key = cv2.waitKey(1) & 0xFF
                if key == ord("q"):
                    break

        except KeyboardInterrupt:
            print("\n🛑 Stopping tracker...")

        finally:
            self.cleanup()

        return True

    def cleanup(self):
        """Clean up resources"""
        self.running = False
        self.stop_recording()

        if self.cap:
            self.cap.release()

        cv2.destroyAllWindows()
        print("✅ Cleanup completed")


def main():
    """Main entry point"""
    tracker = EnhancedYOLOTracker()
    success = tracker.run()

    if success:
        print("✅ Tracker completed successfully")
    else:
        print("❌ Tracker failed")
        exit(1)


if __name__ == "__main__":
    main()
