# Apify Actors: Posts + Comments Comparison (Instagram & YouTube)

## INSTAGRAM - Best Options

### Option 1: `apify/instagram-comment-and-post-export` ⭐ RECOMMENDED
- **Data**: Posts + Comments in ONE output
- **Cost**: Pay per result (posts + comments)
- **Advantage**: No 2-actor strategy needed, simpler, cleaner data
- **Status**: Appears to be removed/discontinued (404 error)

### Option 2: `apify/instagram-scraper` + Comments Actor (Current Setup)
- **Data**: Posts from main actor, comments from separate actor
- **Cost**: 2 separate charges
- **Problem**: Comments actor may not be returning data properly
- **Status**: Active, used in your current code

### Option 3: Alternative - `apify/instagram-post-scraper`
- **Data**: Posts ONLY (no inline comments)
- **Cost**: Pay per post
- **Status**: Active but not suitable (lacks comment support)

---

## YOUTUBE - Best Options

### Option 1: `calm_builder/youtube-scraper` ⭐ RECOMMENDED
- **Data**: Videos + inline comments in ONE output
- **Comment Config**: `scrapeCommentsAndReplies: true`
- **Max Comments**: `maxCommentThreads: 10` (adjustable)
- **Max Replies**: `maxRepliesPerThread: 10`
- **Cost**: Pay-per-event model ($0.001 per record)
- **Advantage**: Comments included with videos, no separate crawl needed
- **Status**: Active & reliable (89 successful runs in last 30 days)

### Option 2: `scrapemint/youtube-scraper` ⭐ ALTERNATIVE
- **Data**: Videos + top comments with replies
- **Comment Config**: `extractTopComments: true`
- **Cost**: Pay per video ($0.005 per video after first 20 free)
- **Advantage**: Full engagement data, transcripts, music credits
- **Status**: Active but newer (41 successful runs in last 30 days)

### Option 3: `streamers/youtube-scraper` (Current)
- **Data**: Videos ONLY (no comments)
- **Problem**: Comments count visible but not actual comment records
- **Status**: Active but not suitable for your needs

---

## RECOMMENDATION FOR INSIGHTPULSE

### Immediate Solution:
Switch to **`calm_builder/youtube-scraper`** for YouTube:
- Enable `scrapeCommentsAndReplies: true`
- Set reasonable limits: `maxCommentThreads: 5-10`
- Simpler, proven, with inline comments

### For Instagram:
**Keep current approach** with `apify/instagram-scraper` + comments actor:
- Since `instagram-comment-and-post-export` appears removed
- OR switch to a different Instagram actor if comments consistently fail
- Verify comments actor is properly configured

### Cost Comparison:
- **YouTube**: ~$0.001/video with comments ✓
- **Instagram**: Variable (posts + separate comments)
- Both are budget-friendly for your use case

---

## NEXT STEPS
1. Test `calm_builder/youtube-scraper` with comments enabled
2. Debug Instagram comments actor output
3. Monitor comment collection in combined CSV
