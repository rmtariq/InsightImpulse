#!/usr/bin/env python3
"""N9 PRN Batch 8 crawl — 7 Blok senario via Apify.

Baca query dari: data/projects/political/PRN/PRN_N9/N9_CRAWL_BATCH8_7BLOK.txt

Usage:
  python scripts/crawl_n9_batch8_7blok.py --pilot          # X sahaja, batch A–F
  python scripts/crawl_n9_batch8_7blok.py --full           # X + FB, A–G
  python scripts/crawl_n9_batch8_7blok.py --batch A --platforms x facebook
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
except ImportError:
    pass

BATCH8_TXT = ROOT / "data/projects/political/PRN/PRN_N9/N9_CRAWL_BATCH8_7BLOK.txt"
OUT_DIR = ROOT / "data/projects/political/pas_break_2026/crawls/N9/batch8_7blok"
MASTER_DIR = ROOT / "data/projects/political/pas_break_2026/master"

BATCH_MAP = {
    "A": "6_bersama",
    "B": "7_bersatu",
    "C": "4_pn",
    "D": "3_mn",
    "E": "1_2_solo",
    "F": "5_ph",
    "G": "mn13_dun",
    "H": "urls",
}


def _parse_batch8(path: Path) -> dict[str, list[dict[str, str]]]:
    text = path.read_text(encoding="utf-8")
    batches: dict[str, list[dict[str, str]]] = {k: [] for k in BATCH_MAP}
    current = None
    dun = None
    for line in text.splitlines():
        raw = line.strip()
        if not raw or raw.startswith("#"):
            m = re.search(r"BATCH\s+([A-H])\s", raw.upper())
            if m:
                current = m.group(1)
            continue
        m_dun = re.match(r"\[(N\d+)\s", raw, re.I)
        if m_dun:
            dun = m_dun.group(1).upper()
            continue
        if raw.startswith("http"):
            if current:
                batches[current].append({"type": "url", "query": raw, "dun": dun or ""})
            continue
        if current and len(raw) > 8:
            batches[current].append({"type": "keyword", "query": raw, "dun": dun or ""})
            dun = None
    return batches


def _apify_ready() -> tuple[bool, str]:
    token = os.getenv("APIFY_API_TOKEN") or os.getenv("APIFY_TOKEN")
    if not token or not str(token).strip():
        return False, "APIFY_API_TOKEN tiada dalam .env"
    if str(token).startswith("your_"):
        return False, "APIFY_API_TOKEN placeholder"
    return True, ""


async def _crawl_keyword(query: str, platforms: list[str], dataset_size: int, days: int) -> list[dict]:
    from backend.data_crawlers.simple_apify_adapter import SimpleApifyAdapter

    adapter = SimpleApifyAdapter()
    since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    result = await adapter.crawl_with_strategy(
        platforms=platforms,
        query=query,
        dataset_size=dataset_size,
        analysis_type="social_listening",
        since_date=since,
    )
    rows: list[dict] = []
    for plat, records in (result.get("results") or {}).items():
        for rec in records or []:
            rows.append({**rec, "Platform": plat, "SeedQuery": query, "crawl_batch": "PRN-N9-Batch8-7Blok"})
    return rows


async def _crawl_urls(urls: list[str], max_posts: int) -> list[dict]:
    from backend.data_crawlers.simple_apify_adapter import SimpleApifyAdapter

    adapter = SimpleApifyAdapter()
    result = await adapter.crawl_direct_urls(urls=urls, max_posts=max_posts)
    rows: list[dict] = []
    for plat, records in (result or {}).items():
        if isinstance(records, list):
            for rec in records:
                rows.append({**rec, "Platform": plat, "crawl_batch": "PRN-N9-Batch8-7Blok"})
    return rows


async def run_batches(
    batch_keys: list[str],
    platforms: list[str],
    dataset_size: int,
    days: int,
    url_max: int,
) -> dict[str, Any]:
    ok, reason = _apify_ready()
    if not ok:
        raise RuntimeError(reason)

    parsed = _parse_batch8(BATCH8_TXT)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    stats: dict[str, Any] = {"batches": {}, "total_rows": 0, "files": []}

    for key in batch_keys:
        items = parsed.get(key, [])
        if not items:
            continue
        bloc = BATCH_MAP.get(key, key)
        print(f"\n=== Batch {key} ({bloc}) · {len(items)} item ===")
        batch_rows: list[dict] = []

        urls = [i["query"] for i in items if i["type"] == "url"]
        keywords = [i for i in items if i["type"] == "keyword"]

        for i, item in enumerate(keywords, 1):
            q = item["query"]
            dun = item.get("dun") or ""
            label = f"{dun} " if dun else ""
            print(f"  [{i}/{len(keywords)}] {label}{q[:70]}...")
            try:
                rows = await _crawl_keyword(q, platforms, dataset_size, days)
                for r in rows:
                    r["bloc_scenario"] = bloc
                    r["dun_hint"] = dun
                batch_rows.extend(rows)
                print(f"      +{len(rows)} rows")
            except Exception as exc:
                print(f"      ❌ {exc}")

        if urls and "facebook" in platforms:
            print(f"  URL crawl: {len(urls)} URLs")
            try:
                url_rows = await _crawl_urls(urls, url_max)
                for r in url_rows:
                    r["bloc_scenario"] = bloc
                batch_rows.extend(url_rows)
                print(f"      +{len(url_rows)} rows")
            except Exception as exc:
                print(f"      ❌ URL: {exc}")

        if batch_rows:
            fname = f"N9_Batch8_{key}_{bloc}_{ts}.csv"
            fpath = OUT_DIR / fname
            pd.DataFrame(batch_rows).to_csv(fpath, index=False, encoding="utf-8")
            stats["files"].append(str(fpath))
            stats["batches"][key] = len(batch_rows)
            stats["total_rows"] += len(batch_rows)
            print(f"  💾 {fpath.name} ({len(batch_rows)} rows)")

    summary_path = OUT_DIR / f"N9_Batch8_summary_{ts}.json"
    summary_path.write_text(json.dumps(stats, indent=2), encoding="utf-8")
    print(f"\n✅ Summary: {summary_path}")
    print(f"   Total rows: {stats['total_rows']}")
    return stats


def merge_to_master(stats: dict[str, Any]) -> Path | None:
    """Append batch8 CSVs to a dated master slice (manual merge helper)."""
    files = stats.get("files") or []
    if not files:
        return None
    frames = [pd.read_csv(f, low_memory=False) for f in files]
    combined = pd.concat(frames, ignore_index=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    MASTER_DIR.mkdir(parents=True, exist_ok=True)
    out = MASTER_DIR / f"N9_Batch8_7Blok_{ts}.csv"
    combined.to_csv(out, index=False, encoding="utf-8")
    print(f"📦 Combined master slice: {out} ({len(combined)} rows)")
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description="N9 Batch 8 Apify crawl (7 Blok)")
    ap.add_argument("--pilot", action="store_true", help="Batch A–F, X only, size 50")
    ap.add_argument("--full", action="store_true", help="Batch A–G, X+FB, size 80")
    ap.add_argument("--batch", action="append", help="Single batch A–H (repeatable)")
    ap.add_argument("--platforms", default="", help="e.g. x facebook")
    ap.add_argument("--dataset-size", type=int, default=0)
    ap.add_argument("--days", type=int, default=7)
    ap.add_argument("--merge", action="store_true", help="Write combined CSV to master/")
    args = ap.parse_args()

    if args.pilot:
        batches = list("ABCDEF")
        platforms = ["x"]
        size = 50
    elif args.full:
        batches = list("ABCDEFG")
        platforms = ["x", "facebook"]
        size = 80
    elif args.batch:
        batches = [b.upper() for b in args.batch]
        platforms = args.platforms.split() if args.platforms else ["x", "facebook"]
        size = args.dataset_size or 60
    else:
        ap.print_help()
        print("\nContoh: python scripts/crawl_n9_batch8_7blok.py --pilot")
        sys.exit(0)

    if args.platforms and not args.pilot and not args.full:
        platforms = args.platforms.split()
    if args.dataset_size and not args.pilot and not args.full:
        size = args.dataset_size

    print(f"Batch 8 crawl · batches={batches} · platforms={platforms} · size={size} · days={args.days}")
    stats = asyncio.run(run_batches(batches, platforms, size, args.days, url_max=80))
    if args.merge and stats.get("total_rows"):
        merge_to_master(stats)
        print("\nSelepas merge ke master penuh, jalankan:")
        print("  python scripts/build_warroom_socmed_by_dun.py")
        print("  python scripts/build_warroom_production_bundle.py --state N9")
        print("  python scripts/update_n9_bloc_factions.py --llm")


if __name__ == "__main__":
    main()
