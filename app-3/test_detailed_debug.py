#!/usr/bin/env python3
"""
Detailed debug script for careers page
"""

import requests

BASE_URL = "http://localhost:5001"

def test_careers_page_detailed():
    """Test careers page with detailed analysis"""
    print("Testing careers page with detailed analysis...")
    
    try:
        response = requests.get(f"{BASE_URL}/employee/careers")
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
                
            # Check for tab content div
            if "tab-skills-test" in content:
                print("✅ Skills test tab content div found")
            else:
                print("❌ Skills test tab content div NOT found")
                
            # Check for template include
            if "{% include 'employee_portal/skills_test_content.html' %}" in content:
                print("✅ Template include directive found")
            else:
                print("❌ Template include directive NOT found")
                
            # Look for any error messages
            if "error" in content.lower() or "exception" in content.lower():
                print("⚠️ Error messages found in content")
                
            return True
        else:
            print(f"❌ Careers page failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Careers page error: {e}")
        return False

if __name__ == "__main__":
    test_careers_page_detailed() 