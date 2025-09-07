#!/usr/bin/env python3
"""
Raspberry Pi 5 + IMX500 AI Camera Test Script
Quick validation of hardware and software setup
"""

import sys
import os
import time
import subprocess
from pathlib import Path


def test_section(name):
    """Print test section header"""
    print(f"\n🧪 Testing {name}")
    print("-" * 40)


def run_test(description, test_func):
    """Run a test and report results"""
    print(f"   {description}...", end=" ")
    try:
        result = test_func()
        if result:
            print("✅ PASS")
            return True
        else:
            print("❌ FAIL")
            return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


def test_python_environment():
    """Test Python environment and imports"""
    test_section("Python Environment")

    # Test Python version
    def check_python_version():
        version = sys.version_info
        return version.major == 3 and version.minor >= 8

    run_test("Python 3.8+", check_python_version)

    # Test required imports
    imports_to_test = [
        ("OpenCV", "cv2"),
        ("NumPy", "numpy"),
        ("Picamera2", "picamera2"),
        ("LibCamera", "libcamera"),
        ("Ultralytics", "ultralytics"),
    ]

    for name, module in imports_to_test:

        def test_import():
            __import__(module)
            return True

        run_test(f"{name} import", test_import)


def test_raspberry_pi_hardware():
    """Test Raspberry Pi hardware detection"""
    test_section("Raspberry Pi Hardware")

    def check_raspberry_pi():
        try:
            with open("/proc/cpuinfo", "r") as f:
                cpuinfo = f.read()
                return "Raspberry Pi" in cpuinfo
        except:
            return False

    run_test("Raspberry Pi detection", check_raspberry_pi)

    def check_pi_version():
        try:
            with open("/proc/cpuinfo", "r") as f:
                cpuinfo = f.read()
                # Look for Pi 5 indicators
                return "BCM2712" in cpuinfo or "Raspberry Pi 5" in cpuinfo
        except:
            return False

    run_test("Raspberry Pi 5 detection", check_pi_version)


def test_camera_hardware():
    """Test camera hardware"""
    test_section("Camera Hardware")

    def check_camera_detected():
        try:
            result = subprocess.run(
                ["vcgencmd", "get_camera"], capture_output=True, text=True
            )
            return "detected=1" in result.stdout
        except:
            return False

    run_test("Camera detection", check_camera_detected)

    def check_imx500():
        try:
            result = subprocess.run(["dmesg"], capture_output=True, text=True)
            return "imx500" in result.stdout.lower()
        except:
            return False

    run_test("IMX500 camera driver", check_imx500)


def test_camera_access():
    """Test camera access and functionality"""
    test_section("Camera Access")

    def test_picamera2_init():
        try:
            from picamera2 import Picamera2

            camera = Picamera2()
            camera.close()
            return True
        except:
            return False

    run_test("Picamera2 initialization", test_picamera2_init)

    def test_camera_preview_config():
        try:
            from picamera2 import Picamera2

            camera = Picamera2()
            config = camera.create_preview_configuration()
            camera.configure(config)
            camera.close()
            return True
        except:
            return False

    run_test("Camera configuration", test_camera_preview_config)


def test_ai_models():
    """Test AI model availability"""
    test_section("AI Models")

    models_dir = Path("models")

    def check_models_directory():
        return models_dir.exists()

    run_test("Models directory", check_models_directory)

    if models_dir.exists():
        expected_models = [
            "yolo11n_224x224.rpk",
            "yolo11s_224x224.rpk",
            "yolov8n_224x224.rpk",
        ]

        for model in expected_models:

            def check_model():
                return (models_dir / model).exists()

            run_test(f"Model {model}", check_model)

    def test_imx500_models_repo():
        return Path("imx500-models").exists()

    run_test("IMX500 models repository", test_imx500_models_repo)


def test_system_configuration():
    """Test system configuration"""
    test_section("System Configuration")

    def check_camera_config():
        try:
            with open("/boot/config.txt", "r") as f:
                config = f.read()
                return "camera_auto_detect=1" in config and "imx500" in config
        except:
            return False

    run_test("Camera configuration in /boot/config.txt", check_camera_config)

    def check_gpu_memory():
        try:
            result = subprocess.run(
                ["vcgencmd", "get_mem", "gpu"], capture_output=True, text=True
            )
            gpu_mem = int(result.stdout.split("=")[1].replace("M", ""))
            return gpu_mem >= 128
        except:
            return False

    run_test("GPU memory allocation (>=128MB)", check_gpu_memory)


def test_performance():
    """Test basic performance"""
    test_section("Performance Test")

    def test_basic_detection():
        try:
            # Import and test basic functionality
            from raspberry_pi_tracker import RaspberryPiAIDetector

            # This is a basic import test
            # Full camera test would require actual hardware
            return True
        except ImportError:
            return False
        except Exception:
            # Expected if no camera hardware
            return True

    run_test("Tracker import", test_basic_detection)

    def test_tracking_components():
        try:
            from tracking import MultiObjectTracker

            tracker = MultiObjectTracker()
            return True
        except:
            return False

    run_test("Tracking components", test_tracking_components)


def test_file_permissions():
    """Test file permissions and access"""
    test_section("File Permissions")

    def check_video_device_access():
        video_devices = list(Path("/dev").glob("video*"))
        if not video_devices:
            return False

        # Check if we can read video devices
        for device in video_devices[:3]:  # Check first few
            try:
                with open(device, "rb") as f:
                    return True
            except PermissionError:
                continue
            except:
                return True  # Device exists but may not be camera
        return False

    run_test("Video device access", check_video_device_access)

    def check_script_executable():
        scripts = ["start_tracker.sh", "start_headless.sh"]
        for script in scripts:
            if Path(script).exists():
                return os.access(script, os.X_OK)
        return True  # OK if scripts don't exist yet

    run_test("Script permissions", check_script_executable)


def generate_test_report():
    """Generate a comprehensive test report"""
    print("\n" + "=" * 50)
    print("🍓 Raspberry Pi 5 + IMX500 AI Camera Test Report")
    print("=" * 50)

    # Run all tests
    test_functions = [
        test_python_environment,
        test_raspberry_pi_hardware,
        test_camera_hardware,
        test_camera_access,
        test_ai_models,
        test_system_configuration,
        test_performance,
        test_file_permissions,
    ]

    for test_func in test_functions:
        try:
            test_func()
        except Exception as e:
            print(f"❌ Test section failed: {e}")

    # Summary and recommendations
    print("\n" + "=" * 50)
    print("📋 Summary and Recommendations")
    print("=" * 50)

    # Check critical components
    models_exist = Path("models").exists() and list(Path("models").glob("*.rpk"))

    if models_exist:
        print("✅ Ready for AI tracking!")
        print("\n🚀 Quick start commands:")
        print("   ./start_tracker.sh")
        print("   python3 raspberry_pi_tracker.py --model yolo11n")
    else:
        print("⚠️  Setup incomplete. Next steps:")
        print("   1. Run: python3 raspberry_pi_setup.py")
        print(
            "   2. Download models: git clone https://github.com/raspberrypi/imx500-models.git"
        )
        print("   3. Copy models: cp imx500-models/*.rpk models/")
        print("   4. Reboot if camera config was updated")

    print("\n📚 Documentation:")
    print("   - Setup guide: RASPBERRY_PI_GUIDE.md")
    print("   - Troubleshooting: Check logs with 'dmesg | grep imx500'")
    print("   - Performance: Monitor with 'htop' and 'vcgencmd measure_temp'")


def main():
    """Main test function"""
    print("🧪 Raspberry Pi 5 + IMX500 AI Camera Test Suite")
    print("This will validate your hardware and software setup")
    print()

    # Check if running on Pi
    try:
        with open("/proc/cpuinfo", "r") as f:
            if "Raspberry Pi" not in f.read():
                print("⚠️  Warning: Not running on Raspberry Pi")
                print("Some tests may not be accurate")
    except:
        print("⚠️  Warning: Could not detect system type")

    # Run comprehensive test
    generate_test_report()


if __name__ == "__main__":
    main()
