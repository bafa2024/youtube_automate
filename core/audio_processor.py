"""
Enhanced audio processor for B-Roll organization
"""
import os
import logging
import subprocess
import json
from typing import Optional, List
from pathlib import Path

logger = logging.getLogger(__name__)

class AudioProcessor:
    def __init__(self):
        self.output_dir = "processed"
        os.makedirs(self.output_dir, exist_ok=True)
    
    def get_duration(self, audio_path: str) -> float:
        """Get duration of an audio file using FFprobe"""
        logger.info(f"Getting duration for audio: {audio_path}")
        
        try:
            cmd = [
                './bin/ffprobe.exe',
                '-v', 'quiet',
                '-show_entries', 'format=duration',
                '-of', 'json',
                audio_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                duration = float(data['format']['duration'])
                logger.info(f"Audio duration: {duration}s")
                return duration
            else:
                logger.error(f"FFprobe error: {result.stderr}")
                return 0.0
                
        except Exception as e:
            logger.error(f"Error getting audio duration: {e}")
            return 0.0
    
    def extract_audio(self, video_path: str, output_path: str) -> str:
        """Extract audio from video file using FFmpeg"""
        logger.info(f"Extracting audio from {video_path}")
        
        try:
            # Create output directory
            output_dir = os.path.dirname(output_path)
            os.makedirs(output_dir, exist_ok=True)
            
            cmd = [
                './bin/ffmpeg.exe',
                '-i', video_path,
                '-vn',  # No video
                '-acodec', 'pcm_s16le',  # PCM 16-bit
                '-ar', '44100',  # 44.1kHz sample rate
                '-ac', '2',  # Stereo
                '-y',  # Overwrite output file
                output_path
            ]
            
            logger.info(f"Running FFmpeg command: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"FFmpeg error: {result.stderr}")
                raise Exception(f"FFmpeg audio extraction failed: {result.stderr}")
            
            logger.info(f"Successfully extracted audio: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error extracting audio: {e}")
            raise
    
    def normalize_audio(self, audio_path: str, output_path: str) -> str:
        """Normalize audio levels using FFmpeg"""
        logger.info(f"Normalizing audio: {audio_path}")
        
        try:
            # Create output directory
            output_dir = os.path.dirname(output_path)
            os.makedirs(output_dir, exist_ok=True)
            
            cmd = [
                './bin/ffmpeg.exe',
                '-i', audio_path,
                '-af', 'loudnorm=I=-16:TP=-1.5:LRA=11',  # EBU R128 loudness normalization
                '-ar', '44100',  # 44.1kHz sample rate
                '-ac', '2',  # Stereo
                '-y',  # Overwrite output file
                output_path
            ]
            
            logger.info(f"Running FFmpeg command: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"FFmpeg error: {result.stderr}")
                raise Exception(f"FFmpeg audio normalization failed: {result.stderr}")
            
            logger.info(f"Successfully normalized audio: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error normalizing audio: {e}")
            raise
    
    def concatenate_audio(self, audio_paths: List[str], output_path: str) -> str:
        """Concatenate multiple audio files using FFmpeg"""
        logger.info(f"Concatenating {len(audio_paths)} audio files")
        
        try:
            # Create output directory
            output_dir = os.path.dirname(output_path)
            os.makedirs(output_dir, exist_ok=True)
            
            # Create a file list for FFmpeg
            file_list_path = os.path.join(output_dir, "audio_list.txt")
            with open(file_list_path, 'w', encoding='utf-8') as f:
                for audio_path in audio_paths:
                    if os.path.exists(audio_path):
                        f.write(f"file '{audio_path}'\n")
                    else:
                        logger.warning(f"Audio file not found: {audio_path}")
            
            cmd = [
                './bin/ffmpeg.exe',
                '-f', 'concat',
                '-safe', '0',
                '-i', file_list_path,
                '-c', 'copy',  # Copy streams without re-encoding
                '-y',  # Overwrite output file
                output_path
            ]
            
            logger.info(f"Running FFmpeg command: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            # Clean up file list
            if os.path.exists(file_list_path):
                os.remove(file_list_path)
            
            if result.returncode != 0:
                logger.error(f"FFmpeg error: {result.stderr}")
                raise Exception(f"FFmpeg audio concatenation failed: {result.stderr}")
            
            logger.info(f"Successfully concatenated audio: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error concatenating audio: {e}")
            raise
    
    def add_silence(self, audio_path: str, duration: float, output_path: str) -> str:
        """Add silence to the end of an audio file using FFmpeg"""
        logger.info(f"Adding {duration}s silence to {audio_path}")
        
        try:
            # Create output directory
            output_dir = os.path.dirname(output_path)
            os.makedirs(output_dir, exist_ok=True)
            
            cmd = [
                './bin/ffmpeg.exe',
                '-i', audio_path,
                '-f', 'lavfi',
                '-i', f'anullsrc=channel_layout=stereo:sample_rate=44100',
                '-filter_complex', f'[0:a][1:a]concat=n=2:v=0:a=1[out]',
                '-map', '[out]',
                '-ar', '44100',
                '-ac', '2',
                '-y',
                output_path
            ]
            
            logger.info(f"Running FFmpeg command: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"FFmpeg error: {result.stderr}")
                raise Exception(f"FFmpeg silence addition failed: {result.stderr}")
            
            logger.info(f"Successfully added silence: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error adding silence: {e}")
            raise
    
    def fade_in_out(self, audio_path: str, fade_duration: float, output_path: str) -> str:
        """Add fade in/out effects to audio using FFmpeg"""
        logger.info(f"Adding fade in/out to {audio_path}")
        
        try:
            # Create output directory
            output_dir = os.path.dirname(output_path)
            os.makedirs(output_dir, exist_ok=True)
            
            # Get audio duration
            duration = self.get_duration(audio_path)
            
            cmd = [
                './bin/ffmpeg.exe',
                '-i', audio_path,
                '-af', f'afade=t=in:st=0:d={fade_duration},afade=t=out:st={duration-fade_duration}:d={fade_duration}',
                '-ar', '44100',
                '-ac', '2',
                '-y',
                output_path
            ]
            
            logger.info(f"Running FFmpeg command: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"FFmpeg error: {result.stderr}")
                raise Exception(f"FFmpeg fade effects failed: {result.stderr}")
            
            logger.info(f"Successfully added fade effects: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error adding fade effects: {e}")
            raise
    
    def generate_timestamps(self, duration: float, count: int) -> List[float]:
        """Generate evenly spaced timestamps for images based on audio duration"""
        logger.info(f"Generating {count} timestamps for {duration}s duration")
        
        if count <= 0:
            return []
        
        if count == 1:
            return [duration / 2]  # Single image at middle
        
        # Generate evenly spaced timestamps
        interval = duration / count
        timestamps = []
        
        for i in range(count):
            timestamp = (i + 0.5) * interval  # Center of each segment
            timestamps.append(round(timestamp, 2))
        
        logger.info(f"Generated timestamps: {timestamps}")
        return timestamps
    
    def convert_audio_format(self, audio_path: str, output_path: str, format: str = 'mp3') -> str:
        """Convert audio to different format using FFmpeg"""
        logger.info(f"Converting audio format: {audio_path} to {format}")
        
        try:
            # Create output directory
            output_dir = os.path.dirname(output_path)
            os.makedirs(output_dir, exist_ok=True)
            
            # Set codec based on format
            if format.lower() == 'mp3':
                codec = 'libmp3lame'
                bitrate = '192k'
            elif format.lower() == 'aac':
                codec = 'aac'
                bitrate = '192k'
            elif format.lower() == 'wav':
                codec = 'pcm_s16le'
                bitrate = None
            else:
                codec = 'libmp3lame'
                bitrate = '192k'
            
            cmd = [
                './bin/ffmpeg.exe',
                '-i', audio_path,
                '-c:a', codec
            ]
            
            if bitrate:
                cmd.extend(['-b:a', bitrate])
            
            cmd.extend([
                '-ar', '44100',
                '-ac', '2',
                '-y',
                output_path
            ])
            
            logger.info(f"Running FFmpeg command: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"FFmpeg error: {result.stderr}")
                raise Exception(f"FFmpeg format conversion failed: {result.stderr}")
            
            logger.info(f"Successfully converted audio format: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error converting audio format: {e}")
            raise 