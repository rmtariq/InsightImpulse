#!/usr/bin/env python3
"""
Crawl all 36 DUN N9 using exact QUERY list (user war room format).

Usage:
  # Berita percuma — 36 kerusi, ~30 min
  python3 scripts/crawl_prn_n9_36dun.py

  # Socmed FB+X+TikTok+News via InsightPulse (8001 must be running)
  python3 scripts/crawl_prn_n9_36dun.py --socmed

  # One seat only
  python3 scripts/crawl_prn_n9_36dun.py --code N05

  # Then update war room
  python3 scripts/build_warroom_from_excel_crawl.py
  python3 scripts/build_warroom_production_bundle.py
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from prn_paths import crawls, ensure_state_dirs  # noqa: E402

QUERIES_JSON = ROOT / "data/projects/political/PRN/PRN_N9/reference/n9_36dun_crawl_queries.json"
API_BASE = "http://localhost:8001"
MYT = timezone(timedelta(hours=8))


def load_seats(code: str | None = None) -> list:
    data = json.loads(QUERIES_JSON.read_text(encoding="utf-8"))
    seats = data["seats"]
    if code:
        seats = [s for s in seats if s["code"].upper() == code.upper()]
    if not seats:
        raise SystemExit(f"Tiada kerusi untuk code={code}")
    return seats


async def crawl_news(seats: list, max_per: int) -> list:
    from backend.data_crawlers.scrapling_adapter import ScraplingAdapter

    adapter = ScraplingAdapter()
    seen: set = set()
    rows: list = []
    total = len(seats)

    for i, seat in enumerate(seats, 1):
        q = seat["query"]
        print(f"\n[{i}/{total}] {seat['code']} {seat['name']} [{seat.get('tier','')}]")
        print(f"   QUERY: {q[:90]}...")
        try:
            batch = await adapter._crawl_news(q, max_results=max_per, decode_urls=False)
        except Exception as exc:
            print(f"   ⚠ error: {exc}")
            continue
        added = 0
        for row in batch:
            rid = row.get("ID") or row.get("URL")
            if not rid or rid in seen:
                continue
            seen.add(rid)
            rows.append({
                **row,
                "SeedDun": seat["code"],
                "SeedDunName": seat["name"],
                "SeedTier": seat.get("tier"),
                "SeedQuery": q,
                "CrawlMethod": "n9_36dun_news",
            })
            added += 1
        print(f"   → +{added} rows (total {len(rows)})")
    return rows


def queue_socmed(seat: dict, dataset_size: int, wait: bool, poll_sec: int) -> dict | None:
    payload = {
        "query": seat["query"][:900],
        "platforms": ["news", "facebook", "x", "tiktok"],
        "analysis_type": "social_listening",
        "date_range": "30days",
        "dataset_size": dataset_size,
        "use_crawl_strategy": True,
        "project_id": "pas_break_2026",
        "analysis_focus": "comprehensive",
        "comment_sampling": "smart",
    }
    try:
        r = requests.post(f"{API_BASE}/analyze_async", json=payload, timeout=30)
        r.raise_for_status()
        data = r.json()
    except requests.RequestException as exc:
        print(f"   ❌ API error: {exc}")
        return None

    task_id = data.get("task_id")
    print(f"   🚀 task {task_id} (~{data.get('estimated_time_minutes')} min est.)")

    if not wait or not task_id:
        return data

    while True:
        time.sleep(poll_sec)
        try:
            st = requests.get(f"{API_BASE}/task_status/{task_id}", timeout=15).json()
        except requests.RequestException:
            continue
        status = st.get("status")
        for line in (st.get("logs") or [])[-3:]:
            print(f"      {line}")
        if status == "completed":
            print(f"   ✅ {seat['code']} siap")
            return st
        if status == "failed":
            print(f"   ❌ {seat['code']} gagal: {st.get('error')}")
            return st
        print(f"   … {status}")


def save_csv(rows: list) -> Path:
    ensure_state_dirs("N9")
    out_dir = crawls("N9", "excel_intel")
    ts = datetime.now(MYT).strftime("%Y%m%d_%H%M%S")
    path = out_dir / f"PRN_N9_36DUN_{ts}.csv"
    pd.DataFrame(rows).to_csv(path, index=False)
    print(f"\n💾 Saved: {path} ({len(rows)} rows, {len({r.get('SeedDun') for r in rows})} DUN)")
    return path


def main() -> int:
    p = argparse.ArgumentParser(description="Crawl 36 DUN N9 — exact QUERY list")
    p.add_argument("--code", help="Single DUN e.g. N05")
    p.add_argument("--socmed", action="store_true", help="InsightPulse FB+X+TikTok+News (8001)")
    p.add_argument("--max-per-query", type=int, default=20)
    p.add_argument("--dataset-size", type=int, default=1500)
    p.add_argument("--wait", action="store_true", help="Wait each socmed task to finish (slow)")
    p.add_argument("--delay", type=int, default=5, help="Seconds between socmed jobs")
    args = p.parse_args()

    seats = load_seats(args.code)
    print(f"📋 {len(seats)} kerusi N9 — queries from {QUERIES_JSON.name}")

    if args.socmed:
        print("🌐 Mode: SOCMED (News+Facebook+X+TikTok) via InsightPulse")
        print("   Pastikan: ./start_full_app.sh hidup di terminal lain\n")
        for i, seat in enumerate(seats, 1):
            print(f"[{i}/{len(seats)}] {seat['code']} {seat['name']}")
            queue_socmed(seat, args.dataset_size, wait=args.wait, poll_sec=20)
            if i < len(seats):
                time.sleep(args.delay)
        print("\n✅ Semua 36 task dihantar ke InsightPulse.")
        print("   Monitor: tail -f backend.log")
        return 0

    print("📰 Mode: NEWS only (percuma, Google News RSS)\n")
    rows = asyncio.run(crawl_news(seats, max_per=args.max_per_query))
    save_csv(rows)
    print("\nNext:")
    print("  python3 scripts/build_warroom_from_excel_crawl.py")
    print("  python3 scripts/build_warroom_production_bundle.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
