#!/usr/bin/env python3
"""Ingest DOSM MyCensus 2020 Johor + N9 package into War Room JSON."""
from __future__ import annotations

import csv
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT / "JITP_2026/Master_File/DOSM_MyCensus2020_Johor_N9_Data_Package"
OUT = ROOT / "data/projects/political/PRN/PRN_N9/reports/war_room/prototype/data/dosm_census_johor_n9.json"

STATE_KEY = {
    "Negeri Sembilan": "N9",
    "Johor": "Johor",
}

MYT = timezone(timedelta(hours=8))


def norm_dun(code: str) -> str:
    c = (code or "").strip().upper().replace(".", "")
    if c.startswith("N") and len(c) <= 3:
        return f"N{c[1:].zfill(2)}"
    return c


def pct(part: float, whole: float) -> float | None:
    if not whole:
        return None
    return round(part / whole * 100, 1)


def read_csv(name: str) -> list[dict]:
    path = PKG / name
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open(encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    return [r for r in rows if any((v or "").strip() for v in r.values())]


def district_ethnic_pct(row: dict) -> dict:
    pop = int(float(row.get("population") or 0))
    if not pop:
        return {}
    malay = int(float(row.get("malay") or 0))
    chinese = int(float(row.get("chinese") or 0))
    indian = int(float(row.get("indian") or 0))
    other_bumi = int(float(row.get("other_bumiputera") or 0))
    other_cit = int(float(row.get("other_citizen") or 0))
    citizen = malay + chinese + indian + other_bumi + other_cit
    base = citizen or pop
    return {
        "malay": pct(malay, base),
        "chinese": pct(chinese, base),
        "indian": pct(indian, base),
        "other": pct(other_bumi + other_cit, base),
        "source": "district_census_2020",
    }


def main() -> None:
    if not PKG.is_dir():
        raise SystemExit(f"Missing DOSM package: {PKG}")

    states_raw = {r["state"]: r for r in read_csv("DOSM_MyCensus2020_State_Summary_Johor_N9.csv")}
    districts_raw = read_csv("DOSM_MyCensus2020_District_Summary_Johor_N9.csv")
    duns_raw = read_csv("DOSM_MyCensus2020_DUN_Summary_Johor_N9.csv")

    districts_by_state: dict[str, dict[str, dict]] = {k: {} for k in STATE_KEY}
    for row in districts_raw:
        st = row["state"]
        if st not in STATE_KEY:
            continue
        name = row["district"]
        pop = int(float(row["population"]))
        districts_by_state[st][name] = {
            "district": name,
            "population": pop,
            "malePct": float(row.get("male_pct") or 0),
            "femalePct": float(row.get("female_pct") or 0),
            "noncitizenPct": float(row.get("noncitizen_pct") or 0),
            "ethnicityPct": district_ethnic_pct(row),
            "sourceUrl": row.get("source_url"),
        }

    states_out = {}
    for st, key in STATE_KEY.items():
        row = states_raw.get(st)
        if not row:
            continue
        pop = int(row.get("exact_mycensus_population") or row.get("tabular_population_rounded") or 0)
        malay = int(float(row.get("malay") or 0))
        chinese = int(float(row.get("chinese") or 0))
        indian = int(float(row.get("indian") or 0))
        other_bumi = int(float(row.get("other_bumiputera") or 0))
        other_cit = int(float(row.get("other_citizen") or 0))
        citizen = malay + chinese + indian + other_bumi + other_cit
        base = citizen or pop
        states_out[key] = {
            "state": st,
            "population": pop,
            "malePct": float(row.get("male_pct") or 0),
            "femalePct": float(row.get("female_pct") or 0),
            "noncitizenPct": float(row.get("noncitizen_pct") or 0),
            "ethnicityPct": {
                "malay": pct(malay, base),
                "chinese": pct(chinese, base),
                "indian": pct(indian, base),
                "other": pct(other_bumi + other_cit, base),
            },
            "sourceUrl": row.get("source_url"),
            "districts": districts_by_state.get(st, {}),
        }

    by_dun: dict[str, dict] = {}
    for row in duns_raw:
        st = row["state"]
        if st not in STATE_KEY:
            continue
        sk = STATE_KEY[st]
        code = norm_dun(row["dun_code"])
        pop = int(float(row["population"]))
        male = int(float(row["male"]))
        female = int(float(row["female"]))
        citizen = int(float(row["citizen"]))
        noncitizen = int(float(row["noncitizen"]))
        district = None
        # Match district from parlimen grouping in manifest is unreliable; use DUN name lookup later in UI via seat.district
        entry = {
            "stateKey": sk,
            "state": st,
            "dunCode": code,
            "dunName": row["dun_name"],
            "parliamentCode": row.get("parliament_code"),
            "parliamentName": row.get("parliament_name"),
            "population2020": pop,
            "male": male,
            "female": female,
            "citizen": citizen,
            "noncitizen": noncitizen,
            "noncitizenPct": float(row.get("noncitizen_pct") or 0),
            "sexRatio": float(row.get("sex_ratio_male_per_100_female") or 0),
            "sourceUrl": row.get("source_url"),
            "censusYear": 2020,
            "disclaimer": "MyCensus 2020 — konteks demografi penduduk, bukan pengundi atau sokongan politik.",
        }
        by_dun[f"{sk}:{code}"] = entry

    payload = {
        "meta": {
            "generated": datetime.now(MYT).strftime("%Y-%m-%d %H:%M:%S"),
            "sourcePackage": str(PKG.relative_to(ROOT)),
            "censusYear": 2020,
            "dunCount": len(by_dun),
            "states": list(states_out.keys()),
            "disclaimer": (
                "Gunakan sebagai konteks demografi (populasi 2020). "
                "Demografi pengundi PRN kekal dari SPR DPI — jangan campur sebagai indikator sokongan."
            ),
            "readme": (PKG / "README_DOSM_MyCensus2020_Johor_N9.txt").read_text(encoding="utf-8").strip(),
        },
        "states": states_out,
        "byDun": by_dun,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ DOSM census → {OUT.relative_to(ROOT)} ({len(by_dun)} DUN)")


if __name__ == "__main__":
    main()
