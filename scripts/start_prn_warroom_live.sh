#!/usr/bin/env bash
# Launch PRN Negeri Sembilan War Room LIVE dashboard + APIs.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PORT="${PORT:-8080}"
SERVER_SCRIPT="$ROOT/scripts/prn_digital_cula_server.py"
PY="$ROOT/NEImpulse/bin/python"
[ -x "$PY" ] || PY="$ROOT/n9_chinese_narrative_dashboard/.venv/bin/python"
[ -x "$PY" ] || PY=python3

echo "Syncing PRN N9 live data..."
"$PY" "$ROOT/scripts/refresh_prn_n9_warroom_dashboard.py" 2>/dev/null || {
  "$PY" "$ROOT/scripts/build_warroom_narrative_json.py" 2>/dev/null || true
  "$PY" "$ROOT/scripts/build_warroom_production_bundle.py" >/dev/null || true
  "$PY" "$ROOT/scripts/refresh_prn_n9_warroom_dashboard.py" --skip-build || true
}
"$PY" "$ROOT/scripts/build_n9_ml_predictions.py" 2>/dev/null || true

if lsof -nP -iTCP:"$PORT" -sTCP:LISTEN >/dev/null 2>&1; then
  LISTENER=$(lsof -nP -iTCP:"$PORT" -sTCP:LISTEN 2>/dev/null | awk 'NR==2 {print $1}')
  if pgrep -f "prn_digital_cula_server.py" >/dev/null 2>&1 || [[ "${LISTENER:-}" == python* ]]; then
    echo ""
    echo "✓ PRN War Room LIVE already running on http://localhost:${PORT}"
    echo "  Command Centre: http://localhost:${PORT}/"
    echo "  Action Center:  http://localhost:${PORT}/?module=action&state=N9"
    echo "  Pulse Digital:  http://localhost:${PORT}/?module=pulse&state=N9"
    echo "  Culaan Digital: http://localhost:${PORT}/?module=cula&state=N9"
    echo ""
    echo "Refresh browser (Cmd+Shift+R) to load latest build."
    exit 0
  fi
  echo "Port ${PORT} is already in use by another process."
  echo "Use: PORT=8081 bash scripts/start_prn_warroom_live.sh"
  exit 1
fi

echo "Starting PRN War Room LIVE on http://localhost:${PORT}"
echo "  Command Centre: http://localhost:${PORT}/"
echo "  Action Center:  http://localhost:${PORT}/?module=action&state=N9"
echo "  Pulse Digital:  http://localhost:${PORT}/?module=pulse&state=N9"
echo "  Culaan Digital: http://localhost:${PORT}/?module=cula&state=N9"
exec "$PY" "$SERVER_SCRIPT" --port "$PORT"
#!/usr/bin/env bash
# Launch PRN War Room LIVE dashboard + APIs.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PORT="${PORT:-8080}"
SERVER_SCRIPT="$ROOT/scripts/prn_digital_cula_server.py"
PY="$ROOT/NEImpulse/bin/python"
[ -x "$PY" ] || PY="$ROOT/n9_chinese_narrative_dashboard/.venv/bin/python"
[ -x "$PY" ] || PY=python3

echo "Syncing live narrative + production data (N9)..."
"$PY" "$ROOT/scripts/build_warroom_narrative_json.py" 2>/dev/null || true
"$PY" "$ROOT/scripts/build_warroom_production_bundle.py" || true

if lsof -nP -iTCP:"$PORT" -sTCP:LISTEN >/dev/null 2>&1; then
  LISTENER=$(lsof -nP -iTCP:"$PORT" -sTCP:LISTEN 2>/dev/null | awk 'NR==2 {print $1}')
  if pgrep -f "prn_digital_cula_server.py" >/dev/null 2>&1 || [[ "${LISTENER:-}" == python* ]]; then
    echo ""
    echo "✓ PRN War Room LIVE already running on http://localhost:${PORT}"
    echo "  Command Centre: http://localhost:${PORT}/"
    echo "  Action Center:  http://localhost:${PORT}/?module=action&state=N9"
    echo "  Pulse Digital:  http://localhost:${PORT}/?module=pulse&state=N9"
    echo "  Culaan:         http://localhost:${PORT}/?module=cula&state=N9"
    echo ""
    echo "Dashboard rebuilt — refresh browser (Cmd+Shift+R) to load latest build."
    exit 0
  fi
  echo "Port ${PORT} is already in use by another process."
  echo "Stop it:  lsof -ti:${PORT} | xargs kill"
  echo "Or use:   PORT=8081 bash scripts/start_prn_warroom_live.sh"
  exit 1
fi

echo "Starting PRN War Room LIVE on http://localhost:${PORT}"
echo "  Command Centre: http://localhost:${PORT}/"
echo "  Action Center:  http://localhost:${PORT}/?module=action&state=N9"
echo "  Pulse Digital:  http://localhost:${PORT}/?module=pulse&state=N9"
echo "  Culaan:         http://localhost:${PORT}/?module=cula&state=N9"
exec "$PY" "$SERVER_SCRIPT" --port "$PORT"

