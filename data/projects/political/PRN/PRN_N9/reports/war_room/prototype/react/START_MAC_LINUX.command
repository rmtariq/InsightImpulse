#!/bin/bash
# ============================================================
#  InsightPulse War Room - Local Launcher (Mac / Linux)
# ============================================================
#  Double-click this file to start the War Room.
#  Mac may ask "cannot be opened because it is from an
#  unidentified developer" - right-click and choose Open.
# ============================================================

cd "$(dirname "$0")"

echo ""
echo " ============================================================"
echo "  InsightPulse War Room - Starting local server..."
echo " ============================================================"
echo ""
echo "  Open your browser at:  http://localhost:8080"
echo ""
echo "  Press CTRL+C to stop the server when done."
echo " ============================================================"
echo ""

# Try opening browser automatically after 2 seconds
(sleep 2 && (open http://localhost:8080 2>/dev/null || xdg-open http://localhost:8080 2>/dev/null)) &

# Try Python 3 first, then Python 2 as fallback
if command -v python3 &> /dev/null; then
    python3 -m http.server 8080
elif command -v python &> /dev/null; then
    python -m SimpleHTTPServer 8080
else
    echo ""
    echo " ERROR: Python not found. Install from https://python.org"
    echo " Or run: npx serve -p 8080  (if Node.js is installed)"
    echo ""
    read -p "Press ENTER to close..."
fi
