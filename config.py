"""
Configuration settings for AI Video Tool web application
"""

import os
from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Application settings
    APP_NAME: str = "AI Video Tool"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 8080
    
    # Security
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Encryption key for API keys (32 bytes base64 encoded)
    ENCRYPTION_KEY: str = "your-32-byte-encryption-key-here!!"
    
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./ai_video_tool.db"
    # For production, use PostgreSQL:
    # DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost/ai_video_tool"
    
    # Redis (for Celery and caching)
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # File storage
    BASE_DIR: Path = Path(__file__).resolve().parent
    UPLOAD_DIR: str = "uploads"
    OUTPUT_DIR: str = "outputs"
    TEMP_DIR: str = "temp"
    
    # File limits
    MAX_UPLOAD_SIZE: int = 5 * 1024 * 1024 * 1024  # 5GB (for 60-minute videos)
    MAX_VOICEOVER_SIZE: int = 500 * 1024 * 1024  # 500MB specifically for voiceover files
    ALLOWED_SCRIPT_EXTENSIONS: List[str] = [".txt", ".docx"]
    ALLOWED_AUDIO_EXTENSIONS: List[str] = [".mp3", ".wav", ".m4a"]
    ALLOWED_VIDEO_EXTENSIONS: List[str] = [".mp4", ".avi", ".mov", ".mkv"]
    
    # Processing limits
    MAX_IMAGES_PER_JOB: int = 20
    MAX_VIDEO_DURATION: int = 3600  # 60 minutes in seconds
    MAX_VOICEOVER_DURATION: int = 3600  # 60 minutes in seconds for voiceover files
    FILE_RETENTION_DAYS: int = 7
    
    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://localhost:8080",
        "https://yourdomain.com"
    ]
    
    # Email settings (for notifications)
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "noreply@aivideotool.com"
    
    # OpenAI settings
    OPENAI_API_KEY: str = ""  # Set via environment or API
    
    # AWS S3 settings (optional, for cloud storage)
    USE_S3: bool = False
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_REGION: str = "us-east-1"
    S3_BUCKET: str = "ai-video-tool"
    
    # CDN settings (optional)
    CDN_URL: str = ""
    
    # Monitoring
    SENTRY_DSN: str = ""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )
    
    def get_upload_path(self, subdir: str = "") -> Path:
        """Get upload directory path"""
        path = Path(self.UPLOAD_DIR) / subdir
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    def get_output_path(self, job_id: str) -> Path:
        """Get output directory path for a job"""
        path = Path(self.OUTPUT_DIR) / job_id
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    def get_temp_path(self) -> Path:
        """Get temporary directory path"""
        path = Path(self.TEMP_DIR)
        path.mkdir(parents=True, exist_ok=True)
        return path

# Create settings instance
settings = Settings()

# Create required directories
for directory in [settings.UPLOAD_DIR, settings.OUTPUT_DIR, settings.TEMP_DIR]:
    Path(directory).mkdir(parents=True, exist_ok=True)