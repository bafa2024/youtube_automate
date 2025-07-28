"""
Enhanced video processor for B-Roll organization
"""
import os
import logging
import random
import subprocess
import json
from typing import List, Optional, Callable, Dict
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import multiprocessing
from .ffmpeg_utils import get_ffmpeg_path, get_ffprobe_path

logger = logging.getLogger(__name__)

class VideoProcessor:
    def __init__(self):
        self.output_dir = "processed"
        os.makedirs(self.output_dir, exist_ok=True)
    
    def process_video(self, input_path: str, title: str = "") -> str:
        """Process video with effects and title overlay"""
        logger.info(f"Processing video: {input_path}")
        # For now, just return the input path
        # In a full implementation, this would add effects and overlays
        return input_path
    
    def concatenate_clips(self, clip_paths: List[str], output_path: str, 
                         target_duration: Optional[float] = None,
                         progress_callback: Optional[Callable] = None) -> str:
        """Concatenate multiple video clips using FFmpeg"""
        logger.info(f"Concatenating {len(clip_paths)} clips to {output_path}")
        
        if not clip_paths:
            raise ValueError("No clips provided")
        
        # Create output directory
        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # Create a file list for FFmpeg
            file_list_path = output_dir / "clips_list.txt"
            with open(file_list_path, 'w', encoding='utf-8') as f:
                for clip_path in clip_paths:
                    # Convert to absolute path to avoid relative path issues
                    abs_clip_path = os.path.abspath(clip_path)
                    if os.path.exists(abs_clip_path):
                        f.write(f"file '{abs_clip_path}'\n")
                    else:
                        logger.warning(f"Clip not found: {abs_clip_path}")
            
            if progress_callback:
                progress_callback(25)
            
            # Build FFmpeg command with optimizations
            cmd = [
                get_ffmpeg_path(),
                '-f', 'concat',
                '-safe', '0',
                '-i', str(file_list_path),
                '-c:v', 'copy',  # Copy video stream without re-encoding
                '-c:a', 'copy',  # Copy audio stream if present
                '-movflags', '+faststart',  # Optimize for streaming
                '-y',  # Overwrite output file
                str(output_path)
            ]
            
            # If target duration is specified, we'll need to process differently
            if target_duration:
                # First concatenate, then trim to target duration
                temp_output = output_dir / "temp_concatenated.mp4"
                temp_cmd = cmd.copy()
                temp_cmd[6] = str(temp_output)  # Change output to temp file
                
                # Run concatenation
                logger.info(f"Running FFmpeg command: {' '.join(temp_cmd)}")
                result = subprocess.run(temp_cmd, capture_output=True, text=True)
                
                if result.returncode != 0:
                    logger.error(f"FFmpeg error: {result.stderr}")
                    raise Exception(f"FFmpeg concatenation failed: {result.stderr}")
                
                if progress_callback:
                    progress_callback(50)
                
                # Now trim to target duration
                trim_cmd = [
                    get_ffmpeg_path(),
                    '-i', str(temp_output),
                    '-t', str(target_duration),
                    '-c', 'copy',
                    '-y',
                    str(output_path)
                ]
                
                logger.info(f"Running FFmpeg trim command: {' '.join(trim_cmd)}")
                result = subprocess.run(trim_cmd, capture_output=True, text=True)
                
                if result.returncode != 0:
                    logger.error(f"FFmpeg trim error: {result.stderr}")
                    raise Exception(f"FFmpeg trim failed: {result.stderr}")
                
                # Clean up temp file
                if temp_output.exists():
                    temp_output.unlink()
            else:
                # Just concatenate without duration constraint
                logger.info(f"Running FFmpeg command: {' '.join(cmd)}")
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode != 0:
                    logger.error(f"FFmpeg error: {result.stderr}")
                    raise Exception(f"FFmpeg concatenation failed: {result.stderr}")
            
            # Clean up file list
            if file_list_path.exists():
                file_list_path.unlink()
            
            if progress_callback:
                progress_callback(100)
            
            logger.info(f"Successfully created concatenated video: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error concatenating clips: {e}")
            raise
    
    def image_to_video(self, image_path: str, output_path: str, duration: float = 5.0) -> str:
        """Convert a single image to a video clip with specified duration"""
        logger.info(f"Converting image {image_path} to video with duration {duration}s")
        
        try:
            # Create output directory
            output_dir = Path(output_path).parent
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Build FFmpeg command with optimizations
            cmd = [
                get_ffmpeg_path(),
                '-loop', '1',  # Loop the image
                '-i', image_path,
                '-c:v', 'libx264',
                '-preset', 'ultrafast',  # Fastest encoding
                '-crf', '23',  # Good quality
                '-t', str(duration),  # Duration in seconds
                '-pix_fmt', 'yuv420p',
                '-vf', 'scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2',
                '-movflags', '+faststart',  # Optimize for streaming
                '-y',
                output_path
            ]
            
            logger.info(f"Running FFmpeg command: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"FFmpeg error: {result.stderr}")
                raise Exception(f"FFmpeg image to video failed: {result.stderr}")
            
            logger.info(f"Successfully created video from image: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error converting image to video: {e}")
            raise
    
    def add_audio_to_video(self, video_path: str, audio_path: str, output_path: str) -> str:
        """Add audio track to video using FFmpeg"""
        logger.info(f"Adding audio {audio_path} to video {video_path}")
        
        try:
            # Create output directory
            output_dir = Path(output_path).parent
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Build FFmpeg command to overlay audio
            cmd = [
                get_ffmpeg_path(),
                '-i', video_path,
                '-i', audio_path,
                '-c:v', 'copy',  # Copy video stream without re-encoding
                '-c:a', 'aac',   # Use AAC codec for audio
                '-shortest',     # End when shortest input ends
                '-y',            # Overwrite output file
                output_path
            ]
            
            logger.info(f"Running FFmpeg command: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"FFmpeg error: {result.stderr}")
                raise Exception(f"FFmpeg audio overlay failed: {result.stderr}")
            
            logger.info(f"Successfully added audio to video: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error adding audio to video: {e}")
            raise
    
    def _create_single_clip(self, args: tuple) -> Optional[str]:
        """Helper function to create a single clip (for parallel processing)"""
        i, image_info, output_dir = args
        image_path = image_info.get('path', '')
        
        if not image_path or not os.path.exists(image_path):
            logger.warning(f"Image not found: {image_path}")
            return None
        
        clip_path = os.path.join(output_dir, f"clip_{i+1:03d}.mp4")
        duration = image_info.get('duration', 3.0)
        
        # Use faster encoding settings
        cmd = [
            get_ffmpeg_path(),
            '-loop', '1',
            '-i', image_path,
            '-c:v', 'libx264',
            '-preset', 'ultrafast',  # Fastest encoding preset
            '-crf', '23',  # Constant rate factor for good quality
            '-t', str(duration),
            '-pix_fmt', 'yuv420p',
            '-movflags', '+faststart',  # Optimize for streaming
            '-y',
            clip_path
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                return clip_path
            else:
                logger.error(f"FFmpeg error creating clip {i+1}: {result.stderr}")
                return None
        except Exception as e:
            logger.error(f"Error creating clip {i+1}: {e}")
            return None
    
    def images_to_clips_fast(self, image_data: List[dict], output_dir: str) -> Optional[str]:
        """Fast method to create a single video from all images if they have the same duration"""
        if not image_data:
            return None
            
        # Check if all images have the same duration
        durations = [img.get('duration', 3.0) for img in image_data]
        if len(set(durations)) != 1:
            # Different durations, can't use fast method
            return None
            
        duration = durations[0]
        logger.info(f"All images have same duration ({duration}s), using fast concatenation")
        
        # Create a file list for FFmpeg
        output_path = os.path.join(output_dir, "all_clips.mp4")
        file_list_path = os.path.join(output_dir, "images_list.txt")
        
        with open(file_list_path, 'w') as f:
            for img in image_data:
                if img.get('path') and os.path.exists(img['path']):
                    f.write(f"file '{os.path.abspath(img['path'])}'\n")
                    f.write(f"duration {duration}\n")
            # Add the last image again (FFmpeg requirement)
            if image_data and image_data[-1].get('path'):
                f.write(f"file '{os.path.abspath(image_data[-1]['path'])}'\n")
        
        # Single FFmpeg command to create video from all images
        cmd = [
            get_ffmpeg_path(),
            '-f', 'concat',
            '-safe', '0',
            '-i', file_list_path,
            '-vsync', 'vfr',
            '-pix_fmt', 'yuv420p',
            '-c:v', 'libx264',
            '-preset', 'ultrafast',
            '-crf', '23',
            '-movflags', '+faststart',
            '-y',
            output_path
        ]
        
        try:
            logger.info("Creating video from all images in single pass")
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                # Clean up temp file
                os.remove(file_list_path)
                return output_path
            else:
                logger.error(f"FFmpeg error: {result.stderr}")
                return None
        except Exception as e:
            logger.error(f"Error in fast image concatenation: {e}")
            return None
    
    def images_to_clips(self, image_data: List[dict], output_dir: str) -> List[str]:
        """Convert images to video clips using FFmpeg with parallel processing"""
        logger.info(f"Converting {len(image_data)} images to clips using parallel processing")
        
        # Prepare arguments for parallel processing
        args_list = [(i, image_info, output_dir) for i, image_info in enumerate(image_data)]
        
        # Use ThreadPoolExecutor for parallel processing
        # Limit workers to CPU count for optimal performance
        max_workers = min(multiprocessing.cpu_count(), len(image_data))
        logger.info(f"Using {max_workers} parallel workers")
        
        clip_paths = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_index = {
                executor.submit(self._create_single_clip, args): args[0] 
                for args in args_list
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_index):
                index = future_to_index[future]
                try:
                    clip_path = future.result()
                    if clip_path:
                        clip_paths.append((index, clip_path))
                except Exception as e:
                    logger.error(f"Exception creating clip {index+1}: {e}")
        
        # Sort clips by index to maintain order
        clip_paths.sort(key=lambda x: x[0])
        sorted_paths = [path for _, path in clip_paths]
        
        logger.info(f"Successfully created {len(sorted_paths)} clips")
        return sorted_paths
    
    def create_full_video(self, image_data: List[dict], audio_path: str, output_path: str) -> str:
        """Create full video from images and audio with optimizations"""
        logger.info(f"Creating full video with {len(image_data)} images")
        
        try:
            # Create output directory
            output_dir = Path(output_path).parent
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Try fast method first if all images have same duration
            fast_video = self.images_to_clips_fast(image_data, str(output_dir))
            
            if fast_video:
                # Fast method succeeded, just add audio
                logger.info("Using fast video creation method")
                self.add_audio_to_video(fast_video, audio_path, output_path)
                
                # Clean up temp file
                if os.path.exists(fast_video):
                    os.remove(fast_video)
            else:
                # Fall back to parallel clip creation
                logger.info("Using parallel clip creation method")
                clips = self.images_to_clips(image_data, str(output_dir))
                
                if not clips:
                    raise Exception("No valid clips created from images")
                
                # Then concatenate clips
                temp_video = output_dir / "temp_video.mp4"
                self.concatenate_clips(clips, str(temp_video))
                
                # Finally add audio
                self.add_audio_to_video(str(temp_video), audio_path, output_path)
                
                # Clean up temp files
                for clip in clips:
                    if os.path.exists(clip):
                        os.remove(clip)
                if temp_video.exists():
                    temp_video.unlink()
            
            logger.info(f"Successfully created full video: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error creating full video: {e}")
            raise
    
    def get_video_duration(self, video_path: str) -> float:
        """Get duration of a video file using FFmpeg"""
        logger.info(f"Getting duration for video: {video_path}")
        
        try:
            cmd = [
                get_ffprobe_path(),
                '-v', 'quiet',
                '-show_entries', 'format=duration',
                '-of', 'json',
                video_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                duration = float(data['format']['duration'])
                logger.info(f"Video duration: {duration}s")
                return duration
            else:
                logger.error(f"FFprobe error: {result.stderr}")
                return 0.0
                
        except Exception as e:
            logger.error(f"Error getting video duration: {e}")
            return 0.0
    
    def extract_thumbnail(self, video_path: str, timestamp: float = 1.0) -> str:
        """Extract thumbnail from video using FFmpeg"""
        logger.info(f"Extracting thumbnail from {video_path} at {timestamp}s")
        
        try:
            # Create output directory
            output_dir = Path(video_path).parent
            thumbnail_path = output_dir / f"{Path(video_path).stem}_thumb.jpg"
            
            cmd = [
                get_ffmpeg_path(),
                '-i', video_path,
                '-ss', str(timestamp),
                '-vframes', '1',
                '-q:v', '2',
                '-y',
                str(thumbnail_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"Thumbnail extracted: {thumbnail_path}")
                return str(thumbnail_path)
            else:
                logger.error(f"FFmpeg error extracting thumbnail: {result.stderr}")
                return ""
                
        except Exception as e:
            logger.error(f"Error extracting thumbnail: {e}")
            return "" 