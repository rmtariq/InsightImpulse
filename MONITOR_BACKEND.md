# 📊 How to Monitor InsightPulse Backend

## 🚀 Quick Commands to Monitor the Backend

### 1️⃣ **Check if Backend is Running**
```bash
ps aux | grep uvicorn | grep -v grep
```
**Expected Output:**
```
rmtariq  40612  0.1  2.3  413100176  581328 s000  S  2:11PM  0:04.83 NEImpulse/bin/python -m uvicorn web_backend.simple_app:app --host 0.0.0.0 --port 8001
```
- **PID**: Process ID (e.g., 40612)
- **%CPU**: CPU usage
- **%MEM**: Memory usage
- **TIME**: How long it's been running

---

### 2️⃣ **Watch Backend Logs in Real-Time**
```bash
tail -f backend.log
```
**To stop watching**: Press `Ctrl+C`

**What you'll see:**
- INFO messages: Normal operations
- WARNING messages: Non-critical issues
- ERROR messages: Problems that need attention
- ✅ Success indicators
- ❌ Error indicators
- 💾 Data saving operations

---

### 3️⃣ **Check Last 30 Lines of Logs**
```bash
tail -30 backend.log
```

---

### 4️⃣ **Check Server Health**
```bash
curl -s http://localhost:8001/health
```
**Expected Output:**
```json
{
  "status": "healthy",
  "timestamp": "2026-05-28T14:12:19.356569",
  "version": "1.0.0",
  "data_directory": "/Users/rmtariq/Documents/InsightPulse/data/smart_crawlers",
  "data_available": true
}
```

---

### 5️⃣ **Check Port 8001 Status**
```bash
lsof -i :8001
```
**Expected Output:**
```
COMMAND     PID    USER   FD   TYPE             DEVICE SIZE/OFF NODE NAME
python3.1 40612 rmtariq   18u  IPv4 0x9e6b3eec6c5b3ada      0t0  TCP *:vcom-tunnel (LISTEN)
```

---

### 6️⃣ **Monitor Analysis in Real-Time**
```bash
tail -f backend.log | grep -E "💾|✅|❌|COMBINED|Sentiment|Platform"
```
This will show:
- Data saving operations (💾)
- Success/errors (✅/❌)
- Combined data saves
- Sentiment analysis progress
- Platform processing

---

### 7️⃣ **Check Combined Data Files**
```bash
ls -lht data/combined/*.csv | head -10
```
Shows the most recent combined data files

---

### 8️⃣ **Count Lines in Latest Combined File**
```bash
wc -l data/combined/*.csv | tail -1
```

---

### 9️⃣ **Watch for New Combined Files**
```bash
watch -n 5 "ls -lht data/combined/*.csv | head -5"
```
Refreshes every 5 seconds. Press `Ctrl+C` to stop.

---

### 🔟 **Check All Data Folders**
```bash
echo "Smart Crawlers:" && find data/smart_crawlers -name "*.csv" | wc -l
echo "Analyzed:" && find data/analyzed -name "*.csv" | wc -l
echo "Combined:" && find data/combined -name "*.csv" | wc -l
```

---

## 🎯 **Complete Monitoring Command** (All-in-One)

```bash
echo "=== 📊 INSIGHTPULSE STATUS ===" && \
echo "" && \
echo "1️⃣ Process:" && ps aux | grep uvicorn | grep -v grep && \
echo "" && \
echo "2️⃣ Health:" && curl -s http://localhost:8001/health && \
echo "" && \
echo "" && \
echo "3️⃣ Data Files:" && \
echo "  Smart Crawlers: $(find data/smart_crawlers -name "*.csv" | wc -l | xargs) files" && \
echo "  Analyzed: $(find data/analyzed -name "*.csv" | wc -l | xargs) files" && \
echo "  Combined: $(find data/combined -name "*.csv" | wc -l | xargs) files" && \
echo "" && \
echo "4️⃣ Latest Logs:" && tail -10 backend.log
```

---

## 🛑 **Stop the Backend**

```bash
./stop_insightpulse.sh
```
Or manually:
```bash
pkill -f "uvicorn web_backend.simple_app"
```

---

## 🔄 **Restart the Backend**

```bash
./stop_insightpulse.sh && ./start_full_app.sh
```

---

## 📝 **Useful Log Patterns**

**Search for errors:**
```bash
grep -i error backend.log | tail -20
```

**Search for combined data saves:**
```bash
grep -i "combined data" backend.log
```

**Search for specific platform:**
```bash
grep -i "facebook" backend.log | tail -20
```

**Search for sentiment analysis:**
```bash
grep -i "sentiment" backend.log | tail -30
```

---

**Last Updated:** 2026-05-28  
**InsightPulse Version:** 1.0.0
