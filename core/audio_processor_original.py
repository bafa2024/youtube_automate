import os
import whisper
import speech_recognition as sr
from pydub import AudioSegment
import logging

logger = logging.getLogger(__name__)

class AudioProcessor:
    def __init__(self):
        self.output_dir = "processed"
        os.makedirs(self.output_dir, exist_ok=True)
        self.recognizer = sr.Recognizer()
        
        # Initialize Whisper model
        try:
            self.whisper_model = whisper.load_model("base")
        except Exception as e:
            logger.warning(f"Could not load Whisper model: {str(e)}")
            self.whisper_model = None
    
    def extract_audio(self, video_path: str) -> str:
        """Extract audio from video file"""
        try:
            # Create output path
            base_name = os.path.splitext(os.path.basename(video_path))[0]
            audio_path = os.path.join(self.output_dir, f"{base_name}_audio.wav")
            
            # Extract audio using pydub
            video = AudioSegment.from_file(video_path)
            video.export(audio_path, format="wav")
            
            logger.info(f"Audio extracted to: {audio_path}")
            return audio_path
            
        except Exception as e:
            logger.error(f"Error extracting audio: {str(e)}")
            raise
    
    def transcribe_audio(self, audio_path: str) -> str:
        """Transcribe audio to text using Whisper or speech_recognition"""
        try:
            # Try Whisper first (more accurate)
            if self.whisper_model:
                return self._transcribe_with_whisper(audio_path)
            else:
                return self._transcribe_with_sr(audio_path)
                
        except Exception as e:
            logger.error(f"Error transcribing audio: {str(e)}")
            raise
    
    def _transcribe_with_whisper(self, audio_path: str) -> str:
        """Transcribe using OpenAI Whisper"""
        try:
            result = self.whisper_model.transcribe(audio_path)
            return result["text"]
            
        except Exception as e:
            logger.error(f"Whisper transcription failed: {str(e)}")
            raise
    
    def _transcribe_with_sr(self, audio_path: str) -> str:
        """Transcribe using speech_recognition library"""
        try:
            # Load audio file
            with sr.AudioFile(audio_path) as source:
                audio = self.recognizer.record(source)
            
            # Recognize speech using Google Speech Recognition
            text = self.recognizer.recognize_google(audio)
            return text
            
        except sr.UnknownValueError:
            logger.warning("Speech recognition could not understand audio")
            return ""
        except sr.RequestError as e:
            logger.error(f"Could not request results from speech recognition service: {str(e)}")
            raise
    
    def enhance_audio(self, audio_path: str) -> str:
        """Enhance audio quality"""
        try:
            # Load audio
            audio = AudioSegment.from_file(audio_path)
            
            # Apply noise reduction and normalization
            # Normalize audio
            normalized_audio = audio.normalize()
            
            # Apply high-pass filter to reduce low-frequency noise
            high_pass_filter = normalized_audio.high_pass_filter(300)
            
            # Save enhanced audio
            enhanced_path = os.path.join(
                self.output_dir, 
                f"enhanced_{os.path.basename(audio_path)}"
            )
            high_pass_filter.export(enhanced_path, format="wav")
            
            return enhanced_path
            
        except Exception as e:
            logger.error(f"Error enhancing audio: {str(e)}")
            raise
    
    def split_audio_by_silence(self, audio_path: str, silence_thresh: int = -40) -> list:
        """Split audio into segments based on silence"""
        try:
            audio = AudioSegment.from_file(audio_path)
            
            # Split on silence
            chunks = silence.split_on_silence(
                audio,
                min_silence_len=1000,  # 1 second
                silence_thresh=silence_thresh,
                keep_silence=500  # Keep 500ms of silence
            )
            
            # Save chunks
            chunk_paths = []
            for i, chunk in enumerate(chunks):
                chunk_path = os.path.join(
                    self.output_dir, 
                    f"chunk_{i}_{os.path.basename(audio_path)}"
                )
                chunk.export(chunk_path, format="wav")
                chunk_paths.append(chunk_path)
            
            return chunk_paths
            
        except Exception as e:
            logger.error(f"Error splitting audio: {str(e)}")
            raise
    
    def get_audio_info(self, audio_path: str) -> dict:
        """Get audio file information"""
        try:
            audio = AudioSegment.from_file(audio_path)
            
            return {
                'duration': len(audio) / 1000.0,  # Convert to seconds
                'channels': audio.channels,
                'sample_rate': audio.frame_rate,
                'bit_depth': audio.sample_width * 8,
                'format': audio_path.split('.')[-1]
            }
            
        except Exception as e:
            logger.error(f"Error getting audio info: {str(e)}")
            raise