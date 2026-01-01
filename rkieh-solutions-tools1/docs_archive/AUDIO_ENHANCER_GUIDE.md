# 🎙️ Audio Enhancer - Guide

## Overview

The **Audio Enhancer** tool cleans voice recordings and removes background noise using advanced audio processing techniques. Perfect for:

- **Podcasts & Voice Recordings**
- **Voice Messages & Calls**
- **Interviews & Lectures**
- **YouTube Audio**
- **Music Production**

---

## ✨ Features

### 1. **Noise Reduction**
Remove background noise with 4 intensity levels:
- **None** - No noise reduction applied
- **Light** - Subtle noise reduction (good for clean recordings)
- **Medium** ⭐ *Recommended* - Balanced noise reduction
- **Heavy** - Aggressive noise reduction (for very noisy recordings)

### 2. **Voice Enhancement**
- Boosts frequencies typical for human speech (200Hz - 3000Hz)
- Applies dynamic range compression for consistent volume
- Makes voices clearer and more intelligible

### 3. **Audio Normalization**
- Normalizes volume levels across the entire audio
- Ensures consistent loudness
- Prevents audio clipping

### 4. **Silence Removal**
- Automatically detects and removes silent portions
- Perfect for voice recordings with pauses
- Reduces file size

---

## 🚀 How to Use

### Step 1: Upload Audio File
1. Click "📁 Choose Audio File"
2. Select your audio file
3. Supported formats: **MP3, WAV, M4A, OGG**
4. Maximum file size: **100MB**

### Step 2: Choose Enhancement Options

**Noise Reduction Level:**
- Start with "Medium" (recommended)
- Adjust based on results

**Enhancement Options:**
- ☑️ **Enhance Voice Clarity** - Recommended for speech
- ☑️ **Normalize Audio Levels** - Recommended for all audio
- ☐ **Remove Silence** - Enable for voice recordings

### Step 3: Enhance Audio
1. Click "🎯 Enhance Audio"
2. Wait for processing (usually 10-30 seconds)
3. Preview enhanced audio
4. Download result

---

## 💡 Tips for Best Results

### For Podcasts & Interviews:
```
✅ Noise Reduction: Medium
✅ Enhance Voice: ON
✅ Normalize Audio: ON
✅ Remove Silence: ON (if desired)
```

### For Music Recordings:
```
✅ Noise Reduction: Light or Medium
✅ Enhance Voice: OFF
✅ Normalize Audio: ON
❌ Remove Silence: OFF
```

### For Very Noisy Recordings:
```
✅ Noise Reduction: Heavy
✅ Enhance Voice: ON
✅ Normalize Audio: ON
✅ Remove Silence: Optional
```

### For Clean Recordings:
```
✅ Noise Reduction: Light
✅ Enhance Voice: ON
✅ Normalize Audio: ON
❌ Remove Silence: OFF
```

---

## 🎯 What Each Option Does

### **Noise Reduction**
Uses high-pass and low-pass filters to remove unwanted frequencies:
- **Light:** High-pass filter at 80Hz
- **Medium:** High-pass at 100Hz + Low-pass at 8000Hz
- **Heavy:** High-pass at 120Hz + Low-pass at 7000Hz

### **Voice Enhancement**
- Applies dynamic range compression (threshold: -20dB, ratio: 3:1)
- Boosts mid-frequencies where human voice resides
- Evens out volume differences

### **Normalization**
- Analyzes entire audio
- Adjusts volume to optimal level
- Prevents distortion

### **Silence Removal**
- Detects silence (threshold: -14dB below average)
- Minimum silence duration: 500ms
- Removes detected silent sections
- Concatenates remaining audio

---

## 📊 Technical Specifications

**Supported Input Formats:**
- MP3, WAV, M4A, OGG, FLAC, AAC

**Output Format:**
- MP3 (192 kbps, highest quality)

**Processing:**
- Uses pydub for audio manipulation
- FFmpeg for audio encoding/decoding
- Real-time progress tracking

**File Size Limit:**
- Maximum: 100MB
- Typical processing time: 10-60 seconds depending on file size

---

## 🔧 Installation

The Audio Enhancer requires FFmpeg to be installed on your system.

### Linux (Ubuntu/Debian):
```bash
sudo apt update
sudo apt install ffmpeg -y
```

### macOS:
```bash
brew install ffmpeg
```

### Windows:
Download from: https://ffmpeg.org/download.html

### Install Python Dependencies:
```bash
pip install pydub noisereduce
```

Or use the virtual environment setup:
```bash
bash setup_and_start.sh
```

---

## 🎨 Access the Tool

1. **Start the web app:**
   ```bash
   bash setup_and_start.sh
   ```

2. **Open browser:** http://localhost:5001

3. **Navigate to:** Tools → Audio Enhancer

Or direct link: http://localhost:5001/tool/audio-enhancer

---

## 📱 Use Cases

### 1. **Podcast Production**
Clean up podcast audio before publishing:
- Remove room echo
- Reduce background hum
- Normalize voice levels
- Remove long pauses

### 2. **Video Content**
Enhance audio for YouTube videos:
- Clean voice-overs
- Remove background noise
- Improve clarity
- Make speech more intelligible

### 3. **Voice Messages**
Clean up voice messages and calls:
- Remove phone static
- Enhance voice clarity
- Normalize volume

### 4. **Interviews & Lectures**
Improve recording quality:
- Remove ambient noise
- Enhance speaker's voice
- Remove coughs and pauses

### 5. **Music Production**
Pre-process vocals:
- Remove recording noise
- Normalize levels
- Prepare for mixing

---

## ⚠️ Important Notes

1. **Original Quality Matters:**
   - Better input = better output
   - Cannot fully recover extremely poor recordings

2. **Experiment with Settings:**
   - Try different noise reduction levels
   - Compare results
   - Find what works best for your audio

3. **Backup Original:**
   - Always keep original files
   - Enhancement is a lossy process

4. **Processing Time:**
   - Depends on file size
   - Typically 10-60 seconds
   - Large files may take longer

---

## 🆘 Troubleshooting

### **"No audio file provided"**
- Make sure you selected a file before clicking "Enhance Audio"

### **"File size too large"**
- Maximum size is 100MB
- Compress or trim your audio file first

### **"Enhancement failed"**
- Check if FFmpeg is installed
- Verify audio file is not corrupted
- Try a different audio format

### **Poor Results**
- Try adjusting noise reduction level
- Very noisy recordings may need heavy reduction
- Clean recordings may sound worse with heavy reduction

---

## 🎉 Enjoy Crystal Clear Audio!

The Audio Enhancer tool makes professional audio enhancement accessible to everyone. Experiment with different settings to find what works best for your specific audio needs!

**Need Help?** Contact RKIEH Solutions support.

