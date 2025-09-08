# 🏆 SportsCam Laptop Testing

This folder contains a simplified version of the SportsCam system that runs on your laptop using your webcam. Perfect for testing the core functionality before deploying to Raspberry Pi.

## 🎯 What This Tests

- ✅ **Camera recording** using laptop webcam
- ✅ **Web dashboard** for starting/stopping recordings
- ✅ **Session management** with metadata
- ✅ **Video storage** and file management
- ✅ **Real-time status** updates

## 🚀 Quick Start

### Windows:
```bash
# Run the setup script
setup_laptop_test.bat

# Or manually:
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python laptop_server.py
```

### Linux/Mac:
```bash
# Run the setup script
chmod +x setup_laptop_test.sh
./setup_laptop_test.sh

# Or manually:
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python laptop_server.py
```

## 🌐 Access the Dashboard

1. **Start the server**: `python laptop_server.py`
2. **Open browser**: Go to `http://localhost:5000`
3. **Test recording**: Click "Start Recording" → Enter session name → Start recording
4. **View recordings**: See recorded videos in the dashboard

## 📁 File Structure

```
laptop_testing/
├── laptop_server.py          # Main server (Flask app)
├── requirements.txt          # Python dependencies
├── setup_laptop_test.bat     # Windows setup script
├── setup_laptop_test.sh      # Linux/Mac setup script
├── README.md                 # This file
└── recordings/               # Created automatically
    ├── session_*.mp4         # Video recordings
    └── session_*_metadata.json # Session metadata
```

## 🔧 Features

### Web Dashboard
- **Real-time status** showing recording state
- **Start/Stop controls** for recording sessions
- **Session management** with custom names
- **Recordings list** showing all saved videos
- **System information** display

### Recording System
- **Webcam capture** at 1280x720 resolution
- **MP4 video encoding** with 30 FPS
- **Background recording** using threading
- **Metadata storage** for each session
- **Automatic file management**

### API Endpoints
- `GET /` - Web dashboard
- `POST /start_recording` - Start recording session
- `POST /stop_recording` - Stop current recording
- `GET /status` - Get system status
- `GET /recordings` - List all recordings
- `GET /system_info` - System information

## 🎮 How to Test

### Basic Recording Test:
1. Start the server
2. Open dashboard in browser
3. Click "Start Recording"
4. Enter session name (e.g., "Test Match 1")
5. Wait 30 seconds
6. Click "Stop Recording"
7. Check recordings list for your video

### Multiple Sessions Test:
1. Record multiple short sessions
2. Verify each gets unique filename
3. Check metadata is saved correctly
4. Confirm file sizes are reasonable

### Status Monitoring:
1. Watch real-time status updates
2. Verify recording indicator works
3. Check system info displays correctly

## 🔍 Troubleshooting

### Camera Issues:
```python
# Test camera manually
import cv2
cap = cv2.VideoCapture(0)
print("Camera available:", cap.isOpened())
cap.release()
```

### Port Already in Use:
```bash
# Change port in laptop_server.py
app.run(host='0.0.0.0', port=5001, debug=True, threaded=True)
```

### Dependencies Issues:
```bash
# Reinstall dependencies
pip uninstall opencv-python
pip install opencv-python==4.8.1.78
```

## 📊 Expected Output

### Console Output:
```
🏆 SportsCam Laptop Testing Server
========================================
Starting server...
Camera initializing...
✅ Camera initialized successfully

🌐 Access the dashboard at: http://localhost:5000
📹 Use the web interface to start/stop recordings
📁 Recordings will be saved in: /path/to/recordings
```

### Dashboard Features:
- **Green status** when ready
- **Red status** when recording
- **Session info** during recording
- **Recordings list** with file details
- **System info** in JSON format

## 🔄 Testing Workflow

1. **Setup**: Run setup script
2. **Start**: Launch laptop_server.py
3. **Test**: Use web dashboard to record
4. **Verify**: Check recordings folder
5. **Iterate**: Test different scenarios

## 🎯 What This Simulates

This laptop testing environment simulates the core SportsCam workflow:

```
Web Dashboard → Start Recording → Laptop Camera → Save Video → Display Results
     ↓              ↓                    ↓            ↓             ↓
(Same as real)  (Same as real)    (Webcam instead  (Local storage (Same as real)
                                   of Pi camera)    instead of 
                                                   Supabase)
```

## ✅ Success Criteria

You'll know it's working when:
- ✅ Camera initializes without errors
- ✅ Web dashboard loads at localhost:5000
- ✅ Recording starts/stops via web interface
- ✅ Video files are created in recordings/
- ✅ Status updates in real-time
- ✅ Multiple sessions work correctly

## 🚀 Next Steps

Once laptop testing works:
1. **Deploy to Raspberry Pi** using the main SportsCam files
2. **Connect to Supabase** for cloud storage
3. **Add AI tracking** with the enhanced football tracker
4. **Test mobile PWA** for highlight sharing

This testing environment gives you confidence that the core system works before moving to production hardware! 🎉
