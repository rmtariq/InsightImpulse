# 💰 InsightPulse Perfect Analytics - Cost Analysis

## 📊 API Pricing (as of February 2025)

### 1. **Apify API** (8 platforms)
- **Pricing Model**: Compute Units (CU) based
- **Cost**: $49/month for 100 CU (~$0.49 per CU)
- **Free Tier**: $5 free credits monthly

**Platform Actors Used:**
- Facebook Posts Scraper
- Instagram Scraper
- Twitter/X Scraper (kaitoeasyapi)
- TikTok Scraper
- Google Search Scraper
- LinkedIn Scraper

**Estimated CU per platform per run:**
- Facebook: 0.5-2 CU (depending on posts/comments)
- Instagram: 0.3-1.5 CU
- Twitter: 0.2-1 CU
- TikTok: 0.4-1.5 CU
- Google: 0.1-0.5 CU
- LinkedIn: 0.3-1 CU

---

### 2. **SerpAPI** (4 platforms)
- **Pricing Model**: Per search request
- **Cost**: $50/month for 5,000 searches ($0.01 per search)
- **Free Tier**: 100 searches/month free

**Platforms Used:**
- YouTube (via SerpAPI YouTube engine)
- Google News (via SerpAPI Google News engine)
- Shopee (via SerpAPI Google Search with site:shopee.com.my)
- Lazada (via SerpAPI Google Search with site:lazada.com.my)

**Searches per platform:**
- YouTube: 1 search per query
- News: 1 search per query
- Shopee: 1 search per query
- Lazada: 1 search per query

---

### 3. **Claude Sonnet 4.5** (PRIMARY LLM)
- **Pricing**: 
  - Input: $3.00 per million tokens
  - Output: $15.00 per million tokens
- **Average per analysis**: ~50K input tokens, ~10K output tokens

**Cost per analysis:**
- Input: 50,000 tokens × $3.00 / 1M = $0.15
- Output: 10,000 tokens × $15.00 / 1M = $0.15
- **Total: ~$0.30 per analysis**

---

### 4. **OpenAI GPT-4o Mini** (FALLBACK)
- **Pricing**:
  - Input: $0.150 per million tokens
  - Output: $0.600 per million tokens
- **Average per analysis**: ~50K input tokens, ~10K output tokens

**Cost per analysis (if Claude fails):**
- Input: 50,000 tokens × $0.15 / 1M = $0.0075
- Output: 10,000 tokens × $0.60 / 1M = $0.006
- **Total: ~$0.014 per analysis**

---

### 5. **Hugging Face Models** (Sentiment & Emotion)
- **Your Custom Models**: FREE (self-hosted inference)
  - `rmtariq/ft-Malay-bert` (Sentiment)
  - `rmtariq/multilingual-emotion-classifier` (Emotion)
- **Cost**: $0.00 (running locally)

---

## 💵 COST BREAKDOWN BY ANALYSIS DEPTH

### ⚡ **QUICK Analysis** (~1-2 min, 200-300 data points)

**Platforms: All 10 platforms**

| Service | Usage | Cost |
|---------|-------|------|
| **Apify** (6 platforms) | ~3 CU total | $1.47 |
| **SerpAPI** (4 platforms) | 4 searches | $0.04 |
| **Claude Sonnet 4.5** | 1 analysis (20K tokens) | $0.12 |
| **Hugging Face** | Sentiment + Emotion | $0.00 |
| **TOTAL** | | **$1.63** |

---

### 📊 **STANDARD Analysis** (~3-5 min, 800-1200 data points) ⭐ DEFAULT

**Platforms: All 10 platforms**

| Service | Usage | Cost |
|---------|-------|------|
| **Apify** (6 platforms) | ~8 CU total | $3.92 |
| **SerpAPI** (4 platforms) | 4 searches | $0.04 |
| **Claude Sonnet 4.5** | 1 analysis (50K tokens) | $0.30 |
| **Hugging Face** | Sentiment + Emotion | $0.00 |
| **TOTAL** | | **$4.26** |

---

### 🔬 **DEEP Analysis** (~5-10 min, 2000-4000 data points)

**Platforms: All 10 platforms**

| Service | Usage | Cost |
|---------|-------|------|
| **Apify** (6 platforms) | ~18 CU total | $8.82 |
| **SerpAPI** (4 platforms) | 4 searches | $0.04 |
| **Claude Sonnet 4.5** | 1 analysis (100K tokens) | $0.60 |
| **Hugging Face** | Sentiment + Emotion | $0.00 |
| **TOTAL** | | **$9.46** |

---

## 📈 MONTHLY COST ESTIMATES

### Scenario 1: **Small Business** (10 analyses/month)
- **Depth**: Standard
- **Cost**: 10 × $4.26 = **$42.60/month**

### Scenario 2: **Medium Business** (50 analyses/month)
- **Depth**: Mix (20 Quick, 25 Standard, 5 Deep)
- **Cost**: (20×$1.63) + (25×$4.26) + (5×$9.46) = **$186.40/month**

### Scenario 3: **Enterprise** (200 analyses/month)
- **Depth**: Mix (100 Quick, 80 Standard, 20 Deep)
- **Cost**: (100×$1.63) + (80×$4.26) + (20×$9.46) = **$693.20/month**

---

## 💡 COST OPTIMIZATION STRATEGIES

### 1. **Use Subscription Plans**
- **Apify**: $49/month for 100 CU (vs pay-as-you-go)
  - Saves ~30% on high volume
- **SerpAPI**: $50/month for 5,000 searches
  - Saves ~50% vs pay-per-search

### 2. **Platform Selection**
- **Cheapest**: Google, News (SerpAPI only)
- **Most Expensive**: Facebook, TikTok (high CU usage)
- **Strategy**: Select only relevant platforms

### 3. **Analysis Depth**
- **Quick**: Use for initial exploration ($1.63)
- **Standard**: Use for regular monitoring ($4.26)
- **Deep**: Use for comprehensive reports ($9.46)

### 4. **Batch Processing**
- Run multiple queries in one session
- Reuse crawled data for similar queries
- Cache results for 24 hours

---

## 🎯 RECOMMENDED MONTHLY BUDGET

| Business Size | Analyses/Month | Recommended Budget |
|---------------|----------------|-------------------|
| **Startup** | 5-10 | $50-100/month |
| **Small Business** | 20-50 | $150-250/month |
| **Medium Business** | 50-100 | $300-500/month |
| **Enterprise** | 200+ | $700-1000/month |

---

## 📊 COST PER PLATFORM (Standard Analysis)

| Platform | Service | Estimated Cost |
|----------|---------|----------------|
| Facebook | Apify | $0.98 |
| Instagram | Apify | $0.74 |
| Twitter/X | Apify | $0.49 |
| TikTok | Apify | $0.74 |
| Google | Apify | $0.25 |
| LinkedIn | Apify | $0.49 |
| YouTube | SerpAPI | $0.01 |
| News | SerpAPI | $0.01 |
| Shopee | SerpAPI | $0.01 |
| Lazada | SerpAPI | $0.01 |
| **Claude Analysis** | Anthropic | $0.30 |
| **Sentiment/Emotion** | HuggingFace | $0.00 |
| **TOTAL (10 platforms)** | | **$4.26** |

---

## 🚀 ACTUAL COST WITH FREE TIERS

### First Month (with free credits):
- **Apify**: $5 free credits = ~10 CU free
- **SerpAPI**: 100 free searches
- **Effective cost for 10 Standard analyses**: 
  - Apify: $3.92 - $0.50 (free) = $3.42
  - SerpAPI: $0.04 (covered by free tier)
  - Claude: $0.30
  - **Total: $3.72 per analysis** (first 10 analyses)

---

## 💰 TOTAL COST SUMMARY

| Analysis Type | Per Analysis | 10/month | 50/month | 200/month |
|---------------|-------------|----------|----------|-----------|
| **Quick** | $1.63 | $16.30 | $81.50 | $326.00 |
| **Standard** | $4.26 | $42.60 | $213.00 | $852.00 |
| **Deep** | $9.46 | $94.60 | $473.00 | $1,892.00 |

**Most Common (Standard, 50/month)**: **~$213/month**


