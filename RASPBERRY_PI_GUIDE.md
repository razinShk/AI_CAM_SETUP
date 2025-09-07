# 🍓 **Raspberry Pi 5 + IMX500 AI Camera Guide**

## 🎯 **Optimized Setup for Maximum AI Performance**

This setup leverages the **IMX500's dedicated neural processor** for AI inference, leaving your **Raspberry Pi 5 CPU free** for tracking and display tasks only.

---

## 🧠 **How It Works**

### **Traditional Setup (CPU-Heavy):**
```
Camera → Pi CPU → AI Processing → Object Detection → Tracking
```
**Problem:** Pi CPU handles everything = slow performance

### **IMX500 Optimized Setup (Efficient):**
```
IMX500 Camera → Built-in AI Processor → Object Detection → Pi CPU → Tracking Only
```
**Result:** AI processing happens on camera, Pi CPU handles lightweight tracking = **fast performance**

---

## 📋 **Hardware Requirements**

### **Essential:**
- ✅ **Raspberry Pi 5** (4GB+ RAM recommended)
- ✅ **IMX500 AI Camera module** 
- ✅ **MicroSD card** (32GB+ Class 10)
- ✅ **Power supply** (5V 3A minimum)

### **Optional:**
- 📺 **Monitor** (for live preview)
- 🖱️ **Keyboard/Mouse** (for setup)
- 📶 **WiFi/Ethernet** (for remote access)
- 💾 **External storage** (for recordings)

---

## 🔧 **Automatic Setup**

### **Method 1: One-Command Setup (Recommended)**
```bash
# Download and run automated setup
wget https://raw.githubusercontent.com/your-repo/main/raspberry_pi_setup.py
python3 raspberry_pi_setup.py
```

### **Method 2: Manual Setup**
```bash
# 1. Clone repository
git clone <your-repo-url>
cd ai-cam

# 2. Run setup script
python3 raspberry_pi_setup.py

# 3. Follow prompts and reboot when asked
sudo reboot
```

---

## 🚀 **Usage**

### **Quick Start:**
```bash
# Start with default settings
./start_tracker.sh

# Or directly:
python3 raspberry_pi_tracker.py
```

### **Advanced Usage:**
```bash
# Use specific model
python3 raspberry_pi_tracker.py --model yolo11s

# Record video
python3 raspberry_pi_tracker.py --record tracking.mp4

# Headless mode (no display)
python3 raspberry_pi_tracker.py --no-preview

# Headless with recording
./start_headless.sh
```

### **Service Mode (Auto-start):**
```bash
# Install as system service
sudo cp pi-ai-tracker.service /etc/systemd/system/
sudo systemctl enable pi-ai-tracker
sudo systemctl start pi-ai-tracker

# Check status
sudo systemctl status pi-ai-tracker

# View logs
journalctl -u pi-ai-tracker -f
```

---

## 🧠 **Available AI Models**

### **IMX500-Optimized Models:**

| Model | Size | Speed | Accuracy | Use Case |
|-------|------|-------|----------|----------|
| **yolo11n** | Small | ⚡⚡⚡ | ⭐⭐⭐ | Real-time tracking |
| **yolo11s** | Medium | ⚡⚡ | ⭐⭐⭐⭐ | Balanced performance |
| **yolov8n** | Small | ⚡⚡⚡ | ⭐⭐⭐ | Legacy support |
| **yolov8s** | Medium | ⚡⚡ | ⭐⭐⭐⭐ | Higher accuracy |

### **Model Selection:**
```bash
# For maximum speed
python3 raspberry_pi_tracker.py --model yolo11n

# For best accuracy
python3 raspberry_pi_tracker.py --model yolo11s
```

---

## 🎮 **Controls & Features**

### **Keyboard Controls (Preview Mode):**
- **Q**: Quit application
- **R**: Reset tracking
- **S**: Save screenshot

### **Features:**
- ✅ **Real-time object detection** (80+ object types)
- ✅ **Multi-object tracking** with IDs
- ✅ **Category-based visualization** (people, vehicles, etc.)
- ✅ **Performance monitoring** (FPS, object counts)
- ✅ **Video recording** with tracking overlays
- ✅ **Screenshot capture** with timestamp
- ✅ **Headless operation** for remote deployment

---

## 📊 **Performance Optimization**

### **IMX500 Neural Processor Benefits:**
- 🧠 **Dedicated AI hardware** - no CPU overhead
- ⚡ **Fast inference** - optimized neural processing
- 🔋 **Power efficient** - specialized AI chip
- 🌡️ **Cool operation** - offloads heat from Pi CPU

### **Expected Performance:**
- 📹 **30 FPS** real-time tracking
- 💻 **Low Pi CPU usage** (tracking only)
- 🧠 **AI processing** entirely on camera
- 📊 **Multiple objects** tracked simultaneously

### **CPU Usage Comparison:**
| Setup | CPU Usage | FPS | AI Location |
|-------|-----------|-----|-------------|
| **CPU-based** | 80-95% | 5-10 | Pi CPU |
| **IMX500-based** | 15-30% | 25-30 | Camera |

---

## 🔧 **Configuration Files**

### **Camera Settings:**
Edit `/boot/config.txt`:
```bash
# AI Camera Configuration
camera_auto_detect=1
dtoverlay=imx500,media-controller=0
gpu_mem=128
start_x=1
```

### **Model Configuration:**
Edit `config.py`:
```python
MODELS = {
    "yolo11n": {
        "path": "models/yolo11n_224x224.rpk",
        "input_size": (224, 224),
        "confidence_threshold": 0.5
    }
}
```

---

## 🐛 **Troubleshooting**

### **Camera Not Detected:**
```bash
# Check camera connection
vcgencmd get_camera

# Check for IMX500
dmesg | grep -i imx500

# Verify config
cat /boot/config.txt | grep -i camera
```

### **Model Not Loading:**
```bash
# Check model files
ls -la models/

# Download models
git clone https://github.com/raspberrypi/imx500-models.git
cp imx500-models/*.rpk models/
```

### **Performance Issues:**
```bash
# Check system load
htop

# Monitor AI inference
python3 raspberry_pi_tracker.py --verbose

# Check temperature
vcgencmd measure_temp
```

### **Permission Issues:**
```bash
# Add user to camera group
sudo usermod -a -G video $USER

# Set camera permissions
sudo chmod 666 /dev/video*
```

---

## 📱 **Remote Access & Control**

### **SSH Access:**
```bash
# Enable SSH
sudo systemctl enable ssh
sudo systemctl start ssh

# Connect from remote
ssh pi@<raspberry-pi-ip>
```

### **VNC for GUI:**
```bash
# Enable VNC
sudo raspi-config
# Interface Options → VNC → Enable

# Connect with VNC viewer to see live preview
```

### **Web Interface (Optional):**
```bash
# Start with web interface
python3 raspberry_pi_tracker.py --web-interface

# Access from browser: http://<pi-ip>:5000
```

---

## 📊 **Monitoring & Logging**

### **Real-time Monitoring:**
```bash
# View live logs
journalctl -u pi-ai-tracker -f

# Performance monitoring
htop

# Camera status
vcgencmd get_camera
```

### **Log Files:**
- 📝 **System logs**: `/var/log/syslog`
- 📊 **Application logs**: `journalctl -u pi-ai-tracker`
- 📹 **Recording files**: Current directory
- 📸 **Screenshots**: `pi_tracking_YYYYMMDD_HHMMSS.jpg`

---

## 🎯 **Use Cases**

### **Security Monitoring:**
```bash
# Continuous recording with motion detection
python3 raspberry_pi_tracker.py --no-preview --record security.mp4
```

### **Wildlife Tracking:**
```bash
# Outdoor wildlife monitoring
python3 raspberry_pi_tracker.py --model yolo11s --record wildlife.mp4
```

### **Traffic Analysis:**
```bash
# Vehicle and pedestrian counting
python3 raspberry_pi_tracker.py --model yolo11n --no-preview
```

### **Research & Development:**
```bash
# Data collection with detailed logging
python3 raspberry_pi_tracker.py --verbose --record data.mp4
```

---

## 🔋 **Power & Deployment**

### **Power Requirements:**
- **Minimum**: 5V 3A power supply
- **Recommended**: 5V 3.5A for stable operation
- **Battery**: Use UPS HAT for portable deployment

### **Outdoor Deployment:**
- 🌡️ **Temperature range**: -10°C to 50°C
- 💧 **Weatherproof case** recommended
- 🔋 **Solar power** compatible with proper battery system
- 📶 **4G/WiFi** for remote monitoring

---

## 🎉 **Summary**

This setup gives you:
- 🧠 **Professional AI performance** with minimal Pi CPU load
- ⚡ **30 FPS real-time tracking** using camera's neural processor
- 📹 **High-quality recordings** with tracking overlays
- 🔧 **Easy deployment** with automated setup
- 📊 **Enterprise-grade monitoring** and logging
- 🍓 **Optimized for Raspberry Pi 5** + IMX500 combination

Perfect for security systems, research projects, wildlife monitoring, or any application requiring efficient AI-powered object tracking! 🎯
