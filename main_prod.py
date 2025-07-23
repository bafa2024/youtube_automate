"""
Production version of main.py without Celery dependencies
"""

import logging
import uuid
import aiofiles
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Request, Form, Depends
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Core imports
from core.video_processor import VideoProcessor
from core.audio_processor import AudioProcessor
from core.api_manager import APIKeyManager
from core.openai_generator import OpenAIImageGenerator

# Database and auth imports
from database import Base, JobStatus, User, FileRecord, get_db
from auth import get_current_user, create_access_token, auth_router
from config import settings

# Database utilities
from db_utils import init_db, create_file, get_file_by_id, create_job, get_job_by_id, update_job_status
from db_utils import get_user_by_id

# WebSocket imports
from fastapi import WebSocket, WebSocketDisconnect
from typing import Set

# Security imports
from cryptography.fernet import Fernet

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="YouTube Automation Tool",
    description="AI-powered video generation and editing tool",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include auth router
app.include_router(auth_router, prefix="/auth", tags=["authentication"])

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Pydantic models
class AIImageGenerationRequest(BaseModel):
    script_text: str = Field(description="Script text for image generation")
    image_count: int = Field(default=5, ge=1, le=20, description="Number of images to generate")
    style: str = Field(default="Photorealistic", description="Image style")
    character_description: str = Field(description="Character description")
    voice_duration: float = Field(gt=0, description="Duration of voiceover in seconds")
    export_options: Dict[str, bool] = Field(
        default={"export_images": True, "export_video": True},
        description="Export options"
    )

class BRollOrganizationRequest(BaseModel):
    intro_clip_ids: List[str] = Field(default=[], description="List of intro clip UUIDs")
    broll_clip_ids: List[str] = Field(description="List of B-roll clip UUIDs")
    voiceover_id: Optional[str] = Field(default=None, description="Voiceover UUID")
    sync_to_voiceover: bool = Field(default=True, description="Sync video to voiceover duration")
    overlay_audio: bool = Field(default=True, description="Overlay voiceover on final video")

class JobResponse(BaseModel):
    job_id: str
    status: str
    message: str
    created_at: datetime
    progress: int = 0
    result_url: Optional[str] = None

class FileUploadResponse(BaseModel):
    file_id: str
    filename: str
    file_type: str
    size: int
    upload_time: datetime

# Application lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up YouTube Automation Tool...")
    await init_db()
    logger.info("Database initialized successfully")
    
    # Create necessary directories
    Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
    Path(settings.OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    Path(settings.TEMP_DIR).mkdir(parents=True, exist_ok=True)
    
    yield
    
    # Shutdown
    logger.info("Shutting down YouTube Automation Tool...")

app = FastAPI(lifespan=lifespan)

# File upload helper
async def save_upload_file(upload_file: UploadFile, upload_type: str = "general") -> Dict[str, Any]:
    """Save uploaded file and return file info"""
    file_id = str(uuid.uuid4())
    file_extension = Path(upload_file.filename).suffix
    saved_filename = f"{file_id}{file_extension}"
    
    # Create type-specific directory
    upload_path = Path(settings.UPLOAD_DIR) / upload_type
    upload_path.mkdir(parents=True, exist_ok=True)
    
    file_path = upload_path / saved_filename
    content = await upload_file.read()
    
    async with aiofiles.open(file_path, 'wb') as f:
        await f.write(content)
    
    return {
        "file_id": file_id,
        "filename": upload_file.filename,
        "saved_path": str(file_path),
        "size": len(content),
        "upload_time": datetime.now().isoformat()
    }

# Routes
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

@app.post("/api/upload/script", response_model=FileUploadResponse)
async def upload_script(
    file: UploadFile = File(..., description="Script file (.txt or .docx)"),
    current_user: dict = Depends(get_current_user)
):
    if not file.filename.endswith((".txt", ".docx")):
        raise HTTPException(400, "Only .txt and .docx files are supported")
    
    file_info = await save_upload_file(file, "scripts")
    
    await create_file(
        user_id=current_user['id'],
        file_id=file_info["file_id"],
        filename=file_info["filename"],
        file_type="script",
        file_path=file_info["saved_path"],
        size=file_info["size"],
        upload_time=file_info["upload_time"]
    )
    
    return FileUploadResponse(**file_info)

@app.post("/api/upload/audio", response_model=FileUploadResponse)
async def upload_audio(
    file: UploadFile = File(..., description="Audio file (.mp3, .wav, .m4a)"),
    current_user: User = Depends(get_current_user)
):
    """Upload an audio file (voiceover)"""
    if not file.filename.endswith(('.mp3', '.wav', '.m4a')):
        raise HTTPException(400, "Only .mp3, .wav, and .m4a files are supported")
    
    file_info = await save_upload_file(file, "audio")
    
    # Get audio duration
    audio_processor = AudioProcessor()
    try:
        duration = audio_processor.get_duration(file_info["saved_path"])
        file_info["duration"] = duration
    except Exception as e:
        logger.error(f"Failed to get audio duration: {e}")
        file_info["duration"] = None
    
    # Store in database
    await create_file(
        user_id=current_user.id,
        file_id=file_info["file_id"],
        filename=file_info["filename"],
        file_type="audio",
        file_path=file_info["saved_path"],
        size=file_info["size"],
        file_metadata={"duration": file_info.get("duration")}
    )
    
    return FileUploadResponse(**file_info)

@app.post("/api/upload/video", response_model=FileUploadResponse)
async def upload_video(
    file: UploadFile = File(..., description="Video file (.mp4, .avi, .mov, .mkv)"),
    video_type: str = Form("broll", description="Type of video: 'broll' or 'intro'"),
    current_user: User = Depends(get_current_user)
):
    """Upload a video file for B-roll organization"""
    if not file.filename.endswith(('.mp4', '.avi', '.mov', '.mkv')):
        raise HTTPException(400, "Unsupported video format")
    
    file_info = await save_upload_file(file, f"videos/{video_type}")
    
    # Store in database
    await create_file(
        user_id=current_user.id,
        file_id=file_info["file_id"],
        filename=file_info["filename"],
        file_type=f"video_{video_type}",
        file_path=file_info["saved_path"],
        size=file_info["size"]
    )
    
    return FileUploadResponse(**file_info)

# Simple job management (without Celery)
@app.post("/api/generate/ai-images", response_model=JobResponse)
async def generate_ai_images(
    request: AIImageGenerationRequest,
    background_tasks: BackgroundTasks,
    script_file_id: str = Form(...),
    voice_file_id: str = Form(...),
    current_user: dict = Depends(get_current_user)
):
    """Generate AI images based on script and voiceover"""
    job_id = str(uuid.uuid4())
    
    # Create job record
    await create_job(
        user_id=current_user['id'],
        job_id=job_id,
        job_type="ai_image_generation",
        status=JobStatus.PENDING,
        parameters=request.dict()
    )
    
    # For now, just return the job ID (in production, this would trigger a background task)
    return JobResponse(
        job_id=job_id,
        status="pending",
        message="Job created successfully",
        created_at=datetime.now(),
        progress=0
    )

@app.get("/api/jobs/{job_id}", response_model=JobResponse)
async def get_job_status_endpoint(job_id: str, current_user: dict = Depends(get_current_user)):
    """Get job status"""
    job = await get_job_by_id(job_id)
    if not job or job.user_id != current_user['id']:
        raise HTTPException(404, "Job not found")
    
    return JobResponse(
        job_id=job.job_id,
        status=job.status.value,
        message=job.message or "Job in progress",
        created_at=job.created_at,
        progress=job.progress or 0,
        result_url=job.result_url
    )

@app.get("/api/jobs", response_model=List[JobResponse])
async def list_jobs(
    skip: int = 0,
    limit: int = 10,
    current_user: User = Depends(get_current_user)
):
    """List user's jobs"""
    # This would need to be implemented in db_utils
    return []

# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    ) 