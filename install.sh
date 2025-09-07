#!/bin/bash

# Football Tracking Software Installation Script for Raspberry Pi
# This script sets up the environment and installs all dependencies

set -e  # Exit on any error

echo "==========================================="
echo "Football Tracking Software Installation"
echo "For Raspberry Pi AI Camera (IMX500)"
echo "==========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running on Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
    print_warning "This script is designed for Raspberry Pi. Continuing anyway..."
fi

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    print_error "Please don't run this script as root. Use a regular user account."
    exit 1
fi

# Update system packages
print_status "Updating system packages..."
sudo apt update
sudo apt upgrade -y

# Install system dependencies
print_status "Installing system dependencies..."
sudo apt install -y \
    python3-dev \
    python3-pip \
    python3-venv \
    libopencv-dev \
    python3-opencv \
    libatlas-base-dev \
    libjasper-dev \
    libqtgui4 \
    libqt4-test \
    libhdf5-dev \
    libhdf5-serial-dev \
    libhdf5-103 \
    libqtcore4 \
    libjpeg-dev \
    libpng-dev \
    libtiff-dev \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    libgtk2.0-dev \
    pkg-config

# Install IMX500 models if available
print_status "Checking for IMX500 models..."
if sudo apt list --installed 2>/dev/null | grep -q "imx500-models"; then
    print_status "IMX500 models already installed"
else
    print_status "Installing IMX500 models..."
    sudo apt install -y imx500-models || {
        print_warning "Could not install imx500-models package. You may need to add the Raspberry Pi repository."
        print_warning "The software will work in offline mode for testing."
    }
fi

# Create virtual environment
print_status "Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
print_status "Upgrading pip..."
pip install --upgrade pip

# Install Python dependencies
print_status "Installing Python dependencies..."
pip install -r requirements.txt

# Install picamera2 if not available
print_status "Installing picamera2..."
pip install picamera2 || {
    print_warning "Could not install picamera2 via pip. Trying system package..."
    sudo apt install -y python3-picamera2
}

# Set up permissions for camera access
print_status "Setting up camera permissions..."
sudo usermod -a -G video $USER

# Create directories for output
print_status "Creating output directories..."
mkdir -p recordings
mkdir -p screenshots
mkdir -p logs

# Make scripts executable
print_status "Making scripts executable..."
chmod +x football_tracker.py

# Create desktop shortcut (optional)
if [ -d "$HOME/Desktop" ]; then
    print_status "Creating desktop shortcut..."
    cat > "$HOME/Desktop/Football Tracker.desktop" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Football Tracker
Comment=AI-powered football tracking with Raspberry Pi Camera
Exec=$PWD/venv/bin/python $PWD/football_tracker.py
Icon=camera-video
Terminal=true
Categories=Graphics;Photography;
EOF
    chmod +x "$HOME/Desktop/Football Tracker.desktop"
fi

# Test installation
print_status "Testing installation..."
source venv/bin/activate
python3 -c "import cv2, numpy, picamera2; print('Core dependencies imported successfully')" || {
    print_error "Failed to import required modules. Please check the installation."
    exit 1
}

echo ""
echo "==========================================="
print_status "Installation completed successfully!"
echo "==========================================="
echo ""
print_status "To run the football tracker:"
echo "  1. Activate the virtual environment: source venv/bin/activate"
echo "  2. Run the tracker: python football_tracker.py"
echo ""
print_status "Usage examples:"
echo "  # Basic usage with YOLO11n model:"
echo "  python football_tracker.py"
echo ""
echo "  # Use YOLOv8n model with recording:"
echo "  python football_tracker.py --model yolov8n --record output.mp4"
echo ""
echo "  # Test without IMX500 hardware (offline mode):"
echo "  python football_tracker.py --offline"
echo ""
echo "  # Adjust confidence threshold:"
echo "  python football_tracker.py --confidence 0.7"
echo ""
print_warning "Note: You may need to log out and log back in for camera permissions to take effect."
print_status "Check the README.md file for detailed usage instructions."
