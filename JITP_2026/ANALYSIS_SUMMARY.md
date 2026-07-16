# JITP_2026: PAS-Bersatu Political Analysis

## 🎯 Project Overview

**Objective:** Analyze social media discourse about the PAS-Bersatu coalition relationship, focusing on:
- Coalition tensions and review of cooperation
- Narrative of "PAS solo" (PAS going independent)
- Public perception: Is "PAS solo" seen as a "firm move" (langkah tegas) or "risky move" (langkah berisiko)?

**Source Document:** `Kalau tuan mahu, saya boleh sambung terus dan tuli.docx`

---

## 📊 Data Collection Summary

### **3 Strategic Queries Executed:**

#### **Query 1: Coalition General (Broadest)**
- **Keywords:** `PAS OR Bersatu OR "Perikatan Nasional" OR PN OR hajihadi OR "haji hadi"`
- **Result:** 13,710 records
- **Purpose:** Capture all PAS-Bersatu-PN discussions

#### **Query 2: PAS Solo (Independence Theme)**
- **Keywords:** `"PAS bergerak solo" OR "PAS solo" OR "PAS gerak solo"`
- **Result:** 10,254 records
- **Purpose:** Focus on PAS independence narrative

#### **Query 3: Coalition Split (Tension & Breakup)**
- **Keywords:** `("PAS Bersatu" OR "PAS-Bersatu") AND ("perpecahan" OR "berpecah" OR "retak" OR "risky rift")`
- **Result:** 7,715 records
- **Purpose:** Capture coalition tension discussions

**Total Raw Data:** 31,679 records across 6 platforms

---

## 🔄 Processing Pipeline

### **Step 1: Data Cleaning & Combination**
- Combined all 3 queries: **5,414 rows**
- Removed empty/meaningless text: **-41 rows**
- Removed exact duplicates (by ID): **-981 rows**
- Removed near-duplicates (text similarity): **-791 rows**
- **Final Clean Dataset:** **3,601 unique records**

**Breakdown:**
- Posts: 2,877
- Comments: 724
- Platforms: facebook, instagram, threads, tiktok, x, youtube

---

### **Step 2: Boolean Filter (Specification-Compliant)**

Applied exact Boolean query from document:
```
("PAS" OR "Parti Islam Se-Malaysia")
AND
("Bersatu" OR "PPBM" OR "Perikatan Nasional" OR "PN")
AND
("kaji semula hubungan" OR "perpecahan" OR "PAS bergerak solo" OR variations)
```

**Result:** **114 highly relevant posts** (3.2% match rate)

This is the **core analytical dataset** that precisely matches the research focus.

---

### **Step 3: Feature Engineering**

Added features per document specification:

#### **Temporal Features:**
- `date_day`, `date_week`, `date_month`, `date_year`

#### **Phrase Detection Flags:**
- `has_pas_solo_phrase`: **20 posts** (17.5%)
- `has_split_phrase`: **96 posts** (84.2%)
- `has_review_phrase`: **3 posts** (2.6%)

#### **Entity Mentions:**
- PAS, Bersatu, PN, UMNO, PH
- Key figures: Muhyiddin, Hadi Awang, Hamzah

#### **Engagement Metrics:**
- Standardized `engagement_score` across platforms

---

## 📈 Key Findings (Preliminary)

### **1. Narrative Distribution**

| Theme | Count | Percentage |
|-------|-------|------------|
| **Split/Tension** (perpecahan, retak) | 96 | 84.2% |
| **PAS Solo** (independence) | 20 | 17.5% |
| **Review Cooperation** (kaji semula) | 3 | 2.6% |

**Key Insight:** The dominant narrative is about **coalition split/tension** (84%), not just review or independence.

---

### **2. Platform Distribution**

The 114 filtered posts came from various platforms, indicating widespread discussion across social media.

---

### **3. Temporal Patterns**

Date range: **Check `step3_feature_summary.txt` for exact dates**

This allows for:
- Spike detection (when did discussions peak?)
- Trend analysis (is tension increasing over time?)

---

## 📂 Output Files

All processed data is in: `JITP_2026/processed_data/`

| File | Description | Rows |
|------|-------------|------|
| `pas_bersatu_split_posts_raw.csv` | Combined, cleaned data | 3,601 |
| `pas_bersatu_split_posts_deduped.csv` | Deduplicated dataset | 3,601 |
| `pas_bersatu_filtered.csv` | Boolean-filtered (core dataset) | 114 |
| **`pas_bersatu_analysis_ready.csv`** | **Feature-engineered (analysis-ready)** | **114** |
| `step1_statistics.txt` | Step 1 stats | - |
| `step2_filter_statistics.txt` | Step 2 filter stats | - |
| `step3_feature_summary.txt` | Step 3 feature summary | - |

---

## 🔍 Next Steps

### **Recommended Analyses (Based on Document):**

1. **Temporal Spike Analysis**
   - When did discussions peak?
   - What triggered the spikes?

2. **Sentiment Analysis**
   - Is "PAS solo" framed positively or negatively?
   - What emotions dominate the discourse?

3. **Platform Influence**
   - Which platform drives the most engagement?
   - Cross-platform narrative comparison

4. **Key Narratives**
   - Extract most viral/engaging posts
   - Identify influential voices

5. **PAS Solo Deep Dive**
   - Among the 20 "PAS solo" posts, how many support vs reject?
   - Is it seen as "langkah tegas" (strength) or "langkah berisiko" (risk)?

---

## 🛠️ Analysis Scripts Created

1. ✅ `step1_combine_and_clean.py` - Data cleaning & combination
2. ✅ `step2_boolean_filter.py` - Boolean query filtering
3. ✅ `step3_feature_engineering.py` - Feature extraction

---

## 🎯 Research Questions (From Document)

The analysis should answer:

1. **When?** (Bila) - When did the issue peak?
2. **Who?** (Siapa) - Who is more supported/blamed? PAS or Bersatu?
3. **What emotions?** (Emosi apa) - Fear, anger, support?
4. **Which platforms?** (Platform mana) - Most influential?
5. **PAS Solo = Strength or Risk?** (Tegas atau berisiko?) - Core question

---

## ✅ Current Status

- [x] Data collection (3 queries, 31,679 raw records)
- [x] Data cleaning & deduplication (3,601 unique records)
- [x] Boolean filtering (114 core records)
- [x] Feature engineering (temporal, flags, entities, scores)
- [ ] **Next: Run detailed analysis and visualization**

**Analysis-ready dataset:** `JITP_2026/processed_data/pas_bersatu_analysis_ready.csv`

---

**Date:** 2026-05-29  
**Analyst:** Based on technical specification document
