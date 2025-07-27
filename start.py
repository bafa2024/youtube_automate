#!/usr/bin/env python3
"""
Start script for B-Roll Organizer
This script ensures the correct app is started regardless of Render configuration
"""
import uvicorn
import os

if __name__ == "__main__":
    # Get port from environment or default to 8080
    port = int(os.environ.get("PORT", 8080))
    
    # Start the FastAPI application
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=False
    ) 