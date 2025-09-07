@echo off
echo ==========================================
echo Football Tracker Windows Installation
echo ==========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.9 or later from https://python.org
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

echo Python found. Installing dependencies...
echo.

REM Install Windows-compatible requirements
echo Installing Windows-compatible packages...
pip install -r requirements-windows.txt

if errorlevel 1 (
    echo.
    echo WARNING: Some packages failed to install
    echo The application may not work correctly
    echo.
    pause
) else (
    echo.
    echo ==========================================
    echo Installation completed successfully!
    echo ==========================================
    echo.
    echo To run the football tracker:
    echo.
    echo   GUI Mode:
    echo   python gui.py
    echo.
    echo   Command Line (offline mode):
    echo   python football_tracker.py --offline
    echo.
    echo   Command Line with webcam:
    echo   python football_tracker.py --offline --record test.mp4
    echo.
    echo Note: This Windows version runs in offline mode only.
    echo For full IMX500 functionality, use a Raspberry Pi.
    echo.
)

pause
