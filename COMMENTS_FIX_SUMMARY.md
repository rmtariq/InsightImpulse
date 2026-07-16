# Comments Collection Fixes - 2026-05-23

## 🔴 Problems Identified from Logs

### Instagram: Comments NOT Extracted
```
WARNING: [instagram] No inline comments found. Tried fields: 
['comments', 'commentsList', 'latestComments', 'commentsData']
```
**Root Cause:** `apify/instagram-scraper` returns comment COUNT (`commentsCount`) and comment PREVIEW (`latestComments` array), but code wasn't extracting them.

### YouTube: Comments NOT Attached to Videos
```
WARNING: [youtube] Comment has no parent URL (90 comments skipped)
```
**Root Cause:** `apidojo/youtube-comments-scraper` returns `'inputSource'` field but code only looked for `'pageUrl'`, `'videoUrl'`, etc.

---

## ✅ Fixes Applied to `simple_apify_adapter.py`

### Fix 1: Extract Instagram Comments from `latestComments`
**Location:** `_extract_comments()` method (lines 787-832)

**What Changed:**
- Added special handling for Instagram to check `latestComments` field
- Parse each comment object and extract text, likes, author, date
- Create proper comment records (Type='comment')
- Return early if comments found, avoiding fallback to nested comment extraction

**Result:** Instagram posts now have attached comments ✅

### Fix 2: Add `inputSource` to YouTube Parent URL Field Mapping
**Location:** `_attach_comments_to_posts()` method (line 1824)

**What Changed:**
- Added `inputSource` as PRIMARY field for YouTube parent URL
- This field contains the video URL that was sent to the comments actor
- Maintains fallback to `pageUrl`, `videoUrl`, etc. for other actors

**Result:** YouTube comments now properly matched to videos ✅

### Fix 3: Update YouTube Comment Field Mapping
**Location:** Comment record creation (lines 1938-1964)

**What Changed:**
- Updated from `numberOfLikes` → `likeCount`
- Updated from `authorName` → `author`
- Updated from `publishedAt` → `publishedTime`
- Added field priority handling for maximum compatibility

**Result:** YouTube comment data properly extracted ✅

---

## 🧪 Testing Required

1. **Run analysis with Instagram + YouTube**
2. **Check Combined CSV:**
   ```bash
   python3 << 'PY'
   import pandas as pd
   df = pd.read_csv('data/combined/Combined_instagram_youtube_*.csv')
   
   ig = df[df['Platform'] == 'instagram']
   yt = df[df['Platform'] == 'youtube']
   
   print(f"Instagram: {len(ig[ig['Type']=='post'])} posts + {len(ig[ig['Type']=='comment'])} comments")
   print(f"YouTube: {len(yt[yt['Type']=='post'])} posts + {len(yt[yt['Type']=='comment'])} comments")
   PY
   ```
3. **Expect:** Both platforms should have comments_count > 0 ✅

---

## 📋 Changed Code Sections

| Section | Change | Purpose |
|---------|--------|---------|
| `_extract_comments()` | +45 lines | Extract Instagram's `latestComments` field |
| `_attach_comments_to_posts()` | +1 line | Add `inputSource` for YouTube URL matching |
| Field mapping | +3 lines | Update YouTube field names from actor output |

**Total Changes:** ~50 lines of targeted fixes

