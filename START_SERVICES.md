# How to Fix "Failed to start generation" Error

## The Problem
The application uses Celery + Redis for background job processing. If these services aren't running, you'll get "Failed to start generation" error.

## Solution 1: Start Required Services (Recommended)

### 1. Install Redis
- Download Redis for Windows from: https://github.com/microsoftarchive/redis/releases
- Or use WSL: `sudo apt-get install redis-server`

### 2. Start Redis
```bash
# If using Windows Redis:
redis-server

# If using WSL:
sudo service redis-server start
```

### 3. Start Celery Worker
Open a new terminal in the project directory and run:
```bash
celery -A celery_app worker --loglevel=info
```

### 4. Keep Both Running
You need to keep both Redis and Celery running while using the app.

## Solution 2: Quick Test Without Celery

For testing purposes, I'll create a version that runs synchronously without Celery:

1. Set your OpenAI API key first (visit http://localhost:8080/set_api_key.html)
2. Use the debug tool at http://localhost:8080/debug_generation_error.html to test

## What's Happening

The error flow:
1. You click "Generate Images"
2. Backend tries to queue a Celery task
3. Celery can't connect to Redis
4. Error: "Failed to start generation"

The fix is to ensure Redis and Celery are running before using the image generation feature.