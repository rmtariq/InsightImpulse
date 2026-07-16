#!/usr/bin/env python3
"""
PRN N9 — Orkestrator crawl penuh per DUN: berita + socmed + sentiment + war room.

Skop:
  • Berita (percuma): 36 DUN — baseline sentiment per kerusi
  • Socmed (Apify): 23 kerusi PAS bertanding — FB + TikTok + News
  • Analitik: ML sentiment + emotion (Tier A) + per-DUN rollup
  • Rebuild: socmed_by_dun_N9.json + n9_production_bundle.json

Usage:
  # Lalai: berita 36 DUN + socmed 23 PAS + analitik + bundle
  python3 scripts/crawl_prn_n9_dun_full.py

  # Berita + analitik sahaja (RM0, backend tidak perlu)
  python3 scripts/crawl_prn_n9_dun_full.py --skip-socmed

  # Socmed 36 DUN (kos tinggi)
  python3 scripts/crawl_prn_n9_dun_full.py --socmed-scope all36

  # Satu kerusi
  python3 scripts/crawl_prn_n9_dun_full.py --code N25

  # Hantar socmed tanpa tunggu (monitor backend.log)
  python3 scripts/crawl_prn_n9_dun_full.py --no-wait-socmed

Pastikan backend hidup untuk socmed:
  ./start_full_app.sh
"""
from __future__ import annotations

import argparse
import asyncio
import json
import subprocess
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Callable

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from prn_paths import crawls, ensure_state_dirs  # noqa: E402

QUERIES_JSON = ROOT / "data/projects/political/PRN/PRN_N9/reference/n9_36dun_crawl_queries.json"
PAS23_JSON = ROOT / "data/projects/political/PRN/PRN_N9/reports/war_room/prototype/data/pas_target_23_N9.json"
API_BASE = "http://localhost:8001"
MYT = timezone(timedelta(hours=8))
RUN_LOG = ROOT / "data/projects/political/PRN/PRN_N9/crawls/n9_dun_full_run.json"

PAS23_DEFAULT = {
    "N02", "N03", "N04", "N05", "N09", "N10", "N13", "N14",
    "N18", "N20", "N25", "N28", "N31", "N33", "N34", "N36",
    "N06", "N07", "N15", "N16", "N17", "N19", "N35",
}


def load_pas23_codes() -> set[str]:
    if PAS23_JSON.exists():
        data = json.loads(PAS23_JSON.read_text(encoding="utf-8"))
        codes = data.get("codes") or [s["code"] for s in data.get("seats", [])]
        if codes:
            return {c.upper() for c in codes}
    return PAS23_DEFAULT


def load_seats(scope: str, code: str | None) -> list[dict]:
    data = json.loads(QUERIES_JSON.read_text(encoding="utf-8"))
    seats = data["seats"]
    pas23 = load_pas23_codes()

    if code:
        seats = [s for s in seats if s["code"].upper() == code.upper()]
    elif scope == "pas23":
        seats = [s for s in seats if s["code"].upper() in pas23]
    # all36: keep all

    if not seats:
        raise SystemExit(f"Tiada kerusi untuk scope={scope} code={code}")
    return seats


async def crawl_news_seats(seats: list[dict], max_per: int) -> tuple[list[dict], Path]:
    from backend.data_crawlers.scrapling_adapter import ScraplingAdapter

    ensure_state_dirs("N9")
    out_dir = crawls("N9", "excel_intel")
    out_dir.mkdir(parents=True, exist_ok=True)

    adapter = ScraplingAdapter()
    seen: set = set()
    rows: list[dict] = []
    total = len(seats)

    for i, seat in enumerate(seats, 1):
        q = seat["query"]
        print(f"\n[NEWS {i}/{total}] {seat['code']} {seat['name']} [{seat.get('tier', '')}]")
        print(f"   QUERY: {q[:88]}...")
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
                "CrawlMethod": "n9_dun_full_news",
            })
            added += 1
        print(f"   → +{added} (total {len(rows)})")

    ts = datetime.now(MYT).strftime("%Y%m%d_%H%M%S")
    path = out_dir / f"PRN_N9_36DUN_{ts}.csv"
    pd.DataFrame(rows).to_csv(path, index=False)
    print(f"\n💾 News CSV: {path} ({len(rows)} rows, {len({r.get('SeedDun') for r in rows})} DUN)")
    return rows, path


def api_alive() -> bool:
    try:
        r = requests.get(f"{API_BASE}/health", timeout=5)
        return r.status_code == 200
    except requests.RequestException:
        try:
            r = requests.get(f"{API_BASE}/", timeout=5)
            return r.status_code in (200, 404)
        except requests.RequestException:
            return False


def queue_socmed(
    seat: dict,
    *,
    dataset_size: int,
    platforms: list[str],
    wait: bool,
    poll_sec: int,
) -> dict | None:
    payload = {
        "query": seat["query"][:900],
        "platforms": platforms,
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
    est = data.get("estimated_time_minutes")
    print(f"   🚀 {seat['code']} task={task_id} (~{est} min)")

    if not wait or not task_id:
        return data

    while True:
        time.sleep(poll_sec)
        try:
            st = requests.get(f"{API_BASE}/task_status/{task_id}", timeout=15).json()
        except requests.RequestException:
            continue
        status = st.get("status")
        for line in (st.get("logs") or [])[-2:]:
            print(f"      {line}")
        if status == "completed":
            print(f"   ✅ {seat['code']} siap")
            return st
        if status == "failed":
            print(f"   ❌ {seat['code']} gagal: {st.get('error')}")
            return st
        print(f"   … {status}")


def run_subprocess(cmd: list[str], label: str) -> int:
    print(f"\n{'=' * 60}\n▶ {label}\n   {' '.join(cmd)}\n{'=' * 60}")
    return subprocess.call(cmd, cwd=str(ROOT))


def build_run_summary(
    *,
    news_csv: Path | None,
    news_rows: int,
    news_seats: int,
    socmed_tasks: list[dict],
    phases_done: list[str],
    scope_news: str,
    scope_socmed: str,
) -> dict:
    return {
        "run_at": datetime.now(MYT).isoformat(timespec="seconds"),
        "scope_news": scope_news,
        "scope_socmed": scope_socmed,
        "phases_done": phases_done,
        "news_csv": str(news_csv.relative_to(ROOT)) if news_csv else None,
        "news_rows": news_rows,
        "news_seats_with_data": news_seats,
        "socmed_tasks": socmed_tasks,
        "next_steps": [
            "Monitor socmed: tail -f backend.log",
            "Selepas task siap: python3 scripts/merge_prn_johor_n9_master.py",
            "Rebuild war room: python3 scripts/build_warroom_production_bundle.py",
            "Hard refresh: localhost:8080 Cmd+Shift+R",
        ],
    }


def main() -> int:
    p = argparse.ArgumentParser(description="PRN N9 full DUN crawl orchestrator")
    p.add_argument(
        "--scope",
        choices=("all36", "pas23"),
        default="all36",
        help="Skop crawl berita (default: all36)",
    )
    p.add_argument(
        "--socmed-scope",
        choices=("pas23", "all36", "none"),
        default="pas23",
        help="Skop socmed Apify (default: pas23 = 23 kerusi PAS)",
    )
    p.add_argument("--code", help="Satu kerusi sahaja e.g. N25")
    p.add_argument("--max-per-query", type=int, default=18, help="Max berita per DUN")
    p.add_argument("--dataset-size", type=int, default=900, help="Socmed dataset_size per kerusi")
    p.add_argument(
        "--platforms",
        default="news,facebook,tiktok",
        help="Platform socmed (comma-separated)",
    )
    p.add_argument("--skip-socmed", action="store_true", help="Langkau fasa socmed")
    p.add_argument("--skip-analyze", action="store_true", help="Langkau ML sentiment berita")
    p.add_argument("--skip-rebuild", action="store_true", help="Langkau rebuild war room bundle")
    p.add_argument("--keyword-only", action="store_true", help="Analitik berita tanpa HF model")
    p.add_argument("--analyze-max-rows", type=int, default=400, help="Max baris Tier A ML")
    p.add_argument("--wait-socmed", action="store_true", help="Tunggu setiap task socmed siap")
    p.add_argument("--no-wait-socmed", action="store_true", help="Hantar socmed tanpa tunggu")
    p.add_argument("--delay", type=int, default=8, help="Saat antara job socmed")
    p.add_argument(
        "--phase",
        default="all",
        help="Fasa: all | news | socmed | analyze | rebuild (comma-separated)",
    )
    args = p.parse_args()

    if args.skip_socmed:
        args.socmed_scope = "none"

    phases = {"news", "socmed", "analyze", "rebuild"} if args.phase == "all" else {
        x.strip() for x in args.phase.split(",") if x.strip()
    }

    news_seats = load_seats(args.scope, args.code)
    pas23 = load_pas23_codes()
    if args.socmed_scope == "pas23":
        socmed_seats = [s for s in load_seats("all36", args.code) if s["code"].upper() in pas23]
    elif args.socmed_scope == "all36":
        socmed_seats = load_seats("all36", args.code)
    else:
        socmed_seats = []

    print("=" * 60)
    print("PRN N9 — FULL DUN CRAWL ORCHESTRATOR")
    print(f"  Berita : {len(news_seats)} kerusi ({args.scope})")
    print(f"  Socmed : {len(socmed_seats)} kerusi ({args.socmed_scope})")
    print(f"  Fasa   : {', '.join(sorted(phases))}")
    print("=" * 60)

    news_csv: Path | None = None
    news_rows = 0
    news_seats_count = 0
    socmed_tasks: list[dict] = []
    phases_done: list[str] = []

    if "news" in phases:
        rows, news_csv = asyncio.run(crawl_news_seats(news_seats, args.max_per_query))
        news_rows = len(rows)
        news_seats_count = len({r.get("SeedDun") for r in rows if r.get("SeedDun")})
        phases_done.append("news")

    if "socmed" in phases and socmed_seats:
        platforms = [x.strip() for x in args.platforms.split(",") if x.strip()]
        wait = args.wait_socmed and not args.no_wait_socmed
        if not api_alive():
            print("\n⚠️  Backend http://localhost:8001 tidak hidup.")
            print("   Jalankan: ./start_full_app.sh")
            print("   Socmed dilangkau — berita + analitik masih jalan.\n")
        else:
            print(f"\n🌐 SOCMED — {len(socmed_seats)} kerusi · platforms={platforms}")
            for i, seat in enumerate(socmed_seats, 1):
                print(f"\n[SOCMED {i}/{len(socmed_seats)}] {seat['code']} {seat['name']}")
                result = queue_socmed(
                    seat,
                    dataset_size=args.dataset_size,
                    platforms=platforms,
                    wait=wait,
                    poll_sec=25,
                )
                if result:
                    socmed_tasks.append({
                        "code": seat["code"],
                        "name": seat["name"],
                        "task_id": result.get("task_id"),
                        "status": result.get("status", "queued"),
                    })
                if i < len(socmed_seats):
                    time.sleep(args.delay)
            phases_done.append("socmed")

    if "analyze" in phases and not args.skip_analyze:
        csv_for_analyze = news_csv
        if not csv_for_analyze:
            folder = crawls("N9", "excel_intel")
            files = sorted(folder.glob("PRN_N9_36DUN_*.csv"), key=lambda p: p.stat().st_mtime, reverse=True)
            csv_for_analyze = files[0] if files else None

        if csv_for_analyze:
            cmd = [
                sys.executable,
                str(ROOT / "scripts/analyze_prn_n9_news.py"),
                "--csv", str(csv_for_analyze),
                "--max-rows", str(args.analyze_max_rows),
            ]
            if args.keyword_only:
                cmd.append("--keyword-only")
            rc = run_subprocess(cmd, "Analitik berita — sentiment + emotion (Tier A)")
            if rc == 0:
                phases_done.append("analyze")
        else:
            print("⚠️  Tiada CSV berita untuk analitik")

    if "rebuild" in phases and not args.skip_rebuild:
        steps: list[tuple[str, list[str]]] = [
            (
                "Per-DUN rollup dari crawl berita",
                [sys.executable, str(ROOT / "scripts/build_warroom_from_excel_crawl.py")],
            ),
            (
                "Per-DUN insight dari master hybrid (jika wujud)",
                [sys.executable, str(ROOT / "scripts/analyze_prn_excel_dun_insights.py")],
            ),
            (
                "Production bundle war room",
                [sys.executable, str(ROOT / "scripts/build_warroom_production_bundle.py")],
            ),
            (
                "Audit keyword DUN",
                [sys.executable, str(ROOT / "scripts/audit_dun_keyword_matching.py")],
            ),
        ]
        ok = True
        for label, cmd in steps:
            rc = run_subprocess(cmd, label)
            if rc != 0 and "audit" not in label.lower():
                ok = False
        if ok:
            phases_done.append("rebuild")

    summary = build_run_summary(
        news_csv=news_csv,
        news_rows=news_rows,
        news_seats=news_seats_count,
        socmed_tasks=socmed_tasks,
        phases_done=phases_done,
        scope_news=args.scope,
        scope_socmed=args.socmed_scope,
    )
    RUN_LOG.parent.mkdir(parents=True, exist_ok=True)
    RUN_LOG.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\n" + "=" * 60)
    print("✅ ORCHESTRATOR SIAP")
    print(f"   Log: {RUN_LOG.relative_to(ROOT)}")
    print(f"   Berita: {news_rows} rows · {news_seats_count} DUN")
    print(f"   Socmed tasks: {len(socmed_tasks)}")
    print(f"   Fasa selesai: {', '.join(phases_done)}")
    if socmed_tasks and not args.wait_socmed:
        print("\n   📡 Socmed di background — monitor: tail -f backend.log")
        print("   Selepas siap: python3 scripts/merge_prn_johor_n9_master.py")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
