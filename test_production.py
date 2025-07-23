#!/usr/bin/env python3
"""
Test script for production deployment
"""

import asyncio
import sys
from pathlib import Path

def test_imports():
    """Test all required imports"""
    print("Testing imports...")
    
    try:
        import fastapi
        print("✓ FastAPI imported successfully")
    except ImportError as e:
        print(f"✗ FastAPI import failed: {e}")
        return False
    
    try:
        import uvicorn
        print("✓ Uvicorn imported successfully")
    except ImportError as e:
        print(f"✗ Uvicorn import failed: {e}")
        return False
    
    try:
        import aiofiles
        print("✓ aiofiles imported successfully")
    except ImportError as e:
        print(f"✗ aiofiles import failed: {e}")
        return False
    
    try:
        import sqlalchemy
        print("✓ SQLAlchemy imported successfully")
    except ImportError as e:
        print(f"✗ SQLAlchemy import failed: {e}")
        return False
    
    try:
        import aiosqlite
        print("✓ aiosqlite imported successfully")
    except ImportError as e:
        print(f"✗ aiosqlite import failed: {e}")
        return False
    
    try:
        import pydantic
        print("✓ Pydantic imported successfully")
    except ImportError as e:
        print(f"✗ Pydantic import failed: {e}")
        return False
    
    try:
        import moviepy
        print("✓ MoviePy imported successfully")
    except ImportError as e:
        print(f"✗ MoviePy import failed: {e}")
        return False
    
    try:
        import openai
        print("✓ OpenAI imported successfully")
    except ImportError as e:
        print(f"✗ OpenAI import failed: {e}")
        return False
    
    return True

def test_config():
    """Test configuration loading"""
    print("\nTesting configuration...")
    
    try:
        from config import settings
        print("✓ Configuration loaded successfully")
        print(f"  - Upload directory: {settings.UPLOAD_DIR}")
        print(f"  - Output directory: {settings.OUTPUT_DIR}")
        print(f"  - Database URL: {settings.DATABASE_URL}")
        return True
    except Exception as e:
        print(f"✗ Configuration loading failed: {e}")
        return False

def test_directories():
    """Test directory creation"""
    print("\nTesting directory creation...")
    
    try:
        from config import settings
        from pathlib import Path
        
        # Test directory creation
        upload_path = Path(settings.UPLOAD_DIR)
        output_path = Path(settings.OUTPUT_DIR)
        temp_path = Path(settings.TEMP_DIR)
        
        upload_path.mkdir(parents=True, exist_ok=True)
        output_path.mkdir(parents=True, exist_ok=True)
        temp_path.mkdir(parents=True, exist_ok=True)
        
        print("✓ Directories created successfully")
        print(f"  - Upload: {upload_path.absolute()}")
        print(f"  - Output: {output_path.absolute()}")
        print(f"  - Temp: {temp_path.absolute()}")
        return True
    except Exception as e:
        print(f"✗ Directory creation failed: {e}")
        return False

def test_app_creation():
    """Test FastAPI app creation"""
    print("\nTesting FastAPI app creation...")
    
    try:
        # Import the production app
        from main_prod import app
        
        print("✓ FastAPI app created successfully")
        print(f"  - Title: {app.title}")
        print(f"  - Version: {app.version}")
        
        # Test health endpoint
        from fastapi.testclient import TestClient
        client = TestClient(app)
        response = client.get("/health")
        
        if response.status_code == 200:
            print("✓ Health endpoint working")
            print(f"  - Response: {response.json()}")
        else:
            print(f"✗ Health endpoint failed: {response.status_code}")
            return False
        
        return True
    except Exception as e:
        print(f"✗ App creation failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Production Deployment Test")
    print("=" * 40)
    
    tests = [
        test_imports,
        test_config,
        test_directories,
        test_app_creation
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        else:
            print(f"\n❌ Test failed: {test.__name__}")
            break
    
    print("\n" + "=" * 40)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Ready for deployment.")
        return 0
    else:
        print("❌ Some tests failed. Please fix issues before deployment.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 