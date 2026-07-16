#!/usr/bin/env python3
"""Audit keyword matching for all N9 + Johor DUN — detect false-positive socmed/headline leaks."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from dun_headline_quality import score_headline  # noqa: E402
from dun_seat_keywords import (  # noqa: E402
    N9_SEAT_KEYWORDS,
    keywords_for_state,
    norm_code,
    row_matches_seat,
)
from warroom_socmed_core import (  # noqa: E402
    JOHOR_PATTERN,
    NS_PATTERN,
    find_johor_master,
    find_pas_break_master,
    load_geo_seats,
    load_state_rows,
)

PROTO = ROOT / "data/projects/political/PRN/PRN_N9/reports/war_room/prototype/data"
MYT = timezone(timedelta(hours=8))


def load_seats(state: str) -> list[dict]:
    path = PROTO / (
        "warroom_dun_N9_production.json" if state == "N9"
        else "warroom_dun_Johor_production.json"
    )
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else []


def audit_matches(state: str, rows: list[dict], keywords: dict[str, list[str]], seats: list[dict]) -> dict:
    seat_by_code = {norm_code(s["id"]): s for s in seats}
    report_seats = []
    totals = {"seats": 0, "with_matches": 0, "bad_ratio_high": 0, "snippet_leak": 0}

    for code in sorted(keywords.keys(), key=lambda c: int(c[1:])):
        seat = seat_by_code.get(code, {"id": code, "name": "", "stateKey": state})
        kws = keywords[code]
        matched = [r for r in rows if row_matches_seat(r["text"], code, kws, state)]
        totals["seats"] += 1
        if not matched:
            report_seats.append({
                "code": code,
                "name": seat.get("name"),
                "matches": 0,
                "bad": 0,
                "status": "ok",
            })
            continue

        totals["with_matches"] += 1
        bad = []
        for r in matched:
            verdict, _ = score_headline(r["text"], {**seat, "code": code, "stateKey": state})
            if verdict in ("irrelevant", "weak", "state_wide"):
                bad.append({"verdict": verdict, "sample": r["text"][:120]})

        bad_n = len(bad)
        ratio = bad_n / len(matched) if matched else 0
        status = "ok"
        if ratio >= 0.5 and len(matched) >= 3:
            status = "review"
            totals["bad_ratio_high"] += 1
        if bad_n and bad_n == len(matched) and len(matched) >= 1:
            status = "fail"
            totals["snippet_leak"] += 1

        report_seats.append({
            "code": code,
            "name": seat.get("name"),
            "keywords": kws,
            "matches": len(matched),
            "bad": bad_n,
            "bad_ratio": round(ratio, 2),
            "status": status,
            "sample_bad": bad[0] if bad else None,
        })

    return {"state": state, "totals": totals, "seats": report_seats}


def audit_production_headlines(state: str, seats: list[dict]) -> dict:
    counts = {"verified": 0, "none": 0, "leak": 0}
    leaks = []
    for s in seats:
        meta = s.get("headlineMeta") or {}
        q = meta.get("quality") or "none"
        counts[q] = counts.get(q, 0) + 1
        for h in s.get("socialHeadlines") or []:
            verdict, _ = score_headline(h, {
                "code": s.get("id"),
                "name": s.get("name"),
                "incumbent": s.get("incumbent"),
                "stateKey": state,
            })
            if verdict != "relevant":
                counts["leak"] += 1
                leaks.append({"code": s.get("id"), "name": s.get("name"), "verdict": verdict, "text": h[:100]})
    return {"counts": counts, "leaks": leaks[:20]}


def main() -> None:
    masters = [p for p in [find_pas_break_master(), find_johor_master()] if p]
    if not masters:
        print("❌ Tiada master crawl", file=sys.stderr)
        sys.exit(1)

    n9_rows, _ = load_state_rows([masters[0]], NS_PATTERN)
    j_rows, _ = load_state_rows(masters, JOHOR_PATTERN)

    n9_seats = load_seats("N9")
    j_seats = load_seats("Johor")
    j_keywords = keywords_for_state(load_geo_seats(PROTO / "warroom_dun_Johor.json"), "Johor")

    out = {
        "generated": datetime.now(MYT).strftime("%Y-%m-%d %H:%M:%S"),
        "rules": [
            "Keyword kurator per kerusi — tiada auto-split generik (johor/bukit/raja/kota)",
            "row_matches_seat + score_headline untuk tapisan",
            "Headline UI hanya papar quality=verified",
        ],
        "matching": {
            "N9": audit_matches("N9", n9_rows, N9_SEAT_KEYWORDS, n9_seats),
            "Johor": audit_matches("Johor", j_rows, j_keywords, j_seats),
        },
        "production_headlines": {
            "N9": audit_production_headlines("N9", n9_seats),
            "Johor": audit_production_headlines("Johor", j_seats),
        },
    }

    out_path = PROTO / "dun_keyword_audit_n9_johor.json"
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    for st in ("N9", "Johor"):
        m = out["matching"][st]
        t = m["totals"]
        h = out["production_headlines"][st]["counts"]
        fails = [s for s in m["seats"] if s["status"] == "fail"]
        review = [s for s in m["seats"] if s["status"] == "review"]
        print(f"\n=== {st} ({t['seats']} kerusi) ===")
        print(f"  ada match: {t['with_matches']} · perlu review: {t['bad_ratio_high']} · gagal penuh: {t['snippet_leak']}")
        print(f"  headline production: {h.get('verified', 0)} disahkan · {h.get('none', 0)} tiada · kebocoran: {h.get('leak', 0)}")
        if fails:
            print("  GAGAL (100% match tidak relevan):")
            for s in fails[:8]:
                sb = s.get("sample_bad") or {}
                print(f"    {s['code']} {s['name']}: {s['matches']} match — [{sb.get('verdict')}] {(sb.get('sample') or '')[:70]}")
        if review:
            print(f"  REVIEW ({len(review)} kerusi ≥50% match lemah):")
            for s in review[:5]:
                print(f"    {s['code']} {s['name']}: {s['bad']}/{s['matches']} bad")

    print(f"\n✅ Audit: {out_path}")


if __name__ == "__main__":
    main()
