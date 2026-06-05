#!/bin/bash

# InsightPulse Startup Script
# Simple shell script to start both backend and frontend

echo "🎯 InsightPulse - Quick Start"
echo "=============================="

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

echo "📁 Project directory: $SCRIPT_DIR"

# Check if required files exist
if [ ! -f "backend/api.py" ]; then
    echo "❌ Backend file not found: backend/api.py"
    exit 1
fi

if [ ! -f "frontend/streamlit_app.py" ]; then
    echo "❌ Frontend file not found: frontend/streamlit_app.py"
    exit 1
fi

# Function to start backend
start_backend() {
    echo "🔧 Starting backend on http://localhost:8000..."
    python backend/api.py
}

# Function to start frontend
start_frontend() {
    echo "🖥️ Starting frontend on http://localhost:8501..."
    streamlit run frontend/streamlit_app.py --server.port 8501
}

# Check command line arguments
case "${1:-both}" in
    "backend")
        echo "🚀 Starting backend only..."
        start_backend
        ;;
    "frontend")
        echo "🚀 Starting frontend only..."
        start_frontend
        ;;
    "both"|"")
        echo "🚀 Starting both backend and frontend..."
        echo "📝 Note: Backend will start first, then frontend"
        echo "🌐 Frontend will open at: http://localhost:8501"
        echo "📊 Backend API docs at: http://localhost:8000/docs"
        echo ""
        
        # Start backend in background
        start_backend &
        BACKEND_PID=$!
        
        # Wait a bit for backend to start
        echo "⏳ Waiting for backend to initialize..."
        sleep 5
        
        # Start frontend
        start_frontend
        
        # Clean up background process when script exits
        trap "kill $BACKEND_PID 2>/dev/null" EXIT
        ;;
    *)
        echo "Usage: $0 [backend|frontend|both]"
        echo ""
        echo "Examples:"
        echo "  $0              # Start both (default)"
        echo "  $0 both         # Start both"
        echo "  $0 backend      # Start backend only"
        echo "  $0 frontend     # Start frontend only"
        exit 1
        ;;
esac
