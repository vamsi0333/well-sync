#!/usr/bin/env python3
"""
Script to reset passwords for test users
"""

import hashlib
from database_helper import db_helper

def reset_passwords():
    """Reset passwords for test users"""
    
    test_users = [
        {
            "email": "admin@example.com",
            "password": "admin123",
            "role": "admin"
        },
        {
            "email": "it@example.com",
            "password": "it123",
            "role": "it"
        },
        {
            "email": "hr@example.com", 
            "password": "hr123",
            "role": "hr"
        },
        {
            "email": "employee@example.com",
            "password": "emp123",
            "role": "employee"
        }
    ]
    
    print("🔧 Resetting passwords for test users...")
    
    for user_data in test_users:
        # Hash the password
        hashed_password = hashlib.sha256(user_data["password"].encode()).hexdigest()
        
        try:
            connection = db_helper.get_connection()
            cursor = connection.cursor()
            
            # Update password
            cursor.execute("""
                UPDATE users 
                SET password = %s 
                WHERE email = %s
            """, (hashed_password, user_data["email"]))
            
            connection.commit()
            cursor.close()
            
            if cursor.rowcount > 0:
                print(f"✅ Updated password for {user_data['email']}")
            else:
                print(f"⚠️  No user found for {user_data['email']}")
                
        except Exception as e:
            print(f"❌ Error updating password for {user_data['email']}: {e}")
    
    print("\n🏁 Password reset complete!")

if __name__ == "__main__":
    reset_passwords() 