#!/usr/bin/env bash
# Refresh PRN N9 dashboard data: BNM macro + news crawl + regenerate HTML
set -euo pipefail
cd "$(dirname "$0")/.."
if [ -f NEImpulse/bin/activate ]; then
  # shellcheck disable=SC1091
  source NEImpulse/bin/activate
fi
echo "=== 1/5 Seat analytics from Excel SPR ==="
python3 scripts/n9_seat_analytics.py
echo ""
echo "=== 2/5 Pull BNM economic data ==="
python3 scripts/pull_economic_n9.py
echo ""
echo "=== 3/5 Crawl PRN NS news (Google News RSS) ==="
python3 scripts/crawl_prn_n9_news.py || true
echo ""
echo "=== 4/5 Crawl ADUN social seeds (Excel) ==="
python3 scripts/crawl_prn_n9_adun_seeds.py || true
echo ""
echo "=== 5/5 Regenerate dashboard ==="
python3 scripts/generate_prn_n9_dashboard.py
echo ""
echo "Done → data/projects/political/pas_break_2026/reports/prn-negeri-sembilan-dashboard.html"
