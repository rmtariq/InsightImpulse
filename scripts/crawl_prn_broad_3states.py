#!/usr/bin/env python3
"""
FASA 1 — Broad crawl 3 negeri (banyak data) via InsightPulse.

Platform: Facebook, Instagram, X, TikTok, News
Dataset default: 5000 per negeri

Usage:
  ./start_full_app.sh   # terminal lain
  python3 scripts/crawl_prn_broad_3states.py
  python3 scripts/crawl_prn_broad_3states.py --state N9
  python3 scripts/crawl_prn_broad_3states.py --state N9 --query '"PRN Negeri Sembilan" OR ... when:30d'
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
API_BASE = "http://localhost:8001"
MYT = timezone(timedelta(hours=8))

PLATFORMS = ["facebook", "instagram", "x", "tiktok", "news"]

BROAD = {
    "N9": {
        "label": "Negeri Sembilan",
        "query": (
            '"PRN Negeri Sembilan" OR #prnn9 OR PAS OR UMNO OR BN OR DAP OR PKR OR Amanah '
            'OR BERSATU OR PN OR PH OR "Pakatan Harapan" OR Gerakan "Negeri Sembilan" when:7d'
        ),
    },
    "Johor": {
        "label": "Johor",
        "query": (
            '"PRN Johor" OR #prnjohor OR PAS OR UMNO OR BN OR DAP OR PKR OR Amanah '
            'OR BERSATU OR PN OR PH OR "Pakatan Harapan" OR Gerakan Johor when:7d'
        ),
    },
    "Melaka": {
        "label": "Melaka",
        "query": (
            '"PRN Melaka" OR "pilihan raya negeri melaka" OR #PRNMelaka '
            'OR PAS OR UMNO OR BN OR DAP OR PKR OR BERSATU OR Gerakan Melaka when:30d'
        ),
    },
}


def check_api() -> None:
    try:
        requests.get(f"{API_BASE}/health", timeout=15).raise_for_status()
    except requests.RequestException as exc:
        raise SystemExit(f"❌ InsightPulse off — run ./start_full_app.sh\n{exc}")


def submit(query: str, dataset_size: int, date_range: str) -> dict:
    payload = {
        "query": query[:900],
        "platforms": PLATFORMS,
        "analysis_type": "social_listening",
        "date_range": date_range,
        "dataset_size": dataset_size,
        "use_crawl_strategy": True,
        "project_id": "pas_break_2026",
        "analysis_focus": "comprehensive",
        "comment_sampling": "smart",
    }
    r = requests.post(f"{API_BASE}/analyze_async", json=payload, timeout=60)
    r.raise_for_status()
    return r.json()


def wait_task(task_id: str, label: str, poll: int = 20, max_min: int = 120) -> dict:
    end = time.time() + max_min * 60
    last = 0
    while time.time() < end:
        st = requests.get(f"{API_BASE}/task_status/{task_id}", timeout=120).json()
        logs = st.get("logs") or []
        for line in logs[last:]:
            print(f"   {line}")
        last = len(logs)
        status = st.get("status")
        print(f"   … {label}: {status}")
        if status == "completed":
            return st
        if status == "failed":
            raise RuntimeError(st.get("error") or "failed")
        time.sleep(poll)
    raise TimeoutError(f"{label} timeout {max_min}min")


def main() -> int:
    p = argparse.ArgumentParser(description="Broad crawl N9 + Johor + Melaka")
    p.add_argument("--state", choices=["N9", "Johor", "Melaka", "all"], default="all")
    p.add_argument("--query", help="Override query (use with --state N9|Johor|Melaka)")
    p.add_argument("--dataset-size", type=int, default=5000)
    p.add_argument("--date-range", default="30days")
    p.add_argument("--no-wait", action="store_true")
    args = p.parse_args()

    if args.query and args.state == "all":
        raise SystemExit("❌ --query requires --state N9, Johor, or Melaka (not all)")

    check_api()
    states = list(BROAD.keys()) if args.state == "all" else [args.state]
    log_path = ROOT / "data/projects/political/PRN/_shared/excel_intel/broad_crawl_run.json"
    run = {"started": datetime.now(MYT).isoformat(), "jobs": []}

    print(f"📡 Broad crawl · dataset {args.dataset_size} · {', '.join(PLATFORMS)}\n")

    for code in states:
        info = BROAD[code]
        query = args.query if args.query else info["query"]
        print(f"\n{'='*60}\n🌐 {info['label']} ({code})\n   {query[:100]}...")
        resp = submit(query, args.dataset_size, args.date_range)
        tid = resp.get("task_id")
        print(f"   🚀 task {tid}")
        job = {"state": code, "task_id": tid, "query": query}
        if not args.no_wait:
            wait_task(tid, info["label"])
            job["status"] = "completed"
        run["jobs"].append(job)

    log_path.write_text(json.dumps(run, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n✅ Broad crawl log: {log_path}")
    print("Next: bash scripts/run_prn_analyze_from_excel.sh")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
