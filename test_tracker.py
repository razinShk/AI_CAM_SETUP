#!/usr/bin/env python3
"""
Quick test script for Football Tracker on Windows
"""

import sys
import cv2
import numpy as np
import time


def test_imports():
    """Test if all required modules can be imported"""
    print("Testing imports...")

    try:
        import cv2

        print("✓ OpenCV imported successfully")
    except ImportError as e:
        print(f"✗ OpenCV import failed: {e}")
        return False

    try:
        import numpy as np

        print("✓ NumPy imported successfully")
    except ImportError as e:
        print(f"✗ NumPy import failed: {e}")
        return False

    try:
        from detection import OfflineDetector

        print("✓ Detection module imported successfully")
    except ImportError as e:
        print(f"✗ Detection module import failed: {e}")
        return False

    try:
        from tracking import MultiObjectTracker

        print("✓ Tracking module imported successfully")
    except ImportError as e:
        print(f"✗ Tracking module import failed: {e}")
        return False

    return True


def test_offline_detector():
    """Test the offline detector"""
    print("\nTesting offline detector...")

    try:
        from detection import OfflineDetector

        # Create detector
        detector = OfflineDetector(use_webcam=False)
        print("✓ Offline detector created")

        # Get a frame
        frame = detector.get_frame()
        if frame is not None:
            print(f"✓ Frame acquired: {frame.shape}")
        else:
            print("✗ Failed to acquire frame")
            return False

        # Test detection
        detections = detector.detect_objects(frame)
        print(f"✓ Detections generated: {len(detections)} objects found")

        # Test categorization
        categorized = detector.categorize_objects(detections)
        total_objects = sum(len(objects) for objects in categorized.values())
        print(f"✓ Categorization works: {total_objects} objects in {len(categorized)} categories")

        return True

    except Exception as e:
        print(f"✗ Offline detector test failed: {e}")
        return False


def test_tracking():
    """Test the tracking module"""
    print("\nTesting tracking...")

    try:
        from tracking import MultiObjectTracker
        from detection import OfflineDetector

        # Create tracker and detector
        tracker = MultiObjectTracker()
        detector = OfflineDetector(use_webcam=False)
        print("✓ Tracker and detector created")

        # Process a few frames
        for i in range(3):
            frame = detector.get_frame()
            detections = detector.detect_objects(frame)
            categorized = detector.categorize_objects(detections)

            # Update tracking
            results = tracker.update(categorized)

            total_tracked = sum(len(objects) for objects in results["objects"].values())
            print(f"✓ Frame {i+1}: {total_tracked} objects tracked across multiple categories")

        return True

    except Exception as e:
        print(f"✗ Tracking test failed: {e}")
        return False


def test_gui_components():
    """Test GUI components"""
    print("\nTesting GUI components...")

    try:
        import tkinter as tk
        from tkinter import ttk

        print("✓ Tkinter available")

        # Test if we can create a simple window
        root = tk.Tk()
        root.withdraw()  # Hide the test window
        root.destroy()
        print("✓ Tkinter window creation works")

        return True

    except Exception as e:
        print(f"✗ GUI test failed: {e}")
        return False


def main():
    """Main test function"""
    print("===========================================")
    print("Object Tracker Windows Compatibility Test")
    print("===========================================")

    tests = [
        ("Import Test", test_imports),
        ("Offline Detector Test", test_offline_detector),
        ("Tracking Test", test_tracking),
        ("GUI Components Test", test_gui_components),
    ]

    results = []

    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ {test_name} crashed: {e}")
            results.append((test_name, False))

    # Summary
    print("\n===========================================")
    print("Test Results Summary")
    print("===========================================")

    passed = 0
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        symbol = "✓" if result else "✗"
        print(f"{symbol} {test_name}: {status}")
        if result:
            passed += 1

    print(f"\nOverall: {passed}/{len(results)} tests passed")

    if passed == len(results):
        print("\n🎉 All tests passed! The object tracker should work on Windows.")
        print("\nTo run the application:")
        print("  GUI mode: python gui.py")
        print("  Command line: python football_tracker.py --offline")
    else:
        print(f"\n⚠️  {len(results) - passed} test(s) failed. Check the errors above.")

    return passed == len(results)


if __name__ == "__main__":
    success = main()
    input("\nPress Enter to exit...")
    sys.exit(0 if success else 1)
