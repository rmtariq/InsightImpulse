#!/bin/bash
# ==============================================================================
# 🚀 InsightPulse Startup Script
# ==============================================================================
# This script will:
# 1. Check if server is already running
# 2. Kill old processes if needed
# 3. Start the InsightPulse backend server
# 4. Open the web interface in your browser
# ==============================================================================

cd /Users/rmtariq/Documents/InsightPulse

echo "🚀 Starting InsightPulse..."
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

# Start the backend server
echo "🔧 Starting backend server..."
nohup NEImpulse/bin/python simple_csv_api.py > csv_api.log 2>&1 &
SERVER_PID=$!

echo "✅ Server started (PID: $SERVER_PID)"
echo ""
echo "⏳ Waiting for server to be ready..."

# Wait for server to be ready
max_attempts=10
attempt=0
while [ $attempt -lt $max_attempts ]; do
    if curl -s http://localhost:8001/health > /dev/null 2>&1; then
        echo "✅ Server is ready!"
        break
    fi
    attempt=$((attempt + 1))
    sleep 1
    echo "   Checking... ($attempt/$max_attempts)"
done

if [ $attempt -eq $max_attempts ]; then
    echo "❌ Server failed to start. Check csv_api.log for errors."
    exit 1
fi

echo ""
echo "================================================"
echo "✅ InsightPulse is NOW RUNNING!"
echo "================================================"
echo ""
echo "📊 Dashboard URL: http://localhost:8001/static/analyze_csv.html"
echo "💻 Server PID: $SERVER_PID"
echo "📝 Logs: csv_api.log"
echo ""
echo "Opening browser..."

# Open browser
sleep 2
open http://localhost:8001/static/analyze_csv.html

echo ""
echo "✅ Done! InsightPulse is ready to use!"
echo ""
echo "To stop the server, run: ./stop_insightpulse.sh"
echo "================================================"
