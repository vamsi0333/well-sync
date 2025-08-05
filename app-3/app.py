from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from werkzeug.utils import secure_filename
from flask_cors import CORS
import re
import random
from dotenv import load_dotenv
import time
import json
import hashlib
from database_helper import db_helper
import pickle
from functools import wraps

# Conditional imports for AI features
try:
    import fitz
    import pandas as pd
    from pdfminer.high_level import extract_text
    from sentence_transformers import SentenceTransformer
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    import numpy as np
    from langchain.schema import Document
    from langchain.text_splitter import CharacterTextSplitter
    from langchain_openai import AzureOpenAIEmbeddings, AzureChatOpenAI
    from langchain_community.vectorstores import AzureSearch
    from langchain.chains import ConversationalRetrievalChain
    from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
    AI_DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    print(f"Some AI dependencies are missing: {e}")
    print("AI features will be disabled. Install requirements.txt for full functionality.")
    AI_DEPENDENCIES_AVAILABLE = False

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = 'supersecretkey'
CORS(app)

# Configure file upload
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Create upload folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize AI models
ats_initialized = False
rag_initialized = False

# Temporarily disable Azure initialization to get server running
print("⚠️ Azure initialization temporarily disabled for server startup")

# Role-based access control decorators
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

def employee_login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        print(f"DEBUG: employee_login_required - session: {dict(session)}")
        if "user" not in session:
            print(f"DEBUG: No user in session, redirecting to employee_login")
            return redirect(url_for("employee_login"))
        print(f"DEBUG: User found in session: {session['user']}")
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("login"))
        if session.get("role") != "admin":
            flash("Access denied. Admin privileges required.", "error")
            return redirect(url_for("dashboard"))
        return f(*args, **kwargs)
    return decorated_function

def it_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("login"))
        if session.get("role") not in ["admin", "it", "employee"]:
            flash("Access denied. IT privileges required.", "error")
            return redirect(url_for("dashboard"))
        return f(*args, **kwargs)
    return decorated_function

def hr_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("login"))
        if session.get("role") not in ["admin", "hr"]:
            flash("Access denied. HR privileges required.", "error")
            return redirect(url_for("dashboard"))
        return f(*args, **kwargs)
    return decorated_function

def employee_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("login"))
        if session.get("role") not in ["admin", "it", "hr", "employee"]:
            flash("Access denied. Employee privileges required.", "error")
            return redirect(url_for("dashboard"))
        return f(*args, **kwargs)
    return decorated_function

# Global variables for data storage
chat_messages = [
    {
        'id': 1,
        'group_id': 1,
        'sender': 'John Doe',
        'message': 'Great progress on the new feature! Let\'s review the latest updates.',
        'timestamp': '2024-01-30 10:30 AM',
        'type': 'text'
    },
    {
        'id': 2,
        'group_id': 1,
        'sender': 'Jane Smith',
        'message': 'I\'ve uploaded the latest design mockups to the shared drive.',
        'timestamp': '2024-01-30 10:32 AM',
        'type': 'file',
        'file_name': 'design_mockups.pdf'
    },
    {
        'id': 3,
        'group_id': 2,
        'sender': 'Emily Davis',
        'message': 'Campaign performance is looking strong this quarter!',
        'timestamp': '2024-01-30 09:15 AM',
        'type': 'text'
    }
]

# Global groups data
groups = [
    {
        'id': 1,
        'name': 'Product Development',
        'description': 'Core product team working on new features',
        'members': ['John Doe', 'Jane Smith', 'Mike Johnson', 'Sarah Wilson'],
        'manager': 'Alex Chen',
        'created_date': '2024-01-15',
        'status': 'active',
        'type': 'project'
    },
    {
        'id': 2,
        'name': 'Marketing Team',
        'description': 'Digital marketing and campaign management',
        'members': ['Emily Davis', 'David Brown', 'Lisa Garcia', 'Tom Wilson'],
        'manager': 'Rachel Green',
        'created_date': '2024-01-20',
        'status': 'active',
        'type': 'department'
    },
    {
        'id': 3,
        'name': 'Sales Operations',
        'description': 'Sales process optimization and customer success',
        'members': ['Mark Johnson', 'Anna Lee', 'Chris Rodriguez', 'Sophie Kim'],
        'manager': 'Michael Scott',
        'created_date': '2024-01-25',
        'status': 'active',
        'type': 'department'
    }
]

# Sample tickets data
tickets = [
    {
        'id': 1,
        'title': 'VPN Connection Issues',
        'description': 'Unable to connect to corporate VPN from home office',
        'priority': 'high',
        'status': 'open',
        'user_email': 'john.doe@example.com',
        'created_at': '2024-01-30 09:00 AM',
        'assigned_to': 'IT Support'
    },
    {
        'id': 2,
        'title': 'Printer Not Working',
        'description': 'Office printer showing error code E-04',
        'priority': 'medium',
        'status': 'in_progress',
        'user_email': 'jane.smith@example.com',
        'created_at': '2024-01-30 08:30 AM',
        'assigned_to': 'IT Support'
    },
    {
        'id': 3,
        'title': 'Email Sync Problem',
        'description': 'Outlook not syncing emails properly',
        'priority': 'low',
        'status': 'resolved',
        'user_email': 'mike.wilson@example.com',
        'created_at': '2024-01-29 02:15 PM',
        'assigned_to': 'IT Support'
    }
]

# Sample timeoff requests
timeoff_requests = [
    {
        'id': 1,
        'employee_name': 'John Doe',
        'start_date': '2024-02-15',
        'end_date': '2024-02-17',
        'reason': 'Family vacation',
        'status': 'pending',
        'days_requested': 3
    },
    {
        'id': 2,
        'employee_name': 'Jane Smith',
        'start_date': '2024-02-20',
        'end_date': '2024-02-20',
        'reason': 'Doctor appointment',
        'status': 'approved',
        'days_requested': 1
    }
]

# Sample paystubs data
paystubs = [
    {
        'id': 1,
        'employee_name': 'John Doe',
        'pay_period': '2024-01-01 to 2024-01-15',
        'gross_pay': 2500.00,
        'net_pay': 2100.00,
        'status': 'paid'
    },
    {
        'id': 2,
        'employee_name': 'Jane Smith',
        'pay_period': '2024-01-01 to 2024-01-15',
        'gross_pay': 2800.00,
        'net_pay': 2350.00,
        'status': 'paid'
    }
]

# Sample benefits data
benefits = [
    {
        'id': 1,
        'name': 'Health Insurance',
        'type': 'Medical',
        'coverage': 'Family',
        'status': 'active'
    },
    {
        'id': 2,
        'name': 'Dental Insurance',
        'type': 'Dental',
        'coverage': 'Individual',
        'status': 'active'
    }
]

# Sample job applications
applications = [
    {
        'id': 1,
        'job_title': 'Senior Software Engineer',
        'applicant_name': 'Alex Johnson',
        'applicant_email': 'alex.johnson@email.com',
        'status': 'pending',
        'applied_date': '2024-01-30'
    },
    {
        'id': 2,
        'job_title': 'Marketing Manager',
        'applicant_name': 'Sarah Wilson',
        'applicant_email': 'sarah.wilson@email.com',
        'status': 'reviewed',
        'applied_date': '2024-01-29'
    }
]

# Sample badges data
badges = [
    {
        'id': 1,
        'name': 'Team Player',
        'description': 'Excellent collaboration skills',
        'icon': '👥',
        'category': 'Collaboration'
    },
    {
        'id': 2,
        'name': 'Problem Solver',
        'description': 'Consistently finds innovative solutions',
        'icon': '💡',
        'category': 'Innovation'
    },
    {
        'id': 3,
        'name': 'Mentor',
        'description': 'Helps others grow and develop',
        'icon': '🎓',
        'category': 'Leadership'
    }
]

# Sample user badges
user_badges = [
    {
        'user_id': 'john.doe@example.com',
        'badge_id': 1,
        'awarded_by': 'Manager',
        'awarded_at': '2024-01-15'
    },
    {
        'user_id': 'jane.smith@example.com',
        'badge_id': 2,
        'awarded_by': 'Team Lead',
        'awarded_at': '2024-01-20'
    }
]

# Sample devices data
devices = [
    {
        'id': 1,
        'name': 'MacBook Pro 16"',
        'type': 'Laptop',
        'status': 'available',
        'assigned_to': None,
        'location': 'IT Department'
    },
    {
        'id': 2,
        'name': 'iPad Pro 12.9"',
        'type': 'Tablet',
        'status': 'assigned',
        'assigned_to': 'John Doe',
        'location': 'Marketing Department'
    },
    {
        'id': 3,
        'name': 'iPhone 15 Pro',
        'type': 'Phone',
        'status': 'available',
        'assigned_to': None,
        'location': 'IT Department'
    }
]

# Sample software catalog
software_catalog = [
    {
        'name': 'Microsoft Office 365',
        'category': 'Productivity',
        'description': 'Word, Excel, PowerPoint, Outlook',
        'license_type': 'Subscription',
        'cost': '$12.99/month'
    },
    {
        'name': 'Adobe Creative Suite',
        'category': 'Design',
        'description': 'Photoshop, Illustrator, InDesign',
        'license_type': 'Subscription',
        'cost': '$52.99/month'
    },
    {
        'name': 'Slack',
        'category': 'Communication',
        'description': 'Team messaging and collaboration',
        'license_type': 'Subscription',
        'cost': '$8.75/month'
    }
]

# Sample IT resources
it_resources = [
    {
        'title': 'VPN Setup Guide',
        'category': 'Network',
        'description': 'Step-by-step guide for connecting to corporate VPN',
        'url': '/resources/vpn-setup'
    },
    {
        'title': 'Password Policy',
        'category': 'Security',
        'description': 'Company password requirements and best practices',
        'url': '/resources/password-policy'
    },
    {
        'title': 'Software Installation',
        'category': 'Software',
        'description': 'How to install approved software on company devices',
        'url': '/resources/software-installation'
    }
]

# Sample FAQs
faqs = [
    {
        'question': 'How do I reset my password?',
        'answer': 'Contact IT support or use the self-service password reset portal.',
        'category': 'Account Management'
    },
    {
        'question': 'What should I do if my laptop breaks?',
        'answer': 'Contact IT support immediately and do not attempt to repair it yourself.',
        'category': 'Hardware'
    },
    {
        'question': 'How do I request software installation?',
        'answer': 'Submit a ticket through the IT portal with the software name and business justification.',
        'category': 'Software'
    }
]

# Sample job listings
jobs = [
    {
        'id': 1,
        'title': 'Senior Software Engineer',
        'department': 'Engineering',
        'location': 'San Francisco, CA',
        'type': 'Full-time',
        'description': 'We are looking for a senior software engineer to join our team...',
        'requirements': '5+ years of experience, Python, JavaScript, React',
        'salary_range': '$120,000 - $150,000',
        'posted_date': '2024-01-15',
        'deadline': '2024-02-15'
    },
    {
        'id': 2,
        'title': 'Marketing Manager',
        'department': 'Marketing',
        'location': 'New York, NY',
        'type': 'Full-time',
        'description': 'Join our marketing team to drive brand awareness...',
        'requirements': '3+ years of experience, Digital marketing, Analytics',
        'salary_range': '$80,000 - $100,000',
        'posted_date': '2024-01-20',
        'deadline': '2024-02-20'
    }
]

# Sample saved jobs
saved_jobs = [1, 2]

# Sample recommended jobs
recommended = [1, 2]

# Sample career goals
career_goals = [
    {
        'id': 1,
        'title': 'Become a Team Lead',
        'description': 'Develop leadership skills and manage a small team',
        'target_date': '2024-12-31',
        'progress': 60
    },
    {
        'id': 2,
        'title': 'Learn Machine Learning',
        'description': 'Complete online courses and work on ML projects',
        'target_date': '2024-06-30',
        'progress': 30
    }
]

# Sample upskilling opportunities
upskilling = [
    {
        'id': 1,
        'title': 'Python for Data Science',
        'provider': 'Coursera',
        'duration': '8 weeks',
        'cost': 'Free',
        'status': 'enrolled'
    },
    {
        'id': 2,
        'title': 'Leadership Skills',
        'provider': 'LinkedIn Learning',
        'duration': '6 weeks',
        'cost': 'Free',
        'status': 'completed'
    }
]

# Sample mentorship opportunities
mentorships = [
    {
        'id': 1,
        'mentor': 'Sarah Johnson',
        'title': 'Senior Software Engineer',
        'expertise': 'Backend Development, System Architecture',
        'availability': '2 hours/week',
        'status': 'available'
    },
    {
        'id': 2,
        'mentor': 'Mike Chen',
        'title': 'Product Manager',
        'expertise': 'Product Strategy, User Research',
        'availability': '1 hour/week',
        'status': 'available'
    }
]

# Sample course progress
course_progress = [
    {
        'id': 1,
        'title': 'Advanced JavaScript',
        'progress': 75,
        'score': 85,
        'status': 'in_progress'
    },
    {
        'id': 2,
        'title': 'Project Management',
        'progress': 100,
        'score': 92,
        'status': 'completed'
    }
]

# Sample learning resources
resources = [
    {
        'id': 1,
        'title': 'JavaScript Best Practices',
        'type': 'Article',
        'url': 'https://example.com/js-best-practices',
        'category': 'Programming'
    },
    {
        'id': 2,
        'title': 'Leadership Fundamentals',
        'type': 'Video',
        'url': 'https://example.com/leadership-video',
        'category': 'Leadership'
    }
]

# Sample feedback
feedback = [
    {
        'id': 1,
        'type': 'General',
        'text': 'Great work environment and supportive team',
        'department': 'Engineering',
        'priority': 'low',
        'status': 'pending',
        'anonymous': True
    },
    {
        'id': 2,
        'type': 'Improvement',
        'text': 'Need better communication between departments',
        'department': 'Cross-functional',
        'priority': 'medium',
        'status': 'in_progress',
        'anonymous': True
    }
]

# Sample notifications
notifications = [
    {
        'id': 1,
        'user_email': 'admin@example.com',
        'message': 'Your ticket #123 has been resolved',
        'type': 'success',
        'read': False,
        'timestamp': '2024-01-30 10:30 AM'
    },
    {
        'id': 2,
        'user_email': 'admin@example.com',
        'message': 'New software update available',
        'type': 'info',
        'read': True,
        'timestamp': '2024-01-30 09:15 AM'
    },
    {
        'id': 3,
        'user_email': 'employee@example.com',
        'message': 'Your service request has been approved',
        'type': 'success',
        'read': False,
        'timestamp': '2024-01-30 11:00 AM'
    },
    {
        'id': 4,
        'user_email': 'employee@example.com',
        'message': 'New learning course available',
        'type': 'info',
        'read': True,
        'timestamp': '2024-01-30 08:30 AM'
    }
]

# Sample leave requests
leave_requests = [
    {
        'id': 1,
        'employee_id': 'john.doe@example.com',
        'employee_name': 'John Doe',
        'leave_type': 'Annual Leave',
        'start_date': '2024-02-15',
        'end_date': '2024-02-17',
        'total_days': 3,
        'reason': 'Family vacation',
        'status': 'pending',
        'submitted_at': '2024-01-30 09:00 AM'
    },
    {
        'id': 2,
        'employee_id': 'jane.smith@example.com',
        'employee_name': 'Jane Smith',
        'leave_type': 'Sick Leave',
        'start_date': '2024-02-20',
        'end_date': '2024-02-20',
        'total_days': 1,
        'reason': 'Doctor appointment',
        'status': 'approved',
        'submitted_at': '2024-01-30 08:30 AM'
    }
]

# Sample timesheets
timesheets = [
    {
        'id': 1,
        'employee_id': 'john.doe@example.com',
        'employee_name': 'John Doe',
        'date': '2024-01-30',
        'hours_worked': 8.5,
        'project': 'Website Redesign',
        'task_description': 'Frontend development and testing',
        'status': 'pending'
    },
    {
        'id': 2,
        'employee_id': 'jane.smith@example.com',
        'employee_name': 'Jane Smith',
        'date': '2024-01-30',
        'hours_worked': 8.0,
        'project': 'Marketing Campaign',
        'task_description': 'Content creation and social media management',
        'status': 'approved'
    }
]

# Sample employees
employees = [
    {
        'id': 1,
        'full_name': 'John Doe',
        'email': 'john.doe@example.com',
        'phone': '+1-555-0123',
        'department': 'Engineering',
        'position': 'Senior Software Engineer',
        'hire_date': '2023-01-15',
        'manager': 'Sarah Johnson',
        'location': 'San Francisco',
        'salary_band': 'Senior',
        'employment_type': 'Full-time'
    },
    {
        'id': 2,
        'full_name': 'Jane Smith',
        'email': 'jane.smith@example.com',
        'phone': '+1-555-0124',
        'department': 'Marketing',
        'position': 'Marketing Manager',
        'hire_date': '2023-03-20',
        'manager': 'Mike Chen',
        'location': 'New York',
        'salary_band': 'Mid-level',
        'employment_type': 'Full-time'
    }
]

# Sample knowledge documents
knowledge_documents = [
    {
        'id': 1,
        'title': 'VPN Setup Guide',
        'category': 'IT',
        'type': 'Guide',
        'description': 'Step-by-step instructions for setting up VPN access',
        'content': '1. Download the VPN client...',
        'created_at': '2024-01-15',
        'updated_at': '2024-01-15',
        'views': 45,
        'downloads': 12,
        'rating': 4.5
    },
    {
        'id': 2,
        'title': 'Password Policy',
        'category': 'Security',
        'type': 'Policy',
        'description': 'Company password requirements and best practices',
        'content': 'All passwords must be at least 12 characters...',
        'created_at': '2024-01-10',
        'updated_at': '2024-01-10',
        'views': 78,
        'downloads': 23,
        'rating': 4.2
    }
]

# Sample induction documents
induction_documents = [
    {
        'id': 1,
        'title': 'Welcome to the Company',
        'category': 'Onboarding',
        'type': 'Welcome',
        'description': 'Introduction to company culture and values',
        'content': 'Welcome to our amazing team...',
        'priority': 'high',
        'status': 'published',
        'created_at': '2024-01-01',
        'tags': 'onboarding, culture, welcome'
    },
    {
        'id': 2,
        'title': 'IT Setup Guide',
        'category': 'IT',
        'type': 'Guide',
        'description': 'Setting up your computer and accounts',
        'content': 'Follow these steps to set up your workstation...',
        'priority': 'critical',
        'status': 'published',
        'created_at': '2024-01-01',
        'tags': 'it, setup, computer'
    }
]

# Sample learning courses
learning_courses = [
    {
        'id': 1,
        'title': 'JavaScript Fundamentals',
        'category': 'Programming',
        'duration': '4 hours',
        'difficulty': 'beginner',
        'description': 'Learn the basics of JavaScript programming',
        'status': 'active',
        'enrolled_students': 25,
        'completion_rate': 85
    },
    {
        'id': 2,
        'title': 'Leadership Skills',
        'category': 'Soft Skills',
        'duration': '6 hours',
        'difficulty': 'intermediate',
        'description': 'Develop essential leadership competencies',
        'status': 'active',
        'enrolled_students': 18,
        'completion_rate': 92
    }
]

# Sample onboarding tasks
onboarding_tasks = [
    {
        'id': 1,
        'title': 'Complete IT Setup',
        'description': 'Set up computer, email, and necessary software',
        'category': 'IT',
        'status': 'completed',
        'due_date': '2024-01-05'
    },
    {
        'id': 2,
        'title': 'HR Paperwork',
        'description': 'Complete all required HR forms and documentation',
        'category': 'HR',
        'status': 'pending',
        'due_date': '2024-01-10'
    }
]

# Sample internal jobs
mock_internal_jobs = [
    {
        'id': 1,
        'title': 'Senior Product Manager',
        'department': 'Product',
        'location': 'San Francisco, CA',
        'job_type': 'full-time',
        'description': 'Lead product strategy and development for our core platform. You will work closely with engineering, design, and business teams to define and execute product vision.',
        'requirements': '<ul><li>5+ years of product management experience</li><li>Strong analytical and problem-solving skills</li><li>Experience with Agile methodology</li><li>Excellent communication and leadership abilities</li><li>Technical background preferred</li></ul>',
        'salary_range': '$130,000 - $160,000',
        'posted_date': '2024-01-15',
        'deadline_date': '2024-02-15',
        'status': 'active'
    },
    {
        'id': 2,
        'title': 'UX Designer',
        'department': 'Design',
        'location': 'Remote',
        'job_type': 'full-time',
        'description': 'Create user-centered design solutions that enhance user experience across our digital products. Collaborate with cross-functional teams to deliver intuitive and accessible designs.',
        'requirements': '<ul><li>3+ years of UX design experience</li><li>Proficiency in Figma, Sketch, or similar tools</li><li>Strong user research and testing skills</li><li>Portfolio demonstrating user-centered design</li><li>Experience with design systems</li></ul>',
        'salary_range': '$90,000 - $120,000',
        'posted_date': '2024-01-20',
        'deadline_date': '2024-02-20',
        'status': 'active'
    },
    {
        'id': 3,
        'title': 'Data Scientist',
        'department': 'Engineering',
        'location': 'New York, NY',
        'job_type': 'full-time',
        'description': 'Develop machine learning models and data-driven insights to drive business decisions. Work with large datasets and collaborate with engineering teams to implement scalable solutions.',
        'requirements': '<ul><li>Masters degree in Computer Science, Statistics, or related field</li><li>3+ years of experience in data science</li><li>Proficiency in Python, R, SQL</li><li>Experience with ML frameworks (TensorFlow, PyTorch)</li><li>Strong statistical analysis skills</li></ul>',
        'salary_range': '$110,000 - $140,000',
        'posted_date': '2024-01-25',
        'deadline_date': '2024-02-25',
        'status': 'active'
    },
    {
        'id': 4,
        'title': 'Marketing Manager',
        'department': 'Marketing',
        'location': 'Los Angeles, CA',
        'job_type': 'full-time',
        'description': 'Develop and execute comprehensive marketing strategies to drive brand awareness and customer acquisition. Lead campaigns across digital and traditional channels.',
        'requirements': '<ul><li>4+ years of marketing experience</li><li>Experience with digital marketing tools and platforms</li><li>Strong analytical and creative skills</li><li>Experience with CRM systems</li><li>Excellent project management abilities</li></ul>',
        'salary_range': '$85,000 - $110,000',
        'posted_date': '2024-01-30',
        'deadline_date': '2024-02-28',
        'status': 'active'
    },
    {
        'id': 5,
        'title': 'DevOps Engineer',
        'department': 'Engineering',
        'location': 'Austin, TX',
        'job_type': 'full-time',
        'description': 'Build and maintain cloud infrastructure, implement CI/CD pipelines, and ensure system reliability and scalability. Work closely with development teams to optimize deployment processes.',
        'requirements': '<ul><li>3+ years of DevOps experience</li><li>Experience with AWS, Azure, or GCP</li><li>Proficiency in Docker, Kubernetes</li><li>Experience with CI/CD tools (Jenkins, GitLab)</li><li>Strong scripting skills (Python, Bash)</li></ul>',
        'salary_range': '$100,000 - $130,000',
        'posted_date': '2024-02-01',
        'deadline_date': '2024-03-01',
        'status': 'active'
    },
    {
        'id': 6,
        'title': 'HR Business Partner',
        'department': 'Human Resources',
        'location': 'Chicago, IL',
        'job_type': 'full-time',
        'description': 'Partner with business leaders to develop and implement HR strategies that support organizational goals. Provide guidance on employee relations, performance management, and talent development.',
        'requirements': '<ul><li>5+ years of HR experience</li><li>Experience in a business partner role</li><li>Strong knowledge of employment law</li><li>Excellent interpersonal and communication skills</li><li>Experience with HRIS systems</li></ul>',
        'salary_range': '$80,000 - $105,000',
        'posted_date': '2024-02-05',
        'deadline_date': '2024-03-05',
        'status': 'active'
    },
    {
        'id': 7,
        'title': 'Frontend Developer',
        'department': 'Engineering',
        'location': 'Remote',
        'job_type': 'full-time',
        'description': 'Build responsive and interactive user interfaces using modern web technologies. Collaborate with designers and backend developers to create seamless user experiences.',
        'requirements': '<ul><li>3+ years of frontend development experience</li><li>Proficiency in JavaScript, React, Vue.js</li><li>Experience with CSS frameworks (Tailwind, Bootstrap)</li><li>Understanding of web accessibility standards</li><li>Experience with version control (Git)</li></ul>',
        'salary_range': '$85,000 - $115,000',
        'posted_date': '2024-02-10',
        'deadline_date': '2024-03-10',
        'status': 'active'
    },
    {
        'id': 8,
        'title': 'Sales Manager',
        'department': 'Sales',
        'location': 'Boston, MA',
        'job_type': 'full-time',
        'description': 'Lead a team of sales representatives to achieve revenue targets and drive business growth. Develop sales strategies and build relationships with key clients.',
        'requirements': '<ul><li>5+ years of sales experience</li><li>2+ years of sales management experience</li><li>Proven track record of meeting/exceeding targets</li><li>Experience with CRM systems (Salesforce)</li><li>Excellent leadership and coaching skills</li></ul>',
        'salary_range': '$90,000 - $120,000 + Commission',
        'posted_date': '2024-02-15',
        'deadline_date': '2024-03-15',
        'status': 'active'
    }
]

# Sample skills assessment questions
skills_assessment_questions = [
    {
        'id': 1,
        'question': 'What is the primary purpose of JavaScript?',
        'options': [
            'To style web pages',
            'To add interactivity to web pages',
            'To create databases',
            'To send emails'
        ],
        'correct_answer': 1,
        'category': 'Programming'
    },
    {
        'id': 2,
        'question': 'Which of the following is NOT a JavaScript framework?',
        'options': [
            'React',
            'Angular',
            'Vue.js',
            'Django'
        ],
        'correct_answer': 3,
        'category': 'Programming'
    },
    {
        'id': 3,
        'question': 'What does API stand for?',
        'options': [
            'Application Programming Interface',
            'Advanced Programming Interface',
            'Automated Programming Interface',
            'Application Process Interface'
        ],
        'correct_answer': 0,
        'category': 'Technical'
    }
]

# Sample learning roadmap
learning_roadmap = {
    'current_level': 'Intermediate',
    'target_level': 'Advanced',
    'improvement_areas': [
        'Advanced JavaScript concepts',
        'System design principles',
        'Performance optimization'
    ],
    'recommended_path': [
        {
            'title': 'Advanced JavaScript Course',
            'duration': '6 weeks',
            'provider': 'Udemy',
            'priority': 'high'
        },
        {
            'title': 'System Design Interview Prep',
            'duration': '8 weeks',
            'provider': 'Coursera',
            'priority': 'medium'
        },
        {
            'title': 'Web Performance Optimization',
            'duration': '4 weeks',
            'provider': 'LinkedIn Learning',
            'priority': 'low'
        }
    ]
}

# Helper functions
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def send_email_notification(to_email, subject, message):
    # Email sending logic would go here
    print(f"Email sent to {to_email}: {subject} - {message}")

def add_notification(user_email, message, notification_type="info"):
    try:
        db_helper.create_notification(user_email, message, notification_type)
    except Exception as e:
        print(f"Error creating notification: {e}")

# Routes
@app.route("/")
def home():
    return render_template("landing.html")

@app.route("/it-portal")
@login_required
def it_portal():
    """IT Portal access - dedicated IT interface"""
    # Allow all logged-in users to access IT portal
    # Get IT-specific data - handle both old and new ticket formats
    it_tickets = []
    for t in tickets:
        if isinstance(t, dict):
            if t.get("category") == "IT" or "IT" in t.get("title", "") or "printer" in t.get("title", "").lower() or "vpn" in t.get("title", "").lower():
                it_tickets.append(t)
    
    # If no IT tickets found, create some sample ones
    if not it_tickets:
        it_tickets = [
            {"id": 1, "title": "Printer not connecting", "priority": "high", "status": "open", "date": "2025-08-04", "description": "Printer shows offline status"},
            {"id": 2, "title": "VPN Login Failure", "priority": "medium", "status": "pending", "date": "2025-08-04", "description": "Cannot connect to VPN"},
            {"id": 3, "title": "Email Server Slow", "priority": "low", "status": "resolved", "date": "2025-08-03", "description": "Email response time improved"}
        ]
    
    system_status = [
        {"service": "Email Server", "status": "Operational", "uptime": "99.9%"},
        {"service": "VPN Gateway", "status": "Operational", "uptime": "99.8%"},
        {"service": "Printer Network", "status": "Degraded", "uptime": "85.2%"},
        {"service": "Remote Desktop", "status": "Down", "uptime": "0%"},
        {"service": "File Server", "status": "Operational", "uptime": "99.7%"},
        {"service": "Database Server", "status": "Operational", "uptime": "99.9%"}
    ]
    
    return render_template("it_portal.html", 
                        tickets=it_tickets, 
                        system_status=system_status,
                        total_tickets=len(it_tickets),
                        open_tickets=len([t for t in it_tickets if t.get("status") == "open"]),
                        resolved_tickets=len([t for t in it_tickets if t.get("status") == "resolved"]))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        
        try:
            # Get user from database
            user = db_helper.get_user_by_email(email)
            
            if user:
                # Hash the input password for comparison
                hashed_password = hashlib.sha256(password.encode()).hexdigest()
                
                if user['password'] == hashed_password:
                    session["user"] = email
                    session["role"] = user['role']
                    flash(f"Logged in successfully as {user['role'].title()}!", "success")
                    
                    # Redirect based on role
                    if user['role'] in ['admin', 'it', 'hr']:
                        return redirect(url_for("admin_dashboard"))
                    elif user['role'] == 'employee':
                        return redirect(url_for("employee_dashboard"))
                    else:
                        return redirect(url_for("dashboard"))
                else:
                    flash("Invalid credentials", "error")
            else:
                flash("Invalid credentials", "error")
        except Exception as e:
            print(f"Database error during login: {e}")
            flash("Login error. Please try again.", "error")
    
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("user", None)
    session.pop("role", None)
    flash("Logged out.", "info")
    return redirect(url_for("login"))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        if request.form["password"] != request.form["confirm"]:
            flash("Passwords do not match.", "error")
        else:
            flash("Registered successfully!", "success")
            return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        flash(f"Reset link sent to {request.form['email']}", "info")
        return redirect(url_for("login"))
    return render_template("forgot_password.html")

@app.route("/dashboard")
@login_required
def dashboard():
    if session.get("role") == "admin":
        return redirect(url_for("admin_dashboard"))
    
    # Get user's tickets
    user_tickets = [t for t in tickets if t["user_email"] == session["user"]]
    
    dashboard_data = {
        "open_tickets": len([t for t in user_tickets if t["status"] == "open"]),
        "resolved_tickets": len([t for t in user_tickets if t["status"] == "resolved"]),
        "avg_resolution_time": "2.1 hrs",
        "system_status": [
            {"service": "Email Server", "status": "Operational"},
            {"service": "VPN Gateway", "status": "Operational"},
            {"service": "Printer Network", "status": "Degraded"},
            {"service": "Remote Desktop", "status": "Down"},
        ],
        "recent_tickets": user_tickets[-3:] if len(user_tickets) > 3 else user_tickets
    }
    return render_template("dashboard.html", **dashboard_data)

@app.route("/admin/dashboard")
@login_required
def admin_dashboard():
    if session.get("role") not in ["admin", "it", "hr", "employee"]:
        flash("Access denied. Admin privileges required.", "error")
        return redirect(url_for("dashboard"))
    
    # Get all data from database
    db_tickets = db_helper.get_all_tickets()
    db_feedback = db_helper.get_all_feedback()
    db_timeoff = db_helper.get_all_timeoff_requests()
    db_leave_requests = db_helper.get_all_leave_requests()
    db_timesheets = db_helper.get_all_timesheets()
    db_applications = db_helper.get_all_applications()
    db_employees = db_helper.get_all_employees()
    
    admin_data = {
        "total_tickets": len(db_tickets),
        "open_tickets": len([t for t in db_tickets if t["status"] == "open"]),
        "resolved_tickets": len([t for t in db_tickets if t["status"] == "resolved"]),
        "total_requests": len(db_timeoff) + len(db_leave_requests),
        "pending_requests": len([r for r in db_timeoff if r["status"] == "pending"]) + len([r for r in db_leave_requests if r["status"] == "pending"]),
        "total_timesheets": len(db_timesheets),
        "pending_timesheets": len([t for t in db_timesheets if t["status"] == "pending"]),
        "total_feedback": len(db_feedback),
        "pending_feedback": len([f for f in db_feedback if f["status"] == "pending"]),
        "total_applications": len(db_applications),
        "pending_applications": len([a for a in db_applications if a["status"] == "pending"]),
        "total_users": len(db_employees),
        "recent_tickets": db_tickets[-3:] if len(db_tickets) > 3 else db_tickets,
        "recent_requests": (db_timeoff + db_leave_requests)[-3:] if len(db_timeoff + db_leave_requests) > 3 else (db_timeoff + db_leave_requests),
        "recent_timesheets": db_timesheets[-3:] if len(db_timesheets) > 3 else db_timesheets,
        "recent_feedback": db_feedback[-3:] if len(db_feedback) > 3 else db_feedback,
        "system_status": {
            "database": "Connected",
            "ai_services": "Available" if rag_initialized else "Unavailable",
            "notifications": "Active"
        }
    }
    return render_template("admin_dashboard.html", **admin_data)

@app.route("/admin/tickets")
@it_required
def admin_tickets():
    if session.get("role") not in ["admin", "it", "hr"]:
        flash("Access denied. Admin privileges required.", "error")
        return redirect(url_for("dashboard"))
    
    # Get tickets from database
    tickets = db_helper.get_all_tickets()
    
    return render_template('admin_tickets.html', tickets=tickets, now=datetime.now())

@app.route("/admin/requests")
@hr_required
def admin_requests():
    if session.get("role") not in ["admin", "it", "hr"]:
        flash("Access denied. Admin privileges required.", "error")
        return redirect(url_for("dashboard"))
    
    # Get timeoff requests from database
    timeoff_requests = db_helper.get_all_timeoff_requests()
    
    # Transform the data to match template expectations
    formatted_requests = []
    for req in timeoff_requests:
        formatted_requests.append({
            'id': req['id'],
            'title': f"Timeoff Request - {req['employee_name']}",
            'description': req.get('reason', 'No reason provided'),
            'user_email': req['employee_name'],
            'type': 'Timeoff',
            'status': req['status'],
            'date': req['submitted_at']
        })
    
    return render_template('admin_requests.html', requests=formatted_requests)

@app.route("/admin/update-ticket-status/<int:ticket_id>", methods=["POST"])
@login_required
def update_ticket_status(ticket_id):
    if session.get("role") not in ["admin", "it", "hr"]:
        flash("Access denied. Admin privileges required.", "error")
        return redirect(url_for("dashboard"))
    
    new_status = request.form["status"]
    
    # Update ticket status in database
    if db_helper.update_ticket_status(ticket_id, new_status):
        # Get ticket details for notification
        tickets = db_helper.get_all_tickets()
        ticket = next((t for t in tickets if t["id"] == ticket_id), None)
        
        if ticket:
            # Add notification
            db_helper.create_notification(ticket["user_email"], f"Your ticket '{ticket['title']}' status changed to {new_status}")
            
            # Send email notification
            send_email_notification(ticket["user_email"], "Ticket Status Updated", 
                                  f"Your ticket '{ticket['title']}' status has been updated to {new_status}")
        
        flash(f"Ticket status updated to {new_status}", "success")
    else:
        flash("Error updating ticket status", "error")
    
    return redirect(url_for("admin_tickets"))

@app.route("/admin/assign-ticket/<int:ticket_id>", methods=["POST"])
@admin_required
def assign_ticket(ticket_id):
    if session.get("role") not in ["admin", "it"]:
        flash("Access denied. Admin privileges required.", "error")
        return redirect(url_for("dashboard"))
    
    ticket = next((t for t in tickets if t["id"] == ticket_id), None)
    if not ticket:
        flash("Ticket not found.", "error")
        return redirect(url_for("admin_tickets"))
    
    assigned_to = request.form.get('assigned_to')
    if assigned_to:
        ticket["assigned_to"] = assigned_to
        ticket["assigned_date"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        ticket["assigned_by"] = session["user"]
        
        # Add notification for the assigned person
        add_notification(assigned_to, f"You have been assigned ticket #{ticket_id}: {ticket['title']}")
        
        flash(f"Ticket assigned to {assigned_to} successfully!", "success")
    else:
        flash("Please provide an assignee", "error")
    
    return redirect(url_for("admin_tickets"))

@app.route("/admin/delete-ticket/<int:ticket_id>", methods=["POST"])
@login_required
def delete_ticket(ticket_id):
    if session.get("role") not in ["admin", "it", "hr"]:
        flash("Access denied. Admin privileges required.", "error")
        return redirect(url_for("dashboard"))
    
    if db_helper.delete_ticket(ticket_id):
        flash("Ticket deleted successfully!", "success")
    else:
        flash("Error deleting ticket", "error")
    
    return redirect(url_for("admin_tickets"))

@app.route("/admin/mark-ticket-done/<int:ticket_id>", methods=["POST"])
@login_required
def mark_ticket_done(ticket_id):
    if session.get("role") not in ["admin", "it", "hr"]:
        flash("Access denied. Admin privileges required.", "error")
        return redirect(url_for("dashboard"))
    
    if db_helper.mark_ticket_done(ticket_id):
        flash("Ticket marked as done!", "success")
    else:
        flash("Error marking ticket as done", "error")
    
    return redirect(url_for("admin_tickets"))

@app.route("/admin/add-ticket-comment/<int:ticket_id>", methods=["POST"])
@login_required
def add_ticket_comment(ticket_id):
    if session.get("role") not in ["admin", "it", "hr"]:
        flash("Access denied. Admin privileges required.", "error")
        return redirect(url_for("dashboard"))
    
    comment = request.form.get("comment")
    if comment:
        if db_helper.add_ticket_comment(ticket_id, comment, session["user"]):
            flash("Comment added successfully!", "success")
        else:
            flash("Error adding comment", "error")
    
    return redirect(url_for("ticket_detail", ticket_id=ticket_id))

@app.route("/admin/update-request-status/<int:request_id>", methods=["POST"])
@login_required
def update_request_status(request_id):
    if session.get("role") not in ["admin", "it", "hr"]:
        flash("Access denied. Admin privileges required.", "error")
        return redirect(url_for("dashboard"))
    
    new_status = request.form["status"]
    request_item = next((r for r in requests_data if r["id"] == request_id), None)
    
    if request_item:
        old_status = request_item["status"]
        request_item["status"] = new_status
        
        # Add notification
        add_notification(request_item["submitted_by"], f"Your request '{request_item['subject']}' status changed from {old_status} to {new_status}")
        
        # Send email notification
        send_email_notification(request_item["submitted_by"], "Request Status Updated", 
                              f"Your request '{request_item['subject']}' status has been updated to {new_status}")
        
        flash(f"Request status updated to {new_status}", "success")
    
    return redirect(url_for("admin_requests"))

@app.route("/admin/add-hr-comment/<int:request_id>", methods=["POST"])
@login_required
def add_hr_comment(request_id):
    if session.get("role") not in ["admin", "it", "hr"]:
        flash("Access denied. Admin privileges required.", "error")
        return redirect(url_for("dashboard"))
    
    comment = request.form["hr_comment"]
    request_item = next((r for r in requests_data if r["id"] == request_id), None)
    
    if request_item:
        request_item["hr_comment"] = comment
        
        # Add notification
        add_notification(request_item["submitted_by"], f"HR comment added to your request '{request_item['subject']}'")
        
        # Send email notification
        send_email_notification(request_item["submitted_by"], "HR Comment Added", 
                              f"An HR comment has been added to your request '{request_item['subject']}': {comment}")
        
        flash("HR comment added successfully", "success")
    
    return redirect(url_for("admin_requests"))

# ===== NEW COMPREHENSIVE ADMIN MANAGEMENT ROUTES =====

@app.route("/admin/timeoff")
@hr_required
def admin_timeoff():
    if session.get("role") not in ["admin", "it", "hr"]:
        flash("Access denied. Admin privileges required.", "error")
        return redirect(url_for("dashboard"))
    
    # Get timeoff requests from database
    timeoff_requests = db_helper.get_all_timeoff_requests()
    
    return render_template('admin_timeoff.html', timeoff_requests=timeoff_requests)

@app.route("/admin/leave")
@hr_required
def admin_leave():
    if session.get("role") not in ["admin", "it", "hr"]:
        flash("Access denied. Admin privileges required.", "error")
        return redirect(url_for("dashboard"))
    
    # Get leave requests from database
    leave_requests = db_helper.get_all_leave_requests()
    
    return render_template('admin_leave.html', leave_requests=leave_requests)

@app.route("/admin/applications")
@hr_required
def admin_applications():
    if session.get("role") not in ["admin", "it", "hr"]:
        flash("Access denied. Admin privileges required.", "error")
        return redirect(url_for("dashboard"))
    
    # Sample applications data
    applications = [
        {
            'id': 1,
            'job_title': 'Senior Software Engineer',
            'applicant_name': 'John Doe',
            'email': 'john.doe@example.com',
            'status': 'pending',
            'applied_date': '2024-01-15',
            'experience': '5 years',
            'skills': ['Python', 'JavaScript', 'React']
        },
        {
            'id': 2,
            'job_title': 'Product Manager',
            'applicant_name': 'Jane Smith',
            'email': 'jane.smith@example.com',
            'status': 'reviewed',
            'applied_date': '2024-01-10',
            'experience': '3 years',
            'skills': ['Product Management', 'Agile', 'User Research']
        },
        {
            'id': 3,
            'job_title': 'Data Scientist',
            'applicant_name': 'Mike Johnson',
            'email': 'mike.johnson@example.com',
            'status': 'approved',
            'applied_date': '2024-01-05',
            'experience': '4 years',
            'skills': ['Python', 'Machine Learning', 'SQL']
        }
    ]
    
    return render_template('admin_applications.html', applications=applications)

@app.route("/admin/badges")
@login_required
def admin_badges():
    if session.get("role") not in ["admin", "it", "hr"]:
        flash("Access denied. Admin privileges required.", "error")
        return redirect(url_for("dashboard"))
    
    # Get badges from database
    badges = db_helper.get_all_badges()
    
    # If no badges exist, create some default ones
    if not badges:
        default_badges = [
            ('Python Expert', 'Advanced Python programming skills', '🐍', 'Technical'),
            ('Team Player', 'Excellent collaboration skills', '🤝', 'Soft Skills'),
            ('Problem Solver', 'Strong analytical thinking', '🧠', 'Problem Solving'),
            ('Leadership', 'Demonstrated leadership abilities', '👑', 'Leadership'),
            ('Communication Pro', 'Excellent communication skills', '🗣️', 'Communication'),
            ('Innovation', 'Creative problem solving', '💡', 'Innovation')
        ]
        
        for name, description, icon, category in default_badges:
            db_helper.create_badge(name, description, icon, category)
        
        badges = db_helper.get_all_badges()
    
    return render_template('admin_badges.html', badges=badges)

# Employee Directory Data Structure
employee_directory = [
    {
        'id': 1,
        'name': 'John Doe',
        'email': 'john.doe@company.com',
        'phone': '+1 (555) 123-4567',
        'department': 'IT',
        'position': 'Software Engineer',
        'hire_date': '2023-01-15',
        'manager': 'Sarah Johnson',
        'location': 'New York',
        'status': 'Active',
        'employee_id': 'EMP001',
        'salary_band': 'Band 3',
        'employment_type': 'Full-time',
        'profile_picture': None
    },
    {
        'id': 2,
        'name': 'Jane Smith',
        'email': 'jane.smith@company.com',
        'phone': '+1 (555) 234-5678',
        'department': 'HR',
        'position': 'HR Manager',
        'hire_date': '2022-06-10',
        'manager': 'Mike Wilson',
        'location': 'San Francisco',
        'status': 'Active',
        'employee_id': 'EMP002',
        'salary_band': 'Band 4',
        'employment_type': 'Full-time',
        'profile_picture': None
    },
    {
        'id': 3,
        'name': 'Bob Johnson',
        'email': 'bob.johnson@company.com',
        'phone': '+1 (555) 345-6789',
        'department': 'Marketing',
        'position': 'Marketing Specialist',
        'hire_date': '2023-03-20',
        'manager': 'Lisa Chen',
        'location': 'Chicago',
        'status': 'Active',
        'employee_id': 'EMP003',
        'salary_band': 'Band 2',
        'employment_type': 'Full-time',
        'profile_picture': None
    },
    {
        'id': 4,
        'name': 'Alice Brown',
        'email': 'alice.brown@company.com',
        'phone': '+1 (555) 456-7890',
        'department': 'Finance',
        'position': 'Financial Analyst',
        'hire_date': '2022-11-05',
        'manager': 'David Lee',
        'location': 'Boston',
        'status': 'Active',
        'employee_id': 'EMP004',
        'salary_band': 'Band 3',
        'employment_type': 'Full-time',
        'profile_picture': None
    },
    {
        'id': 5,
        'name': 'Charlie Wilson',
        'email': 'charlie.wilson@company.com',
        'phone': '+1 (555) 567-8901',
        'department': 'Sales',
        'position': 'Sales Representative',
        'hire_date': '2023-08-12',
        'manager': 'Emma Davis',
        'location': 'Los Angeles',
        'status': 'Active',
        'employee_id': 'EMP005',
        'salary_band': 'Band 2',
        'employment_type': 'Full-time',
        'profile_picture': None
    }
]

@app.route('/admin/employees')
@admin_required
def admin_employees():
    if session.get("role") not in ["admin", "it", "hr"]:
        flash("Access denied. Admin privileges required.", "error")
        return redirect(url_for("dashboard"))
    
    # Use employee_directory for consistency
    return render_template('admin_employees.html', employees=employee_directory)

@app.route('/admin/employees/<int:employee_id>')
@admin_required
def view_employee(employee_id):
    if session.get("role") not in ["admin", "it", "hr"]:
        flash("Access denied. Admin privileges required.", "error")
        return redirect(url_for("dashboard"))
    
    employee = next((e for e in employee_directory if e['id'] == employee_id), None)
    
    if not employee:
        flash('Employee not found!', 'error')
        return redirect(url_for('admin_employees'))
    
    # Get employee's related data
    employee_leaves = [l for l in leave_requests if l['employee_id'] == employee_id]
    employee_timesheets = [t for t in timesheets if t['employee_id'] == employee_id]
    employee_feedback = [f for f in anonymous_feedback if f.get('employee_id') == employee_id]
    
    return render_template('admin_employee_detail.html', 
                         employee=employee,
                         leaves=employee_leaves,
                         timesheets=employee_timesheets,
                         feedback=employee_feedback)

@app.route('/admin/employees/add', methods=['GET', 'POST'])
@admin_required
def add_employee():
    if session.get("role") not in ["admin", "it", "hr"]:
        flash("Access denied. Admin privileges required.", "error")
        return redirect(url_for("dashboard"))
    
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        department = request.form.get('department')
        position = request.form.get('position')
        hire_date = request.form.get('hire_date')
        manager = request.form.get('manager')
        location = request.form.get('location')
        salary_band = request.form.get('salary_band')
        employment_type = request.form.get('employment_type')
        
        if name and email:
            employee_id = len(employee_directory) + 1
            new_employee = {
                'id': employee_id,
                'name': name,
                'email': email,
                'phone': phone or '',
                'department': department or '',
                'position': position or '',
                'hire_date': hire_date or '',
                'manager': manager or '',
                'location': location or '',
                'status': 'Active',
                'employee_id': f'EMP{employee_id:03d}',
                'salary_band': salary_band or '',
                'employment_type': employment_type or 'Full-time',
                'profile_picture': None
            }
            employee_directory.append(new_employee)
            flash('Employee added successfully!', 'success')
            return redirect(url_for('admin_employees'))
    
    return render_template('admin_add_employee.html')

@app.route('/admin/employees/<int:employee_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_employee(employee_id):
    if session.get("role") not in ["admin", "it", "hr"]:
        flash("Access denied. Admin privileges required.", "error")
        return redirect(url_for("dashboard"))
    
    employee = next((e for e in employee_directory if e['id'] == employee_id), None)
    
    if not employee:
        flash('Employee not found!', 'error')
        return redirect(url_for('admin_employees'))
    
    if request.method == 'POST':
        employee.update({
            'name': request.form.get('name', employee['name']),
            'email': request.form.get('email', employee['email']),
            'phone': request.form.get('phone', employee['phone']),
            'department': request.form.get('department', employee['department']),
            'position': request.form.get('position', employee['position']),
            'hire_date': request.form.get('hire_date', employee['hire_date']),
            'manager': request.form.get('manager', employee['manager']),
            'location': request.form.get('location', employee['location']),
            'status': request.form.get('status', employee['status']),
            'salary_band': request.form.get('salary_band', employee['salary_band']),
            'employment_type': request.form.get('employment_type', employee['employment_type'])
        })
        flash('Employee updated successfully!', 'success')
        return redirect(url_for('view_employee', employee_id=employee_id))
    
    return render_template('admin_edit_employee.html', employee=employee)

@app.route("/admin/update-timeoff-status/<int:timeoff_id>", methods=["POST"])
@login_required
def update_timeoff_status(timeoff_id):
    if session.get("role") not in ["admin", "it", "hr"]:
        flash("Access denied. Admin privileges required.", "error")
        return redirect(url_for("dashboard"))
    
    timeoff_item = next((t for t in timeoff_requests if t["id"] == timeoff_id), None)
    if not timeoff_item:
        flash("Time off request not found.", "error")
        return redirect(url_for("admin_timeoff"))
    
    new_status = request.form.get("status")
    if new_status in ["approved", "rejected", "pending"]:
        timeoff_item["status"] = new_status
        timeoff_item["admin_comment"] = request.form.get("admin_comment", "")
        timeoff_item["processed_by"] = session["user"]
        timeoff_item["processed_date"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        # Add notification for employee
        add_notification(timeoff_item["employee_email"], 
                        f"Your time off request has been {new_status}: {timeoff_item['reason']}")
        
        flash(f"Time off request {new_status}.", "success")
    
    return redirect(url_for("admin_timeoff"))

# Update leave status
@app.route("/admin/update-leave-status/<int:leave_id>", methods=["POST"])
@login_required
def update_leave_status(leave_id):
    if session.get("role") not in ["admin", "it", "hr"]:
        flash("Access denied. Admin privileges required.", "error")
        return redirect(url_for("dashboard"))
    
    leave_item = next((l for l in leave_requests if l["id"] == leave_id), None)
    if not leave_item:
        flash("Leave request not found.", "error")
        return redirect(url_for("admin_leave"))
    
    new_status = request.form.get("status")
    if new_status in ["approved", "rejected", "pending"]:
        leave_item["status"] = new_status
        leave_item["admin_comment"] = request.form.get("admin_comment", "")
        leave_item["processed_by"] = session["user"]
        leave_item["processed_date"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        # Add notification for employee
        # Get employee email from employee_id
        employee = next((e for e in employee_directory if e['id'] == leave_item.get('employee_id')), None)
        if employee:
            add_notification(employee["email"], 
                            f"Your leave request has been {new_status}: {leave_item['leave_type']}")
        
        flash(f"Leave request {new_status}.", "success")
    
    return redirect(url_for("admin_leave"))

# Update application status
@app.route("/admin/update-application-status/<int:app_id>", methods=["POST"])
@login_required
def update_general_application_status(app_id):
    if session.get("role") not in ["admin", "it", "hr"]:
        flash("Access denied. Admin privileges required.", "error")
        return redirect(url_for("dashboard"))
    
    application = next((a for a in job_applications if a["id"] == app_id), None)
    if not application:
        flash("Application not found.", "error")
        return redirect(url_for("admin_applications"))
    
    new_status = request.form.get("status")
    if new_status in ["reviewing", "shortlisted", "rejected", "hired"]:
        application["status"] = new_status
        application["admin_comment"] = request.form.get("admin_comment", "")
        application["processed_by"] = session["user"]
        application["processed_date"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        # Add notification for applicant
        add_notification(application["email"], 
                        f"Your job application has been updated to: {new_status}")
        
        flash(f"Application status updated to {new_status}.", "success")
    
    return redirect(url_for("admin_applications"))

# Assign badge to user
@app.route("/admin/assign-badge/<int:user_id>", methods=["POST"])
@login_required
def assign_badge(user_id):
    if session.get("role") not in ["admin", "it", "hr"]:
        flash("Access denied. Admin privileges required.", "error")
        return redirect(url_for("dashboard"))
    
    # Get user from database
    user = db_helper.get_user_by_email(session["user"])
    if not user:
        flash("User not found.", "error")
        return redirect(url_for("admin_badges"))
    
    badge_id = request.form.get("badge_id")
    badge_reason = request.form.get("badge_reason", "")
    
    if badge_id:
        # Assign badge to user in database
        assignment_id = db_helper.assign_badge_to_user(
            user_id, 
            int(badge_id), 
            session["user"], 
            badge_reason
        )
        
        if assignment_id:
            # Get badge details for notification
            badges = db_helper.get_all_badges()
            badge = next((b for b in badges if b['id'] == int(badge_id)), None)
            badge_name = badge['name'] if badge else "Unknown Badge"
            
            # Add notification for user
            db_helper.create_notification(user["email"], f"You've been awarded the '{badge_name}' badge!", "success")
            
            flash(f"Badge '{badge_name}' assigned to user.", "success")
        else:
            flash("Error assigning badge. Please try again.", "error")
    
    return redirect(url_for("admin_badges"))

@app.route('/tickets')
@login_required
def view_tickets():
    if session.get("role") not in ["admin", "it", "hr"]:
        flash("Access denied. Admin privileges required.", "error")
        return redirect(url_for("dashboard"))
    
    # Get user's tickets from database
    user_tickets = db_helper.get_tickets_by_user(session["user"])
    
    return render_template("tickets.html", tickets=user_tickets)

@app.route("/submit-ticket", methods=["GET", "POST"])
@login_required
def submit_ticket():
    if session.get("role") not in ["admin", "it", "hr"]:
        flash("Access denied. Admin privileges required.", "error")
        return redirect(url_for("dashboard"))
    
    if request.method == "POST":
        title = request.form["title"]
        priority = request.form["priority"]
        description = request.form.get("description", "")
        user_email = session["user"]
        
        # Create ticket in database
        ticket_id = db_helper.create_ticket(title, description, priority, user_email)
        
        if ticket_id:
            # Add notification for admin
            db_helper.create_notification("admin@example.com", f"New ticket submitted: {title}", "warning")
            
            flash("Ticket submitted successfully!", "success")
        else:
            flash("Error submitting ticket. Please try again.", "error")
        
        return redirect(url_for("view_tickets"))
    
    return render_template("submit_ticket.html")

@app.route("/ticket/<int:ticket_id>")
@login_required
def ticket_detail(ticket_id):
    if session.get("role") not in ["admin", "it", "hr"]:
        flash("Access denied. Admin privileges required.", "error")
        return redirect(url_for("dashboard"))
    
    # Get ticket from database
    tickets = db_helper.get_all_tickets()
    ticket = next((t for t in tickets if t["id"] == ticket_id), None)
    if not ticket:
        flash("Ticket not found.", "error")
        return redirect(url_for("view_tickets"))
    
    # Check if user can view this ticket
    if session.get("role") != "admin" and ticket["user_email"] != session["user"]:
        flash("Access denied.", "error")
        return redirect(url_for("view_tickets"))
    
    return render_template("ticket_details.html", ticket=ticket, comments=comments.get(ticket_id, []))

@app.route("/ticket/<int:ticket_id>/comment", methods=["POST"])
@login_required
def add_comment(ticket_id):
    if session.get("role") not in ["admin", "it", "hr"]:
        flash("Access denied. Admin privileges required.", "error")
        return redirect(url_for("dashboard"))
    
    ticket = next((t for t in tickets if t["id"] == ticket_id), None)
    if not ticket:
        flash("Ticket not found.", "error")
        return redirect(url_for("view_tickets"))
    
    # Check if user can comment on this ticket
    if session.get("role") != "admin" and ticket["user_email"] != session["user"]:
        flash("Access denied.", "error")
        return redirect(url_for("view_tickets"))
    
    comment_data = {
        "author": session["user"],
        "message": request.form["message"],
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "author_type": session.get("role", "user")
    }
    
    comments.setdefault(ticket_id, []).append(comment_data)
    
    # Add notification for other party
    if session.get("role") == "admin":
        add_notification(ticket["user_email"], f"Admin commented on your ticket: {ticket['title']}")
    else:
        add_notification("admin@example.com", f"User commented on ticket: {ticket['title']}")
    
    flash("Comment added.", "success")
    return redirect(url_for("ticket_detail", ticket_id=ticket_id))

@app.route("/submit-request", methods=["GET", "POST"])
@login_required
def submit_request():
    if session.get("role") not in ["admin", "it", "hr"]:
        flash("Access denied. Admin privileges required.", "error")
        return redirect(url_for("dashboard"))
    
    if request.method == "POST":
        new_request = {
            "id": len(requests_data) + 1,
            "type": request.form["type"],
            "subject": request.form["subject"],
            "description": request.form["description"],
            "submitted_by": session["user"],
            "status": "pending",
            "attachments": []
        }
        
        # Handle file uploads
        if 'attachments' in request.files:
            files = request.files.getlist('attachments')
            for file in files:
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(file_path)
                    new_request["attachments"].append(filename)
        
        requests_data.append(new_request)
        
        # Add notification for admin
        add_notification("admin@example.com", f"New request submitted: {new_request['subject']}", "warning")
        
        flash("Request submitted.", "success")
        return redirect(url_for("dashboard"))
    
    return render_template("submit_request.html", prefill_type=request.args.get("type", ""))

@app.route("/request-history")
@login_required
def request_history():
    if session.get("role") not in ["admin", "it", "hr"]:
        flash("Access denied. Admin privileges required.", "error")
        return redirect(url_for("dashboard"))
    
    if session.get("role") == "admin":
        return redirect(url_for("admin_requests"))
    
    user_requests = [r for r in requests_data if r["submitted_by"] == session["user"]]
    return render_template("request_history.html", requests=user_requests)

@app.route("/cancel-request/<int:req_id>", methods=["POST"])
@login_required
def cancel_request(req_id):
    if session.get("role") not in ["admin", "it", "hr"]:
        flash("Access denied. Admin privileges required.", "error")
        return redirect(url_for("dashboard"))
    
    for r in requests_data:
        if r["id"] == req_id and (r["submitted_by"] == session["user"] or session.get("role") == "admin"):
            r["status"] = "cancelled"
            break
    
    flash("Request cancelled.", "info")
    return redirect(url_for("request_history"))

@app.route("/notifications")
@login_required
def view_notifications():
    # Allow both employees and admins to view notifications
    user_notifications = [n for n in notifications if n["user_email"] == session["user"]]
    return render_template("notifications.html", notifications=user_notifications)

@app.route("/notifications/mark-read/<int:notification_id>", methods=["POST"])
@login_required
def mark_notification_read(notification_id):
    # Allow both employees and admins to mark notifications as read
    notification = next((n for n in notifications if n["id"] == notification_id and n["user_email"] == session["user"]), None)
    if notification:
        notification["read"] = True
    
    return redirect(url_for("view_notifications"))

@app.route("/system-status")
@login_required
def system_status():
    if session.get("role") not in ["admin", "it", "hr"]:
        flash("Access denied. Admin privileges required.", "error")
        return redirect(url_for("dashboard"))
    
    return render_template("system_status.html", systems=[
        {"name": "Email Server", "description": "Handles mail.", "status": "Operational"},
        {"name": "VPN Gateway", "description": "Remote access", "status": "Operational"},
        {"name": "Printer Network", "description": "Print queue", "status": "Degraded"},
        {"name": "Remote Desktop", "description": "Virtual access", "status": "Down"},
    ])

@app.route("/faqs")
@login_required
def faqs():
    if session.get("role") not in ["admin", "it", "hr"]:
        flash("Access denied. Admin privileges required.", "error")
        return redirect(url_for("dashboard"))
    
    return render_template("faqs.html")

@app.route("/resources")
@login_required
def resources():
    if session.get("role") not in ["admin", "it", "hr"]:
        flash("Access denied. Admin privileges required.", "error")
        return redirect(url_for("dashboard"))
    
    # IT Resources data
    it_resources = [
        {"title": "VPN Client", "description": "VPN installation guide", "link": "#", "category": "Security"},
        {"title": "Email Setup", "description": "Configure email client", "link": "#", "category": "Communication"},
        {"title": "Password Policy", "description": "Password requirements", "link": "#", "category": "Security"},
        {"title": "Backup Guide", "description": "Data backup procedures", "link": "#", "category": "Data Protection"},
        {"title": "Software Installation", "description": "Install approved software", "link": "#", "category": "Software"}
    ]
    
    # FAQs data
    faqs = [
        {"question": "How do I reset my password?", "answer": "Contact IT support or use the password reset portal.", "category": "Account Management"},
        {"question": "What should I do if my computer is slow?", "answer": "Restart your computer and close unnecessary applications.", "category": "Performance"},
        {"question": "How do I connect to the VPN?", "answer": "Download the VPN client and follow the setup guide.", "category": "Network"},
        {"question": "Can I install software on my work computer?", "answer": "Only approved software can be installed. Contact IT for requests.", "category": "Software"},
        {"question": "What's the IT support phone number?", "answer": "Call 555-IT-HELP for immediate assistance.", "category": "Support"}
    ]
    
    return render_template("resources.html", resources=it_resources, faqs=faqs)

# Profile Data Structure
user_profiles = {}

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user']  # session['user'] is the email string
    
    if request.method == 'POST':
        # Handle profile picture upload
        if 'profile_picture' in request.files:
            file = request.files['profile_picture']
            if file and file.filename:
                # Save profile picture
                filename = f"profile_{user_id}_{int(time.time())}.jpg"
                filepath = os.path.join('static', 'uploads', 'profiles', filename)
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                file.save(filepath)
                
                if user_id not in user_profiles:
                    user_profiles[user_id] = {}
                user_profiles[user_id]['profile_picture'] = f"uploads/profiles/{filename}"
                flash('Profile picture updated successfully!', 'success')
        
        # Update profile information
        if user_id not in user_profiles:
            user_profiles[user_id] = {}
        
        user_profiles[user_id].update({
            'phone': request.form.get('phone', ''),
            'address': request.form.get('address', ''),
            'emergency_contact': request.form.get('emergency_contact', ''),
            'emergency_phone': request.form.get('emergency_phone', ''),
            'skills': request.form.get('skills', ''),
            'interests': request.form.get('interests', ''),
            'bio': request.form.get('bio', ''),
            'linkedin': request.form.get('linkedin', ''),
            'github': request.form.get('github', ''),
            'website': request.form.get('website', ''),
            'department': request.form.get('department', ''),
            'position': request.form.get('position', ''),
            'hire_date': request.form.get('hire_date', ''),
            'manager': request.form.get('manager', ''),
            'work_location': request.form.get('work_location', ''),
            'employment_type': request.form.get('employment_type', ''),
            'salary_band': request.form.get('salary_band', ''),
            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile'))
    
    # Get user profile data
    profile_data = user_profiles.get(user_id, {})
    
    return render_template('profile.html', 
                         user=session['user'],
                         profile=profile_data)

@app.route('/catalog')
@login_required
def catalog():
    if session.get("role") not in ["admin", "it", "hr"]:
        flash("Access denied. Admin privileges required.", "error")
        return redirect(url_for("dashboard"))
    
    # Software catalog data
    software_catalog = [
        {'name': 'Microsoft Office 365', 'category': 'Productivity', 'version': '2023', 'license': 'Enterprise', 'status': 'Available'},
        {'name': 'Adobe Creative Suite', 'category': 'Design', 'version': '2024', 'license': 'Creative Cloud', 'status': 'Available'},
        {'name': 'Visual Studio Code', 'category': 'Development', 'version': '1.85.0', 'license': 'Free', 'status': 'Available'},
        {'name': 'Slack', 'category': 'Communication', 'version': 'Latest', 'license': 'Pro', 'status': 'Available'},
        {'name': 'Zoom', 'category': 'Communication', 'version': '5.17.0', 'license': 'Pro', 'status': 'Available'}
    ]
    
    # Device management data
    devices = [
        {'id': 1, 'name': 'Dell XPS 13', 'type': 'laptop', 'assigned_to': 'employee1@example.com', 'status': 'lent', 'lent_date': '2025-07-01'},
        {'id': 2, 'name': 'iPhone 13', 'type': 'mobile', 'assigned_to': '', 'status': 'available', 'lent_date': ''},
        {'id': 3, 'name': 'HP EliteDesk', 'type': 'desktop', 'assigned_to': '', 'status': 'available', 'lent_date': ''},
        {'id': 4, 'name': 'MacBook Pro', 'type': 'laptop', 'assigned_to': 'employee2@example.com', 'status': 'lent', 'lent_date': '2025-06-15'},
        {'id': 5, 'name': 'iPad Pro', 'type': 'tablet', 'assigned_to': '', 'status': 'available', 'lent_date': ''}
    ]
    
    return render_template("catalog.html", software_catalog=software_catalog, devices=devices)

@app.route("/careers")
@login_required
def careers():
    if session.get("role") not in ["admin", "it", "hr"]:
        flash("Access denied. Admin privileges required.", "error")
        return redirect(url_for("dashboard"))
    
    # Sample job data
    jobs = [
        {'id': 1, 'title': 'Senior Software Engineer', 'company': 'Tech Corp', 'location': 'Remote', 'type': 'Full-time', 'salary': '$120k-$150k'},
        {'id': 2, 'title': 'Product Manager', 'company': 'Innovation Inc', 'location': 'San Francisco', 'type': 'Full-time', 'salary': '$130k-$160k'},
        {'id': 3, 'title': 'Data Scientist', 'company': 'Analytics Co', 'location': 'New York', 'type': 'Full-time', 'salary': '$110k-$140k'},
        {'id': 4, 'title': 'UX Designer', 'company': 'Design Studio', 'location': 'Remote', 'type': 'Full-time', 'salary': '$90k-$120k'},
        {'id': 5, 'title': 'DevOps Engineer', 'company': 'Cloud Solutions', 'location': 'Austin', 'type': 'Full-time', 'salary': '$100k-$130k'}
    ]
    
    return render_template("careers.html", jobs=jobs)

# Career Portal Sub-routes
@app.route("/careers/applications")
@login_required
def careers_applications():
    if session.get("role") not in ["admin", "it", "hr"]:
        flash("Access denied. Admin privileges required.", "error")
        return redirect(url_for("dashboard"))
    
    return render_template("careers_applications.html")

@app.route("/careers/resume")
@login_required
def careers_resume():
    if session.get("role") not in ["admin", "it", "hr"]:
        flash("Access denied. Admin privileges required.", "error")
        return redirect(url_for("dashboard"))
    
    return render_template("careers_resume.html")

@app.route("/careers/upskilling")
@login_required
def careers_upskilling():
    if session.get("role") not in ["admin", "it", "hr"]:
        flash("Access denied. Admin privileges required.", "error")
        return redirect(url_for("dashboard"))
    
    return render_template("careers_upskilling.html")

@app.route("/careers/mentorship", methods=['GET', 'POST'])
@login_required
def careers_mentorship():
    if session.get("role") not in ["admin", "it", "hr"]:
        flash("Access denied. Admin privileges required.", "error")
        return redirect(url_for("dashboard"))
    
    if request.method == 'POST':
        # Handle mentorship request submission
        mentor_name = request.form.get('mentor_name')
        topic = request.form.get('topic')
        description = request.form.get('description')
        
        # Add to mentorship requests (mock)
        flash('Mentorship request submitted successfully!', 'success')
        return redirect(url_for('careers_mentorship'))
    
    return render_template("careers_mentorship.html")

@app.route("/careers/saved")
@login_required
def careers_saved():
    if session.get("role") not in ["admin", "it", "hr"]:
        flash("Access denied. Admin privileges required.", "error")
        return redirect(url_for("dashboard"))
    
    return render_template("careers_saved.html")

@app.route("/careers/goals")
@login_required
def careers_goals():
    if session.get("role") not in ["admin", "it", "hr"]:
        flash("Access denied. Admin privileges required.", "error")
        return redirect(url_for("dashboard"))
    
    return render_template("careers_goals.html")

@app.route("/careers/badges")
@login_required
def careers_badges():
    if session.get("role") not in ["admin", "it", "hr"]:
        flash("Access denied. Admin privileges required.", "error")
        return redirect(url_for("dashboard"))
    
    return render_template("careers_badges.html")

@app.route("/careers/progress")
@login_required
def careers_progress():
    # Allow both employees and admins to view progress
    user_email = session.get("user")
    
    # Get user's progress data
    user_progress = {
        'courses_completed': 0,
        'total_courses': len(courses) if 'courses' in globals() else 0,
        'skills_assessed': 0,
        'badges_earned': 0,
        'goals_achieved': 0,
        'total_goals': len(career_goals) if 'career_goals' in globals() else 0,
        'learning_hours': 0,
        'certifications': 0
    }
    
    # Calculate course progress
    if 'user_progress' in globals() and user_email in user_progress:
        user_progress['courses_completed'] = len([c for c in user_progress[user_email].values() if c.get('completed', False)])
    
    # Calculate skills progress
    if 'skills_results' in globals() and user_email in skills_results:
        user_progress['skills_assessed'] = len(skills_results[user_email])
    
    # Calculate badges
    user = next((u for u in users if u['email'] == user_email), None) if 'users' in globals() else None
    if user and 'badges' in user:
        user_progress['badges_earned'] = len(user['badges'])
    
    # Calculate goals
    if 'user_goals' in globals() and user_email in user_goals:
        user_progress['goals_achieved'] = len([g for g in user_goals[user_email] if g.get('achieved', False)])
    
    return render_template("careers_progress.html", progress=user_progress)

@app.route("/employee/careers/progress")
@employee_login_required
def employee_careers_progress():
    # Employee-specific career progress
    user_email = session.get("user")
    
    # Get user's progress data
    user_progress = {
        'courses_completed': 0,
        'total_courses': len(courses) if 'courses' in globals() else 0,
        'skills_assessed': 0,
        'badges_earned': 0,
        'goals_achieved': 0,
        'total_goals': len(career_goals) if 'career_goals' in globals() else 0,
        'learning_hours': 0,
        'certifications': 0
    }
    
    # Calculate course progress
    if 'user_progress' in globals() and user_email in user_progress:
        user_progress['courses_completed'] = len([c for c in user_progress[user_email].values() if c.get('completed', False)])
    
    # Calculate skills progress
    if 'skills_results' in globals() and user_email in skills_results:
        user_progress['skills_assessed'] = len(skills_results[user_email])
    
    # Calculate badges
    user = next((u for u in users if u['email'] == user_email), None) if 'users' in globals() else None
    if user and 'badges' in user:
        user_progress['badges_earned'] = len(user['badges'])
    
    # Calculate goals
    if 'user_goals' in globals() and user_email in user_goals:
        user_progress['goals_achieved'] = len([g for g in user_goals[user_email] if g.get('achieved', False)])
    
    return render_template("careers_progress.html", progress=user_progress)

@app.route("/careers/resources")
@login_required
def careers_resources():
    if session.get("role") not in ["admin", "it", "hr"]:
        flash("Access denied. Admin privileges required.", "error")
        return redirect(url_for("dashboard"))
    
    return render_template("careers_resources.html")

@app.route("/careers/jobs")
@login_required
def careers_jobs():
    if session.get("role") not in ["admin", "it", "hr"]:
        flash("Access denied. Admin privileges required.", "error")
        return redirect(url_for("dashboard"))
    
    # Sample job data
    jobs = [
        {'id': 1, 'title': 'Senior Software Engineer', 'company': 'Tech Corp', 'location': 'Remote', 'type': 'Full-time', 'salary': '$120k-$150k'},
        {'id': 2, 'title': 'Product Manager', 'company': 'Innovation Inc', 'location': 'San Francisco', 'type': 'Full-time', 'salary': '$130k-$160k'},
        {'id': 3, 'title': 'Data Scientist', 'company': 'Analytics Co', 'location': 'New York', 'type': 'Full-time', 'salary': '$110k-$140k'},
        {'id': 4, 'title': 'UX Designer', 'company': 'Design Studio', 'location': 'Remote', 'type': 'Full-time', 'salary': '$90k-$120k'},
        {'id': 5, 'title': 'DevOps Engineer', 'company': 'Cloud Solutions', 'location': 'Austin', 'type': 'Full-time', 'salary': '$100k-$130k'}
    ]
    
    return render_template("careers_jobs.html", jobs=jobs)

@app.route("/careers/learning")
@login_required
def careers_learning():
    if session.get("role") not in ["admin", "it", "hr"]:
        flash("Access denied. Admin privileges required.", "error")
        return redirect(url_for("dashboard"))
    
    return render_template("careers_learning.html")

@app.route("/api/ai-assistant", methods=["POST"])
@login_required
def ai_assistant():
    q = request.get_json().get("question", "").lower()
    
    # Comprehensive IT support responses
    responses = {
        # Network & Connectivity
        "vpn": "Try disconnecting and reconnecting to VPN. If that doesn't work, restart your computer and try again.",
        "internet": "Check if your ethernet cable is connected or try reconnecting to WiFi. Restart your router if needed.",
        "wifi": "Try forgetting and reconnecting to the WiFi network. If issues persist, restart your router.",
        "network": "Check your network adapter settings and try restarting your computer.",
        
        # Email & Communication
        "email": "Try logging out and back into your email. Clear browser cache if using webmail.",
        "outlook": "Try restarting Outlook. If that doesn't work, repair your Outlook profile.",
        "teams": "Try signing out and back into Teams. Restart the application if needed.",
        
        # Password & Access
        "password": "Use the 'Forgot Password' link on the login page to reset your password.",
        "login": "Make sure you're using the correct email and password. Try the 'Forgot Password' option if needed.",
        "access": "Contact your manager or HR if you need access to specific systems or applications.",
        
        # Hardware Issues
        "printer": "Try restarting the printer and your computer. Check if the printer is connected to the network.",
        "keyboard": "Try unplugging and reconnecting your keyboard. If wireless, check the battery.",
        "mouse": "Try unplugging and reconnecting your mouse. If wireless, check the battery.",
        "monitor": "Check all cable connections. Try a different cable or port if available.",
        
        # Software Issues
        "software": "Try restarting the application. If that doesn't work, restart your computer.",
        "program": "Try closing and reopening the program. Check for updates if available.",
        "application": "Try restarting the application. Clear cache if it's a web application.",
        
        # System Issues
        "slow": "Try closing unnecessary programs and restarting your computer. Check available disk space.",
        "freeze": "Try Ctrl+Alt+Delete to open Task Manager and end unresponsive programs.",
        "crash": "Try restarting your computer. If the issue persists, contact IT support.",
        
        # General IT Support
        "help": "I can help with common IT issues. Try asking about specific problems like VPN, email, or printer issues.",
        "support": "For immediate assistance, submit a ticket through the Support section or contact IT directly.",
        "ticket": "You can submit a ticket through the 'Submit Ticket' option in the Support menu.",
        
        # Greetings
        "hello": "Hello! I'm your IT assistant. How can I help you today?",
        "hi": "Hi there! I'm here to help with IT issues. What can I assist you with?",
        "hey": "Hey! I'm your IT support assistant. What's the issue?",
        
        # Thank you
        "thank": "You're welcome! Let me know if you need anything else.",
        "thanks": "You're welcome! Feel free to ask if you have more questions."
    }
    
    # Check for exact matches first
    for key, response in responses.items():
        if key in q:
            return jsonify({"answer": response})
    
    # Check for partial matches with common IT terms
    it_keywords = {
        "computer": "Try restarting your computer first. This resolves most common issues.",
        "restart": "Restarting your computer often fixes many technical issues.",
        "update": "Check for system updates in Settings > Update & Security.",
        "virus": "Run a full virus scan using your antivirus software.",
        "backup": "Make sure your important files are backed up regularly.",
        "install": "Make sure you have administrator privileges when installing software.",
        "uninstall": "Use Control Panel > Programs and Features to properly uninstall software."
    }
    
    for keyword, response in it_keywords.items():
        if keyword in q:
            return jsonify({"answer": response})
    
    # Provide helpful default response
    return jsonify({
        "answer": "I'm not sure about that specific issue. For immediate help, please submit a ticket through the Support section or try asking about common issues like VPN, email, printer, or password problems."
    })

@app.route('/devices', methods=['GET', 'POST'])
@login_required
def device_list():
    if session.get('role') != 'admin':
        flash('Admin access required.', 'error')
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        new_device = {
            'id': len(devices) + 1,
            'name': request.form['name'],
            'type': request.form['type'],
            'assigned_to': '',
            'status': 'available',
            'lent_date': '',
            'return_date': '',
            'notes': request.form.get('notes', '')
        }
        devices.append(new_device)
        flash('Device added!', 'success')
        return redirect(url_for('device_list'))
    return render_template('devices.html', devices=devices)

@app.route('/devices/lend/<int:device_id>', methods=['POST'])
@login_required
def lend_device(device_id):
    if session.get('role') != 'admin':
        flash('Admin access required.', 'error')
        return redirect(url_for('dashboard'))
    device = next((d for d in devices if d['id'] == device_id), None)
    if device and device['status'] == 'available':
        device['assigned_to'] = request.form['assigned_to']
        device['status'] = 'lent'
        device['lent_date'] = request.form['lent_date']
        device['return_date'] = ''
        device['notes'] = request.form.get('notes', device['notes'])
        flash('Device lent out!', 'success')
    else:
        flash('Device not available.', 'error')
    return redirect(url_for('device_list'))

@app.route('/devices/return/<int:device_id>', methods=['POST'])
@login_required
def return_device(device_id):
    if session.get('role') != 'admin':
        flash('Admin access required.', 'error')
        return redirect(url_for('dashboard'))
    device = next((d for d in devices if d['id'] == device_id), None)
    if device and device['status'] == 'lent':
        device['status'] = 'available'
        device['return_date'] = request.form['return_date']
        device['assigned_to'] = ''
        flash('Device marked as returned!', 'success')
    else:
        flash('Device not currently lent.', 'error')
    return redirect(url_for('device_list'))

# Employee Portal Routes (mounted at /employee)
@app.route('/employee/')
@login_required
def employee_home():
    return redirect(url_for('employee_dashboard'))

@app.route('/employee/login', methods=['GET', 'POST'])
def employee_login():
    # If already logged in, redirect to employee dashboard
    if 'user' in session:
        return redirect(url_for('employee_dashboard'))
    
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        try:
            # Get user from database
            user = db_helper.get_user_by_email(email)
            
            if user:
                # Hash the input password for comparison
                hashed_password = hashlib.sha256(password.encode()).hexdigest()
                
                if user['password'] == hashed_password:
                    session['user'] = email
                    session['role'] = user['role']
                    print(f"DEBUG: Session set - user: {email}, role: {user['role']}")
                    
                    if user['role'] in ['admin', 'it', 'hr']:
                        flash('Welcome to Admin Portal!', 'success')
                        return redirect(url_for('admin_dashboard'))
                    elif user['role'] == 'employee':
                        flash('Welcome to Employee Portal!', 'success')
                        return redirect(url_for('employee_dashboard'))
                    else:
                        return redirect(url_for('dashboard'))
                else:
                    flash('Invalid credentials. Please try again.', 'error')
            else:
                flash('Invalid credentials. Please try again.', 'error')
        except Exception as e:
            print(f"Database error during employee login: {e}")
            flash('Login error. Please try again.', 'error')
    
    return render_template('employee_portal/login.html')

@app.route('/employee/dashboard')
@employee_login_required
def employee_dashboard():
    if 'user' not in session:
        return redirect(url_for('employee_login'))
    
    # Mock data for employee dashboard
    pto_balance = 15
    recent_paystubs = [
        {'id': 1, 'period': 'January 2024', 'amount': 4500},
        {'id': 2, 'period': 'December 2023', 'amount': 4500}
    ]
    benefits_status = 'Active'
    open_tickets = 2
    
    return render_template('employee_portal/dashboard.html', 
                         pto_balance=pto_balance,
                         recent_paystubs=recent_paystubs,
                         benefits_status=benefits_status,
                         open_tickets=open_tickets)

@app.route('/employee/logout')
@login_required
def employee_logout():
    session.pop('user', None)
    session.pop('role', None)
    flash('Logged out successfully', 'success')
    return redirect(url_for('employee_login'))

@app.route('/employee/timeoff', methods=['GET', 'POST'])
@login_required
def employee_timeoff():
    if 'user' not in session:
        return redirect(url_for('employee_login'))
    
    if request.method == 'POST':
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        reason = request.form['reason']
        
        # Add to database
        request_id = db_helper.create_timeoff_request(session['user'], start_date, end_date, reason)
        
        if request_id:
            # Add notification for admin
            db_helper.create_notification("admin@example.com", f"New time off request from {session['user']}: {start_date} to {end_date}", "warning")
            flash('Time off request submitted successfully!', 'success')
        else:
            flash('Error submitting time off request. Please try again.', 'error')
        
        return redirect(url_for('employee_timeoff'))
    
    return render_template('employee_portal/timeoff.html')

@app.route('/employee/paystubs')
@login_required
def employee_paystubs():
    if 'user' not in session:
        return redirect(url_for('employee_login'))
    
    # Filter paystubs for current user
    user_paystubs = [p for p in paystubs if p['employee_id'] == session['user']]
    
    return render_template('employee_portal/paystubs.html', paystubs=user_paystubs)

@app.route('/employee/benefits')
@login_required
def employee_benefits():
    if 'user' not in session:
        return redirect(url_for('employee_login'))
    
    return render_template('employee_portal/benefits.html', benefits=benefits)

@app.route('/employee/profile', methods=['GET', 'POST'])
@login_required
def employee_profile():
    if 'user' not in session:
        return redirect(url_for('employee_login'))
    
    user_id = session['user']  # session['user'] is the email string
    
    if request.method == 'POST':
        # Handle profile picture upload
        if 'profile_picture' in request.files:
            file = request.files['profile_picture']
            if file and file.filename:
                # Save profile picture
                filename = f"profile_{user_id}_{int(time.time())}.jpg"
                filepath = os.path.join('static', 'uploads', 'profiles', filename)
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                file.save(filepath)
                
                if user_id not in user_profiles:
                    user_profiles[user_id] = {}
                user_profiles[user_id]['profile_picture'] = f"uploads/profiles/{filename}"
                flash('Profile picture updated successfully!', 'success')
        
        # Update profile information
        if user_id not in user_profiles:
            user_profiles[user_id] = {}
        
        user_profiles[user_id].update({
            'phone': request.form.get('phone', ''),
            'address': request.form.get('address', ''),
            'emergency_contact': request.form.get('emergency_contact', ''),
            'emergency_phone': request.form.get('emergency_phone', ''),
            'skills': request.form.get('skills', ''),
            'interests': request.form.get('interests', ''),
            'bio': request.form.get('bio', ''),
            'linkedin': request.form.get('linkedin', ''),
            'github': request.form.get('github', ''),
            'website': request.form.get('website', ''),
            'department': request.form.get('department', ''),
            'position': request.form.get('position', ''),
            'hire_date': request.form.get('hire_date', ''),
            'manager': request.form.get('manager', ''),
            'work_location': request.form.get('work_location', ''),
            'employment_type': request.form.get('employment_type', ''),
            'salary_band': request.form.get('salary_band', ''),
            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('employee_profile'))
    
    # Get user profile data
    profile_data = user_profiles.get(user_id, {})
    
    return render_template('employee_portal/profile.html', 
                         user=session['user'],
                         profile=profile_data)

@app.route('/employee/help', methods=['GET', 'POST'])
@login_required
def employee_help():
    if 'user' not in session:
        return redirect(url_for('employee_login'))
    
    if request.method == 'POST':
        subject = request.form['subject']
        description = request.form['description']
        
        # Add to tickets (mock)
        flash('Support ticket submitted successfully!', 'success')
        return redirect(url_for('employee_help'))
    
    tickets = [
        {'id': 1, 'subject': 'VPN Access Issue', 'status': 'Open', 'created': '2024-01-15'},
        {'id': 2, 'subject': 'Software License Request', 'status': 'In Progress', 'created': '2024-01-10'}
    ]
    
    return render_template('employee_portal/help.html', tickets=tickets)

@app.route('/employee/careers')
@employee_login_required
def employee_careers():
    if 'user' not in session:
        return redirect(url_for('employee_login'))
    
    # Get user's applications and assessments
    user_applications = db_helper.get_user_internal_applications(session['user'])
    user_assessments = db_helper.get_user_skills_assessments(session['user'])
    latest_assessment = db_helper.get_latest_skills_assessment(session['user'])
    
    # Process assessment data for roadmap
    assessment_result = None
    progress = None
    assessment_date = None
    
    if latest_assessment:
        # Parse the assessment data
        answers = json.loads(latest_assessment['answers']) if isinstance(latest_assessment['answers'], str) else latest_assessment['answers']
        
        # Calculate skill level based on score
        percentage = (latest_assessment['score'] / latest_assessment['total_questions']) * 100
        if percentage >= 90:
            skill_level = "Expert"
        elif percentage >= 70:
            skill_level = "Advanced"
        elif percentage >= 50:
            skill_level = "Intermediate"
        else:
            skill_level = "Beginner"
        
        # Determine strengths and improvement areas based on score (mock logic)
        if percentage >= 80:
            strengths = ["Programming Fundamentals", "Problem Solving", "Technical Knowledge"]
            improvement_areas = ["Advanced Concepts", "Specialized Skills"]
        elif percentage >= 60:
            strengths = ["Basic Programming", "Logical Thinking"]
            improvement_areas = ["Advanced Programming", "Web Technologies", "Database Concepts"]
        else:
            strengths = ["Learning Potential"]
            improvement_areas = ["Programming Fundamentals", "Basic Computer Science", "Web Development"]
        
        # Create learning roadmap data (mock data for courses)
        assessment_result = {
            'score': latest_assessment['score'],
            'total_questions': latest_assessment['total_questions'],
            'percentage': percentage,
            'skill_level': skill_level,
            'strengths': strengths,
            'improvement_areas': improvement_areas,
            'phase1_duration': 4,
            'phase2_duration': 6,
            'phase3_duration': 8,
            'phase1_courses': [
                {
                    'title': 'Programming Fundamentals',
                    'description': 'Learn core programming concepts and best practices',
                    'duration': '4 weeks',
                    'provider': 'Coursera',
                    'url': '#'
                },
                {
                    'title': 'Web Development Basics',
                    'description': 'Master HTML, CSS, and JavaScript fundamentals',
                    'duration': '6 weeks',
                    'provider': 'Udemy',
                    'url': '#'
                }
            ],
            'phase2_courses': [
                {
                    'title': 'Advanced JavaScript',
                    'description': 'Deep dive into modern JavaScript features',
                    'duration': '8 weeks',
                    'provider': 'LinkedIn Learning',
                    'url': '#'
                },
                {
                    'title': 'Database Design',
                    'description': 'Learn SQL and database management',
                    'duration': '6 weeks',
                    'provider': 'edX',
                    'url': '#'
                }
            ],
            'phase3_courses': [
                {
                    'title': 'Full-Stack Development',
                    'description': 'Build complete web applications',
                    'duration': '12 weeks',
                    'provider': 'Coursera',
                    'url': '#'
                },
                {
                    'title': 'Cloud Computing',
                    'description': 'Master AWS, Azure, or Google Cloud',
                    'duration': '10 weeks',
                    'provider': 'AWS Training',
                    'url': '#'
                }
            ]
        }
        
        # Mock progress data
        progress = {
            'completed_courses': 3,
            'total_hours': 24,
            'certificates_earned': 2,
            'overall_percentage': 35
        }
        
        assessment_date = latest_assessment['completed_at'].strftime('%B %d, %Y') if latest_assessment['completed_at'] else None
    
    return render_template('employee_portal/careers_minimal.html', 
                         applications=user_applications,
                         assessments=user_assessments,
                         latest_assessment=latest_assessment,
                         assessment_result=assessment_result,
                         progress=progress,
                         assessment_date=assessment_date)

@app.route('/employee/leave', methods=['GET', 'POST'])
@login_required
def employee_leave():
    if 'user' not in session:
        return redirect(url_for('employee_login'))
    
    user_id = session['user']
    
    if request.method == 'POST':
        leave_type = request.form.get('leave_type')
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        reason = request.form.get('reason')
        
        if leave_type and start_date and end_date and reason:
            # Save to database
            leave_id = db_helper.create_leave_request(
                user_id, 
                session['user'], 
                leave_type, 
                start_date, 
                end_date, 
                reason
            )
            
            if leave_id:
                # Add notification for admin
                db_helper.create_notification("admin@example.com", f"New leave request from {session['user']}: {leave_type} from {start_date} to {end_date}", "warning")
                flash('Leave request submitted successfully!', 'success')
            else:
                flash('Error submitting leave request. Please try again.', 'error')
            
            return redirect(url_for('employee_leave'))
    
    # Get employee's leave requests from database
    employee_leaves = db_helper.get_leave_requests_by_employee(user_id)
    
    return render_template('employee_portal/leave.html', 
                         leave_requests=employee_leaves,
                         leave_types=leave_types,
                         user=session['user'])

@app.route('/employee/leave/<int:leave_id>')
@login_required
def view_leave_request(leave_id):
    if 'user' not in session:
        return redirect(url_for('employee_login'))
    
    user_id = session['user']
    leave_request = next((l for l in leave_requests if l['id'] == leave_id and l['employee_id'] == user_id), None)
    
    if not leave_request:
        flash('Leave request not found!', 'error')
        return redirect(url_for('employee_leave'))
    
    return render_template('employee_portal/leave_detail.html', leave_request=leave_request)

@app.route('/employee/leave/<int:leave_id>/cancel', methods=['POST'])
@login_required
def cancel_leave_request(leave_id):
    if 'user' not in session:
        return redirect(url_for('employee_login'))
    
    user_id = session['user']
    leave_request = next((l for l in leave_requests if l['id'] == leave_id and l['employee_id'] == user_id), None)
    
    if leave_request and leave_request['status'] == 'pending':
        leave_request['status'] = 'cancelled'
        flash('Leave request cancelled successfully!', 'success')
    else:
        flash('Cannot cancel this leave request!', 'error')
    
    return redirect(url_for('employee_leave'))

@app.route('/employee/timesheet', methods=['GET', 'POST'])
@login_required
def employee_timesheet():
    if 'user' not in session:
        return redirect(url_for('employee_login'))
    
    if request.method == 'POST':
        date = request.form.get('date')
        hours_worked = float(request.form.get('hours_worked', 0))
        project = request.form.get('project')
        task_description = request.form.get('task_description')
        
        if date and hours_worked > 0:
            # Save to database
            timesheet_id = db_helper.create_timesheet(
                session['user'], 
                session['user'], 
                date, 
                hours_worked, 
                project, 
                task_description
            )
            
            if timesheet_id:
                # Add notification for admin
                db_helper.create_notification("admin@example.com", f"New timesheet submitted by {session['user']} for {date}", "warning")
                flash('Timesheet submitted successfully!', 'success')
            else:
                flash('Error submitting timesheet. Please try again.', 'error')
            
            return redirect(url_for('employee_timesheet'))
    
    # Get employee's timesheets from database
    employee_timesheets = db_helper.get_timesheets_by_employee(session['user'])
    return render_template('employee_portal/timesheet.html', timesheets=employee_timesheets)

# Anonymous Feedback Data Structure
anonymous_feedback = [
    {
        'id': 1,
        'type': 'Work Environment',
        'text': 'The new office layout is great and promotes collaboration.',
        'department': 'Engineering',
        'priority': 4,
        'status': 'pending',
        'submitted_at': '2024-01-30 10:30:00',
        'anonymous': True,
        'category': 'Work Environment',
        'sentiment': 'positive',
        'comment': 'The new office layout is great and promotes collaboration. The open spaces make it easier to work together.'
    },
    {
        'id': 2,
        'type': 'Training',
        'text': 'Would like more technical training opportunities.',
        'department': 'Marketing',
        'priority': 3,
        'status': 'pending',
        'submitted_at': '2024-01-29 14:20:00',
        'anonymous': True,
        'category': 'Training & Development',
        'sentiment': 'neutral',
        'comment': 'Would like more technical training opportunities, especially for new tools and technologies.'
    },
    {
        'id': 3,
        'type': 'Communication',
        'text': 'Team meetings could be more efficient.',
        'department': 'Sales',
        'priority': 2,
        'status': 'pending',
        'submitted_at': '2024-01-28 16:45:00',
        'anonymous': True,
        'category': 'Communication',
        'sentiment': 'negative',
        'comment': 'Team meetings could be more efficient. Sometimes they run too long without clear agendas.'
    }
]

@app.route('/employee/feedback', methods=['GET', 'POST'])
@login_required
def employee_feedback():
    if 'user' not in session:
        return redirect(url_for('employee_login'))
    
    if request.method == 'POST':
        feedback_type = request.form.get('feedback_type')
        feedback_text = request.form.get('feedback_text')
        department = request.form.get('department')
        priority = request.form.get('priority')
        
        if feedback_text.strip():
            # Add to database
            feedback_id = db_helper.create_feedback(feedback_type, feedback_text, department, priority)
            
            if feedback_id:
                # Add notification for admin
                db_helper.create_notification("admin@example.com", f"New anonymous feedback submitted: {feedback_type} - {feedback_text[:50]}...", "info")
                flash('Anonymous feedback submitted successfully!', 'success')
            else:
                flash('Error submitting feedback. Please try again.', 'error')
            
            return redirect(url_for('employee_feedback'))
    
    return render_template('employee_portal/feedback.html')

@app.route('/admin/feedback')
@admin_required
def admin_feedback():
    if 'user' not in session or session.get('role') != 'admin':
        flash("Access denied. Admin privileges required.", "error")
        return redirect(url_for("dashboard"))
    
    # Get feedback from database
    feedback_list = db_helper.get_all_feedback()
    
    return render_template('admin_feedback.html', feedback_list=feedback_list)

@app.route('/admin/feedback/update-status/<int:feedback_id>', methods=['POST'])
@login_required
def update_feedback_status(feedback_id):
    if 'user' not in session or session.get('role') != 'admin':
        flash("Access denied. Admin privileges required.", "error")
        return redirect(url_for("dashboard"))
    
    new_status = request.form.get('status')
    
    # Update in database
    if db_helper.update_feedback_status(feedback_id, new_status):
        flash(f'Feedback status updated to {new_status}', 'success')
    else:
        flash('Error updating feedback status', 'error')
    
    return redirect(url_for('admin_feedback'))

@app.route("/admin/delete-feedback/<int:feedback_id>", methods=["POST"])
@login_required
def delete_feedback(feedback_id):
    if "user" not in session or session.get("role") != "admin":
        flash("Access denied. Admin privileges required.", "error")
        return redirect(url_for("dashboard"))
    
    if db_helper.delete_feedback(feedback_id):
        flash("Feedback deleted successfully!", "success")
    else:
        flash("Error deleting feedback", "error")
    
    return redirect(url_for("admin_feedback"))

@app.route("/admin/add-feedback-comment/<int:feedback_id>", methods=["POST"])
@login_required
def add_feedback_comment(feedback_id):
    if "user" not in session or session.get("role") != "admin":
        flash("Access denied. Admin privileges required.", "error")
        return redirect(url_for("dashboard"))
    
    comment = request.form.get("comment")
    if comment:
        if db_helper.add_feedback_comment(feedback_id, comment, session["user"]):
            flash("Comment added successfully!", "success")
        else:
            flash("Error adding comment", "error")
    
    return redirect(url_for("admin_feedback"))

@app.route('/employee/complimentary')
@login_required
def employee_complimentary():
    if 'user' not in session:
        return redirect(url_for('employee_login'))
    return render_template('employee_portal/complimentary.html')

# AI Integration Routes

@app.route("/ai/ats", methods=["GET", "POST"])
@login_required
def ats_interface():
    if session.get("role") not in ["admin", "it", "hr"]:
        flash("Access denied. Admin privileges required.", "error")
        return redirect(url_for("dashboard"))
    
    if request.method == "POST":
        job_description = request.form.get("job_description")
        threshold = float(request.form.get("threshold", 75))
        uploaded_files = request.files.getlist("resumes_folder")

        if len(uploaded_files) < 3:
            flash("At least 3 resume files are required.", "error")
            return render_template("ats_interface.html")

        valid_resumes, invalid_resumes = [], []

        temp_dir = "temp_uploads"
        os.makedirs(temp_dir, exist_ok=True)

        for uploaded_file in uploaded_files:
            pdf_path = os.path.join(temp_dir, uploaded_file.filename)
            uploaded_file.save(pdf_path)

            extracted = extract_resume_text(pdf_path)
            if extracted:
                valid_resumes.append((uploaded_file.filename, extracted))
            else:
                invalid_resumes.append(uploaded_file.filename)

        if len(valid_resumes) < 3:
            flash("Not enough valid resumes after filtering.", "error")
            return render_template("ats_interface.html")

        valid_files, extracted_texts = zip(*valid_resumes)
        sbert_scores = [compute_sbert_similarity(r, job_description) for r in extracted_texts]
        tfidf_scores = compute_tfidf_similarity(list(extracted_texts), job_description)
        final_scores = [(0.2 * tfidf + 0.8 * sbert) for tfidf, sbert in zip(tfidf_scores, sbert_scores)]

        results = []
        for i, file in enumerate(valid_files):
            results.append({
                "Filename": file,
                "TF-IDF Score (%)": float(tfidf_scores[i]),
                "SBERT Score (%)": float(sbert_scores[i]),
                "Final Match Score (%)": round(float(final_scores[i]), 2),
                "Label": "Selected" if final_scores[i] >= threshold else "Rejected"
            })

        for file in invalid_resumes:
            results.append({
                "Filename": file,
                "TF-IDF Score (%)": "N/A",
                "SBERT Score (%)": "N/A",
                "Final Match Score (%)": "N/A",
                "Label": "Invalid_Resume"
            })

        return render_template("ats_interface.html", results=results, job_description=job_description, threshold=threshold)
    
    return render_template("ats_interface.html")

@app.route("/ai/rag", methods=["GET", "POST"])
@login_required
def rag_interface():
    if session.get("role") not in ["admin", "it", "hr"]:
        flash("Access denied. Admin privileges required.", "error")
        return redirect(url_for("dashboard"))
    
    if request.method == "POST":
        question = request.form.get("question", "").strip().lower()
        
        if not rag_initialized:
            return render_template("rag_interface.html", answer="RAG system not initialized. Please check Azure credentials.")
        
        # Handle greetings
        if question in ["hi", "hello", "hey", "how are you", "good morning", "good evening", "good afternoon"]:
            answer = random.choice([
                "Hi there! 😊 How can I help with Enplify.ai today?",
                "Hello! Ask me anything about Enplify.ai.",
                "Hey 👋 Ready to answer your Enplify.ai questions."
            ])
            return render_template("rag_interface.html", answer=answer, question=question)

        # Handle thank you
        if question in ["thank you", "thanks", "thank u", "thx", "ty"]:
            answer = random.choice([
                "You're welcome! 😊",
                "Happy to help!",
                "Anytime! Let me know if you have more questions."
            ])
            return render_template("rag_interface.html", answer=answer, question=question)

        # Run through RAG chain
        try:
            result = qa_chain({"question": question, "chat_history": chat_history})
            answer = result["answer"].strip()

            # Fallback if no useful info found
            if answer.lower() in ["i don't know.", "i don't know"]:
                answer = "I'm trained only to answer Enplify.ai-related questions 😊"

            chat_history.append((question, answer))
            return render_template("rag_interface.html", answer=answer, question=question)
        except Exception as e:
            return render_template("rag_interface.html", answer=f"Error: {str(e)}", question=question)
    
    return render_template("rag_interface.html")

@app.route("/api/process_resumes", methods=["POST"])
@login_required
def process_resumes_api():
    if "user" not in session:
        return jsonify({"error": "Authentication required"}), 401
    
    job_description = request.form.get("job_description")
    threshold = float(request.form.get("threshold", 75))
    uploaded_files = request.files.getlist("resumes_folder")

    if len(uploaded_files) < 3:
        return jsonify({"error": "At least 3 resume files are required."}), 400

    valid_resumes, invalid_resumes = [], []

    temp_dir = "temp_uploads"
    os.makedirs(temp_dir, exist_ok=True)

    for uploaded_file in uploaded_files:
        pdf_path = os.path.join(temp_dir, uploaded_file.filename)
        uploaded_file.save(pdf_path)

        extracted = extract_resume_text(pdf_path)
        if extracted:
            valid_resumes.append((uploaded_file.filename, extracted))
        else:
            invalid_resumes.append(uploaded_file.filename)

    if len(valid_resumes) < 3:
        return jsonify({"error": "Not enough valid resumes after filtering."}), 400

    valid_files, extracted_texts = zip(*valid_resumes)
    sbert_scores = [compute_sbert_similarity(r, job_description) for r in extracted_texts]
    tfidf_scores = compute_tfidf_similarity(list(extracted_texts), job_description)
    final_scores = [(0.2 * tfidf + 0.8 * sbert) for tfidf, sbert in zip(tfidf_scores, sbert_scores)]

    results = []
    for i, file in enumerate(valid_files):
        results.append({
            "Filename": file,
            "TF-IDF Score (%)": float(tfidf_scores[i]),
            "SBERT Score (%)": float(sbert_scores[i]),
            "Final Match Score (%)": round(float(final_scores[i]), 2),
            "Label": "Selected" if final_scores[i] >= threshold else "Rejected"
        })

    for file in invalid_resumes:
        results.append({
            "Filename": file,
            "TF-IDF Score (%)": "N/A",
            "SBERT Score (%)": "N/A",
            "Final Match Score (%)": "N/A",
            "Label": "Invalid_Resume"
        })

    return jsonify(results), 200

@app.route("/api/rag_ask", methods=["POST"])
@login_required
def rag_ask_api():
    if "user" not in session:
        return jsonify({"error": "Authentication required"}), 401
    
    if not rag_initialized:
        return jsonify({"answer": "RAG system not initialized. Please check Azure credentials."})
    
    data = request.get_json()
    question = data.get("question", "").strip().lower()

    # Handle greetings
    if question in ["hi", "hello", "hey", "how are you", "good morning", "good evening", "good afternoon"]:
        return jsonify({"answer": random.choice([
            "Hi there! 😊 How can I help with Enplify.ai today?",
            "Hello! Ask me anything about Enplify.ai.",
            "Hey 👋 Ready to answer your Enplify.ai questions."
        ])})

    # Handle thank you
    if question in ["thank you", "thanks", "thank u", "thx", "ty"]:
        return jsonify({"answer": random.choice([
            "You're welcome! 😊",
            "Happy to help!",
            "Anytime! Let me know if you have more questions."
        ])})

    # Run through RAG chain
    try:
        result = qa_chain({"question": question, "chat_history": chat_history})
        answer = result["answer"].strip()

        # Fallback if no useful info found
        if answer.lower() in ["i don't know.", "i don't know"]:
            answer = "I'm trained only to answer Enplify.ai-related questions 😊"

        chat_history.append((question, answer))
        return jsonify({"answer": answer})
    except Exception as e:
        return jsonify({"answer": f"Error: {str(e)}"})

# Learning and Development Data Structures
courses = [
    {
        'id': 1,
        'title': 'Python Programming Fundamentals',
        'description': 'Learn the basics of Python programming language',
        'duration': '8 hours',
        'difficulty': 'Beginner',
        'category': 'Technology',
        'questions': [
            {
                'id': 1,
                'question': 'What is the correct way to create a function in Python?',
                'options': [
                    'def myFunction():',
                    'function myFunction():',
                    'create myFunction():',
                    'func myFunction():'
                ],
                'correct_answer': 0,
                'explanation': 'In Python, functions are defined using the "def" keyword.'
            },
            {
                'id': 2,
                'question': 'Which of the following is a mutable data type in Python?',
                'options': [
                    'tuple',
                    'string',
                    'list',
                    'int'
                ],
                'correct_answer': 2,
                'explanation': 'Lists are mutable in Python, meaning they can be modified after creation.'
            },
            {
                'id': 3,
                'question': 'What does the "self" parameter represent in a class method?',
                'options': [
                    'The class itself',
                    'The instance of the class',
                    'A reserved keyword',
                    'The method name'
                ],
                'correct_answer': 1,
                'explanation': 'The "self" parameter refers to the instance of the class.'
            }
        ],
        'badge': 'Python Beginner',
        'passing_score': 70
    },
    {
        'id': 2,
        'title': 'Leadership Skills',
        'description': 'Develop essential leadership and management skills',
        'duration': '6 hours',
        'difficulty': 'Intermediate',
        'category': 'Leadership',
        'questions': [
            {
                'id': 1,
                'question': 'What is the primary role of a leader?',
                'options': [
                    'To give orders',
                    'To inspire and guide others',
                    'To control everything',
                    'To delegate all tasks'
                ],
                'correct_answer': 1,
                'explanation': 'A leader\'s primary role is to inspire and guide others toward a common goal.'
            },
            {
                'id': 2,
                'question': 'Which leadership style focuses on involving team members in decision-making?',
                'options': [
                    'Autocratic',
                    'Democratic',
                    'Laissez-faire',
                    'Transactional'
                ],
                'correct_answer': 1,
                'explanation': 'Democratic leadership involves team members in the decision-making process.'
            }
        ],
        'badge': 'Leadership Essentials',
        'passing_score': 75
    },
    {
        'id': 3,
        'title': 'Data Analytics Basics',
        'description': 'Introduction to data analysis and visualization',
        'duration': '10 hours',
        'difficulty': 'Intermediate',
        'category': 'Data Science',
        'questions': [
            {
                'id': 1,
                'question': 'What is the primary purpose of data visualization?',
                'options': [
                    'To make data look pretty',
                    'To communicate insights clearly',
                    'To hide data complexity',
                    'To reduce data size'
                ],
                'correct_answer': 1,
                'explanation': 'Data visualization helps communicate insights clearly and effectively.'
            }
        ],
        'badge': 'Data Analyst',
        'passing_score': 80
    }
]

# User Progress Data
user_progress = [
    {
        'user_id': 1,
        'course_id': 1,
        'progress': 75,
        'completed': False,
        'last_accessed': '2024-01-15'
    },
    {
        'user_id': 2,
        'course_id': 1,
        'progress': 100,
        'completed': True,
        'last_accessed': '2024-01-20'
    }
]

# User Badges Data
user_badges = [
    {
        'user_id': 1,
        'badge_id': 1,
        'earned_date': '2024-01-10',
        'badge_name': 'Python Expert'
    },
    {
        'user_id': 2,
        'badge_id': 2,
        'earned_date': '2024-01-15',
        'badge_name': 'Team Player'
    }
]

# Users Data
users = [
    {
        'id': 1,
        'name': 'John Doe',
        'email': 'john.doe@example.com',
        'department': 'IT',
        'position': 'Software Engineer',
        'phone': '+1-555-0123',
        'hire_date': '2023-01-15',
        'manager': 'Jane Smith',
        'profile_picture': 'images/default-avatar.png'
    },
    {
        'id': 2,
        'name': 'Jane Smith',
        'email': 'jane.smith@example.com',
        'department': 'HR',
        'position': 'HR Manager',
        'phone': '+1-555-0124',
        'hire_date': '2022-06-01',
        'manager': 'Bob Johnson',
        'profile_picture': 'images/default-avatar.png'
    },
    {
        'id': 3,
        'name': 'Bob Johnson',
        'email': 'bob.johnson@example.com',
        'department': 'Management',
        'position': 'CTO',
        'phone': '+1-555-0125',
        'hire_date': '2021-03-15',
        'manager': '',
        'profile_picture': 'images/default-avatar.png'
    }
]

user_progress = {}  # Store user progress and completed courses
user_badges = {}    # Store user badges

@app.route('/employee/careers/learning', methods=['GET', 'POST'])
@employee_login_required
def employee_learning():
    if 'user' not in session:
        return redirect(url_for('employee_login'))
    
    user_email = session['user']
    
    # Use mock courses data
    available_courses = courses
    
    # Get user's quiz results
    user_quiz_results = db_helper.get_user_quiz_results(user_email)
    
    # Create a progress dictionary from quiz results
    user_progress = {}
    user_badges = []
    
    for result in user_quiz_results:
        course_id = result['course_id']
        user_progress[course_id] = {
            'completed': result['passed'],
            'score': result['percentage'],
            'completed_at': result['completed_at'].strftime('%Y-%m-%d %H:%M:%S') if result['completed_at'] else None
        }
        
        # Add badge if passed
        if result['passed']:
            course = next((c for c in courses if c['id'] == course_id), None)
            if course and course.get('badge') and course['badge'] not in user_badges:
                user_badges.append(course['badge'])
    
    return render_template('employee_portal/learning.html', 
                         courses=available_courses, 
                         user_progress=user_progress,
                         user_badges=user_badges)

@app.route('/employee/careers/learning/course/<int:course_id>')
@employee_login_required
def take_course(course_id):
    if 'user' not in session:
        return redirect(url_for('employee_login'))
    
    # Get course from mock data
    course = next((c for c in courses if c['id'] == course_id), None)
    if not course:
        flash('Course not found!', 'error')
        return redirect(url_for('employee_learning'))
    
    return render_template('employee_portal/course_quiz.html', course=course)

@app.route('/employee/careers/learning/course/<int:course_id>/quiz')
@employee_login_required
def course_quiz(course_id):
    if 'user' not in session:
        return redirect(url_for('employee_login'))
    
    # Get course from mock data
    course = next((c for c in courses if c['id'] == course_id), None)
    if not course:
        flash('Course not found!', 'error')
        return redirect(url_for('employee_learning'))
    
    return render_template('employee_portal/course_quiz.html', course=course)

@app.route('/admin/learning')
@login_required
def admin_learning():
    if 'user' not in session or session.get('role') != 'admin':
        flash("Access denied. Admin privileges required.", "error")
        return redirect(url_for("dashboard"))
    
    # Calculate learning statistics
    total_users = len(users) if 'users' in globals() else 0
    total_courses = len(courses)
    total_badges = len(set([badge for course in courses for badge in course.get('badges', [])]))
    
    # Calculate completion statistics
    completed_courses = sum(1 for user_id, progress in user_progress.items() 
                          for course_id, data in progress.items() 
                          if data.get('completed', False))
    
    # Get top performing users
    user_performance = []
    for user_id, progress in user_progress.items():
        user = next((u for u in users if u['id'] == user_id), None) if 'users' in globals() else None
        if user:
            completed_count = sum(1 for data in progress.values() if data.get('completed', False))
            avg_score = sum(data.get('score', 0) for data in progress.values()) / len(progress) if progress else 0
            badge_count = len(user_badges.get(user_id, []))
            
            user_performance.append({
                'user': user,
                'completed_courses': completed_count,
                'avg_score': avg_score,
                'badge_count': badge_count,
                'total_courses': len(progress)
            })
    
    # Sort by completion rate
    user_performance.sort(key=lambda x: x['completed_courses'], reverse=True)
    
    # Get course statistics
    course_stats = []
    for course in courses:
        enrolled_count = sum(1 for user_id, progress in user_progress.items() 
                           if course['id'] in progress)
        completed_count = sum(1 for user_id, progress in user_progress.items() 
                           if course['id'] in progress and progress[course['id']].get('completed', False))
        avg_score = sum(progress[course['id']].get('score', 0) 
                       for user_id, progress in user_progress.items() 
                       if course['id'] in progress) / enrolled_count if enrolled_count > 0 else 0
        
        course_stats.append({
            'course': course,
            'enrolled_count': enrolled_count,
            'completed_count': completed_count,
            'completion_rate': (completed_count / enrolled_count * 100) if enrolled_count > 0 else 0,
            'avg_score': avg_score
        })
    
    return render_template('admin_learning.html', 
                         user_performance=user_performance[:10],  # Top 10 users
                         course_stats=course_stats,
                         total_users=total_users,
                         total_courses=total_courses,
                         total_badges=total_badges,
                         completed_courses=completed_courses,
                         user_progress=user_progress,
                         user_badges=user_badges)

@app.route('/admin/learning/add', methods=['GET', 'POST'])
@login_required
def admin_add_course():
    if "user" not in session or session.get('role') != 'admin':
        flash("Access denied. Admin privileges required.", "error")
        return redirect(url_for("dashboard"))
    
    if request.method == 'POST':
        title = request.form.get('title')
        category = request.form.get('category')
        instructor = request.form.get('instructor')
        duration = request.form.get('duration')
        difficulty = request.form.get('difficulty')
        badge = request.form.get('badge')
        description = request.form.get('description')
        objectives = request.form.get('objectives')
        prerequisites = request.form.get('prerequisites')
        status = request.form.get('status', 'Draft')
        max_participants = request.form.get('max_participants')
        
        if title and category and instructor:
            course_id = len(courses) + 1
            new_course = {
                'id': course_id,
                'title': title,
                'category': category,
                'instructor': instructor,
                'duration': int(duration) if duration else 0,
                'difficulty': difficulty,
                'badge': badge,
                'description': description,
                'objectives': objectives,
                'prerequisites': prerequisites,
                'status': status,
                'max_participants': int(max_participants) if max_participants else None,
                'enrolled_count': 0,
                'completion_rate': 0,
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            courses.append(new_course)
            flash('Course created successfully!', 'success')
            return redirect(url_for('admin_learning'))
        else:
            flash('Please fill in all required fields.', 'error')
    
    return render_template("admin_add_course.html")

@app.route('/admin/learning/user/<int:user_id>')
@login_required
def admin_user_learning_detail(user_id):
    if 'user' not in session or session.get('role') != 'admin':
        flash("Access denied. Admin privileges required.", "error")
        return redirect(url_for("dashboard"))
    
    user = next((u for u in users if u['id'] == user_id), None) if 'users' in globals() else None
    if not user:
        flash('User not found!', 'error')
        return redirect(url_for('admin_learning'))
    
    # Get user's learning progress
    user_courses = user_progress.get(user_id, {})
    user_badges_earned = user_badges.get(user_id, [])
    
    # Calculate user statistics
    completed_courses = sum(1 for data in user_courses.values() if data.get('completed', False))
    total_enrolled = len(user_courses)
    avg_score = sum(data.get('score', 0) for data in user_courses.values()) / len(user_courses) if user_courses else 0
    
    # Get detailed course progress
    course_details = []
    for course in courses:
        progress = user_courses.get(course['id'], {})
        course_details.append({
            'course': course,
            'enrolled': course['id'] in user_courses,
            'completed': progress.get('completed', False),
            'score': progress.get('score', 0),
            'last_attempt': progress.get('last_attempt'),
            'attempts': progress.get('attempts', 0)
        })
    
    return render_template('admin_user_learning_detail.html', 
                         user=user,
                         course_details=course_details,
                         user_badges_earned=user_badges_earned,
                         completed_courses=completed_courses,
                         total_enrolled=total_enrolled,
                         avg_score=avg_score)

@app.route('/admin/learning/course/<int:course_id>')
@login_required
def admin_course_learning_detail(course_id):
    if 'user' not in session or session.get('role') != 'admin':
        flash("Access denied. Admin privileges required.", "error")
        return redirect(url_for("dashboard"))
    
    course = next((c for c in courses if c['id'] == course_id), None)
    if not course:
        flash('Course not found!', 'error')
        return redirect(url_for('admin_learning'))
    
    # Get all users enrolled in this course
    enrolled_users = []
    for user_id, progress in user_progress.items():
        if course_id in progress:
            user = next((u for u in users if u['id'] == user_id), None) if 'users' in globals() else None
            if user:
                user_progress_data = progress[course_id]
                enrolled_users.append({
                    'user': user,
                    'enrolled': True,
                    'completed': user_progress_data.get('completed', False),
                    'score': user_progress_data.get('score', 0),
                    'last_attempt': user_progress_data.get('last_attempt'),
                    'attempts': user_progress_data.get('attempts', 0),
                    'badge_earned': course.get('badge') in user_badges.get(user_id, [])
                })
    
    # Calculate course statistics
    total_enrolled = len(enrolled_users)
    completed_count = sum(1 for user in enrolled_users if user['completed'])
    avg_score = sum(user['score'] for user in enrolled_users) / total_enrolled if total_enrolled > 0 else 0
    badge_earned_count = sum(1 for user in enrolled_users if user['badge_earned'])
    
    return render_template('admin_course_learning_detail.html', 
                         course=course,
                         enrolled_users=enrolled_users,
                         total_enrolled=total_enrolled,
                         completed_count=completed_count,
                         avg_score=avg_score,
                         badge_earned_count=badge_earned_count)

@app.route('/admin/learning/badges')
@login_required
def admin_badges_overview():
    if 'user' not in session or session.get('role') != 'admin':
        flash("Access denied. Admin privileges required.", "error")
        return redirect(url_for("dashboard"))
    
    # Get all unique badges
    all_badges = set()
    for course in courses:
        if 'badge' in course:
            all_badges.add(course['badge'])
    
    # Calculate badge statistics
    badge_stats = []
    for badge in all_badges:
        earned_count = sum(1 for user_badges_list in user_badges.values() if badge in user_badges_list)
        badge_stats.append({
            'badge': badge,
            'earned_count': earned_count,
            'total_users': len(users) if 'users' in globals() else 0,
            'earned_percentage': (earned_count / len(users) * 100) if 'users' in globals() and len(users) > 0 else 0
        })
    
    # Sort by earned count
    badge_stats.sort(key=lambda x: x['earned_count'], reverse=True)
    
    return render_template('admin_badges_overview.html', 
                         badge_stats=badge_stats,
                         total_badges=len(all_badges))

# Onboarding Data Structures
onboarding_tasks = [
    {
        'id': 1,
        'title': 'Complete HR Paperwork',
        'description': 'Fill out all required HR forms and documentation',
        'category': 'HR',
        'estimated_time': '2 hours',
        'required': True
    },
    {
        'id': 2,
        'title': 'IT Account Setup',
        'description': 'Create email, system access, and necessary accounts',
        'category': 'IT',
        'estimated_time': '1 hour',
        'required': True
    },
    {
        'id': 3,
        'title': 'Equipment Assignment',
        'description': 'Assign laptop, phone, and other necessary equipment',
        'category': 'IT',
        'estimated_time': '30 minutes',
        'required': True
    },
    {
        'id': 4,
        'title': 'Security Training',
        'description': 'Complete mandatory security awareness training',
        'category': 'Training',
        'estimated_time': '1 hour',
        'required': True
    },
    {
        'id': 5,
        'title': 'Team Introduction',
        'description': 'Meet with team members and key stakeholders',
        'category': 'Culture',
        'estimated_time': '2 hours',
        'required': False
    },
    {
        'id': 6,
        'title': 'Benefits Enrollment',
        'description': 'Enroll in health, dental, and other benefits',
        'category': 'HR',
        'estimated_time': '1 hour',
        'required': True
    }
]

onboarding_employees = []

@app.route('/admin/onboarding', methods=['GET', 'POST'])
@login_required
def admin_onboarding():
    if 'user' not in session or session.get('role') != 'admin':
        flash("Access denied. Admin privileges required.", "error")
        return redirect(url_for("dashboard"))
    
    if request.method == 'POST':
        employee_name = request.form.get('employee_name')
        employee_email = request.form.get('employee_email')
        department = request.form.get('department')
        position = request.form.get('position')
        start_date = request.form.get('start_date')
        
        if employee_name and employee_email:
            onboarding_id = len(onboarding_employees) + 1
            new_onboarding = {
                'id': onboarding_id,
                'employee_name': employee_name,
                'employee_email': employee_email,
                'department': department,
                'position': position,
                'start_date': start_date,
                'status': 'in_progress',
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'completed_tasks': [],
                'notes': ''
            }
            onboarding_employees.append(new_onboarding)
            flash('New employee onboarding created successfully!', 'success')
            return redirect(url_for('admin_onboarding'))
    
    return render_template('admin_onboarding.html', 
                         onboarding_list=onboarding_employees,
                         tasks=onboarding_tasks)

@app.route('/admin/onboarding/<int:onboarding_id>')
@login_required
def view_onboarding(onboarding_id):
    if 'user' not in session or session.get('role') != 'admin':
        flash("Access denied. Admin privileges required.", "error")
        return redirect(url_for("dashboard"))
    
    onboarding = next((o for o in onboarding_employees if o['id'] == onboarding_id), None)
    if not onboarding:
        flash('Onboarding not found!', 'error')
        return redirect(url_for('admin_onboarding'))
    
    return render_template('admin_onboarding_detail.html', 
                         onboarding=onboarding,
                         tasks=onboarding_tasks)

@app.route('/admin/onboarding/<int:onboarding_id>/complete-task/<int:task_id>', methods=['POST'])
@login_required
def complete_onboarding_task(onboarding_id, task_id):
    if 'user' not in session or session.get('role') != 'admin':
        flash("Access denied. Admin privileges required.", "error")
        return redirect(url_for("dashboard"))
    
    onboarding = next((o for o in onboarding_employees if o['id'] == onboarding_id), None)
    if onboarding and task_id not in onboarding['completed_tasks']:
        onboarding['completed_tasks'].append(task_id)
        
        # Check if all required tasks are completed
        required_tasks = [t['id'] for t in onboarding_tasks if t['required']]
        if all(task_id in onboarding['completed_tasks'] for task_id in required_tasks):
            onboarding['status'] = 'completed'
            flash('All required tasks completed! Onboarding marked as complete.', 'success')
        else:
            flash('Task marked as completed!', 'success')
    
    return redirect(url_for('view_onboarding', onboarding_id=onboarding_id))

@app.route('/admin/onboarding/<int:onboarding_id>/update-status', methods=['POST'])
@login_required
def update_onboarding_status(onboarding_id):
    if 'user' not in session or session.get('role') != 'admin':
        flash("Access denied. Admin privileges required.", "error")
        return redirect(url_for("dashboard"))
    
    new_status = request.form.get('status')
    notes = request.form.get('notes', '')
    
    onboarding = next((o for o in onboarding_employees if o['id'] == onboarding_id), None)
    if onboarding:
        onboarding['status'] = new_status
        onboarding['notes'] = notes
        flash('Onboarding status updated successfully!', 'success')
    
    return redirect(url_for('view_onboarding', onboarding_id=onboarding_id))

# Paystubs and Benefits Data Structures
paystubs = [
    {
        'id': 1,
        'employee_id': 'user@example.com',
        'period': 'January 2024', 
        'amount': 4500, 
        'gross_pay': 5000.00,
        'net_pay': 4500.00,
        'hours_worked': 160,
        'overtime_hours': 8,
        'pay_date': '2024-01-31',
        'status': 'Paid'
    },
    {
        'id': 2, 
        'employee_id': 'user@example.com',
        'period': 'December 2023', 
        'amount': 4500, 
        'gross_pay': 5000.00,
        'net_pay': 4500.00,
        'hours_worked': 160,
        'overtime_hours': 0,
        'pay_date': '2023-12-31',
        'status': 'Paid'
    },
    {
        'id': 3, 
        'employee_id': 'user@example.com',
        'period': 'November 2023', 
        'amount': 4500, 
        'gross_pay': 5000.00,
        'net_pay': 4500.00,
        'hours_worked': 160,
        'overtime_hours': 12,
        'pay_date': '2023-11-30',
        'status': 'Paid'
    }
]

benefits = [
    {
        'id': 1,
        'name': 'Health Insurance', 
        'status': 'Active', 
        'provider': 'Blue Cross',
        'type': 'Medical',
        'coverage': 'Family',
        'employee_cost': 150.00,
        'employer_contribution': 450.00,
        'monthly_cost': 600.00
    },
    {
        'id': 2,
        'name': 'Dental Insurance', 
        'status': 'Active', 
        'provider': 'Delta Dental',
        'type': 'Dental',
        'coverage': 'Individual',
        'employee_cost': 25.00,
        'employer_contribution': 75.00,
        'monthly_cost': 100.00
    },
    {
        'id': 3,
        'name': '401(k) Retirement', 
        'status': 'Active', 
        'provider': 'Fidelity',
        'type': 'Retirement',
        'coverage': 'Individual',
        'employee_cost': 200.00,
        'employer_contribution': 100.00,
        'monthly_cost': 300.00
    },
    {
        'id': 4,
        'name': 'Life Insurance', 
        'status': 'Active', 
        'provider': 'MetLife',
        'type': 'Life',
        'coverage': '2x Salary',
        'employee_cost': 0.00,
        'employer_contribution': 50.00,
        'monthly_cost': 50.00
    }
]

@app.route('/employee/paystubs/<int:paystub_id>')
@login_required
def view_paystub(paystub_id):
    if 'user' not in session:
        return redirect(url_for('employee_login'))
    
    user_id = session['user']
    paystub = next((p for p in paystubs if p['id'] == paystub_id and p['employee_id'] == user_id), None)
    
    if not paystub:
        flash('Paystub not found!', 'error')
        return redirect(url_for('employee_paystubs'))
    
    return render_template('employee_portal/paystub_detail.html', paystub=paystub)

@app.route('/employee/benefits/<int:benefit_id>')
@login_required
def view_benefit(benefit_id):
    if 'user' not in session:
        return redirect(url_for('employee_login'))
    
    benefit = next((b for b in benefits if b['id'] == benefit_id), None)
    
    if not benefit:
        flash('Benefit not found!', 'error')
        return redirect(url_for('employee_benefits'))
    
    return render_template('employee_portal/benefit_detail.html', benefit=benefit)

# Leave Request Data Structures
leave_types = [
    'Vacation',
    'Sick Leave',
    'Personal Leave',
    'Bereavement',
    'Maternity/Paternity',
    'Jury Duty',
    'Military Leave',
    'Other'
]

# Time Off Requests Data
timeoff_requests = [
    {
        'id': 1,
        'employee_name': 'John Doe',
        'employee_id': 1,
        'type': 'Vacation',
        'start_date': '2024-01-15',
        'end_date': '2024-01-20',
        'total_days': 5,
        'reason': 'Family vacation',
        'status': 'pending',
        'submitted_date': '2024-01-10'
    },
    {
        'id': 2,
        'employee_name': 'Jane Smith',
        'employee_id': 2,
        'type': 'Sick Leave',
        'start_date': '2024-01-12',
        'end_date': '2024-01-14',
        'total_days': 2,
        'reason': 'Medical appointment',
        'status': 'approved',
        'submitted_date': '2024-01-11'
    }
]

# Leave Requests Data
leave_requests = [
    {
        'id': 1,
        'employee_name': 'John Doe',
        'employee_id': 1,
        'leave_type': 'Vacation',
        'start_date': '2024-02-01',
        'end_date': '2024-02-05',
        'total_days': 4,
        'reason': 'Annual family vacation',
        'status': 'pending',
        'submitted_date': '2024-01-25'
    },
    {
        'id': 2,
        'employee_name': 'Jane Smith',
        'employee_id': 2,
        'leave_type': 'Personal Leave',
        'start_date': '2024-01-20',
        'end_date': '2024-01-22',
        'total_days': 2,
        'reason': 'Personal matters',
        'status': 'approved',
        'submitted_date': '2024-01-18'
    }
]

# Timesheets Data
timesheets = [
    {
        'id': 1,
        'employee_name': 'John Doe',
        'employee_id': 1,
        'week_of': '2024-01-08',
        'total_hours': 40,
        'status': 'approved',
        'submitted_at': '2024-01-12'
    },
    {
        'id': 2,
        'employee_name': 'Jane Smith',
        'employee_id': 2,
        'week_of': '2024-01-08',
        'total_hours': 38,
        'status': 'pending',
        'submitted_at': '2024-01-12'
    }
]

# Devices Data
devices = [
    {
        'id': 1,
        'name': 'MacBook Pro 16"',
        'type': 'laptop',
        'model': 'M2 Pro',
        'serial_number': 'MBP2023001',
        'status': 'assigned',
        'location': 'IT Department',
        'assigned_to': 'John Doe'
    },
    {
        'id': 2,
        'name': 'Dell XPS 15',
        'type': 'laptop',
        'model': 'XPS 15 9520',
        'serial_number': 'DLL2023002',
        'status': 'available',
        'location': 'IT Department',
        'assigned_to': None
    },
    {
        'id': 3,
        'name': 'iPhone 15 Pro',
        'type': 'mobile',
        'model': 'iPhone 15 Pro',
        'serial_number': 'IPH2023003',
        'status': 'assigned',
        'location': 'Mobile Devices',
        'assigned_to': 'Jane Smith'
    }
]

leave_requests = [
    {
        'id': 1,
        'employee_id': 1,
        'employee_name': 'John Doe',
        'leave_type': 'Vacation',
        'start_date': '2024-02-15',
        'end_date': '2024-02-20',
        'total_days': 6,
        'reason': 'Family vacation',
        'status': 'approved',
        'submitted_at': '2024-01-15 10:30:00',
        'approved_by': 'HR Manager',
        'approved_at': '2024-01-16 14:20:00',
        'notes': 'Approved for family vacation'
    },
    {
        'id': 2,
        'employee_id': 1,
        'employee_name': 'John Doe',
        'leave_type': 'Sick Leave',
        'start_date': '2024-01-10',
        'end_date': '2024-01-12',
        'total_days': 3,
        'reason': 'Not feeling well',
        'status': 'approved',
        'submitted_at': '2024-01-09 08:15:00',
        'approved_by': 'HR Manager',
        'approved_at': '2024-01-09 16:45:00',
        'notes': 'Approved for medical leave'
    }
]

# Job Posting Data Structures
job_postings = [
    {
        'id': 1,
        'title': 'Senior Software Engineer',
        'department': 'IT',
        'location': 'New York',
        'employment_type': 'Full-time',
        'experience_level': 'Senior',
        'salary_range': '$120,000 - $150,000',
        'description': 'We are looking for a Senior Software Engineer to join our development team...',
        'requirements': [
            '5+ years of experience in software development',
            'Proficiency in Python, JavaScript, and React',
            'Experience with cloud platforms (AWS/Azure)',
            'Strong problem-solving skills',
            'Excellent communication abilities'
        ],
        'benefits': [
            'Competitive salary and equity',
            'Health, dental, and vision insurance',
            '401(k) with company match',
            'Flexible work arrangements',
            'Professional development opportunities'
        ],
        'status': 'Active',
        'created_at': '2024-01-15 10:30:00',
        'applications_count': 12
    },
    {
        'id': 2,
        'title': 'Marketing Specialist',
        'department': 'Marketing',
        'location': 'San Francisco',
        'employment_type': 'Full-time',
        'experience_level': 'Mid-level',
        'salary_range': '$80,000 - $100,000',
        'description': 'Join our marketing team to help drive brand awareness and customer acquisition...',
        'requirements': [
            '3+ years of marketing experience',
            'Experience with digital marketing campaigns',
            'Proficiency in marketing analytics tools',
            'Creative thinking and strategic planning',
            'Strong written and verbal communication'
        ],
        'benefits': [
            'Competitive salary',
            'Health and wellness benefits',
            'Remote work options',
            'Career growth opportunities',
            'Team events and activities'
        ],
        'status': 'Active',
        'created_at': '2024-01-10 14:20:00',
        'applications_count': 8
    }
]

job_applications = [
    {
        'id': 1,
        'job_id': 1,
        'applicant_name': 'Sarah Johnson',
        'applicant_email': 'sarah.johnson@email.com',
        'applicant_phone': '+1 (555) 123-4567',
        'resume_file': 'sarah_johnson_resume.pdf',
        'cover_letter': 'I am excited to apply for the Senior Software Engineer position...',
        'status': 'Under Review',
        'applied_at': '2024-01-20 09:15:00',
        'reviewed_by': None,
        'reviewed_at': None,
        'notes': ''
    },
    {
        'id': 2,
        'job_id': 1,
        'applicant_name': 'Mike Chen',
        'applicant_email': 'mike.chen@email.com',
        'applicant_phone': '+1 (555) 234-5678',
        'resume_file': 'mike_chen_resume.pdf',
        'cover_letter': 'With my 6 years of experience in software development...',
        'status': 'Shortlisted',
        'applied_at': '2024-01-18 16:30:00',
        'reviewed_by': 'HR Manager',
        'reviewed_at': '2024-01-22 11:45:00',
        'notes': 'Strong technical background, good communication skills'
    }
]

@app.route('/admin/jobs')
@login_required
def admin_jobs():
    if 'user' not in session or session.get('role') != 'admin':
        flash("Access denied. Admin privileges required.", "error")
        return redirect(url_for("dashboard"))
    
    return render_template('admin_jobs.html', 
                         jobs=job_postings,
                         applications=job_applications)

@app.route('/admin/jobs/add', methods=['GET', 'POST'])
@login_required
def add_job():
    if 'user' not in session or session.get('role') != 'admin':
        flash("Access denied. Admin privileges required.", "error")
        return redirect(url_for("dashboard"))
    
    if request.method == 'POST':
        title = request.form.get('title')
        department = request.form.get('department')
        location = request.form.get('location')
        type = request.form.get('type')
        salary_min = request.form.get('salary_min')
        salary_max = request.form.get('salary_max')
        description = request.form.get('description')
        requirements = request.form.get('requirements', '')
        experience_level = request.form.get('experience_level')
        status = request.form.get('status', 'Draft')
        
        if title and department:
            job_id = len(job_postings) + 1
            new_job = {
                'id': job_id,
                'title': title,
                'department': department,
                'location': location or '',
                'employment_type': type or 'Full-time',
                'experience_level': experience_level or '',
                'salary_range': f"${salary_min} - ${salary_max}" if salary_min and salary_max else '',
                'description': description or '',
                'requirements': [req.strip() for req in requirements.split('\n') if req.strip()],
                'benefits': [],
                'status': status,
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'applications_count': 0
            }
            job_postings.append(new_job)
            flash('Job posting created successfully!', 'success')
            return redirect(url_for('admin_jobs'))
    
    return render_template('admin_add_job.html')

@app.route('/admin/jobs/<int:job_id>')
@login_required
def view_job(job_id):
    if 'user' not in session or session.get('role') != 'admin':
        flash("Access denied. Admin privileges required.", "error")
        return redirect(url_for("dashboard"))
    
    job = next((j for j in job_postings if j['id'] == job_id), None)
    
    if not job:
        flash('Job posting not found!', 'error')
        return redirect(url_for('admin_jobs'))
    
    # Get applications for this job
    job_applications_list = [a for a in job_applications if a['job_id'] == job_id]
    
    return render_template('admin_job_detail.html', 
                         job=job,
                         applications=job_applications_list)

@app.route('/admin/jobs/<int:job_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_job(job_id):
    if 'user' not in session or session.get('role') != 'admin':
        flash("Access denied. Admin privileges required.", "error")
        return redirect(url_for("dashboard"))
    
    job = next((j for j in job_postings if j['id'] == job_id), None)
    
    if not job:
        flash('Job posting not found!', 'error')
        return redirect(url_for('admin_jobs'))
    
    if request.method == 'POST':
        job.update({
            'title': request.form.get('title', job['title']),
            'department': request.form.get('department', job['department']),
            'location': request.form.get('location', job['location']),
            'employment_type': request.form.get('employment_type', job['employment_type']),
            'experience_level': request.form.get('experience_level', job['experience_level']),
            'salary_range': request.form.get('salary_range', job['salary_range']),
            'description': request.form.get('description', job['description']),
            'status': request.form.get('status', job['status'])
        })
        
        # Update requirements and benefits
        requirements = request.form.get('requirements', '').split('\n')
        benefits = request.form.get('benefits', '').split('\n')
        job['requirements'] = [req.strip() for req in requirements if req.strip()]
        job['benefits'] = [benefit.strip() for benefit in benefits if benefit.strip()]
        
        flash('Job posting updated successfully!', 'success')
        return redirect(url_for('view_job', job_id=job_id))
    
    return render_template('admin_edit_job.html', job=job)

@app.route('/admin/jobs/<int:job_id>/update', methods=['POST'])
@admin_required
def update_job(job_id):
    if 'user' not in session or session.get('role') != 'admin':
        flash("Access denied. Admin privileges required.", "error")
        return redirect(url_for("dashboard"))
    
    job = next((j for j in jobs if j['id'] == job_id), None)
    
    if job:
        job['title'] = request.form.get('title')
        job['department'] = request.form.get('department')
        job['location'] = request.form.get('location')
        job['job_type'] = request.form.get('job_type')
        job['salary_range'] = request.form.get('salary_range')
        job['experience_level'] = request.form.get('experience_level')
        job['description'] = request.form.get('description')
        job['requirements'] = request.form.get('requirements')
        job['benefits'] = request.form.get('benefits')
        job['status'] = request.form.get('status')
        
        flash('Job updated successfully!', 'success')
    else:
        flash('Job not found!', 'error')
    
    return redirect(url_for('admin_jobs'))

@app.route('/admin/jobs/<int:job_id>/applications/<int:application_id>/update-status', methods=['POST'])
@login_required
def update_application_status(job_id, application_id):
    if 'user' not in session or session.get('role') != 'admin':
        flash("Access denied. Admin privileges required.", "error")
        return redirect(url_for("dashboard"))
    
    application = next((a for a in job_applications if a['id'] == application_id), None)
    
    if application:
        new_status = request.form.get('status')
        notes = request.form.get('notes', '')
        
        application['status'] = new_status
        application['notes'] = notes
        application['reviewed_by'] = session['user']['name']
        application['reviewed_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        flash('Application status updated successfully!', 'success')
    
    return redirect(url_for('view_job', job_id=job_id))

# IT Knowledge Hub Data Structures
knowledge_categories = [
    'Getting Started',
    'Software & Tools',
    'Network & Security',
    'Hardware & Equipment',
    'Troubleshooting',
    'Policies & Procedures',
    'Training & Resources',
    'FAQ'
]

knowledge_documents = [
    {
        'id': 1,
        'title': 'New Employee IT Setup Guide',
        'category': 'Getting Started',
        'content': '''
# New Employee IT Setup Guide

## Welcome to the Company!

This guide will help you get set up with all the necessary IT resources on your first day.

### Step 1: Account Creation
- Your IT account will be created automatically
- You'll receive login credentials via email
- Default password: Welcome2024!

### Step 2: Email Setup
- Access your email at: mail.company.com
- Set up email signature with your details
- Configure email forwarding if needed

### Step 3: Software Installation
- Install required software from the company portal
- Essential tools: Office 365, Slack, Zoom
- Development tools: VS Code, Git, Docker

### Step 4: Security Setup
- Enable two-factor authentication
- Set up VPN access
- Complete security training modules

### Need Help?
Contact IT Support at: support@company.com
        ''',
        'author': 'IT Team',
        'created_at': '2024-01-15 09:00:00',
        'updated_at': '2024-01-15 09:00:00',
        'tags': ['onboarding', 'setup', 'new-employee'],
        'views': 45,
        'status': 'Published'
    },
    {
        'id': 2,
        'title': 'VPN Connection Guide',
        'category': 'Network & Security',
        'content': '''
# VPN Connection Guide

## Connecting to Company VPN

### Prerequisites
- Valid company email account
- Two-factor authentication enabled
- VPN client installed

### Connection Steps

1. **Download VPN Client**
   - Visit: vpn.company.com
   - Download appropriate client for your OS

2. **Install and Configure**
   - Run the installer
   - Enter server: vpn.company.com
   - Use your company credentials

3. **Connect**
   - Launch the VPN client
   - Enter username and password
   - Complete 2FA if prompted

### Troubleshooting
- **Connection Failed**: Check internet connection
- **Authentication Error**: Verify credentials
- **Slow Connection**: Try different server locations

### Support
For VPN issues, contact: network@company.com
        ''',
        'author': 'Network Team',
        'created_at': '2024-01-10 14:30:00',
        'updated_at': '2024-01-12 11:15:00',
        'tags': ['vpn', 'security', 'remote-work'],
        'views': 78,
        'status': 'Published'
    },
    {
        'id': 3,
        'title': 'Password Policy Guidelines',
        'category': 'Policies & Procedures',
        'content': '''
# Password Policy Guidelines

## Password Requirements

### Minimum Standards
- **Length**: At least 12 characters
- **Complexity**: Mix of uppercase, lowercase, numbers, symbols
- **History**: Cannot reuse last 5 passwords
- **Expiration**: Change every 90 days

### Examples of Strong Passwords
✅ Good: `MyCompany2024!Secure`
✅ Good: `Blue@Sky#2024$Work`
❌ Bad: `password123`
❌ Bad: `123456789`

### Password Management
- Use a password manager (recommended: LastPass, 1Password)
- Never share passwords
- Report suspicious activity immediately

### Two-Factor Authentication
- Required for all company accounts
- Use authenticator apps (Google Authenticator, Authy)
- Backup codes stored securely

### Security Best Practices
- Never write passwords down
- Don't use personal information
- Log out of shared computers
- Report security incidents immediately

### Support
For password issues: security@company.com
        ''',
        'author': 'Security Team',
        'created_at': '2024-01-08 16:45:00',
        'updated_at': '2024-01-08 16:45:00',
        'tags': ['security', 'password', 'policy'],
        'views': 156,
        'status': 'Published'
    }
]

@app.route('/admin/knowledge')
@login_required
def admin_knowledge():
    if 'user' not in session or session.get('role') != 'admin':
        flash("Access denied. Admin privileges required.", "error")
        return redirect(url_for("dashboard"))
    
    # Get search parameters
    search = request.args.get('search', '').lower()
    category = request.args.get('category', '')
    
    # Filter documents
    filtered_documents = knowledge_documents
    
    if search:
        filtered_documents = [d for d in filtered_documents if 
                           search in d['title'].lower() or 
                           search in d['content'].lower()]
    
    if category:
        filtered_documents = [d for d in filtered_documents if d['category'] == category]
    
    return render_template('admin_knowledge.html', 
                         documents=filtered_documents,
                         categories=knowledge_categories,
                         search=search,
                         selected_category=category)

@app.route('/admin/knowledge/add', methods=['GET', 'POST'])
@login_required
def add_knowledge_document():
    if 'user' not in session or session.get('role') != 'admin':
        flash("Access denied. Admin privileges required.", "error")
        return redirect(url_for("dashboard"))
    
    if request.method == 'POST':
        title = request.form.get('title')
        category = request.form.get('category')
        content = request.form.get('content')
        tags = request.form.get('tags', '').split(',')
        status = request.form.get('status', 'Draft')
        
        if title and category and content:
            doc_id = len(knowledge_documents) + 1
            new_document = {
                'id': doc_id,
                'title': title,
                'category': category,
                'content': content,
                'author': session['user']['name'],
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'tags': [tag.strip() for tag in tags if tag.strip()],
                'views': 0,
                'status': status
            }
            knowledge_documents.append(new_document)
            flash('Knowledge document created successfully!', 'success')
            return redirect(url_for('admin_knowledge'))
    
    return render_template('admin_add_knowledge.html', categories=knowledge_categories)

@app.route('/admin/knowledge/<int:doc_id>')
@login_required
def view_knowledge_document(doc_id):
    if 'user' not in session or session.get('role') != 'admin':
        flash("Access denied. Admin privileges required.", "error")
        return redirect(url_for("dashboard"))
    
    document = next((d for d in knowledge_documents if d['id'] == doc_id), None)
    
    if not document:
        flash('Document not found!', 'error')
        return redirect(url_for('admin_knowledge'))
    
    # Increment view count
    document['views'] += 1
    
    return render_template('admin_knowledge_detail.html', document=document)

@app.route('/admin/knowledge/<int:doc_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_knowledge_document(doc_id):
    if 'user' not in session or session.get('role') != 'admin':
        flash("Access denied. Admin privileges required.", "error")
        return redirect(url_for("dashboard"))
    
    document = next((d for d in knowledge_documents if d['id'] == doc_id), None)
    
    if not document:
        flash('Document not found!', 'error')
        return redirect(url_for('admin_knowledge'))
    
    if request.method == 'POST':
        document.update({
            'title': request.form.get('title', document['title']),
            'category': request.form.get('category', document['category']),
            'content': request.form.get('content', document['content']),
            'status': request.form.get('status', document['status']),
            'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        
        # Update tags
        tags = request.form.get('tags', '').split(',')
        document['tags'] = [tag.strip() for tag in tags if tag.strip()]
        
        flash('Document updated successfully!', 'success')
        return redirect(url_for('view_knowledge_document', doc_id=doc_id))
    
    return render_template('admin_edit_knowledge.html', 
                         document=document,
                         categories=knowledge_categories)

@app.route('/admin/knowledge/<int:doc_id>/delete', methods=['POST'])
@login_required
def delete_knowledge_document(doc_id):
    if 'user' not in session or session.get('role') != 'admin':
        flash("Access denied. Admin privileges required.", "error")
        return redirect(url_for("dashboard"))
    
    document = next((d for d in knowledge_documents if d['id'] == doc_id), None)
    
    if document:
        knowledge_documents.remove(document)
        flash('Document deleted successfully!', 'success')
    else:
        flash('Document not found!', 'error')
    
    return redirect(url_for('admin_knowledge'))

# Public knowledge hub for employees
@app.route('/employee/knowledge')
@login_required
def employee_knowledge():
    if 'user' not in session:
        return redirect(url_for('employee_login'))
    
    # Get search parameters
    search = request.args.get('search', '').lower()
    category = request.args.get('category', '')
    
    # Filter published documents only
    filtered_documents = [d for d in knowledge_documents if d['status'] == 'Published']
    
    if search:
        filtered_documents = [d for d in filtered_documents if 
                           search in d['title'].lower() or 
                           search in d['content'].lower()]
    
    if category:
        filtered_documents = [d for d in filtered_documents if d['category'] == category]
    
    return render_template('employee_portal/knowledge.html', 
                         documents=filtered_documents,
                         categories=knowledge_categories,
                         search=search,
                         selected_category=category)

@app.route('/employee/knowledge/<int:doc_id>')
@login_required
def view_employee_knowledge_document(doc_id):
    if 'user' not in session:
        return redirect(url_for('employee_login'))
    
    document = next((d for d in knowledge_documents if d['id'] == doc_id and d['status'] == 'Published'), None)
    
    if not document:
        flash('Document not found!', 'error')
        return redirect(url_for('employee_knowledge'))
    
    # Increment view count
    document['views'] += 1
    
    return render_template('employee_portal/knowledge_detail.html', document=document)

@app.route('/')
@login_required
def landing_page():
    return render_template('landing.html')

# Induction Page Data Structures
induction_categories = [
    'Company Overview',
    'HR Policies',
    'IT Policies',
    'Benefits & Compensation',
    'Safety & Security',
    'Workplace Guidelines',
    'Training Resources',
    'Contact Information'
]

induction_documents = [
    {
        'id': 1,
        'title': 'Welcome to Our Company',
        'category': 'Company Overview',
        'content': '''
# Welcome to Our Company

## About Us
We are a forward-thinking organization committed to innovation, growth, and employee development. Our mission is to create an inclusive workplace where every employee can thrive and contribute to our success.

## Our Values
- **Integrity**: We operate with honesty and transparency
- **Innovation**: We encourage creative thinking and new ideas
- **Collaboration**: We work together to achieve common goals
- **Excellence**: We strive for the highest quality in everything we do
- **Diversity**: We celebrate and embrace different perspectives

## Company History
Founded in 2010, we have grown from a small startup to a leading organization in our industry. Our journey has been marked by continuous learning, adaptation, and commitment to our employees and customers.

## Organizational Structure
- **CEO**: Sarah Johnson
- **CTO**: Mike Chen
- **CFO**: David Lee
- **CHRO**: Lisa Wang

## Office Locations
- **Headquarters**: New York, NY
- **West Coast**: San Francisco, CA
- **International**: London, UK

## Contact Information
- **General**: info@company.com
- **HR**: hr@company.com
- **IT Support**: support@company.com
        ''',
        'author': 'HR Team',
        'created_at': '2024-01-01 09:00:00',
        'updated_at': '2024-01-01 09:00:00',
        'tags': ['welcome', 'company', 'overview'],
        'views': 89,
        'status': 'Published',
        'required': True
    },
    {
        'id': 2,
        'title': 'Employee Handbook',
        'category': 'HR Policies',
        'content': '''
# Employee Handbook

## Employment Policies

### Equal Opportunity
We are committed to providing equal employment opportunities to all employees and applicants without regard to race, color, religion, sex, national origin, age, disability, or genetic information.

### Anti-Harassment Policy
We maintain a workplace free from harassment and discrimination. Any form of harassment based on protected characteristics is strictly prohibited.

### Dress Code
- **Business Casual**: Monday to Thursday
- **Casual Friday**: Appropriate casual attire
- **Client Meetings**: Business professional attire required

### Working Hours
- **Standard Hours**: 9:00 AM - 5:00 PM
- **Flexible Schedule**: Available with manager approval
- **Remote Work**: Hybrid model available

### Attendance Policy
- Regular attendance is expected
- Notify your manager for absences
- Use the leave request system for planned time off

### Performance Management
- Annual performance reviews
- Regular 1:1 meetings with managers
- Continuous feedback and development

## Code of Conduct
- Act with integrity and professionalism
- Respect colleagues and customers
- Maintain confidentiality
- Report violations promptly
        ''',
        'author': 'HR Team',
        'created_at': '2024-01-01 10:00:00',
        'updated_at': '2024-01-01 10:00:00',
        'tags': ['handbook', 'policies', 'conduct'],
        'views': 156,
        'status': 'Published',
        'required': True
    },
    {
        'id': 3,
        'title': 'IT Security Policy',
        'category': 'IT Policies',
        'content': '''
# IT Security Policy

## Password Requirements
- Minimum 12 characters
- Mix of uppercase, lowercase, numbers, symbols
- Change every 90 days
- No reuse of last 5 passwords

## Data Protection
- Never share login credentials
- Lock computer when away from desk
- Use company-approved software only
- Report security incidents immediately

## Email Security
- Be cautious with attachments
- Verify sender identity
- Report suspicious emails to IT
- Use company email for work only

## Remote Work Security
- Use VPN for remote access
- Secure home network
- Keep software updated
- Use company devices when possible

## Acceptable Use
- Work-related activities only
- No personal file sharing
- Respect copyright laws
- Monitor internet usage

## Incident Reporting
- Report security incidents to IT immediately
- Document all details
- Preserve evidence if possible
- Follow incident response procedures
        ''',
        'author': 'IT Security Team',
        'created_at': '2024-01-01 11:00:00',
        'updated_at': '2024-01-01 11:00:00',
        'tags': ['security', 'it', 'policy'],
        'views': 234,
        'status': 'Published',
        'required': True
    },
    {
        'id': 4,
        'title': 'Benefits Overview',
        'category': 'Benefits & Compensation',
        'content': '''
# Benefits & Compensation Overview

## Health Insurance
- **Medical**: Blue Cross Blue Shield
- **Dental**: Delta Dental
- **Vision**: VSP
- **Coverage**: Family plans available
- **Cost**: 80% employer contribution

## Retirement Benefits
- **401(k)**: 6% employer match
- **Vesting**: 3-year graded vesting
- **Investment Options**: Multiple fund choices
- **Financial Planning**: Free consultations

## Paid Time Off
- **Vacation**: 20 days per year
- **Sick Leave**: 10 days per year
- **Personal Days**: 5 days per year
- **Holidays**: 10 company holidays

## Additional Benefits
- **Life Insurance**: 2x annual salary
- **Disability**: Short and long-term coverage
- **Employee Assistance**: Mental health support
- **Gym Membership**: $50 monthly reimbursement

## Professional Development
- **Tuition Reimbursement**: Up to $5,000/year
- **Conference Attendance**: Approved events
- **Certification**: Professional certifications
- **Training**: Internal and external courses

## Work-Life Balance
- **Flexible Hours**: Available with approval
- **Remote Work**: Hybrid model
- **Parental Leave**: 12 weeks paid
- **Wellness Programs**: Health initiatives
        ''',
        'author': 'HR Benefits Team',
        'created_at': '2024-01-01 12:00:00',
        'updated_at': '2024-01-01 12:00:00',
        'tags': ['benefits', 'compensation', 'health'],
        'views': 198,
        'status': 'Published',
        'required': True
    }
]

@app.route('/induction')
@login_required
def induction_page():
    # Get search parameters
    search = request.args.get('search', '').lower()
    category = request.args.get('category', '')
    
    # Filter documents
    filtered_documents = [d for d in induction_documents if d['status'] == 'Published']
    
    if search:
        filtered_documents = [d for d in filtered_documents if 
                           search in d['title'].lower() or 
                           search in d['content'].lower()]
    
    if category:
        filtered_documents = [d for d in filtered_documents if d['category'] == category]
    
    return render_template('induction.html', 
                         documents=filtered_documents,
                         categories=induction_categories,
                         search=search,
                         selected_category=category)

@app.route('/induction/<int:doc_id>')
@login_required
def view_induction_document(doc_id):
    document = next((d for d in induction_documents if d['id'] == doc_id and d['status'] == 'Published'), None)
    
    if not document:
        flash('Document not found!', 'error')
        return redirect(url_for('induction_page'))
    
    # Increment view count
    document['views'] += 1
    
    return render_template('induction_detail.html', document=document)

@app.route('/admin/induction')
@login_required
def admin_induction():
    if 'user' not in session or session.get('role') != 'admin':
        flash("Access denied. Admin privileges required.", "error")
        return redirect(url_for("dashboard"))
    
    # Get search parameters
    search = request.args.get('search', '').lower()
    category = request.args.get('category', '')
    
    # Filter documents
    filtered_documents = induction_documents
    
    if search:
        filtered_documents = [d for d in filtered_documents if 
                           search in d['title'].lower() or 
                           search in d['content'].lower()]
    
    if category:
        filtered_documents = [d for d in filtered_documents if d['category'] == category]
    
    return render_template('admin_induction.html', 
                         documents=filtered_documents,
                         categories=induction_categories,
                         search=search,
                         selected_category=category)

@app.route('/admin/induction/add', methods=['GET', 'POST'])
@login_required
def add_induction_document():
    if 'user' not in session or session.get('role') != 'admin':
        flash("Access denied. Admin privileges required.", "error")
        return redirect(url_for("dashboard"))
    
    if request.method == 'POST':
        title = request.form.get('title')
        category = request.form.get('category')
        content = request.form.get('content')
        tags = request.form.get('tags', '').split(',')
        status = request.form.get('status', 'Draft')
        required = request.form.get('required', False) == 'on'
        
        if title and category and content:
            doc_id = len(induction_documents) + 1
            new_document = {
                'id': doc_id,
                'title': title,
                'category': category,
                'content': content,
                'author': session['user']['name'],
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'tags': [tag.strip() for tag in tags if tag.strip()],
                'views': 0,
                'status': status,
                'required': required
            }
            induction_documents.append(new_document)
            flash('Induction document created successfully!', 'success')
            return redirect(url_for('admin_induction'))
    
    return render_template('admin_add_induction.html', categories=induction_categories)

@app.route("/support", methods=["GET", "POST"])
@login_required
def support():
    if "user" not in session:
        return redirect(url_for("login"))
    
    if request.method == "POST":
        support_type = request.form.get("support_type")
        
        if support_type == "ticket":
            return redirect(url_for("submit_ticket"))
        elif support_type == "request":
            return redirect(url_for("submit_request"))
    
    return render_template("support.html")

@app.route('/employee/compensation')
@login_required
def employee_compensation():
    if "user" not in session:
        return redirect(url_for("employee_login"))
    
    # Get paystubs data
    user_paystubs = [p for p in paystubs if p.get('employee_email') == session['user']]
    
    # Get benefits data
    user_benefits = [b for b in benefits if b.get('employee_email') == session['user']]
    
    return render_template("employee_portal/compensation.html", 
                         paystubs=user_paystubs, 
                         benefits=user_benefits)

@app.route('/employee/time-management')
@login_required
def employee_time_management():
    if "user" not in session:
        return redirect(url_for("employee_login"))
    
    # Get leave requests data
    user_leave_requests = [l for l in leave_requests if l.get('employee_email') == session['user']]
    
    # Get timesheet data
    user_timesheets = [t for t in timesheets if t.get('employee_email') == session['user']]
    
    return render_template("employee_portal/time_management.html", 
                         leave_requests=user_leave_requests, 
                         timesheets=user_timesheets)

@app.route('/employee/career-development')
@login_required
def employee_career_development():
    # Redirect to the new minimalistic careers page
    return redirect(url_for("employee_careers"))

@app.route('/employee/groups')
@login_required
def employee_groups():
    if 'user' not in session:
        return redirect(url_for('employee_login'))
    
    # Get all groups from database
    groups = db_helper.get_all_groups()
    
    return render_template('employee_portal/groups.html', groups=groups)

@app.route('/employee/support', methods=['GET', 'POST'])
@login_required
def employee_support():
    if "user" not in session:
        return redirect(url_for("employee_login"))
    
    if request.method == 'POST':
        request_type = request.form.get('request_type')
        subject = request.form.get('subject')
        description = request.form.get('description')
        priority = request.form.get('priority', 'medium')
        
        if request_type and subject and description:
            # Save to database
            request_id = db_helper.create_service_request(
                session['user'], 
                request_type, 
                subject, 
                description, 
                priority
            )
            
            if request_id:
                # Add notification for admin
                db_helper.create_notification("admin@example.com", f"New service request submitted by {session['user']}: {subject}", "warning")
                flash('Service request submitted successfully!', 'success')
            else:
                flash('Error submitting service request. Please try again.', 'error')
            
            return redirect(url_for('employee_support'))
    
    # Get user's service requests
    user_requests = db_helper.get_service_requests_by_user(session['user'])
    
    # Support options for employees
    support_options = [
        {
            'title': 'IT Support',
            'description': 'Submit IT tickets and requests',
            'icon': '💻',
            'link': '/submit-ticket',
            'category': 'Technical'
        },
        {
            'title': 'HR Support',
            'description': 'Get help with HR-related questions',
            'icon': '👥',
            'link': '/employee/help',
            'category': 'HR'
        },
        {
            'title': 'Benefits Support',
            'description': 'Questions about benefits and compensation',
            'icon': '💰',
            'link': '/employee/benefits',
            'category': 'Benefits'
        },
        {
            'title': 'Leave Support',
            'description': 'Help with leave requests and policies',
            'icon': '📅',
            'link': '/employee/leave',
            'category': 'Leave'
        }
    ]
    
    return render_template("employee_portal/support.html", 
                         support_options=support_options,
                         user_requests=user_requests,
                         request_types=['IT Support', 'HR Request', 'Facilities', 'Other'])

@app.route('/admin/support-management')
@login_required
def admin_support_management():
    if "user" not in session or session.get('role') != 'admin':
        flash("Access denied. Admin privileges required.", "error")
        return redirect(url_for("dashboard"))
    
    # Get tickets data
    all_tickets = tickets
    
    # Get requests data - use service requests instead of undefined requests_data
    all_requests = service_requests
    
    return render_template("admin/support_management.html", 
                         tickets=all_tickets, 
                         requests=all_requests)

@app.route('/admin/hr-management')
@login_required
def admin_hr_management():
    if "user" not in session or session.get('role') != 'admin':
        flash("Access denied. Admin privileges required.", "error")
        return redirect(url_for("dashboard"))
    
    # Get employees data
    all_employees = users
    
    # Get time off data
    all_timeoff = timeoff_requests
    
    # Get leave data
    all_leave = leave_requests
    
    # Get timesheets data
    all_timesheets = timesheets
    
    return render_template("admin/hr_management.html", 
                         employees=all_employees,
                         timeoff=all_timeoff,
                         leave=all_leave,
                         timesheets=all_timesheets)

@app.route('/admin/recruitment')
@login_required
def admin_recruitment():
    if "user" not in session or session.get('role') != 'admin':
        flash("Access denied. Admin privileges required.", "error")
        return redirect(url_for("dashboard"))
    
    # Get job postings data
    all_jobs = job_postings
    
    # Get job applications data
    all_applications = job_applications
    
    return render_template("admin/recruitment.html", 
                         jobs=all_jobs,
                         applications=all_applications)

@app.route('/admin/knowledge-learning')
@login_required
def admin_knowledge_learning():
    if "user" not in session or session.get('role') != 'admin':
        flash("Access denied. Admin privileges required.", "error")
        return redirect(url_for("dashboard"))
    
    # Get knowledge documents
    all_knowledge = knowledge_documents
    
    # Get learning data
    all_courses = courses
    all_progress = user_progress
    all_badges = user_badges
    
    return render_template("admin/knowledge_learning.html", 
                         knowledge=all_knowledge,
                         courses=all_courses,
                         progress=all_progress,
                         badges=all_badges)

@app.route('/admin/employee-development')
@login_required
def admin_employee_development():
    if "user" not in session or session.get('role') != 'admin':
        flash("Access denied. Admin privileges required.", "error")
        return redirect(url_for("dashboard"))
    
    # Get onboarding data
    all_onboarding = onboarding_employees
    
    # Get feedback data
    all_feedback = anonymous_feedback
    
    return render_template("admin/employee_development.html", 
                         onboarding=all_onboarding,
                         feedback=all_feedback)

@app.route('/admin/asset-management')
@login_required
def admin_asset_management():
    if "user" not in session or session.get('role') != 'admin':
        flash("Access denied. Admin privileges required.", "error")
        return redirect(url_for("dashboard"))
    
    # Get devices data
    all_devices = devices
    
    return render_template("admin/asset_management.html", 
                         devices=all_devices)

@app.route('/admin/ai-tools')
@login_required
def admin_ai_tools():
    if "user" not in session or session.get('role') != 'admin':
        flash("Access denied. Admin privileges required.", "error")
        return redirect(url_for("dashboard"))
    
    # AI tools data
    ai_tools = [
        {
            'name': 'ATS System',
            'description': 'AI-powered Applicant Tracking System',
            'icon': '🤖',
            'link': '/ai/ats',
            'category': 'Recruitment'
        },
        {
            'name': 'AI Assistant',
            'description': 'RAG-powered knowledge assistant',
            'icon': '💬',
            'link': '/ai/rag',
            'category': 'Support'
        }
    ]
    
    return render_template("admin/ai_tools.html", ai_tools=ai_tools)

@app.route('/admin/timesheets')
@login_required
def admin_timesheets():
    if "user" not in session or session.get('role') != 'admin':
        flash("Access denied. Admin privileges required.", "error")
        return redirect(url_for("dashboard"))
    
    # Get all timesheets from database
    timesheets = db_helper.get_all_timesheets()
    return render_template("admin_timesheets.html", timesheets=timesheets)

@app.route('/admin/timesheets/approve/<int:timesheet_id>', methods=['POST'])
@login_required
def approve_timesheet(timesheet_id):
    if "user" not in session or session.get('role') != 'admin':
        flash("Access denied. Admin privileges required.", "error")
        return redirect(url_for("dashboard"))
    
    if db_helper.update_timesheet_status(timesheet_id, 'approved', session['user']):
        flash('Timesheet approved successfully!', 'success')
    else:
        flash('Error approving timesheet.', 'error')
    
    return redirect(url_for('admin_timesheets'))

@app.route('/admin/timesheets/reject/<int:timesheet_id>', methods=['POST'])
@login_required
def reject_timesheet(timesheet_id):
    if "user" not in session or session.get('role') != 'admin':
        flash("Access denied. Admin privileges required.", "error")
        return redirect(url_for("dashboard"))
    
    if db_helper.update_timesheet_status(timesheet_id, 'rejected', session['user']):
        flash('Timesheet rejected successfully!', 'success')
    else:
        flash('Error rejecting timesheet.', 'error')
    
    return redirect(url_for('admin_timesheets'))

@app.route("/admin/delete-timesheet/<int:timesheet_id>", methods=["POST"])
@login_required
def delete_timesheet(timesheet_id):
    if "user" not in session or session.get("role") != "admin":
        flash("Access denied. Admin privileges required.", "error")
        return redirect(url_for("dashboard"))
    
    if db_helper.delete_timesheet(timesheet_id):
        flash("Timesheet deleted successfully!", "success")
    else:
        flash("Error deleting timesheet", "error")
    
    return redirect(url_for("admin_timesheets"))

@app.route("/admin/add-timesheet-comment/<int:timesheet_id>", methods=["POST"])
@login_required
def add_timesheet_comment(timesheet_id):
    if "user" not in session or session.get("role") != "admin":
        flash("Access denied. Admin privileges required.", "error")
        return redirect(url_for("dashboard"))
    
    comment = request.form.get("comment")
    if comment:
        if db_helper.add_timesheet_comment(timesheet_id, comment, session["user"]):
            flash("Comment added successfully!", "success")
        else:
            flash("Error adding comment", "error")
    
    return redirect(url_for("admin_timesheets"))

@app.route('/admin/service-requests')
@admin_required
def admin_service_requests():
    if "user" not in session or session.get('role') != 'admin':
        flash("Access denied. Admin privileges required.", "error")
        return redirect(url_for("dashboard"))
    
    # Get service requests from database
    service_requests = db_helper.get_all_service_requests()
    
    # If no service requests exist, create some sample ones for testing
    if not service_requests:
        # Create sample service requests
        sample_requests = [
            {
                'user_email': 'john.doe@example.com',
                'request_type': 'IT Support',
                'subject': 'Computer not working',
                'description': 'My computer is not turning on. I need help troubleshooting this issue.',
                'priority': 'high'
            },
            {
                'user_email': 'jane.smith@example.com',
                'request_type': 'HR',
                'subject': 'Benefits question',
                'description': 'I have a question about my health insurance benefits and need clarification.',
                'priority': 'medium'
            },
            {
                'user_email': 'mike.wilson@example.com',
                'request_type': 'Facilities',
                'subject': 'Office temperature',
                'description': 'The office temperature is too cold. Can someone adjust the thermostat?',
                'priority': 'low'
            }
        ]
        
        for req in sample_requests:
            db_helper.create_service_request(
                req['user_email'],
                req['request_type'],
                req['subject'],
                req['description'],
                req['priority']
            )
        
        # Get the newly created requests
        service_requests = db_helper.get_all_service_requests()
    
    return render_template('admin_service_requests.html', service_requests=service_requests)

@app.route('/admin/service-requests/<int:request_id>')
@admin_required
def admin_view_service_request(request_id):
    if "user" not in session or session.get('role') != 'admin':
        flash("Access denied. Admin privileges required.", "error")
        return redirect(url_for("dashboard"))
    
    # Get service request from database
    service_requests = db_helper.get_all_service_requests()
    service_request = next((r for r in service_requests if r["id"] == request_id), None)
    
    if not service_request:
        flash("Service request not found", "error")
        return redirect(url_for("admin_service_requests"))
    
    # Get comments for this request
    comments = db_helper.get_service_request_comments(request_id)
    
    return render_template('admin_service_request_detail.html', 
                         service_request=service_request, 
                         comments=comments)

@app.route('/admin/service-requests/<int:request_id>/approve', methods=['POST'])
@admin_required
def approve_service_request(request_id):
    if "user" not in session or session.get('role') != 'admin':
        flash("Access denied. Admin privileges required.", "error")
        return redirect(url_for("dashboard"))
    
    try:
        # Get service request details for notification
        service_requests = db_helper.get_all_service_requests()
        service_request = next((r for r in service_requests if r["id"] == request_id), None)
        
        if db_helper.update_service_request_status(request_id, 'completed'):
            flash("Service request approved successfully!", "success")
            
            # Send notification to the user who submitted the request
            if service_request:
                notification_message = f"Your service request '{service_request['subject']}' has been approved and completed."
                add_notification(service_request['user_email'], notification_message, "success")
        else:
            flash("Error approving service request", "error")
    except Exception as e:
        print(f"Error approving service request: {e}")
        flash("Error approving service request", "error")
    
    return redirect(url_for("admin_service_requests"))

@app.route('/admin/service-requests/<int:request_id>/reject', methods=['POST'])
@admin_required
def reject_service_request(request_id):
    if "user" not in session or session.get('role') != 'admin':
        flash("Access denied. Admin privileges required.", "error")
        return redirect(url_for("dashboard"))
    
    try:
        # Get service request details for notification
        service_requests = db_helper.get_all_service_requests()
        service_request = next((r for r in service_requests if r["id"] == request_id), None)
        
        if db_helper.update_service_request_status(request_id, 'rejected'):
            flash("Service request rejected.", "success")
            
            # Send notification to the user who submitted the request
            if service_request:
                notification_message = f"Your service request '{service_request['subject']}' has been rejected."
                add_notification(service_request['user_email'], notification_message, "error")
        else:
            flash("Error rejecting service request", "error")
    except Exception as e:
        print(f"Error rejecting service request: {e}")
        flash("Error rejecting service request", "error")
    
    return redirect(url_for("admin_service_requests"))

@app.route('/admin/service-requests/<int:request_id>/assign', methods=['POST'])
@admin_required
def assign_service_request(request_id):
    if "user" not in session or session.get('role') != 'admin':
        flash("Access denied. Admin privileges required.", "error")
        return redirect(url_for("dashboard"))
    
    assigned_to = request.form.get('assigned_to')
    if assigned_to:
        try:
            # Get service request details for notification
            service_requests = db_helper.get_all_service_requests()
            service_request = next((r for r in service_requests if r["id"] == request_id), None)
            
            if service_request:
                service_request['assigned_to'] = assigned_to
                service_request['assigned_date'] = datetime.now().strftime("%Y-%m-%d %H:%M")
                service_request['assigned_by'] = session["user"]
                
                flash(f"Service request assigned to {assigned_to} successfully!", "success")
                
                # Send notification to the assigned person
                add_notification(assigned_to, f"You have been assigned service request #{request_id}")
                
                # Send notification to the user who submitted the request
                if service_request:
                    notification_message = f"Your service request '{service_request['subject']}' has been assigned to {assigned_to}."
                    add_notification(service_request['user_email'], notification_message, "info")
            else:
                flash("Service request not found", "error")
        except Exception as e:
            print(f"Error assigning service request: {e}")
            flash("Error assigning service request", "error")
    else:
        flash("Please provide an assignee", "error")
    
    return redirect(url_for("admin_service_requests"))

@app.route('/admin/service-requests/<int:request_id>/update-status', methods=['POST'])
@admin_required
def update_service_request_status(request_id):
    if "user" not in session or session.get('role') != 'admin':
        flash("Access denied. Admin privileges required.", "error")
        return redirect(url_for("dashboard"))
    
    new_status = request.form.get('status')
    if new_status:
        try:
            # Get service request details for notification
            service_requests = db_helper.get_all_service_requests()
            service_request = next((r for r in service_requests if r["id"] == request_id), None)
            
            if db_helper.update_service_request_status(request_id, new_status):
                flash(f"Service request status updated to {new_status}", "success")
                
                # Send notification to the user who submitted the request
                if service_request:
                    notification_message = f"Your service request '{service_request['subject']}' status has been updated to {new_status}."
                    add_notification(service_request['user_email'], notification_message, "info")
            else:
                flash("Error updating service request status", "error")
        except Exception as e:
            print(f"Error updating service request status: {e}")
            flash("Error updating service request status", "error")
    
    return redirect(url_for("admin_service_requests"))

@app.route('/admin/service-requests/<int:request_id>/delete', methods=['POST'])
@admin_required
def delete_service_request(request_id):
    if "user" not in session or session.get('role') != 'admin':
        flash("Access denied. Admin privileges required.", "error")
        return redirect(url_for("dashboard"))
    
    try:
        if db_helper.delete_service_request(request_id):
            flash("Service request deleted successfully!", "success")
        else:
            flash("Error deleting service request", "error")
    except Exception as e:
        print(f"Error deleting service request: {e}")
        flash("Error deleting service request", "error")
    
    return redirect(url_for("admin_service_requests"))

@app.route('/admin/service-requests/<int:request_id>/comment', methods=['POST'])
@admin_required
def add_service_request_comment(request_id):
    if "user" not in session or session.get('role') != 'admin':
        flash("Access denied. Admin privileges required.", "error")
        return redirect(url_for("dashboard"))
    
    comment = request.form.get('comment')
    if comment:
        try:
            # Get service request details for notification
            service_requests = db_helper.get_all_service_requests()
            service_request = next((r for r in service_requests if r["id"] == request_id), None)
            
            if db_helper.add_service_request_comment(request_id, comment, session["user"]):
                flash("Comment added successfully!", "success")
                
                # Send notification to the user who submitted the request
                if service_request:
                    notification_message = f"A new comment has been added to your service request '{service_request['subject']}'."
                    add_notification(service_request['user_email'], notification_message, "info")
            else:
                flash("Error adding comment", "error")
        except Exception as e:
            print(f"Error adding comment: {e}")
            flash("Error adding comment", "error")
    
    return redirect(url_for("admin_view_service_request", request_id=request_id))

# Career Portal Routes
@app.route('/employee/careers/internal-jobs')
@employee_login_required
def internal_jobs():
    if "user" not in session:
        return redirect(url_for("employee_login"))
    
    # Use mock internal jobs data
    return render_template('employee_portal/internal_jobs.html', jobs=mock_internal_jobs)

@app.route('/employee/careers/internal-jobs/<int:job_id>')
@employee_login_required
def view_internal_job(job_id):
    if "user" not in session:
        return redirect(url_for("employee_login"))
    
    # Get specific internal job from mock data
    job = next((job for job in mock_internal_jobs if job['id'] == job_id), None)
    
    if not job:
        flash("Job not found", "error")
        return redirect(url_for("internal_jobs"))
    
    return render_template('employee_portal/internal_job_detail.html', job=job)

@app.route('/employee/careers/applications')
@login_required
def employee_careers_applications():
    if 'user' not in session:
        return redirect(url_for('employee_login'))
    
    # Get user's job applications
    user_applications = db_helper.get_user_internal_applications(session['user'])
    
    return render_template('employee_portal/careers_applications.html', applications=user_applications)

@app.route('/employee/careers/goals')
@login_required
def employee_careers_goals():
    if 'user' not in session:
        return redirect(url_for('employee_login'))
    
    # For now, return empty goals list - can be expanded later
    goals = []
    
    return render_template('employee_portal/careers_goals.html', goals=goals)

@app.route('/employee/careers/skills-test')
@employee_login_required
def skills_test():
    """Skills assessment test page"""
    return render_template('employee_portal/skills_test.html')

@app.route('/test-skills-include')
@login_required
def test_skills_include():
    """Test skills assessment template inclusion"""
    return render_template('employee_portal/test_skills_include.html')

@app.route('/employee/careers/learning-roadmap')
@employee_login_required
def learning_roadmap():
    """Learning roadmap page"""
    # Get user's latest assessment result
    assessment_result = db_helper.get_latest_skills_assessment(session["user"])
    
    if assessment_result:
        # Parse the assessment data
        answers = json.loads(assessment_result['answers']) if isinstance(assessment_result['answers'], str) else assessment_result['answers']
        
        # Calculate skill level based on score
        percentage = (assessment_result['score'] / assessment_result['total_questions']) * 100
        if percentage >= 90:
            skill_level = "Expert"
        elif percentage >= 70:
            skill_level = "Advanced"
        elif percentage >= 50:
            skill_level = "Intermediate"
        else:
            skill_level = "Beginner"
        
        # Determine strengths and improvement areas based on score
        if percentage >= 80:
            strengths = ["Programming Fundamentals", "Problem Solving", "Technical Knowledge"]
            improvement_areas = ["Advanced Concepts", "Specialized Skills"]
        elif percentage >= 60:
            strengths = ["Basic Programming", "Logical Thinking"]
            improvement_areas = ["Advanced Programming", "Web Technologies", "Database Concepts"]
        else:
            strengths = ["Learning Potential"]
            improvement_areas = ["Programming Fundamentals", "Basic Computer Science", "Web Development"]
        
        # Create learning roadmap data
        roadmap_data = {
            'score': assessment_result['score'],
            'total_questions': assessment_result['total_questions'],
            'percentage': percentage,
            'skill_level': skill_level,
            'strengths': strengths,
            'improvement_areas': improvement_areas,
            'phase1_duration': 4,
            'phase2_duration': 6,
            'phase3_duration': 8,
            'phase1_courses': [
                {
                    'title': 'Programming Fundamentals',
                    'description': 'Learn core programming concepts and best practices',
                    'duration': '4 weeks',
                    'provider': 'Coursera',
                    'url': '#'
                },
                {
                    'title': 'Web Development Basics',
                    'description': 'Master HTML, CSS, and JavaScript fundamentals',
                    'duration': '6 weeks',
                    'provider': 'Udemy',
                    'url': '#'
                }
            ],
            'phase2_courses': [
                {
                    'title': 'Advanced JavaScript',
                    'description': 'Deep dive into modern JavaScript features',
                    'duration': '8 weeks',
                    'provider': 'LinkedIn Learning',
                    'url': '#'
                },
                {
                    'title': 'Database Design',
                    'description': 'Learn SQL and database management',
                    'duration': '6 weeks',
                    'provider': 'edX',
                    'url': '#'
                }
            ],
            'phase3_courses': [
                {
                    'title': 'Full-Stack Development',
                    'description': 'Build complete web applications',
                    'duration': '12 weeks',
                    'provider': 'Coursera',
                    'url': '#'
                },
                {
                    'title': 'Cloud Computing',
                    'description': 'Master AWS, Azure, or Google Cloud',
                    'duration': '10 weeks',
                    'provider': 'AWS Training',
                    'url': '#'
                }
            ]
        }
        
        # Mock progress data
        progress = {
            'completed_courses': 3,
            'total_hours': 24,
            'certificates_earned': 2,
            'overall_percentage': 35
        }
        
        return render_template('employee_portal/learning_roadmap.html', 
                             assessment_result=roadmap_data, 
                             progress=progress,
                             assessment_date=assessment_result['completed_at'].strftime('%B %d, %Y') if assessment_result['completed_at'] else None)
    else:
        return render_template('employee_portal/learning_roadmap.html', 
                             assessment_result=None, 
                             progress=None,
                             assessment_date=None)

@app.route('/employee/careers/submit-skills-test', methods=['POST'])
@login_required
def submit_skills_test():
    """Submit skills assessment test"""
    try:
        # Get answers from form
        answers = {
            'q1': request.form.get('q1'),
            'q2': request.form.get('q2'),
            'q3': request.form.get('q3'),
            'q4': request.form.get('q4'),
            'q5': request.form.get('q5'),
            'q6': request.form.get('q6'),
            'q7': request.form.get('q7'),
            'q8': request.form.get('q8'),
            'q9': request.form.get('q9'),
            'q10': request.form.get('q10')
        }
        
        # Correct answers
        correct_answers = {
            'q1': 'b',  # Version control tracks changes and collaborates
            'q2': 'b',  # Object-oriented programming emphasizes objects and classes
            'q3': 'b',  # Database provides better data integrity and query capabilities
            'q4': 'b',  # API enables communication between different software systems
            'q5': 'b',  # Agile delivers value incrementally and responds to change
            'q6': 'b',  # HTTPS encrypts data transmission for security
            'q7': 'b',  # Unit testing tests individual functions in isolation
            'q8': 'b',  # Cloud computing provides scalability and reduced infrastructure costs
            'q9': 'b',  # Sprint delivers a working increment of the product
            'q10': 'b'  # Data visualization communicates insights and patterns effectively
        }
        
        # Calculate score
        score = 0
        total_questions = len(correct_answers)
        
        for question, user_answer in answers.items():
            if user_answer == correct_answers[question]:
                score += 1
        
        percentage = (score / total_questions) * 100
        
        # Save to database
        db_helper.create_skills_assessment(
            user_email=session["user"],
            test_type="comprehensive",
            score=score,
            total_questions=total_questions,
            answers=json.dumps(answers),
            completed_at=datetime.now()
        )
        
        flash(f"Skills assessment completed! Your score: {score}/{total_questions} ({percentage:.1f}%)", "success")
        return redirect(url_for('learning_roadmap'))
        
    except Exception as e:
        print(f"Error submitting skills test: {e}")
        flash("Error submitting skills test. Please try again.", "error")
        return redirect(url_for('skills_test'))

@app.route('/employee/careers/submit-course-quiz', methods=['POST'])
@login_required
def submit_course_quiz():
    """Submit course quiz"""
    try:
        course_id = request.form.get('course_id')
        answers = request.form.getlist('answers[]')
        
        # Get course details
        course = db_helper.get_course_by_id(course_id)
        if not course:
            flash("Course not found.", "error")
            return redirect(url_for('employee_learning'))
        
        # Parse questions from JSON
        questions = json.loads(course['questions']) if isinstance(course['questions'], str) else course['questions']
        
        # Calculate score
        score = 0
        total_questions = len(questions)
        
        for i, answer in enumerate(answers):
            if i < len(questions) and int(answer) == questions[i]['correct_answer']:
                score += 1
        
        percentage = (score / total_questions) * 100
        passed = percentage >= course['passing_score']
        
        # Save quiz result
        db_helper.save_quiz_result(
            user_email=session["user"],
            course_id=course_id,
            score=score,
            total_questions=total_questions,
            percentage=percentage,
            passed=passed
        )
        
        if passed:
            flash(f"Congratulations! You passed the quiz with {score}/{total_questions} ({percentage:.1f}%)", "success")
        else:
            flash(f"Quiz completed. Your score: {score}/{total_questions} ({percentage:.1f}%). Passing score was {course['passing_score']}%", "warning")
        
        return redirect(url_for('employee_learning'))
        
    except Exception as e:
        print(f"Error submitting course quiz: {e}")
        flash("Error submitting quiz. Please try again.", "error")
        return redirect(url_for('employee_learning'))

@app.route('/employee/careers/internal-jobs/<int:job_id>/apply', methods=['GET', 'POST'])
@login_required
def apply_internal_job(job_id):
    if "user" not in session:
        return redirect(url_for("employee_login"))
    
    # Get job details from mock data
    job = next((job for job in mock_internal_jobs if job['id'] == job_id), None)
    
    if not job:
        flash("Job not found.", "error")
        return redirect(url_for("internal_jobs"))
    
    if request.method == 'POST':
        resume_path = None
        cover_letter = request.form.get('cover_letter')
        
        # Handle resume upload
        if 'resume' in request.files:
            file = request.files['resume']
            if file and file.filename:
                filename = secure_filename(file.filename)
                # Save file to uploads directory
                upload_dir = os.path.join(app.static_folder, 'uploads', 'resumes')
                os.makedirs(upload_dir, exist_ok=True)
                file_path = os.path.join(upload_dir, f"{session['user']}_{job_id}_{filename}")
                file.save(file_path)
                resume_path = file_path
        
        # Save application to database
        application_id = db_helper.apply_for_internal_job(
            job_id=job_id,
            user_email=session['user'],
            resume_path=resume_path,
            cover_letter=cover_letter
        )
        
        if application_id:
            flash(f"Application submitted successfully for {job['title']}!", "success")
            # Add notification
            add_notification(
                session['user'],
                f"Your application for {job['title']} has been submitted and is under review.",
                "success"
            )
        else:
            flash("Error submitting application. Please try again.", "error")
        
        return redirect(url_for("employee_careers_applications"))
    
    # GET request - redirect to job detail page
    return redirect(url_for("view_internal_job", job_id=job_id))

# Add bulk actions for tickets
@app.route('/admin/tickets/bulk-action', methods=['POST'])
@admin_required
def bulk_action_tickets():
    action = request.form.get('action')
    selected_tickets = request.form.getlist('selected_tickets')
    
    if not selected_tickets:
        flash('No tickets selected for bulk action', 'error')
        return redirect(url_for('admin_tickets'))
    
    success_count = 0
    for ticket_id in selected_tickets:
        ticket_id = int(ticket_id)
        ticket = next((t for t in tickets if t['id'] == ticket_id), None)
        
        if ticket:
            if action == 'approve':
                ticket['status'] = 'resolved'
                success_count += 1
            elif action == 'reject':
                ticket['status'] = 'closed'
                success_count += 1
            elif action == 'assign':
                assigned_to = request.form.get('assigned_to')
                if assigned_to:
                    ticket['assigned_to'] = assigned_to
                    success_count += 1
            elif action == 'delete':
                tickets.remove(ticket)
                success_count += 1
    
    flash(f'Bulk action completed: {success_count} tickets processed', 'success')
    return redirect(url_for('admin_tickets'))

# Add bulk actions for service requests
@app.route('/admin/service-requests/bulk-action', methods=['POST'])
@admin_required
def bulk_action_service_requests():
    action = request.form.get('action')
    selected_requests = request.form.getlist('selected_requests')
    
    if not selected_requests:
        flash('No service requests selected for bulk action', 'error')
        return redirect(url_for('admin_service_requests'))
    
    success_count = 0
    for request_id in selected_requests:
        request_id = int(request_id)
        
        if action == 'approve':
            if db_helper.update_service_request_status(request_id, 'completed'):
                success_count += 1
        elif action == 'reject':
            if db_helper.update_service_request_status(request_id, 'rejected'):
                success_count += 1
        elif action == 'assign':
            assigned_to = request.form.get('assigned_to')
            if assigned_to and db_helper.assign_service_request(request_id, assigned_to):
                success_count += 1
        elif action == 'delete':
            if db_helper.delete_service_request(request_id):
                success_count += 1
    
    flash(f'Bulk action completed: {success_count} service requests processed', 'success')
    return redirect(url_for('admin_service_requests'))

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5001)