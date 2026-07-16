#!/usr/bin/env python3
"""Backfill sentiment, demographic, language & emotion columns on PAS Break master CSV."""
from __future__ import annotations

import argparse
import csv
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(ROOT))

MASTER_DIR = ROOT / "data/projects/political/pas_break_2026/master"
MYT = timezone(timedelta(hours=8))

ANALYSIS_COLS = [
    "sentiment_label", "sentiment_score", "sentiment_confidence", "emotion_primary",
    "detected_language", "demographic", "analysis_mode", "narrative_split",
    "mentions_pas", "mentions_bersatu",
]

DEMO_NORMALIZE = {
    "malay": "Malay/Bumiputera",
    "malay/bumiputera": "Malay/Bumiputera",
    "mixed/urban": "Mixed/Urban",
    "mixed": "Mixed/Urban",
    "urban": "Mixed/Urban",
    "chinese": "Chinese",
    "indian": "Indian",
    "unknown": "Unknown",
    "multilingual": "Unknown",
}

_NEG_KW = re.compile(
    r"goyah|risiko|krisis|pecah|split|khianat|bantah|protest|gagal|skandal|"
    r"susah|marah|negative|worst|crisis|turun",
    re.I,
)
_POS_KW = re.compile(
    r"menang|jaya|stabil|positif|baik|untung|growth|positive|strong|support|menyokong",
    re.I,
)
_SPLIT_KW = re.compile(
    r"putus|berpisah|perpecahan|retak|khianat|pecah|split|hentikan kerjasama|umdap",
    re.I,
)


def find_latest_master() -> Path | None:
    candidates = sorted(
        MASTER_DIR.glob("PAS_Break_Master_EXCO_Analyzed_*.csv"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return candidates[0] if candidates else None


def find_prior_analyzed(exclude: Path) -> Path | None:
    for p in sorted(
        MASTER_DIR.glob("PAS_Break_Master_EXCO_Analyzed_*.csv"),
        key=lambda x: x.stat().st_mtime,
        reverse=True,
    ):
        if p == exclude:
            continue
        with p.open(encoding="utf-8", errors="replace") as f:
            if "demographic" in (csv.reader(f).__next__() or []):
                return p
    return None


def norm_demo(val: str) -> str:
    key = (val or "").strip().lower()
    return DEMO_NORMALIZE.get(key, val.strip() if val else "Unknown")


def infer_demographic(text: str, lang: str = "") -> str:
    text = text or ""
    if any("\u4e00" <= c <= "\u9fff" for c in text):
        return "Chinese"
    if re.search(r"[\u0B80-\u0BFF]", text):
        return "Indian"
    tl = (lang or "").lower()
    if tl.startswith("zh"):
        return "Chinese"
    if tl.startswith("ta"):
        return "Indian"
    if tl.startswith("ms"):
        return "Malay/Bumiputera"
    if tl.startswith("en"):
        return "Mixed/Urban"
    t = text.lower()
    if re.search(r"\b(yang|dan|tidak|akan|negeri|pas|umno|kerajaan|prn|dun|menteri|felda|getah)\b", t):
        return "Malay/Bumiputera"
    if re.search(r"[a-zA-Z]{4,}", text):
        return "Mixed/Urban"
    return "Unknown"


def keyword_sentiment(text: str) -> tuple[str, float, str]:
    if _NEG_KW.search(text):
        return "negative", 0.25, "concern"
    if _POS_KW.search(text):
        return "positive", 0.85, "joy"
    return "neutral", 0.5, "neutral"


def row_key(row: dict) -> str:
    return f"{(row.get('Platform') or '').lower()}|{row.get('ID') or ''}"


def load_prior_index(path: Path) -> dict[str, dict]:
    idx: dict[str, dict] = {}
    with path.open(encoding="utf-8", errors="replace") as f:
        for row in csv.DictReader(f):
            if not row.get("demographic"):
                continue
            idx[row_key(row)] = row
    return idx


def is_empty(val) -> bool:
    s = str(val or "").strip().lower()
    return s in ("", "nan", "none")


def enrich_rows(rows: list[dict], prior_idx: dict[str, dict], *, keyword_sentiment_flag: bool) -> None:
    for row in rows:
        text = str(row.get("Text") or "")
        t_lower = text.lower()
        pk = row_key(row)
        prev = prior_idx.get(pk) or {}

        for col in ANALYSIS_COLS:
            if col not in row:
                row[col] = prev.get(col) or ""

        if is_empty(row.get("demographic")):
            lang = str(row.get("detected_language") or prev.get("detected_language") or "")
            row["demographic"] = norm_demo(infer_demographic(text, lang))
            if is_empty(row.get("detected_language")):
                demo = row["demographic"]
                if demo == "Chinese":
                    row["detected_language"] = "zh-cn"
                elif demo == "Indian":
                    row["detected_language"] = "ta"
                elif demo == "Malay/Bumiputera":
                    row["detected_language"] = "ms"
                elif demo == "Mixed/Urban":
                    row["detected_language"] = "en"

        if is_empty(row.get("sentiment_label")) and keyword_sentiment_flag:
            label, score, emo = keyword_sentiment(text)
            row["sentiment_label"] = label
            row["Sentiment"] = label
            row["sentiment_score"] = str(score)
            row["sentiment_confidence"] = "0.55"
            row["emotion_primary"] = emo
            row["analysis_mode"] = "keyword_fallback"

        if is_empty(row.get("narrative_split")):
            row["narrative_split"] = "True" if _SPLIT_KW.search(t_lower) else "False"
        if is_empty(row.get("mentions_pas")):
            row["mentions_pas"] = "True" if re.search(r"\bpas\b|muslimat|pejuang", t_lower) else "False"
        if is_empty(row.get("mentions_bersatu")):
            row["mentions_bersatu"] = "True" if re.search(r"bersatu|muhyiddin|sabri", t_lower) else "False"


def main() -> int:
    ap = argparse.ArgumentParser(description="Enrich PAS Break master with analysis columns")
    ap.add_argument("--csv", type=Path, default=None)
    ap.add_argument("--prior", type=Path, default=None)
    ap.add_argument("--keyword-sentiment", action="store_true")
    args = ap.parse_args()

    src = args.csv or find_latest_master()
    if not src or not src.exists():
        print("❌ No master CSV found", file=sys.stderr)
        return 1

    print(f"📥 Master: {src.name} ({src.stat().st_size // 1024} KB)")
    with src.open(encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)

    for col in ANALYSIS_COLS + ["Sentiment"]:
        if col not in fieldnames:
            fieldnames.append(col)

    prior = args.prior or find_prior_analyzed(src)
    prior_idx: dict[str, dict] = {}
    if prior and prior.exists():
        print(f"   Prior: {prior.name}")
        prior_idx = load_prior_index(prior)
        print(f"   ↩︎  Prior index: {len(prior_idx):,} rows with demographic")

    enrich_rows(rows, prior_idx, keyword_sentiment_flag=args.keyword_sentiment)

    labeled = sum(1 for r in rows if not is_empty(r.get("sentiment_label")))
    demo_filled = sum(1 for r in rows if not is_empty(r.get("demographic")))
    demo_counts: dict[str, int] = defaultdict(int)
    for r in rows:
        demo_counts[r.get("demographic") or "Unknown"] += 1

    ts = datetime.now(MYT).strftime("%Y%m%d_%H%M%S")
    out = MASTER_DIR / f"PAS_Break_Master_EXCO_Analyzed_{ts}.csv"
    with out.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

    top_demo = sorted(demo_counts.items(), key=lambda x: -x[1])[:5]
    print(f"\n✅ Saved: {out.name}")
    print(f"   Rows: {len(rows):,} · sentiment: {labeled:,} · demographic: {demo_filled:,}")
    print(f"   Demo top: {top_demo}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
