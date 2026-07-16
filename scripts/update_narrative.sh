#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════
# NARATIF CINA & INDIA — NEGERI SEMBILAN (N9) SAHAJA
# Crawl (opsyen) → build dataset → publish War Room + dashboard Agentic
#
# GUNA SETIAP HARI (2× disyorkan: pagi + petang):
#   ./scripts/update_narrative.sh              ← publish sahaja
#   ./scripts/update_narrative.sh pagi         ← crawl pagi N9 + publish
#   ./scripts/update_narrative.sh petang      ← crawl petang N9 + publish
#
# Lain:
#   ./scripts/update_narrative.sh penuh        ← crawl penuh N9 + India N9
#   ./scripts/update_narrative.sh dashboard    ← regenerate HTML Agentic sahaja
#   ./scripts/update_narrative.sh bantuan
# ═══════════════════════════════════════════════════════════════════════════
set -euo pipefail
cd "$(dirname "$0")/.."
ROOT="$(pwd)"

PY=NEImpulse/bin/python
[ -x "$PY" ] || PY=n9_chinese_narrative_dashboard/.venv/bin/python
[ -x "$PY" ] || PY=python3

# Default: Negeri Sembilan only
DEFAULT_NEGERI="negeri sembilan"

MODE="${1:-semak}"
EXTRA=()
shift || true
for arg in "$@"; do
  [[ "$arg" == \#* ]] && break
  EXTRA+=("$arg")
done

banner() {
  echo ""
  echo "════════════════════════════════════════════════════════════"
  echo " Naratif Cina & India · NEGERI SEMBILAN SAHAJA"
  echo " $(date '+%Y-%m-%d %H:%M:%S')"
  echo "════════════════════════════════════════════════════════════"
}

sync_update_kit() {
  local KIT_REPO="$ROOT/data/projects/political/PRN/_shared/PRN_Crawl_Update_Kit"
  local KIT_DESKTOP="$HOME/Desktop/PRN_Johor_N9_Crawl_Update_Kit"
  [ -d "$KIT_REPO" ] || return 0
  if [ ! -d "$KIT_DESKTOP" ]; then
    echo "   (Kit Desktop tidak dijumpai — skip sync)"
    return 0
  fi
  mkdir -p "$KIT_DESKTOP/09_naratif_cina_india/N9" "$KIT_DESKTOP/06_pautan"
  cp -R "$KIT_REPO/09_naratif_cina_india/"* "$KIT_DESKTOP/09_naratif_cina_india/" 2>/dev/null || true
  cp "$KIT_REPO/README.txt" "$KIT_DESKTOP/README.txt" 2>/dev/null || true
  cp "$KIT_REPO/00_MULA_DI_SINI.txt" "$KIT_DESKTOP/00_MULA_DI_SINI.txt" 2>/dev/null || true
  echo "   Kit Desktop dikemas: $KIT_DESKTOP/09_naratif_cina_india/"
}

regen_dashboard() {
  echo ""
  echo "▶ Jana dashboard Agentic N9…"
  $PY scripts/analyze_naratif_agentic.py --no-llm
  echo "   HTML: data/projects/political/PRN/reports/naratif_cina_india/naratif_cina_india_johor_n9_dashboard.html"
}

publish() {
  echo ""
  echo "▶ Bina dataset + export JSON War Room (N9)…"
  $PY scripts/build_warroom_narrative_json.py --rebuild-dataset
  echo ""
  echo "▶ Sync bundle War Room (N9)…"
  $PY scripts/build_warroom_production_bundle.py 2>/dev/null || true
  regen_dashboard
}

crawl_chinese() {
  local slot="$1"
  local negeri="${2:-$DEFAULT_NEGERI}"
  echo ""
  echo "▶ Crawl berita Cina — slot: $slot · negeri: $negeri (percuma, tiada Apify)…"
  local args=(--slot "$slot" --news-only --negeri "$negeri")
  $PY scripts/crawl_prn_chinese_daily.py "${args[@]}" "${EXTRA[@]+"${EXTRA[@]}"}"
}

crawl_indian() {
  echo ""
  echo "▶ Crawl naratif India/Tamil — Negeri Sembilan sahaja…"
  $PY scripts/crawl_prn_indian_narrative.py --negeri "negeri sembilan"
}

open_hint() {
  sync_update_kit
  echo ""
  echo "✅ SIAP — data N9 live"
  echo ""
  echo "   Dashboard Agentic:"
  echo "   file://$ROOT/data/projects/political/PRN/reports/naratif_cina_india/naratif_cina_india_johor_n9_dashboard.html"
  echo ""
  echo "   War Room Modul #6: http://localhost:8080/?module=narrative"
  echo "   Hard refresh: Cmd+Shift+R"
  echo ""
}

banner

case "$MODE" in
  bantuan|help|-h|--help)
    echo ""
    echo "FOKUS: Negeri Sembilan (N9) sahaja — Johor dibuang dari pipeline harian."
    echo ""
    echo "CADANGAN HARIAN (2× sehari):"
    echo "  Pagi   → ./scripts/update_narrative.sh pagi"
    echo "  Petang → ./scripts/update_narrative.sh petang"
    echo ""
    echo "Crawl penuh + rebuild dashboard:"
    echo "  ./scripts/update_narrative.sh penuh"
    echo ""
    echo "Publish / regenerate sahaja:"
    echo "  ./scripts/update_narrative.sh"
    echo "  ./scripts/update_narrative.sh dashboard"
    echo ""
    echo "Legacy (jika perlu Johor sekali-sekala):"
    echo "  ./scripts/update_narrative.sh johor"
    echo ""
    exit 0
    ;;
  semak|publish|refresh|kemas)
    publish
    open_hint
    ;;
  dashboard|html|agentic)
    regen_dashboard
    open_hint
    ;;
  pagi|morning)
    crawl_chinese morning
    crawl_indian
    publish
    open_hint
    ;;
  tengah|midday)
    crawl_chinese midday
    publish
    open_hint
    ;;
  petang|evening)
    crawl_chinese evening
    crawl_indian
    publish
    open_hint
    ;;
  penuh|full|news|n9|n9-penuh)
    crawl_chinese full
    crawl_indian
    publish
    open_hint
    ;;
  johor|johor-penuh)
    echo ""
    echo "▶ Mod legacy Johor (bukan default)…"
    crawl_chinese full johor
    crawl_chinese midday johor
    $PY scripts/crawl_prn_indian_narrative.py --negeri johor
    $PY scripts/build_warroom_narrative_json.py --rebuild-dataset
    echo "⚠️ Dashboard Agentic kekal N9-only — tidak diganti dengan data Johor."
    open_hint
    ;;
  crawl)
    crawl_chinese "${EXTRA[0]:-morning}"
    crawl_indian
    echo ""
    echo "✅ Crawl N9 selesai. Seterusnya: ./scripts/update_narrative.sh semak"
    ;;
  laporan|reports)
    publish
    echo ""
    echo "▶ Jana laporan PDF/DOCX…"
    $PY scripts/generate_prn_chinese_narrative_reports.py 2>/dev/null || true
    open_hint
    ;;
  *)
    echo "❌ Mod tidak dikenali: $MODE"
    echo "   Guna: semak | pagi | tengah | petang | penuh | dashboard | bantuan"
    exit 1
    ;;
esac
