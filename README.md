# 🎯 InsightPulse - Universal Analysis Platform

**Clean, Essential Version - Only Core Files**

## 🚀 Quick Start

```bash
# Start the application
python start_app.py
```

## 📁 Project Structure

```
InsightPulse/
├── frontend/
│   └── streamlit_app.py          # Main Streamlit frontend
├── backend/
│   ├── api.py                    # FastAPI backend with all endpoints
│   └── data_crawlers/            # Smart crawler integration
├── data/                         # Crawler data storage
│   ├── smart_crawlers/           # Real crawler results
│   ├── raw/                      # Raw data
│   ├── processed/                # Processed data
│   └── reports/                  # Generated reports
├── requirements.txt              # Dependencies
├── start_app.py                  # App launcher
└── README.md                     # This file
```

## 🎯 Features

- **Universal Input**: Analyze any claim/issue in natural language
- **AI Keywords**: Dynamic keyword generation using OpenAI GPT-4
- **Smart Crawling**: Real data collection from social media platforms
- **Real-time Analysis**: Sentiment analysis and insights
- **Report Generation**: Downloadable analysis reports

## 🔧 Dependencies

- Streamlit (Frontend)
- FastAPI (Backend)
- OpenAI (AI Keywords)
- Smart Crawlers (Data Collection)
- Plotly (Visualizations)

## 🌐 Endpoints

- Frontend: http://localhost:8501
- Backend API: http://localhost:8002
- Health Check: http://localhost:8002/health

## 📊 Workflow

1. **Input** - Enter claim/issue
2. **Keywords** - AI generates smart keywords  
3. **Crawling** - Collect real data from platforms
4. **Detection** - AI analyzes content and sentiment
5. **Analysis** - Generate insights and visualizations
6. **Report** - Download comprehensive report

---
*Clean version - All unnecessary files removed*
