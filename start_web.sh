#!/bin/bash

# Start Web Interface for Media Tool
echo "🚀 Starting Media Tool Web Interface..."
echo ""

# Check if Flask is installed
if ! python3 -c "import flask" 2>/dev/null; then
    echo "📦 Installing Flask..."
    pip3 install flask werkzeug --break-system-packages
    echo ""
fi

# Check if yt-dlp is installed
if ! python3 -c "import yt_dlp" 2>/dev/null; then
    echo "📦 Installing yt-dlp..."
    pip3 install yt-dlp --break-system-packages
    echo ""
fi

# Create necessary directories
mkdir -p uploads outputs

# Get IP address
IP_ADDRESS=$(ip addr show eth0 2>/dev/null | grep 'inet ' | awk '{print $2}' | cut -d/ -f1)
if [ -z "$IP_ADDRESS" ]; then
    IP_ADDRESS="localhost"
fi

echo "✅ All dependencies installed!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🌐 Web Interface Starting..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📍 Access the web interface at:"
echo ""
echo "   Local:   http://localhost:5000"
echo "   Network: http://$IP_ADDRESS:5000"
echo ""
echo "⚠️  Press CTRL+C to stop the server"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Start the Flask app
python3 web_app.py

