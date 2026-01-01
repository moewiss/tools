#!/usr/bin/env python3
"""
Pricing Settings Management
Admin can edit subscription plan prices
"""

import json
from pathlib import Path

PRICING_FILE = Path('pricing_settings.json')

# Default pricing with features
DEFAULT_PRICES = {
    'pro': {
        'price': 9.99,
        'daily_limit': 100,
        'features': [
            '100 uses per day',
            'High quality',
            'Priority support',
            'No ads'
        ]
    },
    'premium': {
        'price': 19.99,
        'daily_limit': -1,  # -1 means unlimited
        'features': [
            'Unlimited uses',
            'Ultra quality',
            'VIP support',
            'API access',
            'Custom branding'
        ]
    }
}


def load_pricing():
    """Load pricing settings with backwards compatibility"""
    if PRICING_FILE.exists():
        try:
            with open(PRICING_FILE, 'r') as f:
                data = json.load(f)
                
                # Backwards compatibility: Convert old format to new format
                if 'pro' in data and isinstance(data['pro'], (int, float)):
                    # Old format - just prices
                    data = {
                        'pro': {
                            'price': data['pro'],
                            'daily_limit': DEFAULT_PRICES['pro']['daily_limit'],
                            'features': DEFAULT_PRICES['pro']['features'].copy()
                        },
                        'premium': {
                            'price': data.get('premium', DEFAULT_PRICES['premium']['price']),
                            'daily_limit': DEFAULT_PRICES['premium']['daily_limit'],
                            'features': DEFAULT_PRICES['premium']['features'].copy()
                        }
                    }
                    # Save in new format
                    save_pricing(data)
                
                return data
        except:
            return DEFAULT_PRICES.copy()
    return DEFAULT_PRICES.copy()


def save_pricing(pricing):
    """Save pricing settings"""
    with open(PRICING_FILE, 'w') as f:
        json.dump(pricing, f, indent=2)


def update_plan(plan, new_price=None, daily_limit=None, features=None):
    """Update plan pricing, limits, and features"""
    if plan not in ['pro', 'premium']:
        return {
            'success': False,
            'error': 'Invalid plan'
        }
    
    pricing = load_pricing()
    
    # Update price if provided
    if new_price is not None:
        if new_price < 0:
            return {
                'success': False,
                'error': 'Price cannot be negative'
            }
        pricing[plan]['price'] = float(new_price)
    
    # Update daily limit if provided
    if daily_limit is not None:
        pricing[plan]['daily_limit'] = int(daily_limit)
    
    # Update features if provided
    if features is not None:
        if isinstance(features, list):
            pricing[plan]['features'] = features
        elif isinstance(features, str):
            # Split by newlines and filter empty
            pricing[plan]['features'] = [f.strip() for f in features.split('\n') if f.strip()]
    
    save_pricing(pricing)
    
    return {
        'success': True,
        'message': f'{plan.upper()} plan updated successfully!'
    }


# Keep old function for backwards compatibility
def update_price(plan, new_price):
    """Update price for a plan (backwards compatibility)"""
    return update_plan(plan, new_price=new_price)


def get_prices():
    """Get current prices"""
    return load_pricing()

