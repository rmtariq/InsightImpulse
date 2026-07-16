#!/usr/bin/env python3
"""Build per-DUN socmed stats for N9 + Johor War Room prototype."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from warroom_socmed_core import (  # noqa: E402
    JOHOR_PATTERN,
    N9_SEAT_KEYWORDS,
    NS_PATTERN,
    build_socmed_for_state,
    find_johor_master,
    find_pas_break_master,
    keywords_for_state,
    load_geo_seats,
    load_state_rows,
    norm_code,
)

OUT_DIR = ROOT / "data/projects/political/PRN/PRN_N9/reports/war_room/prototype/data"
GEO_JOHOR = OUT_DIR / "warroom_dun_Johor.json"
GEO_N9 = OUT_DIR / "warroom_dun_N9_production.json"


def _seat_meta(seats: list[dict]) -> dict:
    return {norm_code(s.get("id") or s.get("code")): s for s in seats}


def build_n9() -> dict | None:
    master = find_pas_break_master()
    if not master:
        return None
    rows, sources = load_state_rows([master], NS_PATTERN)
    seats = load_geo_seats(GEO_N9)
    return build_socmed_for_state(
        "N9", N9_SEAT_KEYWORDS, rows, sources, seat_meta=_seat_meta(seats),
    )


def build_johor() -> dict | None:
    masters = [p for p in [find_johor_master(), find_pas_break_master()] if p]
    if not masters:
        return None
    rows, sources = load_state_rows(masters, JOHOR_PATTERN)
    seats = load_geo_seats(GEO_JOHOR)
    keywords = keywords_for_state(seats, "Johor")
    if not keywords:
        return None
    prod = load_geo_seats(OUT_DIR / "warroom_dun_Johor_production.json")
    meta = _seat_meta(prod or seats)
    return build_socmed_for_state("Johor", keywords, rows, sources, seat_meta=meta)


def write_payload(name: str, payload: dict) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / name
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    meta = payload["meta"]
    roll = payload["rollup"]
    print(f"✅ {out_path}")
    print(
        f"   {meta['state']} rows: {meta['state_rows_scanned']} · "
        f"kerusi ada mention: {roll['seats_with_mentions']} · "
        f"headline terkini: {roll['seats_with_recent_headline']}"
    )
    top = roll.get("top_seats_24h") or []
    if top:
        print(f"   Top 24j: {', '.join(f'{c}={n}' for c, n in top[:3])}")


def main() -> None:
    n9 = build_n9()
    if not n9:
        print("❌ Tiada master crawl N9", file=sys.stderr)
        sys.exit(1)
    write_payload("socmed_by_dun_N9.json", n9)

    johor = build_johor()
    if johor:
        write_payload("socmed_by_dun_Johor.json", johor)
    else:
        print("⚠️  Johor socmed tidak dibina — tiada master/geo", file=sys.stderr)


if __name__ == "__main__":
    main()
