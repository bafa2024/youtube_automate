# B-Roll Reorganization Fix and Test Guide

## Summary of Changes

### 1. **Fixed Download URL Generation**
- Updated `main.py` to generate proper download URLs using `/api/files/serve/` endpoint
- Fixed both `/api/jobs/{job_id}` and `/api/jobs` endpoints
- Now returns URLs like `/api/files/serve/outputs/job-id/broll_reorganized.mp4`

### 2. **Added Progress Starting Popup**
- Added modal in `index.html` for immediate user feedback
- Shows animated progress with status messages
- Automatically closes when server responds

### 3. **Restored Proper Validation**
- Removed test mode code
- Requires at least one B-roll clip to be uploaded
- Proper error handling throughout

## Prerequisites

### 1. **Check FFmpeg Installation**
```bash
python test_ffmpeg.py
```

If FFmpeg is not installed:
- **Windows**: Download from https://ffmpeg.org/download.html
- **Mac**: `brew install ffmpeg`
- **Linux**: `sudo apt-get install ffmpeg`

### 2. **Start Required Services**

#### Backend Services:
```bash
# Terminal 1: Start Redis
redis-server

# Terminal 2: Start Celery Worker
celery -A celery_app worker --loglevel=info

# Terminal 3: Start FastAPI Server
python main.py
```

#### Or use the batch file:
```bash
start_server.bat
```

## Testing Steps

### 1. **Access the Application**
Open browser to: http://localhost:8080/static/index.html

### 2. **Navigate to B-Roll Reorganizer**
Click on the "B-Roll Reorganizer" tab

### 3. **Upload Test Files**

#### Create Test Videos (if needed):
```bash
# Create test B-roll clips using FFmpeg
ffmpeg -f lavfi -i testsrc=duration=5:size=640x480:rate=30 -pix_fmt yuv420p test_broll1.mp4
ffmpeg -f lavfi -i testsrc2=duration=5:size=640x480:rate=30 -pix_fmt yuv420p test_broll2.mp4
ffmpeg -f lavfi -i mandelbrot=size=640x480:rate=30 -t 5 -pix_fmt yuv420p test_broll3.mp4
```

#### Upload Process:
1. Click or drag files to "Upload B-Roll Clips" area
2. Upload at least 2-3 test video files
3. Optionally upload intro clips
4. Optionally upload a voiceover audio file

### 4. **Test B-Roll Organization**

1. **Click "Reorganize B-Roll" button**
   - You should see the progress starting popup immediately
   - Popup shows: "Starting B-Roll Organization"
   - Progress animates through stages

2. **Monitor Progress**
   - Starting popup closes after ~1.6 seconds
   - Main progress bar appears in the sidebar
   - Progress updates every 2 seconds
   - Status messages show current operation

3. **Completion**
   - Progress reaches 100%
   - Success notification appears
   - Download button should appear

### 5. **Download and Verify**

1. Click the download button when it appears
2. Video should download as `broll_reorganized.mp4` or `broll_with_voiceover.mp4`
3. Open the video to verify:
   - All clips are concatenated
   - If voiceover was provided, audio is overlaid
   - Video plays correctly

## Expected Behavior

### Progress Popup Sequence:
1. "Initializing..." (0%)
2. "Validating uploaded files..." (20%)
3. "Preparing server request..." (50%)
4. "Starting processing..." (80%)
5. "Job started successfully!" (100%)
6. Popup closes automatically

### Main Progress Updates:
- "Job queued successfully. Processing..." (10%)
- "Processing video clips..." (30-80%)
- "Overlaying voiceover..." (85%) - if audio provided
- "B-roll reorganization completed!" (100%)

## Troubleshooting

### Issue: "FFmpeg not found"
- Install FFmpeg following the prerequisites
- Ensure FFmpeg is in your system PATH
- Restart the server after installation

### Issue: No download button appears
1. Check browser console for errors
2. Check server logs for FFmpeg errors
3. Verify the output directory exists: `outputs/`
4. Check job status in "My Jobs" tab

### Issue: Video won't play
- Try a different video player
- Check if the video file size is > 0
- Look for FFmpeg errors in server logs

### Issue: Progress stuck
1. Check if Celery worker is running
2. Check Redis connection
3. Look for errors in Celery worker logs
4. Try canceling and restarting the job

## Server Logs to Check

### FastAPI Server:
Look for:
- "B-roll organization started"
- FFmpeg commands being executed
- File paths being processed

### Celery Worker:
Look for:
- Task received messages
- Progress updates
- FFmpeg output
- Completion or error messages

## Success Indicators

✅ Progress popup appears immediately when clicking button
✅ Progress updates smoothly in the sidebar
✅ Download button appears after completion
✅ Downloaded video plays correctly
✅ All uploaded clips are included in the output
✅ Voiceover is properly synced (if provided)

## API Endpoints Used

- `POST /api/upload/video` - Upload video clips
- `POST /api/upload/audio` - Upload voiceover
- `POST /api/generate/broll` - Start B-roll organization
- `GET /api/jobs/{job_id}` - Check job status
- `GET /api/files/serve/{path}` - Download results

## Notes

- Videos are processed without re-encoding for speed (using `-c copy`)
- Output videos are stored in `outputs/{job_id}/`
- Files are automatically cleaned up after retention period
- Multiple B-roll jobs can run concurrently