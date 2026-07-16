# Journal Article Anonymization Guide

**Purpose**: Protect client confidentiality by anonymizing all identifying information in journal article

**Date**: June 18, 2026  
**Status**: ✅ Complete

---

## 📋 WHAT WAS ANONYMIZED

### 1. Organization Names

| Original Name | Anonymized To | Context |
|---------------|---------------|---------|
| **KDEBWM** | **Organization A** | Waste management service provider |
| **Kumpulan Darul Ehsan Berhad Waste Management** | **Organization A (waste management service provider)** | Full name |
| **MARA Liner** | **Organization B** | Transportation service |
| **MARA Liner / MARALiner / MaraLiner** | **Organization B (intercity transportation service)** | All variations |

### 2. Geographic Locations

| Original Location | Anonymized To | Context |
|-------------------|---------------|---------|
| **Klang** | **Area X** | Primary complaint hotspot (27.7%) |
| **Petaling Jaya (PJ)** | **Area Y** | Secondary hotspot (18.5%) |
| **Subang Jaya** | **Area Z** | Third hotspot (13.8%) |
| **Kajang** | **Area W** | Fourth hotspot (10.8%) |
| **Shah Alam** | **Area V** | Fifth hotspot (7.7%) |
| **Selangor areas** | **Major urban areas** | General reference |

### 3. Boolean Queries

**Original (KDEBWM)**:
```
("KDEBWM" OR "KDEB Waste Management" OR "KDEB Waste") AND (...)
```

**Anonymized**:
```
("[Organization A]" OR "[Waste Service]") AND (...)
```

**Original (MARA Liner)**:
```
("MARA Liner" OR "MARALiner" OR "MaraLiner") AND (...)
```

**Anonymized**:
```
("[Organization B]" OR "[Bus Service]") AND (...)
```

### 4. Third-Party APIs & Crawlers

| Original Detail | Anonymized To | Reason |
|-----------------|---------------|--------|
| **Apify Actors** (specific actor names) | **Third-party API aggregators** | Avoid platform/vendor issues |
| **SerpAPI** | **Search API integrations** | Generic terminology |
| Facebook, Instagram, TikTok, etc. (specific) | **Social Networks (5), E-commerce (2), News/Forums (3)** | Platform category grouping |
| `danek/facebook-search-ppr` | *Removed* | No vendor attribution |
| `apify/instagram-scraper` | *Removed* | No vendor attribution |
| Model names like `rmtariq/ft-Malay-bert` | **BERT-based architecture, fine-tuned** | Generic architecture description |

**Key Changes:**
- ❌ NO specific API vendor names (Apify, SerpAPI)
- ❌ NO specific actor/scraper names
- ❌ NO platform-specific scraper details
- ✅ Generic "third-party API aggregators"
- ✅ "Ethical web crawling engines"
- ✅ Platform categories instead of names

---

## ✅ FILES UPDATED

1. **JOURNAL_ARTICLE_PUBLIC_SERVICES_ANONYMIZED.md** (renamed from `JOURNAL_ARTICLE_KDEBWM_MARA_LINER.md`)
   - All 560 lines reviewed
   - All company names replaced
   - All location names replaced
   - Ethical statement added to header

2. **JOURNAL_ARTICLE_EXECUTIVE_SUMMARY.md**
   - Quick stats section updated
   - Geographic intelligence section updated
   - Management recommendations updated
   - Data collection section updated

---

## 🔒 CONFIDENTIALITY STATEMENTS ADDED

### In Main Article Header:
```
**Ethical Statement:** Company names and identifiable information have been 
anonymized to protect organizational confidentiality. All data and findings 
are presented in aggregate form.
```

### In Acknowledgments Section:
```
We thank the participating organizations (Organization A and Organization B) 
for their cooperation. All identifying information has been anonymized to 
protect organizational confidentiality.
```

### In Data Availability Statement:
```
Anonymized aggregate data and code repository available upon reasonable request. 
Raw social media data and organizational identifiers cannot be shared due to 
confidentiality agreements, privacy regulations, and platform Terms of Service. 
All results are reported in aggregate form with anonymized location and 
organization names.
```

---

## 📊 DATA & RESULTS REMAIN UNCHANGED

✅ **All numbers are exactly the same:**
- Organization A: 2,925 records, 24.6% negative sentiment
- Organization B: 647 records, 47.2% positive sentiment
- Area X hotspot: 27.7% of complaints
- Platform distribution: TikTok 49.2%, Facebook 27.7%, etc.
- Sentiment scores, engagement metrics, all statistical findings

✅ **Only labels changed:**
- KDEBWM → Organization A
- MARA Liner → Organization B
- Klang → Area X
- Petaling Jaya → Area Y
- (and so on...)

✅ **Process remains identical:**
- Same methodology
- Same analytics framework
- Same InsightPulse platform
- Same sentiment models
- Same validation approach

---

## 🎯 BENEFITS OF ANONYMIZATION

### 1. Protects Client Confidentiality
- No explicit company names revealed
- Geographic areas generalized
- Maintains professional ethics

### 2. Preserves Research Value
- All data intact
- All findings valid
- All insights applicable
- Replicable methodology

### 3. Enables Publication
- Can submit to journals without client approval concerns
- Meets ethical research standards
- Protects competitive information

### 4. Maintains Generalizability
- Findings apply to any waste management org (not just KDEBWM)
- Findings apply to any transportation org (not just MARA Liner)
- Actually STRENGTHENS academic contribution

---

## 📝 HOW TO REFERENCE IN PRESENTATIONS

### If asked about organizations:
> "We studied two Malaysian public service organizations: one in waste 
> management and one in transportation. Due to confidentiality agreements, 
> we cannot disclose their names, but all data and findings are real and 
> have been anonymized to protect client privacy."

### If asked about locations:
> "The waste management organization serves major urban areas in Malaysia. 
> We identified significant geographic variation in complaint patterns, 
> with one area (Area X) accounting for 27.7% of complaints. Specific 
> location names have been anonymized."

### If asked about data validity:
> "All data is real and collected from actual social media platforms. Only 
> identifying labels have been changed—all numbers, patterns, and insights 
> remain exactly as analyzed."

---

## ✅ VERIFICATION CHECKLIST

**Organization & Location Anonymization:**
- [x] All instances of "KDEBWM" replaced with "Organization A"
- [x] All instances of "MARA Liner" replaced with "Organization B"
- [x] All instances of "Klang" replaced with "Area X"
- [x] All instances of "Petaling Jaya" / "PJ" replaced with "Area Y"
- [x] All instances of "Subang Jaya" replaced with "Area Z"
- [x] All instances of "Kajang" replaced with "Area W"
- [x] All instances of "Shah Alam" replaced with "Area V"
- [x] Boolean queries anonymized

**API & Platform Anonymization:**
- [x] Removed "Apify" vendor name → "Third-party API aggregators"
- [x] Removed "SerpAPI" vendor name → "Search API integrations"
- [x] Removed specific actor names (e.g., `danek/facebook-search-ppr`)
- [x] Platform names → Platform categories (Social Networks, E-commerce, News/Forums)
- [x] Model names → Generic architecture descriptions
- [x] Added compliance note (ToS, robots.txt, GDPR/PDPA)

**Documentation Updates:**
- [x] Ethical statement added to header
- [x] Data availability statement updated
- [x] Acknowledgments updated (no vendor attribution)
- [x] File renamed to reflect anonymization
- [x] Executive summary updated
- [x] All numerical data verified unchanged
- [x] Appendix A rewritten with generic terms

---

## 🎉 READY FOR PUBLICATION!

**New File**: `JOURNAL_ARTICLE_PUBLIC_SERVICES_ANONYMIZED.md`

**Status**: ✅ Fully anonymized, ready for journal submission

**Next Steps**:
1. Add author names and affiliations
2. Select target journal
3. Format according to journal guidelines
4. Submit with confidence—no client names exposed!

---

**Document Created**: June 18, 2026  
**Anonymization Method**: Systematic replacement with generic identifiers  
**Data Integrity**: 100% preserved—only labels changed
