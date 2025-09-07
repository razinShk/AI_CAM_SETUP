"""
Configuration settings for the football tracking software
"""

# Model configurations
MODELS = {
    "yolo11n": {
        "path": "/usr/share/imx500-models/imx500_network_yolo11n_pp.rpk",
        "bbox_normalization": True,
        "bbox_order": "xy",
        "input_size": (640, 640),
        "confidence_threshold": 0.5,
        "nms_threshold": 0.4,
    },
    "yolov8n": {
        "path": "/usr/share/imx500-models/imx500_network_yolov8n_pp.rpk",
        "bbox_normalization": True,
        "bbox_order": "xy",
        "input_size": (640, 640),
        "confidence_threshold": 0.5,
        "nms_threshold": 0.4,
    },
}

# COCO class names (80 classes) - focusing on person and sports ball
COCO_CLASSES = [
    "person",
    "bicycle",
    "car",
    "motorbike",
    "aeroplane",
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
    "sofa",
    "pottedplant",
    "bed",
    "diningtable",
    "toilet",
    "tvmonitor",
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

# All COCO classes - track any object
ENABLED_CLASSES = {
    "person": 0,
    "bicycle": 1,
    "car": 2,
    "motorbike": 3,
    "aeroplane": 4,
    "bus": 5,
    "train": 6,
    "truck": 7,
    "boat": 8,
    "traffic light": 9,
    "fire hydrant": 10,
    "stop sign": 11,
    "parking meter": 12,
    "bench": 13,
    "bird": 14,
    "cat": 15,
    "dog": 16,
    "horse": 17,
    "sheep": 18,
    "cow": 19,
    "elephant": 20,
    "bear": 21,
    "zebra": 22,
    "giraffe": 23,
    "backpack": 24,
    "umbrella": 25,
    "handbag": 26,
    "tie": 27,
    "suitcase": 28,
    "frisbee": 29,
    "skis": 30,
    "snowboard": 31,
    "sports ball": 32,
    "kite": 33,
    "baseball bat": 34,
    "baseball glove": 35,
    "skateboard": 36,
    "surfboard": 37,
    "tennis racket": 38,
    "bottle": 39,
    "wine glass": 40,
    "cup": 41,
    "fork": 42,
    "knife": 43,
    "spoon": 44,
    "bowl": 45,
    "banana": 46,
    "apple": 47,
    "sandwich": 48,
    "orange": 49,
    "broccoli": 50,
    "carrot": 51,
    "hot dog": 52,
    "pizza": 53,
    "donut": 54,
    "cake": 55,
    "chair": 56,
    "sofa": 57,
    "pottedplant": 58,
    "bed": 59,
    "diningtable": 60,
    "toilet": 61,
    "tvmonitor": 62,
    "laptop": 63,
    "mouse": 64,
    "remote": 65,
    "keyboard": 66,
    "cell phone": 67,
    "microwave": 68,
    "oven": 69,
    "toaster": 70,
    "sink": 71,
    "refrigerator": 72,
    "book": 73,
    "clock": 74,
    "vase": 75,
    "scissors": 76,
    "teddy bear": 77,
    "hair drier": 78,
    "toothbrush": 79,
}

# Categories for different object types
OBJECT_CATEGORIES = {
    "people": [0],  # person
    "vehicles": [1, 2, 3, 4, 5, 6, 7, 8],  # bicycle, car, motorbike, etc.
    "animals": [14, 15, 16, 17, 18, 19, 20, 21, 22, 23],  # bird, cat, dog, etc.
    "sports": [29, 30, 31, 32, 33, 34, 35, 36, 37, 38],  # frisbee, skis, etc.
    "electronics": [62, 63, 64, 65, 66, 67, 68, 69, 70],  # tvmonitor, laptop, etc.
    "furniture": [56, 57, 58, 59, 60, 61],  # chair, sofa, etc.
    "food": [46, 47, 48, 49, 50, 51, 52, 53, 54, 55],  # banana, apple, etc.
    "other": [],  # Will be populated with remaining classes
}

# Populate 'other' category with remaining classes
all_categorized = set()
for category_classes in OBJECT_CATEGORIES.values():
    all_categorized.update(category_classes)
OBJECT_CATEGORIES["other"] = [i for i in range(80) if i not in all_categorized]

# Tracking parameters
TRACKING = {
    "max_disappeared": 30,  # Maximum frames an object can disappear before being removed
    "max_distance": 100,  # Maximum distance for object association
    "min_area": 500,  # Minimum bounding box area to consider
    "trail_length": 10,  # Number of points in movement trail
}

# Camera settings
CAMERA = {"resolution": (1280, 720), "framerate": 30, "preview_size": (640, 480)}

# Recording settings
RECORDING = {"codec": "mp4v", "fps": 30, "quality": 90}

# Colors for visualization (BGR format) - different colors for different categories
CATEGORY_COLORS = {
    "people": (0, 255, 0),  # Green for people
    "vehicles": (255, 0, 0),  # Blue for vehicles
    "animals": (0, 165, 255),  # Orange for animals
    "sports": (0, 0, 255),  # Red for sports items
    "electronics": (255, 0, 255),  # Magenta for electronics
    "furniture": (255, 255, 0),  # Cyan for furniture
    "food": (0, 255, 255),  # Yellow for food
    "other": (128, 128, 128),  # Gray for other objects
}

# UI Colors
COLORS = {
    "trail": (255, 255, 0),  # Yellow for movement trail
    "text": (255, 255, 255),  # White for text
    "background": (0, 0, 0),  # Black for background
    "bbox": (0, 255, 0),  # Default green for bounding boxes
}
