#!/bin/bash

# Install FFmpeg on Render
echo "Installing FFmpeg..."
if command -v apt-get &> /dev/null; then
    # For Ubuntu/Debian (Render uses Ubuntu)
    apt-get update
    apt-get install -y ffmpeg
elif command -v yum &> /dev/null; then
    # For RHEL/CentOS
    yum install -y ffmpeg
else
    echo "Warning: Could not install FFmpeg automatically"
fi

# Check if FFmpeg was installed successfully
if command -v ffmpeg &> /dev/null; then
    echo "FFmpeg installed successfully"
    ffmpeg -version
else
    echo "Warning: FFmpeg not found in PATH"
fi

# Install Python dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "Build complete!"