# OpenAI API Key Setup Guide

## The Problem
You're getting "Failed to start generation" error because the OpenAI API key is not set or is invalid.

## Solution: Set Your OpenAI API Key

### Step 1: Get an OpenAI API Key
1. Go to https://platform.openai.com/api-keys
2. Sign in to your OpenAI account (or create one if you don't have it)
3. Click "Create new secret key"
4. Give it a name like "AI Video Tool"
5. Copy the key (it starts with `sk-`)

### Step 2: Set the API Key in the App

**Option A: Using the Web Interface (Recommended)**
1. Go to http://localhost:8082/set_api_key.html
2. Paste your API key in the text box
3. Click "Save API Key"
4. You should see "API key saved successfully!"

**Option B: Manual Setup**
1. Create a file called `api_key.txt` in the project directory
2. Put your API key in it (just the key, no extra text)
3. Save the file

### Step 3: Test the Setup
1. Go to http://localhost:8082/static/index.html
2. Upload a script file (any text file)
3. Upload an audio file (any audio file)
4. Click "Generate AI Images"
5. It should work now!

## Troubleshooting

### If you still get "Failed to start generation":
1. **Check API key format**: Should start with `sk-` and be about 50 characters long
2. **Check API key validity**: Make sure it's not expired or revoked
3. **Check internet connection**: You need internet for OpenAI API calls
4. **Check OpenAI credits**: Make sure your account has credits

### If the server won't start:
1. Make sure no other process is using port 8082
2. Try running: `python main_simple.py`
3. Check the terminal for error messages

### If image generation fails:
1. Check the terminal for detailed error messages
2. Make sure your OpenAI account has credits
3. Try generating just 1 image first to test

## Quick Test
Run this command to test your API key:
```bash
python test_image_generation.py
```

If it shows "✅ OpenAI connection successful", your API key is working!

## Cost Information
- Each image generation costs about $0.04-0.08
- You can generate 1-20 images per request
- Monitor your usage at https://platform.openai.com/usage