# Deploy to Render Cloud - Complete Guide

## 🚀 Quick Deploy to Render

### Step 1: Prepare Your Repository

1. **Push your code to GitHub:**
   ```bash
   git add .
   git commit -m "Ready for Render deployment"
   git push origin main
   ```

2. **Make sure these files are in your repository:**
   - `main_simple.py` (main application)
   - `requirements.txt` (dependencies)
   - `render.yaml` (deployment config)
   - `core/` folder (all core modules)
   - `static/` folder (frontend files)
   - `db_utils.py`, `config.py` (database and config)

### Step 2: Deploy to Render

1. **Go to Render Dashboard:**
   - Visit https://dashboard.render.com
   - Sign up/Login with your GitHub account

2. **Create New Web Service:**
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Select your repository

3. **Configure the Service:**
   - **Name:** `ai-video-tool` (or your preferred name)
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn main_simple:app --host 0.0.0.0 --port $PORT`
   - **Health Check Path:** `/health`

4. **Set Environment Variables:**
   - Click "Environment" tab
   - Add your OpenAI API key:
     - **Key:** `OPENAI_API_KEY`
     - **Value:** Your actual OpenAI API key (sk-...)
   - Make sure it's marked as "Secret"

5. **Deploy:**
   - Click "Create Web Service"
   - Wait for build to complete (5-10 minutes)

### Step 3: Access Your App

Once deployed, you'll get a URL like:
```
https://ai-video-tool.onrender.com
```

**Your app endpoints:**
- Main app: `https://ai-video-tool.onrender.com/static/index.html`
- API key setup: `https://ai-video-tool.onrender.com/set_api_key.html`
- Health check: `https://ai-video-tool.onrender.com/health`

## 🔧 Configuration Files

### render.yaml (Auto-deploy)
```yaml
services:
  - type: web
    name: ai-video-tool
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn main_simple:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.0
      - key: OPENAI_API_KEY
        sync: false
    healthCheckPath: /health
    autoDeploy: true
```

### requirements.txt (Dependencies)
```
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-multipart==0.0.6
aiofiles==23.2.0
requests==2.31.0
pydantic==2.5.0
python-dotenv==1.0.0
```

## 🌐 Environment Variables

**Required:**
- `OPENAI_API_KEY` - Your OpenAI API key (set in Render dashboard)

**Optional:**
- `PORT` - Render sets this automatically
- `DATABASE_URL` - For persistent storage (if needed)

## 📁 File Structure for Deployment

```
your-repo/
├── main_simple.py          # Main application
├── requirements.txt         # Python dependencies
├── render.yaml            # Render deployment config
├── core/                  # Core modules
│   ├── openai_generator.py
│   ├── api_manager.py
│   └── ...
├── static/                # Frontend files
│   ├── index.html
│   └── app.js
├── db_utils.py           # Database utilities
├── config.py             # Configuration
└── README.md
```

## 🔍 Troubleshooting

### Common Issues:

1. **Build Fails:**
   - Check `requirements.txt` has all dependencies
   - Ensure Python version is compatible (3.11+)

2. **App Won't Start:**
   - Check logs in Render dashboard
   - Verify `main_simple.py` has no syntax errors
   - Ensure all imports are available

3. **API Key Issues:**
   - Make sure `OPENAI_API_KEY` is set in environment variables
   - Check the key is valid and has credits

4. **File Upload Issues:**
   - Render has read-only filesystem
   - Consider using external storage (S3, etc.) for production

### Check Logs:
- Go to your service in Render dashboard
- Click "Logs" tab
- Look for error messages

## 🚀 Production Considerations

### For Production Use:

1. **Database:**
   - Add PostgreSQL service in Render
   - Update `DATABASE_URL` environment variable

2. **File Storage:**
   - Use AWS S3 or similar for file uploads
   - Render has ephemeral filesystem

3. **Security:**
   - Add authentication
   - Rate limiting
   - CORS configuration

4. **Monitoring:**
   - Set up logging
   - Add error tracking (Sentry)

## 💰 Cost Information

**Render Free Tier:**
- 750 hours/month
- Sleeps after 15 minutes of inactivity
- Perfect for testing and small projects

**Render Paid Plans:**
- $7/month for always-on service
- Better performance and reliability

## 🎯 Quick Test After Deployment

1. **Test Health Check:**
   ```
   https://your-app.onrender.com/health
   ```

2. **Test API Key Setup:**
   ```
   https://your-app.onrender.com/set_api_key.html
   ```

3. **Test Main App:**
   ```
   https://your-app.onrender.com/static/index.html
   ```

## 📞 Support

If you encounter issues:
1. Check Render logs
2. Verify all files are committed to GitHub
3. Ensure environment variables are set correctly
4. Test locally first with `python main_simple.py`

Your app should be live and ready to use! 🎉 