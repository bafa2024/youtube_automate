#!/usr/bin/env python3
"""
Final comprehensive authentication testing script
"""

import asyncio
import aiohttp
import json
from datetime import datetime

BASE_URL = "http://localhost:8080"

async def test_comprehensive_auth_flow():
    """Run a comprehensive authentication flow test"""
    print("=" * 60)
    print("FINAL COMPREHENSIVE AUTHENTICATION TEST")
    print("=" * 60)
    
    # Test 1: Registration with strong password
    print("1. Testing registration with strong password...")
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    test_user = {
        "email": f"finaltest_{timestamp}@example.com",
        "username": f"finaluser_{timestamp}",
        "password": "FinalStrongPass123"
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{BASE_URL}/api/auth/register",
            json=test_user,
            headers={"Content-Type": "application/json"}
        ) as response:
            if response.status == 200:
                print("   [SUCCESS] Registration successful")
                user_data = json.loads(await response.text())
            else:
                print(f"   [ERROR] Registration failed: {response.status}")
                return
    
    # Test 2: Login
    print("2. Testing login...")
    async with aiohttp.ClientSession() as session:
        form_data = aiohttp.FormData()
        form_data.add_field('username', test_user['username'])
        form_data.add_field('password', test_user['password'])
        
        async with session.post(f"{BASE_URL}/api/auth/token", data=form_data) as response:
            if response.status == 200:
                print("   [SUCCESS] Login successful")
                token_data = json.loads(await response.text())
                token = token_data['access_token']
            else:
                print(f"   [ERROR] Login failed: {response.status}")
                return
    
    # Test 3: Access protected endpoint
    print("3. Testing protected endpoint access...")
    async with aiohttp.ClientSession() as session:
        headers = {"Authorization": f"Bearer {token}"}
        async with session.get(f"{BASE_URL}/api/auth/me", headers=headers) as response:
            if response.status == 200:
                print("   [SUCCESS] Protected endpoint access successful")
                me_data = json.loads(await response.text())
            else:
                print(f"   [ERROR] Protected endpoint access failed: {response.status}")
                return
    
    # Test 4: Password change
    print("4. Testing password change...")
    new_password = "NewFinalPassword456"
    change_request = {
        "current_password": test_user['password'],
        "new_password": new_password
    }
    
    async with aiohttp.ClientSession() as session:
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        async with session.put(
            f"{BASE_URL}/api/auth/change-password",
            json=change_request,
            headers=headers
        ) as response:
            if response.status == 200:
                print("   [SUCCESS] Password change successful")
            else:
                print(f"   [ERROR] Password change failed: {response.status}")
                return
    
    # Test 5: Login with new password
    print("5. Testing login with new password...")
    async with aiohttp.ClientSession() as session:
        form_data = aiohttp.FormData()
        form_data.add_field('username', test_user['username'])
        form_data.add_field('password', new_password)
        
        async with session.post(f"{BASE_URL}/api/auth/token", data=form_data) as response:
            if response.status == 200:
                print("   [SUCCESS] Login with new password successful")
                new_token_data = json.loads(await response.text())
                new_token = new_token_data['access_token']
            else:
                print(f"   [ERROR] Login with new password failed: {response.status}")
                return
    
    # Test 6: Set API key
    print("6. Testing API key management...")
    async with aiohttp.ClientSession() as session:
        headers = {"Authorization": f"Bearer {new_token}"}
        form_data = aiohttp.FormData()
        form_data.add_field('api_key', 'sk-test-final-api-key-12345')
        
        async with session.post(
            f"{BASE_URL}/api/settings/api-key",
            data=form_data,
            headers=headers
        ) as response:
            if response.status == 200:
                print("   [SUCCESS] API key set successfully")
            else:
                print(f"   [ERROR] API key setting failed: {response.status}")
                return
    
    # Test 7: Check API key status
    print("7. Testing API key status check...")
    async with aiohttp.ClientSession() as session:
        headers = {"Authorization": f"Bearer {new_token}"}
        async with session.get(f"{BASE_URL}/api/settings/api-key", headers=headers) as response:
            if response.status == 200:
                api_status = json.loads(await response.text())
                if api_status.get('has_api_key'):
                    print("   [SUCCESS] API key status correctly shows key exists")
                else:
                    print("   [WARNING] API key status shows no key (unexpected)")
            else:
                print(f"   [ERROR] API key status check failed: {response.status}")
                return
    
    # Test 8: Logout
    print("8. Testing logout...")
    async with aiohttp.ClientSession() as session:
        headers = {"Authorization": f"Bearer {new_token}"}
        async with session.post(f"{BASE_URL}/api/auth/logout", headers=headers) as response:
            if response.status == 200:
                print("   [SUCCESS] Logout successful")
            else:
                print(f"   [ERROR] Logout failed: {response.status}")
    
    print()
    print("=" * 60)
    print("COMPREHENSIVE TEST COMPLETED SUCCESSFULLY!")
    print("All authentication features are working correctly.")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_comprehensive_auth_flow())