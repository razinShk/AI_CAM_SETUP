#!/usr/bin/env python3
"""
Download YOLO model for real object detection
"""

import os
import urllib.request
import sys


def download_file(url, filename):
    """Download a file with progress indicator"""
    print(f"Downloading {filename}...")

    def progress_hook(block_num, block_size, total_size):
        downloaded = block_num * block_size
        if total_size > 0:
            percent = min(100, (downloaded * 100) // total_size)
            print(f"\r  Progress: {percent}% ({downloaded}/{total_size} bytes)", end="")
        else:
            print(f"\r  Downloaded: {downloaded} bytes", end="")

    try:
        urllib.request.urlretrieve(url, filename, reporthook=progress_hook)
        print(f"\n✓ Downloaded: {filename}")
        return True
    except Exception as e:
        print(f"\n✗ Failed to download {filename}: {e}")
        return False


def main():
    """Download YOLO model files"""
    print("===========================================")
    print("YOLO Model Downloader for Object Tracking")
    print("===========================================")

    # Create models directory
    models_dir = "models"
    if not os.path.exists(models_dir):
        os.makedirs(models_dir)
        print(f"Created directory: {models_dir}")

    # YOLO model files (smaller, faster models)
    files_to_download = [
        {
            "url": "https://github.com/pjreddie/darknet/blob/master/cfg/yolov3-tiny.cfg?raw=true",
            "filename": "models/yolov3-tiny.cfg",
            "description": "YOLOv3-tiny configuration",
        },
        {
            "url": "https://pjreddie.com/media/files/yolov3-tiny.weights",
            "filename": "models/yolov3-tiny.weights",
            "description": "YOLOv3-tiny weights",
        },
    ]

    print("\nThis will download YOLOv3-tiny model (~33MB) for real object detection.")
    print(
        "The model supports all 80 COCO classes including people, vehicles, animals, etc."
    )

    response = input("\nProceed with download? (y/n): ").lower().strip()
    if response != "y":
        print("Download cancelled.")
        return

    # Download files
    success_count = 0
    for file_info in files_to_download:
        print(f"\n{file_info['description']}:")
        if download_file(file_info["url"], file_info["filename"]):
            success_count += 1

    print(f"\n===========================================")
    if success_count == len(files_to_download):
        print("✓ All files downloaded successfully!")
        print("\nTo use real object detection:")
        print("  python football_tracker.py --offline")
        print("\nTo use demo mode with mock objects:")
        print("  python football_tracker.py --offline --demo")
        print("\nThe tracker will automatically detect if you have a webcam")
        print("and try to use real object detection on the live feed.")
    else:
        print(f"⚠️  {len(files_to_download) - success_count} files failed to download.")
        print("You can still use demo mode or try downloading manually.")

    print("\nModel files are stored in the 'models/' directory.")


if __name__ == "__main__":
    main()
