# 🚀 Advanced Crawler Configuration Features

## 📋 Overview
InsightPulse now supports advanced, granular crawler configuration for each platform with specific data collection parameters.

## 🎯 Platform-Specific Configuration

### 📘 Facebook Configuration
- **Max Posts**: 10-10,000 posts (default: 1,000)
- **Max Comments per Post**: 0-1,000 comments (default: 100)
- **Target Pages**: Optional specific pages to crawl
- **Target Groups**: Optional specific groups to crawl

### 🎵 TikTok Configuration
- **Max Videos**: 10-5,000 videos (default: 500)
- **Max Comments per Video**: 0-500 comments (default: 50)
- **Target Hashtags**: Optional specific hashtags to focus on
- **Target Users**: Optional specific users to monitor

### 📷 Instagram Configuration
- **Max Posts**: 10-5,000 posts (default: 800)
- **Max Comments per Post**: 0-500 comments (default: 80)
- **Target Hashtags**: Optional hashtags to track
- **Include Stories**: Option to include story content

### 🐦 Twitter/X Configuration
- **Max Tweets**: 10-10,000 tweets (default: 1,500)
- **Max Replies per Tweet**: 0-200 replies (default: 50)
- **Target Hashtags**: Optional hashtags to monitor
- **Target Users**: Optional users to track

### 🔍 Google Search Configuration
- **Max Search Results**: 10-1,000 results (default: 200)
- **Search Depth**: Surface/Deep/Comprehensive
- **Target Regions**: Malaysia, Singapore, Indonesia, Global
- **Language**: Auto/Malay/English/Chinese

### 📰 Google News Configuration
- **Max Articles**: 10-1,000 articles (default: 300)
- **Days Back**: 1-30 days (default: 7)
- **Preferred Sources**: Optional news sources (malaysiakini, thestar, nst)
- **Language**: Auto/Malay/English

### 💻 Lowyat Forum Configuration
- **Max Threads**: 5-500 threads (default: 100)
- **Max Posts per Thread**: 5-200 posts (default: 50)
- **Target Forums**: Tech Talk, Kopitiam, Cars, Property, All
- **Days Back**: 1-30 days (default: 14)

## 💾 Data Storage Location
All crawler data is guaranteed to be saved at:
```
/Users/rmtariq/InsightPulse/data/smart_crawlers/
├── facebook/
├── tiktok/
├── instagram/
├── twitter/
├── google/
├── news/
└── lowyat/
```

## 🔧 Technical Implementation

### API Endpoints
- **Standard Crawling**: `/crawl/smart` (existing)
- **Advanced Crawling**: `/crawl/advanced` (new)

### Configuration Flow
1. User selects platforms and configures parameters
2. Frontend validates configuration
3. Backend receives detailed platform config
4. Smart crawlers execute with specific parameters
5. Data saved to designated location with proper structure

### Enhanced Features
- ✅ **Granular Control**: Specific limits for posts, comments, videos
- ✅ **Platform Optimization**: Tailored settings for each platform
- ✅ **Data Integrity**: Guaranteed save location
- ✅ **Real-time Feedback**: Configuration summary before execution
- ✅ **Flexible Targeting**: Optional hashtags, users, sources
- ✅ **Scalable Limits**: From small tests to comprehensive analysis

## 🎯 Usage Examples

### Quick Test Configuration
- Facebook: 100 posts, 20 comments each
- Google: 50 results
- News: 30 articles, 3 days back

### Comprehensive Analysis
- Facebook: 5,000 posts, 200 comments each
- TikTok: 2,000 videos, 100 comments each
- Instagram: 3,000 posts, 150 comments each
- Twitter: 8,000 tweets, 100 replies each
- Google: 500 results, comprehensive depth
- News: 800 articles, 14 days back
- Lowyat: 300 threads, 100 posts each

### Targeted Investigation
- Focus on specific hashtags: #SST, #cukai, #MADANI
- Monitor specific users: @official_accounts
- Target specific news sources: malaysiakini, thestar
- Focus on specific forums: Tech Talk, Kopitiam

## 🚀 Benefits
1. **Precision**: Get exactly the data you need
2. **Efficiency**: Avoid over-collection or under-collection
3. **Cost Control**: Manage API usage and processing time
4. **Quality**: Focus on relevant sources and content
5. **Scalability**: From small tests to large-scale analysis
6. **Authenticity**: All data from real smart crawler system
