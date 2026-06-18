#!/bin/bash
# InsightPulse War Room + Digital Culaan API (Mac / Linux)

cd "$(dirname "$0")"
ROOT="$(cd ../../../../../../../.. && pwd)"

echo ""
echo " InsightPulse War Room + Culaan Digital"
echo "  http://localhost:8080"
echo "  Culaan: http://localhost:8080/?module=cula"
echo "  CTRL+C to stop"
echo ""

(sleep 2 && (open "http://localhost:8080/?module=cula" 2>/dev/null || xdg-open "http://localhost:8080/?module=cula" 2>/dev/null)) &

if command -v python3 &> /dev/null; then
    exec python3 "$ROOT/scripts/prn_digital_cula_server.py" --port 8080
else
    echo "ERROR: python3 required"
    read -p "Press ENTER..."
fi
