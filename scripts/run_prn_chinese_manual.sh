#!/usr/bin/env bash
# PRN Chinese Narrative — MANUAL crawl runner (tiada cron / tiada auto)
# Anda jalankan bila sedia · pantau terminal sendiri
#
# Usage:
#   ./scripts/run_prn_chinese_manual.sh morning       # news batch pagi
#   ./scripts/run_prn_chinese_manual.sh midday        # news batch tengah hari
#   ./scripts/run_prn_chinese_manual.sh evening       # news batch petang
#   ./scripts/run_prn_chinese_manual.sh news          # semua news percuma
#   ./scripts/run_prn_chinese_manual.sh full          # semua 17 stream (news)
#   ./scripts/run_prn_chinese_manual.sh morning socmed  # + FB/X (kos Apify — sengaja)
#   ./scripts/run_prn_chinese_manual.sh rebuild       # dashboard sahaja, tanpa crawl
#   ./scripts/run_prn_chinese_manual.sh list          # senarai stream
set -euo pipefail
cd "$(dirname "$0")/.."

PY=NEImpulse/bin/python
[ -x "$PY" ] || PY=n9_chinese_narrative_dashboard/.venv/bin/python
[ -x "$PY" ] || PY=python3

ACTION="${1:-help}"
EXTRA=()
shift || true

for arg in "$@"; do
  # zsh (tanpa interactivecomments) hantar "# ..." sebagai arg — abaikan
  [[ "$arg" == \#* ]] && break
  case "$arg" in
    socmed)   EXTRA+=(--with-socmed) ;;
    api)      EXTRA+=(--via-api) ;;
    full)     EXTRA+=(--full-size) ;;
    rebuild)  EXTRA+=(--rebuild) ;;
    ''|help|-h|--help) ;;
    morning|midday|evening|full|tinggi|news|list|build) ;;
    *)        EXTRA+=("$arg") ;;
  esac
done

echo "════════════════════════════════════════════════════════════"
echo " PRN Chinese Narrative — MANUAL RUN"
echo " $(date '+%Y-%m-%d %H:%M:%S')  |  anda jalankan · anda pantau"
echo "════════════════════════════════════════════════════════════"

case "$ACTION" in
  list)
    $PY scripts/crawl_prn_chinese_daily.py --list
    ;;
  rebuild|build)
    $PY scripts/build_prn_chinese_dashboard_dataset.py
    echo ""
    echo "Dashboard: cd n9_chinese_narrative_dashboard && streamlit run app.py"
    ;;
  reports|laporan)
    $PY scripts/generate_prn_chinese_narrative_reports.py ${EXTRA[@]+"${EXTRA[@]}"}
    ;;
  help|-h|--help)
    echo ""
    echo "Arahan penuh: data/projects/political/pas_break_2026/reference/PROSES_DASHBOARD_DAN_LAPORAN.txt"
    echo ""
    echo "  ./scripts/run_prn_chinese_manual.sh morning"
    echo "  ./scripts/run_prn_chinese_manual.sh midday"
    echo "  ./scripts/run_prn_chinese_manual.sh evening"
    echo "  ./scripts/run_prn_chinese_manual.sh news"
    echo "  ./scripts/run_prn_chinese_manual.sh morning socmed"
    echo "  ./scripts/run_prn_chinese_manual.sh rebuild"
    echo "  ./scripts/run_prn_chinese_manual.sh reports"
    echo "  ./scripts/run_prn_chinese_manual.sh list"
    echo ""
    echo "Nota zsh: jangan letak # di hujung baris command (zsh anggap bukan komen)."
    ;;
  news)
    $PY scripts/crawl_prn_chinese_daily.py --slot full --news-only ${EXTRA[@]+"${EXTRA[@]}"}
    ;;
  *)
    SLOT="$ACTION"
    if [[ "$SLOT" != "morning" && "$SLOT" != "midday" && "$SLOT" != "evening" && "$SLOT" != "full" && "$SLOT" != "tinggi" ]]; then
      echo "❌ Slot tidak dikenali: $SLOT"
      echo "   Guna: morning | midday | evening | full | news | rebuild | list | help"
      exit 1
    fi
    # Default: news sahaja — socmed hanya jika anda tambah arg 'socmed'
    if [[ " ${EXTRA[*]+"${EXTRA[*]}"} " != *" --with-socmed "* && " ${EXTRA[*]+"${EXTRA[*]}"} " != *" --via-api "* ]]; then
      EXTRA+=(--news-only)
    fi
    $PY scripts/crawl_prn_chinese_daily.py --slot "$SLOT" ${EXTRA[@]+"${EXTRA[@]}"}
    ;;
esac

echo ""
echo "✅ Langkah selesai."
case "$ACTION" in
  reports|laporan)
    echo "   Laporan: data/projects/political/pas_break_2026/reports/chinese_narrative/"
    ;;
  rebuild|build)
    echo "   Dashboard: cd n9_chinese_narrative_dashboard && streamlit run app.py"
    ;;
  *)
    echo "   Seterusnya: ./scripts/run_prn_chinese_manual.sh rebuild"
    echo "   Laporan:    ./scripts/run_prn_chinese_manual.sh reports"
    ;;
esac
echo "   Panduan: data/projects/political/pas_break_2026/reference/PROSES_DASHBOARD_DAN_LAPORAN.txt"
