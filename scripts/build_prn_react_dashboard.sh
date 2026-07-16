#!/usr/bin/env bash
# Build React PRN Monitoring dashboard and deploy into War Room static root (port 8080).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
FRONTEND="$ROOT/frontend"
OUT="$ROOT/data/projects/political/PRN/PRN_N9/reports/war_room/prototype/insightpulse/prn-monitoring"
MANIFEST_SRC="$ROOT/data/projects/political/PRN/_shared/excel_intel/prn_excel_intel_manifest.json"

echo "=== PRN React dashboard → War Room (8080) ==="

if [ ! -d "$FRONTEND/node_modules" ]; then
  echo "Installing frontend dependencies…"
  (cd "$FRONTEND" && npm install)
fi

mkdir -p "$FRONTEND/public/data"
if [ -f "$MANIFEST_SRC" ]; then
  cp "$MANIFEST_SRC" "$FRONTEND/public/data/prn_excel_intel_manifest.json"
  echo "✓ Manifest synced"
else
  echo "⚠ Manifest not found — mock fallback will be used"
fi

(cd "$FRONTEND" && npm run build)

rm -rf "$OUT"
mkdir -p "$OUT"
cp -R "$FRONTEND/dist/"* "$OUT/"
echo "✓ Deployed to prototype/insightpulse/prn-monitoring/"
echo "  URL: http://localhost:8080/insightpulse/prn-monitoring/"
