# 🌐 Media Tool - Web Interface

A beautiful, modern web interface for converting MP4 to MP3 and downloading from YouTube!

![Features](https://img.shields.io/badge/Features-Convert%20%7C%20Download-blue)
![Technology](https://img.shields.io/badge/Tech-Flask%20%7C%20HTML%20%7C%20CSS%20%7C%20JS-green)

## ✨ Features

### 🎨 Beautiful Modern UI
- Dark theme with gradient accents
- Smooth animations and transitions
- Responsive design for all devices
- Drag & drop file upload

### 🔄 MP4 to MP3 Conversion
- Upload videos directly in the browser
- Choose audio quality (128k - 320k)
- Real-time progress tracking
- Download converted files instantly

### 📥 YouTube Downloader
- Download videos or audio
- Multiple quality options
- Support for 1000+ websites
- Batch download support

## 🚀 Quick Start

### For WSL Ubuntu (Recommended)

```bash
cd /mnt/d/Desktop/rkieh-solutions-tools1

# Make script executable
chmod +x start_web.sh

# Start the web server
./start_web.sh
```

### For Windows

```cmd
cd D:\Desktop\rkieh-solutions-tools1
start_web.bat
```

### Manual Start

```bash
# Install dependencies
pip3 install flask werkzeug yt-dlp --break-system-packages

# Start the server
python3 web_app.py
```

## 🌐 Access the Interface

Once started, open your browser at:

- **Local Access:** `http://localhost:5000`
- **Network Access:** `http://172.25.26.140:5000`
- **From Windows Browser:** `http://localhost:5000`

## 📱 How to Use

### Convert MP4 to MP3

1. Click on **"Convert to MP3"** tab
2. Drag & drop your video file (or click to browse)
3. Select audio quality (bitrate)
4. Click **"Convert to MP3"**
5. Wait for processing
6. Download your MP3 file!

### Download from YouTube

1. Click on **"YouTube Download"** tab
2. Paste the YouTube URL
3. Select format (Video or MP3)
4. Choose quality
5. Click **"Download"**
6. Wait for download to complete
7. Download your file!

## 🎯 Features in Detail

### 🎵 Audio Quality Options

| Bitrate | Quality | File Size | Best For |
|---------|---------|-----------|----------|
| 128k | Good | Small | Podcasts, audiobooks |
| 192k | High | Medium | General music (default) |
| 256k | Very High | Large | High-quality music |
| 320k | Maximum | Largest | Audiophile quality |

### 📹 Video Quality Options

| Quality | Resolution | Description |
|---------|-----------|-------------|
| Best | Highest available | Maximum quality |
| 1080p | 1920x1080 | Full HD |
| 720p | 1280x720 | HD |
| 480p | 854x480 | Standard Definition |

## 🛠️ Technical Details

### Technology Stack
- **Backend:** Flask (Python)
- **Frontend:** HTML5, CSS3, JavaScript
- **Media Processing:** FFmpeg, yt-dlp
- **Design:** Modern UI with animations

### File Structure
```
rkieh-solutions-tools1/
├── web_app.py              # Flask backend
├── media_tool.py           # Core conversion logic
├── templates/
│   └── index.html          # Main interface
├── static/
│   ├── css/
│   │   └── style.css       # Styling & animations
│   └── js/
│       └── main.js         # Interactive functionality
├── uploads/                # Temporary upload storage
└── outputs/                # Processed files
```

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Main web interface |
| `/upload` | POST | Upload file for conversion |
| `/download-youtube` | POST | Start YouTube download |
| `/status/<job_id>` | GET | Check job progress |
| `/download/<job_id>` | GET | Download result file |

## 🔧 Configuration

### Port Configuration
Default port is `5000`. To change it, edit `web_app.py`:

```python
app.run(host='0.0.0.0', port=5000, debug=True)
```

### File Size Limit
Default maximum file size is 500MB. To change it, edit `web_app.py`:

```python
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB
```

## 🐛 Troubleshooting

### Port Already in Use
```bash
# Kill process on port 5000
sudo kill -9 $(lsof -t -i:5000)

# Or use a different port
python3 web_app.py --port 8000
```

### Module Not Found Error
```bash
# Install missing dependencies
pip3 install flask werkzeug yt-dlp --break-system-packages
```

### Can't Access from Network
```bash
# Check firewall settings
sudo ufw allow 5000

# Verify IP address
ip addr show eth0 | grep inet
```

### Conversion/Download Fails
```bash
# Update yt-dlp
pip3 install --upgrade yt-dlp --break-system-packages

# Check ffmpeg
ffmpeg -version
```

## 💡 Tips & Tricks

### 1. Keep the Terminal Open
The web server needs to keep running in the terminal. Don't close it!

### 2. Access from Phone/Tablet
Use your WSL IP address to access from other devices on the same network:
```
http://172.25.26.140:5000
```

### 3. Batch Processing
Open multiple browser tabs to process multiple files simultaneously.

### 4. Background Processing
Jobs continue processing even if you close the browser tab. Check status by refreshing the page.

### 5. Create Desktop Shortcut
**Windows:**
Create a shortcut to `start_web.bat` on your desktop for quick access.

**WSL:**
Add alias to `~/.bashrc`:
```bash
echo "alias mediaweb='cd /mnt/d/Desktop/rkieh-solutions-tools1 && ./start_web.sh'" >> ~/.bashrc
source ~/.bashrc
```

## 🎨 UI Features

### Drag & Drop
Simply drag video files onto the upload area!

### Real-time Progress
See live progress with animated progress bars

### Instant Feedback
Visual feedback for all actions and errors

### Responsive Design
Works perfectly on desktop, tablet, and mobile

### Dark Theme
Easy on the eyes with modern dark design

## 📊 Performance

- **Conversion Speed:** Depends on file size and CPU
- **Concurrent Jobs:** Multiple files can be processed simultaneously
- **Memory Usage:** Low (streaming processing)
- **Network:** Required for YouTube downloads only

## 🔒 Security Notes

- Files are processed locally on your machine
- No data is sent to external servers (except YouTube downloads)
- Uploaded files are stored temporarily and can be deleted
- Clean up old files regularly to save space

## 🚀 Advanced Usage

### Run on Custom Port
```bash
# Edit web_app.py
sed -i 's/port=5000/port=8080/' web_app.py
python3 web_app.py
```

### Enable Debug Mode
Debug mode is enabled by default for development. For production:
```python
app.run(host='0.0.0.0', port=5000, debug=False)
```

### Auto-cleanup Old Files
Add to crontab:
```bash
# Clean files older than 24 hours
0 * * * * find /path/to/uploads -type f -mtime +1 -delete
0 * * * * find /path/to/outputs -type f -mtime +1 -delete
```

## 📞 Support

Having issues? Check:
1. All dependencies are installed (`./setup.sh`)
2. Port 5000 is not in use
3. FFmpeg is working (`ffmpeg -version`)
4. yt-dlp is updated (`pip3 install --upgrade yt-dlp`)

## 🎉 Enjoy!

Your web interface is ready! Open your browser and start converting and downloading media files with a beautiful, easy-to-use interface.

**Made with ❤️ for WSL Ubuntu Cloud**

---

**Quick Links:**
- [Main README](README.md) - Full documentation
- [Quick Start Guide](QUICKSTART.md) - Fast setup
- [Usage Examples](EXAMPLES.md) - Detailed examples

