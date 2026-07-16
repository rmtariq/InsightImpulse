# 📦 Folder Sharing Checklist for InsightPulse

**Before sharing `/Users/rmtariq/Documents/InsightPulse` with colleagues**

---

## ✅ Required Actions

### 1. Security & Privacy

- [ ] **Remove `.env` file** (contains API keys)
  ```bash
  rm .env
  ```

- [ ] **Create `.env.example`** (template without actual keys)
  ```bash
  cat > .env.example << 'ENVFILE'
  # API Keys (Replace with your own)
  APIFY_API_TOKEN=your_apify_token_here
  SERPAPI_KEY=your_serpapi_key_here
  OPENAI_API_KEY=your_openai_key_here
  ANTHROPIC_API_KEY=your_claude_key_here
  
  # Database
  DATABASE_URL=sqlite:///data/insightpulse.db
  ENVFILE
  ```

- [ ] **Clear sensitive logs**
  ```bash
  > backend.log
  > api.log
  > backend_startup.log
  ```

### 2. Clean Up Data

- [ ] **Remove old crawled data** (optional - keep samples)
  ```bash
  # Keep only recent files
  python -c "from backend.utils.data_cleanup import cleanup_old_data; cleanup_old_data(7, 3)"
  ```

- [ ] **Check JITP 2026 folder** for sensitive political content
  ```bash
  ls -lh JITP_2026/processed_data/
  # Remove if needed: rm JITP_2026/processed_data/*.csv
  ```

- [ ] **Clear reports folder** (optional)
  ```bash
  ls -lh reports/
  # Remove old reports: rm -rf reports/202605*
  ```

### 3. Verify Documentation

- [ ] **Check all docs are up to date**
  ```bash
  ls -lh *.md
  ```

Required files:
- ✅ `INSIGHTPULSE_COMPLETE_GUIDE.md` (Main guide - 1062 lines)
- ✅ `QUICK_START_FOR_COLLEAGUES.md` (Quick start)
- ✅ `DATA_STORAGE_STRUCTURE.md` (Storage details)
- ✅ `CSV_STORAGE_SUMMARY.md` (CSV formats)
- ✅ `START_INSIGHTPULSE.md` (Startup guide)

### 4. Test the Application

- [ ] **Start backend successfully**
  ```bash
  python web_backend/simple_app.py
  ```
  Should see: `Uvicorn running on http://0.0.0.0:8001`

- [ ] **Check frontend loads**
  ```
  http://localhost:8001/
  ```

- [ ] **Test health endpoint**
  ```bash
  curl http://localhost:8001/health
  ```

### 5. Create Archive

- [ ] **Zip the folder** (exclude unnecessary files)
  ```bash
  cd /Users/rmtariq/Documents/
  
  # Create archive excluding large/temp files
  zip -r InsightPulse_Share.zip InsightPulse \
    -x "InsightPulse/.env" \
    -x "InsightPulse/NEImpulse/*" \
    -x "InsightPulse/__pycache__/*" \
    -x "InsightPulse/*/__pycache__/*" \
    -x "InsightPulse/*/*/__pycache__/*" \
    -x "InsightPulse/*.log" \
    -x "InsightPulse/backend.log" \
    -x "InsightPulse/api.log" \
    -x "InsightPulse/xyz_folder/*"
  ```

---

## 📋 What to Share

### Essential Files
✅ `INSIGHTPULSE_COMPLETE_GUIDE.md` - Main documentation  
✅ `QUICK_START_FOR_COLLEAGUES.md` - Quick start  
✅ `requirements.txt` - Dependencies  
✅ `web_backend/` - Backend server  
✅ `web_frontend/` - Frontend UI  
✅ `backend/` - Crawlers & services  
✅ `data/` - Storage folders (empty or sample data)  

### Optional Files
📄 `JITP_2026/` - Political analysis project (check for sensitive data first)  
📄 `reports/` - Sample reports (remove if sensitive)  
📄 Sample CSV files from `data/analyzed/` or `data/combined/`  

### Exclude
❌ `.env` - API keys (NEVER share)  
❌ `NEImpulse/` - Virtual environment (they create their own)  
❌ `__pycache__/` - Python cache  
❌ `*.log` - Log files  
❌ `xyz_folder/` - Deprecated files  
❌ `.git/` - Git history (if any secrets)  

---

## 📝 Instructions Template for Colleague

```
Hi [Colleague Name],

I'm sharing the InsightPulse social media analytics platform with you.

📖 START HERE:
1. Read: QUICK_START_FOR_COLLEAGUES.md (5-minute guide)
2. For complete details: INSIGHTPULSE_COMPLETE_GUIDE.md (1062 lines)

🚀 QUICK START:
1. Create virtual environment: python -m venv venv
2. Activate: source venv/bin/activate (Mac/Linux) or venv\\Scripts\\activate (Windows)
3. Install: pip install -r requirements.txt
4. Create .env file with your API keys (see .env.example)
5. Run: python web_backend/simple_app.py
6. Open: http://localhost:8001/

✨ FEATURES:
- 10 social media platforms (Facebook, Instagram, X, TikTok, YouTube, LinkedIn, Google News, Lowyat, Shopee, Lazada)
- Multilingual sentiment analysis (Malay, English, Chinese)
- Emotion detection (8 emotions)
- Engagement metrics
- AI-powered insights
- Cross-platform analysis

📂 IMPORTANT LOCATIONS:
- Main app: http://localhost:8001/
- CSV upload: http://localhost:8001/analyze_csv.html
- Political dashboard: JITP_2026/PAS_Dashboard_STANDALONE.html
- Data storage: data/smart_crawlers/, data/analyzed/, data/combined/

⚠️ YOU NEED:
- Python 3.10+
- Apify API key (https://apify.com)
- SerpAPI key (https://serpapi.com)
- OpenAI API key (optional - for AI insights)
- Anthropic API key (optional - for Claude)

📞 NEED HELP?
- Check documentation in *.md files
- Review backend.log for errors
- Check http://localhost:8001/health for status

Good luck! 🚀
```

