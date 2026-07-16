#!/usr/bin/env bash
# Update crawl N9 + Johor — safe queries, 7 days, ~30-45 min each
set -euo pipefail
cd "$(dirname "$0")/.."
PY=NEImpulse/bin/python3
[ -x "$PY" ] || PY=python3

echo "╔══════════════════════════════════════════════════════════╗"
echo "║  PRN UPDATE — N9 + Johor (7 hari, query pendek)           ║"
echo "╚══════════════════════════════════════════════════════════╝"

if ! curl -sf http://localhost:8001/health >/dev/null 2>&1; then
  echo "❌ Start server first:"
  echo "   nohup NEImpulse/bin/python -m uvicorn web_backend.simple_app:app --host 0.0.0.0 --port 8001 >> backend.log 2>&1 </dev/null &"
  exit 1
fi

echo ""
echo "=== 1/2 Negeri Sembilan ==="
$PY scripts/crawl_prn_broad_3states.py --state N9 --dataset-size 2000 --date-range 7days

echo ""
echo "=== 2/2 Johor ==="
$PY scripts/crawl_prn_broad_3states.py --state Johor --dataset-size 2000 --date-range 7days

echo ""
echo "=== Merge + analyze ==="
LATEST=$($PY - <<'PY'
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta, timezone
MYT = __import__('datetime').timezone(__import__('datetime').timedelta(hours=8))
files = list(Path("data/combined").glob("Combined_*.csv"))
files = [f for f in files if "manual_stop" not in f.name]
if not files:
    raise SystemExit(0)
latest = max(files, key=lambda p: p.stat().st_mtime)
# also merge with manual if exists
manual = sorted(Path("data/combined").glob("Combined_manual_stop_*.csv"))
parts = [pd.read_csv(latest, low_memory=False)]
if manual:
    parts.append(pd.read_csv(manual[-1], low_memory=False))
df = pd.concat(parts, ignore_index=True).drop_duplicates(subset=["Platform","ID","Text"], keep="first")
ts = datetime.now(MYT).strftime("%Y%m%d_%H%M%S")
out = Path(f"data/combined/Combined_N9_Johor_update_{ts}.csv")
df.to_csv(out, index=False, encoding="utf-8")
print(out)
PY
)

if [ -n "${LATEST:-}" ] && [ -f "$LATEST" ]; then
  echo "   Merged: $LATEST"
fi

$PY scripts/analyze_prn_excel_dun_insights.py || true
$PY scripts/build_warroom_production_bundle.py || true

echo ""
echo "✅ N9 + Johor update selesai"
echo "   Monitor: tail -f backend.log"
echo "   War room: bash scripts/start_prn_warroom_prototype.sh"
