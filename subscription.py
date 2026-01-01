#!/usr/bin/env python3
"""
Subscription Management System
Handle user subscriptions, limits, and upgrades
"""

import json
from pathlib import Path
from datetime import datetime, timedelta
import hashlib

SUBSCRIPTION_FILE = Path('subscriptions_database.json')

# Subscription Plans
PLANS = {
    'free': {
        'name': 'Free',
        'price': 0,
        'daily_limit': 5,
        'features': [
            'Access to all tools',
            '5 uses per day',
            'Standard quality',
            'Community support'
        ]
    },
    'pro': {
        'name': 'Pro',
        'price': 9.99,
        'daily_limit': 100,
        'features': [
            'Access to all tools',
            '100 uses per day',
            'High quality',
            'Priority support',
            'No ads',
            'Export history'
        ]
    },
    'premium': {
        'name': 'Premium',
        'price': 19.99,
        'daily_limit': -1,  # Unlimited
        'features': [
            'Access to all tools',
            'Unlimited uses',
            'Ultra quality',
            'VIP support',
            'No ads',
            'Export history',
            'API access',
            'Custom branding'
        ]
    }
}


def load_subscriptions():
    """Load subscriptions from file"""
    if SUBSCRIPTION_FILE.exists():
        try:
            with open(SUBSCRIPTION_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}


def save_subscriptions(subscriptions):
    """Save subscriptions to file"""
    with open(SUBSCRIPTION_FILE, 'w') as f:
        json.dump(subscriptions, f, indent=2)


def get_user_subscription(user_id):
    """Get user's subscription info"""
    subscriptions = load_subscriptions()
    
    if user_id in subscriptions:
        sub = subscriptions[user_id]
        
        # Check if subscription is expired
        if sub['plan'] != 'free':
            expiry = datetime.fromisoformat(sub['expires_at'])
            if datetime.now() > expiry:
                # Downgrade to free
                sub['plan'] = 'free'
                sub['status'] = 'expired'
                subscriptions[user_id] = sub
                save_subscriptions(subscriptions)
        
        return sub
    else:
        # Create default free subscription
        sub = {
            'user_id': user_id,
            'plan': 'free',
            'status': 'active',
            'created_at': datetime.now().isoformat(),
            'expires_at': None,
            'usage': {
                'today': 0,
                'last_reset': datetime.now().date().isoformat()
            }
        }
        subscriptions[user_id] = sub
        save_subscriptions(subscriptions)
        return sub


def check_usage_limit(user_id):
    """Check if user has reached their daily limit"""
    sub = get_user_subscription(user_id)
    plan_info = PLANS[sub['plan']]
    
    # Reset daily usage if new day
    today = datetime.now().date().isoformat()
    if sub['usage']['last_reset'] != today:
        sub['usage']['today'] = 0
        sub['usage']['last_reset'] = today
        subscriptions = load_subscriptions()
        subscriptions[user_id] = sub
        save_subscriptions(subscriptions)
    
    daily_limit = plan_info['daily_limit']
    
    # -1 means unlimited
    if daily_limit == -1:
        return {
            'allowed': True,
            'remaining': -1,
            'limit': -1
        }
    
    used = sub['usage']['today']
    remaining = daily_limit - used
    
    return {
        'allowed': remaining > 0,
        'remaining': remaining,
        'limit': daily_limit,
        'used': used
    }


def increment_usage(user_id):
    """Increment user's daily usage"""
    subscriptions = load_subscriptions()
    
    if user_id in subscriptions:
        sub = subscriptions[user_id]
        
        # Reset if new day
        today = datetime.now().date().isoformat()
        if sub['usage']['last_reset'] != today:
            sub['usage']['today'] = 0
            sub['usage']['last_reset'] = today
        
        sub['usage']['today'] += 1
        subscriptions[user_id] = sub
        save_subscriptions(subscriptions)


def upgrade_subscription(user_id, plan, payment_info=None):
    """Upgrade user's subscription"""
    if plan not in PLANS:
        return {
            'success': False,
            'error': 'Invalid plan'
        }
    
    subscriptions = load_subscriptions()
    
    # Get or create subscription
    sub = get_user_subscription(user_id)
    
    # Update subscription
    sub['plan'] = plan
    sub['status'] = 'active'
    sub['updated_at'] = datetime.now().isoformat()
    
    # Set expiry (30 days from now)
    if plan != 'free':
        sub['expires_at'] = (datetime.now() + timedelta(days=30)).isoformat()
    else:
        sub['expires_at'] = None
    
    # Store payment info (if provided)
    if payment_info:
        if 'payments' not in sub:
            sub['payments'] = []
        sub['payments'].append({
            'amount': PLANS[plan]['price'],
            'date': datetime.now().isoformat(),
            'method': payment_info.get('method', 'card'),
            'status': 'completed'
        })
    
    subscriptions[user_id] = sub
    save_subscriptions(subscriptions)
    
    return {
        'success': True,
        'subscription': sub
    }


def cancel_subscription(user_id):
    """Cancel user's subscription (downgrade to free at end of period)"""
    subscriptions = load_subscriptions()
    
    if user_id in subscriptions:
        sub = subscriptions[user_id]
        sub['status'] = 'cancelled'
        sub['cancelled_at'] = datetime.now().isoformat()
        subscriptions[user_id] = sub
        save_subscriptions(subscriptions)
        
        return {
            'success': True,
            'message': 'Subscription cancelled. You will be downgraded to Free at the end of your billing period.'
        }
    
    return {
        'success': False,
        'error': 'Subscription not found'
    }


def get_subscription_stats():
    """Get subscription statistics for admin"""
    subscriptions = load_subscriptions()
    
    total = len(subscriptions)
    free = sum(1 for s in subscriptions.values() if s['plan'] == 'free')
    pro = sum(1 for s in subscriptions.values() if s['plan'] == 'pro')
    premium = sum(1 for s in subscriptions.values() if s['plan'] == 'premium')
    
    # Calculate revenue (monthly)
    revenue = (pro * PLANS['pro']['price']) + (premium * PLANS['premium']['price'])
    
    return {
        'total_users': total,
        'free_users': free,
        'pro_users': pro,
        'premium_users': premium,
        'monthly_revenue': revenue
    }

