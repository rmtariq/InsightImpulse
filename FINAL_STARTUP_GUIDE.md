# 🚀 InsightPulse - FINAL Startup Guide

## ✅ ONE COMMAND TO START EVERYTHING

```bash
cd ~/Documents/InsightPulse
./start_insightpulse.sh
```

**That's it!** This command starts the complete InsightPulse app.

---

## 🌐 What You Get

After running the script, two URLs will be available:

### 1. Main App (Keyword Crawling)
**URL:** http://localhost:8001/

**Features:**
- Enter keywords to crawl
- Select platforms (Facebook, Instagram, TikTok, X)
- Real-time data collection
- AI-powered analysis
- Full dashboard with insights

### 2. CSV Analyzer
**URL:** http://localhost:8001/static/analyze_csv.html

**Features:**
- Analyze existing CSV files
- Upload your own CSV
- Same dashboard as main app
- No crawling required

---

## 📋 Quick Start Steps

1. **Open Terminal**
   ```bash
   cd ~/Documents/InsightPulse
   ```

2. **Start InsightPulse**
   ```bash
   ./start_insightpulse.sh
   ```

3. **Wait 5-10 seconds** for server to start

4. **Browser opens automatically** to the dashboard

5. **Use the app!**

---

## 🎯 How to Use

### For Keyword Crawling:
1. Go to: http://localhost:8001/
2. Enter keywords (e.g., "Mara Liner")
3. Select platforms
4. Click "Start Analysis"
5. View results with:
   - Platform breakdown (TikTok, Instagram, FB, X)
   - Sentiment & emotion analysis
   - AI strategic insights in Bahasa Malaysia
   - Hala Tuju (strategic direction)

### For CSV Analysis:
1. Go to: http://localhost:8001/static/analyze_csv.html
2. Select CSV file or upload
3. Enter topic name
4. Click "Analyze CSV"
5. View same dashboard as above

---

## 🛑 How to Stop

```bash
cd ~/Documents/InsightPulse
./stop_insightpulse.sh
```

---

## 🔧 Troubleshooting

### Problem: "This site can't be reached"

**Solution 1:** Check if server is running
```bash
curl http://localhost:8001/health
```

If you get an error, restart:
```bash
./stop_insightpulse.sh
./start_insightpulse.sh
```

**Solution 2:** Kill zombie processes
```bash
lsof -ti:8001 | xargs kill -9
./start_insightpulse.sh
```

### Problem: Script doesn't run

**Solution:** Make it executable
```bash
chmod +x start_insightpulse.sh stop_insightpulse.sh
./start_insightpulse.sh
```

### Problem: "Permission denied"

**Solution:**
```bash
cd ~/Documents/InsightPulse
chmod +x *.sh
./start_insightpulse.sh
```

---

## ✅ What's Included

### AI Features:
- ✅ GPT-4 strategic insights
- ✅ Malaysian market intelligence (TikTok-first strategy)
- ✅ Sentiment analysis (Malay + English + Multilingual)
- ✅ Emotion detection
- ✅ Business priority ranking
- ✅ Actionable recommendations in Bahasa Malaysia

### Platforms Supported:
- ✅ Facebook
- ✅ Instagram
- ✅ TikTok
- ✅ X (Twitter)
- ✅ News articles
- ✅ E-commerce (Shopee, Lazada)

### Analysis Types:
- ✅ Sentiment (Positive/Negative/Neutral)
- ✅ Emotion (Happy, Angry, Sad, Love, Fear, Surprise)
- ✅ Platform breakdown
- ✅ Business priorities
- ✅ Strategic insights
- ✅ Next steps (Hala Tuju)

---

## 📚 More Documentation

- **START_HERE.md** - General guide
- **WHICH_SCRIPT_TO_USE.md** - Choose the right script
- **HOW_TO_START_INSIGHTPULSE.md** - Detailed instructions

---

## 🎉 You're Ready!

```bash
cd ~/Documents/InsightPulse
./start_insightpulse.sh
```

Then open: **http://localhost:8001/**

**Selamat menggunakan InsightPulse! 🇲🇾🚀**
