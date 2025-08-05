from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from datetime import datetime
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

# Initialize AI Models
if AI_DEPENDENCIES_AVAILABLE:
    try:
        # ATS Model
        sbert_model = SentenceTransformer('all-MiniLM-L6-v2')
        tfidf_vectorizer = TfidfVectorizer(stop_words="english")
        ats_initialized = True
        
        # RAG Setup
        try:
            df = pd.read_csv("rag.csv")
            documents = [
                Document(page_content=f"Topic: {row['ki_topic']}\n{row['ki_text']}")
                for _, row in df.iterrows()
            ]
            splitter = CharacterTextSplitter(chunk_size=800, chunk_overlap=100)
            chunks = splitter.split_documents(documents)
            
            # Azure credentials for RAG
            chat_api_key = os.getenv("AZURE_OPENAI_API_KEY_CHAT")
            chat_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT_CHAT")
            chat_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_CHAT")
            embed_api_key = os.getenv("AZURE_OPENAI_API_KEY_EMBED")
            embed_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT_EMBED")
            embed_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_EMBED")
            azure_search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
            azure_search_key = os.getenv("AZURE_SEARCH_ADMIN_KEY")
            azure_index_name = os.getenv("AZURE_SEARCH_INDEX_NAME")
            
            # Initialize RAG components if credentials are available
            if all([chat_api_key, chat_endpoint, chat_deployment, embed_api_key, embed_endpoint, embed_deployment, azure_search_endpoint, azure_search_key, azure_index_name]):
                embedding_model = AzureOpenAIEmbeddings(
                    azure_endpoint=embed_endpoint,
                    api_key=embed_api_key,
                    deployment=embed_deployment,
                    api_version="2025-01-01-preview",
                    chunk_size=1000
                )
                
                vectorstore = AzureSearch.from_documents(
                    documents=chunks,
                    embedding=embedding_model,
                    azure_search_endpoint=azure_search_endpoint,
                    azure_search_key=azure_search_key,
                    index_name=azure_index_name
                )
                
                system_prompt = (
                    "You are Enplify Assistant, a helpful AI that responds only with information available in the provided documents. "
                    "If someone says hello or thank you, respond politely. If the question is unrelated, respond with: "
                    "'I'm trained only to answer Enplify.ai-related questions 😊'"
                )
                
                prompt = ChatPromptTemplate.from_messages([
                    SystemMessagePromptTemplate.from_template(system_prompt),
                    HumanMessagePromptTemplate.from_template("{question}")
                ])
                
                llm = AzureChatOpenAI(
                    azure_endpoint=chat_endpoint,
                    api_key=chat_api_key,
                    deployment_name=chat_deployment,
                    api_version="2025-01-01-preview",
                    temperature=0
                )
                
                qa_chain = ConversationalRetrievalChain.from_llm(
                    llm=llm,
                    retriever=vectorstore.as_retriever(),
                    condense_question_prompt=prompt
                )
                
                rag_initialized = True
                chat_history = []
            else:
                rag_initialized = False
                print("RAG not initialized - missing Azure credentials")
        except Exception as rag_error:
            rag_initialized = False
            print(f"RAG initialization error: {rag_error}")
            
    except Exception as e:
        print(f"AI models initialization error: {e}")
        ats_initialized = False
        rag_initialized = False
else:
    ats_initialized = False
    rag_initialized = False

# ATS Functions
def pdf_contains_large_images(pdf_path, min_pixel_area=10000): 
    if not AI_DEPENDENCIES_AVAILABLE:
        raise Exception("AI dependencies not available")
    doc = fitz.open(pdf_path)
    for page in doc:
        for img in page.get_images(full=True):
            xref = img[0]
            base_image = doc.extract_image(xref)
            if base_image["width"] * base_image["height"] > min_pixel_area:
                return True
    return False

def extract_resume_text(pdf_path):
    if not AI_DEPENDENCIES_AVAILABLE:
        raise Exception("AI dependencies not available")
    if pdf_contains_large_images(pdf_path):
        return None
    text = extract_text(pdf_path)
    return text.strip() if len(text.strip()) > 100 else None

def compute_sbert_similarity(resume_text, job_description):
    if not ats_initialized:
        raise Exception("ATS system not initialized")
    embeddings = sbert_model.encode([resume_text, job_description], convert_to_tensor=True)
    score = cosine_similarity([embeddings[0].cpu().numpy()], [embeddings[1].cpu().numpy()])[0][0]
    return round(float(score) * 100, 2)

def compute_tfidf_similarity(resume_texts, job_description):
    if not ats_initialized:
        raise Exception("ATS system not initialized")
    documents = resume_texts + [job_description]
    matrix = tfidf_vectorizer.fit_transform(documents)
    job_vector = matrix[-1]
    resume_vectors = matrix[:-1]
    return [round(float(score) * 100, 2) for score in cosine_similarity(resume_vectors, job_vector).flatten()]

# Dummy data stores
mock_user = {"email": "user@example.com", "password": "password123"}
mock_admin = {"email": "admin@example.com", "password": "admin123"}

user_profiles = {
    "user@example.com": {
        "name": "John Doe",
        "email": "user@example.com",
        "department": "Engineering",
        "role": "user"
    },
    "admin@example.com": {
        "name": "Admin User",
        "email": "admin@example.com",
        "department": "IT",
        "role": "admin"
    }
}

tickets = [
    {"id": 1, "title": "Printer not connecting", "priority": "high", "status": "open", "date": "2025-07-18", "description": "Printer shows offline status", "user_email": "user@example.com", "attachments": []},
    {"id": 2, "title": "VPN Login Failure", "priority": "medium", "status": "pending", "date": "2025-07-19", "description": "Cannot connect to VPN", "user_email": "user@example.com", "attachments": []}
]

comments = {
    1: [{"author": "Alice", "message": "I tried rebooting it.", "timestamp": "2025-07-18 09:45", "author_type": "user"},
        {"author": "IT Staff", "message": "We're investigating this now.", "timestamp": "2025-07-18 10:15", "author_type": "admin"}],
    2: []
}

requests_data = [
    {"id": 1, "type": "hardware", "subject": "Need a new mouse", "description": "Mouse disconnecting.",
     "status": "pending", "submitted_by": "user@example.com", "hr_comment": "We'll issue one next week.", "attachments": []}
]

notifications = []

# In-memory timesheets tracking
timesheets = []

# In-memory leave tracking
leave_requests = []
leave_types = [
    'Vacation',
    'Sick Leave',
    'Personal Leave',
    'Bereavement',
    'Maternity/Paternity',
    'Military Leave',
    'Other'
]

# In-memory device tracking (simulate for demo)
devices = [
    {
        'id': 1,
        'name': 'Dell XPS 13',
        'type': 'Laptop',
        'assigned_to': 'employee1@example.com',
        'status': 'lent',
        'lent_date': '2025-07-01',
        'return_date': '',
        'notes': 'For remote work'
    },
    {
        'id': 2,
        'name': 'iPhone 13',
        'type': 'Phone',
        'assigned_to': '',
        'status': 'available',
        'lent_date': '',
        'return_date': '',
        'notes': ''
    }
]

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def send_email_notification(to_email, subject, message):
    """Send email notification (placeholder for production)"""
    # In production, configure SMTP settings
    print(f"Email to {to_email}: {subject} - {message}")
    return True

def add_notification(user_email, message, notification_type="info"):
    """Add notification to the system"""
    notification = {
        "id": len(notifications) + 1,
        "user_email": user_email,
        "message": message,
        "type": notification_type,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "read": False
    }
    notifications.append(notification)

@app.route("/")
def home():
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        
        # Check admin login
        if email == mock_admin["email"] and password == mock_admin["password"]:
            session["user"] = email
            session["role"] = "admin"
            flash("Logged in successfully as Admin!", "success")
            return redirect(url_for("admin_dashboard"))
        
        # Check regular user login
        elif email == mock_user["email"] and password == mock_user["password"]:
            session["user"] = email
            session["role"] = "user"
            flash("Logged in successfully!", "success")
            return redirect(url_for("dashboard"))
        
        flash("Invalid credentials", "error")
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
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))
    
    if session.get("role") == "admin":
        return redirect(url_for("admin_dashboard"))
    
    dashboard_data = {
        "open_tickets": len([t for t in tickets if t["status"] == "open" and t["user_email"] == session["user"]]),
        "resolved_tickets": len([t for t in tickets if t["status"] == "resolved" and t["user_email"] == session["user"]]),
        "avg_resolution_time": "2.1 hrs",
        "system_status": [
            {"service": "Email Server", "status": "🟢 Operational"},
            {"service": "VPN Gateway", "status": "🟢 Operational"},
            {"service": "Printer Network", "status": "🟡 Degraded"},
            {"service": "Remote Desktop", "status": "🔴 Down"},
        ]
    }
    return render_template("dashboard.html", **dashboard_data)

@app.route("/admin/dashboard")
def admin_dashboard():
    if "user" not in session or session.get("role") != "admin":
        return redirect(url_for("login"))
    
    admin_data = {
        "total_tickets": len(tickets),
        "open_tickets": len([t for t in tickets if t["status"] == "open"]),
        "resolved_tickets": len([t for t in tickets if t["status"] == "resolved"]),
        "total_requests": len(requests_data),
        "pending_requests": len([r for r in requests_data if r["status"] == "pending"]),
        "total_users": len(user_profiles),
        "recent_tickets": tickets[-5:] if len(tickets) > 5 else tickets,
        "recent_requests": requests_data[-5:] if len(requests_data) > 5 else requests_data
    }
    return render_template("admin_dashboard.html", **admin_data)

@app.route("/admin/tickets")
def admin_tickets():
    if "user" not in session or session.get("role") != "admin":
        return redirect(url_for("login"))
    
    # Get filter parameters
    status_filter = request.args.get("status", "")
    priority_filter = request.args.get("priority", "")
    search_query = request.args.get("search", "")
    
    filtered_tickets = tickets
    
    if status_filter:
        filtered_tickets = [t for t in filtered_tickets if t["status"] == status_filter]
    
    if priority_filter:
        filtered_tickets = [t for t in filtered_tickets if t["priority"] == priority_filter]
    
    if search_query:
        filtered_tickets = [t for t in filtered_tickets if search_query.lower() in t["title"].lower() or search_query.lower() in t.get("description", "").lower()]
    
    return render_template("admin_tickets.html", tickets=filtered_tickets)

@app.route("/admin/requests")
def admin_requests():
    if "user" not in session or session.get("role") != "admin":
        return redirect(url_for("login"))
    
    # Get filter parameters
    status_filter = request.args.get("status", "")
    type_filter = request.args.get("type", "")
    search_query = request.args.get("search", "")
    
    filtered_requests = requests_data
    
    if status_filter:
        filtered_requests = [r for r in filtered_requests if r["status"] == status_filter]
    
    if type_filter:
        filtered_requests = [r for r in filtered_requests if r["type"] == type_filter]
    
    if search_query:
        filtered_requests = [r for r in filtered_requests if search_query.lower() in r["subject"].lower() or search_query.lower() in r.get("description", "").lower()]
    
    return render_template("admin_requests.html", requests=filtered_requests)

@app.route("/admin/update-ticket-status/<int:ticket_id>", methods=["POST"])
def update_ticket_status(ticket_id):
    if "user" not in session or session.get("role") != "admin":
        return redirect(url_for("login"))
    
    new_status = request.form["status"]
    ticket = next((t for t in tickets if t["id"] == ticket_id), None)
    
    if ticket:
        old_status = ticket["status"]
        ticket["status"] = new_status
        
        # Add notification
        add_notification(ticket["user_email"], f"Your ticket '{ticket['title']}' status changed from {old_status} to {new_status}")
        
        # Send email notification
        send_email_notification(ticket["user_email"], "Ticket Status Updated", 
                              f"Your ticket '{ticket['title']}' status has been updated to {new_status}")
        
        flash(f"Ticket status updated to {new_status}", "success")
    
    return redirect(url_for("admin_tickets"))

@app.route("/admin/update-request-status/<int:request_id>", methods=["POST"])
def update_request_status(request_id):
    if "user" not in session or session.get("role") != "admin":
        return redirect(url_for("login"))
    
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
def add_hr_comment(request_id):
    if "user" not in session or session.get("role") != "admin":
        return redirect(url_for("login"))
    
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
def admin_timeoff():
    if "user" not in session or session.get("role") != "admin":
        return redirect(url_for("login"))
    
    # Get all time off requests
    all_timeoff = timeoff_requests if 'timeoff_requests' in globals() else []
    return render_template("admin_timeoff.html", timeoff_requests=all_timeoff)

@app.route("/admin/leave")
def admin_leave():
    if "user" not in session or session.get("role") != "admin":
        return redirect(url_for("login"))
    
    # Get all leave requests
    all_leaves = leave_requests if 'leave_requests' in globals() else []
    return render_template("admin_leave.html", leave_requests=all_leaves)

@app.route("/admin/applications")
def admin_applications():
    if "user" not in session or session.get("role") != "admin":
        return redirect(url_for("login"))
    
    # Get all job applications
    all_applications = job_applications if 'job_applications' in globals() else []
    return render_template("admin_applications.html", applications=all_applications)

@app.route("/admin/badges")
def admin_badges():
    if "user" not in session or session.get("role") != "admin":
        return redirect(url_for("login"))
    
    # Get all badges and users
    all_badges = badges if 'badges' in globals() else []
    all_users = users if 'users' in globals() else []
    return render_template("admin_badges.html", badges=all_badges, users=all_users)

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
def admin_employees():
    if 'user' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
    
    # Get search parameters
    search = request.args.get('search', '').lower()
    department = request.args.get('department', '')
    status = request.args.get('status', '')
    
    # Filter employees
    filtered_employees = employee_directory
    
    if search:
        filtered_employees = [e for e in filtered_employees if 
                           search in e['name'].lower() or 
                           search in e['email'].lower() or 
                           search in e['employee_id'].lower()]
    
    if department:
        filtered_employees = [e for e in filtered_employees if e['department'] == department]
    
    if status:
        filtered_employees = [e for e in filtered_employees if e['status'] == status]
    
    # Get unique departments for filter
    departments = list(set([e['department'] for e in employee_directory]))
    
    return render_template('admin_employees.html', 
                         employees=filtered_employees,
                         departments=departments,
                         search=search,
                         selected_department=department,
                         selected_status=status)

@app.route('/admin/employees/<int:employee_id>')
def view_employee(employee_id):
    if 'user' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
    
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
def add_employee():
    if 'user' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
    
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
def edit_employee(employee_id):
    if 'user' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
    
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
def update_timeoff_status(timeoff_id):
    if "user" not in session or session.get("role") != "admin":
        return redirect(url_for("login"))
    
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
def update_leave_status(leave_id):
    if "user" not in session or session.get("role") != "admin":
        return redirect(url_for("login"))
    
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
        add_notification(leave_item["employee_email"], 
                        f"Your leave request has been {new_status}: {leave_item['leave_type']}")
        
        flash(f"Leave request {new_status}.", "success")
    
    return redirect(url_for("admin_leave"))

# Update application status
@app.route("/admin/update-application-status/<int:app_id>", methods=["POST"])
def update_general_application_status(app_id):
    if "user" not in session or session.get("role") != "admin":
        return redirect(url_for("login"))
    
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
def assign_badge(user_id):
    if "user" not in session or session.get("role") != "admin":
        return redirect(url_for("login"))
    
    user = next((u for u in users if u["id"] == user_id), None)
    if not user:
        flash("User not found.", "error")
        return redirect(url_for("admin_badges"))
    
    badge_name = request.form.get("badge_name")
    badge_reason = request.form.get("badge_reason", "")
    
    if badge_name:
        user["badges"] = user.get("badges", [])
        user["badges"].append({
            "name": badge_name,
            "assigned_by": session["user"],
            "assigned_date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "reason": badge_reason
        })
        
        # Add notification for user
        add_notification(user["email"], f"You've been awarded the '{badge_name}' badge!")
        
        flash(f"Badge '{badge_name}' assigned to {user['name']}.", "success")
    
    return redirect(url_for("admin_badges"))

@app.route('/tickets')
def view_tickets():
    if "user" not in session:
        return redirect(url_for("login"))
    
    if session.get("role") == "admin":
        return redirect(url_for("admin_tickets"))

    user_tickets = [t for t in tickets if t["user_email"] == session["user"]]
    return render_template("tickets.html", tickets=user_tickets)

@app.route("/submit-ticket", methods=["GET", "POST"])
def submit_ticket():
    if "user" not in session:
        return redirect(url_for("login"))
    
    if request.method == "POST":
        new_ticket = {
            "id": len(tickets) + 1,
            "title": request.form["title"],
            "priority": request.form["priority"],
            "status": "open",
            "date": request.form["date"],
            "description": request.form.get("description", ""),
            "user_email": session["user"],
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
                    new_ticket["attachments"].append(filename)
        
        tickets.append(new_ticket)
        
        # Add notification for admin
        add_notification("admin@example.com", f"New ticket submitted: {new_ticket['title']}", "warning")
        
        flash("Ticket submitted!", "success")
        return redirect(url_for("view_tickets"))
    
    return render_template("submit_ticket.html")

@app.route("/ticket/<int:ticket_id>")
def ticket_detail(ticket_id):
    if "user" not in session:
        return redirect(url_for("login"))
    
    ticket = next((t for t in tickets if t["id"] == ticket_id), None)
    if not ticket:
        flash("Not found.", "error")
        return redirect(url_for("view_tickets"))
    
    # Check if user can view this ticket
    if session.get("role") != "admin" and ticket["user_email"] != session["user"]:
        flash("Access denied.", "error")
        return redirect(url_for("view_tickets"))
    
    return render_template("ticket_details.html", ticket=ticket, comments=comments.get(ticket_id, []))

@app.route("/ticket/<int:ticket_id>/comment", methods=["POST"])
def add_comment(ticket_id):
    if "user" not in session:
        return redirect(url_for("login"))
    
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
def submit_request():
    if "user" not in session:
        return redirect(url_for("login"))
    
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
def request_history():
    if "user" not in session:
        return redirect(url_for("login"))
    
    if session.get("role") == "admin":
        return redirect(url_for("admin_requests"))
    
    user_requests = [r for r in requests_data if r["submitted_by"] == session["user"]]
    return render_template("request_history.html", requests=user_requests)

@app.route("/cancel-request/<int:req_id>", methods=["POST"])
def cancel_request(req_id):
    if "user" not in session:
        return redirect(url_for("login"))
    
    for r in requests_data:
        if r["id"] == req_id and (r["submitted_by"] == session["user"] or session.get("role") == "admin"):
            r["status"] = "cancelled"
            break
    
    flash("Request cancelled.", "info")
    return redirect(url_for("request_history"))

@app.route("/notifications")
def view_notifications():
    if "user" not in session:
        return redirect(url_for("login"))
    
    user_notifications = [n for n in notifications if n["user_email"] == session["user"]]
    return render_template("notifications.html", notifications=user_notifications)

@app.route("/notifications/mark-read/<int:notification_id>", methods=["POST"])
def mark_notification_read(notification_id):
    if "user" not in session:
        return redirect(url_for("login"))
    
    notification = next((n for n in notifications if n["id"] == notification_id and n["user_email"] == session["user"]), None)
    if notification:
        notification["read"] = True
    
    return redirect(url_for("view_notifications"))

@app.route("/system-status")
def system_status():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("system_status.html", systems=[
        {"name": "Email Server", "description": "Handles mail.", "status": "Operational"},
        {"name": "VPN Gateway", "description": "Remote access", "status": "Operational"},
        {"name": "Printer Network", "description": "Print queue", "status": "Degraded"},
        {"name": "Remote Desktop", "description": "Virtual access", "status": "Down"},
    ])

@app.route("/faqs")
def faqs():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("faqs.html")

@app.route("/resources")
def resources():
    if "user" not in session:
        return redirect(url_for("login"))
    
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
def catalog():
    if "user" not in session:
        return redirect(url_for("login"))
    
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
        {'id': 1, 'name': 'Dell XPS 13', 'type': 'Laptop', 'assigned_to': 'employee1@example.com', 'status': 'lent', 'lent_date': '2025-07-01'},
        {'id': 2, 'name': 'iPhone 13', 'type': 'Phone', 'assigned_to': '', 'status': 'available', 'lent_date': ''},
        {'id': 3, 'name': 'MacBook Pro', 'type': 'Laptop', 'assigned_to': 'employee2@example.com', 'status': 'lent', 'lent_date': '2025-06-15'},
        {'id': 4, 'name': 'iPad Pro', 'type': 'Tablet', 'assigned_to': '', 'status': 'available', 'lent_date': ''}
    ]
    
    return render_template("catalog.html", software_catalog=software_catalog, devices=devices)

@app.route("/careers")
def careers():
    if "user" not in session:
        return redirect(url_for("login"))
    
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
def careers_applications():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("careers_applications.html")

@app.route("/careers/resume")
def careers_resume():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("careers_resume.html")

@app.route("/careers/upskilling")
def careers_upskilling():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("careers_upskilling.html")

@app.route("/careers/mentorship", methods=['GET', 'POST'])
def careers_mentorship():
    if "user" not in session:
        return redirect(url_for("login"))
    
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
def careers_saved():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("careers_saved.html")

@app.route("/careers/goals")
def careers_goals():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("careers_goals.html")

@app.route("/careers/badges")
def careers_badges():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("careers_badges.html")

@app.route("/careers/progress")
def careers_progress():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("careers_progress.html")

@app.route("/careers/resources")
def careers_resources():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("careers_resources.html")

@app.route("/careers/jobs")
def careers_jobs():
    if "user" not in session:
        return redirect(url_for("login"))
    
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
def careers_learning():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("careers_learning.html")

@app.route("/api/ai-assistant", methods=["POST"])
def ai_assistant():
    q = request.get_json().get("question", "").lower()
    responses = {
        "reset vpn": "Try disconnecting/reconnecting.",
        "email not working": "Try logging out/in.",
        "forgot password": "Click 'Forgot Password'.",
        "printer not working": "Try rebooting the printer."
    }
    for k in responses:
        if k in q:
            return jsonify({"answer": responses[k]})
    return jsonify({"answer": "Not sure. Please submit a ticket."})

@app.route('/devices', methods=['GET', 'POST'])
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
        
        # Use same credentials as IT portal
        if email == mock_user["email"] and password == mock_user["password"]:
            session['user'] = email
            session['role'] = 'employee'  # Set role as employee for employee portal
            flash('Welcome to Employee Portal!', 'success')
            return redirect(url_for('employee_dashboard'))
        elif email == mock_admin["email"] and password == mock_admin["password"]:
            session['user'] = email
            session['role'] = 'admin'
            flash('Welcome to Employee Portal!', 'success')
            return redirect(url_for('employee_dashboard'))
        else:
            flash('Invalid credentials. Try user@example.com / password or admin@example.com / password', 'error')
    
    return render_template('employee_portal/login.html')

@app.route('/employee/dashboard')
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
def employee_logout():
    session.pop('user', None)
    session.pop('role', None)
    flash('Logged out successfully', 'success')
    return redirect(url_for('employee_login'))

@app.route('/employee/timeoff', methods=['GET', 'POST'])
def employee_timeoff():
    if 'user' not in session:
        return redirect(url_for('employee_login'))
    
    if request.method == 'POST':
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        reason = request.form['reason']
        
        # Add to timeoff requests (mock)
        flash('Time off request submitted successfully!', 'success')
        return redirect(url_for('employee_timeoff'))
    
    return render_template('employee_portal/timeoff.html')

@app.route('/employee/paystubs')
def employee_paystubs():
    if 'user' not in session:
        return redirect(url_for('employee_login'))
    
    paystubs = [
        {'id': 1, 'period': 'January 2024', 'amount': 4500, 'date': '2024-01-31'},
        {'id': 2, 'period': 'December 2023', 'amount': 4500, 'date': '2023-12-31'},
        {'id': 3, 'period': 'November 2023', 'amount': 4500, 'date': '2023-11-30'}
    ]
    
    return render_template('employee_portal/paystubs.html', paystubs=paystubs)

@app.route('/employee/benefits')
def employee_benefits():
    if 'user' not in session:
        return redirect(url_for('employee_login'))
    
    benefits = [
        {'name': 'Health Insurance', 'status': 'Active', 'provider': 'Blue Cross'},
        {'name': 'Dental Insurance', 'status': 'Active', 'provider': 'Delta Dental'},
        {'name': '401(k) Retirement', 'status': 'Active', 'provider': 'Fidelity'},
        {'name': 'Life Insurance', 'status': 'Active', 'provider': 'MetLife'}
    ]
    
    return render_template('employee_portal/benefits.html', benefits=benefits)

@app.route('/employee/profile', methods=['GET', 'POST'])
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
def employee_careers():
    if 'user' not in session:
        return redirect(url_for('employee_login'))
    
    jobs = [
        {'id': 1, 'title': 'Senior Software Engineer', 'company': 'Tech Corp', 'location': 'Remote', 'type': 'Full-time'},
        {'id': 2, 'title': 'Product Manager', 'company': 'Innovation Inc', 'location': 'San Francisco', 'type': 'Full-time'},
        {'id': 3, 'title': 'Data Scientist', 'company': 'Analytics Co', 'location': 'New York', 'type': 'Full-time'}
    ]
    
    return render_template('employee_portal/careers.html', jobs=jobs)

@app.route('/employee/leave', methods=['GET', 'POST'])
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
            # Calculate total days
            start = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d')
            total_days = (end - start).days + 1
            
            leave_id = len(leave_requests) + 1
            new_leave = {
                'id': leave_id,
                'employee_id': user_id,
                'employee_name': session['user'],
                'leave_type': leave_type,
                'start_date': start_date,
                'end_date': end_date,
                'total_days': total_days,
                'reason': reason,
                'status': 'pending',
                'submitted_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'approved_by': None,
                'approved_at': None,
                'notes': ''
            }
            leave_requests.append(new_leave)
            flash('Leave request submitted successfully!', 'success')
            return redirect(url_for('employee_leave'))
    
    # Get employee's leave requests
    employee_leaves = [l for l in leave_requests if l['employee_id'] == user_id]
    
    return render_template('employee_portal/leave.html', 
                         leave_requests=employee_leaves,
                         leave_types=leave_types,
                         user=session['user'])

@app.route('/employee/leave/<int:leave_id>')
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
def employee_timesheet():
    if 'user' not in session:
        return redirect(url_for('employee_login'))
    
    if request.method == 'POST':
        date = request.form.get('date')
        hours_worked = float(request.form.get('hours_worked', 0))
        project = request.form.get('project')
        task_description = request.form.get('task_description')
        
        if date and hours_worked > 0:
            timesheet_id = len(timesheets) + 1
            new_timesheet = {
                'id': timesheet_id,
                'employee_id': session['user'],
                'employee_name': session['user'],
                'date': date,
                'hours_worked': hours_worked,
                'project': project,
                'task_description': task_description,
                'status': 'pending',
                'submitted_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            timesheets.append(new_timesheet)
            flash('Timesheet submitted successfully!', 'success')
            return redirect(url_for('employee_timesheet'))
    
    # Get employee's timesheets
    employee_timesheets = [ts for ts in timesheets if ts['employee_id'] == session['user']]
    return render_template('employee_portal/timesheet.html', timesheets=employee_timesheets)

# Anonymous Feedback Data Structure
anonymous_feedback = []

@app.route('/employee/feedback', methods=['GET', 'POST'])
def employee_feedback():
    if 'user' not in session:
        return redirect(url_for('employee_login'))
    
    if request.method == 'POST':
        feedback_type = request.form.get('feedback_type')
        feedback_text = request.form.get('feedback_text')
        department = request.form.get('department')
        priority = request.form.get('priority')
        
        if feedback_text.strip():
            feedback_id = len(anonymous_feedback) + 1
            new_feedback = {
                'id': feedback_id,
                'type': feedback_type,
                'text': feedback_text,
                'department': department,
                'priority': priority,
                'status': 'pending',
                'submitted_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'anonymous': True
            }
            anonymous_feedback.append(new_feedback)
            flash('Anonymous feedback submitted successfully!', 'success')
            return redirect(url_for('employee_feedback'))
    
    return render_template('employee_portal/feedback.html')

@app.route('/admin/feedback')
def admin_feedback():
    if 'user' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
    
    return render_template('admin_feedback.html', feedback_list=anonymous_feedback)

@app.route('/admin/feedback/update-status/<int:feedback_id>', methods=['POST'])
def update_feedback_status(feedback_id):
    if 'user' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
    
    new_status = request.form.get('status')
    for feedback in anonymous_feedback:
        if feedback['id'] == feedback_id:
            feedback['status'] = new_status
            flash(f'Feedback status updated to {new_status}', 'success')
            break
    
    return redirect(url_for('admin_feedback'))

@app.route('/employee/complimentary')
def employee_complimentary():
    if 'user' not in session:
        return redirect(url_for('employee_login'))
    return render_template('employee_portal/complimentary.html')

# AI Integration Routes

@app.route("/ai/ats", methods=["GET", "POST"])
def ats_interface():
    if "user" not in session:
        return redirect(url_for("login"))
    
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
def rag_interface():
    if "user" not in session:
        return redirect(url_for("login"))
    
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
        'category': 'Business',
        'questions': [
            {
                'id': 1,
                'question': 'What is the purpose of data visualization?',
                'options': [
                    'To make data look pretty',
                    'To communicate insights clearly',
                    'To hide important information',
                    'To complicate simple data'
                ],
                'correct_answer': 1,
                'explanation': 'Data visualization helps communicate insights clearly and effectively.'
            },
            {
                'id': 2,
                'question': 'Which chart type is best for showing trends over time?',
                'options': [
                    'Pie chart',
                    'Bar chart',
                    'Line chart',
                    'Scatter plot'
                ],
                'correct_answer': 2,
                'explanation': 'Line charts are ideal for showing trends and changes over time.'
            }
        ],
        'badge': 'Data Analyst',
        'passing_score': 80
    }
]

user_progress = {}  # Store user progress and completed courses
user_badges = {}    # Store user badges

@app.route('/employee/careers/learning', methods=['GET', 'POST'])
def employee_learning():
    if 'user' not in session:
        return redirect(url_for('employee_login'))
    
    user_id = session['user']
    
    if request.method == 'POST':
        course_id = int(request.form.get('course_id'))
        answers = request.form.getlist('answers[]')
        
        # Find the course
        course = next((c for c in courses if c['id'] == course_id), None)
        if course:
            # Calculate score
            correct_answers = 0
            total_questions = len(course['questions'])
            
            for i, answer in enumerate(answers):
                if i < len(course['questions']):
                    if int(answer) == course['questions'][i]['correct_answer']:
                        correct_answers += 1
            
            score = (correct_answers / total_questions) * 100
            
            # Check if passed
            if score >= course['passing_score']:
                # Award badge
                if user_id not in user_badges:
                    user_badges[user_id] = []
                if course['badge'] not in user_badges[user_id]:
                    user_badges[user_id].append(course['badge'])
                
                # Mark course as completed
                if user_id not in user_progress:
                    user_progress[user_id] = {}
                user_progress[user_id][course_id] = {
                    'completed': True,
                    'score': score,
                    'completed_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                
                flash(f'Congratulations! You passed the course with {score:.1f}% and earned the "{course["badge"]}" badge!', 'success')
            else:
                flash(f'You scored {score:.1f}%. You need {course["passing_score"]}% to pass. Please try again.', 'error')
            
            return redirect(url_for('employee_learning'))
    
    # Get user's progress
    user_progress_data = user_progress.get(user_id, {})
    user_badges_data = user_badges.get(user_id, [])
    
    return render_template('employee_portal/learning.html', 
                         courses=courses, 
                         user_progress=user_progress_data,
                         user_badges=user_badges_data)

@app.route('/employee/careers/learning/course/<int:course_id>')
def take_course(course_id):
    if 'user' not in session:
        return redirect(url_for('employee_login'))
    
    course = next((c for c in courses if c['id'] == course_id), None)
    if not course:
        flash('Course not found!', 'error')
        return redirect(url_for('employee_learning'))
    
    return render_template('employee_portal/course_quiz.html', course=course)

@app.route('/admin/learning')
def admin_learning():
    if 'user' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
    
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

@app.route('/admin/learning/user/<int:user_id>')
def admin_user_learning_detail(user_id):
    if 'user' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
    
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
def admin_course_learning_detail(course_id):
    if 'user' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
    
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
def admin_badges_overview():
    if 'user' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
    
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
def admin_onboarding():
    if 'user' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
    
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
def view_onboarding(onboarding_id):
    if 'user' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
    
    onboarding = next((o for o in onboarding_employees if o['id'] == onboarding_id), None)
    if not onboarding:
        flash('Onboarding not found!', 'error')
        return redirect(url_for('admin_onboarding'))
    
    return render_template('admin_onboarding_detail.html', 
                         onboarding=onboarding,
                         tasks=onboarding_tasks)

@app.route('/admin/onboarding/<int:onboarding_id>/complete-task/<int:task_id>', methods=['POST'])
def complete_onboarding_task(onboarding_id, task_id):
    if 'user' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
    
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
def update_onboarding_status(onboarding_id):
    if 'user' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
    
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
        'employee_id': 1,
        'employee_name': 'John Doe',
        'period': 'January 2024',
        'pay_date': '2024-01-31',
        'gross_pay': 5000.00,
        'net_pay': 3750.00,
        'taxes': 1250.00,
        'benefits': 500.00,
        'hours_worked': 160,
        'overtime_hours': 8,
        'overtime_pay': 400.00,
        'status': 'paid'
    },
    {
        'id': 2,
        'employee_id': 1,
        'employee_name': 'John Doe',
        'period': 'December 2023',
        'pay_date': '2023-12-31',
        'gross_pay': 5000.00,
        'net_pay': 3750.00,
        'taxes': 1250.00,
        'benefits': 500.00,
        'hours_worked': 160,
        'overtime_hours': 0,
        'overtime_pay': 0.00,
        'status': 'paid'
    }
]

benefits = [
    {
        'id': 1,
        'name': 'Health Insurance',
        'type': 'Medical',
        'provider': 'Blue Cross Blue Shield',
        'coverage': 'Family',
        'monthly_cost': 200.00,
        'employer_contribution': 150.00,
        'employee_cost': 50.00,
        'status': 'active'
    },
    {
        'id': 2,
        'name': 'Dental Insurance',
        'type': 'Dental',
        'provider': 'Delta Dental',
        'coverage': 'Individual',
        'monthly_cost': 50.00,
        'employer_contribution': 30.00,
        'employee_cost': 20.00,
        'status': 'active'
    },
    {
        'id': 3,
        'name': 'Vision Insurance',
        'type': 'Vision',
        'provider': 'VSP',
        'coverage': 'Family',
        'monthly_cost': 25.00,
        'employer_contribution': 25.00,
        'employee_cost': 0.00,
        'status': 'active'
    },
    {
        'id': 4,
        'name': '401(k) Retirement Plan',
        'type': 'Retirement',
        'provider': 'Fidelity',
        'coverage': 'N/A',
        'monthly_cost': 0.00,
        'employer_contribution': 200.00,
        'employee_cost': 0.00,
        'status': 'active'
    }
]



@app.route('/employee/paystubs/<int:paystub_id>')
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
def admin_jobs():
    if 'user' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
    
    return render_template('admin_jobs.html', 
                         jobs=job_postings,
                         applications=job_applications)

@app.route('/admin/jobs/add', methods=['GET', 'POST'])
def add_job():
    if 'user' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        title = request.form.get('title')
        department = request.form.get('department')
        location = request.form.get('location')
        employment_type = request.form.get('employment_type')
        experience_level = request.form.get('experience_level')
        salary_range = request.form.get('salary_range')
        description = request.form.get('description')
        requirements = request.form.get('requirements', '').split('\n')
        benefits = request.form.get('benefits', '').split('\n')
        
        if title and department:
            job_id = len(job_postings) + 1
            new_job = {
                'id': job_id,
                'title': title,
                'department': department,
                'location': location or '',
                'employment_type': employment_type or 'Full-time',
                'experience_level': experience_level or '',
                'salary_range': salary_range or '',
                'description': description or '',
                'requirements': [req.strip() for req in requirements if req.strip()],
                'benefits': [benefit.strip() for benefit in benefits if benefit.strip()],
                'status': 'Active',
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'applications_count': 0
            }
            job_postings.append(new_job)
            flash('Job posting created successfully!', 'success')
            return redirect(url_for('admin_jobs'))
    
    return render_template('admin_add_job.html')

@app.route('/admin/jobs/<int:job_id>')
def view_job(job_id):
    if 'user' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
    
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
def edit_job(job_id):
    if 'user' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
    
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

@app.route('/admin/jobs/<int:job_id>/applications/<int:application_id>/update-status', methods=['POST'])
def update_application_status(job_id, application_id):
    if 'user' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
    
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
def admin_knowledge():
    if 'user' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
    
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
def add_knowledge_document():
    if 'user' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
    
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
def view_knowledge_document(doc_id):
    if 'user' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
    
    document = next((d for d in knowledge_documents if d['id'] == doc_id), None)
    
    if not document:
        flash('Document not found!', 'error')
        return redirect(url_for('admin_knowledge'))
    
    # Increment view count
    document['views'] += 1
    
    return render_template('admin_knowledge_detail.html', document=document)

@app.route('/admin/knowledge/<int:doc_id>/edit', methods=['GET', 'POST'])
def edit_knowledge_document(doc_id):
    if 'user' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
    
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
def delete_knowledge_document(doc_id):
    if 'user' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
    
    document = next((d for d in knowledge_documents if d['id'] == doc_id), None)
    
    if document:
        knowledge_documents.remove(document)
        flash('Document deleted successfully!', 'success')
    else:
        flash('Document not found!', 'error')
    
    return redirect(url_for('admin_knowledge'))

# Public knowledge hub for employees
@app.route('/employee/knowledge')
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
def view_induction_document(doc_id):
    document = next((d for d in induction_documents if d['id'] == doc_id and d['status'] == 'Published'), None)
    
    if not document:
        flash('Document not found!', 'error')
        return redirect(url_for('induction_page'))
    
    # Increment view count
    document['views'] += 1
    
    return render_template('induction_detail.html', document=document)

@app.route('/admin/induction')
def admin_induction():
    if 'user' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
    
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
def add_induction_document():
    if 'user' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
    
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

@app.route("/submit-ticket", methods=["GET", "POST"])
def submit_ticket():
    if "user" not in session:
        return redirect(url_for("login"))
    
    if request.method == "POST":
        new_ticket = {
            "id": len(tickets) + 1,
            "title": request.form["title"],
            "priority": request.form["priority"],
            "status": "open",
            "date": request.form["date"],
            "description": request.form.get("description", ""),
            "user_email": session["user"],
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
                    new_ticket["attachments"].append(filename)
        
        tickets.append(new_ticket)
        
        # Add notification for admin
        add_notification("admin@example.com", f"New ticket submitted: {new_ticket['title']}", "warning")
        
        flash("Ticket submitted!", "success")
        return redirect(url_for("view_tickets"))
    
    return render_template("submit_ticket.html")

if __name__ == "__main__":
    app.run(debug=True, port=5003)