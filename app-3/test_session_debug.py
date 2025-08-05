#!/usr/bin/env python3
"""
Debug session issues
"""

import requests

BASE_URL = "http://localhost:5001"

def test_session():
    """Test session handling"""
    print("Testing session handling...")
    
    session = requests.Session()
    
    try:
        # Login
        login_data = {
            'email': 'employee@example.com',
            'password': 'emp123'
        }
        
        login_response = session.post(f"{BASE_URL}/employee/login", data=login_data, allow_redirects=False)
        print(f"Login status: {login_response.status_code}")
        
        if login_response.status_code in [200, 302]:
            print("✅ Login successful")
            
            # Check if we have session cookies
            cookies = session.cookies
            print(f"Session cookies: {dict(cookies)}")
            
            # Try to access employee dashboard
            dashboard_response = session.get(f"{BASE_URL}/employee/dashboard", allow_redirects=False)
            print(f"Dashboard status: {dashboard_response.status_code}")
            print(f"Dashboard redirect: {dashboard_response.headers.get('Location', 'None')}")
            
            # Try to access careers page
            careers_response = session.get(f"{BASE_URL}/employee/careers", allow_redirects=False)
            print(f"Careers status: {careers_response.status_code}")
            print(f"Careers redirect: {careers_response.headers.get('Location', 'None')}")
            
        else:
            print(f"❌ Login failed: {login_response.status_code}")
            
    except Exception as e:
        print(f"❌ Session test error: {e}")

if __name__ == "__main__":
    test_session() 