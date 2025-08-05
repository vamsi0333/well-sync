#!/usr/bin/env python3
"""
Test internal jobs functionality
"""

import requests

BASE_URL = "http://localhost:5001"

def test_internal_jobs():
    """Test internal jobs functionality"""
    print("Testing internal jobs...")
    
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
            
            # Test internal jobs page
            internal_jobs_response = session.get(f"{BASE_URL}/employee/careers/internal-jobs", allow_redirects=False)
            print(f"Internal jobs status: {internal_jobs_response.status_code}")
            
            if internal_jobs_response.status_code == 200:
                print("✅ Internal jobs page loads successfully")
                content = internal_jobs_response.text
                
                # Check for job listings
                if "Senior Product Manager" in content:
                    print("✅ Senior Product Manager job found")
                else:
                    print("❌ Senior Product Manager job NOT found")
                    
                if "UX Designer" in content:
                    print("✅ UX Designer job found")
                else:
                    print("❌ UX Designer job NOT found")
                    
                if "Data Scientist" in content:
                    print("✅ Data Scientist job found")
                else:
                    print("❌ Data Scientist job NOT found")
                    
                # Check for apply buttons
                if "Apply Now" in content:
                    print("✅ Apply buttons found")
                else:
                    print("❌ Apply buttons NOT found")
                    
            elif internal_jobs_response.status_code == 500:
                print("❌ Internal jobs page has 500 error")
                print("Response content:")
                print(internal_jobs_response.text[:500])
            else:
                print(f"❌ Internal jobs page error: {internal_jobs_response.status_code}")
                
            # Test individual job page
            job_detail_response = session.get(f"{BASE_URL}/employee/careers/internal-jobs/1", allow_redirects=False)
            print(f"Job detail status: {job_detail_response.status_code}")
            
            if job_detail_response.status_code == 200:
                print("✅ Job detail page loads successfully")
                content = job_detail_response.text
                
                if "Senior Product Manager" in content:
                    print("✅ Job title found in detail page")
                else:
                    print("❌ Job title NOT found in detail page")
                    
                if "Apply for this position" in content:
                    print("✅ Apply form found")
                else:
                    print("❌ Apply form NOT found")
                    
            elif job_detail_response.status_code == 500:
                print("❌ Job detail page has 500 error")
                print("Response content:")
                print(job_detail_response.text[:500])
            else:
                print(f"❌ Job detail page error: {job_detail_response.status_code}")
                
        else:
            print(f"❌ Login failed: {login_response.status_code}")
            
    except Exception as e:
        print(f"❌ Test error: {e}")

if __name__ == "__main__":
    test_internal_jobs() 