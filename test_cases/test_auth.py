import pytest
from flask import session

def test_login_page(client):
    """Test that login page loads properly"""
    response = client.get('/login')
    assert response.status_code == 200
    assert b'Sign In' in response.data

def test_successful_login(client):
    """Test successful login with correct credentials"""
    response = client.post('/login', data={
        'email': 'user@example.com',
        'password': 'password'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Logged in successfully' in response.data

def test_failed_login_wrong_password(client):
    """Test login failure with wrong password"""
    response = client.post('/login', data={
        'email': 'user@example.com',
        'password': 'wrongpassword'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Invalid credentials' in response.data

def test_failed_login_wrong_email(client):
    """Test login failure with non-existent email"""
    response = client.post('/login', data={
        'email': 'nonexistent@example.com',
        'password': 'password'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Invalid credentials' in response.data

def test_logout(client):
    """Test logout functionality"""
    # First login
    client.post('/login', data={
        'email': 'user@example.com',
        'password': 'password'
    })
    
    # Then logout
    response = client.get('/logout', follow_redirects=True)
    assert response.status_code == 200
    assert session.get('user_id') is None

def test_protected_route_redirect(client):
    """Test that protected routes redirect to login when not authenticated"""
    response = client.get('/dashboard', follow_redirects=True)
    assert response.status_code == 200
    assert b'Sign In' in response.data
