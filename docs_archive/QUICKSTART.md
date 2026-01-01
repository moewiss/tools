# 🚀 Quick Start Guide

## Installation (5 minutes)

### Step 1: Navigate to the project directory
```bash
cd /mnt/d/Desktop/rkieh-solutions-tools1
```

### Step 2: Run the setup script
```bash
chmod +x setup.sh
./setup.sh
```

That's it! The tool is ready to use. 🎉

---

## Common Usage

### 🎵 Convert MP4 to MP3

**Single file:**
```bash
python3 media_tool.py convert video.mp4
```

**All MP4s in current folder:**
```bash
python3 media_tool.py convert *.mp4
```

**From Windows folder:**
```bash
python3 media_tool.py convert /mnt/c/Users/area51/Downloads/*.mp4 -o ~/Music/
```

---

### 📥 Download from YouTube

**Download video:**
```bash
python3 media_tool.py download "https://www.youtube.com/watch?v=VIDEO_ID"
```

**Download as MP3:**
```bash
python3 media_tool.py download "https://www.youtube.com/watch?v=VIDEO_ID" -f mp3
```

**Download to specific folder:**
```bash
python3 media_tool.py download "YOUTUBE_URL" -f mp3 -o ~/Music/
```

---

## Pro Tips

### Create shortcuts (aliases)
```bash
# Add to ~/.bashrc
echo "alias mp3convert='python3 ~/rkieh-solutions-tools1/media_tool.py convert'" >> ~/.bashrc
echo "alias ytdl='python3 ~/rkieh-solutions-tools1/media_tool.py download'" >> ~/.bashrc
source ~/.bashrc

# Now use them like this:
mp3convert video.mp4
ytdl "YOUTUBE_URL" -f mp3
```

### Batch download from list
```bash
# Create a file with URLs
nano urls.txt

# Add your URLs (one per line):
# https://www.youtube.com/watch?v=VIDEO_ID_1
# https://www.youtube.com/watch?v=VIDEO_ID_2

# Download all:
while read url; do python3 media_tool.py download "$url" -f mp3; done < urls.txt
```

### Access from Windows
Your files are located at:
```
\\wsl$\Ubuntu\home\area51wsl\rkieh-solutions-tools1
```

Or if you want to work with Windows files:
```bash
# Access Windows Downloads folder
cd /mnt/c/Users/area51/Downloads

# Convert files there
python3 /mnt/d/Desktop/rkieh-solutions-tools1/media_tool.py convert *.mp4
```

---

## Troubleshooting

**If download fails:**
```bash
pip3 install --upgrade yt-dlp
```

**If ffmpeg error:**
```bash
sudo apt install ffmpeg -y
```

**Need help?**
```bash
python3 media_tool.py --help
python3 media_tool.py convert --help
python3 media_tool.py download --help
```

---

## Your System Info
- **WSL IP:** 172.25.26.140
- **Username:** area51wsl
- **Hostname:** DESKTOP-G5NQHFF
- **Project Path:** /mnt/d/Desktop/rkieh-solutions-tools1

Enjoy! 🎉

