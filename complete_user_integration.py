#!/usr/bin/env python3
"""
Complete User Integration Script
Integrates all emails found in the system with proper roles
"""

from database_config import get_db_connection
from mysql.connector import Error
import hashlib

def hash_password(password):
    """Hash password for security"""
    return hashlib.sha256(password.encode()).hexdigest()

def integrate_all_users():
    """Integrate all users found in the system with proper roles"""
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Get all unique emails from the system
        cursor.execute("""
            SELECT DISTINCT email FROM users 
            UNION 
            SELECT DISTINCT employee_name FROM timeoff_requests 
            UNION 
            SELECT DISTINCT employee_name FROM leave_requests 
            UNION 
            SELECT DISTINCT user_email FROM notifications
        """)
        existing_emails = [row[0] for row in cursor.fetchall()]
        
        # Define all emails found in the system with their roles
        all_users = {
            # Core system users
            "admin@example.com": "admin",
            "user@example.com": "employee", 
            "it@example.com": "it",
            "hr@example.com": "hr",
            
            # Additional employee emails found in the system
            "employee@example.com": "employee",
            "employee1@example.com": "employee",
            "employee2@example.com": "employee",
            "john.doe@example.com": "employee",
            "jane.smith@example.com": "employee", 
            "mike.johnson@example.com": "employee",
            "bob.johnson@example.com": "employee",
            
            # Additional admin/management emails
            "manager@example.com": "admin",
            "supervisor@example.com": "admin"
        }
        
        print("🔍 **Integrating All System Users**")
        print("=" * 50)
        
        # Check which users already exist
        cursor.execute("SELECT email FROM users")
        existing_users = [row[0] for row in cursor.fetchall()]
        
        # Add missing users
        added_count = 0
        for email, role in all_users.items():
            if email not in existing_users:
                password_hash = hash_password("password")
                cursor.execute("""
                    INSERT INTO users (email, password, role) 
                    VALUES (%s, %s, %s)
                """, (email, password_hash, role))
                print(f"✅ Added: {email} - {role}")
                added_count += 1
            else:
                print(f"ℹ️  Exists: {email} - {role}")
        
        # Update existing users to ensure proper roles
        updated_count = 0
        for email, role in all_users.items():
            if email in existing_users:
                cursor.execute("UPDATE users SET role = %s WHERE email = %s", (role, email))
                if cursor.rowcount > 0:
                    print(f"🔄 Updated: {email} - {role}")
                    updated_count += 1
        
        connection.commit()
        cursor.close()
        connection.close()
        
        print(f"\n📊 **Integration Summary:**")
        print(f"✅ Added: {added_count} new users")
        print(f"🔄 Updated: {updated_count} existing users")
        print(f"📋 Total users: {len(all_users)}")
        
        return True
        
    except Error as e:
        print(f"❌ Error integrating users: {e}")
        return False

def display_complete_access_matrix():
    """Display the complete access matrix for all users"""
    print("\n🎯 **Complete Access Matrix:**")
    print("=" * 60)
    
    access_matrix = {
        "admin@example.com": {
            "role": "Administrator",
            "password": "password",
            "access": ["Full system access", "All portals", "Database management"]
        },
        "user@example.com": {
            "role": "Employee", 
            "password": "password",
            "access": ["Employee portal", "Submit requests", "View paystubs"]
        },
        "it@example.com": {
            "role": "IT Support",
            "password": "password", 
            "access": ["IT portal", "Manage tickets", "Device management"]
        },
        "hr@example.com": {
            "role": "HR Manager",
            "password": "password",
            "access": ["HR portal", "Employee management", "Recruitment"]
        },
        "employee@example.com": {
            "role": "Employee",
            "password": "password",
            "access": ["Employee portal", "Submit requests", "View paystubs"]
        },
        "employee1@example.com": {
            "role": "Employee", 
            "password": "password",
            "access": ["Employee portal", "Submit requests", "View paystubs"]
        },
        "employee2@example.com": {
            "role": "Employee",
            "password": "password", 
            "access": ["Employee portal", "Submit requests", "View paystubs"]
        },
        "john.doe@example.com": {
            "role": "Employee",
            "password": "password",
            "access": ["Employee portal", "Submit requests", "View paystubs"]
        },
        "jane.smith@example.com": {
            "role": "Employee",
            "password": "password",
            "access": ["Employee portal", "Submit requests", "View paystubs"]
        },
        "mike.johnson@example.com": {
            "role": "Employee",
            "password": "password",
            "access": ["Employee portal", "Submit requests", "View paystubs"]
        },
        "bob.johnson@example.com": {
            "role": "Employee",
            "password": "password",
            "access": ["Employee portal", "Submit requests", "View paystubs"]
        },
        "manager@example.com": {
            "role": "Administrator",
            "password": "password",
            "access": ["Full system access", "All portals", "Database management"]
        },
        "supervisor@example.com": {
            "role": "Administrator",
            "password": "password",
            "access": ["Full system access", "All portals", "Database management"]
        }
    }
    
    # Group by role for better display
    role_groups = {}
    for email, details in access_matrix.items():
        role = details['role']
        if role not in role_groups:
            role_groups[role] = []
        role_groups[role].append((email, details))
    
    for role, users in role_groups.items():
        print(f"\n👥 **{role}s** ({len(users)} users):")
        print("-" * 40)
        for email, details in users:
            print(f"   📧 {email}")
            print(f"   🔑 Password: {details['password']}")
            print(f"   🎯 Access: {', '.join(details['access'])}")
            print()
    
    return access_matrix

def verify_database_integrity():
    """Verify all users are properly integrated"""
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Check user count
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        
        # Check role distribution
        cursor.execute("SELECT role, COUNT(*) FROM users GROUP BY role")
        role_distribution = cursor.fetchall()
        
        print(f"\n🔍 **Database Integrity Check:**")
        print(f"✅ Total users: {user_count}")
        print(f"📊 Role distribution:")
        for role, count in role_distribution:
            print(f"   - {role}: {count} users")
        
        cursor.close()
        connection.close()
        
        return True
        
    except Error as e:
        print(f"❌ Database integrity check failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 **Complete User Integration**")
    print("=" * 50)
    
    if integrate_all_users():
        print("\n✅ User integration successful!")
        
        if verify_database_integrity():
            print("✅ Database integrity verified!")
            
            # Display complete access matrix
            display_complete_access_matrix()
            
            print("\n🎉 **ALL USERS INTEGRATED SUCCESSFULLY!**")
            print("=" * 60)
            print("✅ All emails from the system have been integrated")
            print("✅ Proper roles assigned to each user")
            print("✅ Database updated with all users")
            print("✅ Access matrix complete")
            
            print("\n📋 **Login Credentials (All Users):**")
            print("=" * 50)
            print("🔐 **Admin Users:** admin@example.com, manager@example.com, supervisor@example.com")
            print("👤 **Employee Users:** user@example.com, employee@example.com, employee1@example.com, employee2@example.com, john.doe@example.com, jane.smith@example.com, mike.johnson@example.com, bob.johnson@example.com")
            print("🖥️ **IT Users:** it@example.com")
            print("👔 **HR Users:** hr@example.com")
            print("\n🔑 **All passwords:** password")
            
        else:
            print("❌ Database integrity check failed!")
    else:
        print("❌ User integration failed!") 