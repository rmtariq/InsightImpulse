# Instagram Comments Collection - Real Issue Found & Fixed

## 🔴 The Real Problem (Discovered from Test Logs)

**What we thought:** `apify/instagram-scraper` would return comments in `latestComments` field ❌

**What actually happens:** The actor returns `latestComments` field but **EMPTY/NULL** when scraping hashtag pages ❌

**Why?** The `apify/instagram-scraper` actor can scrape comments, BUT:
- ✅ Works: When given **direct post URLs** (e.g., `https://www.instagram.com/p/XXXX/`)
- ❌ Doesn't work: When given **hashtag URLs** (e.g., `https://www.instagram.com/explore/tags/hashtag/`)

Our implementation scrapes posts from **hashtag pages**, so inline comments aren't available.

---

## ✅ The Solution: Two-Actor Strategy for Instagram

**Same approach as YouTube:**

### Step 1: Get Posts (via hashtag)
```python
apify/instagram-scraper (hashtag-based)
├─ Input: hashtag URL
├─ Output: 75 posts with engagement metrics
└─ NO inline comments (limitation of hashtag scraping)
```

### Step 2: Get Comments (via separate actor)
```python
apify/instagram-comment-scraper (post URL-based)
├─ Input: Direct post URLs from step 1
├─ Batches: 10 posts per batch (IG_BATCH_SIZE)
├─ Max posts: 50 (IG_MAX_POSTS)
└─ Output: Comment records for each post
```

### Step 3: Combine
```python
Attach comments to posts via URL matching
→ Final output: Posts + comments in one CSV
```

---

## 🔧 Code Changes Made

### File: `simple_apify_adapter.py`

1. **Re-added Instagram to comments_actor_map** (line 126)
   - Maps to: `apify/instagram-comment-scraper`

2. **Removed Instagram skip logic** (lines ~1585-1590)
   - Deleted: "Skip Instagram because comments are already included"
   - Reason: Comments are NOT included in hashtag-based scraping

3. **Re-added Instagram comments crawling** (lines ~1683-1710)
   - Batches posts in groups of 10
   - Uses `apify/instagram-comment-scraper` actor
   - Applies same logic as YouTube comments crawling

4. **Removed Instagram latestComments extraction** (lines ~788-840)
   - Deleted: Special case handling for latestComments field
   - Reason: Field is empty for hashtag-based scraping

---

## 📊 Expected Results

| Platform | Posts | Comments | Total |
|----------|-------|----------|-------|
| Instagram | 75 | + X (via separate actor) | 75 + X ✅ |
| YouTube | 75 | + 90+ (working!) | 75 + 90+ ✅ |
| **Combined** | **150** | **90+ total** | **240+** ✅ |

---

## 🧪 Next: Test with Fixed Code

Run analysis again with fresh backend to see Instagram comments working! ✅

