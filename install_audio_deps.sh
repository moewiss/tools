#!/bin/bash
# Install Audio Enhancer dependencies and start server

echo "======================================"
echo "Installing Audio Enhancer Dependencies"
echo "======================================"

cd /mnt/c/Users/Sub101/Downloads/rkieh-solutions-tools1

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install ALL required packages
echo "Installing required packages..."
pip install --upgrade pip
pip install -r requirements.txt

# Install ffmpeg (system dependency) - skip if already installed
if ! command -v ffmpeg &> /dev/null; then
    echo "Installing ffmpeg..."
    sudo apt-get update
    sudo apt-get install -y ffmpeg
else
    echo "ffmpeg already installed ✓"
fi

echo ""
echo "======================================"
echo "✅ Installation Complete!"
echo "======================================"
echo "Starting Flask server..."
echo ""

# Start the server with virtual environment active
python3 web_app.py

