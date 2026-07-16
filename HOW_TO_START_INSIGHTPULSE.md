# 🚀 How to Start InsightPulse

## Method 1: Using Terminal (RECOMMENDED)

### Step 1: Open Terminal
- Press `Cmd + Space` to open Spotlight
- Type "Terminal" and press Enter

### Step 2: Navigate to InsightPulse folder
```bash
cd ~/Documents/InsightPulse
```

### Step 3: Run the startup script
```bash
./start_insightpulse.sh
```

**That's it!** The script will:
- ✅ Check if the server is already running
- ✅ Kill old processes if needed
- ✅ Start the backend server
- ✅ Wait for it to be ready
- ✅ Automatically open your browser to the dashboard

---

## Method 2: Double-Click to Start (Easy!)

### One-Time Setup:

1. **Open Terminal** and run this command:
```bash
cd ~/Documents/InsightPulse && chmod +x start_insightpulse.sh
```

2. **Right-click** on `start_insightpulse.sh` in Finder
3. Select **"Open With"** → **"Terminal"** (or "Terminal.app")
4. If asked, click **"Open"** to confirm

From now on, you can just **double-click** `start_insightpulse.sh` to start InsightPulse!

---

## Method 3: Create Desktop Shortcut

### Create a clickable app icon:

1. **Open Automator** (in Applications folder)
2. Choose **"New Document"**
3. Select **"Application"**
4. Search for **"Run Shell Script"** and drag it to the workflow
5. Paste this code:
```bash
cd /Users/rmtariq/Documents/InsightPulse
./start_insightpulse.sh
```
6. Click **File** → **Save**
7. Name it **"InsightPulse"** and save to **Desktop**

Now you can **double-click the InsightPulse icon** on your desktop to start the app!

---

## 🛑 How to Stop InsightPulse

When you're done using InsightPulse:

```bash
cd ~/Documents/InsightPulse
./stop_insightpulse.sh
```

---

## 📊 What Happens When You Start?

1. ✅ Backend server starts on port 8001
2. ✅ Dashboard opens at: http://localhost:8001/static/analyze_csv.html
3. ✅ Server logs saved to: `csv_api.log`

---

## 🔧 Troubleshooting

### Problem: "Permission denied"
**Solution:**
```bash
cd ~/Documents/InsightPulse
chmod +x start_insightpulse.sh stop_insightpulse.sh
```

### Problem: "Port already in use"
**Solution:** The script automatically kills old processes. If it still fails:
```bash
lsof -ti:8001 | xargs kill -9
```

### Problem: Browser doesn't open
**Solution:** Manually open this URL:
```
http://localhost:8001/static/analyze_csv.html
```

### Problem: "Server failed to start"
**Solution:** Check the logs:
```bash
cd ~/Documents/InsightPulse
tail -50 csv_api.log
```

---

## ✅ Quick Reference

| Action | Command |
|--------|---------|
| **Start InsightPulse** | `./start_insightpulse.sh` |
| **Stop InsightPulse** | `./stop_insightpulse.sh` |
| **Check if running** | `curl http://localhost:8001/health` |
| **View logs** | `tail -f csv_api.log` |
| **Kill zombie processes** | `lsof -ti:8001 \| xargs kill -9` |

---

## 🎯 Dashboard Features

Once the app is running, you can:

1. ✅ **Upload CSV files** (drag & drop)
2. ✅ **Select from 48+ existing CSVs**
3. ✅ **Analyze with AI** (GPT-4 powered)
4. ✅ **View insights** (Sentiment, Emotion, Platform breakdown)
5. ✅ **Get strategic recommendations** in Bahasa Malaysia

---

**Enjoy using InsightPulse! 🚀🇲🇾**
