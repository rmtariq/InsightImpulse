#!/usr/bin/env python3
"""
Gabung master PRN Johor+N9 — hybrid archive.

Layer (lama → baru, dedupe keep=last):
  1. PAS Break archive (Jun 12) — crawl awal / EXCO
  2. Combined manual-stop & PRN master pagi
  3. Batch 7 A/B/C (discourse gap)

Output: PRN_Johor_N9_master_<ts>.csv + pas_break + johor master copies
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
MYT = timezone(timedelta(hours=8))

COMBINED = ROOT / "data/combined"
MASTER_DIR = ROOT / "data/projects/political/pas_break_2026/master"
JOhor_DIR = ROOT / "data/projects/political/PRN/PRN_Johor/master"
SMART = ROOT / "data/smart_crawlers"

# Arkib crawl awal (paling lengkap)
ARCHIVE_PAS_BREAK = MASTER_DIR / "PAS_Break_Master_EXCO_Analyzed_20260612_031929.csv"
PRN_MORNING = COMBINED / "PRN_Johor_N9_master_20260621.csv"
MANUAL_STOP = COMBINED / "Combined_manual_stop_20260621_051322.csv"


def _align(df: pd.DataFrame, source: str, batch: str) -> pd.DataFrame:
    out = df.copy()
    if "Text" not in out.columns and "text" in out.columns:
        out["Text"] = out["text"]
    if "Text" not in out.columns:
        out["Text"] = ""
    out["Text"] = out["Text"].fillna("").astype(str)
    for col in ("Platform", "ID", "URL"):
        if col not in out.columns:
            out[col] = ""
        out[col] = out[col].fillna("").astype(str)
    out["crawl_source_file"] = source
    out["crawl_batch"] = batch
    for col in (
        "Parent_Post_URL", "Parent_Post_ID", "author", "author_followers",
        "sentiment_label", "sentiment_score", "sentiment_confidence", "emotion_primary",
        "total_engagement", "engagement_score", "likes", "comments_count", "shares", "views",
        "Sentiment", "detected_language", "demographic", "analysis_mode",
        "emotion_anger", "emotion_fear", "emotion_happy", "emotion_sadness",
        "emotion_love", "emotion_surprise", "narrative_split", "mentions_pas", "mentions_bersatu",
        "crawl_source", "crawl_source_file", "crawl_batch",
    ):
        if col not in out.columns:
            out[col] = ""
    return out


def _dedupe(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["_key"] = df["Platform"].str.lower() + "|" + df["ID"].astype(str)
    before = len(df)
    df = df.drop_duplicates(subset=["_key"], keep="last").drop(columns=["_key"])
    print(f"  Dedup: {before:,} → {len(df):,} (+{len(df) - before + (before - len(df)):,} net unique)")
    return df


def collect_sources(*, full_archive: bool = True) -> list[tuple[Path, str]]:
    """Susunan lama→baru supaya dedupe keep=last kekalkan data terkini."""
    items: list[tuple[Path, str]] = []

    if full_archive and ARCHIVE_PAS_BREAK.exists():
        items.append((ARCHIVE_PAS_BREAK, "archive_pas_break_jun12"))

    if MANUAL_STOP.exists():
        items.append((MANUAL_STOP, "archive_manual_stop_jun21"))

    if PRN_MORNING.exists():
        items.append((PRN_MORNING, "prn_master_jun21_am"))

    for tag, pat in (
        ("Batch7-A", "Combined_facebook_tiktok_20260621_155059.csv"),
        ("Batch7-B", "Combined_facebook_tiktok_20260621_155904.csv"),
    ):
        p = COMBINED / pat
        if p.exists():
            items.append((p, tag))

    for glob in (
        "facebook/facebook_umdap_20260621_182737.csv",
        "tiktok/tiktok_umdap_20260621_182737.csv",
    ):
        p = SMART / glob
        if p.exists():
            items.append((p, "Batch7-C-UMDAP"))

    if not any(t[1].startswith("Batch7-C") for t in items):
        for p in sorted(SMART.glob("**/facebook_umdap_20260621*.csv"))[-1:]:
            items.append((p, "Batch7-C-UMDAP"))
        for p in sorted(SMART.glob("**/tiktok_umdap_20260621*.csv"))[-1:]:
            items.append((p, "Batch7-C-UMDAP"))

    # Fallback: jika tiada layer asas, guna master terkini
    if not items:
        latest = sorted(COMBINED.glob("PRN_Johor_N9_master_*.csv"), key=lambda p: p.stat().st_mtime, reverse=True)
        if latest:
            items.append((latest[0], "master_latest"))

    return items


def main() -> int:
    p = argparse.ArgumentParser(description="Merge PRN N9+Johor hybrid master")
    p.add_argument("--prn-only", action="store_true", help="Skip PAS Break archive (4.8k PRN-only merge)")
    args = p.parse_args()

    sources = collect_sources(full_archive=not args.prn_only)
    if not sources:
        print("❌ Tiada fail sumber", file=sys.stderr)
        return 1

    print(f"📦 Hybrid merge · {len(sources)} layer(s)\n")
    parts = []
    seen_paths: set[Path] = set()
    for path, batch in sources:
        if path in seen_paths:
            continue
        seen_paths.add(path)
        print(f" + [{batch}] {path.name} ({path.stat().st_size // 1024} KB)")
        parts.append(_align(pd.read_csv(path, low_memory=False), path.name, batch))

    df = pd.concat(parts, ignore_index=True)
    df = _dedupe(df)

    by_batch = df["crawl_batch"].value_counts().to_dict()
    print("\n  Layer selepas dedupe:")
    for k, v in sorted(by_batch.items(), key=lambda x: -x[1]):
        print(f"    {k}: {v:,}")

    ts = datetime.now(MYT).strftime("%Y%m%d_%H%M%S")
    tag = "hybrid" if not args.prn_only else "prn"
    out_combined = COMBINED / f"PRN_Johor_N9_master_{tag}_{ts}.csv"
    df.to_csv(out_combined, index=False, encoding="utf-8")

    exco = MASTER_DIR / f"PAS_Break_Master_EXCO_Analyzed_{ts}.csv"
    johor = JOhor_DIR / f"PRN_Johor_Master_{ts}.csv"
    MASTER_DIR.mkdir(parents=True, exist_ok=True)
    JOhor_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(exco, index=False, encoding="utf-8")
    df.to_csv(johor, index=False, encoding="utf-8")

    print(f"\n✅ Hybrid master: {out_combined.name} ({len(df):,} data points)")
    print(f"   pas_break: {exco.name}")
    print(f"   johor:     {johor.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
