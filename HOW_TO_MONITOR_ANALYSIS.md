# 🔍 How to Monitor Analysis Progress

## 🚀 Quick Start - Run the Monitor

### **Option 1: Full Monitor** (Recommended) ⭐
Shows detailed progress with colors, auto-opens browser when complete:

```bash
cd /Users/rmtariq/Documents/InsightPulse
./watch_analysis.sh
```

**What it does:**
- ✅ Shows analysis start
- ✅ Tracks each platform progress
- ✅ Shows sentiment analysis progress
- ✅ Detects when combined data is saved
- ✅ **Automatically opens browser** when analysis completes
- ✅ Shows file size and record count

**Example Output:**
```
🔍 Starting Analysis Monitor...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 LIVE ANALYSIS PROGRESS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Analysis Started!
📱 Platforms: ['facebook', 'instagram', 'x', 'tiktok', 'threads']
🎯 Total platforms: 5

🔄 Processing: facebook
  ✓ ✅ Collected 84 records from facebook
🧠 Analyzing sentiment: 84 valid texts
✅ Platform 1/5 completed

🔄 Processing: instagram
  ✓ ✅ Collected 2524 records from instagram
🧠 Analyzing sentiment: 2522 valid texts
✅ Platform 2/5 completed

...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎉 COMBINED DATA SAVED!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📁 File: data/combined/Combined_facebook_instagram_x_tiktok_threads_20260528_142530.csv
📊 Size: 976K
📝 Records: 3009

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎉 ANALYSIS COMPLETE!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 Summary:
  ✅ Platforms processed: 5
  ✅ Combined data saved: Yes ✓

🌐 Opening results in browser...

✅ Monitor completed! Check your browser.
```

---

### **Option 2: Simple Monitor**
Just shows key events (no colors, simpler):

```bash
cd /Users/rmtariq/Documents/InsightPulse
./watch_simple.sh
```

**What it shows:**
- Platform collection messages
- Combined data save messages
- Analysis completion
- Errors (if any)

**To stop:** Press `Ctrl+C`

---

### **Option 3: Manual Monitoring**
Watch the full backend log:

```bash
cd /Users/rmtariq/Documents/InsightPulse
tail -f backend.log
```

**To stop:** Press `Ctrl+C`

---

## 📊 What to Look For

### **1. Analysis Started**
```
INFO:__main__:🔍 Starting PERFECT analysis for query: ...
INFO:__main__:📊 Platforms: ['facebook', 'instagram', 'x']
```

### **2. Platform Processing**
```
INFO:__main__:📱 Collecting data from facebook...
INFO:__main__:✅ Collected 84 records from facebook
INFO:__main__:🤖 Running custom sentiment & emotion analysis on 84 valid texts...
INFO:__main__:✅ Processed 84 records for facebook
```

### **3. Combined Data Saved** ⭐ **IMPORTANT!**
```
INFO:__main__:💾 COMBINED DATA saved: data/combined/Combined_facebook_instagram_x_20260528_142530.csv
INFO:__main__:📊 3009 total records from 5 platforms
INFO:__main__:📋 Platforms: facebook, instagram, x, tiktok, threads
```

### **4. Analysis Complete**
```
INFO:__main__:✅ Analysis completed successfully!
```

---

## ⏱️ Typical Timeline

| Stage | Duration | What's Happening |
|-------|----------|------------------|
| **Crawling** | 5-10 min | Apify actors collecting data from each platform |
| **Sentiment Analysis** | 2-3 min | AI models analyzing text (per platform) |
| **Saving Data** | 10-30 sec | Saving to smart_crawlers/, analyzed/, combined/ |
| **Report Generation** | 30-60 sec | Creating PowerPoint, Excel, Dashboard |
| **TOTAL** | 10-15 min | Full end-to-end analysis |

---

## 🎯 Quick Commands Reference

### Check if backend is running:
```bash
ps aux | grep uvicorn | grep -v grep
```

### Check combined data files:
```bash
ls -lht data/combined/*.csv | head -5
```

### Count records in latest combined file:
```bash
wc -l data/combined/*.csv | tail -1
```

### Watch for COMBINED DATA saves only:
```bash
tail -f backend.log | grep "COMBINED"
```

### Check for errors:
```bash
grep -i error backend.log | tail -20
```

---

## 🚨 If Something Goes Wrong

### Browser shows "Failed to fetch":
- ✅ **This is NORMAL** - just means frontend timeout
- ✅ Backend is still processing in background
- ✅ **Solution**: Wait and refresh browser after analysis completes
- ✅ Or use `./watch_analysis.sh` to auto-open when ready

### Analysis taking too long (>20 minutes):
```bash
# Check if backend crashed
curl http://localhost:8001/health

# If no response, restart backend
./stop_insightpulse.sh
./start_full_app.sh
```

### No combined data saved:
```bash
# Check if analysis completed
grep "Analysis completed" backend.log

# Check combined folder
ls -la data/combined/

# Check for errors
grep "COMBINED\|combined" backend.log | tail -20
```

---

## 💡 Tips

1. **Run monitor in separate terminal** - Don't close the terminal running the monitor
2. **Be patient** - Crawling real data takes time (5-15 minutes is normal)
3. **Check combined data** - After analysis, verify file was created in `data/combined/`
4. **Refresh browser** - If you see results but no data, refresh the page

---

**Created:** 2026-05-28  
**For:** InsightPulse v1.0.0
