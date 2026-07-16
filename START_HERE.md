# 🚀 InsightPulse - START HERE

Welcome to InsightPulse! This guide will help you get started.

---

## ⚡ QUICK START (Most Common)

### To Start InsightPulse FULL APP with Crawling:

```bash
cd ~/Documents/InsightPulse
./start_full_app.sh
```

**Wait 10-15 seconds** for the app to load, then your browser will open automatically.

---

## 📱 What is InsightPulse?

InsightPulse is a **Digital Intelligence Platform** that helps you:

✅ **Monitor social media** (Facebook, Instagram, TikTok, X/Twitter)  
✅ **Crawl news articles** and e-commerce reviews  
✅ **Analyze sentiment & emotions** using AI  
✅ **Get strategic insights** in Bahasa Malaysia  
✅ **Track brand mentions** and customer feedback  

---

## 🎯 Two Ways to Use InsightPulse

### 1. 🌐 Full App (Crawling + Analysis)
**Script:** `./start_full_app.sh`

**Use for:**
- Crawling NEW data from social media
- Monitoring keywords in real-time
- Collecting fresh data from multiple platforms

**Opens:** http://localhost:8001/

---

### 2. 📊 CSV Analyzer (Existing Data Only)
**Script:** `./start_insightpulse.sh`

**Use for:**
- Analyzing existing CSV files
- Quick analysis without crawling
- Uploading your own data

**Opens:** http://localhost:8001/static/analyze_csv.html

---

## 📋 Step-by-Step Guide

### For Keyword Crawling:

1. **Start the app:**
   ```bash
   ./start_full_app.sh
   ```

2. **Enter keywords** (e.g., "Mara Liner", "budi95")

3. **Select platforms** you want to crawl

4. **Click "Start Analysis"**

5. **Wait for results** (may take 2-5 minutes)

6. **View dashboard** with:
   - Platform breakdown (TikTok, Instagram, FB, X)
   - Sentiment analysis
   - Emotion analysis
   - AI strategic insights in Bahasa Malaysia
   - Hala Tuju (strategic direction)

---

### For CSV Analysis:

1. **Start the app:**
   ```bash
   ./start_insightpulse.sh
   ```

2. **Select existing CSV** OR **upload your own**

3. **Enter brand/topic name** (e.g., "Mara Liner")

4. **Set time filter** (e.g., 90 days)

5. **Click "Analyze CSV"**

6. **View dashboard** with same insights as above

---

## 🛑 To Stop the App

```bash
./stop_insightpulse.sh
```

---

## 🔧 Troubleshooting

### App doesn't start?
```bash
# Check if port is in use
lsof -ti:8001 | xargs kill -9

# Try starting again
./start_full_app.sh
```

### Browser doesn't open?
Manually open: http://localhost:8001/

### See errors?
Check logs:
```bash
tail -50 backend.log
```

---

## 📚 Documentation

- **Full Guide:** [HOW_TO_START_INSIGHTPULSE.md](HOW_TO_START_INSIGHTPULSE.md)
- **Which Script:** [WHICH_SCRIPT_TO_USE.md](WHICH_SCRIPT_TO_USE.md)
- **CSV Analysis:** [ANALYZE_EXISTING_CSV_GUIDE.md](ANALYZE_EXISTING_CSV_GUIDE.md)

---

## ✅ What You Get

### Dashboard Features:
- 📊 **Platform Breakdown** (with TikTok as main platform for Malaysia)
- 😊 **Sentiment Analysis** (Positive/Negative/Neutral)
- 💭 **Emotion Analysis** (Happy, Angry, Sad, Love, Fear, Surprise)
- 🎯 **Business Priorities** (Critical issues, opportunities)
- 🤖 **AI Strategic Insights** (Bahasa Malaysia)
- ⏭️ **Hala Tuju** (Next steps with priorities)

### AI Features:
- Uses GPT-4 for strategic insights
- Knows Malaysian social media landscape (TikTok-first strategy)
- Provides actionable recommendations in Bahasa Malaysia

---

## 🎯 Common Use Cases

| Task | Script | URL |
|------|--------|-----|
| Monitor "Mara Liner" on social media | `./start_full_app.sh` | http://localhost:8001/ |
| Analyze existing Mara Liner CSV | `./start_insightpulse.sh` | http://localhost:8001/static/analyze_csv.html |
| Track brand sentiment | `./start_full_app.sh` | http://localhost:8001/ |
| Quick report from CSV | `./start_insightpulse.sh` | http://localhost:8001/static/analyze_csv.html |

---

## 🚀 Ready to Start?

```bash
cd ~/Documents/InsightPulse
./start_full_app.sh
```

**Enjoy using InsightPulse! 🇲🇾**
