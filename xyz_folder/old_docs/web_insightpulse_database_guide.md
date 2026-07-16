# 🗄️ InsightPulse Database Architecture Guide

## 🎯 RECOMMENDED FREE DATABASE SETUP

### **Option 1: PostgreSQL (RECOMMENDED) - 100% FREE**

#### **Why PostgreSQL:**
- ✅ **Powerful & Reliable** - Enterprise-grade database
- ✅ **JSON Support** - Perfect for social media data
- ✅ **Full-text Search** - Built-in search capabilities
- ✅ **Scalable** - Handles millions of records
- ✅ **FREE Hosting** - Railway, Render, Supabase

#### **FREE PostgreSQL Hosting Options:**

1. **Railway.app** (BEST CHOICE)
   - **FREE Tier**: 512MB RAM, 1GB Storage
   - **Upgrade**: $5/month for 8GB storage
   - **Features**: Automatic backups, SSL, monitoring
   - **Perfect for**: Production InsightPulse deployment

2. **Supabase** (EXCELLENT ALTERNATIVE)
   - **FREE Tier**: 500MB database, 2GB bandwidth
   - **Features**: Real-time subscriptions, built-in auth
   - **Perfect for**: Real-time dashboard updates

3. **Render.com**
   - **FREE Tier**: 1GB storage, 90 days retention
   - **Features**: Automatic SSL, backups
   - **Perfect for**: Development and testing

#### **Database Schema for InsightPulse:**

```sql
-- Users and Authentication
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Analysis Projects
CREATE TABLE projects (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    name VARCHAR(200) NOT NULL,
    description TEXT,
    platforms TEXT[], -- Array of platforms
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Social Media Data
CREATE TABLE social_media_data (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id),
    platform VARCHAR(50) NOT NULL,
    post_id VARCHAR(200),
    content TEXT,
    author VARCHAR(100),
    engagement_metrics JSONB, -- likes, shares, comments
    sentiment_score FLOAT,
    sentiment_label VARCHAR(20),
    created_at TIMESTAMP,
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- E-commerce Data
CREATE TABLE ecommerce_data (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id),
    platform VARCHAR(50) NOT NULL, -- shopee, lazada
    product_id VARCHAR(200),
    product_name TEXT,
    price DECIMAL(10,2),
    rating FLOAT,
    reviews_count INTEGER,
    seller_info JSONB,
    product_details JSONB,
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Analysis Results
CREATE TABLE analysis_results (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id),
    analysis_type VARCHAR(50), -- social_listening, sme_insights, etc.
    results JSONB, -- Store complex analysis results
    confidence_score FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX idx_social_platform ON social_media_data(platform);
CREATE INDEX idx_social_sentiment ON social_media_data(sentiment_label);
CREATE INDEX idx_social_created ON social_media_data(created_at);
CREATE INDEX idx_ecommerce_platform ON ecommerce_data(platform);
CREATE INDEX idx_ecommerce_price ON ecommerce_data(price);
```

### **Option 2: MongoDB Atlas (For Document Storage) - FREE**

#### **Why MongoDB:**
- ✅ **Flexible Schema** - Perfect for varied social media data
- ✅ **JSON Native** - Natural fit for API responses
- ✅ **Powerful Queries** - Advanced aggregation pipeline
- ✅ **FREE Tier** - 512MB storage, shared cluster

#### **FREE MongoDB Atlas Setup:**
1. **Sign up**: mongodb.com/atlas
2. **FREE Tier**: M0 Sandbox (512MB, shared)
3. **Features**: Built-in security, monitoring, backups
4. **Perfect for**: Storing raw crawler data

#### **MongoDB Collections Structure:**

```javascript
// users collection
{
  "_id": ObjectId,
  "username": "string",
  "email": "string", 
  "password_hash": "string",
  "role": "user|admin",
  "created_at": ISODate
}

// projects collection
{
  "_id": ObjectId,
  "user_id": ObjectId,
  "name": "string",
  "description": "string",
  "platforms": ["facebook", "shopee", "lazada"],
  "settings": {
    "max_results": 1000,
    "include_sentiment": true,
    "real_time": true
  },
  "created_at": ISODate
}

// social_data collection
{
  "_id": ObjectId,
  "project_id": ObjectId,
  "platform": "facebook|instagram|twitter|etc",
  "raw_data": {
    "post_id": "string",
    "content": "string",
    "author": "string",
    "metrics": {
      "likes": 100,
      "shares": 50,
      "comments": 25
    }
  },
  "analysis": {
    "sentiment": {
      "score": 0.75,
      "label": "positive"
    },
    "categories": ["technology", "review"],
    "priority": "medium"
  },
  "collected_at": ISODate
}

// ecommerce_data collection
{
  "_id": ObjectId,
  "project_id": ObjectId,
  "platform": "shopee|lazada",
  "product": {
    "id": "string",
    "name": "string",
    "price": 299.90,
    "currency": "MYR",
    "rating": 4.5,
    "reviews_count": 1250,
    "seller": {
      "name": "Official Store",
      "rating": 4.8
    }
  },
  "reviews": [
    {
      "content": "Great product!",
      "rating": 5,
      "sentiment": "positive"
    }
  ],
  "collected_at": ISODate
}
```

### **Option 3: Hybrid Approach (RECOMMENDED FOR PRODUCTION)**

#### **Best of Both Worlds:**
- **PostgreSQL** - Structured data (users, projects, analysis results)
- **MongoDB** - Raw crawler data (flexible, large volumes)
- **Redis** - Caching and real-time features

#### **Cost Breakdown:**
- **PostgreSQL (Railway)**: FREE (1GB) → $5/month (8GB)
- **MongoDB Atlas**: FREE (512MB) → $9/month (2GB)
- **Redis (Upstash)**: FREE (10K requests/day) → $0.20/100K requests
- **Total**: FREE to start, ~$15/month for production

### **🚀 DEPLOYMENT STRATEGY**

#### **Phase 1: FREE Development Setup**
1. **Frontend**: Netlify/Vercel (FREE)
2. **Backend**: Railway/Render (FREE tier)
3. **Database**: PostgreSQL on Railway (FREE 1GB)
4. **Total Cost**: RM 0/month

#### **Phase 2: Production Scaling**
1. **Frontend**: Netlify Pro ($19/month) or keep FREE
2. **Backend**: Railway Pro ($5/month)
3. **Database**: Railway PostgreSQL ($5/month for 8GB)
4. **MongoDB**: Atlas M10 ($9/month for 2GB)
5. **Total Cost**: RM 80-120/month (~$20-25/month)

### **📊 DATA STORAGE ESTIMATES**

#### **For 9-Platform System:**
- **Social Media Data**: ~100MB/month per platform = 700MB/month
- **E-commerce Data**: ~200MB/month per platform = 400MB/month
- **Analysis Results**: ~50MB/month
- **Total**: ~1.15GB/month

#### **FREE Tier Capacity:**
- **PostgreSQL (Railway)**: 1GB = ~1 month of data
- **MongoDB Atlas**: 512MB = ~2 weeks of raw data
- **Recommendation**: Start FREE, upgrade when needed

### **🔧 IMPLEMENTATION PRIORITY**

#### **Week 1: Basic Setup**
1. Set up PostgreSQL on Railway (FREE)
2. Create basic database schema
3. Implement user authentication
4. Basic CRUD operations

#### **Week 2: Data Integration**
1. Connect 9-platform crawlers to database
2. Implement data storage and retrieval
3. Basic analytics queries
4. Simple web interface

#### **Week 3: Advanced Features**
1. Add MongoDB for raw data storage
2. Implement real-time updates
3. Advanced analytics and reporting
4. Professional web interface

#### **Week 4: Production Ready**
1. Performance optimization
2. Security hardening
3. Backup and monitoring
4. Deployment to production

### **💡 PRO TIPS**

#### **Database Optimization:**
1. **Use Indexes** - Speed up queries
2. **Partition Large Tables** - Better performance
3. **Regular Cleanup** - Remove old data
4. **Connection Pooling** - Efficient resource usage

#### **Cost Management:**
1. **Start with FREE tiers** - Validate the system
2. **Monitor Usage** - Track data growth
3. **Optimize Queries** - Reduce database load
4. **Archive Old Data** - Keep costs low

#### **Scaling Strategy:**
1. **Horizontal Scaling** - Multiple database instances
2. **Read Replicas** - Separate read/write operations
3. **Caching Layer** - Redis for frequently accessed data
4. **CDN** - Fast global content delivery

---

**This database architecture will support your RM 4-5M InsightPulse system while keeping initial costs at ZERO!** 🚀
