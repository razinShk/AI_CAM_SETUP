# detection.py
import cv2
import numpy as np
from ultralytics import YOLO

class FootballDetector:
    def __init__(self):
        self.model = YOLO('yolo11n.pt')
    
    def detect(self, frame):
        results = self.model(frame)
        return results

class OfflineDetector:
    def __init__(self):
        self.model = YOLO('yolo11n.pt')
    
    def detect(self, frame):
        results = self.model(frame)
        return results