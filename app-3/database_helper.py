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
    
    def assign_ticket(self, ticket_id, assignee):
        """Assign ticket to a user"""
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            
            cursor.execute("UPDATE tickets SET assigned_to = %s WHERE id = %s", (assignee, ticket_id))
            connection.commit()
            cursor.close()
            return True
        except Error as e:
            print(f"Error assigning ticket: {e}")
            return False
    
    def delete_ticket(self, ticket_id):
        """Delete a ticket"""
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            
            cursor.execute("DELETE FROM tickets WHERE id = %s", (ticket_id,))
            connection.commit()
            cursor.close()
            return True
        except Error as e:
            print(f"Error deleting ticket: {e}")
            return False
    
    def mark_ticket_done(self, ticket_id):
        """Mark ticket as done"""
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            
            cursor.execute("UPDATE tickets SET status = 'closed' WHERE id = %s", (ticket_id,))
            connection.commit()
            cursor.close()
            return True
        except Error as e:
            print(f"Error marking ticket done: {e}")
            return False
    
    def add_ticket_comment(self, ticket_id, comment, admin_name):
        """Add admin comment to ticket"""
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            
            cursor.execute("""
                INSERT INTO ticket_comments (ticket_id, comment, admin_name, created_at)
                VALUES (%s, %s, %s, NOW())
            """, (ticket_id, comment, admin_name))
            connection.commit()
            comment_id = cursor.lastrowid
            cursor.close()
            return comment_id
        except Error as e:
            print(f"Error adding ticket comment: {e}")
            return None
    
    def get_ticket_comments(self, ticket_id):
        """Get comments for a ticket"""
        try:
            connection = self.get_connection()
            cursor = connection.cursor(dictionary=True)
            
            cursor.execute("SELECT * FROM ticket_comments WHERE ticket_id = %s ORDER BY created_at DESC", (ticket_id,))
            comments = cursor.fetchall()
            cursor.close()
            return comments
        except Error as e:
            print(f"Error getting ticket comments: {e}")
            return []
    
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
    
    def delete_feedback(self, feedback_id):
        """Delete feedback"""
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            
            cursor.execute("DELETE FROM feedback WHERE id = %s", (feedback_id,))
            connection.commit()
            cursor.close()
            return True
        except Error as e:
            print(f"Error deleting feedback: {e}")
            return False
    
    def add_feedback_comment(self, feedback_id, comment, admin_name):
        """Add admin comment to feedback"""
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            
            cursor.execute("""
                INSERT INTO feedback_comments (feedback_id, comment, admin_name, created_at)
                VALUES (%s, %s, %s, NOW())
            """, (feedback_id, comment, admin_name))
            connection.commit()
            comment_id = cursor.lastrowid
            cursor.close()
            return comment_id
        except Error as e:
            print(f"Error adding feedback comment: {e}")
            return None
    
    def get_feedback_comments(self, feedback_id):
        """Get comments for feedback"""
        try:
            connection = self.get_connection()
            cursor = connection.cursor(dictionary=True)
            
            cursor.execute("SELECT * FROM feedback_comments WHERE feedback_id = %s ORDER BY created_at DESC", (feedback_id,))
            comments = cursor.fetchall()
            cursor.close()
            return comments
        except Error as e:
            print(f"Error getting feedback comments: {e}")
            return []
    
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

    # Timesheet Management
    def create_timesheet(self, employee_id, employee_name, date, hours_worked, project, task_description):
        """Create a new timesheet entry"""
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            
            # Convert hours_worked to start_time and end_time (simplified)
            start_time = "09:00:00"
            end_time = f"{int(hours_worked) + 9}:00:00"
            
            cursor.execute("""
                INSERT INTO timesheets (user_id, date, start_time, end_time, description)
                VALUES (%s, %s, %s, %s, %s)
            """, (employee_id, date, start_time, end_time, task_description))
            
            connection.commit()
            timesheet_id = cursor.lastrowid
            cursor.close()
            return timesheet_id
        except Error as e:
            print(f"Error creating timesheet: {e}")
            return None
    
    def get_timesheets_by_employee(self, employee_id):
        """Get timesheets by employee"""
        try:
            connection = self.get_connection()
            cursor = connection.cursor(dictionary=True)
            
            cursor.execute("SELECT * FROM timesheets WHERE user_id = %s ORDER BY date DESC", (employee_id,))
            timesheets = cursor.fetchall()
            cursor.close()
            return timesheets
        except Error as e:
            print(f"Error getting timesheets: {e}")
            return []
    
    def get_all_timesheets(self):
        """Get all timesheets"""
        try:
            connection = self.get_connection()
            cursor = connection.cursor(dictionary=True)
            
            cursor.execute("SELECT * FROM timesheets ORDER BY date DESC")
            timesheets = cursor.fetchall()
            cursor.close()
            return timesheets
        except Error as e:
            print(f"Error getting all timesheets: {e}")
            return []
    
    def update_timesheet_status(self, timesheet_id, status, approved_by=None):
        """Update timesheet status"""
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            
            if approved_by:
                cursor.execute("""
                    UPDATE timesheets SET status = %s, approved_by = %s, approved_at = NOW() 
                    WHERE id = %s
                """, (status, approved_by, timesheet_id))
            else:
                cursor.execute("UPDATE timesheets SET status = %s WHERE id = %s", (status, timesheet_id))
            
            connection.commit()
            cursor.close()
            return True
        except Error as e:
            print(f"Error updating timesheet: {e}")
            return False
    
    def delete_timesheet(self, timesheet_id):
        """Delete timesheet"""
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            
            cursor.execute("DELETE FROM timesheets WHERE id = %s", (timesheet_id,))
            connection.commit()
            cursor.close()
            return True
        except Error as e:
            print(f"Error deleting timesheet: {e}")
            return False
    
    def add_timesheet_comment(self, timesheet_id, comment, admin_name):
        """Add admin comment to timesheet"""
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            
            cursor.execute("""
                INSERT INTO timesheet_comments (timesheet_id, comment, admin_name, created_at)
                VALUES (%s, %s, %s, NOW())
            """, (timesheet_id, comment, admin_name))
            connection.commit()
            comment_id = cursor.lastrowid
            cursor.close()
            return comment_id
        except Error as e:
            print(f"Error adding timesheet comment: {e}")
            return None
    
    def get_timesheet_comments(self, timesheet_id):
        """Get comments for timesheet"""
        try:
            connection = self.get_connection()
            cursor = connection.cursor(dictionary=True)
            
            cursor.execute("SELECT * FROM timesheet_comments WHERE timesheet_id = %s ORDER BY created_at DESC", (timesheet_id,))
            comments = cursor.fetchall()
            cursor.close()
            return comments
        except Error as e:
            print(f"Error getting timesheet comments: {e}")
            return []
    
    # Badge Management
    def create_badge(self, name, description, icon=None, category=None):
        """Create a new badge"""
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            
            cursor.execute("""
                INSERT INTO badges (name, description, icon, category)
                VALUES (%s, %s, %s, %s)
            """, (name, description, icon, category))
            
            connection.commit()
            badge_id = cursor.lastrowid
            cursor.close()
            return badge_id
        except Error as e:
            print(f"Error creating badge: {e}")
            return None
    
    def get_all_badges(self):
        """Get all badges"""
        try:
            connection = self.get_connection()
            cursor = connection.cursor(dictionary=True)
            
            cursor.execute("SELECT * FROM badges ORDER BY created_at DESC")
            badges = cursor.fetchall()
            cursor.close()
            return badges
        except Error as e:
            print(f"Error getting badges: {e}")
            return []
    
    def assign_badge_to_user(self, user_id, badge_id, awarded_by=None, reason=None):
        """Assign a badge to a user"""
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            
            cursor.execute("""
                INSERT INTO user_badges (user_id, badge_id, awarded_by, reason)
                VALUES (%s, %s, %s, %s)
            """, (user_id, badge_id, awarded_by, reason))
            
            connection.commit()
            assignment_id = cursor.lastrowid
            cursor.close()
            return assignment_id
        except Error as e:
            print(f"Error assigning badge: {e}")
            return None
    
    def get_user_badges(self, user_id):
        """Get badges for a specific user"""
        try:
            connection = self.get_connection()
            cursor = connection.cursor(dictionary=True)
            
            cursor.execute("""
                SELECT b.*, ub.awarded_at, ub.reason, ub.awarded_by
                FROM badges b
                JOIN user_badges ub ON b.id = ub.badge_id
                WHERE ub.user_id = %s
                ORDER BY ub.awarded_at DESC
            """, (user_id,))
            badges = cursor.fetchall()
            cursor.close()
            return badges
        except Error as e:
            print(f"Error getting user badges: {e}")
            return []
    
    def get_all_user_badges(self):
        """Get all user badge assignments"""
        try:
            connection = self.get_connection()
            cursor = connection.cursor(dictionary=True)
            
            cursor.execute("""
                SELECT ub.*, b.name as badge_name, b.description, b.icon
                FROM user_badges ub
                JOIN badges b ON ub.badge_id = b.id
                ORDER BY ub.awarded_at DESC
            """)
            assignments = cursor.fetchall()
            cursor.close()
            return assignments
        except Error as e:
            print(f"Error getting all user badges: {e}")
            return []
    
    # Service Request Management
    def create_service_request(self, user_email, request_type, subject, description, priority='medium'):
        """Create a new service request"""
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            
            cursor.execute("""
                INSERT INTO service_requests (user_email, request_type, subject, description, priority, status)
                VALUES (%s, %s, %s, %s, %s, 'pending')
            """, (user_email, request_type, subject, description, priority))
            
            connection.commit()
            request_id = cursor.lastrowid
            cursor.close()
            return request_id
        except Error as e:
            print(f"Error creating service request: {e}")
            return None
    
    def get_all_service_requests(self):
        """Get all service requests"""
        try:
            connection = self.get_connection()
            cursor = connection.cursor(dictionary=True)
            
            cursor.execute("SELECT * FROM service_requests ORDER BY created_at DESC")
            requests = cursor.fetchall()
            cursor.close()
            return requests
        except Error as e:
            print(f"Error getting service requests: {e}")
            return []
    
    def get_service_requests_by_user(self, user_email):
        """Get service requests by user"""
        try:
            connection = self.get_connection()
            cursor = connection.cursor(dictionary=True)
            
            cursor.execute("SELECT * FROM service_requests WHERE user_email = %s ORDER BY created_at DESC", (user_email,))
            requests = cursor.fetchall()
            cursor.close()
            return requests
        except Error as e:
            print(f"Error getting user service requests: {e}")
            return []
    
    def update_service_request_status(self, request_id, status, assigned_to=None):
        """Update service request status"""
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            
            if assigned_to:
                cursor.execute("""
                    UPDATE service_requests SET status = %s, assigned_to = %s, updated_at = NOW() 
                    WHERE id = %s
                """, (status, assigned_to, request_id))
            else:
                cursor.execute("UPDATE service_requests SET status = %s, updated_at = NOW() WHERE id = %s", (status, request_id))
            
            connection.commit()
            cursor.close()
            return True
        except Error as e:
            print(f"Error updating service request: {e}")
            return False
    
    def assign_service_request(self, request_id, assigned_to):
        """Assign service request to someone"""
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            
            cursor.execute("""
                UPDATE service_requests SET assigned_to = %s, status = 'assigned', updated_at = NOW() 
                WHERE id = %s
            """, (assigned_to, request_id))
            
            connection.commit()
            cursor.close()
            return True
        except Error as e:
            print(f"Error assigning service request: {e}")
            return False
    
    def delete_service_request(self, request_id):
        """Delete a service request"""
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            
            cursor.execute("DELETE FROM service_requests WHERE id = %s", (request_id,))
            connection.commit()
            cursor.close()
            return True
        except Error as e:
            print(f"Error deleting service request: {e}")
            return False
    
    def add_service_request_comment(self, request_id, comment, admin_name):
        """Add admin comment to service request"""
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            
            cursor.execute("""
                INSERT INTO service_request_comments (request_id, comment, admin_name, created_at)
                VALUES (%s, %s, %s, NOW())
            """, (request_id, comment, admin_name))
            
            connection.commit()
            comment_id = cursor.lastrowid
            cursor.close()
            return comment_id
        except Error as e:
            print(f"Error adding service request comment: {e}")
            return None
    
    def get_service_request_comments(self, request_id):
        """Get comments for a service request"""
        try:
            connection = self.get_connection()
            cursor = connection.cursor(dictionary=True)
            
            cursor.execute("SELECT * FROM service_request_comments WHERE request_id = %s ORDER BY created_at DESC", (request_id,))
            comments = cursor.fetchall()
            cursor.close()
            return comments
        except Error as e:
            print(f"Error getting service request comments: {e}")
            return []
    
    # Career Portal Management
    def create_internal_job(self, title, department, location, job_type, description, requirements, salary_range, posted_date, deadline_date):
        """Create a new internal job posting"""
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            
            cursor.execute("""
                INSERT INTO internal_jobs (title, department, location, job_type, description, requirements, salary_range, posted_date, deadline_date, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'active')
            """, (title, department, location, job_type, description, requirements, salary_range, posted_date, deadline_date))
            
            connection.commit()
            job_id = cursor.lastrowid
            cursor.close()
            return job_id
        except Error as e:
            print(f"Error creating internal job: {e}")
            return None
    
    def get_all_internal_jobs(self):
        """Get all internal job postings"""
        try:
            connection = self.get_connection()
            cursor = connection.cursor(dictionary=True)
            
            cursor.execute("SELECT * FROM internal_jobs ORDER BY posted_date DESC")
            jobs = cursor.fetchall()
            cursor.close()
            return jobs
        except Error as e:
            print(f"Error getting internal jobs: {e}")
            return []
    
    def get_internal_job_by_id(self, job_id):
        """Get specific internal job by ID"""
        try:
            connection = self.get_connection()
            cursor = connection.cursor(dictionary=True)
            
            cursor.execute("SELECT * FROM internal_jobs WHERE id = %s", (job_id,))
            job = cursor.fetchone()
            cursor.close()
            return job
        except Error as e:
            print(f"Error getting internal job: {e}")
            return None
    
    def apply_for_internal_job(self, job_id, user_email, resume_path=None, cover_letter=None):
        """Apply for an internal job"""
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            
            cursor.execute("""
                INSERT INTO internal_job_applications (job_id, user_email, resume_path, cover_letter, status)
                VALUES (%s, %s, %s, %s, 'pending')
            """, (job_id, user_email, resume_path, cover_letter))
            
            connection.commit()
            application_id = cursor.lastrowid
            cursor.close()
            return application_id
        except Error as e:
            print(f"Error applying for internal job: {e}")
            return None
    
    def get_user_internal_applications(self, user_email):
        """Get user's internal job applications"""
        try:
            connection = self.get_connection()
            cursor = connection.cursor(dictionary=True)
            
            cursor.execute("""
                SELECT ia.*, ij.title as job_title, ij.department, ij.location
                FROM internal_job_applications ia
                JOIN internal_jobs ij ON ia.job_id = ij.id
                WHERE ia.user_email = %s
                ORDER BY ia.applied_date DESC
            """, (user_email,))
            applications = cursor.fetchall()
            cursor.close()
            return applications
        except Error as e:
            print(f"Error getting user internal applications: {e}")
            return []
    
    def get_all_internal_applications(self):
        """Get all internal job applications"""
        try:
            connection = self.get_connection()
            cursor = connection.cursor(dictionary=True)
            
            cursor.execute("""
                SELECT ia.*, ij.title as job_title, ij.department, ij.location
                FROM internal_job_applications ia
                JOIN internal_jobs ij ON ia.job_id = ij.id
                ORDER BY ia.applied_date DESC
            """)
            applications = cursor.fetchall()
            cursor.close()
            return applications
        except Error as e:
            print(f"Error getting all internal applications: {e}")
            return []
    
    # Skills Assessment Management
    def create_skills_assessment(self, user_email, test_type, score, total_questions, answers, completed_at):
        """Create a new skills assessment record"""
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            
            cursor.execute("""
                INSERT INTO skills_assessments (user_email, test_type, score, total_questions, answers, completed_at)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (user_email, test_type, score, total_questions, answers, completed_at))
            
            connection.commit()
            assessment_id = cursor.lastrowid
            cursor.close()
            return assessment_id
        except Error as e:
            print(f"Error creating skills assessment: {e}")
            return None
    
    def get_user_skills_assessments(self, user_email):
        """Get user's skills assessments"""
        try:
            connection = self.get_connection()
            cursor = connection.cursor(dictionary=True)
            
            cursor.execute("SELECT * FROM skills_assessments WHERE user_email = %s ORDER BY completed_at DESC", (user_email,))
            assessments = cursor.fetchall()
            cursor.close()
            return assessments
        except Error as e:
            print(f"Error getting user skills assessments: {e}")
            return []
    
    def get_latest_skills_assessment(self, user_email):
        """Get user's latest skills assessment"""
        try:
            connection = self.get_connection()
            cursor = connection.cursor(dictionary=True)
            
            cursor.execute("""
                SELECT * FROM skills_assessments 
                WHERE user_email = %s 
                ORDER BY completed_at DESC 
                LIMIT 1
            """, (user_email,))
            assessment = cursor.fetchone()
            cursor.close()
            return assessment
        except Error as e:
            print(f"Error getting latest skills assessment: {e}")
            return None
    
    # Learning Roadmap Management
    def create_learning_roadmap(self, user_email, assessment_id, improvement_areas, recommended_path, created_at):
        """Create a learning roadmap based on assessment results"""
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            
            cursor.execute("""
                INSERT INTO learning_roadmaps (user_email, assessment_id, improvement_areas, recommended_path, created_at)
                VALUES (%s, %s, %s, %s, %s)
            """, (user_email, assessment_id, improvement_areas, recommended_path, created_at))
            
            connection.commit()
            roadmap_id = cursor.lastrowid
            cursor.close()
            return roadmap_id
        except Error as e:
            print(f"Error creating learning roadmap: {e}")
            return None
    
    def get_user_learning_roadmap(self, user_email):
        """Get user's learning roadmap"""
        try:
            connection = self.get_connection()
            cursor = connection.cursor(dictionary=True)
            
            cursor.execute("""
                SELECT lr.*, sa.score, sa.test_type
                FROM learning_roadmaps lr
                LEFT JOIN skills_assessments sa ON lr.assessment_id = sa.id
                WHERE lr.user_email = %s
                ORDER BY lr.created_at DESC
                LIMIT 1
            """, (user_email,))
            roadmap = cursor.fetchone()
            cursor.close()
            return roadmap
        except Error as e:
            print(f"Error getting user learning roadmap: {e}")
            return None

    # Course Management
    def get_course_by_id(self, course_id):
        """Get course by ID"""
        try:
            connection = self.get_connection()
            cursor = connection.cursor(dictionary=True)
            
            cursor.execute("SELECT * FROM courses WHERE id = %s", (course_id,))
            course = cursor.fetchone()
            cursor.close()
            return course
        except Error as e:
            print(f"Error getting course: {e}")
            return None
    
    def get_all_courses(self):
        """Get all courses"""
        try:
            connection = self.get_connection()
            cursor = connection.cursor(dictionary=True)
            
            cursor.execute("SELECT * FROM courses ORDER BY created_at DESC")
            courses = cursor.fetchall()
            cursor.close()
            return courses
        except Error as e:
            print(f"Error getting courses: {e}")
            return []
    
    def create_course(self, title, description, content, questions, passing_score, badge=None):
        """Create a new course"""
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            
            cursor.execute("""
                INSERT INTO courses (title, description, content, questions, passing_score, badge)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (title, description, content, json.dumps(questions), passing_score, badge))
            
            connection.commit()
            course_id = cursor.lastrowid
            cursor.close()
            return course_id
        except Error as e:
            print(f"Error creating course: {e}")
            return None
    
    def save_quiz_result(self, user_email, course_id, score, total_questions, percentage, passed):
        """Save quiz result"""
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            
            cursor.execute("""
                INSERT INTO quiz_results (user_email, course_id, score, total_questions, percentage, passed, completed_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (user_email, course_id, score, total_questions, percentage, passed, datetime.now()))
            
            connection.commit()
            result_id = cursor.lastrowid
            cursor.close()
            return result_id
        except Error as e:
            print(f"Error saving quiz result: {e}")
            return None
    
    def get_user_quiz_results(self, user_email):
        """Get user's quiz results"""
        try:
            connection = self.get_connection()
            cursor = connection.cursor(dictionary=True)
            
            cursor.execute("""
                SELECT qr.*, c.title as course_title
                FROM quiz_results qr
                LEFT JOIN courses c ON qr.course_id = c.id
                WHERE qr.user_email = %s
                ORDER BY qr.completed_at DESC
            """, (user_email,))
            results = cursor.fetchall()
            cursor.close()
            return results
        except Error as e:
            print(f"Error getting user quiz results: {e}")
            return []

# Create a global instance
db_helper = DatabaseHelper() 