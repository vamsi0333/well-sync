#!/usr/bin/env python3
"""
Find the correct password for the user
"""

import hashlib

def find_password():
    """Find the correct password for the user"""
    print("Finding correct password...")
    
    stored_hash = "e03d3ec8d5035f8721f5dc64546e59ed790dbcb3b7b598fe57057ccd7b683b00"
    
    # Test common passwords
    test_passwords = [
        "password123",
        "password",
        "123456",
        "admin",
        "employee",
        "test",
        "user",
        "pass",
        "123",
        "password1",
        "password12",
        "password1234",
        "password12345",
        "password123456",
        "password1234567",
        "password12345678",
        "password123456789",
        "password1234567890"
    ]
    
    for password in test_passwords:
        hashed = hashlib.sha256(password.encode()).hexdigest()
        if hashed == stored_hash:
            print(f"✅ Found correct password: '{password}'")
            return password
    
    print("❌ Could not find correct password")
    return None

if __name__ == "__main__":
    find_password() 