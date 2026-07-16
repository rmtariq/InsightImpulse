#!/usr/bin/env bash
# Restart InsightPulse backend (port 8001) with latest code including ML routes.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PORT="${PORT:-8001}"
PY="$ROOT/NEImpulse/bin/python"
[ -x "$PY" ] || PY="$ROOT/n9_chinese_narrative_dashboard/.venv/bin/python"
[ -x "$PY" ] || PY=python3

echo "Stopping anything on port ${PORT}..."
lsof -ti:"$PORT" 2>/dev/null | xargs kill -9 2>/dev/null || true
sleep 2

echo "Starting InsightPulse backend on http://127.0.0.1:${PORT}"
cd "$ROOT"
nohup "$PY" -m uvicorn web_backend.simple_app:app --host 0.0.0.0 --port "$PORT" >> backend.log 2>&1 &

echo "Waiting for startup (HF models may take 30–90s)..."
for i in $(seq 1 60); do
  if curl -sf "http://127.0.0.1:${PORT}/health" >/dev/null 2>&1; then
    echo ""
    echo "✓ Backend ready: http://127.0.0.1:${PORT}"
    if curl -sf "http://127.0.0.1:${PORT}/api/ml/predict/prn_n9" >/dev/null 2>&1; then
      echo "✓ ML endpoint:   http://127.0.0.1:${PORT}/api/ml/predict/prn_n9"
    else
      echo "⚠ ML endpoint not yet available — check backend.log (may still be loading models)"
    fi
    exit 0
  fi
  sleep 2
done

echo "⚠ Backend did not respond within 120s — check: tail -f $ROOT/backend.log"
exit 1
