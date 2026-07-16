#!/usr/bin/env bash
# Start InsightPulse (crawl + analyze) + PRN War Room dashboard, then open both in browser.
set -euo pipefail

ROOT="/Users/rmtariq/Documents/InsightPulse"
cd "$ROOT"

PY="$ROOT/NEImpulse/bin/python"
API_PORT=8001
PRN_PORT=8080
LOG_API="$ROOT/backend.log"
LOG_PRN="$ROOT/data/projects/political/PRN/_shared/excel_intel/prn_warroom.log"

wait_for_url() {
  local url="$1"
  local label="$2"
  local max="${3:-20}"
  local i=0
  while [ "$i" -lt "$max" ]; do
    if curl -sf "$url" >/dev/null 2>&1; then
      echo "   ✅ $label ready"
      return 0
    fi
    i=$((i + 1))
    sleep 1
  done
  echo "   ❌ $label failed to start — check logs"
  return 1
}

echo "🚀 InsightPulse + PRN War Room"
echo ""

# --- 1. InsightPulse backend (port 8001) ---
if curl -sf "http://localhost:${API_PORT}/health" >/dev/null 2>&1; then
  echo "✅ InsightPulse already running → http://localhost:${API_PORT}/"
else
  echo "=== Starting InsightPulse (port ${API_PORT}) ==="
  if lsof -ti:"${API_PORT}" >/dev/null 2>&1; then
    echo "   Clearing stale process on port ${API_PORT}..."
    lsof -ti:"${API_PORT}" | xargs kill -9 2>/dev/null || true
    sleep 1
  fi
  nohup "$PY" -m uvicorn web_backend.simple_app:app \
    --host 0.0.0.0 --port "${API_PORT}" >>"$LOG_API" 2>&1 </dev/null &
  disown
  echo "   Waiting for AI models + server (~15s)..."
  wait_for_url "http://localhost:${API_PORT}/health" "InsightPulse" 25
fi

# --- 2. PRN War Room (port 8080) ---
if curl -sf "http://localhost:${PRN_PORT}/" >/dev/null 2>&1; then
  echo "✅ PRN War Room already running → http://localhost:${PRN_PORT}/"
else
  echo ""
  echo "=== Starting PRN War Room (port ${PRN_PORT}) ==="
  if lsof -ti:"${PRN_PORT}" >/dev/null 2>&1; then
    echo "   Clearing stale process on port ${PRN_PORT}..."
    lsof -ti:"${PRN_PORT}" | xargs kill -9 2>/dev/null || true
    sleep 1
  fi
  echo "   Syncing N9 production bundle..."
  python3 "$ROOT/scripts/build_warroom_production_bundle.py" || true
  bash "$ROOT/scripts/build_prn_react_dashboard.sh" || true
  mkdir -p "$(dirname "$LOG_PRN")"
  nohup python3 "$ROOT/scripts/prn_digital_cula_server.py" --port "${PRN_PORT}" \
    >>"$LOG_PRN" 2>&1 </dev/null &
  disown
  wait_for_url "http://localhost:${PRN_PORT}/" "PRN War Room" 15
fi

echo ""
echo "================================================"
echo "✅ Ready"
echo "================================================"
echo "  InsightPulse app:  http://localhost:${API_PORT}/"
echo "  PRN War Room:      http://localhost:${PRN_PORT}/"
echo "  PRN Intel (React): http://localhost:${PRN_PORT}/insightpulse/prn-monitoring/"
echo "  Digital Culaan:    http://localhost:${PRN_PORT}/?module=cula"
echo ""
echo "  Logs:"
echo "    tail -f $LOG_API"
echo "    tail -f $LOG_PRN"
echo "================================================"

sleep 1
open "http://localhost:${API_PORT}/"
sleep 0.5
open "http://localhost:${PRN_PORT}/"
