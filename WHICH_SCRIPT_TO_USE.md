# 🚀 Which Script Should I Use?

## Quick Guide

InsightPulse has **TWO different apps** for different use cases:

---

## 🎯 Option 1: FULL APP (Crawling + Analysis)
**Script:** `./start_full_app.sh`

### Use this when you want to:
✅ **Crawl NEW data** from social media using keywords  
✅ Monitor **Facebook, Instagram, TikTok, X (Twitter)**  
✅ Crawl **News articles, E-commerce reviews**  
✅ Real-time data collection + analysis  

### What it does:
1. Enter keywords (e.g., "Mara Liner", "budi95")
2. Select platforms to crawl
3. System crawls social media in real-time
4. Analyzes data with AI
5. Shows dashboard with insights

### To start:
```bash
cd ~/Documents/InsightPulse
./start_full_app.sh
```

**Opens:** http://localhost:8001/ (Main crawling interface)

---

## 📊 Option 2: CSV ANALYZER (Analyze Existing Data)
**Script:** `./start_insightpulse.sh`

### Use this when you want to:
✅ **Analyze existing CSV files** (no crawling)  
✅ Quick analysis of previously collected data  
✅ Upload your own CSV files  
✅ Get AI insights from existing data  

### What it does:
1. Select from 48+ existing CSV files
2. OR upload your own CSV
3. System cleans and analyzes data
4. Shows dashboard with insights (same as full app)

### To start:
```bash
cd ~/Documents/InsightPulse
./start_insightpulse.sh
```

**Opens:** http://localhost:8001/static/analyze_csv.html (CSV analyzer only)

---

## 🤔 Which One Should I Use?

| Task | Script to Use |
|------|---------------|
| **Crawl NEW keywords from social media** | `./start_full_app.sh` |
| **Monitor brand mentions in real-time** | `./start_full_app.sh` |
| **Collect fresh data** | `./start_full_app.sh` |
| **Analyze existing CSV files** | `./start_insightpulse.sh` |
| **Quick analysis without crawling** | `./start_insightpulse.sh` |
| **Upload and analyze your own data** | `./start_insightpulse.sh` |

---

## 💡 Recommendation

**For first-time use or keyword monitoring:**
```bash
./start_full_app.sh
```

This gives you the COMPLETE InsightPulse experience with:
- Keyword crawling
- Platform selection
- Real-time data collection
- AI-powered analysis
- Full dashboard

**Note:** Both apps provide the **SAME analysis dashboard** - the difference is how you get the data (crawl vs. upload).

---

## 🛑 To Stop Either App

```bash
./stop_insightpulse.sh
```

This stops BOTH the full app and the CSV analyzer (same server).

---

## 📋 Summary

- **`start_full_app.sh`** → Complete app with crawling + analysis
- **`start_insightpulse.sh`** → CSV analysis only (no crawling)
- **`stop_insightpulse.sh`** → Stop any running app

---

**Choose based on your needs! Both are powerful.** 🚀
