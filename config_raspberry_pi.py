"""
Raspberry Pi 5 + IMX500 AI Camera Configuration
Optimized settings for camera-based AI processing
"""

# IMX500 AI Models - optimized for neural processor
RASPBERRY_PI_MODELS = {
    "yolo11n": {
        "path": "models/yolo11n_224x224.rpk",
        "input_size": (224, 224),
        "confidence_threshold": 0.5,
        "bbox_normalization": True,
        "bbox_order": "xyxy",
        "description": "Fastest model, best for real-time tracking",
    },
    "yolo11s": {
        "path": "models/yolo11s_224x224.rpk",
        "input_size": (224, 224),
        "confidence_threshold": 0.5,
        "bbox_normalization": True,
        "bbox_order": "xyxy",
        "description": "Balanced speed and accuracy",
    },
    "yolov8n": {
        "path": "models/yolov8n_224x224.rpk",
        "input_size": (224, 224),
        "confidence_threshold": 0.5,
        "bbox_normalization": True,
        "bbox_order": "xyxy",
        "description": "Legacy YOLO model support",
    },
    "yolov8s": {
        "path": "models/yolov8s_224x224.rpk",
        "input_size": (224, 224),
        "confidence_threshold": 0.5,
        "bbox_normalization": True,
        "bbox_order": "xyxy",
        "description": "Higher accuracy, slightly slower",
    },
}

# Raspberry Pi Camera Settings - optimized for IMX500
RASPBERRY_PI_CAMERA = {
    "resolution": (1920, 1080),  # Main resolution
    "ai_resolution": (640, 640),  # AI processing resolution
    "framerate": 30,
    "preview_size": (800, 600),
    "auto_exposure": True,
    "auto_white_balance": True,
    "auto_focus": True,
    "exposure_time": 10000,  # microseconds
    "analogue_gain": 1.0,
    "digital_gain": 1.0,
}

# Performance Settings - optimized for Pi 5 + IMX500
RASPBERRY_PI_PERFORMANCE = {
    "ai_on_camera": True,  # Use IMX500 neural processor
    "cpu_tracking_only": True,  # Pi CPU only does tracking
    "max_objects": 50,  # Maximum objects to track
    "tracking_buffer": 30,  # Frame buffer for tracking
    "inference_threads": 1,  # IMX500 handles inference
    "display_fps": 30,  # Display refresh rate
}

# Recording Settings for Raspberry Pi
RASPBERRY_PI_RECORDING = {
    "codec": "H264",  # Hardware accelerated on Pi
    "fps": 30,
    "quality": 23,  # H264 quality (lower = better)
    "bitrate": 2000000,  # 2 Mbps
    "keyframe_interval": 30,
    "use_gpu_encoder": True,  # Use Pi's GPU encoder
}

# Object Categories (same as main config)
PI_OBJECT_CATEGORIES = {
    "people": [0],  # person
    "vehicles": [1, 2, 3, 4, 5, 6, 7, 8],  # bicycle, car, motorbike, etc.
    "animals": [14, 15, 16, 17, 18, 19, 20, 21, 22, 23],  # bird, cat, dog, etc.
    "sports": [29, 30, 31, 32, 33, 34, 35, 36, 37, 38],  # frisbee, skis, etc.
    "electronics": [62, 63, 64, 65, 66, 67, 68, 69, 70],  # tvmonitor, laptop, etc.
    "furniture": [56, 57, 58, 59, 60, 61],  # chair, sofa, etc.
    "food": [46, 47, 48, 49, 50, 51, 52, 53, 54, 55],  # banana, apple, etc.
    "other": [],  # Populated automatically
}

# Populate 'other' category
all_categorized = set()
for category_classes in PI_OBJECT_CATEGORIES.values():
    all_categorized.update(category_classes)
PI_OBJECT_CATEGORIES["other"] = [i for i in range(80) if i not in all_categorized]

# Tracking Settings - lightweight for Pi CPU
RASPBERRY_PI_TRACKING = {
    "max_disappeared": 30,
    "max_distance": 100,
    "min_area": 500,
    "trail_length": 10,
    "update_frequency": 30,  # Update tracking every N frames
    "memory_optimization": True,
}

# Color Scheme for Categories
PI_CATEGORY_COLORS = {
    "people": (0, 255, 0),  # Green for people
    "vehicles": (255, 0, 0),  # Blue for vehicles
    "animals": (0, 165, 255),  # Orange for animals
    "sports": (0, 0, 255),  # Red for sports items
    "electronics": (255, 0, 255),  # Magenta for electronics
    "furniture": (255, 255, 0),  # Cyan for furniture
    "food": (0, 255, 255),  # Yellow for food
    "other": (128, 128, 128),  # Gray for other objects
}

# System Monitoring
RASPBERRY_PI_MONITORING = {
    "log_performance": True,
    "log_interval": 100,  # Log every N frames
    "monitor_temperature": True,
    "monitor_cpu": True,
    "monitor_memory": True,
    "temperature_warning": 70,  # Celsius
    "cpu_warning": 80,  # Percentage
}

# GPIO Settings (for future expansion)
RASPBERRY_PI_GPIO = {
    "status_led": 18,
    "recording_led": 19,
    "button_record": 21,
    "button_reset": 20,
    "enable_gpio": False,  # Set to True to enable GPIO features
}

# Network Settings
RASPBERRY_PI_NETWORK = {
    "enable_web_interface": False,
    "web_port": 5000,
    "enable_mqtt": False,
    "mqtt_broker": "localhost",
    "mqtt_port": 1883,
    "mqtt_topic": "pi/tracker",
}

# File Paths
RASPBERRY_PI_PATHS = {
    "models_dir": "models",
    "recordings_dir": "recordings",
    "screenshots_dir": "screenshots",
    "logs_dir": "logs",
    "config_file": "/boot/config.txt",
}

# Hardware-specific optimizations
RASPBERRY_PI_HARDWARE = {
    "gpu_memory": 128,  # MB allocated to GPU
    "camera_interface": "IMX500",
    "neural_processor": "IMX500_NPU",
    "cpu_cores": 4,
    "optimize_for_pi5": True,
    "enable_hardware_acceleration": True,
}

# Default configuration for Raspberry Pi
DEFAULT_PI_CONFIG = {
    "model": "yolo11n",
    "camera": RASPBERRY_PI_CAMERA,
    "performance": RASPBERRY_PI_PERFORMANCE,
    "recording": RASPBERRY_PI_RECORDING,
    "tracking": RASPBERRY_PI_TRACKING,
    "monitoring": RASPBERRY_PI_MONITORING,
    "enable_preview": True,
    "headless_mode": False,
    "auto_start": False,
}

# Export main configuration
MODELS = RASPBERRY_PI_MODELS
CAMERA = RASPBERRY_PI_CAMERA
RECORDING = RASPBERRY_PI_RECORDING
TRACKING = RASPBERRY_PI_TRACKING
OBJECT_CATEGORIES = PI_OBJECT_CATEGORIES
CATEGORY_COLORS = PI_CATEGORY_COLORS

# COCO class names (same as main config)
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

# Enabled classes for detection (all COCO classes)
ENABLED_CLASSES = {name: idx for idx, name in enumerate(COCO_CLASSES)}
