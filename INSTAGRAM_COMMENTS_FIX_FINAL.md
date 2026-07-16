# Instagram Comments - Root Cause & Fix (FINAL)

## 🔴 Problem Found in Logs

```
ERROR: Field input.directUrls is required
```

The `apify/instagram-comment-scraper` actor was failing because:
- Code was sending: `"postUrls": batch`
- Actor expected: `"directUrls": batch`

Result: All Instagram comment batches failed → 0 comments collected ❌

---

## ✅ Fix Applied

**File:** `backend/data_crawlers/simple_apify_adapter.py`  
**Line:** 1656

Changed from:
```python
run_input = {
    "postUrls": batch,  # ❌ WRONG
    ...
}
```

Changed to:
```python
run_input = {
    "directUrls": batch,  # ✅ CORRECT
    ...
}
```

---

## 🚀 Backend Status

✅ Restarted with the fix  
✅ All models loaded  
✅ Running on port 8001  

---

## 📋 Next: Test Again

Run a new analysis with Instagram + YouTube:

1. Open: http://localhost:8001
2. Select: Instagram + YouTube
3. Click: "Analyze"
4. Wait: 5-10 minutes
5. Check: Comments should appear! ✅

Expected result:
- Instagram: Posts + Comments (via apify/instagram-comment-scraper)
- YouTube: Posts + Comments (already working)

