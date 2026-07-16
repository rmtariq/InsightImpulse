# Testing Actor Optimization - Quick Guide

## 🧪 Step-by-Step Testing

### 1. Start Backend
```bash
cd /Users/rmtariq/Documents/InsightPulse
python -m uvicorn web_backend.simple_app:app --host 0.0.0.0 --port 8001
```

### 2. Open Frontend
```
http://localhost:8001
```

### 3. Run Analysis
- Select platforms: Instagram + YouTube
- Enter search query: e.g., "PKS" or "maraliner"
- Click "Analyze"
- Monitor logs in terminal

### 4. Monitor Execution
In another terminal:
```bash
tail -f backend.log | grep -E "(Instagram|YouTube|comments|Retrieved)"
```

Expected log sequence for **Instagram**:
```
📸 Instagram: Using direct URL → https://www.instagram.com/explore/tags/{hashtag}/
💬 Instagram: ENABLING COMMENTS - 2 per post with replies
🚀 Running actor: apify/instagram-scraper
✅ Retrieved XXX records from actor
```

Expected log sequence for **YouTube**:
```
🎬 YouTube: Search 'query' - 10 videos (comments via separate actor)
🚀 Running actor: streamers/youtube-scraper
✅ Retrieved XX records from actor
📊 Found X posts with comments
🚀 Running YouTube comments actor: apidojo/youtube-comments-scraper in N batches of 10
   Batch 1/N: 10 video URLs
   Batch 1 retrieved XXX records
```

---

## ✅ Verification Checklist

### Instagram Output CSV:
```bash
python3 << 'PY'
import pandas as pd
df = pd.read_csv('data/combined/Combined_instagram_youtube_*.csv')
ig_df = df[df['Platform'] == 'instagram']
ig_posts = len(ig_df[ig_df['Type'] == 'post'])
ig_comments = len(ig_df[ig_df['Type'] == 'comment'])
print(f"Instagram | Posts: {ig_posts:3} | Comments: {ig_comments:3}")
if ig_comments > 0:
    print("✅ Comments ARE being collected from apify/instagram-scraper!")
    print("\nSample comment:")
    print(ig_df[ig_df['Type'] == 'comment'].iloc[0][['Text', 'author', 'likes']])
else:
    print("❌ NO comments found - investigate actor output")
PY
```

### YouTube Output CSV:
```bash
python3 << 'PY'
import pandas as pd
df = pd.read_csv('data/combined/Combined_instagram_youtube_*.csv')
yt_df = df[df['Platform'] == 'youtube']
yt_posts = len(yt_df[yt_df['Type'] == 'post'])
yt_comments = len(yt_df[yt_df['Type'] == 'comment'])
print(f"YouTube | Posts: {yt_posts:3} | Comments: {yt_comments:3}")
if yt_comments > 0:
    print("✅ Comments ARE being collected from apidojo/youtube-comments-scraper!")
    print("\nSample comment:")
    print(yt_df[yt_df['Type'] == 'comment'].iloc[0][['Text', 'author', 'likes']])
else:
    print("❌ NO comments found - investigate actor output")
PY
```

### Report Generation:
Check if reports generate without errors:
- `/data/reports/` folder should have new report files
- Dashboard sentiment should match report exports

---

## 🔧 Troubleshooting

| Issue | Solution |
|-------|----------|
| Instagram: 0 comments | Check apify/instagram-scraper actor output; verify `scrapeComments: True` in config |
| YouTube: 0 comments | Check apidojo/youtube-comments-scraper batching; verify video URLs are valid |
| Timeouts | Instagram: Reduce `maxComments`; YouTube: Reduce videos per batch |
| Actor errors | Check Apify logs; verify actor still exists on marketplace |

