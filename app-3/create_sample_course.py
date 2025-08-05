#!/usr/bin/env python3
"""
Script to create a sample course in the database
"""

from database_helper import db_helper
import json

def create_sample_course():
    """Create a sample course for testing"""
    
    # Sample course data
    course_data = {
        'title': 'Introduction to Cybersecurity',
        'description': 'Learn the fundamentals of cybersecurity including threats, vulnerabilities, and best practices.',
        'content': '''
        <h2>Welcome to Introduction to Cybersecurity</h2>
        <p>This course covers the essential concepts of cybersecurity that every employee should know.</p>
        
        <h3>Module 1: Understanding Cyber Threats</h3>
        <p>Learn about different types of cyber threats including malware, phishing, and social engineering.</p>
        
        <h3>Module 2: Password Security</h3>
        <p>Best practices for creating and managing strong passwords.</p>
        
        <h3>Module 3: Data Protection</h3>
        <p>How to protect sensitive data and recognize potential security risks.</p>
        
        <h3>Module 4: Safe Internet Practices</h3>
        <p>Guidelines for safe browsing, email security, and social media usage.</p>
        ''',
        'questions': [
            {
                'question': 'What is the most common type of cyber attack?',
                'options': ['Malware', 'Phishing', 'DDoS', 'SQL Injection'],
                'correct_answer': 1
            },
            {
                'question': 'Which of the following is NOT a strong password practice?',
                'options': ['Use at least 12 characters', 'Include numbers and symbols', 'Use personal information', 'Use a passphrase'],
                'correct_answer': 2
            },
            {
                'question': 'What should you do if you receive a suspicious email?',
                'options': ['Click all links to check', 'Forward to IT immediately', 'Reply to the sender', 'Ignore it completely'],
                'correct_answer': 1
            },
            {
                'question': 'What is HTTPS?',
                'options': ['A programming language', 'A secure protocol for web communication', 'A type of malware', 'A database system'],
                'correct_answer': 1
            },
            {
                'question': 'Which of the following is a good practice for data protection?',
                'options': ['Share passwords with colleagues', 'Use public Wi-Fi for work', 'Encrypt sensitive files', 'Leave devices unlocked'],
                'correct_answer': 2
            }
        ],
        'passing_score': 80,
        'badge': 'Cybersecurity Basics'
    }
    
    try:
        # Create the course
        course_id = db_helper.create_course(
            title=course_data['title'],
            description=course_data['description'],
            content=course_data['content'],
            questions=course_data['questions'],
            passing_score=course_data['passing_score'],
            badge=course_data['badge']
        )
        
        if course_id:
            print(f"✅ Sample course created successfully with ID: {course_id}")
            print(f"Title: {course_data['title']}")
            print(f"Badge: {course_data['badge']}")
            print(f"Passing Score: {course_data['passing_score']}%")
        else:
            print("❌ Failed to create sample course")
            
    except Exception as e:
        print(f"❌ Error creating sample course: {e}")

if __name__ == "__main__":
    create_sample_course() 