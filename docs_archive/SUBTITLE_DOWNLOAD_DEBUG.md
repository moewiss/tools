# Subtitle Download Debugging Guide

## Current Issue
User reports that after subtitle download completes:
1. Two buttons appear: "Download" and "New Download"
2. "New Download" button works ✅
3. "Download" button does NOTHING ❌
4. In history, "Re-download" button only takes to converter page ❌

## Debugging Steps

### Step 1: Check Browser Console
1. Open browser (Chrome/Edge)
2. Press F12 to open Developer Tools
3. Go to "Console" tab
4. Try downloading a video with subtitles
5. When "Download" button appears, click it
6. Check console for errors

### Step 2: Check Server Logs
After download completes, check terminal for:
```
[SUBTITLE] Starting download for: [URL]
[SUBTITLE] Output directory: [PATH]
[SUBTITLE] Download type: [TYPE]
[SUBTITLE] Download completed. Video title: [TITLE]
[SUBTITLE] Files found in output directory:
[SUBTITLE] - Total files: X
[SUBTITLE] - Video files: X
[SUBTITLE] - Subtitle files: X
[SUBTITLE]   - [filename] (size bytes)
```

### Step 3: Check Download Endpoint
The download button should call: `/download/{job_id}`

This endpoint:
1. Checks if job exists
2. Checks if job is completed
3. Gets `output_path` from job
4. Checks if file exists
5. Sends file to browser

### Step 4: Verify File Path
Check if files are actually being created in `outputs/{job_id}/` folder

### Common Issues

#### Issue 1: File Path is Relative but Should be Absolute
- **Symptom:** File exists but `os.path.exists()` returns False
- **Fix:** Convert to absolute path before checking

#### Issue 2: ZIP File Not Created
- **Symptom:** Multiple files but no ZIP
- **Fix:** Check zipfile creation logic

#### Issue 3: Job Data Lost on Server Restart
- **Symptom:** Download worked but after server reload, job_id not found
- **Fix:** Jobs are stored in memory, lost on restart

#### Issue 4: Browser Blocks Download
- **Symptom:** No error but file doesn't download
- **Fix:** Check browser download settings, popup blockers

## Next Steps
1. Add more logging to download endpoint
2. Check if file_path is valid
3. Verify send_file() is working
4. Test with simple file first

