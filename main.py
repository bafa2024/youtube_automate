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
from typing import List, Optional, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Request, Form, Depends
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
from database import Base, JobStatus, User, FileRecord, get_db
from auth import get_current_user, create_access_token, auth_router
from config import settings
from celery_app import celery_app
import tasks
from db_utils import init_db, create_file, get_file_by_id, create_job, get_job_by_id, update_job_status
from db_utils import get_user_by_id

# WebSocket for real-time job updates
from fastapi import WebSocket, WebSocketDisconnect
from typing import Set

# Setup logging
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up AI Video Tool API...")
    
    # Create necessary directories
    for dir_path in [settings.UPLOAD_DIR, settings.OUTPUT_DIR, settings.TEMP_DIR]:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    # Initialize database
    # Removed: async with engine.begin() as conn:
    # Removed: await conn.run_sync(Base.metadata.create_all)
    
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

# Database setup
# Removed: engine = create_async_engine(settings.DATABASE_URL, echo=True)
# Removed: async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Include routers
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
    file_id = str(uuid.uuid4())
    file_extension = Path(upload_file.filename).suffix
    saved_filename = f"{file_id}{file_extension}"
    file_path = Path(settings.UPLOAD_DIR) / upload_type / saved_filename
    
    # Create type-specific directory
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save file
    async with aiofiles.open(file_path, 'wb') as f:
        content = await upload_file.read()
        await f.write(content)
    
    return {
        "file_id": file_id,
        "filename": upload_file.filename,
        "saved_path": str(file_path),
        "file_type": upload_type,
        "size": len(content),
        "upload_time": datetime.now()
    }

# Helper function for database operations
# Removed: async def get_db_session(): ...

# API Endpoints
@app.on_event("startup")
async def on_startup():
    await init_db()

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
    file_id = str(uuid.uuid4())
    file_extension = Path(file.filename).suffix
    saved_filename = f"{file_id}{file_extension}"
    file_path = Path(settings.UPLOAD_DIR) / "scripts" / saved_filename
    file_path.parent.mkdir(parents=True, exist_ok=True)
    content = await file.read()
    async with aiofiles.open(file_path, 'wb') as f:
        await f.write(content)
    upload_time = datetime.now().isoformat()
    await create_file(
        user_id=current_user['id'],
        file_id=file_id,
        filename=file.filename,
        file_type="script",
        file_path=str(file_path),
        size=len(content),
        upload_time=upload_time
    )
    return FileUploadResponse(
        file_id=file_id,
        filename=file.filename,
        file_type="script",
        size=len(content),
        upload_time=upload_time
    )

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

@app.post("/api/generate/ai-images", response_model=JobResponse)
async def generate_ai_images(
    request: AIImageGenerationRequest,
    background_tasks: BackgroundTasks,
    script_file_id: str = Form(...),
    voice_file_id: str = Form(...),
    current_user: dict = Depends(get_current_user)
):
    """Start AI image generation job"""
    # Validate API key
    api_manager = APIKeyManager()
    if not api_manager.get_api_key():
        raise HTTPException(400, "OpenAI API key not configured. Please set it in settings.")
    
    # Get file paths from database
    script_file = await get_file_by_id(script_file_id)
    voice_file = await get_file_by_id(voice_file_id)
    
    if not script_file or not voice_file:
        raise HTTPException(404, "Script or voice file not found")
    
    # Create job
    job_id = str(uuid.uuid4())
    created_at = datetime.now().isoformat()
    await create_job(
        job_id=job_id,
        user_id=current_user['id'],
        status="pending",
        message="AI image generation job started",
        created_at=created_at,
        progress=0,
        result_path=None
    )
    
    # Queue task
    task = tasks.generate_ai_images_task.apply_async(
        args=[job_id, {
            "script_path": script_file.file_path,
            "voice_path": voice_file.file_path,
            "script_text": request.script_text,
            "image_count": request.image_count,
            "style": request.style,
            "character_description": request.character_description,
            "voice_duration": request.voice_duration,
            "export_options": request.export_options
        }],
        task_id=job_id
    )
    
    return JobResponse(
        job_id=job_id,
        status="pending",
        message="AI image generation job started",
        created_at=created_at,
        progress=0,
        result_url=None
    )

@app.post("/api/generate/broll", response_model=JobResponse)
async def organize_broll(
    request: BRollOrganizationRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
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
        user_id=current_user.id,
        status="pending",
        message="B-roll organization job started",
        created_at=created_at,
        progress=0,
        result_path=None
    )
    
    # Queue task
    task = tasks.organize_broll_task.apply_async(
        args=[job_id, request.dict()],
        task_id=job_id
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
async def get_job_status_endpoint(job_id: str, current_user: dict = Depends(get_current_user)):
    job = await get_job_by_id(job_id)
    if not job or job['user_id'] != current_user['id']:
        raise HTTPException(404, "Job not found")
    return JobResponse(
        job_id=job['job_id'],
        status=job['status'],
        message=job['message'],
        created_at=job['created_at'],
        progress=job['progress'],
        result_url=job['result_path']
    )

@app.get("/api/jobs", response_model=List[JobResponse])
async def list_jobs(
    skip: int = 0,
    limit: int = 10,
    current_user: User = Depends(get_current_user)
):
    """List user's jobs"""
    jobs = await get_user_by_id(current_user.id).get_jobs(skip, limit)
    return [
        JobResponse(
            job_id=job['job_id'],
            status=job['status'],
            message=job['message'],
            created_at=job['created_at'],
            progress=job['progress'],
            result_url=job['result_path']
        )
        for job in jobs
    ]

@app.delete("/api/jobs/{job_id}")
async def cancel_job(
    job_id: str,
    current_user: User = Depends(get_current_user)
):
    """Cancel a running job"""
    job = await get_job_by_id(job_id)
    if not job or job['user_id'] != current_user.id:
        raise HTTPException(404, "Job not found")
    
    if job['status'] not in ["pending", "processing"]:
        raise HTTPException(400, "Job cannot be cancelled")
    
    # Cancel Celery task
    celery_app.control.revoke(job_id, terminate=True)
    
    # Update job status
    await update_job_status(job_id, "cancelled", "Job cancelled by user")
    
    return {"message": "Job cancelled successfully"}

@app.get("/api/download/{job_id}/{filename}")
async def download_result(
    job_id: str,
    filename: str,
    current_user: User = Depends(get_current_user)
):
    """Download job result file"""
    job = await get_job_by_id(job_id)
    if not job or job['user_id'] != current_user.id:
        raise HTTPException(404, "Job not found")
    
    file_path = Path(settings.OUTPUT_DIR) / job_id / filename
    
    if not file_path.exists():
        raise HTTPException(404, "File not found")
    
    return FileResponse(
        file_path,
        media_type='application/octet-stream',
        filename=filename
    )

@app.post("/api/settings/api-key")
async def set_api_key(
    api_key: str = Form(...),
    current_user: User = Depends(get_current_user)
):
    """Set OpenAI API key for the user"""
    # Encrypt and store API key
    from cryptography.fernet import Fernet
    import base64
    
    # Generate a key for encryption (in production, use a secure key)
    key = base64.urlsafe_b64encode(b"your-secret-key-32-bytes-long!!")
    cipher = Fernet(key)
    encrypted_key = cipher.encrypt(api_key.encode())
    
    # Store in database
    await get_user_by_id(current_user.id).set_api_key(encrypted_key.decode())
    
    return {"message": "API key set successfully"}

@app.get("/api/settings/api-key")
async def check_api_key(
    current_user: User = Depends(get_current_user)
):
    """Check if user has API key configured"""
    api_manager = APIKeyManager()
    has_key = api_manager.has_api_key()
    return {"has_api_key": has_key}

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