#!/usr/bin/env python3
"""
FFmpeg Installer for Windows
Downloads and installs FFmpeg automatically
"""

import os
import sys
import zipfile
import requests
from pathlib import Path
import subprocess
import shutil

def download_ffmpeg():
    """Download FFmpeg for Windows"""
    print("🎬 Installing FFmpeg for Windows...")
    
    # FFmpeg download URL (latest release)
    ffmpeg_url = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
    
    # Create temp directory
    temp_dir = Path("temp_ffmpeg")
    temp_dir.mkdir(exist_ok=True)
    
    zip_path = temp_dir / "ffmpeg.zip"
    
    print("📥 Downloading FFmpeg...")
    try:
        response = requests.get(ffmpeg_url, stream=True)
        response.raise_for_status()
        
        with open(zip_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print("✅ Download completed")
        
    except Exception as e:
        print(f"❌ Download failed: {e}")
        return False
    
    # Extract FFmpeg
    print("📦 Extracting FFmpeg...")
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        
        print("✅ Extraction completed")
        
    except Exception as e:
        print(f"❌ Extraction failed: {e}")
        return False
    
    # Find FFmpeg executable
    ffmpeg_exe = None
    for item in temp_dir.rglob("ffmpeg.exe"):
        ffmpeg_exe = item
        break
    
    if not ffmpeg_exe:
        print("❌ Could not find ffmpeg.exe in extracted files")
        return False
    
    # Create bin directory in current folder
    bin_dir = Path("bin")
    bin_dir.mkdir(exist_ok=True)
    
    # Copy FFmpeg files to bin directory
    print("📁 Installing FFmpeg to bin directory...")
    try:
        # Copy ffmpeg.exe
        shutil.copy2(ffmpeg_exe, bin_dir / "ffmpeg.exe")
        
        # Copy ffprobe.exe (should be in same directory)
        ffprobe_exe = ffmpeg_exe.parent / "ffprobe.exe"
        if ffprobe_exe.exists():
            shutil.copy2(ffprobe_exe, bin_dir / "ffprobe.exe")
        
        print("✅ FFmpeg installed successfully")
        
    except Exception as e:
        print(f"❌ Installation failed: {e}")
        return False
    
    # Clean up
    try:
        shutil.rmtree(temp_dir)
        print("🧹 Cleaned up temporary files")
    except Exception as e:
        print(f"⚠️ Could not clean up temp files: {e}")
    
    return True

def test_ffmpeg():
    """Test if FFmpeg is working"""
    print("🧪 Testing FFmpeg installation...")
    
    try:
        # Try to run ffmpeg from bin directory
        result = subprocess.run(
            ["./bin/ffmpeg.exe", "-version"], 
            capture_output=True, 
            text=True,
            cwd=os.getcwd()
        )
        
        if result.returncode == 0:
            print("✅ FFmpeg is working!")
            return True
        else:
            print("❌ FFmpeg test failed")
            return False
            
    except Exception as e:
        print(f"❌ FFmpeg test error: {e}")
        return False

def update_video_processor():
    """Update video processor to use local FFmpeg"""
    print("🔧 Updating video processor to use local FFmpeg...")
    
    try:
        # Read the video processor file
        with open("core/video_processor.py", "r") as f:
            content = f.read()
        
        # Replace ffmpeg and ffprobe commands to use local bin directory
        content = content.replace("ffmpeg", "./bin/ffmpeg.exe")
        content = content.replace("ffprobe", "./bin/ffprobe.exe")
        
        # Write back the updated content
        with open("core/video_processor.py", "w") as f:
            f.write(content)
        
        print("✅ Video processor updated")
        return True
        
    except Exception as e:
        print(f"❌ Failed to update video processor: {e}")
        return False

def main():
    """Main installation function"""
    print("🎬 FFmpeg Installer for B-Roll Organizer")
    print("=" * 50)
    
    # Check if FFmpeg is already installed
    if test_ffmpeg():
        print("✅ FFmpeg is already installed and working!")
        return True
    
    # Install FFmpeg
    if download_ffmpeg():
        # Update video processor
        if update_video_processor():
            # Test again
            if test_ffmpeg():
                print("\n🎉 FFmpeg installation completed successfully!")
                print("🚀 You can now generate B-roll videos!")
                return True
    
    print("\n❌ FFmpeg installation failed.")
    print("💡 You can manually install FFmpeg from: https://ffmpeg.org/download.html")
    return False

if __name__ == "__main__":
    main() 