#!/usr/bin/env python3
"""
Create Test Videos for B-Roll Organizer
Generates simple test video files using FFmpeg
"""

import os
import subprocess
from pathlib import Path

def create_test_video(filename, duration=5, color="red", text="Test Video"):
    """Create a simple test video using FFmpeg"""
    print(f"🎬 Creating {filename} ({duration}s, {color})...")
    
    cmd = [
        './bin/ffmpeg.exe',
        '-f', 'lavfi',
        '-i', f'color=c={color}:size=1280x720:duration={duration}',
        '-f', 'lavfi',
        '-i', f'drawtext=text=\'{text}\':fontsize=60:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2',
        '-filter_complex', '[0:v][1:v]overlay',
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

def create_test_audio(filename, duration=5, frequency=440):
    """Create a simple test audio file using FFmpeg"""
    print(f"🎵 Creating {filename} ({duration}s, {frequency}Hz)...")
    
    cmd = [
        './bin/ffmpeg.exe',
        '-f', 'lavfi',
        '-i', f'sine=frequency={frequency}:duration={duration}',
        '-c:a', 'aac',
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
    print("🎬 Creating Test Videos for B-Roll Organizer")
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
    if create_test_video("test_intro1.mp4", 3, "blue", "INTRO"):
        videos_created.append("test_intro1.mp4")
    
    # B-roll video 1 (green)
    if create_test_video("test_broll1.mp4", 4, "green", "B-ROLL 1"):
        videos_created.append("test_broll1.mp4")
    
    # B-roll video 2 (yellow)
    if create_test_video("test_broll2.mp4", 4, "yellow", "B-ROLL 2"):
        videos_created.append("test_broll2.mp4")
    
    # Create test audio
    audio_created = []
    if create_test_audio("test_voiceover.mp3", 10, 440):
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