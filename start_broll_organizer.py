#!/usr/bin/env python3
"""
Startup script for B-Roll Organizer
This script checks prerequisites and starts the application
"""

import os
import sys
import subprocess
import importlib.util
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    print("🐍 Checking Python version...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Python 3.8+ required. Current version: {version.major}.{version.minor}")
        return False
    print(f"✅ Python version: {version.major}.{version.minor}.{version.micro}")
    return True

def check_ffmpeg():
    """Check if FFmpeg is installed"""
    print("🎬 Checking FFmpeg installation...")
    try:
        result = subprocess.run(['ffmpeg', '-version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ FFmpeg is installed")
            return True
        else:
            print("❌ FFmpeg is not working properly")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("❌ FFmpeg is not installed")
        print("\n📋 To install FFmpeg:")
        print("   Windows: Download from https://ffmpeg.org/download.html")
        print("   macOS: brew install ffmpeg")
        print("   Linux: sudo apt install ffmpeg")
        return False

def check_dependencies():
    """Check if required Python packages are installed"""
    print("📦 Checking Python dependencies...")
    
    required_packages = [
        'fastapi',
        'uvicorn',
        'aiofiles',
        'aiosqlite',
        'celery',
        'redis'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            importlib.import_module(package.replace('-', '_'))
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - Missing")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n📋 Install missing packages:")
        print(f"   pip install {' '.join(missing_packages)}")
        return False
    
    return True

def create_directories():
    """Create necessary directories"""
    print("📁 Creating directories...")
    
    directories = ['uploads', 'outputs', 'temp', 'processed']
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Created {directory}/")

def start_application():
    """Start the B-Roll Organizer application"""
    print("\n🚀 Starting B-Roll Organizer...")
    print("=" * 50)
    
    try:
        # Import and start the application
        from main import app
        import uvicorn
        
        print("✅ Application loaded successfully")
        print("🌐 Starting web server...")
        print("📱 Open your browser to: http://localhost:8080")
        print("🛑 Press Ctrl+C to stop the server")
        print("=" * 50)
        
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8080,
            reload=True,
            log_level="info"
        )
        
    except ImportError as e:
        print(f"❌ Failed to import application: {e}")
        print("💡 Make sure all dependencies are installed:")
        print("   pip install -r requirements.txt")
        return False
    except Exception as e:
        print(f"❌ Failed to start application: {e}")
        return False

def main():
    """Main function"""
    print("🎬 B-Roll Organizer - Startup Check")
    print("=" * 50)
    
    # Check prerequisites
    checks = [
        ("Python Version", check_python_version),
        ("FFmpeg", check_ffmpeg),
        ("Dependencies", check_dependencies)
    ]
    
    all_passed = True
    for check_name, check_func in checks:
        if not check_func():
            all_passed = False
            print(f"\n❌ {check_name} check failed")
            break
        print()
    
    if not all_passed:
        print("\n⚠️  Please fix the issues above before starting the application")
        return False
    
    # Create directories
    create_directories()
    
    # Start application
    return start_application()

if __name__ == "__main__":
    try:
        success = main()
        if not success:
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n👋 Application stopped by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1) 