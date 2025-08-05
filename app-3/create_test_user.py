#!/usr/bin/env python3
"""
Script to create a test user in the database
"""

from database_helper import db_helper
import hashlib

def create_test_user():
    """Create a test user for testing"""
    
    # Test user data
    email = "employee@example.com"
    password = "password123"
    role = "employee"
    
    # Hash the password
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    
    try:
        # Check if user already exists
        existing_user = db_helper.get_user_by_email(email)
        if existing_user:
            print(f"✅ User {email} already exists")
            return existing_user['id']
        
        # Create new user
        user_id = db_helper.create_user(email, hashed_password, role)
        
        if user_id:
            print(f"✅ Test user created successfully!")
            print(f"Email: {email}")
            print(f"Password: {password}")
            print(f"Role: {role}")
            print(f"User ID: {user_id}")
            
            # Create employee record
            employee_id = db_helper.create_employee(
                user_id=user_id,
                full_name="Test Employee",
                email=email,
                phone="123-456-7890",
                department="IT",
                position="Software Developer",
                hire_date="2024-01-01",
                manager="John Manager",
                location="Remote",
                salary_band="Mid",
                employment_type="Full-time"
            )
            
            if employee_id:
                print(f"✅ Employee record created with ID: {employee_id}")
            else:
                print("❌ Failed to create employee record")
                
            return user_id
        else:
            print("❌ Failed to create test user")
            return None
            
    except Exception as e:
        print(f"❌ Error creating test user: {e}")
        return None

if __name__ == "__main__":
    create_test_user() 