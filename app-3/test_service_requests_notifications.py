#!/usr/bin/env python3
"""
Test for service requests and notifications functionality
"""

import requests

BASE_URL = "http://localhost:5001"

def test_service_requests_and_notifications():
    """Test service requests and notifications functionality"""
    print("🧪 Testing Service Requests and Notifications...")
    
    # Test 1: Admin can access service requests
    print("\n🔧 Testing Admin Service Requests Access...")
    admin_session = requests.Session()
    
    # Login as admin
    admin_login_data = {
        'email': 'admin@example.com',
        'password': 'admin123'
    }
    
    admin_login_response = admin_session.post(f"{BASE_URL}/login", data=admin_login_data, allow_redirects=False)
    print(f"Admin login status: {admin_login_response.status_code}")
    
    if admin_login_response.status_code in [200, 302]:
        print("✅ Admin login successful")
        
        # Test admin can access service requests
        service_requests_response = admin_session.get(f"{BASE_URL}/admin/service-requests", allow_redirects=False)
        print(f"Service requests page status: {service_requests_response.status_code}")
        
        if service_requests_response.status_code == 200:
            print("✅ Admin can access service requests page")
            content = service_requests_response.text
            
            # Check for service request functionality
            if "Service Requests" in content:
                print("✅ Service requests page loads correctly")
            else:
                print("❌ Service requests page content not found")
                
        else:
            print(f"❌ Service requests page error: {service_requests_response.status_code}")
    
    # Test 2: Employee can submit service requests
    print("\n👤 Testing Employee Service Request Submission...")
    employee_session = requests.Session()
    
    # Login as employee
    employee_login_data = {
        'email': 'employee@example.com',
        'password': 'emp123'
    }
    
    employee_login_response = employee_session.post(f"{BASE_URL}/employee/login", data=employee_login_data, allow_redirects=False)
    print(f"Employee login status: {employee_login_response.status_code}")
    
    if employee_login_response.status_code in [200, 302]:
        print("✅ Employee login successful")
        
        # Test employee can access support page
        support_response = employee_session.get(f"{BASE_URL}/employee/support", allow_redirects=False)
        print(f"Employee support page status: {support_response.status_code}")
        
        if support_response.status_code == 200:
            print("✅ Employee can access support page")
            content = support_response.text
            
            if "Support" in content or "IT Support" in content:
                print("✅ Support page loads correctly")
            else:
                print("❌ Support page content not found")
        else:
            print(f"❌ Support page error: {support_response.status_code}")
    
    # Test 3: Notifications work for both admin and employee
    print("\n🔔 Testing Notifications...")
    
    # Test admin notifications
    admin_notifications_response = admin_session.get(f"{BASE_URL}/notifications", allow_redirects=False)
    print(f"Admin notifications status: {admin_notifications_response.status_code}")
    
    if admin_notifications_response.status_code == 200:
        print("✅ Admin can access notifications")
        content = admin_notifications_response.text
        
        if "Notifications" in content:
            print("✅ Notifications page loads correctly for admin")
        else:
            print("❌ Notifications page content not found for admin")
    else:
        print(f"❌ Admin notifications error: {admin_notifications_response.status_code}")
    
    # Test employee notifications
    employee_notifications_response = employee_session.get(f"{BASE_URL}/notifications", allow_redirects=False)
    print(f"Employee notifications status: {employee_notifications_response.status_code}")
    
    if employee_notifications_response.status_code == 200:
        print("✅ Employee can access notifications")
        content = employee_notifications_response.text
        
        if "Notifications" in content:
            print("✅ Notifications page loads correctly for employee")
        else:
            print("❌ Notifications page content not found for employee")
    else:
        print(f"❌ Employee notifications error: {employee_notifications_response.status_code}")
    
    # Test 4: Service request actions work
    print("\n⚡ Testing Service Request Actions...")
    
    # Test service request detail page
    service_request_detail_response = admin_session.get(f"{BASE_URL}/admin/service-requests/1", allow_redirects=False)
    print(f"Service request detail status: {service_request_detail_response.status_code}")
    
    if service_request_detail_response.status_code == 200:
        print("✅ Admin can view service request details")
        content = service_request_detail_response.text
        
        if "Service Request" in content or "Details" in content:
            print("✅ Service request detail page loads correctly")
        else:
            print("❌ Service request detail page content not found")
    else:
        print(f"❌ Service request detail error: {service_request_detail_response.status_code}")
    
    # Test 5: Admin can perform actions on service requests
    print("\n🛠️ Testing Service Request Actions...")
    
    # Test approve action (this would normally be a POST, but we'll just check the route exists)
    approve_response = admin_session.get(f"{BASE_URL}/admin/service-requests/1/approve", allow_redirects=False)
    print(f"Approve route status: {approve_response.status_code}")
    
    if approve_response.status_code in [200, 302, 405]:  # 405 is Method Not Allowed (expected for GET on POST route)
        print("✅ Approve route is accessible")
    else:
        print(f"❌ Approve route error: {approve_response.status_code}")
    
    # Test assign action
    assign_response = admin_session.get(f"{BASE_URL}/admin/service-requests/1/assign", allow_redirects=False)
    print(f"Assign route status: {assign_response.status_code}")
    
    if assign_response.status_code in [200, 302, 405]:
        print("✅ Assign route is accessible")
    else:
        print(f"❌ Assign route error: {assign_response.status_code}")
    
    # Test update status action
    update_status_response = admin_session.get(f"{BASE_URL}/admin/service-requests/1/update-status", allow_redirects=False)
    print(f"Update status route status: {update_status_response.status_code}")
    
    if update_status_response.status_code in [200, 302, 405]:
        print("✅ Update status route is accessible")
    else:
        print(f"❌ Update status route error: {update_status_response.status_code}")
    
    # Test comment action
    comment_response = admin_session.get(f"{BASE_URL}/admin/service-requests/1/comment", allow_redirects=False)
    print(f"Comment route status: {comment_response.status_code}")
    
    if comment_response.status_code in [200, 302, 405]:
        print("✅ Comment route is accessible")
    else:
        print(f"❌ Comment route error: {comment_response.status_code}")
    
    print("\n🎉 Service Requests and Notifications Test Complete!")

if __name__ == "__main__":
    test_service_requests_and_notifications() 