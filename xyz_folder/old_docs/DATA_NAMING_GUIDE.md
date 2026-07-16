# 📋 InsightPulse Data Naming & Recognition Guide

## 🎯 **Overview**
This guide explains how to easily recognize and track your crawler data in InsightPulse.

## 📁 **Data File Naming Convention**

### **Current Smart Crawler Files:**
```
platform_factcheck_topic_keywords_YYYYMMDD_HHMMSS.csv
```

### **Examples:**
- `facebook_factcheck_BMT_bantuan_musim_tengkujuh_20250620_232748.csv`
- `lowyat_factcheck_Islam_dalam_politik_Malaysia_OR_PolitikUlama_20250610_225025.csv`
- `google_factcheck_Harga_getah_harian_20250621_002238.csv`

### **File Name Components:**
1. **Platform**: facebook, google, instagram, lowyat, news, tiktok, x
2. **Type**: factcheck (analysis type)
3. **Topic**: Main keywords or claim being analyzed
4. **Date**: YYYYMMDD format
5. **Time**: HHMMSS format

## 🔍 **Easy Recognition System**

### **1. Analysis ID Tracking**
Each analysis gets a unique ID:
```
analysis_20250621_185500
```

### **2. Crawl Summary Display**
InsightPulse now shows:
- **Total Platforms Used**: 7/7 platforms
- **Platform Breakdown**: 
  - Facebook: 1,000 records
  - Lowyat: 2,000 records
  - Google: 200 records
  - etc.
- **Data Quality**: Authentic/Simulated
- **Collection Timestamp**: 2025-06-21 18:55:00

### **3. Report Naming**
Downloaded reports include:
- **Topic**: Your original claim/input
- **Analysis ID**: Unique identifier
- **Crawl ID**: Data collection identifier
- **Timestamp**: When analysis was performed

## 📊 **Data Location Structure**

```
/Users/rmtariq/InsightPulse/data/smart_crawlers/
├── facebook/
│   ├── facebook_factcheck_BMT_bantuan_musim_tengkujuh_20250620_232748.csv
│   ├── facebook_factcheck_ulama_berpengaruh_kepimpinan_ulama_malaysia_20250610_132709.csv
│   └── ...
├── google/
│   ├── google_factcheck_BMT_bantuan_musim_tengkujuh_20250620_230545.csv
│   ├── google_factcheck_Harga_getah_harian_20250621_002238.csv
│   └── ...
├── instagram/
│   ├── instagram_factcheck_BMT_bantuan_musim_tengkujuh_20250620_233342.csv
│   └── ...
├── lowyat/
│   ├── lowyat_factcheck_Islam_dalam_politik_Malaysia_OR_PolitikUlama_20250610_225025.csv
│   ├── lowyat_factcheck_Malaysia_politik_20250610_122055.csv
│   └── ...
├── news/
│   ├── news_factcheck_BMT_bantuan_musim_tengkujuh_20250620_230750.csv
│   └── ...
├── tiktok/
│   ├── tiktok_factcheck_BMT_bantuan_musim_tengkujuh_20250620_233834.csv
│   └── ...
└── x/
    ├── x_factcheck_BMT_bantuan_musim_tengkujuh_20250620_232052.csv
    └── ...
```

## 🏷️ **Topic Recognition Patterns**

### **Agricultural Topics:**
- `BMT_bantuan_musim_tengkujuh` → BMT agricultural subsidies
- `Produktiviti_risda` → RISDA productivity programs
- `Harga_getah_harian` → Daily rubber prices

### **Political Topics:**
- `Islam_dalam_politik_Malaysia` → Islam in Malaysian politics
- `Malaysia_politik` → General Malaysian politics
- `SST_cukai_MADANI` → SST tax policy

### **Economic Topics:**
- `Malaysia_ekonomi_politik_terkini` → Current economic politics
- `Malaysia_ekonomi_getah` → Rubber economy

## 🎯 **Quick Identification Tips**

### **1. By Date Range:**
- **June 10, 2025**: Political/religious topics
- **June 20, 2025**: Agricultural topics (BMT, rubber)
- **June 21, 2025**: Economic analysis

### **2. By Platform:**
- **Facebook**: Largest datasets (60K+ records)
- **Lowyat**: Forum discussions (11K+ records)
- **TikTok**: Video content analysis (14K+ records)
- **Instagram**: Visual content analysis (10K+ records)
- **Google**: Search trends (2K+ records)
- **News**: Media coverage (3K+ records)
- **X/Twitter**: Real-time discussions (12K+ records)

### **3. By File Size:**
- **Large files (1MB+)**: Comprehensive data collection
- **Medium files (100KB-1MB)**: Focused analysis
- **Small files (<100KB)**: Targeted searches

## 📈 **Analysis Tracking**

### **In InsightPulse Interface:**
1. **Step 3 (Crawling)**: Shows platform breakdown
2. **Step 5 (Analysis)**: Displays data sources used
3. **Step 6 (Report)**: Includes analysis ID and metadata

### **Downloaded Reports Include:**
- **Analysis ID**: `analysis_20250621_185500`
- **Crawl ID**: `crawl_20250621_185500`
- **Topic**: Original claim/input
- **Data Sources**: List of platforms used
- **Total Records**: Exact count per platform
- **Collection Time**: When data was gathered

## 🔄 **Data Sync Commands**

### **Manual Sync:**
```bash
python sync_crawler_data.py
```

### **Check Data Status:**
```bash
ls -la /Users/rmtariq/InsightPulse/data/smart_crawlers/*/
```

### **Count Records:**
```bash
wc -l /Users/rmtariq/InsightPulse/data/smart_crawlers/*/*.csv
```

## 💡 **Best Practices**

### **1. Regular Syncing:**
- Run sync script after new crawling sessions
- Check data availability before analysis

### **2. Topic Naming:**
- Use clear, descriptive keywords
- Include relevant context (dates, locations)
- Separate multiple concepts with underscores

### **3. Analysis Organization:**
- Save reports with meaningful names
- Include analysis ID in file names
- Keep track of which data was used

### **4. Data Management:**
- Monitor disk space usage
- Archive old analyses
- Backup important datasets

## 🚀 **Quick Start Checklist**

- [ ] Check data availability status in Step 3
- [ ] Select appropriate platforms for your topic
- [ ] Note the analysis ID when generated
- [ ] Download reports with descriptive names
- [ ] Keep track of data sources used
- [ ] Sync new data regularly

## 📞 **Support**

If you need help with data recognition or naming:
1. Check the data availability status in InsightPulse
2. Run the sync script to update data
3. Review this guide for naming conventions
4. Check file timestamps for recent data
