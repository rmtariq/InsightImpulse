#!/usr/bin/env bash
# Launch PRN War Room prototype + Digital Culaan API (N9, Johor, Melaka)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PORT="${PORT:-8080}"
SERVER_SCRIPT="$ROOT/scripts/prn_digital_cula_server.py"
PY="$ROOT/NEImpulse/bin/python"
[ -x "$PY" ] || PY="$ROOT/n9_chinese_narrative_dashboard/.venv/bin/python"
[ -x "$PY" ] || PY=python3

echo "Syncing narrative + production data (N9)..."
"$PY" "$ROOT/scripts/refresh_prn_n9_warroom_dashboard.py" --skip-build 2>/dev/null || {
  "$PY" "$ROOT/scripts/build_warroom_narrative_json.py" 2>/dev/null || true
  "$PY" "$ROOT/scripts/build_warroom_production_bundle.py" || true
  "$PY" "$ROOT/scripts/refresh_prn_n9_warroom_dashboard.py" --skip-build || true
}
# PRN Intel (Excel monitoring) — HQ sahaja; bukan dalam sidebar War Room
# Jalankan manual jika perlu: bash scripts/build_prn_react_dashboard.sh

if lsof -nP -iTCP:"$PORT" -sTCP:LISTEN >/dev/null 2>&1; then
  LISTENER=$(lsof -nP -iTCP:"$PORT" -sTCP:LISTEN 2>/dev/null | awk 'NR==2 {print $1}')
  if pgrep -f "prn_digital_cula_server.py" >/dev/null 2>&1 || [[ "${LISTENER:-}" == python* ]]; then
    echo ""
    echo "✓ War Room already running on http://localhost:${PORT}"
    echo "  War Room:     http://localhost:${PORT}/"
    echo "  Modul Culaan: http://localhost:${PORT}/?module=cula"
    echo "  Naratif C/I:  http://localhost:${PORT}/?module=narrative"
    echo ""
    echo "Dashboard rebuilt — refresh browser (Cmd+Shift+R) to load latest build."
    exit 0
  fi
  echo "⚠ Port ${PORT} is already in use by another process."
  echo "  Stop it:  lsof -ti:${PORT} | xargs kill"
  echo "  Or use:   PORT=8081 bash scripts/start_prn_warroom_prototype.sh"
  exit 1
fi

echo "Starting War Room + Digital Culaan API on http://localhost:${PORT}"
echo "  War Room:     http://localhost:${PORT}/"
echo "  Modul Culaan: http://localhost:${PORT}/?module=cula"
echo "  Naratif C/I:  http://localhost:${PORT}/?module=narrative"
exec "$PY" "$SERVER_SCRIPT" --port "$PORT"
