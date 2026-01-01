#!/usr/bin/env python3
"""
Tool Reviews and Comments System
Handle user reviews, comments, and ratings for tools
"""

import json
from pathlib import Path
from datetime import datetime
import uuid

REVIEWS_FILE = Path('reviews_database.json')


def load_reviews():
    """Load all reviews from file"""
    if REVIEWS_FILE.exists():
        try:
            with open(REVIEWS_FILE, 'r') as f:
                return json.load(f)
        except:
            return []
    return []


def save_reviews(reviews):
    """Save reviews to file"""
    with open(REVIEWS_FILE, 'w') as f:
        json.dump(reviews, f, indent=2)


def add_review(tool_name, user_id, user_name, user_email, rating, comment):
    """Add a new review for a tool"""
    reviews = load_reviews()
    
    # Check if user already reviewed this tool
    existing = next((r for r in reviews if r['tool_name'] == tool_name and r['user_id'] == user_id), None)
    
    if existing:
        # Update existing review
        existing['rating'] = rating
        existing['comment'] = comment
        existing['updated_at'] = datetime.now().isoformat()
        existing['edited'] = True
    else:
        # Create new review
        review = {
            'id': str(uuid.uuid4()),
            'tool_name': tool_name,
            'user_id': user_id,
            'user_name': user_name,
            'user_email': user_email,
            'rating': rating,
            'comment': comment,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'edited': False,
            'helpful_count': 0,
            'verified_purchase': False  # Can be set based on subscription
        }
        reviews.append(review)
    
    save_reviews(reviews)
    return {
        'success': True,
        'message': 'Review submitted successfully!' if not existing else 'Review updated successfully!'
    }


def get_tool_reviews(tool_name, limit=None, sort_by='recent'):
    """Get all reviews for a specific tool"""
    reviews = load_reviews()
    tool_reviews = [r for r in reviews if r['tool_name'] == tool_name]
    
    # Sort reviews
    if sort_by == 'recent':
        tool_reviews.sort(key=lambda x: x['created_at'], reverse=True)
    elif sort_by == 'rating_high':
        tool_reviews.sort(key=lambda x: x['rating'], reverse=True)
    elif sort_by == 'rating_low':
        tool_reviews.sort(key=lambda x: x['rating'])
    elif sort_by == 'helpful':
        tool_reviews.sort(key=lambda x: x.get('helpful_count', 0), reverse=True)
    
    if limit:
        tool_reviews = tool_reviews[:limit]
    
    return tool_reviews


def get_tool_rating_summary(tool_name):
    """Get rating summary for a tool"""
    reviews = get_tool_reviews(tool_name)
    
    if not reviews:
        return {
            'average_rating': 0,
            'total_reviews': 0,
            'rating_distribution': {5: 0, 4: 0, 3: 0, 2: 0, 1: 0}
        }
    
    total = len(reviews)
    avg = sum(r['rating'] for r in reviews) / total
    
    distribution = {5: 0, 4: 0, 3: 0, 2: 0, 1: 0}
    for review in reviews:
        distribution[review['rating']] += 1
    
    return {
        'average_rating': round(avg, 1),
        'total_reviews': total,
        'rating_distribution': distribution
    }


def delete_review(review_id, user_id):
    """Delete a review (only by the user who created it)"""
    reviews = load_reviews()
    review = next((r for r in reviews if r['id'] == review_id), None)
    
    if not review:
        return {'success': False, 'error': 'Review not found'}
    
    if review['user_id'] != user_id:
        return {'success': False, 'error': 'Unauthorized'}
    
    reviews = [r for r in reviews if r['id'] != review_id]
    save_reviews(reviews)
    
    return {'success': True, 'message': 'Review deleted successfully'}


def admin_delete_review(review_id):
    """Delete a review - Admin only (no user verification)"""
    reviews = load_reviews()
    review = next((r for r in reviews if r['id'] == review_id), None)
    
    if not review:
        return {'success': False, 'error': 'Review not found'}
    
    reviews = [r for r in reviews if r['id'] != review_id]
    save_reviews(reviews)
    
    return {'success': True, 'message': 'Review deleted successfully'}


def mark_helpful(review_id):
    """Mark a review as helpful"""
    reviews = load_reviews()
    review = next((r for r in reviews if r['id'] == review_id), None)
    
    if not review:
        return {'success': False, 'error': 'Review not found'}
    
    review['helpful_count'] = review.get('helpful_count', 0) + 1
    save_reviews(reviews)
    
    return {'success': True, 'helpful_count': review['helpful_count']}


def get_user_reviews(user_id):
    """Get all reviews by a specific user"""
    reviews = load_reviews()
    return [r for r in reviews if r['user_id'] == user_id]


def get_all_reviews_stats():
    """Get overall review statistics"""
    reviews = load_reviews()
    
    if not reviews:
        return {
            'total_reviews': 0,
            'average_rating': 0,
            'total_tools_reviewed': 0
        }
    
    total = len(reviews)
    avg = sum(r['rating'] for r in reviews) / total
    tools = len(set(r['tool_name'] for r in reviews))
    
    return {
        'total_reviews': total,
        'average_rating': round(avg, 1),
        'total_tools_reviewed': tools
    }

