#!/usr/bin/env bash
# Refresh data naratif India → dashboard
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT"

PY=""
for candidate in \
  "NEImpulse/bin/python" \
  "n9_chinese_narrative_dashboard/.venv/bin/python" \
  ".venv/bin/python"; do
  if [ -x "$ROOT/$candidate" ]; then
    PY="$ROOT/$candidate"
    break
  fi
done
if [ -z "$PY" ]; then
  PY="$(command -v python3)"
fi
echo "Python: $PY"

echo "=== 1/3 Crawl naratif India (dedicated — seed queries + Tamil RSS) ==="
"$PY" scripts/crawl_prn_indian_narrative.py

echo ""
echo "=== 2/3 Crawl berita multibahasa (Google RSS + direct) ==="
"$PY" scripts/crawl_prn_n9_news_multilingual.py

echo ""
echo "=== 3/3 Rebuild CSV dashboard ==="
cd n9_chinese_narrative_dashboard
"$PY" -m utils.build_dataset

echo ""
echo "✅ Siap — buka dashboard:"
echo "   cd n9_chinese_narrative_dashboard && .venv/bin/streamlit run app.py"
