#!/usr/bin/env python3
"""
Quick test for YOLOv11 integration
"""

import cv2
from detection import OfflineDetector


def test_yolo11():
    print("Testing YOLOv11 integration...")

    # Create detector
    detector = OfflineDetector(use_webcam=True)

    print(f"Model type: {detector.model_type}")
    print(f"YOLO model available: {detector.yolo_model is not None}")

    if detector.cap is None:
        print("No webcam available")
        return

    print("Press 'q' to quit, 's' for screenshot")

    while True:
        # Get frame
        frame = detector.get_frame()
        if frame is None:
            continue

        # Detect objects
        detections = detector.detect_objects(frame)

        # Draw detections
        for det in detections:
            bbox = det["bbox"]
            confidence = det["confidence"]
            class_name = det["class_name"]

            # Draw box
            cv2.rectangle(frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), (0, 255, 0), 2)

            # Draw label
            label = f"{class_name}: {confidence:.2f}"
            cv2.putText(
                frame,
                label,
                (bbox[0], bbox[1] - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 0),
                2,
            )

        # Show detection count
        cv2.putText(
            frame,
            f"Objects: {len(detections)}",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (255, 255, 255),
            2,
        )

        # Display
        cv2.imshow("YOLOv11 Test", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break
        elif key == ord("s"):
            cv2.imwrite("yolo11_test.jpg", frame)
            print("Screenshot saved!")

    cv2.destroyAllWindows()
    print("Test completed")


if __name__ == "__main__":
    test_yolo11()
