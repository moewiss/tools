# Deployment Guide for Ubuntu Server

## Server Details
- **IP Address:** 157.173.106.72
- **User:** root
- **Application Port:** 5000

---

## 🚀 Quick Deployment Steps

### Step 1: Copy deployment script to server
Run this command in your **local terminal (Windows PowerShell)**:

```powershell
scp deploy_to_server.sh root@157.173.106.72:/root/
```

### Step 2: Connect to your server
```powershell
ssh root@157.173.106.72
```

### Step 3: Run the deployment script
Once connected to the server, run:

```bash
cd /root
chmod +x deploy_to_server.sh
./deploy_to_server.sh
```

This will:
- Install all dependencies (Python, ffmpeg, etc.)
- Clone your GitHub repository
- Set up Python virtual environment
- Install Python packages
- Create a systemd service for auto-start
- Configure firewall
- Start your application

### Step 4: Access your application
Open in browser: **http://157.173.106.72:5000**

---

## 📊 Useful Server Commands

After deployment, you can manage your app with these commands:

```bash
# Check if app is running
systemctl status media-tools

# View live logs
journalctl -u media-tools -f

# Restart the application
systemctl restart media-tools

# Stop the application
systemctl stop media-tools

# Start the application
systemctl start media-tools
```

---

## 🔄 Updating Your Application

When you make changes in Cursor and push to GitHub:

### 1. Push changes from Cursor (Windows)
```powershell
git add .
git commit -m "Your change description"
git push origin main
```

### 2. Update on server
SSH into server and run:
```bash
cd /root/tools
git pull origin main
systemctl restart media-tools
```

Or use the quick update script:
```bash
cd /root/tools
./update_server.sh
```

---

## 🔧 Troubleshooting

### Check if port 5000 is open
```bash
netstat -tulpn | grep 5000
```

### Check firewall status
```bash
ufw status
```

### View detailed logs
```bash
journalctl -u media-tools -n 100
```

### Manual start (for testing)
```bash
cd /root/tools
source venv/bin/activate
python3 web_app.py
```

---

## 🔒 Security Notes

1. Consider changing the default port 5000 to something else
2. Set up a domain name and SSL certificate (Let's Encrypt)
3. Configure nginx as a reverse proxy
4. Don't run as root in production (create dedicated user)
5. Keep your server updated: `apt update && apt upgrade -y`

---

## 📝 Next Steps

1. ✅ Deploy to server (follow steps above)
2. ⚙️ Configure domain name (optional)
3. 🔒 Set up SSL certificate (recommended)
4. 🌐 Set up nginx reverse proxy (recommended)
5. 👥 Create non-root user for app (recommended)

