# 📊 INSIGHTPULSE CRAWLING STRATEGY
## Post + Comments Data Collection Strategy

---

## 🎯 1. RATIO STRATEGY (30:70)

### Posts : Comments = 30% : 70%

| Dataset Size | Posts | Comments | Comments/Post | Estimated Cost (X/Twitter) |
|--------------|-------|----------|---------------|----------------------------|
| **Quick Test (50)** | 15 | 35 | 2-3 | $0.09 |
| **Quick Analysis (1,000)** | 300 | 700 | 2-3 | $1.83 |
| **Standard Analysis (5,000)** | 1,500 | 3,500 | 2-3 | $9.13 |
| **Deep Analysis (10,000)** | 3,000 | 7,000 | 2-3 | $18.25 |
| **Market Research (25,000)** | 7,500 | 17,500 | 2-3 | $45.63 |
| **Enterprise Analysis (50,000)** | 15,000 | 35,000 | 2-3 | $91.25 |
| **Big Data Insights (100,000)** | 30,000 | 70,000 | 2-3 | $182.50 |

**Rationale:**
- ✅ Posts = Data utama (topik, context)
- ✅ Comments = Data sokongan (insights, sentiment, opinions)
- ✅ Comments lebih penting untuk analytics mendalam
- ✅ Public opinion terdapat dalam comments

---

## 🔄 2. CRAWLING WORKFLOW

### Sequential Approach: Posts → Comments

```
STEP 1: Crawl Posts
   ↓
   - Use AI-generated keywords
   - Target: 30% of dataset size
   - Filter by engagement, date range
   ↓
STEP 2: Analyze & Rank Posts
   ↓
   - Rank by engagement (likes + shares + comments)
   - Filter spam, duplicates
   - Select quality posts
   ↓
STEP 3: Crawl Comments
   ↓
   - Use post URLs from Step 1
   - Target: 70% of dataset size
   - Equal distribution per post
   ↓
STEP 4: Combine & Process
   ↓
   - Merge posts + comments
   - Sentiment analysis
   - Generate reports
```

**Advantages:**
- ✅ Faster execution (parallel post crawling)
- ✅ Cost efficient (filter before comments)
- ✅ Better data quality
- ✅ Easier error handling
- ✅ Flexible adjustment

---

## 📊 3. SAMPLING STRATEGY

### Equal Sampling (All Posts Get Same Comments)

**Formula:**
```
comments_per_post = total_comments_target ÷ total_posts
```

**Example (1,000 results):**
```
Posts: 300
Comments target: 700
Comments per post: 700 ÷ 300 = 2-3 comments per post
```

**Implementation:**
- All posts treated equally
- Simple and fair distribution
- Predictable results
- Easy to calculate costs

---

## 🧠 4. ADAPTIVE ALGORITHM

### Scenario-Based Adjustment

#### **Scenario 1: Banyak Posts, Sikit Comments**
```
Condition: avg_comments_available < 3

Strategy: MAXIMIZE POSTS
- Increase posts allocation up to 50%
- Take available comments (1-2 per post)
- Prioritize post diversity

Example:
- Target: 1,000 results (300 posts + 700 comments)
- Found: 500 posts, avg 1.5 comments/post
- Action: Take 400 posts + 600 comments = 1,000 ✅
```

#### **Scenario 2: Sikit Posts, Banyak Comments**
```
Condition: posts_found < target_posts

Strategy: MAXIMIZE COMMENTS
- Take all available posts
- Increase comments per post
- Cap at 50 comments per post

Example:
- Target: 1,000 results (300 posts + 700 comments)
- Found: 100 posts, avg 50 comments/post
- Action: Take 100 posts + 900 comments = 1,000 ✅
```

#### **Scenario 3: Normal (Ideal Case)**
```
Condition: posts_found >= target_posts AND avg_comments >= 3

Strategy: FOLLOW 30:70 RATIO
- Take target posts (30%)
- Take target comments (70%)
- Standard distribution

Example:
- Target: 1,000 results
- Found: 500 posts, avg 5 comments/post
- Action: Take 300 posts + 700 comments = 1,000 ✅
```

---

## 🎯 5. SMART FILTERING RULES

### Post Selection Criteria (Priority Order):

1. **High Engagement**
   - Total engagement = likes + shares + comments + views
   - Rank posts by total engagement
   - Select top N posts

2. **Date Relevance**
   - Within specified date range
   - Prefer recent posts for trending topics
   - Historical posts for trend analysis

3. **Content Quality**
   - Minimum 20 words
   - Not spam or promotional
   - Has meaningful content
   - Diverse authors

4. **Diversity**
   - Avoid multiple posts from same author
   - Different perspectives
   - Various post types (original, retweet, quote)

### Comment Selection Criteria (Priority Order):

1. **Top Comments**
   - Most liked/upvoted
   - High engagement
   - Quality responses

2. **Recent Comments**
   - Latest discussions
   - Current sentiment
   - Trending opinions

3. **Content Quality**
   - Minimum 10 words
   - Substantial content
   - Not spam or bot-generated

4. **Diversity**
   - Different authors
   - Various viewpoints
   - Balanced sentiment

---

## 📐 6. FALLBACK RULES

### Rule 1: Minimum Posts Guarantee
```
minimum_posts = dataset_size × 0.10

Always ensure at least 10% posts
Even if comments are abundant
```

### Rule 2: Maximum Comments per Post
```
max_comments_per_post = 50

If post has >50 comments:
- Take top 25 (most liked)
- Take recent 25 (latest)
```

### Rule 3: Quality Threshold
```
Skip if:
- Text length < 5 words
- Spam detected
- Duplicate content
- Bot-generated
- Invalid/deleted content
```

### Rule 4: Minimum Data Guarantee
```
If total_results < target × 0.50:
- Expand search keywords
- Extend date range
- Try related hashtags
- Use alternative actors
```

---

## 🌐 7. MULTI-PLATFORM DISTRIBUTION

### Equal Split Strategy

**Formula:**
```
per_platform_allocation = total_dataset_size ÷ number_of_platforms
```

**Example: 1,000 results, 3 platforms (X, Facebook, Instagram)**

```
Per platform: 1,000 ÷ 3 = 333 results

X (Twitter):
- Posts: 100 (30%)
- Comments: 233 (70%)
- Total: 333

Facebook:
- Posts: 100 (30%)
- Comments: 233 (70%)
- Total: 333

Instagram:
- Posts: 100 (30%)
- Comments: 233 (70%)
- Total: 333

Grand Total: 300 posts + 699 comments ≈ 1,000 ✅
```

---

## 💰 8. COST ESTIMATION

### Platform Pricing (Apify Actors)

| Platform | Post Cost | Comment Cost | Actor ID |
|----------|-----------|--------------|----------|
| **X (Twitter)** | $0.25/1K | $0.0025/each | kaitoeasyapi/twitter-x-data-tweet-scraper |
| **Instagram** | $0.50/1K | $0.005/each | apify/instagram-scraper |
| **Facebook** | $0.75/1K | $0.008/each | apify/facebook-posts-scraper |
| **TikTok** | $0.40/1K | $0.004/each | apify/tiktok-scraper |
| **LinkedIn** | $1.00/1K | $0.010/each | apify/linkedin-scraper |
| **YouTube** | $0.30/1K | $0.003/each | apify/youtube-scraper |

### Cost Breakdown by Dataset Size (X/Twitter)

| Dataset Size | Posts | Comments | Post Cost | Comment Cost | **Total Cost** |
|--------------|-------|----------|-----------|--------------|----------------|
| 50 | 15 | 35 | $0.004 | $0.088 | **$0.09** |
| 1,000 | 300 | 700 | $0.075 | $1.750 | **$1.83** |
| 5,000 | 1,500 | 3,500 | $0.375 | $8.750 | **$9.13** |
| 10,000 | 3,000 | 7,000 | $0.750 | $17.500 | **$18.25** |
| 25,000 | 7,500 | 17,500 | $1.875 | $43.750 | **$45.63** |
| 50,000 | 15,000 | 35,000 | $3.750 | $87.500 | **$91.25** |
| 100,000 | 30,000 | 70,000 | $7.500 | $175.000 | **$182.50** |

---

## 🔧 9. IMPLEMENTATION ALGORITHM

### Main Calculation Function

```python
def calculate_crawl_strategy(dataset_size: int, platforms_count: int = 1) -> dict:
    """
    Calculate posts and comments distribution

    Args:
        dataset_size: Total results target (50, 1000, 5000, etc.)
        platforms_count: Number of platforms to crawl

    Returns:
        Dictionary with crawl strategy details
    """

    # Per platform allocation
    per_platform = dataset_size // platforms_count

    # 30:70 ratio (Posts:Comments)
    target_posts = int(per_platform * 0.30)
    target_comments = int(per_platform * 0.70)

    # Comments per post
    comments_per_post = target_comments // target_posts if target_posts > 0 else 0

    return {
        "total_target": dataset_size,
        "platforms_count": platforms_count,
        "per_platform": per_platform,
        "posts_per_platform": target_posts,
        "comments_per_platform": target_comments,
        "comments_per_post": comments_per_post,
        "total_posts": target_posts * platforms_count,
        "total_comments": target_comments * platforms_count
    }
```

### Adaptive Adjustment Function

```python
def adaptive_adjustment(
    posts_found: int,
    avg_comments_available: float,
    target_posts: int,
    target_comments: int
) -> dict:
    """
    Adaptive algorithm to handle edge cases

    Args:
        posts_found: Number of posts actually found
        avg_comments_available: Average comments per post available
        target_posts: Target number of posts (30% of dataset)
        target_comments: Target number of comments (70% of dataset)

    Returns:
        Adjusted strategy
    """

    # Scenario 1: Banyak posts, sikit comments
    if avg_comments_available < 3:
        # Maximize posts (up to 50% more)
        actual_posts = min(posts_found, int(target_posts * 1.5))
        comments_per_post = min(int(avg_comments_available), 2)
        actual_comments = actual_posts * comments_per_post
        scenario = "MAXIMIZE_POSTS"

    # Scenario 2: Sikit posts, banyak comments
    elif posts_found < target_posts:
        # Maximize comments
        actual_posts = posts_found
        # Cap at 50 comments per post
        comments_per_post = min(target_comments // actual_posts, 50)
        actual_comments = actual_posts * comments_per_post
        scenario = "MAXIMIZE_COMMENTS"

    # Scenario 3: Normal (ideal case)
    else:
        # Follow 30:70 ratio
        actual_posts = target_posts
        comments_per_post = target_comments // actual_posts
        actual_comments = target_comments
        scenario = "NORMAL"

    return {
        "scenario": scenario,
        "posts": actual_posts,
        "comments_per_post": comments_per_post,
        "total_comments": actual_comments,
        "total_results": actual_posts + actual_comments,
        "posts_percentage": (actual_posts / (actual_posts + actual_comments)) * 100,
        "comments_percentage": (actual_comments / (actual_posts + actual_comments)) * 100
    }
```

### Post Filtering Function

```python
def filter_and_rank_posts(posts: list, target_count: int) -> list:
    """
    Filter and rank posts by engagement

    Args:
        posts: List of post objects
        target_count: Number of posts to select

    Returns:
        Filtered and ranked list of posts
    """

    # Calculate engagement score
    for post in posts:
        post['engagement_score'] = (
            post.get('likes', 0) +
            post.get('shares', 0) * 2 +  # Shares weighted more
            post.get('comments_count', 0) * 3 +  # Comments weighted most
            post.get('views', 0) * 0.001  # Views weighted less
        )

    # Filter quality posts
    quality_posts = [
        post for post in posts
        if len(post.get('text', '')) >= 20  # Minimum 20 characters
        and post.get('id') != '-1'  # Not mock data
        and post.get('url')  # Has valid URL
    ]

    # Sort by engagement score
    ranked_posts = sorted(
        quality_posts,
        key=lambda x: x['engagement_score'],
        reverse=True
    )

    # Return top N posts
    return ranked_posts[:target_count]
```

### Comment Sampling Function

```python
def sample_comments(
    post_url: str,
    target_count: int,
    sampling_method: str = "equal"
) -> dict:
    """
    Sample comments for a post

    Args:
        post_url: URL of the post
        target_count: Number of comments to get
        sampling_method: "equal", "top", or "recent"

    Returns:
        Comment crawl configuration
    """

    if sampling_method == "equal":
        # Equal distribution
        return {
            "url": post_url,
            "max_comments": target_count,
            "sort": "top",  # Get top comments
            "include_replies": True
        }

    elif sampling_method == "top":
        # Top comments only
        return {
            "url": post_url,
            "max_comments": target_count,
            "sort": "top",
            "include_replies": False
        }

    elif sampling_method == "recent":
        # Recent comments only
        return {
            "url": post_url,
            "max_comments": target_count,
            "sort": "recent",
            "include_replies": True
        }
```

---

## 📱 10. PLATFORM-SPECIFIC STRATEGIES

### X (Twitter)

**Posts Actor:** `kaitoeasyapi/twitter-x-data-tweet-scraper-pay-per-result-cheapest`
**Comments Actor:** `scraper_one/x-post-replies-scraper`

**Strategy:**
- Use `searchTerms` parameter (array)
- Include retweets and quotes
- Filter by engagement
- Get replies using tweet URLs

**Input Example:**
```json
{
  "searchTerms": ["pilihan raya pbt"],
  "max_tweets": 300,
  "include_replies": false,
  "include_retweets": true,
  "queryType": "Latest"
}
```

### Instagram

**Posts Actor:** `apify/instagram-scraper`
**Comments Actor:** Same actor with post URLs

**Strategy:**
- Search by hashtags
- Filter by engagement rate
- Get comments from post URLs
- Include story mentions

### Facebook

**Posts Actor:** `apify/facebook-posts-scraper`
**Comments Actor:** Same actor with post URLs

**Strategy:**
- Search by keywords in groups/pages
- Filter by reactions + shares
- Get comments and replies
- Include reactions data

### TikTok

**Posts Actor:** `apify/tiktok-scraper`
**Comments Actor:** Same actor with video URLs

**Strategy:**
- Search by hashtags and keywords
- Filter by views + likes
- Get comments from video URLs
- Include duets and stitches

### LinkedIn

**Posts Actor:** `apify/linkedin-scraper`
**Comments Actor:** Same actor with post URLs

**Strategy:**
- Search in company pages and profiles
- Filter by professional engagement
- Get comments and reactions
- Include shares and reposts

### YouTube

**Posts Actor:** `apify/youtube-scraper`
**Comments Actor:** Same actor with video URLs

**Strategy:**
- Search by keywords
- Filter by views + likes
- Get comments (top + recent)
- Include replies to comments

---

## ✅ 11. QUALITY ASSURANCE

### Data Validation Checks

1. **Post Validation:**
   - ✅ Valid post ID (not "-1" or empty)
   - ✅ Has URL or permalink
   - ✅ Has author information
   - ✅ Has timestamp
   - ✅ Has text content (>5 words)

2. **Comment Validation:**
   - ✅ Valid comment ID
   - ✅ Linked to valid post
   - ✅ Has author information
   - ✅ Has text content (>3 words)
   - ✅ Has timestamp

3. **Engagement Validation:**
   - ✅ Numeric values (not null)
   - ✅ Reasonable ranges
   - ✅ Consistent with platform norms

### Deduplication

```python
def deduplicate_data(posts: list, comments: list) -> tuple:
    """Remove duplicates based on ID"""

    # Deduplicate posts
    unique_posts = {post['id']: post for post in posts}.values()

    # Deduplicate comments
    unique_comments = {comment['id']: comment for comment in comments}.values()

    return list(unique_posts), list(unique_comments)
```

---

## 🎯 12. SUCCESS METRICS

### Target Achievement

- **Minimum:** 50% of target dataset size
- **Good:** 80% of target dataset size
- **Excellent:** 100% of target dataset size

### Quality Metrics

- **Post Quality:** >90% valid posts (not spam/mock)
- **Comment Quality:** >85% substantial comments (>10 words)
- **Engagement Data:** >95% complete engagement metrics
- **Sentiment Coverage:** >80% successfully analyzed

### Performance Metrics

- **Speed:** <2 minutes per 1,000 results
- **Cost Efficiency:** Within estimated budget ±10%
- **Error Rate:** <5% failed crawls
- **Data Freshness:** >80% posts within date range

---

## 📝 13. IMPLEMENTATION CHECKLIST

### Pre-Crawl
- [ ] Calculate target posts and comments
- [ ] Generate AI-powered keywords
- [ ] Configure platform-specific actors
- [ ] Set date range and filters
- [ ] Estimate costs

### During Crawl
- [ ] Monitor actor progress
- [ ] Check for errors
- [ ] Validate data quality
- [ ] Track costs
- [ ] Log performance metrics

### Post-Crawl
- [ ] Validate total results
- [ ] Deduplicate data
- [ ] Filter spam/mock data
- [ ] Calculate actual costs
- [ ] Generate quality report

### Analysis
- [ ] Sentiment analysis
- [ ] Emotion detection
- [ ] Engagement metrics
- [ ] Trend analysis
- [ ] Generate reports

---

## 🚀 14. FUTURE ENHANCEMENTS

### Planned Improvements

1. **Machine Learning Optimization**
   - Predict optimal comments per post
   - Auto-detect trending topics
   - Smart keyword expansion

2. **Cost Optimization**
   - Dynamic actor selection
   - Bulk crawling discounts
   - Cache frequently accessed data

3. **Quality Enhancement**
   - Advanced spam detection
   - Sentiment-based sampling
   - Influencer identification

4. **Performance Boost**
   - Parallel platform crawling
   - Incremental updates
   - Real-time streaming

---

**Document Version:** 1.0
**Last Updated:** 2026-02-09
**Author:** InsightPulse Development Team

