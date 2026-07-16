# 📁 InsightPulse Data Storage Structure

**Last Updated:** 2026-02-15
**Status:** ✅ COMPLETE - All 10 Platforms + Combined Data

---

## Current Folder Structure

```
data/
├── smart_crawlers/              # ✅ RAW crawled data (NO sentiment analysis)
│   ├── facebook/
│   │   └── facebook_query_YYYYMMDD_HHMMSS.csv
│   ├── instagram/
│   │   └── instagram_query_YYYYMMDD_HHMMSS.csv
│   ├── x/
│   │   └── x_query_YYYYMMDD_HHMMSS.csv
│   ├── tiktok/
│   │   └── tiktok_query_YYYYMMDD_HHMMSS.csv
│   ├── youtube/
│   │   └── youtube_query_YYYYMMDD_HHMMSS.csv
│   ├── linkedin/
│   │   └── linkedin_query_YYYYMMDD_HHMMSS.csv
│   ├── news/
│   │   └── news_query_YYYYMMDD_HHMMSS.csv
│   ├── lowyat/
│   │   └── lowyat_query_YYYYMMDD_HHMMSS.csv
│   ├── shopee/
│   │   └── shopee_query_YYYYMMDD_HHMMSS.csv
│   └── lazada/
│       └── lazada_query_YYYYMMDD_HHMMSS.csv
│
├── analyzed/                     # ✅ ANALYZED data (WITH sentiment/emotion) - Per Platform
│   ├── Sentiment_Emotion_FACEBOOK_YYYYMMDD_HHMMSS.csv
│   ├── Sentiment_Emotion_X_YYYYMMDD_HHMMSS.csv
│   ├── Sentiment_Emotion_INSTAGRAM_YYYYMMDD_HHMMSS.csv
│   ├── Sentiment_Emotion_TIKTOK_YYYYMMDD_HHMMSS.csv
│   ├── Sentiment_Emotion_YOUTUBE_YYYYMMDD_HHMMSS.csv
│   ├── Sentiment_Emotion_LINKEDIN_YYYYMMDD_HHMMSS.csv
│   ├── Sentiment_Emotion_NEWS_YYYYMMDD_HHMMSS.csv
│   ├── Sentiment_Emotion_LOWYAT_YYYYMMDD_HHMMSS.csv
│   ├── Sentiment_Emotion_SHOPEE_YYYYMMDD_HHMMSS.csv
│   └── Sentiment_Emotion_LAZADA_YYYYMMDD_HHMMSS.csv
│
├── combined/                     # ⭐ NEW! COMBINED data (ALL platforms merged)
│   ├── Combined_facebook_instagram_x_YYYYMMDD_HHMMSS.csv
│   ├── Combined_facebook_instagram_linkedin_tiktok_x_YYYYMMDD_HHMMSS.csv
│   └── Combined_facebook_google_instagram_lazada_linkedin_YYYYMMDD_HHMMSS.csv
│
├── raw/                          # ❌ DEPRECATED - No longer used
│   └── (empty - not used anymore)
│
├── reports/                      # Generated PDF/HTML reports
│   └── Report_PLATFORM_YYYYMMDD_HHMMSS.pdf
│
└── insightpulse.db              # SQLite database (optional)
```

---

## 📊 Data Flow - Complete Pipeline

```
1. CRAWL (Raw Data - Per Platform)
   ↓
   data/smart_crawlers/PLATFORM/PLATFORM_query_YYYYMMDD_HHMMSS.csv
   (Posts + Comments, NO sentiment/emotion)
   Retention: 30 days

2. ANALYZE (Add Sentiment + Emotion - Per Platform)
   ↓
   data/analyzed/Sentiment_Emotion_PLATFORM_YYYYMMDD_HHMMSS.csv
   (Posts + Comments + Sentiment + Emotion + Engagement)
   Retention: 7 days

3. COMBINE (Merge All Platforms - Cross-Platform Analysis)
   ↓
   data/combined/Combined_PLATFORMS_YYYYMMDD_HHMMSS.csv
   (ALL platforms + Sentiment + Emotion + Engagement in ONE file)
   Retention: Manual cleanup
```

---

## CSV File Formats

### 1. RAW Data (data/smart_crawlers/PLATFORM/*.csv)
**Purpose**: Store crawled data WITHOUT sentiment analysis
**Location**: `data/smart_crawlers/PLATFORM/PLATFORM_query_YYYYMMDD_HHMMSS.csv`
**Retention**: 30 days (automatic cleanup)

**Columns** (15 total):
- Platform, Type, ID, Text, URL, Date
- likes, shares, comments_count, views
- sentiment_score, total_engagement, engagement_score
- author, author_followers

**Example**: `data/smart_crawlers/facebook/facebook_pilihan_raya_20260215_154530.csv`

---

### 2. ANALYZED Data (data/analyzed/*.csv)
**Purpose**: Store data WITH sentiment/emotion analysis (per platform)
**Location**: `data/analyzed/Sentiment_Emotion_PLATFORM_YYYYMMDD_HHMMSS.csv`
**Retention**: 7 days (automatic cleanup)

**Columns** (27 total): All RAW columns PLUS:
- sentiment_label (😊 Positive / 😐 Neutral / 😠 Negative)
- sentiment_confidence (0.0-1.0)
- detected_language (ms/en/zh)
- demographic (Malay/English/Chinese)
- emotion_primary (joy/anger/fear/sadness/love/surprise)
- emotion_anger, emotion_fear, emotion_happy, emotion_sadness, emotion_love, emotion_surprise (0.0-1.0)

**Example**: `data/analyzed/Sentiment_Emotion_FACEBOOK_20260211_133139.csv`

---

### 3. COMBINED Data (data/combined/*.csv) ⭐ NEW!
**Purpose**: Store ALL platforms merged with sentiment/emotion analysis
**Location**: `data/combined/Combined_PLATFORMS_YYYYMMDD_HHMMSS.csv`
**Retention**: Manual cleanup (no automatic deletion)

**Columns** (27 total): Same as ANALYZED data
- Includes data from ALL selected platforms in ONE file
- Perfect for cross-platform comparison
- Used for comprehensive analysis and reporting

**Example**: `data/combined/Combined_facebook_instagram_x_20260215_154530.csv`

**Use Cases**:
- Compare sentiment across platforms
- Identify cross-platform trends
- Generate comprehensive reports
- Export for external analysis tools

---

## Storage Rules (Updated 2026-02-15)

### ✅ RULE 1: Raw Crawled Data
**ALL crawled data goes to:**
- `data/smart_crawlers/PLATFORM/PLATFORM_query_YYYYMMDD_HHMMSS.csv` (ONLY location)

**❌ NO LONGER saves to:**
- `data/raw/PLATFORM.csv` (deprecated)

### ✅ RULE 2: Analyzed Data (Per Platform)
**Analyzed data ALWAYS goes to:**
- `data/analyzed/Sentiment_Emotion_PLATFORM_YYYYMMDD_HHMMSS.csv`

### ✅ RULE 3: Combined Data (All Platforms)
**When analyzing multiple platforms, combined data goes to:**
- `data/combined/Combined_PLATFORMS_YYYYMMDD_HHMMSS.csv`

### ✅ RULE 4: Cleanup Strategy
- **smart_crawlers**: Keep last 30 days (automatic)
- **analyzed**: Keep last 7 days (automatic)
- **combined**: Manual cleanup (no automatic deletion)
- **raw**: ❌ Deprecated (not used)

---

## All 10 Supported Platforms

| # | Platform | Folder | Status |
|---|----------|--------|--------|
| 1 | Facebook | `data/smart_crawlers/facebook/` | ✅ Working |
| 2 | Instagram | `data/smart_crawlers/instagram/` | ✅ Working |
| 3 | X/Twitter | `data/smart_crawlers/x/` | ✅ Working |
| 4 | TikTok | `data/smart_crawlers/tiktok/` | ✅ Working |
| 5 | YouTube | `data/smart_crawlers/youtube/` | ✅ Working |
| 6 | LinkedIn | `data/smart_crawlers/linkedin/` | ✅ Working |
| 7 | Google News | `data/smart_crawlers/news/` | ✅ Working |
| 8 | Lowyat | `data/smart_crawlers/lowyat/` | ✅ Working |
| 9 | Shopee | `data/smart_crawlers/shopee/` | ✅ Working |
| 10 | Lazada | `data/smart_crawlers/lazada/` | ✅ Working |

---

## Cleanup Utility

**Location**: `backend/utils/data_cleanup.py`

**Usage**:
```python
from backend.utils.data_cleanup import cleanup_old_data, get_storage_info

# Get storage statistics
stats = get_storage_info()

# Run cleanup (30 days for smart_crawlers, 7 days for analyzed)
result = cleanup_old_data(days_smart=30, days_analyzed=7)
```

**Features**:
- Automatic deletion of old files
- Configurable retention periods
- Storage statistics reporting
- Safe deletion (never touches combined data)

---

## Summary

**3 Storage Locations:**

| Type | Location | Content | Retention |
|------|----------|---------|-----------|
| **Raw** | `data/smart_crawlers/PLATFORM/` | Posts + Comments (per platform) | 30 days |
| **Analyzed** | `data/analyzed/` | Posts + Comments + Sentiment + Emotion (per platform) | 7 days |
| **Combined** | `data/combined/` | ALL platforms merged + Sentiment + Emotion | Manual |

**All 10 platforms supported!** ✅

