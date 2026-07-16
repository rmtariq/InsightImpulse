# 🚀 InsightPulse Comments Fix - Testing Checklist

## ✅ Backend Status: READY
- Backend restarted with new code ✅
- All models loaded successfully ✅  
- Running on http://localhost:8001 ✅

---

## 📋 TESTING CHECKLIST (Follow in Order)

### ✓ STEP 1: Open Dashboard
```
http://localhost:8001
```
Expected: Dashboard loads with analysis interface

---

### ✓ STEP 2: Run Analysis
In the dashboard, select:
- **Platforms**: Instagram + YouTube ✓
- **Query**: `budi95` (or test keyword) ✓
- **Dataset size**: 50 (faster) ✓
- **Click**: "Analyze" ✓

⏱️ **Wait 5-10 minutes** for crawling + analysis

---

### ✓ STEP 3: Verify Comments in CSV

After analysis completes, run this command:

```bash
cd /Users/rmtariq/Documents/InsightPulse
python3 << 'PY'
import pandas as pd, glob

files = sorted(glob.glob('data/combined/Combined_instagram_youtube_*.csv'))
if not files:
    print("❌ No combined CSV found!")
    exit(1)

latest = files[-1]
df = pd.read_csv(latest)

print("\n" + "="*70)
print(f"📊 RESULTS: {latest.split('/')[-1]}")
print("="*70)

for platform in ['instagram', 'youtube']:
    p_df = df[df['Platform'] == platform]
    posts = len(p_df[p_df['Type'] == 'post'])
    comments = len(p_df[p_df['Type'] == 'comment'])
    status = "✅" if comments > 0 else "❌"
    
    print(f"\n{platform.upper():12} {status}")
    print(f"  Posts:     {posts:3} records")
    print(f"  Comments:  {comments:3} records")
    print(f"  Total:     {posts + comments:3} records")

print("\n" + "="*70 + "\n")
PY
```

---

## 🎯 Expected Results

| Platform  | Posts | Comments | Status |
|-----------|-------|----------|--------|
| Instagram | ~75   | ✅ X+    | 2-Actor Strategy Active |
| YouTube   | ~75   | ✅ 90+   | Working! |

---

## 🔍 What Was Fixed

**Instagram**: Now uses `apify/instagram-scraper` (posts) + `apify/instagram-comment-scraper` (comments)
- Reason: Hashtag pages don't return inline comments

**YouTube**: Uses `streamers/youtube-scraper` (posts) + `apidojo/youtube-comments-scraper` (comments)
- Status: Already working ✅

---

## 🚨 Troubleshooting

| Problem | Solution |
|---------|----------|
| No CSV file | Wait longer, check backend logs: `tail -f backend.log` |
| Instagram 0 comments | Check if actor `apify/instagram-comment-scraper` exists on Apify |
| YouTube 0 comments | Check if actor `apidojo/youtube-comments-scraper` exists on Apify |
| Backend offline | Run: `lsof -i :8001` then restart if needed |

---

## 📚 Reference Files
- `INSTAGRAM_COMMENTS_FIX.md` - Root cause analysis
- `COMMENTS_FIX_SUMMARY.md` - Technical details
- `QUICK_START_TESTING.md` - Extended testing guide

