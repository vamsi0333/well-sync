#!/usr/bin/env python3
"""
Script to create test users for RBAC testing
"""

import hashlib
from database_helper import db_helper

def create_test_users():
    """Create test users with different roles"""
    
    test_users = [
        {
            "email": "admin@example.com",
            "password": "admin123",
            "role": "admin",
            "full_name": "Admin User"
        },
        {
            "email": "it@example.com",
            "password": "it123", 
            "role": "it",
            "full_name": "IT Support"
        },
        {
            "email": "hr@example.com",
            "password": "hr123",
            "role": "hr", 
            "full_name": "HR Manager"
        },
        {
            "email": "employee@example.com",
            "password": "emp123",
            "role": "employee",
            "full_name": "Regular Employee"
        }
    ]
    
    print("🔧 Creating test users...")
    
    for user_data in test_users:
        # Hash the password
        hashed_password = hashlib.sha256(user_data["password"].encode()).hexdigest()
        
        # Check if user already exists
        existing_user = db_helper.get_user_by_email(user_data["email"])
        
        if existing_user:
            print(f"⚠️  User {user_data['email']} already exists")
            continue
        
        # Create user
        user_id = db_helper.create_user(
            email=user_data["email"],
            password=hashed_password,
            role=user_data["role"]
        )
        
        if user_id:
            print(f"✅ Created {user_data['role']} user: {user_data['email']}")
            
            # Create employee record
            employee_id = db_helper.create_employee(
                user_id=user_id,
                full_name=user_data["full_name"],
                email=user_data["email"],
                department="IT" if user_data["role"] == "it" else "HR" if user_data["role"] == "hr" else "General",
                position=user_data["role"].title(),
                hire_date="2024-01-01",
                manager="Admin",
                location="Office",
                salary_band="Mid-level",
                employment_type="Full-time"
            )
            
            if employee_id:
                print(f"✅ Created employee record for {user_data['email']}")
            else:
                print(f"❌ Failed to create employee record for {user_data['email']}")
        else:
            print(f"❌ Failed to create user {user_data['email']}")
    
    print("\n🏁 Test user creation complete!")
    print("\nTest Users:")
    print("- Admin: admin@example.com / admin123")
    print("- IT: it@example.com / it123") 
    print("- HR: hr@example.com / hr123")
    print("- Employee: employee@example.com / emp123")

if __name__ == "__main__":
    create_test_users() 