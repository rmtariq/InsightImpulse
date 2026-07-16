#!/usr/bin/env bash
# Double-click di Mac — crawl penuh naratif Cina + India Johor → War Room
set -euo pipefail
ROOT="/Users/rmtariq/Documents/InsightPulse"
cd "$ROOT"
[ -f NEImpulse/bin/activate ] && source NEImpulse/bin/activate
echo ""
echo "══════════════════════════════════════════"
echo " JOHOR — Naratif Cina & India (PENUH)"
echo " $(date '+%Y-%m-%d %H:%M:%S')"
echo "══════════════════════════════════════════"
echo ""
./scripts/update_narrative.sh johor
echo ""
echo "Buka: http://localhost:8080/?module=narrative&state=Johor"
echo ""
read -r -p "Tekan Enter untuk tutup…" _
