"""
Simplified version of main.py that works without Redis/Celery
For testing image generation without background tasks
"""
import os
import json
import uuid
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pydantic import BaseModel, Field

# Import core modules
from core.openai_generator import OpenAIImageGenerator
from core.api_manager import APIKeyManager
from core.video_processor import VideoProcessor
from core.audio_processor import AudioProcessor
from db_utils import init_db, create_job, get_job_by_id, update_job_status, create_file, get_file_by_id
from config import Settings

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = Settings()

# Simple in-memory job storage for testing
jobs_store = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up AI Video Tool API (Simple Mode)...")
    
    # Create necessary directories
    for dir_path in [settings.UPLOAD_DIR, settings.OUTPUT_DIR, settings.TEMP_DIR]:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    # Initialize database
    await init_db()
    
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
    logger.info("Shutting down...")

app = FastAPI(
    title="AI Video Tool API (Simple)",
    description="Simplified version without Redis/Celery",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Models
class JobResponse(BaseModel):
    job_id: str
    status: str
    message: str
    created_at: datetime
    progress: int = 0
    result_url: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    job_type: Optional[str] = None

class BRollOrganizationRequest(BaseModel):
    intro_clip_ids: List[str] = Field(default=[], description="List of intro clip UUIDs")
    broll_clip_ids: List[str] = Field(..., description="List of B-roll clip UUIDs")
    voiceover_id: Optional[str] = Field(None, description="Voiceover file UUID")
    sync_to_voiceover: bool = Field(True, description="Sync video to voiceover duration")
    overlay_audio: bool = Field(True, description="Overlay voiceover on final video")

async def save_upload_file(upload_file: UploadFile, subdirectory: str = "") -> dict:
    """Save uploaded file and return file info"""
    file_id = str(uuid.uuid4())
    file_extension = Path(upload_file.filename).suffix
    safe_filename = f"{file_id}{file_extension}"
    
    upload_dir = Path(settings.UPLOAD_DIR) / subdirectory
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = upload_dir / safe_filename
    
    # Save file
    content = await upload_file.read()
    with open(file_path, "wb") as f:
        f.write(content)
    
    return {
        "file_id": file_id,
        "filename": upload_file.filename,
        "saved_path": str(file_path),
        "size": len(content)
    }

# Root endpoint
@app.get("/")
async def root():
    """Serve the main application page"""
    return FileResponse("static/index.html")

@app.get("/health")
async def health_check():
    """Health check endpoint for Render"""
    return {"status": "healthy", "message": "AI Video Tool API is running"}

@app.get("/set_api_key.html")
async def set_api_key_page():
    """Serve the API key setup page"""
    return FileResponse("set_api_key.html")

@app.get("/api")
async def api_info():
    """API information endpoint"""
    return {
        "message": "AI Video Tool API (Simple Mode)",
        "version": "1.0.0",
        "endpoints": {
            "main_app": "/",
            "api_key_setup": "/set_api_key.html",
            "health_check": "/health",
            "upload_script": "/api/upload/script",
            "upload_audio": "/api/upload/audio",
            "generate_images": "/api/generate/ai-images",
            "check_api_key": "/api/check-api-key"
        }
    }

# API Key endpoints
@app.post("/api/settings/api-key")
async def set_api_key(api_key: str = Form(...)):
    """Set OpenAI API key"""
    try:
        os.environ['OPENAI_API_KEY'] = api_key
        api_key_file = Path("api_key.txt")
        api_key_file.write_text(api_key)
        return {"message": "API key set successfully"}
    except Exception as e:
        logger.error(f"API key storage error: {e}")
        raise HTTPException(500, "Failed to set API key")

@app.get("/api/check-api-key")
async def check_api_key():
    """Check if OpenAI API key is configured"""
    env_key = os.getenv('OPENAI_API_KEY')
    if env_key:
        return {"configured": True, "source": "environment"}
    
    api_key_file = Path("api_key.txt")
    if api_key_file.exists():
        try:
            stored_key = api_key_file.read_text().strip()
            if stored_key:
                os.environ['OPENAI_API_KEY'] = stored_key
                return {"configured": True, "source": "file"}
        except Exception as e:
            logger.error(f"Error reading API key file: {e}")
    
    return {"configured": False, "source": "none"}

# File upload endpoints
@app.post("/api/upload/script")
async def upload_script(file: UploadFile = File(...)):
    """Upload a script file"""
    if not file.filename.endswith(('.txt', '.docx')):
        raise HTTPException(400, "Only .txt and .docx files are supported")
    
    file_info = await save_upload_file(file, "scripts")
    
    # Store in database
    await create_file(
        user_id=None,
        file_id=file_info["file_id"],
        filename=file_info["filename"],
        file_type="script",
        file_path=file_info["saved_path"],
        size=file_info["size"]
    )
    
    return {"file_id": file_info["file_id"], "filename": file_info["filename"]}

@app.post("/api/upload/audio")
async def upload_audio(file: UploadFile = File(...)):
    """Upload an audio file"""
    if not file.filename.endswith(('.mp3', '.wav', '.m4a')):
        raise HTTPException(400, "Only .mp3, .wav, and .m4a files are supported")
    
    file_info = await save_upload_file(file, "audio")
    
    # Store in database
    await create_file(
        user_id=None,
        file_id=file_info["file_id"],
        filename=file_info["filename"],
        file_type="audio",
        file_path=file_info["saved_path"],
        size=file_info["size"]
    )
    
    return {"file_id": file_info["file_id"], "filename": file_info["filename"]}

@app.post("/api/upload/video")
async def upload_video(
    file: UploadFile = File(...),
    video_type: str = Form("broll", description="Type of video: 'broll' or 'intro'")
):
    """Upload a video file"""
    if not file.filename.endswith(('.mp4', '.avi', '.mov', '.mkv')):
        raise HTTPException(400, "Only .mp4, .avi, .mov, and .mkv files are supported")
    
    subdirectory = "videos" if video_type == "broll" else "intros"
    file_info = await save_upload_file(file, subdirectory)
    
    # Store in database
    await create_file(
        user_id=None,
        file_id=file_info["file_id"],
        filename=file_info["filename"],
        file_type=video_type,
        file_path=file_info["saved_path"],
        size=file_info["size"]
    )
    
    return {"file_id": file_info["file_id"], "filename": file_info["filename"]}

# Simplified image generation without Celery
async def generate_images_simple(job_id: str, params: dict):
    """Generate images synchronously"""
    try:
        # Update job status
        await update_job_status(job_id, "processing", "Starting image generation...", 10)
        
        # Get API key
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise Exception("API key not found")
        
        # Initialize generator
        generator = OpenAIImageGenerator(api_key)
        
        # Test connection
        if not generator.test_connection():
            raise Exception("Failed to connect to OpenAI API")
        
        await update_job_status(job_id, "processing", "Connected to OpenAI...", 20)
        
        # Read script
        script_text = params.get('script_text', 'Generate a beautiful image')
        
        # Create output directory
        output_dir = Path(settings.OUTPUT_DIR) / job_id
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate images
        generated_images = []
        image_count = params.get('image_count', 1)
        style = params.get('style', 'Photorealistic')
        character_desc = params.get('character_description', '')
        
        for i in range(image_count):
            progress = 20 + int((i / image_count) * 60)
            await update_job_status(job_id, "processing", f"Generating image {i+1} of {image_count}...", progress)
            
            # Create prompt
            prompt = f"{style} style. {character_desc}. {script_text}"
            if len(prompt) > 900:
                prompt = prompt[:900]
            
            # Generate image
            try:
                image_path = generator.generate_and_save_image(
                    prompt=prompt,
                    output_dir=str(output_dir),
                    filename=f"image_{i+1:03d}",
                    style=style
                )
                generated_images.append(image_path)
            except Exception as e:
                logger.error(f"Failed to generate image {i+1}: {e}")
                # Continue with other images
        
        # Update job as completed
        result_data = {
            "images": generated_images,
            "output_dir": str(output_dir)
        }
        
        await update_job_status(
            job_id, "completed", 
            f"Generated {len(generated_images)} images successfully!", 
            100, str(output_dir), result_data
        )
        
        # Update in-memory store
        jobs_store[job_id] = {
            "status": "completed",
            "result": result_data,
            "progress": 100
        }
        
    except Exception as e:
        logger.error(f"Image generation failed: {e}")
        await update_job_status(job_id, "failed", str(e), 0)
        jobs_store[job_id] = {"status": "failed", "error": str(e)}

# B-Roll organization function
async def organize_broll_simple(job_id: str, params: dict):
    """Organize B-roll clips synchronously"""
    try:
        # Update job status
        await update_job_status(job_id, "processing", "Starting B-roll reorganization...", 5)
        
        # Initialize processors
        video_proc = VideoProcessor()
        audio_proc = AudioProcessor()
        
        # Get file paths from database
        intro_paths = []
        for file_id in params['intro_clip_ids']:
            file_record = await get_file_by_id(file_id)
            if file_record:
                intro_paths.append(file_record['file_path'])
        
        broll_paths = []
        for file_id in params['broll_clip_ids']:
            file_record = await get_file_by_id(file_id)
            if file_record:
                broll_paths.append(file_record['file_path'])
        
        voiceover_path = None
        if params['voiceover_id']:
            voice_file = await get_file_by_id(params['voiceover_id'])
            if voice_file:
                voiceover_path = voice_file['file_path']
        
        # Create output directory
        output_dir = Path(settings.OUTPUT_DIR) / job_id
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Get target duration if syncing with voiceover
        target_duration = None
        if params['sync_to_voiceover'] and voiceover_path:
            await update_job_status(job_id, "processing", "Analyzing voiceover duration...", 10)
            try:
                target_duration = audio_proc.get_duration(voiceover_path)
            except Exception as e:
                logger.warning(f"Could not get voiceover duration: {e}")
        
        # Shuffle B-roll
        await update_job_status(job_id, "processing", "Shuffling B-roll clips...", 20)
        import random
        shuffled_broll = broll_paths.copy()
        random.shuffle(shuffled_broll)
        
        # Combine clips
        all_clips = intro_paths + shuffled_broll
        
        if not all_clips:
            raise Exception("No video clips found")
        
        # Create reorganized video
        await update_job_status(job_id, "processing", "Creating reorganized video...", 30)
        output_path = output_dir / 'broll_reorganized.mp4'
        
        # Progress callback for video processing
        async def video_progress(p):
            overall_progress = 30 + int(p * 50)  # 30-80%
            await update_job_status(job_id, "processing", "Processing video clips...", overall_progress)
        
        # Process video clips
        video_proc.concatenate_clips(
            all_clips, 
            str(output_path),
            target_duration=target_duration,
            progress_callback=lambda p: asyncio.create_task(video_progress(p))
        )
        
        results = {'video': str(output_path)}
        
        # Overlay audio if requested
        if params['overlay_audio'] and voiceover_path:
            await update_job_status(job_id, "processing", "Overlaying voiceover...", 85)
            final_path = output_dir / 'broll_with_voiceover.mp4'
            video_proc.add_audio_to_video(
                str(output_path), 
                voiceover_path, 
                str(final_path)
            )
            results['video_with_audio'] = str(final_path)
        
        # Update job as completed
        await update_job_status(
            job_id, "completed", 
            "B-roll reorganization completed!", 
            100, str(output_dir), results
        )
        
        # Update in-memory store
        jobs_store[job_id] = {
            "status": "completed",
            "result": results,
            "progress": 100
        }
        
    except Exception as e:
        logger.error(f"B-roll organization failed: {e}")
        await update_job_status(job_id, "failed", str(e), 0)
        jobs_store[job_id] = {"status": "failed", "error": str(e)}

@app.post("/api/generate/ai-images", response_model=JobResponse)
async def generate_ai_images(
    background_tasks: BackgroundTasks,
    script_file_id: str = Form(...),
    voice_file_id: str = Form(...),
    script_text: str = Form(None),
    image_count: int = Form(...),
    style: str = Form(...),
    character_description: str = Form(...),
    voice_duration: float = Form(...),
    export_options: str = Form(...),
):
    """Start AI image generation job"""
    logger.info(f"Received image generation request: images={image_count}, style={style}")
    
    try:
        # Check API key
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise HTTPException(400, "OpenAI API key not configured. Please set it in settings.")
        
        # Get files
        script_file = await get_file_by_id(script_file_id)
        voice_file = await get_file_by_id(voice_file_id)
        
        if not script_file or not voice_file:
            raise HTTPException(404, "Script or voice file not found")
        
        # Read script if not provided
        if not script_text:
            try:
                with open(script_file['file_path'], 'r', encoding='utf-8') as f:
                    script_text = f.read()
            except Exception:
                script_text = "Generate beautiful images"
        
        # Create job
        job_id = str(uuid.uuid4())
        created_at = datetime.now()
        
        await create_job(
            job_id=job_id,
            user_id=None,
            status="pending",
            message="AI image generation job started",
            created_at=created_at.isoformat(),
            progress=0,
            result_path=None,
            job_type="ai_image_generation"
        )
        
        # Start generation in background
        params = {
            "script_text": script_text,
            "image_count": image_count,
            "style": style,
            "character_description": character_description
        }
        
        background_tasks.add_task(generate_images_simple, job_id, params)
        
        return JobResponse(
            job_id=job_id,
            status="pending",
            message="AI image generation job started",
            created_at=created_at,
            progress=0,
            job_type="ai_image_generation"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start generation: {e}")
        raise HTTPException(500, f"Failed to start generation: {str(e)}")

@app.post("/api/generate/broll", response_model=JobResponse)
async def organize_broll(
    request: BRollOrganizationRequest,
    background_tasks: BackgroundTasks
):
    """Start B-roll organization job"""
    logger.info(f"Received B-roll organization request: {len(request.broll_clip_ids)} clips")
    
    try:
        # Validate that we have at least some video clips
        all_video_ids = request.intro_clip_ids + request.broll_clip_ids
        if not all_video_ids:
            raise HTTPException(400, "No video clips provided")
        
        # Create job
        job_id = str(uuid.uuid4())
        created_at = datetime.now()
        
        await create_job(
            job_id=job_id,
            user_id=None,
            status="pending",
            message="B-roll organization job started",
            created_at=created_at.isoformat(),
            progress=0,
            result_path=None,
            job_type="broll_organization"
        )
        
        # Start organization in background
        params = {
            "intro_clip_ids": request.intro_clip_ids,
            "broll_clip_ids": request.broll_clip_ids,
            "voiceover_id": request.voiceover_id,
            "sync_to_voiceover": request.sync_to_voiceover,
            "overlay_audio": request.overlay_audio
        }
        
        background_tasks.add_task(organize_broll_simple, job_id, params)
        
        return JobResponse(
            job_id=job_id,
            status="pending",
            message="B-roll organization job started",
            created_at=created_at,
            progress=0,
            job_type="broll_organization"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start B-roll organization: {e}")
        raise HTTPException(500, f"Failed to start B-roll organization: {str(e)}")

@app.get("/api/jobs/{job_id}", response_model=JobResponse)
async def get_job_status(job_id: str):
    """Get job status"""
    job = await get_job_by_id(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    
    # Parse result if exists
    result_data = None
    if job.get('result'):
        try:
            result_data = json.loads(job['result'])
        except Exception:
            pass
    
    return JobResponse(
        job_id=job['job_id'],
        status=job['status'],
        message=job['message'],
        created_at=job['created_at'],
        progress=job['progress'],
        result_url=job['result_path'],
        result=result_data,
        job_type=job.get('job_type')
    )

@app.get("/api/files/{file_id}/content")
async def get_file_content(file_id: str):
    """Get file content"""
    try:
        file_record = await get_file_by_id(file_id)
        if not file_record:
            raise HTTPException(404, "File not found")
        
        with open(file_record['file_path'], 'r', encoding='utf-8') as f:
            content = f.read()
        
        return JSONResponse(content={"content": content, "file_id": file_id})
    except Exception as e:
        raise HTTPException(500, f"Error reading file: {str(e)}")

@app.get("/api/files/serve/{file_path:path}")
async def serve_file(file_path: str):
    """Serve generated files"""
    full_path = Path(file_path)
    
    if not full_path.exists():
        raise HTTPException(404, "File not found")
    
    # Determine media type
    media_type = 'application/octet-stream'
    if full_path.suffix.lower() in ['.png', '.jpg', '.jpeg']:
        media_type = f'image/{full_path.suffix[1:]}'
    
    return FileResponse(full_path, media_type=media_type)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8082)