#!/usr/bin/env python3
"""
Test script for career portal features
"""

import requests
import json

# Base URL for the application
BASE_URL = "http://localhost:5001"

def test_careers_page_direct():
    """Test careers page directly"""
    print("Testing careers page directly...")
    
    try:
        # Don't follow redirects to see what happens
        response = requests.get(f"{BASE_URL}/employee/careers", allow_redirects=False)
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Careers page loads successfully")
            
            content = response.text
            
            # Check for skills test tab
            if "data-tab=\"skills-test\"" in content:
                print("✅ Skills test tab found")
            else:
                print("❌ Skills test tab NOT found")
                
            # Check for skills test content
            if "Skills Assessment Test" in content:
                print("✅ Skills test content found")
            else:
                print("❌ Skills test content NOT found")
                
            # Check for the tab content div
            if "tab-skills-test" in content:
                print("✅ Skills test tab content div found")
            else:
                print("❌ Skills test tab content div NOT found")
                
            # Check for the buttons
            if "View Internal Jobs" in content:
                print("✅ View Internal Jobs button found")
            else:
                print("❌ View Internal Jobs button NOT found")
                
            if "Skills Assessment" in content:
                print("✅ Skills Assessment button found")
            else:
                print("❌ Skills Assessment button NOT found")
                
        elif response.status_code == 302:
            print("⚠️ Careers page redirects to login (requires authentication)")
            print(f"Redirect location: {response.headers.get('Location', 'Unknown')}")
        else:
            print(f"❌ Careers page error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Careers page error: {e}")

def test_with_authentication():
    """Test with authentication"""
    print("\nTesting with authentication...")
    
    # Create a session to maintain cookies
    session = requests.Session()
    
    try:
        # First, try to login
        login_data = {
            'email': 'employee@example.com',
            'password': 'emp123'
        }
        
        login_response = session.post(f"{BASE_URL}/employee/login", data=login_data, allow_redirects=False)
        print(f"Login status: {login_response.status_code}")
        
        if login_response.status_code in [200, 302]:
            print("✅ Login successful")
            print(f"Login redirect location: {login_response.headers.get('Location', 'None')}")
            
            # Now try to access careers page
            careers_response = session.get(f"{BASE_URL}/employee/careers", allow_redirects=False)
            print(f"Careers page status: {careers_response.status_code}")
            print(f"Careers redirect location: {careers_response.headers.get('Location', 'None')}")
            
            if careers_response.status_code == 200:
                print("✅ Careers page accessible after login")
                
                content = careers_response.text
                
                # Check for skills test tab
                if "data-tab=\"skills-test\"" in content:
                    print("✅ Skills test tab found")
                else:
                    print("❌ Skills test tab NOT found")
                    
                # Check for skills test content
                if "Skills Assessment Test" in content:
                    print("✅ Skills test content found")
                else:
                    print("❌ Skills test content NOT found")
                    
                # Check for the buttons
                if "View Internal Jobs" in content:
                    print("✅ View Internal Jobs button found")
                else:
                    print("❌ View Internal Jobs button NOT found")
                    
                if "Skills Assessment" in content:
                    print("✅ Skills Assessment button found")
                else:
                    print("❌ Skills Assessment button NOT found")
                    
            else:
                print(f"❌ Careers page still not accessible: {careers_response.status_code}")
        else:
            print(f"❌ Login failed: {login_response.status_code}")
            
    except Exception as e:
        print(f"❌ Authentication test error: {e}")

if __name__ == "__main__":
    test_careers_page_direct()
    test_with_authentication() 