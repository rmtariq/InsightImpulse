#!/usr/bin/env bash
# Wait for N9 task to finish, then crawl Johor, then analyze
set -euo pipefail
cd "$(dirname "$0")/.."
PY=NEImpulse/bin/python3
N9_TASK="${1:?Usage: wait_then_johor.sh TASK_ID}"

echo "⏳ Waiting for N9 task $N9_TASK ..."
while true; do
  ST=$($PY -c "
import requests, sys
r = requests.get('http://localhost:8001/task_status/$N9_TASK', timeout=120)
d = r.json()
print(d.get('status','unknown'))
" 2>/dev/null || echo "unknown")
  echo "   N9 status: $ST"
  if [ "$ST" = "completed" ]; then break; fi
  if [ "$ST" = "failed" ]; then echo "❌ N9 failed — check backend.log"; exit 1; fi
  sleep 30
done

echo ""
echo "=== Johor crawl ==="
$PY scripts/crawl_prn_broad_3states.py --state Johor --dataset-size 2000 --date-range 7days

echo ""
echo "=== Analyze ==="
$PY scripts/analyze_prn_excel_dun_insights.py || true
$PY scripts/build_warroom_production_bundle.py || true
echo "✅ N9 + Johor update complete"
