#!/usr/bin/env python3
"""
Simple test to debug leave management functionality
"""

import requests

BASE_URL = "http://localhost:5001"

def test_leave_management():
    """Test leave management functionality"""
    print("🧪 Testing Leave Management Debug...")
    
    session = requests.Session()
    
    # Login as admin
    login_data = {
        "email": "admin@example.com",
        "password": "admin123"
    }
    
    login_response = session.post(f"{BASE_URL}/login", data=login_data, allow_redirects=False)
    if login_response.status_code == 302:
        print("✅ Admin login successful")
        
        # Test leave management page
        leave_response = session.get(f"{BASE_URL}/admin/leave", allow_redirects=False)
        print(f"Leave page status: {leave_response.status_code}")
        
        if leave_response.status_code == 200:
            print("✅ Leave management accessible")
            
            # Test approve leave with different data
            approve_data = {"status": "approved", "admin_comment": "Test approval"}
            approve_response = session.post(f"{BASE_URL}/admin/update-leave-status/1", data=approve_data, allow_redirects=False)
            print(f"Approve response status: {approve_response.status_code}")
            
            if approve_response.status_code == 302:
                print("✅ Leave approval working")
            else:
                print(f"❌ Leave approval failed: {approve_response.status_code}")
                print(f"Response content: {approve_response.text[:200]}")
        else:
            print(f"❌ Leave management not accessible: {leave_response.status_code}")
    else:
        print("❌ Admin login failed")

if __name__ == "__main__":
    test_leave_management() 