#!/bin/bash

# Installation Test Script
echo "🧪 Testing Media Tool Installation..."
echo ""

# Test 1: Check ffmpeg
echo "1️⃣  Checking ffmpeg..."
if command -v ffmpeg &> /dev/null; then
    echo "   ✅ ffmpeg is installed"
    ffmpeg -version | head -n 1
else
    echo "   ❌ ffmpeg is NOT installed"
    echo "   Run: sudo apt install ffmpeg -y"
    exit 1
fi
echo ""

# Test 2: Check Python3
echo "2️⃣  Checking Python3..."
if command -v python3 &> /dev/null; then
    echo "   ✅ Python3 is installed"
    python3 --version
else
    echo "   ❌ Python3 is NOT installed"
    exit 1
fi
echo ""

# Test 3: Check pip3
echo "3️⃣  Checking pip3..."
if command -v pip3 &> /dev/null; then
    echo "   ✅ pip3 is installed"
    pip3 --version
else
    echo "   ❌ pip3 is NOT installed"
    exit 1
fi
echo ""

# Test 4: Check yt-dlp
echo "4️⃣  Checking yt-dlp..."
if python3 -c "import yt_dlp" 2>/dev/null; then
    echo "   ✅ yt-dlp is installed"
    python3 -c "import yt_dlp; print('   Version:', yt_dlp.version.__version__)"
else
    echo "   ⚠️  yt-dlp is NOT installed"
    echo "   Run: pip3 install yt-dlp"
fi
echo ""

# Test 5: Check script permissions
echo "5️⃣  Checking script permissions..."
if [ -x "media_tool.py" ]; then
    echo "   ✅ media_tool.py is executable"
else
    echo "   ⚠️  media_tool.py is not executable"
    echo "   Run: chmod +x media_tool.py"
fi
echo ""

# Test 6: Run help command
echo "6️⃣  Testing media_tool.py..."
if python3 media_tool.py --help &> /dev/null; then
    echo "   ✅ media_tool.py runs successfully"
else
    echo "   ❌ media_tool.py failed to run"
    exit 1
fi
echo ""

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ All tests passed! Media Tool is ready."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📚 Quick Start:"
echo "   python3 media_tool.py convert video.mp4"
echo "   python3 media_tool.py download 'YOUTUBE_URL'"
echo ""
echo "📖 Documentation:"
echo "   README.md      - Full documentation"
echo "   QUICKSTART.md  - Quick setup guide"
echo "   EXAMPLES.md    - Usage examples"

