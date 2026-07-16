#!/usr/bin/env python3
"""Backfill author_demographic + refined demographic from author display names."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.utils.malaysian_name_demographics import merge_demographic


def enrich_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if "author_demographic" not in out.columns:
        out["author_demographic"] = ""
    if "author_demo_confidence" not in out.columns:
        out["author_demo_confidence"] = 0.0

    for idx, row in out.iterrows():
        author = str(row.get("author") or "").strip()
        text_demo = str(row.get("demographic") or "Unknown")
        final, author_demo, conf = merge_demographic(text_demo, author)
        out.at[idx, "author_demographic"] = author_demo
        out.at[idx, "author_demo_confidence"] = round(conf, 3)
        out.at[idx, "demographic"] = final
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Enrich CSV with author name demographics")
    parser.add_argument("csv_path", type=Path, help="Input CSV (also written back unless --output)")
    parser.add_argument("--output", type=Path, default=None, help="Output path (default: overwrite input)")
    args = parser.parse_args()

    df = pd.read_csv(args.csv_path)
    enriched = enrich_dataframe(df)
    out_path = args.output or args.csv_path
    enriched.to_csv(out_path, index=False)

    comments = enriched[enriched.get("Type", pd.Series(dtype=str)).astype(str).str.lower() == "comment"]
    print(f"Saved: {out_path}")
    print(f"Rows: {len(enriched)} | Comments: {len(comments)}")
    if "demographic" in comments.columns:
        print("\nFinal demographic (comments):")
        print(comments["demographic"].value_counts().to_string())
    if "author_demographic" in comments.columns:
        print("\nAuthor-name demographic (comments):")
        print(comments["author_demographic"].value_counts().to_string())


if __name__ == "__main__":
    main()
