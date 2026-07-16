# Fix: Instagram & YouTube Comments Collection

## Problem - Root Cause #1 (FIXED)
Instagram and YouTube crawlers were not collecting comment data.
- **Instagram:** 0 comments (excluded from 2-actor strategy)
- **YouTube:** 0 comments (not properly triggered)

### Root Cause Identified
Line 1505: Instagram was not in the platform list for comments crawling!

## Problem - Root Cause #2 (FIXED)
**CACHE ISSUE:** Even with all the code fixes, the cache system was returning stale data WITHOUT running the comment-fetching logic.

```python
# OLD CODE (BAD):
if age_seconds < 3600:  # Cache fresh
    return cached_data  # ← EXITS WITHOUT FETCHING COMMENTS!
```

The cached posts from 21 mins ago were returned directly, bypassing the new Instagram/YouTube comment actors entirely!

## Solution: 6-Part Fix

### 1. ✅ Added Instagram to comments_actor_map (Line 121-128)
```python
'instagram': 'apify/instagram-comment-scraper',  # NEW
```

### 2. ✅ Updated platform check (Line 1505)
Added Instagram to allowed platforms for 2-actor strategy:
```python
if platform not in ['x', 'twitter', 'facebook', 'instagram', 'youtube']:
```

### 3. ✅ Fixed cache logic (Lines 1112-1129)
**CRITICAL FIX:** Changed from returning immediately to continuing execution:
```python
# NEW CODE (GOOD):
if age_seconds < 3600:
    logger.info("Using cached posts and crawling comments...")
    cached_posts_only = cached_data
    # DON'T RETURN — continue to fetch comments!
```

### 4. ✅ Use cached posts if available (Lines 1140-1190)
Added logic to use cached posts but still run comment fetching:
```python
if cached_posts_only:
    transformed = cached_posts_only  # Use cache
    # Continue to comments section...
else:
    # Run normal actor crawl
```

### 5. ✅ Added Instagram URL extraction (Lines 1530-1539)
- Extract Instagram post URLs for comments actor
- Batch 10 posts per request
- Up to 50 posts max per crawl

### 6. ✅ Added Instagram comments actor & field mapping (Lines 1634-1666, 1887-1909)
- Proper Instagram actor invocation
- Comment field mapping (text, username, likes, timestamp)

## Critical Change: Cache + Comments Strategy

**Before:** Cache → Return immediately (NO comments)
**After:** Cache → Extract posts + Fetch comments → Return posts+comments

This ensures even cached posts get fresh comments!

## Next Steps

1. ✅ Backend restarted with new code
2. Run analysis again with Instagram & YouTube
3. Should now show comment records in combined CSV
