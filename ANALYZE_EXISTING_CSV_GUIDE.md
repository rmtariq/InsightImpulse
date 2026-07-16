# 📊 Analyze Existing CSV Files - Complete Guide

This guide shows you how to run **Universal Intelligence Analysis** on CSV files you've already collected, without re-crawling the data.

---

## 🎯 Why Use This Feature?

✅ **Save Time** - No need to wait for crawling again  
✅ **Save Money** - No additional API costs  
✅ **Re-analyze Old Data** - Apply new insights to past campaigns  
✅ **Multiple Analyses** - Try different time filters or topics  
✅ **Offline Analysis** - Works on any CSV file, anywhere  

---

## 🚀 Method 1: Command Line (Fastest)

### Basic Usage

```bash
python analyze_existing_csv.py <csv_file_path> [topic_name] [days_filter]
```

### Examples

**1. Analyze Mara Liner data (90 days):**
```bash
python analyze_existing_csv.py data/combined/Combined_facebook_instagram_tiktok_x_20260524_004112.csv "Mara Liner" 90
```

**2. Analyze with different time filter (30 days):**
```bash
python analyze_existing_csv.py data/combined/Combined_facebook_instagram_tiktok_x_20260524_004112.csv "Mara Liner" 30
```

**3. Analyze different brand:**
```bash
python analyze_existing_csv.py data/combined/your_brand_data.csv "Your Brand" 60
```

### What You'll Get

After running the analysis, you'll find:

```
reports/universal_analysis_Mara_Liner/
├── insights.json          # Complete analysis with all metrics
└── cleaned_data.csv       # Cleaned, classified dataset
```

---

## 🌐 Method 2: Web Interface (Coming Soon)

### Step 1: Access the Interface

Open your browser and go to:
```
http://localhost:8001/analyze_csv.html
```

### Step 2: Select Your CSV

- Browse through available CSV files in `data/combined/`
- Click on the file you want to analyze
- It will highlight in blue when selected

### Step 3: Configure Analysis

- **Brand/Topic Name**: Enter the brand or topic (e.g., "Mara Liner")
- **Time Filter**: Choose how many days of recent data to analyze (default: 90)

### Step 4: Analyze

- Click "Analyze CSV"
- Wait for analysis to complete (usually 10-30 seconds)
- Results will be saved automatically

---

## 📂 Output Files Explained

### 1. `insights.json`

Complete analysis in JSON format with:
- **Executive Snapshot**: Data quality, time coverage, platform breakdown
- **Business Priorities**: Categorized by type and severity
- **Critical Issues**: High-priority problems needing attention
- **Opportunities**: Positive feedback to amplify
- **Action Plan**: 24h, 7-day, and 30-day recommendations

### 2. `cleaned_data.csv`

Processed dataset with new columns:
- `is_relevant`: Boolean - is this content actually about your topic?
- `category`: Complaint, Praise, Question, Promo Response, Feature Request, General
- `priority`: Critical, High, Medium, Opportunity, Low
- `content_owner`: Owned (brand), Earned (public), News/Media

---

## 🎨 Advanced Usage

### Analyze Multiple Time Periods

Compare different time ranges:

```bash
# Last 7 days
python analyze_existing_csv.py data.csv "Brand" 7

# Last 30 days
python analyze_existing_csv.py data.csv "Brand" 30

# Last 90 days
python analyze_existing_csv.py data.csv "Brand" 90
```

### Batch Analysis

Analyze multiple CSV files at once:

```bash
#!/bin/bash
for csv in data/combined/*.csv; do
    python analyze_existing_csv.py "$csv" "Mara Liner" 90
done
```

### Custom Script Integration

Use in your own Python scripts:

```python
from backend.services.universal_intelligence_dashboard import UniversalIntelligenceDashboard

# Analyze
analyzer = UniversalIntelligenceDashboard(
    csv_path='your_data.csv',
    topic_name='Your Brand'
)

insights = analyzer.analyze(filter_days=90)

# Export
analyzer.export_to_json('output/insights.json')
analyzer.export_cleaned_data('output/cleaned.csv')

# Print summary
analyzer.print_summary()
```

---

## 🔧 Troubleshooting

### Error: "File not found"
- Check the CSV path is correct
- Use absolute path or path relative to project root

### Error: "No relevant content found"
- Try increasing the time filter (e.g., from 30 to 90 days)
- Check that your CSV contains the topic/brand name
- Verify the topic name spelling

### Low data quality score (< 10%)
- Normal! The system filters out noise automatically
- Only truly relevant content is kept
- Higher quality = better insights

---

## 💡 Tips for Best Results

1. **Use descriptive topic names** - "Mara Liner" not just "Mara"
2. **Start with 90 days** - Good balance of recent + enough data
3. **Review cleaned_data.csv** - See what was classified as what
4. **Compare time periods** - Spot trends over time
5. **Use insights.json** - Perfect for reporting to management

---

## 📊 Understanding the Output

### Data Quality Score

- **80-100%**: Excellent - most data is relevant
- **50-79%**: Good - decent signal-to-noise ratio  
- **20-49%**: Fair - topic is mixed with other content
- **< 20%**: Low - lots of noise filtered (but remaining data is high quality!)

### Business Categories

- **Complaint/Issue** (High Priority): Problems, delays, refunds
- **Praise/Positive** (Opportunity): Happy customers, recommendations
- **Questions** (Medium Priority): Customer inquiries
- **Feature Requests** (Medium): Suggestions for improvement
- **General Mentions** (Low): Neutral brand mentions

---

## 🎯 Example Workflow

1. **Collect Data** (one time):
   - Run social media crawl
   - Get CSV in `data/combined/`

2. **Analyze** (anytime):
   ```bash
   python analyze_existing_csv.py data/combined/your_data.csv "Brand" 90
   ```

3. **Review**:
   - Open `insights.json` for summary
   - Open `cleaned_data.csv` in Excel for details

4. **Share**:
   - Send insights.json to management
   - Use cleaned_data.csv for custom reports

5. **Re-analyze** (when needed):
   - Try different time periods
   - Apply new topic names
   - Compare trends

---

## ✅ Quick Checklist

- [ ] CSV file is in `data/combined/` or accessible path
- [ ] Topic/brand name is correct
- [ ] Time filter makes sense for your data
- [ ] Output directory has enough space
- [ ] Ready to review results

---

**Need help?** Check the example command or review the output from a successful run!
