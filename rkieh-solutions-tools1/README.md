# Media Tool 🎬🎵

A powerful tool for converting MP4 to MP3 and downloading videos from YouTube and other platforms. Available as both **command-line** and **beautiful web interface**. Optimized for Ubuntu/WSL with multi-threaded batch processing support.

## 🌟 Two Ways to Use

### 🖥️ Command-Line Interface
Perfect for automation, batch processing, and advanced users.

### 🌐 Web Interface  
Beautiful, modern UI with drag & drop support. [**Learn More →**](WEB_INTERFACE.md)

## ✨ Features

- 🔄 **Bidirectional Conversion**
  - **MP4 → MP3:** Extract audio from videos
  - **MP3 → MP4:** Create videos from audio files
  - Single or batch conversion
  - Multi-threaded processing for speed
  - Custom bitrate selection
  - Supports multiple formats (MP4, MKV, AVI, MOV, FLV, WebM, MP3, M4A, AAC, WAV)

- 📦 **Multi-File & Folder Support**
  - Upload multiple files at once
  - Select entire folders
  - Batch process 50+ files simultaneously
  - Automatic ZIP packaging for multiple outputs
  - Drag & drop support in web interface

- 📥 **YouTube & Video Downloader**
  - Download videos in various qualities
  - Extract audio as MP3
  - Batch download multiple URLs
  - Supports YouTube and many other platforms

## 🚀 Quick Start

### 🌐 Web Interface (Easiest!)

```bash
cd /mnt/d/Desktop/rkieh-solutions-tools1
chmod +x start_web.sh
./start_web.sh
```

Then open your browser at: **http://localhost:5000**

👉 **[Full Web Interface Guide](WEB_INTERFACE.md)**

### 🖥️ Command-Line Interface

```bash
# Clone or download the tool
cd rkieh-solutions-tools1

# Run the setup script
chmod +x setup.sh
./setup.sh
```

### Manual Setup

```bash
# Install ffmpeg
sudo apt update
sudo apt install ffmpeg -y

# Install Python dependencies
pip3 install -r requirements.txt

# Make script executable
chmod +x media_tool.py
```

## 📖 Usage

### Convert MP4 to MP3

**Convert a single file:**
```bash
python3 media_tool.py convert video.mp4
```

**Convert multiple files:**
```bash
python3 media_tool.py convert video1.mp4 video2.mp4 video3.mp4
```

**Convert all videos in a directory:**
```bash
python3 media_tool.py convert /path/to/videos/
```

**Custom output directory and bitrate:**
```bash
python3 media_tool.py convert video.mp4 -o output_folder/ -b 320k
```

**Adjust parallel processing (default is 4):**
```bash
python3 media_tool.py convert *.mp4 -w 8
```

### Download YouTube Videos & Shorts

**Download video (best quality):**
```bash
python3 media_tool.py download "https://www.youtube.com/watch?v=VIDEO_ID"
```

**Download as MP3 (audio only):**
```bash
python3 media_tool.py download "https://www.youtube.com/watch?v=VIDEO_ID" -f mp3
```

**Download with specific quality:**
```bash
python3 media_tool.py download "https://www.youtube.com/watch?v=VIDEO_ID" -q 1080p
```

**Download multiple videos:**
```bash
python3 media_tool.py download "URL1" "URL2" "URL3" -o downloads/
```

**Batch download from file:**
```bash
# Create a file with URLs (one per line)
cat urls.txt | xargs python3 media_tool.py download -f mp3
```

## 🎯 Command Reference

### Convert Command

```bash
python3 media_tool.py convert [FILES...] [OPTIONS]
```

**Options:**
- `-o, --output DIR` : Output directory for MP3 files
- `-b, --bitrate RATE` : Audio bitrate (default: 192k). Options: 128k, 192k, 256k, 320k
- `-w, --workers NUM` : Number of parallel workers (default: 4)

### Download Command

```bash
python3 media_tool.py download [URLS...] [OPTIONS]
```

**Options:**
- `-o, --output DIR` : Output directory (default: current directory)
- `-f, --format TYPE` : Format type: video, audio, mp3 (default: video)
- `-q, --quality QUALITY` : Video quality: best, 1080p, 720p, 480p (default: best)

## 📋 Examples

### Example 1: Convert all MP4s in current directory
```bash
python3 media_tool.py convert *.mp4 -b 320k
```

### Example 2: Download YouTube playlist as MP3
```bash
python3 media_tool.py download "PLAYLIST_URL" -f mp3 -o music/
```

### Example 3: Batch convert with 8 parallel threads
```bash
python3 media_tool.py convert /mnt/d/Videos/ -o /mnt/d/Music/ -w 8
```

### Example 4: Download video in 720p
```bash
python3 media_tool.py download "https://youtu.be/VIDEO_ID" -q 720p -o videos/
```

## 🌐 Supported Platforms

The downloader supports:
- YouTube
- Vimeo
- Dailymotion
- Facebook
- Instagram
- Twitter/X
- TikTok
- And 1000+ more sites!

## 💡 Tips & Tricks

1. **Finding your WSL IP:**
   ```bash
   ip addr show eth0 | grep inet
   ```

2. **Access files from Windows:**
   - WSL files: `\\wsl$\Ubuntu\home\username\`
   - Windows files from WSL: `/mnt/c/Users/username/`

3. **Batch processing large directories:**
   ```bash
   # Use more workers for faster processing
   python3 media_tool.py convert /mnt/d/Videos/ -w 8
   ```

4. **Download entire playlist:**
   ```bash
   python3 media_tool.py download "PLAYLIST_URL" -f mp3
   ```

5. **Create alias for quick access:**
   ```bash
   echo "alias mp3='python3 ~/rkieh-solutions-tools1/media_tool.py convert'" >> ~/.bashrc
   source ~/.bashrc
   # Now you can use: mp3 video.mp4
   ```

## 🐛 Troubleshooting

**Error: ffmpeg not found**
```bash
sudo apt update && sudo apt install ffmpeg -y
```

**Error: yt-dlp not found**
```bash
pip3 install --upgrade yt-dlp
```

**Permission denied**
```bash
chmod +x media_tool.py
```

**Downloads failing**
```bash
# Update yt-dlp to latest version
pip3 install --upgrade yt-dlp
```

## 📊 System Requirements

- Ubuntu 20.04+ / WSL2
- Python 3.7+
- ffmpeg
- Internet connection (for downloads)

## 🚀 Performance

- **Conversion Speed**: Depends on file size and CPU
- **Parallel Processing**: Default 4 workers, adjustable up to your CPU cores
- **Memory Usage**: Low (streaming processing)

## 📝 License

Free to use for personal and commercial projects.

## 🤝 Support

For issues or feature requests, please check:
1. Ensure all dependencies are installed
2. Update yt-dlp: `pip3 install --upgrade yt-dlp`
3. Check ffmpeg: `ffmpeg -version`

---

**Your IP Address:** 172.25.26.140  
**Made with ❤️ for WSL Ubuntu Cloud**

