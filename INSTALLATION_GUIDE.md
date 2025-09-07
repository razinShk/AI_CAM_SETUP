# Football Tracker Installation Guide

This guide will help you set up the Football Tracking Software with Raspberry Pi AI Camera (IMX500).

## Hardware Requirements

### Essential
- **Raspberry Pi 5** (recommended) or **Raspberry Pi 4** (minimum 4GB RAM)
- **Raspberry Pi AI Camera (IMX500)** - [Purchase here](https://www.raspberrypi.com/products/ai-camera/)
- MicroSD card (32GB or larger, Class 10)
- Power supply for your Raspberry Pi
- Monitor, keyboard, and mouse for setup

### Optional
- Case for Raspberry Pi
- Tripod or mounting solution for camera positioning
- External storage for video recordings

## Software Setup

### 1. Raspberry Pi OS Installation

1. **Download Raspberry Pi Imager**: https://www.raspberrypi.com/software/
2. **Flash Raspberry Pi OS** (64-bit, latest version) to your MicroSD card
3. **Enable SSH and Camera** in the imager advanced options if needed
4. **Boot your Raspberry Pi** and complete the initial setup

### 2. System Updates

```bash
sudo apt update
sudo apt upgrade -y
sudo reboot
```

### 3. Install AI Camera Support

```bash
# Install IMX500 model files
sudo apt install imx500-models

# Verify installation
ls /usr/share/imx500-models/
```

### 4. Install Football Tracker

#### Option A: Automatic Installation (Recommended)

```bash
# Clone or download the project
git clone <your-repository-url> football-tracker
cd football-tracker

# Run the installation script
chmod +x install.sh
./install.sh
```

#### Option B: Manual Installation

```bash
# Install system dependencies
sudo apt install -y python3-dev python3-pip python3-venv \
    libopencv-dev python3-opencv libatlas-base-dev \
    libjasper-dev libqtgui4 libqt4-test libhdf5-dev

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python packages
pip install -r requirements.txt

# Install picamera2
pip install picamera2

# Set up permissions
sudo usermod -a -G video $USER
```

### 5. Test Installation

```bash
# Activate virtual environment
source venv/bin/activate

# Test basic functionality
python3 football_tracker.py --offline --help
```

## Model Information

The software uses pre-trained models from the [IMX500 Model Zoo](https://github.com/raspberrypi/imx500-models):

### Available Models

| Model    | Accuracy (mAP) | Resolution | Best Use Case |
|----------|----------------|------------|---------------|
| YOLO11n  | 0.374          | 640x640    | Best balance of speed/accuracy |
| YOLOv8n  | 0.279          | 640x640    | Faster processing |

### Model Features
- **Person Detection**: Identifies football players
- **Sports Ball Detection**: Tracks the football/soccer ball
- **Real-time Processing**: Optimized for IMX500 Edge AI Processor
- **Post-processing Included**: Bounding box extraction on-device

## Usage

### Basic Usage

```bash
# Start with default settings (YOLO11n model)
python football_tracker.py

# Use YOLOv8n model
python football_tracker.py --model yolov8n

# Record video output
python football_tracker.py --record output.mp4

# Adjust detection sensitivity
python football_tracker.py --confidence 0.7
```

### GUI Mode

```bash
# Start graphical interface (easier for beginners)
python gui.py

# On Windows (if testing)
run_gui.bat
```

### Testing Without Hardware

```bash
# Test with mock data (no IMX500 required)
python football_tracker.py --offline
```

## Camera Setup

### 1. Physical Connection
1. **Power off** your Raspberry Pi
2. **Connect the IMX500 camera** to the CSI camera port
3. **Secure the connection** and ensure the cable is properly seated
4. **Power on** the Raspberry Pi

### 2. Camera Configuration

```bash
# Enable camera interface
sudo raspi-config
# Navigate to: Interface Options > Camera > Yes

# Test camera detection
libcamera-hello --list-cameras

# Test IMX500 functionality
libcamera-hello --post-process-file /usr/share/rpi-camera-postprocess/imx500_object_detection_demo.json
```

### 3. Positioning for Football Tracking

- **Height**: Mount camera 3-5 meters above ground for optimal field view
- **Angle**: Position to capture the full field of play
- **Stability**: Use a stable mount to minimize camera shake
- **Lighting**: Ensure adequate lighting for good detection accuracy

## Troubleshooting

### Common Issues

#### 1. Camera Not Detected
```bash
# Check camera connection
libcamera-hello --list-cameras

# If no cameras found:
# - Check physical connection
# - Ensure camera interface is enabled
# - Try a different CSI cable
```

#### 2. IMX500 Models Not Found
```bash
# Install models manually
sudo apt update
sudo apt install imx500-models

# Verify installation
ls -la /usr/share/imx500-models/
```

#### 3. Permission Errors
```bash
# Add user to video group
sudo usermod -a -G video $USER

# Log out and back in, or reboot
sudo reboot
```

#### 4. Poor Detection Performance
- **Lighting**: Ensure good lighting conditions
- **Distance**: Optimal detection range is 5-50 meters
- **Resolution**: Use highest camera resolution setting
- **Confidence**: Adjust threshold with `--confidence` parameter

#### 5. Low Frame Rate
- **SD Card Speed**: Use Class 10 or better SD card
- **Power Supply**: Ensure adequate power (official RPi power supply)
- **Temperature**: Check CPU temperature, add cooling if needed
- **Resolution**: Reduce camera resolution if needed

### Performance Optimization

```bash
# Monitor system performance
htop

# Check temperature
vcgencmd measure_temp

# Optimize GPU memory split
sudo raspi-config
# Advanced Options > Memory Split > 128 or 256
```

## Advanced Configuration

### Custom Model Parameters

Edit `config.py` to adjust:
- Detection confidence thresholds
- Tracking parameters
- Camera resolution settings
- Color schemes for visualization

### Recording Settings

```python
# In config.py
RECORDING = {
    'codec': 'mp4v',  # Video codec
    'fps': 30,        # Recording frame rate
    'quality': 90     # Video quality (0-100)
}
```

## Support and Resources

### Documentation
- [Raspberry Pi AI Camera Documentation](https://www.raspberrypi.com/documentation/accessories/ai-camera.html)
- [IMX500 Model Zoo](https://github.com/raspberrypi/imx500-models)
- [Picamera2 Documentation](https://datasheets.raspberrypi.com/camera/picamera2-manual.pdf)

### Community
- [Raspberry Pi Forums](https://forums.raspberrypi.com/)
- [AI Camera Section](https://forums.raspberrypi.com/viewforum.php?f=130)

### Hardware Purchase
- [Official Raspberry Pi Store](https://www.raspberrypi.com/products/)
- [Approved Resellers](https://www.raspberrypi.com/resellers/)

## Next Steps

Once installed and running:

1. **Test with sample footage** to verify functionality
2. **Adjust camera positioning** for your specific field setup
3. **Fine-tune detection parameters** for your environment
4. **Set up automated recording** for match analysis
5. **Explore advanced features** like trajectory analysis

## Updates and Maintenance

```bash
# Update system packages
sudo apt update && sudo apt upgrade

# Update Python dependencies
source venv/bin/activate
pip install --upgrade -r requirements.txt

# Update IMX500 models (when available)
sudo apt update
sudo apt upgrade imx500-models
```

For the latest updates and features, check the project repository regularly.
