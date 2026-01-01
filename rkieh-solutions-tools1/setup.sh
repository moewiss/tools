#!/bin/bash

# Media Tool Setup Script for Ubuntu/WSL
echo "🚀 Setting up Media Tool..."
echo ""

# Update package list
echo "📦 Updating package list..."
sudo apt update

# Install ffmpeg
echo "📦 Installing ffmpeg..."
sudo apt install ffmpeg -y

# Install Python3 and pip if not already installed
echo "🐍 Checking Python3 and pip..."
sudo apt install python3 python3-pip -y

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip3 install -r requirements.txt

# Make the script executable
echo "🔧 Making script executable..."
chmod +x media_tool.py

echo ""
echo "✅ Setup complete!"
echo ""
echo "📚 Quick Start:"
echo "   Convert: python3 media_tool.py convert video.mp4"
echo "   Download: python3 media_tool.py download 'YOUTUBE_URL'"
echo ""
echo "For more help, run: python3 media_tool.py --help"

