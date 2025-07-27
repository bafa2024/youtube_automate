#!/usr/bin/env python3
"""
Create Simple Test Videos for B-Roll Organizer
Generates basic test video files using FFmpeg
"""

import os
import subprocess
from pathlib import Path

def create_simple_video(filename, duration=5, color="red"):
    """Create a simple test video using FFmpeg"""
    print(f"🎬 Creating {filename} ({duration}s, {color})...")
    
    # Simple command without text overlay
    cmd = [
        './bin/ffmpeg.exe',
        '-f', 'lavfi',
        '-i', f'color=c={color}:size=1280x720:duration={duration}',
        '-c:v', 'libx264',
        '-preset', 'fast',
        '-crf', '23',
        '-y',
        filename
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Created {filename}")
            return True
        else:
            print(f"❌ Failed to create {filename}: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error creating {filename}: {e}")
        return False

def create_simple_audio(filename, duration=5):
    """Create a simple test audio file using FFmpeg"""
    print(f"🎵 Creating {filename} ({duration}s)...")
    
    # Simple sine wave audio
    cmd = [
        './bin/ffmpeg.exe',
        '-f', 'lavfi',
        '-i', f'sine=frequency=440:duration={duration}',
        '-c:a', 'libmp3lame',
        '-b:a', '192k',
        '-y',
        filename
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Created {filename}")
            return True
        else:
            print(f"❌ Failed to create {filename}: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error creating {filename}: {e}")
        return False

def main():
    """Create all test files"""
    print("🎬 Creating Simple Test Videos for B-Roll Organizer")
    print("=" * 50)
    
    # Check if FFmpeg is available
    try:
        result = subprocess.run(['./bin/ffmpeg.exe', '-version'], capture_output=True, text=True)
        if result.returncode != 0:
            print("❌ FFmpeg not found. Please run install_ffmpeg.py first.")
            return
    except Exception as e:
        print(f"❌ FFmpeg not available: {e}")
        return
    
    print("✅ FFmpeg is available")
    
    # Create test videos
    videos_created = []
    
    # Intro video (blue)
    if create_simple_video("test_intro1.mp4", 3, "blue"):
        videos_created.append("test_intro1.mp4")
    
    # B-roll video 1 (green)
    if create_simple_video("test_broll1.mp4", 4, "green"):
        videos_created.append("test_broll1.mp4")
    
    # B-roll video 2 (yellow)
    if create_simple_video("test_broll2.mp4", 4, "yellow"):
        videos_created.append("test_broll2.mp4")
    
    # Create test audio
    audio_created = []
    if create_simple_audio("test_voiceover.mp3", 10):
        audio_created.append("test_voiceover.mp3")
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Files Created:")
    print(f"   Videos: {len(videos_created)}")
    for video in videos_created:
        print(f"     📹 {video}")
    
    print(f"   Audio: {len(audio_created)}")
    for audio in audio_created:
        print(f"     🎵 {audio}")
    
    if videos_created and audio_created:
        print("\n🎉 All test files created successfully!")
        print("🚀 You can now run the B-roll organizer!")
    else:
        print("\n⚠️ Some files failed to create.")
        print("Please check the errors above.")

if __name__ == "__main__":
    main() 