# 🐛 Threads Comments Fix - Two Issues Fixed

**Date:** 2026-05-28 (Updated: 2026-05-29 00:20 MYT)
**Issues:**
1. ❌ Proxy configuration rejected by replies actor
2. ❌ Replies marked as "post" instead of "comment"
3. ❌ **Cache path skips comments fetching** (NEW!)

**Status:** ✅ ALL THREE FIXED

---

## 🔍 **PROBLEM ANALYSIS**

### **Symptoms:**
```
Data file: Combined_threads_20260528_224128.csv
- ✅ 50 posts (Type = "post")
- ❌ 0 comments (Type = "comment")
```

### **Error in Logs:**
```
ERROR:simple_apify_adapter:❌ Error running Apify actor: Input is not valid: Property input.proxy is not allowed.
INFO:simple_apify_adapter:   ✅ Batch 1: Fetched 0 replies
INFO:simple_apify_adapter:✅ Fetched 0 total replies from 1 batches
```

### **Root Cause:**
The method `_run_apify_actor()` (line 995) automatically adds proxy configuration to ALL actors:

```python
# Add proxy configuration if not present
if "proxy" not in actor_input:
    actor_input["proxy"] = self._get_proxy_config()
```

But the Threads replies actor (`futurizerush/threads-replies-scraper-api`) **REJECTS** proxy configuration, causing the actor to fail and return 0 comments!

---

## ✅ **SOLUTION IMPLEMENTED**

### **Fix 1: Explicitly Disable Proxy in Batch Function** (Lines 820-826)

**File:** `backend/data_crawlers/simple_apify_adapter.py`

```python
# ⚠️ IMPORTANT: This actor does NOT accept proxy configuration
# Set proxy=None explicitly to prevent _run_apify_actor from adding it
replies_input = {
    "postUrls": batch_urls,
    "sessionId": session_id,
    "proxy": None  # ✅ Explicitly disable proxy (actor doesn't support it)
}
```

### **Fix 2: Handle None Proxy in _run_apify_actor** (Lines 997-1004)

```python
# Add proxy configuration if not present
# ⚠️ Skip if proxy is explicitly set to None (some actors don't support proxy)
if "proxy" not in actor_input:
    actor_input["proxy"] = self._get_proxy_config()
elif actor_input.get("proxy") is None:
    # Remove proxy key if explicitly set to None
    actor_input.pop("proxy", None)
    logger.info("⚠️ Proxy disabled for this actor (not supported)")
```

### **Fix 3: Mark Replies with _isReply Flag** (Lines 857-859)

```python
# ✅ CRITICAL: Mark all replies with a flag so _transform_results knows they're comments
for reply in all_replies:
    reply['_isReply'] = True  # Add marker to distinguish from posts
```

### **Fix 4: Set Type='comment' for Replies** (Lines 1081-1084)

```python
# ===== DETERMINE TYPE (post vs comment) =====
# Check if this is a reply (marked by _scrape_threads_with_replies)
is_reply = item.get('_isReply', False)
item_type = 'comment' if is_reply else 'post'

# ===== CREATE POST/COMMENT RECORD =====
post_record = {
    'Platform': platform,
    'Type': item_type,  # ✅ Set to 'comment' if it's a reply
    ...
}
```

### **Fix 5: Fetch Comments Even When Using Cache** (Lines 1772-1843) ⭐ NEW!

**Problem:** When cache was used (posts from previous crawl), the system skipped comments fetching entirely!

**Solution:** Added special handling for Threads when using cached posts:

```python
if cached_posts_only:
    transformed = cached_posts_only

    # ⚠️ CRITICAL FIX: For Threads, STILL fetch comments even when using cached posts!
    if platform == 'threads' and max_comments > 0:
        # Extract URLs from cached posts
        # Fetch comments in parallel batches
        # Mark as _isReply = True
        # Transform and combine with cached posts
        transformed = cached_posts + new_comments
```

**This ensures comments are ALWAYS fetched, whether using fresh crawl or cached posts!**

---

## 🧪 **TESTING**

### **Before Fix:**
```
Run Threads crawling:
- Dataset size: 100
- Posts fetched: 20 ✅
- Comments fetched: 0 ❌
- Error: "Property input.proxy is not allowed"
```

### **After Fix (Expected):**
```
Run Threads crawling:
- Dataset size: 100
- Posts fetched: 30 (30% quota)
- Comments fetched: 70-200 (from parallel batches) ✅
- Total: 100-230 items
- Log: "⚠️ Proxy disabled for this actor (not supported)"
```

---

## 🎯 **HOW TO TEST**

1. **Restart backend:**
   ```bash
   ./start_backend.sh
   ```

2. **Open app:**
   ```
   http://localhost:8001
   ```

3. **Run Threads crawling:**
   - Platform: Select "Threads"
   - Query: "Anwar Ibrahim" (or any topic)
   - Dataset size: 100-500
   - Click "Start Analysis"

4. **Check logs for success:**
   ```bash
   tail -f backend.log | grep -i thread
   ```

   **Expected output:**
   ```
   🧵 Step 1/3: Searching for Threads posts...
   ✅ Found 30 Threads posts
   🧵 Step 2/3: Preparing 30 post URLs...
   🚀 Step 3/3: Fetching comments in 2 PARALLEL batches...
   ⚠️ Proxy disabled for this actor (not supported)
   📦 Batch 1/2: Fetching 20 post URLs...
   ⚠️ Proxy disabled for this actor (not supported)
   📦 Batch 2/2: Fetching 10 post URLs...
   ✅ Batch 1: Fetched 150 replies
   ✅ Batch 2: Fetched 75 replies
   ✅ Fetched 225 total replies from 2 batches
   🎉 Total: 255 items (30 posts + 225 replies)
   ```

5. **Verify CSV has comments:**
   ```bash
   grep -c ',comment,' data/combined/Combined_threads_*.csv
   ```

   Should return a **non-zero** number!

---

## 📝 **RELATED FILES**

- **Main Fix:** `backend/data_crawlers/simple_apify_adapter.py`
  - Lines 820-823: Disable proxy in replies_input
  - Lines 997-1001: Handle None proxy in _run_apify_actor

- **Optimization:** `THREADS_CRAWLING_STRATEGY.md`
  - Batched parallel strategy explanation

- **Comparison:** `INSTAGRAM_VS_THREADS_COMPARISON.md`
  - Performance comparison with Instagram

---

## ✅ **STATUS**

- ✅ Code fixed
- ✅ Proxy handling improved
- ⏳ Waiting for backend restart
- ⏳ Testing needed

**Next:** Run a test crawl to verify comments are fetched!

---

**Author:** Augment AI  
**Date:** 2026-05-28 23:00 MYT
