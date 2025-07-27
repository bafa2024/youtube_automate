#!/bin/bash

# B-Roll Organizer Deployment Script
# This script helps deploy the application to various platforms

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if required files exist
print_status "Checking required files..."

required_files=("main.py" "requirements-deploy.txt" "render.yaml" "core/" "static/")

for file in "${required_files[@]}"; do
    if [ ! -e "$file" ]; then
        print_error "Required file/directory not found: $file"
        exit 1
    fi
done

print_success "All required files found!"

# Function to deploy to Render
deploy_render() {
    print_status "Deploying to Render..."
    
    # Check if git is initialized
    if [ ! -d ".git" ]; then
        print_error "Git repository not initialized. Please run 'git init' first."
        exit 1
    fi
    
    # Check if remote origin exists
    if ! git remote get-url origin > /dev/null 2>&1; then
        print_error "Git remote 'origin' not found. Please add your GitHub repository."
        exit 1
    fi
    
    # Push to GitHub
    print_status "Pushing to GitHub..."
    git add .
    git commit -m "Deploy to Render - $(date)"
    git push origin main
    
    print_success "Code pushed to GitHub!"
    print_status "Now go to Render dashboard and deploy from your repository."
    print_status "Use these settings:"
    echo "   - Build Command: pip install -r requirements-deploy.txt"
    echo "   - Start Command: uvicorn main:app --host 0.0.0.0 --port \$PORT"
    echo "   - Health Check Path: /"
}

# Function to deploy to Heroku
deploy_heroku() {
    print_status "Deploying to Heroku..."
    
    # Check if Heroku CLI is installed
    if ! command -v heroku &> /dev/null; then
        print_error "Heroku CLI not found. Please install it first."
        exit 1
    fi
    
    # Create Procfile if it doesn't exist
    if [ ! -f "Procfile" ]; then
        echo "web: uvicorn main:app --host 0.0.0.0 --port \$PORT" > Procfile
        print_status "Created Procfile"
    fi
    
    # Deploy to Heroku
    heroku create
    git add .
    git commit -m "Deploy to Heroku"
    git push heroku main
    
    print_success "Deployed to Heroku!"
}

# Function to deploy to Railway
deploy_railway() {
    print_status "Deploying to Railway..."
    
    # Check if Railway CLI is installed
    if ! command -v railway &> /dev/null; then
        print_error "Railway CLI not found. Please install it first."
        exit 1
    fi
    
    # Deploy to Railway
    railway login
    railway init
    railway up
    
    print_success "Deployed to Railway!"
}

# Main script
case "${1:-render}" in
    "render")
        deploy_render
        ;;
    "heroku")
        deploy_heroku
        ;;
    "railway")
        deploy_railway
        ;;
    *)
        print_error "Unknown deployment target: $1"
        echo "Usage: $0 [render|heroku|railway]"
        exit 1
        ;;
esac 