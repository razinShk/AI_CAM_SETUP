import cv2
from ultralytics import YOLO

# Load YOLO model
print("Loading YOLO model...")
model = YOLO("yolo11n.pt")
print("✅ YOLO model loaded successfully")

# COCO class names (80 classes)
class_names = [
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

# Initialize camera
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("❌ Could not open camera")
    exit(1)

print("✅ Camera opened successfully")
print("Press 'q' to quit")

# Colors for different objects
colors = [
    (255, 0, 0),
    (0, 255, 0),
    (0, 0, 255),
    (255, 255, 0),
    (255, 0, 255),
    (0, 255, 255),
    (128, 0, 128),
    (255, 165, 0),
    (0, 128, 128),
    (128, 128, 0),
]

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Run YOLO detection
    results = model(frame, verbose=False)

    # Draw detections
    for result in results:
        boxes = result.boxes
        if boxes is not None:
            for i, box in enumerate(boxes):
                # Get box coordinates
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                conf = box.conf[0].cpu().numpy()
                cls = int(box.cls[0].cpu().numpy())

                # Only show high confidence detections
                if conf > 0.5:
                    # Get object name
                    object_name = (
                        class_names[cls] if cls < len(class_names) else f"Class {cls}"
                    )

                    # Choose color based on object type
                    color = colors[cls % len(colors)]

                    # Draw bounding box
                    cv2.rectangle(
                        frame, (int(x1), int(y1)), (int(x2), int(y2)), color, 2
                    )

                    # Draw label with object name
                    label = f"{object_name}: {conf:.2f}"
                    label_size = cv2.getTextSize(
                        label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2
                    )[0]

                    # Draw label background
                    cv2.rectangle(
                        frame,
                        (int(x1), int(y1) - label_size[1] - 10),
                        (int(x1) + label_size[0], int(y1)),
                        color,
                        -1,
                    )

                    # Draw label text
                    cv2.putText(
                        frame,
                        label,
                        (int(x1), int(y1) - 5),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (255, 255, 255),
                        2,
                    )

    # Add info overlay
    cv2.putText(
        frame,
        "YOLO Object Detection - Press 'q' to quit",
        (10, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 255),
        2,
    )

    # Show frame
    cv2.imshow("YOLO Object Detection", frame)

    # Press 'q' to quit
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
print("✅ Detection completed")
