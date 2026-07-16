#!/usr/bin/env python3
"""Audit per-DUN headline crawl quality for N9 + Johor War Room."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from dun_headline_quality import score_headline  # noqa: E402

PROTO = ROOT / "data/projects/political/PRN/PRN_N9/reports/war_room/prototype/data"
MYT = timezone(timedelta(hours=8))


def audit_state(state_key: str, path: Path) -> dict:
    seats = json.loads(path.read_text(encoding="utf-8"))
    rows = []
    counts = {"verified": 0, "weak": 0, "none": 0, "stale_leak": 0, "state_wide_leak": 0}

    for s in seats:
        code = s.get("id", "")
        meta = s.get("headlineMeta") or {}
        quality = meta.get("quality") or "none"
        counts[quality] = counts.get(quality, 0) + 1
        headlines = s.get("socialHeadlines") or []
        issue = None
        for h in headlines:
            verdict, hits = score_headline(h, {
                "code": code,
                "name": s.get("name"),
                "incumbent": s.get("incumbent"),
                "stateKey": state_key,
            })
            if verdict == "state_wide":
                counts["state_wide_leak"] += 1
                issue = "state_wide_leak"
            elif verdict == "irrelevant":
                counts["stale_leak"] += 1
                issue = "irrelevant_leak"
        item_date = None
        items = meta.get("items") or []
        if items and items[0].get("date"):
            item_date = items[0]["date"][:10]
        rows.append({
            "code": code,
            "name": s.get("name"),
            "quality": quality,
            "mentions": s.get("socmedMentions", 0),
            "headline": (headlines[0][:120] + "…") if headlines and len(headlines[0]) > 120 else (headlines[0] if headlines else ""),
            "date": item_date,
            "issue": issue,
        })

    return {
        "state": state_key,
        "seatCount": len(seats),
        "counts": counts,
        "seats": rows,
    }


def main() -> None:
    reports = {}
    n9_path = PROTO / "warroom_dun_N9_production.json"
    johor_path = PROTO / "warroom_dun_Johor_production.json"

    if n9_path.exists():
        reports["N9"] = audit_state("N9", n9_path)
    if johor_path.exists():
        reports["Johor"] = audit_state("Johor", johor_path)

    out = {
        "generated": datetime.now(MYT).strftime("%Y-%m-%d %H:%M:%S"),
        "rules": {
            "verified": "Headline spesifik kerusi + ≤90 hari",
            "none": "Tiada headline terkini spesifik kerusi",
            "reject": "Senarai DUN negeri / negeri lain / >90 hari",
        },
        "states": reports,
    }
    out_path = PROTO / "headline_audit_n9_johor.json"
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    for key, rep in reports.items():
        c = rep["counts"]
        print(f"\n=== {key} ({rep['seatCount']} kerusi) ===")
        print(f"  disahkan: {c.get('verified', 0)} · perlu semak: {c.get('weak', 0)} · tiada: {c.get('none', 0)}")
        leaks = c.get("state_wide_leak", 0) + c.get("stale_leak", 0)
        print(f"  kebocoran filter: {leaks}")
        verified = [r for r in rep["seats"] if r["quality"] == "verified"]
        if verified:
            print("  contoh disahkan:")
            for r in verified[:5]:
                print(f"    {r['code']} {r['name']}: {r['headline'][:80]}")
        empty_with_mentions = [r for r in rep["seats"] if r["quality"] == "none" and r["mentions"] > 0]
        if empty_with_mentions:
            print(f"  tiada headline tapi ada socmed: {len(empty_with_mentions)} kerusi")

    print(f"\n✅ Audit: {out_path}")


if __name__ == "__main__":
    main()
