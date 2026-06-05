# 🎯 InsightPulse - Startup Guide

## 📋 Prerequisites
- Python 3.10+ installed
- Virtual environment activated
- All dependencies installed

## 🚀 Quick Start Commands

### Option 1: Manual Start (Recommended)

#### Step 1: Start Backend API
```bash
cd /Users/rmtariq/InsightPulse
python backend/api.py
```
**Backend will run on:** http://localhost:8000

#### Step 2: Start Frontend (New Terminal)
```bash
cd /Users/rmtariq/InsightPulse
streamlit run frontend/streamlit_app.py --server.port 8501
```
**Frontend will run on:** http://localhost:8501

### Option 2: Using Start Script
```bash
cd /Users/rmtariq/InsightPulse
python start_app.py
```

## 🔧 Installation Commands (If Needed)

### Install Dependencies
```bash
cd /Users/rmtariq/InsightPulse
pip install -r requirements.txt
```

### Install Additional Dependencies (If Missing)
```bash
pip install streamlit pandas plotly requests fastapi uvicorn openai python-multipart
```

## 📊 Testing the System

### Test Backend Health
```bash
curl -X GET http://localhost:8000/health
```

### Test Smart Crawler Integration
```bash
curl -X POST http://localhost:8000/crawl/smart \
  -H "Content-Type: application/json" \
  -d '{"platforms": ["facebook"], "claim": "SST naik 10%", "max_results_per_platform": 100}'
```

## 🌐 Access URLs

- **Frontend (Streamlit):** http://localhost:8501
- **Backend API:** http://localhost:8000
- **API Documentation:** http://localhost:8000/docs

## 🛠️ Troubleshooting

### Port Already in Use
```bash
# Kill existing processes
pkill -f streamlit
pkill -f uvicorn
pkill -f "python backend/api.py"
```

### Backend Not Starting
```bash
cd /Users/rmtariq/InsightPulse
python -c "import fastapi, uvicorn; print('Dependencies OK')"
```

### Frontend Not Starting
```bash
cd /Users/rmtariq/InsightPulse
python -c "import streamlit, pandas, plotly; print('Dependencies OK')"
```

## 📁 Project Structure
```
InsightPulse/
├── backend/
│   ├── api.py                 # Main FastAPI backend
│   └── data_crawlers/         # Smart crawler integration
├── frontend/
│   └── streamlit_app.py       # Main Streamlit frontend
├── data/
│   └── smart_crawlers/        # Real crawler data
├── requirements.txt           # Dependencies
└── start_app.py              # Automated startup script
```

## 🎯 Usage Examples

### Test Claims to Analyze:
- "SST naik 10%" (Tax increase)
- "Harga getah harian" (Daily rubber prices)
- "BMT bantuan musim tengkujuh" (Agricultural assistance)
- "Produktiviti risda" (RISDA productivity)

### Expected Results:
- ✅ Real data from smart crawlers (4,342+ records from Facebook)
- ✅ Sentiment analysis and insights
- ✅ Multi-platform data collection
- ✅ AI-powered analysis and reporting

## 🔄 Restart Commands

### Full Restart
```bash
# Kill all processes
pkill -f streamlit
pkill -f uvicorn
pkill -f "python backend/api.py"

# Start backend
cd /Users/rmtariq/InsightPulse
python backend/api.py &

# Start frontend
streamlit run frontend/streamlit_app.py --server.port 8501
```

## ✅ Success Indicators

### Backend Running Successfully:
- Console shows: "Uvicorn running on http://127.0.0.1:8000"
- Health check returns: `{"status":"healthy"}`

### Frontend Running Successfully:
- Console shows: "You can now view your Streamlit app in your browser"
- Browser opens to: http://localhost:8501

### Smart Crawlers Working:
- API returns real data (not 0 records)
- Data sources show: facebook, google, news
- Analysis shows actual sentiment and insights

## 📞 Support

If you encounter issues:
1. Check that both services are running on correct ports
2. Verify smart crawler data exists in `/data/smart_crawlers/`
3. Ensure all dependencies are installed
4. Check console logs for error messages
