#!/usr/bin/env bash
# PRN Excel Intel → crawl → war room update (N9 focus + optional 3 negeri)
set -euo pipefail
cd "$(dirname "$0")/.."
PY=NEImpulse/bin/python
[ -x "$PY" ] || PY=python3

XLSX="${1:-JITP_2026/Master_File/Terkini_20062026_PRN_N9_Johor_Melaka_Update_2026.xlsx}"
STATE="${PRN_STATE:-N9}"
VIA_API="${PRN_VIA_API:-0}"
LIMIT="${PRN_CRAWL_LIMIT:-0}"

echo "=== PRN Excel Intel War Room Pipeline ==="
echo "Excel: $XLSX | State: $STATE | Limit: ${LIMIT:-all queries}"

echo ""
echo "=== 1/6 Import Excel manifest ==="
$PY scripts/import_prn_excel_intel.py --xlsx "$XLSX"

echo ""
echo "=== 2/6 Crawl berita (RM0) dari Query Templates ==="
CRAWL_ARGS=(--state "$STATE" --max-per-query 25)
if [ "$LIMIT" != "0" ]; then
  CRAWL_ARGS+=(--limit "$LIMIT")
fi
if [ "$VIA_API" = "1" ]; then
  CRAWL_ARGS+=(--via-api --api-limit 5)
  echo "   (InsightPulse API enabled — pastikan ./start_full_app.sh hidup)"
fi
$PY scripts/crawl_prn_excel_intel.py "${CRAWL_ARGS[@]}"

echo ""
echo "=== 3/6 Berita komuniti legacy (N9) ==="
$PY scripts/crawl_prn_n9_news_multilingual.py 2>/dev/null || true

echo ""
echo "=== 4/6 Analisis berita (sentiment) ==="
unset HTTP_PROXY HTTPS_PROXY http_proxy https_proxy ALL_PROXY all_proxy \
  APIFY_PROXY_URL SCRAPLING_PROXY_URL 2>/dev/null || true
$PY scripts/analyze_prn_n9_news.py --keyword-only 2>/dev/null || true

echo ""
echo "=== 5/6 Build socmed per DUN + production bundle ==="
$PY scripts/build_warroom_from_excel_crawl.py
$PY scripts/build_warroom_socmed_by_dun.py 2>/dev/null || true
$PY scripts/build_warroom_production_bundle.py

echo ""
echo "=== 6/6 War room playbook ==="
$PY scripts/n9_war_room.py 2>/dev/null || true

echo ""
echo "✅ Siap!"
echo "   War room: bash scripts/start_prn_warroom_prototype.sh → http://localhost:8080/"
echo "   Crawl CSV: data/projects/political/PRN/PRN_N9/crawls/excel_intel/"
echo "   Manifest:  data/projects/political/PRN/_shared/excel_intel/prn_excel_intel_manifest.json"
echo ""
echo "Socmed FB/X/TikTok penuh:"
echo "   PRN_VIA_API=1 bash scripts/run_prn_excel_warroom.sh"
echo "   atau InsightPulse UI http://localhost:8001 (query dari manifest)"
