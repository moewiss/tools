#!/usr/bin/env python3
"""
Leaderboard System
Track and rank users by various metrics
"""

import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict

def get_leaderboard_stats():
    """Get comprehensive leaderboard statistics"""
    from user_auth import load_users
    from subscription import load_subscriptions
    from reviews import load_reviews
    
    users = load_users()
    subscriptions = load_subscriptions()
    reviews = load_reviews()
    
    # Try to load feedback
    feedback_file = Path('feedback_database.json')
    feedback = []
    if feedback_file.exists():
        try:
            with open(feedback_file, 'r') as f:
                feedback = json.load(f)
        except:
            pass
    
    # Calculate user stats
    user_stats = []
    
    for user in users:
        user_id = user['id']
        email = user['email']
        name = f"{user.get('first_name', '')} {user.get('last_name', '')}".strip()
        
        # Get subscription info
        sub = subscriptions.get(user_id, {})
        plan = sub.get('plan', 'free')
        usage = sub.get('usage', {}).get('today', 0)
        
        # Count reviews
        user_reviews = [r for r in reviews if r['user_id'] == user_id]
        review_count = len(user_reviews)
        
        # Count feedback
        user_feedback = [f for f in feedback if f.get('user_email') == email]
        feedback_count = len(user_feedback)
        
        # Calculate total engagement
        total_engagement = usage + review_count + feedback_count
        
        # Get join date
        created_at = sub.get('created_at', user.get('created_at', ''))
        
        user_stats.append({
            'user_id': user_id,
            'name': name or 'Anonymous',
            'email': email,
            'plan': plan,
            'usage_today': usage,
            'total_reviews': review_count,
            'total_feedback': feedback_count,
            'total_engagement': total_engagement,
            'created_at': created_at,
            'is_active': user.get('is_active', True)
        })
    
    # Sort leaderboards
    top_users_by_usage = sorted(user_stats, key=lambda x: x['usage_today'], reverse=True)[:10]
    top_reviewers = sorted(user_stats, key=lambda x: x['total_reviews'], reverse=True)[:10]
    top_engaged = sorted(user_stats, key=lambda x: x['total_engagement'], reverse=True)[:10]
    
    # Get premium users
    premium_users = [u for u in user_stats if u['plan'] in ['pro', 'premium']]
    top_premium = sorted(premium_users, key=lambda x: x['usage_today'], reverse=True)[:10]
    
    # Calculate tool popularity
    tool_usage = defaultdict(int)
    for f in feedback:
        tool_usage[f.get('tool_name', 'Unknown')] += 1
    
    top_tools = sorted(tool_usage.items(), key=lambda x: x[1], reverse=True)[:10]
    
    # Overall stats
    total_active = len([u for u in user_stats if u['is_active']])
    total_premium = len(premium_users)
    total_reviews = sum(u['total_reviews'] for u in user_stats)
    total_feedback_count = sum(u['total_feedback'] for u in user_stats)
    
    return {
        'leaderboards': {
            'top_users_by_usage': top_users_by_usage,
            'top_reviewers': top_reviewers,
            'top_engaged': top_engaged,
            'top_premium': top_premium
        },
        'top_tools': [{'name': name, 'count': count} for name, count in top_tools],
        'overall_stats': {
            'total_users': len(users),
            'active_users': total_active,
            'premium_users': total_premium,
            'total_reviews': total_reviews,
            'total_feedback': total_feedback_count
        }
    }


def get_user_rank(user_id, metric='engagement'):
    """Get a specific user's rank"""
    stats = get_leaderboard_stats()
    
    if metric == 'usage':
        leaderboard = stats['leaderboards']['top_users_by_usage']
    elif metric == 'reviews':
        leaderboard = stats['leaderboards']['top_reviewers']
    else:
        leaderboard = stats['leaderboards']['top_engaged']
    
    for idx, user in enumerate(leaderboard, 1):
        if user['user_id'] == user_id:
            return {
                'rank': idx,
                'total': len(leaderboard)
            }
    
    return {'rank': None, 'total': len(leaderboard)}

