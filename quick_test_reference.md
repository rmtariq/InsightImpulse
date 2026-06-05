# 🎯 QUICK TEST REFERENCE TABLE

## 📊 **READY-TO-USE TEST INPUTS**

| **Input Query** | **Analysis Type** | **Best Crawlers** | **Expected Results** |
|---|---|---|---|
| `tudung paling viral 2025` | `social_listening` | `facebook, instagram, tiktok` | Fashion trends, viral styles, influencer posts |
| `makanan halal sedap di Kuala Lumpur` | `social_listening` | `facebook, instagram, google` | Restaurant reviews, food photos, recommendations |
| `PKS Malaysia online business` | `sme_insights` | `facebook, news, google` | Business opportunities, success stories, tips |
| `smartphone battery problem Malaysia` | `issue_detection` | `facebook, x, lowyat` | Complaints, technical issues, problem reports |
| `iPhone vs Samsung Malaysia 2025` | `competitor_analysis` | `lowyat, facebook, shopee` | Feature comparisons, price analysis, preferences |
| `best budget smartphone Malaysia 2025` | `product_intelligence` | `lowyat, shopee, lazada` | Product specs, reviews, price comparisons |
| `Malaysia e-commerce market trends 2025` | `market_research` | `news, google, facebook` | Market analysis, growth trends, industry insights |
| `Grab Malaysia brand reputation` | `brand_monitoring` | `facebook, x, news` | Brand sentiment, customer feedback, reputation |

## 🚀 **COPY-PASTE API COMMANDS**

### **Fashion Social Listening**
```bash
curl -X POST "http://localhost:8001/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "tudung paling viral 2025",
    "analysis_type": "social_listening",
    "platforms": ["facebook", "instagram", "tiktok"],
    "max_results_per_platform": 25
  }'
```

### **Food Social Listening**
```bash
curl -X POST "http://localhost:8001/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "makanan halal sedap di Kuala Lumpur",
    "analysis_type": "social_listening",
    "platforms": ["facebook", "instagram", "google"],
    "max_results_per_platform": 25
  }'
```

### **Business SME Insights**
```bash
curl -X POST "http://localhost:8001/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "PKS Malaysia online business",
    "analysis_type": "sme_insights",
    "platforms": ["facebook", "news", "google"],
    "max_results_per_platform": 30
  }'
```

### **Tech Issue Detection**
```bash
curl -X POST "http://localhost:8001/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "smartphone battery problem Malaysia",
    "analysis_type": "issue_detection",
    "platforms": ["facebook", "x", "lowyat"],
    "max_results_per_platform": 25
  }'
```

### **Tech Competitor Analysis**
```bash
curl -X POST "http://localhost:8001/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "iPhone vs Samsung Malaysia 2025",
    "analysis_type": "competitor_analysis",
    "platforms": ["lowyat", "facebook", "shopee"],
    "max_results_per_platform": 30
  }'
```

### **Product Intelligence**
```bash
curl -X POST "http://localhost:8001/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "best budget smartphone Malaysia 2025",
    "analysis_type": "product_intelligence",
    "platforms": ["lowyat", "shopee", "lazada"],
    "max_results_per_platform": 30
  }'
```

### **Market Research**
```bash
curl -X POST "http://localhost:8001/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Malaysia e-commerce market trends 2025",
    "analysis_type": "market_research",
    "platforms": ["news", "google", "facebook"],
    "max_results_per_platform": 30
  }'
```

### **Brand Monitoring**
```bash
curl -X POST "http://localhost:8001/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Grab Malaysia brand reputation",
    "analysis_type": "brand_monitoring",
    "platforms": ["facebook", "x", "news"],
    "max_results_per_platform": 30
  }'
```

## 🎯 **DASHBOARD TESTING STEPS**

### **Step 1: Fashion Trend Analysis**
1. Open: `http://localhost:8001`
2. Analysis Type: `Social Listening`
3. Query: `tudung paling viral 2025`
4. Platforms: `Facebook, Instagram, TikTok`
5. Click: `Analyze`
6. Expected: Fashion content, viral trends, Malaysian brands

### **Step 2: Business Intelligence**
1. Analysis Type: `SME Insights`
2. Query: `PKS Malaysia online business`
3. Platforms: `Facebook, News, Google`
4. Expected: Business opportunities, success stories, tips

### **Step 3: Problem Detection**
1. Analysis Type: `Issue Detection`
2. Query: `smartphone battery problem Malaysia`
3. Platforms: `Facebook, X, Lowyat`
4. Expected: Complaints, technical issues, solutions

### **Step 4: Product Comparison**
1. Analysis Type: `Competitor Analysis`
2. Query: `iPhone vs Samsung Malaysia 2025`
3. Platforms: `Lowyat, Facebook, Shopee`
4. Expected: Feature comparisons, price analysis

### **Step 5: Product Research**
1. Analysis Type: `Product Intelligence`
2. Query: `best budget smartphone Malaysia 2025`
3. Platforms: `Lowyat, Shopee, Lazada`
4. Expected: Product specs, reviews, pricing

## 🔍 **CRAWLER SPECIALIZATIONS**

### **Visual Content** 📸
- **Instagram + TikTok**: Fashion, beauty, lifestyle trends
- **Best for**: `tudung viral`, `makeup trending`, `fashion muslimah`

### **Tech Discussions** 💻
- **Lowyat + Facebook**: Technology reviews, comparisons
- **Best for**: `smartphone comparison`, `laptop gaming`, `tech problems`

### **Shopping Intelligence** 🛒
- **Shopee + Lazada**: Product reviews, pricing, availability
- **Best for**: `product reviews`, `price comparison`, `shopping trends`

### **News & Research** 📰
- **News + Google**: Industry reports, market analysis
- **Best for**: `market trends`, `industry growth`, `business insights`

### **Social Complaints** 🗣️
- **Facebook + X**: Customer complaints, service issues
- **Best for**: `brand complaints`, `service problems`, `issue detection`

## ✅ **VALIDATION CHECKLIST**

For each test, verify:
- [ ] **Data Collection**: 20-40 data points per platform
- [ ] **Relevant Content**: Matches query and analysis type
- [ ] **Malaysian Context**: Local brands, locations, language
- [ ] **Platform Variety**: Different content styles per platform
- [ ] **AI Analysis**: LLM insights and recommendations
- [ ] **Response Time**: Under 30 seconds
- [ ] **Dashboard Display**: Professional visualizations

## 🎉 **SUCCESS INDICATORS**

### **Social Listening** ✅
- Sentiment analysis present
- Trending topics identified
- Social engagement metrics
- Viral content detection

### **SME Insights** ✅
- Business opportunities highlighted
- Market gap analysis
- Growth strategies suggested
- Success stories included

### **Issue Detection** ✅
- Problems clearly identified
- Complaint patterns analyzed
- Negative sentiment clustered
- Solution suggestions provided

### **Competitor Analysis** ✅
- Clear comparisons made
- Market positioning analyzed
- Feature differences highlighted
- Brand preferences shown

### **Product Intelligence** ✅
- Product features analyzed
- User satisfaction measured
- Performance metrics included
- Improvement suggestions made

### **Market Research** ✅
- Industry trends identified
- Market size analyzed
- Growth projections provided
- Consumer behavior insights

### **Brand Monitoring** ✅
- Brand mentions tracked
- Reputation score calculated
- Sentiment trends analyzed
- Crisis alerts if needed

**Use this quick reference for instant testing of your InsightPulse app!** 🚀
