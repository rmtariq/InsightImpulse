#!/usr/bin/env python3
"""Legacy alias — use crawl_prn_chinese_news.py instead."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
cmd = [sys.executable, str(ROOT / "scripts/crawl_prn_chinese_news.py"), "--negeri", "negeri sembilan"]
raise SystemExit(subprocess.call(cmd))
