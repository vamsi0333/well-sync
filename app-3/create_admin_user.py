#!/usr/bin/env python3
"""
Script to create an admin user in the database
"""

from database_helper import db_helper
import hashlib

def create_admin_user():
    """Create an admin user for testing"""
    
    # Admin user data
    email = "admin@example.com"
    password = "admin123"
    role = "admin"
    
    # Hash the password
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    
    try:
        # Check if user already exists
        existing_user = db_helper.get_user_by_email(email)
        if existing_user:
            print(f"✅ Admin user {email} already exists")
            return existing_user['id']
        
        # Create new admin user
        user_id = db_helper.create_user(email, hashed_password, role)
        
        if user_id:
            print(f"✅ Admin user created successfully!")
            print(f"Email: {email}")
            print(f"Password: {password}")
            print(f"Role: {role}")
            print(f"User ID: {user_id}")
            
            # Create employee record for admin
            employee_id = db_helper.create_employee(
                user_id=user_id,
                full_name="Admin User",
                email=email,
                phone="123-456-7890",
                department="Administration",
                position="System Administrator",
                hire_date="2024-01-01",
                manager="CEO",
                location="HQ",
                salary_band="Senior",
                employment_type="Full-time"
            )
            
            if employee_id:
                print(f"✅ Admin employee record created with ID: {employee_id}")
            else:
                print("❌ Failed to create admin employee record")
                
            return user_id
        else:
            print("❌ Failed to create admin user")
            return None
            
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        return None

if __name__ == "__main__":
    create_admin_user() 