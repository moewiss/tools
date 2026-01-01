# YouTube Shorts Download Guide

## 📱 What are YouTube Shorts?

YouTube Shorts are vertical, short-form videos (up to 60 seconds) similar to TikTok or Instagram Reels. They have URLs like:
- `https://www.youtube.com/shorts/VIDEO_ID`
- Example: `https://www.youtube.com/shorts/-bRHO5hPbTA`

## ✅ Full Support

Our Media Tool **fully supports** downloading YouTube Shorts in both:
- **Video format** (MP4 - vertical video)
- **Audio format** (MP3 - extract audio only)

## 🚀 How to Download YouTube Shorts

### Method 1: Web Interface (Recommended)

1. **Start the server:**
   ```bash
   python web_app.py
   ```

2. **Open browser:** http://localhost:5000

3. **Go to Media Converter** or visit directly:
   http://localhost:5000/tool/media-converter

4. **Enter the Shorts URL:**
   - Paste: `https://www.youtube.com/shorts/-bRHO5hPbTA`
   - Select format: Video or Audio/MP3
   - Choose quality (for video)
   - Click "Download"

5. **Wait for download** and click "Download File"!

### Method 2: Command Line

#### Download Shorts as Video:
```bash
python media_tool.py download "https://www.youtube.com/shorts/-bRHO5hPbTA"
```

#### Download Shorts as MP3 Audio:
```bash
python media_tool.py download "https://www.youtube.com/shorts/-bRHO5hPbTA" -f audio
```

#### Download with Specific Quality:
```bash
# Best quality
python media_tool.py download "https://www.youtube.com/shorts/-bRHO5hPbTA" -q best

# 720p
python media_tool.py download "https://www.youtube.com/shorts/-bRHO5hPbTA" -q 720p
```

#### Download Multiple Shorts at Once:
```bash
python media_tool.py download \
  "https://www.youtube.com/shorts/-bRHO5hPbTA" \
  "https://www.youtube.com/shorts/ANOTHER_ID" \
  "https://www.youtube.com/shorts/YET_ANOTHER"
```

#### Save to Specific Folder:
```bash
python media_tool.py download "https://www.youtube.com/shorts/-bRHO5hPbTA" -o ~/Downloads/Shorts
```

## 📋 All Supported YouTube Formats

| Type | URL Format | Example | Supported |
|------|-----------|---------|-----------|
| **Regular Videos** | `/watch?v=ID` | `youtube.com/watch?v=dQw4w9WgXcQ` | ✅ |
| **Shorts** | `/shorts/ID` | `youtube.com/shorts/-bRHO5hPbTA` | ✅ |
| **Mobile Links** | `youtu.be/ID` | `youtu.be/dQw4w9WgXcQ` | ✅ |
| **Playlists** | `/playlist?list=` | `youtube.com/playlist?list=...` | ✅ |
| **Live Streams** | `/watch?v=ID` (live) | Any live stream | ✅ |
| **Embedded** | `/embed/ID` | `youtube.com/embed/ID` | ✅ |

## 🎯 Download Options

### Video Download:
- **Best Quality**: Automatically selects highest available
- **1080p**: Full HD (if available)
- **720p**: HD
- **480p**: Standard definition

### Audio Download:
- **Format**: MP3
- **Quality**: 192 kbps (high quality)
- **Extracted from**: Best audio source

## 💡 Tips for Downloading Shorts

### 1. **Quality Considerations**
- Most Shorts are filmed in **vertical orientation** (9:16)
- Resolution varies, typically **720p to 1080p**
- Use "best" quality to get the highest available

### 2. **Audio Extraction**
- Perfect for extracting music from Shorts
- Maintains high audio quality (192kbps MP3)
- Great for creating playlists

### 3. **Batch Downloads**
- Download multiple Shorts at once
- Paste multiple URLs in web interface (one per line)
- Or use command line with multiple URLs

### 4. **File Naming**
- Files are automatically named based on the video title
- Safe characters only (no special characters)
- Extension: `.mp4` for video, `.mp3` for audio

## 🔍 Finding Shorts URLs

### Method 1: Desktop Browser
1. Open YouTube Shorts
2. Click the Share button
3. Copy the link (format: `youtube.com/shorts/ID`)

### Method 2: Mobile App
1. Tap the Share button on a Short
2. Select "Copy Link"
3. Paste into our tool

### Method 3: From Feed
- Right-click on a Short → "Copy link address"

## ⚙️ Advanced Usage

### Convert Shorts to Different Formats

After downloading, you can convert:

```bash
# Download as video
python media_tool.py download "https://www.youtube.com/shorts/-bRHO5hPbTA"

# Then convert to MP3
python media_tool.py convert downloaded_short.mp4 -o audio/ -t mp4_to_mp3

# Or convert to MP4 with custom image
python media_tool.py convert audio.mp3 -o video/ -t mp3_to_mp4 -i cover.jpg
```

### Batch Process Shorts

Create a file `shorts_urls.txt`:
```
https://www.youtube.com/shorts/-bRHO5hPbTA
https://www.youtube.com/shorts/ANOTHER_ID
https://www.youtube.com/shorts/THIRD_ID
```

Download all:
```bash
cat shorts_urls.txt | xargs python media_tool.py download -f audio -o ~/Shorts
```

## 🚨 Common Issues

### Issue: "Video unavailable"
**Solution:** 
- Check if the Short is public
- Verify the URL is correct
- Try downloading as audio only

### Issue: "No formats found"
**Solution:**
- Update yt-dlp: `pip install --upgrade yt-dlp`
- Try different quality setting
- Check your internet connection

### Issue: Slow download speed
**Solution:**
- Use lower quality (720p instead of best)
- Check your internet connection
- YouTube may be throttling

### Issue: File too large
**Solution:**
- Download as audio only (much smaller)
- Use lower quality setting
- Shorts are typically small (<50MB)

## 📊 Performance

| Format | Typical Size | Download Time |
|--------|--------------|---------------|
| Video (1080p) | 10-30 MB | 10-30 seconds |
| Video (720p) | 5-15 MB | 5-15 seconds |
| Audio (MP3) | 1-3 MB | 2-5 seconds |

*Times vary based on internet speed and video length*

## 🎬 Example Workflow

### Scenario: Download trending Shorts for editing

1. **Collect URLs** from YouTube Shorts feed
2. **Save to file** or paste in web interface
3. **Batch download** all at once
4. **Convert if needed** (extract audio, add music, etc.)
5. **Edit** using your favorite video editor

### Example Commands:
```bash
# Download 5 trending Shorts
python media_tool.py download \
  "https://www.youtube.com/shorts/ID1" \
  "https://www.youtube.com/shorts/ID2" \
  "https://www.youtube.com/shorts/ID3" \
  "https://www.youtube.com/shorts/ID4" \
  "https://www.youtube.com/shorts/ID5" \
  -o ~/TrendingShorts -q best
```

## 📚 Related Features

- **Media Converter**: Convert downloaded Shorts between formats
- **Watermark Remover**: Remove watermarks from downloaded Shorts
- **Batch Processing**: Process multiple Shorts simultaneously

## 🆘 Need Help?

If you encounter issues downloading YouTube Shorts:

1. **Update dependencies:**
   ```bash
   pip install --upgrade yt-dlp
   ```

2. **Check FFmpeg:**
   ```bash
   ffmpeg -version
   ```

3. **Test with a known working Short:**
   ```bash
   python media_tool.py download "https://www.youtube.com/shorts/-bRHO5hPbTA"
   ```

4. **Enable verbose output** to see what's happening:
   - The tool already shows detailed progress
   - Check terminal output for error messages

## ✨ Pro Tips

1. **Create a Shorts collection folder:**
   ```bash
   mkdir ~/YouTubeShorts
   python media_tool.py download [URL] -o ~/YouTubeShorts
   ```

2. **Audio-only for music Shorts:**
   ```bash
   python media_tool.py download [URL] -f audio -o ~/ShortsMusic
   ```

3. **Bulk download from playlist** (if Shorts are in a playlist):
   ```bash
   python media_tool.py download "https://youtube.com/playlist?list=..."
   ```

## 🎉 Summary

✅ **YouTube Shorts are fully supported!**
✅ Download as video or audio
✅ Batch download multiple Shorts
✅ Choose quality (best, 1080p, 720p, 480p)
✅ Web interface + Command line
✅ No limitations - download as many as you want!

**Start downloading Shorts now:** http://localhost:5000/tool/media-converter 🚀

