#!/usr/bin/env python3
"""
Test to verify dark mode support in careers page
"""

import requests

BASE_URL = "http://localhost:5001"

def test_dark_mode_careers():
    """Test that the careers page has proper dark mode support"""
    print("🌙 Testing Dark Mode Support...")
    
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
        
        # Test the careers route
        careers_response = session.get(f"{BASE_URL}/employee/careers", allow_redirects=False)
        print(f"Careers page status: {careers_response.status_code}")
        
        if careers_response.status_code == 200:
            print("✅ Careers page loads successfully")
            content = careers_response.text
            
            # Check for dark mode classes
            dark_mode_indicators = [
                "dark:bg-gray-800",
                "dark:text-white", 
                "dark:text-gray-300",
                "dark:border-gray-700",
                "dark:from-gray-900",
                "dark:to-gray-900"
            ]
            
            found_dark_mode = 0
            for indicator in dark_mode_indicators:
                if indicator in content:
                    found_dark_mode += 1
            
            if found_dark_mode >= 3:
                print(f"✅ Dark mode support found! ({found_dark_mode}/6 indicators)")
                print("✅ The page will adapt to dark mode when the browser/system is in dark mode")
            else:
                print(f"⚠️ Limited dark mode support ({found_dark_mode}/6 indicators)")
                
            # Check for modern design elements
            modern_elements = [
                "bg-gradient-to-br",
                "rounded-2xl",
                "shadow-lg",
                "transform hover:-translate-y-2",
                "bg-gradient-to-r",
                "text-transparent"
            ]
            
            found_modern = 0
            for element in modern_elements:
                if element in content:
                    found_modern += 1
            
            if found_modern >= 4:
                print(f"✅ Modern aesthetic design found! ({found_modern}/6 elements)")
                print("✅ The page has gradients, animations, and modern styling")
            else:
                print(f"⚠️ Limited modern design elements ({found_modern}/6 elements)")
                
        else:
            print(f"❌ Careers page error: {careers_response.status_code}")
            
    else:
        print(f"❌ Login failed: {login_response.status_code}")

if __name__ == "__main__":
    test_dark_mode_careers() 