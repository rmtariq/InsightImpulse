#!/usr/bin/env python3
"""Run sentiment + emotion on EXCO master rows missing labels; add geo/narrative flags."""

import argparse
import asyncio
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "web_backend"))

from web_backend.simple_app import initialize_models, process_platform_data  # noqa: E402


def needs_sentiment(df: pd.DataFrame) -> pd.Series:
    if "sentiment_label" not in df.columns:
        return pd.Series(True, index=df.index)
    lab = df["sentiment_label"].fillna("").astype(str).str.strip().str.lower()
    empty = lab.isin(["", "nan", "none"])
    if "sentiment_score" in df.columns:
        empty = empty | (df["sentiment_score"].fillna(0) == 0)
    return empty


def add_geo_narrative(df: pd.DataFrame) -> pd.DataFrame:
    t = df["Text"].fillna("").astype(str).str.lower()
    df["geo_johor"] = t.str.contains(
        r"johor|\bjb\b|muafakat nasional johor|prn johor", regex=True, na=False
    )
    df["geo_melaka"] = t.str.contains(r"melaka|malacca|prn melaka", regex=True, na=False)
    df["geo_ns"] = t.str.contains(
        r"negeri sembilan|\bns\b|aminuddin harun|muslimatpasn9|prn negeri sembilan",
        regex=True,
        na=False,
    )
    df["narrative_solo"] = t.str.contains(
        r"pas solo|pas bergerak solo|gerak solo|plot sd", regex=True, na=False
    )
    if "narrative_split" not in df.columns:
        df["narrative_split"] = t.str.contains(
            r"putus|berpisah|perpecahan|retak|khianat|pecah|split|hentikan kerjasama",
            regex=True,
            na=False,
        )
    return df


def analyze_missing(df: pd.DataFrame, *, posts_only: bool = False) -> pd.DataFrame:
    mask = needs_sentiment(df)
    if posts_only and "Type" in df.columns:
        mask = mask & (df["Type"].str.lower() == "post")
    n = int(mask.sum())
    if n == 0:
        print("✅ No rows need sentiment analysis")
        return df

    print(f"🤖 Analyzing {n:,} rows (posts_only={posts_only})...")
    subset = df.loc[mask].copy()
    process_platform_data(subset, "mixed", "")
    for col in subset.columns:
        df.loc[mask, col] = subset[col].values
    print(f"✅ Sentiment complete for {n:,} rows")
    return df


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--full",
        default="data/projects/political/pas_break_2026/master/PAS_Break_Master_EXCO_20260611_230220.csv",
    )
    parser.add_argument(
        "--event",
        default="data/projects/political/pas_break_2026/master/PAS_Break_Master_EXCO_EventJun9-11_20260611_230220.csv",
    )
    parser.add_argument("--posts-only", action="store_true", help="Analyze posts only (faster)")
    parser.add_argument("--event-only", action="store_true", help="Skip full master update")
    args = parser.parse_args()

    print("🤖 Loading sentiment + emotion models...")
    asyncio.run(initialize_models())

    event_path = ROOT / args.event
    full_path = ROOT / args.full
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    print(f"📥 EVENT: {event_path.name}")
    event = pd.read_csv(event_path, low_memory=False)
    before = int(needs_sentiment(event).sum())
    print(f"   Rows needing sentiment: {before:,} / {len(event):,}")

    event = analyze_missing(event, posts_only=args.posts_only)
    event = add_geo_narrative(event)

    out_event = event_path.with_name(
        event_path.stem.replace("_20260611_230220", f"_Analyzed_{ts}") + ".csv"
    )
    if "_Analyzed_" not in event_path.stem:
        out_event = event_path.parent / f"PAS_Break_Master_EXCO_EventJun9-11_Analyzed_{ts}.csv"
    event.to_csv(out_event, index=False, encoding="utf-8")
    print(f"💾 EVENT analyzed: {out_event} ({len(event):,} rows)")

    posts = event[event["Type"].str.lower() == "post"] if "Type" in event.columns else event
    if "sentiment_label" in posts.columns:
        print("📊 Event POST sentiment:", posts["sentiment_label"].value_counts().to_dict())

    if not args.event_only and full_path.exists():
        print(f"\n📥 FULL: {full_path.name}")
        full = pd.read_csv(full_path, low_memory=False)
        update_cols = [
            c for c in event.columns
            if c in full.columns
            and c not in ("Platform", "Type", "ID", "Text", "URL", "Date")
        ]
        ev_idx = event.drop_duplicates(subset=["ID"]).set_index("ID", drop=False)
        ids = full["ID"].astype(str)
        hit = ids.isin(ev_idx.index.astype(str))
        for col in update_cols:
            mapped = ids.map(ev_idx[col].astype(object))
            full.loc[hit, col] = mapped[hit].values
        still = int(needs_sentiment(full).sum())
        print(f"   Full rows still missing sentiment: {still:,} (outside event window)")
        out_full = full_path.parent / f"PAS_Break_Master_EXCO_Analyzed_{ts}.csv"
        full.to_csv(out_full, index=False, encoding="utf-8")
        print(f"💾 FULL updated: {out_full} ({len(full):,} rows)")

    print(f"\n✅ Done. Use for dashboard:\n   {out_event}")


if __name__ == "__main__":
    main()
