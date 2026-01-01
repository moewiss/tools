# 🚀 Quick Install - Web Interface

## For WSL Ubuntu (Your Setup)

### Step 1: Navigate to Project
```bash
cd /mnt/d/Desktop/rkieh-solutions-tools1
```

### Step 2: Install Flask
```bash
pip3 install flask werkzeug --break-system-packages
```

### Step 3: Start Web Server
```bash
chmod +x start_web.sh
./start_web.sh
```

### Step 4: Open Browser
Open your browser and go to:
```
http://localhost:5000
```

Or from Windows/network:
```
http://172.25.26.140:5000
```

## That's It! 🎉

You should now see a beautiful web interface where you can:
- ✅ Drag & drop video files to convert
- ✅ Paste YouTube URLs to download
- ✅ See real-time progress
- ✅ Download your converted files

---

## Troubleshooting

### "Module not found"
```bash
pip3 install flask werkzeug yt-dlp --break-system-packages
```

### "Port already in use"
```bash
sudo kill -9 $(lsof -t -i:5000)
```

### "ffmpeg not found"
```bash
sudo apt install ffmpeg -y
```

---

## Screenshots Preview

### 🎨 Main Interface
- Dark modern theme
- Gradient accents
- Smooth animations

### 📤 Upload Area
- Drag & drop support
- File size indicator
- Format validation

### 📊 Progress Tracking
- Real-time progress bar
- Status messages
- Percentage indicator

### ✅ Results
- Download button
- File information
- Success animation

---

## Quick Commands Reference

**Start server:**
```bash
./start_web.sh
```

**Stop server:**
Press `CTRL+C` in the terminal

**Update yt-dlp:**
```bash
pip3 install --upgrade yt-dlp --break-system-packages
```

**Check status:**
```bash
python3 web_app.py --help
```

---

Enjoy your new web interface! 🎉

