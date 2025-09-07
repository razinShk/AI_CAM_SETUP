"""
Object tracking module for football players and ball
"""

import cv2
import numpy as np
from scipy.spatial import distance as dist
from collections import OrderedDict, deque
from config import TRACKING, COLORS, CATEGORY_COLORS, OBJECT_CATEGORIES
import logging


class CentroidTracker:
    """
    Centroid-based object tracker for football players and ball
    """

    def __init__(
        self,
        max_disappeared=TRACKING["max_disappeared"],
        max_distance=TRACKING["max_distance"],
    ):
        """
        Initialize the centroid tracker

        Args:
            max_disappeared (int): Maximum number of consecutive frames an object can disappear
            max_distance (float): Maximum distance between centroids for object association
        """
        # Initialize the next unique object ID and dictionaries to track objects
        self.next_object_id = 0
        self.objects = OrderedDict()
        self.disappeared = OrderedDict()
        self.max_disappeared = max_disappeared
        self.max_distance = max_distance

        # Store object trails for visualization
        self.trails = OrderedDict()
        self.trail_length = TRACKING["trail_length"]

        # Logger
        self.logger = logging.getLogger(__name__)

    def register(self, centroid, detection_info):
        """
        Register a new object with a unique ID

        Args:
            centroid (tuple): (x, y) coordinates of object center
            detection_info (dict): Additional detection information
        """
        self.objects[self.next_object_id] = {
            "centroid": centroid,
            "bbox": detection_info.get("bbox", [0, 0, 0, 0]),
            "class_name": detection_info.get("class_name", "unknown"),
            "confidence": detection_info.get("confidence", 0.0),
            "area": detection_info.get("area", 0),
        }
        self.disappeared[self.next_object_id] = 0
        self.trails[self.next_object_id] = deque(maxlen=self.trail_length)
        self.trails[self.next_object_id].append(centroid)

        self.next_object_id += 1

    def deregister(self, object_id):
        """
        Remove an object from tracking

        Args:
            object_id (int): ID of object to remove
        """
        del self.objects[object_id]
        del self.disappeared[object_id]
        del self.trails[object_id]

    def update(self, detections):
        """
        Update tracked objects with new detections

        Args:
            detections (list): List of detection dictionaries

        Returns:
            dict: Updated tracked objects
        """
        # If no detections, mark all objects as disappeared
        if len(detections) == 0:
            for object_id in list(self.disappeared.keys()):
                self.disappeared[object_id] += 1

                # Remove objects that have been missing too long
                if self.disappeared[object_id] > self.max_disappeared:
                    self.deregister(object_id)

            return self.objects

        # Initialize array of input centroids for current frame
        input_centroids = []
        detection_info = []

        for detection in detections:
            cx, cy = detection["center"]
            input_centroids.append((cx, cy))
            detection_info.append(detection)

        # If no existing objects, register all detections as new objects
        if len(self.objects) == 0:
            for i, centroid in enumerate(input_centroids):
                self.register(centroid, detection_info[i])

        # Otherwise, try to match existing objects to new detections
        else:
            # Get existing object centroids
            object_centroids = [obj["centroid"] for obj in self.objects.values()]

            # Compute distance matrix between existing and new centroids
            D = dist.cdist(np.array(object_centroids), input_centroids)

            # Find minimum values and sort by distance
            rows = D.min(axis=1).argsort()
            cols = D.argmin(axis=1)[rows]

            # Keep track of used row and column indices
            used_row_indices = set()
            used_col_indices = set()

            # Loop over the combination of (row, column) index tuples
            for row, col in zip(rows, cols):
                # Ignore if already used or distance too large
                if row in used_row_indices or col in used_col_indices:
                    continue

                if D[row, col] > self.max_distance:
                    continue

                # Update the object with new information
                object_id = list(self.objects.keys())[row]
                self.objects[object_id] = {
                    "centroid": input_centroids[col],
                    "bbox": detection_info[col]["bbox"],
                    "class_name": detection_info[col]["class_name"],
                    "confidence": detection_info[col]["confidence"],
                    "area": detection_info[col]["area"],
                }
                self.disappeared[object_id] = 0

                # Update trail
                self.trails[object_id].append(input_centroids[col])

                # Mark indices as used
                used_row_indices.add(row)
                used_col_indices.add(col)

            # Handle unmatched detections and objects
            unused_row_indices = set(range(0, D.shape[0])).difference(used_row_indices)
            unused_col_indices = set(range(0, D.shape[1])).difference(used_col_indices)

            # If more objects than detections, mark missing objects as disappeared
            if D.shape[0] >= D.shape[1]:
                for row in unused_row_indices:
                    object_id = list(self.objects.keys())[row]
                    self.disappeared[object_id] += 1

                    # Remove if disappeared too long
                    if self.disappeared[object_id] > self.max_disappeared:
                        self.deregister(object_id)

            # Register new objects for unmatched detections
            else:
                for col in unused_col_indices:
                    self.register(input_centroids[col], detection_info[col])

        return self.objects


class MultiObjectTracker:
    """
    High-level tracker for multiple object categories
    """

    def __init__(self):
        """Initialize tracker with separate trackers for each object category"""
        # Create separate trackers for each category
        self.trackers = {}
        for category in OBJECT_CATEGORIES.keys():
            # Different tracking parameters for different object types
            if category == "vehicles":
                # Vehicles move faster, need larger distance threshold
                self.trackers[category] = CentroidTracker(max_disappeared=20, max_distance=120)
            elif category == "animals":
                # Animals can move unpredictably
                self.trackers[category] = CentroidTracker(max_disappeared=15, max_distance=100)
            else:
                # Default parameters for other objects
                self.trackers[category] = CentroidTracker(max_disappeared=30, max_distance=80)

        # Statistics
        self.frame_count = 0
        self.object_count_history = {category: deque(maxlen=30) for category in OBJECT_CATEGORIES.keys()}
        self.total_objects_detected = 0

        self.logger = logging.getLogger(__name__)

    def update(self, categorized_detections):
        """
        Update tracking for all object categories

        Args:
            categorized_detections (dict): Dictionary with objects categorized by type

        Returns:
            dict: Tracking results with updated object information
        """
        self.frame_count += 1

        # Update tracking for each category
        tracked_objects = {}
        total_objects = 0
        
        for category, detections in categorized_detections.items():
            if category in self.trackers:
                tracked_objects[category] = self.trackers[category].update(detections)
                
                # Update statistics
                count = len(tracked_objects[category])
                self.object_count_history[category].append(count)
                total_objects += count

        self.total_objects_detected = total_objects

        return {
            "objects": tracked_objects,
            "frame_count": self.frame_count,
            "stats": self._get_stats(),
        }

    def _get_stats(self):
        """Get tracking statistics"""
        stats = {
            "total_frames": self.frame_count,
            "total_objects": self.total_objects_detected,
        }
        
        # Add average counts for each category
        for category, history in self.object_count_history.items():
            avg_count = np.mean(history) if history else 0
            stats[f"avg_{category}"] = avg_count
            
        return stats

    def draw_tracking_info(self, frame, tracking_results):
        """
        Draw tracking information on frame

        Args:
            frame (np.ndarray): Input frame
            tracking_results (dict): Results from update method

        Returns:
            np.ndarray: Frame with tracking visualization
        """
        height, width = frame.shape[:2]

        # Draw objects from each category
        for category, objects in tracking_results["objects"].items():
            if category in CATEGORY_COLORS:
                color = CATEGORY_COLORS[category]
            else:
                color = COLORS["bbox"]
                
            for object_id, obj_info in objects.items():
                # Use category name as label prefix
                label_prefix = category.title()
                self._draw_object(frame, object_id, obj_info, color, label_prefix)
                
                # Draw trail if tracker exists
                if category in self.trackers and object_id in self.trackers[category].trails:
                    self._draw_trail(frame, self.trackers[category].trails[object_id], color)

        # Draw statistics
        self._draw_stats(frame, tracking_results["stats"])

        return frame

    def _draw_object(self, frame, object_id, obj_info, color, label_prefix):
        """Draw bounding box and label for tracked object"""
        bbox = obj_info["bbox"]
        centroid = obj_info["centroid"]
        confidence = obj_info["confidence"]

        # Draw bounding box
        cv2.rectangle(frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), color, 2)

        # Draw centroid
        cv2.circle(frame, centroid, 5, color, -1)

        # Draw label
        label = f"{label_prefix} {object_id}: {confidence:.2f}"
        label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]

        # Background for text
        cv2.rectangle(
            frame,
            (bbox[0], bbox[1] - label_size[1] - 10),
            (bbox[0] + label_size[0], bbox[1]),
            color,
            -1,
        )

        # Text
        cv2.putText(
            frame,
            label,
            (bbox[0], bbox[1] - 5),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            COLORS["text"],
            2,
        )

    def _draw_trail(self, frame, trail, color):
        """Draw movement trail for object"""
        if len(trail) < 2:
            return

        # Draw lines connecting trail points
        points = list(trail)
        for i in range(1, len(points)):
            # Fade older points
            alpha = i / len(points)
            trail_color = tuple(int(c * alpha) for c in color)

            cv2.line(frame, points[i - 1], points[i], trail_color, 2)

    def _draw_stats(self, frame, stats):
        """Draw tracking statistics on frame"""
        height, width = frame.shape[:2]

        # Create semi-transparent overlay for stats
        overlay = frame.copy()
        cv2.rectangle(overlay, (10, 10), (350, 200), COLORS["background"], -1)
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)

        # Draw stats text
        stats_text = [
            f"Frame: {stats['total_frames']}",
            f"Total Objects: {stats['total_objects']}",
        ]
        
        # Add category counts (only non-zero averages)
        for category in OBJECT_CATEGORIES.keys():
            avg_key = f"avg_{category}"
            if avg_key in stats and stats[avg_key] > 0:
                stats_text.append(f"{category.title()}: {stats[avg_key]:.1f}")

        for i, text in enumerate(stats_text):
            y_pos = 35 + i * 20
            cv2.putText(
                frame,
                text,
                (20, y_pos),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                COLORS["text"],
                1,
            )

    def get_object_positions(self, category=None):
        """Get current positions of tracked objects"""
        if category:
            # Return positions for specific category
            if category in self.trackers:
                return {
                    obj_id: obj_info["centroid"]
                    for obj_id, obj_info in self.trackers[category].objects.items()
                }
            return {}
        else:
            # Return all positions organized by category
            all_positions = {}
            for cat, tracker in self.trackers.items():
                all_positions[cat] = {
                    obj_id: obj_info["centroid"]
                    for obj_id, obj_info in tracker.objects.items()
                }
            return all_positions

    def get_object_count(self, category=None):
        """Get current count of tracked objects"""
        if category:
            return len(self.trackers[category].objects) if category in self.trackers else 0
        else:
            return {cat: len(tracker.objects) for cat, tracker in self.trackers.items()}

    def reset(self):
        """Reset all tracking data"""
        # Reset all trackers
        for category in OBJECT_CATEGORIES.keys():
            if category == "vehicles":
                self.trackers[category] = CentroidTracker(max_disappeared=20, max_distance=120)
            elif category == "animals":
                self.trackers[category] = CentroidTracker(max_disappeared=15, max_distance=100)
            else:
                self.trackers[category] = CentroidTracker(max_disappeared=30, max_distance=80)
        
        self.frame_count = 0
        self.total_objects_detected = 0
        
        # Clear statistics
        for category in OBJECT_CATEGORIES.keys():
            self.object_count_history[category].clear()
            
        self.logger.info("Multi-object tracking reset")
