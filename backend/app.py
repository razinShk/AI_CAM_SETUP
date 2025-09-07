"""
AI Football Tracking Camera System - Backend API
Handles camera control, video processing, and social features
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import (
    JWTManager,
    jwt_required,
    create_access_token,
    get_jwt_identity,
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import uuid
import datetime
import subprocess
import threading
import requests
from pathlib import Path
import cv2
import json
from celery import Celery
import redis

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "your-secret-key-change-this")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL", "postgresql://localhost/football_tracker"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["JWT_SECRET_KEY"] = os.environ.get(
    "JWT_SECRET_KEY", "jwt-secret-change-this"
)
app.config["UPLOAD_FOLDER"] = "uploads"
app.config["MAX_CONTENT_LENGTH"] = 500 * 1024 * 1024  # 500MB max file size

# Initialize extensions
db = SQLAlchemy(app)
jwt = JWTManager(app)
CORS(app)

# Celery configuration for background tasks
celery = Celery(app.name, broker=os.environ.get("REDIS_URL", "redis://localhost:6379"))
celery.conf.update(app.config)

# Ensure upload directory exists
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
os.makedirs("recordings", exist_ok=True)
os.makedirs("highlights", exist_ok=True)


# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), default="player")  # 'admin', 'turf_owner', 'player'
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class TurfLocation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.Text, nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    camera_ip = db.Column(db.String(15))  # Raspberry Pi IP
    camera_status = db.Column(db.String(20), default="offline")
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)


class GameSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    turf_id = db.Column(db.Integer, db.ForeignKey("turf_location.id"), nullable=False)
    session_name = db.Column(db.String(100), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime)
    duration = db.Column(db.Integer)  # in minutes
    status = db.Column(
        db.String(20), default="scheduled"
    )  # 'scheduled', 'recording', 'completed', 'processing'
    recording_path = db.Column(db.String(255))
    created_by = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)


class Highlight(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey("game_session.id"), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    video_path = db.Column(db.String(255), nullable=False)
    thumbnail_path = db.Column(db.String(255))
    start_timestamp = db.Column(db.Float)  # seconds from game start
    end_timestamp = db.Column(db.Float)
    tags = db.Column(db.JSON)  # ['goal', 'save', 'tackle', etc.]
    likes = db.Column(db.Integer, default=0)
    views = db.Column(db.Integer, default=0)
    created_by = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)


class PlayerSession(db.Model):
    """Many-to-many relationship between players and game sessions"""

    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    session_id = db.Column(db.Integer, db.ForeignKey("game_session.id"), nullable=False)
    joined_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)


class SocialPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    highlight_id = db.Column(db.Integer, db.ForeignKey("highlight.id"), nullable=False)
    caption = db.Column(db.Text)
    likes = db.Column(db.Integer, default=0)
    comments_count = db.Column(db.Integer, default=0)
    shares_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)


# Camera Control Functions
class CameraController:
    @staticmethod
    def send_command(camera_ip, command, params=None):
        """Send command to Raspberry Pi camera"""
        try:
            url = f"http://{camera_ip}:5000/api/{command}"
            response = requests.post(url, json=params or {}, timeout=10)
            return response.json()
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def start_recording(camera_ip, session_id):
        """Start recording on Raspberry Pi"""
        params = {
            "session_id": session_id,
            "output_path": f"recordings/session_{session_id}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4",
        }
        return CameraController.send_command(camera_ip, "start_recording", params)

    @staticmethod
    def stop_recording(camera_ip):
        """Stop recording on Raspberry Pi"""
        return CameraController.send_command(camera_ip, "stop_recording")

    @staticmethod
    def get_status(camera_ip):
        """Get camera status"""
        return CameraController.send_command(camera_ip, "status")


# Background Tasks with Celery
@celery.task
def process_video_highlights(session_id):
    """Process recorded video to generate highlights using AI"""
    session = GameSession.query.get(session_id)
    if not session or not session.recording_path:
        return {"error": "Session or recording not found"}

    try:
        # AI processing to detect highlights
        highlights = detect_highlights(session.recording_path)

        for highlight_data in highlights:
            # Create highlight clips
            highlight_path = create_highlight_clip(
                session.recording_path,
                highlight_data["start_time"],
                highlight_data["end_time"],
                session_id,
            )

            # Create thumbnail
            thumbnail_path = create_thumbnail(highlight_path)

            # Save to database
            highlight = Highlight(
                session_id=session_id,
                title=highlight_data["title"],
                description=highlight_data["description"],
                video_path=highlight_path,
                thumbnail_path=thumbnail_path,
                start_timestamp=highlight_data["start_time"],
                end_timestamp=highlight_data["end_time"],
                tags=highlight_data["tags"],
                created_by=session.created_by,
            )
            db.session.add(highlight)

        db.session.commit()

        # Update session status
        session.status = "completed"
        db.session.commit()

        return {"success": True, "highlights_count": len(highlights)}

    except Exception as e:
        session.status = "error"
        db.session.commit()
        return {"error": str(e)}


def detect_highlights(video_path):
    """AI-powered highlight detection"""
    # This would integrate with your existing AI tracking code
    # For now, we'll create a simple implementation

    highlights = []

    # Analyze video for key moments
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = frame_count / fps

    # Simple highlight detection based on motion/activity
    # In production, this would use your AI models to detect:
    # - Goals, saves, tackles, etc.

    # For demo, create highlights every 2 minutes
    for i in range(0, int(duration), 120):  # Every 2 minutes
        if i + 30 < duration:  # 30-second highlights
            highlights.append(
                {
                    "title": f"Highlight {len(highlights) + 1}",
                    "description": "Auto-generated highlight",
                    "start_time": i,
                    "end_time": i + 30,
                    "tags": ["auto-generated"],
                }
            )

    cap.release()
    return highlights


def create_highlight_clip(source_video, start_time, end_time, session_id):
    """Create highlight clip from main video"""
    output_path = (
        f"highlights/highlight_{session_id}_{int(start_time)}_{int(end_time)}.mp4"
    )

    cmd = [
        "ffmpeg",
        "-i",
        source_video,
        "-ss",
        str(start_time),
        "-t",
        str(end_time - start_time),
        "-c:v",
        "libx264",
        "-c:a",
        "aac",
        "-y",
        output_path,
    ]

    subprocess.run(cmd, check=True)
    return output_path


def create_thumbnail(video_path):
    """Create thumbnail from video"""
    thumbnail_path = video_path.replace(".mp4", "_thumb.jpg")

    cmd = [
        "ffmpeg",
        "-i",
        video_path,
        "-ss",
        "00:00:01",
        "-vframes",
        "1",
        "-y",
        thumbnail_path,
    ]

    subprocess.run(cmd, check=True)
    return thumbnail_path


# API Routes


# Authentication Routes
@app.route("/api/register", methods=["POST"])
def register():
    data = request.get_json()

    if User.query.filter_by(email=data["email"]).first():
        return jsonify({"error": "Email already registered"}), 400

    if User.query.filter_by(username=data["username"]).first():
        return jsonify({"error": "Username already taken"}), 400

    user = User(
        email=data["email"], username=data["username"], role=data.get("role", "player")
    )
    user.set_password(data["password"])

    db.session.add(user)
    db.session.commit()

    access_token = create_access_token(identity=user.id)
    return jsonify(
        {
            "access_token": access_token,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
            },
        }
    )


@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json()
    user = User.query.filter_by(email=data["email"]).first()

    if user and user.check_password(data["password"]):
        access_token = create_access_token(identity=user.id)
        return jsonify(
            {
                "access_token": access_token,
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "role": user.role,
                },
            }
        )

    return jsonify({"error": "Invalid credentials"}), 401


# Turf Management Routes
@app.route("/api/turfs", methods=["GET"])
@jwt_required()
def get_turfs():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if user.role == "admin":
        turfs = TurfLocation.query.all()
    elif user.role == "turf_owner":
        turfs = TurfLocation.query.filter_by(owner_id=user_id).all()
    else:
        turfs = TurfLocation.query.all()  # Players can see all turfs

    return jsonify(
        [
            {
                "id": turf.id,
                "name": turf.name,
                "address": turf.address,
                "camera_status": turf.camera_status,
            }
            for turf in turfs
        ]
    )


@app.route("/api/turfs", methods=["POST"])
@jwt_required()
def create_turf():
    user_id = get_jwt_identity()
    data = request.get_json()

    turf = TurfLocation(
        name=data["name"],
        address=data["address"],
        camera_ip=data.get("camera_ip"),
        owner_id=user_id,
    )

    db.session.add(turf)
    db.session.commit()

    return jsonify({"id": turf.id, "message": "Turf created successfully"})


# Camera Control Routes
@app.route("/api/camera/<int:turf_id>/start", methods=["POST"])
@jwt_required()
def start_camera_recording(turf_id):
    user_id = get_jwt_identity()
    data = request.get_json()

    turf = TurfLocation.query.get_or_404(turf_id)

    # Create game session
    session = GameSession(
        turf_id=turf_id,
        session_name=data.get(
            "session_name", f'Game {datetime.datetime.now().strftime("%Y-%m-%d %H:%M")}'
        ),
        start_time=datetime.datetime.utcnow(),
        duration=data.get("duration", 60),  # Default 60 minutes
        created_by=user_id,
        status="recording",
    )

    db.session.add(session)
    db.session.commit()

    # Start recording on Raspberry Pi
    result = CameraController.start_recording(turf.camera_ip, session.id)

    if "error" in result:
        session.status = "error"
        db.session.commit()
        return jsonify(result), 500

    # Update recording path
    session.recording_path = result.get("recording_path")
    db.session.commit()

    return jsonify(
        {
            "session_id": session.id,
            "message": "Recording started",
            "camera_response": result,
        }
    )


@app.route("/api/camera/<int:turf_id>/stop", methods=["POST"])
@jwt_required()
def stop_camera_recording(turf_id):
    turf = TurfLocation.query.get_or_404(turf_id)

    # Find active session
    session = GameSession.query.filter_by(turf_id=turf_id, status="recording").first()

    if not session:
        return jsonify({"error": "No active recording session"}), 400

    # Stop recording on Raspberry Pi
    result = CameraController.stop_recording(turf.camera_ip)

    # Update session
    session.end_time = datetime.datetime.utcnow()
    session.status = "processing"
    db.session.commit()

    # Start background processing
    process_video_highlights.delay(session.id)

    return jsonify(
        {
            "session_id": session.id,
            "message": "Recording stopped, processing highlights...",
            "camera_response": result,
        }
    )


@app.route("/api/camera/<int:turf_id>/status", methods=["GET"])
@jwt_required()
def get_camera_status(turf_id):
    turf = TurfLocation.query.get_or_404(turf_id)

    if not turf.camera_ip:
        return jsonify({"status": "not_configured"})

    result = CameraController.get_status(turf.camera_ip)

    # Update turf status
    turf.camera_status = "online" if "error" not in result else "offline"
    db.session.commit()

    return jsonify(result)


# Game Session Routes
@app.route("/api/sessions", methods=["GET"])
@jwt_required()
def get_sessions():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if user.role == "player":
        # Get sessions where user is a participant
        sessions = (
            db.session.query(GameSession)
            .join(PlayerSession)
            .filter(PlayerSession.player_id == user_id)
            .all()
        )
    else:
        # Turf owners and admins see all sessions for their turfs
        sessions = GameSession.query.all()

    return jsonify(
        [
            {
                "id": session.id,
                "session_name": session.session_name,
                "start_time": session.start_time.isoformat(),
                "end_time": session.end_time.isoformat() if session.end_time else None,
                "status": session.status,
                "turf_name": TurfLocation.query.get(session.turf_id).name,
            }
            for session in sessions
        ]
    )


@app.route("/api/sessions/<int:session_id>/join", methods=["POST"])
@jwt_required()
def join_session(session_id):
    user_id = get_jwt_identity()

    # Check if already joined
    existing = PlayerSession.query.filter_by(
        player_id=user_id, session_id=session_id
    ).first()

    if existing:
        return jsonify({"message": "Already joined this session"})

    player_session = PlayerSession(player_id=user_id, session_id=session_id)

    db.session.add(player_session)
    db.session.commit()

    return jsonify({"message": "Joined session successfully"})


# Highlights Routes
@app.route("/api/highlights", methods=["GET"])
def get_highlights():
    """Get highlights feed (public or filtered)"""
    session_id = request.args.get("session_id")
    user_id = request.args.get("user_id")
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 20))

    query = Highlight.query

    if session_id:
        query = query.filter_by(session_id=session_id)
    if user_id:
        query = query.filter_by(created_by=user_id)

    highlights = query.order_by(Highlight.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify(
        {
            "highlights": [
                {
                    "id": h.id,
                    "title": h.title,
                    "description": h.description,
                    "thumbnail_path": h.thumbnail_path,
                    "video_path": h.video_path,
                    "tags": h.tags,
                    "likes": h.likes,
                    "views": h.views,
                    "created_at": h.created_at.isoformat(),
                    "creator": User.query.get(h.created_by).username,
                }
                for h in highlights.items
            ],
            "total": highlights.total,
            "pages": highlights.pages,
            "current_page": page,
        }
    )


@app.route("/api/highlights/<int:highlight_id>/like", methods=["POST"])
@jwt_required()
def like_highlight(highlight_id):
    highlight = Highlight.query.get_or_404(highlight_id)
    highlight.likes += 1
    db.session.commit()

    return jsonify({"likes": highlight.likes})


@app.route("/api/highlights/<int:highlight_id>/view", methods=["POST"])
def view_highlight(highlight_id):
    highlight = Highlight.query.get_or_404(highlight_id)
    highlight.views += 1
    db.session.commit()

    return jsonify({"views": highlight.views})


# File serving routes
@app.route("/api/video/<path:filename>")
def serve_video(filename):
    """Serve video files"""
    return send_file(filename)


@app.route("/api/thumbnail/<path:filename>")
def serve_thumbnail(filename):
    """Serve thumbnail files"""
    return send_file(filename)


# Social Features
@app.route("/api/social/feed", methods=["GET"])
@jwt_required()
def get_social_feed():
    """Get social media feed of highlights"""
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 20))

    posts = SocialPost.query.order_by(SocialPost.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    feed = []
    for post in posts.items:
        highlight = Highlight.query.get(post.highlight_id)
        user = User.query.get(post.user_id)

        feed.append(
            {
                "id": post.id,
                "caption": post.caption,
                "likes": post.likes,
                "comments_count": post.comments_count,
                "shares_count": post.shares_count,
                "created_at": post.created_at.isoformat(),
                "user": {"username": user.username, "id": user.id},
                "highlight": {
                    "id": highlight.id,
                    "title": highlight.title,
                    "video_path": highlight.video_path,
                    "thumbnail_path": highlight.thumbnail_path,
                    "tags": highlight.tags,
                },
            }
        )

    return jsonify(
        {"feed": feed, "total": posts.total, "pages": posts.pages, "current_page": page}
    )


@app.route("/api/social/post", methods=["POST"])
@jwt_required()
def create_social_post():
    user_id = get_jwt_identity()
    data = request.get_json()

    post = SocialPost(
        user_id=user_id,
        highlight_id=data["highlight_id"],
        caption=data.get("caption", ""),
    )

    db.session.add(post)
    db.session.commit()

    return jsonify({"id": post.id, "message": "Post created successfully"})


# Initialize database
@app.before_first_request
def create_tables():
    db.create_all()


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
