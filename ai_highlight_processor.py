"""
AI-Powered Highlight Generation System
Analyzes football game recordings to automatically create highlights
"""

import cv2
import numpy as np
import json
import os
from datetime import datetime, timedelta
import subprocess
from pathlib import Path
import logging
from typing import List, Dict, Tuple, Optional
import torch
from ultralytics import YOLO
import mediapipe as mp
from scipy.signal import find_peaks
from sklearn.cluster import DBSCAN

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FootballHighlightProcessor:
    """
    Main class for processing football videos and generating highlights
    """

    def __init__(self, model_path: str = "yolo11n.pt"):
        """
        Initialize the highlight processor

        Args:
            model_path: Path to YOLO model file
        """
        self.model = YOLO(model_path)
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=1,
            enable_segmentation=False,
            min_detection_confidence=0.5,
        )

        # Event detection thresholds
        self.config = {
            "min_highlight_duration": 10,  # seconds
            "max_highlight_duration": 30,  # seconds
            "activity_threshold": 0.7,
            "goal_detection_threshold": 0.8,
            "celebration_threshold": 0.6,
            "fast_movement_threshold": 50,  # pixels per frame
            "ball_near_goal_threshold": 100,  # pixels
        }

        # Field detection
        self.field_detector = FieldDetector()

        # Action classifiers
        self.action_classifier = ActionClassifier()

    def process_video(
        self, video_path: str, output_dir: str = "highlights"
    ) -> List[Dict]:
        """
        Process a football video and generate highlights

        Args:
            video_path: Path to input video
            output_dir: Directory to save highlights

        Returns:
            List of highlight information dictionaries
        """
        logger.info(f"Processing video: {video_path}")

        # Create output directory
        os.makedirs(output_dir, exist_ok=True)

        # Analyze video
        analysis_data = self.analyze_video(video_path)

        # Detect highlight moments
        highlight_moments = self.detect_highlights(analysis_data)

        # Generate highlight clips
        highlights = []
        for i, moment in enumerate(highlight_moments):
            highlight_info = self.create_highlight_clip(
                video_path, moment, output_dir, i
            )
            if highlight_info:
                highlights.append(highlight_info)

        logger.info(f"Generated {len(highlights)} highlights")
        return highlights

    def analyze_video(self, video_path: str) -> Dict:
        """
        Analyze video frame by frame to extract features

        Args:
            video_path: Path to video file

        Returns:
            Dictionary containing analysis data
        """
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        analysis_data = {
            "fps": fps,
            "total_frames": total_frames,
            "duration": total_frames / fps,
            "frames": [],
            "field_info": None,
        }

        frame_count = 0

        # Process every nth frame for efficiency
        frame_skip = max(1, int(fps // 5))  # Process 5 frames per second

        logger.info(
            f"Analyzing {total_frames} frames (processing every {frame_skip} frames)"
        )

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_count % frame_skip == 0:
                # Analyze this frame
                frame_data = self.analyze_frame(frame, frame_count / fps)
                analysis_data["frames"].append(frame_data)

                # Detect field on first frame
                if analysis_data["field_info"] is None:
                    analysis_data["field_info"] = self.field_detector.detect_field(
                        frame
                    )

            frame_count += 1

            # Progress logging
            if frame_count % (total_frames // 10) == 0:
                progress = (frame_count / total_frames) * 100
                logger.info(f"Analysis progress: {progress:.1f}%")

        cap.release()
        return analysis_data

    def analyze_frame(self, frame: np.ndarray, timestamp: float) -> Dict:
        """
        Analyze a single frame

        Args:
            frame: Video frame
            timestamp: Frame timestamp in seconds

        Returns:
            Frame analysis data
        """
        # YOLO detection
        results = self.model(frame, verbose=False)

        # Extract detections
        detections = []
        for result in results:
            boxes = result.boxes
            if boxes is not None:
                for box in boxes:
                    cls = int(box.cls[0])
                    conf = float(box.conf[0])
                    xyxy = box.xyxy[0].cpu().numpy()

                    detection = {
                        "class": cls,
                        "class_name": self.model.names[cls],
                        "confidence": conf,
                        "bbox": xyxy.tolist(),
                        "center": [(xyxy[0] + xyxy[2]) / 2, (xyxy[1] + xyxy[3]) / 2],
                    }
                    detections.append(detection)

        # Analyze player poses
        pose_data = self.analyze_poses(frame, detections)

        # Calculate frame activity score
        activity_score = self.calculate_activity_score(detections, pose_data)

        # Detect specific events
        events = self.detect_frame_events(detections, pose_data, frame)

        return {
            "timestamp": timestamp,
            "detections": detections,
            "pose_data": pose_data,
            "activity_score": activity_score,
            "events": events,
            "player_count": len([d for d in detections if d["class_name"] == "person"]),
            "ball_detected": any(d["class_name"] == "sports ball" for d in detections),
        }

    def analyze_poses(self, frame: np.ndarray, detections: List[Dict]) -> List[Dict]:
        """
        Analyze player poses using MediaPipe

        Args:
            frame: Video frame
            detections: YOLO detections

        Returns:
            List of pose analysis data
        """
        pose_data = []

        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        for detection in detections:
            if detection["class_name"] == "person":
                # Extract person region
                bbox = detection["bbox"]
                x1, y1, x2, y2 = map(int, bbox)
                person_roi = rgb_frame[y1:y2, x1:x2]

                if person_roi.size > 0:
                    # Analyze pose
                    results = self.pose.process(person_roi)

                    if results.pose_landmarks:
                        # Extract key pose features
                        landmarks = results.pose_landmarks.landmark

                        # Calculate pose features
                        pose_features = self.extract_pose_features(landmarks)

                        pose_data.append(
                            {
                                "detection_id": len(pose_data),
                                "bbox": bbox,
                                "landmarks": [(lm.x, lm.y, lm.z) for lm in landmarks],
                                "features": pose_features,
                            }
                        )

        return pose_data

    def extract_pose_features(self, landmarks) -> Dict:
        """
        Extract meaningful features from pose landmarks

        Args:
            landmarks: MediaPipe pose landmarks

        Returns:
            Dictionary of pose features
        """
        # Key landmark indices
        LEFT_SHOULDER = 11
        RIGHT_SHOULDER = 12
        LEFT_HIP = 23
        RIGHT_HIP = 24
        LEFT_KNEE = 25
        RIGHT_KNEE = 26
        LEFT_ANKLE = 27
        RIGHT_ANKLE = 28

        features = {}

        try:
            # Body orientation
            shoulder_center = (
                (landmarks[LEFT_SHOULDER].x + landmarks[RIGHT_SHOULDER].x) / 2,
                (landmarks[LEFT_SHOULDER].y + landmarks[RIGHT_SHOULDER].y) / 2,
            )
            hip_center = (
                (landmarks[LEFT_HIP].x + landmarks[RIGHT_HIP].x) / 2,
                (landmarks[LEFT_HIP].y + landmarks[RIGHT_HIP].y) / 2,
            )

            # Calculate body lean
            body_lean = abs(shoulder_center[0] - hip_center[0])
            features["body_lean"] = body_lean

            # Leg spread (running/action indicator)
            leg_spread = abs(landmarks[LEFT_ANKLE].x - landmarks[RIGHT_ANKLE].x)
            features["leg_spread"] = leg_spread

            # Knee bend (action intensity)
            left_knee_bend = abs(landmarks[LEFT_KNEE].y - landmarks[LEFT_ANKLE].y)
            right_knee_bend = abs(landmarks[RIGHT_KNEE].y - landmarks[RIGHT_ANKLE].y)
            features["knee_bend"] = (left_knee_bend + right_knee_bend) / 2

            # Action classification
            features["action_type"] = self.classify_action(features)

        except (IndexError, AttributeError):
            # Handle missing landmarks
            features = {
                "body_lean": 0,
                "leg_spread": 0,
                "knee_bend": 0,
                "action_type": "unknown",
            }

        return features

    def classify_action(self, pose_features: Dict) -> str:
        """
        Classify player action based on pose features

        Args:
            pose_features: Extracted pose features

        Returns:
            Action classification string
        """
        body_lean = pose_features.get("body_lean", 0)
        leg_spread = pose_features.get("leg_spread", 0)
        knee_bend = pose_features.get("knee_bend", 0)

        # Simple rule-based classification
        if knee_bend > 0.3 and leg_spread > 0.2:
            return "running"
        elif body_lean > 0.2:
            return "turning"
        elif knee_bend > 0.4:
            return "jumping"
        elif leg_spread < 0.1 and knee_bend < 0.1:
            return "standing"
        else:
            return "walking"

    def calculate_activity_score(
        self, detections: List[Dict], pose_data: List[Dict]
    ) -> float:
        """
        Calculate overall activity score for the frame

        Args:
            detections: YOLO detections
            pose_data: Pose analysis data

        Returns:
            Activity score (0-1)
        """
        score = 0.0

        # Player count contributes to activity
        player_count = len([d for d in detections if d["class_name"] == "person"])
        score += min(player_count / 10, 0.3)  # Max 0.3 for player count

        # Ball detection
        if any(d["class_name"] == "sports ball" for d in detections):
            score += 0.2

        # Pose-based activity
        if pose_data:
            action_scores = {
                "running": 0.8,
                "jumping": 0.9,
                "turning": 0.6,
                "walking": 0.3,
                "standing": 0.1,
                "unknown": 0.2,
            }

            avg_action_score = np.mean(
                [
                    action_scores.get(pose["features"]["action_type"], 0.2)
                    for pose in pose_data
                ]
            )
            score += avg_action_score * 0.5

        return min(score, 1.0)

    def detect_frame_events(
        self, detections: List[Dict], pose_data: List[Dict], frame: np.ndarray
    ) -> List[Dict]:
        """
        Detect specific events in the frame

        Args:
            detections: YOLO detections
            pose_data: Pose analysis data
            frame: Video frame

        Returns:
            List of detected events
        """
        events = []

        # Find ball and players
        ball = None
        players = []

        for detection in detections:
            if detection["class_name"] == "sports ball":
                ball = detection
            elif detection["class_name"] == "person":
                players.append(detection)

        # Goal area detection (simplified)
        if ball:
            ball_x, ball_y = ball["center"]
            frame_width = frame.shape[1]

            # Check if ball is near goal areas (left/right edges)
            if ball_x < frame_width * 0.1 or ball_x > frame_width * 0.9:
                events.append(
                    {
                        "type": "ball_near_goal",
                        "confidence": 0.7,
                        "location": "left" if ball_x < frame_width * 0.5 else "right",
                    }
                )

        # Celebration detection (multiple players with raised arms)
        celebrating_players = 0
        for pose in pose_data:
            if pose["features"]["action_type"] == "jumping":
                celebrating_players += 1

        if celebrating_players >= 2:
            events.append(
                {
                    "type": "celebration",
                    "confidence": min(celebrating_players / 5, 1.0),
                    "player_count": celebrating_players,
                }
            )

        # Fast movement detection
        running_players = len(
            [pose for pose in pose_data if pose["features"]["action_type"] == "running"]
        )

        if running_players >= 3:
            events.append(
                {
                    "type": "fast_movement",
                    "confidence": min(running_players / 8, 1.0),
                    "player_count": running_players,
                }
            )

        return events

    def detect_highlights(self, analysis_data: Dict) -> List[Dict]:
        """
        Detect highlight moments from analysis data

        Args:
            analysis_data: Video analysis data

        Returns:
            List of highlight moments
        """
        frames = analysis_data["frames"]
        fps = analysis_data["fps"]

        # Extract activity scores
        activity_scores = [frame["activity_score"] for frame in frames]
        timestamps = [frame["timestamp"] for frame in frames]

        # Find peaks in activity
        peaks, properties = find_peaks(
            activity_scores,
            height=self.config["activity_threshold"],
            distance=int(fps * 5),  # Minimum 5 seconds between peaks
        )

        highlight_moments = []

        for peak_idx in peaks:
            peak_timestamp = timestamps[peak_idx]
            peak_score = activity_scores[peak_idx]

            # Analyze events around the peak
            start_idx = max(0, peak_idx - int(fps * 2))
            end_idx = min(len(frames), peak_idx + int(fps * 2))

            peak_events = []
            for i in range(start_idx, end_idx):
                peak_events.extend(frames[i]["events"])

            # Classify highlight type
            highlight_type = self.classify_highlight(peak_events, peak_score)

            # Determine highlight duration
            duration = self.calculate_highlight_duration(
                frames, peak_idx, highlight_type
            )

            highlight_moments.append(
                {
                    "start_time": max(0, peak_timestamp - duration / 2),
                    "end_time": min(
                        analysis_data["duration"], peak_timestamp + duration / 2
                    ),
                    "peak_timestamp": peak_timestamp,
                    "score": peak_score,
                    "type": highlight_type,
                    "events": peak_events,
                    "duration": duration,
                }
            )

        # Sort by score and limit count
        highlight_moments.sort(key=lambda x: x["score"], reverse=True)
        return highlight_moments[:10]  # Top 10 highlights

    def classify_highlight(self, events: List[Dict], activity_score: float) -> str:
        """
        Classify the type of highlight based on events

        Args:
            events: List of events
            activity_score: Activity score

        Returns:
            Highlight type string
        """
        event_types = [event["type"] for event in events]

        if "ball_near_goal" in event_types:
            if "celebration" in event_types:
                return "goal"
            else:
                return "goal_attempt"
        elif "celebration" in event_types:
            return "celebration"
        elif "fast_movement" in event_types and activity_score > 0.8:
            return "fast_action"
        elif activity_score > 0.7:
            return "high_activity"
        else:
            return "general"

    def calculate_highlight_duration(
        self, frames: List[Dict], peak_idx: int, highlight_type: str
    ) -> float:
        """
        Calculate optimal duration for highlight

        Args:
            frames: Frame analysis data
            peak_idx: Peak frame index
            highlight_type: Type of highlight

        Returns:
            Duration in seconds
        """
        base_durations = {
            "goal": 20,
            "goal_attempt": 15,
            "celebration": 10,
            "fast_action": 15,
            "high_activity": 12,
            "general": 10,
        }

        base_duration = base_durations.get(highlight_type, 10)

        # Extend duration based on surrounding activity
        activity_window = 30  # frames to check around peak
        start_check = max(0, peak_idx - activity_window)
        end_check = min(len(frames), peak_idx + activity_window)

        high_activity_frames = sum(
            1
            for i in range(start_check, end_check)
            if frames[i]["activity_score"] > 0.5
        )

        # Extend duration if there's sustained activity
        if high_activity_frames > activity_window * 0.7:
            base_duration += 5

        return min(
            max(base_duration, self.config["min_highlight_duration"]),
            self.config["max_highlight_duration"],
        )

    def create_highlight_clip(
        self, video_path: str, highlight_moment: Dict, output_dir: str, clip_index: int
    ) -> Optional[Dict]:
        """
        Create a highlight video clip

        Args:
            video_path: Source video path
            highlight_moment: Highlight moment data
            output_dir: Output directory
            clip_index: Index for naming

        Returns:
            Highlight information dictionary
        """
        start_time = highlight_moment["start_time"]
        end_time = highlight_moment["end_time"]
        duration = end_time - start_time

        # Generate output filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = (
            f"highlight_{clip_index}_{highlight_moment['type']}_{timestamp}.mp4"
        )
        output_path = os.path.join(output_dir, output_filename)

        # Create thumbnail filename
        thumbnail_filename = output_filename.replace(".mp4", "_thumb.jpg")
        thumbnail_path = os.path.join(output_dir, thumbnail_filename)

        try:
            # Extract video clip using ffmpeg
            cmd = [
                "ffmpeg",
                "-i",
                video_path,
                "-ss",
                str(start_time),
                "-t",
                str(duration),
                "-c:v",
                "libx264",
                "-c:a",
                "aac",
                "-preset",
                "fast",
                "-crf",
                "23",
                "-y",
                output_path,
            ]

            subprocess.run(cmd, check=True, capture_output=True)

            # Create thumbnail
            thumbnail_time = start_time + duration / 2
            thumb_cmd = [
                "ffmpeg",
                "-i",
                video_path,
                "-ss",
                str(thumbnail_time),
                "-vframes",
                "1",
                "-q:v",
                "2",
                "-y",
                thumbnail_path,
            ]

            subprocess.run(thumb_cmd, check=True, capture_output=True)

            # Generate title and description
            title = self.generate_highlight_title(highlight_moment)
            description = self.generate_highlight_description(highlight_moment)
            tags = self.generate_highlight_tags(highlight_moment)

            return {
                "title": title,
                "description": description,
                "video_path": output_path,
                "thumbnail_path": thumbnail_path,
                "start_timestamp": start_time,
                "end_timestamp": end_time,
                "duration": duration,
                "type": highlight_moment["type"],
                "score": highlight_moment["score"],
                "tags": tags,
                "events": highlight_moment["events"],
            }

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to create highlight clip: {e}")
            return None

    def generate_highlight_title(self, highlight_moment: Dict) -> str:
        """Generate a title for the highlight"""
        type_titles = {
            "goal": "Goal!",
            "goal_attempt": "Goal Attempt",
            "celebration": "Team Celebration",
            "fast_action": "Fast-Paced Action",
            "high_activity": "Intense Moment",
            "general": "Game Highlight",
        }

        base_title = type_titles.get(highlight_moment["type"], "Highlight")

        # Add time context
        minutes = int(highlight_moment["peak_timestamp"] // 60)
        return f"{base_title} - {minutes}m"

    def generate_highlight_description(self, highlight_moment: Dict) -> str:
        """Generate a description for the highlight"""
        descriptions = {
            "goal": "An exciting goal-scoring moment with high activity around the goal area.",
            "goal_attempt": "A goal-scoring opportunity with the ball near the goal.",
            "celebration": "Players celebrating an important moment in the game.",
            "fast_action": "Fast-paced action with multiple players in motion.",
            "high_activity": "A moment of high activity and intensity.",
            "general": "An interesting moment from the game.",
        }

        return descriptions.get(highlight_moment["type"], "A highlight from the game.")

    def generate_highlight_tags(self, highlight_moment: Dict) -> List[str]:
        """Generate tags for the highlight"""
        tags = [highlight_moment["type"]]

        # Add event-based tags
        for event in highlight_moment["events"]:
            event_type = event["type"]
            if event_type not in tags:
                tags.append(event_type)

        # Add general tags
        if highlight_moment["score"] > 0.8:
            tags.append("exciting")

        return tags


class FieldDetector:
    """Detects and analyzes the football field"""

    def detect_field(self, frame: np.ndarray) -> Dict:
        """
        Detect field boundaries and key areas

        Args:
            frame: Video frame

        Returns:
            Field information dictionary
        """
        # Convert to HSV for better grass detection
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # Define green color range for grass
        lower_green = np.array([35, 40, 40])
        upper_green = np.array([85, 255, 255])

        # Create mask for green areas
        mask = cv2.inRange(hsv, lower_green, upper_green)

        # Find contours
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if contours:
            # Find largest contour (likely the field)
            largest_contour = max(contours, key=cv2.contourArea)

            # Get bounding rectangle
            x, y, w, h = cv2.boundingRect(largest_contour)

            return {
                "field_bounds": [x, y, x + w, y + h],
                "field_area": w * h,
                "detected": True,
            }

        return {"detected": False}


class ActionClassifier:
    """Classifies player actions and game events"""

    def __init__(self):
        self.action_history = []

    def classify_sequence(self, pose_sequence: List[Dict]) -> str:
        """
        Classify a sequence of poses as an action

        Args:
            pose_sequence: Sequence of pose data

        Returns:
            Action classification
        """
        if len(pose_sequence) < 3:
            return "unknown"

        # Analyze movement patterns
        movements = []
        for i in range(1, len(pose_sequence)):
            prev_pose = pose_sequence[i - 1]
            curr_pose = pose_sequence[i]

            # Calculate movement features
            movement = self.calculate_movement(prev_pose, curr_pose)
            movements.append(movement)

        # Classify based on movement patterns
        return self.classify_movement_pattern(movements)

    def calculate_movement(self, pose1: Dict, pose2: Dict) -> Dict:
        """Calculate movement between two poses"""
        # Simplified movement calculation
        return {
            "speed": np.random.random(),  # Placeholder
            "direction": np.random.random() * 360,  # Placeholder
            "acceleration": np.random.random(),  # Placeholder
        }

    def classify_movement_pattern(self, movements: List[Dict]) -> str:
        """Classify movement pattern"""
        # Simplified classification
        avg_speed = np.mean([m["speed"] for m in movements])

        if avg_speed > 0.7:
            return "running"
        elif avg_speed > 0.4:
            return "walking"
        else:
            return "standing"


# Example usage
if __name__ == "__main__":
    processor = FootballHighlightProcessor()

    # Process a video file
    video_path = "sample_game.mp4"
    if os.path.exists(video_path):
        highlights = processor.process_video(video_path)

        print(f"Generated {len(highlights)} highlights:")
        for i, highlight in enumerate(highlights):
            print(
                f"{i+1}. {highlight['title']} ({highlight['duration']:.1f}s) - Score: {highlight['score']:.2f}"
            )
    else:
        print("Sample video not found. Please provide a video file to process.")
