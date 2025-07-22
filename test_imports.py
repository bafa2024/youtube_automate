"""
Test script to check if all imports work
"""

try:
    print("Testing basic imports...")
    
    # Test config
    from config import settings
    print("+ Config imported successfully")
    
    # Test database
    from database import User, JobStatus, FileRecord
    print("+ Database models imported successfully")
    
    # Test auth
    from auth import create_access_token
    print("+ Auth module imported successfully")
    
    # Test celery app
    from celery_app import celery_app
    print("+ Celery app imported successfully")
    
    # Test main app
    from main import app
    print("+ Main FastAPI app imported successfully")
    
    print("\n[SUCCESS] All core imports successful!")
    
except ImportError as e:
    print(f"[ERROR] Import error: {e}")
    import traceback
    traceback.print_exc()
except Exception as e:
    print(f"[ERROR] Error: {e}")
    import traceback
    traceback.print_exc()