#!/usr/bin/env python3
"""
Script to check users in the database
"""

from database_helper import db_helper

def check_users():
    """Check what users exist in the database"""
    
    print("👥 Checking Users in Database")
    print("=" * 40)
    
    try:
        # Check specific users
        test_users = [
            'employee@example.com',
            'admin@example.com',
            'test@example.com'
        ]
        
        for email in test_users:
            user = db_helper.get_user_by_email(email)
            if user:
                print(f"✅ User {email} exists")
                print(f"   Role: {user.get('role', 'N/A')}")
                print(f"   Password hash: {user.get('password', 'N/A')[:20]}...")
            else:
                print(f"❌ User {email} does not exist")
        
        print("\n" + "=" * 40)
        print("Creating test user if needed...")
        
        # Create a test user with known credentials
        import hashlib
        
        email = "test@example.com"
        password = "test123"
        role = "employee"
        
        # Hash the password
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        # Check if user exists
        existing_user = db_helper.get_user_by_email(email)
        if existing_user:
            print(f"✅ Test user {email} already exists")
        else:
            # Create new user
            user_id = db_helper.create_user(email, hashed_password, role)
            if user_id:
                print(f"✅ Test user created successfully!")
                print(f"Email: {email}")
                print(f"Password: {password}")
                print(f"Role: {role}")
                print(f"User ID: {user_id}")
            else:
                print("❌ Failed to create test user")
                
    except Exception as e:
        print(f"❌ Error checking users: {e}")

if __name__ == "__main__":
    check_users() 