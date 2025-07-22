import os
import cv2
import numpy as np
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
from PIL import Image, ImageDraw, ImageFont
import logging

logger = logging.getLogger(__name__)

class VideoProcessor:
    def __init__(self):
        self.output_dir = "processed"
        os.makedirs(self.output_dir, exist_ok=True)
    
    def process_video(self, input_path: str, title: str = "") -> str:
        """Process video with effects and title overlay"""
        try:
            output_path = os.path.join(self.output_dir, f"processed_{os.path.basename(input_path)}")
            
            # Load video
            video = VideoFileClip(input_path)
            
            # Add title overlay if provided
            if title:
                video = self._add_title_overlay(video, title)
            
            # Apply basic enhancements
            video = self._enhance_video(video)
            
            # Write processed video
            video.write_videofile(
                output_path,
                codec='libx264',
                audio_codec='aac',
                temp_audiofile='temp-audio.m4a',
                remove_temp=True
            )
            
            video.close()
            return output_path
            
        except Exception as e:
            logger.error(f"Error processing video: {str(e)}")
            raise
    
    def _add_title_overlay(self, video: VideoFileClip, title: str) -> VideoFileClip:
        """Add title overlay to video"""
        try:
            # Create title clip
            title_clip = TextClip(
                title,
                fontsize=50,
                color='white',
                font='Arial-Bold',
                stroke_color='black',
                stroke_width=2
            ).set_position(('center', 'top')).set_duration(5)
            
            # Composite video with title
            return CompositeVideoClip([video, title_clip])
            
        except Exception as e:
            logger.warning(f"Could not add title overlay: {str(e)}")
            return video
    
    def _enhance_video(self, video: VideoFileClip) -> VideoFileClip:
        """Apply basic video enhancements"""
        try:
            # Apply basic color correction
            def color_correct(image):
                # Convert to PIL Image
                pil_image = Image.fromarray(image)
                
                # Apply brightness and contrast adjustment
                enhancer = ImageEnhance.Brightness(pil_image)
                pil_image = enhancer.enhance(1.1)
                
                enhancer = ImageEnhance.Contrast(pil_image)
                pil_image = enhancer.enhance(1.2)
                
                return np.array(pil_image)
            
            return video.fl_image(color_correct)
            
        except Exception as e:
            logger.warning(f"Could not enhance video: {str(e)}")
            return video
    
    def extract_thumbnail(self, video_path: str, timestamp: float = 1.0) -> str:
        """Extract thumbnail from video"""
        try:
            video = VideoFileClip(video_path)
            thumbnail_path = os.path.join(self.output_dir, f"thumb_{os.path.basename(video_path)}.jpg")
            
            # Extract frame at timestamp
            frame = video.get_frame(timestamp)
            
            # Convert to PIL Image and save
            image = Image.fromarray(frame)
            image.save(thumbnail_path, quality=95)
            
            video.close()
            return thumbnail_path
            
        except Exception as e:
            logger.error(f"Error extracting thumbnail: {str(e)}")
            raise
    
    def get_video_info(self, video_path: str) -> dict:
        """Get video information"""
        try:
            video = VideoFileClip(video_path)
            info = {
                'duration': video.duration,
                'fps': video.fps,
                'size': video.size,
                'has_audio': video.audio is not None
            }
            video.close()
            return info
            
        except Exception as e:
            logger.error(f"Error getting video info: {str(e)}")
            raise