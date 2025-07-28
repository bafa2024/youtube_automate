"""
FastAPI Web Application for AI Video Tool
Cloud-based version with web interface
"""

import os
import asyncio
import uuid
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any, Union
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Request, Form, Depends, status
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import aiofiles
# Removed: from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
# Removed: from sqlalchemy.orm import sessionmaker
# Removed: engine = create_async_engine(settings.DATABASE_URL, echo=True)
# Removed: async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
# Removed: async with engine.begin() as conn: ...
# Removed: async def get_db_session(): ...
# Remove any usage of get_db_session() in endpoints

# Import our core modules
from core.video_processor import VideoProcessor
from core.audio_processor import AudioProcessor
from core.api_manager import APIKeyManager
from core.openai_generator import OpenAIImageGenerator

# Import new modules for web app
from db_utils import init_db, create_file, get_file_by_id, create_job, get_job_by_id, update_job_status
from db_utils import get_user_by_id
import tasks
from celery_app import celery_app

# WebSocket for real-time job updates
from fastapi import WebSocket, WebSocketDisconnect
from typing import Set

# Setup logging
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from config import Settings
settings = Settings()

# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up AI Video Tool API...")
    
    # Create necessary directories
    for dir_path in [settings.UPLOAD_DIR, settings.OUTPUT_DIR, settings.TEMP_DIR]:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    # Initialize database
    await init_db()
    
    # Check FFmpeg installation
    from core.ffmpeg_utils import check_ffmpeg_installed, check_ffprobe_installed
    if check_ffmpeg_installed():
        logger.info("✓ FFmpeg is installed and accessible")
    else:
        logger.warning("⚠ FFmpeg not found! Video processing features may not work")
    
    if check_ffprobe_installed():
        logger.info("✓ FFprobe is installed and accessible")
    else:
        logger.warning("⚠ FFprobe not found! Audio duration detection may not work")
    
    # Load API key if stored
    api_key_file = Path("api_key.txt")
    if api_key_file.exists():
        try:
            stored_key = api_key_file.read_text().strip()
            if stored_key:
                os.environ['OPENAI_API_KEY'] = stored_key
                logger.info("API key loaded from file")
        except Exception as e:
            logger.error(f"Error loading API key: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down AI Video Tool API...")
    # Cleanup temp files older than 24 hours
    cleanup_old_files()

# Create FastAPI app
app = FastAPI(
    title="AI Video Tool API",
    description="Cloud-based AI Video Generation and B-Roll Organization",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Set maximum request body size to 5GB
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import starlette.status as starlette_status

class MaxBodySizeMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_body_size: int = 5 * 1024 * 1024 * 1024):  # 5GB default
        super().__init__(app)
        self.max_body_size = max_body_size

    async def dispatch(self, request: Request, call_next):
        if request.method in ["POST", "PUT", "PATCH"]:
            content_length = request.headers.get("content-length")
            if content_length:
                content_length = int(content_length)
                if content_length > self.max_body_size:
                    return JSONResponse(
                        status_code=starlette_status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        content={"detail": f"Request body too large. Maximum size is {self.max_body_size // (1024*1024)} MB"}
                    )
        response = await call_next(request)
        return response

# Add the middleware
app.add_middleware(MaxBodySizeMiddleware, max_body_size=5 * 1024 * 1024 * 1024)

# Database setup
# Removed: engine = create_async_engine(settings.DATABASE_URL, echo=True)
# Removed: async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Include routers
from auth import auth_router
app.include_router(auth_router)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/outputs", StaticFiles(directory=settings.OUTPUT_DIR), name="outputs")

# Pydantic models
class AIImageGenerationRequest(BaseModel):
    script_text: str = Field(..., description="Script text for image generation")
    image_count: int = Field(5, ge=1, le=20, description="Number of images to generate")
    style: str = Field("Photorealistic", description="Image style")
    character_description: str = Field(..., description="Character description")
    voice_duration: float = Field(..., gt=0, description="Duration of voiceover in seconds")
    export_options: Dict[str, bool] = Field(
        default={"images": True, "clips": True, "full_video": False}
    )

class BRollOrganizationRequest(BaseModel):
    intro_clip_ids: List[str] = Field(default=[], description="List of intro clip UUIDs")
    broll_clip_ids: List[str] = Field(..., description="List of B-roll clip UUIDs")
    voiceover_id: Optional[str] = Field(None, description="Voiceover UUID")
    sync_to_voiceover: bool = Field(True, description="Sync video to voiceover duration")
    overlay_audio: bool = Field(True, description="Overlay voiceover on final video")

class CreateVideoRequest(BaseModel):
    original_job_id: str = Field(..., description="Job ID of the completed AI image generation")
    create_clips: bool = Field(True, description="Create individual video clips from images")
    create_full_video: bool = Field(True, description="Create full video with voiceover")

class JobResponse(BaseModel):
    job_id: str
    status: str
    message: str
    created_at: datetime
    progress: int = 0
    result_url: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    job_type: Optional[str] = None

class FileUploadResponse(BaseModel):
    file_id: str
    filename: str
    file_type: str
    size: int
    upload_time: datetime

# Utility functions
def cleanup_old_files():
    """Clean up temporary files older than 24 hours"""
    import time
    current_time = time.time()
    
    for directory in [settings.TEMP_DIR, settings.UPLOAD_DIR]:
        for file_path in Path(directory).glob("*"):
            if file_path.is_file():
                file_age = current_time - file_path.stat().st_mtime
                if file_age > 86400:  # 24 hours
                    try:
                        file_path.unlink()
                        logger.info(f"Cleaned up old file: {file_path}")
                    except Exception as e:
                        logger.error(f"Failed to delete {file_path}: {e}")

async def save_upload_file(upload_file: UploadFile, upload_type: str = "general") -> Dict[str, Any]:
    """Save uploaded file and return file info"""
    logger.info(f"=== save_upload_file called ===")
    logger.info(f"Upload type: {upload_type}")
    logger.info(f"Filename: {upload_file.filename}")
    
    try:
        file_id = str(uuid.uuid4())
        file_extension = Path(upload_file.filename).suffix
        saved_filename = f"{file_id}{file_extension}"
        file_path = Path(settings.UPLOAD_DIR) / upload_type / saved_filename
        
        logger.info(f"Target path: {file_path}")
        
        # Create type-specific directory
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            logger.info(f"Directory created/verified: {file_path.parent}")
        except Exception as e:
            logger.error(f"Failed to create directory: {e}")
            raise HTTPException(500, f"Failed to create upload directory: {e}")
        
        # Save file by streaming in chunks to avoid memory issues
        total_size = 0
        try:
            async with aiofiles.open(file_path, 'wb') as f:
                while chunk := await upload_file.read(8192):  # Read in 8KB chunks
                    await f.write(chunk)
                    total_size += len(chunk)
            logger.info(f"File saved successfully, size: {total_size} bytes")
        except Exception as e:
            logger.error(f"Failed to save file: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            raise HTTPException(500, f"Failed to save file: {e}")
        
        return {
            "file_id": file_id,
            "filename": upload_file.filename,
            "saved_path": str(file_path),
            "file_type": upload_type,
            "size": total_size,
            "upload_time": datetime.now()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in save_upload_file: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        raise HTTPException(500, f"Unexpected error saving file: {e}")

# Helper function for database operations
# Removed: async def get_db_session(): ...

# API Endpoints
# Moved to lifespan context manager

@app.get("/")
async def root():
    """Root endpoint - serves the web interface"""
    return FileResponse("static/index.html")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(),
        "version": "1.0.0"
    }

@app.post("/api/test-upload")
async def test_upload(
    file: UploadFile = File(...),
):
    """Test endpoint for debugging uploads"""
    logger.info("=== TEST UPLOAD ===")
    try:
        logger.info(f"File: {file.filename}")
        logger.info(f"Content-Type: {file.content_type}")
        
        # Try to read a small chunk first
        first_chunk = await file.read(1024)
        logger.info(f"Read first chunk: {len(first_chunk)} bytes")
        
        # Reset file position
        await file.seek(0)
        
        # Read file size
        contents = await file.read()
        size = len(contents)
        logger.info(f"Total size read: {size} bytes")
        
        return {
            "status": "success",
            "filename": file.filename,
            "content_type": file.content_type,
            "size": size,
            "size_mb": round(size / (1024 * 1024), 2)
        }
    except Exception as e:
        logger.error(f"Test upload error: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "error": str(e),
                "error_type": type(e).__name__,
                "filename": file.filename if file else "unknown"
            }
        )

@app.post("/api/upload/script", response_model=FileUploadResponse)
async def upload_script(
    file: UploadFile = File(..., description="Script file (.txt or .docx)"),
):
    if not file.filename.endswith((".txt", ".docx")):
        raise HTTPException(400, "Only .txt and .docx files are supported")
    
    # Save file using streaming approach
    file_info = await save_upload_file(file, "scripts")
    
    upload_time = datetime.now().isoformat()
    await create_file(
        user_id=None, # No user ID for public endpoints
        file_id=file_info["file_id"],
        filename=file_info["filename"],
        file_type="script",
        file_path=file_info["saved_path"],
        size=file_info["size"],
        upload_time=upload_time
    )
    return FileUploadResponse(
        file_id=file_info["file_id"],
        filename=file_info["filename"],
        file_type="script",
        size=file_info["size"],
        upload_time=upload_time
    )

@app.post("/api/upload/audio", response_model=FileUploadResponse)
async def upload_audio(
    file: UploadFile = File(..., description="Audio file (.mp3, .wav, .m4a)"),
):
    """Upload an audio file (voiceover)"""
    logger.info(f"=== Audio Upload Request ===")
    logger.info(f"Filename: {file.filename}")
    logger.info(f"Content Type: {file.content_type}")
    logger.info(f"File size (if available): {getattr(file, 'size', 'Unknown')}")
    
    try:
        # Check file extension
        if not file.filename:
            logger.error("No filename provided")
            raise HTTPException(400, "No filename provided")
        
        logger.info(f"Checking file extension for: '{file.filename}'")
        logger.info(f"Filename type: {type(file.filename)}")
        logger.info(f"Filename repr: {repr(file.filename)}")
        
        # Check extension case-insensitively
        filename_lower = file.filename.lower()
        if not filename_lower.endswith((".mp3", ".wav", ".m4a")):
            logger.error(f"Rejected file with invalid extension: {file.filename}")
            logger.error(f"Filename ends with: {file.filename[-4:]}")
            raise HTTPException(400, "Only .mp3, .wav, and .m4a files are supported")
        
        # Check file size before processing (if available)
        if hasattr(file, 'size') and file.size:
            max_size = getattr(settings, 'MAX_VOICEOVER_SIZE', 1 * 1024 * 1024 * 1024)  # 1GB for voiceover files
            if file.size > max_size:
                logger.error(f"Voiceover file too large: {file.size} bytes (limit: {max_size} bytes)")
                raise HTTPException(413, f"Voiceover file too large. Max allowed size is {max_size // (1024*1024)} MB.")
        
        # Save file using streaming approach
        file_info = await save_upload_file(file, "audio")
        
        # Check size after saving (in case size wasn't available before)
        max_size = getattr(settings, 'MAX_VOICEOVER_SIZE', 1 * 1024 * 1024 * 1024)  # 1GB for voiceover files
        if file_info["size"] > max_size:
            logger.error(f"Voiceover file too large: {file_info['size']} bytes (limit: {max_size} bytes)")
            # Clean up the saved file
            try:
                os.remove(file_info["saved_path"])
            except:
                pass
            raise HTTPException(413, f"Voiceover file too large. Max allowed size is {max_size // (1024*1024)} MB.")
        
        audio_processor = AudioProcessor()
        try:
            duration = audio_processor.get_duration(file_info["saved_path"])
            file_info["duration"] = duration
            
            # Check duration limit for voiceover files
            max_duration = getattr(settings, 'MAX_VOICEOVER_DURATION', 3600)  # 60 minutes
            if duration and duration > max_duration:
                logger.error(f"Voiceover duration too long: {duration} seconds (limit: {max_duration} seconds)")
                # Clean up the saved file
                try:
                    os.remove(file_info["saved_path"])
                except:
                    pass
                raise HTTPException(413, f"Voiceover duration too long. Max allowed duration is {max_duration // 60} minutes.")
                
        except Exception as e:
            logger.error(f"Failed to get audio duration: {e}")
            file_info["duration"] = None
        try:
            await create_file(
                user_id=None, # No user ID for public endpoints
                file_id=file_info["file_id"],
                filename=file_info["filename"],
                file_type="audio",
                file_path=file_info["saved_path"],
                size=file_info["size"],
                file_metadata={"duration": file_info.get("duration")}
            )
        except Exception as db_exc:
            logger.error(f"Database error in create_file: {db_exc}")
            raise HTTPException(500, f"Database error: {db_exc}")
        return FileUploadResponse(**file_info)
    except HTTPException as http_exc:
        # Re-raise HTTP exceptions as-is
        logger.error(f"HTTP Exception in voiceover upload: {http_exc.detail}")
        raise http_exc
    except Exception as exc:
        logger.error(f"Voiceover upload failed with unexpected error: {exc}")
        logger.error(f"Error type: {type(exc).__name__}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(500, f"Voiceover upload failed: {str(exc)} (Type: {type(exc).__name__})")

@app.post("/api/upload/video", response_model=FileUploadResponse)
async def upload_video(
    file: UploadFile = File(..., description="Video file (.mp4, .avi, .mov, .mkv)"),
    video_type: str = Form("broll", description="Type of video: 'broll' or 'intro'"),
):
    """Upload a video file for B-roll organization"""
    try:
        if not file.filename.endswith(('.mp4', '.avi', '.mov', '.mkv')):
            raise HTTPException(400, "Unsupported video format")
        
        # Check file size before processing (if available)
        if hasattr(file, 'size') and file.size:
            max_size = getattr(settings, 'MAX_VIDEO_SIZE', 2 * 1024 * 1024 * 1024)  # 2GB for video files
            if file.size > max_size:
                logger.error(f"Video file too large: {file.size} bytes (limit: {max_size} bytes)")
                raise HTTPException(413, f"Video file too large. Max allowed size is {max_size // (1024*1024*1024)} GB.")
        
        # Save file using streaming approach
        file_info = await save_upload_file(file, f"videos/{video_type}")
        
        # Check size after saving (in case size wasn't available before)
        max_size = getattr(settings, 'MAX_VIDEO_SIZE', 2 * 1024 * 1024 * 1024)  # 2GB for video files
        if file_info["size"] > max_size:
            logger.error(f"Video file too large: {file_info['size']} bytes (limit: {max_size} bytes)")
            # Clean up the saved file
            try:
                os.remove(file_info["saved_path"])
            except:
                pass
            raise HTTPException(413, f"Video file too large. Max allowed size is {max_size // (1024*1024*1024)} GB.")
        
        # Check video duration
        video_processor = VideoProcessor()
        try:
            duration = video_processor.get_duration(file_info["saved_path"])
            file_info["duration"] = duration
            
            # Check duration limit for video files
            max_duration = getattr(settings, 'MAX_VIDEO_DURATION', 3600)  # 60 minutes
            if duration and duration > max_duration:
                logger.error(f"Video duration too long: {duration} seconds (limit: {max_duration} seconds)")
                # Clean up the saved file
                try:
                    os.remove(file_info["saved_path"])
                except:
                    pass
                raise HTTPException(413, f"Video duration too long. Max allowed duration is {max_duration // 60} minutes.")
                
        except Exception as e:
            logger.error(f"Failed to get video duration: {e}")
            file_info["duration"] = None
        
        # Store in database
        await create_file(
            user_id=None, # No user ID for public endpoints
            file_id=file_info["file_id"],
            filename=file_info["filename"],
            file_type=f"video_{video_type}",
            file_path=file_info["saved_path"],
            size=file_info["size"],
            file_metadata={"duration": file_info.get("duration")}
        )
        
        return FileUploadResponse(**file_info)
    except Exception as exc:
        logger.error(f"Video upload failed: {exc}")
        raise HTTPException(500, f"Video upload failed: {exc}")

@app.post("/api/generate/ai-images", response_model=JobResponse)
async def generate_ai_images(
    background_tasks: BackgroundTasks,
    script_file_id: str = Form(...),
    voice_file_id: str = Form(...),
    script_text: str = Form(None),  # Make optional
    image_count: int = Form(...),
    style: str = Form(...),
    character_description: str = Form(...),
    voice_duration: float = Form(...),
    export_options: str = Form(...),
):
    """Start AI image generation job"""
    logger.info(f"Received image generation request: images={image_count}, style={style}")
    
    try:
        # Validate API key
        api_manager = APIKeyManager()
        api_key = api_manager.get_api_key()
        logger.info(f"API key check: {'Found' if api_key else 'Not found'}")
        
        if not api_key:
            logger.error("OpenAI API key not configured.")
            raise HTTPException(400, "OpenAI API key not configured. Please set it in settings.")
        # Get file paths from database
        logger.info(f"Looking up files: script={script_file_id}, voice={voice_file_id}")
        script_file = await get_file_by_id(script_file_id)
        voice_file = await get_file_by_id(voice_file_id)
        
        logger.info(f"Script file: {script_file}")
        logger.info(f"Voice file: {voice_file}")
        
        if not script_file or not voice_file:
            logger.error(f"Script or voice file not found: script_file={script_file}, voice_file={voice_file}")
            raise HTTPException(404, "Script or voice file not found")
        
        # If script_text not provided, try to read from file
        if not script_text:
            try:
                with open(script_file['file_path'], 'r', encoding='utf-8') as f:
                    script_text = f.read()
                logger.info("Successfully read script from file")
            except Exception as e:
                logger.error(f"Failed to read script file: {e}")
                script_text = "Generate images based on the uploaded content."
        # Create job
        job_id = str(uuid.uuid4())
        created_at = datetime.now().isoformat()
        logger.info(f"Creating job with ID: {job_id}")
        
        try:
            await create_job(
                job_id=job_id,
                user_id=None, # No user ID for public endpoints
                status="pending",
                message="AI image generation job started",
                created_at=created_at,
                progress=0,
                result_path=None,
                job_type="ai_image_generation"
            )
            logger.info("Job created successfully in database")
        except Exception as db_exc:
            logger.error(f"Database error in create_job: {db_exc}")
            raise HTTPException(500, f"Database error: {db_exc}")
        # Parse export options
        try:
            export_options_dict = json.loads(export_options)
        except json.JSONDecodeError:
            export_options_dict = {"images": True, "clips": True, "full_video": False}
        
        # Start task in background
        try:
            # For now, run the task synchronously since Redis might not be available
            background_tasks.add_task(
                tasks.run_ai_images_task_sync,
                job_id,
                {
                    "user_id": None,  # No user ID for public endpoints
                    "params": {
                        "script_path": script_file['file_path'],
                        "voice_path": voice_file['file_path'],
                        "script_text": script_text,
                        "image_count": image_count,
                        "style": style,
                        "character_description": character_description,
                        "voice_duration": voice_duration,
                        "export_options": export_options_dict
                    }
                }
            )
        except Exception as task_exc:
            logger.error(f"Task start error: {task_exc}")
            raise HTTPException(500, f"Task start error: {task_exc}")
        return JobResponse(
            job_id=job_id,
            status="pending",
            message="AI image generation job started",
            created_at=created_at,
            progress=0,
            result_url=None
        )
    except Exception as exc:
        logger.error(f"Image generation request failed: {exc}")
        raise HTTPException(500, f"Image generation request failed: {exc}")

@app.post("/api/generate/video", response_model=JobResponse)
async def create_video_from_images(
    request: CreateVideoRequest,
    background_tasks: BackgroundTasks,
):
    """Create video from previously generated AI images"""
    # Get the original job to retrieve image data
    original_job = await get_job_by_id(request.original_job_id)
    if not original_job:
        raise HTTPException(404, "Original job not found")
    
    if original_job['status'] != 'completed':
        raise HTTPException(400, "Original job must be completed before creating video")
    
    # Parse result to get image paths
    if not original_job.get('result'):
        raise HTTPException(400, "No images found in original job")
    
    try:
        result_data = json.loads(original_job['result'])
    except:
        raise HTTPException(400, "Invalid job result data")
    
    # Create new job for video creation
    job_id = str(uuid.uuid4())
    created_at = datetime.now().isoformat()
    await create_job(
        job_id=job_id,
        user_id=None,
        status="pending",
        message="Video creation job started",
        created_at=created_at,
        job_type="video_creation",
        params=json.dumps({
            "original_job_id": request.original_job_id,
            "create_clips": request.create_clips,
            "create_full_video": request.create_full_video
        })
    )
    
    # Run task synchronously in background
    from tasks import run_video_creation_task_sync
    
    threading.Thread(
        target=run_video_creation_task_sync,
        args=(job_id, {
            "job_type": "video_creation",
            "user_id": None,
            "params": {
                "original_job_id": request.original_job_id,
                "original_result": result_data,
                "create_clips": request.create_clips,
                "create_full_video": request.create_full_video
            }
        })
    ).start()
    
    return JobResponse(
        job_id=job_id,
        status="pending",
        message="Video creation job started",
        created_at=created_at,
        progress=0,
        result_url=None
    )

@app.post("/api/generate/broll", response_model=JobResponse)
async def organize_broll(
    request: BRollOrganizationRequest,
    background_tasks: BackgroundTasks,
):
    """Start B-roll organization job"""
    # Validate files exist
    all_video_ids = request.intro_clip_ids + request.broll_clip_ids
    for video_id in all_video_ids:
        video_file = await get_file_by_id(video_id)
        if not video_file:
            raise HTTPException(404, f"Video file {video_id} not found")
    
    # Check voiceover if provided
    if request.voiceover_id:
        voice_file = await get_file_by_id(request.voiceover_id)
        if not voice_file:
            raise HTTPException(404, "Voiceover file not found")
    
    # Create job
    job_id = str(uuid.uuid4())
    created_at = datetime.now().isoformat()
    await create_job(
        job_id=job_id,
        user_id=None, # No user ID for public endpoints
        status="pending",
        message="B-roll organization job started",
        created_at=created_at,
        progress=0,
        result_path=None,
        job_type="broll_organization"
    )
    
    # Start task in background
    background_tasks.add_task(
        tasks.run_broll_task_sync,
        job_id,
        {
            "user_id": None,  # No user ID for public endpoints
            "params": request.dict()
        }
    )
    
    return JobResponse(
        job_id=job_id,
        status="pending",
        message="B-roll organization job started",
        created_at=created_at,
        progress=0,
        result_url=None
    )

@app.get("/api/jobs/{job_id}", response_model=JobResponse)
async def get_job_status_endpoint(job_id: str):
    job = await get_job_by_id(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    
    # Parse result if it exists
    result_data = None
    if job.get('result'):
        try:
            result_data = json.loads(job['result'])
        except:
            pass
    
    # Generate proper download URL if result_path exists
    download_url = None
    if job.get('result_path'):
        # For B-roll jobs, the result_path points to the final video
        download_url = f"/api/files/serve/{job['result_path']}"
    
    return JobResponse(
        job_id=job['job_id'],
        status=job['status'],
        message=job['message'],
        created_at=job['created_at'],
        progress=job['progress'],
        result_url=download_url,
        result=result_data,
        job_type=job.get('job_type')
    )

@app.get("/api/jobs", response_model=List[JobResponse])
async def list_jobs(
    skip: int = 0,
    limit: int = 10,
):
    """List user's jobs"""
    from db_utils import get_user_jobs
    jobs = await get_user_jobs(None, skip, limit) # No user ID for public endpoints
    job_responses = []
    for job in jobs:
        # Parse result if it exists
        result_data = None
        if job.get('result'):
            try:
                result_data = json.loads(job['result'])
            except:
                pass
        
        # Generate proper download URL if result_path exists
        download_url = None
        if job.get('result_path'):
            download_url = f"/api/files/serve/{job['result_path']}"
        
        job_responses.append(JobResponse(
            job_id=job['job_id'],
            status=job['status'],
            message=job['message'],
            created_at=job['created_at'],
            progress=job['progress'],
            result_url=download_url,
            result=result_data,
            job_type=job.get('job_type')
        ))
    return job_responses

@app.delete("/api/jobs/{job_id}")
async def cancel_job(
    job_id: str,
):
    """Cancel a running job"""
    job = await get_job_by_id(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    
    if job['status'] not in ["pending", "processing"]:
        raise HTTPException(400, "Job cannot be cancelled")
    
    # Cancel Celery task
    celery_app.control.revoke(job_id, terminate=True)
    
    # Update job status
    await update_job_status(job_id, "cancelled", "Job cancelled by user")
    
    return {"message": "Job cancelled successfully"}

@app.get("/api/files/{file_id}/content")
async def get_file_content(file_id: str):
    """Get the content of a file"""
    try:
        file_record = await get_file_by_id(file_id)
        if not file_record:
            logger.error(f"File record not found for ID: {file_id}")
            raise HTTPException(404, "File not found in database")
        
        file_path = file_record.get('file_path')
        if not file_path:
            logger.error(f"File path is None for file ID: {file_id}")
            raise HTTPException(404, "File path not found")
            
        if not os.path.exists(file_path):
            logger.error(f"File not found on disk: {file_path}")
            raise HTTPException(404, f"File not found on disk: {file_path}")
        
        # Read file content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        # Return as JSON response with proper content type
        return JSONResponse(content={"content": content, "file_id": file_id})
        
    except Exception as e:
        logger.error(f"Error reading file content: {e}")
        raise HTTPException(500, f"Error reading file: {str(e)}")

@app.get("/api/download/{job_id}/{filename}")
async def download_result(
    job_id: str,
    filename: str,
):
    """Download job result file"""
    job = await get_job_by_id(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    
    file_path = Path(settings.OUTPUT_DIR) / job_id / filename
    
    if not file_path.exists():
        raise HTTPException(404, "File not found")
    
    return FileResponse(
        file_path,
        media_type='application/octet-stream',
        filename=filename
    )

@app.get("/api/files/serve/{file_path:path}")
async def serve_file(file_path: str):
    """Serve generated files (images, videos, etc.)"""
    # Try to construct full path - handle both absolute and relative paths
    if Path(file_path).is_absolute():
        full_path = Path(file_path)
    else:
        # Try outputs directory first (for job_id/filename.png format)
        full_path = Path(settings.OUTPUT_DIR) / file_path
        if not full_path.exists():
            # Try uploads directory
            full_path = Path(settings.UPLOAD_DIR) / file_path
    
    # Security check - ensure file is within allowed directories
    allowed_dirs = [
        Path(settings.OUTPUT_DIR).resolve(),
        Path(settings.UPLOAD_DIR).resolve()
    ]
    
    try:
        resolved_path = full_path.resolve()
        if not any(str(resolved_path).startswith(str(allowed_dir)) for allowed_dir in allowed_dirs):
            raise HTTPException(403, "Access denied")
    except Exception:
        raise HTTPException(404, "File not found")
    
    if not full_path.exists() or not full_path.is_file():
        raise HTTPException(404, "File not found")
    
    # Determine media type
    media_type = 'application/octet-stream'
    if full_path.suffix.lower() in ['.png', '.jpg', '.jpeg', '.gif']:
        media_type = f'image/{full_path.suffix[1:]}'
    elif full_path.suffix.lower() in ['.mp4', '.avi', '.mov', '.mkv']:
        media_type = f'video/{full_path.suffix[1:]}'
    elif full_path.suffix.lower() in ['.mp3', '.wav', '.m4a']:
        media_type = f'audio/{full_path.suffix[1:]}'
    
    return FileResponse(
        full_path,
        media_type=media_type,
        filename=full_path.name
    )

@app.post("/api/settings/api-key")
async def set_api_key(
    api_key: str = Form(...),
):
    """Set OpenAI API key for the user"""
    try:
        # For simplicity in public mode, store the API key in environment
        os.environ['OPENAI_API_KEY'] = api_key
        
        # Also store in a file for persistence
        api_key_file = Path("api_key.txt")
        api_key_file.write_text(api_key)
        
        # Validate the API key by testing it
        api_manager = APIKeyManager()
        api_manager.set_api_key(api_key)
        
        return {"message": "API key set successfully"}
    except Exception as e:
        logger.error(f"API key storage error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to set API key"
        )

@app.get("/api/check-api-key")
async def check_api_key():
    """Check if OpenAI API key is configured"""
    # Check environment variable first
    env_key = os.getenv('OPENAI_API_KEY')
    if env_key:
        return {"status": "ok", "source": "environment"}
    
    # Check stored file
    api_key_file = Path("api_key.txt")
    if api_key_file.exists():
        try:
            stored_key = api_key_file.read_text().strip()
            if stored_key:
                # Load it into environment for this session
                os.environ['OPENAI_API_KEY'] = stored_key
                return {"status": "ok", "source": "file"}
        except Exception as e:
            logger.error(f"Error reading API key file: {e}")
    
    raise HTTPException(404, "API key not configured")

@app.get("/api/results")
async def get_results():
    """Get all generated video results"""
    try:
        results = []
        results_dir = Path("results")
        
        if not results_dir.exists():
            return {"results": []}
        
        # Get all MP4 files in results directory
        for file_path in results_dir.rglob("*.mp4"):
            if file_path.is_file():
                stat = file_path.stat()
                
                # Determine if this is a "latest" file
                is_latest = file_path.name.startswith("latest_")
                
                # Get relative path from results directory
                relative_path = file_path.relative_to(results_dir)
                
                results.append({
                    "name": file_path.name,
                    "path": str(relative_path),
                    "size": stat.st_size,
                    "modified": stat.st_mtime,
                    "isLatest": is_latest
                })
        
        # Sort by modification time (newest first)
        results.sort(key=lambda x: x["modified"], reverse=True)
        
        return {"results": results}
    except Exception as e:
        logger.error(f"Error getting results: {e}")
        raise HTTPException(status_code=500, detail="Failed to get results")

@app.get("/api/download/{file_path:path}")
async def download_file(file_path: str):
    """Download a file from the results directory"""
    try:
        # Construct full path
        full_path = Path("results") / file_path
        
        # Security check: ensure the file is within the results directory
        if not str(full_path.resolve()).startswith(str(Path("results").resolve())):
            raise HTTPException(status_code=403, detail="Access denied")
        
        if not full_path.exists() or not full_path.is_file():
            raise HTTPException(status_code=404, detail="File not found")
        
        # Return file as streaming response
        return FileResponse(
            path=str(full_path),
            filename=full_path.name,
            media_type="video/mp4"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading file {file_path}: {e}")
        raise HTTPException(status_code=500, detail="Failed to download file")

# WebSocket for real-time job updates
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Set

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)

    def disconnect(self, websocket: WebSocket, user_id: str):
        if user_id in self.active_connections:
            self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

    async def send_job_update(self, user_id: str, message: dict):
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except:
                    pass

manager = ConnectionManager()

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_text()
            # Handle any client messages if needed
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8080,
        reload=True
    )