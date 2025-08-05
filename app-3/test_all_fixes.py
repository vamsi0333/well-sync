#!/usr/bin/env python3
"""
Comprehensive test for all fixes
"""

import requests

BASE_URL = "http://localhost:5001"

def test_all_fixes():
    """Test all the fixes mentioned by the user"""
    print("🧪 Testing all fixes...")
    
    session = requests.Session()
    
    try:
        # Login as employee
        login_data = {
            'email': 'employee@example.com',
            'password': 'emp123'
        }
        
        login_response = session.post(f"{BASE_URL}/employee/login", data=login_data, allow_redirects=False)
        print(f"Login status: {login_response.status_code}")
        
        if login_response.status_code in [200, 302]:
            print("✅ Login successful")
            
            # Test 1: Course functionality
            print("\n📚 Testing course functionality...")
            course_response = session.get(f"{BASE_URL}/employee/careers/learning/course/1", allow_redirects=False)
            print(f"Course page status: {course_response.status_code}")
            
            if course_response.status_code == 200:
                print("✅ Course page loads successfully")
                content = course_response.text
                if "Quiz Form" in content or "Submit Quiz" in content:
                    print("✅ Course quiz content found")
                else:
                    print("❌ Course quiz content NOT found")
            else:
                print(f"❌ Course page error: {course_response.status_code}")
            
            # Test 2: Skills assessment
            print("\n🧠 Testing skills assessment...")
            skills_response = session.get(f"{BASE_URL}/employee/careers/skills-test", allow_redirects=False)
            print(f"Skills test status: {skills_response.status_code}")
            
            if skills_response.status_code == 200:
                print("✅ Skills test page loads successfully")
                content = skills_response.text
                if "Skills Assessment Test" in content:
                    print("✅ Skills assessment content found")
                else:
                    print("❌ Skills assessment content NOT found")
            else:
                print(f"❌ Skills test error: {skills_response.status_code}")
            
            # Test 3: Learning roadmap
            print("\n🗺️ Testing learning roadmap...")
            roadmap_response = session.get(f"{BASE_URL}/employee/careers/learning-roadmap", allow_redirects=False)
            print(f"Learning roadmap status: {roadmap_response.status_code}")
            
            if roadmap_response.status_code == 200:
                print("✅ Learning roadmap page loads successfully")
                content = roadmap_response.text
                if "Learning Roadmap" in content or "Skill Level" in content:
                    print("✅ Learning roadmap content found")
                else:
                    print("❌ Learning roadmap content NOT found")
            else:
                print(f"❌ Learning roadmap error: {roadmap_response.status_code}")
            
            # Test 4: IT Portal access
            print("\n🖥️ Testing IT portal access...")
            it_response = session.get(f"{BASE_URL}/it-portal", allow_redirects=False)
            print(f"IT portal status: {it_response.status_code}")
            
            if it_response.status_code == 302:
                redirect_location = it_response.headers.get('Location', '')
                print(f"IT portal redirects to: {redirect_location}")
                if "employee/dashboard" in redirect_location:
                    print("✅ IT portal correctly redirects employee to employee dashboard")
                else:
                    print("❌ IT portal redirects to wrong location")
            elif it_response.status_code == 200:
                print("✅ IT portal loads successfully")
            else:
                print(f"❌ IT portal error: {it_response.status_code}")
            
            # Test 5: Career portal with skills assessment
            print("\n💼 Testing career portal with skills assessment...")
            careers_response = session.get(f"{BASE_URL}/employee/careers", allow_redirects=False)
            print(f"Careers page status: {careers_response.status_code}")
            
            if careers_response.status_code == 200:
                print("✅ Careers page loads successfully")
                content = careers_response.text
                
                # Check for skills assessment button
                if "Skills Assessment" in content:
                    print("✅ Skills Assessment button found")
                else:
                    print("❌ Skills Assessment button NOT found")
                
                # Check for skills test tab
                if "data-tab=\"skills-test\"" in content:
                    print("✅ Skills test tab found")
                else:
                    print("❌ Skills test tab NOT found")
                
                # Check for learning roadmap tab
                if "data-tab=\"learning-roadmap\"" in content:
                    print("✅ Learning roadmap tab found")
                else:
                    print("❌ Learning roadmap tab NOT found")
                
            else:
                print(f"❌ Careers page error: {careers_response.status_code}")
                
        else:
            print(f"❌ Login failed: {login_response.status_code}")
            
    except Exception as e:
        print(f"❌ Test error: {e}")

if __name__ == "__main__":
    test_all_fixes() 