#!/usr/bin/env python3
"""
PRN Chinese Narrative — Manual crawl runner (A→Z)

TIADA automatik / cron — anda jalankan script bila sedia dan pantau terminal.
Keywords load dari Excel (Downloads atau reference/) setiap kali script di-run.

Contoh:
  python3 scripts/crawl_prn_chinese_daily.py --slot morning --news-only
  python3 scripts/crawl_prn_chinese_daily.py --slot midday --news-only
  python3 scripts/crawl_prn_chinese_daily.py --stream S2B2 --with-socmed
  python3 scripts/build_prn_chinese_dashboard_dataset.py   # selepas crawl

Panduan: reference/CRAWL_MANUAL_ARAHAN.txt

Kos Apify (--with-socmed sahaja bila anda sengaja luluskan):
  • --news-only     → percuma (RSS/Google News)
  • --with-socmed   → Apify · default 800 · --full-size untuk 2000
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

# Muat .env supaya APIFY_API_TOKEN tersedia (sama seperti start_full_app.sh)
try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
except ImportError:
    pass

import os  # noqa: E402

from prn_chinese_keywords import (  # noqa: E402
    DAILY_SLOTS,
    KeywordStream,
    filter_streams,
    load_streams,
)
from prn_paths import crawls, ensure_state_dirs  # noqa: E402

API_BASE = "http://localhost:8001"
NEWS_DIR = crawls("N9", "chinese_news")
SUMMARY_PATH = ROOT / "data/projects/political/pas_break_2026/reference/prn_chinese_daily_summary.json"

STATE_CRAWL = {
    "Negeri Sembilan": ("N9", crawls("N9", "social")),
    "Johor": ("Johor", crawls("Johor", "social")),
    "Melaka": ("Melaka", crawls("Melaka", "social")),
    "Semua": ("N9", crawls("N9", "social")),
}


def _since_date(days: int = 30) -> str:
    return (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")


async def crawl_news_stream(
    stream: KeywordStream,
    max_per_query: int = 60,
    seen: Optional[set] = None,
) -> List[Dict[str, Any]]:
    from backend.data_crawlers.scrapling_adapter import ScraplingAdapter

    adapter = ScraplingAdapter()
    if seen is None:
        seen = set()
    rows: List[Dict[str, Any]] = []
    batch = await adapter._crawl_news(stream.query, max_results=max_per_query, decode_urls=False)
    for row in batch:
        rid = row.get("ID") or row.get("URL")
        if rid in seen:
            continue
        seen.add(rid)
        rows.append({
            **row,
            "QueryID": stream.stream_id,
            "Negeri": stream.negeri,
            "Jenis_Suara": stream.jenis,
            "Weight_Analisis": stream.prioriti,
            "SeedQuery": stream.query,
            "StreamLabel": stream.label,
        })
    return rows


def _apify_ready() -> tuple[bool, str]:
    token = os.getenv("APIFY_API_TOKEN") or os.getenv("APIFY_TOKEN")
    if not token or not str(token).strip():
        return False, "APIFY_API_TOKEN tiada — pastikan .env wujud di root projek"
    if str(token).startswith("your_"):
        return False, "APIFY_API_TOKEN masih placeholder dalam .env"
    return True, ""


async def crawl_socmed_stream(
    stream: KeywordStream,
    dataset_size: int = 800,
    days: int = 30,
) -> List[Dict[str, Any]]:
    """Socmed via SimpleApifyAdapter (perlukan APIFY token)."""
    from backend.data_crawlers.simple_apify_adapter import SimpleApifyAdapter

    platforms = [p for p in stream.platforms if p != "news"]
    if not platforms:
        return []

    adapter = SimpleApifyAdapter()
    since = _since_date(days)
    result = await adapter.crawl_with_strategy(
        platforms=platforms,
        query=stream.query,
        dataset_size=dataset_size,
        analysis_type="social_listening",
        since_date=since,
    )
    rows: List[Dict[str, Any]] = []
    for plat, records in (result.get("results") or {}).items():
        for rec in records or []:
            rows.append({
                **rec,
                "Platform": plat,
                "QueryID": stream.stream_id,
                "Negeri": stream.negeri,
                "Jenis_Suara": stream.jenis,
                "Weight_Analisis": stream.prioriti,
                "SeedQuery": stream.query,
                "StreamLabel": stream.label,
            })
    return rows


def trigger_socmed_via_api(
    stream: KeywordStream,
    dataset_size: int = 800,
    project_id: str = "pas_break_2026",
) -> Optional[str]:
    """Alternatif: hantar ke InsightPulse backend jika ./start_full_app.sh sedang jalan."""
    platforms = stream.platforms
    payload = {
        "query": stream.query,
        "platforms": platforms,
        "analysis_type": "social_listening",
        "date_range": "30days",
        "dataset_size": dataset_size,
        "use_crawl_strategy": True,
        "project_id": project_id,
        "analysis_focus": "comprehensive",
        "comment_sampling": "smart",
    }
    try:
        r = requests.post(f"{API_BASE}/analyze_async", json=payload, timeout=20)
        if r.status_code == 200:
            task_id = r.json().get("task_id")
            print(f"   🚀 API task {task_id} ({', '.join(platforms)})")
            return task_id
    except requests.RequestException as exc:
        print(f"   ℹ️ API tidak tersedia ({exc})")
    return None


def save_stream_csv(rows: List[Dict[str, Any]], stream: KeywordStream, layer: str) -> Optional[Path]:
    if not rows:
        return None
    _, social_dir = STATE_CRAWL.get(stream.negeri, STATE_CRAWL["Semua"])
    out_dir = NEWS_DIR if layer == "news" else social_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    fname = f"PRN_Chinese_{stream.stream_id}_{layer}_{ts}.csv"
    path = out_dir / fname
    pd.DataFrame(rows).to_csv(path, index=False, encoding="utf-8")
    return path


def rebuild_dashboard() -> int:
    sys.path.insert(0, str(ROOT / "n9_chinese_narrative_dashboard"))
    from utils.build_dataset import build_dataset  # noqa: E402

    df = build_dataset()
    print(f"📊 Dashboard dataset: {len(df):,} rows")
    if "state" in df.columns:
        print(df["state"].value_counts().to_string())
    return len(df)


async def run_slot(
    streams: List[KeywordStream],
    *,
    news_only: bool = False,
    with_socmed: bool = False,
    via_api: bool = False,
    dataset_size: int = 800,
    max_news_per_query: int = 60,
    rebuild: bool = False,
) -> dict:
    ensure_state_dirs("N9")
    ensure_state_dirs("Johor")
    ensure_state_dirs("Melaka")

    all_news: List[Dict[str, Any]] = []
    seen: set = set()
    saved_files: List[str] = []
    api_tasks: List[str] = []
    stats: Dict[str, Any] = {
        "started_at": datetime.now().isoformat(timespec="seconds"),
        "streams_total": len(streams),
        "news_rows": 0,
        "socmed_rows": 0,
        "files": [],
    }

    if with_socmed:
        ok, reason = _apify_ready()
        if not ok:
            print(f"\n⚠️ Socmed dilangkau: {reason}")
            print("   → Guna ./start_full_app.sh + crawl manual UI, atau isi APIFY_API_TOKEN dalam .env")
            with_socmed = False

    for i, stream in enumerate(streams, 1):
        print(f"\n[{i}/{len(streams)}] {stream.stream_id} — {stream.label} ({stream.negeri})")
        print(f"   Q: {stream.query[:90]}...")

        # News — sentiasa percuma
        if "news" in stream.platforms:
            news_rows = await crawl_news_stream(stream, max_per_query=max_news_per_query, seen=seen)
            all_news.extend(news_rows)
            stats["news_rows"] += len(news_rows)
            print(f"   📰 News: +{len(news_rows)}")
            f = save_stream_csv(news_rows, stream, "news")
            if f:
                saved_files.append(str(f))

        if news_only:
            continue

        socmed_plats = [p for p in stream.platforms if p != "news"]
        if not socmed_plats:
            continue

        if via_api:
            tid = trigger_socmed_via_api(stream, dataset_size=dataset_size)
            if tid:
                api_tasks.append(tid)
            continue

        if with_socmed:
            print(f"   📱 Socmed ({', '.join(socmed_plats)}) — dataset {dataset_size}...")
            try:
                soc_rows = await crawl_socmed_stream(stream, dataset_size=dataset_size)
                stats["socmed_rows"] += len(soc_rows)
                print(f"   📱 Socmed: +{len(soc_rows)}")
                if not soc_rows:
                    print("   ℹ️  0 hasil — semak kredit Apify / token / log di atas")
                f = save_stream_csv(soc_rows, stream, "social")
                if f:
                    saved_files.append(str(f))
            except Exception as exc:
                err = str(exc)
                if "x402" in err or "payment" in err.lower() or "APIFY" in err.upper():
                    print("   ❌ Apify: token/kredit — hentikan socmed batch ini")
                    print("      Guna InsightPulse UI: ./start_full_app.sh")
                    with_socmed = False
                else:
                    print(f"   ⚠️ Socmed gagal: {exc}")

    # Combined news snapshot (for build_dataset latest all-file)
    if all_news:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        combined = NEWS_DIR / f"PRN_Chinese_News_all_{ts}.csv"
        NEWS_DIR.mkdir(parents=True, exist_ok=True)
        news_df = pd.DataFrame(all_news)
        news_df.to_csv(combined, index=False, encoding="utf-8")
        saved_files.append(str(combined))
        print(f"\n💾 Combined news: {combined} ({len(all_news)} rows)")
        # Salinan ikut negeri → PRN_Johor / PRN_Melaka (pariti dengan N9)
        for negeri, state_key in (
            ("Johor", "Johor"),
            ("Melaka", "Melaka"),
            ("Negeri Sembilan", "N9"),
        ):
            sub = news_df[news_df["Negeri"].astype(str) == negeri]
            if sub.empty:
                continue
            state_dir = crawls(state_key, "chinese_news")
            state_dir.mkdir(parents=True, exist_ok=True)
            state_path = state_dir / f"PRN_Chinese_News_{state_key}_{ts}.csv"
            sub.to_csv(state_path, index=False, encoding="utf-8")
            saved_files.append(str(state_path))
            print(f"   ↳ {state_key}: {state_path.name} ({len(sub)} rows)")

    if rebuild:
        print("\n🔄 Rebuild dashboard dataset...")
        rebuild_dashboard()

    stats["finished_at"] = datetime.now().isoformat(timespec="seconds")
    stats["files"] = saved_files
    stats["api_tasks"] = api_tasks
    SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_PATH.write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"📋 Summary: {SUMMARY_PATH}")
    return stats


def main() -> int:
    parser = argparse.ArgumentParser(description="PRN Chinese Narrative daily crawl")
    parser.add_argument(
        "--slot",
        default="morning",
        choices=list(DAILY_SLOTS.keys()) + ["news-only"],
        help="Rotasi harian: morning | midday | evening | tinggi | full | news-only",
    )
    parser.add_argument("--excel", help="Path ke Excel keywords (auto-detect jika tiada)")
    parser.add_argument("--negeri", choices=["johor", "melaka", "negeri sembilan"], help="Hadkan satu negeri")
    parser.add_argument("--stream", action="append", dest="streams", help="Stream ID spesifik (S2B2)")
    parser.add_argument("--news-only", action="store_true", help="News RSS sahaja — percuma, cepat")
    parser.add_argument("--with-socmed", action="store_true", help="Crawl FB/X via Apify (direct adapter)")
    parser.add_argument("--via-api", action="store_true", help="Hantar socmed ke InsightPulse API (port 8001)")
    parser.add_argument("--dataset-size", type=int, default=800, help="Saiz dataset socmed harian (default 800)")
    parser.add_argument("--full-size", action="store_true", help="Guna dataset 2000 (crawl penuh)")
    parser.add_argument("--max-news", type=int, default=60, help="Max artikel news per query")
    parser.add_argument("--rebuild", action="store_true", help="Gabung CSV → dashboard (default: TIDAK — jalankan build sendiri)")
    parser.add_argument("--list", action="store_true", help="Senaraikan stream & slot")
    args = parser.parse_args()

    all_streams, source = load_streams(args.excel)
    print(f"📂 Keywords: {source} ({len(all_streams)} streams)")

    if args.list:
        print("\n=== SLOTS ===")
        for name, cfg in DAILY_SLOTS.items():
            ids = cfg.get("stream_ids") or ["ALL"]
            print(f"  {name:8} — {cfg['label']}: {', '.join(ids) if isinstance(ids, list) else ids}")
        print("\n=== STREAMS ===")
        for s in all_streams:
            print(f"  {s.stream_id} [{s.prioriti}] {s.negeri} | {','.join(s.platforms)} | {s.query[:70]}...")
        return 0

    slot = "full" if args.slot == "news-only" else args.slot
    selected = filter_streams(all_streams, slot=slot, negeri=args.negeri)
    if args.streams:
        id_set = set(args.streams)
        selected = [s for s in all_streams if s.stream_id in id_set]

    if not selected:
        print("❌ Tiada stream dipilih.")
        return 1

    cfg = DAILY_SLOTS.get(slot, {})
    print(f"🕐 Slot: {args.slot} — {cfg.get('label', slot)} ({len(selected)} stream)")

    ds = 2000 if args.full_size else args.dataset_size
    news_only = args.news_only or args.slot == "news-only"

    if args.with_socmed and not news_only:
        print(f"💰 Socmed AKTIF — dataset {ds} per stream (kos Apify)")
    elif not news_only:
        print("ℹ️ Socmed dimatikan — tambah --with-socmed atau --via-api untuk FB/X")

    asyncio.run(run_slot(
        selected,
        news_only=news_only,
        with_socmed=args.with_socmed,
        via_api=args.via_api,
        dataset_size=ds,
        max_news_per_query=args.max_news,
        rebuild=args.rebuild,
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
