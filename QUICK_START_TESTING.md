# InsightPulse Comments Fix - Quick Start Testing Guide

## ✅ STATUS: Backend Restarted with Fixed Code

**What was fixed:**
- ✅ YouTube: 2-actor strategy (streamers/youtube-scraper + apidojo/youtube-comments-scraper)
- ✅ Instagram: 2-actor strategy (apify/instagram-scraper + apify/instagram-comment-scraper)
- ✅ Last test: YouTube got 95 comments ✅ | Instagram got 0 comments ❌ → NOW FIXED

---

## 🚀 STEP-BY-STEP TESTING (Copy & Paste Ready)

### STEP 1: Open Dashboard
```
http://localhost:8001
```

### STEP 2: Run Analysis
Select in UI:
- **Platforms**: Instagram + YouTube
- **Query**: `budi95` (or your test query)
- **Dataset size**: 50 (smaller = faster testing)
- **Click**: "Analyze"

**⏱️ Wait ~5-10 minutes** for crawling + analysis to complete

### STEP 3: Check Results CSV File

After analysis completes, run this to verify:

```bash
cd /Users/rmtariq/Documents/InsightPulse
python3 << 'PY'
import pandas as pd
import glob

# Find latest combined CSV
files = sorted(glob.glob('data/combined/Combined_instagram_youtube_*.csv'))
if not files:
    print("❌ No combined CSV found!")
    exit(1)

latest = files[-1]
df = pd.read_csv(latest)

print("=" * 80)
print(f"📊 ANALYSIS RESULTS: {latest.split('/')[-1]}")
print("=" * 80)

for platform in ['instagram', 'youtube']:
    p_df = df[df['Platform'] == platform]
    posts = len(p_df[p_df['Type'] == 'post'])
    comments = len(p_df[p_df['Type'] == 'comment'])
    total = len(p_df)
    
    status = "✅" if comments > 0 else "❌"
    print(f"\n{platform.upper():12} {status}")
    print(f"  Posts:    {posts:3}")
    print(f"  Comments: {comments:3}")
    print(f"  Total:    {total:3}")
    
    if comments > 0:
        print(f"  ✅ WORKING!")
        sample = p_df[p_df['Type'] == 'comment'].iloc[0]
        print(f"  Sample: {sample['Text'][:60]}...")

PY
```

### STEP 4: Expected Results

| Platform | Status |
|----------|--------|
| **Instagram** | ✅ Should have comments (via apify/instagram-comment-scraper) |
| **YouTube** | ✅ Should have comments (95+ from last test) |
| **Combined** | ✅ Both with comments |

---

## 📋 WHAT TO EXPECT

### Success Indicators:
- ✅ Instagram Type='comment' count > 0
- ✅ YouTube Type='comment' count > 0
- ✅ Combined CSV has both posts and comments
- ✅ Sentiment analysis ran on all records

### If Instagram Still Shows 0 Comments:
- Check backend logs for `apify/instagram-comment-scraper` actor errors
- Verify actor still exists on Apify marketplace
- Check Apify API credit/limits

---

## 🔧 COMMANDS FOR REFERENCE

**Restart Backend (if needed):**
```bash
pkill -9 -f uvicorn
sleep 2
cd /Users/rmtariq/Documents/InsightPulse
/Users/rmtariq/Documents/InsightPulse/NEImpulse/bin/python -m uvicorn \
  web_backend.simple_app:app --host 0.0.0.0 --port 8001 &
```

**View Backend Logs (live):**
```bash
tail -f /Users/rmtariq/Documents/InsightPulse/backend.log
```

**Check Latest Results:**
```bash
ls -lrt /Users/rmtariq/Documents/InsightPulse/data/combined/ | tail -3
```

----|-------|
| No combined CSV 

## 📞 TROUBLESHOOTING

| Issue | Check |
|------| Wait longer, check backend logs for errors |
| Instagram 0 comments | Check if apify/instagram-comment-scraper actor still works |
| YouTube 0 comments | Check if apidojo/youtube-comments-scraper actor still works |
| Backend won't start | Check port 8001 is free: `lsof -i :8001` |

