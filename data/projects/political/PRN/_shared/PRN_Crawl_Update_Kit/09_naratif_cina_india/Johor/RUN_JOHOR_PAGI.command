#!/usr/bin/env bash
# Double-click di Mac — crawl pagi (N9+Johor+Melaka) + publish
set -euo pipefail
ROOT="/Users/rmtariq/Documents/InsightPulse"
cd "$ROOT"
[ -f NEImpulse/bin/activate ] && source NEImpulse/bin/activate
echo ""
echo "══════════════════════════════════════════"
echo " NARATIF PAGI — 3 Negeri (termasuk Johor)"
echo " $(date '+%Y-%m-%d %H:%M:%S')"
echo "══════════════════════════════════════════"
echo ""
./scripts/update_narrative.sh pagi
echo ""
echo "Johor: http://localhost:8080/?module=narrative&state=Johor"
echo ""
read -r -p "Tekan Enter untuk tutup…" _
