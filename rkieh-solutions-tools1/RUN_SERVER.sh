#!/bin/bash
# FOOLPROOF SERVER STARTER - Always uses virtual environment

clear
echo "=========================================="
echo "  RKIEH SOLUTIONS - Starting Server"
echo "=========================================="
echo ""

cd /mnt/c/Users/Sub101/Downloads/rkieh-solutions-tools1

# Step 1: Create venv if needed
if [ ! -d "venv" ]; then
    echo "[1/4] Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "[1/4] Virtual environment already exists ✓"
fi

# Step 2: Activate venv
echo "[2/4] Activating virtual environment..."
source venv/bin/activate
echo "✓ Virtual environment activated"
echo "   Python: $(which python3)"

# Step 3: Install dependencies
echo "[3/4] Installing dependencies..."
pip install --quiet pydub noisereduce feedparser requests 2>&1 | grep -v "Requirement already satisfied" || echo "✓ Dependencies installed"

# Step 4: Check ffmpeg
if ! command -v ffmpeg &> /dev/null; then
    echo "[!] ffmpeg not found. Installing..."
    sudo apt-get update -qq && sudo apt-get install -y ffmpeg
fi
echo "✓ ffmpeg available"

echo ""
echo "=========================================="
echo "[4/4] Starting Flask Server..."
echo "=========================================="
echo ""

# Start server with venv python
./venv/bin/python3 web_app.py

