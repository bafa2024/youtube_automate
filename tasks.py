"""
Celery tasks for background processing
"""

import os
import time
import json
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

from celery import Celery, Task
from celery.result import AsyncResult
import redis

# Import core modules
from core.video_processor import VideoProcessor
from core.audio_processor import AudioProcessor
from core.api_manager import APIKeyManager
from core.openai_generator import OpenAIImageGenerator

# Import database and WebSocket manager
from database import JobStatus, GeneratedImage, FileRecord
# Removed: from sqlalchemy.orm import Session
# Removed: from sqlalchemy import create_engine
from config import settings

# Setup Celery
celery_app = Celery(
    'ai_video_tool',
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

# Configure Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour timeout
    task_soft_time_limit=3300,  # 55 minutes soft timeout
)

# Database engine for sync operations in Celery
# Removed: engine = create_engine(settings.DATABASE_URL.replace("sqlite+aiosqlite", "sqlite"))

# Redis client for pub/sub
redis_client = redis.from_url(settings.REDIS_URL)

class CallbackTask(Task):
    """Base task with callbacks for progress updates"""
    
    def __init__(self):
        self.job_id = None
        self.user_id = None
    
    def update_progress(self, progress: int, message: str = ""):
        """Update job progress in database and notify via WebSocket"""
        if not self.job_id:
            return
        
        # Removed: with Session(engine) as db:
        # Removed: job = db.query(JobStatus).filter(JobStatus.job_id == self.job_id).first()
        # Removed: if job:
        # Removed: job.progress = progress
        # Removed: if message:
        # Removed: job.message = message
        # Removed: db.commit()
        
        # Publish update to Redis for WebSocket
        update_data = {
            "job_id": self.job_id,
            "user_id": self.user_id,
            "progress": progress,
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        }
        redis_client.publish(f"job_updates:{self.user_id}", json.dumps(update_data))

@celery_app.task(bind=True, base=CallbackTask, name='tasks.generate_ai_images')
def generate_ai_images_task(self, job_id: str, job_data: Dict[str, Any]):
    """Background task for AI image generation"""
    self.job_id = job_id
    self.user_id = job_data['user_id']
    
    try:
        # Update job status to processing
        # Removed: with Session(engine) as db:
        # Removed: job = db.query(JobStatus).filter(JobStatus.job_id == job_id).first()
        # Removed: job.status = "processing"
        # Removed: job.started_at = datetime.utcnow()
        # Removed: db.commit()
        
        self.update_progress(5, "Initializing AI image generation...")
        
        # Extract parameters
        params = job_data['params']
        script_path = params['script_path']
        voice_path = params['voice_path']
        image_count = params['image_count']
        style = params['style']
        character_desc = params['character_description']
        export_options = params['export_options']
        
        # Create output directory
        output_dir = Path(settings.OUTPUT_DIR) / job_id
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize processors
        self.update_progress(10, "Loading API credentials...")
        api_manager = APIKeyManager()
        api_key = api_manager.get_api_key()
        
        if not api_key:
            raise Exception("OpenAI API key not configured")
        
        openai_gen = OpenAIImageGenerator(api_key)
        audio_proc = AudioProcessor()
        video_proc = VideoProcessor()
        
        # Read script
        self.update_progress(15, "Reading script file...")
        with open(script_path, 'r', encoding='utf-8') as f:
            script_text = f.read()
        
        # Get audio duration and timestamps
        self.update_progress(20, "Analyzing voiceover duration...")
        duration = audio_proc.get_duration(voice_path)
        timestamps = audio_proc.generate_timestamps(duration, image_count)
        
        # Split script into segments
        script_segments = split_script(script_text, image_count)
        
        # Generate images
        generated_images = []
        
        for i, (segment, timestamp) in enumerate(zip(script_segments, timestamps)):
            if self.is_aborted():
                raise Exception("Task cancelled by user")
            
            progress = 20 + int((i / image_count) * 60)  # 20-80% for image generation
            self.update_progress(progress, f"Generating image {i+1} of {image_count}...")
            
            # Create prompt
            prompt = openai_gen.create_scene_prompt(
                segment, 
                character_desc, 
                style,
                scene_number=i+1
            )
            
            # Generate image
            start_time = time.time()
            try:
                image_path = openai_gen.generate_and_save_image(
                    prompt, 
                    str(output_dir),
                    f"scene_{i+1:03d}",
                    style
                )
                generation_time = time.time() - start_time
                
                # Store in database
                # Removed: with Session(engine) as db:
                # Removed: db_image = GeneratedImage(
                # Removed: job_id=job_id,
                # Removed: image_path=image_path,
                # Removed: prompt=prompt,
                # Removed: style=style,
                # Removed: timestamp=timestamp,
                # Removed: scene_number=i+1,
                # Removed: generation_time=generation_time
                # Removed: )
                # Removed: db.add(db_image)
                # Removed: db.commit()
                
                generated_images.append({
                    'path': image_path,
                    'timestamp': timestamp,
                    'duration': timestamps[i+1] - timestamp if i < len(timestamps)-1 else duration - timestamp
                })
                
            except Exception as e:
                self.update_progress(progress, f"Failed to generate image {i+1}: {str(e)}")
                continue
        
        # Save metadata
        metadata_path = output_dir / 'generation_metadata.json'
        with open(metadata_path, 'w') as f:
            json.dump({
                'images': generated_images,
                'script_path': script_path,
                'voice_path': voice_path,
                'total_duration': duration,
                'character_description': character_desc,
                'style': style,
                'job_id': job_id
            }, f, indent=2)
        
        # Export based on options
        results = {'images': str(output_dir)}
        
        if export_options.get('clips', False):
            self.update_progress(85, "Creating video clips from images...")
            video_proc.images_to_clips(generated_images, str(output_dir))
            results['clips'] = str(output_dir)
        
        if export_options.get('full_video', False):
            self.update_progress(90, "Creating full video with voiceover...")
            final_video_path = output_dir / 'final_video.mp4'
            video_proc.create_full_video(
                generated_images, 
                voice_path, 
                str(final_video_path)
            )
            results['video'] = str(final_video_path)
        
        # Update job as completed
        self.update_progress(100, "AI image generation completed!")
        
        # Removed: with Session(engine) as db:
        # Removed: job = db.query(JobStatus).filter(JobStatus.job_id == job_id).first()
        # Removed: job.status = "completed"
        # Removed: job.completed_at = datetime.utcnow()
        # Removed: job.result_path = str(output_dir)
        # Removed: job.result_metadata = results
        # Removed: db.commit()
        
        return {
            "status": "success",
            "job_id": job_id,
            "results": results
        }
        
    except Exception as e:
        # Handle errors
        import traceback
        error_traceback = traceback.format_exc()
        
        # Removed: with Session(engine) as db:
        # Removed: job = db.query(JobStatus).filter(JobStatus.job_id == job_id).first()
        # Removed: job.status = "failed"
        # Removed: job.completed_at = datetime.utcnow()
        # Removed: job.error_message = str(e)
        # Removed: job.error_traceback = error_traceback
        # Removed: db.commit()
        
        self.update_progress(0, f"Error: {str(e)}")
        raise

@celery_app.task(bind=True, base=CallbackTask, name='tasks.organize_broll')
def organize_broll_task(self, job_id: str, job_data: Dict[str, Any]):
    """Background task for B-roll organization"""
    self.job_id = job_id
    self.user_id = job_data['user_id']
    
    try:
        # Update job status
        # Removed: with Session(engine) as db:
        # Removed: job = db.query(JobStatus).filter(JobStatus.job_id == job_id).first()
        # Removed: job.status = "processing"
        # Removed: job.started_at = datetime.utcnow()
        # Removed: db.commit()
        
        self.update_progress(5, "Starting B-roll reorganization...")
        
        # Extract parameters
        params = job_data['params']
        
        # Get file paths from database
        # Removed: with Session(engine) as db:
        intro_paths = []
        for file_id in params['intro_clip_ids']:
            # Removed: file_record = db.query(FileRecord).filter(FileRecord.file_id == file_id).first()
            # Removed: if file_record:
            intro_paths.append(file_id) # Assuming file_id is the path for now
        
        broll_paths = []
        for file_id in params['broll_clip_ids']:
            # Removed: file_record = db.query(FileRecord).filter(FileRecord.file_id == file_id).first()
            # Removed: if file_record:
            broll_paths.append(file_id) # Assuming file_id is the path for now
        
        voiceover_path = None
        if params['voiceover_id']:
            # Removed: voice_file = db.query(FileRecord).filter(
            # Removed: FileRecord.file_id == params['voiceover_id']
            # Removed: ).first()
            # Removed: if voice_file:
            voiceover_path = params['voiceover_id'] # Assuming voiceover_id is the path for now
        
        # Create output directory
        output_dir = Path(settings.OUTPUT_DIR) / job_id
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize processors
        video_proc = VideoProcessor()
        audio_proc = AudioProcessor()
        
        # Get target duration if syncing with voiceover
        target_duration = None
        if params['sync_to_voiceover'] and voiceover_path:
            self.update_progress(10, "Analyzing voiceover duration...")
            # Removed: target_duration = audio_proc.get_duration(voiceover_path)
        
        # Shuffle B-roll
        self.update_progress(20, "Shuffling B-roll clips...")
        import random
        shuffled_broll = broll_paths.copy()
        random.shuffle(shuffled_broll)
        
        # Combine clips
        all_clips = intro_paths + shuffled_broll
        
        # Create reorganized video
        self.update_progress(30, "Creating reorganized video...")
        output_path = output_dir / 'broll_reorganized.mp4'
        
        # Progress callback for video processing
        def video_progress(p):
            overall_progress = 30 + int(p * 50)  # 30-80%
            self.update_progress(overall_progress, "Processing video clips...")
        
        video_proc.concatenate_clips(
            all_clips, 
            str(output_path),
            target_duration=target_duration,
            progress_callback=video_progress
        )
        
        results = {'video': str(output_path)}
        
        # Overlay audio if requested
        if params['overlay_audio'] and voiceover_path:
            self.update_progress(85, "Overlaying voiceover...")
            final_path = output_dir / 'broll_with_voiceover.mp4'
            video_proc.add_audio_to_video(
                str(output_path), 
                voiceover_path, 
                str(final_path)
            )
            results['video_with_audio'] = str(final_path)
        
        # Update job as completed
        self.update_progress(100, "B-roll reorganization completed!")
        
        # Removed: with Session(engine) as db:
        # Removed: job = db.query(JobStatus).filter(JobStatus.job_id == job_id).first()
        # Removed: job.status = "completed"
        # Removed: job.completed_at = datetime.utcnow()
        # Removed: job.result_path = str(results.get('video_with_audio', results['video']))
        # Removed: job.result_metadata = results
        # Removed: db.commit()
        
        return {
            "status": "success",
            "job_id": job_id,
            "results": results
        }
        
    except Exception as e:
        # Handle errors
        import traceback
        error_traceback = traceback.format_exc()
        
        # Removed: with Session(engine) as db:
        # Removed: job = db.query(JobStatus).filter(JobStatus.job_id == job_id).first()
        # Removed: job.status = "failed"
        # Removed: job.completed_at = datetime.utcnow()
        # Removed: job.error_message = str(e)
        # Removed: job.error_traceback = error_traceback
        # Removed: db.commit()
        
        self.update_progress(0, f"Error: {str(e)}")
        raise

# Utility functions
def split_script(script: str, num_segments: int) -> List[str]:
    """Split script into roughly equal segments"""
    words = script.split()
    words_per_segment = len(words) // num_segments
    segments = []
    
    for i in range(num_segments):
        start_idx = i * words_per_segment
        if i == num_segments - 1:
            # Last segment gets remaining words
            segment = ' '.join(words[start_idx:])
        else:
            segment = ' '.join(words[start_idx:start_idx + words_per_segment])
        segments.append(segment)
    
    return segments

# Periodic cleanup task
@celery_app.task(name='tasks.cleanup_old_files')
def cleanup_old_files():
    """Clean up old files and expired jobs"""
    import shutil
    from datetime import timedelta
    
    cutoff_date = datetime.utcnow() - timedelta(days=settings.FILE_RETENTION_DAYS)
    
    # Removed: with Session(engine) as db:
    # Find old files
    old_files = [] # Placeholder for aiosqlite query
    for file_record in old_files:
        # Delete physical file
        try:
            if os.path.exists(file_record.file_path):
                os.remove(file_record.file_path)
        except Exception as e:
            print(f"Error deleting file {file_record.file_path}: {e}")
        
        # Delete record
        # Removed: db.delete(file_record)
    
    # Clean up old job output directories
    old_jobs = [] # Placeholder for aiosqlite query
    for job in old_jobs:
        # Delete output directory
        output_dir = Path(settings.OUTPUT_DIR) / job.job_id
        if output_dir.exists():
            try:
                shutil.rmtree(output_dir)
            except Exception as e:
                print(f"Error deleting directory {output_dir}: {e}")
    
    # Removed: db.commit()

# Schedule periodic tasks
from celery.schedules import crontab

celery_app.conf.beat_schedule = {
    'cleanup-old-files': {
        'task': 'tasks.cleanup_old_files',
        'schedule': crontab(hour=3, minute=0),  # Run at 3 AM daily
    },
}