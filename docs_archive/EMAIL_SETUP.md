# Email Verification Setup Guide

## 📧 How to Enable Email Sending

Currently, verification codes are shown on screen for testing. To send actual emails:

### Option 1: Gmail (Recommended for Testing)

1. **Enable 2-Factor Authentication** on your Gmail account
2. **Generate App Password:**
   - Go to: https://myaccount.google.com/apppasswords
   - Select "Mail" and "Other (Custom name)"
   - Name it "RKIEH Solutions"
   - Copy the 16-character password

3. **Update verification.py:**
   ```python
   SMTP_SERVER = "smtp.gmail.com"
   SMTP_PORT = 587
   SENDER_EMAIL = "your-email@gmail.com"  # Your Gmail
   SENDER_PASSWORD = "xxxx xxxx xxxx xxxx"  # Your app password
   ```

4. **Uncomment email sending code** in `verification.py` (lines marked)

### Option 2: SendGrid (Recommended for Production)

1. **Sign up:** https://sendgrid.com (Free tier: 100 emails/day)
2. **Get API Key:** Settings → API Keys → Create API Key
3. **Install:** `pip install sendgrid`
4. **Update code:**
   ```python
   from sendgrid import SendGridAPIClient
   from sendgrid.helpers.mail import Mail
   
   message = Mail(
       from_email='noreply@yourdomain.com',
       to_emails=to_email,
       subject='Verification Code',
       html_content=html
   )
   sg = SendGridAPIClient('YOUR_API_KEY')
   sg.send(message)
   ```

### Option 3: Other Providers

- **Mailgun:** https://www.mailgun.com
- **AWS SES:** https://aws.amazon.com/ses/
- **Postmark:** https://postmarkapp.com

## 🔒 Security Notes

- ❌ Never commit credentials to Git
- ✅ Use environment variables:
  ```python
  import os
  SENDER_EMAIL = os.getenv('EMAIL_USER')
  SENDER_PASSWORD = os.getenv('EMAIL_PASSWORD')
  ```

- ✅ Create `.env` file:
  ```
  EMAIL_USER=your-email@gmail.com
  EMAIL_PASSWORD=your-app-password
  ```

- ✅ Add `.env` to `.gitignore`

## 🧪 Testing

For now, codes are shown on screen for testing. Remove this line in production:
```python
'code': code,  # Remove this in verification.py
```

## ✅ Production Checklist

- [ ] Configure email provider
- [ ] Add credentials as environment variables
- [ ] Uncomment email sending code
- [ ] Remove 'code' from API response
- [ ] Test with real email
- [ ] Set up error logging
- [ ] Configure bounce handling
- [ ] Add rate limiting

