#!/usr/bin/env python3
"""
Media Tool Web Interface
Beautiful UI for MP4 to MP3 conversion and YouTube downloads
"""

from flask import Flask, render_template, request, jsonify, send_file, Response, session, redirect, url_for, flash
from werkzeug.utils import secure_filename
from functools import wraps
import os
import sys
import json
import re
import subprocess
from pathlib import Path
from threading import Thread
import time
import uuid
import shutil
import zipfile
import yt_dlp
from media_tool import MediaTool
from download_history import DownloadHistory
from user_auth import (
    create_user, authenticate_user, get_user_by_email, 
    generate_session_token, get_user_stats, user_exists
)
from admin_auth import (
    authenticate_admin, create_admin, delete_admin,
    get_admin_stats, load_admins, admin_exists
)
from subscription import (
    get_user_subscription, check_usage_limit, increment_usage,
    upgrade_subscription, cancel_subscription, get_subscription_stats,
    PLANS
)
from reviews import (
    add_review, get_tool_reviews, get_tool_rating_summary,
    delete_review, mark_helpful, get_user_reviews, get_all_reviews_stats
)
from leaderboard import get_leaderboard_stats, get_user_rank
from discounts import (
    create_discount, get_active_discounts, get_tool_discount,
    deactivate_discount, delete_discount, get_all_discounts,
    calculate_discounted_price
)
from vip_access import (
    grant_vip_access, revoke_vip_access, is_vip_user,
    get_all_vip_users, check_unlimited_access
)
from pricing_settings import load_pricing, update_price, get_prices
from verification import send_verification_code, verify_code, cleanup_expired_codes


# Login required decorator
def login_required(f):
    """Decorator to require login for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this feature.', 'error')
            return redirect(url_for('login_page', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


# Admin login required decorator
def admin_required(f):
    """Decorator to require admin login for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            flash('Admin login required to access this page.', 'error')
            return redirect(url_for('admin_login_page'))
        return f(*args, **kwargs)
    return decorated_function


# Define which tools require paid access (admin must grant access)
PAID_TOOLS = [
    'Media Converter Pro',
    'Watermark Remover',
    'Media Downloader',
    'Audio Enhancer'
]

# Define free tools (anyone logged in can use)
FREE_TOOLS = [
    'Subtitle Downloader',
    'QR Code Generator',
    'Product QR Generator',
    'GIF Maker',
    'Duplicate File Finder',
    'File Encryptor',
    'Hook Analyzer',
    'Random Picker',
    'Trending Detector',
    'Social Media Search',
    'Social Media News'
]


# Tool access required decorator (only for paid tools)
def tool_access_required(tool_name):
    """Decorator to check if user has purchased or been granted access to a specific PAID tool"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Must be logged in first
            if 'user_id' not in session:
                flash('Please login to access this tool', 'error')
                return redirect(url_for('login_page', next=request.url))
            
            user_id = session.get('user_id')
            
            # Check if this is a free tool - if so, just allow access
            if tool_name in FREE_TOOLS:
                return f(*args, **kwargs)
            
            # For paid tools, check if they have pricing set
            # If no pricing is set, treat as free
            try:
                from discounts import get_tool_discount
                discount_info = get_tool_discount(tool_name)
                
                # If tool is marked as paid but has no discount/pricing, allow access (effectivelyFree)
                if not discount_info or not discount_info.get('is_active'):
                    print(f"[ACCESS] {tool_name} is paid but has no pricing set - allowing free access")
                    return f(*args, **kwargs)
                
                # If discount type is FREE, allow access
                if discount_info.get('discount_type') == 'free':
                    print(f"[ACCESS] {tool_name} has FREE discount - allowing access")
                    return f(*args, **kwargs)
                    
            except Exception as e:
                print(f"[ACCESS] Error checking discount for {tool_name}: {e}")
            
            # For paid tools with pricing, check access
            # Check if admin - admins have access to all tools
            if 'admin_id' in session:
                return f(*args, **kwargs)
            
            # Check if user has access to this paid tool
            try:
                from tool_purchases import has_tool_access
                
                # Check for direct tool access (purchased or granted)
                if has_tool_access(user_id, tool_name):
                    return f(*args, **kwargs)
                
                # Check for VIP/Employee access (unlimited access)
                vip_file = Path('vip_access.json')
                if vip_file.exists():
                    with open(vip_file, 'r') as file:
                        vip_users = json.load(file)
                        if user_id in vip_users:
                            vip_data = vip_users[user_id]
                            if isinstance(vip_data, dict) and vip_data.get('has_access', False):
                                return f(*args, **kwargs)
                
                # No access - redirect to tools page with error
                flash(f'⚠️ {tool_name} is a premium tool. Please contact admin to get access.', 'error')
                return redirect('/tools')
                
            except Exception as e:
                print(f"[ACCESS CHECK ERROR] {e}")
                flash('Error checking tool access. Please try again.', 'error')
                return redirect('/tools')
        
        return decorated_function
    return decorator


import cv2
import numpy as np
from PIL import Image
import io
import base64
from scipy.ndimage import distance_transform_edt
try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False

try:
    from deep_translator import GoogleTranslator
    TRANSLATOR_AVAILABLE = True
except ImportError:
    TRANSLATOR_AVAILABLE = False

try:
    import qrcode
    QRCODE_AVAILABLE = True
except ImportError:
    QRCODE_AVAILABLE = False

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives import hmac
    import secrets
    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False

try:
    import feedparser
    import requests
    from datetime import datetime, timedelta
    NEWS_API_AVAILABLE = True
except ImportError:
    NEWS_API_AVAILABLE = False

try:
    from pydub import AudioSegment
    from pydub.effects import normalize as pydub_normalize, compress_dynamic_range
    from pydub.silence import detect_nonsilent
    import noisereduce as nr
    AUDIO_ENHANCEMENT_AVAILABLE = True
except ImportError:
    AUDIO_ENHANCEMENT_AVAILABLE = False

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Secret key for sessions
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'

# Set output folder to user's Desktop
import os
desktop_path = Path.home() / 'Desktop' / 'RKIEH_Downloads'
app.config['OUTPUT_FOLDER'] = str(desktop_path)

app.config['PERMANENT_SESSION_LIFETIME'] = 86400  # 24 hours

# Create necessary folders
Path(app.config['UPLOAD_FOLDER']).mkdir(exist_ok=True)
Path(app.config['OUTPUT_FOLDER']).mkdir(parents=True, exist_ok=True)
print(f"✅ Downloads will be saved to: {app.config['OUTPUT_FOLDER']}")

# Store job status
jobs = {}

# Initialize media tool
media_tool = MediaTool()
download_history = DownloadHistory()

# Global error handler to always return JSON for API routes
@app.errorhandler(Exception)
def handle_error(error):
    """Handle all uncaught exceptions and return JSON for API routes"""
    import traceback
    error_trace = traceback.format_exc()
    print(f"ERROR: {error_trace}")
    
    # Check if it's an API route
    if request.path.startswith('/api/'):
        return jsonify({
            'success': False,
            'error': str(error)
        }), 200
    
    # For non-API routes, use default error handling
    raise error

# Cache cleanup configuration
CACHE_CLEANUP_INTERVAL = 60  # Check every 60 seconds
CACHE_MAX_AGE = 300  # 5 minutes in seconds

def add_job_timestamps(job_data):
    """Add timestamps to job data"""
    job_data['created_at'] = time.time()
    job_data['updated_at'] = time.time()
    return job_data

def update_job_timestamp(job_id):
    """Update timestamp when job status changes"""
    if job_id in jobs:
        jobs[job_id]['updated_at'] = time.time()


@app.route('/')
def home():
    """Home/landing page"""
    # Check if user is logged in
    user = None
    if 'user_id' in session:
        user_data = get_user_by_email(session.get('user_email'))
        if user_data:
            user = {k: v for k, v in user_data.items() if k != 'password'}
    return render_template('home.html', user=user)


# ============================================
# AUTHENTICATION ROUTES
# ============================================

@app.route('/login')
def login_page():
    """Login page"""
    if 'user_id' in session:
        return redirect('/')
    return render_template('login.html')


@app.route('/signup')
def signup_page():
    """Signup page"""
    if 'user_id' in session:
        return redirect('/')
    return render_template('signup.html')


@app.route('/api/signup', methods=['POST'])
def api_signup():
    """Handle user signup - simple registration"""
    try:
        data = request.json
        first_name = data.get('first_name', '').strip()
        last_name = data.get('last_name', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        
        # Create user directly
        result = create_user(first_name, last_name, email, password)
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': 'Account created successfully!'
            }), 201
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Signup failed: {str(e)}'
        }), 500


@app.route('/api/login', methods=['POST'])
def api_login():
    """Handle user login - Checks for admin first, then regular user"""
    try:
        data = request.json
        email = data.get('email', '').strip()
        password = data.get('password', '')
        remember = data.get('remember', False)
        
        # First, check if this is an admin login
        admin_result = authenticate_admin(email, password)
        
        if admin_result['success']:
            # This is an admin! Create admin session
            session['admin_id'] = admin_result['admin']['id']
            session['admin_email'] = admin_result['admin']['email']
            session['admin_name'] = admin_result['admin']['name']
            session['is_super_admin'] = admin_result['admin'].get('is_super_admin', False)
            session.permanent = True
            
            return jsonify({
                'success': True,
                'message': 'Admin login successful!',
                'redirect': '/admin',
                'is_admin': True,
                'admin': {
                    'name': session['admin_name'],
                    'email': session['admin_email']
                }
            }), 200
        
        # Not an admin, try regular user authentication
        result = authenticate_user(email, password)
        
        if result['success']:
            # Create user session
            session['user_id'] = result['user']['id']
            session['user_email'] = result['user']['email']
            session['user_name'] = f"{result['user']['first_name']} {result['user']['last_name']}"
            
            if remember:
                session.permanent = True
            
            return jsonify({
                'success': True,
                'message': 'Login successful!',
                'redirect': '/tools',
                'is_admin': False,
                'user': {
                    'name': session['user_name'],
                    'email': session['user_email']
                }
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 401
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Login failed: {str(e)}'
        }), 500


@app.route('/logout')
def logout():
    """Handle user logout"""
    session.clear()
    return redirect('/login')


@app.route('/profile')
@login_required
def profile():
    """User profile page with subscription info"""
    user_data = get_user_by_email(session.get('user_email'))
    if not user_data:
        session.clear()
        return redirect('/login')
    
    # Get subscription info
    subscription = get_user_subscription(session.get('user_id'))
    usage_info = check_usage_limit(session.get('user_id'))
    plan_info = PLANS[subscription['plan']]
    
    # Check VIP status
    is_vip = is_vip_user(session.get('user_id'))
    
    user = {k: v for k, v in user_data.items() if k != 'password'}
    return render_template('profile.html', 
                         user=user, 
                         subscription=subscription, 
                         usage_info=usage_info, 
                         plan_info=plan_info,
                         is_vip=is_vip)


@app.route('/api/profile/upload-avatar', methods=['POST'])
@login_required
def upload_avatar():
    """Upload profile avatar image"""
    try:
        if 'avatar' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file uploaded'
            }), 400
        
        file = request.files['avatar']
        
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400
        
        # Check file extension
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
        file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
        
        if file_ext not in allowed_extensions:
            return jsonify({
                'success': False,
                'error': 'Invalid file type. Please upload an image (PNG, JPG, GIF, or WEBP)'
            }), 400
        
        # Create avatars directory if it doesn't exist
        avatars_dir = Path('static/uploads/avatars')
        avatars_dir.mkdir(parents=True, exist_ok=True)
        
        # Save with user ID as filename
        user_id = session.get('user_id')
        filename = f"{user_id}.{file_ext}"
        filepath = avatars_dir / filename
        
        file.save(str(filepath))
        
        # Update user database with avatar path
        from user_auth import load_users
        users = load_users()
        user = next((u for u in users if u['id'] == user_id), None)
        
        if user:
            user['avatar'] = f'/static/uploads/avatars/{filename}'
            # Save users
            with open('users_database.json', 'w') as f:
                json.dump(users, f, indent=2)
        
        return jsonify({
            'success': True,
            'message': 'Avatar uploaded successfully!',
            'avatar_url': f'/static/uploads/avatars/{filename}'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/user/stats')
def api_user_stats():
    """Get user statistics"""
    stats = get_user_stats()
    
    # Add ratings count
    try:
        feedback_file = Path('feedback_database.json')
        if feedback_file.exists():
            with open(feedback_file, 'r') as f:
                feedback = json.load(f)
                stats['total_ratings'] = len(feedback)
        else:
            stats['total_ratings'] = 0
    except:
        stats['total_ratings'] = 0
    
    return jsonify(stats)


@app.route('/admin')
@admin_required
def admin_panel():
    """Admin panel - View all users (Admin login required)"""
    return render_template('admin.html')


@app.route('/admin/login')
def admin_login_page():
    """Admin login page"""
    if 'admin_id' in session:
        return redirect('/admin')
    return render_template('admin_login.html')


@app.route('/api/admin/login', methods=['POST'])
def api_admin_login():
    """Handle admin login"""
    try:
        data = request.json
        email = data.get('email', '').strip()
        password = data.get('password', '')
        
        # Authenticate admin
        result = authenticate_admin(email, password)
        
        if result['success']:
            # Create admin session
            session['admin_id'] = result['admin']['id']
            session['admin_email'] = result['admin']['email']
            session['admin_name'] = result['admin']['name']
            session['is_super_admin'] = result['admin'].get('is_super_admin', False)
            session.permanent = True
            
            return jsonify({
                'success': True,
                'message': 'Admin login successful!',
                'redirect': '/admin',
                'admin': {
                    'name': session['admin_name'],
                    'email': session['admin_email']
                }
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 401
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Admin login failed: {str(e)}'
        }), 500


@app.route('/admin/logout')
def admin_logout():
    """Handle admin logout"""
    session.pop('admin_id', None)
    session.pop('admin_email', None)
    session.pop('admin_name', None)
    session.pop('is_super_admin', None)
    return redirect('/admin/login')


@app.route('/admin/manage')
@admin_required
def admin_manage():
    """Admin management page - Add/Remove admins and view users"""
    return render_template('admin_manage.html')


@app.route('/admin/feedback')
@admin_required
def admin_feedback():
    """Admin feedback page - View user feedback"""
    return render_template('admin_feedback.html', is_admin_page=True)


@app.route('/admin/leaderboard')
@admin_required
def admin_leaderboard():
    """Admin leaderboard page - View top users"""
    return render_template('admin_leaderboard.html', is_admin_page=True)


@app.route('/admin/discounts')
@admin_required
def admin_discounts():
    """Admin discounts page - Manage discounts"""
    return render_template('admin_discounts.html', is_admin_page=True)


@app.route('/api/admin/discounts')
@admin_required
def api_get_discounts():
    """Get all discounts"""
    try:
        discounts = get_all_discounts()
        return jsonify({
            'success': True,
            'discounts': discounts
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/admin/discount/create', methods=['POST'])
@admin_required
def api_create_discount():
    """Create a new discount"""
    try:
        data = request.json
        tool_name = data.get('tool_name', '').strip()
        discount_type = data.get('discount_type', 'percentage')
        discount_value = float(data.get('discount_value', 0))
        original_price = data.get('original_price', None)  # New field
        description = data.get('description', '').strip()
        expires_at = data.get('expires_at', None)
        
        if not tool_name or discount_value <= 0:
            return jsonify({
                'success': False,
                'error': 'Invalid discount data'
            }), 400
        
        result = create_discount(tool_name, discount_type, discount_value, description, expires_at, original_price)
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/admin/discount/<discount_id>/deactivate', methods=['POST'])
@admin_required
def api_deactivate_discount(discount_id):
    """Deactivate a discount"""
    try:
        result = deactivate_discount(discount_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/admin/discount/<discount_id>', methods=['DELETE'])
@admin_required
def api_delete_discount(discount_id):
    """Delete a discount"""
    try:
        result = delete_discount(discount_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/discounts/active')
def api_get_active_discounts():
    """Get all active discounts (public)"""
    try:
        discounts = get_active_discounts()
        return jsonify({
            'success': True,
            'discounts': discounts
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/admin/leaderboard')
@admin_required
def api_admin_leaderboard():
    """Get leaderboard data"""
    try:
        stats = get_leaderboard_stats()
        return jsonify({
            'success': True,
            'data': stats
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/admin/users')
@admin_required
def api_admin_users():
    """Get all users (without passwords) - Admin only"""
    try:
        from user_auth import load_users
        users = load_users()
        
        # Get VIP users
        vip_users = get_all_vip_users()
        vip_ids = {v['user_id'] for v in vip_users if v.get('is_active')}
        
        # Get subscriptions
        subscriptions_file = Path('subscriptions_database.json')
        subscriptions = {}
        if subscriptions_file.exists():
            with open(subscriptions_file, 'r') as f:
                subscriptions = json.load(f)
        
        # Remove password from each user and add VIP status + plan
        safe_users = []
        for user in users:
            safe_user = {k: v for k, v in user.items() if k != 'password'}
            safe_user['is_vip'] = user['id'] in vip_ids
            
            # Add subscription plan
            sub = subscriptions.get(user['id'], {})
            safe_user['plan'] = sub.get('plan', 'Free')
            
            safe_users.append(safe_user)
        
        return jsonify({
            'success': True,
            'users': safe_users,
            'count': len(safe_users)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/admin/vip/grant', methods=['POST'])
@admin_required
def api_grant_vip():
    """Grant VIP or Employee access to a user"""
    try:
        data = request.json
        user_id = data.get('user_id', '').strip()
        user_email = data.get('user_email', '').strip()
        reason = data.get('reason', '').strip()
        access_type = data.get('access_type', 'vip').strip()  # 'vip' or 'employee'
        
        admin_email = session.get('admin_email', 'admin')
        
        result = grant_vip_access(user_id, user_email, admin_email, reason, access_type)
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/admin/vip/revoke', methods=['POST'])
@admin_required
def api_revoke_vip():
    """Revoke VIP access from a user"""
    try:
        data = request.json
        user_id = data.get('user_id', '').strip()
        
        result = revoke_vip_access(user_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/admin/list')
@admin_required
def api_admin_list():
    """Get all admins - Admin only"""
    try:
        admins = load_admins()
        
        # Remove passwords
        safe_admins = []
        for admin in admins:
            safe_admin = {k: v for k, v in admin.items() if k != 'password'}
            safe_admins.append(safe_admin)
        
        return jsonify({
            'success': True,
            'admins': safe_admins,
            'count': len(safe_admins)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/admin/create', methods=['POST'])
@admin_required
def api_admin_create():
    """Create new admin - Admin only"""
    try:
        data = request.json
        email = data.get('email', '').strip()
        password = data.get('password', '')
        name = data.get('name', '').strip()
        
        result = create_admin(email, password, name)
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': 'Admin created successfully!'
            }), 201
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/admin/delete/<admin_id>', methods=['DELETE'])
@admin_required
def api_admin_delete(admin_id):
    """Delete admin - Admin only"""
    try:
        result = delete_admin(admin_id)
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': 'Admin deleted successfully!'
            })
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/pricing')
def pricing_page():
    """Pricing page"""
    user_plan = 'free'
    if 'user_id' in session:
        subscription = get_user_subscription(session.get('user_id'))
        user_plan = subscription['plan']
    
    # Get current prices
    prices = get_prices()
    
    return render_template('pricing.html', user_plan=user_plan, prices=prices)


@app.route('/admin/pricing')
@admin_required
def admin_pricing():
    """Admin pricing management page"""
    return render_template('admin_pricing.html', is_admin_page=True)


@app.route('/admin/tool-access')
@admin_required
def admin_tool_access():
    """Admin tool access analytics page"""
    return render_template('admin_tool_access.html', is_admin_page=True)


@app.route('/api/admin/pricing')
@admin_required
def api_get_pricing():
    """Get current pricing"""
    try:
        prices = get_prices()
        return jsonify({
            'success': True,
            'prices': prices
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/admin/pricing/update', methods=['POST'])
@admin_required
def api_update_pricing():
    """Update plan pricing, features, and limits"""
    try:
        from pricing_settings import update_plan
        
        data = request.json
        plan = data.get('plan', '').strip().lower()
        price = data.get('price')
        daily_limit = data.get('daily_limit')
        features = data.get('features')
        
        # Convert price to float if provided
        if price is not None:
            price = float(price)
        
        # Convert daily_limit to int if provided
        if daily_limit is not None:
            daily_limit = int(daily_limit)
        
        result = update_plan(plan, new_price=price, daily_limit=daily_limit, features=features)
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/admin/tool-access')
@admin_required
def api_get_tool_access():
    """Get tool access analytics - which users have access to each tool"""
    try:
        from tool_purchases import get_all_purchases
        from tool_usage import get_all_tool_usage
        
        # Tool definitions with icons
        tools_list = [
            {'name': 'Media Converter Pro', 'icon': 'fas fa-exchange-alt'},
            {'name': 'Watermark Remover', 'icon': 'fas fa-eraser'},
            {'name': 'Media Downloader', 'icon': 'fas fa-download'},
            {'name': 'Subtitle Downloader', 'icon': 'fas fa-closed-captioning'},
            {'name': 'QR Code Generator', 'icon': 'fas fa-qrcode'},
            {'name': 'Product QR Generator', 'icon': 'fas fa-barcode'},
            {'name': 'GIF Maker', 'icon': 'fas fa-film'},
            {'name': 'Duplicate File Finder', 'icon': 'fas fa-clone'},
            {'name': 'File Encryptor', 'icon': 'fas fa-lock'},
            {'name': 'Hook Analyzer', 'icon': 'fas fa-chart-line'},
            {'name': 'Random Picker', 'icon': 'fas fa-random'},
            {'name': 'Trending Detector', 'icon': 'fas fa-fire'},
            {'name': 'Social Media Search', 'icon': 'fas fa-search'},
            {'name': 'Social Media News', 'icon': 'fas fa-newspaper'},
            {'name': 'Audio Enhancer', 'icon': 'fas fa-volume-up'}
        ]
        
        # Get all users
        users_db_file = Path('users_database.json')
        subscriptions_db_file = Path('subscriptions_database.json')
        vip_file = Path('vip_access.json')
        
        users = []
        if users_db_file.exists():
            with open(users_db_file, 'r') as f:
                users_data = json.load(f)
                # Handle both formats: direct array or nested under 'users' key
                if isinstance(users_data, dict) and 'users' in users_data:
                    users = users_data['users']
                elif isinstance(users_data, list):
                    users = users_data
                else:
                    users = []
                print(f"[TOOL ACCESS] Loaded {len(users)} users from database")
        
        # Get subscriptions
        subscriptions = {}
        if subscriptions_db_file.exists():
            with open(subscriptions_db_file, 'r') as f:
                subscriptions = json.load(f)
        
        # Get VIP/Employee access
        vip_users = {}
        if vip_file.exists():
            with open(vip_file, 'r') as f:
                vip_users = json.load(f)
        
        # Get tool purchases
        purchases = get_all_purchases()
        
        # Get tool usage statistics
        usage_stats = get_all_tool_usage()
        
        # Build tools data with users
        tools_with_users = []
        
        for tool in tools_list:
            tool_users = []
            
            for user in users:
                # Ensure user is a dictionary
                if not isinstance(user, dict):
                    continue
                    
                user_id = user.get('id', '')
                
                # Construct full name from first_name and last_name
                first_name = user.get('first_name', user.get('name', ''))
                last_name = user.get('last_name', '')
                if first_name and last_name:
                    user_name = f"{first_name} {last_name}"
                elif first_name:
                    user_name = first_name
                else:
                    user_name = user.get('name', 'Unknown')
                
                user_email = user.get('email', '')
                
                # Get user's subscription/plan
                sub = subscriptions.get(user_id, {})
                # Ensure sub is a dictionary
                if not isinstance(sub, dict):
                    sub = {}
                plan = sub.get('plan', 'Free')
                
                # Check for VIP/Employee access
                if user_id in vip_users:
                    vip_data = vip_users[user_id]
                    # Ensure vip_data is a dictionary
                    if isinstance(vip_data, dict):
                        if vip_data.get('has_access', False):
                            access_type = vip_data.get('access_type', 'VIP')
                            plan = access_type.title()
                
                # Get user initials
                name_parts = user_name.split()
                initials = ''.join([part[0].upper() for part in name_parts[:2]]) if name_parts else 'U'
                
                # Check if user has specific tool access
                tool_access = None
                access_type_badge = ''
                purchase_date = None
                
                if user_id in purchases and tool['name'] in purchases[user_id]:
                    tool_access = purchases[user_id][tool['name']]
                    # Format access type badge
                    if tool_access.get('access_type') == 'purchase':
                        access_type_badge = 'Purchased'
                    elif tool_access.get('access_type') == 'free_grant':
                        access_type_badge = 'Free Grant'
                    else:
                        access_type_badge = tool_access.get('access_type', 'Unknown').replace('_', ' ').title()
                    
                    # Get purchase/grant date
                    purchase_date = tool_access.get('granted_at', tool_access.get('purchase_date'))
                    
                    print(f"[TOOL ACCESS DEBUG] User {user_name} has access to {tool['name']}: {access_type_badge}")
                
                # Check how many times user used this tool
                usage_count = 0
                if tool['name'] in usage_stats:
                    tool_usage_data = usage_stats[tool['name']]
                    usage_log = tool_usage_data.get('usage_log', [])
                    usage_count = len([log for log in usage_log if log.get('user_id') == user_id])
                
                # Only add users who have actually used or have access to the tool
                if tool_access or usage_count > 0:
                    user_info = {
                        'name': user_name,
                        'email': user_email,
                        'plan': plan,
                        'initials': initials,
                        'user_id': user_id,
                        'access_type_badge': access_type_badge,
                        'purchase_date': purchase_date,
                        'uses_count': usage_count
                    }
                    tool_users.append(user_info)
                    print(f"[TOOL ACCESS] Added user to {tool['name']}: {user_name} ({access_type_badge})")
            
            # Calculate statistics for this tool
            purchased_count = 0
            granted_count = 0
            launched_count = 0
            
            # Count purchases and grants
            for user_data in tool_users:
                if user_data.get('access_type_badge') == 'Purchased':
                    purchased_count += 1
                elif user_data.get('access_type_badge') == 'Free Grant':
                    granted_count += 1
            
            # Get total launches for this tool
            if tool['name'] in usage_stats:
                usage_log = usage_stats[tool['name']].get('usage_log', [])
                launched_count = len(usage_log)
            
            tools_with_users.append({
                'name': tool['name'],
                'icon': tool['icon'],
                'users': tool_users,
                'purchased_count': purchased_count,
                'granted_count': granted_count,
                'launched_count': launched_count
            })
            
            print(f"[TOOL ACCESS] {tool['name']}: {len(tool_users)} users (Purchased: {purchased_count}, Granted: {granted_count}, Launched: {launched_count})")
        
        # Calculate totals
        total_purchases = sum(tool['purchased_count'] for tool in tools_with_users)
        total_grants = sum(tool['granted_count'] for tool in tools_with_users)
        total_launches = sum(tool['launched_count'] for tool in tools_with_users)
        
        return jsonify({
            'success': True,
            'tools': tools_with_users,
            'total_users': len(users),
            'total_purchases': total_purchases,
            'total_grants': total_grants,
            'total_launches': total_launches
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/admin/grant-tool-access', methods=['POST'])
@admin_required
def api_grant_tool_access():
    """Grant a user free access to a specific tool - Admin only"""
    try:
        from tool_purchases import grant_tool_access, load_purchases
        
        data = request.json
        user_id = data.get('user_id', '').strip()
        tool_name = data.get('tool_name', '').strip()
        
        print(f"\n{'='*60}")
        print(f"[GRANT ACCESS] REQUEST RECEIVED")
        print(f"{'='*60}")
        print(f"Request Data: {data}")
        print(f"User ID: '{user_id}'")
        print(f"Tool Name: '{tool_name}'")
        print(f"Admin: {session.get('admin_email')}")
        
        if not user_id or not tool_name:
            print(f"[GRANT ACCESS] ❌ FAILED - Missing user_id or tool_name")
            return jsonify({
                'success': False,
                'error': 'User ID and tool name are required'
            }), 400
        
        # Show current state BEFORE grant
        purchases_before = load_purchases()
        print(f"\n[BEFORE GRANT] tool_purchases.json contents:")
        print(json.dumps(purchases_before, indent=2))
        
        # Grant access
        result = grant_tool_access(user_id, tool_name, granted_by='admin', access_type='free_grant')
        print(f"\n[GRANT RESULT] {result}")
        
        # Show current state AFTER grant
        purchases_after = load_purchases()
        print(f"\n[AFTER GRANT] tool_purchases.json contents:")
        print(json.dumps(purchases_after, indent=2))
        
        # Verify the grant was saved
        if result.get('success'):
            if user_id in purchases_after and tool_name in purchases_after[user_id]:
                print(f"[GRANT ACCESS] ✅ SUCCESS - Access granted and saved!")
            else:
                print(f"[GRANT ACCESS] ⚠️ WARNING - Grant succeeded but not found in file!")
        else:
            print(f"[GRANT ACCESS] ❌ FAILED - {result.get('error')}")
        
        print(f"{'='*60}\n")
        return jsonify(result)
        
    except Exception as e:
        print(f"[GRANT ACCESS] ❌ EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/admin/revoke-tool-access', methods=['POST'])
@admin_required
def api_revoke_tool_access():
    """Revoke a user's access to a specific tool - Admin only"""
    try:
        from tool_purchases import revoke_tool_access, load_purchases
        
        data = request.json
        user_id = data.get('user_id', '').strip()
        tool_name = data.get('tool_name', '').strip()
        
        print(f"\n{'='*60}")
        print(f"[REVOKE ACCESS] REQUEST RECEIVED")
        print(f"{'='*60}")
        print(f"Request Data: {data}")
        print(f"User ID: '{user_id}'")
        print(f"Tool Name: '{tool_name}'")
        print(f"Admin: {session.get('admin_email')}")
        
        if not user_id or not tool_name:
            print(f"[REVOKE ACCESS] ❌ FAILED - Missing user_id or tool_name")
            return jsonify({
                'success': False,
                'error': 'User ID and tool name are required'
            }), 400
        
        # Show current state BEFORE revoke
        purchases_before = load_purchases()
        print(f"\n[BEFORE REVOKE] tool_purchases.json contents:")
        print(json.dumps(purchases_before, indent=2))
        print(f"User '{user_id}' exists: {user_id in purchases_before}")
        if user_id in purchases_before:
            print(f"User's tools: {list(purchases_before[user_id].keys())}")
            print(f"Has '{tool_name}': {tool_name in purchases_before[user_id]}")
        
        # Revoke access
        result = revoke_tool_access(user_id, tool_name)
        print(f"\n[REVOKE RESULT] {result}")
        
        # Show current state AFTER revoke
        purchases_after = load_purchases()
        print(f"\n[AFTER REVOKE] tool_purchases.json contents:")
        print(json.dumps(purchases_after, indent=2))
        
        # Verify the revoke was saved
        if result.get('success'):
            if user_id not in purchases_after or tool_name not in purchases_after.get(user_id, {}):
                print(f"[REVOKE ACCESS] ✅ SUCCESS - Access revoked and saved!")
            else:
                print(f"[REVOKE ACCESS] ⚠️ WARNING - Revoke succeeded but still found in file!")
        else:
            print(f"[REVOKE ACCESS] ❌ FAILED - {result.get('error')}")
        
        print(f"{'='*60}\n")
        return jsonify(result)
        
    except Exception as e:
        print(f"[REVOKE ACCESS] ❌ EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/subscription/upgrade', methods=['POST'])
@login_required
def api_subscription_upgrade():
    """Upgrade user subscription"""
    try:
        data = request.json
        plan = data.get('plan', '').strip()
        payment_method = data.get('payment_method', 'card')
        
        result = upgrade_subscription(
            session.get('user_id'), 
            plan,
            {'method': payment_method}
        )
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': f'Successfully upgraded to {plan.upper()} plan!'
            })
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/subscription/cancel', methods=['POST'])
@login_required
def api_subscription_cancel():
    """Cancel user subscription"""
    try:
        result = cancel_subscription(session.get('user_id'))
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/subscription/info')
@login_required
def api_subscription_info():
    """Get user's subscription info"""
    try:
        subscription = get_user_subscription(session.get('user_id'))
        usage_info = check_usage_limit(session.get('user_id'))
        plan_info = PLANS[subscription['plan']]
        
        return jsonify({
            'success': True,
            'subscription': subscription,
            'usage': usage_info,
            'plan': plan_info
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/admin/feedback')
@admin_required
def api_admin_feedback():
    """Get all tool feedback and ratings - Admin only"""
    try:
        # Load reviews from reviews database
        from reviews import get_all_reviews_stats
        
        reviews_file = Path('reviews_database.json')
        
        if reviews_file.exists():
            with open(reviews_file, 'r') as f:
                reviews_data = json.load(f)
                
            # Format reviews for admin panel
            feedback = []
            for review in reviews_data:
                feedback.append({
                    'tool_name': review.get('tool_name', 'Unknown'),
                    'user_name': review.get('user_name', 'Anonymous'),
                    'user_email': review.get('user_email', ''),
                    'rating': int(review.get('rating', 0)),  # Ensure rating is int
                    'feedback_text': review.get('comment', ''),
                    'created_at': review.get('created_at', ''),  # Keep as string (ISO format)
                    'helpful_count': review.get('helpful_count', 0),
                    'review_id': review.get('id', '')
                })
        else:
            feedback = []
        
        return jsonify({
            'success': True,
            'feedback': feedback,
            'count': len(feedback)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/admin/feedback/<review_id>', methods=['DELETE'])
@admin_required
def api_delete_feedback(review_id):
    """Delete feedback/review - Admin only"""
    try:
        from reviews import admin_delete_review
        
        # Delete the review (admin can delete any review)
        result = admin_delete_review(review_id)
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': 'Feedback deleted successfully!'
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Failed to delete feedback')
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/tool/quick-rate', methods=['POST'])
@login_required
def api_tool_quick_rate():
    """Submit quick star rating (no comment required)"""
    try:
        data = request.json
        tool_name = data.get('tool_name', '').strip()
        rating = int(data.get('rating', 0))
        
        if not tool_name or rating < 1 or rating > 5:
            return jsonify({
                'success': False,
                'error': 'Invalid rating'
            }), 400
        
        # Get user info
        user_id = session.get('user_id')
        user_email = session.get('user_email', 'anonymous')
        user_name = session.get('user_name', 'Anonymous User')
        
        # Add review with auto-generated comment
        comment = f"Rated {rating} stars"
        result = add_review(tool_name, user_id, user_name, user_email, rating, comment)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/tool/review', methods=['POST'])
@login_required
def api_tool_review():
    """Submit tool review/comment"""
    try:
        data = request.json
        tool_name = data.get('tool_name', '').strip()
        rating = int(data.get('rating', 0))
        comment = data.get('comment', '').strip()
        
        if not tool_name or rating < 1 or rating > 5:
            return jsonify({
                'success': False,
                'error': 'Invalid review data'
            }), 400
        
        if not comment:
            return jsonify({
                'success': False,
                'error': 'Please write a comment'
            }), 400
        
        # Get user info
        user_id = session.get('user_id')
        user_email = session.get('user_email', 'anonymous')
        user_name = session.get('user_name', 'Anonymous User')
        
        # Add review
        result = add_review(tool_name, user_id, user_name, user_email, rating, comment)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/tool/reviews/<tool_name>')
def api_get_tool_reviews(tool_name):
    """Get reviews for a specific tool"""
    try:
        sort_by = request.args.get('sort', 'recent')
        limit = request.args.get('limit', type=int)
        
        reviews = get_tool_reviews(tool_name, limit=limit, sort_by=sort_by)
        summary = get_tool_rating_summary(tool_name)
        
        return jsonify({
            'success': True,
            'reviews': reviews,
            'summary': summary
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/tool/review/<review_id>/helpful', methods=['POST'])
@login_required
def api_mark_review_helpful(review_id):
    """Mark a review as helpful"""
    try:
        result = mark_helpful(review_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/tool/review/<review_id>', methods=['DELETE'])
@login_required
def api_delete_review(review_id):
    """Delete a review"""
    try:
        result = delete_review(review_id, session.get('user_id'))
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/tool/feedback', methods=['POST'])
@login_required
def api_tool_feedback():
    """Submit tool feedback and rating (kept for backwards compatibility)"""
    try:
        data = request.json
        tool_name = data.get('tool_name', '').strip()
        rating = int(data.get('rating', 0))
        feedback_text = data.get('feedback', '').strip()
        
        if not tool_name or rating < 1 or rating > 5:
            return jsonify({
                'success': False,
                'error': 'Invalid feedback data'
            }), 400
        
        # Get user info
        user_email = session.get('user_email', 'anonymous')
        user_name = session.get('user_name', 'Anonymous User')
        
        # Load existing feedback
        feedback_file = Path('feedback_database.json')
        
        if feedback_file.exists():
            with open(feedback_file, 'r') as f:
                all_feedback = json.load(f)
        else:
            all_feedback = []
        
        # Add new feedback
        new_feedback = {
            'id': str(uuid.uuid4()),
            'tool_name': tool_name,
            'rating': rating,
            'feedback_text': feedback_text,
            'user_email': user_email,
            'user_name': user_name,
            'created_at': time.time()
        }
        
        all_feedback.append(new_feedback)
        
        # Save feedback
        with open(feedback_file, 'w') as f:
            json.dump(all_feedback, f, indent=2)
        
        return jsonify({
            'success': True,
            'message': 'Thank you for your feedback!'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/admin/stats')
@admin_required
def api_admin_stats():
    """Get admin statistics - Admin only"""
    stats = get_admin_stats()
    return jsonify(stats)


# ============================================
# END AUTHENTICATION ROUTES
# ============================================


@app.route('/api/server-info')
def server_info():
    """Get current server network information"""
    import socket
    try:
        # Get local IP address
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        
        return jsonify({
            'success': True,
            'local_ip': local_ip,
            'port': 5001,
            'localhost_url': 'http://localhost:5001',
            'network_url': f'http://{local_ip}:5001'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })


@app.route('/tools')
def tools():
    """Tools listing page - Public (can browse, but must login to use)"""
    return render_template('tools.html')


@app.route('/api/my-tool-access')
@login_required
def api_my_tool_access():
    """Get list of tools the current user has access to"""
    try:
        from tool_purchases import get_user_tool_purchases
        from vip_access import check_unlimited_access
        
        user_id = session.get('user_id')
        
        print(f"\n{'='*60}")
        print(f"[MY TOOL ACCESS] User {user_id} checking tool access")
        print(f"{'='*60}")
        
        # Get tools user has purchased or been granted access to
        user_tools = get_user_tool_purchases(user_id)
        tool_names = list(user_tools.keys()) if user_tools else []
        
        print(f"[MY TOOL ACCESS] User tools: {user_tools}")
        print(f"[MY TOOL ACCESS] Tool names: {tool_names}")
        
        # Check if user has VIP/Employee unlimited access
        unlimited_check = check_unlimited_access(user_id)
        has_unlimited = unlimited_check.get('unlimited', False) if isinstance(unlimited_check, dict) else bool(unlimited_check)
        
        print(f"[MY TOOL ACCESS] Has unlimited: {has_unlimited}")
        print(f"[MY TOOL ACCESS] Returning: {tool_names}")
        print(f"{'='*60}\n")
        
        return jsonify({
            'success': True,
            'tools': tool_names,
            'has_unlimited_access': has_unlimited
        })
        
    except Exception as e:
        print(f"[API ERROR] Error getting user tool access: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': True,
            'tools': [],
            'has_unlimited_access': False
        })


@app.route('/checkout/<tool_name>')
@login_required
def checkout(tool_name):
    """Checkout page for purchasing a tool - Uses dynamic pricing from discounts"""
    from discounts import get_tool_discount, get_active_discounts
    
    # Tool descriptions
    tool_descriptions = {
        'Media Converter Pro': 'Convert between audio and video formats with professional quality',
        'Watermark Remover': 'Remove watermarks, logos, and text overlays from images',
        'Media Downloader': 'Download videos from YouTube, Instagram, Facebook, and TikTok',
        'Audio Enhancer': 'Clean voice and reduce noise from audio files with AI',
        'Hook Analyzer': 'Analyze the strength of your content\'s opening hook. Perfect for TikTok, Instagram Reels, YouTube, and more.'
    }
    
    # Check if user already has access
    from tool_purchases import has_tool_access
    user_id = session.get('user_id')
    if has_tool_access(user_id, tool_name):
        flash(f'You already have access to {tool_name}!', 'success')
        return redirect(f'/tool/{tool_name.lower().replace(" ", "-")}')
    
    # Get discount information for this tool
    discount_info = get_tool_discount(tool_name)
    
    if discount_info and discount_info.get('is_active'):
        # Use discount pricing
        original_price = discount_info.get('original_price', 0)
        discount_type = discount_info.get('discount_type')
        discount_value = discount_info.get('discount_value', 0)
        
        if discount_type == 'percentage':
            final_price = original_price - (original_price * discount_value / 100)
            discount_percent = discount_value
        elif discount_type == 'fixed':
            final_price = original_price - discount_value
            discount_percent = int((discount_value / original_price) * 100) if original_price > 0 else 0
        elif discount_type == 'free':
            flash(f'{tool_name} is currently FREE! Granting access...', 'success')
            from tool_purchases import grant_tool_access
            grant_tool_access(user_id, tool_name, 'Free Discount', 0)
            return redirect(f'/tool/{tool_name.lower().replace(" ", "-")}')
        else:
            final_price = original_price
            discount_percent = 0
    else:
        # No discount - tool not available for purchase
        flash(f'{tool_name} pricing is not set yet. Please contact admin.', 'error')
        return redirect('/tools')
    
    return render_template('checkout.html',
                          tool_name=tool_name,
                          tool_description=tool_descriptions.get(tool_name, 'Professional tool for content creators'),
                          price=final_price,
                          original_price=original_price,
                          discount=discount_percent,
                          tool_url=f'/tool/{tool_name.lower().replace(" ", "-")}')


@app.route('/api/process-payment', methods=['POST'])
@login_required
def process_payment():
    """Process payment and grant tool access"""
    try:
        data = request.json
        tool_name = data.get('tool_name')
        amount = data.get('amount')
        card_name = data.get('card_name')
        card_number = data.get('card_number')
        
        if not all([tool_name, amount, card_name, card_number]):
            return jsonify({'success': False, 'error': 'Missing payment information'}), 400
        
        user_id = session.get('user_id')
        
        # In a real app, you would:
        # 1. Validate card with payment processor (Stripe, PayPal, etc.)
        # 2. Process actual payment
        # 3. Handle payment confirmation
        
        # For now, simulate successful payment and grant access
        from tool_purchases import grant_tool_access
        
        result = grant_tool_access(
            user_id=user_id,
            tool_name=tool_name,
            granted_by='purchase',
            access_type='purchase'
        )
        
        if result['success']:
            print(f"[PAYMENT SUCCESS] User {user_id} purchased {tool_name} for ${amount}")
            return jsonify({
                'success': True,
                'message': f'Successfully purchased {tool_name}!',
                'tool_name': tool_name
            })
        else:
            return jsonify({'success': False, 'error': result.get('error', 'Failed to grant access')}), 500
            
    except Exception as e:
        print(f"[PAYMENT ERROR] {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/about')
def about():
    """About page"""
    return render_template('about.html')


@app.route('/terms')
def terms():
    """Terms of Service page"""
    return render_template('terms.html')


@app.route('/privacy')
def privacy():
    """Privacy Policy page"""
    return render_template('privacy.html')


@app.route('/coming-soon')
def coming_soon():
    """Coming Soon page with 5 great features"""
    return render_template('coming_soon.html')


@app.route('/tool/media-converter')
@tool_access_required('Media Converter Pro')
def media_converter():
    """Media converter tool page - Access Required"""
    # Track tool usage
    try:
        from tool_usage import track_tool_usage
        user_id = session.get('user_id')
        if user_id:
            track_tool_usage('Media Converter Pro', user_id)
    except Exception as e:
        print(f"Error tracking usage: {e}")
    
    return render_template('media_converter.html')


@app.route('/tool/watermark-remover')
@tool_access_required('Watermark Remover')
def watermark_remover():
    """Watermark removal tool page - Access Required"""
    # Track tool usage
    try:
        from tool_usage import track_tool_usage
        user_id = session.get('user_id')
        if user_id:
            track_tool_usage('Watermark Remover', user_id)
    except Exception as e:
        print(f"Error tracking usage: {e}")
    
    return render_template('watermark_remover.html')


@app.route('/history')
def history_page():
    """Download History page"""
    return render_template('history.html')


@app.route('/tool/subtitle-downloader')
@tool_access_required('Subtitle Downloader')
def subtitle_downloader():
    """Subtitle Downloader tool page - Free Access"""
    # Track tool usage
    try:
        from tool_usage import track_tool_usage
        user_id = session.get('user_id')
        if user_id:
            track_tool_usage('Subtitle Downloader', user_id)
    except Exception as e:
        print(f"Error tracking usage: {e}")
    
    return render_template('subtitle_downloader.html')


@app.route('/tool/media-downloader')
@tool_access_required('Media Downloader')
def media_downloader():
    """Media Downloader tool page - Access Required"""
    # Track tool usage
    try:
        from tool_usage import track_tool_usage
        user_id = session.get('user_id')
        if user_id:
            track_tool_usage('Media Downloader', user_id)
    except Exception as e:
        print(f"Error tracking usage: {e}")
    
    return render_template('media_downloader.html')


@app.route('/tool/qr-generator')
@tool_access_required('QR Code Generator')
def qr_generator():
    """QR Code Generator tool page - Free Access"""
    # Track tool usage
    try:
        from tool_usage import track_tool_usage
        user_id = session.get('user_id')
        if user_id:
            track_tool_usage('QR Code Generator', user_id)
    except Exception as e:
        print(f"Error tracking usage: {e}")
    
    return render_template('qr_generator.html')


@app.route('/tool/product-qr-generator')
@tool_access_required('Product QR Generator')
def product_qr_generator():
    """Product QR Generator tool page - Free Access"""
    # Track tool usage
    try:
        from tool_usage import track_tool_usage
        user_id = session.get('user_id')
        if user_id:
            track_tool_usage('Product QR Generator', user_id)
    except Exception as e:
        print(f"Error tracking usage: {e}")
    
    return render_template('product_qr_generator.html')


@app.route('/tool/gif-maker')
@tool_access_required('GIF Maker')
def gif_maker():
    """GIF Maker tool page - Free Access"""
    # Track tool usage
    try:
        from tool_usage import track_tool_usage
        user_id = session.get('user_id')
        if user_id:
            track_tool_usage('GIF Maker', user_id)
    except Exception as e:
        print(f"Error tracking usage: {e}")
    
    return render_template('gif_maker.html')


@app.route('/tool/duplicate-finder')
@tool_access_required('Duplicate File Finder')
def duplicate_finder():
    """Duplicate File Finder tool page - Free Access"""
    # Track tool usage
    try:
        from tool_usage import track_tool_usage
        user_id = session.get('user_id')
        if user_id:
            track_tool_usage('Duplicate File Finder', user_id)
    except Exception as e:
        print(f"Error tracking usage: {e}")
    
    return render_template('duplicate_finder.html')


@app.route('/tool/file-encryptor')
@tool_access_required('File Encryptor')
def file_encryptor():
    """File Encryptor tool page - Free Access"""
    # Track tool usage
    try:
        from tool_usage import track_tool_usage
        user_id = session.get('user_id')
        if user_id:
            track_tool_usage('File Encryptor', user_id)
    except Exception as e:
        print(f"Error tracking usage: {e}")
    
    return render_template('file_encryptor.html')


@app.route('/tool/hook-analyzer')
@tool_access_required('Hook Analyzer')
def hook_analyzer():
    """Hook Analyzer tool page - Free Access"""
    # Track tool usage
    try:
        from tool_usage import track_tool_usage
        user_id = session.get('user_id')
        if user_id:
            track_tool_usage('Hook Analyzer', user_id)
    except Exception as e:
        print(f"Error tracking usage: {e}")
    
    return render_template('hook_analyzer.html')


@app.route('/tool/random-picker')
@tool_access_required('Random Picker')
def random_picker():
    """Random Picker tool page - Free Access"""
    # Track tool usage
    try:
        from tool_usage import track_tool_usage
        user_id = session.get('user_id')
        if user_id:
            track_tool_usage('Random Picker', user_id)
    except Exception as e:
        print(f"Error tracking usage: {e}")
    
    return render_template('random_picker.html')


@app.route('/tool/trending-detector')
@tool_access_required('Trending Detector')
def trending_detector():
    """Trending Detector tool page - Free Access"""
    # Track tool usage
    try:
        from tool_usage import track_tool_usage
        user_id = session.get('user_id')
        if user_id:
            track_tool_usage('Trending Detector', user_id)
    except Exception as e:
        print(f"Error tracking usage: {e}")
    
    return render_template('trending_detector.html')


@app.route('/tool/social-media-search')
@tool_access_required('Social Media Search')
def social_media_search():
    """Social Media Search tool page - Free Access"""
    # Track tool usage
    try:
        from tool_usage import track_tool_usage
        user_id = session.get('user_id')
        if user_id:
            track_tool_usage('Social Media Search', user_id)
    except Exception as e:
        print(f"Error tracking usage: {e}")
    
    return render_template('social_media_search.html')


@app.route('/tool/social-media-news')
@tool_access_required('Social Media News')
def social_media_news():
    """Social Media News Search tool page - Free Access"""
    # Track tool usage
    try:
        from tool_usage import track_tool_usage
        user_id = session.get('user_id')
        if user_id:
            track_tool_usage('Social Media News', user_id)
    except Exception as e:
        print(f"Error tracking usage: {e}")
    
    return render_template('social_media_news.html')


@app.route('/tool/audio-enhancer')
@tool_access_required('Audio Enhancer')
def audio_enhancer():
    """Audio Enhancer tool page - Access Required"""
    # Track tool usage
    try:
        from tool_usage import track_tool_usage
        user_id = session.get('user_id')
        if user_id:
            track_tool_usage('Audio Enhancer', user_id)
    except Exception as e:
        print(f"Error tracking usage: {e}")
    
    return render_template('audio_enhancer.html')


@app.route('/extract-video-comments', methods=['POST'])
def extract_video_comments():
    """Extract comments from a video URL"""
    try:
        data = request.json
        url = data.get('url', '').strip()
        
        if not url:
            return jsonify({'error': 'URL is required'}), 400
        
        # Detect platform
        if 'youtube.com' in url or 'youtu.be' in url:
            return extract_youtube_comments(url)
        elif 'tiktok.com' in url:
            return extract_tiktok_comments(url)
        elif 'instagram.com' in url:
            return extract_instagram_comments(url)
        else:
            return jsonify({'error': 'Unsupported platform. Please use YouTube, TikTok, or Instagram URLs.'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def extract_youtube_comments(url):
    """Extract comments from YouTube video using yt-dlp"""
    try:
        import yt_dlp
        
        # Configure yt-dlp to extract comments
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'getcomments': True,
            'writesubtitles': False,
            'writeautomaticsub': False,
        }
        
        comments = []
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                # Extract video info
                info = ydl.extract_info(url, download=False)
                
                # Get comments if available
                if 'comments' in info and info['comments']:
                    for comment in info['comments']:
                        if isinstance(comment, dict):
                            comment_text = comment.get('text', '')
                            if comment_text:
                                # Extract author information
                                author = comment.get('author', '')
                                author_id = comment.get('author_id', '')
                                author_name = comment.get('author', comment.get('uploader', ''))
                                
                                # Create comment object with author info
                                comment_obj = {
                                    'text': comment_text,
                                    'author': author_name or author_id or 'Unknown'
                                }
                                comments.append(comment_obj)
                        elif isinstance(comment, str):
                            # If it's just a string, create object with unknown author
                            comments.append({
                                'text': comment,
                                'author': 'Unknown'
                            })
                
                # If no comments in info, try to get them differently
                if not comments:
                    # Try to get comment count and extract comments
                    comment_count = info.get('comment_count', 0)
                    if comment_count > 0:
                        # yt-dlp might not always extract comments directly
                        # Return a message suggesting manual entry
                        return jsonify({
                            'success': False,
                            'error': f'Video has {comment_count} comments, but yt-dlp cannot extract them directly. Please copy comments manually or use YouTube API.'
                        }), 400
                
            except Exception as e:
                # If extraction fails, try alternative method
                return jsonify({
                    'success': False,
                    'error': f'Could not extract comments: {str(e)}. YouTube may require authentication or the video may have comments disabled.'
                }), 400
        
        if not comments:
            return jsonify({
                'success': False,
                'error': 'No comments found. The video may have comments disabled or be unavailable.'
            }), 400
        
        return jsonify({
            'success': True,
            'comments': comments[:100],  # Limit to first 100 comments
            'count': len(comments)
        })
        
    except ImportError:
        return jsonify({'error': 'yt-dlp library is required'}), 500
    except Exception as e:
        return jsonify({'error': f'Failed to extract comments: {str(e)}'}), 500


def extract_tiktok_comments(url):
    """Extract comments from TikTok video"""
    try:
        import yt_dlp
        
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
        }
        
        comments = []
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
                
                # TikTok comments extraction (if available)
                if 'comments' in info and info['comments']:
                    for comment in info['comments']:
                        if isinstance(comment, dict):
                            comment_text = comment.get('text', '')
                            if comment_text:
                                # Extract author information
                                author = comment.get('author', comment.get('uploader', ''))
                                author_id = comment.get('author_id', '')
                                author_name = author or author_id or 'Unknown'
                                
                                comment_obj = {
                                    'text': comment_text,
                                    'author': author_name
                                }
                                comments.append(comment_obj)
                        elif isinstance(comment, str):
                            comments.append({
                                'text': comment,
                                'author': 'Unknown'
                            })
            
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': f'Could not extract TikTok comments: {str(e)}. TikTok may require authentication.'
                }), 400
        
        if not comments:
            return jsonify({
                'success': False,
                'error': 'No comments found. TikTok comments may require authentication or the video may have comments disabled.'
            }), 400
        
        return jsonify({
            'success': True,
            'comments': comments[:100],
            'count': len(comments)
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to extract TikTok comments: {str(e)}'}), 500


def extract_instagram_comments(url):
    """Extract comments from Instagram video"""
    try:
        import yt_dlp
        
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
        }
        
        comments = []
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
                
                # Instagram comments extraction (if available)
                if 'comments' in info and info['comments']:
                    for comment in info['comments']:
                        if isinstance(comment, dict):
                            comment_text = comment.get('text', '')
                            if comment_text:
                                # Extract author information
                                author = comment.get('author', comment.get('uploader', ''))
                                author_id = comment.get('author_id', '')
                                author_name = author or author_id or 'Unknown'
                                
                                comment_obj = {
                                    'text': comment_text,
                                    'author': author_name
                                }
                                comments.append(comment_obj)
                        elif isinstance(comment, str):
                            comments.append({
                                'text': comment,
                                'author': 'Unknown'
                            })
            
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': f'Could not extract Instagram comments: {str(e)}. Instagram requires authentication.'
                }), 400
        
        if not comments:
            return jsonify({
                'success': False,
                'error': 'No comments found. Instagram comments require authentication or the video may have comments disabled.'
            }), 400
        
        return jsonify({
            'success': True,
            'comments': comments[:100],
            'count': len(comments)
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to extract Instagram comments: {str(e)}'}), 500


@app.route('/search-social-media', methods=['POST'])
def search_social_media():
    """Search for profiles and content across all social media platforms"""
    try:
        data = request.json
        name = data.get('name', '').strip()
        
        if not name:
            return jsonify({'error': 'Name is required'}), 400
        
        # Search across all platforms - Generate real search URLs only
        results = search_all_platforms_real(name)
        
        # Calculate statistics
        stats = calculate_search_stats(results)
        
        return jsonify({
            'success': True,
            'results': results,
            'stats': stats,
            'search_term': name
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def search_all_platforms_real(name):
    """Generate real search URLs for finding actual profiles on social media platforms"""
    import urllib.parse
    
    name_encoded = urllib.parse.quote(name)
    name_lower = name.lower()
    name_no_spaces = name_lower.replace(" ", "")
    name_underscore = name_lower.replace(" ", "_")
    name_dash = name_lower.replace(" ", "-")
    
    # Check if this is a famous person/brand (mark as likely verified)
    famous_keywords = [
        'elon musk', 'cristiano ronaldo', 'lionel messi', 'taylor swift', 'kim kardashian',
        'beyonce', 'justin bieber', 'ariana grande', 'selena gomez', 'dwayne johnson',
        'nike', 'adidas', 'apple', 'microsoft', 'google', 'meta', 'facebook', 'tesla',
        'amazon', 'netflix', 'spotify', 'youtube', 'instagram', 'twitter', 'tiktok',
        'coca cola', 'pepsi', 'mcdonalds', 'starbucks', 'samsung', 'sony', 'disney',
        'ronaldo', 'messi', 'lebron james', 'neymar', 'mbappe', 'real madrid', 'barcelona',
        'manchester united', 'nba', 'nfl', 'fifa', 'uefa', 'premier league'
    ]
    
    is_famous = any(keyword in name_lower for keyword in famous_keywords)
    
    results = {}
    
    # Twitter/X - Only show search + 2 most common variations
    results['twitter'] = [
        {
            'name': f'🔍 Search Twitter/X',
            'handle': f'Search "{name}"',
            'username': 'search',
            'description': f'Search for ALL {name} accounts on Twitter/X (RECOMMENDED)',
            'followers': 'Search',
            'following': 'All',
            'posts': '-',
            'verified': False,
            'type': 'Search',
            'url': f'https://twitter.com/search?q={name_encoded}&src=typed_query&f=user',
            'is_real_search': True
        },
        {
            'name': f'{name}',
            'handle': f'@{name_no_spaces}',
            'username': name_no_spaces,
            'description': f'Official {name} account' if is_famous else f'Try profile @{name_no_spaces} (might not exist)',
            'followers': '10M+' if is_famous else 'Check',
            'following': 'Profile',
            'posts': '5K+' if is_famous else '-',
            'verified': is_famous,  # Mark as verified if famous
            'type': 'Profile',
            'url': f'https://twitter.com/{name_no_spaces}',
            'is_real_search': True
        },
        {
            'name': f'{name}',
            'handle': f'@{name_underscore}',
            'username': name_underscore,
            'description': f'Try profile @{name_underscore} (might not exist)',
            'followers': 'Check',
            'following': 'Profile',
            'posts': '-',
            'verified': False,
            'type': 'Profile',
            'url': f'https://twitter.com/{name_underscore}',
            'is_real_search': True
        }
    ]
    
    # Instagram - Only search + most common variation
    results['instagram'] = [
        {
            'name': f'🔍 Search Instagram',
            'handle': f'Search "{name}"',
            'username': 'search',
            'description': f'Search for ALL {name} accounts on Instagram (RECOMMENDED)',
            'followers': 'Search',
            'following': 'All',
            'posts': '-',
            'verified': False,
            'type': 'Search',
            'url': f'https://www.instagram.com/explore/search/keyword/?q={name_encoded}',
            'is_real_search': True
        },
        {
            'name': f'{name}',
            'handle': f'@{name_no_spaces}',
            'username': name_no_spaces,
            'description': f'Official {name} Instagram account' if is_famous else f'Try profile @{name_no_spaces} (might not exist)',
            'followers': '50M+' if is_famous else 'Check',
            'following': 'Profile',
            'posts': '2K+' if is_famous else '-',
            'verified': is_famous,  # Mark as verified if famous
            'type': 'Profile',
            'url': f'https://www.instagram.com/{name_no_spaces}/',
            'is_real_search': True
        },
        {
            'name': f'{name}',
            'handle': f'@{name_no_spaces}.official',
            'username': f'{name_no_spaces}.official',
            'description': f'Visit {name}\'s Instagram profile',
            'followers': 'Visit',
            'following': 'Profile',
            'posts': '-',
            'verified': False,
            'type': 'Profile',
            'url': f'https://www.instagram.com/{name_no_spaces}.official/',
            'is_real_search': True
        },
        {
            'name': f'Search All "{name}"',
            'handle': 'Search',
            'username': 'search',
            'description': f'Search for all {name} profiles on Instagram',
            'followers': 'Search',
            'following': 'All',
            'posts': '-',
            'verified': False,
            'type': 'Search',
            'url': f'https://www.instagram.com/explore/search/keyword/?q={name_encoded}',
            'is_real_search': True
        }
    ]
    
    # TikTok - Multiple username variations
    results['tiktok'] = [
        {
            'name': f'{name}',
            'handle': f'@{name_no_spaces}',
            'username': name_no_spaces,
            'description': f'Official {name} TikTok' if is_famous else f'Visit {name}\'s TikTok profile',
            'followers': '20M+' if is_famous else 'Visit',
            'following': 'Profile',
            'posts': '500+' if is_famous else '-',
            'verified': is_famous,  # Mark as verified if famous
            'type': 'Profile',
            'url': f'https://www.tiktok.com/@{name_no_spaces}',
            'is_real_search': True
        },
        {
            'name': f'{name}',
            'handle': f'@{name_underscore}',
            'username': name_underscore,
            'description': f'Visit {name}\'s TikTok profile',
            'followers': 'Visit',
            'following': 'Profile',
            'posts': '-',
            'verified': False,
            'type': 'Profile',
            'url': f'https://www.tiktok.com/@{name_underscore}',
            'is_real_search': True
        },
        {
            'name': f'{name}',
            'handle': f'@{name_dash}',
            'username': name_dash,
            'description': f'Visit {name}\'s TikTok profile',
            'followers': 'Visit',
            'following': 'Profile',
            'posts': '-',
            'verified': False,
            'type': 'Profile',
            'url': f'https://www.tiktok.com/@{name_dash}',
            'is_real_search': True
        },
        {
            'name': f'{name} Official',
            'handle': f'@{name_no_spaces}official',
            'username': f'{name_no_spaces}official',
            'description': f'Visit {name}\'s official TikTok profile',
            'followers': 'Visit',
            'following': 'Profile',
            'posts': '-',
            'verified': False,
            'type': 'Profile',
            'url': f'https://www.tiktok.com/@{name_no_spaces}official',
            'is_real_search': True
        },
        {
            'name': f'Search All "{name}"',
            'handle': 'Search',
            'username': 'search',
            'description': f'Search for all {name} profiles on TikTok',
            'followers': 'Search',
            'following': 'All',
            'posts': '-',
            'verified': False,
            'type': 'Search',
            'url': f'https://www.tiktok.com/search/user?q={name_encoded}',
            'is_real_search': True
        }
    ]
    
    # YouTube - Multiple channel variations
    results['youtube'] = [
        {
            'name': f'{name}',
            'handle': f'@{name_no_spaces}',
            'username': name_no_spaces,
            'description': f'Official {name} YouTube Channel' if is_famous else f'Visit {name}\'s YouTube channel',
            'followers': '5M+ Subscribers' if is_famous else 'Visit',
            'following': 'Channel',
            'posts': '1K+ Videos' if is_famous else '-',
            'verified': is_famous,  # Mark as verified if famous
            'type': 'Channel',
            'url': f'https://www.youtube.com/@{name_no_spaces}',
            'is_real_search': True
        },
        {
            'name': f'{name}',
            'handle': f'@{name_dash}',
            'username': name_dash,
            'description': f'Visit {name}\'s YouTube channel',
            'followers': 'Visit',
            'following': 'Channel',
            'posts': '-',
            'verified': False,
            'type': 'Channel',
            'url': f'https://www.youtube.com/@{name_dash}',
            'is_real_search': True
        },
        {
            'name': f'{name} Official',
            'handle': f'@{name_no_spaces}official',
            'username': f'{name_no_spaces}official',
            'description': f'Visit {name}\'s official YouTube channel',
            'followers': 'Visit',
            'following': 'Channel',
            'posts': '-',
            'verified': False,
            'type': 'Channel',
            'url': f'https://www.youtube.com/@{name_no_spaces}official',
            'is_real_search': True
        },
        {
            'name': f'{name} Channel',
            'handle': f'@{name_no_spaces}channel',
            'username': f'{name_no_spaces}channel',
            'description': f'Visit {name}\'s YouTube channel',
            'followers': 'Visit',
            'following': 'Channel',
            'posts': '-',
            'verified': False,
            'type': 'Channel',
            'url': f'https://www.youtube.com/@{name_no_spaces}channel',
            'is_real_search': True
        },
        {
            'name': f'Search All "{name}"',
            'handle': 'Search',
            'username': 'search',
            'description': f'Search for all {name} channels on YouTube',
            'followers': 'Search',
            'following': 'All',
            'posts': '-',
            'verified': False,
            'type': 'Search',
            'url': f'https://www.youtube.com/results?search_query={name_encoded}&sp=EgIQAg%253D%253D',
            'is_real_search': True
        }
    ]
    
    # Facebook - Multiple page/profile variations
    results['facebook'] = [
        {
            'name': f'{name}',
            'handle': name_no_spaces,
            'username': name_no_spaces,
            'description': f'Visit {name}\'s Facebook page/profile',
            'followers': 'Visit',
            'following': 'Page',
            'posts': '-',
            'verified': False,
            'type': 'Page',
            'url': f'https://www.facebook.com/{name_no_spaces}',
            'is_real_search': True
        },
        {
            'name': f'{name}',
            'handle': name_dash,
            'username': name_dash,
            'description': f'Visit {name}\'s Facebook page/profile',
            'followers': 'Visit',
            'following': 'Page',
            'posts': '-',
            'verified': False,
            'type': 'Page',
            'url': f'https://www.facebook.com/{name_dash}',
            'is_real_search': True
        },
        {
            'name': f'{name} Official',
            'handle': f'{name_no_spaces}official',
            'username': f'{name_no_spaces}official',
            'description': f'Visit {name}\'s official Facebook page',
            'followers': 'Visit',
            'following': 'Page',
            'posts': '-',
            'verified': False,
            'type': 'Page',
            'url': f'https://www.facebook.com/{name_no_spaces}official',
            'is_real_search': True
        },
        {
            'name': f'Search All "{name}"',
            'handle': 'Search',
            'username': 'search',
            'description': f'Search for all {name} pages on Facebook',
            'followers': 'Search',
            'following': 'All',
            'posts': '-',
            'verified': False,
            'type': 'Search',
            'url': f'https://www.facebook.com/search/top?q={name_encoded}',
            'is_real_search': True
        }
    ]
    
    # LinkedIn - Multiple profile variations
    results['linkedin'] = [
        {
            'name': f'{name}',
            'handle': name_dash,
            'username': name_dash,
            'description': f'Visit {name}\'s LinkedIn profile',
            'followers': 'Visit',
            'following': 'Profile',
            'posts': '-',
            'verified': False,
            'type': 'Profile',
            'url': f'https://www.linkedin.com/in/{name_dash}/',
            'is_real_search': True
        },
        {
            'name': f'{name}',
            'handle': name_no_spaces,
            'username': name_no_spaces,
            'description': f'Visit {name}\'s LinkedIn profile',
            'followers': 'Visit',
            'following': 'Profile',
            'posts': '-',
            'verified': False,
            'type': 'Profile',
            'url': f'https://www.linkedin.com/in/{name_no_spaces}/',
            'is_real_search': True
        },
        {
            'name': f'{name} Company',
            'handle': name_dash,
            'username': name_dash,
            'description': f'Visit {name}\'s LinkedIn company page',
            'followers': 'Visit',
            'following': 'Company',
            'posts': '-',
            'verified': False,
            'type': 'Company',
            'url': f'https://www.linkedin.com/company/{name_dash}/',
            'is_real_search': True
        },
        {
            'name': f'Search All "{name}"',
            'handle': 'Search',
            'username': 'search',
            'description': f'Search for all {name} profiles on LinkedIn',
            'followers': 'Search',
            'following': 'All',
            'posts': '-',
            'verified': False,
            'type': 'Search',
            'url': f'https://www.linkedin.com/search/results/people/?keywords={name_encoded}',
            'is_real_search': True
        }
    ]
    
    # Reddit - Multiple user variations
    results['reddit'] = [
        {
            'name': f'{name}',
            'handle': f'u/{name_no_spaces}',
            'username': name_no_spaces,
            'description': f'Visit {name}\'s Reddit profile',
            'followers': 'Visit',
            'following': 'Profile',
            'posts': '-',
            'verified': False,
            'type': 'Profile',
            'url': f'https://www.reddit.com/user/{name_no_spaces}',
            'is_real_search': True
        },
        {
            'name': f'{name}',
            'handle': f'u/{name_underscore}',
            'username': name_underscore,
            'description': f'Visit {name}\'s Reddit profile',
            'followers': 'Visit',
            'following': 'Profile',
            'posts': '-',
            'verified': False,
            'type': 'Profile',
            'url': f'https://www.reddit.com/user/{name_underscore}',
            'is_real_search': True
        },
        {
            'name': f'{name}',
            'handle': f'u/{name_dash}',
            'username': name_dash,
            'description': f'Visit {name}\'s Reddit profile',
            'followers': 'Visit',
            'following': 'Profile',
            'posts': '-',
            'verified': False,
            'type': 'Profile',
            'url': f'https://www.reddit.com/user/{name_dash}',
            'is_real_search': True
        },
        {
            'name': f'r/{name_no_spaces}',
            'handle': f'r/{name_no_spaces}',
            'username': name_no_spaces,
            'description': f'Visit r/{name_no_spaces} subreddit',
            'followers': 'Visit',
            'following': 'Subreddit',
            'posts': '-',
            'verified': False,
            'type': 'Subreddit',
            'url': f'https://www.reddit.com/r/{name_no_spaces}',
            'is_real_search': True
        },
        {
            'name': f'Search All "{name}"',
            'handle': 'Search',
            'username': 'search',
            'description': f'Search for all {name} users on Reddit',
            'followers': 'Search',
            'following': 'All',
            'posts': '-',
            'verified': False,
            'type': 'Search',
            'url': f'https://www.reddit.com/search/?q={name_encoded}&type=user',
            'is_real_search': True
        }
    ]
    
    return results


def search_all_platforms(name):
    """OLD FUNCTION - Search for profiles across all social media platforms (SIMULATED DATA)"""
    name_lower = name.lower()
    name_no_spaces = name_lower.replace(" ", "")
    name_underscore = name_lower.replace(" ", "_")
    name_dot = name_lower.replace(" ", ".")
    name_dash = name_lower.replace(" ", "-")
    results = {}
    
    # Generate comprehensive profiles for each platform (OLD SIMULATED DATA)
    # Twitter/X - Multiple users, pages, and accounts
    results['twitter'] = [
        {
            'name': name,
            'handle': f'{name_no_spaces}',
            'username': f'{name_no_spaces}',
            'description': f'Official account for {name}. Updates, news, and more.',
            'followers': 125000,
            'following': 450,
            'posts': 1250,
            'verified': True,
            'type': 'Official Account',
            'url': f'https://twitter.com/{name_no_spaces}'
        },
        {
            'name': f'{name} News',
            'handle': f'{name_no_spaces}news',
            'username': f'{name_no_spaces}news',
            'description': f'Latest news and updates about {name}',
            'followers': 85000,
            'following': 200,
            'posts': 3200,
            'verified': False,
            'type': 'News Page',
            'url': f'https://twitter.com/{name_no_spaces}news'
        },
        {
            'name': f'{name} Fan Page',
            'handle': f'{name_no_spaces}fans',
            'username': f'{name_no_spaces}fans',
            'description': f'Fan page dedicated to {name}. Join the community!',
            'followers': 45000,
            'following': 120,
            'posts': 890,
            'verified': False,
            'type': 'Fan Page',
            'url': f'https://twitter.com/{name_no_spaces}fans'
        },
        {
            'name': f'{name} Updates',
            'handle': f'{name_no_spaces}updates',
            'username': f'{name_no_spaces}updates',
            'description': f'Get the latest updates about {name}',
            'followers': 32000,
            'following': 80,
            'posts': 560,
            'verified': False,
            'type': 'Updates Page',
            'url': f'https://twitter.com/{name_no_spaces}updates'
        },
        {
            'name': f'{name} Community',
            'handle': f'{name_no_spaces}community',
            'username': f'{name_no_spaces}community',
            'description': f'Community page for {name} fans',
            'followers': 28000,
            'following': 150,
            'posts': 420,
            'verified': False,
            'type': 'Community',
            'url': f'https://twitter.com/{name_no_spaces}community'
        },
        {
            'name': f'{name} Official',
            'handle': f'{name_no_spaces}official',
            'username': f'{name_no_spaces}official',
            'description': f'Official Twitter account for {name}',
            'followers': 95000,
            'following': 300,
            'posts': 2100,
            'verified': True,
            'type': 'Official Account',
            'url': f'https://twitter.com/{name_no_spaces}official'
        }
    ]
    
    # Instagram - Multiple accounts and pages
    results['instagram'] = [
        {
            'name': name,
            'handle': f'{name_underscore}',
            'username': f'{name_underscore}',
            'description': f'Welcome to {name}\'s official Instagram! 📸',
            'followers': 245000,
            'following': 380,
            'posts': 890,
            'verified': True,
            'type': 'Official Account',
            'url': f'https://instagram.com/{name_underscore}'
        },
        {
            'name': f'{name} Fan Page',
            'handle': f'{name_underscore}_fans',
            'username': f'{name_underscore}_fans',
            'description': f'Fan page dedicated to {name}',
            'followers': 45000,
            'following': 120,
            'posts': 560,
            'verified': False,
            'type': 'Fan Page',
            'url': f'https://instagram.com/{name_underscore}_fans'
        },
        {
            'name': f'{name} Daily',
            'handle': f'{name_underscore}_daily',
            'username': f'{name_underscore}_daily',
            'description': f'Daily updates about {name}',
            'followers': 32000,
            'following': 200,
            'posts': 1250,
            'verified': False,
            'type': 'Updates Page',
            'url': f'https://instagram.com/{name_underscore}_daily'
        },
        {
            'name': f'{name} Updates',
            'handle': f'{name_underscore}_updates',
            'username': f'{name_underscore}_updates',
            'description': f'Latest updates and news about {name}',
            'followers': 28000,
            'following': 150,
            'posts': 680,
            'verified': False,
            'type': 'News Page',
            'url': f'https://instagram.com/{name_underscore}_updates'
        },
        {
            'name': f'{name} Photos',
            'handle': f'{name_underscore}_photos',
            'username': f'{name_underscore}_photos',
            'description': f'Best photos of {name}',
            'followers': 35000,
            'following': 100,
            'posts': 420,
            'verified': False,
            'type': 'Photo Page',
            'url': f'https://instagram.com/{name_underscore}_photos'
        },
        {
            'name': f'{name} Official',
            'handle': f'{name_underscore}_official',
            'username': f'{name_underscore}_official',
            'description': f'Official Instagram account for {name}',
            'followers': 180000,
            'following': 250,
            'posts': 950,
            'verified': True,
            'type': 'Official Account',
            'url': f'https://instagram.com/{name_underscore}_official'
        }
    ]
    
    # TikTok - Multiple accounts
    results['tiktok'] = [
        {
            'name': name,
            'handle': f'@{name_no_spaces}',
            'username': name_no_spaces,
            'description': f'Follow {name} on TikTok for daily content!',
            'followers': 890000,
            'following': 250,
            'posts': 450,
            'views': 12500000,
            'verified': True,
            'type': 'Official Account',
            'url': f'https://tiktok.com/@{name_no_spaces}'
        },
        {
            'name': f'{name} Clips',
            'handle': f'@{name_no_spaces}clips',
            'username': f'{name_no_spaces}clips',
            'description': f'Best clips and moments of {name}',
            'followers': 320000,
            'following': 180,
            'posts': 280,
            'views': 8500000,
            'verified': False,
            'type': 'Fan Account',
            'url': f'https://tiktok.com/@{name_no_spaces}clips'
        },
        {
            'name': f'{name} Fan',
            'handle': f'@{name_no_spaces}fan',
            'username': f'{name_no_spaces}fan',
            'description': f'Fan account for {name}',
            'followers': 180000,
            'following': 120,
            'posts': 190,
            'views': 4200000,
            'verified': False,
            'type': 'Fan Account',
            'url': f'https://tiktok.com/@{name_no_spaces}fan'
        },
        {
            'name': f'{name} Official',
            'handle': f'@{name_no_spaces}official',
            'username': f'{name_no_spaces}official',
            'description': f'Official TikTok account for {name}',
            'followers': 650000,
            'following': 200,
            'posts': 380,
            'views': 9800000,
            'verified': True,
            'type': 'Official Account',
            'url': f'https://tiktok.com/@{name_no_spaces}official'
        }
    ]
    
    # YouTube - Multiple channels
    results['youtube'] = [
        {
            'name': f'{name} Official',
            'handle': f'{name} Official',
            'username': f'{name_no_spaces}official',
            'description': f'Official YouTube channel for {name}. Subscribe for updates!',
            'followers': 450000,
            'posts': 320,
            'views': 25000000,
            'verified': True,
            'type': 'Official Channel',
            'url': f'https://youtube.com/@{name_no_spaces}official'
        },
        {
            'name': f'{name} Clips',
            'handle': f'{name} Clips',
            'username': f'{name_no_spaces}clips',
            'description': f'Best clips and highlights of {name}',
            'followers': 180000,
            'posts': 450,
            'views': 12000000,
            'verified': False,
            'type': 'Fan Channel',
            'url': f'https://youtube.com/@{name_no_spaces}clips'
        },
        {
            'name': f'{name} News',
            'handle': f'{name} News',
            'username': f'{name_no_spaces}news',
            'description': f'Latest news and updates about {name}',
            'followers': 95000,
            'posts': 280,
            'views': 6500000,
            'verified': False,
            'type': 'News Channel',
            'url': f'https://youtube.com/@{name_no_spaces}news'
        },
        {
            'name': f'{name} Archive',
            'handle': f'{name} Archive',
            'username': f'{name_no_spaces}archive',
            'description': f'Archive of {name} content',
            'followers': 75000,
            'posts': 520,
            'views': 4200000,
            'verified': False,
            'type': 'Archive Channel',
            'url': f'https://youtube.com/@{name_no_spaces}archive'
        }
    ]
    
    # Facebook - Multiple pages and groups
    results['facebook'] = [
        {
            'name': name,
            'handle': name,
            'username': name_dot,
            'description': f'Official Facebook page for {name}',
            'followers': 180000,
            'posts': 1250,
            'verified': True,
            'type': 'Official Page',
            'url': f'https://facebook.com/{name_dot}'
        },
        {
            'name': f'{name} Fan Page',
            'handle': f'{name} Fan Page',
            'username': f'{name_dot}.fans',
            'description': f'Fan page for {name}',
            'followers': 85000,
            'posts': 680,
            'verified': False,
            'type': 'Fan Page',
            'url': f'https://facebook.com/{name_dot}.fans'
        },
        {
            'name': f'{name} Community',
            'handle': f'{name} Community',
            'username': f'{name_dot}.community',
            'description': f'Community group for {name} fans',
            'followers': 45000,
            'posts': 3200,
            'verified': False,
            'type': 'Community Group',
            'url': f'https://facebook.com/groups/{name_dot}.community'
        },
        {
            'name': f'{name} Updates',
            'handle': f'{name} Updates',
            'username': f'{name_dot}.updates',
            'description': f'Latest updates about {name}',
            'followers': 32000,
            'posts': 420,
            'verified': False,
            'type': 'Updates Page',
            'url': f'https://facebook.com/{name_dot}.updates'
        }
    ]
    
    # LinkedIn - Multiple profiles and pages
    results['linkedin'] = [
        {
            'name': name,
            'handle': name,
            'username': name_dash,
            'description': f'Professional profile for {name}',
            'followers': 25000,
            'posts': 180,
            'verified': False,
            'type': 'Personal Profile',
            'url': f'https://linkedin.com/in/{name_dash}'
        },
        {
            'name': f'{name} Company',
            'handle': f'{name} Company',
            'username': f'{name_dash}-company',
            'description': f'Company page for {name}',
            'followers': 45000,
            'posts': 320,
            'verified': True,
            'type': 'Company Page',
            'url': f'https://linkedin.com/company/{name_dash}-company'
        },
        {
            'name': f'{name} Professional',
            'handle': f'{name} Professional',
            'username': f'{name_dash}-professional',
            'description': f'Professional network for {name}',
            'followers': 18000,
            'posts': 120,
            'verified': False,
            'type': 'Professional Profile',
            'url': f'https://linkedin.com/in/{name_dash}-professional'
        }
    ]
    
    # Reddit - Multiple subreddits
    results['reddit'] = [
        {
            'name': f'r/{name_no_spaces}',
            'handle': name_no_spaces,
            'username': name_no_spaces,
            'description': f'Subreddit dedicated to {name}',
            'followers': 12500,
            'posts': 850,
            'verified': False,
            'type': 'Subreddit',
            'url': f'https://reddit.com/r/{name_no_spaces}'
        },
        {
            'name': f'r/{name_no_spaces}fans',
            'handle': f'{name_no_spaces}fans',
            'username': f'{name_no_spaces}fans',
            'description': f'Fan community for {name}',
            'followers': 8500,
            'posts': 420,
            'verified': False,
            'type': 'Fan Subreddit',
            'url': f'https://reddit.com/r/{name_no_spaces}fans'
        },
        {
            'name': f'r/{name_no_spaces}discussion',
            'handle': f'{name_no_spaces}discussion',
            'username': f'{name_no_spaces}discussion',
            'description': f'Discussion forum about {name}',
            'followers': 6500,
            'posts': 320,
            'verified': False,
            'type': 'Discussion Forum',
            'url': f'https://reddit.com/r/{name_no_spaces}discussion'
        }
    ]
    
    # Snapchat - Multiple accounts
    results['snapchat'] = [
        {
            'name': name,
            'handle': f'{name_no_spaces}',
            'username': name_no_spaces,
            'description': f'Official Snapchat for {name}',
            'followers': 125000,
            'posts': 450,
            'verified': True,
            'type': 'Official Account',
            'url': f'https://snapchat.com/add/{name_no_spaces}'
        },
        {
            'name': f'{name} Updates',
            'handle': f'{name_no_spaces}updates',
            'username': f'{name_no_spaces}updates',
            'description': f'Daily updates from {name}',
            'followers': 45000,
            'posts': 280,
            'verified': False,
            'type': 'Updates Account',
            'url': f'https://snapchat.com/add/{name_no_spaces}updates'
        }
    ]
    
    # Filter out empty results
    results = {k: v for k, v in results.items() if v}
    
    return results


def calculate_search_stats(results):
    """Calculate statistics from search results"""
    total_profiles = sum(len(profiles) for profiles in results.values())
    platforms_found = len(results)
    
    # Calculate total followers - handle both int and string values
    total_followers = 0
    for profiles in results.values():
        for p in profiles:
            followers = p.get('followers', 0)
            # Only add if it's a number (not a string like 'Search' or 'Visit')
            if isinstance(followers, (int, float)):
                total_followers += followers
    
    verified_count = sum(
        sum(1 for p in profiles if p.get('verified', False))
        for profiles in results.values()
    )
    
    # Check if we have any numeric follower data
    has_follower_data = total_followers > 0
    
    return {
        'total_profiles': total_profiles,
        'platforms_found': platforms_found,
        'total_followers': format_search_number(total_followers) if has_follower_data else 'N/A',
        'verified_count': verified_count,
        'has_follower_data': has_follower_data
    }


def format_search_number(num):
    """Format large numbers for display"""
    if num >= 1000000:
        return f"{num / 1000000:.1f}M"
    elif num >= 1000:
        return f"{num / 1000:.1f}K"
    return str(num)


@app.route('/search-social-media-news', methods=['POST'])
def search_social_media_news():
    """Search for news and content related to a name across all social media platforms"""
    try:
        data = request.json
        name = data.get('name', '').strip()
        
        if not name:
            return jsonify({'error': 'Name is required'}), 400
        
        # Search for news across all platforms (simulated - in production, this would use APIs)
        news_results = search_news_all_platforms(name)
        
        # Detect and mark repeated news
        news_results = detect_repeated_news(news_results)
        
        # Get trending news that appears on multiple platforms
        trending_repeated = get_trending_repeated_news(news_results)
        
        # Calculate statistics
        stats = calculate_news_stats(news_results)
        
        return jsonify({
            'success': True,
            'news': news_results,
            'stats': stats,
            'search_term': name,
            'trending_repeated': trending_repeated
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def fetch_real_news(query, max_results=10):
    """Fetch real news from Google News RSS and other sources"""
    if not NEWS_API_AVAILABLE:
        return []
    
    try:
        news_items = []
        
        # Google News RSS feed
        google_news_url = f"https://news.google.com/rss/search?q={requests.utils.quote(query)}&hl=en-US&gl=US&ceid=US:en"
        
        try:
            feed = feedparser.parse(google_news_url)
            
            for entry in feed.entries[:max_results]:
                # Parse publication date
                pub_date = entry.get('published', '')
                time_ago = 'Recently'
                
                if pub_date:
                    try:
                        pub_datetime = datetime(*entry.published_parsed[:6])
                        time_diff = datetime.now() - pub_datetime
                        
                        if time_diff.days > 0:
                            time_ago = f"{time_diff.days} day{'s' if time_diff.days > 1 else ''} ago"
                        elif time_diff.seconds >= 3600:
                            hours = time_diff.seconds // 3600
                            time_ago = f"{hours} hour{'s' if hours > 1 else ''} ago"
                        else:
                            minutes = time_diff.seconds // 60
                            time_ago = f"{minutes} minute{'s' if minutes > 1 else ''} ago"
                    except:
                        pass
                
                # Extract source name from title (Google News format: "Title - Source")
                title = entry.get('title', 'No title')
                source_name = 'News Source'
                
                if ' - ' in title:
                    parts = title.rsplit(' - ', 1)
                    if len(parts) == 2:
                        title = parts[0]
                        source_name = parts[1]
                
                # Get description/summary
                summary = entry.get('summary', entry.get('description', ''))
                # Remove HTML tags from summary
                import html
                summary = html.unescape(re.sub('<[^<]+?>', '', summary))
                
                news_item = {
                    'title': title,
                    'headline': title,
                    'content': summary[:300] + '...' if len(summary) > 300 else summary,
                    'source_name': source_name,
                    'source_handle': source_name.lower().replace(' ', ''),
                    'author': source_name,
                    'author_handle': source_name.lower().replace(' ', ''),
                    'time_ago': time_ago,
                    'url': entry.get('link', '#'),
                    'likes': 0,  # Not available from RSS
                    'shares': 0,
                    'comments': 0,
                    'views': 0,
                    'trending': False,
                    'breaking': 'breaking' in title.lower(),
                    'verified': True,
                    'is_real': True  # Mark as real news
                }
                
                news_items.append(news_item)
        
        except Exception as e:
            print(f"Error fetching Google News: {e}")
        
        return news_items
        
    except Exception as e:
        print(f"Error in fetch_real_news: {e}")
        return []


def search_news_all_platforms(name):
    """Search for news articles across all social media platforms"""
    name_lower = name.lower()
    news = {}
    
    # Try to fetch real news first
    if NEWS_API_AVAILABLE:
        try:
            real_news = fetch_real_news(name, max_results=15)
            
            if real_news:
                # Organize real news by platform/source
                news['google_news'] = []
                news['twitter'] = []
                news['youtube'] = []
                news['bbc'] = []
                news['reuters'] = []
                
                for item in real_news:
                    source_lower = item['source_name'].lower()
                    
                    # Categorize by source
                    if 'bbc' in source_lower:
                        news['bbc'].append(item)
                    elif 'reuters' in source_lower:
                        news['reuters'].append(item)
                    elif 'twitter' in source_lower or 'x.com' in source_lower:
                        news['twitter'].append(item)
                    elif 'youtube' in source_lower:
                        news['youtube'].append(item)
                    else:
                        news['google_news'].append(item)
                
                # If we have real news, return it
                if any(len(articles) > 0 for articles in news.values()):
                    return news
        except Exception as e:
            print(f"Error fetching real news: {e}")
    
    # Fallback to simulated news if real news fetch fails
    print("Using simulated news data (fallback)")
    
    # Helper function to create search URL with title
    def create_search_url(platform, article_title, name_param=name):
        """Create a search URL that includes both name and article title"""
        # Extract key words from title (remove common words like "Breaking:", "Latest", etc.)
        title_words = article_title.replace("Breaking:", "").replace("Latest", "").replace("News", "").strip()
        # Combine name and title for better search results
        search_query = f"{name_param} {title_words}"
        
        # Platform-specific URL formats
        if platform == 'twitter':
            return f'https://twitter.com/search?q={search_query.replace(" ", "%20")}'
        elif platform == 'instagram':
            return f'https://www.instagram.com/explore/tags/{search_query.replace(" ", "").replace(":", "")}/'
        elif platform == 'tiktok':
            return f'https://www.tiktok.com/search?q={search_query.replace(" ", "%20")}'
        elif platform == 'youtube':
            return f'https://www.youtube.com/results?search_query={search_query.replace(" ", "+")}'
        elif platform == 'facebook':
            return f'https://www.facebook.com/search/top/?q={search_query.replace(" ", "%20")}'
        elif platform == 'reddit':
            return f'https://www.reddit.com/search/?q={search_query.replace(" ", "%20")}'
        elif platform == 'linkedin':
            return f'https://www.linkedin.com/search/results/all/?keywords={search_query.replace(" ", "%20")}'
        elif platform == 'cnn':
            return f'https://www.cnn.com/search?q={search_query.replace(" ", "+")}'
        elif platform == 'bbc':
            return f'https://www.bbc.com/search?q={search_query.replace(" ", "+")}'
        elif platform == 'reuters':
            return f'https://www.reuters.com/search/news?blob={search_query.replace(" ", "+")}'
        elif platform == 'guardian':
            return f'https://www.theguardian.com/search?q={search_query.replace(" ", "+")}'
        elif platform == 'forbes':
            return f'https://www.forbes.com/search/?q={search_query.replace(" ", "+")}'
        elif platform == 'techcrunch':
            return f'https://techcrunch.com/?s={search_query.replace(" ", "+")}'
        elif platform == 'nytimes':
            return f'https://www.nytimes.com/search?query={search_query.replace(" ", "+")}'
        elif platform == 'washingtonpost':
            return f'https://www.washingtonpost.com/newssearch/?query={search_query.replace(" ", "+")}'
        elif platform == 'ap':
            return f'https://apnews.com/search?q={search_query.replace(" ", "+")}'
        elif platform == 'bloomberg':
            return f'https://www.bloomberg.com/search?query={search_query.replace(" ", "+")}'
        else:
            # Default fallback
            return f'https://www.google.com/search?q={search_query.replace(" ", "+")}'
    
    # Twitter/X News - At least 5 articles
    # Create some repeated news that will appear across multiple platforms
    common_news_title = f'{name} Makes Major Announcement'
    common_news_content = f'{name} revealed exciting news about their upcoming project. The announcement has generated significant buzz across social media platforms and news outlets worldwide.'
    
    news['twitter'] = [
        {
            'title': f'Breaking: {common_news_title}',
            'headline': f'{name} announces new project',
            'content': f'In a recent tweet, {common_news_content}',
            'source_name': f'{name} Official',
            'source_handle': f'{name_lower.replace(" ", "")}',
            'author': f'{name}',
            'author_handle': f'{name_lower.replace(" ", "")}',
            'time_ago': '2 hours ago',
            'likes': 12500,
            'shares': 3200,
            'comments': 890,
            'views': 450000,
            'trending': True,
            'breaking': True,
            'verified': True,
            'url': create_search_url('twitter', f'Breaking: {common_news_title}')
        },
        {
            'title': f'{name} Trending on Twitter',
            'headline': f'Discussion about {name} goes viral',
            'content': f'Users are sharing their thoughts about {name}, creating a trending topic on Twitter. The conversation has reached thousands of users.',
            'source_name': 'News Source',
            'source_handle': 'newssource',
            'author': 'News Reporter',
            'author_handle': 'newsreporter',
            'time_ago': '5 hours ago',
            'likes': 8500,
            'shares': 2100,
            'comments': 560,
            'views': 280000,
            'trending': True,
            'breaking': False,
            'verified': False,
            'url': create_search_url('twitter', f'{name} Trending on Twitter')
        },
        {
            'title': f'Latest Updates from {name}',
            'headline': f'{name} shares new information',
            'content': f'{name} posted an update on Twitter providing fans with the latest information and developments.',
            'source_name': f'{name} Updates',
            'source_handle': f'{name_lower.replace(" ", "")}updates',
            'author': f'{name}',
            'author_handle': f'{name_lower.replace(" ", "")}updates',
            'time_ago': '8 hours ago',
            'likes': 6200,
            'shares': 1500,
            'comments': 320,
            'views': 180000,
            'trending': False,
            'breaking': False,
            'verified': False,
            'url': create_search_url('twitter', f'Latest Updates from {name}')
        },
        {
            'title': f'Fan Reactions to {name} News',
            'headline': f'Fans react to latest {name} developments',
            'content': f'Twitter users are expressing their reactions to the latest news about {name}, with many sharing their thoughts and opinions.',
            'source_name': 'Fan Community',
            'source_handle': f'{name_lower.replace(" ", "")}fans',
            'author': 'Fan Account',
            'author_handle': f'{name_lower.replace(" ", "")}fans',
            'time_ago': '12 hours ago',
            'likes': 4200,
            'shares': 980,
            'comments': 250,
            'views': 125000,
            'trending': False,
            'breaking': False,
            'verified': False,
            'url': create_search_url('twitter', f'Fan Reactions to {name} News')
        },
        {
            'title': f'{name} in the News Today',
            'headline': f'Daily news roundup about {name}',
            'content': f'A comprehensive roundup of today\'s news about {name}, covering all the latest developments and updates.',
            'source_name': 'Daily News',
            'source_handle': 'dailynews',
            'author': 'News Editor',
            'author_handle': 'newseditor',
            'time_ago': '1 day ago',
            'likes': 3800,
            'shares': 850,
            'comments': 180,
            'views': 95000,
            'trending': False,
            'breaking': False,
            'verified': True,
            'url': create_search_url('twitter', f'{name} in the News Today')
        }
    ]
    
    # Instagram News - At least 5 articles
    news['instagram'] = [
        {
            'title': f'Breaking: {common_news_title}',
            'headline': f'{name} announces new project',
            'content': f'Instagram post: {common_news_content} {name} shared this exciting news with their followers.',
            'source_name': name,
            'source_handle': f'{name_lower.replace(" ", "_")}',
            'author': name,
            'author_handle': f'{name_lower.replace(" ", "_")}',
            'time_ago': '1 hour ago',
            'likes': 45000,
            'comments': 1200,
            'views': 890000,
            'trending': True,
            'breaking': True,
            'verified': True,
            'url': create_search_url('instagram', f'Breaking: {common_news_title}')
        },
        {
            'title': f'{name} Shares Behind-the-Scenes Content',
            'headline': f'Exclusive content from {name}',
            'content': f'{name} posted exclusive behind-the-scenes content on Instagram, giving fans a glimpse into their daily life and work process.',
            'source_name': name,
            'source_handle': f'{name_lower.replace(" ", "_")}',
            'author': name,
            'author_handle': f'{name_lower.replace(" ", "_")}',
            'time_ago': '3 hours ago',
            'likes': 32000,
            'comments': 850,
            'views': 650000,
            'trending': False,
            'breaking': False,
            'verified': True,
            'url': create_search_url('instagram', f'{name} Shares Behind-the-Scenes Content')
        },
        {
            'title': f'{name} Posts New Photo Series',
            'headline': f'Latest photos from {name}',
            'content': f'{name} shared a new series of photos on Instagram, showcasing their latest work and activities.',
            'source_name': name,
            'source_handle': f'{name_lower.replace(" ", "_")}',
            'author': name,
            'author_handle': f'{name_lower.replace(" ", "_")}',
            'time_ago': '4 hours ago',
            'likes': 32000,
            'comments': 850,
            'views': 650000,
            'trending': False,
            'breaking': False,
            'verified': True,
            'url': create_search_url('instagram', f'{name} Posts New Photo Series')
        },
        {
            'title': f'Fan Page Shares {name} Content',
            'headline': f'Fan page updates about {name}',
            'content': f'A popular fan page dedicated to {name} shared the latest updates and news, keeping fans informed.',
            'source_name': f'{name} Fan Page',
            'source_handle': f'{name_lower.replace(" ", "_")}_fans',
            'author': 'Fan Page Admin',
            'author_handle': f'{name_lower.replace(" ", "_")}_fans',
            'time_ago': '6 hours ago',
            'likes': 18000,
            'comments': 420,
            'views': 320000,
            'trending': False,
            'breaking': False,
            'verified': False,
            'url': create_search_url('instagram', f'Fan Page Shares {name} Content')
        },
        {
            'title': f'{name} Instagram Story Highlights',
            'headline': f'Story updates from {name}',
            'content': f'{name} posted new story highlights on Instagram, sharing moments and updates with followers.',
            'source_name': name,
            'source_handle': f'{name_lower.replace(" ", "_")}',
            'author': name,
            'author_handle': f'{name_lower.replace(" ", "_")}',
            'time_ago': '10 hours ago',
            'likes': 25000,
            'comments': 680,
            'views': 480000,
            'trending': False,
            'breaking': False,
            'verified': True,
            'url': create_search_url('instagram', f'{name} Instagram Story Highlights')
        },
        {
            'title': f'{name} Reels Go Viral',
            'headline': f'Popular Reels from {name}',
            'content': f'{name} created new Reels that have gained significant attention, with millions of views and engagement.',
            'source_name': name,
            'source_handle': f'{name_lower.replace(" ", "_")}',
            'author': name,
            'author_handle': f'{name_lower.replace(" ", "_")}',
            'time_ago': '1 day ago',
            'likes': 125000,
            'comments': 3200,
            'views': 2500000,
            'trending': True,
            'breaking': False,
            'verified': True,
            'url': create_search_url('instagram', f'{name} Reels Go Viral')
        }
    ]
    
    # TikTok News - At least 5 articles
    news['tiktok'] = [
        {
            'title': f'{name} Goes Viral on TikTok',
            'headline': f'Video about {name} reaches millions',
            'content': f'A video featuring {name} has gone viral on TikTok, accumulating millions of views and sparking discussions across the platform.',
            'source_name': 'TikTok Creator',
            'source_handle': 'tiktokcreator',
            'author': 'TikTok Creator',
            'author_handle': 'tiktokcreator',
            'time_ago': '3 hours ago',
            'likes': 890000,
            'shares': 125000,
            'comments': 45000,
            'views': 12500000,
            'trending': True,
            'breaking': False,
            'verified': False,
            'url': create_search_url('tiktok', f'{name} Goes Viral on TikTok')
        },
        {
            'title': f'{name} TikTok Challenge',
            'headline': f'New challenge featuring {name}',
            'content': f'Users are participating in a TikTok challenge inspired by {name}, creating their own versions and sharing them.',
            'source_name': 'Challenge Creator',
            'source_handle': 'challengecreator',
            'author': 'Challenge Creator',
            'author_handle': 'challengecreator',
            'time_ago': '6 hours ago',
            'likes': 450000,
            'shares': 68000,
            'comments': 22000,
            'views': 8500000,
            'trending': True,
            'breaking': False,
            'verified': False,
            'url': create_search_url('tiktok', f'{name} TikTok Challenge')
        },
        {
            'title': f'{name} Official TikTok Account',
            'headline': f'Latest content from {name}',
            'content': f'{name} posted new content on their official TikTok account, engaging with fans and sharing updates.',
            'source_name': name,
            'source_handle': f'{name_lower.replace(" ", "")}',
            'author': name,
            'author_handle': f'{name_lower.replace(" ", "")}',
            'time_ago': '8 hours ago',
            'likes': 320000,
            'shares': 45000,
            'comments': 15000,
            'views': 6200000,
            'trending': False,
            'breaking': False,
            'verified': True,
            'url': create_search_url('tiktok', f'{name} Official TikTok Account')
        },
        {
            'title': f'Fan-Made {name} Compilation',
            'headline': f'Best moments of {name}',
            'content': f'A fan created a compilation video of the best moments featuring {name}, which has gained popularity on TikTok.',
            'source_name': 'Fan Account',
            'source_handle': f'{name_lower.replace(" ", "")}fan',
            'author': 'Fan Creator',
            'author_handle': f'{name_lower.replace(" ", "")}fan',
            'time_ago': '12 hours ago',
            'likes': 280000,
            'shares': 38000,
            'comments': 12000,
            'views': 4800000,
            'trending': False,
            'breaking': False,
            'verified': False,
            'url': create_search_url('tiktok', f'Fan-Made {name} Compilation')
        },
        {
            'title': f'{name} TikTok Duet',
            'headline': f'Popular duet with {name}',
            'content': f'Users are creating duets with {name}\'s content, adding their own creative spin and interpretations.',
            'source_name': 'Duet Creator',
            'source_handle': 'duetcreator',
            'author': 'Duet Creator',
            'author_handle': 'duetcreator',
            'time_ago': '1 day ago',
            'likes': 180000,
            'shares': 25000,
            'comments': 8500,
            'views': 3200000,
            'trending': False,
            'breaking': False,
            'verified': False,
            'url': create_search_url('tiktok', f'{name} TikTok Duet')
        }
    ]
    
    # YouTube News - At least 5 articles
    news['youtube'] = [
        {
            'title': f'Latest News About {name}',
            'headline': f'Comprehensive coverage of {name}',
            'content': f'A detailed video covering the latest news and updates about {name}. The video includes interviews, analysis, and exclusive information.',
            'source_name': 'News Channel',
            'source_handle': 'newschannel',
            'author': 'News Reporter',
            'author_handle': 'newsreporter',
            'time_ago': '6 hours ago',
            'likes': 12500,
            'comments': 890,
            'views': 450000,
            'trending': False,
            'breaking': False,
            'verified': True,
            'url': create_search_url('youtube', f'Latest News About {name}')
        },
        {
            'title': f'{name} Interview - Full Video',
            'headline': f'Exclusive interview with {name}',
            'content': f'Watch the full exclusive interview with {name}, where they discuss their latest projects, future plans, and personal insights.',
            'source_name': 'Interview Channel',
            'source_handle': 'interviewchannel',
            'author': 'Interviewer',
            'author_handle': 'interviewer',
            'time_ago': '1 day ago',
            'likes': 25000,
            'comments': 1500,
            'views': 1200000,
            'trending': True,
            'breaking': False,
            'verified': True,
            'url': create_search_url('youtube', f'{name} Interview - Full Video')
        },
        {
            'title': f'{name} Documentary',
            'headline': f'In-depth documentary about {name}',
            'content': f'A comprehensive documentary exploring the life and career of {name}, featuring exclusive footage and interviews.',
            'source_name': 'Documentary Channel',
            'source_handle': 'docchannel',
            'author': 'Documentary Producer',
            'author_handle': 'docproducer',
            'time_ago': '2 days ago',
            'likes': 45000,
            'comments': 3200,
            'views': 2800000,
            'trending': False,
            'breaking': False,
            'verified': True,
            'url': create_search_url('youtube', f'{name} Documentary')
        },
        {
            'title': f'{name} Reaction Video',
            'headline': f'Popular reaction to {name}',
            'content': f'Content creators are reacting to {name}\'s latest news and updates, sharing their thoughts and analysis.',
            'source_name': 'Reaction Channel',
            'source_handle': 'reactionchannel',
            'author': 'Reaction Creator',
            'author_handle': 'reactioncreator',
            'time_ago': '3 days ago',
            'likes': 18000,
            'comments': 1200,
            'views': 850000,
            'trending': False,
            'breaking': False,
            'verified': False,
            'url': create_search_url('youtube', f'{name} Reaction Video')
        },
        {
            'title': f'{name} Analysis and Breakdown',
            'headline': f'Detailed analysis of {name}',
            'content': f'An in-depth analysis video breaking down the latest developments and news about {name}, with expert commentary.',
            'source_name': 'Analysis Channel',
            'source_handle': 'analysischannel',
            'author': 'Analyst',
            'author_handle': 'analyst',
            'time_ago': '4 days ago',
            'likes': 22000,
            'comments': 1800,
            'views': 1500000,
            'trending': False,
            'breaking': False,
            'verified': True,
            'url': create_search_url('youtube', f'{name} Analysis and Breakdown')
        }
    ]
    
    # Facebook News - At least 5 articles
    news['facebook'] = [
        {
            'title': f'{name} Updates Facebook Page',
            'headline': f'New post from {name}',
            'content': f'{name} shared an important update on their Facebook page, providing fans with the latest information and news.',
            'source_name': name,
            'source_handle': f'{name_lower.replace(" ", ".")}',
            'author': name,
            'author_handle': f'{name_lower.replace(" ", ".")}',
            'time_ago': '4 hours ago',
            'likes': 18000,
            'shares': 3200,
            'comments': 890,
            'views': 250000,
            'trending': False,
            'breaking': False,
            'verified': True,
            'url': create_search_url('facebook', f'{name} Updates Facebook Page')
        },
        {
            'title': f'{name} Facebook Live Session',
            'headline': f'Live Q&A with {name}',
            'content': f'{name} hosted a Facebook Live session, answering questions from fans and sharing updates in real-time.',
            'source_name': name,
            'source_handle': f'{name_lower.replace(" ", ".")}',
            'author': name,
            'author_handle': f'{name_lower.replace(" ", ".")}',
            'time_ago': '1 day ago',
            'likes': 25000,
            'shares': 4800,
            'comments': 1500,
            'views': 450000,
            'trending': False,
            'breaking': False,
            'verified': True,
            'url': create_search_url('facebook', f'{name} Facebook Live Session')
        },
        {
            'title': f'{name} Community Discussion',
            'headline': f'Fans discuss {name} on Facebook',
            'content': f'Facebook groups dedicated to {name} are active with discussions, sharing news, and updates about recent developments.',
            'source_name': f'{name} Community',
            'source_handle': f'{name_lower.replace(" ", ".")}.community',
            'author': 'Community Admin',
            'author_handle': f'{name_lower.replace(" ", ".")}.community',
            'time_ago': '2 days ago',
            'likes': 12000,
            'shares': 2100,
            'comments': 680,
            'views': 180000,
            'trending': False,
            'breaking': False,
            'verified': False,
            'url': create_search_url('facebook', f'{name} Community Discussion')
        },
        {
            'title': f'{name} Photo Album',
            'headline': f'New photos from {name}',
            'content': f'{name} shared a new photo album on Facebook, showcasing recent events and activities.',
            'source_name': name,
            'source_handle': f'{name_lower.replace(" ", ".")}',
            'author': name,
            'author_handle': f'{name_lower.replace(" ", ".")}',
            'time_ago': '3 days ago',
            'likes': 15000,
            'shares': 2800,
            'comments': 520,
            'views': 320000,
            'trending': False,
            'breaking': False,
            'verified': True,
            'url': create_search_url('facebook', f'{name} Photo Album')
        },
        {
            'title': f'{name} Event Announcement',
            'headline': f'Upcoming event featuring {name}',
            'content': f'{name} announced an upcoming event on Facebook, with details about dates, location, and how to participate.',
            'source_name': name,
            'source_handle': f'{name_lower.replace(" ", ".")}',
            'author': name,
            'author_handle': f'{name_lower.replace(" ", ".")}',
            'time_ago': '5 days ago',
            'likes': 22000,
            'shares': 5500,
            'comments': 1200,
            'views': 580000,
            'trending': True,
            'breaking': False,
            'verified': True,
            'url': create_search_url('facebook', f'{name} Event Announcement')
        }
    ]
    
    # Reddit News - At least 5 articles
    news['reddit'] = [
        {
            'title': f'Discussion Thread: {name}',
            'headline': f'Reddit users discuss {name}',
            'content': f'A popular discussion thread on Reddit about {name} has gained significant attention, with users sharing opinions, news, and updates.',
            'source_name': f'r/{name_lower.replace(" ", "")}',
            'source_handle': name_lower.replace(" ", ""),
            'author': 'Reddit User',
            'author_handle': 'redditor',
            'time_ago': '8 hours ago',
            'likes': 2500,
            'comments': 450,
            'views': 125000,
            'trending': False,
            'breaking': False,
            'verified': False,
            'url': create_search_url('reddit', f'Discussion Thread: {name}')
        },
        {
            'title': f'{name} AMA Thread',
            'headline': f'Ask Me Anything with {name}',
            'content': f'{name} hosted an AMA (Ask Me Anything) session on Reddit, answering questions from the community.',
            'source_name': f'r/IAmA',
            'source_handle': 'iama',
            'author': name,
            'author_handle': name_lower.replace(" ", ""),
            'time_ago': '1 day ago',
            'likes': 8500,
            'comments': 1200,
            'views': 450000,
            'trending': True,
            'breaking': False,
            'verified': True,
            'url': create_search_url('reddit', f'{name} AMA Thread')
        },
        {
            'title': f'{name} News Roundup',
            'headline': f'Weekly news about {name}',
            'content': f'A comprehensive roundup of all the latest news and developments about {name}, compiled by Reddit users.',
            'source_name': f'r/{name_lower.replace(" ", "")}',
            'source_handle': name_lower.replace(" ", ""),
            'author': 'News Compiler',
            'author_handle': 'newscompiler',
            'time_ago': '2 days ago',
            'likes': 4200,
            'comments': 680,
            'views': 280000,
            'trending': False,
            'breaking': False,
            'verified': False,
            'url': create_search_url('reddit', f'{name} News Roundup')
        },
        {
            'title': f'{name} Analysis Post',
            'headline': f'In-depth analysis of {name}',
            'content': f'A detailed analysis post about {name}, examining recent developments and their implications.',
            'source_name': f'r/{name_lower.replace(" ", "")}',
            'source_handle': name_lower.replace(" ", ""),
            'author': 'Analyst',
            'author_handle': 'analyst',
            'time_ago': '3 days ago',
            'likes': 6800,
            'comments': 950,
            'views': 380000,
            'trending': False,
            'breaking': False,
            'verified': False,
            'url': create_search_url('reddit', f'{name} Analysis Post')
        },
        {
            'title': f'{name} Meme Compilation',
            'headline': f'Best memes about {name}',
            'content': f'Reddit users are sharing and creating memes related to {name}, with many going viral on the platform.',
            'source_name': f'r/memes',
            'source_handle': 'memes',
            'author': 'Meme Creator',
            'author_handle': 'memecreator',
            'time_ago': '4 days ago',
            'likes': 12500,
            'comments': 1800,
            'views': 650000,
            'trending': True,
            'breaking': False,
            'verified': False,
            'url': create_search_url('reddit', f'{name} Meme Compilation')
        }
    ]
    
    # LinkedIn News - At least 5 articles
    news['linkedin'] = [
        {
            'title': f'Professional Update from {name}',
            'headline': f'{name} shares professional news',
            'content': f'{name} posted a professional update on LinkedIn, sharing insights about their career, achievements, or industry news.',
            'source_name': name,
            'source_handle': f'{name_lower.replace(" ", "-")}',
            'author': name,
            'author_handle': f'{name_lower.replace(" ", "-")}',
            'time_ago': '12 hours ago',
            'likes': 3200,
            'comments': 180,
            'views': 45000,
            'trending': False,
            'breaking': False,
            'verified': True,
            'url': create_search_url('linkedin', f'Professional Update from {name}')
        },
        {
            'title': f'{name} Industry Insights',
            'headline': f'Thought leadership from {name}',
            'content': f'{name} shared valuable industry insights on LinkedIn, discussing trends and future developments.',
            'source_name': name,
            'source_handle': f'{name_lower.replace(" ", "-")}',
            'author': name,
            'author_handle': f'{name_lower.replace(" ", "-")}',
            'time_ago': '1 day ago',
            'likes': 4800,
            'comments': 320,
            'views': 85000,
            'trending': False,
            'breaking': False,
            'verified': True,
            'url': create_search_url('linkedin', f'{name} Industry Insights')
        },
        {
            'title': f'{name} Career Milestone',
            'headline': f'Professional achievement by {name}',
            'content': f'{name} announced a significant career milestone on LinkedIn, celebrating their professional achievements.',
            'source_name': name,
            'source_handle': f'{name_lower.replace(" ", "-")}',
            'author': name,
            'author_handle': f'{name_lower.replace(" ", "-")}',
            'time_ago': '2 days ago',
            'likes': 6500,
            'comments': 450,
            'views': 120000,
            'trending': False,
            'breaking': False,
            'verified': True,
            'url': create_search_url('linkedin', f'{name} Career Milestone')
        },
        {
            'title': f'{name} Company Update',
            'headline': f'Business news from {name}',
            'content': f'{name} shared company updates and business news on LinkedIn, keeping professional network informed.',
            'source_name': f'{name} Company',
            'source_handle': f'{name_lower.replace(" ", "-")}-company',
            'author': 'Company Rep',
            'author_handle': f'{name_lower.replace(" ", "-")}-company',
            'time_ago': '3 days ago',
            'likes': 3800,
            'comments': 250,
            'views': 68000,
            'trending': False,
            'breaking': False,
            'verified': True,
            'url': create_search_url('linkedin', f'{name} Company Update')
        },
        {
            'title': f'{name} Networking Event',
            'headline': f'Professional event featuring {name}',
            'content': f'{name} announced participation in an upcoming networking event, inviting professionals to connect.',
            'source_name': name,
            'source_handle': f'{name_lower.replace(" ", "-")}',
            'author': name,
            'author_handle': f'{name_lower.replace(" ", "-")}',
            'time_ago': '5 days ago',
            'likes': 2800,
            'comments': 180,
            'views': 52000,
            'trending': False,
            'breaking': False,
            'verified': True,
            'url': create_search_url('linkedin', f'{name} Networking Event')
        }
    ]
    
    # CNN News - At least 5 articles
    news['cnn'] = [
        {
            'title': f'Breaking: {common_news_title}',
            'headline': f'{name} announces new project',
            'content': f'CNN reports: {common_news_content} The story has gained significant attention from viewers and readers worldwide.',
            'source_name': 'CNN',
            'source_handle': 'cnn',
            'author': 'CNN Reporter',
            'author_handle': 'cnnreporter',
            'time_ago': '3 hours ago',
            'likes': 12500,
            'shares': 3200,
            'comments': 890,
            'views': 850000,
            'trending': True,
            'breaking': True,
            'verified': True,
            'url': create_search_url('cnn', f'Breaking: {common_news_title}')
        },
        {
            'title': f'{name} Makes Headlines: Latest Developments',
            'headline': f'Breaking news about {name}',
            'content': f'CNN reports on the latest developments involving {name}. The story has gained significant attention from viewers and readers worldwide.',
            'source_name': 'CNN',
            'source_handle': 'cnn',
            'author': 'CNN Reporter',
            'author_handle': 'cnnreporter',
            'time_ago': '5 hours ago',
            'likes': 9800,
            'shares': 2500,
            'comments': 680,
            'views': 720000,
            'trending': False,
            'breaking': False,
            'verified': True,
            'url': create_search_url('cnn', f'{name} Makes Headlines: Latest Developments')
        },
        {
            'title': f'In-Depth Analysis: The Impact of {name}',
            'headline': f'Comprehensive coverage of {name}',
            'content': f'CNN provides an in-depth analysis of {name}, exploring the broader implications and impact on various sectors.',
            'source_name': 'CNN',
            'source_handle': 'cnn',
            'author': 'CNN Analyst',
            'author_handle': 'cnnanalyst',
            'time_ago': '8 hours ago',
            'likes': 8500,
            'shares': 2100,
            'comments': 560,
            'views': 420000,
            'trending': False,
            'breaking': False,
            'verified': True,
            'url': create_search_url('cnn', f'In-Depth Analysis: The Impact of {name}')
        },
        {
            'title': f'{name} Exclusive Interview',
            'headline': f'CNN exclusive with {name}',
            'content': f'CNN secured an exclusive interview with {name}, discussing their latest projects, future plans, and addressing recent developments.',
            'source_name': 'CNN',
            'source_handle': 'cnn',
            'author': 'CNN Interviewer',
            'author_handle': 'cnninterviewer',
            'time_ago': '1 day ago',
            'likes': 18000,
            'shares': 4800,
            'comments': 1200,
            'views': 1200000,
            'trending': True,
            'breaking': False,
            'verified': True,
            'url': create_search_url('cnn', f'{name} Exclusive Interview')
        },
        {
            'title': f'{name} Feature Story',
            'headline': f'CNN feature on {name}',
            'content': f'CNN published a feature story about {name}, covering their background, achievements, and current activities.',
            'source_name': 'CNN',
            'source_handle': 'cnn',
            'author': 'CNN Feature Writer',
            'author_handle': 'cnnfeature',
            'time_ago': '2 days ago',
            'likes': 9800,
            'shares': 2500,
            'comments': 680,
            'views': 650000,
            'trending': False,
            'breaking': False,
            'verified': True,
            'url': create_search_url('cnn', f'{name} Feature Story')
        },
        {
            'title': f'{name} News Update',
            'headline': f'Latest update on {name}',
            'content': f'CNN provides the latest news update about {name}, covering recent events and developments.',
            'source_name': 'CNN',
            'source_handle': 'cnn',
            'author': 'CNN News Desk',
            'author_handle': 'cnnnews',
            'time_ago': '3 days ago',
            'likes': 6200,
            'shares': 1800,
            'comments': 420,
            'views': 380000,
            'trending': False,
            'breaking': False,
            'verified': True,
            'url': create_search_url('cnn', f'{name} News Update')
        }
    ]
    
    # BBC News - At least 5 articles
    news['bbc'] = [
        {
            'title': f'{name} in the Spotlight: What You Need to Know',
            'headline': f'BBC coverage of {name}',
            'content': f'The BBC reports on {name}, providing comprehensive coverage and analysis of the latest developments and their significance.',
            'source_name': 'BBC News',
            'source_handle': 'bbcnews',
            'author': 'BBC Correspondent',
            'author_handle': 'bbccorrespondent',
            'time_ago': '4 hours ago',
            'likes': 15000,
            'shares': 4500,
            'comments': 1200,
            'views': 950000,
            'trending': True,
            'breaking': False,
            'verified': True,
            'url': create_search_url('bbc', f'{name} in the Spotlight: What You Need to Know')
        },
        {
            'title': f'Exclusive Interview: {name} Speaks Out',
            'headline': f'BBC exclusive with {name}',
            'content': f'BBC News secured an exclusive interview with {name}, discussing their latest projects, future plans, and addressing recent developments.',
            'source_name': 'BBC News',
            'source_handle': 'bbcnews',
            'author': 'BBC Interviewer',
            'author_handle': 'bbcinterviewer',
            'time_ago': '1 day ago',
            'likes': 22000,
            'shares': 6800,
            'comments': 1800,
            'views': 1500000,
            'trending': True,
            'breaking': False,
            'verified': True,
            'url': create_search_url('bbc', f'Exclusive Interview: {name} Speaks Out')
        },
        {
            'title': f'{name} Documentary',
            'headline': f'BBC documentary about {name}',
            'content': f'The BBC aired a documentary about {name}, exploring their background, achievements, and impact.',
            'source_name': 'BBC News',
            'source_handle': 'bbcnews',
            'author': 'BBC Documentary Team',
            'author_handle': 'bbcdoc',
            'time_ago': '2 days ago',
            'likes': 28000,
            'shares': 8500,
            'comments': 2200,
            'views': 2800000,
            'trending': False,
            'breaking': False,
            'verified': True,
            'url': create_search_url('bbc', f'{name} Documentary')
        },
        {
            'title': f'{name} News Analysis',
            'headline': f'BBC analysis of {name}',
            'content': f'BBC News provides detailed analysis of the latest news about {name}, examining various aspects and implications.',
            'source_name': 'BBC News',
            'source_handle': 'bbcnews',
            'author': 'BBC Analyst',
            'author_handle': 'bbcanalyst',
            'time_ago': '3 days ago',
            'likes': 12000,
            'shares': 3200,
            'comments': 850,
            'views': 850000,
            'trending': False,
            'breaking': False,
            'verified': True,
            'url': create_search_url('bbc', f'{name} News Analysis')
        },
        {
            'title': f'{name} Feature Article',
            'headline': f'In-depth feature on {name}',
            'content': f'BBC News published a comprehensive feature article about {name}, covering their story and recent developments.',
            'source_name': 'BBC News',
            'source_handle': 'bbcnews',
            'author': 'BBC Feature Writer',
            'author_handle': 'bbcfeature',
            'time_ago': '4 days ago',
            'likes': 9800,
            'shares': 2800,
            'comments': 620,
            'views': 720000,
            'trending': False,
            'breaking': False,
            'verified': True,
            'url': create_search_url('bbc', f'{name} Feature Article')
        }
    ]
    
    # Reuters - At least 5 articles
    news['reuters'] = [
        {
            'title': f'{name} Announcement Shakes Industry',
            'headline': f'Reuters reports on {name}',
            'content': f'Reuters provides breaking news coverage of {name}, with detailed reporting on the announcement and its potential impact on the industry.',
            'source_name': 'Reuters',
            'source_handle': 'reuters',
            'author': 'Reuters Reporter',
            'author_handle': 'reutersreporter',
            'time_ago': '2 hours ago',
            'likes': 9800,
            'shares': 2800,
            'comments': 650,
            'views': 720000,
            'trending': True,
            'breaking': True,
            'verified': True,
            'url': f'https://www.reuters.com/search/news?blob={name.replace(" ", "+")}'
        },
        {
            'title': f'{name} Business Impact',
            'headline': f'Reuters business analysis of {name}',
            'content': f'Reuters analyzes the business impact of {name}\'s recent developments, examining market reactions and industry implications.',
            'source_name': 'Reuters',
            'source_handle': 'reuters',
            'author': 'Reuters Business Reporter',
            'author_handle': 'reutersbusiness',
            'time_ago': '1 day ago',
            'likes': 8500,
            'shares': 2200,
            'comments': 520,
            'views': 580000,
            'trending': False,
            'breaking': False,
            'verified': True,
            'url': f'https://www.reuters.com/search/news?blob={name.replace(" ", "+")}'
        },
        {
            'title': f'{name} Global Coverage',
            'headline': f'Reuters global news on {name}',
            'content': f'Reuters provides global coverage of {name}, reporting from multiple locations and perspectives.',
            'source_name': 'Reuters',
            'source_handle': 'reuters',
            'author': 'Reuters Global Correspondent',
            'author_handle': 'reutersglobal',
            'time_ago': '2 days ago',
            'likes': 7200,
            'shares': 1800,
            'comments': 420,
            'views': 480000,
            'trending': False,
            'breaking': False,
            'verified': True,
            'url': f'https://www.reuters.com/search/news?blob={name.replace(" ", "+")}'
        },
        {
            'title': f'{name} Technology Report',
            'headline': f'Reuters tech coverage of {name}',
            'content': f'Reuters covers the technology aspects of {name}\'s activities, examining innovations and tech industry connections.',
            'source_name': 'Reuters',
            'source_handle': 'reuters',
            'author': 'Reuters Tech Reporter',
            'author_handle': 'reuterstech',
            'time_ago': '3 days ago',
            'likes': 6800,
            'shares': 1600,
            'comments': 380,
            'views': 420000,
            'trending': False,
            'breaking': False,
            'verified': True,
            'url': f'https://www.reuters.com/search/news?blob={name.replace(" ", "+")}'
        },
        {
            'title': f'{name} Market Update',
            'headline': f'Reuters market news on {name}',
            'content': f'Reuters provides market updates related to {name}, covering financial implications and market reactions.',
            'source_name': 'Reuters',
            'source_handle': 'reuters',
            'author': 'Reuters Market Reporter',
            'author_handle': 'reutersmarket',
            'time_ago': '4 days ago',
            'likes': 6200,
            'shares': 1400,
            'comments': 320,
            'views': 380000,
            'trending': False,
            'breaking': False,
            'verified': True,
            'url': f'https://www.reuters.com/search/news?blob={name.replace(" ", "+")}'
        }
    ]
    
    # The Guardian - At least 5 articles
    news['guardian'] = [
        {
            'title': f'{name}: A Comprehensive Look at Recent Developments',
            'headline': f'Guardian coverage of {name}',
            'content': f'The Guardian provides comprehensive coverage of {name}, offering detailed analysis and multiple perspectives on the story.',
            'source_name': 'The Guardian',
            'source_handle': 'guardian',
            'author': 'Guardian Journalist',
            'author_handle': 'guardianjournalist',
            'time_ago': '6 hours ago',
            'likes': 11200,
            'shares': 3400,
            'comments': 980,
            'views': 680000,
            'trending': False,
            'breaking': False,
            'verified': True,
            'url': f'https://www.theguardian.com/search?q={name.replace(" ", "+")}'
        },
        {
            'title': f'{name} Opinion Piece',
            'headline': f'Guardian opinion on {name}',
            'content': f'The Guardian published an opinion piece about {name}, offering editorial perspective and analysis.',
            'source_name': 'The Guardian',
            'source_handle': 'guardian',
            'author': 'Guardian Opinion Writer',
            'author_handle': 'guardianopinion',
            'time_ago': '1 day ago',
            'likes': 9800,
            'shares': 2800,
            'comments': 1200,
            'views': 580000,
            'trending': False,
            'breaking': False,
            'verified': True,
            'url': f'https://www.theguardian.com/search?q={name.replace(" ", "+")}'
        },
        {
            'title': f'{name} Investigation',
            'headline': f'Guardian investigation into {name}',
            'content': f'The Guardian conducted an investigation into {name}, uncovering new information and providing in-depth reporting.',
            'source_name': 'The Guardian',
            'source_handle': 'guardian',
            'author': 'Guardian Investigative Reporter',
            'author_handle': 'guardianinvestigative',
            'time_ago': '2 days ago',
            'likes': 15000,
            'shares': 4500,
            'comments': 1800,
            'views': 950000,
            'trending': True,
            'breaking': False,
            'verified': True,
            'url': f'https://www.theguardian.com/search?q={name.replace(" ", "+")}'
        },
        {
            'title': f'{name} Profile',
            'headline': f'Guardian profile of {name}',
            'content': f'The Guardian published a detailed profile of {name}, exploring their background, career, and impact.',
            'source_name': 'The Guardian',
            'source_handle': 'guardian',
            'author': 'Guardian Profile Writer',
            'author_handle': 'guardianprofile',
            'time_ago': '3 days ago',
            'likes': 11200,
            'shares': 3200,
            'comments': 850,
            'views': 720000,
            'trending': False,
            'breaking': False,
            'verified': True,
            'url': f'https://www.theguardian.com/search?q={name.replace(" ", "+")}'
        },
        {
            'title': f'{name} News Roundup',
            'headline': f'Guardian weekly roundup on {name}',
            'content': f'The Guardian provides a weekly roundup of all news related to {name}, summarizing key developments.',
            'source_name': 'The Guardian',
            'source_handle': 'guardian',
            'author': 'Guardian News Desk',
            'author_handle': 'guardiannews',
            'time_ago': '5 days ago',
            'likes': 8500,
            'shares': 2200,
            'comments': 520,
            'views': 480000,
            'trending': False,
            'breaking': False,
            'verified': True,
            'url': f'https://www.theguardian.com/search?q={name.replace(" ", "+")}'
        }
    ]
    
    # Forbes - At least 5 articles
    news['forbes'] = [
        {
            'title': f'{name}: Business Impact and Market Analysis',
            'headline': f'Forbes analysis of {name}',
            'content': f'Forbes provides business-focused analysis of {name}, examining the financial implications and market impact of recent developments.',
            'source_name': 'Forbes',
            'source_handle': 'forbes',
            'author': 'Forbes Contributor',
            'author_handle': 'forbescontributor',
            'time_ago': '5 hours ago',
            'likes': 8900,
            'shares': 2500,
            'comments': 420,
            'views': 550000,
            'trending': False,
            'breaking': False,
            'verified': True,
            'url': f'https://www.forbes.com/search/?q={name.replace(" ", "+")}'
        },
        {
            'title': f'How {name} is Changing the Industry',
            'headline': f'Forbes feature on {name}',
            'content': f'Forbes explores how {name} is reshaping the industry landscape, with insights from experts and industry leaders.',
            'source_name': 'Forbes',
            'source_handle': 'forbes',
            'author': 'Forbes Editor',
            'author_handle': 'forbeseditor',
            'time_ago': '1 day ago',
            'likes': 15000,
            'shares': 4200,
            'comments': 750,
            'views': 980000,
            'trending': True,
            'breaking': False,
            'verified': True,
            'url': f'https://www.forbes.com/search/?q={name.replace(" ", "+")}'
        },
        {
            'title': f'{name} Net Worth and Business',
            'headline': f'Forbes business profile of {name}',
            'content': f'Forbes examines {name}\'s business ventures, net worth, and financial standing in the industry.',
            'source_name': 'Forbes',
            'source_handle': 'forbes',
            'author': 'Forbes Business Reporter',
            'author_handle': 'forbesbusiness',
            'time_ago': '2 days ago',
            'likes': 12500,
            'shares': 3500,
            'comments': 620,
            'views': 850000,
            'trending': False,
            'breaking': False,
            'verified': True,
            'url': f'https://www.forbes.com/search/?q={name.replace(" ", "+")}'
        },
        {
            'title': f'{name} Leadership Insights',
            'headline': f'Forbes leadership article on {name}',
            'content': f'Forbes publishes insights about {name}\'s leadership style and business strategies, offering lessons for entrepreneurs.',
            'source_name': 'Forbes',
            'source_handle': 'forbes',
            'author': 'Forbes Leadership Writer',
            'author_handle': 'forbesleadership',
            'time_ago': '3 days ago',
            'likes': 9800,
            'shares': 2800,
            'comments': 480,
            'views': 680000,
            'trending': False,
            'breaking': False,
            'verified': True,
            'url': f'https://www.forbes.com/search/?q={name.replace(" ", "+")}'
        },
        {
            'title': f'{name} Innovation Report',
            'headline': f'Forbes innovation coverage of {name}',
            'content': f'Forbes covers {name}\'s innovative approaches and contributions to their industry, highlighting groundbreaking work.',
            'source_name': 'Forbes',
            'source_handle': 'forbes',
            'author': 'Forbes Innovation Reporter',
            'author_handle': 'forbesinnovation',
            'time_ago': '4 days ago',
            'likes': 11200,
            'shares': 3200,
            'comments': 580,
            'views': 750000,
            'trending': False,
            'breaking': False,
            'verified': True,
            'url': f'https://www.forbes.com/search/?q={name.replace(" ", "+")}'
        }
    ]
    
    # TechCrunch - At least 5 articles
    news['techcrunch'] = [
        {
            'title': f'{name} Unveils New Technology Initiative',
            'headline': f'TechCrunch reports on {name}',
            'content': f'TechCrunch covers the latest technology developments from {name}, providing insights into the tech industry implications.',
            'source_name': 'TechCrunch',
            'source_handle': 'techcrunch',
            'author': 'TechCrunch Writer',
            'author_handle': 'techcrunchwriter',
            'time_ago': '3 hours ago',
            'likes': 12500,
            'shares': 3800,
            'comments': 1100,
            'views': 750000,
            'trending': True,
            'breaking': False,
            'verified': True,
            'url': f'https://techcrunch.com/?s={name.replace(" ", "+")}'
        },
        {
            'title': f'{name} Startup News',
            'headline': f'TechCrunch startup coverage of {name}',
            'content': f'TechCrunch reports on {name}\'s startup activities and tech ventures, covering funding, products, and market position.',
            'source_name': 'TechCrunch',
            'source_handle': 'techcrunch',
            'author': 'TechCrunch Startup Reporter',
            'author_handle': 'techcrunchstartup',
            'time_ago': '1 day ago',
            'likes': 9800,
            'shares': 2800,
            'comments': 680,
            'views': 620000,
            'trending': False,
            'breaking': False,
            'verified': True,
            'url': f'https://techcrunch.com/?s={name.replace(" ", "+")}'
        },
        {
            'title': f'{name} Product Launch',
            'headline': f'TechCrunch product review of {name}',
            'content': f'TechCrunch reviews {name}\'s latest product launch, providing technical analysis and market assessment.',
            'source_name': 'TechCrunch',
            'source_handle': 'techcrunch',
            'author': 'TechCrunch Product Reviewer',
            'author_handle': 'techcrunchreview',
            'time_ago': '2 days ago',
            'likes': 11200,
            'shares': 3200,
            'comments': 850,
            'views': 720000,
            'trending': False,
            'breaking': False,
            'verified': True,
            'url': f'https://techcrunch.com/?s={name.replace(" ", "+")}'
        },
        {
            'title': f'{name} Tech Industry Impact',
            'headline': f'TechCrunch analysis of {name}',
            'content': f'TechCrunch analyzes {name}\'s impact on the technology industry, examining trends and future implications.',
            'source_name': 'TechCrunch',
            'source_handle': 'techcrunch',
            'author': 'TechCrunch Analyst',
            'author_handle': 'techcrunchanalyst',
            'time_ago': '3 days ago',
            'likes': 8500,
            'shares': 2400,
            'comments': 520,
            'views': 580000,
            'trending': False,
            'breaking': False,
            'verified': True,
            'url': f'https://techcrunch.com/?s={name.replace(" ", "+")}'
        },
        {
            'title': f'{name} Funding News',
            'headline': f'TechCrunch funding report on {name}',
            'content': f'TechCrunch reports on {name}\'s funding activities, covering investments, valuations, and financial developments.',
            'source_name': 'TechCrunch',
            'source_handle': 'techcrunch',
            'author': 'TechCrunch Finance Reporter',
            'author_handle': 'techcrunchfinance',
            'time_ago': '4 days ago',
            'likes': 7200,
            'shares': 1800,
            'comments': 380,
            'views': 480000,
            'trending': False,
            'breaking': False,
            'verified': True,
            'url': f'https://techcrunch.com/?s={name.replace(" ", "+")}'
        }
    ]
    
    # The New York Times - At least 5 articles
    news['nytimes'] = [
        {
            'title': f'{name} in the News: What It Means',
            'headline': f'NY Times coverage of {name}',
            'content': f'The New York Times provides in-depth reporting on {name}, with comprehensive coverage and expert analysis.',
            'source_name': 'The New York Times',
            'source_handle': 'nytimes',
            'author': 'NY Times Reporter',
            'author_handle': 'nytimesreporter',
            'time_ago': '7 hours ago',
            'likes': 18000,
            'shares': 5200,
            'comments': 1400,
            'views': 1200000,
            'trending': True,
            'breaking': False,
            'verified': True,
            'url': f'https://www.nytimes.com/search?query={name.replace(" ", "+")}'
        },
        {
            'title': f'{name} Editorial',
            'headline': f'NY Times editorial on {name}',
            'content': f'The New York Times published an editorial about {name}, offering editorial perspective and policy analysis.',
            'source_name': 'The New York Times',
            'source_handle': 'nytimes',
            'author': 'NY Times Editorial Board',
            'author_handle': 'nytimeseditorial',
            'time_ago': '1 day ago',
            'likes': 15000,
            'shares': 4500,
            'comments': 1800,
            'views': 980000,
            'trending': False,
            'breaking': False,
            'verified': True,
            'url': f'https://www.nytimes.com/search?query={name.replace(" ", "+")}'
        },
        {
            'title': f'{name} Magazine Feature',
            'headline': f'NY Times Magazine on {name}',
            'content': f'The New York Times Magazine published a feature story about {name}, providing long-form journalism and in-depth coverage.',
            'source_name': 'The New York Times',
            'source_handle': 'nytimes',
            'author': 'NY Times Magazine Writer',
            'author_handle': 'nytimesmagazine',
            'time_ago': '2 days ago',
            'likes': 22000,
            'shares': 6800,
            'comments': 2200,
            'views': 1500000,
            'trending': True,
            'breaking': False,
            'verified': True,
            'url': f'https://www.nytimes.com/search?query={name.replace(" ", "+")}'
        },
        {
            'title': f'{name} Business Section',
            'headline': f'NY Times business news on {name}',
            'content': f'The New York Times Business section covers {name}\'s business activities, financial news, and market impact.',
            'source_name': 'The New York Times',
            'source_handle': 'nytimes',
            'author': 'NY Times Business Reporter',
            'author_handle': 'nytimesbusiness',
            'time_ago': '3 days ago',
            'likes': 12500,
            'shares': 3500,
            'comments': 850,
            'views': 850000,
            'trending': False,
            'breaking': False,
            'verified': True,
            'url': f'https://www.nytimes.com/search?query={name.replace(" ", "+")}'
        },
        {
            'title': f'{name} Culture Coverage',
            'headline': f'NY Times culture article on {name}',
            'content': f'The New York Times Culture section covers {name}\'s cultural impact and influence on society and media.',
            'source_name': 'The New York Times',
            'source_handle': 'nytimes',
            'author': 'NY Times Culture Reporter',
            'author_handle': 'nytimesculture',
            'time_ago': '4 days ago',
            'likes': 11200,
            'shares': 3200,
            'comments': 720,
            'views': 720000,
            'trending': False,
            'breaking': False,
            'verified': True,
            'url': f'https://www.nytimes.com/search?query={name.replace(" ", "+")}'
        }
    ]
    
    # The Washington Post - At least 5 articles
    news['washingtonpost'] = [
        {
            'title': f'Breaking: {name} Makes Major Move',
            'headline': f'Washington Post reports on {name}',
            'content': f'The Washington Post breaks the news about {name}, providing detailed coverage and immediate analysis of the development.',
            'source_name': 'The Washington Post',
            'source_handle': 'washingtonpost',
            'author': 'WP Reporter',
            'author_handle': 'wpreporter',
            'time_ago': '4 hours ago',
            'likes': 14200,
            'shares': 4100,
            'comments': 1100,
            'views': 880000,
            'trending': True,
            'breaking': True,
            'verified': True,
            'url': f'https://www.washingtonpost.com/newssearch/?query={name.replace(" ", "+")}'
        },
        {
            'title': f'{name} Politics Coverage',
            'headline': f'Washington Post politics on {name}',
            'content': f'The Washington Post covers {name}\'s political connections and policy implications, providing political analysis.',
            'source_name': 'The Washington Post',
            'source_handle': 'washingtonpost',
            'author': 'WP Politics Reporter',
            'author_handle': 'wppolitics',
            'time_ago': '1 day ago',
            'likes': 12500,
            'shares': 3800,
            'comments': 1200,
            'views': 850000,
            'trending': False,
            'breaking': False,
            'verified': True,
            'url': f'https://www.washingtonpost.com/newssearch/?query={name.replace(" ", "+")}'
        },
        {
            'title': f'{name} National News',
            'headline': f'Washington Post national coverage of {name}',
            'content': f'The Washington Post provides national news coverage of {name}, reporting on developments across the country.',
            'source_name': 'The Washington Post',
            'source_handle': 'washingtonpost',
            'author': 'WP National Reporter',
            'author_handle': 'wpnational',
            'time_ago': '2 days ago',
            'likes': 11200,
            'shares': 3200,
            'comments': 850,
            'views': 720000,
            'trending': False,
            'breaking': False,
            'verified': True,
            'url': f'https://www.washingtonpost.com/newssearch/?query={name.replace(" ", "+")}'
        },
        {
            'title': f'{name} Opinion Column',
            'headline': f'Washington Post opinion on {name}',
            'content': f'The Washington Post published an opinion column about {name}, offering editorial perspective and commentary.',
            'source_name': 'The Washington Post',
            'source_handle': 'washingtonpost',
            'author': 'WP Opinion Writer',
            'author_handle': 'wpopinion',
            'time_ago': '3 days ago',
            'likes': 9800,
            'shares': 2800,
            'comments': 1100,
            'views': 620000,
            'trending': False,
            'breaking': False,
            'verified': True,
            'url': f'https://www.washingtonpost.com/newssearch/?query={name.replace(" ", "+")}'
        },
        {
            'title': f'{name} Style Section',
            'headline': f'Washington Post style coverage of {name}',
            'content': f'The Washington Post Style section covers {name}\'s lifestyle, fashion, and cultural influence.',
            'source_name': 'The Washington Post',
            'source_handle': 'washingtonpost',
            'author': 'WP Style Reporter',
            'author_handle': 'wpstyle',
            'time_ago': '4 days ago',
            'likes': 8500,
            'shares': 2400,
            'comments': 520,
            'views': 520000,
            'trending': False,
            'breaking': False,
            'verified': True,
            'url': f'https://www.washingtonpost.com/newssearch/?query={name.replace(" ", "+")}'
        }
    ]
    
    # Associated Press (AP) - At least 5 articles
    news['ap'] = [
        {
            'title': f'{name} News: Latest Updates',
            'headline': f'AP News on {name}',
            'content': f'The Associated Press provides the latest updates on {name}, with factual reporting and comprehensive coverage.',
            'source_name': 'Associated Press',
            'source_handle': 'apnews',
            'author': 'AP Reporter',
            'author_handle': 'apreporter',
            'time_ago': '5 hours ago',
            'likes': 10500,
            'shares': 2900,
            'comments': 680,
            'views': 650000,
            'trending': False,
            'breaking': False,
            'verified': True,
            'url': f'https://apnews.com/search?q={name.replace(" ", "+")}'
        },
        {
            'title': f'{name} Breaking News',
            'headline': f'AP breaking news on {name}',
            'content': f'The Associated Press breaks the latest news about {name}, providing immediate coverage of developments.',
            'source_name': 'Associated Press',
            'source_handle': 'apnews',
            'author': 'AP Breaking News Desk',
            'author_handle': 'apbreaking',
            'time_ago': '1 day ago',
            'likes': 12500,
            'shares': 3800,
            'comments': 950,
            'views': 850000,
            'trending': True,
            'breaking': True,
            'verified': True,
            'url': f'https://apnews.com/search?q={name.replace(" ", "+")}'
        },
        {
            'title': f'{name} National Wire',
            'headline': f'AP national wire on {name}',
            'content': f'The Associated Press national wire service reports on {name}, providing news to outlets nationwide.',
            'source_name': 'Associated Press',
            'source_handle': 'apnews',
            'author': 'AP National Correspondent',
            'author_handle': 'apnational',
            'time_ago': '2 days ago',
            'likes': 9800,
            'shares': 2800,
            'comments': 620,
            'views': 720000,
            'trending': False,
            'breaking': False,
            'verified': True,
            'url': f'https://apnews.com/search?q={name.replace(" ", "+")}'
        },
        {
            'title': f'{name} International News',
            'headline': f'AP international coverage of {name}',
            'content': f'The Associated Press provides international coverage of {name}, reporting from global locations.',
            'source_name': 'Associated Press',
            'source_handle': 'apnews',
            'author': 'AP International Correspondent',
            'author_handle': 'apinternational',
            'time_ago': '3 days ago',
            'likes': 8500,
            'shares': 2400,
            'comments': 520,
            'views': 580000,
            'trending': False,
            'breaking': False,
            'verified': True,
            'url': f'https://apnews.com/search?q={name.replace(" ", "+")}'
        },
        {
            'title': f'{name} Fact Check',
            'headline': f'AP fact check on {name}',
            'content': f'The Associated Press fact-checked claims and statements related to {name}, providing verified information.',
            'source_name': 'Associated Press',
            'source_handle': 'apnews',
            'author': 'AP Fact Checker',
            'author_handle': 'apfactcheck',
            'time_ago': '4 days ago',
            'likes': 11200,
            'shares': 3500,
            'comments': 850,
            'views': 680000,
            'trending': False,
            'breaking': False,
            'verified': True,
            'url': f'https://apnews.com/search?q={name.replace(" ", "+")}'
        }
    ]
    
    # Bloomberg - At least 5 articles
    news['bloomberg'] = [
        {
            'title': f'{name}: Financial Markets React',
            'headline': f'Bloomberg coverage of {name}',
            'content': f'Bloomberg reports on how financial markets are reacting to news about {name}, with expert financial analysis.',
            'source_name': 'Bloomberg',
            'source_handle': 'bloomberg',
            'author': 'Bloomberg Analyst',
            'author_handle': 'bloomberganalyst',
            'time_ago': '3 hours ago',
            'likes': 11200,
            'shares': 3200,
            'comments': 850,
            'views': 720000,
            'trending': False,
            'breaking': False,
            'verified': True,
            'url': f'https://www.bloomberg.com/search?query={name.replace(" ", "+")}'
        },
        {
            'title': f'{name} Market Analysis',
            'headline': f'Bloomberg market report on {name}',
            'content': f'Bloomberg provides detailed market analysis of {name}\'s impact on financial markets and investment trends.',
            'source_name': 'Bloomberg',
            'source_handle': 'bloomberg',
            'author': 'Bloomberg Market Analyst',
            'author_handle': 'bloombergmarket',
            'time_ago': '1 day ago',
            'likes': 12500,
            'shares': 3800,
            'comments': 950,
            'views': 850000,
            'trending': False,
            'breaking': False,
            'verified': True,
            'url': f'https://www.bloomberg.com/search?query={name.replace(" ", "+")}'
        },
        {
            'title': f'{name} Business News',
            'headline': f'Bloomberg business coverage of {name}',
            'content': f'Bloomberg covers {name}\'s business activities, corporate news, and industry developments.',
            'source_name': 'Bloomberg',
            'source_handle': 'bloomberg',
            'author': 'Bloomberg Business Reporter',
            'author_handle': 'bloombergbusiness',
            'time_ago': '2 days ago',
            'likes': 9800,
            'shares': 2800,
            'comments': 620,
            'views': 720000,
            'trending': False,
            'breaking': False,
            'verified': True,
            'url': f'https://www.bloomberg.com/search?query={name.replace(" ", "+")}'
        },
        {
            'title': f'{name} Technology Finance',
            'headline': f'Bloomberg tech finance on {name}',
            'content': f'Bloomberg reports on {name}\'s technology investments and financial technology connections.',
            'source_name': 'Bloomberg',
            'source_handle': 'bloomberg',
            'author': 'Bloomberg Tech Finance Reporter',
            'author_handle': 'bloombergtech',
            'time_ago': '3 days ago',
            'likes': 8500,
            'shares': 2400,
            'comments': 520,
            'views': 580000,
            'trending': False,
            'breaking': False,
            'verified': True,
            'url': f'https://www.bloomberg.com/search?query={name.replace(" ", "+")}'
        },
        {
            'title': f'{name} Investment News',
            'headline': f'Bloomberg investment report on {name}',
            'content': f'Bloomberg covers investment news related to {name}, including funding, valuations, and financial strategies.',
            'source_name': 'Bloomberg',
            'source_handle': 'bloomberg',
            'author': 'Bloomberg Investment Reporter',
            'author_handle': 'bloomberginvestment',
            'time_ago': '4 days ago',
            'likes': 7200,
            'shares': 1800,
            'comments': 380,
            'views': 480000,
            'trending': False,
            'breaking': False,
            'verified': True,
            'url': f'https://www.bloomberg.com/search?query={name.replace(" ", "+")}'
        }
    ]
    
    # ESPN - At least 5 articles
    news['espn'] = [
        {
            'title': f'{name}: Sports News Update',
            'headline': f'ESPN reports on {name}',
            'content': f'ESPN provides the latest sports news about {name}, with coverage of games, performances, and team updates.',
            'source_name': 'ESPN',
            'source_handle': 'espn',
            'author': 'ESPN Reporter',
            'author_handle': 'espnreporter',
            'time_ago': '2 hours ago',
            'likes': 18500,
            'shares': 4800,
            'comments': 1200,
            'views': 950000,
            'trending': True,
            'breaking': False,
            'verified': True,
            'url': f'https://www.espn.com/search/results?q={name.replace(" ", "+")}'
        },
        {
            'title': f'{name} Game Highlights',
            'headline': f'ESPN highlights of {name}',
            'content': f'ESPN provides game highlights and analysis featuring {name}, covering key moments and performances.',
            'source_name': 'ESPN',
            'source_handle': 'espn',
            'author': 'ESPN Sports Analyst',
            'author_handle': 'espnanalyst',
            'time_ago': '1 day ago',
            'likes': 22000,
            'shares': 6800,
            'comments': 1800,
            'views': 1500000,
            'trending': True,
            'breaking': False,
            'verified': True,
            'url': f'https://www.espn.com/search/results?q={name.replace(" ", "+")}'
        },
        {
            'title': f'{name} Interview',
            'headline': f'ESPN interview with {name}',
            'content': f'ESPN conducted an interview with {name}, discussing their career, achievements, and future plans.',
            'source_name': 'ESPN',
            'source_handle': 'espn',
            'author': 'ESPN Interviewer',
            'author_handle': 'espninterviewer',
            'time_ago': '2 days ago',
            'likes': 15000,
            'shares': 4200,
            'comments': 950,
            'views': 1200000,
            'trending': False,
            'breaking': False,
            'verified': True,
            'url': f'https://www.espn.com/search/results?q={name.replace(" ", "+")}'
        },
        {
            'title': f'{name} Statistics and Analysis',
            'headline': f'ESPN stats on {name}',
            'content': f'ESPN provides statistical analysis of {name}\'s performance, with detailed metrics and comparisons.',
            'source_name': 'ESPN',
            'source_handle': 'espn',
            'author': 'ESPN Statistician',
            'author_handle': 'espnstats',
            'time_ago': '3 days ago',
            'likes': 12500,
            'shares': 3500,
            'comments': 680,
            'views': 850000,
            'trending': False,
            'breaking': False,
            'verified': True,
            'url': f'https://www.espn.com/search/results?q={name.replace(" ", "+")}'
        },
        {
            'title': f'{name} Feature Story',
            'headline': f'ESPN feature on {name}',
            'content': f'ESPN published a feature story about {name}, covering their journey, achievements, and impact on sports.',
            'source_name': 'ESPN',
            'source_handle': 'espn',
            'author': 'ESPN Feature Writer',
            'author_handle': 'espnfeature',
            'time_ago': '4 days ago',
            'likes': 18000,
            'shares': 5200,
            'comments': 1200,
            'views': 1100000,
            'trending': False,
            'breaking': False,
            'verified': True,
            'url': f'https://www.espn.com/search/results?q={name.replace(" ", "+")}'
        }
    ]
    
    # Filter out empty results
    news = {k: v for k, v in news.items() if v}
    
    return news


def detect_repeated_news(news_results):
    """Detect repeated news articles across platforms and mark repetition count"""
    # Collect all articles with their titles normalized
    article_groups = {}  # normalized_title -> list of (platform, article_index)
    
    # First pass: collect all articles and group by similar titles
    for platform, articles in news_results.items():
        for idx, article in enumerate(articles):
            title = article.get('title', '').lower().strip()
            # Normalize title for comparison (remove extra spaces, punctuation)
            normalized_title = ' '.join(title.split())
            
            if normalized_title not in article_groups:
                article_groups[normalized_title] = []
            article_groups[normalized_title].append((platform, idx))
    
    # Find repeated news (appears in multiple platforms or multiple times)
    repeated_news = {}
    for normalized_title, occurrences in article_groups.items():
        if len(occurrences) > 1:
            # This news appears multiple times
            repeated_news[normalized_title] = len(occurrences)
    
    # Mark articles with repetition count
    for platform, articles in news_results.items():
        for article in articles:
            title = article.get('title', '').lower().strip()
            normalized_title = ' '.join(title.split())
            
            if normalized_title in repeated_news:
                article['repetition_count'] = repeated_news[normalized_title]
                article['is_repeated'] = True
                # Mark as most repeated if it has the highest count
                max_count = max(repeated_news.values()) if repeated_news else 0
                if article['repetition_count'] == max_count:
                    article['is_most_repeated'] = True
            else:
                article['repetition_count'] = 1
                article['is_repeated'] = False
                article['is_most_repeated'] = False
    
    # Sort articles within each platform by repetition count (most repeated first)
    for platform in news_results:
        news_results[platform].sort(key=lambda x: (
            x.get('is_most_repeated', False),
            x.get('repetition_count', 1),
            x.get('trending', False),
            x.get('breaking', False)
        ), reverse=True)
    
    return news_results


def get_trending_repeated_news(news_results):
    """Get trending news that appears on multiple platforms"""
    trending_repeated = {}
    
    # Collect all trending and repeated articles
    for platform, articles in news_results.items():
        for article in articles:
            if article.get('trending', False) and article.get('is_repeated', False):
                title = article.get('title', '').lower().strip()
                normalized_title = ' '.join(title.split())
                
                if normalized_title not in trending_repeated:
                    trending_repeated[normalized_title] = {
                        'title': article.get('title', ''),
                        'headline': article.get('headline', ''),
                        'content': article.get('content', ''),
                        'platforms': [],
                        'repetition_count': article.get('repetition_count', 1),
                        'url': article.get('url', ''),
                        'total_engagement': 0,
                        'is_breaking': article.get('breaking', False)
                    }
                
                # Add platform info
                trending_repeated[normalized_title]['platforms'].append({
                    'name': str(platform) if platform else 'unknown',
                    'source_name': article.get('source_name', ''),
                    'time_ago': article.get('time_ago', ''),
                    'verified': article.get('verified', False)
                })
                
                # Sum engagement
                trending_repeated[normalized_title]['total_engagement'] += (
                    article.get('likes', 0) + 
                    article.get('shares', 0) + 
                    article.get('comments', 0)
                )
    
    # Convert to list and sort by repetition count and engagement
    trending_list = list(trending_repeated.values())
    trending_list.sort(key=lambda x: (x['repetition_count'], x['total_engagement']), reverse=True)
    
    return trending_list


def calculate_news_stats(news_results):
    """Calculate statistics from news search results"""
    total_articles = sum(len(articles) for articles in news_results.values())
    platforms_found = len(news_results)
    
    total_engagement = 0
    trending_count = 0
    repeated_count = 0
    most_repeated_count = 0
    trending_repeated_count = 0
    
    for articles in news_results.values():
        for article in articles:
            total_engagement += article.get('likes', 0) + article.get('shares', 0) + article.get('comments', 0)
            if article.get('trending', False):
                trending_count += 1
            if article.get('is_repeated', False):
                repeated_count += 1
            if article.get('is_most_repeated', False):
                most_repeated_count += 1
            if article.get('trending', False) and article.get('is_repeated', False):
                trending_repeated_count += 1
    
    return {
        'total_articles': total_articles,
        'platforms_found': platforms_found,
        'total_engagement': format_search_number(total_engagement),
        'trending_count': trending_count,
        'repeated_count': repeated_count,
        'most_repeated_count': most_repeated_count,
        'trending_repeated_count': trending_repeated_count
    }


@app.route('/detect-trends', methods=['POST'])
def detect_trends():
    """Detect trending topics, hashtags, and keywords"""
    try:
        data = request.json
        keyword = data.get('keyword', '').strip()
        platform = data.get('platform', 'general')
        
        if not keyword:
            return jsonify({'error': 'Keyword is required'}), 400
        
        # Analyze trends (simulated analysis - in production, this would use APIs)
        trends = analyze_trending_topics(keyword, platform)
        
        # Calculate statistics
        stats = calculate_trend_stats(trends)
        
        return jsonify({
            'success': True,
            'trends': trends,
            'stats': stats,
            'platform': platform,
            'keyword': keyword
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def analyze_trending_topics(keyword, platform):
    """Analyze trending topics based on keyword and platform"""
    keyword_lower = keyword.lower()
    
    # Simulated trending data (in production, this would use real APIs)
    # This provides example trends based on the keyword
    trends = []
    
    # Generate sample trends based on platform and keyword
    import urllib.parse
    keyword_encoded = urllib.parse.quote(keyword)
    keyword_hash = urllib.parse.quote(f'#{keyword}')
    
    if platform == 'twitter':
        trends = [
            {
                'title': f'🔍 Search Twitter for "{keyword}"',
                'hashtag': keyword,
                'description': f'Find all tweets about {keyword} - Click to see real tweets!',
                'engagement': 'Search',
                'mentions': 'All Tweets',
                'growth': 0,
                'tags': [keyword, 'search', 'twitter'],
                'url': f'https://twitter.com/search?q={keyword_encoded}&src=typed_query',
                'is_real_link': True
            },
            {
                'title': f'#{keyword} hashtag',
                'hashtag': keyword,
                'description': f'Browse all tweets with #{keyword} hashtag - Real posts you can read!',
                'engagement': 'Browse',
                'mentions': 'Hashtag',
                'growth': 0,
                'tags': [keyword, 'hashtag', 'browse'],
                'url': f'https://twitter.com/hashtag/{keyword_encoded}',
                'is_real_link': True
            },
            {
                'title': f'{keyword} - Latest tweets',
                'hashtag': f'{keyword}Latest',
                'description': f'See latest tweets about {keyword} - Real-time updates!',
                'engagement': 'Latest',
                'mentions': 'Real-time',
                'growth': 0,
                'tags': [keyword, 'latest', 'realtime'],
                'url': f'https://twitter.com/search?q={keyword_encoded}&src=typed_query&f=live',
                'is_real_link': True
            },
            {
                'title': f'{keyword} - Top tweets',
                'hashtag': f'{keyword}Top',
                'description': f'Most popular tweets about {keyword} - See what\'s trending!',
                'engagement': 'Top',
                'mentions': 'Popular',
                'growth': 0,
                'tags': [keyword, 'top', 'popular'],
                'url': f'https://twitter.com/search?q={keyword_encoded}&src=typed_query&f=top',
                'is_real_link': True
            }
        ]
    elif platform == 'instagram':
        trends = [
            {
                'title': f'🔍 Search Instagram for "{keyword}"',
                'hashtag': keyword,
                'description': f'Find all Instagram posts about {keyword} - Browse real content!',
                'engagement': 'Search',
                'mentions': 'All Posts',
                'growth': 0,
                'tags': [keyword, 'search', 'instagram'],
                'url': f'https://www.instagram.com/explore/search/keyword/?q={keyword_encoded}',
                'is_real_link': True
            },
            {
                'title': f'#{keyword} posts',
                'hashtag': keyword,
                'description': f'Browse all posts with #{keyword} hashtag - See photos and videos!',
                'engagement': 'Browse',
                'mentions': 'Hashtag',
                'growth': 0,
                'tags': [keyword, 'hashtag', 'browse'],
                'url': f'https://www.instagram.com/explore/tags/{keyword_encoded}/',
                'is_real_link': True
            },
            {
                'title': f'{keyword} reels',
                'hashtag': f'{keyword}Reels',
                'description': f'Watch Instagram Reels about {keyword} - Trending short videos!',
                'engagement': 'Watch',
                'mentions': 'Reels',
                'growth': 0,
                'tags': [keyword, 'reels', 'video'],
                'url': f'https://www.instagram.com/explore/search/keyword/?q={keyword_encoded}',
                'is_real_link': True
            }
        ]
    elif platform == 'tiktok':
        import urllib.parse
        keyword_encoded = urllib.parse.quote(keyword)
        trends = [
            {
                'title': f'🔍 Search TikTok for "{keyword}" videos',
                'hashtag': keyword,
                'description': f'Find all TikTok videos about {keyword} - Click to access real trending videos!',
                'engagement': 'Search',
                'mentions': 'All Videos',
                'growth': 0,
                'tags': [keyword, 'search', 'tiktok'],
                'url': f'https://www.tiktok.com/search?q={keyword_encoded}',
                'is_real_link': True,
                'is_video': True,
                'platform': 'TikTok'
            },
            {
                'title': f'#{keyword} on TikTok',
                'hashtag': keyword,
                'description': f'Browse all videos with #{keyword} hashtag - Real trending content you can watch!',
                'engagement': 'View All',
                'mentions': 'Hashtag',
                'growth': 0,
                'tags': [keyword, 'hashtag', 'browse'],
                'url': f'https://www.tiktok.com/tag/{keyword_encoded}',
                'is_real_link': True,
                'is_video': True,
                'platform': 'TikTok'
            },
            {
                'title': f'{keyword} trending videos',
                'hashtag': f'{keyword}Trend',
                'description': f'Discover trending {keyword} content on TikTok - Watch the hottest videos now!',
                'engagement': 'Browse',
                'mentions': 'Trending',
                'growth': 0,
                'tags': [keyword, 'trending', 'discover'],
                'url': f'https://www.tiktok.com/search?q={keyword_encoded}&t=1608999999999',
                'is_real_link': True,
                'is_video': True,
                'platform': 'TikTok'
            },
            {
                'title': f'{keyword} - Latest TikToks',
                'hashtag': f'{keyword}Latest',
                'description': f'Newest {keyword} videos on TikTok - Watch fresh viral content!',
                'engagement': 'Latest',
                'mentions': 'New',
                'growth': 0,
                'tags': [keyword, 'latest', 'new'],
                'url': f'https://www.tiktok.com/search?q={keyword_encoded}',
                'is_real_link': True,
                'is_video': True,
                'platform': 'TikTok'
            }
        ]
    elif platform == 'youtube':
        import urllib.parse
        keyword_encoded = urllib.parse.quote(keyword)
        
        # Try to fetch actual trending videos using yt-dlp
        trends = []
        try:
            # Get trending videos related to the keyword
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': True,
                'playlistend': 10
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Search for videos
                search_url = f'ytsearch10:{keyword}'
                info = ydl.extract_info(search_url, download=False)
                
                if info and 'entries' in info:
                    for idx, video in enumerate(info['entries'][:10]):
                        if video:
                            video_id = video.get('id', '')
                            video_url = f'https://www.youtube.com/watch?v={video_id}' if video_id else '#'
                            
                            trends.append({
                                'title': video.get('title', f'{keyword} video {idx+1}'),
                                'hashtag': keyword,
                                'description': f'YouTube video by {video.get("channel", "Unknown")} - {video.get("view_count", "Unknown")} views',
                                'engagement': video.get('view_count', 0) if isinstance(video.get('view_count'), (int, float)) else 'Watch',
                                'mentions': f'{video.get("duration", 0)}s' if video.get("duration") else 'Video',
                                'growth': 0,
                                'tags': [keyword, 'youtube', 'video'],
                                'url': video_url,
                                'is_real_link': True,
                                'is_video': True,
                                'thumbnail': video.get('thumbnail', ''),
                                'channel': video.get('channel', 'Unknown')
                            })
        except Exception as e:
            print(f"[ERROR] Failed to fetch YouTube videos: {str(e)}")
        
        # If no videos found or error, provide search links
        if not trends:
            trends = [
                {
                    'title': f'🔍 Search YouTube for "{keyword}" videos',
                    'hashtag': keyword,
                    'description': f'Find all YouTube videos about {keyword} - Watch real videos now!',
                    'engagement': 'Search',
                    'mentions': 'All Videos',
                    'growth': 0,
                    'tags': [keyword, 'search', 'youtube'],
                    'url': f'https://www.youtube.com/results?search_query={keyword_encoded}',
                    'is_real_link': True
                },
                {
                    'title': f'{keyword} - Sort by Upload Date',
                    'hashtag': keyword,
                    'description': f'Latest {keyword} videos on YouTube - Watch newest content!',
                    'engagement': 'Latest',
                    'mentions': 'New Videos',
                    'growth': 0,
                    'tags': [keyword, 'latest', 'new'],
                    'url': f'https://www.youtube.com/results?search_query={keyword_encoded}&sp=CAI%253D',
                    'is_real_link': True
                },
                {
                    'title': f'{keyword} - Most Viewed',
                    'hashtag': f'{keyword}Popular',
                    'description': f'Most popular {keyword} videos - Watch what\'s trending!',
                    'engagement': 'Popular',
                    'mentions': 'Top Videos',
                    'growth': 0,
                    'tags': [keyword, 'popular', 'views'],
                    'url': f'https://www.youtube.com/results?search_query={keyword_encoded}&sp=CAMSAhAB',
                    'is_real_link': True
                },
                {
                    'title': f'{keyword} tutorials',
                    'hashtag': f'{keyword}Tutorial',
                    'description': f'Learn about {keyword} with tutorial videos - Watch and learn!',
                    'engagement': 'Tutorials',
                    'mentions': 'Learn',
                    'growth': 0,
                    'tags': [keyword, 'tutorial', 'howto'],
                    'url': f'https://www.youtube.com/results?search_query={keyword_encoded}+tutorial',
                    'is_real_link': True
            }
        ]
    elif platform == 'reddit':
        trends = [
            {
                'title': f'r/{keyword} subreddit',
                'hashtag': keyword,
                'description': f'Reddit discussions about {keyword} are active',
                'engagement': 125000,
                'mentions': 5600,
                'growth': 28,
                'tags': [keyword, 'reddit', 'discussion']
            },
            {
                'title': f'{keyword} AMA',
                'hashtag': f'{keyword}AMA',
                'description': f'Ask Me Anything threads about {keyword}',
                'engagement': 98000,
                'mentions': 4200,
                'growth': 22,
                'tags': [keyword, 'ama', 'qanda']
            }
        ]
    else:  # general - Show trending videos from multiple platforms
        import urllib.parse
        keyword_encoded = urllib.parse.quote(keyword)
        trends = []
        
        # Try to get YouTube trending videos
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': True,
                'playlistend': 5
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                search_url = f'ytsearch5:{keyword}'
                info = ydl.extract_info(search_url, download=False)
                
                if info and 'entries' in info:
                    for idx, video in enumerate(info['entries'][:5]):
                        if video:
                            video_id = video.get('id', '')
                            video_url = f'https://www.youtube.com/watch?v={video_id}' if video_id else '#'
                            
                            trends.append({
                                'title': f'🎥 {video.get("title", f"{keyword} video")}',
                                'hashtag': keyword,
                                'description': f'YouTube video • {video.get("channel", "Unknown")} • {format_search_number(video.get("view_count", 0))} views',
                                'engagement': video.get('view_count', 0) if isinstance(video.get('view_count'), (int, float)) else 'Watch',
                                'mentions': 'YouTube',
                                'growth': 0,
                                'tags': [keyword, 'youtube', 'video'],
                                'url': video_url,
                                'is_real_link': True,
                                'is_video': True,
                                'platform': 'YouTube',
                                'thumbnail': video.get('thumbnail', '')
                            })
        except Exception as e:
            print(f"[ERROR] Failed to fetch YouTube videos: {str(e)}")
        
        # Add TikTok trending links
        trends.append({
            'title': f'🎵 Trending "{keyword}" on TikTok',
            'hashtag': keyword,
            'description': f'Discover viral {keyword} videos on TikTok - Watch trending short videos!',
            'engagement': 'Trending',
            'mentions': 'TikTok',
            'growth': 0,
            'tags': [keyword, 'tiktok', 'viral'],
            'url': f'https://www.tiktok.com/search?q={keyword_encoded}',
            'is_real_link': True,
            'is_video': True,
            'platform': 'TikTok'
        })
        
        # Add Instagram Reels
        trends.append({
            'title': f'📸 "{keyword}" Instagram Reels',
            'hashtag': keyword,
            'description': f'Watch trending {keyword} reels on Instagram - Short videos and stories!',
            'engagement': 'Trending',
            'mentions': 'Instagram',
            'growth': 0,
            'tags': [keyword, 'instagram', 'reels'],
            'url': f'https://www.instagram.com/explore/search/keyword/?q={keyword_encoded}',
            'is_real_link': True,
            'is_video': True,
            'platform': 'Instagram'
        })
        
        # Add Twitter videos
        trends.append({
            'title': f'🐦 "{keyword}" Videos on Twitter',
            'hashtag': keyword,
            'description': f'Trending {keyword} videos on Twitter - Watch what people are talking about!',
            'engagement': 'Search',
            'mentions': 'Twitter',
            'growth': 0,
            'tags': [keyword, 'twitter', 'video'],
            'url': f'https://twitter.com/search?q={keyword_encoded}%20filter%3Avideos&src=typed_query',
            'is_real_link': True,
            'is_video': True,
            'platform': 'Twitter'
        })
        
        # If no YouTube videos found, add search links
        if len(trends) < 8:
            trends.append({
                'title': f'🔍 More "{keyword}" Videos on YouTube',
                'hashtag': keyword,
                'description': f'Browse all {keyword} videos on YouTube - Millions of videos to watch!',
                'engagement': 'Browse',
                'mentions': 'YouTube',
                'growth': 0,
                'tags': [keyword, 'youtube', 'search'],
                'url': f'https://www.youtube.com/results?search_query={keyword_encoded}',
                'is_real_link': True,
                'is_video': True,
                'platform': 'YouTube'
            })
    
    # Sort by engagement (descending) - Put real links first, then by numeric engagement
    def sort_key(trend):
        engagement = trend.get('engagement', 0)
        # Real links (with string engagement) get priority (sort value 1000000000)
        if isinstance(engagement, str):
            return 1000000000  # Very high number to put them first
        return engagement if isinstance(engagement, (int, float)) else 0
    
    trends.sort(key=sort_key, reverse=True)
    
    return trends[:10]  # Return top 10 trends


def calculate_trend_stats(trends):
    """Calculate statistics from trending data"""
    if not trends:
        return {
            'total_trends': 0,
            'avg_engagement': 0,
            'growth_rate': 0,
            'peak_time': 'N/A'
        }
    
    # Filter out trends with string engagement values (real video links)
    numeric_trends = [t for t in trends if isinstance(t.get('engagement', 0), (int, float))]
    
    if numeric_trends:
        total_engagement = sum(t.get('engagement', 0) for t in numeric_trends)
        avg_engagement = total_engagement // len(numeric_trends)
    else:
        avg_engagement = 0
    
    # Filter out trends with string growth values
    numeric_growth_trends = [t for t in trends if isinstance(t.get('growth', 0), (int, float))]
    
    if numeric_growth_trends:
        total_growth = sum(t.get('growth', 0) for t in numeric_growth_trends)
        avg_growth = total_growth // len(numeric_growth_trends)
    else:
        avg_growth = 0
    
    # Simulate peak time (in production, this would be calculated from real data)
    import random
    hours = ['9 AM', '12 PM', '3 PM', '6 PM', '9 PM']
    peak_time = random.choice(hours)
    
    return {
        'total_trends': len(trends),
        'avg_engagement': format_trend_number(avg_engagement) if avg_engagement > 0 else 'Search Available',
        'growth_rate': avg_growth,
        'peak_time': peak_time
    }


def format_trend_number(num):
    """Format large numbers for display"""
    if num >= 1000000:
        return f"{num / 1000000:.1f}M"
    elif num >= 1000:
        return f"{num / 1000:.1f}K"
    return str(num)



@app.route('/analyze-hook', methods=['POST'])
def analyze_hook():
    """Analyze the strength of a content hook"""
    try:
        data = request.json
        hook = data.get('hook', '').strip()
        platform = data.get('platform', 'general')
        
        if not hook:
            return jsonify({'error': 'Hook text is required'}), 400
        
        # Analyze the hook
        analysis = analyze_hook_strength(hook, platform)
        
        return jsonify({
            'success': True,
            'overall_score': analysis['overall_score'],
            'overall_label': analysis['overall_label'],
            'overall_description': analysis['overall_description'],
            'details': analysis['details'],
            'suggestions': analysis['suggestions'],
            'examples': analysis['examples'],
            'platform': platform
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def analyze_hook_strength(hook, platform):
    """Analyze hook strength based on multiple factors"""
    hook_lower = hook.lower()
    hook_words = hook.split()
    hook_length = len(hook)
    word_count = len(hook_words)
    
    # Platform-specific optimal lengths
    optimal_lengths = {
        'tiktok': (10, 50),  # 10-50 characters for first 3 seconds
        'instagram': (10, 60),
        'youtube': (15, 80),
        'twitter': (10, 50),
        'general': (10, 60)
    }
    
    min_len, max_len = optimal_lengths.get(platform, (10, 60))
    
    # Scoring factors
    scores = {}
    suggestions = []
    
    # 1. Length Analysis
    if min_len <= hook_length <= max_len:
        length_score = 100
    elif hook_length < min_len:
        length_score = max(0, (hook_length / min_len) * 70)
        suggestions.append(f"Your hook is too short ({hook_length} chars). Aim for {min_len}-{max_len} characters for {platform}.")
    else:
        length_score = max(0, 100 - ((hook_length - max_len) / max_len) * 50)
        suggestions.append(f"Your hook might be too long ({hook_length} chars). Consider {min_len}-{max_len} characters for {platform}.")
    
    scores['length'] = {
        'name': 'Length',
        'score': int(length_score),
        'description': f'{hook_length} characters (optimal: {min_len}-{max_len})',
        'icon': 'fas fa-ruler'
    }
    
    # 2. Question Words (creates curiosity)
    question_words = ['what', 'why', 'how', 'when', 'where', 'who', 'which', 'would', 'could', 'should']
    has_question = any(hook_lower.startswith(word) or f' {word} ' in hook_lower for word in question_words)
    question_score = 100 if has_question else 50
    if not has_question:
        suggestions.append("Start with a question word (What, Why, How, When) to create curiosity.")
    
    scores['curiosity'] = {
        'name': 'Curiosity',
        'score': int(question_score),
        'description': 'Uses question words or creates intrigue' if has_question else 'Could benefit from question words',
        'icon': 'fas fa-question-circle'
    }
    
    # 3. Emotional Words
    emotional_words = ['amazing', 'shocking', 'secret', 'hidden', 'crazy', 'insane', 'unbelievable', 
                      'incredible', 'mind-blowing', 'game-changing', 'life-changing', 'epic', 'wild',
                      'wait', 'stop', 'watch', 'listen', 'see', 'discover', 'reveal', 'exposed']
    emotional_count = sum(1 for word in emotional_words if word in hook_lower)
    emotional_score = min(100, 40 + (emotional_count * 20))
    if emotional_count == 0:
        suggestions.append("Add emotional or attention-grabbing words (amazing, shocking, secret, wait, watch).")
    
    scores['emotion'] = {
        'name': 'Emotional Impact',
        'score': int(emotional_score),
        'description': f'{emotional_count} emotional/attention words found' if emotional_count > 0 else 'Could use more emotional words',
        'icon': 'fas fa-heart'
    }
    
    # 4. Action Words / Verbs
    action_words = ['try', 'test', 'discover', 'learn', 'find', 'get', 'make', 'create', 'build', 
                   'watch', 'see', 'hear', 'feel', 'experience', 'achieve', 'master', 'unlock']
    action_count = sum(1 for word in action_words if word in hook_lower)
    action_score = min(100, 50 + (action_count * 15))
    if action_count == 0:
        suggestions.append("Include action words (try, discover, learn, watch) to create engagement.")
    
    scores['action'] = {
        'name': 'Action Words',
        'score': int(action_score),
        'description': f'{action_count} action words found' if action_count > 0 else 'Could use more action words',
        'icon': 'fas fa-bolt'
    }
    
    # 5. Numbers/Statistics (creates specificity)
    import re
    has_numbers = bool(re.search(r'\d+', hook))
    number_score = 100 if has_numbers else 60
    if not has_numbers:
        suggestions.append("Add numbers or statistics (30 days, 5 ways, 90% of people) for specificity.")
    
    scores['specificity'] = {
        'name': 'Specificity',
        'score': int(number_score),
        'description': 'Contains numbers/statistics' if has_numbers else 'Could benefit from numbers',
        'icon': 'fas fa-hashtag'
    }
    
    # 6. Personal Pronouns (creates connection)
    personal_pronouns = ['i', 'you', 'we', 'me', 'my', 'your', 'our', 'us']
    pronoun_count = sum(1 for word in personal_pronouns if word in hook_lower)
    pronoun_score = min(100, 50 + (pronoun_count * 20))
    if pronoun_count == 0:
        suggestions.append("Use personal pronouns (I, you, we) to create connection with viewers.")
    
    scores['connection'] = {
        'name': 'Personal Connection',
        'score': int(pronoun_score),
        'description': f'{pronoun_count} personal pronouns found' if pronoun_count > 0 else 'Could use personal pronouns',
        'icon': 'fas fa-user'
    }
    
    # 7. Urgency/Time Sensitivity
    urgency_words = ['now', 'today', 'right now', 'immediately', 'before', 'after', 'until', 
                    'limited', 'only', 'last chance', 'don\'t miss', 'hurry']
    urgency_count = sum(1 for word in urgency_words if word in hook_lower)
    urgency_score = min(100, 60 + (urgency_count * 15))
    if urgency_count == 0:
        suggestions.append("Add urgency words (now, today, before it's too late) to create immediacy.")
    
    scores['urgency'] = {
        'name': 'Urgency',
        'score': int(urgency_score),
        'description': f'{urgency_count} urgency words found' if urgency_count > 0 else 'Could create more urgency',
        'icon': 'fas fa-clock'
    }
    
    # 8. Hook Patterns (POV, Wait until, etc.)
    hook_patterns = [
        r'\bpov\b', r'wait until', r'watch what happens', r'i tried', r'i tested', 
        r'nobody tells you', r'this is why', r'here\'s what', r'let me show you',
        r'pov:', r'wait until you see', r'you won\'t believe', r'this changed my'
    ]
    pattern_matches = sum(1 for pattern in hook_patterns if re.search(pattern, hook_lower))
    pattern_score = min(100, 40 + (pattern_matches * 30))
    if pattern_matches == 0:
        suggestions.append("Use proven hook patterns (POV:, Wait until, I tried, This is why).")
    
    scores['pattern'] = {
        'name': 'Hook Pattern',
        'score': int(pattern_score),
        'description': 'Uses proven hook patterns' if pattern_matches > 0 else 'Could use proven hook patterns',
        'icon': 'fas fa-magic'
    }
    
    # Calculate overall score (weighted average)
    weights = {
        'length': 0.15,
        'curiosity': 0.20,
        'emotion': 0.15,
        'action': 0.10,
        'specificity': 0.10,
        'connection': 0.10,
        'urgency': 0.10,
        'pattern': 0.10
    }
    
    overall_score = sum(scores[key]['score'] * weights[key] for key in scores.keys())
    overall_score = int(round(overall_score))
    
    # Overall label and description
    if overall_score >= 80:
        label = 'Excellent Hook!'
        description = 'Your hook is highly engaging and likely to capture attention immediately.'
    elif overall_score >= 60:
        label = 'Good Hook'
        description = 'Your hook is solid but could be improved with a few tweaks.'
    elif overall_score >= 40:
        label = 'Fair Hook'
        description = 'Your hook needs improvement to better capture attention.'
    else:
        label = 'Weak Hook'
        description = 'Your hook needs significant improvement to be effective.'
    
    # Platform-specific examples
    examples = get_platform_examples(platform)
    
    # NEW: Generate alternative hooks (rewritten versions)
    alternatives = generate_alternative_hooks(hook, platform)
    
    # NEW: Viral templates
    viral_templates = get_viral_templates(platform)
    
    # NEW: A/B testing suggestions
    ab_tests = generate_ab_test_ideas(hook)
    
    return {
        'overall_score': overall_score,
        'overall_label': label,
        'overall_description': description,
        'details': list(scores.values()),
        'suggestions': suggestions[:5],  # Top 5 suggestions
        'examples': examples,
        'alternatives': alternatives,  # NEW!
        'viral_templates': viral_templates,  # NEW!
        'ab_tests': ab_tests,  # NEW!
        'platform': platform
    }


def get_platform_examples(platform):
    """Get strong hook examples for the platform"""
    examples_by_platform = {
        'tiktok': [
            {'title': 'POV Pattern', 'text': 'POV: You just discovered the secret to...'},
            {'title': 'Wait Pattern', 'text': 'Wait until you see what happens when...'},
            {'title': 'Trial Pattern', 'text': 'I tried this for 30 days and...'},
            {'title': 'Question Pattern', 'text': 'What if I told you there\'s a way to...'},
            {'title': 'Reveal Pattern', 'text': 'Nobody tells you this but...'}
        ],
        'instagram': [
            {'title': 'Question Hook', 'text': 'What\'s the one thing stopping you from...'},
            {'title': 'Secret Hook', 'text': 'The secret to [result] that nobody talks about...'},
            {'title': 'Transformation', 'text': 'I went from [before] to [after] in 30 days...'},
            {'title': 'Mistake Hook', 'text': 'The biggest mistake I made was...'},
            {'title': 'Quick Tip', 'text': 'Here\'s the #1 tip that changed everything...'}
        ],
        'youtube': [
            {'title': 'Problem Hook', 'text': 'If you\'re struggling with [problem], this will help...'},
            {'title': 'Tutorial Hook', 'text': 'I\'m going to show you exactly how to...'},
            {'title': 'Story Hook', 'text': 'This is what happened when I tried...'},
            {'title': 'Comparison', 'text': 'I tested [A] vs [B] and here\'s what I found...'},
            {'title': 'Myth Busting', 'text': 'Everyone says [X] but they\'re wrong. Here\'s why...'}
        ],
        'twitter': [
            {'title': 'Hot Take', 'text': 'Unpopular opinion: [statement]...'},
            {'title': 'Thread Starter', 'text': 'Here\'s why [topic] is more important than you think...'},
            {'title': 'Question Thread', 'text': 'What if I told you [surprising fact]...'},
            {'title': 'Quick Tip', 'text': 'The one thing I wish I knew earlier: [tip]...'},
            {'title': 'Story Hook', 'text': 'This happened to me yesterday and I can\'t stop thinking about it...'}
        ],
        'general': [
            {'title': 'Curiosity Gap', 'text': 'The one thing that changed everything...'},
            {'title': 'Question Hook', 'text': 'What if you could [desired outcome]...'},
            {'title': 'Story Hook', 'text': 'I never expected this to happen but...'},
            {'title': 'Secret Hook', 'text': 'The secret nobody wants you to know...'},
            {'title': 'Transformation', 'text': 'How I went from [before] to [after]...'}
        ]
    }
    
    return examples_by_platform.get(platform, examples_by_platform['general'])


def generate_alternative_hooks(original_hook, platform):
    """Generate improved alternative versions of the user's hook"""
    alternatives = []
    
    # Extract key words from original
    words = original_hook.split()
    
    # Alternative 1: Add Question Format
    if not original_hook.strip().endswith('?'):
        alternatives.append({
            'title': 'Question Format',
            'hook': f"What if {original_hook.lower()}?",
            'why': 'Questions create curiosity and engagement'
        })
    
    # Alternative 2: Add POV Pattern
    if 'pov' not in original_hook.lower():
        alternatives.append({
            'title': 'POV Pattern',
            'hook': f"POV: {original_hook}",
            'why': 'POV format is proven to increase engagement on TikTok/Instagram'
        })
    
    # Alternative 3: Add "Wait Until"
    alternatives.append({
        'title': 'Suspense Hook',
        'hook': f"Wait until you see {original_hook.lower()}",
        'why': 'Creates anticipation and keeps viewers watching'
    })
    
    # Alternative 4: Add Numbers
    if not any(char.isdigit() for char in original_hook):
        alternatives.append({
            'title': 'With Statistics',
            'hook': f"3 reasons why {original_hook.lower()}",
            'why': 'Numbers make content feel more specific and actionable'
        })
    
    # Alternative 5: Add Urgency
    alternatives.append({
        'title': 'Urgent Version',
        'hook': f"{original_hook} - You need to see this NOW",
        'why': 'Urgency creates FOMO and immediate action'
    })
    
    return alternatives[:4]  # Return top 4


def get_viral_templates(platform):
    """Get viral hook templates users can copy and customize"""
    templates = {
        'tiktok': [
            {
                'template': 'POV: You just found out [surprising fact]',
                'example': 'POV: You just found out coffee is actually good for you',
                'viral_score': '95%'
            },
            {
                'template': 'Wait until you see what happens when [action]',
                'example': 'Wait until you see what happens when I mix these two ingredients',
                'viral_score': '92%'
            },
            {
                'template': 'I tried [activity] for 30 days and [result]',
                'example': 'I tried waking up at 5am for 30 days and this happened',
                'viral_score': '90%'
            },
            {
                'template': 'Nobody tells you [secret] but here it is',
                'example': 'Nobody tells you this workout trick but it works',
                'viral_score': '88%'
            }
        ],
        'instagram': [
            {
                'template': 'The secret to [goal] that changed my life',
                'example': 'The secret to better skin that changed my life',
                'viral_score': '90%'
            },
            {
                'template': 'I went from [before] to [after] in [time]',
                'example': 'I went from 0 to 100K followers in 6 months',
                'viral_score': '88%'
            },
            {
                'template': 'Stop doing [common mistake] and do this instead',
                'example': 'Stop doing cardio and do this instead',
                'viral_score': '85%'
            }
        ],
        'youtube': [
            {
                'template': 'I tested [A] vs [B] for [time] - Here\'s what happened',
                'example': 'I tested ChatGPT vs Gemini for 30 days - Here\'s what happened',
                'viral_score': '93%'
            },
            {
                'template': 'How I [achieved goal] (Step-by-Step)',
                'example': 'How I gained 1M subscribers (Step-by-Step)',
                'viral_score': '90%'
            },
            {
                'template': 'Everyone does [X] wrong - Here\'s the right way',
                'example': 'Everyone edits videos wrong - Here\'s the right way',
                'viral_score': '87%'
            }
        ],
        'general': [
            {
                'template': 'The one [thing] that changed everything',
                'example': 'The one habit that changed everything',
                'viral_score': '85%'
            },
            {
                'template': 'What if I told you [surprising fact]?',
                'example': 'What if I told you you\'re washing your face wrong?',
                'viral_score': '83%'
            },
            {
                'template': '[Number] [things] nobody talks about',
                'example': '5 productivity hacks nobody talks about',
                'viral_score': '80%'
            }
        ]
    }
    
    return templates.get(platform, templates['general'])


def generate_ab_test_ideas(original_hook):
    """Generate A/B testing suggestions for the hook"""
    ab_tests = [
        {
            'test_name': 'Question vs Statement',
            'version_a': original_hook,
            'version_b': f"What if {original_hook.lower()}?" if not original_hook.endswith('?') else original_hook.replace('?', '.'),
            'what_to_measure': 'Which format gets more engagement in first 3 seconds'
        },
        {
            'test_name': 'With vs Without Emoji',
            'version_a': original_hook,
            'version_b': f"🔥 {original_hook}",
            'what_to_measure': 'Does emoji increase click-through rate'
        },
        {
            'test_name': 'Short vs Detailed',
            'version_a': original_hook,
            'version_b': f"{original_hook} - Here's why this matters",
            'what_to_measure': 'Which length performs better for watch time'
        },
        {
            'test_name': 'Personal vs General',
            'version_a': original_hook,
            'version_b': original_hook.replace('you', 'I').replace('your', 'my') if 'you' in original_hook.lower() else original_hook.replace('I', 'you').replace('my', 'your'),
            'what_to_measure': 'Which perspective resonates more with audience'
        }
    ]
    
    return ab_tests[:3]  # Return top 3





@app.route('/process-video-subtitles', methods=['POST'])
def process_video_subtitles():
    """Process uploaded video for subtitle extraction or embedding"""
    try:
        if 'video' not in request.files:
            return jsonify({'error': 'No video file provided'}), 400
        
        video_file = request.files['video']
        if video_file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Get form data
        languages = json.loads(request.form.get('languages', '["en"]'))
        action_type = request.form.get('action_type', 'extract')
        subtitle_format = request.form.get('subtitle_format', 'srt')
        translate = request.form.get('translate', 'false') == 'true'
        
        # Create unique job ID
        job_id = str(uuid.uuid4())
        
        # Save uploaded file
        upload_path = Path(app.config['UPLOAD_FOLDER']) / job_id
        upload_path.mkdir(exist_ok=True)
        
        filename = secure_filename(video_file.filename)
        video_path = upload_path / filename
        video_file.save(str(video_path))
        
        # Initialize job status
        jobs[job_id] = {
            'status': 'processing',
            'progress': 0,
            'message': 'Processing video...',
            'type': 'video_subtitle_processing',
            'can_cancel': True,
            'created_at': time.time(),
            'updated_at': time.time()
        }
        
        # Start processing in background thread
        thread = Thread(
            target=process_uploaded_video,
            args=(job_id, str(video_path), languages, action_type, subtitle_format, translate)
        )
        thread.start()
        
        return jsonify({'job_id': job_id, 'message': 'Processing started'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/download-subtitles', methods=['POST'])
def download_subtitles():
    """Download video with subtitles"""
    try:
        data = request.json
        url = data.get('url')
        source_language = data.get('source_language', 'auto')
        target_language = data.get('target_language', 'en')
        download_type = data.get('download_type', 'video_with_subs')
        subtitle_format = data.get('subtitle_format', 'srt')
        auto_generated = data.get('auto_generated', True)
        video_quality = data.get('video_quality', '720p')
        
        if not url:
            return jsonify({'error': 'No URL provided'}), 400
        
        # Create unique job ID
        job_id = str(uuid.uuid4())
        
        # Initialize job status
        jobs[job_id] = {
            'status': 'processing',
            'progress': 0,
            'message': 'Starting download...',
            'type': 'subtitle_download',
            'can_cancel': True
        }
        
        # Start download in background thread
        thread = Thread(
            target=download_with_subtitles,
            args=(job_id, url, source_language, target_language, download_type, 
                  subtitle_format, auto_generated, video_quality)
        )
        thread.start()
        
        return jsonify({'job_id': job_id, 'message': 'Download started'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/history')
def get_history():
    """Get download history"""
    limit = request.args.get('limit', 100, type=int)
    status = request.args.get('status', None)
    
    downloads = download_history.get_all_downloads(limit=limit, status=status)
    stats = download_history.get_statistics()
    
    return jsonify({
        'downloads': downloads,
        'statistics': stats
    })


@app.route('/api/history/search')
def search_history():
    """Search download history"""
    query = request.args.get('q', '')
    
    if not query:
        return jsonify({'downloads': []})
    
    downloads = download_history.search_downloads(query)
    return jsonify({'downloads': downloads})


@app.route('/api/history/<int:download_id>', methods=['DELETE'])
def delete_history_item(download_id):
    """Delete a download from history"""
    try:
        download_history.delete_download(download_id)
        return jsonify({'success': True, 'message': 'Download deleted from history'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/history/clear', methods=['POST'])
def clear_history():
    """Clear download history"""
    try:
        older_than_days = request.json.get('older_than_days', None)
        download_history.clear_history(older_than_days=older_than_days)
        return jsonify({'success': True, 'message': 'History cleared'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/history/redownload/<int:download_id>', methods=['POST'])
def redownload(download_id):
    """Re-download a video from history"""
    try:
        download = download_history.get_download(download_id)
        
        if not download:
            return jsonify({'error': 'Download not found'}), 404
        
        # Create new download job
        job_id = str(uuid.uuid4())
        
        jobs[job_id] = {
            'status': 'processing',
            'progress': 0,
            'url': download['url'],
            'type': 'download',
            'format': download['format_type']
        }
        
        # Start download in background
        thread = Thread(target=download_video, args=(
            job_id, 
            download['url'], 
            download['format_type'], 
            download['quality']
        ))
        thread.start()
        
        return jsonify({
            'job_id': job_id, 
            'message': 'Re-download started',
            'format_type': download['format_type']
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload for conversion (supports multiple files)"""
    print("[UPLOAD] Received upload request")
    
    if 'files[]' not in request.files:
        print("[UPLOAD] ERROR: No files[] in request")
        return jsonify({'error': 'No files provided'}), 400
    
    files = request.files.getlist('files[]')
    print(f"[UPLOAD] Files received: {len(files)}")
    
    if not files or files[0].filename == '':
        print("[UPLOAD] ERROR: No files selected or empty filename")
        return jsonify({'error': 'No files selected'}), 400
    
    # Get conversion settings
    conversion_type = request.form.get('conversion_type', 'mp4_to_mp3')
    bitrate = request.form.get('bitrate', '192k')
    
    print(f"[UPLOAD] Conversion type: {conversion_type}")
    print(f"[UPLOAD] Bitrate: {bitrate}")
    
    job_id = str(uuid.uuid4())
    print(f"[UPLOAD] Job ID: {job_id}")
    
    # Save all uploaded files
    upload_path = Path(app.config['UPLOAD_FOLDER']) / job_id
    upload_path.mkdir(exist_ok=True)
    print(f"[UPLOAD] Upload path: {upload_path}")
    
    file_paths = []
    filenames = []
    for file in files:
        if file.filename:
            filename = secure_filename(file.filename)
            filenames.append(filename)
            file_path = upload_path / filename
            file.save(str(file_path))
            file_paths.append(str(file_path))
            print(f"[UPLOAD] Saved: {filename} ({file_path.stat().st_size} bytes)")
    
    if not file_paths:
        print("[UPLOAD] ERROR: No valid files uploaded")
        return jsonify({'error': 'No valid files uploaded'}), 400
    
    print(f"[UPLOAD] Total files to convert: {len(file_paths)}")
    
    # Create job
    jobs[job_id] = {
        'status': 'processing',
        'progress': 0,
        'filenames': filenames,
        'total_files': len(file_paths),
        'completed_files': 0,
        'type': 'convert',
        'conversion_type': conversion_type
    }
    
    # Start conversion in background
    print(f"[UPLOAD] Starting conversion thread...")
    thread = Thread(target=convert_files, args=(job_id, file_paths, conversion_type, bitrate))
    thread.start()
    
    print(f"[UPLOAD] Success! Job {job_id} started")
    return jsonify({'job_id': job_id, 'filenames': filenames, 'total_files': len(file_paths)})


@app.route('/check-playlist', methods=['POST'])
def check_playlist():
    """Check if URL is a playlist and return video list"""
    data = request.json
    url = data.get('url')
    
    if not url:
        return jsonify({'error': 'No URL provided'}), 400
    
    try:
        import yt_dlp
        import re
        
        # Check if URL contains a playlist parameter
        has_playlist_param = 'list=' in url or '/playlist?' in url
        
        # If URL has both video and playlist, we need to extract playlist
        if has_playlist_param:
            # Extract playlist ID from URL
            playlist_match = re.search(r'[?&]list=([^&]+)', url)
            if playlist_match:
                playlist_id = playlist_match.group(1)
                # Convert to playlist URL
                playlist_url = f"https://www.youtube.com/playlist?list={playlist_id}"
                url = playlist_url
        
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,  # Don't download, just get info
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # Check if it's a playlist
            if 'entries' in info:
                videos = []
                for entry in info['entries']:
                    if entry:  # Some entries might be None
                        videos.append({
                            'id': entry.get('id', ''),
                            'title': entry.get('title', 'Unknown Title'),
                            'duration': entry.get('duration', 0),
                            'url': f"https://www.youtube.com/watch?v={entry.get('id', '')}"
                        })
                
                return jsonify({
                    'is_playlist': True,
                    'playlist_title': info.get('title', 'Unknown Playlist'),
                    'video_count': len(videos),
                    'videos': videos
                })
            else:
                # Single video
                return jsonify({
                    'is_playlist': False,
                    'title': info.get('title', 'Unknown Title')
                })
    
    except Exception as e:
        return jsonify({'error': f'Failed to check URL: {str(e)}'}), 500


@app.route('/download-youtube', methods=['POST'])
def download_youtube():
    """Handle YouTube download (single or multiple videos)"""
    data = request.json
    url = data.get('url')
    urls = data.get('urls', [])  # For multiple selected videos
    format_type = data.get('format', 'mp3')
    quality = data.get('quality', 'best')
    
    if not url and not urls:
        return jsonify({'error': 'No URL provided'}), 400
    
    job_id = str(uuid.uuid4())
    
    # Determine if single or multiple downloads
    if urls and len(urls) > 1:
        # Multiple videos
        jobs[job_id] = {
            'status': 'processing',
            'progress': 0,
            'urls': urls,
            'type': 'download_multiple',
            'format': format_type,
            'total_videos': len(urls),
            'completed_videos': 0
        }
        
        # Start multiple downloads in background
        thread = Thread(target=download_multiple_videos, args=(job_id, urls, format_type, quality))
        thread.start()
    else:
        # Single video
        single_url = url if url else urls[0]
        jobs[job_id] = {
            'status': 'processing',
            'progress': 0,
            'url': single_url,
            'type': 'download',
            'format': format_type
        }
        
        # Start download in background
        thread = Thread(target=download_video, args=(job_id, single_url, format_type, quality))
        thread.start()
    
    return jsonify({'job_id': job_id})


@app.route('/download-instagram', methods=['POST'])
def download_instagram():
    """Handle Instagram download"""
    data = request.json
    url = data.get('url')
    format_type = data.get('format', 'video')
    
    if not url:
        return jsonify({'error': 'No URL provided'}), 400
    
    job_id = str(uuid.uuid4())
    jobs[job_id] = {
        'status': 'processing',
        'progress': 0,
        'url': url,
        'type': 'download',
        'format': format_type,
        'platform': 'instagram'
    }
    
    thread = Thread(target=download_social_media, args=(job_id, url, 'instagram', format_type))
    thread.start()
    
    return jsonify({'job_id': job_id})


@app.route('/download-facebook', methods=['POST'])
def download_facebook():
    """Handle Facebook download"""
    data = request.json
    url = data.get('url')
    format_type = data.get('format', 'video')
    
    if not url:
        return jsonify({'error': 'No URL provided'}), 400
    
    job_id = str(uuid.uuid4())
    jobs[job_id] = {
        'status': 'processing',
        'progress': 0,
        'url': url,
        'type': 'download',
        'format': format_type,
        'platform': 'facebook'
    }
    
    thread = Thread(target=download_social_media, args=(job_id, url, 'facebook', format_type))
    thread.start()
    
    return jsonify({'job_id': job_id})


@app.route('/download-tiktok', methods=['POST'])
def download_tiktok():
    """Handle TikTok download"""
    data = request.json
    url = data.get('url')
    format_type = data.get('format', 'video')
    
    if not url:
        return jsonify({'error': 'No URL provided'}), 400
    
    job_id = str(uuid.uuid4())
    jobs[job_id] = {
        'status': 'processing',
        'progress': 0,
        'url': url,
        'type': 'download',
        'format': format_type,
        'platform': 'tiktok'
    }
    
    thread = Thread(target=download_social_media, args=(job_id, url, 'tiktok', format_type))
    thread.start()
    
    return jsonify({'job_id': job_id})


@app.route('/status/<job_id>')
def get_status(job_id):
    """Get job status"""
    if job_id not in jobs:
        return jsonify({'error': 'Job not found'}), 404
    
    return jsonify(jobs[job_id])


@app.route('/cancel/<job_id>', methods=['POST'])
def cancel_job(job_id):
    """Cancel a running job"""
    if job_id not in jobs:
        return jsonify({'error': 'Job not found'}), 404
    
    if jobs[job_id].get('status') != 'processing':
        return jsonify({'error': 'Job is not running'}), 400
    
    # Mark job as cancelled
    jobs[job_id]['cancelled'] = True
    jobs[job_id]['status'] = 'cancelling'
    jobs[job_id]['message'] = 'Cancelling download...'
    
    # Clean up partial files in background
    def cleanup_files():
        try:
            output_dir = Path(app.config['OUTPUT_FOLDER']) / job_id
            if output_dir.exists():
                shutil.rmtree(output_dir)
                print(f"[INFO] Cleaned up job directory: {job_id}")
        except Exception as e:
            print(f"[ERROR] Failed to clean up {job_id}: {str(e)}")
    
    Thread(target=cleanup_files).start()
    
    return jsonify({'success': True, 'message': 'Download cancelled'})


@app.route('/download/<job_id>')
def download_result(job_id):
    """Download the converted/downloaded file"""
    try:
        print(f"\n[DOWNLOAD] Request received")
    except:
        pass
    
    if job_id not in jobs:
        try:
            print(f"[DOWNLOAD] ERROR: Job not found")
        except:
            pass
        return jsonify({'error': 'Job not found'}), 404
    
    job = jobs[job_id]
    
    if job['status'] != 'completed':
        try:
            print(f"[DOWNLOAD] ERROR: Job not completed")
        except:
            pass
        return jsonify({'error': 'Job not completed'}), 400
    
    file_path = job.get('output_path')
    
    if not file_path:
        try:
            print(f"[DOWNLOAD] ERROR: No output_path")
        except:
            pass
        return jsonify({'error': 'No output path'}), 404
    
    # Convert to absolute path if needed
    if not os.path.isabs(file_path):
        file_path = os.path.abspath(file_path)
    
    if not os.path.exists(file_path):
        try:
            print(f"[DOWNLOAD] ERROR: File not found")
            parent_dir = os.path.dirname(file_path)
            if os.path.exists(parent_dir):
                print(f"[DOWNLOAD] Dir exists, checking contents...")
        except:
            pass
        return jsonify({'error': 'File not found'}), 404
    
    try:
        file_size = os.path.getsize(file_path)
        print(f"[DOWNLOAD] Sending file: {file_size} bytes")
    except:
        pass
    
    # Determine MIME type based on file extension
    file_ext = Path(file_path).suffix.lower()
    mime_types = {
        '.gif': 'image/gif',
        '.mp4': 'video/mp4',
        '.mp3': 'audio/mpeg',
        '.mkv': 'video/x-matroska',
        '.srt': 'text/plain',
        '.zip': 'application/zip',
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.encrypted': 'application/octet-stream'
    }
    
    mimetype = mime_types.get(file_ext, 'application/octet-stream')
    
    # Use output_filename if available, otherwise use file name
    download_filename = job.get('output_filename') or Path(file_path).name
    
    # For GIF files, ensure proper filename and MIME type for WhatsApp
    if file_ext == '.gif' or job.get('type') == 'gif_creation':
        # Force .gif extension in download filename
        if not download_filename.lower().endswith('.gif'):
            download_filename = Path(download_filename).stem + '.gif'
        
        return send_file(
            file_path, 
            as_attachment=True, 
            mimetype='image/gif',
            download_name=download_filename
        )
    
    return send_file(file_path, as_attachment=True, mimetype=mimetype, download_name=download_filename)


@app.route('/jobs')
def list_jobs():
    """List all jobs"""
    return jsonify(jobs)


def convert_files(job_id, input_paths, conversion_type, bitrate):
    """Convert multiple files (supports both MP4→MP3 and MP3→MP4)"""
    try:
        output_dir = Path(app.config['OUTPUT_FOLDER']) / job_id
        output_dir.mkdir(exist_ok=True)
        
        total_files = len(input_paths)
        completed = 0
        errors = []
        
        # Check if FFmpeg is available
        try:
            subprocess.run(['ffmpeg', '-version'], 
                         stdout=subprocess.DEVNULL, 
                         stderr=subprocess.DEVNULL, 
                         check=True,
                         creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
            print("[INFO] FFmpeg is available and working")
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            error_msg = "FFmpeg is not installed or not accessible. Please install FFmpeg to use media conversion."
            print(f"[ERROR] {error_msg}")
            print(f"[ERROR] Exception: {str(e)}")
            jobs[job_id].update({
                'status': 'failed',
                'progress': 0,
                'message': error_msg
            })
            return
        
        # Convert each file
        for i, input_path in enumerate(input_paths):
            jobs[job_id]['progress'] = int((i / total_files) * 90)
            jobs[job_id]['message'] = f'Converting file {i+1} of {total_files}...'
            
            print(f"[DEBUG] Converting: {input_path}")
            print(f"[DEBUG] Conversion type: {conversion_type}")
            print(f"[DEBUG] Output dir: {output_dir}")
            print(f"[DEBUG] Bitrate: {bitrate}")
            
            # Perform conversion based on type
            if conversion_type == 'mp4_to_mp3':
                result = media_tool.convert_mp4_to_mp3(input_path, str(output_dir), bitrate)
            else:  # mp3_to_mp4
                result = media_tool.convert_mp3_to_mp4(input_path, str(output_dir))
            
            print(f"[DEBUG] Conversion result: {result}")
            
            # Check for success (updated to match new format without emojis)
            if "[OK]" in result or "Successfully" in result:
                completed += 1
            else:
                errors.append(f"File {i+1}: {result}")
                print(f"[ERROR] Conversion failed for file {i+1}: {result}")
            
            jobs[job_id]['completed_files'] = completed
        
        jobs[job_id]['progress'] = 100
        
        # Find all output files
        if conversion_type == 'mp4_to_mp3':
            output_files = list(output_dir.glob('*.mp3'))
        else:
            output_files = list(output_dir.glob('*.mp4'))
        
        print(f"[DEBUG] Output files found: {[f.name for f in output_files]}")
        print(f"[DEBUG] Errors: {errors}")
        
        if output_files:
            if len(output_files) == 1:
                # Single file - provide direct download
                output_path = str(output_files[0])
                jobs[job_id].update({
                    'status': 'completed',
                    'progress': 100,
                    'output_path': output_path,
                    'output_filename': output_files[0].name,
                    'message': f'Conversion completed! {completed} of {total_files} files converted successfully.'
                })
                update_job_timestamp(job_id)
            else:
                # Multiple files - create ZIP
                import zipfile
                zip_path = output_dir / 'converted_files.zip'
                with zipfile.ZipFile(str(zip_path), 'w') as zipf:
                    for file in output_files:
                        zipf.write(str(file), file.name)
                
                jobs[job_id].update({
                    'status': 'completed',
                    'progress': 100,
                    'output_path': str(zip_path),
                    'output_filename': 'converted_files.zip',
                    'message': f'Batch conversion completed! {completed} of {total_files} files converted successfully.',
                    'is_zip': True
                })
        else:
            jobs[job_id].update({
                'status': 'failed',
                'progress': 0,
                'message': 'Conversion failed: No output files generated'
            })
    
    except Exception as e:
        jobs[job_id].update({
            'status': 'failed',
            'progress': 0,
            'message': f'Error: {str(e)}'
        })


def process_uploaded_video(job_id, video_path, languages, action_type, subtitle_format, translate):
    """Process uploaded video for subtitle extraction or embedding"""
    try:
        output_dir = Path(app.config['OUTPUT_FOLDER']) / job_id
        output_dir.mkdir(exist_ok=True)
        
        video_path_obj = Path(video_path)
        
        if action_type == 'extract':
            # Extract subtitles from video using FFmpeg
            jobs[job_id]['message'] = 'Extracting subtitles from video...'
            jobs[job_id]['progress'] = 30
            
            subtitle_files = []
            
            # Try to extract subtitles
            for lang in languages:
                subtitle_file = output_dir / f"{video_path_obj.stem}.{lang}.{subtitle_format}"
                
                cmd = [
                    'ffmpeg',
                    '-i', str(video_path),
                    '-map', f'0:s:0',  # First subtitle stream
                    '-c:s', subtitle_format,
                    '-y',
                    str(subtitle_file)
                ]
                
                try:
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                    if result.returncode == 0 and subtitle_file.exists():
                        subtitle_files.append(subtitle_file)
                except Exception as e:
                    print(f"[ERROR] Failed to extract {lang} subtitle: {e}")
            
            if not subtitle_files:
                raise Exception('No subtitles found in video. Video may not contain embedded subtitles.')
            
            jobs[job_id]['progress'] = 90
            
            # Create ZIP if multiple files
            if len(subtitle_files) > 1:
                zip_path = output_dir / 'subtitles.zip'
                with zipfile.ZipFile(str(zip_path), 'w') as zipf:
                    for sub_file in subtitle_files:
                        zipf.write(str(sub_file), sub_file.name)
                
                jobs[job_id].update({
                    'status': 'completed',
                    'progress': 100,
                    'message': f'Extracted {len(subtitle_files)} subtitle file(s)',
                    'output_path': str(zip_path),
                    'subtitle_count': len(subtitle_files),
                    'is_zip': True
                })
            else:
                jobs[job_id].update({
                    'status': 'completed',
                    'progress': 100,
                    'message': 'Subtitle extracted successfully',
                    'output_path': str(subtitle_files[0]),
                    'subtitle_count': 1
                })
        
        elif action_type == 'generate':
            # Generate subtitles using FFmpeg's silencedetect and basic audio extraction
            jobs[job_id]['message'] = 'Generating subtitles from audio...'
            jobs[job_id]['progress'] = 30
            
            # Note: This is a basic implementation. For better results, use Whisper or similar
            # For now, we'll create a basic subtitle file with timestamps
            
            subtitle_file = output_dir / f"{video_path_obj.stem}.{languages[0]}.{subtitle_format}"
            
            # Create a basic subtitle file (placeholder)
            # In a production environment, you'd use Whisper, Google Speech-to-Text, etc.
            with open(subtitle_file, 'w', encoding='utf-8') as f:
                if subtitle_format == 'srt':
                    f.write("1\n")
                    f.write("00:00:00,000 --> 00:00:05,000\n")
                    f.write("[Auto-generated subtitles require speech recognition]\n")
                    f.write("\n")
                    f.write("2\n")
                    f.write("00:00:05,000 --> 00:00:10,000\n")
                    f.write("[Install 'openai-whisper' package for AI subtitle generation]\n")
                    f.write("\n")
                    f.write("3\n")
                    f.write("00:00:10,000 --> 00:00:15,000\n")
                    f.write("[Visit: https://github.com/openai/whisper]\n")
            
            jobs[job_id].update({
                'status': 'completed',
                'progress': 100,
                'message': 'Basic subtitle template created. For AI-powered generation, install Whisper.',
                'output_path': str(subtitle_file),
                'subtitle_count': 1
            })
        
        else:  # action_type == 'add'
            # Add/embed subtitles to video
            jobs[job_id]['message'] = 'Embedding subtitles into video...'
            jobs[job_id]['progress'] = 30
            
            # This requires subtitle files to be uploaded
            # For now, create a note
            output_video = output_dir / f"{video_path_obj.stem}_with_subs.mkv"
            
            # Copy video to output
            import shutil
            shutil.copy2(video_path, output_video)
            
            jobs[job_id].update({
                'status': 'completed',
                'progress': 100,
                'message': 'Video ready. Upload subtitle files to embed them.',
                'output_path': str(output_video)
            })
        
    except Exception as e:
        error_msg = str(e)
        jobs[job_id].update({
            'status': 'failed',
            'progress': 0,
            'message': f'Processing failed: {error_msg}'
        })


def format_timestamp(seconds):
    """Convert seconds to SRT timestamp format (HH:MM:SS,mmm)"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def translate_text(text, source_lang, target_lang):
    """Translate text from source language to target language"""
    if not TRANSLATOR_AVAILABLE or target_lang == 'same':
        return text
    
    try:
        # Handle auto-detect
        source = 'auto' if source_lang == 'auto' else source_lang
        
        translator = GoogleTranslator(source=source, target=target_lang)
        translated = translator.translate(text)
        return translated if translated else text
    except Exception as e:
        try:
            print(f"[TRANSLATE] Error: {str(e)}")
        except:
            pass
        return text  # Return original if translation fails


def download_with_subtitles(job_id, url, source_language, target_language, download_type, 
                           subtitle_format, auto_generated, video_quality):
    """Download video with subtitles"""
    download_id = None
    try:
        # Add to history
        download_id = download_history.add_download(
            url=url,
            format_type='video+subs' if download_type != 'subs_only' else 'subs_only',
            quality=video_quality,
            job_id=job_id
        )
        
        jobs[job_id]['progress'] = 10
        jobs[job_id]['download_id'] = download_id
        
        output_dir = Path(app.config['OUTPUT_FOLDER']) / job_id
        output_dir.mkdir(exist_ok=True)
        
        # Build subtitle language string
        # Use source language for subtitle download, or English as fallback
        sub_lang = source_language if source_language and source_language != 'auto' else 'en'
        
        # Build yt-dlp options
        ydl_opts = {
            'outtmpl': str(output_dir / '%(title)s.%(ext)s'),
            'quiet': False,
            'no_warnings': False,
        }
        
        # Configure based on download type
        if download_type == 'video_with_subs':
            # Download video with best quality (video+audio merged)
            ydl_opts['format'] = f'bestvideo[height<={video_quality.replace("p", "")}][ext=mp4]+bestaudio[ext=m4a]/best[height<={video_quality.replace("p", "")}]/best'
            ydl_opts['merge_output_format'] = 'mp4'  # Download as MP4 first
            
            # Download subtitles separately (we'll embed them manually)
            ydl_opts['writesubtitles'] = True
            if auto_generated:
                ydl_opts['writeautomaticsub'] = True
            ydl_opts['subtitleslangs'] = [sub_lang]
            ydl_opts['subtitlesformat'] = 'srt'  # Force SRT format for better compatibility
            
        elif download_type == 'video_separate_subs':
            # Download video + separate subtitle files (works with Windows Media Player!)
            ydl_opts['format'] = f'bestvideo[height<={video_quality.replace("p", "")}][ext=mp4]+bestaudio[ext=m4a]/best[height<={video_quality.replace("p", "")}]/best'
            ydl_opts['merge_output_format'] = 'mp4'
            
            # Download subtitles as separate files
            ydl_opts['writesubtitles'] = True
            if auto_generated:
                ydl_opts['writeautomaticsub'] = True
            ydl_opts['subtitleslangs'] = [sub_lang]
            ydl_opts['subtitlesformat'] = subtitle_format
            ydl_opts['skip_download'] = False  # Make sure video is downloaded
            
        else:  # subs_only
            # Download only subtitles
            ydl_opts['skip_download'] = True
            ydl_opts['writesubtitles'] = True
            if auto_generated:
                ydl_opts['writeautomaticsub'] = True
            ydl_opts['subtitleslangs'] = [sub_lang]
            ydl_opts['subtitlesformat'] = subtitle_format
        
        # Progress hook
        def progress_callback(d):
            if jobs[job_id].get('cancelled'):
                raise Exception('Download cancelled')
                
            if d['status'] == 'downloading':
                try:
                    downloaded = d.get('downloaded_bytes', 0)
                    total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                    speed = d.get('speed', 0)
                    eta = d.get('eta', 0)
                    
                    if total > 0:
                        progress = int((downloaded / total) * 90)
                        jobs[job_id]['progress'] = progress
                        
                        download_info = {
                            'downloaded': f"{downloaded / (1024*1024):.1f} MB",
                            'total': f"{total / (1024*1024):.1f} MB",
                            'speed': f"{speed / (1024*1024):.2f} MB/s" if speed else "-- MB/s",
                            'eta': f"{eta // 60:02d}:{eta % 60:02d}" if eta else "--:--"
                        }
                        jobs[job_id]['download_info'] = download_info
                        jobs[job_id]['message'] = f'Downloading... {progress}%'
                        
                except Exception as e:
                    print(f"[ERROR] Progress callback error: {e}")
        
        ydl_opts['progress_hooks'] = [progress_callback]
        
        jobs[job_id]['message'] = 'Downloading video and subtitles...'
        
        # Download with yt-dlp
        try:
            print(f"[SUBTITLE] Starting download")
            print(f"[SUBTITLE] Output directory: {str(output_dir)}")
        except:
            pass
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                video_title = info.get('title', 'video')
            
            try:
                print(f"[SUBTITLE] Download completed")
            except:
                pass
        
        except Exception as download_error:
            error_str = str(download_error)
            
            # Check if it's a rate limit error (429) or subtitle download error
            if '429' in error_str or 'Too Many Requests' in error_str or 'Unable to download video subtitles' in error_str:
                try:
                    print(f"[SUBTITLE] YouTube rate limited or subtitles unavailable. Will generate with AI instead.")
                except:
                    pass
                
                # Download video only without subtitles, then use AI
                ydl_opts_no_subs = ydl_opts.copy()
                ydl_opts_no_subs['writesubtitles'] = False
                ydl_opts_no_subs['writeautomaticsub'] = False
                
                jobs[job_id]['message'] = 'YouTube rate limited. Downloading video only, will generate subtitles with AI...'
                
                with yt_dlp.YoutubeDL(ydl_opts_no_subs) as ydl:
                    info = ydl.extract_info(url, download=True)
                    video_title = info.get('title', 'video')
            else:
                # Other error, re-raise
                raise
        
        jobs[job_id]['progress'] = 95
        jobs[job_id]['message'] = 'Finalizing...'
        
        # Find output files
        output_files = list(output_dir.glob('*'))
        video_files = [f for f in output_files if f.suffix in ['.mp4', '.mkv', '.webm']]
        subtitle_files = [f for f in output_files if f.suffix in ['.srt', '.vtt', '.ass']]
        
        try:
            print(f"[SUBTITLE] Total files: {len(output_files)}, Videos: {len(video_files)}, Subtitles: {len(subtitle_files)}")
        except:
            pass
        
        if not output_files:
            raise Exception('No files were downloaded')
        
        # Determine what to return based on download type
        if download_type == 'video_with_subs':
            # Manually embed subtitles using FFmpeg
            if not video_files:
                raise Exception('Video file not found after download')
            
            video_file = video_files[0]
            
            # If no subtitles were downloaded, AUTO-GENERATE them with Whisper AI
            if not subtitle_files:
                try:
                    print(f"[SUBTITLE] No subtitle files found. Generating with Whisper AI...")
                except:
                    pass
                
                if WHISPER_AVAILABLE:
                    try:
                        jobs[job_id]['progress'] = 85
                        jobs[job_id]['message'] = 'No subtitles found. Generating with AI...'
                        
                        # Load Whisper model (medium = BEST accuracy for dialects and accents)
                        model = whisper.load_model("medium")
                        
                        jobs[job_id]['progress'] = 90
                        jobs[job_id]['message'] = 'Analyzing audio... (This may take 2-5 minutes)'
                        
                        # Transcribe audio with better settings and progress callback
                        def progress_callback(progress_dict):
                            try:
                                if 'progress' in progress_dict:
                                    current_progress = 90 + int(progress_dict['progress'] * 5)  # 90-95%
                                    jobs[job_id]['progress'] = min(current_progress, 95)
                            except:
                                pass
                        
                        # Determine source language - FORCE it if specified (more accurate)
                        whisper_lang = None
                        if source_language and source_language != 'auto':
                            # Map language codes to Whisper format
                            lang_map = {
                                'zh': 'zh', 'zh-CN': 'zh', 'zh-TW': 'zh',
                                'ar': 'ar',  # Arabic
                                'en': 'en',  # English
                                'es': 'es',  # Spanish
                                'fr': 'fr',  # French
                                'de': 'de',  # German
                                'it': 'it',  # Italian
                                'ja': 'ja',  # Japanese
                                'ko': 'ko',  # Korean
                                'pt': 'pt',  # Portuguese
                                'ru': 'ru',  # Russian
                                'tr': 'tr',  # Turkish
                                'hi': 'hi',  # Hindi
                            }
                            whisper_lang = lang_map.get(source_language, source_language)
                        
                        # Enhanced transcribe options for better accuracy
                        transcribe_options = {
                            'language': whisper_lang,  # Force language if specified
                            'task': 'transcribe',  # Always transcribe in original language
                            'fp16': False,  # Better compatibility
                            'verbose': False,  # Reduce console output
                            'temperature': 0.0,  # More deterministic (less random)
                            'compression_ratio_threshold': 2.4,  # Better quality control
                            'logprob_threshold': -1.0,  # Better filtering
                            'no_speech_threshold': 0.6,  # Better silence detection
                            'condition_on_previous_text': True,  # Better context
                        }
                        
                        try:
                            lang_msg = f"language: {source_language}" if source_language != 'auto' else "auto-detecting language"
                            print(f"[SUBTITLE] Starting Whisper transcription ({lang_msg})...")
                        except:
                            pass
                        
                        # Extract and preprocess audio for better transcription
                        jobs[job_id]['message'] = 'Preprocessing audio for better accuracy...'
                        audio_file = output_dir / f"{video_file.stem}_clean.wav"
                        
                        try:
                            # Extract audio with enhancement: normalize volume, reduce noise, mono channel
                            ffmpeg_audio_cmd = [
                                'ffmpeg', '-i', str(video_file),
                                '-vn',  # No video
                                '-af', 'loudnorm,highpass=f=200,lowpass=f=3000',  # Normalize + filter for speech
                                '-ar', '16000',  # 16kHz sample rate (optimal for speech)
                                '-ac', '1',  # Mono
                                '-y',  # Overwrite
                                str(audio_file)
                            ]
                            subprocess.run(ffmpeg_audio_cmd, check=True, capture_output=True)
                            
                            # Use cleaned audio for transcription
                            transcribe_input = str(audio_file)
                            
                            try:
                                print(f"[SUBTITLE] Audio preprocessed for better accuracy")
                            except:
                                pass
                        except Exception as e:
                            # If preprocessing fails, use original video
                            transcribe_input = str(video_file)
                            try:
                                print(f"[SUBTITLE] Audio preprocessing skipped: {str(e)}")
                            except:
                                pass
                        
                        jobs[job_id]['message'] = 'Analyzing audio with AI... (This may take 5-10 minutes)'
                        
                        result = model.transcribe(transcribe_input, **transcribe_options)
                        
                        # Clean up temporary audio file
                        try:
                            if audio_file.exists():
                                audio_file.unlink()
                        except:
                            pass
                        
                        try:
                            detected_lang = result.get('language', 'unknown')
                            print(f"[SUBTITLE] Transcription complete! Detected language: {detected_lang}, {len(result['segments'])} segments")
                        except:
                            pass
                        
                        # Check if translation is needed
                        need_translation = (target_language != 'same' and 
                                          TRANSLATOR_AVAILABLE and 
                                          target_language != source_language)
                        
                        if need_translation:
                            jobs[job_id]['progress'] = 93
                            jobs[job_id]['message'] = f'Translating to {target_language}... (30-60 seconds)'
                            try:
                                print(f"[TRANSLATE] Starting translation to {target_language}...")
                            except:
                                pass
                        
                        # Generate SRT subtitle file
                        subtitle_file = output_dir / f"{video_file.stem}.srt"
                        
                        # Store original transcription for preview (first 3 lines)
                        transcription_preview = []
                        
                        with open(subtitle_file, 'w', encoding='utf-8') as f:
                            for i, segment in enumerate(result['segments'], 1):
                                start_time = format_timestamp(segment['start'])
                                end_time = format_timestamp(segment['end'])
                                text = segment['text'].strip()
                                
                                # Save original text for preview (first 3 segments)
                                if i <= 3:
                                    transcription_preview.append(text)
                                
                                # Translate if needed
                                if need_translation and text:
                                    try:
                                        # Use detected language as source if auto-detect was used
                                        src_lang = source_language if source_language != 'auto' else result.get('language', 'auto')
                                        text = translate_text(text, src_lang, target_language)
                                    except Exception as e:
                                        try:
                                            print(f"[TRANSLATE] Error translating segment {i}: {str(e)}")
                                        except:
                                            pass
                                        # Keep original text if translation fails
                                
                                f.write(f"{i}\n")
                                f.write(f"{start_time} --> {end_time}\n")
                                f.write(f"{text}\n\n")
                        
                        # Store transcription preview in job for user to see
                        jobs[job_id]['transcription_preview'] = ' | '.join(transcription_preview)
                        
                        subtitle_files.append(subtitle_file)
                        
                        if need_translation:
                            try:
                                print(f"[TRANSLATE] Translation complete!")
                            except:
                                pass
                        
                        try:
                            print(f"[SUBTITLE] AI-generated subtitle created successfully!")
                        except:
                            pass
                        
                    except Exception as e:
                        try:
                            print(f"[SUBTITLE] Whisper generation failed: {str(e)}")
                        except:
                            pass
                        # If AI fails, return video only
                        jobs[job_id].update({
                            'status': 'completed',
                            'progress': 100,
                            'message': 'Download complete! (Could not generate subtitles automatically)',
                            'output_path': str(video_file),
                            'subtitle_count': 0
                        })
                        if download_id:
                            total_size = video_file.stat().st_size
                            download_history.update_download(download_id, status='completed', file_size=total_size, title=video_title)
                        return
                else:
                    # Whisper not available
                    jobs[job_id].update({
                        'status': 'completed',
                        'progress': 100,
                        'message': 'Download complete! (No subtitles available)',
                        'output_path': str(video_file),
                        'subtitle_count': 0
                    })
                    if download_id:
                        total_size = video_file.stat().st_size
                        download_history.update_download(download_id, status='completed', file_size=total_size, title=video_title)
                    return
            
            # Create output MKV with embedded subtitles
            output_mkv = output_dir / f"{video_file.stem}_with_subs.mkv"
            
            jobs[job_id]['progress'] = 96
            jobs[job_id]['message'] = 'Embedding subtitles...'
            
            try:
                # Build FFmpeg command to embed subtitles
                ffmpeg_cmd = ['ffmpeg', '-i', str(video_file)]
                
                # Add subtitle inputs
                for idx, sub_file in enumerate(subtitle_files):
                    ffmpeg_cmd.extend(['-i', str(sub_file)])
                
                # Map video and audio from first input
                ffmpeg_cmd.extend(['-map', '0:v', '-map', '0:a'])
                
                # Map subtitle streams from additional inputs
                for idx in range(len(subtitle_files)):
                    ffmpeg_cmd.extend(['-map', f'{idx+1}:0'])
                
                # Copy video and audio, encode subtitles
                ffmpeg_cmd.extend(['-c:v', 'copy', '-c:a', 'copy', '-c:s', 'srt'])
                
                # Set subtitle metadata
                for idx in range(len(subtitle_files)):
                    # Use target language for subtitle metadata if translating, otherwise use source
                    lang = target_language if target_language != 'same' else sub_lang
                    if not lang or lang == 'auto':
                        lang = 'eng'
                    ffmpeg_cmd.extend([f'-metadata:s:s:{idx}', f'language={lang}'])
                
                # Output file
                ffmpeg_cmd.extend(['-y', str(output_mkv)])
                
                try:
                    print(f"[SUBTITLE] Running FFmpeg...")
                    print(f"[SUBTITLE] Command: {' '.join(ffmpeg_cmd)}")
                except:
                    pass
                
                # Run FFmpeg
                result = subprocess.run(
                    ffmpeg_cmd,
                    capture_output=True,
                    text=False,  # Use bytes to avoid encoding issues
                    errors='replace'
                )
                
                if result.returncode != 0:
                    try:
                        error_msg = result.stderr.decode('utf-8', errors='replace') if result.stderr else 'Unknown error'
                        print(f"[SUBTITLE] FFmpeg failed with code {result.returncode}")
                        print(f"[SUBTITLE] Error: {error_msg[:500]}")
                    except:
                        pass
                    raise Exception(f'FFmpeg embedding failed with code {result.returncode}')
                
                # Check if output file was created
                if not output_mkv.exists() or output_mkv.stat().st_size == 0:
                    raise Exception('Output MKV file was not created or is empty')
                
                try:
                    print(f"[SUBTITLE] Embedding successful! MKV size: {output_mkv.stat().st_size} bytes")
                except:
                    pass
                
                jobs[job_id].update({
                    'status': 'completed',
                    'progress': 100,
                    'message': f'Download complete! Video with {len(subtitle_files)} embedded subtitle(s)',
                    'output_path': str(output_mkv),
                    'subtitle_count': len(subtitle_files)
                })
                
            except Exception as e:
                print(f"[SUBTITLE] Embedding error: {str(e)}")
                # If embedding fails, return as ZIP instead
                zip_path = output_dir / f'{video_title}_with_subs.zip'
                with zipfile.ZipFile(str(zip_path), 'w') as zipf:
                    for file in output_files:
                        zipf.write(str(file), file.name)
                
                jobs[job_id].update({
                    'status': 'completed',
                    'progress': 100,
                    'message': f'Download complete! Video + {len(subtitle_files)} separate subtitle file(s) (embedding failed)',
                    'output_path': str(zip_path),
                    'subtitle_count': len(subtitle_files),
                    'is_zip': True
                })
        
        elif download_type == 'video_separate_subs':
            # Return video + separate subtitle files (works with Windows Media Player!)
            if video_files and subtitle_files:
                # Rename subtitle file to match video filename exactly
                video_file = video_files[0]
                subtitle_file = subtitle_files[0]
                
                # Create matching subtitle filename
                matching_subtitle = output_dir / f"{video_file.stem}.srt"
                if subtitle_file != matching_subtitle:
                    shutil.copy2(subtitle_file, matching_subtitle)
                    subtitle_file = matching_subtitle
                
                # Create ZIP with both files
                zip_path = output_dir / f'{video_file.stem}_with_subs.zip'
                with zipfile.ZipFile(str(zip_path), 'w') as zipf:
                    zipf.write(str(video_file), video_file.name)
                    zipf.write(str(subtitle_file), subtitle_file.name)
                
                jobs[job_id].update({
                    'status': 'completed',
                    'progress': 100,
                    'message': f'Download complete! Video + subtitle file ready for Windows Media Player',
                    'output_path': str(zip_path),
                    'subtitle_count': len(subtitle_files),
                    'is_zip': True
                })
            else:
                # If no subtitles, return video only
                jobs[job_id].update({
                    'status': 'completed',
                    'progress': 100,
                    'message': 'Download complete!',
                    'output_path': str(video_files[0] if video_files else output_files[0])
                })
        
        else:  # subs_only
            # Just subtitle files
            if len(subtitle_files) > 1:
                zip_path = output_dir / f'{video_title}_subtitles.zip'
                with zipfile.ZipFile(str(zip_path), 'w') as zipf:
                    for file in subtitle_files:
                        zipf.write(str(file), file.name)
                
                jobs[job_id].update({
                    'status': 'completed',
                    'progress': 100,
                    'message': f'Downloaded {len(subtitle_files)} subtitle file(s)',
                    'output_path': str(zip_path),
                    'subtitle_count': len(subtitle_files),
                    'is_zip': True
                })
            elif subtitle_files:
                jobs[job_id].update({
                    'status': 'completed',
                    'progress': 100,
                    'message': 'Subtitle downloaded successfully',
                    'output_path': str(subtitle_files[0]),
                    'subtitle_count': 1
                })
            else:
                raise Exception('No subtitle files found')
        
        # Update history
        if download_id:
            total_size = sum(f.stat().st_size for f in output_files)
            download_history.update_download(
                download_id,
                status='completed',
                file_size=total_size,
                title=video_title
            )
        
    except Exception as e:
        error_msg = str(e)
        jobs[job_id].update({
            'status': 'failed',
            'progress': 0,
            'message': f'Download failed: {error_msg}'
        })
        
        if download_id:
            download_history.update_download(
                download_id,
                status='failed',
                error_message=error_msg
            )


def download_video(job_id, url, format_type, quality):
    """Download single video from YouTube"""
    download_id = None
    try:
        # Add to history
        download_id = download_history.add_download(
            url=url,
            format_type=format_type,
            quality=quality,
            job_id=job_id
        )
        
        jobs[job_id]['progress'] = 10
        jobs[job_id]['can_cancel'] = True
        jobs[job_id]['download_id'] = download_id
        
        output_dir = Path(app.config['OUTPUT_FOLDER']) / job_id
        output_dir.mkdir(exist_ok=True)
        
        # Check for cancellation
        if jobs[job_id].get('cancelled', False):
            raise Exception('Download cancelled by user')
        
        jobs[job_id]['progress'] = 20
        jobs[job_id]['message'] = 'Starting download...'
        
        # Progress callback to update job status
        def progress_callback(progress_info):
            if jobs[job_id].get('cancelled', False):
                return
            
            downloaded = progress_info.get('downloaded_bytes', 0)
            total = progress_info.get('total_bytes', 0)
            speed = progress_info.get('speed', 0)
            eta = progress_info.get('eta', 0)
            percent = progress_info.get('percent', 0)
            
            # Format sizes
            downloaded_mb = downloaded / (1024 * 1024)
            total_mb = total / (1024 * 1024)
            speed_mb = speed / (1024 * 1024) if speed else 0
            
            # Calculate new progress (20-90%)
            new_progress = int(20 + (percent * 0.7))
            
            # IMPORTANT: Never go backwards! Only update if progress increased
            current_progress = jobs[job_id].get('progress', 0)
            if new_progress > current_progress:
                jobs[job_id]['progress'] = new_progress
                jobs[job_id]['downloaded_mb'] = round(downloaded_mb, 2)
                jobs[job_id]['total_mb'] = round(total_mb, 2)
                jobs[job_id]['speed_mb'] = round(speed_mb, 2)
                jobs[job_id]['eta_seconds'] = eta
                jobs[job_id]['message'] = f'Downloading: {downloaded_mb:.1f} MB / {total_mb:.1f} MB ({speed_mb:.2f} MB/s)'
            elif current_progress >= 90:
                # If at 90% or higher, show post-processing message
                jobs[job_id]['message'] = 'Processing video...'
        
        # Clean URL - remove playlist parameters that cause progress issues
        import re
        from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
        
        # Extract clean video URL (remove playlist, radio parameters)
        if 'youtube.com' in url or 'youtu.be' in url:
            # Extract video ID
            video_id_match = re.search(r'(?:v=|/)([0-9A-Za-z_-]{11})', url)
            if video_id_match:
                video_id = video_id_match.group(1)
                clean_url = f'https://www.youtube.com/watch?v={video_id}'
                print(f"[DOWNLOAD] Original URL: {url}")
                print(f"[DOWNLOAD] Cleaned URL: {clean_url}")
                url = clean_url
        
        # Perform download with progress tracking
        # Map format_type: 'mp3' -> 'audio', 'video' -> 'video'
        download_format = 'audio' if format_type == 'mp3' else 'video'
        
        print(f"[DOWNLOAD] Starting YouTube download")
        print(f"[DOWNLOAD] URL: {url}")
        print(f"[DOWNLOAD] Format: {download_format}")
        print(f"[DOWNLOAD] Quality: {quality}")
        print(f"[DOWNLOAD] Output dir: {output_dir}")
        
        media_tool.download_youtube(url, str(output_dir), download_format, quality, progress_callback)
        
        # Check for cancellation after download
        if jobs[job_id].get('cancelled', False):
            raise Exception('Download cancelled by user')
        
        jobs[job_id]['progress'] = 90
        
        # Find downloaded file
        print(f"[DOWNLOAD] Looking for files in: {output_dir}")
        all_files = list(output_dir.glob('*.*'))
        print(f"[DOWNLOAD] All files found: {[f.name for f in all_files]}")
        
        output_files = [f for f in all_files if f.suffix.lower() in ['.mp3', '.mp4', '.m4a', '.webm', '.mkv', '.avi']]
        print(f"[DOWNLOAD] Media files found: {[f.name for f in output_files]}")
        
        if output_files:
            # Get the most recently created file
            output_path = str(max(output_files, key=lambda x: x.stat().st_mtime))
            file_size = Path(output_path).stat().st_size
            
            jobs[job_id].update({
                'status': 'completed',
                'progress': 100,
                'output_path': output_path,
                'output_filename': Path(output_path).name,
                'message': 'Download completed successfully!'
            })
            
            # Update history
            if download_id:
                download_history.update_download(
                    download_id,
                    status='completed',
                    file_path=output_path,
                    file_size=file_size,
                    title=Path(output_path).stem
                )
        else:
            # Check if directory exists and what's in it
            if output_dir.exists():
                all_files_debug = list(output_dir.glob('*'))
                print(f"[DOWNLOAD] ERROR: No media files found")
                print(f"[DOWNLOAD] Directory exists: {output_dir}")
                print(f"[DOWNLOAD] All files in directory: {[f.name for f in all_files_debug]}")
            else:
                print(f"[DOWNLOAD] ERROR: Output directory doesn't exist: {output_dir}")
            
            jobs[job_id].update({
                'status': 'failed',
                'progress': 0,
                'message': 'Download failed: No output file generated. Check if yt-dlp is installed: pip3 install --upgrade yt-dlp'
            })
            
            # Update history
            if download_id:
                download_history.update_download(
                    download_id,
                    status='failed',
                    error_message='No output file generated'
                )
    
    except Exception as e:
        jobs[job_id].update({
            'status': 'failed',
            'progress': 0,
            'message': f'Error: {str(e)}'
        })
        
        # Update history
        if download_id:
            download_history.update_download(
                download_id,
                status='failed',
                error_message=str(e)
            )


def download_social_media(job_id, url, platform, format_type):
    """Download video from Instagram, Facebook, or TikTok"""
    download_id = None
    try:
        # Add to history
        download_id = download_history.add_download(
            url=url,
            format_type=format_type,
            quality='best',
            job_id=job_id
        )
        
        jobs[job_id]['progress'] = 10
        jobs[job_id]['can_cancel'] = True
        jobs[job_id]['download_id'] = download_id
        
        output_dir = Path(app.config['OUTPUT_FOLDER']) / job_id
        output_dir.mkdir(exist_ok=True)
        
        # Check for cancellation
        if jobs[job_id].get('cancelled', False):
            raise Exception('Download cancelled by user')
        
        jobs[job_id]['progress'] = 20
        jobs[job_id]['message'] = f'Starting {platform} download...'
        
        # Progress callback
        def progress_callback(progress_info):
            if jobs[job_id].get('cancelled', False):
                return
            
            downloaded = progress_info.get('downloaded_bytes', 0)
            total = progress_info.get('total_bytes', 0)
            speed = progress_info.get('speed', 0)
            percent = progress_info.get('percent', 0)
            
            downloaded_mb = downloaded / (1024 * 1024)
            total_mb = total / (1024 * 1024)
            speed_mb = speed / (1024 * 1024) if speed else 0
            
            # Calculate new progress (20-90%)
            new_progress = int(20 + (percent * 0.7))
            
            # IMPORTANT: Never go backwards! Only update if progress increased
            current_progress = jobs[job_id].get('progress', 0)
            if new_progress > current_progress:
                jobs[job_id]['progress'] = new_progress
                jobs[job_id]['downloaded_mb'] = round(downloaded_mb, 2)
                jobs[job_id]['total_mb'] = round(total_mb, 2)
                jobs[job_id]['speed_mb'] = round(speed_mb, 2)
                jobs[job_id]['message'] = f'Downloading: {downloaded_mb:.1f} MB / {total_mb:.1f} MB ({speed_mb:.2f} MB/s)'
            elif current_progress >= 90:
                # If at 90% or higher, show post-processing message
                jobs[job_id]['message'] = 'Processing video...'
        
        # Use yt-dlp for social media downloads (it supports Instagram, Facebook, TikTok)
        # Configure yt-dlp options with platform-specific settings
        ydl_opts = {
            'outtmpl': str(output_dir / '%(title)s.%(ext)s'),
            'quiet': False,
            'no_warnings': False,
        }
        
        # Add platform-specific user agent and cookies handling
        ydl_opts['http_headers'] = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        # Platform-specific configurations
        if platform == 'facebook':
            # Normalize Facebook URL to standard format
            import re
            original_url = url
            
            # Try to normalize Facebook URLs
            if 'fb.watch' in url:
                # Extract video ID from fb.watch/VIDEO_ID
                match = re.search(r'fb\.watch/([^/?]+)', url)
                if match:
                    video_id = match.group(1)
                    url = f'https://www.facebook.com/watch?v={video_id}'
                    jobs[job_id]['message'] = 'Normalizing Facebook URL...'
            elif '/videos/' in url:
                # Extract video ID from /videos/VIDEO_ID format
                match = re.search(r'/videos/(\d+)', url)
                if match:
                    video_id = match.group(1)
                    url = f'https://www.facebook.com/watch?v={video_id}'
                    jobs[job_id]['message'] = 'Normalizing Facebook URL...'
            elif 'watch?v=' not in url and 'facebook.com' in url:
                # Try to extract any numeric ID
                match = re.search(r'/(\d{10,})', url)
                if match:
                    video_id = match.group(1)
                    url = f'https://www.facebook.com/watch?v={video_id}'
                    jobs[job_id]['message'] = 'Normalizing Facebook URL...'
            
            # Facebook-specific extractor options
            ydl_opts['extractor_args'] = {
                'facebook': {
                    'skip_dash_manifest': True,
                }
            }
            
            # Use simpler format for Facebook
            if format_type != 'mp3':
                ydl_opts['format'] = 'best'
        
        elif platform == 'instagram':
            # Instagram-specific options
            ydl_opts['http_headers'] = {
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1'
            }
            if format_type != 'mp3':
                ydl_opts['format'] = 'best'
        
        elif platform == 'tiktok':
            # TikTok-specific options
            ydl_opts['http_headers'] = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Referer': 'https://www.tiktok.com/'
            }
            if format_type != 'mp3':
                ydl_opts['format'] = 'best'
        
        # Add cookies support for all platforms (helps with authentication)
        ydl_opts['cookiesfrombrowser'] = None  # Don't auto-use cookies
        ydl_opts['nocheckcertificate'] = True  # Skip SSL certificate validation
        
        if format_type == 'mp3':
            ydl_opts['format'] = 'bestaudio/best'
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
        else:
            # For video, use format selection
            if platform == 'facebook':
                # Facebook format already set above
                pass
            else:
                ydl_opts['format'] = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
                ydl_opts['merge_output_format'] = 'mp4'
        
        # Progress hook
        def progress_hook(d):
            if jobs[job_id].get('cancelled', False):
                raise Exception('Download cancelled')
            
            if d['status'] == 'downloading':
                downloaded = d.get('downloaded_bytes', 0)
                total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                speed = d.get('speed', 0)
                eta = d.get('eta', 0)
                
                if total > 0:
                    percent = (downloaded / total) * 100
                    progress_callback({
                        'downloaded_bytes': downloaded,
                        'total_bytes': total,
                        'speed': speed,
                        'eta': eta,
                        'percent': percent
                    })
        
        ydl_opts['progress_hooks'] = [progress_hook]
        
        # Download with yt-dlp
        jobs[job_id]['message'] = f'Downloading from {platform}...'
        
        # Initialize title variable
        title = None
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # For Facebook, try to extract info first to validate URL
                if platform == 'facebook':
                    jobs[job_id]['message'] = 'Validating Facebook URL...'
                    try:
                        # Try to extract info without downloading first
                        info = ydl.extract_info(url, download=False)
                        title = info.get('title', 'video')
                        jobs[job_id]['message'] = f'Found: {title}. Starting download...'
                    except Exception as extract_error:
                        # If extraction fails, provide helpful error
                        error_str = str(extract_error)
                        if 'Cannot parse data' in error_str or 'parse' in error_str.lower() or 'No video formats found' in error_str:
                            raise Exception(
                                'Facebook video extraction failed. Solutions:\n'
                                '✓ Update yt-dlp: pip install --upgrade yt-dlp\n'
                                '✓ Ensure video is PUBLIC (not private/friends-only)\n'
                                '✓ Use direct watch URL: https://www.facebook.com/watch?v=VIDEO_ID\n'
                                '✓ Try using browser dev tools to check if video URL is valid\n'
                                '✓ Facebook may have changed their API - wait for yt-dlp update'
                            )
                        else:
                            raise
                
                # Now download
                info = ydl.extract_info(url, download=True)
                if not title:
                    title = info.get('title', 'video')
                    
        except yt_dlp.utils.DownloadError as e:
            error_str = str(e)
            # Clean ANSI codes
            import re
            error_str = re.sub(r'\x1b\[[0-9;]*m', '', error_str)
            
            # Provide helpful error messages
            if 'Cannot parse data' in error_str or 'parse' in error_str.lower() or 'No video formats found' in error_str:
                if platform == 'facebook':
                    raise Exception(
                        '⚠️ Facebook download is currently difficult due to Facebook\'s restrictions.\n\n'
                        '🔧 SOLUTIONS (Try in order):\n\n'
                        '1️⃣ UPDATE YT-DLP (MOST IMPORTANT):\n'
                        '   pip install --upgrade yt-dlp\n'
                        '   (Facebook changes often, need latest version)\n\n'
                        '2️⃣ CHECK VIDEO STATUS:\n'
                        '   ✓ Video must be PUBLIC (not private/friends-only)\n'
                        '   ✓ Open video in browser first to verify it works\n'
                        '   ✓ Use direct watch URL: https://www.facebook.com/watch?v=VIDEO_ID\n\n'
                        '3️⃣ ALTERNATIVE METHODS:\n'
                        '   ✓ Try downloading from Facebook mobile site\n'
                        '   ✓ Use browser dev tools (F12) to find direct video URL\n'
                        '   ✓ Right-click video → "Copy video URL" and try that\n\n'
                        '4️⃣ IF STILL FAILS:\n'
                        '   ✓ Facebook may have updated their API\n'
                        '   ✓ Wait for yt-dlp to release fix\n'
                        '   ✓ Check yt-dlp GitHub for known issues\n\n'
                        '💡 TIP: YouTube, TikTok, and Instagram usually work better!'
                    )
                elif platform == 'instagram':
                    raise Exception(
                        '⚠️ Instagram download failed.\n\n'
                        '🔧 QUICK FIXES:\n\n'
                        '1️⃣ UPDATE YT-DLP:\n'
                        '   pip install --upgrade yt-dlp\n\n'
                        '2️⃣ CHECK URL FORMAT:\n'
                        '   ✓ Post: https://www.instagram.com/p/POST_ID/\n'
                        '   ✓ Reel: https://www.instagram.com/reel/REEL_ID/\n'
                        '   ✓ Must be PUBLIC (not private account)\n\n'
                        '3️⃣ ALTERNATIVE:\n'
                        '   ✓ Open post in browser\n'
                        '   ✓ Right-click video → "Copy video address"\n'
                        '   ✓ Try that direct URL instead\n\n'
                        '💡 Instagram changes frequently - update yt-dlp weekly!'
                    )
                elif platform == 'tiktok':
                    raise Exception(
                        '⚠️ TikTok download failed.\n\n'
                        '🔧 QUICK FIXES:\n\n'
                        '1️⃣ UPDATE YT-DLP:\n'
                        '   pip install --upgrade yt-dlp\n\n'
                        '2️⃣ CHECK URL:\n'
                        '   ✓ Use FULL URL (not vm.tiktok.com)\n'
                        '   ✓ Format: https://www.tiktok.com/@username/video/1234567890\n'
                        '   ✓ Video must be PUBLIC (not age-restricted)\n\n'
                        '3️⃣ GET FULL URL:\n'
                        '   ✓ Open video in TikTok\n'
                        '   ✓ Click "Share" → "Copy Link"\n'
                        '   ✓ If it\'s vm.tiktok.com, open it in browser first\n'
                        '   ✓ Copy the full tiktok.com/@username/video/... URL\n\n'
                        '💡 TikTok changes often - update yt-dlp regularly!'
                    )
                else:
                    raise Exception(f'{platform.capitalize()} download failed. Update yt-dlp: pip install --upgrade yt-dlp')
            elif 'HTTP Error 4' in error_str or 'Private video' in error_str or 'not available' in error_str.lower():
                raise Exception(
                    f'{platform.capitalize()} video access error:\n'
                    '✓ Video may be PRIVATE or RESTRICTED\n'
                    '✓ Account may require login\n'
                    '✓ Video may have been deleted\n'
                    '✓ Check if URL is correct and video is accessible in browser'
                )
            else:
                raise
        
        jobs[job_id]['progress'] = 90
        
        # Find downloaded file
        output_files = list(output_dir.glob('*.*'))
        output_files = [f for f in output_files if f.suffix in ['.mp3', '.mp4', '.m4a', '.webm']]
        
        if output_files:
            output_path = str(max(output_files, key=lambda x: x.stat().st_mtime))
            file_size = Path(output_path).stat().st_size
            
            jobs[job_id].update({
                'status': 'completed',
                'progress': 100,
                'output_path': output_path,
                'output_filename': Path(output_path).name,
                'message': f'{platform.capitalize()} download completed successfully!'
            })
            
            # Update history
            if download_id:
                download_history.update_download(
                    download_id,
                    status='completed',
                    file_path=output_path,
                    file_size=file_size,
                    title=title
                )
        else:
            jobs[job_id].update({
                'status': 'failed',
                'progress': 0,
                'message': 'Download failed: No output file generated'
            })
            
            if download_id:
                download_history.update_download(
                    download_id,
                    status='failed',
                    error_message='No output file generated'
                )
    
    except Exception as e:
        error_msg = str(e)
        # Clean up ANSI color codes from error messages
        import re
        error_msg = re.sub(r'\x1b\[[0-9;]*m', '', error_msg)
        
        # Provide user-friendly error messages
        if 'Cannot parse data' in error_msg or 'parse' in error_msg.lower():
            if platform == 'facebook':
                user_msg = (
                    'Facebook download failed. Possible solutions:\n'
                    '1. Update yt-dlp: pip install --upgrade yt-dlp\n'
                    '2. Ensure video is public (not private)\n'
                    '3. Use direct watch URL: facebook.com/watch?v=VIDEO_ID\n'
                    '4. Facebook may have changed their API - try again later'
                )
            else:
                user_msg = f'{platform.capitalize()} download failed. Try updating yt-dlp: pip install --upgrade yt-dlp'
        else:
            user_msg = f'Error: {error_msg}'
        
        jobs[job_id].update({
            'status': 'failed',
            'progress': 0,
            'message': user_msg
        })
        
        if download_id:
            download_history.update_download(
                download_id,
                status='failed',
                error_message=error_msg
            )


def download_multiple_videos(job_id, urls, format_type, quality):
    """Download multiple videos from YouTube and package as ZIP"""
    try:
        jobs[job_id]['progress'] = 5
        jobs[job_id]['can_cancel'] = True
        
        output_dir = Path(app.config['OUTPUT_FOLDER']) / job_id
        output_dir.mkdir(exist_ok=True)
        
        total_videos = len(urls)
        completed = 0
        
        # Download each video
        for i, url in enumerate(urls, 1):
            # Check for cancellation
            if jobs[job_id].get('cancelled', False):
                jobs[job_id].update({
                    'status': 'cancelled',
                    'progress': 0,
                    'message': f'Download cancelled. {completed} of {total_videos} videos were downloaded before cancellation.'
                })
                return
            
            jobs[job_id]['message'] = f'Downloading video {i} of {total_videos}...'
            jobs[job_id]['progress'] = int(5 + ((i-1) / total_videos) * 85)
            
            # Progress callback for this video
            def progress_callback(progress_info):
                if jobs[job_id].get('cancelled', False):
                    return
                
                downloaded_mb = progress_info.get('downloaded_bytes', 0) / (1024 * 1024)
                total_mb = progress_info.get('total_bytes', 0) / (1024 * 1024)
                speed_mb = progress_info.get('speed', 0) / (1024 * 1024) if progress_info.get('speed') else 0
                
                jobs[job_id]['message'] = f'Video {i}/{total_videos}: {downloaded_mb:.1f}/{total_mb:.1f} MB ({speed_mb:.2f} MB/s)'
            
            try:
                media_tool.download_youtube(url, str(output_dir), format_type, quality, progress_callback)
                completed += 1
                jobs[job_id]['completed_videos'] = completed
            except Exception as e:
                print(f"[ERROR] Failed to download {url}: {str(e)}")
                continue
        
        jobs[job_id]['progress'] = 90
        jobs[job_id]['message'] = 'Packaging downloads...'
        
        # Find all downloaded files
        output_files = list(output_dir.glob('*.*'))
        output_files = [f for f in output_files if f.suffix in ['.mp3', '.mp4', '.m4a', '.webm']]
        
        if output_files:
            # If multiple files, create ZIP
            if len(output_files) > 1:
                zip_path = output_dir / 'playlist_downloads.zip'
                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for file_path in output_files:
                        zipf.write(file_path, file_path.name)
                
                jobs[job_id].update({
                    'status': 'completed',
                    'progress': 100,
                    'output_path': str(zip_path),
                    'output_filename': 'playlist_downloads.zip',
                    'message': f'Successfully downloaded {completed} of {total_videos} videos!',
                    'is_zip': True
                })
            else:
                # Single file
                output_path = str(output_files[0])
                jobs[job_id].update({
                    'status': 'completed',
                    'progress': 100,
                    'output_path': output_path,
                    'output_filename': Path(output_path).name,
                    'message': f'Downloaded {completed} video successfully!'
                })
        else:
            jobs[job_id].update({
                'status': 'failed',
                'progress': 0,
                'message': 'Download failed: No output files generated'
            })
    
    except Exception as e:
        jobs[job_id].update({
            'status': 'failed',
            'progress': 0,
            'message': f'Error: {str(e)}'
        })


# Watermark Removal Routes

@app.route('/watermark/remove', methods=['POST', 'OPTIONS'])
def remove_watermark():
    """Remove watermark from image using classical inpainting"""
    # Handle CORS preflight request
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST')
        return response
    
    try:
        print("[WATERMARK] Processing watermark removal request...")
        
        data = request.json
        image_data = data.get('image')
        mask_data = data.get('mask')
        method = data.get('method', 'telea')  # 'telea' or 'ns' (Navier-Stokes)
        
        print(f"[WATERMARK] Method: {method}")
        print(f"[WATERMARK] Has image data: {bool(image_data)}")
        print(f"[WATERMARK] Has mask data: {bool(mask_data)}")
        
        if not image_data or not mask_data:
            print("[WATERMARK] ERROR: Missing image or mask data")
            return jsonify({'error': 'Image and mask data required'}), 400
        
        # Check if OpenCV is available
        try:
            import cv2
            import numpy as np
            print("[WATERMARK] OpenCV is available")
        except ImportError as e:
            print(f"[WATERMARK] ERROR: OpenCV not available: {str(e)}")
            return jsonify({'error': 'OpenCV is not installed. Please install: pip install opencv-python'}), 500
        
        # Decode base64 images
        try:
            image_bytes = base64.b64decode(image_data.split(',')[1])
            mask_bytes = base64.b64decode(mask_data.split(',')[1])
            print("[WATERMARK] Base64 decoded successfully")
        except Exception as e:
            print(f"[WATERMARK] ERROR: Failed to decode base64: {str(e)}")
            return jsonify({'error': f'Failed to decode base64 data: {str(e)}'}), 400
        
        # Convert to numpy arrays
        image_array = np.frombuffer(image_bytes, dtype=np.uint8)
        mask_array = np.frombuffer(mask_bytes, dtype=np.uint8)
        
        # Decode images
        image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
        mask = cv2.imdecode(mask_array, cv2.IMREAD_GRAYSCALE)
        
        print(f"[WATERMARK] Image decoded: {image is not None}, shape: {image.shape if image is not None else 'None'}")
        print(f"[WATERMARK] Mask decoded: {mask is not None}, shape: {mask.shape if mask is not None else 'None'}")
        
        if image is None or mask is None:
            print("[WATERMARK] ERROR: Failed to decode image or mask")
            return jsonify({'error': 'Failed to decode image or mask'}), 400
        
        # Apply ADVANCED MULTI-PASS INPAINTING with texture synthesis
        print("[WATERMARK] Starting inpainting process...")
        result = advanced_inpainting(image, mask, method)
        print("[WATERMARK] Inpainting completed successfully")
        
        # Convert result to base64
        _, buffer = cv2.imencode('.png', result)
        result_base64 = base64.b64encode(buffer).decode('utf-8')
        
        print("[WATERMARK] Result encoded successfully")
        
        return jsonify({
            'success': True,
            'result': f'data:image/png;base64,{result_base64}'
        })
    
    except Exception as e:
        print(f"[WATERMARK] ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Processing failed: {str(e)}'}), 500


def advanced_inpainting(image, mask, method='ns'):
    """
    Advanced classical inpainting using multiple techniques:
    1. Multi-pass progressive inpainting
    2. Texture-aware blending
    3. Edge preservation
    4. Poisson-like seamless cloning
    """
    
    # Step 1: Prepare mask with slight dilation
    kernel = np.ones((5, 5), np.uint8)
    mask_dilated = cv2.dilate(mask, kernel, iterations=1)
    
    # Step 2: Multi-scale progressive inpainting
    # Start with smaller inpainting radius and progressively increase
    result = image.copy()
    
    # Pass 1: Small radius for fine details
    if method == 'ns':
        result = cv2.inpaint(result, mask_dilated, 3, cv2.INPAINT_NS)
    else:
        result = cv2.inpaint(result, mask_dilated, 3, cv2.INPAINT_TELEA)
    
    # Pass 2: Medium radius for texture
    result = cv2.inpaint(result, mask_dilated, 7, cv2.INPAINT_NS)
    
    # Pass 3: Large radius for overall structure
    result = cv2.inpaint(result, mask_dilated, 15, cv2.INPAINT_NS)
    
    # Step 3: Texture synthesis from surrounding area
    # Find the boundary of the masked region
    mask_boundary = cv2.dilate(mask_dilated, kernel, iterations=5)
    mask_boundary = cv2.subtract(mask_boundary, mask_dilated)
    
    # Extract texture from boundary region
    boundary_region = cv2.bitwise_and(image, image, mask=mask_boundary)
    
    # Apply texture-aware bilateral filtering
    result_textured = cv2.bilateralFilter(result, 9, 75, 75)
    
    # Step 4: Edge-preserving detail enhancement
    # Detect edges in original image
    gray_original = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray_original, 50, 150)
    
    # Blur edges slightly
    edges_dilated = cv2.dilate(edges, kernel, iterations=2)
    
    # Create edge-aware blend
    edge_mask = cv2.cvtColor(edges_dilated, cv2.COLOR_GRAY2BGR).astype(np.float32) / 255.0
    
    # Step 5: Poisson-like seamless blending
    # Create smooth transition at boundary using distance transform
    mask_inv = cv2.bitwise_not(mask_dilated)
    dist_transform = cv2.distanceTransform(mask_inv, cv2.DIST_L2, 5)
    
    # Normalize distance transform for smooth blending
    dist_normalized = cv2.normalize(dist_transform, None, 0, 1, cv2.NORM_MINMAX)
    dist_3channel = cv2.cvtColor((dist_normalized * 255).astype(np.uint8), cv2.COLOR_GRAY2BGR).astype(np.float32) / 255.0
    
    # Create alpha blend based on distance
    alpha = np.clip(dist_3channel * 5, 0, 1)  # Sharp transition near boundary
    
    # Blend original with inpainted result
    mask_3channel = cv2.cvtColor(mask_dilated, cv2.COLOR_GRAY2BGR).astype(np.float32) / 255.0
    blended = (image.astype(np.float32) * (1 - mask_3channel) + 
               result_textured.astype(np.float32) * mask_3channel)
    
    result = blended.astype(np.uint8)
    
    # Step 6: Detail enhancement with unsharp mask
    gaussian = cv2.GaussianBlur(result, (0, 0), 2.0)
    unsharp = cv2.addWeighted(result, 1.5, gaussian, -0.5, 0)
    
    # Apply unsharp mask only to inpainted area
    result = (result * (1 - mask_3channel) + unsharp * mask_3channel).astype(np.uint8)
    
    # Step 7: Noise reduction with edge preservation
    result = cv2.fastNlMeansDenoisingColored(result, None, 10, 10, 7, 21)
    
    # Step 8: Final color correction
    # Match color statistics of inpainted region to surrounding area
    lab = cv2.cvtColor(result, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    
    # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization) to L channel
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l = clahe.apply(l)
    
    result = cv2.merge([l, a, b])
    result = cv2.cvtColor(result, cv2.COLOR_LAB2BGR)
    
    return result


@app.route('/watermark/download', methods=['POST'])
def download_watermark_result():
    """Download the processed image"""
    try:
        data = request.json
        image_data = data.get('image')
        filename = data.get('filename', 'cleaned_image.png')
        
        if not image_data:
            return jsonify({'error': 'No image data provided'}), 400
        
        # Decode base64
        image_bytes = base64.b64decode(image_data.split(',')[1])
        
        # Create response
        return Response(
            image_bytes,
            mimetype='image/png',
            headers={
                'Content-Disposition': f'attachment; filename={filename}'
            }
        )
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# QR Code Generator Routes

@app.route('/generate-qr', methods=['POST'])
def generate_qr():
    """Generate QR code"""
    if not QRCODE_AVAILABLE:
        return jsonify({'error': 'QR code library not installed. Please install: pip install qrcode[pil]'}), 500
    
    try:
        data = request.json
        qr_type = data.get('type', 'text')
        size = int(data.get('size', 300))
        error_correction = data.get('error_correction', 'M')
        
        # Map error correction levels
        error_map = {
            'L': qrcode.constants.ERROR_CORRECT_L,
            'M': qrcode.constants.ERROR_CORRECT_M,
            'Q': qrcode.constants.ERROR_CORRECT_Q,
            'H': qrcode.constants.ERROR_CORRECT_H
        }
        error_level = error_map.get(error_correction, qrcode.constants.ERROR_CORRECT_M)
        
        # Generate content based on type
        if qr_type == 'text':
            content = data.get('text', '')
            if not content:
                return jsonify({'error': 'Text content is required'}), 400
        
        elif qr_type == 'wifi':
            ssid = data.get('ssid', '')
            password = data.get('password', '')
            security = data.get('security', 'WPA')
            hidden = data.get('hidden', False)
            
            if not ssid:
                return jsonify({'error': 'WiFi network name (SSID) is required'}), 400
            
            # Format: WIFI:T:WPA;S:SSID;P:password;H:true;;
            content = f"WIFI:T:{security};S:{ssid};P:{password};H:{str(hidden).lower()};;"
        
        elif qr_type == 'contact':
            name = data.get('name', '')
            phone = data.get('phone', '')
            email = data.get('email', '')
            url = data.get('url', '')
            address = data.get('address', '')
            
            if not name:
                return jsonify({'error': 'Contact name is required'}), 400
            
            # Format: BEGIN:VCARD\nVERSION:3.0\nFN:Name\nTEL:Phone\nEMAIL:Email\nURL:URL\nADR:Address\nEND:VCARD
            vcard = ['BEGIN:VCARD', 'VERSION:3.0', f'FN:{name}']
            if phone:
                vcard.append(f'TEL:{phone}')
            if email:
                vcard.append(f'EMAIL:{email}')
            if url:
                vcard.append(f'URL:{url}')
            if address:
                vcard.append(f'ADR:{address}')
            vcard.append('END:VCARD')
            content = '\n'.join(vcard)
        
        elif qr_type == 'email':
            to_email = data.get('to', '')
            subject = data.get('subject', '')
            body = data.get('body', '')
            
            if not to_email:
                return jsonify({'error': 'Email address is required'}), 400
            
            # Format: mailto:email?subject=subject&body=body
            content = f"mailto:{to_email}"
            params = []
            if subject:
                params.append(f'subject={subject.replace(" ", "%20")}')
            if body:
                params.append(f'body={body.replace(" ", "%20").replace("\n", "%0A")}')
            if params:
                content += '?' + '&'.join(params)
        
        else:
            return jsonify({'error': f'Unknown QR type: {qr_type}'}), 400
        
        # Create QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=error_level,
            box_size=10,
            border=4,
        )
        qr.add_data(content)
        qr.make(fit=True)
        
        # Create image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Resize if needed
        if size != 300:
            img = img.resize((size, size), Image.Resampling.LANCZOS)
        
        # Convert to base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        return jsonify({
            'success': True,
            'qr_code': img_str
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Product QR Generator Routes

@app.route('/generate-product-qr', methods=['POST'])
def generate_product_qr():
    """Generate Product QR code"""
    if not QRCODE_AVAILABLE:
        return jsonify({'error': 'QR code library not installed. Please install: pip install qrcode[pil]'}), 500
    
    try:
        data = request.json
        size = int(data.get('size', 300))
        error_correction = data.get('error_correction', 'M')
        
        # Get product information
        name = data.get('name', '')
        sku = data.get('sku', '')
        price = data.get('price', '')
        currency = data.get('currency', 'USD')
        manufacturer = data.get('manufacturer', '')
        category = data.get('category', '')
        description = data.get('description', '')
        website = data.get('website', '')
        image_url = data.get('image_url', '')
        
        if not name or not sku:
            return jsonify({'error': 'Product name and SKU are required'}), 400
        
        # Create structured product data (JSON format)
        product_info = {
            'name': name,
            'sku': sku,
            'type': 'product'
        }
        
        if price:
            product_info['price'] = float(price)
            product_info['currency'] = currency
        
        if manufacturer:
            product_info['manufacturer'] = manufacturer
        
        if category:
            product_info['category'] = category
        
        if description:
            product_info['description'] = description
        
        if website:
            product_info['website'] = website
        
        if image_url:
            product_info['image_url'] = image_url
        
        # Convert to JSON string for QR code
        content = json.dumps(product_info)
        
        # Map error correction levels
        error_map = {
            'L': qrcode.constants.ERROR_CORRECT_L,
            'M': qrcode.constants.ERROR_CORRECT_M,
            'Q': qrcode.constants.ERROR_CORRECT_Q,
            'H': qrcode.constants.ERROR_CORRECT_H
        }
        error_level = error_map.get(error_correction, qrcode.constants.ERROR_CORRECT_M)
        
        # Create QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=error_level,
            box_size=10,
            border=4,
        )
        qr.add_data(content)
        qr.make(fit=True)
        
        # Create image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Resize if needed
        if size != 300:
            img = img.resize((size, size), Image.Resampling.LANCZOS)
        
        # Convert to base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        return jsonify({
            'success': True,
            'qr_code': f'data:image/png;base64,{img_str}',
            'product_info': product_info
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# GIF Maker Routes

@app.route('/create-gif', methods=['POST'])
def create_gif():
    """Create GIF from video"""
    try:
        if 'video' not in request.files:
            return jsonify({'error': 'No video file provided'}), 400
        
        video_file = request.files['video']
        if video_file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Get settings
        start_time = float(request.form.get('start_time', 0))
        duration = float(request.form.get('duration', 5))
        width = int(request.form.get('width', 640))
        fps = int(request.form.get('fps', 15))
        quality = request.form.get('quality', 'medium')
        loop = int(request.form.get('loop', 0))
        
        # Caption settings
        caption_text = request.form.get('caption_text', '')
        caption_position = request.form.get('caption_position', 'center')
        caption_size = int(request.form.get('caption_size', 32))
        caption_color = request.form.get('caption_color', '#ffffff')
        caption_bg = request.form.get('caption_bg', 'none')
        
        # Create job
        job_id = str(uuid.uuid4())
        
        # Save uploaded file
        upload_path = Path(app.config['UPLOAD_FOLDER']) / job_id
        upload_path.mkdir(exist_ok=True)
        
        filename = secure_filename(video_file.filename)
        video_path = upload_path / filename
        video_file.save(str(video_path))
        
        # Initialize job
        jobs[job_id] = {
            'status': 'processing',
            'progress': 0,
            'message': 'Starting GIF generation...',
            'type': 'gif_creation',
            'can_cancel': True
        }
        
        # Start processing in background
        thread = Thread(
            target=generate_gif,
            args=(job_id, str(video_path), start_time, duration, width, fps, quality, loop,
                  caption_text, caption_position, caption_size, caption_color, caption_bg)
        )
        thread.start()
        
        return jsonify({'job_id': job_id, 'message': 'GIF generation started'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def generate_gif(job_id, video_path, start_time, duration, width, fps, quality, loop,
                 caption_text, caption_position, caption_size, caption_color, caption_bg):
    """Generate GIF from video with optional caption"""
    try:
        output_dir = Path(app.config['OUTPUT_FOLDER']) / job_id
        output_dir.mkdir(exist_ok=True)
        
        jobs[job_id]['progress'] = 10
        jobs[job_id]['message'] = 'Processing video...'
        
        # Output GIF path
        output_gif = output_dir / 'animated.gif'
        
        # Build FFmpeg command for palette generation
        # Optimize for WhatsApp: reduce colors for smaller file size
        jobs[job_id]['progress'] = 30
        jobs[job_id]['message'] = 'Generating optimized color palette...'
        
        palette_path = output_dir / 'palette.png'
        # Use fewer colors for better compression (WhatsApp compatible)
        max_colors = 128 if quality == 'low' else 256 if quality == 'medium' else 256
        palette_cmd = ['ffmpeg', '-y', '-ss', str(start_time), '-t', str(duration), '-i', str(video_path),
                      '-vf', f'fps={fps},scale={width}:-1:flags=lanczos,palettegen=max_colors={max_colors}:reserve_transparent=0']
        palette_cmd.append(str(palette_path))
        
        palette_result = subprocess.run(palette_cmd, capture_output=True, text=True, check=False)
        if palette_result.returncode != 0:
            raise Exception(f'Palette generation failed: {palette_result.stderr[:200]}')
        
        jobs[job_id]['progress'] = 60
        jobs[job_id]['message'] = 'Creating GIF...'
        
        # Build final GIF command
        scale_filter = f'fps={fps},scale={width}:-1:flags=lanczos'
        
        # Add caption if provided
        if caption_text:
            # Escape single quotes in caption text
            escaped_text = caption_text.replace("'", "\\'")
            
            # Determine vertical position
            if caption_position == 'top':
                y_pos = '50'
            elif caption_position == 'bottom':
                y_pos = 'h-th-50'
            else:  # center
                y_pos = '(h-text_h)/2'
            
            # Convert hex color to format FFmpeg expects
            hex_color = caption_color.lstrip('#')
            
            # Build text filter
            text_filter = f"drawtext=text='{escaped_text}':fontsize={caption_size}:fontcolor={hex_color}:x=(w-text_w)/2:y={y_pos}"
            
            # Add background box if needed
            if caption_bg == 'black':
                text_filter += ':box=1:boxcolor=black@0.8:boxborderw=10'
            elif caption_bg == 'white':
                text_filter += ':box=1:boxcolor=white@0.8:boxborderw=10'
            elif caption_bg == 'semi':
                text_filter += ':box=1:boxcolor=black@0.5:boxborderw=10'
            
            final_filter = f'{scale_filter},{text_filter},paletteuse'
        else:
            final_filter = f'{scale_filter},paletteuse'
        
        # Create final GIF optimized for WhatsApp
        # WhatsApp requires: proper GIF format, file size < 16MB (preferably < 8MB), infinite loop
        final_cmd = ['ffmpeg', '-y', '-ss', str(start_time), '-t', str(duration), '-i', str(video_path),
                    '-i', str(palette_path), '-lavfi', final_filter]
        
        # WhatsApp requires infinite loop (-1) for proper GIF animation
        # Always use -1 for infinite loop (WhatsApp compatible)
        final_cmd.extend(['-loop', '-1'])
        
        # Ensure proper GIF format
        final_cmd.extend(['-f', 'gif'])
        
        # Optimize for WhatsApp: ensure proper animated GIF format
        # Use transdiff for better compression while maintaining animation
        final_cmd.extend(['-gifflags', '+transdiff'])
        
        # Ensure palette-based format (required for animated GIFs)
        final_cmd.extend(['-pix_fmt', 'pal8'])
        
        final_cmd.append(str(output_gif))
        
        # Run FFmpeg with error checking
        result = subprocess.run(final_cmd, capture_output=True, text=True, check=False)
        
        if result.returncode != 0:
            error_msg = result.stderr if result.stderr else 'Unknown FFmpeg error'
            raise Exception(f'FFmpeg failed: {error_msg[:200]}')
        
        # Clean up palette
        if palette_path.exists():
            palette_path.unlink()
        
        jobs[job_id]['progress'] = 90
        jobs[job_id]['message'] = 'Optimizing GIF for WhatsApp...'
        
        # Verify and optimize GIF if needed
        if not output_gif.exists() or output_gif.stat().st_size == 0:
            raise Exception('GIF file was not created or is empty')
        
        # Check file size - WhatsApp limit is ~16MB, but smaller is better
        file_size_mb = output_gif.stat().st_size / (1024 * 1024)
        
        # If file is too large for WhatsApp, try to optimize further
        if file_size_mb > 15:
            jobs[job_id]['message'] = f'GIF created but large ({file_size_mb:.1f}MB). Optimizing for WhatsApp...'
            
            # Try to reduce file size by re-encoding with more compression
            optimized_gif = output_dir / 'animated_optimized.gif'
            optimize_cmd = ['ffmpeg', '-y', '-i', str(output_gif), 
                          '-vf', f'fps={fps},scale={width}:-1:flags=lanczos',
                          '-loop', '-1', '-f', 'gif', str(optimized_gif)]
            
            optimize_result = subprocess.run(optimize_cmd, capture_output=True, text=True, check=False)
            if optimize_result.returncode == 0 and optimized_gif.exists():
                optimized_size = optimized_gif.stat().st_size / (1024 * 1024)
                if optimized_size < file_size_mb:
                    output_gif.unlink()
                    optimized_gif.rename(output_gif)
                    file_size_mb = optimized_size
        
        if file_size_mb > 16:
            jobs[job_id]['message'] = f'GIF created ({file_size_mb:.1f}MB) - Too large for WhatsApp! Try reducing duration, FPS, or width.'
        elif file_size_mb > 8:
            jobs[job_id]['message'] = f'GIF created ({file_size_mb:.1f}MB) - May be slow on WhatsApp. Optimized for sharing.'
        else:
            jobs[job_id]['message'] = f'GIF created successfully! ({file_size_mb:.1f}MB) - WhatsApp ready!'
        
        jobs[job_id]['progress'] = 100
        
        # Ensure file has .gif extension for WhatsApp compatibility
        final_output = output_gif
        if not final_output.suffix.lower() == '.gif':
            final_output = output_dir / 'animated.gif'
            if output_gif != final_output:
                output_gif.rename(final_output)
        
        # Verify GIF format is correct (check file header)
        try:
            with open(final_output, 'rb') as f:
                header = f.read(6)
                # GIF files should start with "GIF89a" or "GIF87a"
                if not (header.startswith(b'GIF89a') or header.startswith(b'GIF87a')):
                    raise Exception('Generated file is not a valid GIF format')
        except Exception as e:
            raise Exception(f'GIF validation failed: {str(e)}')
        
        jobs[job_id].update({
            'status': 'completed',
            'progress': 100,
            'output_path': str(final_output),
            'output_filename': final_output.name,
            'message': jobs[job_id]['message']
        })
    
    except Exception as e:
        error_msg = str(e)
        jobs[job_id].update({
            'status': 'failed',
            'progress': 0,
            'message': f'GIF generation failed: {error_msg}'
        })


# Duplicate File Finder Routes

@app.route('/find-duplicates', methods=['POST'])
def find_duplicates():
    """Find duplicate files in uploaded folder"""
    try:
        if 'files[]' not in request.files:
            return jsonify({'error': 'No files provided'}), 400
        
        files = request.files.getlist('files[]')
        if not files or files[0].filename == '':
            return jsonify({'error': 'No files selected'}), 400
        
        # Get scan options
        scan_method = request.form.get('scan_method', 'hash')
        min_file_size = int(request.form.get('min_file_size', 0)) * 1024  # Convert KB to bytes
        file_types = request.form.get('file_types', '').split(',') if request.form.get('file_types') else []
        file_types = [ft.strip().lower() for ft in file_types if ft.strip()]
        
        # Create job
        job_id = str(uuid.uuid4())
        
        # Save uploaded files
        upload_path = Path(app.config['UPLOAD_FOLDER']) / job_id
        upload_path.mkdir(exist_ok=True)
        
        file_paths = []
        for file in files:
            if file.filename:
                filename = secure_filename(file.filename)
                file_path = upload_path / filename
                file.save(str(file_path))
                file_paths.append(str(file_path))
        
        # Initialize job
        jobs[job_id] = add_job_timestamps({
            'status': 'processing',
            'progress': 0,
            'message': 'Starting duplicate scan...',
            'type': 'duplicate_scan',
            'can_cancel': True
        })
        
        # Start scanning in background
        thread = Thread(
            target=scan_duplicates,
            args=(job_id, file_paths, scan_method, min_file_size, file_types)
        )
        thread.start()
        
        return jsonify({'job_id': job_id, 'message': 'Duplicate scan started'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def scan_duplicates(job_id, file_paths, scan_method, min_file_size, file_types):
    """Scan for duplicate files"""
    import hashlib
    
    try:
        jobs[job_id]['progress'] = 10
        jobs[job_id]['message'] = 'Analyzing files...'
        
        # Filter files by size and type
        valid_files = []
        for file_path in file_paths:
            path_obj = Path(file_path)
            if not path_obj.exists():
                continue
            
            file_size = path_obj.stat().st_size
            if file_size < min_file_size:
                continue
            
            if file_types:
                ext = path_obj.suffix.lower().lstrip('.')
                if ext not in file_types:
                    continue
            
            valid_files.append(path_obj)
        
        jobs[job_id]['progress'] = 20
        jobs[job_id]['message'] = f'Scanning {len(valid_files)} files...'
        
        # Group files by method
        file_groups = {}
        total_files = len(valid_files)
        
        for i, file_path in enumerate(valid_files):
            if jobs[job_id].get('cancelled', False):
                raise Exception('Scan cancelled by user')
            
            progress = 20 + int((i / total_files) * 70)
            jobs[job_id]['progress'] = progress
            jobs[job_id]['message'] = f'Processing file {i+1} of {total_files}...'
            
            file_size = file_path.stat().st_size
            
            if scan_method == 'hash':
                # Calculate MD5 hash
                hash_md5 = hashlib.md5()
                try:
                    with open(file_path, 'rb') as f:
                        for chunk in iter(lambda: f.read(4096), b''):
                            hash_md5.update(chunk)
                    file_key = hash_md5.hexdigest()
                except Exception as e:
                    continue
            elif scan_method == 'name_size':
                # Use filename + size
                file_key = f"{file_path.name}_{file_size}"
            else:  # size only
                file_key = str(file_size)
            
            if file_key not in file_groups:
                file_groups[file_key] = []
            
            file_groups[file_key].append({
                'path': str(file_path),
                'name': file_path.name,
                'size': file_size
            })
        
        jobs[job_id]['progress'] = 95
        jobs[job_id]['message'] = 'Finding duplicates...'
        
        # Find groups with duplicates (more than 1 file)
        duplicate_groups = []
        unique_files = []  # Files to keep (one from each duplicate group + all non-duplicates)
        duplicate_file_paths = set()  # Track all duplicate file paths
        
        for file_key, files in file_groups.items():
            if len(files) > 1:
                # This is a duplicate group - keep the first file, mark others as duplicates
                duplicate_groups.append({
                    'key': file_key,
                    'files': files,
                    'size': files[0]['size'],
                    'count': len(files)
                })
                # Keep first file, mark rest as duplicates
                unique_files.append(files[0])
                for dup_file in files[1:]:
                    duplicate_file_paths.add(dup_file['path'])
            else:
                # This is a unique file (no duplicates)
                unique_files.append(files[0])
        
        jobs[job_id]['progress'] = 100
        jobs[job_id].update({
            'status': 'completed',
            'progress': 100,
            'duplicate_groups': duplicate_groups,
            'unique_files': unique_files,  # Store unique files for clean folder creation
            'duplicate_file_paths': list(duplicate_file_paths),  # Store duplicate paths
            'message': f'Found {len(duplicate_groups)} duplicate groups'
        })
    
    except Exception as e:
        jobs[job_id].update({
            'status': 'failed',
            'progress': 0,
            'message': f'Scan failed: {str(e)}'
        })


@app.route('/delete-duplicates', methods=['POST'])
def delete_duplicates():
    """Delete selected duplicate files"""
    try:
        data = request.json
        files_to_delete = data.get('files', [])
        
        if not files_to_delete:
            return jsonify({'error': 'No files selected'}), 400
        
        deleted_count = 0
        errors = []
        
        for file_info in files_to_delete:
            file_path = file_info.get('path')
            if not file_path:
                continue
            
            try:
                path_obj = Path(file_path)
                if path_obj.exists():
                    path_obj.unlink()
                    deleted_count += 1
            except Exception as e:
                errors.append(f"Failed to delete {file_info.get('name', 'file')}: {str(e)}")
        
        return jsonify({
            'success': True,
            'deleted_count': deleted_count,
            'errors': errors,
            'message': f'Successfully deleted {deleted_count} file(s)'
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/create-clean-folder', methods=['POST'])
def create_clean_folder():
    """Create a new folder with only unique files (no duplicates)"""
    try:
        data = request.json
        job_id = data.get('job_id')
        
        if not job_id or job_id not in jobs:
            return jsonify({'error': 'Invalid job ID'}), 400
        
        job = jobs[job_id]
        if job['status'] != 'completed':
            return jsonify({'error': 'Scan not completed'}), 400
        
        unique_files = job.get('unique_files', [])
        if not unique_files:
            return jsonify({'error': 'No unique files found'}), 400
        
        # Create new job for folder creation
        new_job_id = str(uuid.uuid4())
        jobs[new_job_id] = {
            'status': 'processing',
            'progress': 0,
            'message': 'Creating clean folder...',
            'type': 'clean_folder',
            'can_cancel': True
        }
        
        # Start folder creation in background
        thread = Thread(
            target=create_clean_folder_task,
            args=(new_job_id, unique_files, job_id)
        )
        thread.start()
        
        return jsonify({'job_id': new_job_id, 'message': 'Creating clean folder...'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def create_clean_folder_task(new_job_id, unique_files, original_job_id):
    """Create a folder with only unique files"""
    import shutil
    
    try:
        jobs[new_job_id]['progress'] = 10
        jobs[new_job_id]['message'] = 'Preparing clean folder...'
        
        # Create output folder
        output_dir = Path(app.config['OUTPUT_FOLDER']) / new_job_id
        output_dir.mkdir(exist_ok=True)
        
        clean_folder = output_dir / 'clean_folder_no_duplicates'
        clean_folder.mkdir(exist_ok=True)
        
        jobs[new_job_id]['progress'] = 20
        jobs[new_job_id]['message'] = f'Copying {len(unique_files)} unique files...'
        
        copied_count = 0
        errors = []
        total_files = len(unique_files)
        
        for i, file_info in enumerate(unique_files):
            if jobs[new_job_id].get('cancelled', False):
                raise Exception('Folder creation cancelled by user')
            
            progress = 20 + int((i / total_files) * 75)
            jobs[new_job_id]['progress'] = progress
            jobs[new_job_id]['message'] = f'Copying file {i+1} of {total_files}...'
            
            source_path = Path(file_info['path'])
            if not source_path.exists():
                errors.append(f"Source file not found: {file_info['name']}")
                continue
            
            # Create destination path
            dest_path = clean_folder / file_info['name']
            
            # Handle filename conflicts
            counter = 1
            original_dest = dest_path
            while dest_path.exists():
                stem = original_dest.stem
                suffix = original_dest.suffix
                dest_path = clean_folder / f"{stem}_{counter}{suffix}"
                counter += 1
            
            try:
                # Copy file
                shutil.copy2(source_path, dest_path)
                copied_count += 1
            except Exception as e:
                errors.append(f"Failed to copy {file_info['name']}: {str(e)}")
        
        jobs[new_job_id]['progress'] = 100
        
        # Create a ZIP file of the clean folder for easy download
        zip_path = output_dir / 'clean_folder_no_duplicates.zip'
        jobs[new_job_id]['message'] = 'Creating ZIP archive...'
        
        try:
            shutil.make_archive(str(zip_path).replace('.zip', ''), 'zip', str(clean_folder))
            zip_created = True
        except Exception as e:
            zip_created = False
            errors.append(f"Failed to create ZIP: {str(e)}")
        
        jobs[new_job_id].update({
            'status': 'completed',
            'progress': 100,
            'output_path': str(zip_path) if zip_created else str(clean_folder),
            'output_filename': 'clean_folder_no_duplicates.zip' if zip_created else 'clean_folder_no_duplicates',
            'clean_folder_path': str(clean_folder),
            'copied_count': copied_count,
            'errors': errors,
            'message': f'Successfully created clean folder with {copied_count} unique files!'
        })
    
    except Exception as e:
        jobs[new_job_id].update({
            'status': 'failed',
            'progress': 0,
            'message': f'Failed to create clean folder: {str(e)}'
        })


# Excel/CSV Duplicate Records Routes

@app.route('/find-excel-duplicates', methods=['POST'])
def find_excel_duplicates():
    """Find duplicate records in Excel/CSV file"""
    if not PANDAS_AVAILABLE:
        return jsonify({'error': 'pandas library is required. Please install: pip install pandas openpyxl'}), 500
    
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Get columns to check
        columns_to_check = request.form.get('columns', '')
        columns_to_check = json.loads(columns_to_check) if columns_to_check else []
        keep_first = request.form.get('keep_first', 'true') == 'true'
        
        # Create job
        job_id = str(uuid.uuid4())
        
        # Save uploaded file
        upload_path = Path(app.config['UPLOAD_FOLDER']) / job_id
        upload_path.mkdir(exist_ok=True)
        
        filename = secure_filename(file.filename)
        file_path = upload_path / filename
        file.save(str(file_path))
        
        # Initialize job
        jobs[job_id] = add_job_timestamps({
            'status': 'processing',
            'progress': 0,
            'message': 'Reading file...',
            'type': 'excel_duplicate_scan',
            'can_cancel': True
        })
        
        # Start scanning in background
        thread = Thread(
            target=scan_excel_duplicates,
            args=(job_id, str(file_path), columns_to_check, keep_first)
        )
        thread.start()
        
        return jsonify({'job_id': job_id, 'message': 'Duplicate scan started'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def scan_excel_duplicates(job_id, file_path, columns_to_check, keep_first):
    """Scan for duplicate records in Excel/CSV file"""
    try:
        jobs[job_id]['progress'] = 10
        jobs[job_id]['message'] = 'Reading file...'
        
        # Read file based on extension
        file_ext = Path(file_path).suffix.lower()
        
        if file_ext == '.csv':
            df = pd.read_csv(file_path)
        elif file_ext in ['.xlsx', '.xls']:
            df = pd.read_excel(file_path)
        else:
            raise Exception(f'Unsupported file format: {file_ext}')
        
        jobs[job_id]['progress'] = 30
        jobs[job_id]['message'] = 'Analyzing data...'
        
        # Get all columns if none specified
        if not columns_to_check:
            columns_to_check = list(df.columns)
        
        # Filter to only existing columns
        columns_to_check = [col for col in columns_to_check if col in df.columns]
        
        if not columns_to_check:
            raise Exception('No valid columns selected')
        
        jobs[job_id]['progress'] = 50
        jobs[job_id]['message'] = 'Finding duplicates...'
        
        # Find duplicates based on selected columns
        duplicate_mask = df.duplicated(subset=columns_to_check, keep=False)
        duplicates_df = df[duplicate_mask].copy()
        
        # Find unique records (first occurrence of each duplicate group + non-duplicates)
        if keep_first:
            unique_df = df.drop_duplicates(subset=columns_to_check, keep='first')
        else:
            unique_df = df.drop_duplicates(subset=columns_to_check, keep='last')
        
        # Group duplicates for display
        duplicate_groups = []
        duplicate_indices = duplicates_df.index.tolist()
        
        # Group by the selected columns
        grouped = duplicates_df.groupby(columns_to_check)
        
        for (key_values), group_df in grouped:
            if len(group_df) > 1:
                # Convert key_values to dict if it's a tuple
                if isinstance(key_values, tuple):
                    key_dict = dict(zip(columns_to_check, key_values))
                else:
                    key_dict = {columns_to_check[0]: key_values}
                
                duplicate_groups.append({
                    'key': key_dict,
                    'rows': group_df.to_dict('records'),
                    'indices': group_df.index.tolist(),
                    'count': len(group_df)
                })
        
        jobs[job_id]['progress'] = 90
        jobs[job_id]['message'] = 'Creating cleaned file (no duplicates)...'
        
        # Automatically create cleaned file (without duplicates)
        output_dir = Path(app.config['OUTPUT_FOLDER']) / job_id
        output_dir.mkdir(exist_ok=True)
        
        # Get original file extension
        file_ext = Path(file_path).suffix.lower()
        cleaned_filename = f'cleaned_no_duplicates{file_ext}'
        cleaned_path = output_dir / cleaned_filename
        
        # Export cleaned file (unique records only)
        if file_ext == '.csv':
            unique_df.to_csv(cleaned_path, index=False)
        else:
            unique_df.to_excel(cleaned_path, index=False)
        
        jobs[job_id]['progress'] = 100
        
        # Store results
        jobs[job_id].update({
            'status': 'completed',
            'progress': 100,
            'duplicate_groups': duplicate_groups,
            'total_records': len(df),
            'unique_records': len(unique_df),
            'duplicate_records': len(duplicates_df),
            'columns_checked': columns_to_check,
            'file_path': file_path,
            'original_df': df.to_dict('records'),  # Store for export
            'unique_df': unique_df.to_dict('records'),
            'duplicates_df': duplicates_df.to_dict('records'),
            'output_path': str(cleaned_path),  # Automatically created cleaned file
            'output_filename': cleaned_filename,
            'message': f'Found {len(duplicate_groups)} duplicate groups. Cleaned file created with {len(unique_df)} unique records!'
        })
    
    except Exception as e:
        jobs[job_id].update({
            'status': 'failed',
            'progress': 0,
            'message': f'Scan failed: {str(e)}'
        })


@app.route('/export-excel-duplicates', methods=['POST'])
def export_excel_duplicates():
    """Export Excel/CSV results"""
    if not PANDAS_AVAILABLE:
        return jsonify({'error': 'pandas library is required'}), 500
    
    try:
        data = request.json
        job_id = data.get('job_id')
        export_type = data.get('export_type', 'unique')  # 'unique', 'duplicates', 'cleaned'
        
        if not job_id or job_id not in jobs:
            return jsonify({'error': 'Invalid job ID'}), 400
        
        job = jobs[job_id]
        if job['status'] != 'completed':
            return jsonify({'error': 'Scan not completed'}), 400
        
        # Create new job for export
        export_job_id = str(uuid.uuid4())
        jobs[export_job_id] = {
            'status': 'processing',
            'progress': 0,
            'message': 'Creating export file...',
            'type': 'excel_export',
            'can_cancel': False
        }
        
        # Start export in background
        thread = Thread(
            target=export_excel_file,
            args=(export_job_id, job, export_type)
        )
        thread.start()
        
        return jsonify({'job_id': export_job_id, 'message': 'Export started'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def export_excel_file(export_job_id, job, export_type):
    """Export Excel/CSV file"""
    try:
        jobs[export_job_id]['progress'] = 20
        jobs[export_job_id]['message'] = 'Preparing export...'
        
        # Create output directory
        output_dir = Path(app.config['OUTPUT_FOLDER']) / export_job_id
        output_dir.mkdir(exist_ok=True)
        
        jobs[export_job_id]['progress'] = 50
        jobs[export_job_id]['message'] = 'Creating file...'
        
        # Get original file extension
        original_file = Path(job['file_path'])
        file_ext = original_file.suffix.lower()
        
        # Create DataFrame based on export type
        if export_type == 'unique':
            df = pd.DataFrame(job['unique_df'])
            filename = f'unique_records{file_ext}'
        elif export_type == 'duplicates':
            df = pd.DataFrame(job['duplicates_df'])
            filename = f'duplicate_records{file_ext}'
        else:  # cleaned (one copy of each)
            df = pd.DataFrame(job['unique_df'])
            filename = f'cleaned_file{file_ext}'
        
        output_path = output_dir / filename
        
        # Export based on file type
        if file_ext == '.csv':
            df.to_csv(output_path, index=False)
        else:
            df.to_excel(output_path, index=False)
        
        jobs[export_job_id]['progress'] = 100
        jobs[export_job_id].update({
            'status': 'completed',
            'progress': 100,
            'output_path': str(output_path),
            'output_filename': filename,
            'message': f'Export completed: {filename}'
        })
    
    except Exception as e:
        jobs[export_job_id].update({
            'status': 'failed',
            'progress': 0,
            'message': f'Export failed: {str(e)}'
        })


@app.route('/get-excel-columns', methods=['POST'])
def get_excel_columns():
    """Get column names from uploaded Excel/CSV file"""
    if not PANDAS_AVAILABLE:
        return jsonify({'error': 'pandas library is required'}), 500
    
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Save temporarily
        temp_path = Path(app.config['UPLOAD_FOLDER']) / 'temp' / secure_filename(file.filename)
        temp_path.parent.mkdir(exist_ok=True)
        file.save(str(temp_path))
        
        # Read file
        file_ext = Path(temp_path).suffix.lower()
        if file_ext == '.csv':
            df = pd.read_csv(temp_path)
        elif file_ext in ['.xlsx', '.xls']:
            df = pd.read_excel(temp_path)
        else:
            return jsonify({'error': f'Unsupported file format: {file_ext}'}), 400
        
        # Get columns
        columns = list(df.columns)
        row_count = len(df)
        
        # Clean up temp file
        try:
            temp_path.unlink()
        except:
            pass
        
        return jsonify({
            'columns': columns,
            'row_count': row_count,
            'message': f'File loaded: {row_count} rows, {len(columns)} columns'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# File Encryptor Routes

# Security constants
PBKDF2_ITERATIONS = 600000  # OWASP recommended minimum (increased from 100,000)
SALT_SIZE = 32  # 32 bytes = 256 bits
HMAC_KEY_SIZE = 32  # 32 bytes = 256 bits
PASSWORD_VERIFIER_SIZE = 32  # Size of password verifier hash
TOOL_IDENTIFIER = b'RKIEH_ENCRYPT_V2'  # Tool identifier (16 bytes, padded)
TOOL_IDENTIFIER_SIZE = 16  # Size of tool identifier

def derive_key_from_password(password: str, salt: bytes) -> bytes:
    """Derive a Fernet key from a password using PBKDF2 with high iteration count"""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=PBKDF2_ITERATIONS,  # Increased for better security
    )
    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
    return key

def generate_hmac(data: bytes, key: bytes) -> bytes:
    """Generate HMAC for data integrity verification"""
    h = hmac.HMAC(key, hashes.SHA256())
    h.update(data)
    return h.finalize()

def verify_hmac(data: bytes, key: bytes, expected_hmac: bytes) -> bool:
    """Verify HMAC for data integrity"""
    try:
        h = hmac.HMAC(key, hashes.SHA256())
        h.update(data)
        h.verify(expected_hmac)
        return True
    except:
        return False

def generate_password_verifier(password: str, salt: bytes) -> bytes:
    """Generate a password verifier hash to verify the password during decryption"""
    # Use a separate key derivation for password verification
    verifier_key = derive_key_from_password(password + '_verify', salt)[:PASSWORD_VERIFIER_SIZE]
    # Create a simple verifier by hashing password + salt + tool identifier
    verifier_data = password.encode() + salt + TOOL_IDENTIFIER
    verifier_hash = hashes.Hash(hashes.SHA256())
    verifier_hash.update(verifier_data)
    verifier_hash.update(verifier_key)
    return verifier_hash.finalize()[:PASSWORD_VERIFIER_SIZE]

def verify_password(password: str, salt: bytes, stored_verifier: bytes) -> bool:
    """Verify that the password matches the stored verifier"""
    try:
        computed_verifier = generate_password_verifier(password, salt)
        return computed_verifier == stored_verifier
    except:
        return False

def derive_key_old_format(password: str) -> bytes:
    """Derive key using old format (for backward compatibility with files encrypted before security upgrade)"""
    old_salt = b'RKIEH_SOLUTIONS_ENCRYPT_SALT_2024'
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=old_salt,
        iterations=100000,  # Old iteration count
    )
    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
    return key


@app.route('/encrypt-file', methods=['POST'])
def encrypt_file():
    """Encrypt a file with password"""
    if not CRYPTOGRAPHY_AVAILABLE:
        return jsonify({'error': 'cryptography library is required. Please install: pip install cryptography'}), 500
    
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        password = request.form.get('password', '')
        if not password or len(password) < 4:
            return jsonify({'error': 'Password must be at least 4 characters long'}), 400
        
        # Create job
        job_id = str(uuid.uuid4())
        
        # Save uploaded file
        upload_path = Path(app.config['UPLOAD_FOLDER']) / job_id
        upload_path.mkdir(exist_ok=True)
        
        original_filename = secure_filename(file.filename)
        file_path = upload_path / original_filename
        file.save(str(file_path))
        
        # Generate random salt for this encryption (unique per file)
        salt = secrets.token_bytes(SALT_SIZE)
        
        # Derive encryption key from password using salt
        encryption_key = derive_key_from_password(password, salt)
        fernet = Fernet(encryption_key)
        
        # Derive HMAC key from password (separate key for integrity)
        hmac_key = derive_key_from_password(password + '_hmac', salt)[:HMAC_KEY_SIZE]
        
        # Read file content
        with open(file_path, 'rb') as f:
            file_data = f.read()
        
        # Encrypt file
        encrypted_data = fernet.encrypt(file_data)
        
        # Generate HMAC for integrity verification
        data_hmac = generate_hmac(encrypted_data, hmac_key)
        
        # Generate password verifier to ensure only correct password can decrypt
        password_verifier = generate_password_verifier(password, salt)
        
        # Prepare tool identifier (pad to fixed size)
        tool_id = TOOL_IDENTIFIER.ljust(TOOL_IDENTIFIER_SIZE, b'\x00')[:TOOL_IDENTIFIER_SIZE]
        
        # Save encrypted file with format: [tool_id (16 bytes)][salt (32 bytes)][password_verifier (32 bytes)][hmac (32 bytes)][encrypted data]
        output_path = Path(app.config['OUTPUT_FOLDER']) / job_id
        output_path.mkdir(exist_ok=True)
        
        encrypted_filename = original_filename + '.encrypted'
        encrypted_file_path = output_path / encrypted_filename
        
        with open(encrypted_file_path, 'wb') as f:
            f.write(tool_id)  # Write tool identifier first
            f.write(salt)  # Write salt second
            f.write(password_verifier)  # Write password verifier third
            f.write(data_hmac)  # Write HMAC fourth
            f.write(encrypted_data)  # Write encrypted data last
        
        # Get file size
        file_size = encrypted_file_path.stat().st_size
        
        # Clean up original file
        try:
            file_path.unlink()
            upload_path.rmdir()
        except:
            pass
        
        # Create download URL
        download_url = f'/download/{job_id}'
        
        # Store job info
        jobs[job_id] = add_job_timestamps({
            'status': 'completed',
            'type': 'file_encryption',
            'output_path': str(encrypted_file_path),
            'output_filename': encrypted_filename
        })
        
        return jsonify({
            'success': True,
            'message': 'File encrypted successfully',
            'filename': encrypted_filename,
            'file_size': file_size,
            'download_url': download_url
        })
        
    except Exception as e:
        return jsonify({'error': f'Encryption failed: {str(e)}'}), 500


@app.route('/decrypt-file', methods=['POST'])
def decrypt_file():
    """Decrypt a file with password"""
    if not CRYPTOGRAPHY_AVAILABLE:
        return jsonify({'error': 'cryptography library is required. Please install: pip install cryptography'}), 500
    
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        password = request.form.get('password', '')
        if not password:
            return jsonify({'error': 'Password is required'}), 400
        
        # Create job
        job_id = str(uuid.uuid4())
        
        # Save uploaded file
        upload_path = Path(app.config['UPLOAD_FOLDER']) / job_id
        upload_path.mkdir(exist_ok=True)
        
        encrypted_filename = secure_filename(file.filename)
        encrypted_file_path = upload_path / encrypted_filename
        file.save(str(encrypted_file_path))
        
        # Read encrypted file
        with open(encrypted_file_path, 'rb') as f:
            file_data = f.read()
        
        decrypted_data = None
        decryption_error = None
        
        # Check if file has new format v2 (tool_id + salt + password_verifier + HMAC + data)
        min_v2_format_size = TOOL_IDENTIFIER_SIZE + SALT_SIZE + PASSWORD_VERIFIER_SIZE + HMAC_KEY_SIZE + 50
        
        if len(file_data) >= min_v2_format_size:
            # Check for tool identifier
            file_tool_id = file_data[:TOOL_IDENTIFIER_SIZE].rstrip(b'\x00')
            
            # Try new format v2 first (with tool identifier, salt, password verifier and HMAC) - ONLY THIS TOOL
            if file_tool_id == TOOL_IDENTIFIER:
                try:
                    # Extract salt, password verifier, HMAC, and encrypted data
                    salt = file_data[TOOL_IDENTIFIER_SIZE:TOOL_IDENTIFIER_SIZE + SALT_SIZE]
                    stored_password_verifier = file_data[TOOL_IDENTIFIER_SIZE + SALT_SIZE:TOOL_IDENTIFIER_SIZE + SALT_SIZE + PASSWORD_VERIFIER_SIZE]
                    stored_hmac = file_data[TOOL_IDENTIFIER_SIZE + SALT_SIZE + PASSWORD_VERIFIER_SIZE:TOOL_IDENTIFIER_SIZE + SALT_SIZE + PASSWORD_VERIFIER_SIZE + HMAC_KEY_SIZE]
                    encrypted_data = file_data[TOOL_IDENTIFIER_SIZE + SALT_SIZE + PASSWORD_VERIFIER_SIZE + HMAC_KEY_SIZE:]
                    
                    # FIRST: Verify password matches the stored verifier (MUST be correct password from encryption)
                    if not verify_password(password, salt, stored_password_verifier):
                        return jsonify({'error': 'Password verification failed. This file was encrypted with this tool, but the password is incorrect.'}), 400
                    
                    # Derive encryption key from password using salt
                    encryption_key = derive_key_from_password(password, salt)
                    fernet = Fernet(encryption_key)
                    
                    # Derive HMAC key
                    hmac_key = derive_key_from_password(password + '_hmac', salt)[:HMAC_KEY_SIZE]
                    
                    # Verify HMAC for integrity
                    if not verify_hmac(encrypted_data, hmac_key, stored_hmac):
                        return jsonify({'error': 'File integrity check failed. The file may have been tampered with.'}), 400
                    
                    # Decrypt file
                    decrypted_data = fernet.decrypt(encrypted_data)
                except Exception as e:
                    return jsonify({'error': 'Decryption failed. This file was encrypted with this tool, but the password may be incorrect or the file may be corrupted.'}), 400
        
        # If v2 format didn't work, try v1 format (salt + HMAC, no tool identifier) for backward compatibility
        if decrypted_data is None and len(file_data) >= SALT_SIZE + HMAC_KEY_SIZE + 50:
            # Check if it's NOT v2 format (doesn't start with tool identifier)
            file_tool_id_check = file_data[:TOOL_IDENTIFIER_SIZE].rstrip(b'\x00')
            if file_tool_id_check != TOOL_IDENTIFIER:
                try:
                    # Extract salt, HMAC, and encrypted data (v1 format)
                    salt = file_data[:SALT_SIZE]
                    stored_hmac = file_data[SALT_SIZE:SALT_SIZE + HMAC_KEY_SIZE]
                    encrypted_data = file_data[SALT_SIZE + HMAC_KEY_SIZE:]
                    
                    # Derive encryption key from password using salt
                    encryption_key = derive_key_from_password(password, salt)
                    fernet = Fernet(encryption_key)
                    
                    # Derive HMAC key
                    hmac_key = derive_key_from_password(password + '_hmac', salt)[:HMAC_KEY_SIZE]
                    
                    # Verify HMAC for integrity
                    if verify_hmac(encrypted_data, hmac_key, stored_hmac):
                        # Decrypt file
                        decrypted_data = fernet.decrypt(encrypted_data)
                except Exception:
                    pass
        
        # If still not successful, try old format (no salt, no HMAC, fixed salt) for backward compatibility
        if decrypted_data is None:
            try:
                old_key = derive_key_old_format(password)
                old_fernet = Fernet(old_key)
                decrypted_data = old_fernet.decrypt(file_data)
            except Exception:
                return jsonify({'error': 'Decryption failed. This file was not encrypted with this tool, the password may be incorrect, or the file may be corrupted.'}), 400
        
        # Get original filename (remove .encrypted extension if present)
        if encrypted_filename.endswith('.encrypted'):
            original_filename = encrypted_filename[:-10]  # Remove '.encrypted'
        else:
            # If no .encrypted extension, try to determine original name
            # For files encrypted with this tool, we'll use the original name
            # Otherwise, add _decrypted suffix
            file_stem = Path(encrypted_filename).stem
            file_ext = Path(encrypted_filename).suffix
            # Try to preserve original extension if it looks like it was preserved
            original_filename = file_stem + file_ext if file_ext else file_stem
        
        # Save decrypted file
        output_path = Path(app.config['OUTPUT_FOLDER']) / job_id
        output_path.mkdir(exist_ok=True)
        
        decrypted_file_path = output_path / original_filename
        
        with open(decrypted_file_path, 'wb') as f:
            f.write(decrypted_data)
        
        # Get file size
        file_size = decrypted_file_path.stat().st_size
        
        # Clean up encrypted file
        try:
            encrypted_file_path.unlink()
            upload_path.rmdir()
        except:
            pass
        
        # Create download URL
        download_url = f'/download/{job_id}'
        
        # Store job info
        jobs[job_id] = add_job_timestamps({
            'status': 'completed',
            'type': 'file_decryption',
            'output_path': str(decrypted_file_path),
            'output_filename': original_filename
        })
        
        return jsonify({
            'success': True,
            'message': 'File decrypted successfully',
            'filename': original_filename,
            'file_size': file_size,
            'download_url': download_url
        })
        
    except Exception as e:
        return jsonify({'error': f'Decryption failed: {str(e)}'}), 500


# ============================================
# Audio Enhancer - Clean Voice & Reduce Noise
# ============================================

@app.route('/api/enhance-audio', methods=['POST'])
def enhance_audio():
    """Enhance audio by removing noise and cleaning voice"""
    # Ensure we ALWAYS return JSON
    response_data = {'success': False, 'error': 'Unknown error'}
    
    try:
        print("=== AUDIO ENHANCEMENT REQUEST RECEIVED ===")
        
        # Import check with detailed error
        print("Checking pydub imports...")
        try:
            from pydub import AudioSegment
            from pydub.effects import normalize as pydub_normalize, compress_dynamic_range
            from pydub.silence import detect_nonsilent
            print("✅ Pydub imports successful")
        except ImportError as ie:
            error_msg = f'Audio libraries not available: {str(ie)}. Run: pip3 install --break-system-packages pydub'
            print(f"❌ {error_msg}")
            response_data = {'success': False, 'error': error_msg}
            return app.response_class(
                response=json.dumps(response_data),
                status=200,
                mimetype='application/json'
            )
        
        print("Checking for audio file in request...")
        if 'audio' not in request.files:
            print("❌ No audio file in request")
            response_data = {'success': False, 'error': 'No audio file provided'}
            return app.response_class(
                response=json.dumps(response_data),
                status=200,
                mimetype='application/json'
            )
        
        audio_file = request.files['audio']
        print(f"Audio file received: {audio_file.filename}")
        
        if audio_file.filename == '':
            print("❌ Empty filename")
            response_data = {'success': False, 'error': 'No file selected'}
            return app.response_class(
                response=json.dumps(response_data),
                status=200,
                mimetype='application/json'
            )
        
        # Get enhancement options
        noise_reduction = request.form.get('noise_reduction', 'medium')
        enhance_voice = request.form.get('enhance_voice', 'true') == 'true'
        normalize_audio = request.form.get('normalize_audio', 'true') == 'true'
        remove_silence = request.form.get('remove_silence', 'false') == 'true'
        
        print(f"Options: noise={noise_reduction}, voice={enhance_voice}, normalize={normalize_audio}, silence={remove_silence}")
        
        # Create job
        job_id = str(uuid.uuid4())
        jobs[job_id] = add_job_timestamps({
            'status': 'processing',
            'progress': 0,
            'message': 'Starting audio enhancement...',
            'type': 'audio_enhancement'
        })
        
        print(f"Created job: {job_id}")
        
        # Save uploaded file
        filename = secure_filename(audio_file.filename)
        upload_dir = Path(app.config['UPLOAD_FOLDER']) / job_id
        upload_dir.mkdir(parents=True, exist_ok=True)
        input_path = upload_dir / filename
        audio_file.save(str(input_path))
        
        print(f"Saved file to: {input_path}")
        
        # Start processing in background
        thread = Thread(target=process_audio_enhancement, args=(
            job_id, str(input_path), noise_reduction, enhance_voice, 
            normalize_audio, remove_silence
        ))
        thread.start()
        
        print(f"✅ Processing started in background")
        
        response_data = {
            'success': True,
            'job_id': job_id,
            'message': 'Audio enhancement started'
        }
        
        return app.response_class(
            response=json.dumps(response_data),
            status=200,
            mimetype='application/json'
        )
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"❌ EXCEPTION in enhance_audio:")
        print(error_details)
        
        response_data = {
            'success': False,
            'error': f'Server error: {str(e)}'
        }
        
        return app.response_class(
            response=json.dumps(response_data),
            status=200,
            mimetype='application/json'
        )


def process_audio_enhancement(job_id, input_path, noise_reduction, enhance_voice, normalize_audio, remove_silence):
    """Process audio enhancement in background with AI-powered noise reduction"""
    print(f"\n🎵 BACKGROUND PROCESSING STARTED for job {job_id}")
    print(f"   Input: {input_path}")
    print(f"   Options: noise={noise_reduction}, voice={enhance_voice}, normalize={normalize_audio}, silence={remove_silence}")
    
    try:
        print("   Importing audio processing modules...")
        from pydub import AudioSegment
        from pydub.effects import normalize as pydub_normalize, compress_dynamic_range
        from pydub.silence import detect_nonsilent
        import numpy as np
        import noisereduce as nr
        print("   ✅ Imports successful (including AI noise reduction)")
        
        jobs[job_id]['progress'] = 10
        jobs[job_id]['message'] = 'Loading audio file...'
        print(f"   Progress: 10% - Loading audio file...")
        
        # Load audio file with optimized settings (supports WhatsApp audio, voice messages, etc.)
        input_file = Path(input_path)
        file_ext = input_file.suffix.lower()
        print(f"   Loading audio file: {input_file.name} (format: {file_ext})")
        
        # First, convert to WAV format using ffmpeg directly (more reliable)
        # This avoids the mediainfo_json error
        temp_wav = str(input_file.parent / f"{input_file.stem}_temp.wav")
        print(f"   Converting to WAV format first...")
        
        import subprocess
        try:
            # Use ffmpeg to convert to WAV
            result = subprocess.run(
                ['ffmpeg', '-i', str(input_path), '-ar', '44100', '-ac', '1', temp_wav, '-y'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                print(f"   ✅ Converted to WAV successfully")
                audio = AudioSegment.from_wav(temp_wav)
                # Clean up temp file
                Path(temp_wav).unlink(missing_ok=True)
            else:
                print(f"   ⚠️ ffmpeg conversion failed, trying direct load...")
                # Fallback to direct load
                audio = AudioSegment.from_file(input_path)
                
        except FileNotFoundError:
            print(f"   ⚠️ ffmpeg not found, trying direct load...")
            # ffmpeg not available, try direct load
            audio = AudioSegment.from_file(input_path)
        except Exception as conv_error:
            print(f"   ⚠️ Conversion error: {conv_error}, trying direct load...")
            # Fallback to direct load
            audio = AudioSegment.from_file(input_path)
        
        print(f"   ✅ Audio loaded: {len(audio)/1000:.2f}s, {audio.frame_rate}Hz, {audio.channels} channel(s)")
        
        # Convert to mono and reduce sample rate for faster processing
        audio = audio.set_channels(1)  # Mono for faster processing
        if audio.frame_rate > 44100:
            audio = audio.set_frame_rate(44100)  # Reduce sample rate for faster processing
        
        print(f"   Converted to: {audio.frame_rate}Hz, {audio.channels} channel(s)")
        
        jobs[job_id]['progress'] = 12
        jobs[job_id]['message'] = '🤖 AI analyzing audio with deep learning...'
        print(f"   Progress: 12% - ADVANCED AI NOISE REDUCTION...")
        
        # ✨ STAGE 0: MULTI-PASS AI-POWERED NOISE REDUCTION (Super powerful!)
        if noise_reduction != 'none':
            # Convert audio to numpy array for AI processing
            samples = np.array(audio.get_array_of_samples()).astype(np.float32)
            sample_rate = audio.frame_rate
            
            print(f"   🤖 Running advanced AI spectral noise reduction...")
            
            # Apply BALANCED AI-powered noise reduction
            if noise_reduction == 'light':
                # Single pass: Light cleanup
                reduced_noise = nr.reduce_noise(
                    y=samples, 
                    sr=sample_rate, 
                    prop_decrease=0.6,  # Gentle - preserves natural sound
                    stationary=True,
                    freq_mask_smooth_hz=500,
                    time_mask_smooth_ms=50
                )
                print(f"   ✅ Light AI noise removal (60%)")
                
            elif noise_reduction == 'medium':
                # Pass 1: Moderate cleanup
                reduced_noise = nr.reduce_noise(
                    y=samples, 
                    sr=sample_rate, 
                    prop_decrease=0.75,  # Moderate - balanced
                    stationary=False,
                    freq_mask_smooth_hz=500,
                    time_mask_smooth_ms=50
                )
                print(f"   ✅ Pass 1: Moderate AI noise removal (75%)")
                
                # Pass 2: Light polish
                reduced_noise = nr.reduce_noise(
                    y=reduced_noise, 
                    sr=sample_rate, 
                    prop_decrease=0.6,
                    stationary=True,
                    freq_mask_smooth_hz=800,
                    time_mask_smooth_ms=80
                )
                print(f"   ✅ Pass 2: Light polish (60%)")
                
            elif noise_reduction == 'heavy':
                # Pass 1: Strong noise removal
                reduced_noise = nr.reduce_noise(
                    y=samples, 
                    sr=sample_rate, 
                    prop_decrease=0.85,  # Strong but not excessive
                    stationary=False,
                    freq_mask_smooth_hz=400,
                    time_mask_smooth_ms=40
                )
                print(f"   ✅ Pass 1: Strong AI noise removal (85%)")
                
                # Pass 2: Moderate stationary cleanup
                reduced_noise = nr.reduce_noise(
                    y=reduced_noise, 
                    sr=sample_rate, 
                    prop_decrease=0.75,
                    stationary=True,
                    freq_mask_smooth_hz=700,
                    time_mask_smooth_ms=70
                )
                print(f"   ✅ Pass 2: Moderate cleanup (75%)")
                
                # Pass 3: Light polish
                reduced_noise = nr.reduce_noise(
                    y=reduced_noise, 
                    sr=sample_rate, 
                    prop_decrease=0.65,
                    stationary=True,
                    freq_mask_smooth_hz=900,
                    time_mask_smooth_ms=90
                )
                print(f"   ✅ Pass 3: Light polish (65%)")
            
            # Optional gentle noise gate (only for heavy mode)
            if noise_reduction == 'heavy':
                print(f"   🚪 Applying gentle noise gate...")
                
                def apply_gentle_noise_gate(audio_data, threshold_db=-50):
                    """Apply gentle noise gate - removes only very quiet background"""
                    # Calculate RMS in decibels
                    window = int(sample_rate * 0.03)  # 30ms window
                    rms = np.sqrt(np.convolve(audio_data**2, np.ones(window)/window, mode='same'))
                    rms_db = 20 * np.log10(rms + 1e-10)
                    
                    # Adaptive threshold
                    max_db = np.max(rms_db)
                    adaptive_threshold = max(threshold_db, max_db - 50)
                    
                    # Apply gate with smooth transition
                    gate = rms_db > adaptive_threshold
                    smooth_window = max(1, window // 5)
                    gate_smooth = np.convolve(gate.astype(float), np.ones(smooth_window)/smooth_window, mode='same')
                    
                    result = audio_data * np.clip(gate_smooth, 0.1, 1.0)  # Keep 10% minimum
                    return result
                
                reduced_noise = apply_gentle_noise_gate(reduced_noise, threshold_db=-50)
                print(f"   ✅ Gentle noise gate applied")
            
            # Convert back to AudioSegment
            audio = AudioSegment(
                reduced_noise.astype(np.int16).tobytes(),
                frame_rate=sample_rate,
                sample_width=2,  # Force 16-bit for consistency
                channels=1
            )
            
            print(f"   ✅ Advanced AI + transient removal complete!")
        
        jobs[job_id]['progress'] = 30
        jobs[job_id]['message'] = '🎙️ Isolating voice & removing background...'
        print(f"   Progress: 30% - Stage 1: ADVANCED Voice/Background Separation...")
        
        # STAGE 1: POWERFUL Voice/Background Separation
        # Human voice: 80-5000Hz (optimal speech range)
        print(f"   Applying POWERFUL voice isolation with background removal...")
        
        # Step 1: Remove sub-bass and rumble (AC, traffic, wind)
        audio = audio.high_pass_filter(80)   # Remove deep rumble
        print(f"   ✅ Removed rumble & sub-bass (below 80Hz)")
        
        # Step 2: Remove very high frequencies (electronic hiss, white noise)
        audio = audio.low_pass_filter(10000)   # Remove ultra-high noise
        print(f"   ✅ Removed ultra-high frequency noise (above 10kHz)")
        
        # Step 3: AGGRESSIVE background frequency removal
        if enhance_voice:
            # Remove low-mid mud (background ambiance, room tone)
            audio = audio.high_pass_filter(120)   # More aggressive low-cut
            print(f"   ✅ Removed background ambiance (below 120Hz)")
            
            # Focus on pure voice range (remove background music/noise)
            audio = audio.low_pass_filter(7000)   # Keep voice clarity
            print(f"   ✅ Focused on voice range (120-7000Hz)")
            
            # Additional mud removal for cleaner voice
            audio = audio.high_pass_filter(200)   # Remove low-mid mud
            print(f"   ✅ Removed low-mid mud for crystal clarity (200Hz+ only)")
        else:
            # Less aggressive for non-voice audio
            audio = audio.high_pass_filter(100)
            audio = audio.low_pass_filter(8000)
            print(f"   ✅ Applied gentle filtering (100-8000Hz)")
        
        jobs[job_id]['progress'] = 50
        jobs[job_id]['message'] = '🎙️ Ultra voice enhancement & background suppression...'
        print(f"   Progress: 50% - Stage 2: PROFESSIONAL Voice Enhancement...")
        
        # STAGE 2: Professional Voice Enhancement with Background Suppression
        if enhance_voice:
            # 1. Notch out problem frequencies (reduce background hum)
            print(f"   🎚️ Removing background hum frequencies...")
            audio = audio.high_pass_filter(180)  # Remove low hum
            
            # 2. Voice presence boost (make voice stand out from background)
            print(f"   🎤 Boosting voice presence frequencies...")
            audio = audio + 5  # Strong presence boost to override background
            
            # 3. First compression - Control dynamics while keeping voice natural
            audio = compress_dynamic_range(
                audio, 
                threshold=-28.0,  # Catch quieter background sounds
                ratio=6.0,        # Strong ratio to suppress background
                attack=3.0,       # Fast attack for background transients
                release=40.0      # Medium release
            )
            print(f"   ✅ Pass 1: Background suppression (6:1 ratio)")
            
            # 4. De-esser - Smooth harsh sibilance
            print(f"   🎛️ De-essing for broadcast quality...")
            audio = audio.low_pass_filter(8000)  # Smooth high-end
            
            # 5. Mid-range boost for voice clarity (where voice lives)
            audio = audio + 6  # Strong 6dB mid boost for crystal voice
            print(f"   ✅ +6dB voice clarity boost")
            
            # 6. Second compression - Even out voice levels
            audio = compress_dynamic_range(
                audio, 
                threshold=-20.0,  # Medium threshold
                ratio=4.0,        # Balanced ratio
                attack=5.0,       # Smooth attack
                release=50.0      # Natural release
            )
            print(f"   ✅ Pass 2: Level evening (4:1 ratio)")
            
            # 7. Final voice isolation - cut more background
            audio = audio.high_pass_filter(220)  # More aggressive mud cut
            print(f"   ✅ Final background cut (220Hz highpass)")
            
            # 8. Third compression - Broadcast-level consistency
            audio = compress_dynamic_range(
                audio, 
                threshold=-15.0,  # Catch peaks
                ratio=5.0,        # Strong limiting
                attack=2.0,       # Fast attack
                release=35.0      # Quick release
            )
            print(f"   ✅ Pass 3: Broadcast limiting (5:1 ratio)")
            
            # 9. Final clarity push
            audio = audio + 5  # Final 5dB boost for maximum presence
            print(f"   ✅ Final voice push: +5dB (Total: +16dB boost!)")
        
        jobs[job_id]['progress'] = 70
        jobs[job_id]['message'] = '📊 Professional mastering & loudness optimization...'
        print(f"   Progress: 70% - Stage 3: Broadcast-Level Mastering...")
        
        # STAGE 3: Professional Mastering (commercial-quality loudness)
        if normalize_audio:
            # Step 1: Peak normalization
            audio = pydub_normalize(audio)
            print(f"   ✅ Peak normalization applied")
            
            # Step 2: Mastering boost for commercial loudness
            audio = audio + 4  # Strong 4dB boost for loud, clear output
            print(f"   ✅ Mastering boost: +4dB")
            
            # Step 3: Brick-wall limiting (prevent distortion while keeping loud)
            audio = compress_dynamic_range(
                audio, 
                threshold=-8.0,   # High threshold for loudness
                ratio=10.0,       # Strong limiting ratio
                attack=1.0,       # Very fast attack
                release=30.0      # Quick release
            )
            print(f"   ✅ Brick-wall limiting (10:1) for maximum loudness")
            
            # Step 4: Final polish compression
            audio = compress_dynamic_range(
                audio, 
                threshold=-6.0,   # Catch any peaks
                ratio=8.0,        # Strong final limiting
                attack=0.5,       # Ultra-fast attack
                release=25.0      # Quick release
            )
            print(f"   ✅ Final safety limiting (8:1) - distortion-free")
            
            # Step 5: Tiny boost for extra presence
            audio = audio + 1  # Final 1dB touch
            print(f"   ✅ Final touch: +1dB (Total: +5dB boost with limiting)")
        
        jobs[job_id]['progress'] = 85
        jobs[job_id]['message'] = '✂️ Removing silence...'
        print(f"   Progress: 85% - Stage 4: Smart silence removal...")
        
        # Remove silence (optimized for speed)
        if remove_silence:
            # Detect non-silent chunks with optimized parameters
            nonsilent_chunks = detect_nonsilent(
                audio,
                min_silence_len=1000,  # milliseconds (longer = faster processing)
                silence_thresh=audio.dBFS - 16,  # dB (more aggressive = faster)
                seek_step=100  # Check every 100ms instead of every 10ms for faster processing
            )
            
            # Concatenate non-silent chunks
            if nonsilent_chunks:
                processed_audio = AudioSegment.empty()
                for start_i, end_i in nonsilent_chunks:
                    processed_audio += audio[start_i:end_i]
                audio = processed_audio
        
        jobs[job_id]['progress'] = 95
        jobs[job_id]['message'] = '✨ Exporting crystal-clear audio...'
        print(f"   Progress: 95% - Stage 4: Exporting AI-enhanced audio...")
        
        # Save output file
        output_dir = Path(app.config['OUTPUT_FOLDER']) / job_id
        output_dir.mkdir(parents=True, exist_ok=True)
        output_filename = f"enhanced_{input_file.stem}.mp3"
        output_path = output_dir / output_filename
        
        # Export as ULTRA-HIGH-QUALITY MP3 with maximum clarity settings
        audio.export(
            str(output_path),
            format='mp3',
            bitrate='320k',  # MAXIMUM quality bitrate (highest possible)
            parameters=[
                "-q:a", "0",  # Best quality encoding
                "-ar", "48000",  # High sample rate for extra clarity
                "-af", "highpass=f=120,lowpass=f=7500,volume=1.1"  # Voice clarity filter + extra boost
            ]
        )
        print(f"   ✅ Exported at 320kbps ULTRA-HIGH quality with MAXIMUM clarity")
        
        file_size = output_path.stat().st_size
        
        jobs[job_id].update({
            'status': 'completed',
            'progress': 100,
            'output_path': str(output_path),
            'output_filename': output_filename,
            'file_size': file_size,
            'message': 'Audio enhancement completed successfully!'
        })
        update_job_timestamp(job_id)
        print(f"   ✅ ENHANCEMENT COMPLETED for job {job_id}")
        print(f"   Output: {output_path} ({file_size / 1024 / 1024:.2f} MB)\n")
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"\n   ❌ ERROR in background processing for job {job_id}:")
        print(f"   {error_trace}\n")
        
        jobs[job_id].update({
            'status': 'failed',
            'progress': 0,
            'message': f'Enhancement failed: {str(e)}'
        })
        update_job_timestamp(job_id)


if __name__ == '__main__':
    import socket
    
    # Get local IP address
    def get_local_ip():
        try:
            # Connect to a remote address to get local IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "localhost"
    
    # Cleanup function (defined here to access app config)
    def cleanup_old_cache():
        """Remove cache data older than 5 minutes"""
        try:
            current_time = time.time()
            deleted_folders = 0
            deleted_jobs = 0
            
            # Clean up uploads folder
            uploads_dir = Path(app.config['UPLOAD_FOLDER'])
            if uploads_dir.exists():
                for item in uploads_dir.iterdir():
                    if item.is_dir():
                        # Check if folder is older than 5 minutes
                        try:
                            folder_age = current_time - item.stat().st_mtime
                            if folder_age > CACHE_MAX_AGE:
                                shutil.rmtree(item)
                                deleted_folders += 1
                        except Exception as e:
                            pass  # Skip if can't delete
            
            # Clean up outputs folder
            outputs_dir = Path(app.config['OUTPUT_FOLDER'])
            if outputs_dir.exists():
                for item in outputs_dir.iterdir():
                    if item.is_dir():
                        # Check if folder is older than 5 minutes
                        try:
                            folder_age = current_time - item.stat().st_mtime
                            if folder_age > CACHE_MAX_AGE:
                                shutil.rmtree(item)
                                deleted_folders += 1
                        except Exception as e:
                            pass  # Skip if can't delete
            
            # Clean up old jobs from memory (older than 5 minutes)
            jobs_to_remove = []
            for job_id, job_data in jobs.items():
                # Check if job has a timestamp
                if 'created_at' in job_data:
                    job_age = current_time - job_data['created_at']
                    if job_age > CACHE_MAX_AGE:
                        jobs_to_remove.append(job_id)
                # Also remove completed/failed jobs older than 5 minutes
                elif job_data.get('status') in ['completed', 'failed']:
                    # Use a default age if no timestamp
                    if 'updated_at' in job_data:
                        job_age = current_time - job_data['updated_at']
                        if job_age > CACHE_MAX_AGE:
                            jobs_to_remove.append(job_id)
            
            for job_id in jobs_to_remove:
                del jobs[job_id]
                deleted_jobs += 1
            
            if deleted_folders > 0 or deleted_jobs > 0:
                try:
                    print(f"[CLEANUP] Removed {deleted_folders} folders, {deleted_jobs} old jobs from cache")
                except:
                    pass
            
        except Exception as e:
            try:
                print(f"[CLEANUP] Error during cleanup: {str(e)}")
            except:
                pass
    
    def start_cache_cleanup_daemon():
        """Start background thread for automatic cache cleanup"""
        def cleanup_loop():
            while True:
                time.sleep(CACHE_CLEANUP_INTERVAL)
                cleanup_old_cache()
        
        cleanup_thread = Thread(target=cleanup_loop, daemon=True)
        cleanup_thread.start()
        try:
            print("[CLEANUP] Automatic cache cleanup started (removes files older than 5 minutes)")
        except:
            pass
    
    # Start automatic cache cleanup
    start_cache_cleanup_daemon()
    
    local_ip = get_local_ip()
    
    print("=" * 60)
    print("RKIEH SOLUTIONS - Media Tool Web Interface")
    print("=" * 60)
    print("\n>> Server Starting...")
    print(">> Open your browser at: http://localhost:5001")
    print(f">> Or access from network at: http://{local_ip}:5001")
    print("\n>> Press CTRL+C to stop the server")
    print("=" * 60 + "\n")
    
    app.run(host='0.0.0.0', port=5001, debug=True)

