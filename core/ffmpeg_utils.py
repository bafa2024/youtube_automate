"""
FFmpeg utility functions for cross-platform compatibility
"""
import os
import platform
import subprocess
import shutil
from pathlib import Path

def get_ffmpeg_path():
    """Get the correct FFmpeg executable path based on the platform"""
    system = platform.system().lower()
    
    # First, check if ffmpeg is in system PATH
    ffmpeg_in_path = shutil.which('ffmpeg')
    if ffmpeg_in_path:
        return 'ffmpeg'
    
    # For Windows, check local bin directory
    if system == 'windows':
        local_ffmpeg = Path('./bin/ffmpeg.exe')
        if local_ffmpeg.exists():
            return str(local_ffmpeg)
    
    # For Linux/Mac, check common locations
    common_paths = [
        '/usr/bin/ffmpeg',
        '/usr/local/bin/ffmpeg',
        '/opt/ffmpeg/bin/ffmpeg',
    ]
    
    for path in common_paths:
        if Path(path).exists():
            return path
    
    # Default to 'ffmpeg' and hope it's in PATH
    return 'ffmpeg'

def get_ffprobe_path():
    """Get the correct FFprobe executable path based on the platform"""
    system = platform.system().lower()
    
    # First, check if ffprobe is in system PATH
    ffprobe_in_path = shutil.which('ffprobe')
    if ffprobe_in_path:
        return 'ffprobe'
    
    # For Windows, check local bin directory
    if system == 'windows':
        local_ffprobe = Path('./bin/ffprobe.exe')
        if local_ffprobe.exists():
            return str(local_ffprobe)
    
    # For Linux/Mac, check common locations
    common_paths = [
        '/usr/bin/ffprobe',
        '/usr/local/bin/ffprobe',
        '/opt/ffmpeg/bin/ffprobe',
    ]
    
    for path in common_paths:
        if Path(path).exists():
            return path
    
    # Default to 'ffprobe' and hope it's in PATH
    return 'ffprobe'

def check_ffmpeg_installed():
    """Check if FFmpeg is properly installed and accessible"""
    try:
        ffmpeg = get_ffmpeg_path()
        result = subprocess.run([ffmpeg, '-version'], capture_output=True, text=True)
        return result.returncode == 0
    except Exception:
        return False

def check_ffprobe_installed():
    """Check if FFprobe is properly installed and accessible"""
    try:
        ffprobe = get_ffprobe_path()
        result = subprocess.run([ffprobe, '-version'], capture_output=True, text=True)
        return result.returncode == 0
    except Exception:
        return False