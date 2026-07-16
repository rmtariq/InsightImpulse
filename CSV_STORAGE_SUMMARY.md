# ✅ CSV Storage & Folder Structure - COMPLETE UPDATE

**Last Updated:** 2026-02-15
**Status:** ✅ All 10 Platforms + Combined Data Support

---

## 📊 **CURRENT STATUS** (After Update)

### Storage Statistics:
- **Smart Crawlers**: 99 files (3.00 MB) - Historical archives (30-day retention)
- **Analyzed**: 3 files (0.57 MB) - Sentiment/emotion analyzed data (7-day retention)
- **Combined**: 0 files (0 MB) - Cross-platform merged data (manual cleanup)
- **Raw**: ❌ DEPRECATED - No longer used
- **TOTAL**: 102 files (3.57 MB) - After cleanup

**Previous Cleanup**: ✅ Deleted 57 old files, freed 14.12 MB

---

## 📁 **UPDATED FOLDER STRUCTURE**

```
data/
├── smart_crawlers/              # ✅ RAW crawled data (NO sentiment) - ONLY location
│   ├── facebook/
│   │   ├── facebook_pilihan_raya_PBT_20260208_143022.csv
│   │   └── facebook_pilihan_raya_PBT_20260215_154530.csv
│   ├── instagram/
│   │   └── instagram_fashion_20260215_155012.csv
│   ├── x/
│   │   └── x_election_20260215_160145.csv
│   ├── tiktok/
│   │   └── tiktok_viral_dance_20260215_161230.csv
│   ├── youtube/
│   │   └── youtube_Malaysia_20260215_162233.csv
│   ├── linkedin/
│   │   └── linkedin_jobs_Malaysia_20260215_163045.csv
│   ├── news/
│   │   └── news_Malaysia_politik_20260215_164512.csv
│   ├── lowyat/
│   │   └── lowyat_smartphone_review_20260215_165234.csv
│   ├── shopee/
│   │   └── shopee_smartphone_20260215_170123.csv
│   └── lazada/
│       └── lazada_electronics_20260215_171045.csv
│
├── analyzed/                     # ✅ ANALYZED data (WITH sentiment/emotion) - Per Platform
│   ├── Sentiment_Emotion_FACEBOOK_20260215_154530.csv
│   ├── Sentiment_Emotion_INSTAGRAM_20260215_155012.csv
│   ├── Sentiment_Emotion_X_20260215_160145.csv
│   ├── Sentiment_Emotion_TIKTOK_20260215_161230.csv
│   ├── Sentiment_Emotion_YOUTUBE_20260215_162233.csv
│   ├── Sentiment_Emotion_LINKEDIN_20260215_163045.csv
│   ├── Sentiment_Emotion_NEWS_20260215_164512.csv
│   ├── Sentiment_Emotion_LOWYAT_20260215_165234.csv
│   ├── Sentiment_Emotion_SHOPEE_20260215_170123.csv
│   └── Sentiment_Emotion_LAZADA_20260215_171045.csv
│
├── combined/                     # ⭐ NEW! COMBINED data (ALL platforms merged)
│   ├── Combined_facebook_instagram_x_20260215_154530.csv
│   ├── Combined_facebook_instagram_linkedin_tiktok_x_20260215_155012.csv
│   └── Combined_facebook_google_instagram_lazada_linkedin_20260215_160145.csv
│
├── raw/                          # ❌ DEPRECATED - No longer used
│   └── (empty - not used anymore)
│
└── reports/                      # Generated reports
    └── Report_FACEBOOK_20260215_154530.pdf
```

---

## 🔄 **UPDATED CRAWLER BEHAVIOR**

### When Crawler Runs:

**BEFORE** (Old behavior - Feb 14):
- ❌ Saved to BOTH `data/raw/` AND `data/smart_crawlers/`
- ❌ Duplicate storage
- ❌ Wasted disk space

**AFTER** (New behavior - Feb 15):
- ✅ Saves to **ONE location ONLY**:
  - `data/smart_crawlers/PLATFORM/PLATFORM_query_YYYYMMDD_HHMMSS.csv` (archive)
- ✅ No duplicate storage
- ✅ All data timestamped and archived

### Example:
```
User searches: "pilihan raya PBT" on Facebook
Timestamp: 2026-02-15 14:30:45

Crawler saves to:
✅ data/smart_crawlers/facebook/facebook_pilihan_raya_PBT_20260215_143045.csv
❌ NO LONGER saves to data/raw/FACEBOOK.csv
```

---

## 📊 **DATA FLOW - Complete Pipeline**

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

## 🧹 **AUTOMATIC CLEANUP**

### Retention Policy:
- **data/smart_crawlers/**: ✅ Keep last 30 days (automatic)
- **data/analyzed/**: ✅ Keep last 7 days (automatic)
- **data/combined/**: ⚠️ Manual cleanup (no automatic deletion)
- **data/raw/**: ❌ DEPRECATED (not used)

### Run Cleanup:
```bash
# Manual cleanup
python backend/utils/data_cleanup.py

# Or in code
from backend.utils.data_cleanup import cleanup_old_data
cleanup_old_data(days_smart=30, days_analyzed=7)
```

### Previous Cleanup Results:
- Files deleted: 57
- Space freed: 14.12 MB
- Old files removed: 139-238 days old

---

## 📋 **CSV COLUMN FORMATS**

### 1. RAW Data Columns (15 total):
**Location**: `data/smart_crawlers/PLATFORM/*.csv`
```
Platform, Type, ID, Text, URL, Date
likes, shares, comments_count, views
sentiment_score, total_engagement, engagement_score
author, author_followers
```

### 2. ANALYZED Data Columns (27 total):
**Location**: `data/analyzed/*.csv`
**Content**: RAW columns + these additional columns:
```
sentiment_label (😊 Positive / 😐 Neutral / 😠 Negative)
sentiment_confidence (0.0-1.0)
detected_language (ms/en/zh)
demographic (Malay/English/Chinese)
emotion_primary (joy/anger/fear/sadness/love/surprise)
emotion_anger, emotion_fear, emotion_happy
emotion_sadness, emotion_love, emotion_surprise (all 0.0-1.0)
```

### 3. COMBINED Data Columns (27 total):
**Location**: `data/combined/*.csv`
**Content**: Same as ANALYZED data, but includes ALL platforms in ONE file
```
All columns from ANALYZED data
Platform column shows: facebook, instagram, x, tiktok, youtube, linkedin, news, lowyat, shopee, lazada
```

---

## ✅ **WHAT WAS FIXED** (2026-02-15)

### 1. **Single Storage System** (Updated Feb 15)
- ✅ Updated `_save_results()` in `simple_apify_adapter.py` (lines 701-754)
- ✅ Now saves to **ONLY** `data/smart_crawlers/` (removed dual storage)
- ✅ Unique timestamped filenames for all archives
- ❌ NO LONGER saves to `data/raw/`

### 2. **Combined Data Support** (NEW - Feb 15)
- ✅ Updated `web_backend/simple_app.py` (lines 2720-2743)
- ✅ Automatically saves combined data from ALL platforms
- ✅ Location: `data/combined/Combined_PLATFORMS_YYYYMMDD_HHMMSS.csv`
- ✅ Perfect for cross-platform analysis

### 3. **Cleanup Utility**
- ✅ Created `backend/utils/data_cleanup.py`
- ✅ Automatic deletion of old files
- ✅ Configurable retention periods (30 days smart, 7 days analyzed)
- ✅ Storage statistics reporting
- ✅ Tested: Deleted 57 files, freed 14.12 MB

### 4. **All 10 Platforms Supported**
- ✅ Facebook, Instagram, X/Twitter, TikTok, YouTube
- ✅ LinkedIn, Google News, Lowyat, Shopee, Lazada
- ✅ Each platform has dedicated folder in `smart_crawlers/`
- ✅ All platforms save to `analyzed/` with sentiment/emotion
- ✅ All platforms included in `combined/` for cross-platform analysis

---

## 🚀 **USAGE EXAMPLES**

### Check Storage Stats:
```python
from backend.utils.data_cleanup import get_storage_info

stats = get_storage_info()
print(f"Total files: {stats['total_files']}")
print(f"Total size: {stats['total_size_mb']:.2f} MB")
```

### Run Cleanup:
```python
from backend.utils.data_cleanup import cleanup_old_data

result = cleanup_old_data(days_smart=30, days_analyzed=7)
print(f"Deleted {result['files_deleted']} files")
print(f"Freed {result['mb_freed']:.2f} MB")
```

### Access Combined Data:
```python
import pandas as pd
from pathlib import Path

# Find most recent combined file
combined_dir = Path("data/combined")
combined_files = sorted(combined_dir.glob("Combined_*.csv"), key=lambda f: f.stat().st_mtime, reverse=True)

if combined_files:
    latest_combined = combined_files[0]
    df = pd.read_csv(latest_combined)
    print(f"Loaded {len(df)} records from {len(df['Platform'].unique())} platforms")
```

### Compare Sentiment Across Platforms:
```python
import pandas as pd

# Load combined data
df = pd.read_csv("data/combined/Combined_facebook_instagram_x_20260215_154530.csv")

# Group by platform and calculate average sentiment
platform_sentiment = df.groupby('Platform').agg({
    'sentiment_score': 'mean',
    'total_engagement': 'sum',
    'likes': 'sum'
}).round(2)

print(platform_sentiment)
```

### Export to Excel for Reporting:
```python
import pandas as pd

# Load combined data
df = pd.read_csv("data/combined/Combined_facebook_instagram_x_20260215_154530.csv")

# Export to Excel with multiple sheets
with pd.ExcelWriter('InsightPulse_Report.xlsx') as writer:
    df.to_excel(writer, sheet_name='All Data', index=False)

    # Sentiment summary by platform
    sentiment_summary = df.groupby('Platform')['sentiment_label'].value_counts().unstack(fill_value=0)
    sentiment_summary.to_excel(writer, sheet_name='Sentiment Summary')

    # Top posts by engagement
    top_posts = df.nlargest(50, 'total_engagement')[['Platform', 'Text', 'total_engagement', 'sentiment_label']]
    top_posts.to_excel(writer, sheet_name='Top Posts', index=False)

print("✅ Excel report generated!")
```

---

## 📝 **SUMMARY - 3 STORAGE LOCATIONS**

| Type | Location | Content | Retention | Status |
|------|----------|---------|-----------|--------|
| **Raw** | `data/smart_crawlers/PLATFORM/` | Posts + Comments (per platform) | 30 days | ✅ Active |
| **Analyzed** | `data/analyzed/` | Posts + Comments + Sentiment + Emotion (per platform) | 7 days | ✅ Active |
| **Combined** | `data/combined/` | ALL platforms merged + Sentiment + Emotion | Manual | ⭐ NEW! |
| **data/raw/** | `data/raw/` | (deprecated) | N/A | ❌ Not used |

---

## 🎯 **READY TO USE!**

**Next time you run analysis:**
1. ✅ Each platform saves RAW data to `data/smart_crawlers/PLATFORM/`
2. ✅ Each platform saves ANALYZED data to `data/analyzed/`
3. ✅ **ALL platforms COMBINED** save to `data/combined/` ⭐ NEW!

**Perfect for:**
- ✅ Cross-platform sentiment comparison
- ✅ Comprehensive trend analysis
- ✅ Multi-platform reporting
- ✅ Export for external tools (Excel, Tableau, Power BI)
- ✅ Historical data analysis
- ✅ Competitive intelligence
- ✅ Crisis monitoring across platforms

---

## 📚 **RELATED FILES**

- **Main Documentation**: `DATA_STORAGE_STRUCTURE.md` - Complete technical details
- **Crawler Code**: `backend/data_crawlers/simple_apify_adapter.py` - Lines 701-754
- **Backend Code**: `web_backend/simple_app.py` - Lines 2720-2743
- **Cleanup Utility**: `backend/utils/data_cleanup.py`
- **Quick Start**: `START_INSIGHTPULSE.md`

---

**Last Updated:** 2026-02-15
**Version:** 2.0 - Combined Data Support
**All 10 Platforms:** ✅ Facebook, Instagram, X, TikTok, YouTube, LinkedIn, Google News, Lowyat, Shopee, Lazada

