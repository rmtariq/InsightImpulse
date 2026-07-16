#!/usr/bin/env python3
"""Label Cula Digital comments: Jelas + Debat→condong (MN/Solo/Labu)."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.utils.cula_debate_labels import ISSUE_LABU, ISSUE_MN_SOLO, TIER_JELAS


def _soft_assumption(row: pd.Series) -> str:
    """Weak inference for comments still labelled Tidak Jelas."""
    if str(row.get("cula_bucket", "")) != "Tidak Jelas":
        return str(row.get("cula_bucket", ""))

    issue = str(row.get("cula_issue", ""))
    sent = str(row.get("sentiment_label", "")).lower()
    emo = str(row.get("emotion_primary", "")).lower()
    text = str(row.get("Text", row.get("text", ""))).lower()

    supportive_emo = emo in {"love", "happy", "surprise"}
    critical_emo = emo in {"anger", "fear", "sadness"}

    if issue == ISSUE_LABU:
        if sent == "positive" or supportive_emo or any(k in text for k in ("pas", "calon", "hirman", "norhirman")):
            return "Assume→Condong Sokong PAS"
        if sent == "negative" or critical_emo or any(k in text for k in ("ph", "tak")):
            return "Assume→Condong Tak Sokong/Kritik"
        return "Assume→Masih Tidak Jelas"

    if sent == "positive" or supportive_emo:
        return "Assume→Soft Pro-PAS/Pro-post"
    if sent == "negative" or critical_emo:
        return "Assume→Soft Kritik/Lawan"
    return "Assume→Masih Tidak Jelas"


def _type_col(df: pd.DataFrame) -> str:
    if "Type" in df.columns:
        return "Type"
    if "type" in df.columns:
        return "type"
    raise KeyError("CSV missing Type column")


def _text_col(df: pd.DataFrame) -> str:
    if "Text" in df.columns:
        return "Text"
    if "text" in df.columns:
        return "text"
    raise KeyError("CSV missing Text column")


def _parent_url_col(df: pd.DataFrame) -> str:
    if "Parent_Post_URL" in df.columns:
        return "Parent_Post_URL"
    if "parent_post_url" in df.columns:
        return "parent_post_url"
    return ""


def _url_col(df: pd.DataFrame) -> str:
    if "URL" in df.columns:
        return "URL"
    if "url" in df.columns:
        return "url"
    return "URL"


def build_post_text_map(df: pd.DataFrame) -> dict[str, str]:
    tcol = _type_col(df)
    xcol = _text_col(df)
    ucol = _url_col(df)
    posts = df[df[tcol].astype(str).str.lower() == "post"]
    return {str(r[ucol]): str(r[xcol] or "") for _, r in posts.iterrows()}


def label_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    from backend.utils.cula_debate_labels import classify_row

    out = df.copy()
    for col in ("cula_issue", "cula_tier", "cula_label", "cula_bucket", "cula_assumption"):
        if col not in out.columns:
            out[col] = ""

    tcol = _type_col(out)
    xcol = _text_col(out)
    pcol = _parent_url_col(out)
    post_map = build_post_text_map(out)

    for idx, row in out.iterrows():
        parent = str(row.get(pcol, "") if pcol else "")
        issue, tier, label, bucket = classify_row(
            str(row.get(xcol) or ""),
            str(row.get(tcol) or ""),
            post_text_by_url=post_map,
            parent_post_url=parent,
        )
        out.at[idx, "cula_issue"] = issue
        out.at[idx, "cula_tier"] = tier
        out.at[idx, "cula_label"] = label
        out.at[idx, "cula_bucket"] = bucket
    out["cula_assumption"] = out.apply(_soft_assumption, axis=1)
    return out


def print_summary(df: pd.DataFrame) -> None:
    tcol = _type_col(df)
    comments = df[df[tcol].astype(str).str.lower() == "comment"]
    print(f"Saved rows: {len(df)} | Comments labelled: {len(comments)}")

    for issue in (ISSUE_MN_SOLO, ISSUE_LABU):
        sub = comments[comments["cula_issue"] == issue]
        if sub.empty:
            continue
        print(f"\n=== {issue} ({len(sub)} komen) ===")
        print("\nTier:")
        print(sub["cula_tier"].value_counts().to_string())
        print("\nLabel:")
        print(sub["cula_label"].value_counts().to_string())
        print("\nBucket (Jelas + Debat gabung):")
        print(sub["cula_bucket"].value_counts().to_string())
        print("\nAssumption (Tidak Jelas dipecahkan dengan sentiment+emotion):")
        print(sub["cula_assumption"].value_counts().to_string())
        jelas = sub[sub["cula_tier"] == TIER_JELAS]
        if not jelas.empty:
            print("\nPeringkat 1 — Jelas sahaja:")
            print(jelas["cula_bucket"].value_counts().to_string())


def main() -> None:
    parser = argparse.ArgumentParser(description="Label Cula debate comments (Jelas + Debat→condong)")
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    df = pd.read_csv(args.csv_path)
    labelled = label_dataframe(df)
    out_path = args.output or args.csv_path
    labelled.to_csv(out_path, index=False)
    print(f"Saved: {out_path}")
    print_summary(labelled)


if __name__ == "__main__":
    main()
