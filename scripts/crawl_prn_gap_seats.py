#!/usr/bin/env python3
"""
Targeted gap-DUN crawl — fast, bounded, sufficient for analytics.

Uses InsightPulse API with crawl_guard (no 56-keyword OR explosion).
Default: gap seats only, 7 days, dataset 400, FB+IG+X+TikTok+News (no Threads/YouTube).

Usage:
  ./start_full_app.sh
  python3 scripts/crawl_prn_gap_seats.py --state N9 --max-seats 5   # test
  python3 scripts/crawl_prn_gap_seats.py --state all
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
GAP_JSON = ROOT / "data/projects/political/PRN/_shared/excel_intel/PRN_GAP_CRAWL_N9_JOHOR.json"
API = "http://localhost:8001"
MYT = timezone(timedelta(hours=8))

# Fast + cukup analitik — skip Threads/YouTube (paling lambat)
PLATFORMS = ["facebook", "instagram", "x", "tiktok", "news"]


def check_api() -> None:
    try:
        requests.get(f"{API}/health", timeout=15).raise_for_status()
    except requests.RequestException as exc:
        raise SystemExit(f"❌ Start InsightPulse first: ./start_full_app.sh\n{exc}")


def submit(query: str, dataset_size: int) -> str:
    payload = {
        "query": query[:900],
        "platforms": PLATFORMS,
        "analysis_type": "social_listening",
        "date_range": "7days",
        "dataset_size": dataset_size,
        "use_crawl_strategy": True,
        "project_id": "pas_break_2026",
        "analysis_focus": "comprehensive",
        "comment_sampling": "smart",
    }
    r = requests.post(f"{API}/analyze_async", json=payload, timeout=60)
    r.raise_for_status()
    return r.json()["task_id"]


def wait_task(task_id: str, label: str, poll: int = 15, max_min: int = 45) -> bool:
    end = time.time() + max_min * 60
    while time.time() < end:
        st = requests.get(f"{API}/task_status/{task_id}", timeout=30).json()
        status = st.get("status")
        prog = st.get("progress") or {}
        msg = prog.get("message") or status
        print(f"   … {label}: {msg}")
        if status == "completed":
            return True
        if status == "failed":
            print(f"   ❌ {st.get('error')}")
            return False
        time.sleep(poll)
    print(f"   ⏱️ timeout {max_min}min — check backend.log")
    return False


def main() -> int:
    p = argparse.ArgumentParser(description="Crawl gap DUN seats (N9 + Johor)")
    p.add_argument("--state", choices=["N9", "Johor", "all"], default="all")
    p.add_argument("--max-seats", type=int, default=0, help="Limit seats (0=all gaps)")
    p.add_argument("--dataset-size", type=int, default=400)
    p.add_argument("--regenerate-gaps", action="store_true")
    args = p.parse_args()

    if args.regenerate_gaps or not GAP_JSON.exists():
        import subprocess
        subprocess.check_call([sys.executable, str(ROOT / "scripts/generate_prn_gap_crawl_list.py")])

    data = json.loads(GAP_JSON.read_text(encoding="utf-8"))
    state_map = {"N9": "Negeri Sembilan", "Johor": "Johor"}
    states = list(state_map.values()) if args.state == "all" else [state_map[args.state]]

    check_api()
    jobs = []
    for state in states:
        seats = data["gaps"].get(state, [])
        if args.max_seats:
            seats = seats[: args.max_seats]
        print(f"\n{'='*60}\n🎯 {state} — {len(seats)} gap seat(s)\n")
        for i, seat in enumerate(seats, 1):
            code, name = seat["dun_code"], seat["dun_name"]
            q = seat["query"]
            print(f"[{i}/{len(seats)}] {code} {name} (strict={seat['strict_mentions']})")
            tid = submit(q, args.dataset_size)
            print(f"   🚀 task {tid}")
            ok = wait_task(tid, f"{code}")
            jobs.append({"state": state, "dun": code, "task_id": tid, "ok": ok})

    log = ROOT / "data/projects/political/PRN/_shared/excel_intel/gap_crawl_run.json"
    log.write_text(json.dumps({"started": datetime.now(MYT).isoformat(), "jobs": jobs}, indent=2))
    print(f"\n✅ Gap crawl log: {log}")
    print("Next: merge latest Combined_* or re-run analyze_prn_excel_dun_insights.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
