#!/usr/bin/env python3
"""
Script to generate B-roll reorganized videos in the results folder
"""

import os
import sys
import asyncio
import uuid
from pathlib import Path
from datetime import datetime

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tasks import organize_broll_task
from db_utils import create_job, update_job_status

def create_test_job():
    """Create a test job for B-roll organization"""
    job_id = str(uuid.uuid4())
    
    # Create job in database
    asyncio.run(create_job(
        job_id=job_id,
        user_id=None,
        job_type="broll_organization",
        status="pending",
        message="Test B-roll organization job"
    ))
    
    return job_id

def generate_broll_videos():
    """Generate B-roll reorganized videos using test files"""
    
    print("🎬 Starting B-Roll Video Generation")
    print("=" * 50)
    
    # Check if test files exist
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
    
    # Create test job
    job_id = create_test_job()
    print(f"📋 Created test job: {job_id}")
    
    # Prepare job data
    job_data = {
        "user_id": None,
        "params": {
            "intro_clip_ids": ["test_intro1"],  # We'll use file paths directly
            "broll_clip_ids": ["test_broll1", "test_broll2"],
            "voiceover_id": "test_voiceover",
            "sync_to_voiceover": True,
            "overlay_audio": True
        }
    }
    
    # Create results directory
    results_dir = Path("results")
    results_dir.mkdir(exist_ok=True)
    
    print(f"📁 Results will be saved to: {results_dir.absolute()}")
    
    try:
        # Run the B-roll organization task
        print("🚀 Starting B-roll organization...")
        result = organize_broll_task.apply_async(
            args=[job_id, job_data],
            task_id=job_id
        )
        
        print(f"✅ Task queued successfully: {result.id}")
        print("⏳ Processing... This may take a few minutes.")
        
        # Wait for completion
        while not result.ready():
            print(".", end="", flush=True)
            import time
            time.sleep(2)
        
        print("\n✅ Task completed!")
        
        # Get the result
        task_result = result.get()
        print(f"📊 Task result: {task_result}")
        
        # Check results folder
        print("\n📁 Generated files in results folder:")
        for file_path in results_dir.rglob("*.mp4"):
            print(f"   📹 {file_path.name}")
            print(f"      Size: {file_path.stat().st_size / (1024*1024):.1f} MB")
            print(f"      Path: {file_path.absolute()}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error generating B-roll videos: {e}")
        import traceback
        traceback.print_exc()
        return False

def generate_multiple_variations():
    """Generate multiple B-roll variations with different settings"""
    
    print("\n🎬 Generating Multiple B-Roll Variations")
    print("=" * 50)
    
    variations = [
        {
            "name": "with_intro_and_voiceover",
            "params": {
                "intro_clip_ids": ["test_intro1"],
                "broll_clip_ids": ["test_broll1", "test_broll2"],
                "voiceover_id": "test_voiceover",
                "sync_to_voiceover": True,
                "overlay_audio": True
            }
        },
        {
            "name": "broll_only",
            "params": {
                "intro_clip_ids": [],
                "broll_clip_ids": ["test_broll1", "test_broll2"],
                "voiceover_id": None,
                "sync_to_voiceover": False,
                "overlay_audio": False
            }
        },
        {
            "name": "with_voiceover_no_intro",
            "params": {
                "intro_clip_ids": [],
                "broll_clip_ids": ["test_broll1", "test_broll2"],
                "voiceover_id": "test_voiceover",
                "sync_to_voiceover": True,
                "overlay_audio": True
            }
        }
    ]
    
    for i, variation in enumerate(variations, 1):
        print(f"\n🎬 Generating variation {i}/{len(variations)}: {variation['name']}")
        
        job_id = create_test_job()
        job_data = {
            "user_id": None,
            "params": variation["params"]
        }
        
        try:
            result = organize_broll_task.apply_async(
                args=[job_id, job_data],
                task_id=job_id
            )
            
            print(f"   ⏳ Processing {variation['name']}...")
            
            # Wait for completion
            while not result.ready():
                print(".", end="", flush=True)
                import time
                time.sleep(2)
            
            print(f"\n   ✅ {variation['name']} completed!")
            
        except Exception as e:
            print(f"\n   ❌ Error with {variation['name']}: {e}")

if __name__ == "__main__":
    print("🎬 B-Roll Video Generator")
    print("=" * 50)
    
    # Check if server is running
    try:
        import requests
        response = requests.get("http://localhost:8080/api/jobs", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running")
        else:
            print("⚠️ Server responded but may not be fully ready")
    except Exception as e:
        print("❌ Server is not running. Please start the server first:")
        print("   python main.py")
        sys.exit(1)
    
    # Generate basic B-roll video
    success = generate_broll_videos()
    
    if success:
        print("\n🎉 B-Roll video generation completed successfully!")
        print("\n📁 Check the 'results' folder for generated videos.")
        
        # Ask if user wants multiple variations
        try:
            response = input("\n🤔 Generate multiple variations? (y/n): ").lower().strip()
            if response in ['y', 'yes']:
                generate_multiple_variations()
        except KeyboardInterrupt:
            print("\n\n⏹️ Generation interrupted by user")
    else:
        print("\n❌ B-Roll video generation failed.")
        sys.exit(1) 