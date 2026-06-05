# 🚀 InsightPulse - Quick Start for Colleagues

**Hi! Welcome to InsightPulse!** 👋

This is a **quick 5-minute guide** to get you started. For complete details, see `INSIGHTPULSE_COMPLETE_GUIDE.md`.

---

## ⚡ Super Quick Start (3 Steps)

### Step 1: Start the Backend
```bash
cd /Users/rmtariq/Documents/InsightPulse
python web_backend/simple_app.py
```

**Wait until you see:**
```
INFO:     Uvicorn running on http://0.0.0.0:8001
```

### Step 2: Open the App
Open browser and go to:
```
http://localhost:8001/
```

### Step 3: Run Analysis
1. Select platforms (e.g., Facebook, Instagram, X)
2. Enter your query (e.g., "budi95" or "mara liner")
3. Set dataset size (100-1000)
4. Click "Start Analysis"
5. Wait for results!

---

## 📂 Important Files & Folders

### Main Application
- **Backend Server**: `web_backend/simple_app.py`
- **Frontend**: `http://localhost:8001/`
- **CSV Analysis**: `http://localhost:8001/analyze_csv.html`

### Data Storage
```
data/
├── smart_crawlers/     # Raw data from platforms
├── analyzed/           # With sentiment + emotion
└── combined/           # All platforms merged
```

### Documentation
- **Complete Guide**: `INSIGHTPULSE_COMPLETE_GUIDE.md` ⭐ (1062 lines - READ THIS!)
- **Storage Guide**: `DATA_STORAGE_STRUCTURE.md`
- **CSV Guide**: `CSV_STORAGE_SUMMARY.md`

### JITP 2026 Project (Political Analysis)
- **Dashboard**: `JITP_2026/PAS_Dashboard_STANDALONE.html`
- **Data**: `JITP_2026/processed_data/`
- **Reports**: `JITP_2026/analysis_reports/`

---

## 🎯 What Can You Do?

### 1. Social Listening
Monitor what people say about your brand/topic:
- ✅ Track sentiment (Positive/Negative/Neutral)
- ✅ Detect emotions (Joy, Anger, Sadness, etc.)
- ✅ Measure engagement (Likes, Shares, Comments)
- ✅ Compare platforms

### 2. Crisis Detection
Alert on negative sentiment spikes:
- ✅ Real-time monitoring
- ✅ Negative content alerts
- ✅ High-engagement issues

### 3. Trend Analysis
Track topics over time:
- ✅ Time-series sentiment
- ✅ Volume tracking
- ✅ Viral content detection

### 4. Analyze Your CSV
Upload your own data:
- ✅ Go to: http://localhost:8001/analyze_csv.html
- ✅ Upload CSV with "Text" column
- ✅ Get sentiment + emotion analysis

---

## 🌐 Supported Platforms (10 Total)

| Platform | Type | Best For |
|----------|------|----------|
| Facebook | Social | Consumer sentiment |
| Instagram | Social | Brand monitoring |
| X (Twitter) | Social | News & trends |
| TikTok | Social | Viral content |
| YouTube | Social | Video comments |
| LinkedIn | Professional | B2B insights |
| Google News | News | Media coverage |
| Lowyat Forum | Forum | Tech discussions |
| Shopee | E-commerce | Product reviews |
| Lazada | E-commerce | Product reviews |

---

## 🔧 Common Commands

### Start Backend
```bash
python web_backend/simple_app.py
```

### Check Backend Status
```bash
curl http://localhost:8001/health
```

### Stop Backend (if stuck)
```bash
lsof -ti:8001 | xargs kill -9
```

### View Data
```bash
# Raw data
ls -lh data/smart_crawlers/facebook/

# Analyzed data
ls -lh data/analyzed/

# Combined data
ls -lh data/combined/
```

### Cleanup Old Files
```python
from backend.utils.data_cleanup import cleanup_old_data
result = cleanup_old_data(days_smart=30, days_analyzed=7)
```

---

## 📊 Understanding Results

### Sentiment Score
- **Range**: -1.0 to +1.0
- **Negative**: -1.0 to -0.3
- **Neutral**: -0.3 to +0.3
- **Positive**: +0.3 to +1.0

### Sentiment Labels
- **Negative**: Bad reviews, complaints
- **Neutral**: Factual statements
- **Positive**: Praise, recommendations

### Emotions (8 Types)
- Joy, Anger, Sadness, Fear, Love, Surprise, Neutral, Disgust
- Each scored 0-1 (highest = dominant emotion)

### Engagement Score
- **Formula**: Likes + Shares + Comments + (Views/10)
- **High Score**: Viral potential
- **Low Score**: Limited reach

---

## 🎨 Special Dashboards

### Political Dashboard (JITP 2026)
```bash
# Open in browser
open JITP_2026/PAS_Dashboard_STANDALONE.html
```

**Features:**
- PAS vs Bersatu sentiment tracking
- Platform influence ranking
- Temporal trends
- Entity analysis

**Data Location:**
- `JITP_2026/processed_data/` - Raw data
- `JITP_2026/analysis_reports/` - Analysis results

---

## ⚠️ Troubleshooting

### Backend Won't Start
```bash
# Kill existing process
lsof -ti:8001 | xargs kill -9

# Restart
python web_backend/simple_app.py
```

### No Data After Analysis
- Check `data/smart_crawlers/` for raw data
- Check `data/analyzed/` for sentiment data
- Check `data/combined/` for merged data
- Review `backend.log` for errors

### Models Not Loading
```bash
# Clear cache
rm -rf ~/.cache/huggingface/

# Restart backend
python web_backend/simple_app.py
```

---

## 💡 Tips for Best Results

### Choose Right Dataset Size
- **Quick Test**: 100-500
- **Brand Monitoring**: 1,000-5,000
- **Research**: 10,000+

### Good Keywords
✅ Specific: "Budi95 subsidi" (good)  
❌ Generic: "Malaysia" (bad)

✅ Multilingual: "mara liner OR maraliner"  
❌ Single word: "bus"

### Best Platform Combinations
- **Consumer Products**: Facebook + Instagram + TikTok
- **News Monitoring**: X + Google News + Lowyat
- **E-commerce**: Shopee + Lazada + Facebook
- **Professional**: LinkedIn + X

---

## 📈 Export Data

### Download CSV
After analysis completes:
1. Click "Download Results" button
2. Open in Excel
3. Use pivot tables for analysis

### Export to Excel Programmatically
```python
import pandas as pd

# Load combined data
df = pd.read_csv("data/combined/Combined_*.csv")

# Export with multiple sheets
with pd.ExcelWriter('Report.xlsx') as writer:
    df.to_excel(writer, sheet_name='All Data', index=False)
    
    # Sentiment summary
    summary = df.groupby('Platform')['sentiment_label'].value_counts().unstack()
    summary.to_excel(writer, sheet_name='Summary')
```

---

## 🎓 Next Steps

1. ✅ **Read Complete Guide**: `INSIGHTPULSE_COMPLETE_GUIDE.md`
2. ✅ **Run First Analysis**: Use http://localhost:8001/
3. ✅ **Explore Dashboards**: Check JITP 2026 folder
4. ✅ **Review Data**: Look at `data/` folders
5. ✅ **Test CSV Upload**: Use analyze_csv.html

---

## 📞 Need Help?

### Check Logs
- `backend.log` - Backend errors
- `api.log` - API requests
- Terminal output - Real-time logs

### Review Documentation
- `INSIGHTPULSE_COMPLETE_GUIDE.md` - Complete guide (1062 lines)
- `DATA_STORAGE_STRUCTURE.md` - Storage details
- `CSV_STORAGE_SUMMARY.md` - CSV formats

### Contact
- **Developer**: Ts Dr Raja Mohd Tariqi Bin Raja Lope Ahmad
- **Project**: JITP 2026

---

## ✅ Checklist Before Sharing

Before sharing this folder with others, make sure:

- [ ] Remove `.env` file (contains API keys)
- [ ] Clear `backend.log` if contains sensitive data
- [ ] Remove old data from `data/smart_crawlers/`
- [ ] Check `JITP_2026/` for sensitive political data
- [ ] Test backend starts successfully
- [ ] Verify frontend opens at http://localhost:8001/

---

**Ready to go! 🚀**

**Main Guide**: `INSIGHTPULSE_COMPLETE_GUIDE.md`  
**Dashboard**: `http://localhost:8001/`  
**Political Analysis**: `JITP_2026/PAS_Dashboard_STANDALONE.html`

**Have fun analyzing! 📊**
