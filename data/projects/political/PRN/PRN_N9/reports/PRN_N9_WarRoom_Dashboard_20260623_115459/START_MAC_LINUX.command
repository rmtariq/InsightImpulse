#!/bin/bash
cd "$(dirname "$0")"
echo ""
echo " InsightPulse — PRN Negeri Sembilan War Room"
echo "  http://localhost:8080"
echo "  CTRL+C to stop"
echo ""
(sleep 2 && open "http://localhost:8080" 2>/dev/null || xdg-open "http://localhost:8080" 2>/dev/null) &
if command -v python3 &>/dev/null; then
  exec python3 -m http.server 8080
else
  echo "ERROR: python3 required — install from https://python.org"
  read -p "Press ENTER…"
fi
