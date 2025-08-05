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
    
    # Timesheets table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS timesheets (
            id INT AUTO_INCREMENT PRIMARY KEY,
            employee_id VARCHAR(255) NOT NULL,
            employee_name VARCHAR(255) NOT NULL,
            date DATE NOT NULL,
            hours_worked DECIMAL(5,2) NOT NULL,
            project VARCHAR(255),
            task_description TEXT,
            status VARCHAR(50) DEFAULT 'pending',
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            approved_by VARCHAR(255),
            approved_at TIMESTAMP NULL
        )
    """)
    
    # Badges table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS badges (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            description TEXT,
            icon VARCHAR(50),
            category VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # User badges table (many-to-many relationship)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_badges (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id VARCHAR(255) NOT NULL,
            badge_id INT NOT NULL,
            awarded_by VARCHAR(255),
            awarded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            reason TEXT,
            FOREIGN KEY (badge_id) REFERENCES badges(id)
        )
    """)
    
    # Ticket comments table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ticket_comments (
            id INT AUTO_INCREMENT PRIMARY KEY,
            ticket_id INT NOT NULL,
            comment TEXT NOT NULL,
            admin_name VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (ticket_id) REFERENCES tickets(id) ON DELETE CASCADE
        )
    """)
    
    # Feedback comments table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS feedback_comments (
            id INT AUTO_INCREMENT PRIMARY KEY,
            feedback_id INT NOT NULL,
            comment TEXT NOT NULL,
            admin_name VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (feedback_id) REFERENCES feedback(id) ON DELETE CASCADE
        )
    """)
    
    # Timesheet comments table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS timesheet_comments (
            id INT AUTO_INCREMENT PRIMARY KEY,
            timesheet_id INT NOT NULL,
            comment TEXT NOT NULL,
            admin_name VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (timesheet_id) REFERENCES timesheets(id) ON DELETE CASCADE
        )
    """)
    
    # Leave request comments table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS leave_comments (
            id INT AUTO_INCREMENT PRIMARY KEY,
            leave_id INT NOT NULL,
            comment TEXT NOT NULL,
            admin_name VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (leave_id) REFERENCES leave_requests(id) ON DELETE CASCADE
        )
    """)
    
    # Service requests table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS service_requests (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_email VARCHAR(255) NOT NULL,
            request_type VARCHAR(100) NOT NULL,
            subject VARCHAR(255) NOT NULL,
            description TEXT NOT NULL,
            priority ENUM('low', 'medium', 'high', 'urgent') DEFAULT 'medium',
            status ENUM('pending', 'assigned', 'in_progress', 'completed', 'cancelled') DEFAULT 'pending',
            assigned_to VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
    """)
    
    # Service request comments table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS service_request_comments (
            id INT AUTO_INCREMENT PRIMARY KEY,
            request_id INT NOT NULL,
            comment TEXT NOT NULL,
            admin_name VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (request_id) REFERENCES service_requests(id) ON DELETE CASCADE
        )
    """)
    
    # Internal jobs table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS internal_jobs (
            id INT AUTO_INCREMENT PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            department VARCHAR(100) NOT NULL,
            location VARCHAR(100) NOT NULL,
            job_type ENUM('full-time', 'part-time', 'contract', 'internship') DEFAULT 'full-time',
            description TEXT NOT NULL,
            requirements TEXT NOT NULL,
            salary_range VARCHAR(100),
            posted_date DATE NOT NULL,
            deadline_date DATE NOT NULL,
            status ENUM('active', 'closed', 'draft') DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Internal job applications table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS internal_job_applications (
            id INT AUTO_INCREMENT PRIMARY KEY,
            job_id INT NOT NULL,
            user_email VARCHAR(255) NOT NULL,
            resume_path VARCHAR(500),
            cover_letter TEXT,
            status ENUM('pending', 'reviewed', 'shortlisted', 'rejected', 'hired') DEFAULT 'pending',
            applied_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            reviewed_date TIMESTAMP NULL,
            reviewed_by VARCHAR(255),
            notes TEXT,
            FOREIGN KEY (job_id) REFERENCES internal_jobs(id) ON DELETE CASCADE
        )
    """)
    
    # Skills assessments table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS skills_assessments (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_email VARCHAR(255) NOT NULL,
            test_type VARCHAR(100) NOT NULL,
            score INT NOT NULL,
            total_questions INT NOT NULL,
            answers JSON,
            completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Learning roadmaps table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS learning_roadmaps (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_email VARCHAR(255) NOT NULL,
            assessment_id INT,
            improvement_areas JSON,
            recommended_path JSON,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (assessment_id) REFERENCES skills_assessments(id) ON DELETE SET NULL
        )
    """)
    
    # Courses table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS courses (
            id INT AUTO_INCREMENT PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            description TEXT,
            content TEXT,
            questions JSON,
            passing_score INT DEFAULT 70,
            badge VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Quiz results table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quiz_results (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_email VARCHAR(255) NOT NULL,
            course_id INT NOT NULL,
            score INT NOT NULL,
            total_questions INT NOT NULL,
            percentage DECIMAL(5,2) NOT NULL,
            passed BOOLEAN NOT NULL,
            completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE
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