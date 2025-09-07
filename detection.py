"""
Football detection module using Raspberry Pi AI Camera (IMX500) models
"""

import cv2
import numpy as np
import logging
import os
from config import (
    MODELS,
    COCO_CLASSES,
    ENABLED_CLASSES,
    OBJECT_CATEGORIES,
    CATEGORY_COLORS,
    CAMERA,
)

# Try to import picamera2, but handle gracefully if not available (Windows)
try:
    from picamera2 import Picamera2

    PICAMERA2_AVAILABLE = True
except ImportError:
    PICAMERA2_AVAILABLE = False
    print("Warning: picamera2 not available. Running in offline mode only.")

# Try to import ultralytics YOLO for modern YOLO models
try:
    from ultralytics import YOLO

    ULTRALYTICS_AVAILABLE = True
except ImportError:
    ULTRALYTICS_AVAILABLE = False


class FootballDetector:
    """
    Football player and ball detection using IMX500 models
    """

    def __init__(self, model_name="yolo11n"):
        """
        Initialize the detector with specified model

        Args:
            model_name (str): Model to use ('yolo11n' or 'yolov8n')
        """
        self.model_name = model_name
        self.model_config = MODELS[model_name]
        self.camera = None
        self.is_running = False

        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        # Initialize camera
        self._setup_camera()

    def _setup_camera(self):
        """Setup and configure the Picamera2 for IMX500"""
        if not PICAMERA2_AVAILABLE:
            raise ImportError(
                "picamera2 not available. Use --offline mode for testing."
            )

        try:
            self.camera = Picamera2()

            # Configure camera for IMX500 model inference
            config = self.camera.create_preview_configuration(
                main={"size": CAMERA["resolution"]},
                lores={"size": self.model_config["input_size"]},
                controls={"FrameRate": CAMERA["framerate"]},
            )

            # Enable IMX500 model
            config["transform"] = {}

            self.camera.configure(config)
            self.logger.info(f"Camera configured for {self.model_name} model")

        except Exception as e:
            self.logger.error(f"Failed to setup camera: {e}")
            raise

    def load_model(self):
        """Load the IMX500 model"""
        try:
            # Set the model file for IMX500
            self.camera.set_controls(
                {"rpi.imx500.model_file": self.model_config["path"]}
            )
            self.logger.info(f"Loaded model: {self.model_config['path']}")

        except Exception as e:
            self.logger.error(f"Failed to load model: {e}")
            raise

    def start(self):
        """Start the camera and model inference"""
        try:
            self.load_model()
            self.camera.start()
            self.is_running = True
            self.logger.info("Detection started")

        except Exception as e:
            self.logger.error(f"Failed to start detection: {e}")
            raise

    def stop(self):
        """Stop the camera and inference"""
        if self.camera and self.is_running:
            self.camera.stop()
            self.is_running = False
            self.logger.info("Detection stopped")

    def get_detections(self):
        """
        Get current frame with detections

        Returns:
            tuple: (frame, detections) where detections is list of detection objects
        """
        if not self.is_running:
            return None, []

        try:
            # Capture frame
            frame = self.camera.capture_array("main")

            # Get inference results from IMX500
            metadata = self.camera.capture_metadata()

            detections = []

            # Process inference results if available
            if "rpi.imx500.results" in metadata:
                inference_results = metadata["rpi.imx500.results"]
                detections = self._process_inference_results(
                    inference_results, frame.shape
                )

            return frame, detections

        except Exception as e:
            self.logger.error(f"Error getting detections: {e}")
            return None, []

    def _process_inference_results(self, results, frame_shape):
        """
        Process raw inference results into detection objects

        Args:
            results: Raw inference results from IMX500
            frame_shape: Shape of the captured frame (height, width, channels)

        Returns:
            list: List of detection dictionaries
        """
        detections = []

        try:
            # Parse results based on model type
            if "detections" in results:
                raw_detections = results["detections"]

                for detection in raw_detections:
                    # Extract detection data
                    class_id = int(detection.get("class_id", -1))
                    confidence = float(detection.get("confidence", 0.0))
                    bbox = detection.get("bbox", [0, 0, 0, 0])

                    # Filter by confidence threshold
                    if confidence < self.model_config["confidence_threshold"]:
                        continue

                    # Filter for enabled classes only
                    if class_id not in ENABLED_CLASSES.values():
                        continue

                    # Convert normalized coordinates to pixel coordinates
                    h, w = frame_shape[:2]

                    if self.model_config["bbox_normalization"]:
                        if self.model_config["bbox_order"] == "xy":
                            x1, y1, x2, y2 = bbox
                            x1, x2 = int(x1 * w), int(x2 * w)
                            y1, y2 = int(y1 * h), int(y2 * h)
                        else:  # 'yx' order
                            y1, x1, y2, x2 = bbox
                            x1, x2 = int(x1 * w), int(x2 * w)
                            y1, y2 = int(y1 * h), int(y2 * h)
                    else:
                        x1, y1, x2, y2 = [int(coord) for coord in bbox]

                    # Create detection object
                    det = {
                        "class_id": class_id,
                        "class_name": (
                            COCO_CLASSES[class_id]
                            if class_id < len(COCO_CLASSES)
                            else "unknown"
                        ),
                        "confidence": confidence,
                        "bbox": [x1, y1, x2, y2],
                        "center": [(x1 + x2) // 2, (y1 + y2) // 2],
                        "area": (x2 - x1) * (y2 - y1),
                    }

                    detections.append(det)

        except Exception as e:
            self.logger.error(f"Error processing inference results: {e}")

        return detections

    def categorize_objects(self, detections):
        """
        Categorize detections by object type

        Args:
            detections (list): List of detection objects

        Returns:
            dict: Objects categorized by type
        """
        categorized = {}
        for category in OBJECT_CATEGORIES.keys():
            categorized[category] = []

        for detection in detections:
            class_id = detection["class_id"]

            # Find which category this class belongs to
            object_category = "other"  # default
            for category, class_ids in OBJECT_CATEGORIES.items():
                if class_id in class_ids:
                    object_category = category
                    break

            # Add category info to detection
            detection["category"] = object_category
            categorized[object_category].append(detection)

        return categorized

    def __del__(self):
        """Cleanup when object is destroyed"""
        self.stop()


class OfflineDetector:
    """
    Alternative detector for testing without IMX500 hardware
    Uses standard OpenCV/YOLO for development and testing
    """

    def __init__(self, model_path=None, use_webcam=True, camera_index=None):
        """Initialize offline detector with YOLO model"""
        self.model_path = model_path
        self.use_webcam = use_webcam
        self.camera_index = camera_index
        self.cap = None
        self.net = None
        self.yolo_model = None
        self.model_type = None
        self.output_layers = None
        self.classes = COCO_CLASSES
        self._demo_mode = False

        # Try to initialize webcam if requested
        if self.use_webcam:
            self._setup_webcam()

        # Try to load model - either provided path or auto-detect
        if model_path:
            self._load_yolo_model()
        else:
            self._try_auto_load_model()

    def _setup_webcam(self):
        """Setup webcam for testing - tries multiple camera indices"""
        try:
            # If a specific camera index is requested, try that first
            if self.camera_index is not None:
                cap = cv2.VideoCapture(self.camera_index)
                if cap.isOpened():
                    ret, frame = cap.read()
                    if ret and frame is not None:
                        self.cap = cap
                        # Try to set higher resolution for phone cameras
                        if self.camera_index > 0:
                            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
                            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

                        # Get camera info
                        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                        fps = cap.get(cv2.CAP_PROP_FPS)

                        print(
                            f"📱 Using camera {self.camera_index}: {width}x{height}, FPS: {fps}"
                        )
                        if self.camera_index > 0:
                            print("🔄 External/Phone camera detected")
                        else:
                            print("📷 Built-in camera detected")
                        return
                    else:
                        cap.release()
                        print(f"❌ Camera {self.camera_index} not working")
                else:
                    cap.release()
                    print(f"❌ Could not open camera {self.camera_index}")

            # Auto-detect cameras, prioritizing external cameras (phone cameras)
            print("🔍 Auto-detecting cameras...")
            camera_indices = [
                1,
                2,
                3,
                4,
                0,
            ]  # Try external cameras first, then built-in

            for camera_index in camera_indices:
                cap = cv2.VideoCapture(camera_index)
                if cap.isOpened():
                    # Test if camera actually works
                    ret, frame = cap.read()
                    if ret and frame is not None:
                        self.cap = cap

                        # Try to set higher resolution for external cameras
                        if camera_index > 0:
                            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
                            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

                        # Get camera info
                        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                        fps = cap.get(cv2.CAP_PROP_FPS)
                        print(
                            f"✅ Camera {camera_index} initialized: {width}x{height}, FPS: {fps}"
                        )

                        # If this is not camera 0, it's likely an external/phone camera
                        if camera_index > 0:
                            print(
                                "📱 External/Phone camera detected - prioritizing over built-in"
                            )
                        else:
                            print("📷 Built-in camera detected")

                        return
                    else:
                        cap.release()
                else:
                    cap.release()

            # If no camera found
            print("❌ No working camera found")
            print("📱 If using phone camera:")
            print("   1. Connect phone via USB")
            print("   2. Enable USB Debugging")
            print("   3. Select File Transfer mode")
            print("   4. Use: python camera_selector.py")
            self.cap = None

        except Exception as e:
            print(f"Failed to setup webcam: {e}")
            self.cap = None

    def _try_auto_load_model(self):
        """Try to automatically load YOLO model if available"""
        # First try ultralytics YOLO models (YOLOv11, YOLOv8, etc.)
        ultralytics_models = [
            "yolo11s.pt",
            "yolo11n.pt",
            "yolov8s.pt",
            "yolov8n.pt",
            "models/yolo11s.pt",
            "models/yolo11n.pt",
            "models/yolov8s.pt",
            "models/yolov8n.pt",
        ]

        for model_path in ultralytics_models:
            if os.path.exists(model_path):
                print(f"Found Ultralytics YOLO model: {model_path}")
                try:
                    self._load_ultralytics_model(model_path)
                    return
                except Exception as e:
                    print(f"Failed to load {model_path}: {e}")

        # Try to download and use YOLOv11 automatically
        try:
            print("Attempting to download YOLOv11n model...")
            self._load_ultralytics_model("yolo11n.pt")  # This will auto-download
            return
        except Exception as e:
            print(f"Failed to auto-download YOLOv11: {e}")

        # Fallback to OpenCV DNN models
        opencv_model_paths = [
            ("models/yolov3-tiny.weights", "models/yolov3-tiny.cfg"),
            ("yolov3-tiny.weights", "yolov3-tiny.cfg"),
        ]

        for weights_path, config_path in opencv_model_paths:
            if os.path.exists(weights_path) and os.path.exists(config_path):
                print(f"Found OpenCV YOLO model: {weights_path}")
                try:
                    self._load_yolo_model_files(weights_path, config_path)
                    return
                except Exception as e:
                    print(f"Failed to load {weights_path}: {e}")

        print("No YOLO model found. Install ultralytics: pip install ultralytics")
        print("Or use 'python download_yolo_model.py' to download OpenCV models.")
        print("Running without real object detection.")

    def _load_yolo_model(self):
        """Load YOLO model using OpenCV DNN (single file)"""
        try:
            # This would load a standard YOLO model for testing
            # In actual implementation, you'd need YOLO weights and config
            self.net = cv2.dnn.readNet(self.model_path)
            layer_names = self.net.getLayerNames()
            self.output_layers = [
                layer_names[i[0] - 1] for i in self.net.getUnconnectedOutLayers()
            ]
            print(f"Loaded YOLO model: {self.model_path}")

        except Exception as e:
            print(f"Could not load YOLO model: {e}")
            print("Using mock detections for testing")

    def _load_ultralytics_model(self, model_path):
        """Load ultralytics YOLO model (YOLOv11, YOLOv8, etc.)"""
        if not ULTRALYTICS_AVAILABLE:
            raise ImportError(
                "ultralytics not available. Install with: pip install ultralytics"
            )

        try:
            self.yolo_model = YOLO(model_path)
            self.model_type = "ultralytics"
            print(f"Loaded Ultralytics YOLO model: {model_path}")
        except Exception as e:
            print(f"Could not load Ultralytics YOLO model: {e}")
            raise

    def _load_yolo_model_files(self, weights_path, config_path):
        """Load YOLO model from weights and config files"""
        try:
            self.net = cv2.dnn.readNet(weights_path, config_path)
            layer_names = self.net.getLayerNames()
            self.output_layers = [
                layer_names[i[0] - 1] for i in self.net.getUnconnectedOutLayers()
            ]
            self.model_type = "opencv"
            print(f"Loaded OpenCV YOLO model: {weights_path}")

        except Exception as e:
            print(f"Could not load YOLO model: {e}")
            print("Using mock detections for testing")

    def get_frame(self):
        """Get frame from webcam or create mock frame"""
        if self.cap is not None:
            ret, frame = self.cap.read()
            if ret:
                return frame

        # Fallback to mock frame
        return self._create_mock_frame()

    def _create_mock_frame(self):
        """Create a mock frame for testing"""
        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        # Add some visual elements to simulate a football field
        # Green background (grass)
        frame[:, :] = (34, 139, 34)  # Forest green in BGR

        # White lines (field markings)
        cv2.line(frame, (320, 0), (320, 480), (255, 255, 255), 2)  # Center line
        cv2.rectangle(frame, (50, 50), (590, 430), (255, 255, 255), 2)  # Field boundary

        # Center circle
        cv2.circle(frame, (320, 240), 50, (255, 255, 255), 2)

        # Add some moving elements for testing
        import time

        t = time.time()
        x = int(320 + 200 * np.sin(t * 0.5))
        y = int(240 + 100 * np.cos(t * 0.3))
        cv2.circle(frame, (x, y), 20, (0, 0, 255), -1)  # Moving ball

        return frame

    def detect_objects(self, frame=None):
        """
        Detect objects in frame using real detection or no detection

        Args:
            frame: Input image frame (if None, will get from webcam/mock)

        Returns:
            list: List of detection objects
        """
        if frame is None:
            frame = self.get_frame()

        # Try to use real object detection if available
        if self.model_type == "ultralytics" and self.yolo_model is not None:
            return self._detect_with_ultralytics(frame)
        elif self.model_type == "opencv" and self.net is not None:
            return self._detect_with_opencv(frame)

        # If no real detection model, return empty list for realistic behavior
        # This way the tracker only shows real objects, not mock boxes
        return []

    def _detect_with_ultralytics(self, frame):
        """Use Ultralytics YOLO for real object detection - optimized for speed"""
        try:
            # Resize frame for faster inference (trade quality for speed)
            height, width = frame.shape[:2]

            # Use smaller input size for phone cameras to boost FPS
            if self.camera_index is not None and self.camera_index > 0:
                target_size = 320  # Much smaller for phone cameras
            else:
                target_size = 416  # Standard size for laptop cameras

            # Maintain aspect ratio
            scale = min(target_size / width, target_size / height)
            new_width = int(width * scale)
            new_height = int(height * scale)

            # Resize frame
            resized_frame = cv2.resize(frame, (new_width, new_height))

            # Run inference with optimizations
            results = self.yolo_model.predict(
                resized_frame,
                verbose=False,
                imgsz=target_size,  # Input size
                conf=0.3,  # Lower confidence for more detections
                iou=0.5,  # IoU threshold
                max_det=20,  # Limit detections for speed
                device="cpu",  # Explicit CPU
            )

            # Process results and scale back to original size
            detections = []
            scale_x = width / new_width
            scale_y = height / new_height

            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for i, box in enumerate(boxes):
                        # Get box coordinates
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        confidence = box.conf[0].cpu().numpy()
                        class_id = int(box.cls[0].cpu().numpy())

                        # Filter by confidence (lower threshold for better detection)
                        if confidence > 0.3:
                            # Scale coordinates back to original frame size
                            x1_scaled = int(x1 * scale_x)
                            y1_scaled = int(y1 * scale_y)
                            x2_scaled = int(x2 * scale_x)
                            y2_scaled = int(y2 * scale_y)

                            detection_obj = {
                                "class_id": int(class_id),
                                "class_name": (
                                    self.classes[class_id]
                                    if class_id < len(self.classes)
                                    else "unknown"
                                ),
                                "confidence": float(confidence),
                                "bbox": [x1_scaled, y1_scaled, x2_scaled, y2_scaled],
                                "center": [
                                    int((x1_scaled + x2_scaled) / 2),
                                    int((y1_scaled + y2_scaled) / 2),
                                ],
                                "area": int(
                                    (x2_scaled - x1_scaled) * (y2_scaled - y1_scaled)
                                ),
                            }
                            detections.append(detection_obj)

            return detections

        except Exception as e:
            print(f"Ultralytics detection failed: {e}")
            return []

    def _detect_with_opencv(self, frame):
        """Use OpenCV DNN for real object detection"""
        height, width = frame.shape[:2]

        try:
            # Create blob from frame
            blob = cv2.dnn.blobFromImage(
                frame, 1 / 255.0, (416, 416), swapRB=True, crop=False
            )
            self.net.setInput(blob)
            outputs = self.net.forward(self.output_layers)

            # Process detections
            detections = []
            for output in outputs:
                for detection in output:
                    scores = detection[5:]
                    class_id = np.argmax(scores)
                    confidence = scores[class_id]

                    if confidence > 0.5:  # Confidence threshold
                        # Get bounding box
                        center_x = int(detection[0] * width)
                        center_y = int(detection[1] * height)
                        w = int(detection[2] * width)
                        h = int(detection[3] * height)

                        x1 = int(center_x - w / 2)
                        y1 = int(center_y - h / 2)
                        x2 = int(center_x + w / 2)
                        y2 = int(center_y + h / 2)

                        detection_obj = {
                            "class_id": int(class_id),
                            "class_name": (
                                self.classes[class_id]
                                if class_id < len(self.classes)
                                else "unknown"
                            ),
                            "confidence": float(confidence),
                            "bbox": [x1, y1, x2, y2],
                            "center": [center_x, center_y],
                            "area": w * h,
                        }
                        detections.append(detection_obj)

            return detections

        except Exception as e:
            print(f"OpenCV detection failed: {e}")
            return []

    def enable_demo_mode(self):
        """Enable demo mode with moving mock objects for demonstration"""
        self._demo_mode = True

    def get_demo_detections(self, frame):
        """Get mock detections for demo purposes only"""
        height, width = frame.shape[:2]

        # Create diverse mock detections for testing different object types
        import time

        t = time.time()

        mock_detections = [
            {
                "class_id": 0,  # person
                "class_name": "person",
                "confidence": 0.85,
                "bbox": [width // 4, height // 4, width // 2, height // 2],
                "center": [width // 3, height // 3],
                "area": (width // 4) * (height // 4),
            },
            {
                "class_id": 2,  # car
                "class_name": "car",
                "confidence": 0.92,
                "bbox": [
                    int(width * 0.1),
                    int(height * 0.6),
                    int(width * 0.4),
                    int(height * 0.9),
                ],
                "center": [int(width * 0.25), int(height * 0.75)],
                "area": int(width * 0.3 * height * 0.3),
            },
            {
                "class_id": 15,  # cat
                "class_name": "cat",
                "confidence": 0.78,
                "bbox": [
                    int(width * 0.6 + 50 * np.sin(t)),
                    int(height * 0.7),
                    int(width * 0.7 + 50 * np.sin(t)),
                    int(height * 0.85),
                ],
                "center": [int(width * 0.65 + 50 * np.sin(t)), int(height * 0.775)],
                "area": int(width * 0.1 * height * 0.15),
            },
            {
                "class_id": 39,  # bottle
                "class_name": "bottle",
                "confidence": 0.67,
                "bbox": [
                    int(width * 0.8),
                    int(height * 0.2),
                    int(width * 0.85),
                    int(height * 0.4),
                ],
                "center": [int(width * 0.825), int(height * 0.3)],
                "area": int(width * 0.05 * height * 0.2),
            },
            {
                "class_id": 56,  # chair
                "class_name": "chair",
                "confidence": 0.81,
                "bbox": [
                    int(width * 0.05),
                    int(height * 0.3),
                    int(width * 0.2),
                    int(height * 0.7),
                ],
                "center": [int(width * 0.125), int(height * 0.5)],
                "area": int(width * 0.15 * height * 0.4),
            },
        ]

        return mock_detections

    def categorize_objects(self, detections):
        """
        Categorize detections by object type

        Args:
            detections (list): List of detection objects

        Returns:
            dict: Objects categorized by type
        """
        categorized = {}
        for category in OBJECT_CATEGORIES.keys():
            categorized[category] = []

        for detection in detections:
            class_id = detection["class_id"]

            # Find which category this class belongs to
            object_category = "other"  # default
            for category, class_ids in OBJECT_CATEGORIES.items():
                if class_id in class_ids:
                    object_category = category
                    break

            # Add category info to detection
            detection["category"] = object_category
            categorized[object_category].append(detection)

        return categorized

    def __del__(self):
        """Cleanup webcam resources"""
        if self.cap is not None:
            self.cap.release()
