import pytest
from werkzeug.security import check_password_hash

def test_registration_page(client):
    """Test that registration page loads properly"""
    response = client.get('/register')
    assert response.status_code == 200
    assert b'Create Account' in response.data

def test_successful_registration(client, db):
    """Test successful user registration"""
    test_email = 'newuser@example.com'
    test_password = 'testpassword123'
    
    response = client.post('/register', data={
        'email': test_email,
        'password': test_password,
        'confirm_password': test_password
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'Account created successfully' in response.data
    
    # Verify user was created in database
    user = db.get_user_by_email(test_email)
    assert user is not None
    assert user['email'] == test_email

def test_registration_existing_email(client):
    """Test registration with already existing email"""
    response = client.post('/register', data={
        'email': 'user@example.com',  # This email already exists
        'password': 'newpassword123',
        'confirm_password': 'newpassword123'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'Email already registered' in response.data

def test_registration_password_mismatch(client):
    """Test registration with mismatched passwords"""
    response = client.post('/register', data={
        'email': 'newuser@example.com',
        'password': 'password123',
        'confirm_password': 'password456'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'Passwords do not match' in response.data

def test_registration_invalid_email(client):
    """Test registration with invalid email format"""
    response = client.post('/register', data={
        'email': 'invalid-email',
        'password': 'password123',
        'confirm_password': 'password123'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'Invalid email address' in response.data

def test_registration_weak_password(client):
    """Test registration with weak password"""
    response = client.post('/register', data={
        'email': 'newuser@example.com',
        'password': '123',  # Too short
        'confirm_password': '123'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'Password must be at least 8 characters' in response.data
