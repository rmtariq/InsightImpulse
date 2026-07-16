#!/usr/bin/env python3
"""Crawl PRN Negeri Sembilan news (+ optional InsightPulse async API)."""
from __future__ import annotations

import asyncio
import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from prn_paths import crawls, reference, ensure_state_dirs  # noqa: E402

ensure_state_dirs("N9")
CRAWL_DIR = crawls("N9", "news")
SUMMARY_JSON = reference("N9") / "prn_n9_news_summary.json"
API_BASE = "http://localhost:8001"

QUERIES = [
    '"PRN Negeri Sembilan" OR "pilihan raya negeri sembilan" when:30d',
    '"SPR" "Negeri Sembilan" penamaan OR mengundi when:30d',
    'Aminuddin OR "Undang-empat" "Negeri Sembilan" when:30d',
    'PAS OR PN OR UMNO "Negeri Sembilan" PRN when:30d',
]


async def crawl_news_direct(max_per_query: int = 80) -> List[Dict[str, Any]]:
    from backend.data_crawlers.scrapling_adapter import ScraplingAdapter

    adapter = ScraplingAdapter()
    seen: set = set()
    rows: List[Dict[str, Any]] = []

    for q in QUERIES:
        print(f"📰 Crawling: {q[:70]}...")
        batch = await adapter._crawl_news(q, max_results=max_per_query, decode_urls=False)
        for r in batch:
            rid = r.get("ID") or r.get("URL")
            if rid in seen:
                continue
            seen.add(rid)
            rows.append(r)
        print(f"   → {len(batch)} articles ({len(rows)} total unique)")

    return rows


def save_crawl_csv(rows: List[Dict[str, Any]]) -> Path:
    CRAWL_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = CRAWL_DIR / f"PRN_N9_News_{ts}.csv"
    df = pd.DataFrame(rows)
    if df.empty:
        df = pd.DataFrame(columns=["Platform", "Type", "ID", "Text", "URL", "Date"])
    df.to_csv(out, index=False)
    print(f"💾 Saved: {out} ({len(df)} rows)")
    return out


# Relevansi Negeri Sembilan — kekalkan hanya berita berkaitan N9/PRN.
_NS_RELEVANT = re.compile(
    r"negeri sembilan|seremban|aminuddin|port dickson|bagan pinang|kuala pilah|"
    r"undang.?empat|prn n9|dun .*sembilan|\bn\.?\s*sembilan\b|"
    r"\b(nilai|rembau|jelebu|jempol|tampin|rasah|paroi|chembong|rantau|seri menanti)\b",
    re.I,
)
# Buang siaran akhbar global (token "PRN" memadan "PRNewswire" dll).
_PR_NOISE = re.compile(
    r"prnewswire|globenewswire|businesswire|einpresswire|accesswire|newswire|"
    r"market research|cagr|nasdaq|/prnewswire",
    re.I,
)


def _clean_headline(text: str) -> str:
    """Google News Text selalunya 'Tajuk. Tajuk&nbsp;&nbsp;Sumber' — ambil tajuk bersih."""
    s = str(text or "").split("&nbsp;")[0].strip()
    # Buang tajuk berganda 'X. X'
    half = len(s) // 2
    if half > 20 and s[:half].strip().rstrip(".") == s[half:].strip().rstrip("."):
        s = s[:half].strip()
    return s.rstrip(". ").strip()


def _headline_date_key(row: Dict[str, Any]) -> str:
    return str(row.get("Date") or "")


def build_summary(rows: List[Dict[str, Any]], csv_path: Path) -> dict:
    # 1) Tapis: relevan NS dan bukan siaran PR global.
    relevant = [
        r for r in rows
        if _NS_RELEVANT.search(str(r.get("Text", "")))
        and not _PR_NOISE.search(str(r.get("Text", "")) + " " + str(r.get("URL", "")))
    ]
    pool = relevant or rows  # fallback jika tapisan terlalu agresif

    texts = " ".join(str(r.get("Text", "")).lower() for r in pool)
    keywords = {
        "spr": texts.count("spr") + texts.count("suruhanjaya pilihan raya"),
        "penamaan": texts.count("penamaan"),
        "mengundi": texts.count("mengundi"),
        "pas": texts.count(" pas ") + texts.count("pas "),
        "umno": texts.count("umno"),
        "ph": texts.count(" ph ") + texts.count("pakatan harapan"),
        "aminuddin": texts.count("aminuddin"),
        "bubar": texts.count("bubar") + texts.count("pembubaran"),
    }

    # 2) Pilih headline ikut kebaruan (Date desc), dedupe tajuk serupa.
    ranked = sorted(pool, key=_headline_date_key, reverse=True)
    seen: set = set()
    top_headlines: List[dict] = []
    for r in ranked:
        clean = _clean_headline(r.get("Text", ""))
        norm = clean.lower()[:80]
        if not clean or norm in seen:
            continue
        seen.add(norm)
        top_headlines.append({"text": clean[:200], "url": r.get("URL"), "date": r.get("Date")})
        if len(top_headlines) >= 12:
            break

    return {
        "fetched_at": datetime.now().isoformat(timespec="seconds"),
        "csv_file": str(csv_path.relative_to(ROOT)),
        "total_articles": len(rows),
        "total_relevant": len(relevant),
        "queries": QUERIES,
        "keyword_hits": keywords,
        "top_headlines": top_headlines,
    }


def trigger_insightpulse_async() -> Optional[dict]:
    """Fire broader crawl via running InsightPulse backend (news + x + tiktok)."""
    payload = {
        "query": (
            '"PRN Negeri Sembilan" OR "pilihan raya negeri sembilan" OR '
            '"SPR Negeri Sembilan" OR Aminuddin OR "PAS Negeri Sembilan"'
        ),
        "platforms": ["news", "x", "tiktok", "facebook"],
        "analysis_type": "social_listening",
        "date_range": "30days",
        "dataset_size": 500,
        "use_crawl_strategy": True,
        "project_id": "PRN_N9",
        "analysis_focus": "comprehensive",
        "comment_sampling": "smart",
    }
    try:
        r = requests.post(f"{API_BASE}/analyze_async", json=payload, timeout=15)
        if r.status_code == 200:
            data = r.json()
            print(f"🚀 InsightPulse async task: {data.get('task_id')} (~{data.get('estimated_time_minutes')} min)")
            return data
        print(f"⚠️ InsightPulse API returned {r.status_code}: {r.text[:200]}")
    except requests.RequestException as exc:
        print(f"ℹ️ InsightPulse not running ({exc}) — direct news crawl only.")
    return None


async def main_async() -> int:
    api_task = trigger_insightpulse_async()
    rows = await crawl_news_direct()
    csv_path = save_crawl_csv(rows)
    summary = build_summary(rows, csv_path)
    if api_task:
        summary["insightpulse_task"] = api_task
    SUMMARY_JSON.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"📋 Summary: {SUMMARY_JSON}")
    return 0 if rows else 1


def main() -> int:
    return asyncio.run(main_async())


if __name__ == "__main__":
    raise SystemExit(main())
