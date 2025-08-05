#!/usr/bin/env python3
"""
Test to verify careers navigation is working correctly
"""

import requests

BASE_URL = "http://localhost:5001"

def test_careers_navigation():
    """Test that the careers navigation works correctly"""
    print("🧪 Testing Careers Navigation...")
    
    session = requests.Session()
    
    # Login as employee
    login_data = {
        'email': 'employee@example.com',
        'password': 'emp123'
    }
    
    login_response = session.post(f"{BASE_URL}/employee/login", data=login_data, allow_redirects=False)
    print(f"Login status: {login_response.status_code}")
    
    if login_response.status_code in [200, 302]:
        print("✅ Login successful")
        
        # Test the correct careers route
        careers_response = session.get(f"{BASE_URL}/employee/careers", allow_redirects=False)
        print(f"Careers page status: {careers_response.status_code}")
        
        if careers_response.status_code == 200:
            print("✅ Careers page loads successfully")
            content = careers_response.text
            
            # Check for new minimalistic design
            if "Career Development" in content and "Skills Assessment" in content:
                print("✅ New minimalistic design is showing!")
                print("✅ You should now see the new career portal design")
            else:
                print("❌ New design not found")
                
        else:
            print(f"❌ Careers page error: {careers_response.status_code}")
            
        # Test the old route to make sure it's different
        old_careers_response = session.get(f"{BASE_URL}/employee/career-development", allow_redirects=False)
        print(f"Old career-development page status: {old_careers_response.status_code}")
        
        if old_careers_response.status_code == 200:
            print("⚠️ Old route still exists but should redirect to new one")
        else:
            print("✅ Old route properly handled")
            
    else:
        print(f"❌ Login failed: {login_response.status_code}")

if __name__ == "__main__":
    test_careers_navigation() 