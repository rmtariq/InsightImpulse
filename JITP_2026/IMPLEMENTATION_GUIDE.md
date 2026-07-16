# PAS-Bersatu Political Analysis - Implementation Guide

## 📄 Source Document
**File:** `Kalau tuan mahu, saya boleh sambung terus dan tuli.docx`

This document contains a **technical specification** for analyzing PAS-Bersatu coalition dynamics using InsightPulse.

---

## 🎯 Objective

Build an analytics pipeline to:
1. **Detect** social media conversations about PAS-Bersatu relationship
2. **Filter** relevant discussions about "coalition review", "split", "PAS solo"
3. **Analyze** sentiment, emotions, and public perception
4. **Generate insights** on electoral implications (PRN/PRU)

---

## 🔍 Key Research Questions

The analysis must answer:
1. **When** does the issue peak? (temporal analysis)
2. **Who** is more supported or blamed? (party comparison)
3. **What emotions** are dominant? (sentiment & emotion analysis)
4. **Which platforms** are most influential? (platform comparison)
5. **Is "PAS solo"** seen as strength or risk? (strategic assessment)

---

## 📊 Search Query (Boolean)

```
("PAS" OR "Parti Islam Se-Malaysia" OR "Parti Islam Se Malaysia")
AND
("Bersatu" OR "PPBM" OR "Perikatan Nasional" OR "PN")
AND
("kaji semula hubungan" OR "teliti semula hubungan" OR 
 "putus kerjasama" OR "perpecahan" OR 
 "PAS bergerak solo" OR "PAS boleh bergerak solo")
```

---

## 🚀 How to Implement with InsightPulse

### **Step 1: Data Collection**

Run multiple crawls to capture comprehensive data:

#### **Crawl 1: Broad Coalition Discussion**
- **Query:** `PAS Bersatu Perikatan Nasional`
- **Platforms:** Facebook, Twitter, LinkedIn, YouTube
- **Size:** 300-500 per platform
- **Focus:** General coalition discourse

#### **Crawl 2: Split/Review Narrative**
- **Query:** `PAS Bersatu perpecahan kaji semula`
- **Platforms:** Facebook, Twitter, TikTok
- **Size:** 200-300 per platform
- **Focus:** Coalition tension discussions

#### **Crawl 3: PAS Independence Theme**
- **Query:** `PAS bergerak solo`
- **Platforms:** Facebook, Twitter, Instagram
- **Size:** 200-300 per platform
- **Focus:** PAS autonomy narrative

---

### **Step 2: Data Processing**

The specification document outlines these processing steps:

1. **Data Cleaning**
   - Remove duplicates
   - Normalize encoding (UTF-8)
   - Standardize platform names
   - Clean text (HTML entities, extra whitespace)

2. **Filtering**
   - Apply Boolean query logic
   - Case-insensitive matching
   - Support variations (e.g., "pas kaji hubungan")

3. **Feature Engineering**
   - Add temporal features (day, week, month)
   - Extract party mentions
   - Calculate engagement scores
   - Identify key themes

4. **Sentiment & Emotion Analysis**
   - Already done by InsightPulse! ✅
   - sentiment_label, sentiment_score
   - emotion_primary, emotion_* scores

---

### **Step 3: Analysis Tables**

According to the document, create these output tables:

1. **`pas_bersatu_split_posts`**
   - All filtered posts matching criteria
   - Includes parent-child linking

2. **`temporal_spike_analysis`**
   - Daily/weekly volume trends
   - Peak periods identification

3. **`party_sentiment_comparison`**
   - PAS vs Bersatu sentiment
   - Pro/anti sentiment by party

4. **`platform_influence_ranking`**
   - Engagement by platform
   - Virality metrics

5. **`emotion_distribution`**
   - Dominant emotions (anger, fear, love)
   - Emotion trends over time

6. **`key_narratives`**
   - Top themes
   - Influential posts (most commented/shared)

---

## 📋 Implementation Checklist

### **Phase 1: Data Collection (Now)**
- [ ] Run Crawl 1: PAS Bersatu PN (broad)
- [ ] Run Crawl 2: perpecahan kaji semula (tension)
- [ ] Run Crawl 3: PAS solo (independence)
- [ ] Verify parent-child linking works
- [ ] Check sentiment analysis coverage

### **Phase 2: Data Processing**
- [ ] Combine all crawled CSVs
- [ ] Apply Boolean filtering
- [ ] Remove duplicates
- [ ] Add temporal features
- [ ] Extract party mentions

### **Phase 3: Analysis**
- [ ] Temporal spike analysis
- [ ] Party sentiment comparison
- [ ] Platform influence ranking
- [ ] Emotion distribution
- [ ] Key narratives extraction

### **Phase 4: Insights & Reporting**
- [ ] Answer 5 key research questions
- [ ] Generate visualizations
- [ ] Create executive summary
- [ ] Prepare recommendations

---

## 🛠️ Tools Needed

1. **InsightPulse** (✅ Ready)
   - Multi-platform crawling
   - Parent-child linking
   - Sentiment & emotion analysis

2. **Python Analysis Scripts** (To Build)
   - Data combination
   - Boolean filtering
   - Temporal analysis
   - Comparison tables

3. **Visualization** (Optional)
   - Pandas/Matplotlib
   - Power BI / Tableau
   - Excel pivot tables

---

## 📈 Expected Output

### **Deliverables:**
1. **Raw Data:** Combined CSV with all posts + comments
2. **Filtered Data:** Boolean-matched subset
3. **Analysis Tables:** 6 tables as specified
4. **Insights Report:** Answers to 5 research questions
5. **Visualizations:** Charts showing trends, sentiment, emotions

---

## 🚀 Next Steps

**Ready to start?**

1. **Go to:** http://localhost:8001
2. **Run first crawl** with query: `PAS Bersatu Perikatan Nasional`
3. **Select platforms:** Facebook, Twitter, YouTube
4. **Set size:** 300 per platform
5. **Click Analyze**

Once done, tell me the CSV filename and I'll help you:
- Filter using the Boolean query
- Create analysis tables
- Generate insights

**Let's start the political analysis!** 🎯
