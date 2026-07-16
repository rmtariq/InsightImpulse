#!/usr/bin/env python3
"""
Crawl 36 DUN Negeri Sembilan via InsightPulse API (FB + IG + X + TikTok + News).

Source: Terkini_20062026_PRN_N9_Johor_Melaka_Update_2026.xlsx
  - Query Templates (TIER2_DUN_LOCAL) — primary query per DUN
  - DUN Keywords — metadata + query_bm fallback

Requires InsightPulse running:
  ./start_full_app.sh   →  http://localhost:8001

Usage:
  # Full 36 kerusi (sequential — one at a time, ~15–25 min/kerusi)
  python3 scripts/crawl_prn_n9_36dun_insightpulse.py

  # Test 1 kerusi
  python3 scripts/crawl_prn_n9_36dun_insightpulse.py --code N05

  # Resume after interrupt
  python3 scripts/crawl_prn_n9_36dun_insightpulse.py --resume

  # Queue only (no wait — NOT recommended; backend runs 1 task at a time)
  python3 scripts/crawl_prn_n9_36dun_insightpulse.py --no-wait
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from prn_paths import crawls, ensure_state_dirs  # noqa: E402

DEFAULT_XLSX = ROOT / "JITP_2026/Master_File/Terkini_20062026_PRN_N9_Johor_Melaka_Update_2026.xlsx"
API_BASE = "http://localhost:8001"
MYT = timezone(timedelta(hours=8))

PLATFORMS = ["facebook", "instagram", "x", "tiktok", "news"]

PAS_23 = {
    "N02", "N03", "N04", "N05", "N09", "N10", "N13", "N14", "N18", "N20",
    "N25", "N28", "N31", "N33", "N34", "N36", "N06", "N07", "N15", "N16",
    "N17", "N19", "N35",
}
IMBANG = {"N06", "N07", "N15", "N16", "N17", "N19", "N35"}


def tier_for(code: str) -> str:
    if code in IMBANG:
        return "IMBANG"
    if code in PAS_23:
        return "WAJIB-PAS23"
    return "LAWAN"


def normalize_query(q: str, code: str, name: str) -> str:
    q = (q or "").strip()
    if not q:
        q = f'"{code}" OR "{name}" OR PRN "Negeri Sembilan"'
    if code.upper() not in q.upper():
        q = f'"{code}" OR {name} OR ({q})'
    if "when:" not in q.lower():
        q = f"{q} when:30d"
    return q[:900]


def load_seats_from_excel(xlsx: Path) -> List[dict]:
    if not xlsx.exists():
        raise FileNotFoundError(xlsx)

    dun = pd.read_excel(xlsx, sheet_name="DUN Keywords")
    qt = pd.read_excel(xlsx, sheet_name="Query Templates")

    n9_dun = dun[dun["state"] == "Negeri Sembilan"].copy()
    tier2 = qt[(qt["state"] == "Negeri Sembilan") & (qt["tier"] == "TIER2_DUN_LOCAL")].copy()
    tier2_by = {str(r["dun_code"]).strip(): str(r["query"]) for _, r in tier2.iterrows()}

    seats: List[dict] = []
    for _, row in n9_dun.sort_values("dun_code").iterrows():
        code = str(row["dun_code"]).strip()
        name = str(row["dun_name"]).strip()
        query = tier2_by.get(code) or str(row.get("query_bm") or "")
        query = normalize_query(query, code, name)
        seats.append({
            "code": code,
            "name": name,
            "tier": tier_for(code),
            "parlimen": f"{row.get('parlimen_code', '')} {row.get('parlimen_name', '')}".strip(),
            "penyandang": str(row.get("candidate_keywords") or ""),
            "query": query,
            "primary_keywords": str(row.get("primary_keywords") or ""),
            "hashtags": str(row.get("hashtags") or ""),
            "local_issues": str(row.get("local_issues") or ""),
        })
    return seats


def run_manifest_path() -> Path:
    ensure_state_dirs("N9")
    return crawls("N9", "excel_intel") / "n9_36dun_insightpulse_run.json"


def load_run_manifest() -> dict:
    p = run_manifest_path()
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return {"started_at": None, "completed": {}, "failed": {}, "pending": []}


def save_run_manifest(manifest: dict) -> None:
    manifest["updated_at"] = datetime.now(MYT).isoformat(timespec="seconds")
    run_manifest_path().write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


def check_api() -> None:
    try:
        r = requests.get(f"{API_BASE}/health", timeout=10)
        r.raise_for_status()
    except requests.RequestException as exc:
        raise SystemExit(
            f"❌ InsightPulse tidak hidup di {API_BASE}\n"
            f"   Jalankan: ./start_full_app.sh\n"
            f"   Error: {exc}"
        )


def submit_crawl(seat: dict, dataset_size: int, date_range: str) -> dict:
    payload = {
        "query": seat["query"],
        "platforms": PLATFORMS,
        "analysis_type": "social_listening",
        "date_range": date_range,
        "dataset_size": dataset_size,
        "use_crawl_strategy": True,
        "project_id": "pas_break_2026",
        "analysis_focus": "comprehensive",
        "comment_sampling": "smart",
        "crawl_mode": "keyword",
    }
    r = requests.post(f"{API_BASE}/analyze_async", json=payload, timeout=60)
    r.raise_for_status()
    return r.json()


def wait_task(task_id: str, seat_code: str, poll_sec: int = 15, max_minutes: int = 45) -> dict:
    deadline = time.time() + max_minutes * 60
    last_log = 0
    while time.time() < deadline:
        try:
            st = requests.get(f"{API_BASE}/task_status/{task_id}", timeout=30).json()
        except requests.RequestException:
            time.sleep(poll_sec)
            continue

        status = st.get("status", "unknown")
        logs = st.get("logs") or []
        if len(logs) > last_log:
            for line in logs[last_log:]:
                print(f"      {line}")
            last_log = len(logs)

        prog = st.get("progress") or {}
        msg = prog.get("message") or status
        print(f"   … {seat_code}: {msg}")

        if status == "completed":
            return st
        if status == "failed":
            raise RuntimeError(st.get("error") or "task failed")

        time.sleep(poll_sec)

    raise TimeoutError(f"Task {task_id} timeout after {max_minutes} min")


def export_seat_manifest(seats: List[dict], xlsx: Path) -> Path:
    out = crawls("N9", "excel_intel") / "n9_36dun_seats_from_excel.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "meta": {
            "source": str(xlsx),
            "generated": datetime.now(MYT).isoformat(timespec="seconds"),
            "platforms": PLATFORMS,
            "count": len(seats),
        },
        "seats": seats,
    }
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return out


def main() -> int:
    p = argparse.ArgumentParser(description="InsightPulse crawl — 36 DUN N9 (5 platforms)")
    p.add_argument("--xlsx", type=Path, default=DEFAULT_XLSX)
    p.add_argument("--code", help="Single DUN e.g. N05")
    p.add_argument("--dataset-size", type=int, default=1500)
    p.add_argument("--date-range", default="30days", choices=["7days", "30days", "90days"])
    p.add_argument("--resume", action="store_true", help="Skip kerusi already completed")
    p.add_argument("--no-wait", action="store_true", help="Submit only, do not wait")
    p.add_argument("--delay", type=int, default=10, help="Seconds between jobs if --no-wait")
    p.add_argument("--max-minutes", type=int, default=45, help="Timeout per kerusi")
    args = p.parse_args()

    check_api()
    seats = load_seats_from_excel(args.xlsx)
    if args.code:
        seats = [s for s in seats if s["code"].upper() == args.code.upper()]
        if not seats:
            raise SystemExit(f"Kerusi {args.code} tidak dijumpai")

    manifest_path = export_seat_manifest(seats, args.xlsx)
    print(f"📋 Loaded {len(seats)} DUN from Excel")
    print(f"   Seat manifest: {manifest_path}")
    print(f"   Platforms: {', '.join(PLATFORMS)}")
    print(f"   Dataset: {args.dataset_size} | Date: {args.date_range}")
    print(f"   API: {API_BASE}\n")

    run = load_run_manifest()
    if not run.get("started_at"):
        run["started_at"] = datetime.now(MYT).isoformat(timespec="seconds")
    run["xlsx"] = str(args.xlsx)

    total = len(seats)
    for i, seat in enumerate(seats, 1):
        code = seat["code"]
        if args.resume and code in run.get("completed", {}):
            print(f"[{i}/{total}] {code} {seat['name']} — skip (done)")
            continue

        print(f"\n{'='*60}")
        print(f"[{i}/{total}] {code} {seat['name']} [{seat['tier']}]")
        print(f"   Parlimen: {seat['parlimen']}")
        print(f"   QUERY: {seat['query'][:120]}...")

        try:
            resp = submit_crawl(seat, args.dataset_size, args.date_range)
            task_id = resp.get("task_id")
            est = resp.get("estimated_time_minutes")
            print(f"   🚀 Task {task_id} (~{est} min est.)")

            if args.no_wait:
                run.setdefault("pending", []).append({"code": code, "task_id": task_id})
                save_run_manifest(run)
                time.sleep(args.delay)
                continue

            result = wait_task(task_id, code, max_minutes=args.max_minutes)
            run.setdefault("completed", {})[code] = {
                "task_id": task_id,
                "finished_at": datetime.now(MYT).isoformat(timespec="seconds"),
                "platforms": PLATFORMS,
            }
            save_run_manifest(run)
            print(f"   ✅ {code} selesai")

        except Exception as exc:
            print(f"   ❌ {code} gagal: {exc}")
            run.setdefault("failed", {})[code] = str(exc)
            save_run_manifest(run)
            if not args.no_wait:
                print("   Teruskan kerusi seterusnya...")
            continue

    print(f"\n{'='*60}")
    done = len(run.get("completed", {}))
    fail = len(run.get("failed", {}))
    print(f"✅ Selesai: {done}/{total} | Gagal: {fail}")
    print(f"   Run log: {run_manifest_path()}")
    print("\nSelepas semua siap:")
    print("   python3 scripts/build_warroom_from_excel_crawl.py")
    print("   python3 scripts/build_warroom_production_bundle.py")
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
