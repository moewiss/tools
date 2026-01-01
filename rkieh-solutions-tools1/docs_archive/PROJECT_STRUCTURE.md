# 📁 Project Structure

## Overview

This project provides both **command-line** and **web interface** tools for media conversion and downloading.

```
rkieh-solutions-tools1/
│
├── 🎯 Core Scripts
│   ├── media_tool.py          # Main CLI tool
│   ├── web_app.py             # Flask web server
│   ├── setup.sh               # Installation script (Linux)
│   ├── start_web.sh           # Start web interface (Linux)
│   └── start_web.bat          # Start web interface (Windows)
│
├── 🌐 Web Interface
│   ├── templates/
│   │   └── index.html         # Main web page
│   └── static/
│       ├── css/
│       │   └── style.css      # Styles & animations
│       └── js/
│           └── main.js        # Interactive functionality
│
├── 📚 Documentation
│   ├── README.md              # Main documentation
│   ├── QUICKSTART.md          # Quick start guide
│   ├── EXAMPLES.md            # Usage examples
│   ├── WEB_INTERFACE.md       # Web interface guide
│   └── PROJECT_STRUCTURE.md   # This file
│
├── 🔧 Configuration
│   ├── requirements.txt       # Python dependencies
│   ├── .gitignore            # Git ignore rules
│   └── example_urls.txt      # Example URLs template
│
├── 🧪 Testing
│   └── test_install.sh        # Installation test script
│
└── 📦 Runtime Directories (created automatically)
    ├── uploads/               # Temporary upload storage
    └── outputs/               # Processed output files
```

## 🎯 Main Components

### Command-Line Tool (`media_tool.py`)
- Convert MP4 to MP3
- Download from YouTube
- Batch processing
- Multi-threaded conversion

### Web Interface (`web_app.py`)
- Flask-based web server
- Beautiful modern UI
- Drag & drop upload
- Real-time progress tracking
- REST API endpoints

## 🌐 Web Interface Files

### HTML Template (`templates/index.html`)
- Responsive layout
- Tab-based navigation
- File upload interface
- Progress indicators
- Result display

### CSS Styling (`static/css/style.css`)
- Modern dark theme
- Gradient effects
- Smooth animations
- Responsive design
- Custom components

### JavaScript (`static/js/main.js`)
- File upload handling
- Drag & drop functionality
- AJAX requests
- Progress polling
- Error handling

## 📚 Documentation Files

| File | Purpose |
|------|---------|
| `README.md` | Complete project documentation |
| `QUICKSTART.md` | Fast setup guide for beginners |
| `EXAMPLES.md` | Detailed usage examples |
| `WEB_INTERFACE.md` | Web interface specific guide |
| `PROJECT_STRUCTURE.md` | This file - project organization |

## 🔧 Configuration Files

### `requirements.txt`
Python package dependencies:
- `yt-dlp` - YouTube downloader
- `flask` - Web framework
- `werkzeug` - WSGI utilities

### `.gitignore`
Excludes from version control:
- Python cache files
- Media files (MP4, MP3, etc.)
- Upload/output directories
- OS-specific files

### `example_urls.txt`
Template for batch URL downloads

## 🚀 Entry Points

### For Command-Line Usage
```bash
python3 media_tool.py [command] [options]
```

### For Web Interface
```bash
# Linux/WSL
./start_web.sh

# Windows
start_web.bat

# Manual
python3 web_app.py
```

## 📦 Dependencies

### System Requirements
- **Python 3.7+**
- **FFmpeg** (for video/audio conversion)
- **pip3** (Python package manager)

### Python Packages
- **yt-dlp** - Media downloading
- **flask** - Web server
- **werkzeug** - File handling

### Optional
- **dos2unix** - Line ending conversion (if needed)

## 🔄 Data Flow

### Command-Line Conversion
```
Input File → media_tool.py → FFmpeg → Output MP3
```

### Command-Line Download
```
YouTube URL → yt-dlp → media_tool.py → Output File
```

### Web Interface Conversion
```
Browser → Upload → web_app.py → media_tool.py → FFmpeg → Output → Download
```

### Web Interface Download
```
Browser → URL → web_app.py → yt-dlp → Output → Download
```

## 🗂️ Directory Usage

### `uploads/`
- Temporary storage for uploaded files
- Created automatically by web server
- Can be cleaned regularly

### `outputs/`
- Stores processed files
- Organized by job ID
- Files available for download

## 🎨 UI Components

The web interface uses:
- **Font Awesome** icons (CDN)
- **Custom CSS** animations
- **Vanilla JavaScript** (no frameworks)
- **Flask Jinja2** templating

## 🔌 API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | Serve web interface |
| `/upload` | POST | Upload file for conversion |
| `/download-youtube` | POST | Start YouTube download |
| `/status/<job_id>` | GET | Check job progress |
| `/download/<job_id>` | GET | Download result file |
| `/jobs` | GET | List all jobs |

## 💾 Storage

### Temporary Files
- Uploads stored in `uploads/`
- Organized by job UUID
- Should be cleaned periodically

### Output Files
- Results stored in `outputs/`
- Organized by job UUID
- Persist until manually deleted

## 🔒 Security Considerations

1. **File Size Limits**: 500MB max upload
2. **File Type Validation**: Only video files accepted
3. **Secure Filenames**: Using `secure_filename()`
4. **Local Processing**: No external data sharing
5. **Temporary Storage**: Files can be auto-cleaned

## 🚀 Deployment

### Development
```bash
python3 web_app.py  # Debug mode enabled
```

### Production
- Disable debug mode in `web_app.py`
- Use production WSGI server (gunicorn, uwsgi)
- Set up reverse proxy (nginx, apache)
- Configure SSL/TLS
- Enable auto-cleanup cron jobs

## 📊 Performance

- **Parallel Processing**: Multiple conversions simultaneously
- **Background Jobs**: Non-blocking task execution
- **Efficient Storage**: Streaming file operations
- **Resource Management**: Automatic cleanup options

## 🛠️ Customization

### Change Port
Edit `web_app.py`:
```python
app.run(host='0.0.0.0', port=YOUR_PORT)
```

### Change Upload Limit
Edit `web_app.py`:
```python
app.config['MAX_CONTENT_LENGTH'] = SIZE_IN_BYTES
```

### Add New Features
1. Add route in `web_app.py`
2. Update `index.html` template
3. Add styling in `style.css`
4. Add interactivity in `main.js`

## 📱 Responsive Design

The web interface is fully responsive:
- **Desktop**: Full feature layout
- **Tablet**: Optimized grid layout
- **Mobile**: Single column, touch-friendly

## 🎉 Quick Reference

| Task | File to Edit |
|------|-------------|
| Add CLI feature | `media_tool.py` |
| Add web route | `web_app.py` |
| Change UI layout | `templates/index.html` |
| Modify styling | `static/css/style.css` |
| Add interactivity | `static/js/main.js` |
| Update dependencies | `requirements.txt` |

---

**Project Version:** 1.0
**Last Updated:** December 2025
**Maintained by:** WSL Ubuntu Team

