"""
Enhanced Football Tracker for Server Integration
Provides AI tracking capabilities that can be used by the camera server
"""

import cv2
import numpy as np
import time
import json
from datetime import datetime
import threading
import queue
from pathlib import Path

# Import existing modules
from detection import FootballDetector, OfflineDetector
from tracking import MultiObjectTracker
from config import MODELS, OBJECT_CATEGORIES


class FootballTracker:
    """
    Enhanced football tracker for server integration
    """

    def __init__(self, model_name="yolo11n", confidence_threshold=0.5, use_imx500=True):
        self.model_name = model_name
        self.confidence_threshold = confidence_threshold
        self.use_imx500 = use_imx500

        # Initialize detector
        if use_imx500:
            self.detector = FootballDetector(
                model_name=model_name, confidence_threshold=confidence_threshold
            )
        else:
            self.detector = OfflineDetector()

        # Initialize tracker
        self.tracker = MultiObjectTracker()

        # Tracking state
        self.frame_count = 0
        self.start_time = time.time()
        self.fps_counter = 0
        self.fps_start_time = time.time()
        self.current_fps = 0

        # Event detection
        self.event_detector = FootballEventDetector()

        # Statistics
        self.stats = {
            "total_frames": 0,
            "total_detections": 0,
            "player_count": 0,
            "ball_detections": 0,
            "events": [],
        }

    def process_frame(self, frame):
        """
        Process a single frame and return detection/tracking results

        Args:
            frame: Input frame (numpy array)

        Returns:
            dict: Detection and tracking results
        """
        self.frame_count += 1
        current_time = time.time()

        # Run detection
        detections = self.detector.detect(frame)

        # Update tracker
        tracked_objects = self.tracker.update(detections)

        # Detect events
        events = self.event_detector.detect_events(tracked_objects, frame)

        # Update statistics
        self.update_stats(detections, tracked_objects, events)

        # Calculate FPS
        self.fps_counter += 1
        if current_time - self.fps_start_time >= 1.0:
            self.current_fps = self.fps_counter / (current_time - self.fps_start_time)
            self.fps_counter = 0
            self.fps_start_time = current_time

        return {
            "frame_number": self.frame_count,
            "timestamp": current_time,
            "fps": self.current_fps,
            "detections": detections,
            "tracked_objects": tracked_objects,
            "events": events,
            "stats": self.stats.copy(),
        }

    def update_stats(self, detections, tracked_objects, events):
        """Update tracking statistics"""
        self.stats["total_frames"] = self.frame_count
        self.stats["total_detections"] += len(detections)

        # Count players and balls
        players = [obj for obj in tracked_objects if obj.get("class_name") == "person"]
        balls = [
            obj for obj in tracked_objects if obj.get("class_name") == "sports ball"
        ]

        self.stats["player_count"] = len(players)
        self.stats["ball_detections"] += len(balls)

        # Add events
        self.stats["events"].extend(events)

        # Keep only recent events (last 100)
        if len(self.stats["events"]) > 100:
            self.stats["events"] = self.stats["events"][-100:]

    def reset(self):
        """Reset tracker state"""
        self.tracker.reset()
        self.frame_count = 0
        self.start_time = time.time()
        self.stats = {
            "total_frames": 0,
            "total_detections": 0,
            "player_count": 0,
            "ball_detections": 0,
            "events": [],
        }


class FootballEventDetector:
    """
    Detects football events like goals, saves, tackles, etc.
    """

    def __init__(self):
        self.previous_positions = {}
        self.event_cooldown = {}  # Prevent duplicate events
        self.goal_areas = self.define_goal_areas()

    def define_goal_areas(self):
        """Define goal areas (will be calibrated based on field detection)"""
        # These would be dynamically calculated based on field detection
        return {
            "left_goal": {"x1": 0, "y1": 200, "x2": 100, "y2": 400},
            "right_goal": {"x1": 540, "y1": 200, "x2": 640, "y2": 400},
        }

    def detect_events(self, tracked_objects, frame):
        """
        Detect football events from tracked objects

        Args:
            tracked_objects: List of tracked objects
            frame: Current frame

        Returns:
            list: Detected events
        """
        events = []
        current_time = time.time()

        # Find ball and players
        ball = None
        players = []

        for obj in tracked_objects:
            if obj.get("class_name") == "sports ball":
                ball = obj
            elif obj.get("class_name") == "person":
                players.append(obj)

        # Goal detection
        if ball:
            goal_event = self.detect_goal(ball, current_time)
            if goal_event:
                events.append(goal_event)

        # Fast movement detection (potential highlight moments)
        for player in players:
            speed_event = self.detect_fast_movement(player, current_time)
            if speed_event:
                events.append(speed_event)

        # Ball possession changes
        if ball and players:
            possession_event = self.detect_possession_change(
                ball, players, current_time
            )
            if possession_event:
                events.append(possession_event)

        return events

    def detect_goal(self, ball, current_time):
        """Detect if ball enters goal area"""
        ball_x = ball.get("bbox", [0, 0, 0, 0])[0]
        ball_y = ball.get("bbox", [0, 0, 0, 0])[1]

        # Check if ball is in goal area
        for goal_name, goal_area in self.goal_areas.items():
            if (
                goal_area["x1"] <= ball_x <= goal_area["x2"]
                and goal_area["y1"] <= ball_y <= goal_area["y2"]
            ):

                # Check cooldown to prevent duplicate events
                cooldown_key = f"goal_{goal_name}"
                if (
                    cooldown_key not in self.event_cooldown
                    or current_time - self.event_cooldown[cooldown_key] > 5.0
                ):

                    self.event_cooldown[cooldown_key] = current_time

                    return {
                        "type": "goal",
                        "timestamp": current_time,
                        "location": goal_name,
                        "confidence": 0.8,
                        "description": f"Potential goal detected at {goal_name}",
                    }

        return None

    def detect_fast_movement(self, player, current_time):
        """Detect fast player movement (sprints, tackles)"""
        player_id = player.get("track_id")
        if not player_id:
            return None

        current_pos = player.get("bbox", [0, 0, 0, 0])
        current_center = (
            current_pos[0] + current_pos[2] / 2,
            current_pos[1] + current_pos[3] / 2,
        )

        if player_id in self.previous_positions:
            prev_pos, prev_time = self.previous_positions[player_id]

            # Calculate speed
            distance = np.sqrt(
                (current_center[0] - prev_pos[0]) ** 2
                + (current_center[1] - prev_pos[1]) ** 2
            )
            time_diff = current_time - prev_time

            if time_diff > 0:
                speed = distance / time_diff

                # Threshold for fast movement (adjust based on field size)
                if speed > 50:  # pixels per second
                    cooldown_key = f"fast_movement_{player_id}"
                    if (
                        cooldown_key not in self.event_cooldown
                        or current_time - self.event_cooldown[cooldown_key] > 3.0
                    ):

                        self.event_cooldown[cooldown_key] = current_time

                        return {
                            "type": "fast_movement",
                            "timestamp": current_time,
                            "player_id": player_id,
                            "speed": speed,
                            "confidence": min(speed / 100, 1.0),
                            "description": f"Fast movement detected for player {player_id}",
                        }

        # Update position history
        self.previous_positions[player_id] = (current_center, current_time)

        return None

    def detect_possession_change(self, ball, players, current_time):
        """Detect ball possession changes"""
        # Find closest player to ball
        ball_center = ball.get("bbox", [0, 0, 0, 0])
        ball_pos = (
            ball_center[0] + ball_center[2] / 2,
            ball_center[1] + ball_center[3] / 2,
        )

        closest_player = None
        min_distance = float("inf")

        for player in players:
            player_center = player.get("bbox", [0, 0, 0, 0])
            player_pos = (
                player_center[0] + player_center[2] / 2,
                player_center[1] + player_center[3] / 2,
            )

            distance = np.sqrt(
                (ball_pos[0] - player_pos[0]) ** 2 + (ball_pos[1] - player_pos[1]) ** 2
            )

            if distance < min_distance:
                min_distance = distance
                closest_player = player

        # Check if possession changed
        if closest_player and min_distance < 50:  # Within 50 pixels
            player_id = closest_player.get("track_id")

            if hasattr(self, "current_possession"):
                if (
                    self.current_possession != player_id
                    and current_time - getattr(self, "last_possession_change", 0) > 2.0
                ):

                    self.last_possession_change = current_time
                    old_possession = self.current_possession
                    self.current_possession = player_id

                    return {
                        "type": "possession_change",
                        "timestamp": current_time,
                        "from_player": old_possession,
                        "to_player": player_id,
                        "confidence": 0.7,
                        "description": f"Ball possession changed from player {old_possession} to {player_id}",
                    }
            else:
                self.current_possession = player_id

        return None


class HighlightGenerator:
    """
    Generates highlights from tracking data and events
    """

    def __init__(self):
        self.event_weights = {
            "goal": 1.0,
            "fast_movement": 0.6,
            "possession_change": 0.3,
        }

    def generate_highlights(
        self, tracking_data, min_highlight_duration=10, max_highlights=10
    ):
        """
        Generate highlights from tracking data

        Args:
            tracking_data: List of tracking results
            min_highlight_duration: Minimum duration for highlights (seconds)
            max_highlights: Maximum number of highlights to generate

        Returns:
            list: Highlight segments with start/end times
        """
        if not tracking_data:
            return []

        # Score each time segment based on events
        segment_scores = self.score_segments(tracking_data)

        # Find peak moments
        highlights = self.find_peak_moments(segment_scores, min_highlight_duration)

        # Sort by score and limit count
        highlights.sort(key=lambda x: x["score"], reverse=True)
        highlights = highlights[:max_highlights]

        # Add metadata
        for i, highlight in enumerate(highlights):
            highlight["title"] = f"Highlight {i + 1}"
            highlight["description"] = self.generate_description(highlight)

        return highlights

    def score_segments(self, tracking_data, segment_duration=5):
        """Score time segments based on activity and events"""
        segments = []

        if not tracking_data:
            return segments

        start_time = tracking_data[0]["timestamp"]
        end_time = tracking_data[-1]["timestamp"]

        current_time = start_time
        while current_time < end_time:
            segment_end = min(current_time + segment_duration, end_time)

            # Get data for this segment
            segment_data = [
                data
                for data in tracking_data
                if current_time <= data["timestamp"] < segment_end
            ]

            # Calculate score
            score = self.calculate_segment_score(segment_data)

            segments.append(
                {
                    "start_time": current_time,
                    "end_time": segment_end,
                    "score": score,
                    "data": segment_data,
                }
            )

            current_time = segment_end

        return segments

    def calculate_segment_score(self, segment_data):
        """Calculate score for a time segment"""
        if not segment_data:
            return 0

        score = 0

        # Event-based scoring
        for data in segment_data:
            events = data.get("events", [])
            for event in events:
                event_type = event.get("type", "")
                weight = self.event_weights.get(event_type, 0.1)
                confidence = event.get("confidence", 0.5)
                score += weight * confidence

        # Activity-based scoring
        avg_players = np.mean(
            [len(data.get("tracked_objects", [])) for data in segment_data]
        )
        score += avg_players * 0.1  # More players = more activity

        # Ball activity
        ball_detections = sum(
            1
            for data in segment_data
            if any(
                obj.get("class_name") == "sports ball"
                for obj in data.get("tracked_objects", [])
            )
        )
        score += ball_detections * 0.2

        return score

    def find_peak_moments(self, segments, min_duration):
        """Find peak moments for highlights"""
        if not segments:
            return []

        highlights = []

        # Find local maxima
        for i, segment in enumerate(segments):
            if segment["score"] > 0.5:  # Minimum threshold
                # Check if it's a local maximum
                is_peak = True

                # Check previous segments
                for j in range(max(0, i - 2), i):
                    if segments[j]["score"] >= segment["score"]:
                        is_peak = False
                        break

                # Check next segments
                for j in range(i + 1, min(len(segments), i + 3)):
                    if segments[j]["score"] >= segment["score"]:
                        is_peak = False
                        break

                if is_peak:
                    # Extend highlight to include surrounding activity
                    start_idx = max(0, i - 1)
                    end_idx = min(len(segments) - 1, i + 1)

                    highlight_start = segments[start_idx]["start_time"]
                    highlight_end = segments[end_idx]["end_time"]

                    if highlight_end - highlight_start >= min_duration:
                        highlights.append(
                            {
                                "start_time": highlight_start,
                                "end_time": highlight_end,
                                "score": segment["score"],
                                "peak_segment": segment,
                            }
                        )

        return highlights

    def generate_description(self, highlight):
        """Generate description for highlight"""
        peak_segment = highlight.get("peak_segment", {})
        events = []

        for data in peak_segment.get("data", []):
            events.extend(data.get("events", []))

        if not events:
            return "Exciting game moment"

        # Describe main events
        event_types = [event.get("type", "") for event in events]

        if "goal" in event_types:
            return "Goal scoring opportunity"
        elif "fast_movement" in event_types:
            return "Fast-paced action"
        elif "possession_change" in event_types:
            return "Ball possession battle"
        else:
            return "Key game moment"


# Export main classes
__all__ = ["FootballTracker", "FootballEventDetector", "HighlightGenerator"]
