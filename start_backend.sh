#!/bin/bash
# InsightPulse Backend Startup Script
# Ensures environment variables are loaded correctly

echo "🚀 Starting InsightPulse Backend..."
echo ""

# Navigate to project directory
cd /Users/rmtariq/Documents/InsightPulse

# Kill existing processes
echo "🧹 Cleaning up existing processes..."
pkill -9 -f "python.*simple_app|uvicorn.*simple_app" 2>/dev/null
lsof -ti:8001 | xargs kill -9 2>/dev/null
sleep 2

# Verify .env file exists
if [ ! -f ".env" ]; then
    echo "❌ ERROR: .env file not found!"
    exit 1
fi

echo "✅ Found .env file"

# Set python path
PYTHON_PATH="/Users/rmtariq/Documents/InsightPulse/NEImpulse/bin/python"

if [ ! -f "$PYTHON_PATH" ]; then
    echo "❌ ERROR: Python not found at $PYTHON_PATH"
    exit 1
fi

echo "✅ Python found: $PYTHON_PATH"

# Verify environment variables can be loaded
echo ""
echo "🔍 Verifying environment variables..."
$PYTHON_PATH -c "
from dotenv import load_dotenv
from pathlib import Path
import os

env_path = Path('.env')
load_dotenv(env_path)

apify_token = os.getenv('APIFY_API_TOKEN')
serpapi_key = os.getenv('SERPAPI_KEY')

print('APIFY_API_TOKEN:', '✅ SET' if apify_token else '❌ NOT SET')
print('SERPAPI_KEY:', '✅ SET' if serpapi_key else '❌ NOT SET')

if not apify_token or not serpapi_key:
    print('')
    print('❌ ERROR: API keys not loaded from .env file!')
    exit(1)
"

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Environment variable check failed!"
    exit 1
fi

echo ""
echo "✅ All environment variables loaded successfully!"
echo ""

# Start backend using uvicorn
echo "🌟 Starting backend server on http://0.0.0.0:8001"
echo ""

# Run in background with nohup
nohup $PYTHON_PATH -m uvicorn web_backend.simple_app:app --host 0.0.0.0 --port 8001 > backend.log 2>&1 &

BACKEND_PID=$!
echo "✅ Backend started with PID: $BACKEND_PID"
echo "📝 Logs: backend.log"
echo ""

# Wait for backend to start
echo "⏳ Waiting for backend to initialize..."
sleep 15

# Check if backend is running
if curl -s http://localhost:8001/health > /dev/null 2>&1; then
    echo "✅ Backend is healthy and ready!"
    echo ""
    echo "🎉 InsightPulse is running at: http://localhost:8001"
    echo ""
    echo "📊 To view logs: tail -f backend.log"
    echo "🛑 To stop: pkill -f 'uvicorn.*simple_app'"
else
    echo "⚠️ Backend may still be initializing..."
    echo "📝 Check logs: tail -f backend.log"
fi
