#!/bin/bash
# Simple script to install audio enhancement dependencies

echo "============================================"
echo "Installing Audio Enhancement Dependencies"
echo "============================================"
echo ""

# Make sure we're in the right directory
cd /mnt/c/Users/Sub101/Downloads/rkieh-solutions-tools1

echo "[1/3] Installing Python packages..."
pip3 install --user pydub noisereduce
echo "✓ Python packages installed"

echo ""
echo "[2/3] Installing ffmpeg..."
sudo apt-get update -qq
sudo apt-get install -y ffmpeg
echo "✓ ffmpeg installed"

echo ""
echo "[3/3] Verifying installation..."
python3 -c "import pydub; print('✓ pydub is working')" 2>/dev/null || echo "⚠ pydub still not available"
python3 -c "import noisereduce; print('✓ noisereduce is working')" 2>/dev/null || echo "⚠ noisereduce still not available"
which ffmpeg > /dev/null && echo "✓ ffmpeg is available" || echo "⚠ ffmpeg not found"

echo ""
echo "============================================"
echo "✅ Installation Complete!"
echo "============================================"
echo ""
echo "Now restart your Flask server!"
echo ""

