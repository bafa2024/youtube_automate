# 🚀 Render Deployment Checklist

## ✅ Pre-Deployment Checklist

### 1. **Code Preparation**
- [ ] `main_simple.py` is working locally
- [ ] `requirements-deploy.txt` contains all dependencies
- [ ] `render.yaml` is configured correctly
- [ ] `/health` endpoint is added to main_simple.py
- [ ] All core modules are present (`core/` folder)
- [ ] Static files are present (`static/` folder)

### 2. **GitHub Repository**
- [ ] Code is pushed to GitHub
- [ ] Repository is public (or Render has access)
- [ ] All files are committed and pushed

### 3. **OpenAI API Key**
- [ ] You have a valid OpenAI API key
- [ ] API key has credits
- [ ] API key is ready to add to Render environment variables

## 🎯 Quick Deploy Steps

### Step 1: Push to GitHub
```bash
git add .
git commit -m "Ready for Render deployment"
git push origin main
```

### Step 2: Deploy on Render
1. Go to https://dashboard.render.com
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Configure:
   - **Name:** `ai-video-tool`
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements-deploy.txt`
   - **Start Command:** `uvicorn main_simple:app --host 0.0.0.0 --port $PORT`
   - **Health Check Path:** `/health`

### Step 3: Set Environment Variables
- Go to "Environment" tab
- Add: `OPENAI_API_KEY` = your actual API key
- Mark as "Secret"

### Step 4: Deploy
- Click "Create Web Service"
- Wait 5-10 minutes for build

## 🔍 Post-Deployment Tests

### Test 1: Health Check
```
https://your-app.onrender.com/health
```
Expected: `{"status": "healthy", "message": "AI Video Tool API is running"}`

### Test 2: API Key Setup
```
https://your-app.onrender.com/set_api_key.html
```
Expected: API key setup page loads

### Test 3: Main App
```
https://your-app.onrender.com/static/index.html
```
Expected: Main application loads

### Test 4: Image Generation
1. Upload a script file
2. Upload an audio file
3. Set image count to 1
4. Click "Generate AI Images"
5. Should start generating images

## 🚨 Troubleshooting

### Build Fails
- Check `requirements-deploy.txt` has all dependencies
- Ensure Python version is 3.11+
- Check Render logs for specific errors

### App Won't Start
- Verify `main_simple.py` has no syntax errors
- Check all imports are available
- Ensure `/health` endpoint exists

### API Key Issues
- Make sure `OPENAI_API_KEY` is set in environment variables
- Verify the key is valid and has credits
- Test locally first with `python test_image_generation.py`

### File Upload Issues
- Render has read-only filesystem
- Consider using external storage for production
- For testing, files are stored temporarily

## 📊 Monitoring

### Check Logs
- Go to your service in Render dashboard
- Click "Logs" tab
- Look for error messages

### Health Monitoring
- Render automatically checks `/health` endpoint
- Service will restart if health check fails

## 💰 Cost Information

### Free Tier
- 750 hours/month
- Sleeps after 15 minutes of inactivity
- Perfect for testing

### Paid Plans
- $7/month for always-on service
- Better performance and reliability

## 🎉 Success Indicators

✅ **Deployment Successful When:**
- Build completes without errors
- Health check returns 200 OK
- Main app loads in browser
- Image generation works
- API key setup page is accessible

Your app is now live and ready to use! 🚀 