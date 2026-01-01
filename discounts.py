#!/usr/bin/env python3
"""
Discount Management System
Handle promotional discounts for subscription plans
"""

import json
from pathlib import Path
from datetime import datetime
import uuid

DISCOUNTS_FILE = Path('discounts_database.json')


def load_discounts():
    """Load all discounts from file"""
    if DISCOUNTS_FILE.exists():
        try:
            with open(DISCOUNTS_FILE, 'r') as f:
                return json.load(f)
        except:
            return []
    return []


def save_discounts(discounts):
    """Save discounts to file"""
    with open(DISCOUNTS_FILE, 'w') as f:
        json.dump(discounts, f, indent=2)


def create_discount(tool_name, discount_type, discount_value, description='', expires_at=None, original_price=None):
    """
    Create a new discount
    
    tool_name: Name of the tool (or 'all' for all tools)
    discount_type: 'percentage' or 'fixed'
    discount_value: Discount amount (e.g., 20 for 20% or 5 for $5 off)
    description: Optional description
    expires_at: Optional expiry date (ISO format)
    original_price: Optional original price before discount
    """
    discounts = load_discounts()
    
    # Check if discount already exists for this tool
    existing = next((d for d in discounts if d['tool_name'] == tool_name and d['is_active']), None)
    
    if existing:
        return {
            'success': False,
            'error': f'An active discount already exists for {tool_name}'
        }
    
    discount = {
        'id': str(uuid.uuid4()),
        'tool_name': tool_name,
        'discount_type': discount_type,
        'discount_value': discount_value,
        'original_price': original_price,  # New field
        'description': description,
        'is_active': True,
        'created_at': datetime.now().isoformat(),
        'expires_at': expires_at,
        'used_count': 0
    }
    
    discounts.append(discount)
    save_discounts(discounts)
    
    return {
        'success': True,
        'discount': discount,
        'message': 'Discount created successfully!'
    }


def get_active_discounts():
    """Get all active discounts"""
    discounts = load_discounts()
    now = datetime.now()
    
    active = []
    for discount in discounts:
        if not discount['is_active']:
            continue
        
        # Check if expired
        if discount.get('expires_at'):
            expires = datetime.fromisoformat(discount['expires_at'])
            if now > expires:
                discount['is_active'] = False
                continue
        
        active.append(discount)
    
    save_discounts(discounts)
    return active


def get_tool_discount(tool_name):
    """Get active discount for a specific tool"""
    active_discounts = get_active_discounts()
    
    # Check for tool-specific discount first
    tool_discount = next((d for d in active_discounts if d['tool_name'] == tool_name), None)
    if tool_discount:
        return tool_discount
    
    # Check for "all tools" discount
    all_discount = next((d for d in active_discounts if d['tool_name'] == 'all'), None)
    return all_discount


def deactivate_discount(discount_id):
    """Deactivate a discount"""
    discounts = load_discounts()
    discount = next((d for d in discounts if d['id'] == discount_id), None)
    
    if not discount:
        return {
            'success': False,
            'error': 'Discount not found'
        }
    
    discount['is_active'] = False
    discount['deactivated_at'] = datetime.now().isoformat()
    save_discounts(discounts)
    
    return {
        'success': True,
        'message': 'Discount deactivated successfully'
    }


def delete_discount(discount_id):
    """Delete a discount"""
    discounts = load_discounts()
    discounts = [d for d in discounts if d['id'] != discount_id]
    save_discounts(discounts)
    
    return {
        'success': True,
        'message': 'Discount deleted successfully'
    }


def increment_discount_usage(discount_id):
    """Increment the usage counter for a discount"""
    discounts = load_discounts()
    discount = next((d for d in discounts if d['id'] == discount_id), None)
    
    if discount:
        discount['used_count'] = discount.get('used_count', 0) + 1
        save_discounts(discounts)


def get_all_discounts():
    """Get all discounts (active and inactive) for admin"""
    return load_discounts()


def calculate_discounted_price(original_price, discount):
    """Calculate the discounted price"""
    if not discount:
        return original_price
    
    if discount['discount_type'] == 'percentage':
        discount_amount = original_price * (discount['discount_value'] / 100)
        return round(original_price - discount_amount, 2)
    else:  # fixed
        return round(max(0, original_price - discount['discount_value']), 2)

