#!/bin/bash
# Install Audio Enhancement Libraries

echo "🎙️ Installing Audio Enhancement Libraries..."
echo "============================================"

# Update pip
echo ""
echo "📦 Updating pip..."
pip3 install --upgrade pip --break-system-packages

# Install audio processing libraries
echo ""
echo "🔊 Installing pydub (audio processing)..."
pip3 install --break-system-packages pydub

echo ""
echo "🤖 Installing noisereduce (AI noise reduction)..."
pip3 install --break-system-packages noisereduce

echo ""
echo "📊 Installing numpy (required dependency)..."
pip3 install --break-system-packages numpy

echo ""
echo "📈 Installing scipy (required dependency)..."
pip3 install --break-system-packages scipy

# Install FFmpeg
echo ""
echo "🎬 Installing FFmpeg (audio/video codec)..."
if command -v ffmpeg &> /dev/null; then
    echo "✅ FFmpeg is already installed!"
    ffmpeg -version | head -n 1
else
    echo "Installing FFmpeg..."
    sudo apt update
    sudo apt install -y ffmpeg
    echo "✅ FFmpeg installed successfully!"
fi

# Verify installations
echo ""
echo "============================================"
echo "✅ Verifying installations..."
echo "============================================"

python3 -c "import pydub; print('✅ pydub:', pydub.__version__)" || echo "❌ pydub NOT installed"
python3 -c "import noisereduce; print('✅ noisereduce: OK')" || echo "❌ noisereduce NOT installed"
python3 -c "import numpy; print('✅ numpy:', numpy.__version__)" || echo "❌ numpy NOT installed"
python3 -c "import scipy; print('✅ scipy:', scipy.__version__)" || echo "❌ scipy NOT installed"
ffmpeg -version | head -n 1 || echo "❌ FFmpeg NOT installed"

echo ""
echo "============================================"
echo "🎉 Installation Complete!"
echo "============================================"
echo ""
echo "📝 Next Steps:"
echo "1. Restart the server: python3 web_app.py"
echo "2. Open Audio Enhancer: http://127.0.0.1:5001/tool/audio-enhancer"
echo "3. Upload an audio file and test!"
echo ""

