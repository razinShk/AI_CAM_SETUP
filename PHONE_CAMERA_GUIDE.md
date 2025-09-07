# 📱 Phone Camera Setup Guide

## 🎯 **Use Your Phone Camera for Object Tracking**

Your phone camera typically has better resolution and quality than laptop cameras! Here's how to set it up:

## 📋 **Step 1: Phone Setup**

### **Android Phones:**
1. **Enable Developer Options:**
   - Go to `Settings > About Phone`
   - Tap "Build Number" 7 times
   - Go back to `Settings > Developer Options`

2. **Enable USB Debugging:**
   - In Developer Options, turn on "USB Debugging"
   - Select "Always allow from this computer" when prompted

3. **Connect via USB:**
   - Use a **good quality USB cable**
   - Connect phone to laptop
   - Select "File Transfer (MTP)" or "Camera (PTP)" mode

### **iPhone:**
1. **Connect via USB:**
   - Use Lightning to USB cable
   - Trust the computer when prompted
   - May work with some USB camera apps

## 🔍 **Step 2: Find Your Phone Camera**

### **Auto-Detection (Recommended):**
```bash
# The tracker will automatically prioritize external cameras
python football_tracker.py --offline
```

### **Camera Selector Tool:**
```bash
# See all available cameras and test them
python camera_selector.py
```

### **Manual Camera Selection:**
```bash
# Use specific camera index (usually 1 or 2 for phones)
python football_tracker.py --offline --camera 1
python football_tracker.py --offline --camera 2
```

## 🎮 **Step 3: Usage Examples**

### **Best Quality (Phone Camera Auto-Detect):**
```bash
python football_tracker.py --offline
```
*Will automatically use the highest-quality external camera*

### **Specific Phone Camera:**
```bash
python football_tracker.py --offline --camera 1
```

### **Demo Mode with Phone Camera:**
```bash
python football_tracker.py --offline --camera 1 --demo
```

### **GUI with Phone Camera:**
```bash
python gui.py
# Then select camera index in the interface
```

## 📊 **Camera Quality Comparison**

| Camera Type | Typical Resolution | FPS | Quality |
|-------------|-------------------|-----|---------|
| **Phone Camera** | 1280x720+ | 30+ | ⭐⭐⭐⭐⭐ |
| Laptop Built-in | 640x480 | 30 | ⭐⭐⭐ |
| External Webcam | 1920x1080 | 30+ | ⭐⭐⭐⭐ |

## 🔧 **Troubleshooting**

### **Phone Not Detected:**
```bash
# 1. Check if phone camera is available
python camera_selector.py

# 2. Try different USB modes on phone:
#    - File Transfer (MTP)
#    - Camera (PTP) 
#    - USB Tethering

# 3. Try different camera indices
python football_tracker.py --offline --camera 1
python football_tracker.py --offline --camera 2
python football_tracker.py --offline --camera 3
```

### **Camera Access Denied:**
1. **Close other camera apps** (Zoom, Skype, etc.)
2. **Restart the tracker**
3. **Try different USB port**
4. **Reinstall phone drivers**

### **Poor Performance:**
```bash
# Use lighter model for better FPS
python football_tracker.py --offline --camera 1 --model yolo11n
```

### **Camera Preview Issues:**
```bash
# Test camera directly
python camera_selector.py
# Select your phone camera index
# Choose "Preview camera" to test
```

## 🎉 **Expected Results**

When using phone camera, you should see:
- ✅ **Higher resolution** (1280x720 or better)
- ✅ **Better image quality** and color accuracy
- ✅ **More accurate object detection** due to better camera
- ✅ **Automatic focus** and exposure adjustment
- ✅ **Better low-light performance**

## 📱 **Phone Camera Apps (Advanced)**

For even better results, you can use camera apps that provide USB webcam functionality:

### **Android:**
- **DroidCam** - Turn phone into webcam
- **IP Webcam** - Stream over WiFi/USB
- **EpocCam** - Professional webcam app

### **iPhone:**
- **EpocCam** - High-quality camera streaming
- **Reincubate Camo** - Professional iPhone webcam

These apps often provide better USB camera integration and higher quality streams.

## 🚀 **Quick Start Summary**

1. **Connect phone via USB**
2. **Enable USB debugging** (Android)
3. **Run camera selector:** `python camera_selector.py`
4. **Note your camera index** (usually 1 or 2)
5. **Start tracking:** `python football_tracker.py --offline --camera X`

Your phone camera will give you much better object detection results! 📱✨
