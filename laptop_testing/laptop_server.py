"""
Laptop Testing Server for SportsCam
Simulates the Raspberry Pi server but uses laptop webcam
"""

import cv2
import os
import json
import threading
import time
from datetime import datetime
from flask import Flask, request, jsonify, render_template_string
from werkzeug.serving import make_server
import numpy as np

app = Flask(__name__)

# Global variables
camera = None
recording = False
current_session = None
recording_thread = None
recordings_dir = "recordings"
session_data = {}

# Ensure recordings directory exists
os.makedirs(recordings_dir, exist_ok=True)


class LaptopRecorder:
    def __init__(self):
        self.cap = None
        self.writer = None
        self.recording = False

    def start_camera(self):
        """Initialize laptop camera"""
        try:
            self.cap = cv2.VideoCapture(0)  # Use default camera
            if not self.cap.isOpened():
                return False

            # Set camera properties
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            self.cap.set(cv2.CAP_PROP_FPS, 30)

            return True
        except Exception as e:
            print(f"Error starting camera: {e}")
            return False

    def start_recording(self, session_id):
        """Start recording video"""
        if not self.cap or not self.cap.isOpened():
            if not self.start_camera():
                return False

        try:
            # Set up video writer
            filename = f"{recordings_dir}/session_{session_id}.mp4"
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            fps = 30
            frame_size = (1280, 720)

            self.writer = cv2.VideoWriter(filename, fourcc, fps, frame_size)
            self.recording = True

            print(f"Started recording: {filename}")
            return True

        except Exception as e:
            print(f"Error starting recording: {e}")
            return False

    def stop_recording(self):
        """Stop recording video"""
        self.recording = False
        if self.writer:
            self.writer.release()
            self.writer = None
        print("Recording stopped")

    def record_frame(self):
        """Record a single frame"""
        if self.recording and self.cap and self.writer:
            ret, frame = self.cap.read()
            if ret:
                # Resize frame to match expected size
                frame = cv2.resize(frame, (1280, 720))
                self.writer.write(frame)
                return True
        return False

    def cleanup(self):
        """Clean up resources"""
        self.recording = False
        if self.writer:
            self.writer.release()
        if self.cap:
            self.cap.release()


# Initialize recorder
recorder = LaptopRecorder()


def recording_worker(session_id):
    """Background thread for recording"""
    global recording, current_session

    print(f"Recording worker started for session {session_id}")

    if not recorder.start_recording(session_id):
        print("Failed to start recording")
        recording = False
        return

    frame_count = 0
    start_time = time.time()

    while recording:
        if recorder.record_frame():
            frame_count += 1

            # Print progress every 100 frames
            if frame_count % 100 == 0:
                elapsed = time.time() - start_time
                fps = frame_count / elapsed if elapsed > 0 else 0
                print(f"Recorded {frame_count} frames, FPS: {fps:.1f}")

        time.sleep(1 / 30)  # 30 FPS

    recorder.stop_recording()

    # Update session data
    if current_session:
        session_data[current_session]["end_time"] = datetime.now().isoformat()
        session_data[current_session]["status"] = "completed"
        session_data[current_session]["frame_count"] = frame_count

        # Save session data
        with open(
            f"{recordings_dir}/session_{current_session}_metadata.json", "w"
        ) as f:
            json.dump(session_data[current_session], f, indent=2)

    print(f"Recording completed: {frame_count} frames recorded")


@app.route("/")
def dashboard():
    """Simple web dashboard"""
    return render_template_string(
        """
<!DOCTYPE html>
<html>
<head>
    <title>SportsCam Laptop Testing</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #2c3e50; text-align: center; }
        .status { padding: 15px; margin: 20px 0; border-radius: 5px; font-weight: bold; }
        .status.recording { background: #e74c3c; color: white; }
        .status.ready { background: #27ae60; color: white; }
        .status.idle { background: #95a5a6; color: white; }
        button { padding: 12px 24px; margin: 10px; border: none; border-radius: 5px; font-size: 16px; cursor: pointer; }
        .btn-start { background: #27ae60; color: white; }
        .btn-stop { background: #e74c3c; color: white; }
        .btn-refresh { background: #3498db; color: white; }
        .session-info { background: #ecf0f1; padding: 15px; margin: 20px 0; border-radius: 5px; }
        .recordings { margin-top: 30px; }
        .recording-item { background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 5px; border-left: 4px solid #3498db; }
        pre { background: #2c3e50; color: #ecf0f1; padding: 15px; border-radius: 5px; overflow-x: auto; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🏆 SportsCam Laptop Testing</h1>
        
        <div id="status" class="status idle">
            System Status: Ready
        </div>
        
        <div>
            <button class="btn-start" onclick="startRecording()">📹 Start Recording</button>
            <button class="btn-stop" onclick="stopRecording()">⏹️ Stop Recording</button>
            <button class="btn-refresh" onclick="refreshStatus()">🔄 Refresh</button>
        </div>
        
        <div id="session-info" class="session-info" style="display: none;">
            <h3>Current Session</h3>
            <p id="session-details"></p>
        </div>
        
        <div class="recordings">
            <h3>📁 Recorded Sessions</h3>
            <div id="recordings-list">
                <p>Loading recordings...</p>
            </div>
        </div>
        
        <div style="margin-top: 30px;">
            <h3>📋 System Info</h3>
            <pre id="system-info">Loading system info...</pre>
        </div>
    </div>

    <script>
        let currentSession = null;
        
        async function startRecording() {
            try {
                const sessionName = prompt("Enter session name:", "Test Session " + new Date().toLocaleTimeString());
                if (!sessionName) return;
                
                const response = await fetch('/start_recording', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ session_name: sessionName })
                });
                
                const result = await response.json();
                if (result.success) {
                    currentSession = result.session_id;
                    updateStatus();
                    showSessionInfo(result);
                } else {
                    alert('Failed to start recording: ' + result.error);
                }
            } catch (error) {
                alert('Error: ' + error.message);
            }
        }
        
        async function stopRecording() {
            try {
                const response = await fetch('/stop_recording', {
                    method: 'POST'
                });
                
                const result = await response.json();
                if (result.success) {
                    currentSession = null;
                    updateStatus();
                    hideSessionInfo();
                    loadRecordings();
                } else {
                    alert('Failed to stop recording: ' + result.error);
                }
            } catch (error) {
                alert('Error: ' + error.message);
            }
        }
        
        async function refreshStatus() {
            updateStatus();
            loadRecordings();
            loadSystemInfo();
        }
        
        async function updateStatus() {
            try {
                const response = await fetch('/status');
                const status = await response.json();
                
                const statusDiv = document.getElementById('status');
                if (status.recording) {
                    statusDiv.className = 'status recording';
                    statusDiv.textContent = `Recording: ${status.session_name || 'Unknown Session'}`;
                } else {
                    statusDiv.className = 'status ready';
                    statusDiv.textContent = 'System Status: Ready';
                }
            } catch (error) {
                const statusDiv = document.getElementById('status');
                statusDiv.className = 'status idle';
                statusDiv.textContent = 'System Status: Error';
            }
        }
        
        function showSessionInfo(sessionData) {
            const sessionInfo = document.getElementById('session-info');
            const sessionDetails = document.getElementById('session-details');
            
            sessionDetails.innerHTML = `
                <strong>Session ID:</strong> ${sessionData.session_id}<br>
                <strong>Name:</strong> ${sessionData.session_name}<br>
                <strong>Started:</strong> ${new Date(sessionData.start_time).toLocaleString()}<br>
                <strong>Status:</strong> Recording...
            `;
            
            sessionInfo.style.display = 'block';
        }
        
        function hideSessionInfo() {
            document.getElementById('session-info').style.display = 'none';
        }
        
        async function loadRecordings() {
            try {
                const response = await fetch('/recordings');
                const recordings = await response.json();
                
                const recordingsList = document.getElementById('recordings-list');
                
                if (recordings.length === 0) {
                    recordingsList.innerHTML = '<p>No recordings found. Start a recording to see it here!</p>';
                    return;
                }
                
                recordingsList.innerHTML = recordings.map(recording => `
                    <div class="recording-item">
                        <h4>${recording.name}</h4>
                        <p><strong>File:</strong> ${recording.filename}</p>
                        <p><strong>Size:</strong> ${recording.size_mb} MB</p>
                        <p><strong>Created:</strong> ${new Date(recording.created).toLocaleString()}</p>
                        ${recording.metadata ? `
                            <p><strong>Frames:</strong> ${recording.metadata.frame_count || 'Unknown'}</p>
                            <p><strong>Duration:</strong> ${recording.metadata.duration || 'Unknown'}</p>
                        ` : ''}
                    </div>
                `).join('');
                
            } catch (error) {
                document.getElementById('recordings-list').innerHTML = '<p>Error loading recordings</p>';
            }
        }
        
        async function loadSystemInfo() {
            try {
                const response = await fetch('/system_info');
                const info = await response.json();
                
                document.getElementById('system-info').textContent = JSON.stringify(info, null, 2);
            } catch (error) {
                document.getElementById('system-info').textContent = 'Error loading system info';
            }
        }
        
        // Initialize page
        document.addEventListener('DOMContentLoaded', function() {
            refreshStatus();
            setInterval(updateStatus, 2000); // Update status every 2 seconds
        });
    </script>
</body>
</html>
    """
    )


@app.route("/start_recording", methods=["POST"])
def start_recording():
    """Start recording endpoint"""
    global recording, current_session, recording_thread

    if recording:
        return jsonify({"success": False, "error": "Already recording"})

    try:
        data = request.get_json()
        session_name = data.get(
            "session_name", f'Session_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
        )

        # Generate session ID
        session_id = f"{int(time.time())}_{hash(session_name) % 10000}"
        current_session = session_id

        # Store session data
        session_data[session_id] = {
            "session_id": session_id,
            "session_name": session_name,
            "start_time": datetime.now().isoformat(),
            "status": "recording",
        }

        # Start recording in background thread
        recording = True
        recording_thread = threading.Thread(target=recording_worker, args=(session_id,))
        recording_thread.start()

        return jsonify(
            {
                "success": True,
                "session_id": session_id,
                "session_name": session_name,
                "start_time": session_data[session_id]["start_time"],
            }
        )

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/stop_recording", methods=["POST"])
def stop_recording():
    """Stop recording endpoint"""
    global recording, current_session, recording_thread

    if not recording:
        return jsonify({"success": False, "error": "Not recording"})

    try:
        recording = False

        # Wait for recording thread to finish
        if recording_thread:
            recording_thread.join(timeout=5)

        session_id = current_session
        current_session = None

        return jsonify(
            {
                "success": True,
                "session_id": session_id,
                "message": "Recording stopped successfully",
            }
        )

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/status")
def get_status():
    """Get current system status"""
    return jsonify(
        {
            "recording": recording,
            "session_id": current_session,
            "session_name": (
                session_data.get(current_session, {}).get("session_name")
                if current_session
                else None
            ),
            "camera_available": recorder.cap is not None,
        }
    )


@app.route("/recordings")
def get_recordings():
    """Get list of recorded sessions"""
    try:
        recordings = []

        for filename in os.listdir(recordings_dir):
            if filename.endswith(".mp4"):
                filepath = os.path.join(recordings_dir, filename)
                stat = os.stat(filepath)

                # Try to load metadata
                metadata_file = filepath.replace(".mp4", "_metadata.json")
                metadata = None
                if os.path.exists(metadata_file):
                    try:
                        with open(metadata_file, "r") as f:
                            metadata = json.load(f)
                    except:
                        pass

                recordings.append(
                    {
                        "filename": filename,
                        "name": filename.replace(".mp4", "").replace(
                            "session_", "Session "
                        ),
                        "size_mb": round(stat.st_size / (1024 * 1024), 2),
                        "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                        "metadata": metadata,
                    }
                )

        # Sort by creation time (newest first)
        recordings.sort(key=lambda x: x["created"], reverse=True)

        return jsonify(recordings)

    except Exception as e:
        return jsonify({"error": str(e)})


@app.route("/system_info")
def get_system_info():
    """Get system information"""
    try:
        info = {
            "camera_status": "Available" if recorder.cap else "Not initialized",
            "recordings_directory": os.path.abspath(recordings_dir),
            "total_sessions": len(
                [f for f in os.listdir(recordings_dir) if f.endswith(".mp4")]
            ),
            "current_session": current_session,
            "recording_status": "Recording" if recording else "Idle",
            "opencv_version": cv2.__version__,
            "timestamp": datetime.now().isoformat(),
        }

        return jsonify(info)

    except Exception as e:
        return jsonify({"error": str(e)})


def cleanup_on_exit():
    """Clean up resources on exit"""
    global recording
    recording = False
    recorder.cleanup()


if __name__ == "__main__":
    import atexit

    atexit.register(cleanup_on_exit)

    print("🏆 SportsCam Laptop Testing Server")
    print("=" * 40)
    print("Starting server...")
    print("Camera initializing...")

    # Initialize camera
    if recorder.start_camera():
        print("✅ Camera initialized successfully")
    else:
        print("❌ Camera initialization failed")

    print("\n🌐 Access the dashboard at: http://localhost:5000")
    print("📹 Use the web interface to start/stop recordings")
    print("📁 Recordings will be saved in:", os.path.abspath(recordings_dir))
    print("\nPress Ctrl+C to stop the server")
    print("=" * 40)

    try:
        app.run(host="0.0.0.0", port=5000, debug=True, threaded=True)
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
        cleanup_on_exit()
