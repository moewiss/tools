# Testing Playlist Feature

## Quick Test URLs

### Small Public Playlists (2-5 videos):
```
https://www.youtube.com/playlist?list=PL59LTecnGM1Mg6I4i_KbS0w5bXQzHXFvf
https://www.youtube.com/playlist?list=PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf
```

### Test Single Video (Should NOT trigger playlist):
```
https://www.youtube.com/watch?v=dQw4w9WgXcQ
```

## Steps to Test:

1. **Open Page:**
   - Go to: http://localhost:5000/tool/media-converter
   - Open Browser Console (Press F12)

2. **Clear Browser Cache:**
   - Press `Ctrl + Shift + R` (Windows) or `Cmd + Shift + R` (Mac)
   - Or: F12 → Network tab → Check "Disable cache"

3. **Test with Single Video:**
   - Paste: `https://www.youtube.com/watch?v=dQw4w9WgXcQ`
   - Click Download
   - **Expected:** Direct download (NO modal)
   - **Console:** Should show `[PLAYLIST CHECK] Single video`

4. **Test with Playlist:**
   - Paste: `https://www.youtube.com/playlist?list=PL59LTecnGM1Mg6I4i_KbS0w5bXQzHXFvf`
   - Click Download
   - **Expected:** Modal appears with video list
   - **Console:** Should show `[PLAYLIST CHECK] IS PLAYLIST!`

## What to Look For in Console:

### Working Correctly:
```
[PLAYLIST CHECK] Starting check for URL: https://youtube.com/playlist?...
[PLAYLIST CHECK] Response status: 200
[PLAYLIST CHECK] Response data: {is_playlist: true, video_count: 5, ...}
[PLAYLIST CHECK] IS PLAYLIST! Showing selector with 5 videos
```

### If Not Working:
```
[PLAYLIST CHECK] Error: Failed to fetch
[PLAYLIST CHECK] Response status: 500
```

## Troubleshooting:

### If Modal Doesn't Appear:

1. **Check Console for Errors**
   - Press F12
   - Look for red errors
   - Share any error messages

2. **Hard Refresh**
   - Ctrl + Shift + R to clear cache
   - Or close and reopen browser

3. **Verify Endpoint**
   - Open new tab: http://localhost:5000/check-playlist
   - Should show "Method Not Allowed" (normal - it's POST only)
   - If shows 404, server needs restart

4. **Check Server Logs**
   - Look at terminal running `python web_app.py`
   - Should see POST requests to /check-playlist

### If Seeing JavaScript Errors:

Common issues:
- `showPlaylistSelector is not defined` → Cache issue, hard refresh
- `fetch is not defined` → Old browser, update browser
- `Cannot read property 'display'` → HTML element missing

## Expected Behavior:

### For Playlists:
```
You paste playlist URL
    ↓
"Checking URL..." (2-5 seconds)
    ↓
Modal appears with:
- Playlist title
- Video count
- List of all videos
- Select All / Deselect All buttons
- Download All button
- Download Selected button
    ↓
You choose videos or click Download All
    ↓
Confirmation: "Download 5 videos?"
    ↓
Download starts
```

### For Single Videos:
```
You paste video URL
    ↓
"Checking URL..." (1-2 seconds)
    ↓
Download starts immediately (no modal)
```

## If Still Not Working:

Share:
1. Browser console output (copy all)
2. URL you're testing with
3. Any error messages from server terminal
4. Screenshot of what you see

