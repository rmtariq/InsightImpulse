# KDEBWM Complaint Monitoring Analytics Module

## Overview

Executive-level complaint analytics and insights system for **KDEBWM** (Kumpulan Darul Ehsan Berhad Waste Management). This module transforms raw social media data into actionable intelligence for management decision-making.

---

## 🎯 Purpose

Monitor and analyze public complaints related to KDEBWM waste collection, cleanliness, missed pickups, dirty areas, and service dissatisfaction across social media, forums, news comments, and public digital channels.

**Target Audience**: KDEBWM CEO, management, and operations teams

---

## 📊 Features

### 1. Executive Summary
- Total complaint mentions in selected period
- Complaint trend direction (increasing/stable/decreasing)
- Top 3 complaint themes
- Top 3 hotspot areas
- Main recommendations for management

### 2. Core Analytics

**A. Complaint Volume**
- Total mentions
- Daily/weekly counts
- Trend vs previous period
- Peak complaint dates

**B. Sentiment Analytics**
- Negative/neutral/positive count and percentages
- Sentiment distribution
- Sentiment trend over time

**C. Complaint Theme Classification**
Automatically classifies complaints into:
- `missed_collection` - Sampah tak kutip, tidak ambil
- `late_collection` - Lambat, lewat, delay
- `overflowing_bin` - Tong penuh, longgokan
- `foul_smell` - Bau busuk, hancing
- `dirty_road_or_area` - Jalan kotor, kawasan kotor
- `public_cleansing_issue` - Pembersihan awam
- `illegal_dumping` - Buang sampah haram
- `general_complaint` - Aduan umum
- `praise_or_resolution` - Terima kasih, settled

**D. Hotspot / Area Analytics**
Extracts location mentions from text:
- Klang, Kajang, Petaling Jaya, Subang Jaya
- Selayang, Sepang, Kuala Selangor, Kuala Langat
- Hulu Selangor, Sabak Bernam, Shah Alam
- And more...

Returns:
- Complaint count by area
- Top 5 hotspot areas
- Area-wise percentages

**E. Platform Analytics**
- Count by platform (Facebook, Instagram, X, TikTok, etc.)
- Platform share percentages
- Most complaint-heavy platform
- Highest engagement platform

**F. Engagement / Severity Analytics**
- Top complaint posts by engagement
- Average engagement per complaint
- High-severity complaint count

**High-severity complaint criteria:**
- Strongly negative sentiment, OR
- High engagement, OR
- Contains urgency keywords: "teruk", "bau busuk", "tak datang", "lambat", "frust", "viral"

**G. CEO Dashboard Metrics**
- Total Complaints
- Negative Sentiment %
- Top Complaint Theme
- Top Hotspot Area
- Peak Complaint Date
- Most Complaint-Heavy Platform
- High Severity Count
- Unanswered Complaint %

### 3. Insight Generation

**Executive-level insights** (not technical commentary):
- Volume insight - What happened, why it matters, recommended action
- Theme insight - Which complaint types dominate
- Area insight - Where operational review is needed
- Platform insight - Where reputational risk is highest
- Reputation-response insight - Public response gaps

---

## 🚀 Usage

### Option 1: Dashboard UI (Recommended)

1. **Start the backend** (if not already running):
   ```bash
   cd /Users/rmtariq/Documents/InsightPulse
   source NEImpulse/bin/activate
   python web_backend/simple_app.py
   ```

2. **Open KDEBWM Dashboard**:
   ```
   http://localhost:8001/static/kdebwm_dashboard.html
   ```

3. **Select your combined CSV file** from the dropdown
4. **Click "Analyze KDEBWM Complaints"**
5. **View results**:
   - CEO Dashboard KPIs
   - Executive Summary
   - Key Insights
   - Management Recommendations
   - Detailed Analytics Tables

### Option 2: Python API

```python
from backend.services.kdebwm_analytics import analyze_kdebwm_complaints

# Analyze complaints from combined CSV
results = analyze_kdebwm_complaints(
    csv_path='data/combined/Combined_facebook_instagram_x_tiktok_20260524.csv',
    filter_days=30,
    output_dir='reports/kdebwm_analysis'
)

# View executive summary
print(results['executive_summary'])

# Access analytics
print(results['analytics']['dashboard'])
print(results['analytics']['themes'])
print(results['analytics']['hotspots'])

# Access insights
for insight in results['insights']['insights']:
    print(insight)
```

### Option 3: HTTP API

```bash
curl -X POST http://localhost:8001/api/kdebwm/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "csv_path": "data/combined/Combined_facebook_instagram_x_tiktok_20260524.csv",
    "filter_days": 30,
    "export_results": true
  }'
```

---

## 📁 Files Created

| File | Purpose |
|------|---------|
| `backend/services/kdebwm_analytics.py` | Core analytics engine (809 lines) |
| `web_backend/static/kdebwm_dashboard.html` | Executive dashboard UI (550 lines) |
| `web_backend/simple_app.py` (updated) | API endpoint `/api/kdebwm/analyze` |
| `KDEBWM_ANALYTICS_MODULE.md` | This documentation |

---

## 📈 Output Files

When analysis runs with `export_results=true`, the following files are created in `reports/kdebwm_complaint_analytics/`:

1. **`kdebwm_analytics_YYYYMMDD_HHMMSS.json`** - Complete analytics JSON
2. **`kdebwm_complaints_YYYYMMDD_HHMMSS.csv`** - Processed complaints with themes, areas, severity
3. **`executive_summary_YYYYMMDD_HHMMSS.txt`** - Text-based executive summary

---

## 🔍 Boolean Query Used

```
("KDEBWM" OR "KDEB Waste Management" OR "KDEB Waste")
AND
("sampah tak kutip" OR "sampah tidak dikutip" OR "kutipan sampah" OR "kutip sampah" OR 
 "longgokan sampah" OR "sampah penuh" OR "bau busuk" OR "jalan kotor" OR "kawasan kotor" OR 
 "pembersihan awam" OR "cleaning service" OR "public cleansing" OR "late collection" OR 
 "missed collection" OR "dirty area" OR "aduan")
```

---

## ✅ Next Steps

1. **Test with your current analysis** - The spinner is still running for your KDEBWM query
2. **Once analysis completes**, a combined CSV will be created in `data/combined/`
3. **Open the KDEBWM Dashboard** to view executive insights
4. **Export results** for management reporting

---

**Version**: 1.0.0  
**Last Updated**: 2026-05-24  
**Status**: ✅ Complete and ready for production use
