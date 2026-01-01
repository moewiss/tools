"""
Admin Authentication System for RKIEH Solutions
Separate from regular user authentication
"""

import json
import hashlib
import os
from datetime import datetime

# Admin database file
ADMIN_DB_FILE = 'admins_database.json'

def init_admin_database():
    """Initialize the admin database if it doesn't exist"""
    if not os.path.exists(ADMIN_DB_FILE):
        # Create with default admin
        default_admin = {
            'admins': [
                {
                    'id': 'admin_001',
                    'email': 'Omar99leb@icloud.com',
                    'password': hash_password('Omar99leb'),
                    'name': 'Omar',
                    'created_at': datetime.now().isoformat(),
                    'is_super_admin': True,
                    'last_login': None
                }
            ]
        }
        with open(ADMIN_DB_FILE, 'w') as f:
            json.dump(default_admin, f, indent=2)
        print(f"✅ Admin database created with default admin: Omar99leb@icloud.com")
    else:
        print(f"✅ Admin database already exists")

def load_admins():
    """Load admins from the database"""
    init_admin_database()
    try:
        with open(ADMIN_DB_FILE, 'r') as f:
            data = json.load(f)
            return data.get('admins', [])
    except:
        return []

def save_admins(admins):
    """Save admins to the database"""
    with open(ADMIN_DB_FILE, 'w') as f:
        json.dump({'admins': admins}, f, indent=2)

def hash_password(password):
    """Hash a password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, hashed_password):
    """Verify a password against its hash"""
    return hash_password(password) == hashed_password

def admin_exists(email):
    """Check if an admin with the given email exists"""
    admins = load_admins()
    return any(admin['email'].lower() == email.lower() for admin in admins)

def get_admin_by_email(email):
    """Get admin by email"""
    admins = load_admins()
    for admin in admins:
        if admin['email'].lower() == email.lower():
            return admin
    return None

def authenticate_admin(email, password):
    """Authenticate an admin with email and password"""
    admin = get_admin_by_email(email)
    
    if not admin:
        return {'success': False, 'error': 'Invalid email or password'}
    
    if not verify_password(password, admin['password']):
        return {'success': False, 'error': 'Invalid email or password'}
    
    # Update last login
    admins = load_admins()
    for a in admins:
        if a['id'] == admin['id']:
            a['last_login'] = datetime.now().isoformat()
            break
    save_admins(admins)
    
    # Return admin info (without password)
    admin_info = {k: v for k, v in admin.items() if k != 'password'}
    return {'success': True, 'admin': admin_info}

def create_admin(email, password, name):
    """Create a new admin account"""
    # Check if admin already exists
    if admin_exists(email):
        return {'success': False, 'error': 'Admin email already exists'}
    
    # Validate inputs
    if not email or '@' not in email:
        return {'success': False, 'error': 'Valid email address is required'}
    
    if not password or len(password) < 8:
        return {'success': False, 'error': 'Password must be at least 8 characters'}
    
    if not name:
        return {'success': False, 'error': 'Name is required'}
    
    # Create new admin
    admins = load_admins()
    admin_id = f'admin_{str(len(admins) + 1).zfill(3)}'
    
    new_admin = {
        'id': admin_id,
        'email': email.lower(),
        'password': hash_password(password),
        'name': name,
        'created_at': datetime.now().isoformat(),
        'is_super_admin': False,
        'last_login': None
    }
    
    admins.append(new_admin)
    save_admins(admins)
    
    return {'success': True, 'admin_id': admin_id}

def delete_admin(admin_id):
    """Delete an admin account"""
    admins = load_admins()
    
    # Don't allow deleting the super admin
    admin_to_delete = next((a for a in admins if a['id'] == admin_id), None)
    if admin_to_delete and admin_to_delete.get('is_super_admin'):
        return {'success': False, 'error': 'Cannot delete super admin'}
    
    # Remove admin
    admins = [a for a in admins if a['id'] != admin_id]
    save_admins(admins)
    
    return {'success': True}

def get_admin_stats():
    """Get statistics about admins"""
    admins = load_admins()
    
    return {
        'total_admins': len(admins),
        'super_admins': sum(1 for a in admins if a.get('is_super_admin', False)),
        'regular_admins': sum(1 for a in admins if not a.get('is_super_admin', False))
    }

# Initialize database on import
init_admin_database()

