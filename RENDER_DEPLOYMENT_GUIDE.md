# Render Deployment Guide

This guide will help you deploy the B-Roll Organizer to Render successfully.

## Prerequisites

1. **Render Account**: Sign up at [render.com](https://render.com)
2. **GitHub Repository**: Your code should be pushed to GitHub
3. **API Keys**: You'll need to set up environment variables

## Deployment Steps

### 1. Connect Your Repository

1. Go to your Render dashboard
2. Click "New +" and select "Web Service"
3. Connect your GitHub repository
4. Select the repository: `bafa2024/youtube_automate`

### 2. Configure the Service

Use these settings:

- **Name**: `broll-organizer`
- **Environment**: `Python 3`
- **Build Command**: 
  ```bash
  pip install --upgrade pip
  pip install -r requirements-render.txt
  ```
- **Start Command**: 
  ```bash
  uvicorn main:app --host 0.0.0.0 --port $PORT
  ```

### 3. Environment Variables

Add these environment variables in Render:

- `OPENAI_API_KEY`: Your OpenAI API key
- `PORT`: `8080` (Render will override this)
- `PYTHON_VERSION`: `3.11.0`

### 4. Advanced Settings

- **Health Check Path**: `/`
- **Auto-Deploy**: Enabled
- **Plan**: Free

## Troubleshooting

### Common Issues

1. **Build Failures**
   - The updated `requirements-render.txt` uses newer, pre-compiled packages
   - If you still get Rust compilation errors, try using `requirements.txt` instead

2. **Port Issues**
   - Render automatically sets the `PORT` environment variable
   - The app listens on `0.0.0.0:$PORT`

3. **Missing Dependencies**
   - All required packages are in `requirements-render.txt`
   - The build command upgrades pip first

4. **FFmpeg Issues**
   - FFmpeg is not included in the deployment (large files)
   - For production, you'll need to install FFmpeg on the server
   - Consider using a service like AWS or Google Cloud for video processing

### Alternative Deployment

If you continue to have issues with Render, consider:

1. **Heroku**: Similar deployment process
2. **Railway**: Good for Python apps
3. **DigitalOcean App Platform**: More control over the environment

## Local Testing

Before deploying, test locally:

```bash
# Install dependencies
pip install -r requirements-render.txt

# Start the server
python main.py

# Test the application
curl http://localhost:8080/
```

## Production Considerations

1. **Video Processing**: Render's free tier has limitations for video processing
2. **File Storage**: Consider using cloud storage (AWS S3, Google Cloud Storage)
3. **Database**: For production, use a proper database service
4. **Scaling**: Monitor usage and upgrade plans as needed

## Support

If you encounter issues:

1. Check the Render logs in the dashboard
2. Verify all environment variables are set
3. Test the application locally first
4. Check the GitHub repository for the latest updates 