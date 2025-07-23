"""
Minimal production version without SQLAlchemy for initial deployment
"""

import logging
import uuid
import aiofiles
import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Request, Form, Depends
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

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

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Simple in-memory storage (for testing)
jobs_db = {}
files_db = {}

# Pydantic models
class FileUploadResponse(BaseModel):
    file_id: str
    filename: str
    file_type: str
    size: int
    upload_time: datetime

class JobResponse(BaseModel):
    job_id: str
    status: str
    message: str
    created_at: datetime
    progress: int = 0
    result_url: Optional[str] = None

# Application lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up YouTube Automation Tool...")
    
    # Create necessary directories
    Path("uploads").mkdir(parents=True, exist_ok=True)
    Path("outputs").mkdir(parents=True, exist_ok=True)
    Path("temp").mkdir(parents=True, exist_ok=True)
    
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
    upload_path = Path("uploads") / upload_type
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
        "version": "1.0.0",
        "message": "YouTube Automation Tool is running"
    }

@app.post("/api/upload/script", response_model=FileUploadResponse)
async def upload_script(
    file: UploadFile = File(..., description="Script file (.txt or .docx)")
):
    """Upload a script file"""
    if not file.filename.endswith((".txt", ".docx")):
        raise HTTPException(400, "Only .txt and .docx files are supported")
    
    file_info = await save_upload_file(file, "scripts")
    
    # Store in memory (for testing)
    files_db[file_info["file_id"]] = {
        "filename": file_info["filename"],
        "file_type": "script",
        "file_path": file_info["saved_path"],
        "size": file_info["size"],
        "upload_time": file_info["upload_time"]
    }
    
    return FileUploadResponse(
        file_id=file_info["file_id"],
        filename=file_info["filename"],
        file_type="script",
        size=file_info["size"],
        upload_time=datetime.fromisoformat(file_info["upload_time"])
    )

@app.post("/api/upload/audio", response_model=FileUploadResponse)
async def upload_audio(
    file: UploadFile = File(..., description="Audio file (.mp3, .wav, .m4a)")
):
    """Upload an audio file (voiceover)"""
    if not file.filename.endswith(('.mp3', '.wav', '.m4a')):
        raise HTTPException(400, "Only .mp3, .wav, and .m4a files are supported")
    
    file_info = await save_upload_file(file, "audio")
    
    # Store in memory (for testing)
    files_db[file_info["file_id"]] = {
        "filename": file_info["filename"],
        "file_type": "audio",
        "file_path": file_info["saved_path"],
        "size": file_info["size"],
        "upload_time": file_info["upload_time"]
    }
    
    return FileUploadResponse(
        file_id=file_info["file_id"],
        filename=file_info["filename"],
        file_type="audio",
        size=file_info["size"],
        upload_time=datetime.fromisoformat(file_info["upload_time"])
    )

@app.post("/api/upload/video", response_model=FileUploadResponse)
async def upload_video(
    file: UploadFile = File(..., description="Video file (.mp4, .avi, .mov, .mkv)"),
    video_type: str = Form("broll", description="Type of video: 'broll' or 'intro'")
):
    """Upload a video file for B-roll organization"""
    if not file.filename.endswith(('.mp4', '.avi', '.mov', '.mkv')):
        raise HTTPException(400, "Unsupported video format")
    
    file_info = await save_upload_file(file, f"videos/{video_type}")
    
    # Store in memory (for testing)
    files_db[file_info["file_id"]] = {
        "filename": file_info["filename"],
        "file_type": f"video_{video_type}",
        "file_path": file_info["saved_path"],
        "size": file_info["size"],
        "upload_time": file_info["upload_time"]
    }
    
    return FileUploadResponse(
        file_id=file_info["file_id"],
        filename=file_info["filename"],
        file_type=f"video_{video_type}",
        size=file_info["size"],
        upload_time=datetime.fromisoformat(file_info["upload_time"])
    )

@app.post("/api/generate/ai-images", response_model=JobResponse)
async def generate_ai_images(
    script_file_id: str = Form(...),
    voice_file_id: str = Form(...)
):
    """Generate AI images based on script and voiceover"""
    job_id = str(uuid.uuid4())
    
    # Create job record in memory
    jobs_db[job_id] = {
        "job_id": job_id,
        "job_type": "ai_image_generation",
        "status": "pending",
        "message": "Job created successfully",
        "created_at": datetime.now(),
        "progress": 0,
        "result_url": None
    }
    
    return JobResponse(
        job_id=job_id,
        status="pending",
        message="Job created successfully",
        created_at=datetime.now(),
        progress=0
    )

@app.get("/api/jobs/{job_id}", response_model=JobResponse)
async def get_job_status_endpoint(job_id: str):
    """Get job status"""
    job = jobs_db.get(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    
    return JobResponse(
        job_id=job["job_id"],
        status=job["status"],
        message=job["message"],
        created_at=job["created_at"],
        progress=job["progress"],
        result_url=job["result_url"]
    )

@app.get("/api/files")
async def list_files():
    """List uploaded files"""
    return list(files_db.values())

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