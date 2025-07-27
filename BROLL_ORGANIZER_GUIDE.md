# B-Roll Organizer - Complete Guide

## Overview

The B-Roll Organizer is a powerful feature that allows you to upload, organize, and combine multiple video clips with optional voiceover audio. It's perfect for content creators who want to create dynamic videos from multiple footage sources.

## Features

### 🎬 Video Management
- **Upload Multiple Video Clips**: Support for .mp4, .avi, .mov, .mkv formats
- **Intro Clips**: Designate specific clips to play at the beginning
- **B-Roll Clips**: Main footage that gets shuffled and organized
- **Automatic Shuffling**: Randomize the order of B-roll clips for variety

### 🎧 Audio Integration
- **Voiceover Support**: Upload .mp3, .wav, .m4a audio files
- **Duration Synchronization**: Sync video length to voiceover duration
- **Audio Overlay**: Automatically overlay voiceover on the final video
- **Audio Processing**: Normalization, fade effects, and format conversion

### ⚙️ Advanced Options
- **Duration Control**: Match video length to voiceover or let it run naturally
- **Quality Settings**: High-quality video processing with FFmpeg
- **Progress Tracking**: Real-time progress updates during processing
- **Job Management**: Track and manage multiple organization jobs

## How to Use

### 1. Access the B-Roll Organizer

1. Open the web application
2. Click on the "B-Roll Reorganizer" tab
3. You'll see three main sections:
   - Upload B-Roll Clips
   - Upload Intro Clips (Optional)
   - Upload Voiceover (Optional)

### 2. Upload Your Content

#### B-Roll Clips (Required)
- Click on the B-Roll dropzone or drag files directly
- Select multiple video files (.mp4, .avi, .mov, .mkv)
- These clips will be shuffled and combined
- You can remove individual clips by clicking the X button

#### Intro Clips (Optional)
- Upload clips that should play at the beginning
- These clips will play in order before the B-roll
- Useful for title sequences or introductions

#### Voiceover (Optional)
- Upload an audio file (.mp3, .wav, .m4a)
- This will be overlaid on the final video
- The video duration can be synced to match the audio length

### 3. Configure Settings

#### Organization Settings
- **Sync video to voiceover length**: When enabled, the final video will match the voiceover duration
- **Overlay voiceover on final video**: When enabled, the voiceover will be mixed with the video audio

### 4. Start Organization

1. Click the "Reorganize B-Roll" button
2. The system will:
   - Shuffle your B-roll clips randomly
   - Combine intro clips + shuffled B-roll
   - Sync to voiceover duration (if enabled)
   - Overlay voiceover audio (if enabled)
   - Generate the final video

### 5. Monitor Progress

- Watch real-time progress updates
- See current processing status
- Get notified when the job completes

### 6. Download Results

- Once complete, download your organized video
- The final file will be in MP4 format
- Check the Jobs tab to see all your processing history

## Technical Details

### Video Processing Pipeline

1. **File Validation**: Check file formats and sizes
2. **Duration Analysis**: Get video and audio durations
3. **Clip Shuffling**: Randomize B-roll clip order
4. **Concatenation**: Combine all clips using FFmpeg
5. **Duration Sync**: Trim or extend to match voiceover (if enabled)
6. **Audio Overlay**: Mix voiceover with video audio (if enabled)
7. **Final Output**: Generate optimized MP4 file

### Supported Formats

#### Video Input
- **MP4** (.mp4) - Recommended
- **AVI** (.avi)
- **MOV** (.mov)
- **MKV** (.mkv)

#### Audio Input
- **MP3** (.mp3) - Recommended
- **WAV** (.wav)
- **M4A** (.m4a)

#### Output
- **MP4** (.mp4) - H.264 video, AAC audio

### Processing Options

#### Duration Synchronization
When "Sync to voiceover length" is enabled:
- The system calculates the total duration of all clips
- If longer than voiceover: clips are trimmed to fit
- If shorter than voiceover: clips are looped or extended
- Ensures perfect synchronization with voiceover

#### Audio Overlay
When "Overlay voiceover" is enabled:
- Voiceover is mixed with any existing video audio
- Audio levels are automatically balanced
- Final audio uses AAC codec for compatibility

## Best Practices

### File Preparation
1. **Use consistent formats**: MP4 for video, MP3 for audio
2. **Optimize file sizes**: Compress large files before upload
3. **Check audio quality**: Ensure voiceover is clear and normalized
4. **Plan your intro**: Keep intro clips short and engaging

### Organization Strategy
1. **Mix clip lengths**: Use varying durations for visual interest
2. **Consider transitions**: Plan how clips will flow together
3. **Test with voiceover**: Upload a test voiceover to check timing
4. **Backup originals**: Keep your source files safe

### Performance Tips
1. **Limit clip count**: 10-20 clips work best for most projects
2. **Use reasonable durations**: 3-10 seconds per clip is ideal
3. **Monitor file sizes**: Large files take longer to process
4. **Check progress**: Use the progress bar to monitor processing

## Troubleshooting

### Common Issues

#### Upload Problems
- **File too large**: Compress videos before upload
- **Unsupported format**: Convert to MP4/MOV/AVI/MKV
- **Upload fails**: Check internet connection and try again

#### Processing Issues
- **Job fails**: Check that all files are valid video/audio
- **No audio**: Ensure voiceover file is not corrupted
- **Wrong duration**: Verify voiceover length matches expectations

#### Quality Issues
- **Poor video quality**: Use higher resolution source files
- **Audio sync problems**: Check voiceover file format and quality
- **Large output files**: Consider using shorter clips or lower quality

### Error Messages

#### "No video clips found"
- Upload at least one B-roll clip
- Check that files are valid video formats

#### "Voiceover file not found"
- Upload a valid audio file
- Check file format (.mp3, .wav, .m4a)

#### "Processing failed"
- Check all uploaded files are valid
- Try with fewer clips or shorter durations
- Contact support if problem persists

## Advanced Features

### Batch Processing
- Upload multiple projects at once
- Each job is processed independently
- Monitor all jobs from the Jobs tab

### Job History
- View all previous organization jobs
- Download results from past projects
- Track processing times and success rates

### File Management
- Automatic cleanup of old files
- Secure file storage and access
- Backup and recovery options

## API Integration

The B-Roll Organizer also provides a REST API for programmatic access:

### Endpoints
- `POST /api/upload/video` - Upload video files
- `POST /api/upload/audio` - Upload audio files
- `POST /api/generate/broll` - Start organization job
- `GET /api/jobs/{job_id}` - Get job status
- `GET /api/download/{job_id}/{filename}` - Download results

### Example Usage
```bash
# Upload a video file
curl -X POST -F "file=@video.mp4" -F "video_type=broll" http://localhost:8080/api/upload/video

# Start organization
curl -X POST -H "Content-Type: application/json" \
  -d '{"broll_clip_ids":["file_id_1","file_id_2"],"voiceover_id":"audio_id","sync_to_voiceover":true}' \
  http://localhost:8080/api/generate/broll
```

## System Requirements

### Server Requirements
- **Python 3.8+**: For the web application
- **FFmpeg**: For video processing (automatically installed)
- **Storage**: Sufficient space for uploaded and processed files
- **Memory**: 2GB+ RAM for video processing

### Client Requirements
- **Modern Browser**: Chrome, Firefox, Safari, Edge
- **JavaScript Enabled**: Required for the web interface
- **Internet Connection**: For uploading and downloading files

## Performance Considerations

### Processing Speed
- **Small clips (1-5 seconds)**: ~30-60 seconds processing time
- **Medium clips (5-15 seconds)**: ~1-3 minutes processing time
- **Large clips (15+ seconds)**: ~3-10 minutes processing time
- **With voiceover sync**: Additional 30-60 seconds

### File Size Limits
- **Individual files**: Up to 500MB per file
- **Total project**: Up to 2GB per organization job
- **Output files**: Typically 50-200MB depending on quality

### Concurrent Jobs
- **Recommended**: 1-3 jobs at a time
- **Maximum**: 5 concurrent jobs
- **Queue system**: Additional jobs are queued automatically

## Support and Updates

### Getting Help
- Check this guide for common solutions
- Review the troubleshooting section
- Contact support for technical issues

### Updates and Improvements
- Regular feature updates
- Performance optimizations
- New format support
- Enhanced processing options

---

**Note**: The B-Roll Organizer is designed to be user-friendly while providing professional-grade video processing capabilities. For best results, follow the best practices outlined in this guide and ensure your source files are of good quality. 