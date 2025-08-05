#!/usr/bin/env python3
"""
Test script to verify course quiz functionality
"""

import requests
from bs4 import BeautifulSoup
import json

BASE_URL = "http://localhost:5001"

def test_course_quiz():
    """Test the course quiz functionality"""
    
    # Create a session to maintain cookies
    session = requests.Session()
    
    print("🧪 Testing Course Quiz Functionality")
    print("=" * 50)
    
    # 1. Test login
    print("1. Testing login...")
    login_data = {
        'email': 'test@example.com',
        'password': 'test123'
    }
    
    response = session.post(f"{BASE_URL}/employee/login", data=login_data, allow_redirects=False)
    if response.status_code == 302:
        print("✅ Login successful")
    else:
        print("❌ Login failed")
        return
    
    # 2. Test accessing learning page
    print("\n2. Testing learning page access...")
    response = session.get(f"{BASE_URL}/employee/careers/learning")
    if response.status_code == 200:
        print("✅ Learning page accessible")
    else:
        print("❌ Learning page not accessible")
        return
    
    # 3. Test accessing course quiz page
    print("\n3. Testing course quiz page access...")
    response = session.get(f"{BASE_URL}/employee/careers/learning/course/1")
    if response.status_code == 200:
        print("✅ Course quiz page accessible")
        
        # Check if the page contains quiz questions
        soup = BeautifulSoup(response.text, 'html.parser')
        questions = soup.find_all('input', {'name': 'answers[]'})
        if questions:
            print(f"✅ Found {len(questions)} quiz questions")
        else:
            print("❌ No quiz questions found")
    else:
        print("❌ Course quiz page not accessible")
        return
    
    # 4. Test submitting quiz
    print("\n4. Testing quiz submission...")
    quiz_data = {
        'course_id': '1',
        'answers[]': ['1', '2', '1', '1', '2']  # Sample answers
    }
    
    response = session.post(f"{BASE_URL}/employee/careers/submit-course-quiz", data=quiz_data, allow_redirects=False)
    if response.status_code == 302:
        print("✅ Quiz submission successful")
    else:
        print("❌ Quiz submission failed")
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.text[:200]}...")
    
    print("\n🎉 Course quiz functionality test completed!")

if __name__ == "__main__":
    test_course_quiz() 