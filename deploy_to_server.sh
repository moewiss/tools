#!/bin/bash

# Deployment script for Ubuntu Server
# Run this on the Ubuntu server: 157.173.106.72

echo "========================================="
echo "Starting deployment of Media Tools App"
echo "========================================="

# Update system
echo "Updating system packages..."
apt update && apt upgrade -y

# Install Python and required system packages
echo "Installing Python and dependencies..."
apt install -y python3 python3-pip python3-venv git

# Install ffmpeg for media processing
echo "Installing ffmpeg..."
apt install -y ffmpeg

# Install additional dependencies for audio/video processing
apt install -y libavcodec-extra libavformat-dev libavutil-dev libswscale-dev libswresample-dev

# Create application directory
echo "Setting up application directory..."
cd /root
rm -rf tools
git clone https://github.com/moewiss/tools.git
cd tools

# Create virtual environment
echo "Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo "Installing Python packages..."
pip install --upgrade pip
pip install -r requirements.txt

# Make shell scripts executable
echo "Making scripts executable..."
chmod +x *.sh

# Create systemd service for auto-start
echo "Creating systemd service..."
cat > /etc/systemd/system/media-tools.service << 'EOF'
[Unit]
Description=Media Tools Web Application
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/tools
Environment="PATH=/root/tools/venv/bin"
ExecStart=/root/tools/venv/bin/python3 /root/tools/web_app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and enable service
systemctl daemon-reload
systemctl enable media-tools.service
systemctl start media-tools.service

# Configure firewall (if UFW is installed)
if command -v ufw &> /dev/null; then
    echo "Configuring firewall..."
    ufw allow 5000/tcp
    ufw allow 22/tcp
    ufw --force enable
fi

echo "========================================="
echo "Deployment complete!"
echo "========================================="
echo ""
echo "Application is running on port 5000"
echo "Access it at: http://157.173.106.72:5000"
echo ""
echo "Useful commands:"
echo "  - Check status: systemctl status media-tools"
echo "  - View logs: journalctl -u media-tools -f"
echo "  - Restart: systemctl restart media-tools"
echo "  - Stop: systemctl stop media-tools"
echo ""

