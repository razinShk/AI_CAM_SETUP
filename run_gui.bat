@echo off
echo ==========================================
echo Football Tracker GUI Launcher
echo ==========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.9 or later from https://python.org
    pause
    exit /b 1
)

REM Check if required files exist
if not exist "gui.py" (
    echo ERROR: gui.py not found
    echo Make sure you're running this from the correct directory
    pause
    exit /b 1
)

if not exist "football_tracker.py" (
    echo ERROR: football_tracker.py not found
    echo Make sure you're running this from the correct directory
    pause
    exit /b 1
)

REM Try to install requirements if requirements.txt exists
if exist "requirements.txt" (
    echo Installing/updating Python dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo WARNING: Failed to install some dependencies
        echo The application may not work correctly
        echo.
    )
)

echo Starting Football Tracker GUI...
echo.
python gui.py

if errorlevel 1 (
    echo.
    echo ERROR: Failed to start the GUI application
    echo Check the error messages above for details
    pause
)
