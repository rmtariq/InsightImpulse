#!/usr/bin/env bash
# Crawl 36 DUN N9 — FB + IG + X + TikTok + News via InsightPulse
set -euo pipefail
cd "$(dirname "$0")/.."
PY=NEImpulse/bin/python
[ -x "$PY" ] || PY=python3

XLSX="JITP_2026/Master_File/Terkini_20062026_PRN_N9_Johor_Melaka_Update_2026.xlsx"
CODE="${1:-}"
EXTRA=()

echo "=== N9 · 36 DUN · InsightPulse Socmed Crawl ==="
echo "Excel: $XLSX"
echo "Platform: Facebook, Instagram, X, TikTok, News"
echo ""

if ! curl -sf http://localhost:8001/health >/dev/null 2>&1; then
  echo "❌ InsightPulse tidak hidup."
  echo "   Terminal lain: ./start_full_app.sh"
  echo "   Monitor: tail -f backend.log"
  exit 1
fi

echo "✅ InsightPulse OK (port 8001)"
echo ""

$PY scripts/import_prn_excel_intel.py --xlsx "$XLSX"

if [ -n "$CODE" ]; then
  EXTRA+=(--code "$CODE")
  echo "Mode: 1 kerusi ($CODE)"
else
  echo "Mode: 36 kerusi (sequential, ~15–25 min/kerusi)"
  echo "Anggaran masa penuh: 9–15 jam"
fi

echo ""
echo "Monitor crawl (terminal lain):"
echo "  tail -f backend.log"
echo ""

$PY scripts/crawl_prn_n9_36dun_insightpulse.py --resume "${EXTRA[@]}"

echo ""
echo "Update war room bila crawl siap:"
echo "  $PY scripts/build_warroom_production_bundle.py"
echo "  bash scripts/start_prn_warroom_prototype.sh"
