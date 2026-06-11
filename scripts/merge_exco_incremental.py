#!/usr/bin/env python3
"""Append new crawl CSV(s) to PAS Break EXCO master with dedup + event window."""

import argparse
import json
from datetime import datetime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "data/projects/political/pas_break_2026"
MASTER_DIR = PROJECT / "master"

EVENT_START = pd.Timestamp("2026-06-09", tz="UTC")
EVENT_END = pd.Timestamp("2026-06-11 23:59:59", tz="UTC")

MASTER_COLS = [
    "Platform", "Type", "ID", "Text", "URL", "Parent_Post_URL", "Parent_Post_ID",
    "Sentiment", "Date", "likes", "shares", "comments_count", "views",
    "sentiment_score", "total_engagement", "crawl_source",
    "mentions_pas", "mentions_bersatu", "narrative_split",
]


def parse_dates(series: pd.Series) -> pd.Series:
    from backend.utils.crawl_records import parse_crawl_dates
    return parse_crawl_dates(series)


def add_flags(df: pd.DataFrame) -> pd.DataFrame:
    t = df["Text"].fillna("").astype(str).str.lower()
    df["mentions_pas"] = t.str.contains(r"\bpas\b|parti islam", regex=True, na=False)
    df["mentions_bersatu"] = t.str.contains(
        r"\bbersatu\b|ppbm|perikatan nasional|\bpn\b", regex=True, na=False
    )
    df["narrative_split"] = t.str.contains(
        r"putus|berpisah|perpecahan|retak|khianat|pecah|split|hentikan kerjasama", regex=True, na=False
    )
    return df


def align(df: pd.DataFrame, crawl_source: str | None) -> pd.DataFrame:
    df = df.copy()
    if crawl_source:
        df["crawl_source"] = crawl_source
    elif "crawl_source" not in df.columns:
        df["crawl_source"] = "unknown"
    df["Text"] = df.get("Text", df.get("text", "")).fillna("").astype(str)
    df["Platform"] = df["Platform"].astype(str).str.lower()
    for col in MASTER_COLS:
        if col not in df.columns:
            df[col] = "" if col not in ("likes", "shares", "comments_count", "views", "sentiment_score", "total_engagement", "mentions_pas", "mentions_bersatu", "narrative_split") else 0
    return df[MASTER_COLS]


def dedupe(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["_key"] = (
        df["Platform"].astype(str).str.lower() + "|"
        + df["URL"].fillna("").astype(str) + "|"
        + df["Text"].fillna("").astype(str).str[:120]
    )
    before = len(df)
    out = df.drop_duplicates(subset=["_key"], keep="first").drop(columns=["_key"])
    print(f"  Dedup: {before:,} → {len(out):,} (−{before - len(out):,})")
    return out


def platform_summary(df: pd.DataFrame) -> dict:
    return df.groupby(df["Platform"].str.lower()).size().to_dict()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True, help="Existing EXCO FULL master CSV")
    parser.add_argument("--add", action="append", required=True, help="Crawl CSV to append")
    parser.add_argument("--source", action="append", required=True, help="crawl_source label per --add file")
    args = parser.parse_args()

    base_path = Path(args.base)
    if not base_path.is_absolute():
        base_path = ROOT / base_path

    print(f"📥 Base: {base_path.name}")
    merged = pd.read_csv(base_path, low_memory=False)
    merged = align(merged, None)

    for path, source in zip(args.add, args.source):
        p = Path(path)
        if not p.is_absolute():
            p = ROOT / p
        print(f"📥 Adding: {p.name} ({source})")
        chunk = pd.read_csv(p, low_memory=False)
        chunk = align(chunk, source)
        merged = pd.concat([merged, chunk], ignore_index=True)

    merged = dedupe(merged)
    merged = add_flags(merged)

    dates = parse_dates(merged["Date"])
    merged["in_event_window"] = dates.between(EVENT_START, EVENT_END, inclusive="both")
    event_df = merged[merged["in_event_window"]].drop(columns=["in_event_window"])
    merged = merged.drop(columns=["in_event_window"])

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    full_path = MASTER_DIR / f"PAS_Break_Master_EXCO_{ts}.csv"
    event_path = MASTER_DIR / f"PAS_Break_Master_EXCO_EventJun9-11_{ts}.csv"
    readme_path = MASTER_DIR / f"PAS_Break_Master_EXCO_{ts}_README.txt"

    merged.to_csv(full_path, index=False, encoding="utf-8")
    event_df.to_csv(event_path, index=False, encoding="utf-8")

    posts = (merged["Type"].str.lower() == "post").sum()
    comments = (merged["Type"].str.lower() == "comment").sum()
    plat = platform_summary(merged)
    split_n = int(merged["narrative_split"].sum())

    readme = f"""PAS Break 2026 — EXCO Master Merge
Generated: {ts}

FULL: {full_path.name}
  Rows: {len(merged)} ({posts} posts + {comments} comments)
  Platforms: {plat}
  Split-relevant: {split_n}

EVENT (Jun 9-11): {event_path.name}
  Rows: {len(event_df)}

Sources appended this run:
"""
    for path, source in zip(args.add, args.source):
        readme += f"  - {source}: {Path(path).name}\n"
    readme += f"\nPrevious base: {base_path.name}\n"
    readme_path.write_text(readme, encoding="utf-8")

    meta_path = PROJECT / "metadata.json"
    if meta_path.exists():
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        meta.setdefault("masters", []).append({
            "file": f"master/{full_path.name}",
            "rows": len(merged),
            "saved_at": datetime.now().isoformat(),
            "note": f"EXCO merge + {', '.join(args.source)}",
        })
        meta["latest_exco_master"] = f"master/{full_path.name}"
        meta["latest_exco_event"] = f"master/{event_path.name}"
        meta["updated_at"] = datetime.now().isoformat()
        meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")

    print("\n✅ EXCO MERGE COMPLETE")
    print(f"   FULL:  {full_path} ({len(merged):,} rows)")
    print(f"   EVENT: {event_path} ({len(event_df):,} rows)")
    print(f"   Platforms: {plat}")


if __name__ == "__main__":
    main()
