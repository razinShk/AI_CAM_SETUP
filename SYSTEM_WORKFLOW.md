# 🏆 SportsCam System Workflow & Code Explanation

This document explains the complete workflow of how your SportsCam system works, from player interaction to highlight generation.

## 🔄 **Complete System Workflow**

### **Phase 1: Setup & Registration**
```
1. Turf Owner → Sets up Raspberry Pi → Runs pi_setup.sh
2. Pi connects to Supabase → Registers camera → Updates turf status to "online"
3. Turf Owner → Opens web dashboard → Sees camera status
```

### **Phase 2: Game Recording**
```
Player/Turf Owner → Web Dashboard → Clicks "Start Recording"
    ↓
Web sends API call to Supabase → Creates game session
    ↓
Raspberry Pi polls Supabase → Detects new session → Starts camera recording
    ↓
Pi runs AI tracking (YOLO + MediaPipe) → Saves tracking data
    ↓
Game ends → Pi stops recording → Uploads video to Supabase Storage
```

### **Phase 3: AI Processing & Highlights**
```
Pi finishes upload → Triggers highlight processing
    ↓
AI Highlight Processor analyzes video → Detects events (goals, saves, skills)
    ↓
Creates highlight clips → Generates thumbnails → Uploads to Supabase
    ↓
Updates database with highlight metadata
```

### **Phase 4: Player Access**
```
Players → Open mobile PWA → Browse highlights from their session
    ↓
Select highlight → Share as social post → Add caption
    ↓
Other players see in feed → Like, comment, share
```

---

## 📁 **Code Structure & What Runs Where**

### **🖥️ On Your Development Machine**
```bash
# 1. Setup files locally
.env.example                    # Environment template
supabase/schema.sql            # Database structure
supabase/sample_data.sql       # Demo data
supabase_client.py             # Supabase integration
requirements-supabase.txt      # Python dependencies
pi_setup.sh                    # Raspberry Pi setup script
deploy.md                      # Deployment guide

# 2. Frontend files (deploy to Vercel/Netlify)
frontend/index.html            # Turf owner dashboard
frontend/mobile.html           # Player PWA
frontend/js/app.js            # Dashboard logic
frontend/js/mobile-app.js     # Mobile app logic
frontend/manifest.json         # PWA configuration
frontend/sw.js                # Service worker
```

### **🍓 On Raspberry Pi**
```bash
# Core system files
raspberry_pi_server.py         # Main camera server
enhanced_football_tracker.py   # AI tracking engine
ai_highlight_processor.py      # Highlight generation
supabase_client.py            # Database communication

# Configuration
.env                          # Pi-specific settings (CAMERA_ID, TURF_ID)
requirements-raspberry-pi.txt  # Pi dependencies
requirements-supabase.txt     # Supabase dependencies

# Runtime directories
/recordings/                  # Local video storage
/uploads/                     # Processed videos
/tracking_data/              # AI tracking results
/highlights/                 # Generated highlight clips
/logs/                       # System logs
```

### **☁️ On Supabase Cloud**
```sql
-- Database tables (from schema.sql)
profiles                      # User accounts
turf_locations               # Turf information
game_sessions               # Recording sessions
highlights                  # Generated clips
social_posts               # Player shares
comments, likes            # Social interactions

-- Storage buckets
videos/                    # Full game recordings
highlights/               # Highlight clips
thumbnails/              # Video thumbnails
```

---

## 🚀 **Detailed Step-by-Step Workflow**

### **Step 1: Initial Setup**

**On Raspberry Pi:**
```bash
# 1. Clone your repository
git clone https://github.com/your-username/ai-cam.git
cd ai-cam

# 2. Run setup script
chmod +x pi_setup.sh
./pi_setup.sh

# 3. Configure environment
nano .env
# Set: CAMERA_ID=turf_1_camera_1, TURF_ID=your-turf-uuid

# 4. Start camera server
python raspberry_pi_server.py
```

**What happens:**
- Pi installs dependencies, sets up camera permissions
- `supabase_client.py` registers camera with main system
- `raspberry_pi_server.py` starts Flask server on Pi
- Turf status updates to "online" in database

### **Step 2: Game Session Management**

**Player/Owner opens web dashboard:**
```javascript
// frontend/js/app.js
function startRecording() {
    // Creates new session in Supabase
    const session = await supabase
        .from('game_sessions')
        .insert({
            turf_id: currentTurfId,
            session_name: 'Evening Match',
            status: 'recording'
        });
}
```

**Raspberry Pi detects new session:**
```python
# raspberry_pi_server.py
def check_for_sessions():
    # Polls Supabase every 10 seconds
    sessions = supabase_client.get_active_sessions()
    if sessions:
        start_recording(session_id)

def start_recording(session_id):
    # Starts camera recording
    camera.start_recording(f'/recordings/session_{session_id}.mp4')
    # Starts AI tracking
    tracker.start_tracking()
```

### **Step 3: AI Tracking During Game**

**Real-time processing:**
```python
# enhanced_football_tracker.py
class FootballTracker:
    def process_frame(self, frame):
        # 1. YOLO detects players and ball
        detections = self.model(frame)
        
        # 2. Track objects across frames
        tracks = self.tracker.update(detections)
        
        # 3. Analyze player poses with MediaPipe
        poses = self.pose_detector.process(frame)
        
        # 4. Detect events (goals, saves, skills)
        events = self.event_detector.analyze(tracks, poses)
        
        # 5. Save tracking data
        self.save_tracking_data(events, timestamp)
```

### **Step 4: Highlight Generation**

**After game ends:**
```python
# ai_highlight_processor.py
class AIHighlightProcessor:
    def process_video(self, video_path, session_id):
        # 1. Load tracking data
        events = self.load_tracking_data(session_id)
        
        # 2. Score video segments
        segments = self.score_segments(events)
        
        # 3. Generate highlights
        for segment in high_scoring_segments:
            highlight = self.create_highlight_clip(segment)
            thumbnail = self.generate_thumbnail(highlight)
            
            # 4. Upload to Supabase
            supabase_client.upload_highlight(highlight, thumbnail)
```

### **Step 5: Player Mobile Experience**

**Players access highlights:**
```javascript
// frontend/js/mobile-app.js
async function loadHighlights() {
    // Fetch highlights from Supabase
    const { data } = await supabase
        .from('highlights')
        .select('*')
        .order('created_at', { ascending: false });
    
    // Display in Instagram-like feed
    displayHighlights(data);
}

function shareHighlight(highlightId) {
    // Create social post
    await supabase
        .from('social_posts')
        .insert({
            user_id: currentUser.id,
            highlight_id: highlightId,
            caption: userCaption
        });
}
```

---

## 🔧 **Key Components Explained**

### **1. Supabase Client (`supabase_client.py`)**
```python
class SupabaseClient:
    def register_camera(self):
        # Updates turf status to "online"
    
    def create_session(self, name):
        # Creates new recording session
    
    def upload_video(self, path, session_id):
        # Uploads to Supabase Storage
    
    def heartbeat(self):
        # Keeps camera status updated
```

### **2. Raspberry Pi Server (`raspberry_pi_server.py`)**
```python
# Flask routes for camera control
@app.route('/start_recording', methods=['POST'])
@app.route('/stop_recording', methods=['POST'])
@app.route('/status', methods=['GET'])

# Background tasks
- Session polling (every 10s)
- Heartbeat sending (every 30s)
- Video processing queue
```

### **3. AI Tracking (`enhanced_football_tracker.py`)**
```python
class FootballEventDetector:
    def detect_goal(self):
        # Ball near goal + celebration poses
    
    def detect_save(self):
        # Goalkeeper dive + ball trajectory change
    
    def detect_skill_move(self):
        # Rapid direction changes + close ball control
```

### **4. Web Dashboard (`frontend/js/app.js`)**
```javascript
// Real-time features
- Camera status monitoring
- Session management
- Live recording controls
- Highlight preview
```

### **5. Mobile PWA (`frontend/js/mobile-app.js`)**
```javascript
// Instagram-like features
- Vertical video feed
- Social interactions (like, comment, share)
- Offline caching
- Push notifications
```

---

## 📊 **Data Flow Architecture**

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Web Dashboard │    │   Supabase DB    │    │  Raspberry Pi   │
│                 │    │                  │    │                 │
│ 1. Start Record ├───►│ 2. Create Session├───►│ 3. Poll & Start │
│                 │    │                  │    │                 │
│ 8. View Results │◄───┤ 7. Store Results │◄───┤ 4. AI Tracking  │
└─────────────────┘    │                  │    │                 │
                       │ 6. Upload Files  │◄───┤ 5. Process Video│
┌─────────────────┐    │                  │    └─────────────────┘
│   Mobile PWA    │    │                  │
│                 │    │                  │
│ 9. Browse Feed  ├───►│ 10. Social Posts │
│                 │    │                  │
│ 11. Share Clips │───►│ 12. Interactions │
└─────────────────┘    └──────────────────┘
```

---

## 🎯 **Deployment Order**

### **1. First: Setup Supabase**
```bash
# Run in Supabase SQL Editor
1. supabase/schema.sql       # Create tables
2. supabase/sample_data.sql  # Add demo data
3. Create storage buckets: videos, highlights, thumbnails
```

### **2. Second: Deploy Frontend**
```bash
# Deploy to Vercel/Netlify
1. Upload frontend/ folder
2. Configure environment variables
3. Test web dashboard
```

### **3. Third: Setup Raspberry Pi**
```bash
# On each Pi
1. git clone your-repo
2. ./pi_setup.sh
3. Edit .env with Pi-specific settings
4. python raspberry_pi_server.py
```

### **4. Fourth: Test Complete Flow**
```bash
1. Open web dashboard
2. Start recording session
3. Let Pi record for a few minutes
4. Stop recording
5. Wait for highlight processing
6. Check mobile PWA for highlights
```

---

## 🚨 **Troubleshooting Commands**

### **Check Pi Status:**
```bash
# On Raspberry Pi
sudo systemctl status sportscam-camera
sudo journalctl -u sportscam-camera -f
python -c "from supabase_client import get_supabase_client; print(get_supabase_client().heartbeat())"
```

### **Check Database:**
```sql
-- In Supabase SQL Editor
SELECT * FROM turf_locations WHERE camera_status = 'online';
SELECT * FROM game_sessions ORDER BY created_at DESC LIMIT 5;
SELECT * FROM highlights ORDER BY created_at DESC LIMIT 5;
```

### **Check Storage:**
```bash
# In Supabase Dashboard > Storage
- videos/ bucket should have game recordings
- highlights/ bucket should have clips
- thumbnails/ bucket should have preview images
```

---

## 🔀 **File Dependencies Map**

### **Core Dependencies:**
```
raspberry_pi_server.py
├── supabase_client.py
├── enhanced_football_tracker.py
└── ai_highlight_processor.py

enhanced_football_tracker.py
├── YOLO models (ultralytics)
├── MediaPipe (pose detection)
└── OpenCV (video processing)

ai_highlight_processor.py
├── FFmpeg (video editing)
├── OpenCV (frame analysis)
└── supabase_client.py

Frontend Dashboard
├── Supabase JS client
├── Bootstrap/Tailwind CSS
└── Modern browser APIs

Mobile PWA
├── Service Worker (sw.js)
├── Web App Manifest
└── Supabase JS client
```

### **Environment Files:**
```
.env (on Pi)
├── SUPABASE_URL
├── SUPABASE_ANON_KEY
├── CAMERA_ID
├── TURF_ID
└── Local paths

Frontend Environment
├── SUPABASE_URL
├── SUPABASE_ANON_KEY
└── API endpoints
```

---

## 🎬 **User Journey Examples**

### **Scenario 1: Weekend Tournament**
```
1. Tournament organizer opens web dashboard
2. Creates session: "Weekend Cup - Semi Final"
3. Players arrive, Pi automatically starts recording
4. 60-minute match with multiple goals and saves
5. Pi processes video, generates 8 highlight clips
6. Players get notification on mobile app
7. Players share highlights with custom captions
8. Highlights go viral on social feed
```

### **Scenario 2: Training Session**
```
1. Coach starts "Skill Training - Dribbling"
2. Pi tracks individual player movements
3. AI detects skill moves, close ball control
4. Generates personalized highlights for each player
5. Players review their performance
6. Coach analyzes team patterns from full recording
```

### **Scenario 3: Casual Match**
```
1. Friends book turf for casual game
2. Use mobile app to start recording
3. Pi captures 30-minute match
4. AI generates best moments automatically
5. Group shares memories on social feed
6. Friends from other turfs see and comment
```

---

## 🔧 **System Requirements**

### **Raspberry Pi Requirements:**
- Raspberry Pi 5 (8GB recommended)
- IMX500 AI Camera module
- 64GB+ microSD card (Class 10)
- Stable internet connection
- Power supply with backup

### **Network Requirements:**
- Minimum 50 Mbps upload speed
- Low latency internet connection
- Port forwarding for remote access
- Static IP (recommended)

### **Browser Requirements:**
- Modern browsers (Chrome 90+, Firefox 88+, Safari 14+)
- WebRTC support for real-time features
- Local storage for PWA caching
- Push notification support

This complete workflow ensures your SportsCam system works seamlessly from recording to social sharing! 🎉

**Ready to deploy? Follow the steps in `deploy.md` for the complete setup process.**
