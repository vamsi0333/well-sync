# Enplify.ai - Employee Management & Career Portal System

## Project Overview
Enplify.ai is a comprehensive employee management and career development platform that combines HR management, IT support, and career advancement features in a single, integrated solution.

## Core Features

### 1. Authentication & User Management
- Multi-role authentication system (Admin, Employee, IT)
- Secure login with session management
- Password reset functionality
- User profile management
- Role-based access control

### 2. Admin Dashboard
#### Employee Management
- Complete employee directory
- Employee profile management
- Department and role assignment
- Salary band management
- Employment status tracking
- Location tracking
- Manager assignment

#### Leave Management
- Leave request processing
- Multiple leave types support
- Leave balance tracking
- Calendar integration
- Approval workflow

#### Time-off Management
- Time-off request handling
- Approval/rejection workflow
- Admin comments feature
- Email notifications
- Status tracking

#### Applications & Recruitment
- Job posting management
- Application tracking
- Candidate evaluation
- Resume scoring (AI-powered)
- Interview scheduling
- Hiring workflow

### 3. Employee Portal
#### Dashboard
- Personal information overview
- Recent tickets and requests
- System status updates
- Notifications center
- Quick actions menu

#### IT Support System
- Ticket submission
- Priority-based ticketing
- File attachments
- Comment system
- Status tracking
- Email notifications

#### Career Development
- Skills tracking
- Badge system
- Learning resources
- Career progression
- Mentorship opportunities
- Goal setting

#### Request Management
- Hardware/software requests
- Leave applications
- Time-off requests
- Document requests
- Status tracking

### 4. AI Integration Features
- Resume parsing and scoring
- Job matching
- Knowledge base integration
- Chatbot assistance
- Performance analytics

## Technical Specifications

### Frontend
- HTML5, CSS3, JavaScript
- Responsive design
- Bootstrap framework
- Interactive dashboards
- Real-time notifications
- File upload capability

### Backend
- Python Flask framework
- RESTful API architecture
- MySQL database
- Session management
- Email integration
- File handling system

### AI Components
- PDF text extraction
- Sentence transformers
- TF-IDF vectorization
- Azure OpenAI integration
- Cosine similarity matching
- RAG (Retrieval-Augmented Generation)

### Security Features
- Session management
- Password hashing
- Role-based access
- Secure file uploads
- Input validation
- Error handling

## Database Schema

### Users Table
- id (Primary Key)
- email
- password (hashed)
- role
- status
- created_at
- last_login

### Employee Records
- id (Primary Key)
- user_id (Foreign Key)
- name
- department
- position
- hire_date
- manager_id
- location
- salary_band
- employment_type

### Tickets
- id (Primary Key)
- user_id (Foreign Key)
- title
- description
- priority
- status
- created_at
- updated_at
- attachments

### Leave Requests
- id (Primary Key)
- employee_id (Foreign Key)
- leave_type
- start_date
- end_date
- status
- reason
- admin_comment

### Job Applications
- id (Primary Key)
- job_id (Foreign Key)
- applicant_name
- email
- resume_path
- status
- score
- applied_date

## File Structure
```
app-3/
├── app.py              # Main application file
├── database_helper.py  # Database operations
├── database_config.py  # Database configuration
├── requirements.txt    # Project dependencies
├── static/
│   ├── css/           # Stylesheets
│   ├── js/            # JavaScript files
│   ├── images/        # Image assets
│   └── uploads/       # User uploads
└── templates/
    ├── admin/         # Admin panel templates
    ├── employee/      # Employee portal templates
    └── shared/        # Shared components
```

## Third-Party Integrations
- Azure OpenAI for AI features
- SMTP for email notifications
- Azure Search for knowledge base
- PDF processing libraries

## Non-Functional Requirements
1. Performance
   - Page load time < 2 seconds
   - API response time < 1 second
   - Support for concurrent users

2. Security
   - HTTPS encryption
   - Session timeout
   - Input sanitization
   - File upload restrictions

3. Scalability
   - Modular architecture
   - Cacheable components
   - Efficient database queries

4. Reliability
   - Error logging
   - Data backup
   - Failover handling

## Deployment Requirements
- Python 3.8+
- MySQL 8.0+
- Web server (e.g., Nginx)
- SSL certificate
- Environment variables configuration
- Required Python packages
- Sufficient storage for uploads
- Memory for AI operations

## Future Enhancements
1. Mobile application
2. Advanced analytics dashboard
3. Integration with other HR systems
4. Enhanced AI features
5. Performance review system
6. Training management
7. Automated onboarding
8. Calendar integration
9. Document management system
10. Advanced reporting tools
