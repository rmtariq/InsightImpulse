#!/usr/bin/env python3
"""
FASA 2 — Analitik + insight per 36 DUN N9 dari data crawl + Excel Terkini.

Input:
  - Master/combined CSV (InsightPulse pas_break_2026/master atau data/combined)
  - Terkini Excel → keywords per DUN

Output:
  - socmed_by_dun_N9.json
  - n9_production_bundle.json (via build_warroom_production_bundle)
"""
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

from prn_paths import crawls  # noqa: E402
from crawl_prn_n9_36dun_insightpulse import DEFAULT_XLSX, load_seats_from_excel  # noqa: E402

OUT = ROOT / "data/projects/political/PRN/PRN_N9/reports/war_room/prototype/data/socmed_by_dun_N9.json"
MYT = timezone(timedelta(hours=8))

MASTER_DIRS = [
    ROOT / "data/projects/political/pas_break_2026/master",
    ROOT / "data/combined",
]


def find_latest_csv() -> Optional[Path]:
    files: List[Path] = []
    for d in MASTER_DIRS:
        if not d.exists():
            continue
        files.extend(d.glob("PAS_Break_Master_EXCO_Analyzed_*.csv"))
        files.extend(d.glob("Combined_*.csv"))
    if not files:
        return None
    return max(files, key=lambda p: p.stat().st_mtime)


def keywords_for_seat(seat: dict) -> List[str]:
    kws: List[str] = []
    for field in ("primary_keywords", "hashtags", "local_issues", "name"):
        raw = str(seat.get(field) or "")
        for part in re.split(r"[;,#]", raw):
            t = part.strip().lower()
            if len(t) >= 3 and t not in ("prn", "pru", "malaysia", "pilihanrayanegeri"):
                kws.append(t)
    kws.append(seat["code"].lower())
    kws.append(seat["name"].lower())
    return list(dict.fromkeys(kws))


def row_matches(text: str, code: str, kws: List[str]) -> bool:
    t = text.lower()
    if re.search(rf"\b{re.escape(code.lower())}\b", t):
        return True
    hits = sum(1 for k in kws if k in t)
    return hits >= 2 or (hits >= 1 and seat_name_in_text(t, kws))


def seat_name_in_text(t: str, kws: List[str]) -> bool:
    for k in kws:
        if " " in k and k in t:
            return True
    return False


def sentiment_bucket(label: str, text: str) -> str:
    s = (label or "").lower()
    if "neg" in s:
        return "negative"
    if "pos" in s:
        return "positive"
    t = text.lower()
    if any(w in t for w in ("rosak", "banjir", "mahal", "bantah", "gagal", "aduan")):
        return "negative"
    if any(w in t for w in ("terbaik", "jaya", "membantu", "terima kasih")):
        return "positive"
    return "neutral"


def parse_date(raw) -> Optional[datetime]:
    if raw is None or (isinstance(raw, float) and pd.isna(raw)):
        return None
    s = str(raw).strip()
    if not s or s.lower() == "nan":
        return None
    try:
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def build_insights(csv_path: Path, seats: List[dict]) -> dict:
    df = pd.read_csv(csv_path, encoding="utf-8", low_memory=False)
    text_col = next((c for c in ("Text", "text", "content") if c in df.columns), None)
    if not text_col:
        raise SystemExit(f"No text column in {csv_path.name}")

    rows = []
    max_dt = None
    for _, r in df.iterrows():
        text = str(r.get(text_col) or "")
        if len(text) < 10:
            continue
        dt = parse_date(r.get("Date") or r.get("date") or r.get("created_at"))
        if dt and (max_dt is None or dt > max_dt):
            max_dt = dt
        sent = sentiment_bucket(str(r.get("sentiment_label") or r.get("Sentiment") or ""), text)
        rows.append({
            "text": text,
            "date": dt,
            "platform": str(r.get("Platform") or "unknown").lower(),
            "sentiment": sent,
        })

    window_end = max_dt or datetime.now(timezone.utc)
    w24 = window_end - timedelta(hours=24)
    w7 = window_end - timedelta(days=7)

    seat_kw = {s["code"]: keywords_for_seat(s) for s in seats}
    by_dun: Dict[str, dict] = {}

    for s in seats:
        code = s["code"]
        kws = seat_kw[code]
        matched = [r for r in rows if row_matches(r["text"], code, kws)]
        if not matched:
            by_dun[code] = {
                "mentions_total": 0, "mentions_24h": 0, "mentions_7d": 0,
                "neg_pct": 0.0, "pos_pct": 0.0, "platforms": {},
                "alert_level": "ok", "top_snippet": "", "source": "broad_master+excel",
            }
            continue
        m24 = [r for r in matched if r["date"] and w24 <= r["date"] <= window_end]
        m7 = [r for r in matched if r["date"] and w7 <= r["date"] <= window_end]
        neg = sum(1 for r in matched if r["sentiment"] == "negative")
        total = len(matched)
        neg_pct = round(neg / total * 100, 1) if total else 0
        plats = Counter(r["platform"] for r in matched)
        alert = "critical" if neg_pct >= 25 else "warning" if neg_pct >= 15 else "ok"
        by_dun[code] = {
            "mentions_total": total,
            "mentions_24h": len(m24),
            "mentions_7d": len(m7),
            "neg_pct": neg_pct,
            "pos_pct": round(sum(1 for r in matched if r["sentiment"] == "positive") / total * 100, 1),
            "platforms": dict(plats),
            "alert_level": alert,
            "top_snippet": re.sub(r"\s+", " ", matched[0]["text"])[:160],
            "source": "broad_master+excel",
            "tier": s.get("tier"),
            "local_issues": s.get("local_issues"),
        }

    return {
        "meta": {
            "state": "N9",
            "generated": datetime.now(MYT).strftime("%Y-%m-%d %H:%M:%S"),
            "master_csv": str(csv_path.relative_to(ROOT)),
            "total_rows_scanned": len(rows),
            "excel_source": str(DEFAULT_XLSX.relative_to(ROOT)),
            "method": "FASA2 broad crawl + Excel DUN keyword mapping",
        },
        "byDun": by_dun,
        "rollup": {
            "mentions_total": len(rows),
            "seats_with_mentions": sum(1 for d in by_dun.values() if d["mentions_total"] > 0),
            "top_seats": sorted(
                [(c, d["mentions_total"]) for c, d in by_dun.items()],
                key=lambda x: -x[1],
            )[:10],
        },
    }


def main() -> int:
    csv_path = find_latest_csv()
    if not csv_path:
        print("❌ Tiada master/combined CSV. Jalankan FASA 1 crawl dulu.", file=sys.stderr)
        return 1

    seats = load_seats_from_excel(DEFAULT_XLSX)
    payload = build_insights(csv_path, seats)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    r = payload["rollup"]
    print(f"✅ {OUT}")
    print(f"   Master: {csv_path.name} ({payload['meta']['total_rows_scanned']} rows)")
    print(f"   Kerusi ada data: {r['seats_with_mentions']}/36")
    if r["top_seats"]:
        print(f"   Top: {', '.join(f'{c}={n}' for c,n in r['top_seats'][:5])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
