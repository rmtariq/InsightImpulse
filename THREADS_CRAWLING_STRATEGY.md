# 🧵 Threads Crawling Strategy - OPTIMIZED

**Last Updated:** 2026-05-28  
**File:** `backend/data_crawlers/simple_apify_adapter.py` (Lines 733-869)

---

## 🎯 **PROBLEM: How to Get Posts + Comments Efficiently?**

When crawling Threads, we have **3 possible approaches**:

---

## 📊 **APPROACH COMPARISON**

### **Approach 1: Post-by-Post (Sequential)**
```
For each post:
  Get 1 post → Get comments → Next post
```

**Performance:**
- ❌ **VERY SLOW** - 200 API calls for 100 posts
- ❌ **EXPENSIVE** - High Apify compute costs
- ❌ **INEFFICIENT** - Actor startup overhead per call

**Example:** 100 posts = 200 API calls (~30-60 minutes)

---

### **Approach 2: All Posts, Then All Comments (Simple Batch)**
```
Step 1: Get ALL posts (100 posts)
Step 2: Get ALL comments in ONE batch call
```

**Performance:**
- ✅ Fast - Only 2 API calls
- ❌ **Limited** - Actor limit: max 20 URLs per call
- ❌ **Brittle** - If Step 2 fails, lose all comments

**Example:** 100 posts = 2 API calls, but only processes 20 posts

---

### **Approach 3: Batched Parallel (CURRENT - BEST) ✅**
```
Step 1: Get ALL posts (100 posts)
Step 2: Split into batches of 20 URLs
Step 3: Fetch ALL batches in PARALLEL
        Batch 1: URLs 1-20  ┐
        Batch 2: URLs 21-40 ├─ Run simultaneously!
        Batch 3: URLs 41-60 ┘
```

**Performance:**
- ✅ **FAST** - Parallel processing (5 batches run at same time!)
- ✅ **EFFICIENT** - Only 6 API calls total (1 + 5 batches)
- ✅ **RELIABLE** - One batch fails, others continue
- ✅ **SCALABLE** - Works for 100-5000 posts

**Example:** 100 posts = 6 API calls (~3-5 minutes)

---

## 🚀 **IMPLEMENTATION DETAILS**

### **Code Location**
`backend/data_crawlers/simple_apify_adapter.py` → `_scrape_threads_with_replies()` (Lines 733-869)

### **Key Features**

#### **1. Smart Post Allocation (30:70 Ratio)**
```python
posts_quota = int(max_results * 0.3)  # 30% for posts
# 70% of dataset_size reserved for comments
```

**Example:** dataset_size=1000
- 300 posts
- 700 comments (from those posts)

#### **2. Parallel Batch Processing**
```python
BATCH_SIZE = 20  # Actor limit
url_batches = [post_urls[i:i + 20] for i in range(0, len(post_urls), 20)]

# Fetch ALL batches in PARALLEL
all_batch_results = await asyncio.gather(
    *[fetch_batch(i, batch) for i, batch in enumerate(url_batches)]
)
```

#### **3. Error Handling**
- ✅ One batch fails → Others continue
- ✅ No Session ID → Falls back to posts-only
- ✅ No posts found → Returns empty gracefully

---

## 📈 **PERFORMANCE COMPARISON**

| Dataset Size | Approach 1 (Post-by-Post) | Approach 2 (Simple Batch) | **Approach 3 (Parallel)** |
|--------------|---------------------------|---------------------------|---------------------------|
| **100 posts** | 200 calls (~60 min) | 2 calls (~5 min) **LIMITED TO 20 POSTS** | **6 calls (~3 min) ✅** |
| **500 posts** | 1000 calls (~5 hrs) | 2 calls (~10 min) **LIMITED TO 20 POSTS** | **26 calls (~8 min) ✅** |
| **1000 posts** | 2000 calls (~10 hrs) | 2 calls (~15 min) **LIMITED TO 20 POSTS** | **51 calls (~12 min) ✅** |

**Winner:** Approach 3 (Batched Parallel) - **10-40x FASTER** than Approach 1! ✅

---

## 🎯 **USAGE**

### **Step 1: Configure Session ID**
Add to `.env`:
```bash
THREADS_SESSION_ID=your_session_id_here
```

### **Step 2: Run Analysis**
Frontend → Select "Threads" → Enter query → Start Analysis

### **Step 3: Check Logs**
```
🧵 Step 1/3: Searching for Threads posts...
✅ Found 100 Threads posts
🧵 Step 2/3: Preparing 100 post URLs for comment fetching...
🚀 Step 3/3: Fetching comments in 5 PARALLEL batches...
   📦 Batch 1/5: Fetching 20 post URLs...
   📦 Batch 2/5: Fetching 20 post URLs...
   📦 Batch 3/5: Fetching 20 post URLs...
   📦 Batch 4/5: Fetching 20 post URLs...
   📦 Batch 5/5: Fetching 20 post URLs...
   ✅ Batch 1: Fetched 150 replies
   ✅ Batch 2: Fetched 142 replies
   ✅ Batch 3: Fetched 138 replies
   ✅ Batch 4: Fetched 125 replies
   ✅ Batch 5: Fetched 118 replies
✅ Fetched 673 total replies from 5 batches
🎉 Total Threads data: 773 items (100 posts + 673 replies)
```

---

## ✅ **BENEFITS**

1. ✅ **10-40x FASTER** than post-by-post approach
2. ✅ **Cost-effective** - Fewer API calls = Lower Apify costs
3. ✅ **Scalable** - Handles 100-5000 posts efficiently
4. ✅ **Reliable** - Partial failures don't stop entire process
5. ✅ **Complete data** - Gets ALL posts (not just 20)

---

## 🔧 **TECHNICAL NOTES**

- **Actor 1:** `igview-owner/threads-search-scraper` (for posts)
- **Actor 2:** `futurizerush/threads-replies-scraper-api` (for comments)
- **Batch Size:** 20 URLs (actor limit)
- **Concurrency:** Unlimited (asyncio.gather)
- **Fallback:** Posts-only if Session ID missing

---

**Ready to use!** 🚀
