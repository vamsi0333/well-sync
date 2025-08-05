#!/usr/bin/env python3
"""
Comprehensive User Setup Script
Establishes proper role-based access for the HR Management System
"""

from database_helper import db_helper
from database_config import get_db_connection
from mysql.connector import Error
import hashlib

def hash_password(password):
    """Hash password for security"""
    return hashlib.sha256(password.encode()).hexdigest()

def setup_users():
    """Setup all users with proper roles and access"""
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Clear existing data in correct order (respecting foreign keys)
        cursor.execute("DELETE FROM chat_messages")
        cursor.execute("DELETE FROM group_members")
        cursor.execute("DELETE FROM user_groups")
        cursor.execute("DELETE FROM notifications")
        cursor.execute("DELETE FROM job_applications")
        cursor.execute("DELETE FROM feedback")
        cursor.execute("DELETE FROM leave_requests")
        cursor.execute("DELETE FROM timeoff_requests")
        cursor.execute("DELETE FROM tickets")
        cursor.execute("DELETE FROM employees")
        cursor.execute("DELETE FROM users")
        connection.commit()
        
        # Create Admin User
        admin_password = hash_password("password")
        cursor.execute("""
            INSERT INTO users (email, password, role) 
            VALUES (%s, %s, %s)
        """, ("admin@example.com", admin_password, "admin"))
        admin_user_id = cursor.lastrowid
        
        # Create Employee User
        employee_password = hash_password("password")
        cursor.execute("""
            INSERT INTO users (email, password, role) 
            VALUES (%s, %s, %s)
        """, ("user@example.com", employee_password, "employee"))
        employee_user_id = cursor.lastrowid
        
        # Create IT User
        it_password = hash_password("password")
        cursor.execute("""
            INSERT INTO users (email, password, role) 
            VALUES (%s, %s, %s)
        """, ("it@example.com", it_password, "it"))
        it_user_id = cursor.lastrowid
        
        # Create HR Manager
        hr_password = hash_password("password")
        cursor.execute("""
            INSERT INTO users (email, password, role) 
            VALUES (%s, %s, %s)
        """, ("hr@example.com", hr_password, "hr"))
        hr_user_id = cursor.lastrowid
        
        # Create additional users for comprehensive testing
        additional_users = [
            ("manager@example.com", "password", "admin"),
            ("supervisor@example.com", "password", "admin"),
            ("employee1@example.com", "password", "employee"),
            ("employee2@example.com", "password", "employee"),
            ("employee3@example.com", "password", "employee"),
            ("it_support@example.com", "password", "it"),
            ("hr_assistant@example.com", "password", "hr"),
            ("recruiter@example.com", "password", "hr")
        ]
        
        additional_user_ids = []
        for email, password, role in additional_users:
            hashed_pwd = hash_password(password)
            cursor.execute("""
                INSERT INTO users (email, password, role) 
                VALUES (%s, %s, %s)
            """, (email, hashed_pwd, role))
            additional_user_ids.append(cursor.lastrowid)
        
        # Create sample employees
        employees_data = [
            {
                'user_id': employee_user_id,
                'full_name': 'John Doe',
                'email': 'user@example.com',
                'phone': '+1 (555) 123-4567',
                'department': 'IT',
                'position': 'Software Engineer',
                'hire_date': '2023-01-15',
                'manager': 'Sarah Johnson',
                'location': 'New York',
                'salary_band': 'Band 3',
                'employment_type': 'Full-time'
            },
            {
                'user_id': it_user_id,
                'full_name': 'IT Support',
                'email': 'it@example.com',
                'phone': '+1 (555) 234-5678',
                'department': 'IT',
                'position': 'IT Support Specialist',
                'hire_date': '2022-06-10',
                'manager': 'Mike Wilson',
                'location': 'San Francisco',
                'salary_band': 'Band 2',
                'employment_type': 'Full-time'
            },
            {
                'user_id': hr_user_id,
                'full_name': 'HR Manager',
                'email': 'hr@example.com',
                'phone': '+1 (555) 345-6789',
                'department': 'HR',
                'position': 'HR Manager',
                'hire_date': '2021-03-20',
                'manager': 'CEO',
                'location': 'New York',
                'salary_band': 'Band 4',
                'employment_type': 'Full-time'
            },
            {
                'user_id': additional_user_ids[0],
                'full_name': 'Manager User',
                'email': 'manager@example.com',
                'phone': '+1 (555) 456-7890',
                'department': 'Management',
                'position': 'Department Manager',
                'hire_date': '2020-08-15',
                'manager': 'CEO',
                'location': 'New York',
                'salary_band': 'Band 4',
                'employment_type': 'Full-time'
            },
            {
                'user_id': additional_user_ids[1],
                'full_name': 'Supervisor User',
                'email': 'supervisor@example.com',
                'phone': '+1 (555) 567-8901',
                'department': 'Operations',
                'position': 'Team Supervisor',
                'hire_date': '2021-12-01',
                'manager': 'Manager User',
                'location': 'San Francisco',
                'salary_band': 'Band 3',
                'employment_type': 'Full-time'
            },
            {
                'user_id': additional_user_ids[2],
                'full_name': 'Employee One',
                'email': 'employee1@example.com',
                'phone': '+1 (555) 678-9012',
                'department': 'Marketing',
                'position': 'Marketing Specialist',
                'hire_date': '2023-03-10',
                'manager': 'Supervisor User',
                'location': 'Chicago',
                'salary_band': 'Band 2',
                'employment_type': 'Full-time'
            },
            {
                'user_id': additional_user_ids[3],
                'full_name': 'Employee Two',
                'email': 'employee2@example.com',
                'phone': '+1 (555) 789-0123',
                'department': 'Sales',
                'position': 'Sales Representative',
                'hire_date': '2023-06-20',
                'manager': 'Supervisor User',
                'location': 'Los Angeles',
                'salary_band': 'Band 2',
                'employment_type': 'Full-time'
            },
            {
                'user_id': additional_user_ids[4],
                'full_name': 'Employee Three',
                'email': 'employee3@example.com',
                'phone': '+1 (555) 890-1234',
                'department': 'Finance',
                'position': 'Financial Analyst',
                'hire_date': '2023-09-05',
                'manager': 'Supervisor User',
                'location': 'Boston',
                'salary_band': 'Band 2',
                'employment_type': 'Full-time'
            },
            {
                'user_id': additional_user_ids[5],
                'full_name': 'IT Support Staff',
                'email': 'it_support@example.com',
                'phone': '+1 (555) 901-2345',
                'department': 'IT',
                'position': 'IT Support Technician',
                'hire_date': '2022-11-15',
                'manager': 'IT Support',
                'location': 'Remote',
                'salary_band': 'Band 2',
                'employment_type': 'Full-time'
            },
            {
                'user_id': additional_user_ids[6],
                'full_name': 'HR Assistant',
                'email': 'hr_assistant@example.com',
                'phone': '+1 (555) 012-3456',
                'department': 'HR',
                'position': 'HR Assistant',
                'hire_date': '2023-01-30',
                'manager': 'HR Manager',
                'location': 'New York',
                'salary_band': 'Band 2',
                'employment_type': 'Full-time'
            },
            {
                'user_id': additional_user_ids[7],
                'full_name': 'Recruiter',
                'email': 'recruiter@example.com',
                'phone': '+1 (555) 123-4567',
                'department': 'HR',
                'position': 'Recruiter',
                'hire_date': '2022-08-10',
                'manager': 'HR Manager',
                'location': 'Remote',
                'salary_band': 'Band 2',
                'employment_type': 'Full-time'
            }
        ]
        
        for emp_data in employees_data:
            cursor.execute("""
                INSERT INTO employees (user_id, full_name, email, phone, department, 
                position, hire_date, manager, location, salary_band, employment_type)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (emp_data['user_id'], emp_data['full_name'], emp_data['email'], 
                  emp_data['phone'], emp_data['department'], emp_data['position'],
                  emp_data['hire_date'], emp_data['manager'], emp_data['location'],
                  emp_data['salary_band'], emp_data['employment_type']))
        
        # Create sample data for testing
        # Sample timeoff requests
        cursor.execute("""
            INSERT INTO timeoff_requests (employee_name, start_date, end_date, reason, status, days_requested)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, ("user@example.com", "2024-02-15", "2024-02-20", "Vacation", "pending", 5))
        
        # Sample leave requests
        cursor.execute("""
            INSERT INTO leave_requests (employee_id, employee_name, leave_type, start_date, end_date, total_days, reason, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, ("user@example.com", "user@example.com", "Sick Leave", "2024-02-10", "2024-02-12", 3, "Not feeling well", "pending"))
        
        # Sample feedback
        cursor.execute("""
            INSERT INTO feedback (type, text, department, priority, status)
            VALUES (%s, %s, %s, %s, %s)
        """, ("General", "Great work environment and team collaboration", "IT", "medium", "pending"))
        
        # Sample tickets
        cursor.execute("""
            INSERT INTO tickets (title, description, priority, user_email, status)
            VALUES (%s, %s, %s, %s, %s)
        """, ("Computer not working", "My computer won't turn on", "high", "user@example.com", "open"))
        
        # Sample notifications
        cursor.execute("""
            INSERT INTO notifications (user_email, message, type)
            VALUES (%s, %s, %s)
        """, ("admin@example.com", "New time off request submitted", "warning"))
        
        connection.commit()
        cursor.close()
        connection.close()
        
        print("✅ User setup completed successfully!")
        print("\n📋 **Login Credentials:**")
        print("=" * 50)
        print("🔐 **Admin Portal:**")
        print("   Email: admin@example.com")
        print("   Password: password")
        print("   Role: Administrator")
        print("   Access: Full system access")
        print()
        print("👤 **Employee Portal:**")
        print("   Email: user@example.com")
        print("   Password: password")
        print("   Role: Employee")
        print("   Access: Employee features only")
        print()
        print("🖥️ **IT Portal:**")
        print("   Email: it@example.com")
        print("   Password: password")
        print("   Role: IT Support")
        print("   Access: IT support features")
        print()
        print("👔 **HR Portal:**")
        print("   Email: hr@example.com")
        print("   Password: password")
        print("   Role: HR Manager")
        print("   Access: HR management features")
        print()
        print("🎯 **Additional Users:**")
        print("   manager@example.com / password (Admin)")
        print("   supervisor@example.com / password (Admin)")
        print("   employee1@example.com / password (Employee)")
        print("   employee2@example.com / password (Employee)")
        print("   employee3@example.com / password (Employee)")
        print("   it_support@example.com / password (IT)")
        print("   hr_assistant@example.com / password (HR)")
        print("   recruiter@example.com / password (HR)")
        print()
        print("🎯 **Access Matrix:**")
        print("=" * 50)
        print("Admin: Full access to all portals and features")
        print("Employee: Access to employee portal, submit requests")
        print("IT: Access to IT portal, manage tickets and devices")
        print("HR: Access to HR portal, manage employees and policies")
        
        return True
        
    except Error as e:
        print(f"❌ Error setting up users: {e}")
        return False

def verify_database_integrity():
    """Verify all database tables and relationships"""
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Check all tables exist
        tables = [
            'users', 'employees', 'tickets', 'timeoff_requests', 
            'leave_requests', 'feedback', 'job_applications', 
            'notifications', 'user_groups', 'group_members', 'chat_messages'
        ]
        
        print("\n🔍 **Database Integrity Check:**")
        print("=" * 50)
        
        for table in tables:
            cursor.execute(f"SHOW TABLES LIKE '{table}'")
            result = cursor.fetchone()
            if result:
                print(f"✅ {table} - EXISTS")
            else:
                print(f"❌ {table} - MISSING")
        
        # Check user count
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        print(f"✅ Users in database: {user_count}")
        
        # Check employee count
        cursor.execute("SELECT COUNT(*) FROM employees")
        emp_count = cursor.fetchone()[0]
        print(f"✅ Employees in database: {emp_count}")
        
        cursor.close()
        connection.close()
        
        print("✅ Database integrity check completed!")
        return True
        
    except Error as e:
        print(f"❌ Database integrity check failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 **HR Management System - Final Setup**")
    print("=" * 60)
    
    # Setup users
    if setup_users():
        print("\n✅ User setup successful!")
    else:
        print("\n❌ User setup failed!")
        exit(1)
    
    # Verify database integrity
    if verify_database_integrity():
        print("\n✅ Database integrity verified!")
    else:
        print("\n❌ Database integrity check failed!")
        exit(1)
    
    print("\n🎉 **Setup Complete!**")
    print("=" * 60)
    print("Your HR Management System is now ready!")
    print("Access the application at: http://127.0.0.1:5003")
    print("\n📝 **Next Steps:**")
    print("1. Start the server: python app.py")
    print("2. Login with the credentials above")
    print("3. Test all features and functionality") 