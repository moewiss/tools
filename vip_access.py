#!/usr/bin/env python3
"""
VIP Access Management
Grant specific users unlimited free access to all tools
"""

import json
from pathlib import Path
from datetime import datetime

VIP_FILE = Path('vip_access.json')


def load_vip_users():
    """Load VIP users list"""
    if VIP_FILE.exists():
        try:
            with open(VIP_FILE, 'r') as f:
                return json.load(f)
        except:
            return []
    return []


def save_vip_users(vip_users):
    """Save VIP users list"""
    with open(VIP_FILE, 'w') as f:
        json.dump(vip_users, f, indent=2)


def grant_vip_access(user_id, user_email, granted_by, reason='', access_type='vip'):
    """Grant VIP or Employee access to a user"""
    vip_users = load_vip_users()
    
    # Check if already has access
    existing = next((v for v in vip_users if v['user_id'] == user_id), None)
    if existing:
        return {
            'success': False,
            'error': f'User already has {existing.get("access_type", "VIP")} access'
        }
    
    vip_entry = {
        'user_id': user_id,
        'user_email': user_email,
        'granted_by': granted_by,
        'granted_at': datetime.now().isoformat(),
        'reason': reason,
        'is_active': True,
        'access_type': access_type  # 'vip' or 'employee'
    }
    
    vip_users.append(vip_entry)
    save_vip_users(vip_users)
    
    access_name = 'Employee' if access_type == 'employee' else 'VIP'
    return {
        'success': True,
        'message': f'{access_name} access granted successfully!'
    }


def revoke_vip_access(user_id):
    """Revoke VIP access from a user"""
    vip_users = load_vip_users()
    
    vip_entry = next((v for v in vip_users if v['user_id'] == user_id), None)
    if not vip_entry:
        return {
            'success': False,
            'error': 'User does not have VIP access'
        }
    
    vip_entry['is_active'] = False
    vip_entry['revoked_at'] = datetime.now().isoformat()
    save_vip_users(vip_users)
    
    return {
        'success': True,
        'message': 'VIP access revoked successfully'
    }


def is_vip_user(user_id):
    """Check if user has VIP access"""
    vip_users = load_vip_users()
    vip_entry = next((v for v in vip_users if v['user_id'] == user_id and v['is_active']), None)
    return vip_entry is not None


def get_all_vip_users():
    """Get all VIP users"""
    return load_vip_users()


def check_unlimited_access(user_id):
    """Check if user has unlimited access (VIP or Premium plan)"""
    # Check VIP status
    if is_vip_user(user_id):
        return {
            'unlimited': True,
            'reason': 'VIP Access',
            'bypass_limits': True
        }
    
    # Check subscription (if Premium plan)
    try:
        from subscription import get_user_subscription
        sub = get_user_subscription(user_id)
        if sub['plan'] == 'premium':
            return {
                'unlimited': True,
                'reason': 'Premium Subscription',
                'bypass_limits': False
            }
    except:
        pass
    
    return {
        'unlimited': False,
        'reason': None,
        'bypass_limits': False
    }

