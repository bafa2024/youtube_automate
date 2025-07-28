#!/usr/bin/env python3
"""
Development startup script for AI Video Tool
Runs the FastAPI application on port 8080
"""

import uvicorn
import os
import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

if __name__ == "__main__":
    print("Starting AI Video Tool on port 8080...")
    print("Web interface: http://localhost:8080")
    print("API docs: http://localhost:8080/docs")
    print("Health check: http://localhost:8080/health")
    print("\nPress Ctrl+C to stop the server\n")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
        log_level="info"
    ) 