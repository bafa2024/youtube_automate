#!/usr/bin/env python3
"""
Enhanced authentication testing script
Tests register, login, password change, and protected endpoints
"""

import asyncio
import aiohttp
import json
from datetime import datetime

BASE_URL = "http://localhost:8080"

async def test_password_validation():
    """Test password validation requirements"""
    print("Testing password validation...")
    
    weak_passwords = [
        "weak",  # Too short
        "weakpassword",  # No uppercase
        "WEAKPASSWORD",  # No lowercase  
        "WeakPassword",  # No digit
        "w3akP4ss"  # Valid but short
    ]
    
    for weak_password in weak_passwords:
        test_user = {
            "email": f"weak_{datetime.now().strftime('%Y%m%d_%H%M%S')}@example.com",
            "username": f"weakuser_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "password": weak_password
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    f"{BASE_URL}/api/auth/register",
                    json=test_user,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 422:
                        print(f"[SUCCESS] Weak password '{weak_password}' correctly rejected")
                    else:
                        print(f"[ERROR] Weak password '{weak_password}' should be rejected")
                        
            except Exception as e:
                print(f"[ERROR] Password validation test error: {e}")

async def test_registration_with_strong_password():
    """Test registration with strong password"""
    print("Testing registration with strong password...")
    
    test_user = {
        "email": f"strong_{datetime.now().strftime('%Y%m%d_%H%M%S')}@example.com",
        "username": f"stronguser_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "password": "StrongPassword123"
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
                    print(f"[SUCCESS] Strong password registration successful")
                    return test_user, data
                else:
                    print(f"[ERROR] Strong password registration failed: {status} - {text}")
                    return None, None
                    
        except Exception as e:
            print(f"[ERROR] Strong password registration error: {e}")
            return None, None

async def test_password_change(token, old_password):
    """Test password change functionality"""
    print("Testing password change...")
    
    # Test with weak new password first
    weak_change_request = {
        "current_password": old_password,
        "new_password": "weak"
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
            
            async with session.put(
                f"{BASE_URL}/api/auth/change-password",
                json=weak_change_request,
                headers=headers
            ) as response:
                if response.status == 422:
                    print("[SUCCESS] Weak new password correctly rejected")
                else:
                    print(f"[ERROR] Weak new password should be rejected, got {response.status}")
            
            # Test with strong new password
            strong_change_request = {
                "current_password": old_password,
                "new_password": "NewStrongPassword456"
            }
            
            async with session.put(
                f"{BASE_URL}/api/auth/change-password",
                json=strong_change_request,
                headers=headers
            ) as response:
                if response.status == 200:
                    print("[SUCCESS] Password change with strong password successful")
                    return "NewStrongPassword456"
                else:
                    text = await response.text()
                    print(f"[ERROR] Password change failed: {response.status} - {text}")
                    return None
                    
        except Exception as e:
            print(f"[ERROR] Password change test error: {e}")
            return None

async def test_login_after_password_change(username, new_password):
    """Test login with new password after change"""
    print("Testing login with new password...")
    
    async with aiohttp.ClientSession() as session:
        try:
            form_data = aiohttp.FormData()
            form_data.add_field('username', username)
            form_data.add_field('password', new_password)
            
            async with session.post(
                f"{BASE_URL}/api/auth/token",
                data=form_data
            ) as response:
                if response.status == 200:
                    data = json.loads(await response.text())
                    print("[SUCCESS] Login with new password successful")
                    return data.get('access_token')
                else:
                    print(f"[ERROR] Login with new password failed: {response.status}")
                    return None
                    
        except Exception as e:
            print(f"[ERROR] Login with new password error: {e}")
            return None

async def test_api_key_functionality(token):
    """Test API key setting and checking"""
    print("Testing API key functionality...")
    
    async with aiohttp.ClientSession() as session:
        try:
            headers = {"Authorization": f"Bearer {token}"}
            
            # Check if API key exists (should be false initially)
            async with session.get(
                f"{BASE_URL}/api/settings/api-key",
                headers=headers
            ) as response:
                if response.status == 200:
                    data = json.loads(await response.text())
                    if not data.get('has_api_key', True):
                        print("[SUCCESS] Initial API key check shows no key")
                    else:
                        print("[WARNING] Initial API key check shows key exists")
                
            # Set API key
            form_data = aiohttp.FormData()
            form_data.add_field('api_key', 'test-api-key-12345')
            
            async with session.post(
                f"{BASE_URL}/api/settings/api-key",
                data=form_data,
                headers=headers
            ) as response:
                if response.status == 200:
                    print("[SUCCESS] API key set successfully")
                else:
                    text = await response.text()
                    print(f"[ERROR] API key setting failed: {response.status} - {text}")
                    
        except Exception as e:
            print(f"[ERROR] API key test error: {e}")

async def test_logout(token):
    """Test logout functionality"""
    print("Testing logout...")
    
    async with aiohttp.ClientSession() as session:
        try:
            headers = {"Authorization": f"Bearer {token}"}
            
            async with session.post(
                f"{BASE_URL}/api/auth/logout",
                headers=headers
            ) as response:
                if response.status == 200:
                    print("[SUCCESS] Logout successful")
                    return True
                else:
                    print(f"[ERROR] Logout failed: {response.status}")
                    return False
                    
        except Exception as e:
            print(f"[ERROR] Logout test error: {e}")
            return False

async def run_enhanced_tests():
    """Run enhanced authentication test suite"""
    print("=" * 60)
    print("ENHANCED AUTHENTICATION SYSTEM TEST SUITE")
    print("=" * 60)
    
    # Test password validation
    await test_password_validation()
    print()
    
    # Test registration with strong password
    test_user, registered_data = await test_registration_with_strong_password()
    if not test_user:
        print("Cannot proceed with tests - registration failed")
        return
    
    print()
    
    # Test login
    async with aiohttp.ClientSession() as session:
        form_data = aiohttp.FormData()
        form_data.add_field('username', test_user['username'])
        form_data.add_field('password', test_user['password'])
        
        async with session.post(f"{BASE_URL}/api/auth/token", data=form_data) as response:
            if response.status == 200:
                data = json.loads(await response.text())
                token = data.get('access_token')
                print("[SUCCESS] Login successful")
            else:
                print("[ERROR] Login failed")
                return
    
    print()
    
    # Test password change
    new_password = await test_password_change(token, test_user['password'])
    if new_password:
        print()
        
        # Test login with new password
        new_token = await test_login_after_password_change(test_user['username'], new_password)
        if new_token:
            token = new_token
    
    print()
    
    # Test API key functionality
    await test_api_key_functionality(token)
    
    print()
    
    # Test logout
    await test_logout(token)
    
    print()
    print("=" * 60)
    print("ENHANCED TEST SUITE COMPLETED")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(run_enhanced_tests())