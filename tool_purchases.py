#!/usr/bin/env python3
"""
Tool Purchases and Access Management
Track which users have purchased or been granted access to specific tools
"""

import json
from pathlib import Path
from datetime import datetime
import uuid

PURCHASES_FILE = Path('tool_purchases.json')


def load_purchases():
    """Load all tool purchases/access grants"""
    if PURCHASES_FILE.exists():
        try:
            with open(PURCHASES_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}


def save_purchases(purchases):
    """Save purchases to file"""
    with open(PURCHASES_FILE, 'w') as f:
        json.dump(purchases, f, indent=2)


def grant_tool_access(user_id, tool_name, granted_by='admin', access_type='free_grant'):
    """
    Grant a user access to a specific tool
    
    access_type: 'purchase' or 'free_grant'
    """
    print(f"\n[TOOL_PURCHASES.PY] grant_tool_access called")
    print(f"  user_id: '{user_id}'")
    print(f"  tool_name: '{tool_name}'")
    print(f"  granted_by: '{granted_by}'")
    print(f"  access_type: '{access_type}'")
    
    purchases = load_purchases()
    print(f"  Loaded purchases: {purchases}")
    
    # Initialize user's purchases if not exists
    if user_id not in purchases:
        print(f"  Creating new entry for user '{user_id}'")
        purchases[user_id] = {}
    
    # Check if already has access
    if tool_name in purchases[user_id]:
        print(f"  ❌ User already has access to '{tool_name}'")
        return {
            'success': False,
            'error': 'User already has access to this tool'
        }
    
    # Grant access
    access_data = {
        'access_id': str(uuid.uuid4()),
        'tool_name': tool_name,
        'access_type': access_type,
        'granted_by': granted_by,
        'granted_at': datetime.now().isoformat(),
        'status': 'active'
    }
    purchases[user_id][tool_name] = access_data
    print(f"  Added access: {access_data}")
    
    print(f"  Saving to {PURCHASES_FILE.absolute()}...")
    save_purchases(purchases)
    
    # Verify it was saved
    verify = load_purchases()
    if user_id in verify and tool_name in verify[user_id]:
        print(f"  ✅ Verified: Access saved successfully!")
    else:
        print(f"  ⚠️ WARNING: Access not found after save!")
    
    return {
        'success': True,
        'message': f'Access granted to {tool_name}',
        'access': purchases[user_id][tool_name]
    }


def revoke_tool_access(user_id, tool_name):
    """Revoke a user's access to a specific tool"""
    print(f"\n[TOOL_PURCHASES.PY] revoke_tool_access called")
    print(f"  user_id: '{user_id}'")
    print(f"  tool_name: '{tool_name}'")
    
    purchases = load_purchases()
    print(f"  Loaded purchases: {purchases}")
    print(f"  User exists: {user_id in purchases}")
    if user_id in purchases:
        print(f"  User's tools: {list(purchases[user_id].keys())}")
        print(f"  Has tool: {tool_name in purchases[user_id]}")
    
    if user_id not in purchases or tool_name not in purchases[user_id]:
        print(f"  ❌ User does not have a purchase/grant record for this tool")
        return {
            'success': False,
            'error': 'User does not have a purchase/grant record for this tool. Free tool users cannot be deleted from access (they just used the tool).'
        }
    
    # Remove access
    print(f"  Deleting '{tool_name}' from user '{user_id}'...")
    del purchases[user_id][tool_name]
    
    # Clean up empty user entries
    if not purchases[user_id]:
        print(f"  User has no more tools, removing user entry...")
        del purchases[user_id]
    
    print(f"  Saving to {PURCHASES_FILE.absolute()}...")
    save_purchases(purchases)
    
    # Verify it was deleted
    verify = load_purchases()
    if user_id not in verify or tool_name not in verify.get(user_id, {}):
        print(f"  ✅ Verified: Access revoked successfully!")
    else:
        print(f"  ⚠️ WARNING: Access still found after delete!")
    
    return {
        'success': True,
        'message': f'Access revoked for {tool_name}'
    }


def has_tool_access(user_id, tool_name):
    """Check if a user has access to a specific tool"""
    purchases = load_purchases()
    
    has_access = user_id in purchases and tool_name in purchases[user_id]
    
    print(f"[has_tool_access] user_id='{user_id}', tool_name='{tool_name}' -> {has_access}")
    if user_id in purchases:
        print(f"  User's tools: {list(purchases[user_id].keys())}")
    
    return has_access


def get_user_tool_purchases(user_id):
    """Get all tools a user has access to"""
    purchases = load_purchases()
    return purchases.get(user_id, {})


def get_tool_users(tool_name):
    """Get all users who have access to a specific tool"""
    purchases = load_purchases()
    users = []
    
    for user_id, tools in purchases.items():
        if tool_name in tools:
            users.append({
                'user_id': user_id,
                'access_info': tools[tool_name]
            })
    
    return users


def record_purchase(user_id, tool_name, payment_info=None):
    """Record a tool purchase"""
    return grant_tool_access(user_id, tool_name, granted_by='purchase', access_type='purchase')


def get_all_purchases():
    """Get all purchases (for admin)"""
    return load_purchases()

