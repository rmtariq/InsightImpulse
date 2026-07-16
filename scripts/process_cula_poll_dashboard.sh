#!/usr/bin/env bash
# Proses CSV crawl FB poll → label komen → JSON dashboard → production bundle
# Usage:
#   ./scripts/process_cula_poll_dashboard.sh path/to/Combined_facebook_XXXX.csv
#   ./scripts/process_cula_poll_dashboard.sh   # guna CSV default/latest

set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
PY="${ROOT}/.venv/bin/python3"
CSV="${1:-}"

if [[ -z "$CSV" ]]; then
  CSV="$("$PY" -c "
from pathlib import Path
from scripts.build_cula_poll_by_dun_n9 import find_default_csv
print(find_default_csv())
" 2>/dev/null || true)"
fi

if [[ -z "$CSV" || ! -f "$CSV" ]]; then
  echo "Guna: $0 <Combined_facebook_*.csv>"
  exit 1
fi

echo "① Label komen (Jelas + Debat + assumption)…"
"$PY" scripts/classify_cula_debate.py "$CSV"

echo "② Build poll per DUN…"
"$PY" scripts/build_cula_poll_by_dun_n9.py "$CSV"

echo "③ Rebuild production bundle…"
"$PY" scripts/build_warroom_production_bundle.py

echo "✓ Siap — refresh dashboard: http://localhost:8080 → Command Center"
echo "  CSV: $CSV"
