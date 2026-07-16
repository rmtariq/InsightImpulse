# 🚀 How to Start InsightPulse App

## **EASIEST METHOD - Use Startup Script**

### Step 1: Open Terminal
- Press `Cmd + Space` (Spotlight)
- Type "Terminal" and press Enter

### Step 2: Run the Startup Script
Copy and paste this command into Terminal:

```bash
cd /Users/rmtariq/Documents/InsightPulse && ./start_app.sh
```

Press **Enter**

### Step 3: Wait for Models to Load
You'll see:
```
🚀 Starting InsightPulse Application...
✅ Activating virtual environment...
🤖 Loading AI Models (this takes 30-60 seconds)...
⏳ Please wait...
```

### Step 4: Look for This Message
When you see:
```
INFO:     Uvicorn running on http://0.0.0.0:8001 (Press CTRL+C to quit)
```

**The app is READY!** ✅

### Step 5: Open Your Browser
Open any web browser and go to:
```
http://localhost:8001
```

---

## **ALTERNATIVE METHOD - Manual Commands**

If the script doesn't work, run these commands **one by one**:

```bash
# 1. Go to project folder
cd /Users/rmtariq/Documents/InsightPulse

# 2. Activate virtual environment
source NEImpulse/bin/activate

# 3. Start backend
python web_backend/simple_app.py
```

Wait for "Uvicorn running on http://0.0.0.0:8001", then open http://localhost:8001

---

## **To STOP the App**

Press `Ctrl + C` in the Terminal window where the app is running

---

## **Troubleshooting**

### Problem: Port 8001 already in use
**Solution:**
```bash
lsof -ti:8001 | xargs kill -9
```
Then start the app again.

### Problem: "command not found: python"
**Solution:** Use `python3` instead:
```bash
python3 web_backend/simple_app.py
```

### Problem: Models taking too long to load
**Solution:** This is normal! AI models are large files. First time loading can take 1-2 minutes. Be patient! ⏳

### Problem: Browser shows "Connection refused"
**Solution:** Make sure you see "Uvicorn running on http://0.0.0.0:8001" in Terminal first!

---

## **Quick Reference**

| What | Command |
|------|---------|
| **Start App** | `./start_app.sh` |
| **Stop App** | Press `Ctrl + C` |
| **Check if Running** | `lsof -i :8001` |
| **Kill Port 8001** | `lsof -ti:8001 \| xargs kill -9` |
| **URL** | http://localhost:8001 |

---

## **Expected Startup Time**

- ⏱️ **First time:** 1-2 minutes (downloading models)
- ⏱️ **Subsequent runs:** 30-60 seconds (loading models from cache)

---

**Last Updated:** 2026-02-15  
**All 10 Platforms Ready:** ✅ Facebook, Instagram, X, TikTok, YouTube, LinkedIn, Google News, Lowyat, Shopee, Lazada
