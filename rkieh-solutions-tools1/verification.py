#!/usr/bin/env python3
"""
Email Verification System
Send and verify email verification codes
"""

import json
import random
import string
from datetime import datetime, timedelta
from pathlib import Path

VERIFICATION_FILE = Path('verification_codes.json')
CODE_EXPIRY_MINUTES = 10


def load_verification_codes():
    """Load verification codes"""
    if VERIFICATION_FILE.exists():
        try:
            with open(VERIFICATION_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}


def save_verification_codes(codes):
    """Save verification codes"""
    with open(VERIFICATION_FILE, 'w') as f:
        json.dump(codes, f, indent=2)


def generate_code():
    """Generate a 6-digit verification code"""
    return ''.join(random.choices(string.digits, k=6))


def send_verification_code(email):
    """
    Generate and store verification code for email
    Sends actual email with verification code
    """
    codes = load_verification_codes()
    
    # Generate new code
    code = generate_code()
    expiry = (datetime.now() + timedelta(minutes=CODE_EXPIRY_MINUTES)).isoformat()
    
    codes[email] = {
        'code': code,
        'expiry': expiry,
        'attempts': 0,
        'created_at': datetime.now().isoformat()
    }
    
    save_verification_codes(codes)
    
    # Send email
    email_sent = send_email(email, code)
    
    # Console log for admin debugging only
    print(f"[VERIFICATION] Code sent to {email}: {code} (expires in {CODE_EXPIRY_MINUTES} min)")
    
    return {
        'success': True,
        'message': 'Verification code sent to your email!',
        'expiry_minutes': CODE_EXPIRY_MINUTES,
        'email_sent': email_sent
    }


def send_email(to_email, code):
    """
    Send verification code via email
    Configure with your email service (Gmail, SendGrid, etc.)
    """
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        # Email configuration
        import os
        
        # Try to get from environment variables first (recommended)
        SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
        SENDER_EMAIL = os.getenv('SENDER_EMAIL', 'your-email@gmail.com')  # UPDATE THIS
        SENDER_PASSWORD = os.getenv('SENDER_PASSWORD', 'your-app-password')  # UPDATE THIS
        
        # Create message
        message = MIMEMultipart("alternative")
        message["Subject"] = "Your RKIEH Solutions Verification Code"
        message["From"] = f"RKIEH Solutions <{SENDER_EMAIL}>"
        message["To"] = to_email
        
        # Email body
        html = f"""
        <html>
            <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
                <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 10px; padding: 30px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                    <h1 style="color: #ff3333; text-align: center; margin-bottom: 20px;">RKIEH Solutions</h1>
                    <h2 style="color: #333; text-align: center;">Email Verification</h2>
                    
                    <p style="color: #666; font-size: 16px; line-height: 1.6;">
                        Thank you for signing up! To complete your registration, please use the verification code below:
                    </p>
                    
                    <div style="background: linear-gradient(135deg, #4CAF50, #66BB6A); border-radius: 10px; padding: 25px; text-align: center; margin: 30px 0;">
                        <p style="color: #fff; font-size: 14px; margin: 0 0 10px 0;">Your Verification Code:</p>
                        <h1 style="color: #fff; font-size: 48px; letter-spacing: 10px; margin: 10px 0; font-family: monospace;">
                            {code}
                        </h1>
                    </div>
                    
                    <p style="color: #666; font-size: 14px; line-height: 1.6;">
                        This code will expire in <strong>{CODE_EXPIRY_MINUTES} minutes</strong>.
                    </p>
                    
                    <p style="color: #999; font-size: 12px; margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee;">
                        If you didn't request this code, please ignore this email.
                    </p>
                </div>
            </body>
        </html>
        """
        
        part = MIMEText(html, "html")
        message.attach(part)
        
        # Check if email is configured
        if SENDER_EMAIL == 'your-email@gmail.com' or SENDER_PASSWORD == 'your-app-password':
            print(f"[EMAIL] ⚠️ Email not configured! Code for {to_email}: {code}")
            print(f"[EMAIL] Please configure SENDER_EMAIL and SENDER_PASSWORD in verification.py")
            return False
        
        # Send email (uncomment these lines when email is configured)
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, to_email, message.as_string())
        server.quit()
        
        print(f"[EMAIL] ✅ Successfully sent to {to_email}")
        return True
        
    except Exception as e:
        print(f"[EMAIL ERROR] Failed to send email: {str(e)}")
        return False


def verify_code(email, code):
    """Verify the code for an email"""
    codes = load_verification_codes()
    
    if email not in codes:
        return {
            'success': False,
            'error': 'No verification code found for this email'
        }
    
    stored = codes[email]
    
    # Check expiry
    expiry = datetime.fromisoformat(stored['expiry'])
    if datetime.now() > expiry:
        del codes[email]
        save_verification_codes(codes)
        return {
            'success': False,
            'error': 'Verification code has expired. Please request a new one.'
        }
    
    # Check attempts
    if stored['attempts'] >= 3:
        del codes[email]
        save_verification_codes(codes)
        return {
            'success': False,
            'error': 'Too many failed attempts. Please request a new code.'
        }
    
    # Verify code
    if stored['code'] == code.strip():
        # Success - remove code
        del codes[email]
        save_verification_codes(codes)
        return {
            'success': True,
            'message': 'Email verified successfully!'
        }
    else:
        # Failed - increment attempts
        stored['attempts'] += 1
        save_verification_codes(codes)
        remaining = 3 - stored['attempts']
        return {
            'success': False,
            'error': f'Invalid code. {remaining} attempt(s) remaining.'
        }


def cleanup_expired_codes():
    """Remove expired verification codes"""
    codes = load_verification_codes()
    now = datetime.now()
    
    expired = []
    for email, data in codes.items():
        expiry = datetime.fromisoformat(data['expiry'])
        if now > expiry:
            expired.append(email)
    
    for email in expired:
        del codes[email]
    
    if expired:
        save_verification_codes(codes)
    
    return len(expired)

