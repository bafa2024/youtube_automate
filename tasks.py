"""
Celery tasks for background processing
"""

import os
import time
import json
# import asyncio  # Not needed for synchronous tasks
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
from core.document_processor import DocumentProcessor

# Import database and WebSocket manager
from db_utils import create_job, get_job_by_id, update_job_status, get_file_by_id
from db_utils_sync import get_file_by_id_sync, update_job_status_sync
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
try:
    redis_client = redis.from_url(settings.REDIS_URL)
except:
    redis_client = None

class CallbackTask(Task):
    """Base task with callbacks for progress updates"""
    
    def __init__(self):
        self.job_id = None
        self.user_id = None
    
    def update_progress(self, progress: int, message: str = ""):
        """Update job progress in database and notify via WebSocket"""
        if not self.job_id:
            return
        
        # Update job status in database
        try:
            update_job_status_sync(
                job_id=self.job_id,
                status="processing",
                message=message,
                progress=progress
            )
        except Exception as e:
            # Log error but don't fail the task
            print(f"Failed to update job status in database: {e}")
        
        # Publish update to Redis for WebSocket
        if redis_client:
            update_data = {
                "job_id": self.job_id,
                "user_id": self.user_id,
                "progress": progress,
                "message": message,
                "timestamp": datetime.utcnow().isoformat()
            }
            redis_client.publish(f"job_updates:{self.user_id}", json.dumps(update_data))

# Synchronous task functions (no Redis required)
def run_ai_images_task_sync(job_id: str, job_data: Dict[str, Any]):
    """Synchronous AI image generation task"""
    try:
        # Update job status to processing
        update_job_status_sync(
            job_id=job_id,
            status="processing",
            message="Initializing AI image generation...",
            progress=5
        )
        
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
        update_job_status_sync(job_id, "processing", "Loading API credentials...", 10)
        api_manager = APIKeyManager()
        api_key = api_manager.get_api_key()
        
        if not api_key:
            raise Exception("OpenAI API key not configured")
        
        openai_gen = OpenAIImageGenerator(api_key)
        audio_proc = AudioProcessor()
        video_proc = VideoProcessor()
        
        # Read script using DocumentProcessor
        update_job_status_sync(job_id, "processing", "Reading script file...", 15)
        doc_processor = DocumentProcessor()
        try:
            script_text = doc_processor.extract_text(script_path)
            if not script_text or script_text.strip() == "":
                script_text = params.get('script_text', 'Generate images based on the uploaded content.')
        except Exception as e:
            logger.error(f"Failed to extract text from script: {e}")
            script_text = params.get('script_text', 'Generate images based on the uploaded content.')
        
        # Get audio duration and timestamps
        update_job_status_sync(job_id, "processing", "Analyzing voiceover duration...", 20)
        duration = audio_proc.get_duration(voice_path)
        timestamps = audio_proc.generate_timestamps(duration, image_count)
        
        # Split script into segments
        script_segments = split_script(script_text, image_count)
        
        # Generate images
        generated_images = []
        
        for i, (segment, timestamp) in enumerate(zip(script_segments, timestamps)):
            # More granular progress calculation
            progress = 20 + int(((i + 0.5) / image_count) * 60)  # 20-80% for image generation
            update_job_status_sync(job_id, "processing", f"Generating image {i+1} of {image_count}...", progress)
            
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
                
                generated_images.append({
                    'path': image_path,
                    'timestamp': timestamp,
                    'duration': timestamps[i+1] - timestamp if i < len(timestamps)-1 else duration - timestamp
                })
                
            except Exception as e:
                update_job_status_sync(job_id, "processing", f"Failed to generate image {i+1}: {str(e)}", progress)
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
        
        # Store results - only images for now
        results = {'images': str(output_dir)}
        
        # Prepare result data with image paths relative to output directory
        image_filenames = []
        for img in generated_images:
            # Get just the filename from the full path
            filename = Path(img['path']).name
            image_filenames.append(f"{job_id}/{filename}")
        
        result_data = {
            "images": image_filenames,
            "script_text": script_text,
            "output_dir": str(output_dir),
            "image_count": len(generated_images),
            "style": style,
            "character_description": character_desc
        }
        
        # Update progress to 95% before final updates
        update_job_status_sync(job_id, "processing", "Finalizing results...", 95)
        
        # Small delay to ensure progress is visible
        time.sleep(0.5)
        
        # Update job as completed with result data
        update_job_status_sync(job_id, "completed", "AI image generation completed!", 100, str(output_dir), result_data)
        
        return {
            "status": "success",
            "job_id": job_id,
            "results": results,
            "result_data": result_data
        }
        
    except Exception as e:
        # Handle errors
        import traceback
        error_traceback = traceback.format_exc()
        
        update_job_status_sync(job_id, "failed", f"Error: {str(e)}", 0)
        raise

def run_video_creation_task_sync(job_id: str, job_data: Dict[str, Any]):
    """Synchronous task to create video from previously generated images"""
    try:
        # Update job status to processing
        update_job_status_sync(
            job_id=job_id,
            status="processing",
            message="Initializing video creation...",
            progress=5
        )
        
        # Extract parameters
        params = job_data['params']
        original_result = params['original_result']
        create_clips = params.get('create_clips', True)
        create_full_video = params.get('create_full_video', True)
        
        # Get paths from original job
        output_dir = Path(original_result['output_dir'])
        script_text = original_result.get('script_text', '')
        
        # Load metadata
        metadata_path = output_dir / 'generation_metadata.json'
        if not metadata_path.exists():
            raise Exception("Generation metadata not found")
        
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        generated_images = metadata['images']
        voice_path = metadata['voice_path']
        
        # Initialize processors
        update_job_status_sync(job_id, "processing", "Preparing video processors...", 10)
        video_proc = VideoProcessor()
        
        results = {}
        
        # Create video clips if requested
        if create_clips:
            update_job_status_sync(job_id, "processing", "Creating video clips from images...", 30)
            clips_dir = output_dir / 'clips'
            clips_dir.mkdir(exist_ok=True)
            
            # Try fast method first
            fast_video = video_proc.images_to_clips_fast(generated_images, str(clips_dir))
            
            if fast_video:
                # Fast method succeeded, we have a single video file
                update_job_status_sync(job_id, "processing", "Created all clips in single pass", 70)
                results['clips'] = str(clips_dir)
            else:
                # Use parallel processing for individual clips
                update_job_status_sync(job_id, "processing", "Creating clips using parallel processing...", 40)
                clip_paths = video_proc.images_to_clips(generated_images, str(clips_dir))
                
                if clip_paths:
                    update_job_status_sync(job_id, "processing", f"Created {len(clip_paths)} clips", 70)
                    results['clips'] = str(clips_dir)
                else:
                    logger.warning("No clips were created")
        
        # Create full video if requested
        if create_full_video:
            update_job_status_sync(job_id, "processing", "Creating full video with voiceover...", 75)
            final_video_path = output_dir / 'final_video_with_audio.mp4'
            video_proc.create_full_video(
                generated_images, 
                voice_path, 
                str(final_video_path)
            )
            results['video'] = str(final_video_path)
            
            # Update progress
            update_job_status_sync(job_id, "processing", "Finalizing video...", 90)
        
        # Prepare result data with video URLs
        result_data = {
            "clips_created": create_clips,
            "full_video_created": create_full_video,
            "output_dir": str(output_dir),
            "results": results,
            "videos": {}
        }
        
        # Add video paths for preview
        if 'clips' in results:
            result_data['clips_path'] = results['clips']
            try:
                # Convert to relative path for serving
                clips_relative = Path(results['clips']).relative_to(Path(settings.RESULTS_DIR))
                result_data['videos']['clips'] = f"results/{clips_relative.as_posix()}"
            except:
                # Fallback to full path if relative path fails
                result_data['videos']['clips'] = results['clips']
            
        if 'video' in results:
            result_data['video_path'] = results['video']
            try:
                # Convert to relative path for serving
                video_relative = Path(results['video']).relative_to(Path(settings.RESULTS_DIR))
                result_data['videos']['full_video'] = f"results/{video_relative.as_posix()}"
            except:
                # Fallback to full path if relative path fails
                result_data['videos']['full_video'] = results['video']
        
        # Update job as completed
        update_job_status_sync(job_id, "completed", "Video creation completed!", 100, results.get('video', str(output_dir)), result_data)
        
        return {
            "status": "success",
            "job_id": job_id,
            "results": results,
            "result_data": result_data
        }
        
    except Exception as e:
        # Handle errors
        import traceback
        error_traceback = traceback.format_exc()
        
        update_job_status_sync(job_id, "failed", f"Error: {str(e)}", 0)
        raise

def run_broll_task_sync(job_id: str, job_data: Dict[str, Any]):
    """Synchronous B-roll organization task"""
    try:
        # Update job status to processing
        update_job_status_sync(
            job_id=job_id,
            status="processing",
            message="Initializing B-roll organization...",
            progress=5
        )
        
        # Extract parameters
        params = job_data['params']
        intro_clip_ids = params.get('intro_clip_ids', [])
        broll_clip_ids = params.get('broll_clip_ids', [])
        voiceover_id = params.get('voiceover_id')
        sync_to_voiceover = params.get('sync_to_voiceover', True)
        overlay_audio = params.get('overlay_audio', True)
        
        # Get file paths
        update_job_status_sync(job_id, "processing", "Loading video files...", 10)
        
        all_clips = []
        
        # Get intro clips
        for clip_id in intro_clip_ids:
            clip_file = get_file_by_id_sync(clip_id)
            if clip_file:
                all_clips.append(clip_file['file_path'])
        
        # Get B-roll clips
        for clip_id in broll_clip_ids:
            clip_file = get_file_by_id_sync(clip_id)
            if clip_file:
                all_clips.append(clip_file['file_path'])
        
        if not all_clips:
            raise Exception("No valid video clips found")
        
        # Get voiceover if provided
        voiceover_path = None
        if voiceover_id:
            voiceover_file = get_file_by_id_sync(voiceover_id)
            if voiceover_file:
                voiceover_path = voiceover_file['file_path']
        
        # Create output directory
        output_dir = Path(settings.OUTPUT_DIR) / job_id
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize video processor
        update_job_status_sync(job_id, "processing", "Processing video clips...", 20)
        video_proc = VideoProcessor()
        
        # Concatenate clips
        concatenated_path = output_dir / "concatenated.mp4"
        update_job_status_sync(job_id, "processing", "Concatenating video clips...", 40)
        video_proc.concatenate_clips(all_clips, str(concatenated_path))
        
        # Add voiceover if provided
        final_video_path = output_dir / "final_video.mp4"
        if voiceover_path and overlay_audio:
            update_job_status_sync(job_id, "processing", "Adding voiceover audio...", 60)
            video_proc.add_audio_to_video(str(concatenated_path), voiceover_path, str(final_video_path))
        else:
            # Just copy the concatenated video as final
            import shutil
            shutil.copy2(str(concatenated_path), str(final_video_path))
        
        # Create results directory and copy final video
        results_dir = Path("results")
        results_dir.mkdir(exist_ok=True)
        
        # Create a symlink or copy to results directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_filename = f"broll_organized_{timestamp}.mp4"
        result_path = results_dir / result_filename
        
        import shutil
        shutil.copy2(str(final_video_path), str(result_path))
        
        # Also create a "latest" version
        latest_path = results_dir / "latest_broll_organized.mp4"
        shutil.copy2(str(final_video_path), str(latest_path))
        
        update_job_status_sync(
            job_id, 
            "completed", 
            "B-roll organization completed successfully!", 
            100, 
            str(result_path)
        )
        
        return {
            "status": "success",
            "job_id": job_id,
            "result_path": str(result_path)
        }
        
    except Exception as e:
        # Handle errors
        import traceback
        error_traceback = traceback.format_exc()
        
        update_job_status_sync(job_id, "failed", f"Error: {str(e)}", 0)
        raise

@celery_app.task(bind=True, base=CallbackTask, name='tasks.generate_ai_images')
def generate_ai_images_task(self, job_id: str, job_data: Dict[str, Any]):
    """Background task for AI image generation"""
    self.job_id = job_id
    self.user_id = job_data['user_id']
    
    try:
        # Update job status to processing
        try:
            update_job_status_sync(
                job_id=job_id,
                status="processing",
                message="Initializing AI image generation...",
                progress=5
            )
        except Exception as e:
            print(f"Failed to update initial job status: {e}")
        
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
        
        # Read script using DocumentProcessor
        self.update_progress(15, "Reading script file...")
        doc_processor = DocumentProcessor()
        try:
            script_text = doc_processor.extract_text(script_path)
            if not script_text or script_text.strip() == "":
                script_text = params.get('script_text', 'Generate images based on the uploaded content.')
        except Exception as e:
            logger.error(f"Failed to extract text from script: {e}")
            script_text = params.get('script_text', 'Generate images based on the uploaded content.')
        
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
            
            # More granular progress calculation
            progress = 20 + int(((i + 0.5) / image_count) * 60)  # 20-80% for image generation
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
        
        # Store results - only images for now
        results = {'images': str(output_dir)}
        
        # Prepare result data with image paths relative to output directory
        image_filenames = []
        for img in generated_images:
            # Get just the filename from the full path
            filename = Path(img['path']).name
            image_filenames.append(f"{job_id}/{filename}")
        
        result_data = {
            "images": image_filenames,
            "script_text": script_text,
            "output_dir": str(output_dir),
            "image_count": len(generated_images),
            "style": style,
            "character_description": character_desc,
            "metadata_path": str(metadata_path)
        }
        
        if 'clips' in results:
            result_data['clips'] = results['clips']
        if 'video' in results:
            result_data['video'] = results['video']
        
        # Update progress to 95% before final updates
        self.update_progress(95, "Finalizing results...")
        
        # Update job status to completed
        try:
            update_job_status_sync(
                job_id=job_id,
                status="completed",
                message="AI image generation completed successfully",
                progress=100,
                result_path=str(output_dir),
                result=result_data
            )
        except Exception as e:
            print(f"Failed to update job completion status: {e}")
        
        # Final progress update to ensure it reaches 100%
        self.update_progress(100, "AI image generation completed!")
        
        # Small delay to ensure the update is sent
        time.sleep(0.5)
        
        return {
            "status": "success",
            "job_id": job_id,
            "results": results,
            "result_data": result_data
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
        # Update job status to processing
        try:
            update_job_status_sync(
                job_id=job_id,
                status="processing",
                message="Starting B-roll reorganization...",
                progress=5
            )
        except Exception as e:
            print(f"Failed to update initial job status: {e}")
        
        self.update_progress(5, "Starting B-roll reorganization...")
        
        # Extract parameters
        params = job_data['params']
        
        # Get file paths from database
        intro_paths = []
        for file_id in params['intro_clip_ids']:
            try:
                file_record = get_file_by_id_sync(file_id)
                if file_record and file_record.get('file_path'):
                    intro_paths.append(file_record['file_path'])
                else:
                    raise Exception(f"Intro file {file_id} not found")
            except Exception as e:
                raise Exception(f"Failed to get intro file {file_id}: {e}")
        
        broll_paths = []
        for file_id in params['broll_clip_ids']:
            try:
                file_record = get_file_by_id_sync(file_id)
                if file_record and file_record.get('file_path'):
                    broll_paths.append(file_record['file_path'])
                else:
                    raise Exception(f"B-roll file {file_id} not found")
            except Exception as e:
                raise Exception(f"Failed to get B-roll file {file_id}: {e}")
        
        voiceover_path = None
        if params['voiceover_id']:
            try:
                voice_file = get_file_by_id_sync(params['voiceover_id'])
                if voice_file and voice_file.get('file_path'):
                    voiceover_path = voice_file['file_path']
                else:
                    raise Exception(f"Voiceover file {params['voiceover_id']} not found")
            except Exception as e:
                raise Exception(f"Failed to get voiceover file {params['voiceover_id']}: {e}")
        
        # Create output directory in results folder
        results_dir = Path("results")
        results_dir.mkdir(parents=True, exist_ok=True)
        output_dir = results_dir / f"broll_job_{job_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize processors
        video_proc = VideoProcessor()
        audio_proc = AudioProcessor()
        
        # Get target duration if syncing with voiceover
        target_duration = None
        if params['sync_to_voiceover'] and voiceover_path:
            self.update_progress(10, "Analyzing voiceover duration...")
            try:
                target_duration = audio_proc.get_duration(voiceover_path)
                print(f"Voiceover duration: {target_duration} seconds")
            except Exception as e:
                print(f"Warning: Could not get voiceover duration: {e}")
                target_duration = None
        
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
        
        # Update job status to completed
        try:
            final_video_path = results.get('video_with_audio', results['video'])
            update_job_status_sync(
                job_id=job_id,
                status="completed",
                message="B-roll reorganization completed successfully",
                progress=100,
                result_path=str(final_video_path)
            )
            
            # Also create a symlink or copy to results folder for easy access
            final_filename = Path(final_video_path).name
            results_link = results_dir / f"latest_broll_{final_filename}"
            try:
                if results_link.exists():
                    results_link.unlink()
                results_link.symlink_to(Path(final_video_path).absolute())
            except Exception as link_error:
                print(f"Could not create symlink: {link_error}")
                # Fallback: copy the file
                try:
                    import shutil
                    shutil.copy2(final_video_path, results_link)
                except Exception as copy_error:
                    print(f"Could not copy file: {copy_error}")
                    
        except Exception as e:
            print(f"Failed to update job completion status: {e}")
        
        return {
            "status": "success",
            "job_id": job_id,
            "results": results
        }
        
    except Exception as e:
        # Handle errors
        import traceback
        error_traceback = traceback.format_exc()
        
        # Update job status to failed
        try:
            update_job_status_sync(
                job_id=job_id,
                status="failed",
                message=f"Job failed: {str(e)}",
                progress=0
            )
        except Exception as db_error:
            print(f"Failed to update job failure status: {db_error}")
        
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