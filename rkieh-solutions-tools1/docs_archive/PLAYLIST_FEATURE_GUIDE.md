# YouTube Playlist Download Feature 🎵

## Overview

The Media Tool now includes **smart playlist detection** with video selection! You can download entire playlists or pick specific videos.

## ✨ Features

### 1. **Automatic Playlist Detection**
- Paste any YouTube playlist URL
- Tool automatically detects if it's a playlist
- Shows confirmation modal before downloading

### 2. **Video Selection Options**
- ✅ **Download All**: Get the entire playlist
- ✅ **Select Specific Videos**: Choose which videos to download
- ✅ **Visual Interface**: See all videos with titles and durations
- ✅ **Quick Actions**: Select All / Deselect All buttons

### 3. **Smart Download Management**
- Individual progress tracking for each video
- Automatic ZIP packaging for multiple videos
- Single download button for easy access
- Error handling for failed downloads

### 4. **Confirmation Dialogs**
- Asks before downloading full playlists
- Confirms selected video count
- Prevents accidental large downloads

## 🚀 How to Use

### Method 1: Download Entire Playlist

1. **Go to Media Converter:**
   - http://localhost:5000/tool/media-converter

2. **Paste Playlist URL:**
   ```
   https://www.youtube.com/playlist?list=PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf
   ```

3. **Playlist Modal Appears:**
   - Shows playlist title
   - Displays video count
   - Lists all videos

4. **Click "Download All":**
   - Confirms you want all videos
   - Downloads all and packages as ZIP

### Method 2: Select Specific Videos

1. **Paste Playlist URL**

2. **In the Modal:**
   - Browse through video list
   - Check boxes next to videos you want
   - Or use "Select All" then uncheck unwanted videos

3. **Click "Download Selected":**
   - Shows count of selected videos
   - Confirms download
   - Downloads and packages as ZIP

### Method 3: Cancel and Download Single Video

1. **Paste Playlist URL**

2. **In the Modal:**
   - Click "Cancel"
   - Modify URL to single video
   - Download normally

## 📋 Supported Playlist Types

| Type | Example URL | Supported |
|------|-------------|-----------|
| **Public Playlists** | `youtube.com/playlist?list=...` | ✅ |
| **User Playlists** | `youtube.com/playlist?list=...` | ✅ |
| **Watch Later** | Private playlists | ❌ |
| **Liked Videos** | Private playlists | ❌ |
| **Mix Playlists** | Auto-generated mixes | ⚠️ May work |

## 🎯 Features Breakdown

### Playlist Detection Modal

```
┌─────────────────────────────────────────────┐
│  🎵 Playlist Detected!                  [×] │
├─────────────────────────────────────────────┤
│  Playlist Title: My Awesome Playlist        │
│  25 videos found                            │
│  ⚠️ Warning: May take time & storage        │
│                                             │
│  [Select All] [Deselect All]  0 of 25 ✓    │
│                                             │
│  ☐ Video 1 - Title Here (3:45)             │
│  ☐ Video 2 - Another Title (5:12)          │
│  ☐ Video 3 - More Content (2:30)           │
│  ... (scrollable list)                      │
│                                             │
│  [Cancel] [Download All (25)]  [Download    │
│                                 Selected]    │
└─────────────────────────────────────────────┘
```

### Progress Tracking

When downloading multiple videos:
- Shows current video number (e.g., "Downloading video 3 of 15...")
- Progress bar updates for each video
- Final message shows completion count

### Output Files

**Single Video:**
- Direct download of video/audio file
- Original YouTube title as filename

**Multiple Videos:**
- All files packaged in `playlist_downloads.zip`
- Each file named with original YouTube title
- Easy extraction and organization

## 💡 Pro Tips

### 1. **Check Storage Space**
Before downloading large playlists:
- Video quality "best" can be 50-200MB per video
- Audio (MP3) is typically 3-10MB per video
- Calculate: Number of videos × Average size

### 2. **Select Quality First**
- Choose quality BEFORE pasting playlist URL
- Lower quality = faster downloads + less storage
- 720p is a good balance

### 3. **Use Audio Format for Music Playlists**
- Select "Audio/MP3" format
- Much smaller files
- Perfect for music playlists

### 4. **Batch Processing**
- Select specific videos across multiple playlists
- Download separately
- Organize manually if needed

### 5. **Internet Connection**
- Stable connection recommended
- Large playlists may take 10-30+ minutes
- Don't close browser during download

## ⚙️ Advanced Usage

### Download Playlist via Command Line

```bash
# Get all videos in a playlist
python media_tool.py download "https://youtube.com/playlist?list=PLxxx..." -o ~/Playlists

# Get playlist as MP3
python media_tool.py download "https://youtube.com/playlist?list=PLxxx..." -f audio

# Specific quality
python media_tool.py download "https://youtube.com/playlist?list=PLxxx..." -q 720p
```

### Processing After Download

```bash
# Extract ZIP
unzip playlist_downloads.zip -d MyPlaylist/

# Convert all to different format
python media_tool.py convert MyPlaylist/*.mp4 -o Converted/ -t mp4_to_mp3
```

## 🚨 Troubleshooting

### Issue: Modal doesn't appear
**Solution:**
- Check browser console (F12)
- Ensure JavaScript is enabled
- Try refreshing the page

### Issue: "Failed to check URL"
**Solution:**
- Verify playlist is public
- Check internet connection
- Try copying URL again from YouTube

### Issue: Some videos fail to download
**Solution:**
- Age-restricted videos may fail
- Private or removed videos will be skipped
- Check final ZIP for successful downloads

### Issue: Download stuck at "Checking URL..."
**Solution:**
- Very large playlists (100+ videos) take longer to check
- Wait up to 30 seconds
- If still stuck, refresh and try again

### Issue: ZIP file won't open
**Solution:**
- Ensure download completed (100%)
- File may be large, give it time to extract
- Use modern extraction tool (7-Zip, WinRAR, etc.)

## 📊 Performance Expectations

| Videos | Format | Est. Time | Est. Size |
|--------|--------|-----------|-----------|
| 5 videos | MP3 | 1-2 min | 20-50 MB |
| 5 videos | Best Video | 3-5 min | 250-500 MB |
| 20 videos | MP3 | 5-10 min | 100-200 MB |
| 20 videos | Best Video | 15-30 min | 1-2 GB |
| 50+ videos | MP3 | 20-30 min | 300-500 MB |
| 50+ videos | Best Video | 1-2 hours | 3-10 GB |

*Times vary based on internet speed and video quality*

## 🎬 Example Workflows

### Workflow 1: Download Music Album Playlist

1. Find album playlist on YouTube
2. Select "Audio/MP3" format
3. Paste playlist URL
4. Click "Download All"
5. Extract ZIP
6. Import to music library

### Workflow 2: Download Tutorial Series (Select Specific Videos)

1. Find tutorial playlist
2. Select "Video" format, 720p quality
3. Paste playlist URL
4. In modal, check only videos you need
5. Click "Download Selected"
6. Extract and watch offline

### Workflow 3: Download and Convert

1. Download playlist as video (best quality)
2. Extract ZIP to folder
3. Use batch convert to MP3
4. Keep original videos for later

## 🔧 Backend Details (For Developers)

### New Endpoints

**POST /check-playlist**
- Checks if URL is playlist
- Returns video list without downloading
- Uses yt-dlp with `extract_flat=True`

**POST /download-youtube** (Enhanced)
- Now accepts `urls` array for multiple videos
- Automatically packages multiple downloads as ZIP
- Tracks progress per video

### Response Format

```json
{
  "is_playlist": true,
  "playlist_title": "My Playlist",
  "video_count": 25,
  "videos": [
    {
      "id": "abc123",
      "title": "Video Title",
      "duration": 225,
      "url": "https://youtube.com/watch?v=abc123"
    }
  ]
}
```

## 📚 Related Features

- **Single Video Download**: Still works as before
- **YouTube Shorts**: Detected and downloadable
- **Media Converter**: Convert downloaded videos
- **Batch Processing**: Convert multiple playlist downloads

## ✅ Summary

### What Works:
✅ Automatic playlist detection
✅ Video selection interface
✅ Download all or selected videos
✅ ZIP packaging for multiple videos
✅ Progress tracking per video
✅ Confirmation dialogs
✅ Error handling

### What's New:
- Smart URL checking
- Interactive video selector
- Warning about storage/time
- Select/Deselect all buttons
- Visual video list with durations
- Separate "Download All" vs "Download Selected"

### What to Remember:
- Large playlists take time
- Check storage space first
- Use MP3 for music playlists
- Private playlists won't work
- ZIP file for multiple videos

---

**Ready to download playlists!** Go to: http://localhost:5000/tool/media-converter 🚀

