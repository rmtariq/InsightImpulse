#!/usr/bin/env python3
"""Crawl PRN Chinese Narrative news — NS + Melaka + Johor (Google News RSS, percuma)."""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from prn_paths import crawls, reference, ensure_state_dirs  # noqa: E402

ensure_state_dirs("N9")
CRAWL_DIR = crawls("N9", "chinese_news")
SUMMARY_JSON = reference("N9") / "prn_chinese_news_summary.json"

QUERY_PACK = {
    "negeri sembilan": [
        {"id": "S1A1", "query": '"Sin Chew" OR "China Press" "Negeri Sembilan" OR 森美兰 when:30d', "voice": "media_chinese", "weight": "Tinggi", "negeri": "Negeri Sembilan"},
        {"id": "S1A2", "query": '"pengundi Cina" OR "komuniti Cina" "Negeri Sembilan" PRN when:30d', "voice": "proxy_about_chinese", "weight": "Rendah", "negeri": "Negeri Sembilan"},
        {"id": "S1B1", "query": 'DAP OR "Pakatan Harapan" "Negeri Sembilan" PRN when:30d', "voice": "party_official", "weight": "Tinggi", "negeri": "Negeri Sembilan"},
    ],
    "johor": [
        {"id": "S2A1", "query": '"Sin Chew" OR "China Press" Johor OR 柔佛 when:30d', "voice": "media_chinese", "weight": "Tinggi", "negeri": "Johor"},
        {"id": "S2A2", "query": '"pengundi Cina" OR "komuniti Cina" Johor PRN when:30d', "voice": "proxy_about_chinese", "weight": "Rendah", "negeri": "Johor"},
        {"id": "S2B1", "query": 'DAP OR Liew Chin Tong OR "Johor Bahru" PRN when:30d', "voice": "party_official", "weight": "Tinggi", "negeri": "Johor"},
    ],
    "melaka": [
        {"id": "S3A1", "query": '"Sin Chew" OR "China Press" Melaka OR 马六甲 when:30d', "voice": "media_chinese", "weight": "Tinggi", "negeri": "Melaka"},
        {"id": "S3A2", "query": '"pengundi Cina" OR "komuniti Cina" Melaka PRN when:30d', "voice": "proxy_about_chinese", "weight": "Rendah", "negeri": "Melaka"},
        {"id": "S3B1", "query": 'DAP OR "Kerajaan Melaka" OR Khoo Poay Tiong Melaka when:30d', "voice": "party_official", "weight": "Tinggi", "negeri": "Melaka"},
    ],
    "all": [
        {"id": "SX1", "query": '"Sin Chew" OR "China Press" ("Negeri Sembilan" OR Johor OR Melaka) PRN when:30d', "voice": "media_chinese", "weight": "Tinggi", "negeri": "Semua"},
        {"id": "SX2", "query": '"pengundi Cina" ("Negeri Sembilan" OR Johor OR Melaka) when:30d', "voice": "proxy_about_chinese", "weight": "Rendah", "negeri": "Semua"},
    ],
}


async def crawl_queries(items: List[dict], max_per_query: int = 60) -> List[Dict[str, Any]]:
    from backend.data_crawlers.scrapling_adapter import ScraplingAdapter

    adapter = ScraplingAdapter()
    seen: set = set()
    rows: List[Dict[str, Any]] = []

    for item in items:
        q = item["query"]
        print(f"📰 [{item['id']}] {item.get('negeri', '')} — {q[:65]}...")
        batch = await adapter._crawl_news(q, max_results=max_per_query, decode_urls=False)
        added = 0
        for row in batch:
            rid = row.get("ID") or row.get("URL")
            if rid in seen:
                continue
            seen.add(rid)
            rows.append({
                **row,
                "QueryID": item["id"],
                "Negeri": item.get("negeri", ""),
                "Jenis_Suara": item["voice"],
                "Weight_Analisis": item["weight"],
                "SeedQuery": q,
            })
            added += 1
        print(f"   → +{added} (total {len(rows)})")
    return rows


def save_outputs(rows: List[Dict[str, Any]], negeri: str) -> Path:
    CRAWL_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    tag = negeri.replace(" ", "_")
    csv_path = CRAWL_DIR / f"PRN_Chinese_News_{tag}_{ts}.csv"
    df = pd.DataFrame(rows)
    if df.empty:
        df = pd.DataFrame(columns=["Platform", "Text", "URL", "Negeri", "Jenis_Suara"])
    df.to_csv(csv_path, index=False, encoding="utf-8")

    by_negeri = df.groupby("Negeri").size().to_dict() if "Negeri" in df.columns and not df.empty else {}
    by_voice = df.groupby("Jenis_Suara").size().to_dict() if not df.empty else {}
    summary = {
        "fetched_at": datetime.now().isoformat(timespec="seconds"),
        "csv_file": str(csv_path.relative_to(ROOT)),
        "filter_negeri": negeri,
        "total_rows": len(df),
        "by_negeri": by_negeri,
        "by_voice": by_voice,
        "note": "Pisah analisis ikut Negeri + Weight (ANALYSIS_RULES dalam Excel)",
    }
    SUMMARY_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"💾 {csv_path} ({len(df)} rows)")
    return csv_path


async def main_async(negeri: str) -> int:
    key = negeri.lower().replace("_", " ")
    if key not in QUERY_PACK:
        raise SystemExit(f"Negeri tidak sah: {negeri}. Guna: all | negeri sembilan | johor | melaka")
    items = []
    if key == "all":
        for k in ("negeri sembilan", "johor", "melaka", "all"):
            items.extend(QUERY_PACK[k])
    else:
        items.extend(QUERY_PACK[key])
        items.extend(QUERY_PACK["all"])
    rows = await crawl_queries(items)
    save_outputs(rows, key)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Crawl PRN Chinese narrative news (NS/Melaka/Johor)")
    parser.add_argument(
        "--negeri",
        default="all",
        choices=["all", "negeri sembilan", "johor", "melaka"],
        help="Negeri untuk crawl (default: all = 3 negeri + cross-state)",
    )
    args = parser.parse_args()
    return asyncio.run(main_async(args.negeri))


if __name__ == "__main__":
    raise SystemExit(main())
