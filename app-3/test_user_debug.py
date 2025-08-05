#!/usr/bin/env python3
"""
Debug user database issues
"""

from database_helper import db_helper
import hashlib

def test_user_retrieval():
    """Test user retrieval from database"""
    print("Testing user retrieval...")
    
    email = "employee@example.com"
    
    try:
        # Get user from database
        user = db_helper.get_user_by_email(email)
        
        if user:
            print(f"✅ User found: {user}")
            print(f"Email: {user.get('email')}")
            print(f"Role: {user.get('role')}")
            print(f"Password hash: {user.get('password')[:20]}...")
            
            # Test password verification
            password = "password123"
            hashed_password = hashlib.sha256(password.encode()).hexdigest()
            
            if user['password'] == hashed_password:
                print("✅ Password verification successful")
            else:
                print("❌ Password verification failed")
                print(f"Expected: {hashed_password}")
                print(f"Got: {user['password']}")
        else:
            print("❌ User not found in database")
            
    except Exception as e:
        print(f"❌ Error retrieving user: {e}")

if __name__ == "__main__":
    test_user_retrieval() 