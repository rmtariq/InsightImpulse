#!/usr/bin/env bash
# Kill old processes → start http://localhost:8001 → crawl N9 broad keywords
set -euo pipefail
cd "$(dirname "$0")/.."
PY=NEImpulse/bin/python3
[ -x "$PY" ] || PY=python3

QUERY='"PRN Negeri Sembilan" OR #prnn9 OR PAS OR UMNO OR BN OR DAP OR PKR OR Amanah OR BERSATU OR PN OR PH OR "Pakatan Harapan" OR Gerakan "Negeri Sembilan" when:7d'

echo "=== 1/3 Kill existing ==="
bash stop_insightpulse.sh 2>/dev/null || true
lsof -ti:8080 2>/dev/null | xargs kill -9 2>/dev/null || true
lsof -ti:8501 2>/dev/null | xargs kill -9 2>/dev/null || true
pkill -f crawl_prn 2>/dev/null || true
pkill -f import_apify 2>/dev/null || true
sleep 1

echo ""
echo "=== 2/3 Start InsightPulse (port 8001) ==="
nohup NEImpulse/bin/python -m uvicorn web_backend.simple_app:app --host 0.0.0.0 --port 8001 >> backend.log 2>&1 </dev/null &
disown
SERVER_PID=$!
echo "   PID: $SERVER_PID"
for i in $(seq 1 30); do
  if curl -sf http://localhost:8001/health >/dev/null 2>&1; then
    echo "   ✅ http://localhost:8001/ is ready"
    break
  fi
  sleep 2
  if [ "$i" -eq 30 ]; then
    echo "   ❌ Server failed — check: tail -50 backend.log"
    exit 1
  fi
done

echo ""
echo "=== 3/3 Start N9 crawl ==="
echo "   Query: ${QUERY:0:80}..."
echo "   Monitor: tail -f backend.log"
echo ""
$PY scripts/crawl_prn_broad_3states.py --state N9 --query "$QUERY" --dataset-size 5000
