#!/usr/bin/env python3
"""Crawl ADUN social seeds from PRN2023 Excel — news mentions per kerusi + optional InsightPulse."""
from __future__ import annotations

import asyncio
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from prn_paths import crawls, reference, reports, resolve_existing, ensure_state_dirs  # noqa: E402
from dun_headline_quality import build_display_headlines  # noqa: E402

ensure_state_dirs("N9")
EXCEL = ROOT / "JITP_2026/Master_File/PRN2023_NegeriSembilan_v2.xlsx"
CRAWL_DIR = crawls("N9", "adun_seeds")
SUMMARY_JSON = reference("N9") / "prn_n9_adun_social_summary.json"
SEATS_JSON = resolve_existing(
    reports("N9") / "seats/n9_seats_export.json",
    ROOT / "data/projects/political/pas_break_2026/reports/n9_seats_export.json",
)
API_BASE = "http://localhost:8001"

PRIORITY_CODES = {
    "N05", "N25", "N31",  # defend
    "N03", "N09", "N18",  # winnable
    "N02", "N19", "N27", "N35", "N20", "N34",  # tough
}

MEDIA_SEEDS = [
    {"code": "MEDIA", "name": "Negeri FM", "query": '"Negeri FM" "Negeri Sembilan" PRN when:30d'},
    {"code": "MEDIA", "name": "Utusan NS", "query": 'Utusan "Negeri Sembilan" PRN when:30d'},
    {"code": "MEDIA", "name": "Sinar Harian NS", "query": '"Sinar Harian" "Negeri Sembilan" when:30d'},
]


def _clean_social(val: Any) -> str:
    s = str(val or "").strip()
    if not s or s.lower() in ("nan", "—", "-", "cari di fb", "cari di tiktok", "cari di x"):
        return ""
    return s


def load_seeds() -> List[dict]:
    if not EXCEL.exists():
        raise FileNotFoundError(EXCEL)

    keputusan = pd.read_excel(EXCEL, sheet_name="Keputusan Penuh", header=2)
    keputusan.columns = [re.sub(r"\s+", "_", str(c).strip().lower()) for c in keputusan.columns]
    keputusan = keputusan.dropna(subset=["kod_dun"])

    adun = pd.read_excel(EXCEL, sheet_name="ADUN Terpilih", header=1)
    adun.columns = [re.sub(r"[^a-z0-9_]", "_", str(c).strip().lower()) for c in adun.columns]
    adun = adun.dropna(subset=["kod_dun"])

    merged = keputusan.merge(adun, on="kod_dun", how="left", suffixes=("_k", "_a"))
    seeds: List[dict] = []

    for _, r in merged.iterrows():
        code = str(r["kod_dun"]).strip()
        name = str(r.get("kawasan_dun_k") or r.get("kawasan_dun") or "").strip()
        adun_name = str(r.get("nama_adun") or r.get("nama_pemenang_k") or r.get("nama_pemenang") or "").strip()
        fb = _clean_social(r.get("facebook"))
        tt = _clean_social(r.get("tiktok"))
        xh = _clean_social(r.get("x_twitter"))
        first = adun_name.split()[0] if adun_name else name

        queries = [
            f'"{adun_name}" "{name}" "Negeri Sembilan" when:30d',
            f'"{name}" DUN PRN "Negeri Sembilan" when:30d',
        ]
        if tt.startswith("@"):
            queries.append(f'{tt} "Negeri Sembilan" when:30d')
        if xh.startswith("@"):
            queries.append(f'{xh} PRN when:30d')

        seeds.append({
            "code": code,
            "kawasan": name,
            "namaAdun": adun_name,
            "parti": str(r.get("parti_k") or r.get("parti") or "").strip(),
            "facebookUrl": fb,
            "tiktokHandle": tt,
            "xHandle": xh,
            "queries": queries,
            "priority": code in PRIORITY_CODES,
            "maxPerQuery": 12 if code in PRIORITY_CODES else 5,
        })

    seeds.extend(MEDIA_SEEDS)
    return seeds


async def crawl_seed_queries(seeds: List[dict]) -> tuple[List[dict], Dict[str, List[dict]]]:
    from backend.data_crawlers.scrapling_adapter import ScraplingAdapter

    adapter = ScraplingAdapter()
    all_rows: List[dict] = []
    by_seat: Dict[str, List[dict]] = {}
    seen: set = set()

    for seed in seeds:
        code = seed["code"]
        bucket = by_seat.setdefault(code, [])
        for q in seed.get("queries", [seed.get("query", "")]):
            if not q:
                continue
            label = seed.get("namaAdun") or seed.get("name", code)
            print(f"🔍 {code} {label[:30]}: {q[:65]}...")
            batch = await adapter._crawl_news(q, max_results=seed.get("maxPerQuery", 8), decode_urls=False)
            added = 0
            for row in batch:
                rid = row.get("ID") or row.get("URL")
                if rid in seen:
                    continue
                seen.add(rid)
                row = dict(row)
                row["SeedCode"] = code
                row["SeedLabel"] = label
                row["SeedQuery"] = q
                all_rows.append(row)
                bucket.append(row)
                added += 1
            print(f"   → +{added} ({len(bucket)} for {code})")

    return all_rows, by_seat


def build_summary(seeds: List[dict], by_seat: Dict[str, List[dict]], csv_path: Path) -> dict:
    per_seat = []
    for seed in seeds:
        if seed["code"] == "MEDIA":
            continue
        code = seed["code"]
        posts = by_seat.get(code, [])
        texts = [str(p.get("Text", "")) for p in posts]
        per_seat.append({
            "code": code,
            "kawasan": seed.get("kawasan", ""),
            "namaAdun": seed.get("namaAdun", ""),
            "parti": seed.get("parti", ""),
            "priority": seed.get("priority", False),
            "facebookUrl": seed.get("facebookUrl", ""),
            "tiktokHandle": seed.get("tiktokHandle", ""),
            "xHandle": seed.get("xHandle", ""),
            "newsMentions": len(posts),
            "hasSocialSeed": bool(seed.get("facebookUrl") or seed.get("tiktokHandle") or seed.get("xHandle")),
            "statusSocialFb": "seed" if seed.get("facebookUrl") else "pending",
            "statusSocialTiktok": "seed" if seed.get("tiktokHandle") else "pending",
            "statusSocialX": "seed" if seed.get("xHandle") else "pending",
            "topHeadlines": [
                t[:160]
                for t in texts
                if build_display_headlines(seed, crawl_headlines=[t])["quality"] != "none"
            ][:3],
        })

    media_rows = by_seat.get("MEDIA", [])
    return {
        "fetched_at": datetime.now().isoformat(timespec="seconds"),
        "source_excel": str(EXCEL),
        "csv_file": str(csv_path.relative_to(ROOT)),
        "total_rows": sum(len(v) for v in by_seat.values()),
        "seats_crawled": len([s for s in per_seat if s["newsMentions"] > 0]),
        "priority_seats": sorted(PRIORITY_CODES),
        "seeds_with_handles": sum(1 for s in per_seat if s["hasSocialSeed"]),
        "per_seat": per_seat,
        "media_mentions": len(media_rows),
        "insightpulse_task": None,
    }


def trigger_insightpulse(seeds: List[dict]) -> Optional[dict]:
    names = [s["namaAdun"] for s in seeds if s.get("namaAdun") and s["code"] != "MEDIA"][:8]
    query = (
        '"PRN Negeri Sembilan" OR "pilihan raya negeri sembilan" OR '
        + " OR ".join(f'"{n.split()[0]}"' for n in names if n)
    )
    payload = {
        "query": query[:500],
        "platforms": ["news", "x", "tiktok", "facebook"],
        "analysis_type": "social_listening",
        "date_range": "30days",
        "dataset_size": 400,
        "use_crawl_strategy": True,
        "project_id": "pas_break_2026",
        "analysis_focus": "comprehensive",
        "comment_sampling": "smart",
    }
    try:
        r = requests.post(f"{API_BASE}/analyze_async", json=payload, timeout=15)
        if r.status_code == 200:
            data = r.json()
            print(f"🚀 InsightPulse async: {data.get('task_id')} (~{data.get('estimated_time_minutes')} min)")
            return data
    except requests.RequestException as exc:
        print(f"ℹ️ InsightPulse not running ({exc}) — news seed crawl only.")
    return None


def save_csv(rows: List[dict]) -> Path:
    CRAWL_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = CRAWL_DIR / f"PRN_N9_ADUN_Seeds_{ts}.csv"
    df = pd.DataFrame(rows)
    if df.empty:
        df = pd.DataFrame(columns=["Platform", "Type", "ID", "Text", "URL", "Date", "SeedCode", "SeedLabel"])
    df.to_csv(out, index=False)
    print(f"💾 Saved: {out} ({len(df)} rows)")
    return out


async def main_async() -> int:
    seeds = load_seeds()
    print(f"📋 Loaded {len(seeds)} seeds ({sum(1 for s in seeds if s.get('priority'))} priority kerusi)")
    api = trigger_insightpulse(seeds)
    rows, by_seat = await crawl_seed_queries(seeds)
    csv_path = save_csv(rows)
    summary = build_summary(seeds, by_seat, csv_path)
    if api:
        summary["insightpulse_task"] = api
    SUMMARY_JSON.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"📋 Summary: {SUMMARY_JSON}")
    print(f"✅ {summary['seats_crawled']}/36 kerusi ada mention berita · {summary['total_rows']} rows total")
    return 0


def main() -> int:
    return asyncio.run(main_async())


if __name__ == "__main__":
    raise SystemExit(main())
