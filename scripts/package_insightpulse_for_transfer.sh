#!/bin/bash
# Package InsightPulse for transfer to another Mac (e.g. Raja's MacBook Pro).
# Creates a lean zip: app code + PRN N9 project + configs. Excludes secrets & heavy caches.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
STAMP="$(date +%Y%m%d_%H%M%S)"
OUT_DIR="${HOME}/Downloads"
ZIP_NAME="InsightPulse_APP_Transfer_${STAMP}.zip"
ZIP_PATH="${OUT_DIR}/${ZIP_NAME}"
STAGING="${TMPDIR:-/tmp}/insightpulse_pkg_${STAMP}"

echo "📦 Packaging InsightPulse from: ${ROOT}"
echo "   Output: ${ZIP_PATH}"
echo ""

rm -rf "${STAGING}"
mkdir -p "${STAGING}"

RSYNC_EXCLUDES=(
  --exclude '.git'
  --exclude '.venv'
  --exclude '.venv_*'
  --exclude 'NEImpulse'
  --exclude 'node_modules'
  --exclude '__pycache__'
  --exclude '*.pyc'
  --exclude '.DS_Store'
  --exclude '.env'
  --exclude '.env.local'
  --exclude '.env.production'
  --exclude 'data/combined'
  --exclude 'data/smart_crawlers'
  --exclude 'data/analyzed'
  --exclude 'reports'
  --exclude 'xyz_folder'
  --exclude '*.zip'
  --exclude '*.log'
)

copy_if_exists() {
  for item in "$@"; do
    if [[ -e "${ROOT}/${item}" ]]; then
      dest_dir="${STAGING}/$(dirname "${item}")"
      mkdir -p "${dest_dir}"
      rsync -a "${RSYNC_EXCLUDES[@]}" "${ROOT}/${item}" "${dest_dir}/"
    fi
  done
}

copy_if_exists \
  backend web_backend web_frontend scripts \
  data/projects requirements.txt \
  start_insightpulse.sh stop_insightpulse.sh \
  HOW_TO_START.md HOW_TO_START_INSIGHTPULSE.md FINAL_STARTUP_GUIDE.md \
  .env.example .env.nemotron.example TRANSFER_TO_SECOND_MAC.md

cd "${STAGING}"
zip -r -q "${ZIP_PATH}" . -x "*.DS_Store"

rm -rf "${STAGING}"

SIZE="$(du -h "${ZIP_PATH}" | cut -f1)"
echo ""
echo "✅ Done: ${ZIP_PATH}"
echo "   Size: ${SIZE}"
echo ""
echo "⚠️  .env TIDAK disertakan (API keys). Hantar .env secara berasingan via AirDrop/iMessage."
