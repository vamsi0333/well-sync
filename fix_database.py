#!/usr/bin/env python3
"""
Database Fix Script
Fixes schema issues and creates missing tables
"""

from database_config import get_db_connection
from mysql.connector import Error

def fix_database_schema():
    """Fix database schema issues"""
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Fix users table role column
        cursor.execute("ALTER TABLE users MODIFY COLUMN role VARCHAR(100) DEFAULT 'employee'")
        
        # Create missing tables
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_email VARCHAR(255) NOT NULL,
                message TEXT NOT NULL,
                type VARCHAR(50) DEFAULT 'info',
                read_status BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS timeoff_requests (
                id INT AUTO_INCREMENT PRIMARY KEY,
                employee_name VARCHAR(255) NOT NULL,
                start_date DATE NOT NULL,
                end_date DATE NOT NULL,
                reason TEXT,
                status VARCHAR(50) DEFAULT 'pending',
                submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                days_requested INT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS leave_requests (
                id INT AUTO_INCREMENT PRIMARY KEY,
                employee_id VARCHAR(255) NOT NULL,
                employee_name VARCHAR(255) NOT NULL,
                leave_type VARCHAR(100) NOT NULL,
                start_date DATE NOT NULL,
                end_date DATE NOT NULL,
                total_days INT,
                reason TEXT,
                status VARCHAR(50) DEFAULT 'pending',
                submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                approved_by VARCHAR(255),
                approved_at TIMESTAMP NULL,
                notes TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id INT AUTO_INCREMENT PRIMARY KEY,
                type VARCHAR(100),
                text TEXT NOT NULL,
                department VARCHAR(100),
                priority VARCHAR(50),
                status VARCHAR(50) DEFAULT 'pending',
                submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                anonymous BOOLEAN DEFAULT TRUE
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_groups (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                created_by VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS group_members (
                id INT AUTO_INCREMENT PRIMARY KEY,
                group_id INT,
                member_name VARCHAR(255) NOT NULL,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (group_id) REFERENCES user_groups(id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_messages (
                id INT AUTO_INCREMENT PRIMARY KEY,
                group_id INT,
                sender_name VARCHAR(255) NOT NULL,
                message TEXT,
                message_type VARCHAR(50) DEFAULT 'text',
                file_name VARCHAR(255),
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (group_id) REFERENCES user_groups(id)
            )
        """)
        
        connection.commit()
        cursor.close()
        connection.close()
        
        print("✅ Database schema fixed successfully!")
        return True
        
    except Error as e:
        print(f"❌ Error fixing database schema: {e}")
        return False

def setup_users_with_fixed_schema():
    """Setup users with the fixed schema"""
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Clear existing users
        cursor.execute("DELETE FROM users")
        connection.commit()
        
        # Create users with proper roles
        users_data = [
            ("admin@example.com", "admin"),
            ("user@example.com", "employee"),
            ("it@example.com", "it"),
            ("hr@example.com", "hr")
        ]
        
        for email, role in users_data:
            password_hash = "5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8"  # "password"
            cursor.execute("""
                INSERT INTO users (email, password, role) 
                VALUES (%s, %s, %s)
            """, (email, password_hash, role))
        
        connection.commit()
        cursor.close()
        connection.close()
        
        print("✅ Users setup completed successfully!")
        return True
        
    except Error as e:
        print(f"❌ Error setting up users: {e}")
        return False

if __name__ == "__main__":
    print("🔧 **Database Schema Fix**")
    print("=" * 40)
    
    if fix_database_schema():
        print("✅ Schema fixed!")
        
        if setup_users_with_fixed_schema():
            print("✅ Users setup complete!")
            print("\n🎉 **Database is now ready!**")
        else:
            print("❌ User setup failed!")
    else:
        print("❌ Schema fix failed!") 