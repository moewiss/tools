# 📚 Usage Examples

## Conversion Examples

### Basic Conversion
```bash
# Convert single file (output in same directory)
python3 media_tool.py convert video.mp4

# Result: video.mp3 created in same folder
```

### Multiple Files
```bash
# Convert multiple specific files
python3 media_tool.py convert video1.mp4 video2.mp4 video3.mp4

# Convert all MP4s in current directory
python3 media_tool.py convert *.mp4

# Convert all videos (multiple formats)
python3 media_tool.py convert *.mp4 *.mkv *.avi
```

### Directory Conversion
```bash
# Convert all videos in a directory
python3 media_tool.py convert /path/to/videos/

# Convert from Windows folder
python3 media_tool.py convert /mnt/c/Users/area51/Videos/
```

### Custom Output
```bash
# Specify output directory
python3 media_tool.py convert video.mp4 -o output/

# Convert with specific bitrate
python3 media_tool.py convert video.mp4 -b 320k

# Both output dir and high quality
python3 media_tool.py convert *.mp4 -o ~/Music/ -b 320k
```

### Performance Tuning
```bash
# Use 8 parallel workers (faster on multi-core CPUs)
python3 media_tool.py convert *.mp4 -w 8

# Use 2 workers (lighter on system resources)
python3 media_tool.py convert *.mp4 -w 2
```

---

## Download Examples

### YouTube Videos

```bash
# Download best quality video
python3 media_tool.py download "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

# Download in 1080p
python3 media_tool.py download "https://youtu.be/VIDEO_ID" -q 1080p

# Download in 720p to save space
python3 media_tool.py download "https://youtu.be/VIDEO_ID" -q 720p -o videos/
```

### Audio Downloads

```bash
# Download as MP3 (audio only)
python3 media_tool.py download "https://www.youtube.com/watch?v=VIDEO_ID" -f mp3

# Download to specific folder
python3 media_tool.py download "YOUTUBE_URL" -f mp3 -o ~/Music/

# Download audio to Windows Music folder
python3 media_tool.py download "YOUTUBE_URL" -f audio -o /mnt/c/Users/area51/Music/
```

### Batch Downloads

```bash
# Download multiple videos
python3 media_tool.py download \
  "https://www.youtube.com/watch?v=VIDEO_1" \
  "https://www.youtube.com/watch?v=VIDEO_2" \
  "https://www.youtube.com/watch?v=VIDEO_3"

# Download multiple as MP3
python3 media_tool.py download \
  "URL1" "URL2" "URL3" \
  -f mp3 -o ~/Downloads/music/

# Download entire playlist
python3 media_tool.py download "https://www.youtube.com/playlist?list=PLAYLIST_ID" -f mp3
```

---

## Advanced Examples

### Combine Operations
```bash
# Download and convert workflow
python3 media_tool.py download "YOUTUBE_URL" -o temp/
python3 media_tool.py convert temp/*.mp4 -o music/ -b 320k
rm -rf temp/
```

### Batch from File
```bash
# Create urls.txt with your links:
cat > urls.txt << EOF
https://www.youtube.com/watch?v=VIDEO_1
https://www.youtube.com/watch?v=VIDEO_2
https://www.youtube.com/watch?v=VIDEO_3
EOF

# Download all as MP3
while read url; do 
  python3 media_tool.py download "$url" -f mp3 -o ~/Music/
done < urls.txt
```

### Process Large Directory
```bash
# Convert all videos in a large directory with 8 workers
python3 media_tool.py convert /mnt/d/MyVideos/ -o /mnt/d/MyMusic/ -w 8 -b 256k
```

### Cross-Platform Paths
```bash
# From WSL, access Windows Downloads
python3 media_tool.py convert /mnt/c/Users/area51/Downloads/*.mp4 -o ~/Music/

# From WSL, save to Windows Desktop
python3 media_tool.py download "YOUTUBE_URL" -f mp3 -o /mnt/c/Users/area51/Desktop/
```

---

## Bitrate Quality Guide

| Bitrate | Quality | Use Case |
|---------|---------|----------|
| 128k | Good | Speech, podcasts, save space |
| 192k | High | General music (default) |
| 256k | Very High | High-quality music |
| 320k | Maximum | Audiophile quality |

**Example:**
```bash
# Podcast conversion (lower quality, smaller files)
python3 media_tool.py convert podcast.mp4 -b 128k

# Music conversion (high quality)
python3 media_tool.py convert album/*.mp4 -b 320k
```

---

## Video Quality Guide

| Quality | Resolution | File Size |
|---------|-----------|-----------|
| 480p | 854×480 | Small |
| 720p | 1280×720 | Medium |
| 1080p | 1920×1080 | Large |
| best | Highest available | Largest |

**Example:**
```bash
# Save bandwidth, download 720p
python3 media_tool.py download "YOUTUBE_URL" -q 720p

# Best quality available
python3 media_tool.py download "YOUTUBE_URL" -q best
```

---

## Real-World Scenarios

### Scenario 1: Music Collection
```bash
# Download your favorite songs as MP3
python3 media_tool.py download \
  "https://www.youtube.com/watch?v=SONG1" \
  "https://www.youtube.com/watch?v=SONG2" \
  "https://www.youtube.com/watch?v=SONG3" \
  -f mp3 -o ~/Music/Favorites/
```

### Scenario 2: Video Archive
```bash
# Download educational videos in 720p
python3 media_tool.py download \
  "https://www.youtube.com/watch?v=COURSE_VIDEO_1" \
  "https://www.youtube.com/watch?v=COURSE_VIDEO_2" \
  -q 720p -o ~/Education/
```

### Scenario 3: Converting Old Collection
```bash
# Convert all old video files to MP3
cd ~/OldVideos
python3 ~/rkieh-solutions-tools1/media_tool.py convert *.* -o ~/Music/Converted/ -w 8
```

### Scenario 4: Podcast Processing
```bash
# Download podcast and convert to low-quality MP3 for mobile
python3 media_tool.py download "PODCAST_URL" -f audio
python3 media_tool.py convert *.m4a -b 96k -o ~/Podcasts/
```

---

## Tips for Best Results

1. **Use full URLs** with quotes for downloads
2. **Start with lower workers** (-w 2) if system is slow
3. **Use 192k bitrate** for general purpose (good balance)
4. **Download to WSL** first, then move to Windows if needed
5. **Test with one file** before batch processing

---

## Need More Help?

```bash
# Show all options
python3 media_tool.py --help

# Conversion help
python3 media_tool.py convert --help

# Download help
python3 media_tool.py download --help
```

