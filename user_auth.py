"""
User Authentication System for RKIEH Solutions
Handles user registration, login, and session management
"""

import json
import hashlib
import os
import secrets
from datetime import datetime, timedelta

# User database file
USER_DB_FILE = 'users_database.json'

def init_user_database():
    """Initialize the user database if it doesn't exist"""
    if not os.path.exists(USER_DB_FILE):
        with open(USER_DB_FILE, 'w') as f:
            json.dump({'users': []}, f)

def load_users():
    """Load users from the database"""
    init_user_database()
    try:
        with open(USER_DB_FILE, 'r') as f:
            data = json.load(f)
            return data.get('users', [])
    except:
        return []

def save_users(users):
    """Save users to the database"""
    with open(USER_DB_FILE, 'w') as f:
        json.dump({'users': users}, f, indent=2)

def hash_password(password):
    """Hash a password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, hashed_password):
    """Verify a password against its hash"""
    return hash_password(password) == hashed_password

def user_exists(email):
    """Check if a user with the given email exists"""
    users = load_users()
    return any(user['email'].lower() == email.lower() for user in users)

def get_user_by_email(email):
    """Get user by email"""
    users = load_users()
    for user in users:
        if user['email'].lower() == email.lower():
            return user
    return None

def create_user(first_name, last_name, email, password):
    """Create a new user account"""
    # Check if user already exists
    if user_exists(email):
        return {'success': False, 'error': 'Email already registered'}
    
    # Validate inputs
    if not first_name or not last_name:
        return {'success': False, 'error': 'First and last name are required'}
    
    if not email or '@' not in email:
        return {'success': False, 'error': 'Valid email address is required'}
    
    if not password or len(password) < 8:
        return {'success': False, 'error': 'Password must be at least 8 characters'}
    
    # Create new user
    users = load_users()
    new_user = {
        'id': generate_user_id(),
        'first_name': first_name,
        'last_name': last_name,
        'email': email.lower(),
        'password': hash_password(password),
        'created_at': datetime.now().isoformat(),
        'last_login': None,
        'is_active': True,
        'profile_image': None
    }
    
    users.append(new_user)
    save_users(users)
    
    return {'success': True, 'user_id': new_user['id']}

def authenticate_user(email, password):
    """Authenticate a user with email and password"""
    user = get_user_by_email(email)
    
    if not user:
        return {'success': False, 'error': 'Invalid email or password'}
    
    if not user.get('is_active', True):
        return {'success': False, 'error': 'Account is disabled'}
    
    if not verify_password(password, user['password']):
        return {'success': False, 'error': 'Invalid email or password'}
    
    # Update last login
    users = load_users()
    for u in users:
        if u['id'] == user['id']:
            u['last_login'] = datetime.now().isoformat()
            break
    save_users(users)
    
    # Return user info (without password)
    user_info = {k: v for k, v in user.items() if k != 'password'}
    return {'success': True, 'user': user_info}

def generate_user_id():
    """Generate a unique user ID"""
    return secrets.token_hex(16)

def generate_session_token():
    """Generate a secure session token"""
    return secrets.token_urlsafe(32)

def get_user_stats():
    """Get statistics about registered users"""
    users = load_users()
    
    active_users = sum(1 for user in users if user.get('is_active', True))
    
    # Count logins in last 30 days
    thirty_days_ago = datetime.now() - timedelta(days=30)
    recent_logins = 0
    
    for user in users:
        last_login = user.get('last_login')
        if last_login:
            try:
                login_date = datetime.fromisoformat(last_login)
                if login_date >= thirty_days_ago:
                    recent_logins += 1
            except:
                pass
    
    return {
        'total_users': len(users),
        'active_users': active_users,
        'recent_logins': recent_logins
    }

def update_user_profile(user_id, updates):
    """Update user profile information"""
    users = load_users()
    
    for user in users:
        if user['id'] == user_id:
            # Only allow certain fields to be updated
            allowed_fields = ['first_name', 'last_name', 'profile_image']
            for field in allowed_fields:
                if field in updates:
                    user[field] = updates[field]
            
            save_users(users)
            return {'success': True}
    
    return {'success': False, 'error': 'User not found'}

def change_user_password(user_id, old_password, new_password):
    """Change user password"""
    users = load_users()
    
    for user in users:
        if user['id'] == user_id:
            # Verify old password
            if not verify_password(old_password, user['password']):
                return {'success': False, 'error': 'Current password is incorrect'}
            
            # Validate new password
            if len(new_password) < 8:
                return {'success': False, 'error': 'New password must be at least 8 characters'}
            
            # Update password
            user['password'] = hash_password(new_password)
            save_users(users)
            return {'success': True}
    
    return {'success': False, 'error': 'User not found'}

# Initialize database on import
init_user_database()

