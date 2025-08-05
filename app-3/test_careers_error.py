#!/usr/bin/env python3
"""
Test careers route error
"""

import requests

BASE_URL = "http://localhost:5001"

def test_careers_error():
    """Test careers route to see what error occurs"""
    print("Testing careers route error...")
    
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
            
            # Try to access careers page
            careers_response = session.get(f"{BASE_URL}/employee/careers", allow_redirects=False)
            print(f"Careers status: {careers_response.status_code}")
            
            if careers_response.status_code == 500:
                print("❌ Careers page has 500 error")
                print("Response content:")
                print(careers_response.text[:500])  # First 500 characters
            elif careers_response.status_code == 200:
                print("✅ Careers page loads successfully")
                content = careers_response.text
                
                # Check for the buttons
                if "View Internal Jobs" in content:
                    print("✅ View Internal Jobs button found")
                else:
                    print("❌ View Internal Jobs button NOT found")
                    
                if "Skills Assessment" in content:
                    print("✅ Skills Assessment button found")
                else:
                    print("❌ Skills Assessment button NOT found")
                    
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
            else:
                print(f"❌ Careers page error: {careers_response.status_code}")
                
        else:
            print(f"❌ Login failed: {login_response.status_code}")
            
    except Exception as e:
        print(f"❌ Test error: {e}")

if __name__ == "__main__":
    test_careers_error() 