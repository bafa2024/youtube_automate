#!/usr/bin/env python3
"""
Test script for minimal deployment
"""

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
        import pydantic
        print("✓ Pydantic imported successfully")
    except ImportError as e:
        print(f"✗ Pydantic import failed: {e}")
        return False
    
    return True

def test_app():
    """Test app creation"""
    print("\nTesting app creation...")
    
    try:
        from main_minimal import app
        print("✓ App created successfully")
        print(f"  - Title: {app.title}")
        print(f"  - Version: {app.version}")
        return True
    except Exception as e:
        print(f"✗ App creation failed: {e}")
        return False

def test_health():
    """Test health endpoint"""
    print("\nTesting health endpoint...")
    
    try:
        from main_minimal import app
        from fastapi.testclient import TestClient
        
        client = TestClient(app)
        response = client.get("/health")
        
        if response.status_code == 200:
            data = response.json()
            print("✓ Health endpoint working")
            print(f"  - Status: {data.get('status')}")
            print(f"  - Version: {data.get('version')}")
            return True
        else:
            print(f"✗ Health endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Health test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Minimal Deployment Test")
    print("=" * 40)
    
    tests = [
        test_imports,
        test_app,
        test_health
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
    import sys
    sys.exit(main()) 