#!/bin/bash
# ==============================================================================
# 🛑 InsightPulse Stop Script
# ==============================================================================
# This script will stop the InsightPulse backend server
# ==============================================================================

cd /Users/rmtariq/Documents/InsightPulse

echo "🛑 Stopping InsightPulse..."
echo ""

# Check if port 8001 is in use
if lsof -ti:8001 > /dev/null 2>&1; then
    echo "🔍 Found processes running on port 8001:"
    lsof -ti:8001 | while read pid; do
        echo "   - PID: $pid"
    done
    echo ""
    echo "Killing processes..."
    lsof -ti:8001 | xargs kill -9 2>/dev/null
    sleep 1
    echo "✅ InsightPulse stopped successfully!"
else
    echo "ℹ️  No InsightPulse processes found running."
fi

echo ""
echo "================================================"
echo "✅ Done!"
echo "================================================"
