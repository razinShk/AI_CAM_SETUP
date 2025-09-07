#!/usr/bin/env python3
"""
Phone Display App - Show tracking results on phone screen
"""

import cv2
import numpy as np
import socket
import threading
import json
import base64
import time
from flask import Flask, render_template_string, jsonify, request
import logging

# Disable Flask logs
logging.getLogger("werkzeug").setLevel(logging.ERROR)

app = Flask(__name__)


class PhoneDisplayServer:
    """Server to send tracking results to phone display"""

    def __init__(self, port=5001):
        self.port = port
        self.latest_frame = None
        self.latest_detections = []
        self.detection_stats = {}
        self.frame_count = 0

    def update_frame(self, frame, detections):
        """Update the frame and detections to display on phone"""
        # Encode frame for web display
        _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        self.latest_frame = base64.b64encode(buffer).decode()
        self.latest_detections = detections
        self.frame_count += 1

        # Update stats
        self.detection_stats = {
            "total_objects": len(detections),
            "frame_count": self.frame_count,
            "timestamp": time.strftime("%H:%M:%S"),
        }

        # Count by category
        categories = {}
        for det in detections:
            category = det.get("category", "other")
            categories[category] = categories.get(category, 0) + 1
        self.detection_stats["categories"] = categories


# Global server instance
phone_server = PhoneDisplayServer()


@app.route("/")
def phone_display():
    """Main phone display page"""
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>📱 Object Tracking Display</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {
                margin: 0;
                padding: 10px;
                background: #000;
                color: #fff;
                font-family: Arial, sans-serif;
            }
            .header {
                text-align: center;
                padding: 10px;
                background: #1a1a1a;
                border-radius: 10px;
                margin-bottom: 10px;
            }
            .video-container {
                text-align: center;
                margin-bottom: 10px;
            }
            .video-frame {
                max-width: 100%;
                border-radius: 10px;
                border: 2px solid #333;
            }
            .stats {
                background: #1a1a1a;
                padding: 15px;
                border-radius: 10px;
                margin-bottom: 10px;
            }
            .stat-item {
                display: flex;
                justify-content: space-between;
                margin: 5px 0;
                padding: 5px;
                background: #2a2a2a;
                border-radius: 5px;
            }
            .category {
                display: inline-block;
                margin: 3px;
                padding: 5px 10px;
                border-radius: 15px;
                font-size: 12px;
            }
            .people { background: #4CAF50; }
            .vehicles { background: #2196F3; }
            .animals { background: #FF9800; }
            .electronics { background: #E91E63; }
            .other { background: #9E9E9E; }
            .controls {
                text-align: center;
                padding: 10px;
            }
            .btn {
                background: #4CAF50;
                color: white;
                border: none;
                padding: 10px 20px;
                margin: 5px;
                border-radius: 5px;
                font-size: 16px;
            }
            .fullscreen-btn {
                position: fixed;
                top: 10px;
                right: 10px;
                background: #333;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 50%;
                font-size: 20px;
            }
        </style>
    </head>
    <body>
        <button class="fullscreen-btn" onclick="toggleFullscreen()">⛶</button>
        
        <div class="header">
            <h2>📱 Live Object Tracking</h2>
            <div id="connection-status">🔄 Connecting...</div>
        </div>
        
        <div class="video-container">
            <img id="video-frame" class="video-frame" src="" alt="Waiting for video...">
        </div>
        
        <div class="stats">
            <h3>📊 Detection Stats</h3>
            <div class="stat-item">
                <span>Objects Detected:</span>
                <span id="total-objects">0</span>
            </div>
            <div class="stat-item">
                <span>Frames Processed:</span>
                <span id="frame-count">0</span>
            </div>
            <div class="stat-item">
                <span>Last Update:</span>
                <span id="timestamp">--:--:--</span>
            </div>
            
            <div id="categories" style="margin-top: 10px;">
                <!-- Categories will be populated here -->
            </div>
        </div>
        
        <div class="controls">
            <button class="btn" onclick="toggleFullscreen()">🔍 Fullscreen</button>
            <button class="btn" onclick="saveScreenshot()">📸 Screenshot</button>
        </div>
        
        <script>
            function updateDisplay() {
                fetch('/api/frame')
                    .then(response => response.json())
                    .then(data => {
                        if (data.frame) {
                            document.getElementById('video-frame').src = 'data:image/jpeg;base64,' + data.frame;
                            document.getElementById('connection-status').innerHTML = '🟢 Connected';
                            document.getElementById('connection-status').style.color = '#4CAF50';
                        }
                        
                        if (data.stats) {
                            document.getElementById('total-objects').textContent = data.stats.total_objects;
                            document.getElementById('frame-count').textContent = data.stats.frame_count;
                            document.getElementById('timestamp').textContent = data.stats.timestamp;
                            
                            // Update categories
                            const categoriesDiv = document.getElementById('categories');
                            categoriesDiv.innerHTML = '';
                            if (data.stats.categories) {
                                for (const [category, count] of Object.entries(data.stats.categories)) {
                                    const span = document.createElement('span');
                                    span.className = 'category ' + category;
                                    span.textContent = category + ': ' + count;
                                    categoriesDiv.appendChild(span);
                                }
                            }
                        }
                    })
                    .catch(error => {
                        document.getElementById('connection-status').innerHTML = '🔴 Disconnected';
                        document.getElementById('connection-status').style.color = '#f44336';
                    });
            }
            
            function toggleFullscreen() {
                if (!document.fullscreenElement) {
                    document.documentElement.requestFullscreen();
                } else {
                    document.exitFullscreen();
                }
            }
            
            function saveScreenshot() {
                const frame = document.getElementById('video-frame');
                const link = document.createElement('a');
                link.download = 'tracking_' + Date.now() + '.jpg';
                link.href = frame.src;
                link.click();
            }
            
            // Update every 100ms for smooth display
            setInterval(updateDisplay, 100);
            
            // Initial update
            updateDisplay();
        </script>
    </body>
    </html>
    """
    return html_template


@app.route("/api/frame")
def get_frame():
    """API endpoint to get latest frame and stats"""
    return jsonify(
        {
            "frame": phone_server.latest_frame,
            "stats": phone_server.detection_stats,
            "detections": phone_server.latest_detections,
        }
    )


def start_phone_display_server():
    """Start the phone display server"""
    print("📱 Starting phone display server...")
    print("📋 Phone Display Setup:")
    print("   1. Connect phone to same WiFi as laptop")
    print("   2. Find your laptop IP address:")
    print("      Windows: ipconfig")
    print("      Mac/Linux: ifconfig")
    print("   3. Open browser on phone")
    print("   4. Go to: http://YOUR_LAPTOP_IP:5001")
    print("   5. Bookmark for easy access")
    print()

    # Get local IP
    import socket

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        print(f"📱 Your laptop IP: {local_ip}")
        print(f"📱 Phone URL: http://{local_ip}:5001")
    except:
        print("📱 Could not detect IP automatically")
    finally:
        s.close()

    print("\n🚀 Starting server on port 5001...")
    app.run(host="0.0.0.0", port=5001, debug=False)


if __name__ == "__main__":
    start_phone_display_server()
