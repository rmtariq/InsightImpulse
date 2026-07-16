#!/usr/bin/env python3
"""
Crawl PRN states using Excel Query Templates (news via Scrapling — RM0).

Manifest: data/projects/political/PRN/_shared/excel_intel/prn_excel_intel_manifest.json

Usage:
  python3 scripts/import_prn_excel_intel.py
  python3 scripts/crawl_prn_excel_intel.py --state N9
  python3 scripts/crawl_prn_excel_intel.py --state N9 --tiers TIER1_ELECTION,TIER2_DUN_LOCAL
  python3 scripts/crawl_prn_excel_intel.py --state all --limit 10   # ujian
  python3 scripts/crawl_prn_excel_intel.py --state N9 --via-api     # InsightPulse :8001 (Apify)
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT))

from prn_paths import SHARED, crawls, ensure_state_dirs  # noqa: E402

MANIFEST = SHARED / "excel_intel/prn_excel_intel_manifest.json"
API_BASE = "http://localhost:8001"
MYT = timezone(timedelta(hours=8))

STATE_LABEL = {"N9": "Negeri Sembilan", "Johor": "Johor", "Melaka": "Melaka"}
LABEL_TO_CODE = {v: k for k, v in STATE_LABEL.items()}
DEFAULT_TIERS_N9 = ["TIER1_ELECTION", "TIER2_DUN_LOCAL", "TIER3_LOCAL_ISSUE"]

PLATFORM_ALIASES = {
    "news": "news",
    "facebook": "facebook",
    "x": "x",
    "twitter": "x",
    "tiktok": "tiktok",
    "instagram": "instagram",
}


def load_manifest() -> dict:
    if not MANIFEST.exists():
        raise FileNotFoundError(
            f"Manifest missing: {MANIFEST}\nRun: python3 scripts/import_prn_excel_intel.py"
        )
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def parse_platforms(platform_group: str) -> List[str]:
    out = []
    for part in str(platform_group or "").split(","):
        key = part.strip().lower()
        if key in PLATFORM_ALIASES:
            out.append(PLATFORM_ALIASES[key])
    return list(dict.fromkeys(out))


def select_queries(
    manifest: dict,
    state: str,
    tiers: Optional[List[str]],
    priority: Optional[str],
    limit: int,
) -> List[dict]:
    label = STATE_LABEL.get(state, state)
    rows = [r for r in manifest["query_templates"] if r.get("state") == label]
    if tiers:
        tier_set = {t.strip() for t in tiers}
        rows = [r for r in rows if r.get("tier") in tier_set]
    if priority:
        rows = [r for r in rows if (r.get("monitoring_priority") or "").upper() == priority.upper()]
    # News-capable first for free crawl
    rows.sort(key=lambda r: (r.get("dun_code") or "", r.get("tier") or ""))
    if limit > 0:
        rows = rows[:limit]
    return rows


async def crawl_news_batch(queries: List[dict], max_per: int) -> List[dict]:
    from backend.data_crawlers.scrapling_adapter import ScraplingAdapter

    adapter = ScraplingAdapter()
    seen: set = set()
    all_rows: List[dict] = []

    for i, q in enumerate(queries, 1):
        query = str(q.get("query") or "").strip()
        if not query or query.lower() == "nan":
            continue
        dun = q.get("dun_code") or ""
        tier = q.get("tier") or ""
        state_label = q.get("state") or ""
        print(f"[{i}/{len(queries)}] {state_label} {dun} {tier}: {query[:72]}...")
        try:
            batch = await adapter._crawl_news(query, max_results=max_per, decode_urls=False)
        except Exception as exc:
            print(f"   ⚠ crawl error: {exc}")
            continue
        added = 0
        for row in batch:
            rid = row.get("ID") or row.get("URL")
            if not rid or rid in seen:
                continue
            seen.add(rid)
            enriched = dict(row)
            enriched.update({
                "SeedState": LABEL_TO_CODE.get(state_label, state_label),
                "SeedStateLabel": state_label,
                "SeedDun": dun,
                "SeedDunName": q.get("dun_name"),
                "SeedTier": tier,
                "SeedPlatformGroup": q.get("platform_group"),
                "SeedQuery": query,
                "SeedPurpose": q.get("purpose"),
                "CrawlMethod": "excel_intel_news",
            })
            all_rows.append(enriched)
            added += 1
        print(f"   → +{added} (total {len(all_rows)})")
    return all_rows


def trigger_api_crawl(query_row: dict, dataset_size: int, date_range: str) -> Optional[dict]:
    query = str(query_row.get("query") or "").strip()
    if not query:
        return None
    platforms = parse_platforms(query_row.get("platform_group"))
    if not platforms:
        platforms = ["news", "facebook", "x"]
    payload = {
        "query": query[:900],
        "platforms": platforms,
        "analysis_type": "social_listening",
        "date_range": date_range,
        "dataset_size": dataset_size,
        "use_crawl_strategy": True,
        "project_id": "pas_break_2026",
        "analysis_focus": "comprehensive",
        "comment_sampling": "smart",
    }
    try:
        r = requests.post(f"{API_BASE}/analyze_async", json=payload, timeout=20)
        if r.status_code == 200:
            data = r.json()
            print(f"   🚀 API task {data.get('task_id')} (~{data.get('estimated_time_minutes')} min)")
            return data
    except requests.RequestException as exc:
        print(f"   ℹ️ InsightPulse unavailable: {exc}")
    return None


def save_csv(rows: List[dict], state: str) -> Path:
    ensure_state_dirs(state)
    out_dir = crawls(state, "excel_intel")
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(MYT).strftime("%Y%m%d_%H%M%S")
    path = out_dir / f"PRN_ExcelIntel_{state}_{ts}.csv"
    df = pd.DataFrame(rows)
    if df.empty:
        df = pd.DataFrame(columns=[
            "Platform", "Type", "ID", "Text", "URL", "Date",
            "SeedState", "SeedDun", "SeedTier", "SeedQuery",
        ])
    df.to_csv(path, index=False)
    summary = {
        "generated_at": datetime.now(MYT).isoformat(timespec="seconds"),
        "state": state,
        "csv": str(path.relative_to(ROOT)),
        "rows": len(rows),
        "dun_with_hits": len({r.get("SeedDun") for r in rows if r.get("SeedDun")}),
        "tiers": sorted({r.get("SeedTier") for r in rows if r.get("SeedTier")}),
    }
    (out_dir / f"PRN_ExcelIntel_{state}_{ts}_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (out_dir / "latest_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return path


async def run_state(
    manifest: dict,
    state: str,
    tiers: Optional[List[str]],
    priority: Optional[str],
    limit: int,
    max_per: int,
    via_api: bool,
    api_limit: int,
    dataset_size: int,
    date_range: str,
    api_delay: int,
) -> Path:
    queries = select_queries(manifest, state, tiers, priority, limit)
    print(f"\n📋 {state}: {len(queries)} query templates selected")
    if not queries:
        print("   (tiada query — semak --state / --tiers)")
        return save_csv([], state)

    rows = await crawl_news_batch(queries, max_per=max_per)

    if via_api:
        api_rows = queries[:api_limit] if api_limit > 0 else queries
        print(f"\n🌐 InsightPulse API: queue {len(api_rows)} socmed crawl(s)...")
        tasks = []
        for q in api_rows:
            if "news" in parse_platforms(q.get("platform_group")) and len(parse_platforms(q.get("platform_group"))) == 1:
                continue
            task = trigger_api_crawl(q, dataset_size=dataset_size, date_range=date_range)
            if task:
                tasks.append(task)
            time.sleep(api_delay)
        if tasks:
            queue_path = crawls(state, "excel_intel") / "insightpulse_queue.json"
            queue_path.write_text(json.dumps(tasks, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"   Queue saved: {queue_path}")

    path = save_csv(rows, state)
    print(f"💾 {path} ({len(rows)} rows)")
    return path


async def main_async(args: argparse.Namespace) -> int:
    manifest = load_manifest()
    states = list(STATE_LABEL.keys()) if args.state == "all" else [args.state]
    tiers = [t.strip() for t in args.tiers.split(",") if t.strip()] if args.tiers else None
    if args.state == "N9" and tiers is None:
        tiers = DEFAULT_TIERS_N9

    for st in states:
        if st not in STATE_LABEL:
            print(f"⚠ Unknown state: {st}", file=sys.stderr)
            continue
        await run_state(
            manifest,
            st,
            tiers,
            args.priority,
            args.limit,
            args.max_per_query,
            args.via_api,
            args.api_limit,
            args.dataset_size,
            args.date_range,
            args.api_delay,
        )
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description="Crawl from PRN Excel intel manifest")
    p.add_argument("--state", default="N9", help="N9 | Johor | Melaka | all")
    p.add_argument("--tiers", default="", help="Comma tiers e.g. TIER1_ELECTION,TIER2_DUN_LOCAL")
    p.add_argument("--priority", default="", help="HIGH | MEDIUM | LOW")
    p.add_argument("--limit", type=int, default=0, help="Max queries (0=all)")
    p.add_argument("--max-per-query", type=int, default=25)
    p.add_argument("--via-api", action="store_true", help="Queue socmed crawls on localhost:8001")
    p.add_argument("--api-limit", type=int, default=5, help="Max API crawls per run")
    p.add_argument("--dataset-size", type=int, default=2000)
    p.add_argument("--date-range", default="30days", choices=["24h", "7days", "30days", "90days"])
    p.add_argument("--api-delay", type=int, default=3, help="Seconds between API jobs")
    args = p.parse_args()
    return asyncio.run(main_async(args))


if __name__ == "__main__":
    raise SystemExit(main())
