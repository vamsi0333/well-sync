#!/usr/bin/env python3
"""
Debug script to check login response
"""

import requests

BASE_URL = "http://localhost:5001"

def debug_login():
    """Debug the login process"""
    
    session = requests.Session()
    
    print("🔍 Debugging Login Process")
    print("=" * 40)
    
    # Test login
    login_data = {
        'email': 'employee@example.com',
        'password': 'password123'
    }
    
    print(f"Attempting login with: {login_data}")
    
    response = session.post(f"{BASE_URL}/employee/login", data=login_data, allow_redirects=False)
    
    print(f"Status Code: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")
    print(f"Response Text (first 500 chars): {response.text[:500]}")
    
    # Check if we got redirected
    if response.status_code == 302:
        print(f"Redirect Location: {response.headers.get('Location', 'None')}")
    
    # Try the regular login endpoint too
    print("\n" + "=" * 40)
    print("Trying regular login endpoint...")
    
    response2 = session.post(f"{BASE_URL}/login", data=login_data, allow_redirects=False)
    
    print(f"Status Code: {response2.status_code}")
    print(f"Headers: {dict(response2.headers)}")
    print(f"Response Text (first 500 chars): {response2.text[:500]}")

if __name__ == "__main__":
    debug_login() 