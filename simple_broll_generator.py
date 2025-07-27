#!/usr/bin/env python3
"""
Simple B-Roll Video Generator
Generates reorganized B-roll videos directly using the video processor
"""

import os
import sys
import random
from pathlib import Path
from datetime import datetime

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.video_processor import VideoProcessor
from core.audio_processor import AudioProcessor

def check_test_files():
    """Check if required test files exist"""
    test_files = {
        'intro': 'test_intro1.mp4',
        'broll1': 'test_broll1.mp4', 
        'broll2': 'test_broll2.mp4',
        'voiceover': 'test_voiceover.mp3'
    }
    
    missing_files = []
    for file_type, filename in test_files.items():
        if not os.path.exists(filename):
            missing_files.append(filename)
    
    if missing_files:
        print(f"❌ Missing test files: {missing_files}")
        print("Please ensure all test files are present in the current directory.")
        return False
    
    print("✅ All test files found")
    return True

def generate_broll_video(output_name="broll_reorganized", include_intro=True, include_voiceover=True):
    """Generate a B-roll reorganized video"""
    
    print(f"🎬 Generating: {output_name}")
    
    # Create results directory
    results_dir = Path("results")
    results_dir.mkdir(exist_ok=True)
    
    # Create timestamped output directory
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_dir = results_dir / f"{output_name}_{timestamp}"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize processors
    video_proc = VideoProcessor()
    audio_proc = AudioProcessor()
    
    # Prepare clip lists
    intro_clips = []
    broll_clips = []
    
    if include_intro and os.path.exists('test_intro1.mp4'):
        intro_clips.append('test_intro1.mp4')
    
    if os.path.exists('test_broll1.mp4'):
        broll_clips.append('test_broll1.mp4')
    if os.path.exists('test_broll2.mp4'):
        broll_clips.append('test_broll2.mp4')
    
    # Shuffle B-roll clips
    random.shuffle(broll_clips)
    
    # Combine all clips
    all_clips = intro_clips + broll_clips
    
    if not all_clips:
        print("❌ No video clips found!")
        return False
    
    print(f"📹 Processing {len(all_clips)} clips:")
    for i, clip in enumerate(all_clips, 1):
        print(f"   {i}. {os.path.basename(clip)}")
    
    # Get target duration if voiceover exists
    target_duration = None
    if include_voiceover and os.path.exists('test_voiceover.mp3'):
        try:
            target_duration = audio_proc.get_duration('test_voiceover.mp3')
            print(f"🎵 Voiceover duration: {target_duration:.2f} seconds")
        except Exception as e:
            print(f"⚠️ Could not get voiceover duration: {e}")
    
    # Create reorganized video
    output_path = output_dir / 'broll_reorganized.mp4'
    print(f"🎬 Creating reorganized video: {output_path}")
    
    try:
        # For now, don't use target_duration to avoid concatenation issues
        video_proc.concatenate_clips(all_clips, str(output_path), target_duration=None)
        print(f"✅ Base video created: {output_path}")
        
        # Add voiceover if requested
        if include_voiceover and os.path.exists('test_voiceover.mp3'):
            final_path = output_dir / 'broll_with_voiceover.mp4'
            print(f"🎵 Adding voiceover: {final_path}")
            
            video_proc.add_audio_to_video(str(output_path), 'test_voiceover.mp3', str(final_path))
            print(f"✅ Final video with voiceover: {final_path}")
            
            # Create a copy in results folder for easy access
            results_copy = results_dir / f"latest_{output_name}.mp4"
            import shutil
            shutil.copy2(final_path, results_copy)
            print(f"📁 Easy access copy: {results_copy}")
            
            return str(final_path)
        else:
            # Create a copy in results folder for easy access
            results_copy = results_dir / f"latest_{output_name}.mp4"
            import shutil
            shutil.copy2(output_path, results_copy)
            print(f"📁 Easy access copy: {results_copy}")
            
            return str(output_path)
            
    except Exception as e:
        print(f"❌ Error creating video: {e}")
        import traceback
        traceback.print_exc()
        return False

def generate_multiple_variations():
    """Generate multiple B-roll variations"""
    
    print("\n🎬 Generating Multiple B-Roll Variations")
    print("=" * 50)
    
    variations = [
        {
            "name": "with_intro_and_voiceover",
            "include_intro": True,
            "include_voiceover": True
        },
        {
            "name": "broll_only",
            "include_intro": False,
            "include_voiceover": False
        },
        {
            "name": "with_voiceover_no_intro",
            "include_intro": False,
            "include_voiceover": True
        },
        {
            "name": "with_intro_no_voiceover",
            "include_intro": True,
            "include_voiceover": False
        }
    ]
    
    results = []
    
    for i, variation in enumerate(variations, 1):
        print(f"\n🎬 Generating variation {i}/{len(variations)}: {variation['name']}")
        
        result = generate_broll_video(
            output_name=variation['name'],
            include_intro=variation['include_intro'],
            include_voiceover=variation['include_voiceover']
        )
        
        if result:
            results.append((variation['name'], result))
            print(f"✅ {variation['name']} completed!")
        else:
            print(f"❌ {variation['name']} failed!")
    
    return results

def main():
    """Main function"""
    print("🎬 Simple B-Roll Video Generator")
    print("=" * 50)
    
    # Check test files
    if not check_test_files():
        return
    
    # Create results directory
    results_dir = Path("results")
    results_dir.mkdir(exist_ok=True)
    print(f"📁 Results will be saved to: {results_dir.absolute()}")
    
    # Generate basic B-roll video
    print("\n🎬 Generating basic B-roll video...")
    result = generate_broll_video("basic_broll", include_intro=True, include_voiceover=True)
    
    if result:
        print(f"\n✅ Basic B-roll video created: {result}")
        
        # Ask if user wants multiple variations
        try:
            response = input("\n🤔 Generate multiple variations? (y/n): ").lower().strip()
            if response in ['y', 'yes']:
                results = generate_multiple_variations()
                
                print(f"\n🎉 Generated {len(results)} variations:")
                for name, path in results:
                    print(f"   📹 {name}: {path}")
        except KeyboardInterrupt:
            print("\n\n⏹️ Generation interrupted by user")
        
        print(f"\n📁 All videos saved in: {results_dir.absolute()}")
        print("🎬 B-roll video generation completed!")
        
    else:
        print("\n❌ B-roll video generation failed.")

if __name__ == "__main__":
    main() 