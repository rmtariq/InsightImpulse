#!/usr/bin/env python3
"""Build war room per-DUN socmed stats from Excel intel crawl CSV."""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from prn_paths import crawls, reports  # noqa: E402

OUT_DIR = ROOT / "data/projects/political/PRN/PRN_N9/reports/war_room/prototype/data"
MYT = timezone(timedelta(hours=8))

SEAT_KEYWORDS: Dict[str, List[str]] = {
    "N01": ["chennah", "n01"],
    "N02": ["pertang", "n02"],
    "N03": ["sungai lui", "sg lui", "n03"],
    "N04": ["klawang", "n04"],
    "N05": ["serting", "n05"],
    "N06": ["palong", "n06"],
    "N07": ["jeram padang", "n07"],
    "N08": ["bahau", "n08"],
    "N09": ["lenggeng", "n09"],
    "N10": ["nilai", "n10"],
    "N11": ["lobak", "n11"],
    "N12": ["temiang", "n12"],
    "N13": ["sikamat", "n13"],
    "N14": ["ampangan", "n14"],
    "N15": ["juasseh", "n15"],
    "N16": ["seri menanti", "menanti", "n16"],
    "N17": ["senaling", "n17"],
    "N18": ["pilah", "kuala pilah", "n18"],
    "N19": ["johol", "n19"],
    "N20": ["labu", "n20"],
    "N21": ["bukit kepayang", "kepayang", "n21"],
    "N22": ["rahang", "n22"],
    "N23": ["mambau", "n23"],
    "N24": ["seremban jaya", "n24"],
    "N25": ["paroi", "n25"],
    "N26": ["chembong", "n26"],
    "N27": ["rantau", "n27"],
    "N28": ["kota", "seremban kota", "n28"],
    "N29": ["chuah", "n29"],
    "N30": ["lukut", "n30"],
    "N31": ["bagan pinang", "port dickson", "n31"],
    "N32": ["linggi", "n32"],
    "N33": ["sri tanjung", "tanjung", "n33"],
    "N34": ["gemas", "n34"],
    "N35": ["gemencheh", "n35"],
    "N36": ["repah", "tampin", "n36"],
}


def latest_excel_crawl(state: str = "N9") -> Optional[Path]:
    folder = crawls(state, "excel_intel")
    if not folder.exists():
        return None
    files = sorted(
        list(folder.glob("PRN_ExcelIntel_*.csv")) + list(folder.glob("PRN_N9_36DUN_*.csv")),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return files[0] if files else None


def parse_date(raw) -> Optional[datetime]:
    if raw is None or (isinstance(raw, float) and pd.isna(raw)):
        return None
    s = str(raw).strip()
    if not s or s.lower() == "nan":
        return None
    try:
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        return None


def row_matches_seat(text: str, code: str, seed_dun: str, keywords: List[str]) -> bool:
    if seed_dun and seed_dun.upper() == code.upper():
        return True
    t = text.lower()
    if re.search(rf"\b{re.escape(code.lower())}\b", t):
        return True
    return any(kw in t for kw in keywords)


def sentiment_from_text(text: str) -> str:
    t = text.lower()
    neg = ("rosak", "banjir", "mahal", "marah", "protest", "bantah", "gagal", "isu", "aduan")
    pos = ("terima kasih", "terbaik", "jaya", "berjaya", "membantu", "baik", "hebat")
    if any(w in t for w in neg):
        return "negative"
    if any(w in t for w in pos):
        return "positive"
    return "neutral"


def build_from_csv(csv_path: Path) -> dict:
    df = pd.read_csv(csv_path, encoding="utf-8")
    rows: List[dict] = []
    max_dt: Optional[datetime] = None

    for _, row in df.iterrows():
        text = str(row.get("Text") or "")
        if not text.strip():
            continue
        dt = parse_date(row.get("Date"))
        if dt and (max_dt is None or dt > max_dt):
            max_dt = dt
        rows.append({
            "text": text,
            "date": dt,
            "platform": str(row.get("Platform") or "news").lower(),
            "sentiment": sentiment_from_text(text),
            "engagement": 0,
            "seed_dun": str(row.get("SeedDun") or "").strip(),
        })

    window_end = max_dt or datetime.now(timezone.utc)
    window_start_24h = window_end - timedelta(hours=24)
    window_start_7d = window_end - timedelta(days=7)

    by_dun: Dict[str, dict] = {}
    for code, keywords in SEAT_KEYWORDS.items():
        matched = [
            r for r in rows
            if row_matches_seat(r["text"], code, r["seed_dun"], keywords)
        ]
        if not matched:
            by_dun[code] = {
                "mentions_total": 0,
                "mentions_24h": 0,
                "mentions_7d": 0,
                "neg_pct": 0.0,
                "pos_pct": 0.0,
                "engagement_total": 0,
                "engagement_24h": 0,
                "platforms": {},
                "alert_level": "ok",
                "top_snippet": "",
                "source": "excel_intel",
            }
            continue

        def in_window(r, start):
            return r["date"] is not None and start <= r["date"] <= window_end

        m24 = [r for r in matched if in_window(r, window_start_24h)]
        m7 = [r for r in matched if in_window(r, window_start_7d)]
        neg = sum(1 for r in matched if r["sentiment"] == "negative")
        pos = sum(1 for r in matched if r["sentiment"] == "positive")
        total = len(matched)
        neg_pct = round(neg / total * 100, 1) if total else 0.0
        pos_pct = round(pos / total * 100, 1) if total else 0.0
        plats = Counter(r["platform"] for r in matched)

        alert = "ok"
        ref = m24 if m24 else m7 if m7 else matched
        ref_neg = sum(1 for r in ref if r["sentiment"] == "negative")
        ref_n = len(ref)
        ref_neg_pct = (ref_neg / ref_n * 100) if ref_n else 0
        if ref_neg_pct >= 25:
            alert = "critical"
        elif ref_neg_pct >= 15:
            alert = "warning"
        elif ref_n >= 3 and ref_neg_pct >= 10:
            alert = "watch"

        snippet = re.sub(r"\s+", " ", matched[0]["text"])[:140]

        by_dun[code] = {
            "mentions_total": total,
            "mentions_24h": len(m24),
            "mentions_7d": len(m7),
            "neg_pct": neg_pct,
            "pos_pct": pos_pct,
            "engagement_total": 0,
            "engagement_24h": 0,
            "platforms": dict(plats),
            "alert_level": alert,
            "top_snippet": snippet,
            "source": "excel_intel",
        }

    return {
        "meta": {
            "state": "N9",
            "generated": datetime.now(MYT).strftime("%Y-%m-%d %H:%M:%S"),
            "excel_crawl_source": str(csv_path.relative_to(ROOT)),
            "rows_scanned": len(rows),
            "window_end_utc": window_end.isoformat() if window_end else None,
        },
        "byDun": by_dun,
        "rollup": {
            "mentions_total": len(rows),
            "seats_with_mentions": sum(1 for d in by_dun.values() if d["mentions_total"] > 0),
            "top_seats_24h": sorted(
                [(c, d["mentions_24h"]) for c, d in by_dun.items() if d["mentions_24h"] > 0],
                key=lambda x: -x[1],
            )[:10],
        },
    }


def merge_with_existing(new_payload: dict, existing_path: Path) -> dict:
    if not existing_path.exists():
        return new_payload
    try:
        old = json.loads(existing_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return new_payload
    merged = dict(new_payload)
    by_dun = dict(old.get("byDun") or {})
    for code, stats in (new_payload.get("byDun") or {}).items():
        if stats.get("mentions_total", 0) > 0:
            by_dun[code] = stats
        elif code not in by_dun:
            by_dun[code] = stats
    merged["byDun"] = by_dun
    merged["meta"]["merged_with"] = str(existing_path.name)
    merged["rollup"]["seats_with_mentions"] = sum(
        1 for d in by_dun.values() if d.get("mentions_total", 0) > 0
    )
    return merged


def main() -> int:
    csv_path = latest_excel_crawl("N9")
    if not csv_path:
        print("❌ Tiada crawl excel_intel — jalankan crawl_prn_excel_intel.py dulu", file=sys.stderr)
        return 1

    payload = build_from_csv(csv_path)
    out_path = OUT_DIR / "socmed_by_dun_N9.json"
    payload = merge_with_existing(payload, out_path)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    active = payload["rollup"]["seats_with_mentions"]
    print(f"✅ {out_path}")
    print(f"   Rows: {payload['meta']['rows_scanned']} · kerusi ada mention: {active}/{len(SEAT_KEYWORDS)}")
    top = payload["rollup"].get("top_seats_24h") or []
    if top:
        print(f"   Top 24j: {', '.join(f'{c}={n}' for c, n in top[:5])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
