# InsightPulse Actor Optimization Summary

## 📋 Final Actor Configuration (2026-05-23)

### ✅ INSTAGRAM - Single-Actor Approach
**Actor:** `apify/instagram-scraper`

**Configuration:**
- Posts collection: ✅ Enabled (via `resultsType: "posts"`)
- Comments collection: ✅ Enabled (via `scrapeComments: True`)
- Max comments per post: Dynamic (based on analysis parameters)
- Comment mode: `"top"` (most relevant comments)
- Include comment replies: ✅ Yes

**Flow:**
```
apify/instagram-scraper
  ├─ Scrapes posts from hashtag URL
  └─ Collects comments in single actor call
     └─ Returns both posts (Type='post') and comments (Type='comment')
```

**Why:** The `apify/instagram-scraper` actor includes both posts AND comments in a single output, eliminating need for separate comments actor.

---

### ✅ YOUTUBE - Two-Actor Approach
**Post Actor:** `streamers/youtube-scraper`
**Comments Actor:** `apidojo/youtube-comments-scraper`

**Configuration:**

#### Posts (streamers/youtube-scraper):
- Search videos: ✅ Enabled
- Inline comments: ❌ Disabled (`scrapeComments: False`)
- Channel info: ✅ Enabled
- Video stats (views, likes): ✅ Enabled

#### Comments (apidojo/youtube-comments-scraper):
- Triggered separately after posts collection
- Batched: 10 video URLs per batch (max 50 videos)
- Max items: Dynamic (based on comments_per_post parameter)
- Sort: `"top"` (most relevant comments)
- Include replies: ❌ No (reduces API cost)

**Flow:**
```
streamers/youtube-scraper
  └─ Scrapes videos (posts only)
     └─ Extracts video URLs
        └─ apidojo/youtube-comments-scraper (batched)
           └─ Scrapes comments per video URL
              └─ Returns comment records (Type='comment')
```

**Why:** `streamers/youtube-scraper` times out when trying to scrape both videos + comments inline. Splitting into two actors is more reliable and cost-effective.

---

## 🔧 Code Changes Made

### File: `backend/data_crawlers/simple_apify_adapter.py`

1. **lines 121-127:** Updated `comments_actor_map`
   - Removed Instagram from 2-actor strategy
   - Kept YouTube with `apidojo/youtube-comments-scraper`

2. **lines 238-256:** Updated `_prepare_youtube_input()`
   - Changed `scrapeComments: False` (was True)
   - Removed comment-related parameters
   - Added documentation about separate comments actor

3. **lines 1585-1590:** Added Instagram skip logic
   - Skip separate comments crawling for Instagram
   - Log message explains single-actor approach

4. **lines 1647-1648:** Removed Instagram comments crawling block
   - Eliminated redundant Instagram comments actor calls

---

## 📊 Expected Behavior After Optimization

### Instagram Analysis:
- Single actor call to `apify/instagram-scraper`
- Output includes:
  - Posts with engagement metrics (likes, shares, comments_count)
  - **Actual comment records** with text, author, likes, dates
- No separate comments crawling needed ✅

### YouTube Analysis:
- First call to `streamers/youtube-scraper` (posts only)
- Second call to `apidojo/youtube-comments-scraper` (comments only, batched)
- Output includes:
  - Videos with engagement metrics
  - **Actual comment records** with text, author, likes, dates
- Comments matched to videos via URL ✅

---

## 🧪 Testing Checklist

- [ ] Run multi-platform analysis (including Instagram + YouTube)
- [ ] Check Instagram CSV: Verify Type='comment' rows > 0
- [ ] Check YouTube CSV: Verify Type='comment' rows > 0
- [ ] Verify comment fields populated: Text, Author, Likes, Date
- [ ] Run sentiment analysis on all records
- [ ] Generate reports and verify execution
- [ ] Check logs for any actor errors or timeouts

