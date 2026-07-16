#!/usr/bin/env bash
# Batch 7 — PAS implisit, UMDAP, anti-PH, Gen Z/Gen Y (automatik via localhost:8001)
set -euo pipefail
cd "$(dirname "$0")/.."
PY=NEImpulse/bin/python3
[ -x "$PY" ] || PY=python3
LOG="$PWD/data/projects/political/PRN/_shared/excel_intel/batch7_crawl_console.log"

echo "=== Batch 7 Discourse Crawl ==="
echo "    Backend: http://localhost:8001"
echo "    Log:     $LOG"
echo ""

if ! curl -sf http://localhost:8001/health >/dev/null 2>&1; then
  echo "⚠️  Backend tidak jalan — start dulu..."
  nohup NEImpulse/bin/python -m uvicorn web_backend.simple_app:app \
    --host 0.0.0.0 --port 8001 >> backend.log 2>&1 </dev/null &
  disown
  for i in $(seq 1 30); do
    curl -sf http://localhost:8001/health >/dev/null 2>&1 && break
    sleep 2
  done
fi

echo "✅ Backend ready"
echo "🚀 Mula Batch 7 (11 run — anggaran 3–6 jam total)"
echo "   Pantau: tail -f $LOG"
echo "   Task:   http://localhost:8001"
echo ""

"$PY" scripts/crawl_prn_batch7_discourse.py "$@" 2>&1 | tee -a "$LOG"
