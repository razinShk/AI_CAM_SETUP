"""
Multi-Object Tracking for SportsCam
Simplified tracking implementation for laptop testing
"""

import cv2
import numpy as np
from collections import defaultdict


class MultiObjectTracker:
    def __init__(self, max_disappeared=30, max_distance=50):
        self.next_object_id = 0
        self.objects = {}
        self.disappeared = {}
        self.max_disappeared = max_disappeared
        self.max_distance = max_distance

    def register(self, centroid):
        """Register a new object"""
        self.objects[self.next_object_id] = centroid
        self.disappeared[self.next_object_id] = 0
        self.next_object_id += 1

    def deregister(self, object_id):
        """Deregister an object"""
        del self.objects[object_id]
        del self.disappeared[object_id]

    def update(self, rects):
        """Update object tracking"""
        if len(rects) == 0:
            # Mark all objects as disappeared
            for object_id in list(self.disappeared.keys()):
                self.disappeared[object_id] += 1
                if self.disappeared[object_id] > self.max_disappeared:
                    self.deregister(object_id)
            return self.objects

        # Compute centroids
        input_centroids = np.zeros((len(rects), 2), dtype="int")
        for i, (x, y, w, h) in enumerate(rects):
            cx = int(x + w / 2.0)
            cy = int(y + h / 2.0)
            input_centroids[i] = (cx, cy)

        # If no existing objects, register all
        if len(self.objects) == 0:
            for i in range(len(input_centroids)):
                self.register(input_centroids[i])
        else:
            # Match existing objects to new centroids
            object_centroids = list(self.objects.values())
            D = np.linalg.norm(
                np.array(object_centroids)[:, np.newaxis] - input_centroids, axis=2
            )
            rows = D.min(axis=1).argsort()
            cols = D.argmin(axis=1)[rows]

            used_row_indices = set()
            used_col_indices = set()

            for row, col in zip(rows, cols):
                if row in used_row_indices or col in used_col_indices:
                    continue

                if D[row, col] > self.max_distance:
                    continue

                object_id = list(self.objects.keys())[row]
                self.objects[object_id] = input_centroids[col]
                self.disappeared[object_id] = 0

                used_row_indices.add(row)
                used_col_indices.add(col)

            # Handle unmatched objects
            unused_row_indices = set(range(0, D.shape[0])).difference(used_row_indices)
            unused_col_indices = set(range(0, D.shape[1])).difference(used_col_indices)

            # If more objects than detections, mark as disappeared
            if D.shape[0] >= D.shape[1]:
                for row in unused_row_indices:
                    object_id = list(self.objects.keys())[row]
                    self.disappeared[object_id] += 1

                    if self.disappeared[object_id] > self.max_disappeared:
                        self.deregister(object_id)
            else:
                # Register new objects
                for col in unused_col_indices:
                    self.register(input_centroids[col])

        return self.objects
