#!/usr/bin/env bash
# Tunggu task siap → sambung run seterusnya (Batch 7)
set -euo pipefail
cd "$(dirname "$0")/.."
PY=NEImpulse/bin/python3
LOG="$PWD/data/projects/political/PRN/_shared/excel_intel/batch7_crawl_console.log"

WAIT_TASK="${1:-47602874-e014-4a5c-9d9a-3bc53b3fc249}"
NEXT_RUN="${2:-C}"

echo "⏳ Tunggu task $WAIT_TASK siap..."
while true; do
  ST=$($PY - <<PY
import requests, json
try:
    r = requests.get("http://localhost:8001/task_status/$WAIT_TASK", timeout=180)
    print(json.dumps(r.json()))
except Exception as e:
    print(json.dumps({"status": "pending", "error": str(e)}))
PY
)
  STATUS=$(echo "$ST" | $PY -c "import sys,json; print(json.load(sys.stdin).get('status','?'))")
  echo "   $(date +%H:%M:%S) — $WAIT_TASK: $STATUS"
  if [ "$STATUS" = "completed" ] || [ "$STATUS" = "failed" ]; then
    break
  fi
  sleep 30
done

echo "✅ Task $STATUS — mula Run $NEXT_RUN → L"
"$PY" -u scripts/crawl_prn_batch7_discourse.py --from-run "$NEXT_RUN" 2>&1 | tee -a "$LOG"
