# Render Deployment Guide

## Quick Deploy to Render

### Option 1: Using render.yaml (Recommended)
1. Push your code to GitHub
2. Connect your repository to Render
3. Render will automatically detect the `render.yaml` file and deploy

### Option 2: Manual Setup
1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Configure:
   - **Name**: yt-automation-web
   - **Environment**: Python
   - **Build Command**: `pip install -r requirements-minimal.txt`
   - **Start Command**: `uvicorn main_minimal:app --host 0.0.0.0 --port $PORT`
   - **Plan**: Starter (or higher for more resources)

## Environment Variables
Add these in your Render service settings:
- `PYTHON_VERSION`: `3.13.0`
- `PORT`: `8000` (Render sets this automatically)
- `OPENAI_API_KEY`: Your OpenAI API key (when ready to add AI features)
- Any other environment variables your app needs

## Deployment Strategy

### Phase 1: Minimal Deployment (Current)
- Uses `main_minimal.py` and `requirements-minimal.txt`
- No database dependencies (uses in-memory storage)
- Basic file upload and health check functionality
- Fast deployment for testing

### Phase 2: Full Features (Future)
- Switch to `main_prod.py` and `requirements-prod.txt`
- Add database and authentication
- Full AI video processing features

## Troubleshooting

### Common Issues:

1. **Package Download Failures**
   - Solution: Using minimal requirements with pinned versions
   - Reduced dependencies for faster builds

2. **Python Version Issues**
   - Ensure `PYTHON_VERSION=3.13.0` is set
   - Compatible with current Python 3.13

3. **Build Timeouts**
   - Use the starter plan or higher
   - Minimal requirements reduce build time

4. **Memory Issues**
   - Upgrade to a paid plan for more memory
   - Video processing requires significant memory

### Health Check
Your app includes a health endpoint at `/health` that Render uses to verify the service is running.

### Logs
Check the logs in Render dashboard for detailed error information.

## Testing Locally
Run the test script to verify everything works:
```bash
python test_minimal.py
```

## Performance Tips
- Use the minimal requirements file for faster builds
- The `.dockerignore` file reduces build context size
- Consider using a paid plan for video processing workloads
- Start with minimal deployment, then upgrade to full features 