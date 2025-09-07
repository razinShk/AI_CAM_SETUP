#!/bin/bash

# SportsCam Raspberry Pi Setup Script
# Run this on your Raspberry Pi after cloning from GitHub

set -e

echo "🍓 SportsCam Raspberry Pi Setup Starting..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

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

# Update system
print_status "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install system dependencies
print_status "Installing system dependencies..."
sudo apt install -y \
    python3-dev python3-pip python3-venv \
    libopencv-dev python3-opencv libatlas-base-dev \
    git curl wget ffmpeg nginx \
    libjpeg-dev libpng-dev libtiff-dev \
    libavcodec-dev libavformat-dev libswscale-dev

# Install IMX500 models
print_status "Installing IMX500 models..."
sudo apt install -y imx500-models || {
    print_warning "Could not install imx500-models package. You may need to add the Raspberry Pi repository."
}

# Create virtual environment
print_status "Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install Python dependencies
print_status "Installing Python dependencies..."
pip install -r requirements-raspberry-pi.txt
pip install -r requirements-supabase.txt

# Set up permissions for camera access
print_status "Setting up camera permissions..."
sudo usermod -a -G video $USER

# Create directories
print_status "Creating directories..."
mkdir -p recordings
mkdir -p uploads
mkdir -p tracking_data
mkdir -p screenshots
mkdir -p highlights
mkdir -p logs

# Copy environment file
if [ ! -f .env ]; then
    print_status "Creating environment file..."
    cp .env.example .env
    print_warning "Please edit .env file with your specific camera configuration!"
fi

# Create systemd service
print_status "Creating systemd service..."
sudo tee /etc/systemd/system/sportscam-camera.service > /dev/null <<EOF
[Unit]
Description=SportsCam Camera Server
After=network.target

[Service]
Type=simple
User=pi
Group=pi
WorkingDirectory=$PWD
Environment=PATH=$PWD/venv/bin
ExecStart=$PWD/venv/bin/python raspberry_pi_server.py
Restart=always
RestartSec=10
EnvironmentFile=$PWD/.env

[Install]
WantedBy=multi-user.target
EOF

# Enable service (but don't start yet)
sudo systemctl enable sportscam-camera

# Test camera
print_status "Testing camera setup..."
libcamera-hello --list-cameras || print_warning "Camera test failed. Check camera connection."

# Test Python imports
print_status "Testing Python dependencies..."
python3 -c "
import cv2
import numpy as np
from supabase import create_client
print('✅ All dependencies imported successfully')
" || print_error "Python dependency test failed"

echo ""
echo "🎉 Setup completed successfully!"
echo ""
print_status "Next steps:"
echo "1. Edit .env file with your camera configuration"
echo "2. Test the camera server: python raspberry_pi_server.py"
echo "3. Start the service: sudo systemctl start sportscam-camera"
echo "4. Check status: sudo systemctl status sportscam-camera"
echo ""
print_warning "Remember to reboot or log out/in for camera permissions to take effect!"