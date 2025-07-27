@echo off
echo.
echo ========================================
echo    B-Roll Organizer - Startup Script
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

echo ✅ Python found
echo.

REM Check if FFmpeg is installed
ffmpeg -version >nul 2>&1
if errorlevel 1 (
    echo ❌ FFmpeg is not installed
    echo.
    echo 📋 To install FFmpeg:
    echo   1. Download from https://ffmpeg.org/download.html
    echo   2. Extract to a folder (e.g., C:\ffmpeg)
    echo   3. Add C:\ffmpeg\bin to your PATH environment variable
    echo.
    echo Or use Chocolatey: choco install ffmpeg
    echo Or use Scoop: scoop install ffmpeg
    echo.
    pause
    exit /b 1
)

echo ✅ FFmpeg found
echo.

REM Install dependencies if needed
echo 📦 Checking dependencies...
pip install -r requirements.txt >nul 2>&1
if errorlevel 1 (
    echo ⚠️  Some dependencies may be missing
    echo Installing requirements...
    pip install -r requirements.txt
)

echo ✅ Dependencies ready
echo.

REM Create necessary directories
if not exist "uploads" mkdir uploads
if not exist "outputs" mkdir outputs
if not exist "temp" mkdir temp
if not exist "processed" mkdir processed

echo ✅ Directories created
echo.

REM Start the application
echo 🚀 Starting B-Roll Organizer...
echo.
echo 📱 Open your browser to: http://localhost:8080
echo 🛑 Press Ctrl+C to stop the server
echo.
echo ========================================

python start_broll_organizer.py

pause 