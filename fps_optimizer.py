#!/usr/bin/env python3
"""
FPS Optimization Tools for Object Tracking
"""

import cv2
import numpy as np
import time
import threading
from queue import Queue
import logging
from concurrent.futures import ThreadPoolExecutor


class FrameSkipper:
    """Skip frames to increase effective FPS"""

    def __init__(self, skip_frames=2):
        """
        Args:
            skip_frames: Process every Nth frame (2 = process every 2nd frame)
        """
        self.skip_frames = skip_frames
        self.frame_counter = 0
        self.last_detections = []

    def should_process(self):
        """Check if current frame should be processed"""
        self.frame_counter += 1
        return (self.frame_counter % self.skip_frames) == 0

    def get_detections(self, new_detections=None):
        """Get detections - either new or cached"""
        if new_detections is not None:
            self.last_detections = new_detections
        return self.last_detections


class AsyncDetector:
    """Asynchronous detection to decouple frame capture from inference"""

    def __init__(self, detector, max_queue_size=3):
        self.detector = detector
        self.frame_queue = Queue(maxsize=max_queue_size)
        self.result_queue = Queue(maxsize=max_queue_size)
        self.processing = True

        # Start detection thread
        self.detection_thread = threading.Thread(target=self._detection_worker)
        self.detection_thread.daemon = True
        self.detection_thread.start()

    def _detection_worker(self):
        """Background thread for processing detections"""
        while self.processing:
            try:
                if not self.frame_queue.empty():
                    frame = self.frame_queue.get(timeout=0.1)
                    detections = self.detector.detect_objects(frame)

                    # Put result, drop old results if queue is full
                    if self.result_queue.full():
                        try:
                            self.result_queue.get_nowait()
                        except:
                            pass

                    self.result_queue.put(detections)
            except Exception as e:
                print(f"Detection thread error: {e}")

    def add_frame(self, frame):
        """Add frame for processing (non-blocking)"""
        if not self.frame_queue.full():
            self.frame_queue.put(frame)

    def get_latest_detections(self):
        """Get latest detections (non-blocking)"""
        latest = []
        while not self.result_queue.empty():
            try:
                latest = self.result_queue.get_nowait()
            except:
                break
        return latest

    def stop(self):
        """Stop the detection thread"""
        self.processing = False
        if self.detection_thread.is_alive():
            self.detection_thread.join()


class FrameResizer:
    """Resize frames for faster processing"""

    def __init__(self, target_width=416, target_height=416):
        self.target_width = target_width
        self.target_height = target_height

    def resize_for_detection(self, frame):
        """Resize frame for detection (smaller = faster)"""
        return cv2.resize(frame, (self.target_width, self.target_height))

    def scale_detections(self, detections, original_shape, resized_shape):
        """Scale detection coordinates back to original frame size"""
        orig_h, orig_w = original_shape[:2]
        resized_h, resized_w = resized_shape[:2]

        scale_x = orig_w / resized_w
        scale_y = orig_h / resized_h

        scaled_detections = []
        for det in detections:
            scaled_det = det.copy()

            # Scale bounding box
            x1, y1, x2, y2 = det["bbox"]
            scaled_det["bbox"] = [
                int(x1 * scale_x),
                int(y1 * scale_y),
                int(x2 * scale_x),
                int(y2 * scale_y),
            ]

            # Scale center
            cx, cy = det["center"]
            scaled_det["center"] = [int(cx * scale_x), int(cy * scale_y)]

            # Scale area
            scaled_det["area"] = int(det["area"] * scale_x * scale_y)

            scaled_detections.append(scaled_det)

        return scaled_detections


class OptimizedDetector:
    """Optimized detector combining multiple performance improvements"""

    def __init__(self, base_detector, camera_index=None):
        self.base_detector = base_detector
        self.camera_index = camera_index

        # Optimization components
        self.frame_skipper = FrameSkipper(skip_frames=2)  # Process every 2nd frame
        self.frame_resizer = FrameResizer(
            target_width=320, target_height=320
        )  # Smaller for speed
        self.async_detector = AsyncDetector(self)

        # Phone camera optimizations
        self.phone_camera_mode = camera_index is not None and camera_index > 0
        if self.phone_camera_mode:
            print("📱 Phone camera detected - enabling optimizations:")
            print("  ✅ Frame skipping (2x speedup)")
            print("  ✅ Reduced resolution processing")
            print("  ✅ Async detection")

    def detect_objects(self, frame):
        """Optimized detection with frame skipping and resizing"""
        # For async processing, use base detector directly
        if hasattr(self, "_async_mode"):
            resized_frame = self.frame_resizer.resize_for_detection(frame)
            detections = self.base_detector.detect_objects(resized_frame)
            return self.frame_resizer.scale_detections(
                detections, frame.shape, resized_frame.shape
            )

        # Check if we should process this frame
        if not self.frame_skipper.should_process():
            return self.frame_skipper.get_detections()

        # Resize frame for faster processing
        resized_frame = self.frame_resizer.resize_for_detection(frame)

        # Run detection on smaller frame
        detections = self.base_detector.detect_objects(resized_frame)

        # Scale detections back to original size
        scaled_detections = self.frame_resizer.scale_detections(
            detections, frame.shape, resized_frame.shape
        )

        # Cache results
        self.frame_skipper.get_detections(scaled_detections)

        return scaled_detections

    def enable_async_mode(self):
        """Enable asynchronous detection mode"""
        self._async_mode = True
        self.async_detector = AsyncDetector(self)

    def add_frame_async(self, frame):
        """Add frame for async processing"""
        if hasattr(self, "async_detector"):
            self.async_detector.add_frame(frame)

    def get_async_detections(self):
        """Get latest async detections"""
        if hasattr(self, "async_detector"):
            return self.async_detector.get_latest_detections()
        return []

    def get_frame(self):
        """Get frame from base detector"""
        return self.base_detector.get_frame()

    def categorize_objects(self, detections):
        """Categorize objects using base detector"""
        return self.base_detector.categorize_objects(detections)

    def enable_demo_mode(self):
        """Enable demo mode"""
        if hasattr(self.base_detector, "enable_demo_mode"):
            self.base_detector.enable_demo_mode()

    def get_demo_detections(self, frame):
        """Get demo detections"""
        if hasattr(self.base_detector, "get_demo_detections"):
            return self.base_detector.get_demo_detections(frame)
        return []


class FPSCounter:
    """Accurate FPS counter"""

    def __init__(self, window_size=30):
        self.window_size = window_size
        self.frame_times = []
        self.last_time = time.time()

    def tick(self):
        """Record a frame"""
        current_time = time.time()
        self.frame_times.append(current_time - self.last_time)
        self.last_time = current_time

        # Keep only recent frames
        if len(self.frame_times) > self.window_size:
            self.frame_times.pop(0)

    def get_fps(self):
        """Get current FPS"""
        if len(self.frame_times) < 2:
            return 0.0

        avg_frame_time = sum(self.frame_times) / len(self.frame_times)
        return 1.0 / avg_frame_time if avg_frame_time > 0 else 0.0


def optimize_yolo_model(model):
    """Apply YOLO-specific optimizations"""
    if hasattr(model, "yolo_model"):
        # Set to fastest inference mode
        model.yolo_model.overrides["verbose"] = False
        model.yolo_model.overrides["device"] = "cpu"  # Explicit CPU

        # Reduce precision if possible
        try:
            import torch

            if hasattr(model.yolo_model.model, "half"):
                model.yolo_model.model.half()  # FP16 for speed
                print("✅ Enabled FP16 precision for 2x speedup")
        except:
            pass

    return model


def create_lightweight_tracker():
    """Create a lightweight tracker for better FPS"""
    from tracking import CentroidTracker

    # Lighter tracking parameters
    return CentroidTracker(
        max_disappeared=10,  # Shorter memory
        max_distance=50,  # Smaller search area
    )


def benchmark_fps(detector, duration=10):
    """Benchmark detector FPS"""
    print(f"🔬 Benchmarking detector for {duration} seconds...")

    fps_counter = FPSCounter()
    start_time = time.time()
    frame_count = 0

    while time.time() - start_time < duration:
        frame = detector.get_frame()
        if frame is not None:
            detections = detector.detect_objects(frame)
            fps_counter.tick()
            frame_count += 1

            if frame_count % 30 == 0:
                current_fps = fps_counter.get_fps()
                print(f"Current FPS: {current_fps:.1f}")

    final_fps = fps_counter.get_fps()
    print(f"📊 Benchmark Results:")
    print(f"   Average FPS: {final_fps:.2f}")
    print(f"   Total frames: {frame_count}")

    return final_fps


if __name__ == "__main__":
    # Test optimizations
    from detection import OfflineDetector

    print("🚀 Testing FPS Optimizations")
    print("=" * 40)

    # Create base detector
    base_detector = OfflineDetector(camera_index=0)

    print("📊 Benchmarking base detector...")
    base_fps = benchmark_fps(base_detector, duration=5)

    print("\n🔧 Testing optimized detector...")
    optimized_detector = OptimizedDetector(base_detector, camera_index=0)
    optimized_fps = benchmark_fps(optimized_detector, duration=5)

    improvement = (optimized_fps / base_fps) if base_fps > 0 else 0
    print(f"\n🎯 FPS Improvement: {improvement:.2f}x faster!")
