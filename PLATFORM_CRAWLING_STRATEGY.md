# 🎯 PLATFORM CRAWLING STRATEGY - Apply Instagram Success to All Platforms

## ✅ WHY INSTAGRAM WORKS (2,014 records!)

Instagram crawler berjaya kerana:

### 1. **SINGLE ACTOR - Posts + Comments in ONE call**
```python
# Instagram menggunakan apify/instagram-post-scraper
# Actor ini dapat BOTH posts AND comments sekaligus!

input_data = {
    "directUrls": [hashtag_url],  # Direct hashtag URL
    "resultsLimit": adjusted_max_results,
    "scrapeComments": True,  # ✅ KEY: Enable comments!
    "maxComments": adjusted_max_comments,  # ✅ Get comments per post
    "includeHasStories": False
}
```

### 2. **SMART BUFFER STRATEGY**
```python
buffer = self.calculate_smart_buffer(max_results)
adjusted_max_results = int(max_results * buffer)  # 1.5x-2.5x buffer
adjusted_max_comments = int(max_comments * 1.2)   # 20% buffer for comments
```

### 3. **DIRECT URL APPROACH - No complex query**
```python
# Instead of complex Boolean search:
hashtag_url = f"https://www.instagram.com/explore/tags/{hashtag}/"

# Clean, simple, reliable!
```

### 4. **ALWAYS CRAWL COMMENTS**
```python
# Instagram ALWAYS crawls comments (actors under-report):
if platform in ['facebook', 'instagram', 'youtube']:
    should_crawl = True  # Always crawl comments!
```

---

## 🔧 CURRENT PROBLEM - Other Platforms

### ❌ **Threads - 2-Step Process (COMPLEX)**
Current approach:
```python
# Step 1: Get posts (igview-owner/threads-search-scraper)
posts = search_threads_posts(query)

# Step 2: Get replies (futurizerush/threads-replies-scraper-api)  
replies = fetch_threads_replies(post_urls, session_id)

# Problem: 2 API calls, need Session ID, proxy issues!
```

### ❌ **Facebook/TikTok/X - Unknown Issues**
- Tak tahu actors yang digunakan
- Mungkin guna 2-step juga
- Configuration issues

---

## 🎯 SOLUTION - Apply Instagram Pattern

### **TARGET: All platforms dapat 1,000-2,000 records like Instagram!**

### **Strategy untuk setiap platform:**

#### 1. **Facebook**
```python
Actor: 'danek/facebook-posts-scraper'  # Check if includes comments
Input: {
    "queries": [query],
    "maxPosts": adjusted_max_posts,
    "scrapeComments": True,  # ✅ Enable comments
    "maxComments": max_comments
}
```

#### 2. **TikTok**
```python
Actor: 'clockworks/tiktok-scraper'
Input: {
    "searchQueries": [query],
    "maxVideos": adjusted_max_videos,
    "scrapeComments": True,  # ✅ Enable comments
    "maxCommentsPerVideo": max_comments
}
```

#### 3. **X/Twitter**
```python
Actor: 'apidojo/twitter-scraper'
Input: {
    "queries": [query],
    "maxTweets": adjusted_max_tweets,
    "scrapeReplies": True,  # ✅ Enable replies
    "maxRepliesPerTweet": max_comments
}
```

#### 4. **Threads**
```python
# OPTION A: Find single actor that does both
Actor: TBD - search Apify for "threads posts comments"

# OPTION B: Keep 2-step but FIX IT
# Current issues:
# - Field name errors (postUrls vs urls)
# - Proxy not accepted
# - Session ID required
```

---

## 📋 NEXT STEPS

1. ✅ **Check current actors** - Which actors are being used?
2. ✅ **Verify comment support** - Do they support `scrapeComments`?
3. ✅ **Fix input parameters** - Match exact field names
4. ✅ **Test each platform** - One by one like Instagram
5. ✅ **Monitor results** - Aim for 1,000+ records each

---

## 📊 CURRENT ACTOR CONFIGURATION

### **Posts Actors (Step 1):**
```python
'facebook': 'danek/facebook-search-ppr'
'instagram': 'apify/instagram-scraper'
'twitter/x': 'kaitoeasyapi/twitter-x-data-tweet-scraper-pay-per-result-cheapest'
'tiktok': 'clockworks/tiktok-scraper'
'threads': 'igview-owner/threads-search-scraper'
```

### **Comments Actors (Step 2 - SEPARATE!):**
```python
'facebook': 'apify/facebook-comments-scraper'
'instagram': 'apify/instagram-comment-scraper'
'twitter/x': 'scraper_one/x-post-replies-scraper'
# TikTok: NO COMMENTS ACTOR! ❌
# Threads: 'futurizerush/threads-replies-scraper-api' (in code but has issues)
```

---

## ❌ ROOT PROBLEM IDENTIFIED!

**ALL platforms use 2-STEP process:**
1. Get posts with main actor
2. Get comments with separate actor

**Instagram works because:**
- ✅ Both steps are properly configured
- ✅ Field names are correct (`directUrls`, `maxComments`)
- ✅ Proxy configuration accepted
- ✅ Comments ALWAYS crawled

**Other platforms FAIL because:**
- ❌ Step 2 has configuration errors
- ❌ Wrong field names
- ❌ Missing or broken comments actors
- ❌ Filtering removes all data

---

## 🎯 FIX STRATEGY

### **Option A: Fix 2-Step Process for ALL platforms** ⭐ (RECOMMENDED)

Follow Instagram's working pattern exactly:

```python
# For EACH platform:
# 1. Get posts
posts = await self._run_apify_actor(posts_actor, posts_input)

# 2. Extract post URLs
post_urls = [post.get('url') or post.get('postUrl') for post in posts]

# 3. Get comments (with CORRECT field names!)
comments_input = {
    # ✅ Use exact field name for each actor
    "directUrls": post_urls,  # Instagram
    "postUrls": post_urls,     # Threads
    "urls": post_urls,         # Facebook
    "tweetUrls": post_urls,    # Twitter/X
    "maxComments": max_comments,
    "proxy": {...}  # Only if actor accepts it!
}
comments = await self._run_apify_actor(comments_actor, comments_input)

# 4. Combine
all_data = posts + comments
```

### **Option B: Find Single Actors** (HARDER)

Search Apify for actors yang dapat BOTH posts + comments:
- `apify/facebook-posts-scraper` (with comments)
- `apify/twitter-scraper-pro` (with replies)
- `clockworks/tiktok-hashtag-scraper` (with comments)

---

## 🔧 IMMEDIATE ACTION PLAN

### **PRIORITY 1: Fix Field Names ✅**

Check each comments actor documentation for correct field names:

1. **Facebook** (`apify/facebook-comments-scraper`):
   - Check: https://apify.com/apify/facebook-comments-scraper
   - Find correct field name for post URLs

2. **TikTok** (`clockworks/tiktok-scraper`):
   - Check if main actor supports comments
   - If yes, enable `scrapeComments: true`

3. **X/Twitter** (`scraper_one/x-post-replies-scraper`):
   - Check: https://apify.com/scraper_one/x-post-replies-scraper
   - Find correct field names

4. **Threads** - Already documented issues:
   - ✅ Field: `postUrls` (correct)
   - ❌ Issue: `proxy` not accepted (FIXED)
   - ❌ Issue: Needs Session ID

### **PRIORITY 2: Test Each Platform ✅**

Run analysis untuk SATU platform sahaja, monitor logs:

```bash
# Test Facebook only
platforms: [facebook]
dataset: 500 results

# Check terminal for:
✅ Found XX posts
✅ Fetched XX comments
✅ Total: XX items
```

### **PRIORITY 3: Remove Bad Filters ✅**

Current issue - data filtered to 0:
```python
✅ [threads] Filtered to 0 top posts + 0 comments
⚠️ No records to save
```

Need to check filtering logic and disable aggressive filters!
