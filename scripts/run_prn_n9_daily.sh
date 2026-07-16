#!/usr/bin/env bash
# PRN N9 — tugasan harian: crawl → smart analyze → war room → dashboard
set -euo pipefail
cd "$(dirname "$0")/.."
PY=NEImpulse/bin/python
[ -x "$PY" ] || PY=python3

echo "=== 1/5 Berita Komuniti (RSS + Direct + Komen) — RM0 ==="
$PY scripts/crawl_prn_n9_news_multilingual.py || $PY scripts/crawl_prn_n9_news.py || true

echo ""
echo "=== 2/5 Smart Analyze Tier A (direct + komen → sentiment/emotion) ==="
# Elak proxy Apify block HuggingFace — model cache tempatan
unset HTTP_PROXY HTTPS_PROXY http_proxy https_proxy ALL_PROXY all_proxy \
  APIFY_PROXY_URL SCRAPLING_PROXY_URL 2>/dev/null || true
if ! $PY scripts/analyze_prn_n9_news.py; then
  echo "   ↪ ML gagal — keyword fallback (~1 saat)"
  $PY scripts/analyze_prn_n9_news.py --keyword-only || true
fi

echo ""
echo "=== 3/5 Berita Cina (3 negeri) — optional ==="
$PY scripts/crawl_prn_chinese_news.py --negeri "negeri sembilan" 2>/dev/null || true

echo ""
echo "=== 4/5 War Room Hari Ini ==="
$PY scripts/n9_war_room.py

echo ""
echo "=== 5/5 Regenerate dashboard ==="
$PY scripts/generate_prn_n9_dashboard.py

echo ""
echo "✅ Siap!"
echo "   Dashboard: data/projects/political/PRN/PRN_N9/reports/dashboards/prn-negeri-sembilan-dashboard.html"
echo "   WhatsApp:  data/projects/political/PRN/PRN_N9/reports/war_room/n9_hari_ini_whatsapp.txt"
echo "   Analyzed:  data/projects/political/PRN/PRN_N9/crawls/news_analyzed/PRN_N9_News_Analyzed_TierA_*.csv"
echo ""
echo "Socmed (FB/TikTok/X) — buka app: ./start_full_app.sh"
echo "Query: data/projects/political/PRN/PRN_N9/reference/queries/PRN_N9_SOCMED_QUERIES_SIAP_GUNA.txt"
