# Create Supabase client file

"""
Supabase Client for SportsCam
Handles all database operations and file uploads
"""

import os
from supabase import create_client, Client
from datetime import datetime
import json
import logging
from typing import Optional, Dict, List
import requests
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SupabaseClient:
    def __init__(self):
        """Initialize Supabase client with credentials"""
        self.url = os.environ.get(
            "SUPABASE_URL", "https://iifhyrcwuvymcrlmqsfr.supabase.co"
        )
        self.key = os.environ.get(
            "SUPABASE_ANON_KEY",
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlpZmh5cmN3dXZ5bWNybG1xc2ZyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTcyMDc4NDYsImV4cCI6MjA3Mjc4Mzg0Nn0.P8UzfKIC_aiGfhrZM3gnjz9L4Fk8Y-WQRSeAWDZlIFk",
        )

        self.supabase: Client = create_client(self.url, self.key)
        self.camera_id = os.environ.get("CAMERA_ID", "default_camera")
        self.turf_id = os.environ.get("TURF_ID", "550e8400-e29b-41d4-a716-446655440001")

        logger.info(f"Supabase client initialized for camera: {self.camera_id}")

    def get_local_ip(self) -> str:
        """Get local IP address"""
        import socket

        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception as e:
            logger.error(f"Failed to get local IP: {e}")
            return "127.0.0.1"

    def register_camera(self) -> bool:
        """Register camera with main system"""
        try:
            # Update turf location with camera status
            result = (
                self.supabase.table("turf_locations")
                .update(
                    {
                        "camera_status": "online",
                        "camera_ip": self.get_local_ip(),
                        "updated_at": datetime.now().isoformat(),
                    }
                )
                .eq("id", self.turf_id)
                .execute()
            )

            logger.info("Camera registered successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to register camera: {e}")
            return False

    def create_session(self, session_name: str, duration: int = 60) -> Optional[str]:
        """Create a new game session"""
        try:
            result = (
                self.supabase.table("game_sessions")
                .insert(
                    {
                        "turf_id": self.turf_id,
                        "session_name": session_name,
                        "start_time": datetime.now().isoformat(),
                        "duration": duration,
                        "status": "recording",
                        "metadata": {
                            "camera_id": self.camera_id,
                            "recording_started_by": "camera_system",
                        },
                    }
                )
                .execute()
            )

            if result.data:
                session_id = result.data[0]["id"]
                logger.info(f"Created session: {session_id}")
                return session_id
            return None
        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            return None

    def update_session_status(
        self, session_id: str, status: str, recording_path: Optional[str] = None
    ) -> bool:
        """Update session status"""
        try:
            update_data = {"status": status, "updated_at": datetime.now().isoformat()}

            if status == "completed":
                update_data["end_time"] = datetime.now().isoformat()

            if recording_path:
                update_data["recording_path"] = recording_path

            result = (
                self.supabase.table("game_sessions")
                .update(update_data)
                .eq("id", session_id)
                .execute()
            )
            logger.info(f"Updated session {session_id} status to {status}")
            return True
        except Exception as e:
            logger.error(f"Failed to update session: {e}")
            return False

    def upload_video(self, file_path: str, session_id: str) -> Optional[str]:
        """Upload video to Supabase Storage"""
        try:
            bucket_name = "videos"
            file_name = (
                f"session_{session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
            )

            # Upload file
            with open(file_path, "rb") as f:
                result = self.supabase.storage.from_(bucket_name).upload(file_name, f)

            if result:
                # Get public URL
                url = self.supabase.storage.from_(bucket_name).get_public_url(file_name)

                # Update session with video URL
                self.supabase.table("game_sessions").update({"recording_url": url}).eq(
                    "id", session_id
                ).execute()

                logger.info(f"Video uploaded: {url}")
                return url
            return None
        except Exception as e:
            logger.error(f"Failed to upload video: {e}")
            return None

    def heartbeat(self) -> bool:
        """Send heartbeat to keep camera status updated"""
        try:
            self.supabase.table("turf_locations").update(
                {"camera_status": "online", "updated_at": datetime.now().isoformat()}
            ).eq("id", self.turf_id).execute()
            return True
        except Exception as e:
            logger.error(f"Heartbeat failed: {e}")
            return False


# Singleton instance
_supabase_client = None


def get_supabase_client() -> SupabaseClient:
    """Get singleton Supabase client instance"""
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = SupabaseClient()
    return _supabase_client

