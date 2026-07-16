#!/usr/bin/env bash
# Refresh InsightPulse project dashboard package (stats + optional dashboard HTML)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

PROJECT="${1:-}"
if [[ -z "$PROJECT" ]]; then
  echo "Usage: $0 <project_id>"
  echo "Examples: smebank | PRN_N9 | mbjb"
  exit 1
fi

echo "==> InsightPulse refresh for project: $PROJECT"

case "$PROJECT" in
  smebank)
    if [[ -f scripts/build_smebank_dashboard_stats.py ]]; then
      python3 scripts/build_smebank_dashboard_stats.py || true
    fi
    echo "Dashboard: JITP_2026/SMEBank_InsightPulse_Dashboard.html"
    ;;
  PRN_N9|prn_n9)
    bash scripts/build_warroom_production_bundle.py || true
    echo "War room: data/projects/political/PRN/PRN_N9/reports/war_room/prototype/"
    ;;
  mbjb|kdebwm)
    echo "Agency project — run latest report analysis or open reports/*mbjb* dashboard"
    ;;
  *)
    echo "Generic project refresh — promote latest combined CSV to project master if available"
    ;;
esac

echo "Done."
