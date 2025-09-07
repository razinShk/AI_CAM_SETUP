"""
GUI Interface for Football Tracking Software
Simple control panel for configuring and running the tracker
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os
import subprocess
import sys
from config import MODELS


class FootballTrackerGUI:
    """
    Graphical User Interface for Football Tracker
    """

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Object Tracker - AI Camera Control")
        self.root.geometry("600x500")
        self.root.resizable(True, True)

        # Variables
        self.model_var = tk.StringVar(value="yolo11n")
        self.confidence_var = tk.DoubleVar(value=0.5)
        self.offline_var = tk.BooleanVar(value=False)
        self.record_var = tk.BooleanVar(value=False)
        self.record_path_var = tk.StringVar(value="")
        self.verbose_var = tk.BooleanVar(value=False)

        # Tracking process
        self.tracking_process = None
        self.is_tracking = False

        self.setup_ui()

    def setup_ui(self):
        """Setup the user interface"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)

        # Title
        title_label = ttk.Label(
            main_frame,
            text="Object Tracker Control Panel",
            font=("Arial", 16, "bold"),
        )
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))

        # Model Selection
        ttk.Label(main_frame, text="AI Model:").grid(
            row=1, column=0, sticky=tk.W, pady=5
        )
        model_frame = ttk.Frame(main_frame)
        model_frame.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5)

        ttk.Radiobutton(
            model_frame,
            text="YOLO11n (Recommended)",
            variable=self.model_var,
            value="yolo11n",
        ).pack(anchor=tk.W)
        ttk.Radiobutton(
            model_frame, text="YOLOv8n", variable=self.model_var, value="yolov8n"
        ).pack(anchor=tk.W)

        # Confidence Threshold
        ttk.Label(main_frame, text="Confidence Threshold:").grid(
            row=2, column=0, sticky=tk.W, pady=5
        )
        conf_frame = ttk.Frame(main_frame)
        conf_frame.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5)

        confidence_scale = ttk.Scale(
            conf_frame,
            from_=0.1,
            to=0.9,
            variable=self.confidence_var,
            orient=tk.HORIZONTAL,
        )
        confidence_scale.pack(fill=tk.X, padx=(0, 10))

        conf_label = ttk.Label(conf_frame, text="0.5")
        conf_label.pack(side=tk.RIGHT)

        # Update confidence label
        def update_conf_label(*args):
            conf_label.config(text=f"{self.confidence_var.get():.2f}")

        self.confidence_var.trace("w", update_conf_label)

        # Mode Selection
        ttk.Label(main_frame, text="Mode:").grid(row=3, column=0, sticky=tk.W, pady=5)
        mode_frame = ttk.Frame(main_frame)
        mode_frame.grid(row=3, column=1, sticky=(tk.W, tk.E), pady=5)

        ttk.Checkbutton(
            mode_frame,
            text="Offline Mode (Testing without IMX500)",
            variable=self.offline_var,
        ).pack(anchor=tk.W)
        ttk.Checkbutton(
            mode_frame, text="Verbose Logging", variable=self.verbose_var
        ).pack(anchor=tk.W)

        # Recording Options
        ttk.Label(main_frame, text="Recording:").grid(
            row=4, column=0, sticky=tk.W, pady=5
        )
        record_frame = ttk.Frame(main_frame)
        record_frame.grid(row=4, column=1, sticky=(tk.W, tk.E), pady=5)

        ttk.Checkbutton(
            record_frame,
            text="Enable Recording",
            variable=self.record_var,
            command=self.toggle_recording,
        ).pack(anchor=tk.W)

        self.record_path_frame = ttk.Frame(record_frame)
        self.record_path_frame.pack(fill=tk.X, pady=(5, 0))

        self.record_entry = ttk.Entry(
            self.record_path_frame, textvariable=self.record_path_var, state=tk.DISABLED
        )
        self.record_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.browse_button = ttk.Button(
            self.record_path_frame,
            text="Browse",
            command=self.browse_record_path,
            state=tk.DISABLED,
        )
        self.browse_button.pack(side=tk.RIGHT, padx=(5, 0))

        # Separator
        ttk.Separator(main_frame, orient="horizontal").grid(
            row=5, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=20
        )

        # Control Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=6, column=0, columnspan=2, pady=10)

        self.start_button = ttk.Button(
            button_frame,
            text="Start Tracking",
            command=self.start_tracking,
            style="Accent.TButton",
        )
        self.start_button.pack(side=tk.LEFT, padx=(0, 10))

        self.stop_button = ttk.Button(
            button_frame,
            text="Stop Tracking",
            command=self.stop_tracking,
            state=tk.DISABLED,
        )
        self.stop_button.pack(side=tk.LEFT, padx=(0, 10))

        self.reset_button = ttk.Button(
            button_frame, text="Reset Settings", command=self.reset_settings
        )
        self.reset_button.pack(side=tk.LEFT)

        # Status Frame
        status_frame = ttk.LabelFrame(main_frame, text="Status", padding="10")
        status_frame.grid(row=7, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=20)
        status_frame.columnconfigure(0, weight=1)

        self.status_label = ttk.Label(
            status_frame, text="Ready to start tracking", foreground="green"
        )
        self.status_label.pack()

        # Information Frame
        info_frame = ttk.LabelFrame(main_frame, text="Information", padding="10")
        info_frame.grid(
            row=8, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10)
        )

        info_text = """
Controls while tracking:
• Q - Quit tracking
• R - Reset tracking data
• S - Save screenshot

Models:
• YOLO11n: Better accuracy (mAP 0.374)
• YOLOv8n: Faster processing (mAP 0.279)

Detects and tracks:
• People, vehicles, animals, sports items
• Electronics, furniture, food items
• And 70+ other object types from COCO dataset
        """.strip()

        ttk.Label(info_frame, text=info_text, justify=tk.LEFT).pack(anchor=tk.W)

    def toggle_recording(self):
        """Toggle recording options"""
        if self.record_var.get():
            self.record_entry.config(state=tk.NORMAL)
            self.browse_button.config(state=tk.NORMAL)
            if not self.record_path_var.get():
                from datetime import datetime

                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                self.record_path_var.set(f"object_tracking_{timestamp}.mp4")
        else:
            self.record_entry.config(state=tk.DISABLED)
            self.browse_button.config(state=tk.DISABLED)

    def browse_record_path(self):
        """Browse for recording output path"""
        filename = filedialog.asksaveasfilename(
            title="Select Recording Output File",
            defaultextension=".mp4",
            filetypes=[
                ("MP4 files", "*.mp4"),
                ("AVI files", "*.avi"),
                ("All files", "*.*"),
            ],
        )
        if filename:
            self.record_path_var.set(filename)

    def reset_settings(self):
        """Reset all settings to defaults"""
        self.model_var.set("yolo11n")
        self.confidence_var.set(0.5)
        self.offline_var.set(False)
        self.record_var.set(False)
        self.record_path_var.set("")
        self.verbose_var.set(False)
        self.toggle_recording()
        self.update_status("Settings reset to defaults", "blue")

    def start_tracking(self):
        """Start the tracking process"""
        if self.is_tracking:
            return

        # Build command
        cmd = [sys.executable, "football_tracker.py"]

        # Add arguments
        cmd.extend(["--model", self.model_var.get()])
        cmd.extend(["--confidence", str(self.confidence_var.get())])

        if self.offline_var.get():
            cmd.append("--offline")

        if self.record_var.get() and self.record_path_var.get():
            cmd.extend(["--record", self.record_path_var.get()])

        if self.verbose_var.get():
            cmd.append("--verbose")

        try:
            # Start the tracking process
            self.tracking_process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )

            self.is_tracking = True
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)

            mode = "Offline" if self.offline_var.get() else "IMX500"
            self.update_status(f"Tracking started ({mode} mode)", "green")

            # Start monitoring thread
            threading.Thread(target=self.monitor_process, daemon=True).start()

        except Exception as e:
            self.update_status(f"Failed to start tracking: {e}", "red")
            messagebox.showerror("Error", f"Failed to start tracking:\n{e}")

    def stop_tracking(self):
        """Stop the tracking process"""
        if self.tracking_process and self.is_tracking:
            try:
                self.tracking_process.terminate()
                self.tracking_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.tracking_process.kill()
            except Exception as e:
                print(f"Error stopping process: {e}")

            self.tracking_process = None
            self.is_tracking = False
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            self.update_status("Tracking stopped", "orange")

    def monitor_process(self):
        """Monitor the tracking process"""
        if self.tracking_process:
            try:
                self.tracking_process.wait()

                # Process ended, update UI
                self.root.after(
                    0,
                    lambda: [
                        setattr(self, "is_tracking", False),
                        self.start_button.config(state=tk.NORMAL),
                        self.stop_button.config(state=tk.DISABLED),
                        self.update_status("Tracking completed", "blue"),
                    ],
                )

            except Exception as e:
                self.root.after(
                    0, lambda: self.update_status(f"Process error: {e}", "red")
                )

    def update_status(self, message, color="black"):
        """Update status label"""
        self.status_label.config(text=message, foreground=color)

    def on_closing(self):
        """Handle window closing"""
        if self.is_tracking:
            if messagebox.askokcancel("Quit", "Tracking is running. Stop and quit?"):
                self.stop_tracking()
                self.root.after(1000, self.root.destroy)  # Give time for cleanup
            else:
                return
        else:
            self.root.destroy()

    def run(self):
        """Run the GUI application"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Set style
        style = ttk.Style()
        if "Accent.TButton" not in style.theme_names():
            style.configure("Accent.TButton", foreground="white", background="blue")

        self.root.mainloop()


def main():
    """Main entry point for GUI"""
    try:
        app = FootballTrackerGUI()
        app.run()
    except Exception as e:
        messagebox.showerror("Error", f"Failed to start GUI:\n{e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
