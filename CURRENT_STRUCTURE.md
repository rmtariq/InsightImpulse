# ✅ InsightPulse - Clean Production Structure

## 📂 Current Active Files and Folders

```
InsightPulse/
├── .env                                 # Environment variables (API keys)
├── .env.example                         # Environment template
├── requirements.txt                     # Python dependencies
│
├── README.md                           # Main documentation
├── START_INSIGHTPULSE.md               # Quick start guide
├── HOW_TO_START.md                     # Detailed start instructions
├── CSV_STORAGE_SUMMARY.md              # Storage summary (updated Feb 15)
├── DATA_STORAGE_STRUCTURE.md           # Technical storage docs (updated Feb 15)
├── CLEANUP_PLAN.md                     # This cleanup plan
├── CURRENT_STRUCTURE.md                # This file
│
├── start_insightpulse.sh               # Main startup script ⭐
├── backend.log                         # Current runtime log
│
├── backend/                            # Backend code
│   ├── data_crawlers/                  # All crawler implementations
│   │   ├── simple_apify_adapter.py     # Main Apify adapter ⭐
│   │   ├── scrapling_adapter.py        # FREE crawler (news, youtube)
│   │   ├── platform_crawlers/          # Platform-specific crawlers
│   │   │   ├── facebook_crawler.py
│   │   │   ├── instagram_crawler.py
│   │   │   ├── x_crawler.py
│   │   │   ├── tiktok_crawler.py
│   │   │   ├── youtube_crawler.py
│   │   │   ├── linkedin_crawler.py
│   │   │   ├── news_crawler.py
│   │   │   ├── lowyat_crawler.py
│   │   │   ├── shopee_crawler.py
│   │   │   └── lazada_crawler.py
│   │   └── crawl_strategy.py           # Crawl strategy engine
│   │
│   ├── utils/                          # Utility functions
│   │   ├── data_cleanup.py             # Auto cleanup (30-day retention)
│   │   └── crawl_cache.py              # SQLite caching
│   │
│   ├── services/                       # AI services
│   │   ├── ai_keyword_generator.py     # AI keyword generation
│   │   ├── batch_sentiment_processor.py # Batch sentiment processing
│   │   └── trend_detection.py          # Trend analysis
│   │
│   └── logs/                           # Backend logs
│
├── web_backend/                        # Web backend
│   ├── simple_app.py                   # Main FastAPI backend ⭐⭐⭐
│   ├── advanced_nlp_processor.py       # NLP processing engine
│   └── llm_service.py                  # LLM integration (OpenAI, Claude)
│
├── web_frontend/                       # Web frontend
│   ├── simple_index.html               # Main UI dashboard ⭐⭐⭐
│   └── assets/                         # CSS, JS, images
│       ├── styles.css
│       └── scripts.js
│
├── data/                               # Data storage
│   ├── smart_crawlers/                 # Raw crawled data (30-day retention)
│   │   ├── facebook/                   # (99 files total across all platforms)
│   │   ├── instagram/
│   │   ├── x/
│   │   ├── tiktok/
│   │   ├── youtube/
│   │   ├── linkedin/
│   │   ├── news/
│   │   ├── lowyat/
│   │   ├── shopee/
│   │   └── lazada/
│   │
│   ├── analyzed/                       # Sentiment analysis results (7-day retention)
│   │   └── Sentiment_Emotion_PLATFORM_YYYYMMDD_HHMMSS.csv (3 files)
│   │
│   ├── combined/                       # Cross-platform merged data ⭐ NEW!
│   │   └── Combined_PLATFORMS_YYYYMMDD_HHMMSS.csv
│   │
│   └── insightpulse.db                 # SQLite database (cache)
│
└── xyz_folder/                         # Archived old files (54,597 files)
    ├── old_docs/                       # Old documentation (40+ files)
    ├── old_code/                       # Old code files (30+ files)
    ├── old_tests/                      # Test files (15+ files)
    ├── old_reports/                    # Old reports (70+ folders)
    ├── old_frontend/                   # Old HTML files (8 files)
    ├── old_backend/                    # Old backend files (5 files)
    ├── old_folders/                    # Unused folders (9 folders)
    ├── deprecated_data/                # Deprecated data folders (8 folders)
    ├── config_files/                   # Old config (Procfile, etc.)
    └── log_files/                      # Old log files
```

---

## 🎯 Key Active Files

### Core Application
1. **`web_backend/simple_app.py`** - Main FastAPI backend (runs on port 8001)
2. **`web_frontend/simple_index.html`** - Main dashboard UI
3. **`backend/data_crawlers/simple_apify_adapter.py`** - Crawler adapter

### Startup
- **`start_insightpulse.sh`** - Main startup script

### Configuration
- **`.env`** - Environment variables (API keys)
- **`requirements.txt`** - Python dependencies

### Documentation
- **`README.md`** - Main readme
- **`START_INSIGHTPULSE.md`** - Quick start guide
- **`CSV_STORAGE_SUMMARY.md`** - Storage summary
- **`DATA_STORAGE_STRUCTURE.md`** - Technical docs

---

## 📊 Cleanup Results

**Before:**
- 200+ files in root
- Complex structure
- Many duplicates
- Hard to navigate

**After:**
- 15 files in root (essential only)
- Clean structure
- Easy to monitor
- Production-ready ✅

**Archived:**
- 54,597 files moved to `xyz_folder/`
- All safely backed up
- Can restore if needed

---

## 🚀 How to Start InsightPulse

```bash
# 1. Navigate to project
cd /Users/rmtariq/Documents/InsightPulse

# 2. Run startup script
bash start_insightpulse.sh

# 3. Open browser
# http://localhost:8001
```

---

**Last Updated:** 2026-05-17  
**Status:** ✅ Production-ready & Clean
**All 10 Platforms:** Facebook, Instagram, X, TikTok, YouTube, LinkedIn, Google News, Lowyat, Shopee, Lazada
