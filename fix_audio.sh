#!/bin/bash
# Fix Audio Enhancer - Install modules and restart server

echo "=========================================="
echo "  Fixing Audio Enhancer"
echo "=========================================="
echo ""

cd /mnt/c/Users/Sub101/Downloads/rkieh-solutions-tools1

# Step 1: Install Python packages
echo "[1/3] Installing pydub and noisereduce..."
pip3 install --user pydub noisereduce
echo ""

# Step 2: Verify installation
echo "[2/3] Verifying installation..."
python3 << 'EOF'
try:
    import pydub
    print("✅ pydub is installed")
except:
    print("❌ pydub NOT installed")

try:
    import noisereduce
    print("✅ noisereduce is installed")
except:
    print("❌ noisereduce NOT installed")
EOF

echo ""

# Step 3: Check ffmpeg
echo "[3/3] Checking ffmpeg..."
if command -v ffmpeg &> /dev/null; then
    echo "✅ ffmpeg is available"
else
    echo "⚠️  ffmpeg not found (optional, but recommended)"
    echo "   You can install it later with: sudo apt-get install ffmpeg"
fi

echo ""
echo "=========================================="
echo "✅ Setup Complete!"
echo "=========================================="
echo ""
echo "NOW DO THIS:"
echo "1. Stop your Flask server (press CTRL+C)"
echo "2. Run: python3 web_app.py"
echo "3. Try Audio Enhancer again!"
echo ""

