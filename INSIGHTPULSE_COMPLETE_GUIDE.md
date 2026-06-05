# 🎯 InsightPulse - Complete A to Z Guide

**Version 2.0 - Last Updated: 2026-06-05**

> **Comprehensive Social Media Analytics Platform**  
> Crawl, Analyze, Visualize data from 10+ social media platforms with AI-powered sentiment & emotion analysis

---

## 📑 Table of Contents

1. [What is InsightPulse?](#what-is-insightpulse)
2. [Key Features](#key-features)
3. [System Architecture](#system-architecture)
4. [Installation & Setup](#installation--setup)
5. [How to Use](#how-to-use)
6. [Data Storage](#data-storage)
7. [Advanced Features](#advanced-features)
8. [JITP 2026 Project](#jitp-2026-project)
9. [API Reference](#api-reference)
10. [Troubleshooting](#troubleshooting)
11. [For Developers](#for-developers)

---

## 🎯 What is InsightPulse?

**InsightPulse** is a comprehensive social media analytics platform designed to:

- **Crawl data** from 10+ social media platforms
- **Analyze sentiment** using multilingual AI models (Malay, English, Chinese)
- **Detect emotions** (joy, anger, sadness, fear, love, surprise, neutral, disgust)
- **Calculate engagement** metrics (likes, shares, comments, views)
- **Generate insights** with AI-powered analysis
- **Create dashboards** for visual data exploration

### 🌐 Supported Platforms (10 Total)

| Platform | Type | Data Collected |
|----------|------|----------------|
| **Facebook** | Social Media | Posts + Comments |
| **Instagram** | Social Media | Posts + Comments |
| **X (Twitter)** | Social Media | Tweets + Replies |
| **TikTok** | Social Media | Videos + Comments |
| **YouTube** | Social Media | Videos + Comments |
| **LinkedIn** | Professional | Posts + Comments |
| **Google News** | News | Articles |
| **Lowyat Forum** | Forum | Threads + Posts |
| **Shopee** | E-commerce | Products + Reviews |
| **Lazada** | E-commerce | Products + Reviews |

---

## ✨ Key Features

### 1. **AI-Powered Keyword Generation**
- Uses OpenAI GPT-4 & Anthropic Claude
- Generates platform-specific keywords
- Supports multilingual queries (Malay, English, Chinese)

### 2. **Multilingual Sentiment Analysis**
- **Malay**: `rmtariq/ft-Malay-bert` (85% accuracy)
- **English**: `cardiffnlp/twitter-roberta-base-sentiment-latest`
- **Chinese**: `uer/roberta-base-finetuned-chinanews-chinese`
- **Multilingual**: `nlptown/bert-base-multilingual-uncased-sentiment`

### 3. **Emotion Detection**
- **Model**: `rmtariq/multilingual-emotion-classifier`
- **Emotions**: Joy, Anger, Sadness, Fear, Love, Surprise, Neutral, Disgust
- **Languages**: Malay, English, Chinese

### 4. **Engagement Metrics**
- Likes, Shares, Comments, Views
- Total Engagement Score
- Engagement Rate Calculation
- Author Influence Metrics

### 5. **Cross-Platform Analysis**
- Combine data from multiple platforms
- Compare sentiment across platforms
- Track trends over time
- Export to Excel, CSV, JSON

### 6. **Real-Time Crawling**
- Uses Apify & SerpAPI actors
- 2-actor strategy for posts + comments
- Error handling & retry logic
- Progress tracking

---

## 🏗️ System Architecture

```
InsightPulse/
├── 📱 Frontend (Web UI)
│   ├── web_frontend/simple_index.html     # Main interface
│   └── web_frontend/analyze_csv.html      # CSV analysis
│
├── 🔧 Backend (FastAPI Server)
│   ├── web_backend/simple_app.py          # Main server (8001)
│   ├── web_backend/llm_service.py         # AI service
│   └── web_backend/advanced_nlp_processor.py
│
├── 🕷️ Data Crawlers
│   ├── backend/data_crawlers/simple_apify_adapter.py
│   └── crawlers/                          # Platform-specific
│
├── 📊 Data Storage
│   ├── data/smart_crawlers/               # Raw crawled data
│   ├── data/analyzed/                     # Sentiment analyzed
│   └── data/combined/                     # Cross-platform merged
│
├── 🎨 JITP 2026 Project
│   ├── PAS_Dashboard_STANDALONE.html      # Political dashboard
│   └── processed_data/                    # Election analysis
│
└── 📚 Documentation
    ├── DATA_STORAGE_STRUCTURE.md
    ├── CSV_STORAGE_SUMMARY.md
    └── This file!
```

---

## 🚀 Installation & Setup

### Prerequisites

- **Python**: 3.10 or higher
- **RAM**: Minimum 8GB (16GB recommended for ML models)
- **Disk**: 5GB free space
- **OS**: macOS, Linux, or Windows

### Step 1: Clone Repository

```bash
cd /Users/rmtariq/Documents/InsightPulse
```

### Step 2: Create Virtual Environment

```bash
python -m venv NEImpulse
source NEImpulse/bin/activate  # macOS/Linux
# or
NEImpulse\Scripts\activate  # Windows
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Download NLP Models

```bash
python -m spacy download en_core_web_sm
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"
```

### Step 5: Set Environment Variables

Create `.env` file:

```bash
# API Keys
APIFY_API_TOKEN=your_apify_token
SERPAPI_KEY=your_serpapi_key
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_claude_key

# Database (Optional)
DATABASE_URL=sqlite:///data/insightpulse.db
```

---

## 🎮 How to Use

### Method 1: Quick Start (Recommended)

#### Start Backend Server:
```bash
cd /Users/rmtariq/Documents/InsightPulse
python web_backend/simple_app.py
```

**Backend runs on:** http://localhost:8001

#### Open Frontend:
Open browser and navigate to: **http://localhost:8001/**

### Method 2: Background Process

```bash
nohup python web_backend/simple_app.py > backend.log 2>&1 &
```

Check health:
```bash
curl http://localhost:8001/health
```

### Using the Application

#### 1. **Social Listening Analysis**

**Step-by-step:**

a. Open: http://localhost:8001/
b. Select **Analysis Type**: "Social Listening"
c. Select **Platforms**: Facebook, Instagram, X, TikTok, etc.
d. Enter **Query**: e.g., "budi95" or "mara liner"
e. Set **Dataset Size**: 100-1000 (small) or 1000-10000 (large)
f. Click **"Start Analysis"**

**What happens:**
1. ✅ AI generates platform-specific keywords
2. ✅ Crawlers collect data from selected platforms
3. ✅ Sentiment analysis runs (Malay/English/Chinese)
4. ✅ Emotion detection applied
5. ✅ Engagement metrics calculated
6. ✅ Results saved to `data/analyzed/` and `data/combined/`
7. ✅ Dashboard displays results

#### 2. **Crisis Detection**

Monitors for negative sentiment spikes and urgent keywords:
- Selects crisis-related keywords
- Filters for negative sentiment
- Highlights high-engagement negative posts
- Alerts on sentiment drops

#### 3. **Trend Analysis**

Tracks topics over time:
- Time-series sentiment analysis
- Volume tracking
- Platform comparison
- Viral content detection

#### 4. **Analyze Existing CSV**

**URL:** http://localhost:8001/analyze_csv.html

Upload your own CSV file:
- Must contain "Text" column
- Optional: Platform, Date, URL columns
- Outputs: Sentiment, Emotion, Engagement scores

---

## 📂 Data Storage

### Storage Structure (Updated Feb 15, 2026)

```
data/
├── smart_crawlers/           # RAW crawled data (30-day retention)
│   ├── facebook/
│   │   └── facebook_query_YYYYMMDD_HHMMSS.csv
│   ├── instagram/
│   ├── x/
│   ├── tiktok/
│   ├── youtube/
│   ├── linkedin/
│   ├── news/
│   ├── lowyat/
│   ├── shopee/
│   └── lazada/
│
├── analyzed/                 # Sentiment + Emotion (7-day retention)
│   └── Sentiment_Emotion_PLATFORM_YYYYMMDD_HHMMSS.csv
│
└── combined/                 # Cross-platform merged (manual cleanup)
    └── Combined_PLATFORMS_YYYYMMDD_HHMMSS.csv
```

### CSV File Formats

#### Raw Data (15 columns):
```
Platform, Type, ID, Text, URL, Sentiment, Date,
likes, shares, comments_count, views,
author, author_followers, author_url, location
```

#### Analyzed Data (27 columns):
```
All above + sentiment_score, sentiment_label, sentiment_confidence,
detected_language, demographic, total_engagement, engagement_score,
emotion_anger, emotion_disgust, emotion_fear, emotion_joy,
emotion_neutral, emotion_sadness, emotion_love, emotion_surprise
```

#### Combined Data (27 columns):
- Merges ALL platforms into ONE CSV
- Same format as Analyzed Data
- Perfect for cross-platform comparison

### Data Cleanup

Run cleanup utility:
```python
from backend.utils.data_cleanup import cleanup_old_data

result = cleanup_old_data(days_smart=30, days_analyzed=7)
print(f"Deleted {result['files_deleted']} files")
print(f"Freed {result['mb_freed']:.2f} MB")
```

---

## 🎨 Advanced Features

### 1. **AI Insights Generation**

Uses OpenAI GPT-4 to generate:
- Executive summaries
- Key findings
- Recommendations
- Risk assessments

### 2. **Political Analysis (JITP 2026)**

**Dashboard:** `file:///Users/rmtariq/Documents/InsightPulse/JITP_2026/PAS_Dashboard_STANDALONE.html`

Features:
- Political sentiment tracking
- Entity extraction (PAS, Bersatu, PN, etc.)
- Narrative analysis
- Temporal trends
- Platform influence ranking

**Data Location:**
- Raw data: `JITP_2026/processed_data/`
- Analysis reports: `JITP_2026/analysis_reports/`

### 3. **KDEBWM Analytics Module**

Specialized for waste management complaints:
```python
from backend.services.kdebwm_analytics import KDEBWMAnalytics

analyzer = KDEBWMAnalytics()
results = analyzer.analyze_csv("your_data.csv")
```

### 4. **Mara Liner Analysis**

Transport service analysis:
```python
from backend.services.mara_liner_analysis import MaraLinerAnalyzer

analyzer = MaraLinerAnalyzer()
insights = analyzer.analyze("Mara Liner")
```

---

## 🔌 API Reference

### Base URL
```
http://localhost:8001
```

### Endpoints

#### 1. Health Check
```bash
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "data_available": true
}
```

#### 2. Start Analysis
```bash
POST /api/analyze
Content-Type: application/json

{
  "query": "budi95",
  "platforms": ["facebook", "instagram", "x"],
  "analysis_type": "social_listening",
  "dataset_size": 500
}
```

**Response:**
```json
{
  "status": "success",
  "task_id": "abc123",
  "message": "Analysis started"
}
```

#### 3. Generate Keywords
```bash
POST /api/generate-keywords
Content-Type: application/json

{
  "query": "fuel subsidy Malaysia",
  "platforms": ["facebook", "x"],
  "num_keywords": 10
}
```

#### 4. Analyze CSV File
```bash
POST /api/analyze-csv
Content-Type: multipart/form-data

file: your_file.csv
```

#### 5. Get Available Files
```bash
GET /api/files/smart_crawlers
GET /api/files/analyzed
GET /api/files/combined
```

---

## 🛠️ Troubleshooting

### Common Issues

#### 1. **Backend Won't Start - Port 8001 Already in Use**

**Solution:**
```bash
# Kill existing process
lsof -ti:8001 | xargs kill -9

# Restart backend
python web_backend/simple_app.py
```

#### 2. **Models Not Loading**

**Error:** `Model not found` or `Out of memory`

**Solution:**
```bash
# Clear cache
rm -rf ~/.cache/huggingface/

# Restart with more memory
export PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.0
python web_backend/simple_app.py
```

#### 3. **Apify API Error: "Insufficient credits"**

**Solution:**
- Check Apify dashboard: https://console.apify.com/
- Add credits or use smaller dataset sizes
- Use SerpAPI for cheaper alternatives (News, Lowyat)

#### 4. **No Data in Combined Folder**

**Reason:** Combined data feature is NEW (Feb 15, 2026)

**Solution:** Run a new analysis with multiple platforms

#### 5. **Sentiment Analysis Slow**

**Reason:** ML models running on CPU

**Solution:**
- Use GPU if available
- Reduce batch size
- Process in batches

---

## 👨‍💻 For Developers

### Project Structure Explained

#### Frontend (`web_frontend/`)
- **simple_index.html**: Main UI (Social Listening, Crisis, Trends)
- **analyze_csv.html**: Upload & analyze CSV files
- **assets/**: CSS, JS, images

#### Backend (`web_backend/`)
- **simple_app.py**: Main FastAPI server (2700+ lines)
  - Routes: `/api/analyze`, `/api/generate-keywords`, etc.
  - Sentiment analysis logic (lines 2296-2331)
  - Combined data saving (lines 2720-2743)
- **llm_service.py**: OpenAI + Anthropic integration
- **advanced_nlp_processor.py**: KeyBERT, spaCy, NER

#### Data Crawlers (`backend/data_crawlers/`)
- **simple_apify_adapter.py**: Universal adapter (754 lines)
  - `crawl()`: Main crawling method
  - `_save_results()`: Save to smart_crawlers/ (lines 701-754)
  - Actor mapping for 10 platforms
- **crawl_strategy.py**: 2-actor strategy (posts + comments)

#### Services (`backend/services/`)
- **ai_keyword_generator.py**: GPT-4 keyword generation
- **batch_sentiment_processor.py**: Batch ML processing
- **kdebwm_analytics.py**: Waste management analysis
- **universal_intelligence_dashboard.py**: Dashboard generation

#### Utils (`backend/utils/`)
- **data_cleanup.py**: Automatic file cleanup (30-day retention)

### Adding a New Platform

**Example: Adding "Reddit"**

1. **Add to actor_map** (`simple_apify_adapter.py`):
```python
self.actor_map = {
    # ... existing
    'reddit': 'apify/reddit-scraper'
}
```

2. **Add input mapping** (`crawl_strategy.py`):
```python
def _prepare_reddit_input(self, query: str, dataset_size: int) -> Dict:
    return {
        "searchTerms": [query],
        "maxResults": dataset_size
    }
```

3. **Add to frontend** (`simple_index.html`):
```html
<label>
    <input type="checkbox" name="platform" value="reddit">
    Reddit
</label>
```

4. **Create folder**:
```bash
mkdir -p data/smart_crawlers/reddit
```

### Testing

Run platform tests:
```bash
python test_single_platform.py facebook
python test_single_platform.py instagram
```

Run full test:
```bash
pytest backend/tests/
```

---

## 📊 JITP 2026 Project

### Overview

**JITP 2026** is a political analysis project focused on **Malaysian election monitoring**.

**Main Dashboard:**
```
file:///Users/rmtariq/Documents/InsightPulse/JITP_2026/PAS_Dashboard_STANDALONE.html
```

### Features

1. **Political Sentiment Tracking**
   - PAS vs Bersatu discourse
   - Positive/Negative/Neutral trends
   - Daily/Weekly/Monthly aggregation

2. **Entity Analysis**
   - PAS, Bersatu, PN (Perikatan Nasional)
   - Leaders: Hadi Awang, Muhyiddin, etc.
   - Issues: Religion, corruption, governance

3. **Platform Influence Ranking**
   - Which platform has most engagement?
   - Facebook vs X vs TikTok vs Threads

4. **Narrative Analysis**
   - What are people talking about?
   - Key themes and topics
   - Sentiment by narrative

### Data Files

**Location:** `JITP_2026/processed_data/`

- `Combined_facebook_threads_tiktok_*.csv` - Raw crawled data
- `pas_bersatu_analysis_ready.csv` - Cleaned & processed
- `step1_statistics.txt` - Data quality report

**Analysis Reports:** `JITP_2026/analysis_reports/`

- `EXECUTIVE_SUMMARY.md` - High-level insights
- `top_10_most_engaged_posts.csv` - Viral content
- `platform_influence_ranking.csv` - Platform comparison
- `temporal_weekly_volume.csv` - Time series

### Usage

**Open Dashboard:**
```bash
# macOS
open JITP_2026/PAS_Dashboard_STANDALONE.html

# Linux
xdg-open JITP_2026/PAS_Dashboard_STANDALONE.html

# Windows
start JITP_2026/PAS_Dashboard_STANDALONE.html
```

**Run Analysis:**
```bash
cd JITP_2026
python generate_dashboard.py
```

---

## 📖 Documentation Files

### Essential Docs

1. **DATA_STORAGE_STRUCTURE.md** (216 lines)
   - Complete technical documentation
   - Folder structure
   - CSV formats
   - Data flow pipeline

2. **CSV_STORAGE_SUMMARY.md** (332 lines)
   - User-friendly summary
   - Usage examples
   - Excel export guide
   - Related files

3. **START_INSIGHTPULSE.md** (154 lines)
   - Quick start guide
   - Installation steps
   - Testing commands

4. **This File** - A to Z complete guide

### Platform-Specific Docs

- `ACTIVE_CRAWLERS_BY_PLATFORM.md` - Crawler status
- `APIFY_ACTORS_SUMMARY.md` - Actor comparison
- `CRAWLER_OPTIMIZATION_SUMMARY.md` - Performance tips

---

## 🎯 Use Cases

### 1. **Brand Monitoring**
```
Query: "Your Brand Name"
Platforms: Facebook, Instagram, X, TikTok
Analysis Type: Social Listening
```

**Output:**
- Sentiment: Positive, Negative, Neutral breakdown
- Engagement: Total likes, shares, comments
- Trends: Volume over time
- Alerts: Negative spikes

### 2. **Crisis Management**
```
Query: "Product Recall" or "Company Scandal"
Platforms: All platforms
Analysis Type: Crisis Detection
```

**Output:**
- Real-time negative sentiment tracking
- Urgent keywords detection
- High-engagement negative posts
- Response recommendations

### 3. **Political Campaign**
```
Query: "PAS" or "Bersatu" or "Election"
Platforms: Facebook, X, Threads, TikTok
Analysis Type: Trend Analysis
```

**Output:**
- Sentiment by entity
- Platform influence
- Viral content
- Strategic messaging suggestions

### 4. **Product Launch**
```
Query: "New Product Name"
Platforms: Shopee, Lazada, Facebook, Instagram
Analysis Type: Social Listening
```

**Output:**
- Customer sentiment
- Review analysis
- Comparison with competitors
- Purchase intent signals

### 5. **Government Services**
```
Query: "KDEBWM" or "Waste Management"
Platforms: Facebook, X, Lowyat
Analysis Type: Crisis Detection
```

**Output:**
- Complaint detection
- Service issue categorization
- Response urgency scoring
- Geographic distribution

---

## 🚀 Advanced Usage

### Export to Excel

```python
import pandas as pd

# Load combined data
df = pd.read_csv("data/combined/Combined_facebook_instagram_x_20260605.csv")

# Create Excel with multiple sheets
with pd.ExcelWriter('InsightPulse_Report.xlsx') as writer:
    # All data
    df.to_excel(writer, sheet_name='All Data', index=False)

    # Sentiment summary
    sentiment_summary = df.groupby('Platform')['sentiment_label'].value_counts().unstack(fill_value=0)
    sentiment_summary.to_excel(writer, sheet_name='Sentiment Summary')

    # Top posts
    top_posts = df.nlargest(50, 'total_engagement')[['Platform', 'Text', 'total_engagement', 'sentiment_label']]
    top_posts.to_excel(writer, sheet_name='Top Posts', index=False)
```

### Compare Platforms

```python
# Load combined data
df = pd.read_csv("data/combined/Combined_*.csv")

# Group by platform
platform_stats = df.groupby('Platform').agg({
    'sentiment_score': 'mean',
    'total_engagement': 'sum',
    'likes': 'sum',
    'Text': 'count'
}).round(2)

platform_stats.columns = ['Avg Sentiment', 'Total Engagement', 'Total Likes', 'Posts']
print(platform_stats)
```

### Track Trends Over Time

```python
# Load data
df = pd.read_csv("data/combined/Combined_*.csv")
df['Date'] = pd.to_datetime(df['Date'])

# Daily sentiment
daily_sentiment = df.groupby(df['Date'].dt.date)['sentiment_score'].mean()

# Plot
import matplotlib.pyplot as plt
daily_sentiment.plot(kind='line', title='Sentiment Trend')
plt.ylabel('Sentiment Score')
plt.show()
```

---

## 🔐 Security & Privacy

### Environment Variables

**NEVER commit these to git:**
- `APIFY_API_TOKEN`
- `SERPAPI_KEY`
- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`

**Always use `.env` file:**
```bash
# Add to .gitignore
echo ".env" >> .gitignore
```

### Data Privacy

- Personal data (names, emails) should be anonymized
- Comply with data protection regulations (GDPR, PDPA)
- Use encryption for sensitive data
- Implement access controls

---

## 💡 Tips & Best Practices

### 1. **Optimize Dataset Size**

| Use Case | Recommended Size |
|----------|------------------|
| Quick Test | 100-500 |
| Brand Monitoring | 1,000-5,000 |
| Crisis Detection | 5,000-10,000 |
| Research Project | 10,000+ |

### 2. **Choose Right Platforms**

| Goal | Recommended Platforms |
|------|----------------------|
| Consumer Sentiment | Facebook, Instagram, X |
| Product Reviews | Shopee, Lazada |
| News Monitoring | Google News, Lowyat |
| Professional Insights | LinkedIn |
| Viral Content | TikTok, YouTube |

### 3. **Keyword Strategy**

**Good Keywords:**
- Specific: "Budi95 subsidi" vs "Malaysia"
- Multilingual: Mix Malay + English
- Boolean: Use OR, AND for combinations

**Bad Keywords:**
- Too generic: "news", "Malaysia"
- Single word: "car"
- No context: Random characters

### 4. **Data Cleanup**

Run cleanup weekly:
```bash
python -c "from backend.utils.data_cleanup import cleanup_old_data; cleanup_old_data(30, 7)"
```

---

## 📞 Support & Contact

### Documentation
- **Main Guide**: This file
- **Storage Guide**: `DATA_STORAGE_STRUCTURE.md`
- **CSV Guide**: `CSV_STORAGE_SUMMARY.md`
- **Quick Start**: `START_INSIGHTPULSE.md`

### Logs
- **Backend Log**: `backend.log`
- **API Log**: `api.log`
- **Crawler Log**: Check terminal output

### Common Locations

**Frontend:**
```
http://localhost:8001/
http://localhost:8001/analyze_csv.html
```

**Dashboards:**
```
file:///Users/rmtariq/Documents/InsightPulse/JITP_2026/PAS_Dashboard_STANDALONE.html
```

**Data:**
```
/Users/rmtariq/Documents/InsightPulse/data/smart_crawlers/
/Users/rmtariq/Documents/InsightPulse/data/analyzed/
/Users/rmtariq/Documents/InsightPulse/data/combined/
```

---

## 🎓 Learning Resources

### Understanding Sentiment Analysis
- **Score Range**: -1 (very negative) to +1 (very positive)
- **Labels**: Negative, Neutral, Positive
- **Confidence**: 0-1 (higher = more confident)

### Understanding Emotions
- **8 Emotions**: Anger, Disgust, Fear, Joy, Neutral, Sadness, Love, Surprise
- **Scores**: 0-1 for each emotion
- **Dominant**: Highest score wins

### Understanding Engagement
- **Total Engagement** = Likes + Shares + Comments + (Views/10)
- **Engagement Rate** = Total Engagement / Author Followers
- **High Engagement** = Viral content potential

---

## 🚦 Quick Reference

### Start Application
```bash
python web_backend/simple_app.py
```
**Open:** http://localhost:8001/

### Run Analysis
1. Select platforms
2. Enter query
3. Set dataset size
4. Click "Start Analysis"
5. Wait for results
6. Download CSV or view dashboard

### Check Data
```bash
# Smart crawlers (raw)
ls -lh data/smart_crawlers/facebook/

# Analyzed (with sentiment)
ls -lh data/analyzed/

# Combined (cross-platform)
ls -lh data/combined/
```

### Cleanup
```python
from backend.utils.data_cleanup import cleanup_old_data
result = cleanup_old_data(days_smart=30, days_analyzed=7)
```

---

## 🎉 Summary

### What You Can Do

✅ **Crawl** data from 10+ platforms
✅ **Analyze** sentiment in 3 languages (Malay, English, Chinese)
✅ **Detect** 8 emotions (Joy, Anger, Sadness, etc.)
✅ **Calculate** engagement metrics (Likes, Shares, Comments)
✅ **Generate** AI insights with GPT-4
✅ **Create** visual dashboards
✅ **Export** to Excel, CSV, JSON
✅ **Monitor** brands, products, campaigns
✅ **Detect** crises in real-time
✅ **Track** trends over time
✅ **Compare** platforms

### Quick Numbers

- **10 Platforms** supported
- **4 Sentiment Models** (Malay, English, Chinese, Multilingual)
- **1 Emotion Model** (8 emotions)
- **3 Storage Locations** (Raw, Analyzed, Combined)
- **27 Columns** in analyzed CSV
- **30-day** retention for raw data
- **7-day** retention for analyzed data

---

## 📝 Version History

**Version 2.0** (2026-06-05)
- ✅ Added combined data feature
- ✅ Removed data/raw/ storage (deprecated)
- ✅ Updated documentation
- ✅ Added JITP 2026 project
- ✅ Improved cleanup utility

**Version 1.0** (2026-02-08)
- ✅ Initial release
- ✅ 10 platforms support
- ✅ Multilingual sentiment
- ✅ Emotion detection

---

## 🙏 Credits

**Developed by:** Ts Dr Raja Mohd Tariqi Bin Raja Lope Ahmad
**Organization:** JITP 2026 Project
**Models Used:**
- `rmtariq/ft-Malay-bert` (Malay Sentiment)
- `cardiffnlp/twitter-roberta-base-sentiment-latest` (English)
- `uer/roberta-base-finetuned-chinanews-chinese` (Chinese)
- `nlptown/bert-base-multilingual-uncased-sentiment` (Multilingual)
- `rmtariq/multilingual-emotion-classifier` (Emotions)

**Services:**
- Apify (Web Scraping)
- SerpAPI (Search & News)
- OpenAI (GPT-4 for insights)
- Anthropic (Claude for analysis)

---

## 🎯 Next Steps

### For New Users
1. ✅ Read this guide (you're doing it!)
2. ✅ Install dependencies
3. ✅ Set environment variables
4. ✅ Start backend server
5. ✅ Run first analysis
6. ✅ Explore dashboards

### For Developers
1. ✅ Review code structure
2. ✅ Check `simple_app.py` (main server)
3. ✅ Review `simple_apify_adapter.py` (crawlers)
4. ✅ Test individual platforms
5. ✅ Add new features
6. ✅ Contribute improvements

### For Researchers
1. ✅ Run analysis on your topic
2. ✅ Export data to Excel
3. ✅ Analyze sentiment trends
4. ✅ Compare platforms
5. ✅ Generate insights
6. ✅ Publish findings

---

**🎯 InsightPulse - Your Complete Social Media Analytics Solution**

**Last Updated:** 2026-06-05
**Version:** 2.0
**Status:** ✅ Production Ready

**Need Help?** Check the documentation files or review the logs!

---

**END OF GUIDE**

