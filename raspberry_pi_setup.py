#!/usr/bin/env python3
"""
Raspberry Pi Setup and Configuration Tool
Automated setup for Raspberry Pi 5 with IMX500 AI Camera
"""

import os
import subprocess
import sys
import json
import shutil
from pathlib import Path


def run_command(command, description=""):
    """Run a shell command and handle errors"""
    print(f"🔄 {description}")
    print(f"   Running: {command}")

    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"   ✅ Success")
            return True
        else:
            print(f"   ❌ Failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def check_raspberry_pi():
    """Check if running on Raspberry Pi"""
    try:
        with open("/proc/cpuinfo", "r") as f:
            cpuinfo = f.read()
            if "Raspberry Pi" in cpuinfo:
                print("✅ Running on Raspberry Pi")
                return True
    except:
        pass

    print("❌ Not running on Raspberry Pi")
    return False


def check_imx500_camera():
    """Check if IMX500 camera is connected"""
    print("🔍 Checking for IMX500 AI Camera...")

    # Check if camera is detected
    if run_command("vcgencmd get_camera", "Checking camera detection"):
        print("✅ Camera subsystem detected")
    else:
        print("❌ Camera not detected")
        return False

    # Check for IMX500 specifically
    if run_command("dmesg | grep -i imx500", "Checking for IMX500 driver"):
        print("✅ IMX500 camera detected")
        return True
    else:
        print("⚠️  IMX500 camera may not be properly connected")
        return False


def install_system_dependencies():
    """Install required system packages"""
    print("\n📦 Installing system dependencies...")

    packages = [
        "python3-picamera2",
        "python3-opencv",
        "python3-numpy",
        "python3-pip",
        "git",
        "cmake",
        "libhdf5-dev",
        "libatlas-base-dev",
        "libjasper-dev",
        "libqtgui4",
        "libqt4-test",
    ]

    # Update package list
    if run_command("sudo apt update", "Updating package list"):
        print("✅ Package list updated")

    # Install packages
    for package in packages:
        if not run_command(f"sudo apt install -y {package}", f"Installing {package}"):
            print(f"⚠️  Failed to install {package}, continuing...")

    print("✅ System dependencies installation completed")


def install_python_dependencies():
    """Install Python packages"""
    print("\n🐍 Installing Python dependencies...")

    # Install from requirements
    if os.path.exists("requirements.txt"):
        run_command(
            "pip3 install -r requirements.txt", "Installing from requirements.txt"
        )

    # Install additional packages for Raspberry Pi
    pi_packages = [
        "ultralytics",
        "torch --index-url https://download.pytorch.org/whl/cpu",  # CPU-only PyTorch
        "torchvision --index-url https://download.pytorch.org/whl/cpu",
    ]

    for package in pi_packages:
        run_command(f"pip3 install {package}", f"Installing {package}")

    print("✅ Python dependencies installation completed")


def setup_imx500_models():
    """Setup IMX500 AI models"""
    print("\n🧠 Setting up IMX500 AI models...")

    models_dir = Path("models")
    models_dir.mkdir(exist_ok=True)

    # Clone IMX500 models repository
    if not Path("imx500-models").exists():
        if run_command(
            "git clone https://github.com/raspberrypi/imx500-models.git",
            "Downloading IMX500 models repository",
        ):
            print("✅ IMX500 models repository downloaded")
        else:
            print("❌ Failed to download models repository")
            return False

    # Copy models to local directory
    imx500_models = Path("imx500-models")
    if imx500_models.exists():
        print("📂 Copying model files...")

        # Common model files to copy
        model_files = [
            "yolo11n_224x224.rpk",
            "yolo11s_224x224.rpk",
            "yolov8n_224x224.rpk",
            "yolov8s_224x224.rpk",
        ]

        for model_file in model_files:
            src = imx500_models / model_file
            dst = models_dir / model_file

            if src.exists():
                shutil.copy2(src, dst)
                print(f"   ✅ Copied {model_file}")
            else:
                print(f"   ⚠️  {model_file} not found")

    print("✅ IMX500 models setup completed")
    return True


def configure_camera_settings():
    """Configure camera settings for optimal performance"""
    print("\n⚙️  Configuring camera settings...")

    # Enable camera in config.txt
    config_lines = [
        "# AI Camera Configuration",
        "camera_auto_detect=1",
        "dtoverlay=imx500,media-controller=0",
        "gpu_mem=128",
        "start_x=1",
    ]

    config_file = "/boot/config.txt"
    if os.path.exists(config_file):
        print("📝 Updating camera configuration...")

        try:
            # Read existing config
            with open(config_file, "r") as f:
                existing_config = f.read()

            # Add our configuration if not present
            needs_update = False
            for line in config_lines:
                if line.startswith("#"):
                    continue
                if line not in existing_config:
                    needs_update = True
                    break

            if needs_update:
                print("   Adding camera configuration to /boot/config.txt")
                print("   ⚠️  System reboot will be required")

                # Backup original
                run_command(
                    f"sudo cp {config_file} {config_file}.backup", "Backing up config"
                )

                # Append configuration
                config_text = "\n\n" + "\n".join(config_lines) + "\n"
                run_command(
                    f"echo '{config_text}' | sudo tee -a {config_file}",
                    "Updating config",
                )

                print("   ✅ Camera configuration updated")
                return True
            else:
                print("   ✅ Camera already configured")

        except Exception as e:
            print(f"   ❌ Failed to update config: {e}")

    return False


def create_startup_script():
    """Create startup script for easy launching"""
    print("\n📜 Creating startup scripts...")

    # Main startup script
    startup_script = """#!/bin/bash
# Raspberry Pi AI Object Tracker Startup Script

echo "🚀 Starting Raspberry Pi AI Object Tracker"
echo "📷 IMX500 AI Camera"
echo "🧠 Neural Processing on Camera"
echo ""

cd "$(dirname "$0")"

# Check if running with arguments
if [ $# -eq 0 ]; then
    echo "Usage examples:"
    echo "  $0 --model yolo11n                    # Basic tracking"
    echo "  $0 --model yolo11s --record video.mp4 # Record video"
    echo "  $0 --no-preview                       # Headless mode"
    echo ""
    read -p "Press Enter to start with default settings..."
    python3 raspberry_pi_tracker.py
else
    python3 raspberry_pi_tracker.py "$@"
fi
"""

    with open("start_tracker.sh", "w") as f:
        f.write(startup_script)

    # Make executable
    os.chmod("start_tracker.sh", 0o755)

    # Headless startup script
    headless_script = """#!/bin/bash
# Headless Raspberry Pi AI Tracker (no display)
cd "$(dirname "$0")"
python3 raspberry_pi_tracker.py --no-preview --model yolo11n --record "tracking_$(date +%Y%m%d_%H%M%S).mp4"
"""

    with open("start_headless.sh", "w") as f:
        f.write(headless_script)

    os.chmod("start_headless.sh", 0o755)

    print("✅ Startup scripts created:")
    print("   📜 start_tracker.sh - Interactive mode")
    print("   📜 start_headless.sh - Headless recording")


def create_service_file():
    """Create systemd service for auto-start"""
    print("\n🔧 Creating systemd service...")

    current_dir = os.getcwd()
    username = os.getenv("USER", "pi")

    service_content = f"""[Unit]
Description=Raspberry Pi AI Object Tracker
After=network.target

[Service]
Type=simple
User={username}
WorkingDirectory={current_dir}
ExecStart=/usr/bin/python3 {current_dir}/raspberry_pi_tracker.py --no-preview --model yolo11n
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
"""

    service_file = "/etc/systemd/system/pi-ai-tracker.service"

    try:
        with open("pi-ai-tracker.service", "w") as f:
            f.write(service_content)

        print("📝 Service file created: pi-ai-tracker.service")
        print("   To install: sudo cp pi-ai-tracker.service /etc/systemd/system/")
        print("   To enable:  sudo systemctl enable pi-ai-tracker")
        print("   To start:   sudo systemctl start pi-ai-tracker")

    except Exception as e:
        print(f"❌ Failed to create service file: {e}")


def test_setup():
    """Test the installation"""
    print("\n🧪 Testing setup...")

    # Test Python imports
    test_imports = ["picamera2", "cv2", "numpy", "ultralytics"]

    for module in test_imports:
        try:
            __import__(module)
            print(f"   ✅ {module} import successful")
        except ImportError:
            print(f"   ❌ {module} import failed")

    # Test camera access
    try:
        from picamera2 import Picamera2

        camera = Picamera2()
        camera.close()
        print("   ✅ Camera access successful")
    except Exception as e:
        print(f"   ❌ Camera access failed: {e}")

    # Test model files
    models_dir = Path("models")
    if models_dir.exists():
        model_files = list(models_dir.glob("*.rpk"))
        if model_files:
            print(f"   ✅ Found {len(model_files)} model files")
        else:
            print("   ⚠️  No model files found")

    print("✅ Setup testing completed")


def main():
    """Main setup function"""
    print("🍓 Raspberry Pi 5 + IMX500 AI Camera Setup")
    print("=" * 50)

    # Check environment
    if not check_raspberry_pi():
        print("❌ This setup is designed for Raspberry Pi")
        return 1

    # Setup steps
    steps = [
        ("System Dependencies", install_system_dependencies),
        ("Python Dependencies", install_python_dependencies),
        ("IMX500 Models", setup_imx500_models),
        ("Camera Settings", configure_camera_settings),
        ("Startup Scripts", create_startup_script),
        ("Service File", create_service_file),
        ("Testing", test_setup),
    ]

    for step_name, step_func in steps:
        print(f"\n🔄 {step_name}")
        print("-" * 30)

        try:
            step_func()
        except Exception as e:
            print(f"❌ {step_name} failed: {e}")
            continue

    # Final instructions
    print("\n" + "=" * 50)
    print("🎉 Setup completed!")
    print("\n📋 Next steps:")
    print("1. 🔄 Reboot Pi: sudo reboot")
    print("2. 🚀 Test tracker: ./start_tracker.sh")
    print("3. 📹 Record video: ./start_headless.sh")
    print("4. 🔧 Auto-start: sudo systemctl enable pi-ai-tracker")
    print("\n💡 Tips:")
    print("   - Models are optimized for IMX500 neural processor")
    print("   - AI processing happens on camera, not Pi CPU")
    print("   - Use --no-preview for headless operation")
    print("   - Check logs with: journalctl -u pi-ai-tracker")

    return 0


if __name__ == "__main__":
    exit(main())
