#!/usr/bin/env python3
"""
Camera Selector Tool - Find and select available cameras
"""

import cv2
import time


def test_camera(index):
    """Test if a camera index works and get its properties"""
    try:
        cap = cv2.VideoCapture(index)
        if not cap.isOpened():
            return None

        # Try to read a frame
        ret, frame = cap.read()
        if not ret or frame is None:
            cap.release()
            return None

        # Get camera properties
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)

        cap.release()

        return {
            "index": index,
            "width": width,
            "height": height,
            "fps": fps,
            "name": get_camera_name(index),
        }
    except Exception:
        return None


def get_camera_name(index):
    """Get a descriptive name for the camera"""
    if index == 0:
        return "Built-in Camera (Laptop)"
    else:
        return f"External Camera #{index} (USB/Phone)"


def find_all_cameras():
    """Find all available cameras"""
    print("🔍 Scanning for available cameras...")
    cameras = []

    # Check camera indices 0-9
    for i in range(10):
        print(f"  Testing camera {i}...", end=" ")
        camera_info = test_camera(i)
        if camera_info:
            cameras.append(camera_info)
            print(f"✅ Found: {camera_info['name']}")
        else:
            print("❌")

    return cameras


def preview_camera(camera_index):
    """Preview a specific camera"""
    print(f"\n📹 Previewing camera {camera_index}...")
    print("Press 'q' to quit preview, 's' for screenshot")

    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        print("❌ Could not open camera")
        return

    # Try to set higher resolution if it's a phone camera
    if camera_index > 0:
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    frame_count = 0
    start_time = time.time()

    while True:
        ret, frame = cap.read()
        if not ret:
            print("❌ Could not read frame")
            break

        frame_count += 1

        # Calculate FPS
        if frame_count % 30 == 0:
            elapsed = time.time() - start_time
            fps = frame_count / elapsed
            print(f"Actual FPS: {fps:.1f}")

        # Add info overlay
        height, width = frame.shape[:2]
        cv2.putText(
            frame,
            f"Camera {camera_index}: {width}x{height}",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2,
        )
        cv2.putText(
            frame,
            "Press 'q' to quit, 's' for screenshot",
            (10, height - 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            2,
        )

        cv2.imshow(f"Camera {camera_index} Preview", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break
        elif key == ord("s"):
            filename = f"camera_{camera_index}_test.jpg"
            cv2.imwrite(filename, frame)
            print(f"📸 Screenshot saved: {filename}")

    cap.release()
    cv2.destroyAllWindows()


def main():
    """Main camera selector interface"""
    print("📱💻 Camera Selector for Object Tracking")
    print("=" * 50)

    # Find all cameras
    cameras = find_all_cameras()

    if not cameras:
        print("\n❌ No cameras found!")
        print("\nTroubleshooting:")
        print("1. Make sure your phone is connected via USB")
        print("2. Enable 'USB Debugging' on your phone")
        print("3. Select 'File Transfer (MTP)' mode on phone")
        print("4. Try a different USB cable")
        print("5. Close other camera apps (Zoom, Skype, etc.)")
        return

    print(f"\n✅ Found {len(cameras)} camera(s):")
    print("-" * 40)

    for camera in cameras:
        print(f"📷 Camera {camera['index']}: {camera['name']}")
        print(f"   Resolution: {camera['width']}x{camera['height']}")
        print(f"   FPS: {camera['fps']}")
        print()

    # Interactive selection
    while True:
        print("Options:")
        print("1. Preview a camera")
        print("2. Test object tracking")
        print("3. Exit")

        choice = input("\nEnter choice (1-3): ").strip()

        if choice == "1":
            try:
                camera_index = int(input("Enter camera index to preview: "))
                if any(c["index"] == camera_index for c in cameras):
                    preview_camera(camera_index)
                else:
                    print("❌ Invalid camera index")
            except ValueError:
                print("❌ Please enter a valid number")

        elif choice == "2":
            try:
                camera_index = int(input("Enter camera index for tracking: "))
                if any(c["index"] == camera_index for c in cameras):
                    print(
                        f"\n🚀 Starting object tracking with camera {camera_index}..."
                    )
                    print("Run this command:")
                    print(
                        f"python football_tracker.py --offline --camera {camera_index}"
                    )
                    break
                else:
                    print("❌ Invalid camera index")
            except ValueError:
                print("❌ Please enter a valid number")

        elif choice == "3":
            break
        else:
            print("❌ Invalid choice")


if __name__ == "__main__":
    main()
