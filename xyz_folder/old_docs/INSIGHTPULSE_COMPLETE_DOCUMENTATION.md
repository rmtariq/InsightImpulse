# 📚 InsightPulse - Complete A-Z Documentation

> **Complete Reference Guide for InsightPulse Social Media Analytics Platform**  
> Last Updated: 2026-02-15  
> Version: 2.0 - Combined Data Support

---

## 📖 Table of Contents

1. [Overview](#overview)
2. [What is InsightPulse?](#what-is-insightpulse)
3. [All 10 Platforms](#all-10-platforms)
4. [AI & ML Models](#ai--ml-models)
5. [Data Crawlers](#data-crawlers)
6. [Backend Architecture](#backend-architecture)
7. [Frontend Interface](#frontend-interface)
8. [Data Storage](#data-storage)
9. [API Integrations](#api-integrations)
10. [Analysis Types](#analysis-types)
11. [Features](#features)
12. [File Structure](#file-structure)
13. [How to Start](#how-to-start)
14. [Configuration](#configuration)
15. [Dependencies](#dependencies)

---

## 🎯 Overview

**InsightPulse** is a comprehensive, AI-powered social media analytics platform designed for:
- Real-time data crawling from 10 platforms
- Multilingual sentiment analysis (Malay, English, Chinese, Multilingual)
- Emotion classification (8 emotions)
- Crisis detection and trend analysis
- Professional report generation
- Malaysian market focus

---

## 💡 What is InsightPulse?

### **Purpose**
InsightPulse helps businesses, governments, and researchers:
- Monitor public sentiment across social media and e-commerce platforms
- Detect trending topics and emerging issues
- Analyze customer feedback and reviews
- Track brand reputation
- Perform crisis monitoring
- Generate professional reports

### **Key Capabilities**
1. **Multi-Platform Data Collection** - Crawl 10 platforms simultaneously
2. **AI-Powered Analysis** - 5 sentiment models + 1 emotion model
3. **Multilingual Support** - Malay, English, Chinese, and more
4. **Real-Time Insights** - Live data collection and analysis
5. **Professional Reports** - Auto-generate Excel, PDF, and HTML reports
6. **Malaysian Context** - Optimized for Malaysian market (language, demographics, platforms)

---

## 🌐 All 10 Platforms

| # | Platform | Type | Data Source | Comments Support |
|---|----------|------|-------------|------------------|
| 1 | **Facebook** | Social Media | Apify + SerpAPI | ✅ Yes (2-actor) |
| 2 | **Instagram** | Social Media | Apify | ✅ Yes |
| 3 | **X/Twitter** | Social Media | Apify | ✅ Yes (2-actor) |
| 4 | **TikTok** | Social Media | Apify | ✅ Yes |
| 5 | **YouTube** | Video Platform | Apify | ✅ Yes |
| 6 | **LinkedIn** | Professional Network | Apify | ✅ Yes |
| 7 | **Google News** | News Aggregator | SerpAPI | ❌ No |
| 8 | **Lowyat** | Forum (Malaysia) | SerpAPI | ❌ No |
| 9 | **Shopee** | E-commerce (Malaysia) | Apify | ✅ Yes (Reviews) |
| 10 | **Lazada** | E-commerce (Malaysia) | Apify | ✅ Yes (Reviews) |

### **Platform Details**

#### 1. **Facebook**
- **Actor**: `danek/facebook-search-ppr` (posts) + `apify/facebook-comments-scraper` (comments)
- **Strategy**: 2-actor (separate posts and comments)
- **Data**: Posts, comments, likes, shares, reactions
- **Language**: Malay, English, mixed

#### 2. **Instagram**
- **Actor**: `apify/instagram-scraper`
- **Strategy**: Hashtag-based search
- **Data**: Posts, comments, likes, hashtags, mentions
- **Language**: English, Malay, mixed

#### 3. **X/Twitter**
- **Actor**: `kaitoeasyapi/twitter-x-data-tweet-scraper-pay-per-result-cheapest` (posts) + `scraper_one/x-post-replies-scraper` (replies)
- **Strategy**: 2-actor (separate tweets and replies)
- **Data**: Tweets, replies, retweets, likes, quotes
- **Language**: English, Malay, mixed

#### 4. **TikTok**
- **Actor**: `clockworks/tiktok-scraper`
- **Strategy**: Single-actor (posts + comments)
- **Data**: Videos, comments, likes, shares, views
- **Language**: Mixed languages

#### 5. **YouTube**
- **Actor**: `streamers/youtube-scraper`
- **Strategy**: Single-actor (videos + comments)
- **Data**: Videos, comments, likes, views, channel info
- **Language**: Mixed languages

#### 6. **LinkedIn**
- **Actor**: `testdepth/linkedin-post-search`
- **Strategy**: Single-actor (posts + comments)
- **Data**: Posts, comments, reactions, shares, professional context
- **Language**: English, Malay

#### 7. **Google News**
- **Actor**: SerpAPI (`engine: google_news`)
- **Strategy**: News article search
- **Data**: Articles, headlines, sources, dates
- **Language**: Mixed languages

#### 8. **Lowyat** (Malaysian Tech Forum)
- **Actor**: SerpAPI (`site:lowyat.net`)
- **Strategy**: Google search with site filter
- **Data**: Forum posts, threads, discussions
- **Language**: English, Malay

#### 9. **Shopee** (E-commerce - Malaysia)
- **Actor**: `ecomscrape/shopee-scraper`
- **Strategy**: Product + reviews
- **Data**: Products, reviews (comments), ratings, sales
- **Language**: Malay, English, Chinese

#### 10. **Lazada** (E-commerce - Malaysia)
- **Actor**: `ecomscrape/lazada-reviews-scraper`
- **Strategy**: Product + reviews
- **Data**: Products, reviews (comments), ratings, sales
- **Language**: Malay, English, Chinese

---

## 🤖 AI & ML Models

### **Sentiment Analysis Models** (4 models)

| Model | Language | Accuracy | Use Case |
|-------|----------|----------|----------|
| `rmtariq/ft-Malay-bert` | Malay | 85% | Primary for Malay text |
| `cardiffnlp/twitter-roberta-base-sentiment-latest` | English | High | Social media English |
| `uer/roberta-base-finetuned-chinanews-chinese` | Chinese | High | Chinese text |
| `nlptown/bert-base-multilingual-uncased-sentiment` | Mixed | Good | Fallback for mixed languages |

### **Emotion Classification Model** (1 model)

| Model | Emotions | Languages |
|-------|----------|-----------|
| `rmtariq/multilingual-emotion-classifier` | 8 emotions: anger, disgust, fear, joy, neutral, sadness, love, surprise | Multilingual |

### **NLP Processing**

**Advanced NLP Processor** (`advanced_nlp_processor.py`):
- spaCy English model (`en_core_web_sm`)
- SentenceTransformers (`all-MiniLM-L6-v2`)
- KeyBERT for keyword extraction
- Named Entity Recognition (NER)
- Query expansion
- Malaysian context detection

### **LLM Integration**

**AI Services**:
- **OpenAI**: GPT-4o, GPT-4o-mini (for intelligent analysis)
- **Anthropic**: Claude-3.5-Sonnet, Claude-3-Haiku (for analysis)
- **Use Cases**:
  - AI-powered keyword generation
  - Intelligent insights extraction
  - Report enhancement
  - Query understanding

---

## 🕷️ Data Crawlers

### **Crawler Architecture**

**Main Adapter**: `backend/data_crawlers/simple_apify_adapter.py`

**Features**:
- Multi-platform support (10 platforms)
- Parallel crawling (all platforms simultaneously)
- AI-powered keyword generation
- Smart comment sampling
- 30:70 Posts-to-Comments ratio strategy
- Error handling and retry logic
- Data deduplication

### **Crawling Strategies**

#### **1. Single-Actor Strategy**
Used for: Instagram, TikTok, YouTube, LinkedIn, Shopee, Lazada
- One actor handles both posts and comments
- Simpler, faster
- All data in one API call

#### **2. Two-Actor Strategy**
Used for: Facebook, X/Twitter
- Actor 1: Fetch posts only
- Actor 2: Fetch comments separately
- More reliable for high-volume platforms
- Better comment quality control

#### **3. 30:70 Posts:Comments Ratio**
- 30% of dataset for posts
- 70% of dataset for comments
- Ensures rich engagement data
- Optimized for sentiment analysis

### **AI-Powered Crawling**

**AI Keyword Generator** (`backend/services/ai_keyword_generator.py`):
- Generates platform-optimized keywords
- Understands user intent
- Expands query for better coverage
- Platform-specific formatting (hashtags for Instagram, etc.)

**Example**:
- User query: "pilihan raya PBT"
- AI generates:
  - Facebook: ["pilihan raya PBT", "pilihanraya tempatan", "PBT election"]
  - Instagram: ["#pilihanrayaPBT", "#PBTelection", "#undipru"]
  - Twitter/X: ["pilihanraya PBT", "#PBT2026", "local election MY"]

### **Platform-Specific Crawlers**

Located in: `backend/data_crawlers/platform_crawlers/`

| Crawler File | Platform | Special Features |
|--------------|----------|------------------|
| `facebook_crawler.py` | Facebook | Search-based, 2-actor strategy |
| `instagram_crawler.py` | Instagram | Hashtag optimization |
| `twitter_crawler.py` | X/Twitter | Reply handling, 2-actor |
| `tiktok_crawler.py` | TikTok | Video metadata |
| `youtube_crawler.py` | YouTube | Channel info, video stats |
| `linkedin_crawler.py` | LinkedIn | Professional context |
| `news_crawler.py` | Google News | Article extraction |
| `lowyat_crawler.py` | Lowyat | Forum thread parsing |
| `shopee_crawler.py` | Shopee | Product reviews |
| `lazada_crawler.py` | Lazada | Product reviews |

### **Crawler Settings**

**Apify Configuration** (in `simple_apify_adapter.py`):
```python
actor_map = {
    'facebook': 'danek/facebook-search-ppr',
    'instagram': 'apify/instagram-scraper',
    'twitter': 'kaitoeasyapi/twitter-x-data-tweet-scraper-pay-per-result-cheapest',
    'x': 'kaitoeasyapi/twitter-x-data-tweet-scraper-pay-per-result-cheapest',
    'tiktok': 'clockworks/tiktok-scraper',
    'youtube': 'streamers/youtube-scraper',
    'google': 'apify/google-search-scraper',
    'news': 'serpapi',
    'lowyat': 'serpapi',
    'linkedin': 'testdepth/linkedin-post-search',
    'shopee': 'ecomscrape/shopee-scraper',
    'lazada': 'ecomscrape/lazada-reviews-scraper'
}
```

---

## 🏗️ Backend Architecture

### **Technology Stack**

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Framework** | FastAPI | REST API server |
| **Database** | SQLite/PostgreSQL | Data persistence |
| **ORM** | SQLAlchemy | Database abstraction |
| **AI/ML** | HuggingFace Transformers | Sentiment & emotion analysis |
| **NLP** | spaCy, NLTK, KeyBERT | Text processing |
| **Crawler** | Apify, SerpAPI | Data collection |
| **LLM** | OpenAI, Anthropic | Intelligent analysis |

### **Main Backend File**

**File**: `web_backend/simple_app.py` (2772 lines)

**Key Components**:

1. **FastAPI Application**
   - Port: 8001
   - CORS enabled
   - WebSocket support for real-time updates

2. **Model Initialization** (lines 205-322)
   - Load 4 sentiment models
   - Load 1 emotion model
   - Initialize batch processor

3. **Main Endpoint**: `/analyze` (lines 2023-2772)
   - Phase 1: NLP processing
   - Phase 2: Real-time crawling (parallel)
   - Phase 3: Sentiment & emotion analysis
   - Phase 4: LLM intelligent analysis
   - Phase 5: Trend analysis
   - Phase 6: Report generation

4. **Other Endpoints**:
   - `GET /` - Homepage
   - `GET /health` - Health check
   - `POST /analyze` - Main analysis
   - `GET /platforms` - Available platforms
   - `GET /data/{platform}` - Historical data
   - `WebSocket /ws` - Real-time updates

### **Analysis Pipeline**

```
User Query
    ↓
🧠 Advanced NLP Processing
    ↓
🤖 AI Keyword Generation
    ↓
🕷️ Parallel Multi-Platform Crawling
    ↓
💾 Data Storage (smart_crawlers/)
    ↓
🎭 Sentiment & Emotion Analysis
    ↓
💾 Data Storage (analyzed/)
    ↓
🔗 Combine All Platforms
    ↓
💾 Data Storage (combined/)
    ↓
📊 Trend Analysis
    ↓
🤖 LLM Intelligent Insights
    ↓
📄 Professional Report Generation
    ↓
📊 Return Results to Frontend
```

---

## 🖥️ Frontend Interface

### **Main Interface File**

**File**: `web_frontend/simple_index.html`

**Features**:
- Modern, responsive UI
- Real-time progress updates (WebSocket)
- Platform selection (all 10 platforms)
- Analysis type selection
- Date range filtering
- Interactive visualizations
- Export to Excel/CSV

### **Analysis Types Available**

| Analysis Type | Description | Best For |
|---------------|-------------|----------|
| **Social Listening** | Monitor brand mentions and sentiment | Brand monitoring |
| **Crisis Detection** | Identify negative sentiment spikes | Crisis management |
| **Trend Analysis** | Track trending topics over time | Market research |
| **Competitive Analysis** | Compare multiple brands/topics | Competitive intelligence |
| **Campaign Performance** | Measure marketing campaign impact | Marketing teams |
| **Product Feedback** | Analyze product reviews and feedback | Product managers |
| **Customer Service** | Monitor customer complaints/issues | Support teams |

### **User Interface Components**

1. **Query Input**
   - Natural language search
   - Boolean operators support
   - Malay & English support

2. **Platform Selection**
   - Checkboxes for all 10 platforms
   - Select all/none buttons
   - Platform-specific configuration

3. **Analysis Configuration**
   - Analysis type dropdown
   - Dataset size slider (100-10,000)
   - Date range picker
   - Comment sampling options

4. **Results Display**
   - Summary cards (sentiment, engagement, data points)
   - Sentiment distribution charts
   - Emotion distribution charts
   - Platform comparison tables
   - Top posts/comments
   - Trending topics word cloud

5. **Export Options**
   - Download Excel report
   - Download CSV data
   - Download PDF report
   - View HTML report

---

## 💾 Data Storage

### **Storage Structure** (Updated 2026-02-15)

```
data/
├── smart_crawlers/        # Raw crawled data (30-day retention)
│   ├── facebook/
│   │   └── facebook_query_YYYYMMDD_HHMMSS.csv
│   ├── instagram/
│   │   └── instagram_query_YYYYMMDD_HHMMSS.csv
│   ├── x/
│   │   └── x_query_YYYYMMDD_HHMMSS.csv
│   ├── tiktok/
│   ├── youtube/
│   ├── linkedin/
│   ├── news/
│   ├── lowyat/
│   ├── shopee/
│   └── lazada/
│
├── analyzed/              # Sentiment analysis results (7-day retention)
│   └── Sentiment_Emotion_PLATFORM_YYYYMMDD_HHMMSS.csv
│
├── combined/              # Cross-platform merged data (manual cleanup) ⭐ NEW!
│   └── Combined_PLATFORMS_YYYYMMDD_HHMMSS.csv
│
└── raw/                   # ❌ DEPRECATED - No longer used
```

### **CSV File Formats**

#### 1. **Raw Data** (smart_crawlers/)
**Columns (15)**:
- Platform, Type, ID, Text, URL, Sentiment, Date
- likes, shares, comments_count, views
- author, author_followers
- hashtags, mentions

#### 2. **Analyzed Data** (analyzed/)
**Columns (27)**:
All raw columns PLUS:
- sentiment_score, sentiment_label, sentiment_confidence
- detected_language, demographic
- total_engagement, engagement_score
- emotion_anger, emotion_disgust, emotion_fear, emotion_joy
- emotion_neutral, emotion_sadness, emotion_love, emotion_surprise

#### 3. **Combined Data** (combined/)
**Columns (27)** - Same as analyzed
- Combines ALL selected platforms in ONE file
- Perfect for cross-platform comparison
- Includes sentiment + emotion + engagement

### **Storage Rules** (Updated Feb 15, 2026)

| Location | Saves When | Retention | Cleanup |
|----------|------------|-----------|---------|
| `smart_crawlers/` | After crawling | 30 days | Automatic |
| `analyzed/` | After analysis | 7 days | Automatic |
| `combined/` | After multi-platform analysis | Manual | Manual |
| `raw/` | ❌ NEVER (deprecated) | N/A | N/A |

### **Data Cleanup Utility**

**File**: `backend/utils/data_cleanup.py`

**Features**:
- Automatic deletion of old files
- Configurable retention periods
- Storage statistics reporting
- Safe deletion (never touches combined data)

**Usage**:
```python
from backend.utils.data_cleanup import cleanup_old_data, get_storage_info

# Get storage stats
stats = get_storage_info()
print(f"Total files: {stats['total_files']}")
print(f"Total size: {stats['total_size_mb']:.2f} MB")

# Run cleanup
result = cleanup_old_data(days_smart=30, days_analyzed=7)
print(f"Deleted {result['files_deleted']} files")
print(f"Freed {result['mb_freed']:.2f} MB")
```

---

## 🔌 API Integrations

### **Required APIs**

#### 1. **Apify** (Primary Crawler)
- **Token**: `APIFY_API_TOKEN`
- **Use**: Facebook, Instagram, X, TikTok, YouTube, LinkedIn, Shopee, Lazada (8 platforms)
- **Cost**: Pay-per-result
- **Location**: `.env` file

#### 2. **SerpAPI** (Backup Crawler)
- **Key**: `SERPAPI_KEY`
- **Use**: Google News, Lowyat (2 platforms)
- **Cost**: $50/month (5,000 searches)
- **Location**: `.env` file

#### 3. **OpenAI** (LLM Analysis)
- **Key**: `OPENAI_API_KEY`
- **Use**: AI keyword generation, intelligent insights
- **Models**: GPT-4o, GPT-4o-mini
- **Location**: `.env` file

#### 4. **Anthropic** (LLM Analysis)
- **Key**: `ANTHROPIC_API_KEY`
- **Use**: Alternative LLM for analysis
- **Models**: Claude-3.5-Sonnet, Claude-3-Haiku
- **Location**: `.env` file

#### 5. **HuggingFace** (AI Models)
- **Token**: `HUGGINGFACE_API_TOKEN`
- **Use**: Access custom models (rmtariq/*)
- **Models**: Malay sentiment, emotion classifier
- **Location**: `.env` file

### **Optional APIs**

Located in `.env` file (empty by default):
- Facebook Graph API
- Instagram Basic Display API
- Twitter/X API v2
- TikTok API
- YouTube Data API v3
- LinkedIn API

### **API Configuration**

**File**: `.env`

**Structure**:
```bash
# AI/LLM APIs (Required)
OPENAI_API_KEY=sk-proj-...
ANTHROPIC_API_KEY=sk-ant-api03-...
HUGGINGFACE_API_TOKEN=hf_...

# Crawler APIs (Required)
APIFY_API_TOKEN=apify_api_...
SERPAPI_KEY=...

# Database
DATABASE_URL=sqlite:///./insightpulse.db

# Server
HOST=0.0.0.0
PORT=8001
ENVIRONMENT=development
```

---

## 📊 Analysis Types

### **1. Social Listening**
- **Purpose**: Monitor brand mentions, sentiment, and engagement
- **Best For**: Brand management, reputation monitoring
- **Focus**: Posts with high engagement, brand mentions
- **Output**: Sentiment trends, top posts, engagement metrics

### **2. Crisis Detection**
- **Purpose**: Identify sudden spikes in negative sentiment
- **Best For**: Crisis management teams
- **Focus**: Negative posts, high-engagement complaints
- **Output**: Crisis alerts, negative sentiment timeline

### **3. Trend Analysis**
- **Purpose**: Track trending topics and emerging patterns
- **Best For**: Market research, content strategy
- **Focus**: Viral posts, trending hashtags, topic clusters
- **Output**: Trending topics, hashtag analysis, topic evolution

### **4. Competitive Analysis**
- **Purpose**: Compare multiple brands or topics
- **Best For**: Strategy teams, market intelligence
- **Focus**: Cross-brand comparison, market share
- **Output**: Comparative sentiment, share of voice

### **5. Campaign Performance**
- **Purpose**: Measure marketing campaign effectiveness
- **Best For**: Marketing teams, agencies
- **Focus**: Campaign-related posts, hashtag performance
- **Output**: Campaign reach, engagement rate, ROI indicators

### **6. Product Feedback**
- **Purpose**: Analyze customer reviews and feedback
- **Best For**: Product managers, QA teams
- **Focus**: Product mentions, feature requests, complaints
- **Output**: Feature sentiment, bug reports, improvement suggestions

### **7. Customer Service**
- **Purpose**: Monitor and respond to customer issues
- **Best For**: Support teams, CX managers
- **Focus**: Customer complaints, support requests
- **Output**: Issue categories, response time needs, satisfaction

---

## ✨ Features

### **Core Features**

1. **Multi-Platform Crawling**
   - 10 platforms supported
   - Parallel execution for speed
   - AI-powered keyword generation
   - Smart comment sampling

2. **Multilingual Sentiment Analysis**
   - Malay (85% accuracy)
   - English (Twitter-optimized)
   - Chinese (News-optimized)
   - Multilingual (Fallback)

3. **Emotion Classification**
   - 8 emotions detected
   - Multilingual support
   - Confidence scores

4. **Real-Time Analysis**
   - Live data collection
   - WebSocket updates
   - Progress tracking

5. **Professional Reports**
   - Excel with multiple sheets
   - PDF formatted reports
   - HTML interactive reports
   - Auto-generated insights

6. **Malaysian Context**
   - Malay language support
   - Demographic detection
   - Local platform support (Lowyat, Shopee, Lazada)
   - Malaysian time zone

### **Advanced Features**

7. **AI-Powered Insights**
   - LLM-based analysis (GPT-4o, Claude)
   - Intelligent keyword generation
   - Context-aware recommendations

8. **Smart Data Management**
   - Automatic cleanup (30-day retention)
   - Combined data storage
   - Efficient CSV format
   - Deduplication

9. **Engagement Scoring**
   - Platform-specific calculations
   - Weighted metrics
   - Trending score algorithm

10. **Trend Detection**
    - Time-series analysis
    - Topic clustering
    - Hashtag tracking
    - Viral content identification

---

## 📁 File Structure

```
InsightPulse/
│
├── 📂 backend/                          # Backend services
│   ├── 📂 data_crawlers/
│   │   ├── simple_apify_adapter.py      # Main crawler adapter (1330 lines)
│   │   ├── crawl_strategy.py            # 30:70 strategy
│   │   ├── 📂 platform_crawlers/        # Individual platform crawlers
│   │   │   ├── facebook_crawler.py
│   │   │   ├── instagram_crawler.py
│   │   │   ├── twitter_crawler.py
│   │   │   ├── tiktok_crawler.py
│   │   │   ├── youtube_crawler.py
│   │   │   ├── linkedin_crawler.py
│   │   │   ├── news_crawler.py
│   │   │   ├── lowyat_crawler.py
│   │   │   ├── shopee_crawler.py
│   │   │   └── lazada_crawler.py
│   │   └── settings.py                  # Actor configurations
│   │
│   ├── 📂 services/
│   │   ├── ai_keyword_generator.py      # AI keyword generation
│   │   ├── batch_sentiment_processor.py # Batch processing
│   │   ├── report_generator.py          # Report creation
│   │   └── report_templates.py          # Report templates
│   │
│   ├── 📂 utils/
│   │   └── data_cleanup.py              # Storage cleanup utility
│   │
│   └── 📂 database/
│       ├── models.py                    # Database models
│       └── repository.py                # Data access layer
│
├── 📂 web_backend/                      # FastAPI backend
│   ├── simple_app.py                    # Main backend (2772 lines)
│   ├── config.py                        # Configuration
│   ├── llm_service.py                   # LLM integration
│   └── advanced_nlp_processor.py        # NLP processing
│
├── 📂 web_frontend/                     # Frontend interface
│   ├── simple_index.html               # Main UI
│   ├── 📂 assets/                       # CSS, JS, images
│   └── test_simple.html                # Test interface
│
├── 📂 data/                             # Data storage
│   ├── 📂 smart_crawlers/               # Raw crawled data (30 days)
│   │   ├── facebook/
│   │   ├── instagram/
│   │   ├── x/
│   │   ├── tiktok/
│   │   ├── youtube/
│   │   ├── linkedin/
│   │   ├── news/
│   │   ├── lowyat/
│   │   ├── shopee/
│   │   └── lazada/
│   ├── 📂 analyzed/                     # Analyzed data (7 days)
│   ├── 📂 combined/                     # Combined data (manual) ⭐ NEW!
│   └── 📂 reports/                      # Generated reports
│
├── 📂 NEImpulse/                        # Virtual environment
│
├── 📄 .env                              # API keys & configuration
├── 📄 requirements.txt                  # Python dependencies
├── 📄 start_app.sh                      # Startup script
│
├── 📄 INSIGHTPULSE_COMPLETE_DOCUMENTATION.md  # This file ⭐
├── 📄 DATA_STORAGE_STRUCTURE.md         # Storage details
├── 📄 CSV_STORAGE_SUMMARY.md            # CSV formats
├── 📄 HOW_TO_START.md                   # Startup guide
├── 📄 START_HERE.txt                    # Quick start
│
└── 📄 README.md                         # Project overview
```

---

## 🚀 How to Start

### **Quick Start**

#### **Option 1: Using Startup Script**

```bash
cd /Users/rmtariq/Documents/InsightPulse
./start_app.sh
```

Wait for "Uvicorn running on http://0.0.0.0:8001", then open http://localhost:8001

#### **Option 2: Manual Commands**

```bash
# Step 1: Navigate to project
cd /Users/rmtariq/Documents/InsightPulse

# Step 2: Activate virtual environment
source NEImpulse/bin/activate

# Step 3: Start backend
python web_backend/simple_app.py
```

Wait for startup message, then open http://localhost:8001

### **First-Time Setup**

1. **Install Dependencies**
```bash
pip install -r requirements.txt
```

2. **Configure API Keys**
Edit `.env` file and add:
- APIFY_API_TOKEN
- SERPAPI_KEY
- OPENAI_API_KEY (or ANTHROPIC_API_KEY)
- HUGGINGFACE_API_TOKEN

3. **Test Installation**
```bash
python test_ai_models.py
```

### **Expected Startup Time**

- **First time**: 1-2 minutes (downloading AI models)
- **Subsequent runs**: 30-60 seconds (loading from cache)

---

## ⚙️ Configuration

### **Environment Variables** (`.env`)

#### **Required**
```bash
APIFY_API_TOKEN=apify_api_...           # Apify crawler
SERPAPI_KEY=...                          # SerpAPI for News/Lowyat
OPENAI_API_KEY=sk-proj-...              # OpenAI GPT models
HUGGINGFACE_API_TOKEN=hf_...            # HuggingFace models
```

#### **Optional**
```bash
ANTHROPIC_API_KEY=sk-ant-api03-...      # Claude models (alternative to OpenAI)
DATABASE_URL=sqlite:///./insightpulse.db # Database connection
HOST=0.0.0.0                             # Server host
PORT=8001                                # Server port
ENVIRONMENT=development                  # Environment (development/production)
DEBUG=true                               # Debug mode
```

#### **Malaysian Settings**
```bash
TIMEZONE=Asia/Kuala_Lumpur               # Time zone
DEFAULT_LANGUAGE=bahasa_malaysia         # Default language
DEFAULT_CURRENCY=MYR                     # Currency
```

### **Model Configuration**

**Sentiment Models** (in `web_backend/simple_app.py`):
```python
SENTIMENT_MODELS = {
    'malay': 'rmtariq/ft-Malay-bert',
    'english': 'cardiffnlp/twitter-roberta-base-sentiment-latest',
    'chinese': 'uer/roberta-base-finetuned-chinanews-chinese',
    'multilingual': 'nlptown/bert-base-multilingual-uncased-sentiment',
}

EMOTION_MODEL = "rmtariq/multilingual-emotion-classifier"
```

### **Storage Configuration**

**Retention Periods** (in `backend/utils/data_cleanup.py`):
```python
RETENTION_DAYS = {
    'smart_crawlers': 30,  # Raw data - 30 days
    'analyzed': 7,          # Analyzed data - 7 days
    'combined': None        # Manual cleanup
}
```

---

## 📦 Dependencies

### **Core Dependencies** (from `requirements.txt`)

#### **Web Framework**
- `fastapi==0.104.1` - REST API framework
- `uvicorn==0.24.0` - ASGI server
- `websockets==12.0` - Real-time communication

#### **Data Processing**
- `pandas==2.1.3` - Data manipulation
- `numpy==1.26.2` - Numerical computing

#### **AI/ML**
- `transformers==4.36.0` - HuggingFace models
- `torch==2.1.1` - PyTorch (deep learning)
- `sentence-transformers==2.2.2` - Text embeddings
- `spacy==3.7.2` - NLP processing
- `nltk==3.8.1` - Natural language toolkit

#### **Crawlers**
- `apify-client==1.6.3` - Apify API client
- `serpapi==0.1.5` - SerpAPI client

#### **LLM Services**
- `openai==1.3.7` - OpenAI GPT API
- `anthropic==0.7.0` - Anthropic Claude API

#### **Utilities**
- `python-dotenv==1.0.0` - Environment variables
- `requests==2.31.0` - HTTP requests
- `pydantic==2.5.0` - Data validation
- `sqlalchemy==2.0.23` - Database ORM

### **Installation**

```bash
# Install all dependencies
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_sm

# Download NLTK data
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"
```

### **System Requirements**

- **Python**: 3.9+ (tested on 3.13.5)
- **RAM**: 8GB minimum, 16GB recommended (AI models are large)
- **Disk**: 10GB free space (for models and data)
- **OS**: macOS, Linux, Windows (WSL)

---

## 📚 Additional Documentation

### **Related Files**

| File | Purpose |
|------|---------|
| `DATA_STORAGE_STRUCTURE.md` | Complete technical details on storage |
| `CSV_STORAGE_SUMMARY.md` | User-friendly CSV format guide |
| `HOW_TO_START.md` | Detailed startup instructions |
| `START_HERE.txt` | Quick start guide |
| `CRAWLING_STRATEGY.md` | 30:70 posts:comments strategy |
| `PROFESSIONAL_REPORTS_GUIDE.md` | Report generation guide |

### **For Developers**

- `backend/data_crawlers/settings.py` - Apify actor configurations
- `web_backend/config.py` - Application configuration
- `backend/services/` - Reusable services
- `backend/utils/` - Utility functions

### **For Users**

- `START_HERE.txt` - Fastest way to get started
- `HOW_TO_START.md` - Step-by-step guide
- `CSV_STORAGE_SUMMARY.md` - Understanding the data

---

## 🎯 Summary

**InsightPulse** is a comprehensive social media analytics platform that:

✅ Crawls **10 platforms** simultaneously
✅ Analyzes sentiment in **4 languages** (Malay, English, Chinese, Multilingual)
✅ Detects **8 emotions** (anger, disgust, fear, joy, neutral, sadness, love, surprise)
✅ Generates **professional reports** (Excel, PDF, HTML)
✅ Provides **real-time insights** with AI-powered analysis
✅ Optimized for **Malaysian market** (language, platforms, demographics)

**Perfect for**: Brand monitoring, crisis detection, market research, competitive analysis, customer feedback analysis

**Tech Stack**: FastAPI + HuggingFace + Apify + OpenAI + spaCy + Pandas

**Storage**: 3 locations - Raw data (30 days), Analyzed data (7 days), Combined data (manual)

**Models**: 5 AI models (4 sentiment + 1 emotion) + LLM integration (GPT-4o/Claude)

---

**Last Updated**: 2026-02-15
**Version**: 2.0 - Combined Data Support
**All 10 Platforms**: ✅ Facebook, Instagram, X, TikTok, YouTube, LinkedIn, Google News, Lowyat, Shopee, Lazada

---

**For Questions or Support**: Refer to documentation files in project root directory.

