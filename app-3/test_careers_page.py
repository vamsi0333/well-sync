#!/usr/bin/env python3
"""
Test to verify the careers page is showing the new minimalistic design
"""

import requests

BASE_URL = "http://localhost:5001"

def test_careers_page():
    """Test that the careers page shows the new minimalistic design"""
    print("🧪 Testing Careers Page - New Minimalistic Design...")
    
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
        
        # Test careers page
        careers_response = session.get(f"{BASE_URL}/employee/careers", allow_redirects=False)
        print(f"Careers page status: {careers_response.status_code}")
        
        if careers_response.status_code == 200:
            print("✅ Careers page loads successfully")
            content = careers_response.text
            
            # Check for new minimalistic design elements
            checks = [
                ("Career Development", "Main header"),
                ("Skills Assessment", "Skills assessment card"),
                ("Learning Roadmap", "Learning roadmap card"),
                ("Internal Jobs", "Internal jobs card"),
                ("Learning Hub", "Learning hub card"),
                ("Career Goals", "Career goals card"),
                ("Progress", "Progress tracking card"),
                ("Recent Activity", "Recent activity section")
            ]
            
            all_found = True
            for text, description in checks:
                if text in content:
                    print(f"✅ {description} found: '{text}'")
                else:
                    print(f"❌ {description} NOT found: '{text}'")
                    all_found = False
            
            if all_found:
                print("\n🎉 ALL NEW MINIMALISTIC DESIGN ELEMENTS FOUND!")
                print("The careers page is showing the new minimalistic design correctly.")
            else:
                print("\n⚠️ Some elements are missing from the new design.")
                
        else:
            print(f"❌ Careers page error: {careers_response.status_code}")
    else:
        print(f"❌ Login failed: {login_response.status_code}")

if __name__ == "__main__":
    test_careers_page() 