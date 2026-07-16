#!/usr/bin/env python3
"""
N9 hybrid scenario model — Command Center / war room.

Strategi MN (muafakat):
  · PAS bertanding solo (perjanjian): 23 kerusi
  · UMNO/BN bertanding solo: 13 kerusi
  · Senario hipotesis solo penuh: ~27 kerusi medan PAS

27 kerusi medan contest PAS: semua senario solo PAS > UMNO (berperingkat — 13 kuat, 14 rapat).
Lead13 = 13 teratas skor hybrid. Bukan 27/27 menang — kebarangkalian ≠ kemenangan pasti.

Bukan polling SPR. Gabungan: PRN2023 + DPI + DOSM + socmed + kategori PAS.
"""
from __future__ import annotations

from typing import Any

MAJORITY_N9 = 19
PAS_MN_23 = {
    "N02", "N03", "N04", "N05", "N09", "N10", "N13", "N14",
    "N18", "N20", "N25", "N28", "N31", "N33", "N34", "N36",
    "N06", "N07", "N15", "N16", "N17", "N19", "N35",
}
UMNO_MN_13 = {f"N{i:02d}" for i in range(1, 37)} - PAS_MN_23
# Senario S2 — 4 kerusi audit dari peruntukan UMNO13 (extend medan PAS solo; bukan overlap 23 MN)
PAS_SOLO_CONTEST_EXTRA = {"N01", "N08", "N24", "N26"}
assert PAS_SOLO_CONTEST_EXTRA <= UMNO_MN_13
PAS_SOLO_CONTEST_27 = PAS_MN_23 | PAS_SOLO_CONTEST_EXTRA
PAS_SOLO_LEAD_TARGET = 13
PAS_SOLO_LEAD_BASE = 55.0
UMNO_SOLO_BASE = 45.0


def kategori_margin(majority: int | None) -> str:
    m = int(majority or 0)
    if m <= 199:
        return "ultra_marginal"
    if m <= 499:
        return "super_marginal"
    if m <= 999:
        return "marginal"
    if m <= 2999:
        return "semi_safe"
    return "safe"


def _clamp(v: float, lo: float = 8.0, hi: float = 92.0) -> float:
    return round(max(lo, min(hi, v)), 1)


def malay_pct(seat: dict) -> float:
    demo = seat.get("demo") or {}
    dpi = seat.get("dpi") or {}
    census = seat.get("census") or {}
    eth = census.get("districtEthnicityPct") or {}
    for src in (demo.get("malay"), dpi.get("pctMelayu"), eth.get("malay"), seat.get("pctMelayu")):
        if src is not None:
            return float(src)
    return 55.0


def chinese_pct(seat: dict) -> float:
    demo = seat.get("demo") or {}
    dpi = seat.get("dpi") or {}
    census = seat.get("census") or {}
    eth = census.get("districtEthnicityPct") or {}
    for src in (demo.get("chinese"), dpi.get("pctCina"), eth.get("chinese"), seat.get("pctCina")):
        if src is not None:
            return float(src)
    return 30.0


def pas_solo_lead_score(seat: dict) -> float:
    """Skor hybrid — kerusi layak PAS solo > UMNO solo."""
    code = seat.get("code") or seat.get("id") or ""
    score = float(seat.get("pasWinProb") or 0)
    kp = seat.get("kategoriPas") or seat.get("kategori_pas") or ""
    if kp == "defend":
        score += 35
    elif kp == "winnable":
        score += 22
    elif kp == "tough":
        score += 8
    maj = int(seat.get("majority") or seat.get("majority2023") or 0)
    party = (seat.get("party2023") or seat.get("party") or "").upper()
    if party == "UMNO" and maj < 1000:
        score += 12
    if party in ("PKR", "AMANAH") and maj < 1200:
        score += 8
    if party == "BERSATU":
        score += 6
    if code in PAS_SOLO_CONTEST_EXTRA:
        score += 2
    cula = (seat.get("dpi") or {}).get("culaPct") or seat.get("culaPct") or 0
    if cula and float(cula) >= 10:
        score += min(6, float(cula) * 0.4)
    return score


def rank_pas_solo_contest_27(seats: list[dict]) -> dict[str, int]:
    """Rank 1–27 dalam medan contest PAS (1 = terkuat)."""
    pool = [s for s in seats if (s.get("code") or s.get("id")) in PAS_SOLO_CONTEST_27]
    ranked = sorted(pool, key=lambda s: pas_solo_lead_score(s), reverse=True)
    return {(s.get("code") or s.get("id")): i + 1 for i, s in enumerate(ranked)}


def select_pas_solo_lead_seats(seats: list[dict], limit: int = PAS_SOLO_LEAD_TARGET) -> set[str]:
    """13 kerusi teratas — tier Lead13 (PAS solo lead terkuat)."""
    ranks = rank_pas_solo_contest_27(seats)
    return {code for code, r in ranks.items() if r <= limit}


def _contest_solo_probs(rank: int, adj: float) -> tuple[float, float]:
    """Semua 27 contest: PAS solo > UMNO solo — margin ikut ranking."""
    if rank <= 13:
        base = 56.0 + min(4.0, (13 - rank) * 0.25)
    elif rank <= 20:
        base = 53.5 - (rank - 14) * 0.2
    else:
        base = 51.5 - (rank - 21) * 0.12
    pas_pp = max(50.4, min(72.0, base + adj))
    umno_pp = 100.0 - pas_pp
    if pas_pp <= umno_pp:
        pas_pp = umno_pp + 0.8
    return round(pas_pp, 1), round(100.0 - pas_pp, 1)


def _compute_pas_mn(
    pas_solo_pp: float,
    in_pas23: bool,
    in_contest_27: bool,
    party: str,
    winner: str,
    ph_pp: float,
    p_pas: float,
) -> float:
    """PAS+MN sentiasa ≥ PAS solo pada kerusi peruntukan PAS; boost vs PH."""
    ph_held = party in ("DAP", "PKR", "AMANAH") or winner == "PH"
    if in_pas23:
        boost = 14 if ph_held else 10
        return min(92.0, max(pas_solo_pp + boost, p_pas * 100 + 12))
    if in_contest_27:
        return min(88.0, max(pas_solo_pp + 8, p_pas * 100 + 10))
    if ph_held:
        return min(75.0, max(pas_solo_pp + 4, p_pas * 100 + 6))
    return min(85.0, max(pas_solo_pp + 3, p_pas * 100 + 4))


def _is_ph_held(party: str, winner: str) -> bool:
    return party in ("DAP", "PKR", "AMANAH") or winner == "PH"


def _compute_ph_pp(maj: int, chinese: float) -> float:
    return min(72.0, max(38.0, 48 + min(20, maj / 500.0) + (chinese / 15.0)))


def _contest_solo_ph_low(adj: float) -> tuple[float, float]:
    """PH sandang — solo PAS vs UMNO rendah & rapat (MN belum mengatasi PH)."""
    pas_pp = max(48.8, min(51.2, 50.0 + adj * 0.25))
    if pas_pp <= 50.0:
        pas_pp = 50.0 + max(0.4, adj * 0.12)
    umno_pp = 100.0 - pas_pp
    if pas_pp <= umno_pp:
        pas_pp = umno_pp + 0.6
        umno_pp = 100.0 - pas_pp
    return round(pas_pp, 1), round(umno_pp, 1)


def _boost_ph_solo_when_mn_wins(
    legacy: float, adj: float, pas_mn_pp: float, ph_pp: float
) -> tuple[float, float]:
    """MN > PH → PAS solo jelas melebihi UMNO solo dan legacy."""
    margin = pas_mn_pp - ph_pp
    pas_pp = min(65.0, max(legacy + 12, 53.0 + margin * 0.28 + adj * 0.4))
    pas_pp = max(pas_pp, legacy + 8, 52.5)
    umno_pp = round(100.0 - pas_pp, 1)
    return pas_pp, umno_pp


def _solo_data_adj(seat: dict, km: str, maj: int, malay: float, chinese: float, sm: dict | None) -> float:
    malay_w = max(0.0, min(1.0, (malay - 42.0) / 48.0))
    adj = {"ultra_marginal": 2.0, "super_marginal": 1.5, "marginal": 1.0, "semi_safe": -0.5, "safe": -1.0}.get(km, 0)
    adj += (malay_w - 0.5) * 2.0
    if maj <= 200:
        adj += 1.0
    elif maj <= 500:
        adj += 0.5
    adj += min(0.6, chinese / 100.0 * 0.5) - 0.15
    mentions = (sm or {}).get("mentions_total") or 0
    if mentions >= 2:
        neg = (sm or {}).get("neg_pct") or 0
        adj += max(-1.0, min(1.0, (neg - 40) * 0.05))
    return max(-3.0, min(3.0, adj))


def _two_way_solo(pas_pp: float, adj: float) -> tuple[float, float]:
    pas_pp = max(48.0, min(62.0, pas_pp + adj))
    return pas_pp, 100.0 - pas_pp


def pas_solo_vs_umno_edge(pas_pp: float, umno_pp: float) -> tuple[str, float]:
    gap = round(pas_pp - umno_pp, 1)
    if abs(gap) <= 3.0:
        return "close", gap
    return ("pas_lead", gap) if gap > 0 else ("umno_lead", gap)


def predict_n9_seat_scenarios(
    seat: dict,
    socmed: dict | None = None,
    pas_lead_set: set[str] | None = None,
    contest_rank: dict[str, int] | None = None,
) -> dict[str, Any]:
    code = (seat.get("code") or seat.get("id") or "").upper()
    party = (seat.get("party2023") or seat.get("party") or "").upper()
    winner = (seat.get("winner2023") or seat.get("winner2022") or "").upper()
    maj = int(seat.get("majority") or seat.get("majority2023") or 0)
    km = kategori_margin(maj)
    malay = malay_pct(seat)
    chinese = chinese_pct(seat)
    sm = socmed or {}
    pas_lead = pas_lead_set or set()
    in_contest_27 = code in PAS_SOLO_CONTEST_27
    in_pas23 = code in PAS_MN_23
    in_umno13 = code in UMNO_MN_13
    is_lead = code in pas_lead

    p_pas = float(seat.get("pasWinProb") or 0) / 100.0
    pas_pn = float(seat.get("scenarioPasPn") or min(92, (seat.get("pasWinProb") or 0) + 5)) / 100.0
    rank = (contest_rank or {}).get(code, 99)
    contest_tier = "lead13" if rank <= 13 else ("mid" if rank <= 20 else "slight") if in_contest_27 else None

    adj = _solo_data_adj(seat, km, maj, malay, chinese, sm)
    archetype = "other"
    pas_mn_pp: float | None = None
    ctx: dict[str, Any] = {
        "hybridModel": True,
        "n9Allocation": "PAS23" if in_pas23 else ("UMNO13" if in_umno13 else "other"),
        "pasSoloContest27": in_contest_27,
        "pasSoloLead13": is_lead,
        "contestRank27": rank if in_contest_27 else None,
        "contestTier": contest_tier,
        "malayPct": round(malay, 1),
        "chinesePct": round(chinese, 1),
        "majority2023": maj,
        "kategoriMargin": km,
        "soloDataAdjPct": round(adj, 1),
    }

    if party == "PAS":
        pas_solo_pp = min(82.0, max(68.0, 72 + adj))
        umno_pp = max(8.0, (100 - pas_solo_pp) * 0.35)
        ph_pp = max(5.0, 100 - pas_solo_pp - umno_pp)
        archetype = "pas_sandang"
    elif party == "BERSATU":
        pas_solo_pp = min(72.0, max(55.0, 58 + adj + p_pas * 8))
        umno_pp = max(12.0, 100 - pas_solo_pp - 18)
        ph_pp = 18.0
        archetype = "pn_sandang"
    elif in_contest_27:
        ph_held = _is_ph_held(party, winner)
        legacy = float(seat.get("pasWinProb") or 15)
        if ph_held:
            ph_pp = _compute_ph_pp(maj, chinese)
            pas_solo_pp, umno_pp = _contest_solo_ph_low(adj)
            pas_mn_pp = _compute_pas_mn(pas_solo_pp, in_pas23, in_contest_27, party, winner, ph_pp, p_pas)
            if pas_mn_pp > ph_pp:
                pas_solo_pp, umno_pp = _boost_ph_solo_when_mn_wins(legacy, adj, pas_mn_pp, ph_pp)
                pas_mn_pp = _compute_pas_mn(pas_solo_pp, in_pas23, in_contest_27, party, winner, ph_pp, p_pas)
                archetype = "ph_mn_over_ph"
                ctx["insightNote"] = "PH sandang · MN > PH — PAS solo dipertingkat vs legacy & UMNO"
                ctx["mnOverPh"] = True
            else:
                archetype = "ph_stronghold"
                ctx["insightNote"] = "PH sandang kuat (PH > MN) — solo PAS/UMNO rendah; fokus elak 3 penjuru"
                ctx["mnOverPh"] = False
            ctx["legacyPasWinProb"] = legacy
            ctx["phSandang"] = True
        else:
            pas_solo_pp, umno_pp = _contest_solo_probs(rank, adj)
            ph_pp = max(8.0, 22.0 - malay / 8.0)
            pas_mn_pp = None
            if is_lead:
                archetype = "pas_solo_lead_13"
                ctx["soloScenarioBase"] = f"{PAS_SOLO_LEAD_BASE:.0f}/{UMNO_SOLO_BASE:.0f}"
            elif contest_tier == "mid":
                archetype = "pas_solo_lead_mid"
                ctx["insightNote"] = "27 contest — PAS solo lead rapat vs UMNO; MN vs PH lebih realistik"
            else:
                archetype = "pas_solo_lead_slight"
                ctx["insightNote"] = "27 contest — PAS solo lead tipis vs UMNO; kebergantungan MN tinggi"
    elif in_umno13:
        umno_pp, pas_solo_pp = _two_way_solo(PAS_SOLO_LEAD_BASE, -adj - 2.0)
        ph_pp = min(55.0, max(18.0, 28 + chinese / 4.0))
        archetype = "umno13_contest"
        ctx["insightNote"] = "Peruntukan UMNO 13 — contest vs PH; PAS tidak field solo"
    elif party in ("DAP", "PKR", "AMANAH") or winner == "PH":
        ph_pp = min(72.0, max(38.0, 48 + min(20, maj / 500.0) + (chinese / 15.0)))
        umno_pp = max(12.0, 16 + malay / 12.0)
        pas_solo_pp = max(10.0, 14 + malay / 10.0 + p_pas * 5)
        total = ph_pp + umno_pp + pas_solo_pp
        if total > 88:
            s = 85 / total
            ph_pp, umno_pp, pas_solo_pp = ph_pp * s, umno_pp * s, pas_solo_pp * s
        archetype = "ph_campuran"
    else:
        umno_pp = min(58.0, max(42.0, 50 - adj))
        pas_solo_pp = 100 - umno_pp
        ph_pp = 12.0
        archetype = "bn_other"

    if pas_mn_pp is None:
        pas_mn_pp = _compute_pas_mn(pas_solo_pp, in_pas23, in_contest_27, party, winner, ph_pp, p_pas)
    pas_mn = pas_mn_pp / 100.0
    ctx["pasMnBoostPct"] = round(pas_mn_pp - pas_solo_pp, 1)

    pas_solo = pas_solo_pp / 100.0
    umno_solo = umno_pp / 100.0
    ph = ph_pp / 100.0

    edge, gap = pas_solo_vs_umno_edge(pas_solo_pp, umno_pp)
    ctx["pasSoloVsUmno"] = edge
    ctx["pasSoloUmnoGapPct"] = gap
    ctx["seatArchetype"] = archetype

    scenario_base = {
        "pasWinProb": _clamp(float(seat.get("pasWinProb") or 0)),
        "pasSoloWinProb": _clamp(pas_solo_pp),
        "pasMnWinProb": _clamp(pas_mn * 100),
        "pasPnWinProb": _clamp(pas_pn * 100),
        "umnoSoloWinProb": _clamp(umno_pp),
        "bnSoloWinProb": _clamp(umno_pp),
        "phWinProb": _clamp(ph_pp),
    }

    return {
        "pasSoloWinProb": _clamp(pas_solo_pp),
        "pasMnWinProb": _clamp(pas_mn * 100),
        "pasPnWinProb": _clamp(pas_pn * 100),
        "umnoSoloWinProb": _clamp(umno_pp),
        "bnSoloWinProb": _clamp(umno_pp),
        "phWinProb": _clamp(ph_pp),
        "pasSoloVsUmno": edge,
        "pasSoloUmnoGapPct": gap,
        "n9Archetype": archetype,
        "scenarioBase": scenario_base,
        "scenarioMeta": {
            "party2023": party,
            "bloc2023": winner,
            "kategoriMargin": km,
            "majority2023": maj,
            "malayPct": round(malay, 1),
            "chinesePct": round(chinese, 1),
            "n9Allocation": ctx["n9Allocation"],
            "pasSoloContest27": in_contest_27,
            "pasSoloLead13": is_lead,
        },
        "modelContext": {
            "methodology": (
                "Agihan MN (HQ): PAS/PN 13 kerusi (9 wajib + 4 berhasrat), UMNO/BN 23 kerusi. "
                "Senario solo Melayu (27 kerusi): PAS > UMNO — 13 jelas, 14 rapat. "
                "PAS+MN > PAS solo. SPR."
            ),
            **ctx,
        },
    }


def compute_n9_mn_insight(seats: list[dict], pas_lead_set: set[str] | None = None) -> dict[str, Any]:
    if not seats:
        return {}
    lead = pas_lead_set or select_pas_solo_lead_seats(seats)
    contest = [s for s in seats if (s.get("code") or s.get("id")) in PAS_SOLO_CONTEST_27]
    pas_lead_n = sum(1 for s in seats if s.get("pasSoloVsUmno") == "pas_lead" or (s.get("code") or s.get("id")) in lead)
    pas_mn_exp = round(sum((s.get("pasMnWinProb") or s.get("scenarioPasMn") or 0) / 100 for s in seats), 1)
    pas_solo_exp = round(sum((s.get("pasSoloWinProb") or 0) / 100 for s in seats), 1)
    flip_from_lead = round(sum((s.get("pasSoloWinProb") or 0) / 100 for s in seats if (s.get("code") or s.get("id")) in lead), 1)

    return {
        "majorityThreshold": MAJORITY_N9,
        "totalSeats": len(seats),
        "pasMn23": len(PAS_MN_23),
        "umnoMn13": len(UMNO_MN_13),
        "pasSoloContest27": len(PAS_SOLO_CONTEST_27),
        "pasSoloLead13": len(lead),
        "pasSoloLeadCodes": sorted(lead),
        "expectedMnBlocSeats": pas_mn_exp,
        "expectedPasSoloSeats": pas_solo_exp,
        "expectedFlipsFromLead13": flip_from_lead,
        "mnReachesMajority": pas_mn_exp >= MAJORITY_N9,
        "soloInsight": {
            "contest27Note": (
                f"Senario solo Melayu ({len(PAS_SOLO_CONTEST_27)} kerusi): PAS dijangka > UMNO — "
                f"{len(lead)} kerusi jelas, {max(0, len(contest) - len(lead))} kerusi rapat."
            ),
            "expectedFlipsFromLead13": flip_from_lead,
            "phInContest27": sorted(
                (s.get("code") or s.get("id"))
                for s in contest
                if (s.get("party2023") or s.get("party") or "").upper() in ("DAP", "PKR", "AMANAH")
                or (s.get("winner2023") or s.get("winner2022") or "").upper() == "PH"
            ),
            "notAll27Wins": (
                f"27/27 PAS solo > UMNO solo (berperingkat) — flip dijangka ~{flip_from_lead:.1f} "
                f"dari 13 lead kuat, bukan menang semua."
            ),
        },
        "mbNote": (
            f"Agihan MN (HQ): PAS/PN 13 kerusi (9 wajib + 4 berhasrat) · UMNO/BN 23 kerusi. "
            f"Bloc PAS+MN dijangka ~{pas_mn_exp} kerusi (majoriti = {MAJORITY_N9}). "
            f"PAS realistik cerah ~3 drpd 4 berhasrat (Chennah terbaik · Nilai stretch)."
        ),
        "disclaimer": "Model hibrid PRN2023 + DPI + DOSM + socmed. SPR.",
    }
