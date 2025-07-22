#!/usr/bin/env python3
"""
Test script for user registration
"""

import requests
import json

# Test registration endpoint
def test_registration():
    url = "http://127.0.0.1:8080/api/auth/register"
    
    # Test data
    user_data = {
        "email": "test@example.com",
        "username": "testuser",
        "password": "testpassword123"
    }
    
    try:
        response = requests.post(url, json=user_data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Registration successful!")
            return response.json()
        else:
            print("❌ Registration failed!")
            return None
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Make sure the app is running on port 8080.")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_login():
    url = "http://127.0.0.1:8080/api/auth/token"
    
    # Test login data
    login_data = {
        "username": "testuser",
        "password": "testpassword123"
    }
    
    try:
        response = requests.post(url, data=login_data)
        print(f"\nLogin Status Code: {response.status_code}")
        print(f"Login Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Login successful!")
            return response.json()
        else:
            print("❌ Login failed!")
            return None
            
    except Exception as e:
        print(f"❌ Login Error: {e}")
        return None

if __name__ == "__main__":
    print("Testing User Registration...")
    print("=" * 40)
    
    # Test registration
    user = test_registration()
    
    if user:
        # Test login
        token = test_login()
        
        if token:
            print(f"\n🎉 All tests passed! User ID: {user.get('id')}")
            print(f"Access Token: {token.get('access_token', 'N/A')[:20]}...")
        else:
            print("\n⚠️ Registration worked but login failed.")
    else:
        print("\n❌ Registration test failed.") 