#!/usr/bin/env bash
# Package PRN Negeri Sembilan War Room dashboard for offline sharing.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PROTO="$ROOT/data/projects/political/PRN/PRN_N9/reports/war_room/prototype"
OUT_DIR="$ROOT/data/projects/political/PRN/PRN_N9/reports"
STAMP="$(date +%Y%m%d_%H%M%S)"
PKG_NAME="PRN_N9_WarRoom_Dashboard_${STAMP}"
PKG_ROOT="$OUT_DIR/${PKG_NAME}"

echo "📦 Packaging PRN N9 War Room dashboard…"

# Optional: refresh production JSON before packaging
if [[ "${SKIP_REBUILD:-0}" != "1" ]]; then
  echo "   Rebuilding production bundle…"
  python3 "$ROOT/scripts/build_warroom_production_bundle.py" >/dev/null
fi

rm -rf "$PKG_ROOT"
mkdir -p "$PKG_ROOT/js" "$PKG_ROOT/data"

cp "$PROTO/index.html" "$PKG_ROOT/"
cp "$PROTO/js/"*.js "$PKG_ROOT/js/"

N9_DATA=(
  warroom_dun_N9_production.json
  warroom_dun_N9.json
  n9_production_bundle.json
  n9_social_summary.json
  war_room_intel_N9.json
  pas_target_16_N9.json
  pas_target_23_N9.json
  socmed_by_dun_N9.json
  cula_hub_N9.json
  cula_socmed_hub_N9.json
  n9_narrative_community.json
  n9_dpi_updates.json
  n9_dun_seats.json
  dosm_census_johor_n9.json
  warroom_dun_meta.json
)

for f in "${N9_DATA[@]}"; do
  if [[ -f "$PROTO/data/$f" ]]; then
    cp "$PROTO/data/$f" "$PKG_ROOT/data/"
  else
    echo "   ⚠ Missing (skipped): data/$f"
  fi
done

cat > "$PKG_ROOT/START_MAC_LINUX.command" << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
echo ""
echo " InsightPulse — PRN Negeri Sembilan War Room"
echo "  http://localhost:8080"
echo "  CTRL+C to stop"
echo ""
(sleep 2 && open "http://localhost:8080" 2>/dev/null || xdg-open "http://localhost:8080" 2>/dev/null) &
if command -v python3 &>/dev/null; then
  exec python3 -m http.server 8080
else
  echo "ERROR: python3 required — install from https://python.org"
  read -p "Press ENTER…"
fi
EOF
chmod +x "$PKG_ROOT/START_MAC_LINUX.command"

cat > "$PKG_ROOT/START_WINDOWS.bat" << 'EOF'
@echo off
cd /d "%~dp0"
echo.
echo  InsightPulse — PRN Negeri Sembilan War Room
echo  http://localhost:8080
echo  Press CTRL+C to stop
echo.
start "" "http://localhost:8080"
python -m http.server 8080 2>nul || py -3 -m http.server 8080 2>nul || (
  echo ERROR: Python not found. Install from https://python.org
  pause
)
EOF

GENERATED="$(date '+%Y-%m-%d %H:%M:%S %Z')"
cat > "$PKG_ROOT/README.txt" << EOF
============================================================
  InsightPulse — PRN Negeri Sembilan War Room Dashboard
  Pakej perkongsian · N9 sahaja
============================================================

Dijana: ${GENERATED}

MODUL TERMASUK (7):
  1. Command Centre      — KPI strategik + senario MN/PAS solo
  2. DUN Drill-Down      — Peta 36 kerusi + drawer analitik
  3. Rapid Response      — Amaran + templat respons
  4. Daily Briefing      — Ringkasan harian
  5. Polling Day Mode    — Mod hari mengundi
  6. Naratif Cina & India — Pemantauan komuniti
  7. Culaan Digital      — Paparan data lapangan (baca sahaja tanpa API)

CARA BUKA:
  MAC:     Right-click START_MAC_LINUX.command → Open
  WINDOWS: Double-click START_WINDOWS.bat
  MANUAL:  python3 -m http.server 8080
           kemudian buka http://localhost:8080

NOTA:
  • Pakej ini LOCKED untuk Negeri Sembilan (36 DUN).
  • Perlukan sambungan internet untuk fon & peta Leaflet (CDN).
  • Modul Culaan: hantar borang perlukan server penuh InsightPulse
    (bukan termasuk dalam zip ini) — paparan data sedia ada masih berfungsi.
  • Refresh data: hubungi pasukan InsightPulse untuk bundle terkini.

Pautan pantas:
  Command Centre:  http://localhost:8080/
  Naratif C/I:     http://localhost:8080/?module=narrative&state=N9
  DUN Drill-Down:  http://localhost:8080/?module=dun&state=N9

============================================================
  InsightPulse  |  AI Social Listening Platform
============================================================
EOF

cd "$OUT_DIR"
ZIP_FILE="${PKG_NAME}.zip"
rm -f "$ZIP_FILE"
zip -r -q "$ZIP_FILE" "$PKG_NAME"

BYTES=$(stat -f%z "$ZIP_FILE" 2>/dev/null || stat -c%s "$ZIP_FILE")
MB=$(echo "scale=2; $BYTES / 1048576" | bc 2>/dev/null || echo "?")

echo ""
echo "✅ Zip created:"
echo "   $OUT_DIR/$ZIP_FILE"
echo "   Size: ${MB} MB"
echo ""
echo "📧 Kongsi fail zip ini — penerima unzip dan jalankan START_*"
