# 📦 Archive Log - InsightPulse

## May 17, 2026 - Cleanup Actions

### ✅ Action 1: Moved platform_crawlers/ to Archive

**Date:** 2026-05-17  
**Action:** Moved `backend/data_crawlers/platform_crawlers/` to `xyz_folder/old_code/`

**Reason:**
- ❌ NOT integrated with main app
- ❌ NOT imported by simple_apify_adapter.py
- ❌ Different architecture (database vs CSV)
- ❌ Duplicate functionality
- ❌ Would cost MORE money to use

**Files Archived (15 files):**
1. `__init__.py`
2. `base_crawler.py`
3. `facebook_crawler.py`
4. `google_news_crawler.py`
5. `instagram_crawler.py`
6. `lazada_crawler.py`
7. `linkedin_comments_crawler.py`
8. `linkedin_crawler.py`
9. `linkedin_posts_crawler.py`
10. `lowyat_crawler.py`
11. `reddit_crawler.py`
12. `shopee_crawler.py`
13. `tiktok_crawler.py`
14. `twitter_crawler.py`
15. `youtube_crawler.py`

**Location:** `xyz_folder/old_code/platform_crawlers/`

**Active Crawlers (Remain in Production):**
- ✅ `simple_apify_adapter.py` - Main router for all 10 platforms
- ✅ `scrapling_adapter.py` - FREE news crawler

**Impact:**
- ✅ Cleaner codebase
- ✅ No confusion about which crawlers are active
- ✅ Easy to monitor active code
- ✅ Can restore if needed (files backed up in xyz_folder/)

---

## Summary

**Total Files Archived Today:** 15 crawler files  
**Total Size:** ~150 KB  
**Status:** ✅ Successfully archived  
**Main App:** ✅ Still working perfectly

**Active Production System:**
```
backend/data_crawlers/
├── simple_apify_adapter.py    ✅ ACTIVE (all 10 platforms)
└── scrapling_adapter.py        ✅ ACTIVE (FREE news)
```

**Archived (Not Used):**
```
xyz_folder/old_code/platform_crawlers/
├── google_news_crawler.py      ❌ NOT USED
├── facebook_crawler.py          ❌ NOT USED
├── instagram_crawler.py         ❌ NOT USED
├── twitter_crawler.py           ❌ NOT USED
├── tiktok_crawler.py            ❌ NOT USED
├── youtube_crawler.py           ❌ NOT USED
├── linkedin_crawler.py          ❌ NOT USED
├── lowyat_crawler.py            ❌ NOT USED
├── shopee_crawler.py            ❌ NOT USED
├── lazada_crawler.py            ❌ NOT USED
├── reddit_crawler.py            ❌ NOT USED
└── ... (15 files total)
```

---

**Last Updated:** 2026-05-17  
**Status:** ✅ Archive complete  
**Next Steps:** Monitor active crawlers only
