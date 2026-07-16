#!/usr/bin/env bash
# PRN 2-FASA: (1) Broad crawl banyak data → (2) Analitik 36 DUN dari Excel
set -euo pipefail
cd "$(dirname "$0")/.."
PY=NEImpulse/bin/python
[ -x "$PY" ] || PY=python3

XLSX="JITP_2026/Master_File/Terkini_20062026_PRN_N9_Johor_Melaka_Update_2026.xlsx"
PHASE="${1:-all}"

echo "╔══════════════════════════════════════════════════════════╗"
echo "║  PRN 2-FASA PIPELINE                                     ║"
echo "║  Excel: Terkini_20062026                                 ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

if ! curl -sf http://localhost:8001/health >/dev/null 2>&1; then
  echo "❌ InsightPulse mesti hidup: ./start_full_app.sh"
  exit 1
fi

echo "=== Import Excel manifest ==="
$PY scripts/import_prn_excel_intel.py --xlsx "$XLSX"

if [ "$PHASE" = "1" ] || [ "$PHASE" = "all" ]; then
  echo ""
  echo "=== FASA 1: Broad crawl (banyak data) — 3 negeri ==="
  echo "    Platform: FB + IG + X + TikTok + News"
  echo "    Dataset: 5000/negeri · Monitor: tail -f backend.log"
  echo ""
  $PY scripts/crawl_prn_broad_3states.py --dataset-size 5000
fi

if [ "$PHASE" = "2" ] || [ "$PHASE" = "all" ]; then
  echo ""
  echo "=== FASA 2: Analitik + insight per 36 DUN (Excel mapping) ==="
  $PY scripts/analyze_prn_excel_dun_insights.py
  $PY scripts/build_warroom_production_bundle.py
  echo ""
  echo "✅ War room data updated"
  echo "   bash scripts/start_prn_warroom_prototype.sh → http://localhost:8080/"
fi

echo ""
echo "Keywords rujukan: data/projects/political/PRN/_shared/excel_intel/PRN_BROAD_CRAWL_QUERIES.txt"
