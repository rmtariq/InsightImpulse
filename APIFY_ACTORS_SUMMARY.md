# Apify Actors: Instagram & YouTube - Comments Capability

## Problem Found

Current actors do NOT include comments in their output:

### Instagram: `apify/instagram-scraper` ❌
- **Returns:** Posts ONLY (no comments in output)
- **Has:** comments_count field
- **Missing:** Actual comment records
- **Solution:** Need separate comment scraper

**Separate Instagram Actors Available:**
1. `apify/instagram-comments-scraper` - Get comments ONLY (NOT post data)
2. `apify/instagram-post-scraper` - Alternative post scraper (still no comments)
3. `apify/instagram-comment-and-post-export` - **Combines posts + comments!** ✅

### YouTube: `streamers/youtube-scraper` ❌
- **Returns:** Videos ONLY (no comments)
- **Has:** commentsCount field
- **Missing:** Actual comment records
- **Solution:** Need separate comment scraper

**Separate YouTube Actors Available:**
1. `streamers/youtube-comments-scraper` - Get comments ONLY (NOT video data)
2. `apidojo/youtube-comments-scraper` - Alternative comments actor
3. `calm_builder/youtube-scraper` - Supports inline comments! ✅
4. `scrapemint/youtube-scraper` - Full data with top comments! ✅

---

## Recommended Solution

### For Instagram:
**Use:** `apify/instagram-comment-and-post-export`
- ✅ Returns both posts AND comments in one actor
- ✅ No need for 2-actor strategy
- ✅ Simpler, cheaper, faster

### For YouTube:
**Use:** `calm_builder/youtube-scraper` OR `scrapemint/youtube-scraper`
- ✅ Both support inline comments collection
- ✅ Set `scrapeCommentsAndReplies: true`
- ✅ No separate comment actor needed

---

## Current Issue

We're using 2-actor strategy (post actor + separate comments actor)
But comments actor is NOT being invoked properly or returning no data

Easier fix: Switch to single actors that include comments by default
