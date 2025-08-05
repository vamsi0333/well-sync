#!/usr/bin/env python3
"""
Test script to verify IT portal access for employees
"""

import requests
from urllib.parse import urljoin

BASE_URL = "http://localhost:5000"

def test_it_portal_access():
    """Test that employees can access IT portal"""
    print("🧪 Testing IT Portal Access for Employees...")
    
    # Create a session
    session = requests.Session()
    
    # Test employee login
    login_data = {
        "email": "employee@example.com",
        "password": "emp123"
    }
    
    login_response = session.post(f"{BASE_URL}/employee/login", data=login_data, allow_redirects=False)
    print(f"Employee login status: {login_response.status_code}")
    
    if login_response.status_code == 302:
        print("✅ Employee login successful")
        
        # Test IT portal access
        it_response = session.get(f"{BASE_URL}/it-portal", allow_redirects=False)
        print(f"IT Portal access status: {it_response.status_code}")
        
        if it_response.status_code == 302:
            print("✅ IT Portal redirects employees")
            
            # Follow the redirect to see where it goes
            redirect_url = it_response.headers.get('Location', '')
            print(f"Redirect URL: {redirect_url}")
            
            if '/admin/dashboard' in redirect_url:
                print("✅ IT Portal redirects employees to admin dashboard")
            else:
                print(f"⚠️ IT Portal redirects to: {redirect_url}")
        else:
            print("❌ IT Portal access failed")
    else:
        print("❌ Employee login failed")

if __name__ == "__main__":
    test_it_portal_access() 