from database_config import get_db_connection, get_pymysql_connection
from mysql.connector import Error
from datetime import datetime
import json

class DatabaseHelper:
    def __init__(self):
        self.connection = None
    
    def get_connection(self):
        """Get database connection"""
        if not self.connection or not self.connection.is_connected():
            self.connection = get_db_connection()
        return self.connection
    
    def close_connection(self):
        """Close database connection"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
    
    # User Management
    def create_user(self, email, password, role='employee'):
        """Create a new user"""
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            
            cursor.execute("""
                INSERT INTO users (email, password, role) 
                VALUES (%s, %s, %s)
            """, (email, password, role))
            
            connection.commit()
            user_id = cursor.lastrowid
            cursor.close()
            return user_id
        except Error as e:
            print(f"Error creating user: {e}")
            return None
    
    def get_user_by_email(self, email):
        """Get user by email"""
        try:
            connection = self.get_connection()
            cursor = connection.cursor(dictionary=True)
            
            cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
            user = cursor.fetchone()
            cursor.close()
            return user
        except Error as e:
            print(f"Error getting user: {e}")
            return None
    
    # Employee Management
    def create_employee(self, user_id, full_name, email, **kwargs):
        """Create a new employee"""
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            
            cursor.execute("""
                INSERT INTO employees (user_id, full_name, email, phone, department, 
                position, hire_date, manager, location, salary_band, employment_type)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (user_id, full_name, email, kwargs.get('phone'), kwargs.get('department'),
                  kwargs.get('position'), kwargs.get('hire_date'), kwargs.get('manager'),
                  kwargs.get('location'), kwargs.get('salary_band'), kwargs.get('employment_type')))
            
            connection.commit()
            employee_id = cursor.lastrowid
            cursor.close()
            return employee_id
        except Error as e:
            print(f"Error creating employee: {e}")
            return None
    
    def get_all_employees(self):
        """Get all employees"""
        try:
            connection = self.get_connection()
            cursor = connection.cursor(dictionary=True)
            
            cursor.execute("SELECT * FROM employees ORDER BY created_at DESC")
            employees = cursor.fetchall()
            cursor.close()
            return employees
        except Error as e:
            print(f"Error getting employees: {e}")
            return []
    
    # Ticket Management
    def create_ticket(self, title, description, priority, user_email, attachments=None):
        """Create a new ticket"""
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            
            cursor.execute("""
                INSERT INTO tickets (title, description, priority, user_email)
                VALUES (%s, %s, %s, %s)
            """, (title, description, priority, user_email))
            
            connection.commit()
            ticket_id = cursor.lastrowid
            cursor.close()
            return ticket_id
        except Error as e:
            print(f"Error creating ticket: {e}")
            return None
    
    def get_tickets_by_user(self, user_email):
        """Get tickets by user email"""
        try:
            connection = self.get_connection()
            cursor = connection.cursor(dictionary=True)
            
            cursor.execute("SELECT * FROM tickets WHERE user_email = %s ORDER BY created_at DESC", (user_email,))
            tickets = cursor.fetchall()
            cursor.close()
            return tickets
        except Error as e:
            print(f"Error getting tickets: {e}")
            return []
    
    def get_all_tickets(self):
        """Get all tickets"""
        try:
            connection = self.get_connection()
            cursor = connection.cursor(dictionary=True)
            
            cursor.execute("SELECT * FROM tickets ORDER BY created_at DESC")
            tickets = cursor.fetchall()
            cursor.close()
            return tickets
        except Error as e:
            print(f"Error getting all tickets: {e}")
            return []
    
    def update_ticket_status(self, ticket_id, status):
        """Update ticket status"""
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            
            cursor.execute("UPDATE tickets SET status = %s WHERE id = %s", (status, ticket_id))
            connection.commit()
            cursor.close()
            return True
        except Error as e:
            print(f"Error updating ticket: {e}")
            return False
    
    # Timeoff Management
    def create_timeoff_request(self, employee_name, start_date, end_date, reason):
        """Create a new timeoff request"""
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            
            # Calculate days requested
            start = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d')
            days_requested = (end - start).days + 1
            
            cursor.execute("""
                INSERT INTO timeoff_requests (employee_name, start_date, end_date, reason, days_requested)
                VALUES (%s, %s, %s, %s, %s)
            """, (employee_name, start_date, end_date, reason, days_requested))
            
            connection.commit()
            request_id = cursor.lastrowid
            cursor.close()
            return request_id
        except Error as e:
            print(f"Error creating timeoff request: {e}")
            return None
    
    def get_all_timeoff_requests(self):
        """Get all timeoff requests"""
        try:
            connection = self.get_connection()
            cursor = connection.cursor(dictionary=True)
            
            cursor.execute("SELECT * FROM timeoff_requests ORDER BY submitted_at DESC")
            requests = cursor.fetchall()
            cursor.close()
            return requests
        except Error as e:
            print(f"Error getting timeoff requests: {e}")
            return []
    
    def update_timeoff_status(self, request_id, status):
        """Update timeoff request status"""
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            
            cursor.execute("UPDATE timeoff_requests SET status = %s WHERE id = %s", (status, request_id))
            connection.commit()
            cursor.close()
            return True
        except Error as e:
            print(f"Error updating timeoff request: {e}")
            return False
    
    # Leave Management
    def create_leave_request(self, employee_id, employee_name, leave_type, start_date, end_date, reason):
        """Create a new leave request"""
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            
            # Calculate total days
            start = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d')
            total_days = (end - start).days + 1
            
            cursor.execute("""
                INSERT INTO leave_requests (employee_id, employee_name, leave_type, start_date, end_date, total_days, reason)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (employee_id, employee_name, leave_type, start_date, end_date, total_days, reason))
            
            connection.commit()
            request_id = cursor.lastrowid
            cursor.close()
            return request_id
        except Error as e:
            print(f"Error creating leave request: {e}")
            return None
    
    def get_leave_requests_by_employee(self, employee_id):
        """Get leave requests by employee"""
        try:
            connection = self.get_connection()
            cursor = connection.cursor(dictionary=True)
            
            cursor.execute("SELECT * FROM leave_requests WHERE employee_id = %s ORDER BY submitted_at DESC", (employee_id,))
            requests = cursor.fetchall()
            cursor.close()
            return requests
        except Error as e:
            print(f"Error getting leave requests: {e}")
            return []
    
    def get_all_leave_requests(self):
        """Get all leave requests"""
        try:
            connection = self.get_connection()
            cursor = connection.cursor(dictionary=True)
            
            cursor.execute("SELECT * FROM leave_requests ORDER BY submitted_at DESC")
            requests = cursor.fetchall()
            cursor.close()
            return requests
        except Error as e:
            print(f"Error getting all leave requests: {e}")
            return []
    
    def update_leave_status(self, request_id, status, approved_by=None):
        """Update leave request status"""
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            
            if approved_by:
                cursor.execute("""
                    UPDATE leave_requests SET status = %s, approved_by = %s, approved_at = NOW() 
                    WHERE id = %s
                """, (status, approved_by, request_id))
            else:
                cursor.execute("UPDATE leave_requests SET status = %s WHERE id = %s", (status, request_id))
            
            connection.commit()
            cursor.close()
            return True
        except Error as e:
            print(f"Error updating leave request: {e}")
            return False
    
    # Feedback Management
    def create_feedback(self, feedback_type, text, department, priority):
        """Create a new feedback"""
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            
            cursor.execute("""
                INSERT INTO feedback (type, text, department, priority)
                VALUES (%s, %s, %s, %s)
            """, (feedback_type, text, department, priority))
            
            connection.commit()
            feedback_id = cursor.lastrowid
            cursor.close()
            return feedback_id
        except Error as e:
            print(f"Error creating feedback: {e}")
            return None
    
    def get_all_feedback(self):
        """Get all feedback"""
        try:
            connection = self.get_connection()
            cursor = connection.cursor(dictionary=True)
            
            cursor.execute("SELECT * FROM feedback ORDER BY submitted_at DESC")
            feedback_list = cursor.fetchall()
            cursor.close()
            return feedback_list
        except Error as e:
            print(f"Error getting feedback: {e}")
            return []
    
    def update_feedback_status(self, feedback_id, status):
        """Update feedback status"""
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            
            cursor.execute("UPDATE feedback SET status = %s WHERE id = %s", (status, feedback_id))
            connection.commit()
            cursor.close()
            return True
        except Error as e:
            print(f"Error updating feedback: {e}")
            return False
    
    # Job Applications
    def create_job_application(self, job_id, applicant_name, applicant_email, resume_path=None, cover_letter=None):
        """Create a new job application"""
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            
            cursor.execute("""
                INSERT INTO job_applications (job_id, applicant_name, applicant_email, resume_path, cover_letter)
                VALUES (%s, %s, %s, %s, %s)
            """, (job_id, applicant_name, applicant_email, resume_path, cover_letter))
            
            connection.commit()
            application_id = cursor.lastrowid
            cursor.close()
            return application_id
        except Error as e:
            print(f"Error creating job application: {e}")
            return None
    
    def get_all_applications(self):
        """Get all job applications"""
        try:
            connection = self.get_connection()
            cursor = connection.cursor(dictionary=True)
            
            cursor.execute("SELECT * FROM job_applications ORDER BY applied_at DESC")
            applications = cursor.fetchall()
            cursor.close()
            return applications
        except Error as e:
            print(f"Error getting applications: {e}")
            return []
    
    def update_application_status(self, application_id, status, reviewed_by=None):
        """Update application status"""
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            
            if reviewed_by:
                cursor.execute("""
                    UPDATE job_applications SET status = %s, reviewed_by = %s, reviewed_at = NOW() 
                    WHERE id = %s
                """, (status, reviewed_by, application_id))
            else:
                cursor.execute("UPDATE job_applications SET status = %s WHERE id = %s", (status, application_id))
            
            connection.commit()
            cursor.close()
            return True
        except Error as e:
            print(f"Error updating application: {e}")
            return False
    
    # Notifications
    def create_notification(self, user_email, message, notification_type='info'):
        """Create a new notification"""
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            
            cursor.execute("""
                INSERT INTO notifications (user_email, message, type)
                VALUES (%s, %s, %s)
            """, (user_email, message, notification_type))
            
            connection.commit()
            notification_id = cursor.lastrowid
            cursor.close()
            return notification_id
        except Error as e:
            print(f"Error creating notification: {e}")
            return None
    
    def get_notifications_by_user(self, user_email):
        """Get notifications by user"""
        try:
            connection = self.get_connection()
            cursor = connection.cursor(dictionary=True)
            
            cursor.execute("SELECT * FROM notifications WHERE user_email = %s ORDER BY created_at DESC", (user_email,))
            notifications = cursor.fetchall()
            cursor.close()
            return notifications
        except Error as e:
            print(f"Error getting notifications: {e}")
            return []
    
    def mark_notification_read(self, notification_id):
        """Mark notification as read"""
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            
            cursor.execute("UPDATE notifications SET read_status = TRUE WHERE id = %s", (notification_id,))
            connection.commit()
            cursor.close()
            return True
        except Error as e:
            print(f"Error marking notification read: {e}")
            return False
    
    # Groups Management
    def create_group(self, name, description, created_by):
        """Create a new group"""
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            
            cursor.execute("""
                INSERT INTO user_groups (name, description, created_by)
                VALUES (%s, %s, %s)
            """, (name, description, created_by))
            
            connection.commit()
            group_id = cursor.lastrowid
            cursor.close()
            return group_id
        except Error as e:
            print(f"Error creating group: {e}")
            return None
    
    def get_all_groups(self):
        """Get all groups"""
        try:
            connection = self.get_connection()
            cursor = connection.cursor(dictionary=True)
            
            cursor.execute("SELECT * FROM user_groups ORDER BY created_at DESC")
            groups = cursor.fetchall()
            cursor.close()
            return groups
        except Error as e:
            print(f"Error getting groups: {e}")
            return []
    
    def add_group_member(self, group_id, member_name):
        """Add member to group"""
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            
            cursor.execute("""
                INSERT INTO group_members (group_id, member_name)
                VALUES (%s, %s)
            """, (group_id, member_name))
            
            connection.commit()
            cursor.close()
            return True
        except Error as e:
            print(f"Error adding group member: {e}")
            return False
    
    def get_group_members(self, group_id):
        """Get group members"""
        try:
            connection = self.get_connection()
            cursor = connection.cursor(dictionary=True)
            
            cursor.execute("SELECT * FROM group_members WHERE group_id = %s", (group_id,))
            members = cursor.fetchall()
            cursor.close()
            return members
        except Error as e:
            print(f"Error getting group members: {e}")
            return []
    
    # Chat Messages
    def add_chat_message(self, group_id, sender_name, message, message_type='text', file_name=None):
        """Add a chat message"""
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            
            cursor.execute("""
                INSERT INTO chat_messages (group_id, sender_name, message, message_type, file_name)
                VALUES (%s, %s, %s, %s, %s)
            """, (group_id, sender_name, message, message_type, file_name))
            
            connection.commit()
            message_id = cursor.lastrowid
            cursor.close()
            return message_id
        except Error as e:
            print(f"Error adding chat message: {e}")
            return None
    
    def get_group_messages(self, group_id):
        """Get group messages"""
        try:
            connection = self.get_connection()
            cursor = connection.cursor(dictionary=True)
            
            cursor.execute("SELECT * FROM chat_messages WHERE group_id = %s ORDER BY sent_at ASC", (group_id,))
            messages = cursor.fetchall()
            cursor.close()
            return messages
        except Error as e:
            print(f"Error getting group messages: {e}")
            return []

# Create a global instance
db_helper = DatabaseHelper() 