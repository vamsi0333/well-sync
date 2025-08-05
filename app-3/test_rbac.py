#!/usr/bin/env python3
"""
Test script for Role-Based Access Control (RBAC) system
"""

import requests
import hashlib
import json

# Test configuration
BASE_URL = "http://localhost:5001"
TEST_USERS = {
    "admin": {
        "email": "admin@example.com",
        "password": "admin123",
        "role": "admin"
    },
    "it": {
        "email": "it@example.com", 
        "password": "it123",
        "role": "it"
    },
    "hr": {
        "email": "hr@example.com",
        "password": "hr123", 
        "role": "hr"
    },
    "employee": {
        "email": "employee@example.com",
        "password": "emp123",
        "role": "employee"
    }
}

def test_login(user_type):
    """Test login for different user types"""
    print(f"\n🔐 Testing login for {user_type.upper()} user...")
    
    user = TEST_USERS[user_type]
    session = requests.Session()
    
    # Get login page
    response = session.get(f"{BASE_URL}/login")
    if response.status_code != 200:
        print(f"❌ Failed to get login page: {response.status_code}")
        return None
    
    # Login
    login_data = {
        "email": user["email"],
        "password": user["password"]
    }
    
    response = session.post(f"{BASE_URL}/login", data=login_data, allow_redirects=False)
    
    if response.status_code == 302:  # Redirect after successful login
        print(f"✅ {user_type.upper()} login successful")
        return session
    else:
        print(f"❌ {user_type.upper()} login failed: {response.status_code}")
        return None

def test_access_control(session, user_type):
    """Test access control for different routes"""
    print(f"\n🔒 Testing access control for {user_type.upper()} user...")
    
    # Define routes and expected access
    routes_to_test = {
        "/admin/dashboard": "all",
        "/admin/tickets": ["admin", "it"],
        "/admin/requests": ["admin", "hr"], 
        "/admin/employees": ["admin"],
        "/admin/feedback": ["admin"],
        "/admin/timeoff": ["admin", "hr"],
        "/admin/leave": ["admin", "hr"],
        "/admin/applications": ["admin", "hr"],
        "/it-portal": "all",
        "/employee/dashboard": "all"
    }
    
    for route, allowed_roles in routes_to_test.items():
        response = session.get(f"{BASE_URL}{route}", allow_redirects=False)
        
        if allowed_roles == "all" or user_type in allowed_roles:
            if response.status_code == 200:
                print(f"✅ {route}: Access granted")
            elif response.status_code == 302:
                print(f"⚠️  {route}: Redirected (may be login required)")
            else:
                print(f"❌ {route}: Unexpected status {response.status_code}")
        else:
            if response.status_code == 302:
                print(f"✅ {route}: Access denied (redirected to login)")
            elif response.status_code == 403:
                print(f"✅ {route}: Access denied (403)")
            else:
                print(f"❌ {route}: Unexpected access control - status {response.status_code}")

def test_it_portal_access():
    """Test IT Portal access without password prompt"""
    print(f"\n🖥️  Testing IT Portal access...")
    
    # Test as employee
    session = test_login("employee")
    if session:
        response = session.get(f"{BASE_URL}/it-portal", allow_redirects=False)
        if response.status_code == 302:
            print("✅ IT Portal redirects properly for employees")
        else:
            print(f"❌ IT Portal access issue: {response.status_code}")
    
    # Test as IT user
    session = test_login("it")
    if session:
        response = session.get(f"{BASE_URL}/it-portal", allow_redirects=False)
        if response.status_code == 302:
            print("✅ IT Portal redirects properly for IT users")
        else:
            print(f"❌ IT Portal access issue: {response.status_code}")

def main():
    """Main test function"""
    print("🚀 Starting RBAC System Test")
    print("=" * 50)
    
    # Test server availability
    try:
        response = requests.get(f"{BASE_URL}/login")
        if response.status_code == 200:
            print("✅ Server is running and accessible")
        else:
            print(f"❌ Server issue: {response.status_code}")
            return
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Make sure it's running on port 5001")
        return
    
    # Test each user type
    for user_type in ["admin", "it", "hr", "employee"]:
        session = test_login(user_type)
        if session:
            test_access_control(session, user_type)
    
    # Test IT Portal specifically
    test_it_portal_access()
    
    print("\n" + "=" * 50)
    print("🏁 RBAC System Test Complete")

if __name__ == "__main__":
    main() 