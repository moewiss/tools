#!/bin/bash
# Setup and Start Script for RKIEH Solutions Media Tool
# This script creates a virtual environment and starts the web app

echo "============================================================"
echo "  RKIEH Solutions - Media Tool Setup"
echo "============================================================"
echo ""

# Check if Python3 is installed
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python3 is not installed!"
    echo "Install it with: sudo apt update && sudo apt install python3 python3-venv python3-pip"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "[SETUP] Creating virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "[ERROR] Failed to create virtual environment!"
        echo "Install venv with: sudo apt install python3-venv"
        exit 1
    fi
    echo "[OK] Virtual environment created!"
else
    echo "[OK] Virtual environment already exists"
fi

# Activate virtual environment
echo "[SETUP] Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "[SETUP] Upgrading pip..."
pip install --upgrade pip -q

# Install requirements
echo "[SETUP] Installing dependencies..."
echo "This may take a few minutes..."
pip install -r requirements.txt -q

if [ $? -ne 0 ]; then
    echo "[WARNING] Some packages may have failed to install"
    echo "Installing essential packages only..."
    pip install flask werkzeug yt-dlp opencv-python numpy pillow scipy -q
fi

# Create necessary directories
mkdir -p uploads outputs

echo ""
echo "============================================================"
echo "  Setup Complete! Starting Web Server..."
echo "============================================================"
echo ""

# Start the Flask app
python3 web_app.py

