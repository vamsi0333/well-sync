from database_helper import DatabaseHelper
from database_config import get_db_connection

def reset_and_create_users():
    try:
        # Get database connection
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Disable foreign key checks temporarily
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
        
        # Clear existing users
        cursor.execute("TRUNCATE TABLE employees")
        cursor.execute("TRUNCATE TABLE users")
        
        # Re-enable foreign key checks
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
        
        # Create database helper
        db = DatabaseHelper()
        
        # Create default users with plain text passwords (for testing)
        default_users = [
            ("admin@example.com", "password", "admin"),
            ("user@example.com", "password", "employee"),
            ("it@example.com", "password", "it")
        ]
        
        for email, password, role in default_users:
            user_id = db.create_user(email, password, role)
            print(f"Created user: {email} with role {role}")
            
            # Create employee record for non-admin users
            if role != "admin":
                cursor.execute("""
                    INSERT INTO employees (user_id, full_name, email, department, position)
                    VALUES (%s, %s, %s, %s, %s)
                """, (user_id, f"Test {role.title()}", email, role.upper(), f"{role.title()} Staff"))
        
        connection.commit()
        cursor.close()
        connection.close()
        
        print("Users created successfully!")
        return True
        
    except Exception as e:
        print(f"Error creating users: {e}")
        return False

if __name__ == "__main__":
    reset_and_create_users()
