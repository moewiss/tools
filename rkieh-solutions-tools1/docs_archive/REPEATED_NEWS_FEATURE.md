# 🔥 Repeated News Section - Feature Documentation

## Overview

The **Repeated News Section** displays news articles that appear on **MULTIPLE SOURCES/WEBSITES**. This indicates high importance, credibility, and trending status.

---

## ✨ What's New?

### **Dedicated Repeated News Section**
A prominent section at the top showing:
- ✅ **News reported by multiple sources**
- ✅ **Source badges showing where it's reported**
- ✅ **Trending indicators**
- ✅ **Breaking news highlights**
- ✅ **Repeat count (how many sources)**

### **Visual Design**
- 🔥 **Fire icon** - Indicates hot/trending news
- 🎨 **Red gradient border** - Stands out from regular news
- 📊 **Source badges** - Shows all reporting sources
- 🏷️ **Trending badges** - "TRENDING ON X SOURCES"

---

## 🎯 Why This Matters

### **Credibility Indicator**
When multiple independent sources report the same story:
- ✅ Higher credibility
- ✅ More likely to be accurate
- ✅ Important/significant news

### **Filter Out Noise**
- See what's REALLY trending
- Skip single-source stories
- Focus on verified news

### **Save Time**
- Don't read the same story from multiple sources
- See consolidated view
- Get key information quickly

---

## 📊 How It Works

### **Step 1: News Collection**
System fetches news from multiple sources:
- Google News
- BBC
- Reuters
- Twitter/X
- YouTube
- And more...

### **Step 2: Duplicate Detection**
Algorithm analyzes titles to find similar articles:
- Normalizes text (lowercase, removes special chars)
- Compares title similarity
- Groups similar articles together

### **Step 3: Repeated News Identification**
Identifies articles appearing on 2+ sources:
- Counts how many sources report it
- Tracks which platforms
- Calculates trending score

### **Step 4: Display**
Shows in dedicated section:
- Most repeated news first
- Breaking news highlighted
- Source badges for each platform
- Direct links to read full articles

---

## 🎨 Visual Features

### **Repeated News Card**
```
┌─────────────────────────────────────────┐
│ 🔥 TRENDING ON 5 SOURCES              │
│                                          │
│ Article Title (BREAKING) (TRENDING)     │
│ Headline/Summary                         │
│                                          │
│ Content preview...                       │
│                                          │
│ 🕒 2 hours ago  📰 BBC News            │
│ 🔗 Read Full Article                    │
│                                          │
│ 🔄 Also reported by:                    │
│ [BBC] [Reuters] [CNN] [Forbes] [Tech+] │
└─────────────────────────────────────────┘
```

### **Styling Features:**
- **Red border** - Makes it stand out
- **Fire emoji watermark** - Subtle background
- **Gradient background** - Eye-catching
- **Hover effects** - Interactive
- **Shadow effects** - Depth and prominence

---

## 🔢 Repeat Count Badge

Shows how many sources are reporting:

```
🔥 TRENDING ON 2 SOURCES
🔥 TRENDING ON 3 SOURCES
🔥 TRENDING ON 5 SOURCES
```

**Color coding:**
- Red gradient = High importance
- Bold text = Attention-grabbing
- Uppercase = Urgent/important

---

## 📱 Section Location

The Repeated News section appears:

1. **After** Search Summary Stats
2. **Before** All Platform Results
3. **Only when** repeated news is found

### **Layout:**
```
┌─ Search Box ─────────────────┐
└──────────────────────────────┘

┌─ Summary Stats ──────────────┐
│ Total Articles | Platforms   │
└──────────────────────────────┘

┌─ 🔥 REPEATED NEWS ───────────┐  ← NEW SECTION
│ Trending across sources      │
│ [Article 1]                   │
│ [Article 2]                   │
└──────────────────────────────┘

┌─ All Platform Results ───────┐
│ Twitter News                  │
│ YouTube News                  │
│ BBC News                      │
└──────────────────────────────┘
```

---

## 🎯 Use Cases

### **1. Breaking News Verification**
```
Search: "Major Event"
Result: See if multiple sources confirm it
Benefit: Verify authenticity
```

### **2. Trending Topics**
```
Search: "Tech Company"
Result: See what's trending about them
Benefit: Stay informed on hot topics
```

### **3. Important Announcements**
```
Search: "Celebrity Name"
Result: See major news everyone's reporting
Benefit: Don't miss important news
```

### **4. Research & Fact-Checking**
```
Search: "Scientific Discovery"
Result: See if reputable sources report it
Benefit: Verify scientific claims
```

---

## 🔍 Example Searches

### **Tech News:**
```
Search: "OpenAI GPT-5"
Expected: Articles from:
  - TechCrunch
  - The Verge
  - Ars Technica
  - Bloomberg
  - Reuters
```

### **Business News:**
```
Search: "Tesla Stock"
Expected: Articles from:
  - Bloomberg
  - Reuters
  - CNBC
  - Financial Times
  - Wall Street Journal
```

### **Entertainment News:**
```
Search: "Taylor Swift"
Expected: Articles from:
  - Billboard
  - Rolling Stone
  - Entertainment Weekly
  - People Magazine
  - TMZ
```

---

## 📊 Source Badges

Each repeated news card shows source badges:

| Platform | Badge Color | Icon |
|----------|-------------|------|
| **BBC** | Red | 📡 Broadcast Tower |
| **Reuters** | Orange | 📰 Newspaper |
| **CNN** | Red | 📺 TV |
| **Forbes** | Black | 📈 Chart |
| **TechCrunch** | Green | 💻 Laptop |
| **Bloomberg** | Black | 📊 Bar Chart |
| **Twitter/X** | Blue | 🐦 Twitter |
| **YouTube** | Red | ▶️ Play |

---

## ⚙️ Technical Implementation

### **Frontend (JavaScript):**
```javascript
// Display repeated news section
if (data.trending_repeated && data.trending_repeated.length > 0) {
    repeatedNewsSection.style.display = 'block';
    displayRepeatedNews(data.trending_repeated, platformConfig);
}
```

### **Backend (Python):**
```python
# Detect repeated news
news_results = detect_repeated_news(news_results)

# Get trending repeated news
trending_repeated = get_trending_repeated_news(news_results)

# Return in response
return jsonify({
    'trending_repeated': trending_repeated
})
```

### **Detection Algorithm:**
1. Normalize all article titles
2. Group similar titles together
3. Count occurrences across platforms
4. Mark articles with repeat_count
5. Filter articles with count >= 2
6. Sort by repeat count (highest first)

---

## 🎨 Customization

### **Change Minimum Repeat Count:**
Edit `get_trending_repeated_news()`:
```python
# Show only if repeated 3+ times
if len(platforms) >= 3:  # Change from 2 to 3
```

### **Change Section Position:**
Edit `social_media_news.html`:
```html
<!-- Move section up/down in HTML -->
<div id="repeated-news-section">...</div>
```

### **Customize Colors:**
Edit CSS in `social_media_news.html`:
```css
.repeated-news-card {
    border: 2px solid #YOUR_COLOR;  /* Change border */
    background: #YOUR_BG;            /* Change background */
}
```

---

## 🆘 Troubleshooting

### **No Repeated News Showing:**
**Causes:**
- Not enough news articles found
- Articles too different (not detected as duplicates)
- Only single-source stories

**Solutions:**
- Try popular topics ("Elon Musk", "Bitcoin")
- Search for recent breaking news
- Check if internet connection is stable

### **Section Not Appearing:**
**Check:**
1. Is there repeated news in data? Check browser console
2. Is `repeated-news-section` element present?
3. Are there JavaScript errors?

### **Source Badges Not Showing:**
**Check:**
- Platform names are recognized in `platformConfig`
- Icons are loading (Font Awesome)
- CSS styles are applied

---

## 🚀 Getting Started

### **1. Files Updated:**
- ✅ `templates/social_media_news.html` - Added section HTML + CSS
- ✅ `static/js/social_media_news.js` - Added display function
- ✅ `web_app.py` - Backend already has logic

### **2. Start the App:**
```bash
bash setup_and_start.sh
```

### **3. Test It:**
```
1. Open: http://localhost:5001/tool/social-media-news
2. Search: "Elon Musk" (or any popular topic)
3. Look for: 🔥 Repeated News section at top
4. Check: Source badges and repeat count
```

### **4. Verify:**
- Section appears with red border
- Fire icon is visible
- Source badges show platforms
- Repeat count is displayed

---

## 🎉 Benefits

### **For Users:**
✅ See important news first  
✅ Verify news credibility  
✅ Save time reading  
✅ Avoid duplicate content  
✅ Focus on trending topics  

### **For Content:**
✅ Multi-source verification  
✅ Trending indicators  
✅ Breaking news highlights  
✅ Direct source attribution  
✅ Professional presentation  

---

## 📈 Future Enhancements

Potential improvements:
- [ ] Sentiment analysis across sources
- [ ] Timeline of how news spread
- [ ] Map showing geographic coverage
- [ ] Source reliability scores
- [ ] Save repeated news for later
- [ ] Share repeated news to social media
- [ ] Export as PDF/report

---

## 🎊 Enjoy!

The **Repeated News Section** helps you identify the most important, credible, and trending news by showing you stories reported by multiple sources. 

**Start searching now!** 📰🔥

---

**Need Help?** Contact RKIEH Solutions support.

