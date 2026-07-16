#!/bin/bash
# ==============================================================================
# 🚀 InsightPulse FULL APP Startup Script
# ==============================================================================
# This script will start the COMPLETE InsightPulse application with:
# 1. Keyword crawling (Facebook, Instagram, TikTok, X, News, etc.)
# 2. Real-time analysis with AI
# 3. Full dashboard with sentiment, emotion, and strategic insights
# ==============================================================================

cd /Users/rmtariq/Documents/InsightPulse

echo "🚀 Starting InsightPulse FULL Application..."
echo ""
echo "Features:"
echo "  ✅ Multi-platform keyword crawling"
echo "  ✅ Real-time sentiment & emotion analysis"
echo "  ✅ AI-powered strategic insights"
echo "  ✅ Platform: Facebook, Instagram, TikTok, X, News, E-commerce"
echo ""

# Check if port 8001 is already in use
if lsof -ti:8001 > /dev/null 2>&1; then
    echo "⚠️  Port 8001 is already in use. Killing old processes..."
    lsof -ti:8001 | xargs kill -9 2>/dev/null
    sleep 2
    echo "✅ Old processes killed"
fi

# Ensure index.html exists
if [ ! -f "web_frontend/index.html" ]; then
    echo "📝 Creating index.html..."
    cp web_frontend/simple_index.html web_frontend/index.html
fi

# Start the FULL backend server (simple_app.py) with output to log
echo "🔧 Starting full backend server (with crawling capabilities)..."
echo "📝 Loading AI models (this takes ~15 seconds)..."

# Start in background (</dev/null prevents zsh "suspended (tty output)")
nohup NEImpulse/bin/python -m uvicorn web_backend.simple_app:app --host 0.0.0.0 --port 8001 >> backend.log 2>&1 </dev/null &
disown
SERVER_PID=$!

echo "✅ Server started (PID: $SERVER_PID)"
echo ""
echo "⏳ Waiting for server to be ready (AI models may take 30–60s)..."

# Wait for server to be ready (model load on MPS can exceed 15s)
max_attempts=60
attempt=0
while [ $attempt -lt $max_attempts ]; do
    if curl -s http://localhost:8001/health > /dev/null 2>&1; then
        echo "✅ Server is ready!"
        break
    fi
    attempt=$((attempt + 1))
    sleep 2
    if [ $((attempt % 5)) -eq 0 ]; then
        echo "   Still loading models... ($((attempt * 2))s)"
    fi
done

if [ $attempt -eq $max_attempts ]; then
    echo "❌ Server failed to start. Check backend.log for errors."
    echo ""
    echo "To view logs:"
    echo "  tail -50 backend.log"
    exit 1
fi

echo ""
echo "================================================"
echo "✅ InsightPulse FULL APP is NOW RUNNING!"
echo "================================================"
echo ""
echo "🌐 Main Dashboard: http://localhost:8001/"
echo "📊 CSV Analyzer:   http://localhost:8001/static/analyze_csv.html"
echo "💻 Server PID:     $SERVER_PID"
echo "📝 Logs:           backend.log"
echo ""
echo "Opening main dashboard..."

# Open browser to main app
sleep 2
open http://localhost:8001/

echo ""
echo "✅ Done! InsightPulse is ready to use!"
echo ""
echo "📋 What you can do:"
echo "  1. Enter keywords to crawl social media"
echo "  2. Select platforms (Facebook, Instagram, TikTok, X, News)"
echo "  3. Get real-time analysis with AI insights"
echo "  4. View sentiment, emotion, and strategic recommendations"
echo ""
echo "To stop the server, run: ./stop_insightpulse.sh"
echo "================================================"
