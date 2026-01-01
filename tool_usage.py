#!/usr/bin/env python3
"""
Tool Usage Tracking
Track when users actually use/launch tools
"""

import json
from pathlib import Path
from datetime import datetime

USAGE_FILE = Path('tool_usage.json')


def load_usage():
    """Load tool usage data"""
    if USAGE_FILE.exists():
        try:
            with open(USAGE_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}


def save_usage(usage_data):
    """Save tool usage data"""
    with open(USAGE_FILE, 'w') as f:
        json.dump(usage_data, f, indent=2)


def track_tool_usage(tool_name, user_id):
    """Track when a user uses a tool"""
    usage = load_usage()
    
    # Initialize tool if not exists
    if tool_name not in usage:
        usage[tool_name] = {
            'total_uses': 0,
            'unique_users': [],
            'usage_log': []
        }
    
    # Increment total uses
    usage[tool_name]['total_uses'] += 1
    
    # Add user to unique users if not already there
    if user_id not in usage[tool_name]['unique_users']:
        usage[tool_name]['unique_users'].append(user_id)
    
    # Log this usage
    usage[tool_name]['usage_log'].append({
        'user_id': user_id,
        'timestamp': datetime.now().isoformat()
    })
    
    # Keep only last 1000 logs per tool to prevent file bloat
    if len(usage[tool_name]['usage_log']) > 1000:
        usage[tool_name]['usage_log'] = usage[tool_name]['usage_log'][-1000:]
    
    save_usage(usage)
    
    print(f"[USAGE TRACKED] Tool: {tool_name} | User: {user_id} | Total: {usage[tool_name]['total_uses']}")
    
    return usage[tool_name]


def get_tool_usage(tool_name):
    """Get usage stats for a specific tool"""
    usage = load_usage()
    return usage.get(tool_name, {
        'total_uses': 0,
        'unique_users': [],
        'usage_log': []
    })


def get_all_tool_usage():
    """Get usage stats for all tools"""
    return load_usage()


def get_user_tool_usage(user_id):
    """Get all tools a user has used"""
    usage = load_usage()
    user_tools = []
    
    for tool_name, tool_data in usage.items():
        if user_id in tool_data.get('unique_users', []):
            user_tools.append({
                'tool_name': tool_name,
                'total_uses': len([log for log in tool_data.get('usage_log', []) if log['user_id'] == user_id])
            })
    
    return user_tools

