#!/usr/bin/env python3
"""
Complete authentication testing script
Tests register, login, and protected endpoints
"""

import asyncio
import aiohttp
import json
from datetime import datetime

BASE_URL = "http://localhost:8080"

async def test_registration():
    """Test user registration"""
    print("Testing user registration...")
    
    # Test data
    test_user = {
        "email": f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}@example.com",
        "username": f"testuser_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "password": "testpassword123"
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                f"{BASE_URL}/api/auth/register",
                json=test_user,
                headers={"Content-Type": "application/json"}
            ) as response:
                status = response.status
                text = await response.text()
                
                if status == 200:
                    data = json.loads(text)
                    print(f"[SUCCESS] Registration successful: {data}")
                    return test_user, data
                else:
                    print(f"[ERROR] Registration failed: {status} - {text}")
                    return None, None
                    
        except Exception as e:
            print(f"[ERROR] Registration error: {e}")
            return None, None

async def test_login(username, password):
    """Test user login"""
    print(f"Testing login for user: {username}")
    
    async with aiohttp.ClientSession() as session:
        try:
            # Prepare form data for OAuth2PasswordRequestForm
            form_data = aiohttp.FormData()
            form_data.add_field('username', username)
            form_data.add_field('password', password)
            
            async with session.post(
                f"{BASE_URL}/api/auth/token",
                data=form_data
            ) as response:
                status = response.status
                text = await response.text()
                
                if status == 200:
                    data = json.loads(text)
                    print(f"[SUCCESS] Login successful: {data}")
                    return data.get('access_token')
                else:
                    print(f"[ERROR] Login failed: {status} - {text}")
                    return None
                    
        except Exception as e:
            print(f"[ERROR] Login error: {e}")
            return None

async def test_protected_endpoint(token):
    """Test access to protected endpoint"""
    print("Testing protected endpoint access...")
    
    async with aiohttp.ClientSession() as session:
        try:
            headers = {"Authorization": f"Bearer {token}"}
            
            async with session.get(
                f"{BASE_URL}/api/auth/me",
                headers=headers
            ) as response:
                status = response.status
                text = await response.text()
                
                if status == 200:
                    data = json.loads(text)
                    print(f"[SUCCESS] Protected endpoint access successful: {data}")
                    return True
                else:
                    print(f"[ERROR] Protected endpoint access failed: {status} - {text}")
                    return False
                    
        except Exception as e:
            print(f"[ERROR] Protected endpoint error: {e}")
            return False

async def test_invalid_login():
    """Test login with invalid credentials"""
    print("Testing login with invalid credentials...")
    
    async with aiohttp.ClientSession() as session:
        try:
            form_data = aiohttp.FormData()
            form_data.add_field('username', 'invalid_user')
            form_data.add_field('password', 'invalid_password')
            
            async with session.post(
                f"{BASE_URL}/api/auth/token",
                data=form_data
            ) as response:
                status = response.status
                
                if status == 401:
                    print("[SUCCESS] Invalid login correctly rejected")
                    return True
                else:
                    print(f"[ERROR] Invalid login should return 401, got {status}")
                    return False
                    
        except Exception as e:
            print(f"[ERROR] Invalid login test error: {e}")
            return False

async def test_duplicate_registration(existing_user):
    """Test registration with existing email/username"""
    print("Testing duplicate registration...")
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                f"{BASE_URL}/api/auth/register",
                json=existing_user,
                headers={"Content-Type": "application/json"}
            ) as response:
                status = response.status
                
                if status == 400:
                    print("[SUCCESS] Duplicate registration correctly rejected")
                    return True
                else:
                    print(f"[ERROR] Duplicate registration should return 400, got {status}")
                    return False
                    
        except Exception as e:
            print(f"[ERROR] Duplicate registration test error: {e}")
            return False

async def test_server_health():
    """Test if server is running"""
    print("Checking server health...")
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{BASE_URL}/health") as response:
                if response.status == 200:
                    print("[SUCCESS] Server is running")
                    return True
                else:
                    print(f"[ERROR] Server health check failed: {response.status}")
                    return False
        except Exception as e:
            print(f"[ERROR] Server is not running: {e}")
            return False

async def run_all_tests():
    """Run complete authentication test suite"""
    print("=" * 60)
    print("AUTHENTICATION SYSTEM TEST SUITE")
    print("=" * 60)
    
    # Check server health first
    if not await test_server_health():
        print("Cannot proceed with tests - server is not running")
        print("Please start the server with: python main.py")
        return
    
    print()
    
    # Test registration
    test_user, registered_data = await test_registration()
    if not test_user:
        print("Cannot proceed with tests - registration failed")
        return
    
    print()
    
    # Test login
    token = await test_login(test_user['username'], test_user['password'])
    if not token:
        print("Cannot proceed with tests - login failed")
        return
    
    print()
    
    # Test protected endpoint
    await test_protected_endpoint(token)
    
    print()
    
    # Test invalid login
    await test_invalid_login()
    
    print()
    
    # Test duplicate registration
    await test_duplicate_registration(test_user)
    
    print()
    print("=" * 60)
    print("TEST SUITE COMPLETED")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(run_all_tests())