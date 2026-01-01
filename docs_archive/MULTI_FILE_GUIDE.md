# 🎯 Multi-File & Bidirectional Conversion Guide

## 🆕 New Features

### ✨ What's New
1. **MP3 to MP4 Conversion** - Convert audio files to video format
2. **Multi-File Upload** - Upload and convert multiple files at once
3. **Folder Upload** - Select entire folders to convert
4. **Batch Processing** - All files converted simultaneously
5. **ZIP Download** - Multiple files packaged into one ZIP

---

## 🔄 Two-Way Conversion

### Video → MP3 (MP4 to MP3)
Convert video files to audio format
- **Input:** MP4, MKV, AVI, MOV, WebM, FLV
- **Output:** MP3
- **Quality:** 128k, 192k, 256k, 320k bitrate options

### Audio → Video (MP3 to MP4)
Convert audio files to video format with solid color background
- **Input:** MP3, M4A, AAC, WAV, FLAC, OGG
- **Output:** MP4 (1280x720)
- **Use Case:** Upload to YouTube, social media, video platforms

---

## 🌐 Web Interface Usage

### Step 1: Choose Conversion Direction
Click one of the conversion type buttons:
- **Video → MP3** (extract audio from videos)
- **MP3 → Video** (create video from audio)

### Step 2: Upload Files

#### Option A: Select Multiple Files
1. Click **"Select Files"** button
2. Hold `Ctrl` (Windows) or `Cmd` (Mac) to select multiple files
3. Click **Open**

#### Option B: Select Entire Folder
1. Click **"Select Folder"** button
2. Choose a folder containing your media files
3. All compatible files will be added

#### Option C: Drag & Drop
1. Open your file explorer
2. Select multiple files or a folder
3. Drag and drop onto the upload area

### Step 3: Review Selected Files
- See all selected files in the list
- Remove individual files by clicking the ❌ button
- Clear all files with **"Clear All"** button
- File count displayed at top

### Step 4: Configure Settings
- **Audio Quality:** Choose bitrate (192k recommended)
- Higher bitrate = better quality but larger file size

### Step 5: Convert!
1. Click **"Convert X File(s)"** button
2. Watch real-time progress
3. Download your converted file(s)

---

## 🖥️ Command-Line Usage

### Convert Video to MP3

**Single file:**
```bash
python3 media_tool.py convert video.mp4 -t mp4_to_mp3
```

**Multiple files:**
```bash
python3 media_tool.py convert video1.mp4 video2.mp4 video3.mp4 -t mp4_to_mp3 -b 320k
```

**Entire folder:**
```bash
python3 media_tool.py convert /path/to/videos/ -t mp4_to_mp3 -o output/
```

### Convert MP3 to MP4

**Single file:**
```bash
python3 media_tool.py convert song.mp3 -t mp3_to_mp4
```

**Multiple files:**
```bash
python3 media_tool.py convert song1.mp3 song2.mp3 song3.mp3 -t mp3_to_mp4
```

**Entire folder:**
```bash
python3 media_tool.py convert /path/to/music/ -t mp3_to_mp4 -o output/
```

**With custom background image:**
```bash
python3 media_tool.py convert song.mp3 -t mp3_to_mp4 -i background.jpg
```

---

## 📊 Batch Processing

### How It Works
- Upload up to 50+ files at once
- All files converted in parallel (4 workers by default)
- Progress tracked in real-time
- Single file = direct download
- Multiple files = automatically packaged in ZIP

### Performance
| Files | Approx. Time (1GB total) |
|-------|-------------------------|
| 1 file | 30-60 seconds |
| 5 files | 1-2 minutes |
| 10 files | 2-4 minutes |
| 20+ files | 4-8 minutes |

*Depends on file size, format, and CPU speed*

---

## 💡 Use Cases

### 1. Music Library Conversion
**Scenario:** Convert entire music collection to MP4 for YouTube uploads

```bash
python3 media_tool.py convert ~/Music/ -t mp3_to_mp4 -o ~/Videos/Music/
```

### 2. Video to Audio Extraction
**Scenario:** Extract audio from multiple tutorial videos

Via Web:
1. Select "Video → MP3"
2. Click "Select Folder"
3. Choose your tutorials folder
4. Set quality to 192k
5. Convert and download ZIP

### 3. Podcast Processing
**Scenario:** Convert podcast episodes for video platforms

```bash
python3 media_tool.py convert podcast_*.mp3 -t mp3_to_mp4 -i podcast_cover.jpg
```

### 4. Social Media Content
**Scenario:** Prepare audio for Instagram/TikTok (need video format)

Via Web:
1. Select "MP3 → Video"
2. Upload your audio files
3. Convert to MP4
4. Upload to social media

---

## 🎨 MP3 to MP4 Technical Details

### Output Specifications
- **Resolution:** 1280x720 (HD)
- **Video Codec:** H.264
- **Audio Codec:** AAC (192k)
- **Background:** Solid black color (customizable with -i flag)
- **Duration:** Matches audio length

### Why Convert MP3 to MP4?
- Upload audio to YouTube
- Share on video platforms
- Add to video editing timeline
- Social media requirements
- Professional presentations

---

## 📁 File Organization

### Web Interface
```
uploads/
└── [job-id]/
    ├── file1.mp4
    ├── file2.mp4
    └── file3.mp4

outputs/
└── [job-id]/
    ├── file1.mp3
    ├── file2.mp3
    ├── file3.mp3
    └── converted_files.zip  (if multiple files)
```

### Command-Line
```
input_folder/
├── video1.mp4
├── video2.mp4
└── video3.mp4

output_folder/
├── video1.mp3
├── video2.mp3
└── video3.mp3
```

---

## ⚠️ Limitations & Tips

### File Size
- **Web:** Max 500MB per file
- **CLI:** No strict limit (disk space dependent)

### Number of Files
- **Web:** Recommended up to 50 files at once
- **CLI:** Unlimited (depends on system resources)

### Performance Tips
1. **Smaller batches** = faster feedback
2. **Close other programs** for faster processing
3. **SSD storage** speeds up conversion
4. **Adjust workers** with `-w` flag (CLI)
   ```bash
   python3 media_tool.py convert *.mp4 -w 8  # Use 8 parallel workers
   ```

### Best Practices
- ✅ Organize files in folders before conversion
- ✅ Use consistent naming for easy sorting
- ✅ Test with 1-2 files first
- ✅ Keep original files until verifying output
- ✅ Delete old uploads/outputs to save space

---

## 🔧 Advanced Options

### Command-Line Arguments

```bash
python3 media_tool.py convert [files...] [options]

Options:
  -t, --type {mp4_to_mp3,mp3_to_mp4}
                        Conversion type (default: mp4_to_mp3)
  -o, --output DIR      Output directory
  -b, --bitrate RATE    Audio bitrate for MP4→MP3 (default: 192k)
  -i, --image FILE      Background image for MP3→MP4 conversion
  -w, --workers NUM     Number of parallel workers (default: 4)
```

### Examples

**High quality with 8 workers:**
```bash
python3 media_tool.py convert *.mp4 -t mp4_to_mp3 -b 320k -w 8
```

**MP3 to MP4 with custom image:**
```bash
python3 media_tool.py convert album/*.mp3 -t mp3_to_mp4 -i album_art.jpg -o videos/
```

**Entire folder with specific output:**
```bash
python3 media_tool.py convert ~/Downloads/videos/ -t mp4_to_mp3 -o ~/Music/converted/ -b 256k
```

---

## 🐛 Troubleshooting

### "No valid files selected"
- Check file format matches conversion type
- Verify file isn't corrupted
- Check file size (max 500MB web)

### "Conversion failed"
- Ensure FFmpeg is installed: `ffmpeg -version`
- Check disk space: `df -h`
- Verify file isn't DRM protected

### ZIP file not created
- Only happens with 2+ files
- Single file gets direct download
- Check outputs folder manually

### Slow conversion
- Reduce number of files per batch
- Close other applications
- Check CPU usage
- Adjust workers with `-w` flag

---

## 📞 Quick Reference

| Task | Command/Action |
|------|----------------|
| Multi-file web upload | Ctrl+Click or Cmd+Click files |
| Folder web upload | Click "Select Folder" button |
| Clear file list | Click "Clear All" button |
| Remove one file | Click ❌ on file item |
| CLI batch convert | `convert file1 file2 file3` |
| CLI folder convert | `convert /path/to/folder/` |
| Change workers | Add `-w 8` flag |
| Custom bitrate | Add `-b 320k` flag |

---

## 🎉 Summary

You can now:
- ✅ Convert MP4 → MP3 (video to audio)
- ✅ Convert MP3 → MP4 (audio to video)
- ✅ Upload multiple files at once
- ✅ Upload entire folders
- ✅ Download as ZIP (multiple files)
- ✅ Track progress in real-time
- ✅ Use via web or command-line

**Enjoy your powerful multi-file converter!** 🚀

