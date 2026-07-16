#!/usr/bin/env bash
# Salin kit naratif (termasuk Johor) ke Desktop — jalankan sekali atau selepas kemas kini repo
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
KIT_REPO="$ROOT/data/projects/political/PRN/_shared/PRN_Crawl_Update_Kit"
KIT_DESKTOP="$HOME/Desktop/PRN_Johor_N9_Crawl_Update_Kit"

if [ ! -d "$KIT_DESKTOP" ]; then
  echo "❌ Folder Desktop tidak dijumpai: $KIT_DESKTOP"
  exit 1
fi

mkdir -p "$KIT_DESKTOP/09_naratif_cina_india/Johor" "$KIT_DESKTOP/06_pautan"
cp -R "$KIT_REPO/09_naratif_cina_india/"* "$KIT_DESKTOP/09_naratif_cina_india/"
cp "$KIT_REPO/README.txt" "$KIT_DESKTOP/README.txt"
cp "$KIT_REPO/00_MULA_DI_SINI.txt" "$KIT_DESKTOP/00_MULA_DI_SINI.txt"
cp "$KIT_REPO/06_pautan/QUICK_LINKS.txt" "$KIT_DESKTOP/06_pautan/QUICK_LINKS.txt" 2>/dev/null || true
chmod +x "$KIT_DESKTOP/09_naratif_cina_india/Johor/"*.command 2>/dev/null || true

echo "✅ Kit Desktop dikemas:"
echo "   $KIT_DESKTOP/09_naratif_cina_india/Johor/"
ls -la "$KIT_DESKTOP/09_naratif_cina_india/Johor/"
