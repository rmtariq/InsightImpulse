#!/usr/bin/env bash
# Double-click di Mac — publish sahaja (~30 saat, tanpa crawl baru)
set -euo pipefail
ROOT="/Users/rmtariq/Documents/InsightPulse"
cd "$ROOT"
[ -f NEImpulse/bin/activate ] && source NEImpulse/bin/activate
echo ""
echo "══════════════════════════════════════════"
echo " JOHOR — Publish data sedia ada ke War Room"
echo " $(date '+%Y-%m-%d %H:%M:%S')"
echo "══════════════════════════════════════════"
echo ""
./scripts/update_narrative.sh semak
echo ""
echo "Johor: http://localhost:8080/?module=narrative&state=Johor"
echo ""
read -r -p "Tekan Enter untuk tutup…" _
