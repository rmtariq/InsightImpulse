#!/usr/bin/env python3
"""Enrich PRN N9 seats with official SPR Helaian Mata 2023 (36 DUN).

Party column order per DUN (P=PH · N=PN · B=BN · X=bebas/kcil) — terkurasi dari nama calon SPR.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

# Susunan parti ikut urutan candVotes dalam Helaian Mata (Borang SPR 760)
PARTY_COLS: dict[str, list[str]] = {
    "N01": ["N", "P"], "N02": ["B", "N"], "N03": ["B", "N"], "N04": ["B", "N", "P"],
    "N05": ["N", "B"], "N06": ["N", "B"], "N07": ["B", "N"], "N08": ["N", "P"],
    "N09": ["X", "N", "B"], "N10": ["N", "B", "X", "P"], "N11": ["B", "P"],
    "N12": ["P", "N", "B"], "N13": ["N", "P", "X", "X"], "N14": ["P", "N", "B"],
    "N15": ["N", "B"], "N16": ["B", "N"], "N17": ["B", "N"], "N18": ["N", "P"],
    "N19": ["B", "N"], "N20": ["N", "P"], "N21": ["N", "X", "P"], "N22": ["P", "B"],
    "N23": ["P", "X", "N"], "N24": ["P", "B"], "N25": ["X", "P", "N"], "N26": ["N", "B"],
    "N27": ["N", "B"], "N28": ["B", "N"], "N29": ["B", "P"], "N30": ["N", "P"],
    "N31": ["N", "B"], "N32": ["B", "N"], "N33": ["N", "P"], "N34": ["N", "B"],
    "N35": ["N", "B"], "N36": ["B", "P"],
}

BLOC_LABEL = {"P": "PH", "N": "PN", "B": "BN", "X": "Bebas"}


def norm_code(code: str) -> str:
    if not code:
        return ""
    m = re.match(r"N\.?0*(\d+)", str(code).upper().replace(" ", ""))
    return f"N{int(m.group(1)):02d}" if m else str(code).upper()


def _tally(votes: list[int], cols: list[str]) -> dict[str, int]:
    out = {"P": 0, "N": 0, "B": 0, "X": 0}
    for v, c in zip(votes, cols):
        out[c] = out.get(c, 0) + int(v)
    return out


def _verdict(t: dict[str, int], winner_bloc: str, majority: int) -> tuple[str, str]:
    ph, pn, bn = t["P"], t["N"], t["B"]
    muafakat = pn + bn
    mvp = muafakat - ph
    if winner_bloc in ("N", "PN"):
        if majority < 1000:
            return "PERTAHAN_RAPAT", f"Pertahan PN/PAS tipis (+{majority:,})"
        return "PERTAHAN", f"Pertahan PN/PAS (+{majority:,})"
    if winner_bloc in ("B", "BN"):
        if mvp > 1500:
            return "MUAFakat_KUAT", f"Muafakat PN+BN vs PH (+{mvp:,})"
        if mvp > 0:
            return "MUAFakat_RAPAT", f"Muafakat PN+BN vs PH (+{mvp:,})"
        return "BN_PERTAHAN", f"Pertahan BN (+{majority:,})"
    # PH won
    if mvp > 1500:
        return "FLIP_KUAT", f"Flip muafakat kuat (+{mvp:,} vs PH)"
    if mvp > 0:
        return "FLIP_RAPAT", f"Flip muafakat rapat (+{mvp:,} vs PH)"
    if mvp > -1500:
        return "SUKAR", f"Sukar flip (muafakat {mvp:+,})"
    return "SANGAT_SUKAR", f"Sangat sukar (muafakat {mvp:+,})"


def _leak_note(st: dict[str, list[int]], cols: list[str]) -> str | None:
    def split(area: str) -> dict[str, int] | None:
        arr = st.get(area)
        if not arr:
            return None
        return _tally(arr, cols)

    india = split("India/Ladang")
    cina = split("Cina")
    melayu = split("Melayu/Campuran")
    parts: list[str] = []
    if india and india["P"] + india["N"] > 100:
        gap = india["P"] - india["N"]
        if abs(gap) >= 400:
            lead = "PH" if gap > 0 else "PN"
            parts.append(f"Ladang/India: {lead} +{abs(gap):,}")
    if cina and cina["P"] + cina["B"] > 100:
        if cina["P"] > cina["B"] + 300:
            parts.append(f"Cina: PH +{cina['P'] - cina['B']:,}")
        elif cina["B"] > cina["P"] + 300:
            parts.append(f"Cina: BN +{cina['B'] - cina['P']:,}")
    if melayu and melayu["P"] + melayu["N"] + melayu["B"] > 500:
        best = max(("PH", melayu["P"]), ("PN", melayu["N"]), ("BN", melayu["B"]), key=lambda x: x[1])
        parts.append(f"Melayu: {best[0]} {best[1]:,}")
    return " · ".join(parts[:2]) if parts else None


def _winner_bloc(t: dict[str, int]) -> str:
    best = max(t.items(), key=lambda x: x[1])
    return BLOC_LABEL.get(best[0], best[0])


def load_streams(path: Path | None = None) -> dict[str, dict]:
    p = path or (ROOT / "data/projects/political/PRN/PRN_N9/reports/seats/n9_scoresheet_streams_2023.json")
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def enrich_seat(code: str, raw: dict) -> dict[str, Any]:
    """Build spr2023 block for one DUN from parsed scoresheet row."""
    cols = PARTY_COLS.get(code)
    if not cols or raw.get("error"):
        return {}
    votes = raw.get("candVotes") or []
    if len(votes) != len(cols):
        return {"error": "column mismatch", "code": code}

    t = _tally(votes, cols)
    valid = raw.get("validTotal") or sum(votes)
    maj = int(raw.get("majority") or 0)
    winner_bloc_key = max(
        [(k, t[k]) for k in ("P", "N", "B")],
        key=lambda x: x[1],
    )[0]
    winner_bloc = BLOC_LABEL[winner_bloc_key]
    verdict_key, verdict_label = _verdict(t, winner_bloc_key, maj)
    st = raw.get("streamsByType") or {}

    def area_pack(area: str) -> dict | None:
        arr = st.get(area)
        if not arr:
            return None
        tt = _tally(arr, cols)
        return {"PH": tt["P"], "PN": tt["N"], "BN": tt["B"], "total": sum(tt.values())}

    muafakat = t["N"] + t["B"]
    return {
        "source": "SPR Helaian Mata PRN 2023 (Borang 760)",
        "registered": raw.get("registered"),
        "turnoutPct": raw.get("turnoutPct"),
        "validVotes": valid,
        "rejected": raw.get("rejected"),
        "spoiltPct": raw.get("spoiltPct"),
        "numCandidates": raw.get("numCands"),
        "candidateNames": raw.get("namesRaw"),
        "blocVotes": {"PH": t["P"], "PN": t["N"], "BN": t["B"], "Bebas": t["X"]},
        "winnerBloc2023": winner_bloc,
        "majorityOfficial": maj,
        "majorityPct": round(maj / valid * 100, 1) if valid else None,
        "muafakatPnBn": muafakat,
        "muafakatVsPh": muafakat - t["P"],
        "verdictKey": verdict_key,
        "verdictLabel": verdict_label,
        "streams": {
            "melayu": area_pack("Melayu/Campuran"),
            "cina": area_pack("Cina"),
            "indiaLadang": area_pack("India/Ladang"),
            "pos": area_pack("Pos"),
            "awal": area_pack("Awal"),
        },
        "leakNote": _leak_note(st, cols),
    }


def build_all_enrichment(streams: dict[str, dict] | None = None) -> dict[str, dict]:
    streams = streams or load_streams()
    out: dict[str, dict] = {}
    for code in sorted(PARTY_COLS.keys()):
        raw = streams.get(code)
        if raw:
            block = enrich_seat(code, raw)
            if block:
                out[code] = block
    return out


def summary_stats(enriched: dict[str, dict]) -> dict:
    flip_kuat = [c for c, e in enriched.items() if e.get("verdictKey") == "FLIP_KUAT"]
    flip_rapat = [c for c, e in enriched.items() if e.get("verdictKey") == "FLIP_RAPAT"]
    pertahan_tipis = [
        c for c, e in enriched.items()
        if e.get("verdictKey") == "PERTAHAN_RAPAT"
    ]
    return {
        "seatsWithData": len(enriched),
        "flipKuat": flip_kuat,
        "flipRapat": flip_rapat,
        "pertahanTipisPn": pertahan_tipis,
    }
