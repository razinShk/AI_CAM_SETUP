# 📱 Phone Camera Setup Guide

## 🎯 **Use Phone Camera for Object Tracking**

### **Method 1: USB Connection (Recommended)**

#### **Step 1: Enable Developer Mode on Phone**
1. **Android**: Settings → About Phone → Tap "Build Number" 7 times
2. **iPhone**: Connect and trust computer

#### **Step 2: Enable USB Debugging (Android)**
1. Settings → Developer Options → USB Debugging → ON
2. Connect USB cable
3. Select "File Transfer" mode

#### **Step 3: Install Phone Camera App**
**Option A: DroidCam (Best for USB)**
- Download "DroidCam" on phone and computer
- Connect via USB
- Phone becomes webcam automatically

**Option B: IP Webcam (WiFi)**
- Install "IP Webcam" on Android
- Start camera server
- Note phone IP address

#### **Step 4: Test Phone Camera**
```bash
# Find available cameras
python camera_selector.py

# Should show:
# Camera 0: Built-in Camera (Laptop) 
# Camera 1: External Camera #1 (USB/Phone)  ← Your phone
```

#### **Step 5: Use Phone Camera**
```bash
# Use phone camera with fast mode
python football_tracker.py --offline --camera 1 --fast

# If camera 1 doesn't work, try camera 2
python football_tracker.py --offline --camera 2 --fast
```

### **Method 2: WiFi IP Camera**

#### **Setup:**
1. Install "IP Webcam" on Android
2. Start IP camera
3. Note IP address (e.g., 192.168.1.100)
4. Run: `python phone_stream_server.py --phone-ip 192.168.1.100`

### **Expected Results with Phone Camera:**
- ✅ **Higher resolution**: 1280x720+ vs 640x480
- ✅ **Better image quality**: Phone cameras are superior
- ✅ **Better object detection**: Higher quality = more accurate
- ✅ **Same tracking interface**: Everything else works the same

## 🔧 **Troubleshooting Phone Camera**

### **Phone Not Detected:**
```bash
# 1. Check camera detection
python camera_selector.py

# 2. Try different camera indices
python football_tracker.py --offline --camera 0 --fast  # Laptop
python football_tracker.py --offline --camera 1 --fast  # Phone
python football_tracker.py --offline --camera 2 --fast  # Phone alt

# 3. Check USB connection
# - Try different USB cable
# - Try different USB port
# - Restart both devices
```

### **Poor Performance:**
```bash
# Use fast mode for better FPS
python football_tracker.py --offline --camera 1 --fast
```
