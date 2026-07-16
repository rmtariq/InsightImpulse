#!/bin/bash

# =============================================================================
# 🚀 InsightPulse - Easy Startup Script
# =============================================================================

echo "🚀 Starting InsightPulse Application..."
echo ""

# Navigate to project directory
cd /Users/rmtariq/Documents/InsightPulse

# Check if virtual environment exists
if [ ! -d "NEImpulse" ]; then
    echo "❌ Virtual environment 'NEImpulse' not found!"
    echo "Please create it first with: python3 -m venv NEImpulse"
    exit 1
fi

# Activate virtual environment
echo "✅ Activating virtual environment..."
source NEImpulse/bin/activate

# Check if backend file exists
if [ ! -f "web_backend/app.py" ]; then
    echo "❌ Backend file 'web_backend/app.py' not found!"
    exit 1
fi

# Kill any existing process on port 8001
echo "🔄 Checking for existing processes on port 8001..."
lsof -ti:8001 | xargs kill -9 2>/dev/null
sleep 2

echo ""
echo "==================================================================="
echo "🤖 Loading AI Models (this takes 30-60 seconds)..."
echo "==================================================================="
echo "Models to load:"
echo "  - Malay Sentiment (rmtariq/ft-Malay-bert)"
echo "  - English Sentiment (cardiffnlp/twitter-roberta-base-sentiment-latest)"
echo "  - Chinese Sentiment (uer/roberta-base-finetuned-chinanews-chinese)"
echo "  - Multilingual Sentiment (nlptown/bert-base-multilingual-uncased-sentiment)"
echo "  - Emotion Model (rmtariq/multilingual-emotion-classifier)"
echo ""
echo "⏳ Please wait..."
echo "==================================================================="
echo ""

# Start the backend
python -m uvicorn web_backend.app:app --host 0.0.0.0 --port 8001

# This line will only run if the server stops
echo ""
echo "⚠️  Backend server stopped!"
