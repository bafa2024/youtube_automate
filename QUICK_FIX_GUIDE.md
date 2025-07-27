# Quick Fix for "Failed to start generation" Error

## The Problem
The original app requires Redis + Celery for background job processing, which aren't running.

## The Solution
I've created a simplified version that works without these dependencies.

## Steps to Fix:

### 1. Stop the Current Server
Press `Ctrl+C` in the terminal where the server is running

### 2. Run the Simplified Version
```bash
python main_simple.py
```

Or double-click `run_simple.bat`

### 3. Use the App Normally
- Go to http://localhost:8080/static/index.html
- Your API key should already be set (check with the API Key button)
- Upload a script and audio file
- Click "Generate AI Images"
- It should work now!

## What's Different?

**Original main.py**:
- Uses Redis + Celery for background tasks
- Requires additional services running
- More complex but scalable

**New main_simple.py**:
- Uses FastAPI's built-in background tasks
- No external dependencies needed
- Simpler but less scalable
- Perfect for testing and development

## Testing the Fix

1. Make sure you see "AI Video Tool API (Simple Mode)" in the terminal
2. The API key you already set will be automatically loaded
3. Try generating a single image first to test
4. Check the terminal for any error messages

## If It Still Doesn't Work

Check that:
1. Your API key is valid (not expired or revoked)
2. You have internet connection (for OpenAI API)
3. The terminal shows no error messages
4. Your OpenAI account has credits

The simplified version should work immediately without needing Redis or Celery!