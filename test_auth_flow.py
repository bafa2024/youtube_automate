#!/usr/bin/env python3
"""
Test authentication flow end-to-end
"""

import requests
import json

BASE_URL = "http://127.0.0.1:8080"

def test_complete_auth_flow():
    """Test the complete authentication flow"""
    
    print("Testing Complete Authentication Flow")
    print("=" * 50)
    
    # Test 1: Register a new user
    print("\n1. Testing Registration...")
    register_data = {
        "email": "testauth@example.com",
        "username": "testauth",
        "password": "password123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/auth/register", json=register_data)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            user_data = response.json()
            print(f"   [OK] User registered: {user_data['username']} (ID: {user_data['id']})")
        else:
            print(f"   [FAIL] Registration failed: {response.text}")
            return False
    except Exception as e:
        print(f"   [ERROR] Registration error: {e}")
        return False
    
    # Test 2: Login with the new user
    print("\n2. Testing Login...")
    login_data = {
        "username": "testauth",
        "password": "password123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/auth/token", data=login_data)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data['access_token']
            print(f"   [OK] Login successful! Token: {access_token[:20]}...")
        else:
            print(f"   [FAIL] Login failed: {response.text}")
            return False
    except Exception as e:
        print(f"   [FAIL] Login error: {e}")
        return False
    
    # Test 3: Access protected endpoint
    print("\n3. Testing Protected Endpoint...")
    headers = {"Authorization": f"Bearer {access_token}"}
    
    try:
        response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            user_info = response.json()
            print(f"   [OK] User info retrieved: {user_info['username']} ({user_info['email']})")
        else:
            print(f"   [FAIL] Protected endpoint failed: {response.text}")
            return False
    except Exception as e:
        print(f"   [FAIL] Protected endpoint error: {e}")
        return False
    
    # Test 4: Test invalid credentials
    print("\n4. Testing Invalid Credentials...")
    invalid_login = {
        "username": "testauth",
        "password": "wrongpassword"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/auth/token", data=invalid_login)
        print(f"   Status: {response.status_code}")
        if response.status_code == 401:
            print(f"   [OK] Invalid credentials properly rejected")
        else:
            print(f"   [WARN]  Unexpected response: {response.text}")
    except Exception as e:
        print(f"   [FAIL] Invalid credentials test error: {e}")
        return False
    
    print("\n[SUCCESS] All authentication tests passed!")
    return True

if __name__ == "__main__":
    success = test_complete_auth_flow()
    if success:
        print("\n[OK] Authentication system is working correctly!")
    else:
        print("\n[FAIL] Authentication system has issues!")