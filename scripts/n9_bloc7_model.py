"""N9 7-bloc senario — Python mirror of prototype/js/n9-bloc7-model.js (SPR 2023 + slider)."""
from __future__ import annotations

import math
from typing import Any

MAJORITY_N9 = 19
TOTAL_DUN = 36
PN_SANS_PENALTY = 2
PN_SANS_BERSATU_SEAT_PENALTY = 7
DEFAULT_BERSAMA_PCT = 3

BLOC_META = [
    {"id": "pas_solo", "num": 1, "label": "#1 PAS Solo", "color": "#22c55e"},
    {"id": "umno_solo", "num": 2, "label": "#2 UMNO Solo", "color": "#ef4444"},
    {"id": "mn", "num": 3, "label": "#3 MN ★", "color": "#a855f7", "default": True},
    {"id": "pn", "num": 4, "label": "#4 PN (tanpa Bersatu)", "color": "#10b981"},
    {"id": "ph", "num": 5, "label": "#5 PH", "color": "#3b82f6"},
    {"id": "bersama", "num": 6, "label": "#6 Bersama", "color": "#f59e0b"},
    {"id": "pn_plus", "num": 7, "label": "#7 PN (+ Bersatu)", "color": "#059669"},
]


def _bersatu_seat(seat: dict) -> bool:
    p = str(seat.get("party2023") or seat.get("party") or "").upper()
    return p == "BERSATU"


def compute_votes(seat: dict, bersama_pct: float = DEFAULT_BERSAMA_PCT) -> dict[str, int] | None:
    spr = seat.get("spr2023") or {}
    bv = spr.get("blocVotes") or {}
    if not bv:
        return None
    ph0 = int(bv.get("PH") or 0)
    pn0 = int(bv.get("PN") or 0)
    bn0 = int(bv.get("BN") or 0)
    bersama = round(ph0 * bersama_pct / 100)
    ph_net = ph0 - bersama
    sans = PN_SANS_BERSATU_SEAT_PENALTY if _bersatu_seat(seat) else PN_SANS_PENALTY
    pn_plus = pn0
    pn_net = round(pn0 * (1 - sans / 100))
    return {
        "pasSolo": pn0,
        "umnoSolo": bn0,
        "mn": pn_plus + bn0,
        "pn": pn_net,
        "pn_plus": pn_plus,
        "ph": ph_net,
        "bersama": bersama,
        "raw": {"ph0": ph0, "pn0": pn0, "bn0": bn0},
    }


def _spr_win(bloc_id: str, v: dict) -> bool:
    if bloc_id == "mn":
        return v["mn"] > v["ph"]
    if bloc_id == "pn":
        return v["pn"] > v["ph"]
    if bloc_id == "pn_plus":
        return v["pn_plus"] > v["ph"]
    if bloc_id == "ph":
        return v["ph"] > v["mn"]
    if bloc_id == "pas_solo":
        return v["pasSolo"] > v["ph"] and v["pasSolo"] > v["umnoSolo"]
    if bloc_id == "umno_solo":
        return v["umnoSolo"] > v["ph"] and v["umnoSolo"] > v["pasSolo"]
    return False


def _majority_prob(expected: float, majority: int = MAJORITY_N9, scale: float = 3) -> int:
    x = (expected or 0) - majority
    pct = 100 / (1 + math.exp(-x / scale))
    return int(round(max(2, min(97, pct))))


def _aggregate_spr(seats: list[dict], bloc_id: str, bersama_pct: float) -> dict:
    wins = 0
    vote_share = 0
    total_valid = 0
    for s in seats:
        v = compute_votes(s, bersama_pct)
        if not v:
            continue
        valid = v["raw"]["ph0"] + v["raw"]["pn0"] + v["raw"]["bn0"]
        total_valid += valid
        key = bloc_id
        if bloc_id == "pas_solo":
            key = "pasSolo"
        elif bloc_id == "umno_solo":
            key = "umnoSolo"
        vote_share += v.get(key, 0)
        if _spr_win(bloc_id, v):
            wins += 1
    return {
        "seatsWon": wins,
        "votePct": round(vote_share / total_valid * 100, 1) if total_valid else 0,
    }


def _model_expected(seats: list[dict], key: str) -> float:
    prob_key = {
        "pas_solo": "pasSoloWinProb",
        "umno_solo": "umnoSoloWinProb",
    }.get(key, key)
    total = 0.0
    for s in seats:
        if key == "umno_solo":
            total += (s.get("umnoSoloWinProb") or s.get("bnSoloWinProb") or 0) / 100
        else:
            total += (s.get(prob_key) or 0) / 100
    return round(total, 1)


def coalition_scenarios(seats: list[dict], bersama_pct: float = DEFAULT_BERSAMA_PCT) -> list[dict]:
    """State-level P(≥19) — selari dashboard Command Center."""
    rows: list[dict] = []
    spr_seats = [s for s in seats if (s.get("spr2023") or {}).get("blocVotes")]

    for b in BLOC_META:
        bid = b["id"]
        if bid in ("pas_solo", "umno_solo"):
            exp = _model_expected(seats, bid)
            expected = round(exp)
            mp = _majority_prob(exp)
            seat_label = f"~{expected}/{TOTAL_DUN}"
        elif bid == "bersama":
            flips = 0
            for s in spr_seats:
                base = compute_votes(s, 0)
                adj = compute_votes(s, bersama_pct)
                if base and adj and base["ph"] > base["mn"] and adj["mn"] > adj["ph"]:
                    flips += 1
            expected = flips
            mp = min(12, flips * 2)
            seat_label = f"+{flips} flip MN"
        elif bid == "pn":
            agg = _aggregate_spr(spr_seats, bid, bersama_pct)
            plus = _aggregate_spr(spr_seats, "pn_plus", bersama_pct)
            expected = agg["seatsWon"]
            vote_gap = max(0, (plus.get("votePct") or 0) - (agg.get("votePct") or 0))
            eff = round((expected - 0.4 - vote_gap / 2) * 10) / 10
            mp = _majority_prob(eff)
            seat_label = f"~{eff}/{TOTAL_DUN}"
        else:
            agg = _aggregate_spr(spr_seats, bid, bersama_pct)
            expected = agg["seatsWon"]
            mp = _majority_prob(expected)
            seat_label = f"~{expected}/{TOTAL_DUN}"

        rows.append({
            "blocId": bid,
            "num": b["num"],
            "name": b["label"] + (" ★" if b.get("default") else ""),
            "expectedSeats": expected,
            "seatLabel": seat_label,
            "majorityPct": mp,
            "color": b["color"],
        })

    # hung risk
    main = [r for r in rows if r["blocId"] != "bersama"]
    sorted_main = sorted(main, key=lambda x: x.get("majorityPct", 0), reverse=True)
    top_mp = sorted_main[0]["majorityPct"] if sorted_main else 0
    max_exp = max((r["expectedSeats"] or 0) for r in main if isinstance(r["expectedSeats"], (int, float)))
    if max_exp < MAJORITY_N9 - 2:
        hung = 25 + (MAJORITY_N9 - max_exp) * 5
    elif top_mp < 55:
        hung = max(10, 35 - max(0, top_mp - 40))
    else:
        hung = max(10, 20 - (max_exp - MAJORITY_N9) * 6)
    rows.append({
        "blocId": "hung",
        "num": 0,
        "name": "Risiko tiada majoriti",
        "expectedSeats": None,
        "seatLabel": f"tiada bloc ≥{MAJORITY_N9}",
        "majorityPct": int(round(max(10, min(42, hung)))),
        "color": "#f59e0b",
    })
    rows.sort(key=lambda x: x.get("majorityPct", 0), reverse=True)
    return rows


def seat_scenario_rows(seat: dict, bersama_pct: float = DEFAULT_BERSAMA_PCT) -> list[dict]:
    """Per-DUN scenario strip — selari dashboard drawer."""
    pas_solo = seat.get("pasSoloWinProb")
    pas_mn = seat.get("pasMnWinProb")
    umno = seat.get("umnoSoloWinProb") or seat.get("bnSoloWinProb")
    ph = seat.get("phWinProb")
    pn_est = min(100, pas_mn - 2) if pas_mn else None
    v = compute_votes(seat, bersama_pct)

    def spr_win(bid: str) -> bool | None:
        return _spr_win(bid, v) if v else None

    raw_rows: list[tuple[str, Any, str, bool | None]] = [
        ("#1 PAS Solo", pas_solo, "#22c55e", spr_win("pas_solo")),
        ("#2 UMNO Solo", umno, "#ef4444", spr_win("umno_solo")),
        ("#3 MN", pas_mn, "#a855f7", spr_win("mn")),
        ("#4 PN tanpa Bersatu", pn_est, "#10b981", spr_win("pn")),
        ("#7 PN + Bersatu", min(100, pn_est + 2) if pn_est is not None else None, "#059669", spr_win("pn_plus")),
        ("#5 PH", ph, "#3b82f6", spr_win("ph")),
        ("#6 Bersama", bersama_pct, "#f59e0b", None),
    ]
    out = []
    for label, pct, color, win in raw_rows:
        if pct is None:
            continue
        out.append({
            "label": label,
            "pct": pct,
            "pctDisplay": f"{pct}%" if "Bersama" not in label else f"{pct}% split",
            "color": color,
            "sprWin": win,
            "leader": False,
        })
    if not out:
        return out
    # highlight best scenario for this seat (max prob among model rows, prefer MN if tie)
    model_rows = [r for r in out if "Bersama" not in r["label"]]
    if model_rows:
        best = max(model_rows, key=lambda r: (r["pct"] or 0, 10 if "MN" in r["label"] else 0))
        best["leader"] = True
    return out


def seat_scenario_insight(seat: dict) -> str:
    pas_solo = seat.get("pasSoloWinProb")
    pas_mn = seat.get("pasMnWinProb")
    umno = seat.get("umnoSoloWinProb") or seat.get("bnSoloWinProb")
    parts = []
    if pas_mn and pas_solo and pas_mn > pas_solo:
        parts.append(f"MN {pas_mn}% > PAS solo {pas_solo}% (+{round(pas_mn - pas_solo, 1)}pp)")
    if pas_solo and umno and pas_solo > umno:
        parts.append(f"Lead: PAS solo vs UMNO (+{round(pas_solo - umno, 1)}pp)")
    v = compute_votes(seat)
    if v:
        winners = []
        for bid, lbl in [("mn", "MN"), ("pn", "PN"), ("pn_plus", "PN+"), ("ph", "PH")]:
            if _spr_win(bid, v):
                winners.append(lbl)
        if winners:
            parts.append(f"SPR 2023 menang: {', '.join(winners)}")
    return " · ".join(parts) if parts else "—"
