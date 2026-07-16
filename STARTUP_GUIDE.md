# InsightPulse - Startup Guide

## 🎯 Current Status

| Service | Status | Port | Action |
|---------|--------|------|--------|
| **Backend** | ✅ RUNNING | 8001 | Already running |
| **Frontend** | ❌ NOT NEEDED | - | Self-contained HTML |
| **Database** | ✅ SQLITE | - | Auto-created |

---

## 📝 Architecture

**InsightPulse is a SINGLE-SERVICE APPLICATION:**

```
Browser (localhost:8001)
    ↓
FastAPI Backend (Port 8001)
    ├─ Apify Crawlers (cloud-based)
    ├─ Sentiment Analysis (local ML models)
    ├─ CSV Storage (local filesystem)
    └─ SQLite Cache (data/insightpulse.db)
```

**Frontend is NOT separate** - it's embedded in the backend!

---

## ✅ What's Already Running

```bash
# Backend is RUNNING:
/Users/rmtariq/Documents/InsightPulse/NEImpulse/bin/python \
  -m uvicorn web_backend.simple_app:app --host 0.0.0.0 --port 8001
```

**Status:** ✅ All models loaded  
**Listening:** http://localhost:8001

---

## 🚀 To Start/Restart

### Option 1: Start Backend (if not running)
```bash
cd /Users/rmtariq/Documents/InsightPulse
nohup /Users/rmtariq/Documents/InsightPulse/NEImpulse/bin/python \
  -m uvicorn web_backend.simple_app:app --host 0.0.0.0 --port 8001 \
  > backend.log 2>&1 &
```

### Option 2: Stop & Restart
```bash
pkill -9 -f uvicorn
sleep 2
nohup /Users/rmtariq/Documents/InsightPulse/NEImpulse/bin/python \
  -m uvicorn web_backend.simple_app:app --host 0.0.0.0 --port 8001 \
  > backend.log 2>&1 &
```

### Option 3: Check Logs
```bash
tail -f backend.log
```

---

## 🎨 Access Dashboard

Open in browser:
```
http://localhost:8001
```

**No frontend build needed!** It's served directly from the backend.

---

## 📋 Quick Test

1. Open: http://localhost:8001
2. Select: Instagram + YouTube
3. Query: `budi95`
4. Click: "Analyze"
5. Wait: 5-10 minutes
6. Check: CSV in `data/combined/` folder

---

## 🛠️ Troubleshooting

| Issue | Solution |
|-------|----------|
| Port 8001 already in use | `lsof -i :8001` then kill process |
| Backend won't start | Check logs: `tail -50 backend.log` |
| No CSV generated | Wait longer, check crawler logs |
| Instagram 0 comments | Already fixed! (directUrls parameter) |

---

## 📚 Key Files

- Backend: `web_backend/simple_app.py`
- Crawler: `backend/data_crawlers/simple_apify_adapter.py`
- Frontend HTML: `web_frontend/simple_index.html`
- Database: `data/insightpulse.db`

