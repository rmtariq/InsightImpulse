#!/usr/bin/env python3
"""
Hybrid PRN Johor seat scenarios — analitik profesional, berasaskan data.

Kerusi UMNO (33): senario solo dua penjuru PAS 55% vs UMNO 45% (±laras data),
  BUKAN bermaksud PAS menang 33/33 — dijangka flip ~18/33 (55% × 33).
Kerusi PAS/PN sandang: PAS solo tinggi (disahkan).
Kerusi PH: campuran PH + BN + PAS/MN realistik.
MB Johor = laluan MN (≥29) + rundingan.
"""
from __future__ import annotations

from typing import Any

POST_MADANI_CONTEXT = True
PH_TRUST_COLLAPSE_SIGNAL = 0.18
ECON_UNCERTAINTY_PH_BASE = 0.10
ECON_UNCERTAINTY_CHINESE_EXTRA = 0.10
MADANI_MALAY_BACKLASH_MAX = 0.28
MAJORITY_JOHOR = 29
UMNO_SOLO_PAS_PCT = 55.0  # asas senario solo: PAS vs UMNO dua penjuru
UMNO_SOLO_BN_PCT = 45.0


def kategori_margin(majority: int | None) -> str:
    maj = int(majority or 0)
    if maj <= 300:
        return "ultra_marginal"
    if maj <= 800:
        return "super_marginal"
    if maj <= 2000:
        return "marginal"
    if maj <= 5000:
        return "semi_safe"
    return "safe"


def _clamp(v: float, lo: float = 8.0, hi: float = 92.0) -> float:
    return round(max(lo, min(hi, v)), 1)


def malay_pct(seat: dict) -> float:
    demo = seat.get("demo") or {}
    census = seat.get("census") or {}
    eth = census.get("districtEthnicityPct") or {}
    if demo.get("malay") is not None:
        return float(demo["malay"])
    if eth.get("malay") is not None:
        return float(eth["malay"])
    return 55.0


def chinese_pct(seat: dict) -> float:
    demo = seat.get("demo") or {}
    census = seat.get("census") or {}
    eth = census.get("districtEthnicityPct") or {}
    if demo.get("chinese") is not None:
        return float(demo["chinese"])
    if eth.get("chinese") is not None:
        return float(eth["chinese"])
    return 30.0


def estimate_pas_base_prob(party: str, status: str, majority: int | None, malay: float = 55.0) -> float:
    """Peluang PN/PAS menang kerusi — asas rule-based."""
    p = (party or "").upper()
    st = (status or "battleground").lower()
    maj = int(majority or 0)
    km_val = kategori_margin(maj)
    base = {
        "PN": 68.0, "PAS": 72.0, "BERSATU": 65.0,
        "BN": 30.0, "UMNO": 32.0, "MCA": 28.0, "MIC": 26.0,
        "PH": 16.0, "DAP": 14.0, "PKR": 18.0, "AMANAH": 20.0,
        "MUDA": 22.0, "ALONE": 22.0,
    }.get(p, 25.0)
    if p in ("PAS", "BERSATU", "PN"):
        base += min(12.0, maj / 100.0)
    elif p in ("BN", "UMNO", "MCA", "MIC", "PH", "DAP", "PKR", "AMANAH", "MUDA"):
        base -= min(12.0, maj / 250.0)
    if st == "stronghold":
        if p in ("PN", "PAS", "BERSATU"):
            base = min(88.0, base + 8.0)
        else:
            base = max(10.0, base - 6.0)
    elif st == "battleground" and p in ("BN", "UMNO"):
        base = max(18.0, min(45.0, base))
    if POST_MADANI_CONTEXT and p in ("BN", "UMNO", "MCA", "MIC"):
        malay_boost = max(0.0, (malay - 50.0) / 50.0) * 12.0
        base += malay_boost
        if km_val in ("ultra_marginal", "super_marginal"):
            base += 3.0
    return _clamp(base)


def _historical_bn_strength(km: str, maj: int) -> float:
    """Kekuatan penyandang BN/UMNO PRN 2022 — dicairkan pasca-Madani, bukan dibuang."""
    table = {
        "ultra_marginal": 0.48, "super_marginal": 0.54, "marginal": 0.62,
        "semi_safe": 0.70, "safe": 0.76,
    }
    s = table.get(km, 0.58)
    if maj >= 5000:
        s += 0.04
    return min(0.82, s)


def _umno_pas_solo_mult(km: str) -> float:
    """PAS solo vs undi protes — lebih tinggi di marginal, bukan semua kerusi."""
    return {
        "ultra_marginal": 0.92,
        "super_marginal": 0.86,
        "marginal": 0.80,
        "semi_safe": 0.72,
        "safe": 0.65,
    }.get(km, 0.75)


def pas_solo_vs_bn_edge(pas_solo: float, bn: float) -> tuple[str, float]:
    """Klasifikasi per kerusi dari gap PAS solo vs BN solo."""
    gap = round((pas_solo - bn) * 100, 1)
    if abs(gap) <= 3.0:
        return "close", gap
    return ("pas_lead", gap) if gap > 0 else ("bn_lead", gap)


def umno_solo_data_adjustment(
    km: str,
    maj: int,
    malay: float,
    chinese: float,
    sm: dict | None = None,
) -> float:
    """Pelarasan ±pp pada asas 55/45 — dari majoriti, etnik, socmed (max ±3pp)."""
    malay_w = max(0.0, min(1.0, (malay - 42.0) / 48.0))
    adj = {
        "ultra_marginal": 2.0,
        "super_marginal": 1.5,
        "marginal": 1.0,
        "semi_safe": -0.5,
        "safe": -1.0,
    }.get(km, 0.0)
    adj += (malay_w - 0.5) * 2.0
    if maj <= 400:
        adj += 1.0
    elif maj <= 800:
        adj += 0.5
    adj += min(0.8, chinese / 100.0 * 0.6) - 0.2
    mentions = (sm or {}).get("mentions_total") or 0
    if mentions >= 2:
        neg = (sm or {}).get("neg_pct") or 0
        adj += max(-1.0, min(1.0, (neg - 40) * 0.05))
    return max(-3.0, min(3.0, adj))


def compute_umno_hybrid_solo(
    seat: dict,
    km: str,
    maj: int,
    malay: float,
    chinese: float,
    p_pas: float,
    sm: dict | None = None,
) -> tuple[float, float, dict[str, Any]]:
    """
    Senario solo kerusi UMNO: PAS 55% vs UMNO 45% (dua penjuru = 100%).
    Pelarasan kecil dari PRN2022 + DOSM + socmed — bukan inflate 33/33 menang.
    """
    adj = umno_solo_data_adjustment(km, maj, malay, chinese, sm)
    pas_pp = UMNO_SOLO_PAS_PCT + adj
    pas_pp = max(52.0, min(58.0, pas_pp))
    bn_pp = 100.0 - pas_pp
    pas_solo = pas_pp / 100.0
    bn = bn_pp / 100.0

    ctx: dict[str, Any] = {
        "hybridModel": True,
        "seatArchetype": "umno_sandang",
        "hybridLayers": ["prn2022_majority", "dosm_ethnicity", "socmed_crawl"],
        "soloScenarioBase": f"{UMNO_SOLO_PAS_PCT}/{UMNO_SOLO_BN_PCT}",
        "soloDataAdjPct": round(adj, 1),
        "hybridGapTargetPct": round(pas_pp - bn_pp, 1),
        "socmedMentions": (sm or {}).get("mentions_total") or 0,
        "malayPct": round(malay, 1),
        "chinesePct": round(chinese, 1),
        "majority2022": maj,
        "kategoriMargin": km,
        "insightNote": (
            f"Senario solo: PAS {pas_pp:.0f}% vs UMNO {bn_pp:.0f}% — "
            "bukan jaminan menang; probabiliti per kerusi."
        ),
    }
    return bn, pas_solo, ctx


def compute_pn_sandang_solo(party: str, km: str, p_pas: float) -> tuple[float, float]:
    """Kerusi PAS/Bersatu sandang — PAS solo tinggi, disahkan."""
    if party == "PAS":
        pas_solo = min(0.88, max(0.72, p_pas * 0.98))
        bn = max(0.06, (1.0 - pas_solo) * 0.35)
    else:  # BERSATU
        pas_solo = min(0.78, max(0.58, p_pas * 0.85))
        bn = max(0.08, (1.0 - pas_solo) * 0.40)
    return bn, pas_solo


def compute_ph_seat_scenarios(
    party: str, km: str, maj: int, malay: float, chinese: float, p_pas: float,
) -> tuple[float, float, float]:
    """Kerusi PH — campuran PH + BN + PAS/MN (3–4 penjuru), PH fav di bandar/Cina."""
    margin_ph_boost = {
        "ultra_marginal": 0.06, "super_marginal": 0.08, "marginal": 0.10,
        "semi_safe": 0.14, "safe": 0.18,
    }.get(km, 0.10)
    ph = 0.42 + margin_ph_boost + min(0.28, maj / 4500.0)
    if party == "DAP" and chinese >= 35:
        ph += 0.08
    if maj >= 5000:
        ph += 0.06
    ph = min(0.78, max(0.38, ph - p_pas * 0.06))
    bn = max(0.10, 0.18 + malay / 100.0 * 0.10 - chinese / 250.0)
    pas_solo = max(0.10, 0.14 + malay / 100.0 * 0.12 + p_pas * 0.06)
    total = ph + bn + pas_solo
    if total > 0.90:
        scale = 0.86 / total
        ph, bn, pas_solo = ph * scale, bn * scale, pas_solo * scale
    return bn, pas_solo, ph


def apply_post_madani_context(
    seat: dict,
    party: str,
    bloc: str,
    km: str,
    maj: int,
    p_pas: float,
    bn: float,
    ph: float,
    pas_solo: float,
    pas_mn: float,
    *,
    madani_mult: float = 1.0,
    ph_trust_mult: float = 1.0,
) -> tuple[float, float, float, float, float, dict[str, float]]:
    factors: dict[str, float] = {}
    if not POST_MADANI_CONTEXT:
        return p_pas, bn, ph, pas_solo, pas_mn, factors

    malay = malay_pct(seat)
    chinese = chinese_pct(seat)
    malay_w = max(0.0, min(1.0, (malay - 42.0) / 48.0))

    if bloc == "BN" or party in ("UMNO", "MCA", "MIC"):
        madani_bn_pen = (0.08 + malay_w * MADANI_MALAY_BACKLASH_MAX) * madani_mult
        if party == "UMNO":
            madani_bn_pen += 0.03 * madani_mult
        if km in ("ultra_marginal", "super_marginal"):
            madani_bn_pen += 0.04 * madani_mult

        bn_before = bn
        bn_after = bn * max(0.38, 1.0 - madani_bn_pen)
        swing = (bn_before - bn_after) / 100.0

        if party == "UMNO":
            # Solo split dari model hibrid — Madani hanya alir ke MN & pasWinProb
            p_pas = min(0.72, p_pas + swing * 0.55)
            pas_mn = min(0.96, pas_mn + swing * 0.72 + malay_w * 0.02)
        else:
            bn = bn_after
            solo_share = 0.40
            pas_solo = min(0.72, pas_solo + swing * solo_share)
            p_pas = min(0.72, p_pas + swing * 0.55)
            pas_mn = min(0.96, pas_mn + swing * 0.72 + malay_w * 0.02)

        factors["madaniBnPenaltyPct"] = round(madani_bn_pen * 100, 1)
        factors["malayPct"] = round(malay, 1)

    if party in ("DAP", "PKR", "AMANAH") or bloc == "PH":
        ph_pen = PH_TRUST_COLLAPSE_SIGNAL * ph_trust_mult
        if party == "DAP":
            ph_pen += 0.06 * ph_trust_mult
        if malay >= 35:
            ph_pen += 0.04 * ph_trust_mult
        econ_pen = ECON_UNCERTAINTY_PH_BASE
        if chinese >= 30:
            econ_pen += ECON_UNCERTAINTY_CHINESE_EXTRA * min(1.0, chinese / 55.0)
        if party == "DAP" and chinese >= 40:
            econ_pen += 0.04
        ph_pen += econ_pen * ph_trust_mult
        if chinese >= 45 and malay < 42:
            ph_pen *= 0.85

        ph_before = ph
        ph *= max(0.20, 1.0 - ph_pen)
        swing_ph = (ph_before - ph) / 100.0
        pas_solo += swing_ph * 0.30
        bn += swing_ph * 0.25
        p_pas = min(0.68, p_pas + swing_ph * 0.22)

        factors["phTrustPenaltyPct"] = round(ph_pen * 100, 1)
        factors["econPhPenaltyPct"] = round(econ_pen * 100, 1)

    if party in ("MCA", "MIC"):
        bn *= 0.96
        ph = max(ph, 0.02)

    factors["postMadaniContext"] = 1.0
    return p_pas, bn, ph, pas_solo, pas_mn, factors


def apply_socmed_adjustment(probs: dict[str, float], sm: dict | None) -> dict[str, float]:
    ctx = probs.get("modelContext") or {}
    if ctx.get("hybridModel"):
        return probs
    if not sm or not (sm.get("mentions_total") or 0):
        return probs
    neg = sm.get("neg_pct") or 0
    pos = sm.get("pos_pct") or 0
    delta = 0.0
    if neg >= 45:
        delta -= 3.0
    elif pos >= 50:
        delta += 2.0
    if not delta:
        return probs
    out = dict(probs)
    for key in ("pasWinProb", "pasSoloWinProb", "pasMnWinProb"):
        if key in out:
            out[key] = _clamp((out[key] or 0) + delta)
    if delta < 0:
        for key in ("bnSoloWinProb", "phWinProb"):
            if key in out:
                out[key] = _clamp((out[key] or 0) - delta * 0.5)
    return out


def compute_johor_mb_insight(seats: list[dict]) -> dict[str, Any]:
    """
    Laluan MB Johor via MN — analitik peringkat negeri, bukan tipu per kerusi.

    PAS layak tuan hati MB jika bloc MN capai 29+ DUN dan PAS membawa
    kerusi menang langsung + flip yang cukup; bukan auto MB.
    """
    if not seats:
        return {}
    pas_solo_exp = round(sum((s.get("pasSoloWinProb") or 0) / 100 for s in seats), 1)
    pas_mn_exp = round(sum((s.get("pasMnWinProb") or 0) / 100 for s in seats), 1)
    bn_solo_exp = round(sum((s.get("bnSoloWinProb") or 0) / 100 for s in seats), 1)
    ph_exp = round(sum((s.get("phWinProb") or 0) / 100 for s in seats), 1)

    umno = [s for s in seats if s.get("party2022") == "UMNO"]
    pas_lead = sum(1 for s in umno if s.get("pasSoloVsBn") == "pas_lead")
    bn_lead = sum(1 for s in umno if s.get("pasSoloVsBn") == "bn_lead")
    close = sum(1 for s in umno if s.get("pasSoloVsBn") == "close")
    umno_flip_exp = round(
        sum((s.get("pasSoloWinProb") or 0) / 100 for s in umno), 1,
    )

    pas_direct = round(
        sum(
            (s.get("pasSoloWinProb") or 0) / 100
            for s in seats
            if s.get("party2022") in ("PAS", "BERSATU")
        )
        + umno_flip_exp,
        1,
    )

    mn_majority = pas_mn_exp >= MAJORITY_JOHOR
    mb_eligible = mn_majority and pas_direct >= 8

    return {
        "majorityThreshold": MAJORITY_JOHOR,
        "totalSeats": len(seats),
        "expectedPasSoloSeats": pas_solo_exp,
        "expectedMnBlocSeats": pas_mn_exp,
        "expectedBnSoloSeats": bn_solo_exp,
        "expectedPhSeats": ph_exp,
        "umnoSeatBreakdown": {"pasSoloLead": pas_lead, "bnSoloLead": bn_lead, "close": close},
        "umnoSoloInsight": {
            "totalUmnoSeats": len(umno),
            "soloScenarioBase": f"PAS {UMNO_SOLO_PAS_PCT:.0f}% vs UMNO {UMNO_SOLO_BN_PCT:.0f}% (dua penjuru)",
            "expectedFlipsFromUmno": umno_flip_exp,
            "notAll33Wins": (
                f"PAS solo fav pada 33 kerusi UMNO ≠ menang 33/33. "
                f"Dijangka ~{umno_flip_exp}/33 flip (purata probabiliti ~55%)."
            ),
        },
        "estimatedPasDirectWinsUnderMn": pas_direct,
        "mnReachesMajority": mn_majority,
        "pasMbEligibility": "layak_runding" if mb_eligible else "perlu_flip_lagi",
        "mbNote": (
            f"MB Johor perlukan ≥{MAJORITY_JOHOR}/56 kerusi. MN dijangka ~{pas_mn_exp} kerusi; "
            f"PAS solo ~{pas_solo_exp} kerusi. PAS layak tuan hati MB jika MN capai majoriti "
            f"dan PAS sumbangan kerusi menang (flip+sandang) ≥8 — melalui rundingan, bukan auto."
        ),
        "disclaimer": (
            "Model hibrid PRN 2022 + DOSM + socmed. Kerusi UMNO: senario solo 55/45. "
            "SPR. Probabiliti ≠ jaminan menang."
        ),
    }


def predict_johor_seat(seat: dict, socmed: dict | None = None) -> dict[str, Any]:
    party = (seat.get("party2022") or seat.get("semasaParti") or seat.get("party") or "").upper()
    bloc = (seat.get("winner2022") or seat.get("party") or "").upper()
    maj = int(seat.get("majority2022") or seat.get("majority") or 0)
    status = (seat.get("status") or "battleground").lower()
    km = kategori_margin(maj)
    malay = malay_pct(seat)
    chinese = chinese_pct(seat)
    hybrid_ctx: dict[str, Any] = {}

    pas_base = seat.get("pasWinProb")
    if pas_base is None:
        pas_base = estimate_pas_base_prob(party, status, maj, malay)
    p_pas = float(pas_base) / 100.0

    margin_ph_boost = {
        "ultra_marginal": 0.04, "super_marginal": 0.06, "marginal": 0.08,
        "semi_safe": 0.12, "safe": 0.16,
    }.get(km, 0.08)

    ph = max(0.02, 0.05 - p_pas * 0.04)
    if party in ("DAP", "PKR", "AMANAH") or bloc == "PH":
        bn, pas_solo, ph = compute_ph_seat_scenarios(party, km, maj, malay, chinese, p_pas)
    elif party in ("MCA", "MIC") and maj >= 1500:
        ph = max(0.04, 0.10 - p_pas * 0.08)

    if party == "UMNO":
        bn, pas_solo, hybrid_ctx = compute_umno_hybrid_solo(
            seat, km, maj, malay, chinese, p_pas, socmed,
        )
    elif party in ("PAS", "BERSATU"):
        bn, pas_solo = compute_pn_sandang_solo(party, km, p_pas)
    elif bloc == "BN" or party in ("MCA", "MIC"):
        hist = _historical_bn_strength(km, maj)
        bn = hist * (1.0 - p_pas * 0.32)
        bn = min(0.78, bn)
    elif bloc == "PH":
        pass  # sudah dikira
    elif party == "MUDA":
        bn = max(0.10, (1.0 - p_pas) * 0.32)
    else:
        bn = max(0.08, (1.0 - p_pas) * 0.50)

    if party == "PAS":
        pass
    elif party == "BERSATU":
        pass
    elif party == "UMNO":
        pass
    elif party in ("DAP", "PKR", "AMANAH") or bloc == "PH":
        pass
    elif bloc == "BN" or party in ("MCA", "MIC"):
        pas_solo = max(0.08, p_pas * (0.82 if km == "ultra_marginal" else 0.74))
    elif party == "MUDA":
        pas_solo = max(0.08, p_pas * 0.68)
    else:
        pas_solo = max(0.08, p_pas * 0.68)

    if bloc == "PH":
        pas_mn = pas_solo + malay / 100.0 * 0.06
    elif bloc == "BN" or party in ("UMNO", "MCA", "MIC"):
        pas_mn = min(0.96, p_pas + (1.0 - p_pas) * (0.86 - malay / 1200.0))
    elif bloc == "PN" or party in ("PAS", "BERSATU"):
        pas_mn = min(0.95, max(p_pas, 0.62))
    elif party == "MUDA":
        pas_mn = max(0.15, p_pas * 0.45)
    else:
        pas_mn = p_pas * 0.35

    scenario_base = {
        "pasWinProb": _clamp(float(pas_base)),
        "pasSoloWinProb": _clamp(pas_solo * 100),
        "pasMnWinProb": _clamp(pas_mn * 100),
        "bnSoloWinProb": _clamp(bn * 100),
        "phWinProb": _clamp(ph * 100),
    }
    scenario_meta = {
        "party2022": party,
        "bloc2022": bloc,
        "kategoriMargin": km,
        "majority2022": maj,
        "malayPct": round(malay, 1),
        "chinesePct": round(chinese, 1),
    }

    p_pas, bn, ph, pas_solo, pas_mn, ctx = apply_post_madani_context(
        seat, party, bloc, km, maj, p_pas, bn, ph, pas_solo, pas_mn,
    )
    if party == "UMNO":
        ctx = {**hybrid_ctx, **ctx}
    pas_base_adj = _clamp(p_pas * 100)

    edge, gap = pas_solo_vs_bn_edge(pas_solo, bn)
    ctx["pasSoloVsBn"] = edge
    ctx["pasSoloBnGapPct"] = gap

    predicted_bloc = bloc
    if p_pas >= 0.50 and party not in ("DAP", "PKR", "AMANAH"):
        predicted_bloc = "PN"
    elif ph >= 0.55:
        predicted_bloc = "PH"
    elif pas_mn >= 0.55 and party == "UMNO":
        predicted_bloc = "MN"
    elif bn >= 0.50:
        predicted_bloc = "BN"

    conf = "Tinggi" if km in ("safe", "semi_safe") else ("Sederhana" if km == "marginal" else "Rendah")

    if pas_base_adj >= 62:
        label = "PN/PAS fav"
    elif pas_base_adj >= 48:
        label = "PERTARUNGAN"
    elif pas_base_adj >= 32:
        label = "Perlu swing"
    else:
        label = "Bukan sasaran PAS"

    out = {
        "pasWinProb": pas_base_adj,
        "pasSoloWinProb": _clamp(pas_solo * 100),
        "pasMnWinProb": _clamp(pas_mn * 100),
        "bnSoloWinProb": _clamp(bn * 100),
        "phWinProb": _clamp(ph * 100),
        "scenarioPasSolo": _clamp(pas_solo * 100),
        "scenarioPasMn": _clamp(pas_mn * 100),
        "scenarioPasPn": _clamp(min(92.0, pas_base_adj + 6.0)),
        "pasSoloVsBn": edge,
        "pasSoloBnGapPct": gap,
        "modelConfidence": conf,
        "scenarioBase": scenario_base,
        "scenarioMeta": scenario_meta,
        "predictedBloc": predicted_bloc,
        "predictionLabel": label,
        "kategoriMargin": km,
        "modelContext": {
            "prn2022Baseline": True,
            "postMadaniAdjustment": POST_MADANI_CONTEXT,
            "sliderDefaults": {"madaniLevel": "sederhana", "phTrustLevel": "sederhana"},
            "methodology": (
                "UMNO 33 kerusi: senario solo PAS 55% vs UMNO 45% (±data). "
                "PAS/PN sandang: solo tinggi. PH: campuran 3–4 penjuru. "
                "MB = MN ≥29 + rundingan."
            ),
            **ctx,
        },
    }
    return apply_socmed_adjustment(out, socmed)
