# 📧 Email Verification Setup Guide

## Quick Setup (5 minutes)

### Step 1: Choose Email Provider

#### Option A: Gmail (Easiest - Recommended)

1. **Enable 2-Factor Authentication:**
   - Go to: https://myaccount.google.com/security
   - Enable 2-Step Verification

2. **Generate App Password:**
   - Go to: https://myaccount.google.com/apppasswords
   - Select App: "Mail"
   - Select Device: "Other (Custom name)"
   - Enter: "RKIEH Solutions"
   - Click "Generate"
   - Copy the 16-character password

3. **Configure Application:**
   
   **Method 1: Direct Edit (Quick)**
   ```python
   # Edit verification.py, line ~80:
   SENDER_EMAIL = "your-email@gmail.com"  # Your Gmail
   SENDER_PASSWORD = "xxxx xxxx xxxx xxxx"  # Your app password
   ```

   **Method 2: Environment Variables (Recommended)**
   ```bash
   # Create .env file in project root:
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587
   SENDER_EMAIL=your-email@gmail.com
   SENDER_PASSWORD=xxxx xxxx xxxx xxxx
   ```

4. **Install python-dotenv (if using .env):**
   ```bash
   pip install python-dotenv
   ```

   Add to web_app.py (top):
   ```python
   from dotenv import load_dotenv
   load_dotenv()
   ```

#### Option B: SendGrid (Professional - Free 100 emails/day)

1. **Sign Up:** https://sendgrid.com
2. **Get API Key:** Settings → API Keys → Create API Key
3. **Install SDK:**
   ```bash
   pip install sendgrid
   ```
4. **Replace send_email() in verification.py:**
   ```python
   from sendgrid import SendGridAPIClient
   from sendgrid.helpers.mail import Mail
   
   def send_email(to_email, code):
       message = Mail(
           from_email='noreply@yourdomain.com',
           to_emails=to_email,
           subject='Your RKIEH Solutions Verification Code',
           html_content=html  # Use the same HTML template
       )
       try:
           sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
           response = sg.send(message)
           return True
       except Exception as e:
           print(f"Error: {e}")
           return False
   ```

#### Option C: Other Providers

**Outlook/Hotmail:**
```python
SMTP_SERVER = "smtp-mail.outlook.com"
SMTP_PORT = 587
SENDER_EMAIL = "your-email@outlook.com"
SENDER_PASSWORD = "your-password"
```

**Yahoo:**
```python
SMTP_SERVER = "smtp.mail.yahoo.com"
SMTP_PORT = 587
SENDER_EMAIL = "your-email@yahoo.com"
SENDER_PASSWORD = "your-app-password"  # Generate at Yahoo Account Security
```

**Mailgun, AWS SES, Postmark:** See their documentation

---

## Testing

### Test Email Sending:

```python
# Run in Python console:
from verification import send_email

send_email("your-test-email@gmail.com", "123456")
# Check your inbox!
```

### Test Full Flow:

1. Go to `/signup`
2. Enter email
3. Click "Send Code"
4. Check email inbox (and spam folder)
5. Enter code
6. Complete signup

---

## Troubleshooting

### "Email not configured" error:
- ✅ Make sure you replaced `your-email@gmail.com` with your actual email
- ✅ Make sure you replaced `your-app-password` with your actual app password

### "Authentication failed" error:
- ✅ Enable 2FA on Gmail
- ✅ Use App Password, not regular password
- ✅ Copy password exactly (no spaces at ends)

### Email not received:
- ✅ Check spam folder
- ✅ Check "Promotions" tab (Gmail)
- ✅ Verify email address is correct
- ✅ Check console logs for errors

### "Connection refused" error:
- ✅ Check SMTP server and port
- ✅ Check firewall settings
- ✅ Verify internet connection

---

## Security Best Practices

### ❌ DON'T:
- Hardcode passwords in code (if sharing)
- Commit credentials to Git
- Use regular Gmail password (must use App Password)
- Share your App Password

### ✅ DO:
- Use environment variables
- Add `.env` to `.gitignore`
- Use App Passwords for Gmail
- Rotate passwords periodically
- Monitor email sending logs

---

## Production Checklist

- [ ] Email provider configured
- [ ] Credentials added (via .env or direct edit)
- [ ] python-dotenv installed (if using .env)
- [ ] `.env` added to `.gitignore`
- [ ] Test email sent successfully
- [ ] Spam filter tested
- [ ] Error logging set up
- [ ] Rate limiting configured
- [ ] Email deliverability checked

---

## Current Status

**What's Working:**
- ✅ Code generation
- ✅ Code validation
- ✅ Expiry (10 minutes)
- ✅ Attempt limiting (3 tries)
- ✅ HTML email template
- ✅ Console logging

**What Needs Setup:**
- ⚠️ Email sending (needs your credentials)

---

## Quick Start (Gmail):

```bash
# 1. Get Gmail App Password (see instructions above)

# 2. Edit verification.py (line ~80):
SENDER_EMAIL = "youremail@gmail.com"
SENDER_PASSWORD = "your 16-char app password"

# 3. Restart server
python3 web_app.py

# 4. Test signup!
```

---

## Support

If you need help:
1. Check console logs for errors
2. Verify credentials are correct
3. Test with a different email provider
4. Check EMAIL_SETUP.md for more details

**The code is sending to console for now. Configure email to send to real inboxes!**

