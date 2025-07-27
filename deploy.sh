#!/bin/bash

# Deploy to Render - Helper Script

echo "🚀 Preparing for Render deployment..."

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "❌ Git repository not found. Please initialize git first:"
    echo "   git init"
    echo "   git add ."
    echo "   git commit -m 'Initial commit'"
    exit 1
fi

# Check if remote is set
if ! git remote get-url origin > /dev/null 2>&1; then
    echo "❌ No GitHub remote found. Please add your GitHub repository:"
    echo "   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git"
    exit 1
fi

# Check if all required files exist
required_files=("main_simple.py" "requirements-deploy.txt" "render.yaml" "core/" "static/")
missing_files=()

for file in "${required_files[@]}"; do
    if [ ! -e "$file" ]; then
        missing_files+=("$file")
    fi
done

if [ ${#missing_files[@]} -ne 0 ]; then
    echo "❌ Missing required files for deployment:"
    for file in "${missing_files[@]}"; do
        echo "   - $file"
    done
    exit 1
fi

echo "✅ All required files found"

# Push to GitHub
echo "📤 Pushing to GitHub..."
git add .
git commit -m "Deploy to Render - $(date)"
git push origin main

echo ""
echo "🎉 Code pushed to GitHub!"
echo ""
echo "📋 Next steps:"
echo "1. Go to https://dashboard.render.com"
echo "2. Click 'New +' → 'Web Service'"
echo "3. Connect your GitHub repository"
echo "4. Configure:"
echo "   - Name: ai-video-tool"
echo "   - Build Command: pip install -r requirements-deploy.txt"
echo "   - Start Command: uvicorn main_simple:app --host 0.0.0.0 --port \$PORT"
echo "   - Health Check Path: /health"
echo "5. Add environment variable:"
echo "   - Key: OPENAI_API_KEY"
echo "   - Value: Your OpenAI API key"
echo "6. Click 'Create Web Service'"
echo ""
echo "🔗 Your app will be available at: https://ai-video-tool.onrender.com" 