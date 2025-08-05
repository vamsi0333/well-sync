#!/usr/bin/env python3
"""
Debug script for skills assessment issues
"""

import requests
import json

BASE_URL = "http://localhost:5001"

def test_careers_page():
    """Test if careers page loads"""
    print("Testing careers page...")
    
    try:
        response = requests.get(f"{BASE_URL}/employee/careers")
        if response.status_code == 200:
            print("✅ Careers page loads successfully")
            
            # Check if skills test content is in the response
            if "Skills Assessment Test" in response.text:
                print("✅ Skills test content found in page")
            else:
                print("❌ Skills test content NOT found in page")
                
            # Check if skills test tab is present
            if "data-tab=\"skills-test\"" in response.text:
                print("✅ Skills test tab found in page")
            else:
                print("❌ Skills test tab NOT found in page")
                
            return True
        else:
            print(f"❌ Careers page failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Careers page error: {e}")
        return False

def test_skills_test_direct():
    """Test skills test page directly"""
    print("\nTesting skills test page directly...")
    
    try:
        response = requests.get(f"{BASE_URL}/employee/careers/skills-test")
        if response.status_code == 200:
            print("✅ Skills test page loads successfully")
            return True
        else:
            print(f"❌ Skills test page failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Skills test page error: {e}")
        return False

def test_internal_jobs():
    """Test internal jobs page"""
    print("\nTesting internal jobs page...")
    
    try:
        response = requests.get(f"{BASE_URL}/employee/careers/internal-jobs")
        if response.status_code == 200:
            print("✅ Internal jobs page loads successfully")
            return True
        else:
            print(f"❌ Internal jobs page failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Internal jobs page error: {e}")
        return False

def main():
    """Run all tests"""
    print("🔍 Debugging Skills Assessment Issues")
    print("=" * 50)
    
    tests = [
        test_careers_page,
        test_skills_test_direct,
        test_internal_jobs
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The issue might be with JavaScript or CSS.")
    else:
        print("⚠️ Some tests failed. Check the application logs.")

if __name__ == "__main__":
    main() 