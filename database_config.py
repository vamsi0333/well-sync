import mysql.connector
from mysql.connector import Error
import pymysql

# Database Configuration
DB_CONFIG = {
    'host': 'quadprserver.mysql.database.azure.com',
    'port': 3306,
    'user': 'adminuser',
    'password': 'Quad@2025',
    'database': 'employee_portal',
    'charset': 'utf8mb4',
    'autocommit': True
}

def get_db_connection():
    """Create and return a database connection"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        if connection.is_connected():
            return connection
    except Error as e:
        print(f"Error connecting to MySQL Database: {e}")
        return None

def get_pymysql_connection():
    """Create and return a PyMySQL connection (for some operations)"""
    try:
        connection = pymysql.connect(**DB_CONFIG)
        return connection
    except Exception as e:
        print(f"Error connecting to MySQL Database with PyMySQL: {e}")
        return None

def test_connection():
    """Test the database connection"""
    connection = get_db_connection()
    if connection:
        cursor = connection.cursor()
        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()
        print(f"Connected to MySQL Database. Version: {version[0]}")
        cursor.close()
        connection.close()
        return True
    return False

def create_tables():
    """Create necessary tables if they don't exist"""
    connection = get_db_connection()
    if not connection:
        return False
    
    cursor = connection.cursor()
    
    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            email VARCHAR(255) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            role VARCHAR(100) DEFAULT 'employee',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Employees table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT,
            full_name VARCHAR(255) NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            phone VARCHAR(20),
            department VARCHAR(100),
            position VARCHAR(100),
            hire_date DATE,
            manager VARCHAR(255),
            location VARCHAR(100),
            salary_band VARCHAR(50),
            employment_type VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    
    # Tickets table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tickets (
            id INT AUTO_INCREMENT PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            description TEXT,
            priority VARCHAR(50) DEFAULT 'medium',
            status VARCHAR(50) DEFAULT 'open',
            user_email VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
    """)
    
    # Timeoff requests table
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
    
    # Leave requests table
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
    
    # Feedback table
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
    
    # Job applications table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS job_applications (
            id INT AUTO_INCREMENT PRIMARY KEY,
            job_id INT,
            applicant_name VARCHAR(255) NOT NULL,
            applicant_email VARCHAR(255) NOT NULL,
            resume_path VARCHAR(500),
            cover_letter TEXT,
            status VARCHAR(50) DEFAULT 'pending',
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            reviewed_by VARCHAR(255),
            reviewed_at TIMESTAMP NULL
        )
    """)
    
    # Notifications table
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
    
    # Groups table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_groups (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            description TEXT,
            created_by VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Group members table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS group_members (
            id INT AUTO_INCREMENT PRIMARY KEY,
            group_id INT,
            member_name VARCHAR(255) NOT NULL,
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (group_id) REFERENCES user_groups(id)
        )
    """)
    
    # Chat messages table
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
    print("Database tables created successfully!")
    return True

if __name__ == "__main__":
    # Test the connection
    if test_connection():
        # Create tables
        create_tables()
    else:
        print("Failed to connect to database!") 