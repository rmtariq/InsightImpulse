#!/usr/bin/env python3
"""Merge PAS Break Crawl 1 (social) + Crawl 2 (news) into project master."""

import json
from datetime import datetime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "data/projects/political/pas_break_2026"
SOCIAL = PROJECT / "master/PAS_Break_Master_Social_MERGED_20260610.csv"
NEWS = PROJECT / "crawls/pas_break_news_20260610_230655.csv"
OUT_DIR = PROJECT / "master"
JITP_OUT = ROOT / "JITP_2026/PAS_Break_2026/processed_data"

WINDOW_START = pd.Timestamp("2026-06-09", tz="UTC")
WINDOW_END = pd.Timestamp("2026-06-10 23:59:59", tz="UTC")


def load_and_align(path: Path, source: str) -> pd.DataFrame:
    df = pd.read_csv(path, low_memory=False)
    df["crawl_source"] = source
    for col in ["Parent_Post_URL", "Parent_Post_ID", "author", "author_followers",
                "sentiment_label", "sentiment_confidence", "emotion_primary"]:
        if col not in df.columns:
            df[col] = ""
    if "Text" not in df.columns and "text" in df.columns:
        df["Text"] = df["text"]
    df["Text"] = df["Text"].fillna("").astype(str)
    return df


def dedupe(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["_dedupe_key"] = (
        df["Platform"].astype(str).str.lower() + "|"
        + df["ID"].astype(str) + "|"
        + df["URL"].fillna("").astype(str)
    )
    before = len(df)
    df = df.drop_duplicates(subset=["_dedupe_key"], keep="first").drop(columns=["_dedupe_key"])
    print(f"  Dedup: {before} → {len(df)}")
    return df


def parse_dates(df: pd.DataFrame) -> pd.Series:
    """Parse Date column — social and news formats differ; all UTC."""
    out = pd.Series(index=df.index, dtype="datetime64[ns, UTC]")
    for plat in df["Platform"].astype(str).str.lower().unique():
        mask = df["Platform"].astype(str).str.lower() == plat
        parsed = pd.to_datetime(df.loc[mask, "Date"], errors="coerce", utc=True)
        out.loc[mask] = parsed.dt.tz_convert("UTC") if parsed.dt.tz else parsed.dt.tz_localize("UTC")
    return out


def add_flags(df: pd.DataFrame) -> pd.DataFrame:
    t = df["Text"].str.lower()
    df["is_news"] = df["Platform"].str.lower().isin(["news", "google"])
    df["is_social"] = ~df["is_news"]
    df["mentions_pas"] = t.str.contains(r"\bpas\b|parti islam", regex=True, na=False)
    df["mentions_bersatu"] = t.str.contains(r"\bbersatu\b|ppbm|perikatan nasional|\bpn\b", regex=True, na=False)
    df["narrative_split"] = t.str.contains(
        r"putus|berpisah|perpecahan|retak|khianat|pecah", regex=True, na=False
    )
    df["narrative_solo"] = t.str.contains(r"pas solo|pas bergerak solo|\bsolo\b", regex=True, na=False)
    df["geo_johor"] = t.str.contains(r"johor|dun johor", regex=True, na=False)
    df["geo_melaka"] = t.str.contains(r"melaka|melaka", regex=True, na=False)
    df["geo_ns"] = t.str.contains(
        r"negeri sembilan|\bns\b|seremban|port dickson|aminuddin", regex=True, na=False
    )
    dates = parse_dates(df)
    df["date_parsed"] = dates
    df["in_event_window"] = dates.between(WINDOW_START, WINDOW_END, inclusive="both")
    return df


def main():
    print("📥 Loading Crawl 1 social...")
    social = load_and_align(SOCIAL, "crawl1_social_merged")
    print(f"   {len(social)} rows")

    print("📥 Loading Crawl 2 news...")
    news = load_and_align(NEWS, "crawl2_news")
    print(f"   {len(news)} rows")

    print("🔗 Merging...")
    merged = pd.concat([social, news], ignore_index=True)
    merged = dedupe(merged)
    merged = add_flags(merged)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    full_path = OUT_DIR / f"PAS_Break_Master_FULL_{ts}.csv"
    window_path = OUT_DIR / f"PAS_Break_Master_EventWindow_Jun9-10_{ts}.csv"

    merged.to_csv(full_path, index=False, encoding="utf-8")
    window_df = merged[merged["in_event_window"]].copy()
    window_df.to_csv(window_path, index=False, encoding="utf-8")

    JITP_OUT.mkdir(parents=True, exist_ok=True)
    jtp_full = JITP_OUT / f"PAS_Break_Master_FULL_{ts}.csv"
    jtp_win = JITP_OUT / f"PAS_Break_Master_EventWindow_Jun9-10_{ts}.csv"
    merged.to_csv(jtp_full, index=False, encoding="utf-8")
    window_df.to_csv(jtp_win, index=False, encoding="utf-8")

    meta_path = PROJECT / "metadata.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    meta["masters"].append({
        "file": f"master/{full_path.name}",
        "rows": len(merged),
        "saved_at": datetime.now().isoformat(),
        "note": "Crawl1 social 7395 + Crawl2 news 1066 merged",
    })
    meta["masters"].append({
        "file": f"master/{window_path.name}",
        "rows": len(window_df),
        "saved_at": datetime.now().isoformat(),
        "note": "Event window 9-10 Jun 2026",
    })
    meta["latest_master"] = f"master/{full_path.name}"
    meta["latest_event_window"] = f"master/{window_path.name}"
    meta["pending"] = ["dashboard_exco"]
    meta["merge_stats"] = {
        "full_total": len(merged),
        "social_rows": int(merged["is_social"].sum()),
        "news_rows": int(merged["is_news"].sum()),
        "event_window_rows": len(window_df),
        "event_window_posts": int((window_df["Type"] == "post").sum()) if "Type" in window_df.columns else None,
        "mentions_pas_event": int(window_df["mentions_pas"].sum()),
        "mentions_bersatu_event": int(window_df["mentions_bersatu"].sum()),
        "narrative_split_event": int(window_df["narrative_split"].sum()),
        "narrative_solo_event": int(window_df["narrative_solo"].sum()),
    }
    meta["updated_at"] = datetime.now().isoformat()
    meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")

    print("\n✅ MERGE COMPLETE")
    print(f"   FULL:          {full_path} ({len(merged):,} rows)")
    print(f"   EVENT WINDOW:  {window_path} ({len(window_df):,} rows)")
    print(f"   Social: {merged['is_social'].sum():,} | News: {merged['is_news'].sum():,}")
    print(f"   Jun 9-10: split={window_df['narrative_split'].sum()} solo={window_df['narrative_solo'].sum()}")


if __name__ == "__main__":
    main()
