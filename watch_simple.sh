#!/bin/bash
# Simple analysis monitor - just shows key events

cd /Users/rmtariq/Documents/InsightPulse

echo "🔍 Watching for analysis completion..."
echo "Press Ctrl+C to stop"
echo ""

tail -f backend.log | grep --line-buffered -E "✅|💾|❌|COMBINED|Analysis completed|Collecting data from|Platform" 
