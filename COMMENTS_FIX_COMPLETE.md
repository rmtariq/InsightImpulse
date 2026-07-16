# Complete Fix: Instagram & YouTube Comments Collection

## Root Causes Identified & Fixed

### Issue #1: Instagram Excluded from Comments Strategy
**Line 1321** - Instagram was not in platform list for automatic comment crawling
```python
# BEFORE:
if platform_lower in ['x', 'twitter', 'facebook', 'youtube']:

# AFTER:
if platform_lower in ['x', 'twitter', 'facebook', 'instagram', 'youtube']:
```

### Issue #2: Cache Bypass Comments Actor
**Lines 1112-1129** - Fresh cached data returned immediately without fetching comments
```python
# BEFORE:
if age_seconds < 3600:
    return cached_data  # ← EXIT without comments!

# AFTER:
if age_seconds < 3600:
    cached_posts_only = cached_data
    # Continue execution to fetch comments
```

### Issue #3: YouTube Always Shows Zero Comments
**Lines 1547-1553** - YouTube actor under-reports comment counts (all show 0)
```python
# BEFORE:
if platform == 'youtube':
    should_crawl = reply_count > 0  # Never true since all = 0!

# AFTER:
if platform in ['facebook', 'instagram', 'youtube']:
    should_crawl = True  # Always crawl (actors under-report)
```

### Issue #4: Code Not Using Cached Posts + Comments
**Lines 1140-1190** - Added logic to use cached posts but still fetch comments
```python
if cached_posts_only:
    transformed = cached_posts_only
    # Continue to comments fetching...
```

## All Changes Made

**File:** `backend/data_crawlers/simple_apify_adapter.py`

1. ✅ Line 121-128: Instagram in `comments_actor_map`
2. ✅ Line 1112-1129: Cache logic doesn't return early
3. ✅ Line 1140-1190: Use cached posts + fetch comments
4. ✅ Line 1321: Instagram in auto-comment platforms
5. ✅ Line 1530-1575: Instagram URL extraction
6. ✅ Line 1547-1555: Always crawl (Facebook/Instagram/YouTube)
7. ✅ Line 1634-1666: Instagram comments actor impl
8. ✅ Line 1887-1909: Instagram comment mapping

## What Happens Now

**When you run analysis with Instagram & YouTube:**

1. Posts crawled (from Apify actor)
2. If cache is fresh → use cached posts
3. Crawl comments for ALL posts (not just > 0)
4. Instagram & YouTube comments actors invoked
5. Comments attached to posts
6. Combined CSV has Type='comment' rows

## Test It

Run analysis with Instagram & YouTube again.
Should now see comment records!
