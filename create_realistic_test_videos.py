#!/usr/bin/env python3
"""
Create Realistic Test Videos for B-Roll Organizer
Generates test video files with actual content and better audio
"""
import os
import subprocess
from pathlib import Path

def create_video_with_text(filename, duration=5, text="Test Video", color="white", bg_color="black"):
    """Create a video with text overlay"""
    cmd = [
        "./bin/ffmpeg.exe",
        "-f", "lavfi",
        "-i", f"color=c={bg_color}:s=1280x720:r=30:d={duration}",
        "-vf", f"drawtext=text='{text}':fontcolor={color}:fontsize=60:x=(w-text_w)/2:y=(h-text_h)/2",
        "-c:a", "aac",
        "-b:a", "128k",
        "-y",  # Overwrite output file
        filename
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(f"✅ Created {filename}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error creating {filename}: {e}")
        print(f"FFmpeg output: {e.stderr}")
        return False

def create_audio_with_music(filename, duration=5):
    """Create audio with a more pleasant tone"""
    cmd = [
        "./bin/ffmpeg.exe",
        "-f", "lavfi",
        "-i", f"sine=frequency=440:duration={duration}",
        "-f", "lavfi",
        "-i", f"sine=frequency=880:duration={duration}",
        "-filter_complex", "[0:a][1:a]amix=inputs=2:duration=longest",
        "-c:a", "mp3",
        "-b:a", "192k",
        "-y",
        filename
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(f"✅ Created {filename}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error creating {filename}: {e}")
        print(f"FFmpeg output: {e.stderr}")
        return False

def main():
    """Create all test videos"""
    print("🎬 Creating realistic test videos...")
    
    # Create intro video
    success1 = create_video_with_text("test_intro1.mp4", 3, "INTRO VIDEO", "white", "darkblue")
    
    # Create B-roll videos with different content
    success2 = create_video_with_text("test_broll1.mp4", 4, "B-ROLL CLIP 1", "white", "darkgreen")
    success3 = create_video_with_text("test_broll2.mp4", 4, "B-ROLL CLIP 2", "white", "darkred")
    
    # Create voiceover audio
    success4 = create_audio_with_music("test_voiceover.mp3", 10)
    
    if all([success1, success2, success3, success4]):
        print("\n🎉 All test videos created successfully!")
        print("📁 Files created:")
        print("  - test_intro1.mp4 (Intro video)")
        print("  - test_broll1.mp4 (B-roll clip 1)")
        print("  - test_broll2.mp4 (B-roll clip 2)")
        print("  - test_voiceover.mp3 (Voiceover audio)")
        print("\nThese videos now contain actual text content instead of just colored screens.")
    else:
        print("\n❌ Some videos failed to create. Check the errors above.")

if __name__ == "__main__":
    main() 