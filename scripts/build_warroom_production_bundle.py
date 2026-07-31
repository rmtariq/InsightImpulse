#!/usr/bin/env python3
"""
Sync production PRN N9 data into War Room prototype (real dashboard mode).

Sources (same as prn-negeri-sembilan-dashboard.html):
  - reports/seats/n9_seats_export.json
  - reports/war_room/n9_war_room.json
  - reference/n9_dpi_updates.json
  - pas_break master crawl → socmed_by_dun_N9.json

Usage:
  python3 scripts/build_warroom_production_bundle.py
  python3 scripts/build_warroom_socmed_by_dun.py   # optional if crawl updated
"""
from __future__ import annotations

import csv
import json
import math
import re
import shutil
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from johor_seat_analytics import predict_johor_seat, compute_johor_mb_insight  # noqa: E402
from n9_seat_scenario_model import (  # noqa: E402
    compute_n9_mn_insight,
    predict_n9_seat_scenarios,
    rank_pas_solo_contest_27,
    select_pas_solo_lead_seats,
)
from prn_paths import reference, reports  # noqa: E402
from dun_headline_quality import build_display_headlines  # noqa: E402
from warroom_socmed_core import ISSUE_LEXICON  # noqa: E402
from n9_scoresheet_enrich import build_all_enrichment, summary_stats  # noqa: E402

PROTO_DATA = ROOT / "data/projects/political/PRN/PRN_N9/reports/war_room/prototype/data"
SEATS_EXPORT = reports("N9") / "seats/n9_seats_export.json"
WAR_ROOM_JSON = reports("N9") / "war_room/n9_war_room.json"
DPI_JSON = reference("N9") / "n9_dpi_updates.json"
GEO_MOCK = PROTO_DATA / "warroom_dun_N9.json"
OUT_BUNDLE = PROTO_DATA / "n9_production_bundle.json"
OUT_DUN = PROTO_DATA / "warroom_dun_N9_production.json"
OUT_DUN_JOHOR = PROTO_DATA / "warroom_dun_Johor_production.json"
OUT_BUNDLE_JOHOR = PROTO_DATA / "johor_production_bundle.json"
GEO_JOHOR = PROTO_DATA / "warroom_dun_Johor.json"
OUT_INTEL = PROTO_DATA / "war_room_intel_N9.json"
OUT_SOCIAL = PROTO_DATA / "n9_social_summary.json"
OUT_SOCIAL_JOHOR = PROTO_DATA / "johor_social_summary.json"
OUT_PAS_TARGET = PROTO_DATA / "pas_target_23_N9.json"
OUT_PAS_TARGET_16 = PROTO_DATA / "pas_target_16_N9.json"
OUT_SPR2023 = PROTO_DATA / "n9_spr2023_by_dun.json"
OUT_CULA_POLL = PROTO_DATA / "cula_poll_by_dun_N9.json"
OUT_CULA_SUMMARY = PROTO_DATA / "cula_poll_summary_N9.json"
SCORESHEET_STREAMS = reports("N9") / "seats/n9_scoresheet_streams_2023.json"
DOSM_CENSUS_JSON = PROTO_DATA / "dosm_census_johor_n9.json"

# 16 kerusi wajib PAS — input war room (mesti bertanding, tiada calon UMNO)
PAS_MUST_16 = {
    "N02", "N03", "N04", "N05", "N09", "N10", "N13", "N14",
    "N18", "N20", "N25", "N28", "N31", "N33", "N34", "N36",
}
# 7 kerusi imbang — hybrid score tertinggi selepas 16 wajib
PAS_BALANCE_7 = {"N06", "N07", "N15", "N16", "N17", "N19", "N35"}
PAS_23 = PAS_MUST_16 | PAS_BALANCE_7

MYT = timezone(timedelta(hours=8))

KATEGORI_STATUS = {
    "defend": "stronghold",
    "winnable": "battleground",
    "tough": "weak",
    "not_priority": "weak",
}

NS_PATTERN = re.compile(
    r"negeri sembilan|n\.?\s*sembilan|prn.*sembilan|sembilan.*prn|dun sembilan|prn n9|\bn9\b",
    re.I,
)
JOHOR_PATTERN = re.compile(
    r"\bjohor\b|prn\s*johor|prnnjohor|dun\s*johor|mb\s*johor|mbjb|sultan\s*johor",
    re.I,
)

# Diselaraskan dengan leksikon per-DUN (16 label) dari warroom_socmed_core —
# kotak "Isu Panas (Semua Platform)" papar top-6 daripada label sama.
_ISSUE_COLORS = [
    "var(--amber)", "var(--cyan)", "var(--primary)", "var(--purple)",
    "var(--red)", "var(--green)", "var(--muted)",
]
ISSUE_TAXONOMY = [
    (label, "|".join(rf"\b{re.escape(k)}\b" for k in kws), _ISSUE_COLORS[i % len(_ISSUE_COLORS)])
    for i, (label, kws) in enumerate(ISSUE_LEXICON.items())
]

# Jun 2026 PRN realignment: PAS↔Bersatu split; BN solo; MN / third-force paths
COALITION_COLORS = {
    "BN Solo (UMNO-led)": "var(--primary)",
    "PH (Madani)": "var(--red)",
    "PAS Solo": "var(--green)",
    "PAS + Gerakan (PN baru)": "#2dd4bf",
    "MN / PAS + BN": "var(--purple)",
    "Third Force (MUDA·PSM·BERSAMA)": "var(--cyan)",
    "Risiko tiada majoriti": "var(--amber)",
}

COALITION_CONTEXT_NOTE = (
    "Peluang majoriti = kebarangkalian capai ≥19/36 kerusi (bukan % undi rakyat). "
    "Model kerusi N9: pasWinProb + margin 2023 + DPI. Bukan polling SPR."
)

MAJORITY_N9 = 19
MAJORITY_JOHOR = 29
TOTAL_JOHOR = 56

COALITION_JOHOR_NOTE = (
    "Peluang majoriti = kebarangkalian capai ≥29/56 kerusi (bukan % undi rakyat). "
    "Model kerusi Johor: incumbent 2023 + socmed per DUN + penyesuaian crawl. Bukan polling SPR."
)


def _pas_p(seat: dict) -> float:
    return (seat.get("pasWinProb") or 0) / 100.0


def _majority_prob(expected: float, majority: int = MAJORITY_N9, scale: float = 3.0) -> int:
    """Map expected seats → P(≥ majority) via logistic curve centred at threshold."""
    x = expected - majority
    pct = 100.0 / (1.0 + math.exp(-x / scale))
    return int(round(max(2, min(97, pct))))


def _status_label(expected: float, majority: int = MAJORITY_N9) -> str:
    if expected >= majority + 1.5:
        return "kuat"
    if expected >= majority - 0.5:
        return "sederhana"
    if expected >= majority - 3:
        return "sukar"
    return "lemah"


def _expected_mn_seats(exports: list) -> float:
    """PAS+BN post-election pact: each seat contributes PAS win prob or BN hold prob."""
    total = 0.0
    for s in exports:
        p_pas = _pas_p(s)
        bloc = s.get("predictedBloc") or ""
        if bloc == "PH":
            total += p_pas
        elif bloc == "BN":
            total += min(1.0, p_pas + (1.0 - p_pas) * 0.92)
        elif bloc == "PN":
            total += min(1.0, max(p_pas, 0.60))
        else:
            total += p_pas * 0.35
    return round(total, 1)


def _expected_ph_seats(exports: list) -> float:
    total = 0.0
    for s in exports:
        p_pas = _pas_p(s)
        bloc = s.get("predictedBloc") or ""
        if bloc == "PH":
            total += min(1.0, 0.90 - p_pas * 0.38)
        elif bloc == "BN":
            total += max(0.0, (1.0 - p_pas) * 0.06)
    return round(total, 1)


def _expected_bn_solo_seats(exports: list) -> float:
    total = 0.0
    for s in exports:
        if s.get("predictedBloc") != "BN":
            continue
        total += (1.0 - _pas_p(s)) * 0.88
    return round(total, 1)


def _expected_pas_solo_seats(exports: list) -> float:
    return round(sum(_pas_p(s) for s in exports), 1)


def _expected_pas_gerakan_seats(exports: list) -> float:
    total = 0.0
    for s in exports:
        p_pas = _pas_p(s)
        pn = (s.get("scenarioPasPn") or 0) / 100.0
        if s.get("predictedBloc") == "PN":
            total += min(1.0, max(p_pas, pn * 0.88))
        elif pn >= 0.35:
            total += min(1.0, p_pas + pn * 0.25)
    return round(total, 1)


def _expected_third_force_seats(exports: list) -> float:
    total = 0.0
    for s in exports:
        risk = str(s.get("threeCornerRisk") or "").lower()
        if risk in ("tinggi", "high"):
            total += 0.35
        elif risk in ("sederhana", "medium"):
            total += 0.18
    return round(min(4.0, 1.2 + total), 1)


N9_PARTY_PATTERNS = {
    # Eksplisit + implisit sokongan PAS (tak perlu perkataan "solo")
    "pas": re.compile(
        r"\bpas\b|parti\s*islam|bulan\s*sabit|panah\s+pas|#panahpas|"
        r"suka\s+pas|pas\s+terbaik|all\s*out\s+pas|teguh\s+pas|gas\s+pas|"
        r"bulan\s+pas|islam\s+pas|undilah\s+pas|kita\s+pas",
        re.I,
    ),
    "bn": re.compile(r"\bumno\b|\bbn\b|barisan\s*nasional", re.I),
    "ph": re.compile(r"\bdap\b|\bpkr\b|\bph\b|pakatan\s*harapan|madani", re.I),
    "pn_legacy": re.compile(r"\bbersatu\b|\bpn\b|perikatan\s*nasional", re.I),
    "third": re.compile(r"\bmuda\b|\bpsm\b|blok\s*progresif|bersama", re.I),
    "mn": re.compile(r"\bmn\b|muafakat\s*nasional|pas.*umno|umno.*pas", re.I),
    "gerakan": re.compile(r"\bgerakan\b", re.I),
    "split": re.compile(r"pecah\s*undi|hung|tiada\s*majoriti|3\s*penjuru|three\s*corner", re.I),
}

# UMDAP = retorik anti-gabungan UMNO+DAP (Kerajaan Perpaduan) — bukan mention UMNO/DAP berasingan
N9_UMDAP_PATTERN = re.compile(
    r"umdap|umno\s*\+\s*dap|umno\s+dap|dap\s+umno|umno\s+dan\s+dap|"
    r"dap\s+dan\s+umno|m\s*&\s*d|madani\s+umno|umno\s+madani|"
    r"kerajaan\s+perpaduan.*(?:dap|umno)|(?:dap|umno).*kerajaan\s+perpaduan",
    re.I,
)

# Raguan PH/Madani: ekonomi, flip-flop PMX, kekecewaan pengundi (termasuk Cina terhadap DAP)
N9_PH_ANTI_PATTERN = re.compile(
    r"flip\s*flop|ekonomi\s*(?:lemah|gagal|buruk)|harga\s*(?:barang|naik|mahal)|"
    r"minyak\s*(?:naik|mahal)|inflasi|mahal\s*hidup|kecewa.*(?:dap|ph|madani|anwar)|"
    r"ragu.*(?:dap|ph|madani)|(?:dap|ph|madani|anwar).*(?:gagal|lemah|kecewa)|"
    r"pmx|gst|sst|kos\s*sara\s*hidup",
    re.I,
)

# Gen Z / Gen Y — pengundi muda tiada parti tetap, undi automatik (UND18 wave)
N9_YOUTH_WAVE_PATTERN = re.compile(
    r"gen\s*z|gen\s*y|anak\s*muda|pengundi\s*muda|undi\s*automatik|undi\s*18|"
    r"swing\s*voter|tiada\s*parti|first\s*time\s*voter|pengundi\s*baru|"
    r"generasi\s*(?:z|y|muda)|#undi18|#anakmuda|tunggu\s*(?:dan\s*)?lihat",
    re.I,
)

# Isu konkrit anak muda — kerjaya, sukan, kos hidup, calon viral (bukan sekadar label Gen Z)
N9_YOUTH_ISSUES_PATTERN = re.compile(
    r"kerjaya|pekerjaan|jawatan\s*kosong|pengangguran|graduan|"
    r"sukan|fasiliti\s*sukan|gelanggang|kompleks\s*sukan|padang|"
    r"komuter|bas\s*inter|laluan\s*bas|"
    r"rumah\s*(?:mampu\s*milik|murah|first\s*home|sewa)|"
    r"kos\s*sara\s*hidup|gaji\s*(?:minimum|rendah)|"
    r"wifi|internet|digital|startup|usahawan\s*muda|"
    r"calon\s*(?:muda|viral|influencer|baitulmal)|"
    r"IPT|universiti|politeknik|TVET",
    re.I,
)

# Krisis istana/adat N9 — Yam Tuan Besar, Undang Empat, Adat Perpatih
N9_ISTANA_UNDANG_PATTERN = re.compile(
    r"tuanku\s*muhriz|yang\s*di-?pertuan\s*besar|undang\s*yang\s*empat|"
    r"undang\s*(?:sungai\s*ujong|jelebu|johol|rembau)|tunku\s*besar(?:\s*(?:seri\s*menanti|tampin))?|"
    r"adat\s*perpatih|dewan\s*keadilan.*undang|institusi\s*(?:undang|diraja|adat)|"
    r"krisis\s*(?:perlembagaan|istana)|istana\s*(?:negeri\s*sembilan|n9)|"
    r"(?:undang\s*(?:ke-?5|kelima)|gelaran\s*undang|biar\s*hilang\s*jawatan)",
    re.I,
)

# Istana/adat + kerajaan negeri (PH MB + DAP/PKR + UMNO dalam kerajaan) — prestasi jatuh
N9_ISTANA_PH_BLAME_PATTERN = re.compile(
    r"menteri\s*besar|aminuddin|anthony\s*loke|"
    r"(?:dap|pkr|harapan|pakatan\s*harapan|madani).*(?:undang|adat|istana|muhriz|perpatih)|"
    r"(?:undang|adat|istana|perpatih).*(?:dap|pkr|harapan|aminuddin|menteri\s*besar|madani)|"
    r"umno.*(?:undang|adat|istana|perpatih|muhriz)|pegawai\s*(?:mb|menteri\s*besar)",
    re.I,
)


def _row_engagement(row: dict) -> float:
    for key in ("total_engagement", "engagement_score", "likes", "comments_count", "shares", "views"):
        val = row.get(key)
        if val in (None, ""):
            continue
        try:
            return float(val)
        except (TypeError, ValueError):
            continue
    return 0.0


def extract_coalition_crawl_signals(
    master_path: Path | None,
    socmed: dict | None,
    scope_pattern: re.Pattern | None = None,
) -> dict:
    """State social + news signals for coalition adjustment (mentions, sentiment, engagement)."""
    scope = scope_pattern or NS_PATTERN
    stats = {k: {"posts": 0, "engagement": 0.0, "pos": 0, "neg": 0, "neu": 0} for k in N9_PARTY_PATTERNS}
    umdap_stats = {"posts": 0, "engagement": 0.0, "pos": 0, "neg": 0, "neu": 0}
    ph_anti_stats = {"posts": 0, "engagement": 0.0, "pos": 0, "neg": 0, "neu": 0}
    youth_wave_stats = {"posts": 0, "engagement": 0.0, "pos": 0, "neg": 0, "neu": 0}
    youth_issues_stats = {"posts": 0, "engagement": 0.0, "pos": 0, "neg": 0, "neu": 0, "viralCandidate": 0}
    istana_stats = {"posts": 0, "engagement": 0.0, "pos": 0, "neg": 0, "neu": 0, "blamePosts": 0}
    pas_implicit_stats = {"posts": 0, "engagement": 0.0, "pos": 0, "neg": 0, "neu": 0}
    pas_implicit_re = re.compile(
        r"suka\s+pas|pas\s+terbaik|all\s*out\s+pas|teguh\s+pas|panah\s+pas|#panahpas|gas\s+pas|undilah\s+pas",
        re.I,
    )
    viral_cand_re = re.compile(r"calon\s*(?:muda|viral|influencer|baitulmal)|#calonmuda", re.I)
    split_posts = 0
    total_state = 0
    news_state = social_state = 0

    if master_path and master_path.exists():
        with master_path.open(encoding="utf-8", errors="replace") as f:
            for row in csv.DictReader(f):
                text = row.get("Text") or ""
                url = row.get("URL") or ""
                if not scope.search(f"{text} {url}"):
                    continue
                total_state += 1
                plat = (row.get("Platform") or "").lower()
                if plat == "news":
                    news_state += 1
                else:
                    social_state += 1
                sent = (row.get("Sentiment") or row.get("sentiment_label") or "neutral").lower()
                eng = _row_engagement(row)
                if N9_PARTY_PATTERNS["split"].search(text):
                    split_posts += 1
                if N9_UMDAP_PATTERN.search(text):
                    umdap_stats["posts"] += 1
                    umdap_stats["engagement"] += eng
                    if "neg" in sent:
                        umdap_stats["neg"] += 1
                    elif "pos" in sent:
                        umdap_stats["pos"] += 1
                    else:
                        umdap_stats["neu"] += 1
                if N9_PH_ANTI_PATTERN.search(text) and N9_PARTY_PATTERNS["ph"].search(text):
                    ph_anti_stats["posts"] += 1
                    ph_anti_stats["engagement"] += eng
                    if "neg" in sent:
                        ph_anti_stats["neg"] += 1
                    elif "pos" in sent:
                        ph_anti_stats["pos"] += 1
                    else:
                        ph_anti_stats["neu"] += 1
                if N9_YOUTH_WAVE_PATTERN.search(text):
                    youth_wave_stats["posts"] += 1
                    youth_wave_stats["engagement"] += eng
                    if "neg" in sent:
                        youth_wave_stats["neg"] += 1
                    elif "pos" in sent:
                        youth_wave_stats["pos"] += 1
                    else:
                        youth_wave_stats["neu"] += 1
                if N9_YOUTH_ISSUES_PATTERN.search(text):
                    youth_issues_stats["posts"] += 1
                    youth_issues_stats["engagement"] += eng
                    if viral_cand_re.search(text):
                        youth_issues_stats["viralCandidate"] += 1
                    if "neg" in sent:
                        youth_issues_stats["neg"] += 1
                    elif "pos" in sent:
                        youth_issues_stats["pos"] += 1
                    else:
                        youth_issues_stats["neu"] += 1
                if N9_ISTANA_UNDANG_PATTERN.search(text):
                    istana_stats["posts"] += 1
                    istana_stats["engagement"] += eng
                    if N9_ISTANA_PH_BLAME_PATTERN.search(text):
                        istana_stats["blamePosts"] += 1
                    if "neg" in sent:
                        istana_stats["neg"] += 1
                    elif "pos" in sent:
                        istana_stats["pos"] += 1
                    else:
                        istana_stats["neu"] += 1
                if pas_implicit_re.search(text):
                    pas_implicit_stats["posts"] += 1
                    pas_implicit_stats["engagement"] += eng
                    if "neg" in sent:
                        pas_implicit_stats["neg"] += 1
                    elif "pos" in sent:
                        pas_implicit_stats["pos"] += 1
                    else:
                        pas_implicit_stats["neu"] += 1
                for key, pat in N9_PARTY_PATTERNS.items():
                    if key == "split":
                        continue
                    if pat.search(text):
                        bucket = stats[key]
                        bucket["posts"] += 1
                        bucket["engagement"] += eng
                        if "neg" in sent:
                            bucket["neg"] += 1
                        elif "pos" in sent:
                            bucket["pos"] += 1
                        else:
                            bucket["neu"] += 1

    soc_mentions = soc_eng = soc_neg_w = 0.0
    for dun in ((socmed or {}).get("byDun") or {}).values():
        t = dun.get("mentions_total") or 0
        if not t:
            continue
        soc_mentions += t
        soc_eng += dun.get("engagement_total") or 0
        soc_neg_w += t * (dun.get("neg_pct") or 0) / 100

    return {
        "totalStatePosts": total_state,
        "totalN9Posts": total_state,
        "newsPosts": news_state,
        "socialPosts": social_state,
        "splitMentionPosts": split_posts,
        "party": stats,
        "pasImplicit": pas_implicit_stats,
        "umdapAntiMd": umdap_stats,
        "phEconomicAngst": ph_anti_stats,
        "youthGenZWave": youth_wave_stats,
        "youthIssuesConcrete": youth_issues_stats,
        "n9IstanaAdat": istana_stats,
        "socmedDunMentions": int(soc_mentions),
        "socmedDunEngagement": int(soc_eng),
        "socmedWeightedNegPct": round(soc_neg_w / soc_mentions * 100, 1) if soc_mentions else None,
    }


def compute_state_demographic_hybrid(
    exports: list,
    socmed: dict | None,
    dpi_data: dict | None = None,
) -> dict:
    """
    Weighted SPR DPI (pengundi) vs socmed narrative proxy (mentions per DUN).
    Drives ±nudge on coalition / 7-bloc majority probabilities.
    """
    dpi_by = (dpi_data or {}).get("byCode") or {}
    by_dun = (socmed or {}).get("byDun") or {}
    rollup_demo = (socmed or {}).get("rollup") or {}

    total_voters = 0
    w_dpi = {"malay": 0.0, "chinese": 0.0, "indian": 0.0}
    for ex in exports or []:
        code = norm_code(ex.get("code"))
        dpi = dpi_by.get(code) or ex.get("dpi") or {}
        voters = int(dpi.get("registeredVotersDpi") or ex.get("registeredVoters") or 0)
        if voters <= 0:
            continue
        total_voters += voters
        w_dpi["malay"] += voters * float(dpi.get("pctMelayu") or ex.get("pctMelayu") or 0)
        w_dpi["chinese"] += voters * float(dpi.get("pctCina") or ex.get("pctCina") or 0)
        w_dpi["indian"] += voters * float(dpi.get("pctIndia") or ex.get("pctIndia") or 0)

    dpi_pct = (
        {k: round(v / total_voters, 1) for k, v in w_dpi.items()}
        if total_voters
        else {"malay": 61.2, "chinese": 21.9, "indian": 14.3}
    )

    total_m = sum(int(d.get("mentions_total") or 0) for d in by_dun.values())
    w_soc = {"malay": 0.0, "urban": 0.0, "chinese": 0.0, "indian": 0.0, "unknown": 0.0}
    raw_state = rollup_demo.get("state_demo") or {}
    if raw_state and (rollup_demo.get("mentions_total_state") or socmed.get("meta", {}).get("state_rows_scanned")):
        soc_pct = {
            "malay": float(raw_state.get("malay") or 0),
            "urban": float(raw_state.get("urban") or 0),
            "chinese": float(raw_state.get("chinese") or 0),
            "indian": float(raw_state.get("indian") or 0),
            "unknown": float(raw_state.get("unknown") or 0),
        }
        total_m = int(rollup_demo.get("mentions_total_state") or socmed.get("meta", {}).get("state_rows_scanned") or 0)
    elif total_m:
        for d in by_dun.values():
            m = int(d.get("mentions_total") or 0)
            if not m:
                continue
            mix = d.get("demo_mix") or {}
            for k in w_soc:
                w_soc[k] += m * float(mix.get(k) or 0)
        soc_pct = {k: round(v / total_m, 1) for k, v in w_soc.items()}
    else:
        soc_pct = {"malay": 0, "urban": 0, "chinese": 0, "indian": 0, "unknown": 0}

    delta_malay = round(soc_pct.get("malay", 0) - dpi_pct.get("malay", 0), 1)
    delta_chinese = round(soc_pct.get("chinese", 0) - dpi_pct.get("chinese", 0), 1)
    delta_urban = round(soc_pct.get("urban", 0), 1)
    dun_mentions = sum(int(d.get("mentions_total") or 0) for d in by_dun.values())

    bloc7: dict[str, int] = {}
    legacy: dict[str, int] = {}
    notes: list[str] = []

    def nudge(bloc_id: str, legacy_name: str, mp: int, reason: str) -> None:
        bloc7[bloc_id] = bloc7.get(bloc_id, 0) + mp
        legacy[legacy_name] = legacy.get(legacy_name, 0) + mp
        notes.append(f"{reason} ({mp:+d}%)")

    if delta_malay >= 10:
        nudge("pas_solo", "PAS Solo", 3, f"Naratif Melayu +{delta_malay}pp vs DPI")
        nudge("mn", "MN (PAS+BN)", 3, "Skew Melayu → MN")
        nudge("pn", "PAS + Gerakan (PN baru)", 2, "Skew Melayu → PN")
        nudge("pn_plus", "PN + Bersatu (bloc penuh)", 2, "Skew Melayu → PN+")
        nudge("umno_solo", "BN Solo (UMNO-led)", 1, "Ground Melayu kuat")
        nudge("ph", "PH (Madani)", -3, "Urban/PH relatif lemah bila naratif Melayu dominan")
    elif delta_malay >= 5:
        nudge("pas_solo", "PAS Solo", 2, f"Naratif Melayu +{delta_malay}pp vs DPI")
        nudge("mn", "MN (PAS+BN)", 2, "Skew Melayu → MN")
        nudge("pn", "PAS + Gerakan (PN baru)", 1, "Skew Melayu → PN")
        nudge("pn_plus", "PN + Bersatu (bloc penuh)", 1, "Skew Melayu → PN+")
        nudge("ph", "PH (Madani)", -2, "PH relatif lemah vs naratif Melayu")

    if delta_chinese >= 4:
        nudge("ph", "PH (Madani)", 2, f"Naratif Cina +{delta_chinese}pp vs DPI")
        nudge("pas_solo", "PAS Solo", -1, "Kerosak bandar/Cina → kurang PAS solo")
    elif delta_chinese <= -3 and dpi_pct.get("chinese", 0) >= 20:
        nudge("pas_solo", "PAS Solo", 1, "Kurang suara Cina dalam socmed vs profil DUN bandar")

    if delta_urban >= 25 and delta_malay < 5:
        nudge("ph", "PH (Madani)", 2, f"Naratif bandar {delta_urban}% — PH/DAP proxy")
        nudge("pas_solo", "PAS Solo", -2, "Digital urban skew — PAS solo lemah")

    # Dampen nudges bila sample socmed per-DUN tipis
    conf = 1.0
    if dun_mentions < 80:
        conf = 0.35
    elif dun_mentions < 200:
        conf = 0.55
    elif dun_mentions < 400:
        conf = 0.75
    if conf < 1.0:
        for k in list(bloc7.keys()):
            bloc7[k] = int(round(bloc7[k] * conf)) if bloc7[k] else 0
        for k in list(legacy.keys()):
            legacy[k] = int(round(legacy[k] * conf)) if legacy[k] else 0
        notes.append(f"Keyakinan demografi rendah ({dun_mentions} mention per-DUN) — nudge ×{conf:.0%}")

    if not notes:
        notes.append("Profil naratif socmed selari dengan DPI negeri (±5pp Melayu)")

    insight = (
        f"Melayu DPI {dpi_pct.get('malay')}% vs socmed {soc_pct.get('malay')}% "
        f"({delta_malay:+.1f}pp) · bandar/campuran {soc_pct.get('urban', 0)}%"
    )

    return {
        "dpi": dpi_pct,
        "socmed": soc_pct,
        "delta": {"malay": delta_malay, "chinese": delta_chinese, "urban": delta_urban},
        "bloc7Nudges": bloc7,
        "legacyNudges": legacy,
        "adjustmentNotes": notes,
        "insight": insight,
        "mentionsWeighted": total_m,
        "dunMentionsWeighted": dun_mentions,
        "confidenceScale": conf,
        "votersTotal": total_voters,
        "disclaimer": "DPI = pengundi berdaftar SPR · socmed = proxy bahasa post (bukan etnik sebenar)",
    }


def _apply_demographic_adjustments(scenarios: list, demo: dict | None) -> list[str]:
    """Nudge legacy coalition scenarios from DPI vs socmed skew (max ±3% stacked per bloc)."""
    if not demo or not demo.get("legacyNudges"):
        return []
    by_name = {s["name"]: s for s in scenarios}
    notes: list[str] = []
    for name, delta in demo["legacyNudges"].items():
        s = by_name.get(name)
        if not s or not delta:
            continue
        s["majorityPct"] = int(round(max(2, min(97, s["majorityPct"] + delta))))
        if s.get("expectedSeats") is not None and abs(delta) >= 2:
            s["expectedSeats"] = round(s["expectedSeats"] + delta * 0.08, 1)
            s["status"] = _status_label(s["expectedSeats"])
    notes.extend(demo.get("adjustmentNotes") or [])
    return notes


def _apply_crawl_adjustments(scenarios: list, signals: dict) -> tuple[list, list[str]]:
    """Light-touch nudge to majorityPct + expectedSeats from crawl/sentiment (max ±5% each)."""
    if not signals or not (signals.get("totalStatePosts") or signals.get("totalN9Posts")):
        return scenarios, []

    by_name = {s["name"]: s for s in scenarios}
    notes: list[str] = []
    party = signals.get("party") or {}

    def bump(name: str, mp_delta: int = 0, seat_delta: float = 0, reason: str = "") -> None:
        s = by_name.get(name)
        if not s:
            return
        s["majorityPct"] = int(round(max(2, min(97, s["majorityPct"] + mp_delta))))
        if seat_delta and s.get("expectedSeats") is not None:
            s["expectedSeats"] = round(s["expectedSeats"] + seat_delta, 1)
            s["status"] = _status_label(s["expectedSeats"])
        if reason:
            notes.append(f"{name}: {reason} ({mp_delta:+d}%)")

    bn = party.get("bn") or {}
    ph = party.get("ph") or {}
    pas = party.get("pas") or {}
    pas_implicit = signals.get("pasImplicit") or {}
    umdap = signals.get("umdapAntiMd") or {}
    ph_anti = signals.get("phEconomicAngst") or {}
    youth = signals.get("youthGenZWave") or {}
    youth_issues = signals.get("youthIssuesConcrete") or {}
    istana = signals.get("n9IstanaAdat") or {}
    third = party.get("third") or {}
    mn = party.get("mn") or {}

    # Krisis istana/adat — MB PH (PKR) + DAP + UMNO dalam kerajaan negeri terpalit
    istana_fired = False
    if istana.get("posts", 0) >= 2:
        ist_neg = istana["neg"] / istana["posts"]
        blame = istana.get("blamePosts", 0)
        if blame >= 2 or ist_neg >= 0.35 or istana["neg"] >= istana["pos"]:
            istana_fired = True
            bump("PH (Madani)", -5, -0.5, "Isu istana/adat — MB PH + DAP terpalit")
            bump("BN Solo (UMNO-led)", -4, -0.3, "UMNO dalam kerajaan negeri N9 — istana/adat")
            bump("MN (PAS+BN)", +5, 0.5, "Istana/adat → laluan MN (Melayu rural/adat)")
            bump("PAS Solo", +4, 0.4, "Krisis adat — PAS pembangkang + segmen Melayu-Islam")
            notes.append("Risiko tiada majoriti: isu istana/adat — UMNO kerajaan vs pembangkang (+3%)")

    # UMDAP / anti-UMNO+DAP → pro-PAS/MN dalam kalangan Melayu-Islam (bukan pro-PH)
    if umdap.get("posts", 0) >= 2:
        bump("PAS Solo", +3, 0.3, "Retorik UMDAP/anti-UMNO+DAP (crawl)")
        bump("MN (PAS+BN)", +2, 0.1, "UMDAP → laluan PAS/MN")
        bump("PH (Madani)", -3, -0.2, "UMDAP = tolak narrative PH+UMNO")
        bump("BN Solo (UMNO-led)", -2, -0.1, "UMDAP stigma UMNO+DAP")

    # Raguan PH: ekonomi, flip-flop, kekecewaan DAP/PMX (termasuk pengundi Cina)
    if ph_anti.get("posts", 0) >= 3:
        anti_neg = ph_anti["neg"] / ph_anti["posts"]
        if anti_neg >= 0.35 or ph_anti["neg"] >= ph_anti["pos"]:
            bump("PH (Madani)", -4, -0.4, "Raguan PH/Madani (ekonomi/flip-flop/DAP)")
            bump("PAS Solo", +1, 0.1, "PH lemah → ruang PAS")
            bump("MN (PAS+BN)", +1, 0.1, "PH lemah → MN relatif")

    # Sokongan implisit: "saya suka pas", "pas terbaik" — tanpa perkataan solo
    if pas_implicit.get("posts", 0) >= 2:
        impl_pos = pas_implicit["pos"] / pas_implicit["posts"]
        if impl_pos >= 0.4:
            bump("PAS Solo", +3, 0.3, "Sokongan implisit PAS positif (suka pas/pas terbaik)")
            bump("MN (PAS+BN)", +1, 0.1, "Afiniti PAS implisit")
        elif pas_implicit["neg"] / pas_implicit["posts"] >= 0.4:
            bump("PAS Solo", -1, 0, "Sokongan implisit PAS negatif")

    if bn.get("posts", 0) >= 5:
        bn_neg_rate = bn["neg"] / bn["posts"]
        if bn_neg_rate >= 0.45:
            bump("MN (PAS+BN)", +4, 0.3, "BN/UMNO sentiment negatif tinggi (crawl N9)")
            bump("BN Solo (UMNO-led)", -3, -0.2, "BN coverage negatif")

    if ph.get("posts", 0) >= 5:
        ph_neg_rate = ph["neg"] / ph["posts"]
        ph_pos_rate = ph["pos"] / ph["posts"]
        if ph_neg_rate >= 0.40 or ph_neg_rate > ph_pos_rate:
            bump("PH (Madani)", -3, -0.3, "PH sentiment negatif > positif (crawl N9)")
            bump("PAS Solo", +1, 0.1, "Sentimen anti-PH → laluan PAS")
        elif ph.get("engagement", 0) > bn.get("engagement", 0) and ph_pos_rate >= 0.35:
            bump("PH (Madani)", +2, 0.2, "PH engagement + sentiment positif")

    if pas.get("posts", 0) >= 3 or pas_implicit.get("posts", 0) >= 2:
        combined = pas.get("posts", 0) + pas_implicit.get("posts", 0)
        combined_neg = pas.get("neg", 0) + pas_implicit.get("neg", 0)
        combined_pos = pas.get("pos", 0) + pas_implicit.get("pos", 0)
        pas_neg_rate = combined_neg / max(1, combined)
        pas_pos_rate = combined_pos / max(1, combined)
        if pas_neg_rate >= 0.45 and not pas_implicit.get("posts"):
            bump("PAS Solo", -2, -0.2, "PAS mention eksplisit negatif (bukan sokongan implisit)")
        elif pas_pos_rate >= 0.35 or pas.get("engagement", 0) > 500:
            bump("PAS Solo", +2, 0.2, "Afiniti PAS positif dalam crawl")

    # Gen Z/Gen Y tiada parti tetap — swing + Third Force + risiko hung (hung adjusted later)
    if youth.get("posts", 0) >= 5:
        youth_neg = youth["neg"] / youth["posts"]
        if youth_neg >= 0.40:
            bump("PH (Madani)", -2, -0.2, "Gen Z/Gen Y sentiment anti-establishment")
            bump("Third Force (MUDA·PSM·BERSAMA)", +2, 0.2, "Anak muda tiada parti — MUDA/PSM")
        notes.append("Risiko tiada majoriti: Gen Z tunggu & lihat (+3%)")

    # Isu konkrit anak muda — calon viral + jawapan kerjaya/sukan → siapa capai, dia menang segmen
    if youth_issues.get("posts", 0) >= 3:
        viral_n = youth_issues.get("viralCandidate", 0)
        yi_neg = youth_issues["neg"] / youth_issues["posts"]
        if viral_n >= 1 and (pas_implicit.get("posts", 0) >= 1 or pas.get("posts", 0) >= 2):
            bump("PAS Solo", +3, 0.3, "Calon muda PAS viral + isu kerjaya/sukan")
            bump("MN (PAS+BN)", +2, 0.2, "Anak muda Melayu — calon PAS/UMNO menonjol")
        elif yi_neg >= 0.40:
            bump("PH (Madani)", -2, -0.2, "Anak muda kecewa isu kerjaya/sukan/kos hidup")
            bump("PAS Solo", +2, 0.2, "Kos hidup/kerjaya — ruang PAS (Melayu muda)")
        notes.append(
            f"Youth issues: {youth_issues['posts']} post (kerjaya/sukan/komuter) · "
            f"{'calon viral dikesan' if viral_n else 'tunggu calon — belum lock parti'}"
        )

    if third.get("posts", 0) >= 8:
        third_pos = third["pos"] / third["posts"]
        if third_pos >= 0.35:
            bump("Third Force (MUDA·PSM·BERSAMA)", +3, 0.4, "MUDA/PSM sentiment positif")

    if mn.get("posts", 0) >= 2:
        bump("MN (PAS+BN)", +2, 0.1, "MN/muafakat disebut dalam crawl")

    if (party.get("pn_legacy") or {}).get("posts", 0) >= 10:
        bump("PAS + Gerakan (PN baru)", +2, 0.2, "PN/Bersatu masih dominan dalam perbincangan")

    # Gelombang Melayu-Islam/Bumiputera — isu berlapis (istana + UMDAP + anti-PH + UMNO negatif)
    stack = 0
    if istana_fired:
        stack += 1
    if umdap.get("posts", 0) >= 2:
        stack += 1
    if ph_anti.get("posts", 0) >= 3:
        anti_neg = ph_anti["neg"] / ph_anti["posts"]
        if anti_neg >= 0.35 or ph_anti["neg"] >= ph_anti["pos"]:
            stack += 1
    if bn.get("posts", 0) >= 5 and bn["neg"] / bn["posts"] >= 0.45:
        stack += 1
    if stack >= 2:
        bump("PAS Solo", +5, 0.5, "Gelombang Melayu-Islam/Bumiputera — isu berlapis")
        bump("MN (PAS+BN)", +4, 0.4, "Afiniti MN segmen Melayu rural + adat + UMDAP")
        bump("PH (Madani)", -3, -0.3, "PH lemah dalam segmen Melayu-Islam")
        notes.append(f"Melayu-Islam stack: {stack}/4 isyarat aktif (istana/UMDAP/anti-PH/BN negatif)")

    return list(by_name.values()), notes


def _build_coalition_by_dun(exports: list) -> list:
    """Per-DUN: pasWinProb, bloc 2023, laluan MN vs PAS solo vs PH hold."""
    rows = []
    for s in exports:
        p = _pas_p(s)
        bloc = s.get("predictedBloc") or "?"
        if bloc == "PH":
            mn_contrib = p
            ph_hold = min(1.0, 0.90 - p * 0.38)
        elif bloc == "BN":
            mn_contrib = min(1.0, p + (1.0 - p) * 0.92)
            ph_hold = max(0.0, (1.0 - p) * 0.06)
        elif bloc == "PN":
            mn_contrib = min(1.0, max(p, 0.60))
            ph_hold = 0.0
        else:
            mn_contrib = p * 0.35
            ph_hold = 0.0
        if p >= 0.50:
            lean = "PAS fav"
        elif p >= 0.35:
            lean = "contested"
        else:
            lean = bloc
        rows.append(
            {
                "code": s.get("code"),
                "name": s.get("name"),
                "predictedBloc2023": bloc,
                "party2022": s.get("party2022") or s.get("party2023"),
                "pasWinProb": s.get("pasWinProb"),
                "pasSoloWinProb": s.get("pasSoloWinProb"),
                "pasMnWinProb": s.get("pasMnWinProb"),
                "bnSoloWinProb": s.get("bnSoloWinProb"),
                "phWinProb": s.get("phWinProb"),
                "pasSoloExpected": round(p, 3),
                "mnContrib": round(mn_contrib, 3),
                "phHoldProb": round(ph_hold, 3),
                "bnSoloExpected": round((s.get("bnSoloWinProb") or 0) / 100.0, 3),
                "lean": lean,
            }
        )
    rows.sort(key=lambda r: (-(r["pasWinProb"] or 0), r["code"] or ""))
    return rows


def _hung_majority_prob(main_scenarios: list, signals: dict | None, majority: int = MAJORITY_N9) -> int:
    """
    P(no bloc reaches majority comfortably).
    Higher when top coalition is borderline (~majority seats, ~50% majority prob).
    """
    max_exp = max(s["expectedSeats"] for s in main_scenarios)
    top_mp = max(s["majorityPct"] for s in main_scenarios)
    second_mp = sorted((s["majorityPct"] for s in main_scenarios), reverse=True)[1]
    margin = top_mp - second_mp

    low = majority - 1
    high = majority + 1.5
    if low <= max_exp <= high:
        hung = 26 + (high - max_exp) * 5 + max(0, 52 - top_mp) * 0.25
    elif max_exp < low:
        hung = 36 + (low - max_exp) * 5
    else:
        hung = max(10, 20 - (max_exp - high) * 6)

    split_n = (signals or {}).get("splitMentionPosts") or 0
    hung += min(10, split_n * 2)
    youth_n = ((signals or {}).get("youthGenZWave") or {}).get("posts") or 0
    if youth_n >= 5:
        hung += min(8, 2 + youth_n // 3)
    if margin < 12:
        hung += 6

    return int(round(max(10, min(42, hung))))


def compute_coalition_formation(
    exports: list,
    master_path: Path | None = None,
    socmed: dict | None = None,
    demo_hybrid: dict | None = None,
    *,
    majority: int = MAJORITY_N9,
    scope_pattern: re.Pattern | None = None,
    state_label: str = "N9",
    disclaimer: str | None = None,
) -> dict:
    """
    Government-formation model (Jun 2026).

    Output: expected seats per scenario + peluang majoriti (≥majority seats).
    Each seat contributes win probability; coalition totals are summed
    (MN counts PAS-held + BN-held seats under post-election pact assumption).
    """
    n = len(exports) or (TOTAL_JOHOR if state_label == "Johor" else 36)

    defs = [
        (
            "MN (PAS+BN)",
            _expected_mn_seats(exports),
            COALITION_COLORS["MN / PAS + BN"],
            "PAS & BN/UMNO berunding selepas undi",
        ),
        (
            "PH (Madani)",
            _expected_ph_seats(exports),
            COALITION_COLORS["PH (Madani)"],
            "DAP/PKR/Amanah kekal di kerusi bandar",
        ),
        (
            "BN Solo (UMNO-led)",
            _expected_bn_solo_seats(exports),
            COALITION_COLORS["BN Solo (UMNO-led)"],
            "BN/UMNO tanpa gabungan PH",
        ),
        (
            "PAS Solo",
            _expected_pas_solo_seats(exports),
            COALITION_COLORS["PAS Solo"],
            f"PAS capai {majority}+ kerusi (bukan keyword 'solo' dalam socmed)",
        ),
        (
            "PAS + Gerakan (PN baru)",
            _expected_pas_gerakan_seats(exports),
            COALITION_COLORS["PAS + Gerakan (PN baru)"],
            "PAS + Gerakan/rakan (tanpa Bersatu)",
        ),
        (
            "Third Force (MUDA·PSM·BERSAMA)",
            _expected_third_force_seats(exports),
            COALITION_COLORS["Third Force (MUDA·PSM·BERSAMA)"],
            "Blok progresif / parti kecil",
        ),
    ]

    scenarios = []
    for name, expected, color, assumption in defs:
        mp = _majority_prob(expected, majority)
        scenarios.append(
            {
                "name": name,
                "expectedSeats": expected,
                "majorityThreshold": majority,
                "totalSeats": n,
                "majorityPct": mp,
                "status": _status_label(expected, majority),
                "assumption": assumption,
                "color": color,
            }
        )

    crawl_signals = extract_coalition_crawl_signals(master_path, socmed, scope_pattern)
    scenarios, crawl_notes = _apply_crawl_adjustments(scenarios, crawl_signals)
    demo_notes = _apply_demographic_adjustments(scenarios, demo_hybrid)
    crawl_notes.extend(demo_notes)

    hung_mp = _hung_majority_prob(scenarios, crawl_signals, majority)
    scenarios.append(
        {
            "name": "Risiko tiada majoriti",
            "expectedSeats": None,
            "seatLabel": f"tiada bloc ≥{majority}",
            "majorityThreshold": majority,
            "totalSeats": n,
            "majorityPct": hung_mp,
            "status": "sederhana" if hung_mp >= 22 else "lemah",
            "assumption": (
                f"Tiada bloc capai {majority} kerusi dengan selesa · perlu rundingan selepas undi"
            ),
            "color": COALITION_COLORS["Risiko tiada majoriti"],
        }
    )

    scenarios.sort(key=lambda x: (-x["majorityPct"], -(x["expectedSeats"] or 0)))

    coalition_bars = [
        {
            "name": s["name"],
            "pct": s["majorityPct"],
            "color": s["color"],
            "expectedSeats": s.get("expectedSeats"),
            "seatLabel": s.get("seatLabel"),
            "status": s["status"],
            "assumption": s.get("assumption", ""),
        }
        for s in scenarios
    ]

    by_dun = _build_coalition_by_dun(exports)
    data_quality = {
        "statePostsInMaster": crawl_signals.get("totalStatePosts") or crawl_signals.get("totalN9Posts") or 0,
        "n9PostsInMaster": crawl_signals.get("totalN9Posts") or 0,
        "pasExplicitPosts": (crawl_signals.get("party") or {}).get("pas", {}).get("posts", 0),
        "pasImplicitPosts": (crawl_signals.get("pasImplicit") or {}).get("posts", 0),
        "umdapPosts": (crawl_signals.get("umdapAntiMd") or {}).get("posts", 0),
        "phAntiThemePosts": (crawl_signals.get("phEconomicAngst") or {}).get("posts", 0),
        "youthGenZPosts": (crawl_signals.get("youthGenZWave") or {}).get("posts", 0),
        "youthIssuesPosts": (crawl_signals.get("youthIssuesConcrete") or {}).get("posts", 0),
        "istanaAdatPosts": (crawl_signals.get("n9IstanaAdat") or {}).get("posts", 0),
        "istanaAdatBlamePosts": (crawl_signals.get("n9IstanaAdat") or {}).get("blamePosts", 0),
        "dunsWithSocmedMention": sum(
            1 for d in ((socmed or {}).get("byDun") or {}).values() if (d.get("mentions_total") or 0) > 0
        ),
        "note": (
            "PAS Solo = Σ pasWinProb (~10/36 kerusi) + penyesuaian crawl. "
            "Bukan polling — naik % majoriti ≠ 19 kerusi solo. "
            "Gelombang Melayu-Islam (istana+UMDAP) naik PAS/MN apabila isyarat berlapis. "
            "Anak muda: tunggu & lihat — undi ikut calon viral + isu kerjaya/sukan."
        ),
    }

    return {
        "majorityThreshold": majority,
        "totalSeats": n,
        "methodology": (
            "Kerusi dijangka = Σ kebarangkalian menang/DUN (pasWinProb + predictedBloc). "
            f"Peluang majoriti = logistik centred {majority} kerusi. "
            f"Risiko tiada majoriti = kebarangkalian tiada bloc capai {majority} kerusi dengan selesa. "
            f"Penyesuaian crawl: sentiment + engagement {state_label} dari master socmed/news (±5%)."
        ),
        "disclaimer": disclaimer or (
            COALITION_JOHOR_NOTE if state_label == "Johor" else COALITION_CONTEXT_NOTE
        ),
        "crawlSignals": crawl_signals,
        "crawlAdjustments": crawl_notes,
        "demographicHybrid": demo_hybrid or {},
        "dataQuality": data_quality,
        "byDun": by_dun,
        "scenarios": scenarios,
        "coalition": coalition_bars,
    }

MASTER_DIR = ROOT / "data/projects/political/pas_break_2026/master"
COMBINED_DIR = ROOT / "data/combined"


def norm_code(code: str) -> str:
    if not code:
        return ""
    s = str(code).strip().upper().replace(" ", "")
    m = re.match(r"N\.?0*(\d+)", s)
    return f"N{int(m.group(1)):02d}" if m else s


def load_json(path: Path, default=None):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def geo_index(geo_list: list) -> dict:
    out = {}
    for g in geo_list or []:
        c = norm_code(g.get("id") or g.get("code") or "")
        if c:
            out[c] = g
    return out


def find_master() -> Path | None:
    """Prefer latest analyzed EXCO master (full labels); fallback hybrid combined."""
    analyzed = sorted(
        MASTER_DIR.glob("PAS_Break_Master_EXCO_Analyzed_*.csv"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if analyzed:
        return analyzed[0]
    combined = sorted(
        COMBINED_DIR.glob("PRN_Johor_N9_master_*.csv"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return combined[0] if combined else None


def compute_master_analytics(master_path: Path | None) -> dict:
    """Jumlah post + engagement dari master crawl (semua + N9 + hybrid layers)."""
    empty = {
        "totalPosts": 0,
        "totalEngagement": 0,
        "totalDataPoints": 0,
        "nsPosts": 0,
        "nsEngagement": 0,
        "johorPosts": 0,
        "johorEngagement": 0,
        "prnScopedPosts": 0,
        "byPlatform": {},
        "byBatch": {},
        "byLayer": {},
        "masterFile": None,
        "hybridModel": {
            "layers": [
                "Arkib PAS Break (Jun 12)",
                "PRN master + Batch 1–7",
                "DPI / MyCensus per DUN",
                "pasWinProb + margin 2023",
                "Socmed by DUN + sentiment crawl",
            ],
            "note": "Lebih banyak data point → coverage isu/coalition lebih kukuh; dedupe Platform+ID keep=last.",
        },
    }
    if not master_path or not master_path.exists():
        return empty

    johor_re = re.compile(r"\bjohor\b|prn\s*johor|prnnjohor|dun\s*johor", re.I)
    total = ns = jh = 0
    eng_total = eng_ns = eng_jh = 0.0
    by_plat: dict[str, int] = {}
    by_batch: dict[str, int] = {}
    by_layer: dict[str, int] = {}

    with master_path.open(encoding="utf-8", errors="replace") as f:
        for row in csv.DictReader(f):
            total += 1
            text = row.get("Text") or ""
            url = row.get("URL") or ""
            blob = f"{text} {url}"
            eng = _row_engagement(row)
            eng_total += eng
            plat = (row.get("Platform") or "unknown").lower()
            by_plat[plat] = by_plat.get(plat, 0) + 1
            batch = row.get("crawl_batch") or row.get("crawl_source_file") or "legacy"
            by_batch[batch] = by_batch.get(batch, 0) + 1
            layer = batch.split("_")[0] if batch.startswith("archive") else (
                "prn_recent" if batch.startswith(("prn_", "Batch7", "master")) else "other"
            )
            by_layer[layer] = by_layer.get(layer, 0) + 1
            is_ns = bool(NS_PATTERN.search(blob))
            is_jh = bool(johor_re.search(blob))
            if is_ns:
                ns += 1
                eng_ns += eng
            elif is_jh:
                jh += 1
                eng_jh += eng

    prn_scoped = ns + jh

    return {
        "totalPosts": total,
        "totalDataPoints": total,
        "totalEngagement": int(round(eng_total)),
        "nsPosts": ns,
        "nsEngagement": int(round(eng_ns)),
        "johorPosts": jh,
        "johorEngagement": int(round(eng_jh)),
        "prnScopedPosts": prn_scoped,
        "byPlatform": dict(sorted(by_plat.items(), key=lambda x: -x[1])),
        "byBatch": dict(sorted(by_batch.items(), key=lambda x: -x[1])),
        "byLayer": dict(sorted(by_layer.items(), key=lambda x: -x[1])),
        "masterFile": master_path.name,
        "hybridModel": empty["hybridModel"],
    }


def parse_crawl_date(raw: str) -> datetime | None:
    if not raw or not str(raw).strip():
        return None
    s = str(raw).strip()
    if s.isdigit():
        try:
            return datetime.fromtimestamp(int(s), tz=timezone.utc)
        except (ValueError, OSError):
            return None
    try:
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt
    except ValueError:
        return None


def extract_issue_heatmap(
    master_path: Path | None,
    socmed: dict | None,
    scope_pattern: re.Pattern | None = None,
    seats_fallback: list | None = None,
) -> dict:
    """Top issues from crawl text (24h window) + seat isuUtama fallback."""
    scope = scope_pattern or NS_PATTERN
    window_note = (socmed or {}).get("meta", {}).get("window_24h_note") or "24j crawl window"
    fallback_fn = lambda: _issues_from_seats_only(seats_fallback)
    if not master_path or not master_path.exists():
        return {"windowNote": window_note, "top": fallback_fn()}

    rows_24h: list[str] = []
    max_dt: datetime | None = None
    with master_path.open(encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            text = row.get("Text") or ""
            url = row.get("URL") or ""
            if not scope.search(f"{text} {url}"):
                continue
            dt = parse_crawl_date(row.get("Date") or "")
            if dt and (max_dt is None or dt > max_dt):
                max_dt = dt
            rows_24h.append((dt, text.lower()))

    if not rows_24h:
        return {"windowNote": window_note, "top": fallback_fn()}

    window_end = max_dt or datetime.now(timezone.utc)
    window_start = window_end - timedelta(hours=24)
    texts = [t for dt, t in rows_24h if dt is None or window_start <= dt <= window_end]
    if len(texts) < 5:
        texts = [t for _, t in rows_24h]

    counts: Counter = Counter()
    for label, pattern, _color in ISSUE_TAXONOMY:
        hits = sum(1 for t in texts if re.search(pattern, t, re.I))
        if hits:
            counts[label] = hits

    total_hits = sum(counts.values()) or 1
    top = []
    color_map = {label: color for label, _, color in ISSUE_TAXONOMY}
    for label, hits in counts.most_common(6):
        top.append({
            "label": label,
            "pct": round(hits / total_hits * 100),
            "mentions": hits,
            "color": color_map.get(label, "var(--amber)"),
        })

    if len(top) < 4:
        top.extend(fallback_fn()[: 4 - len(top)])

    _normalize_pct(top)
    return {"windowNote": window_note, "top": top[:6], "postsScanned": len(texts)}


def _issues_from_seats_only(exports: list | None = None) -> list:
    if exports:
        seat_issues: Counter = Counter()
        for ex in exports:
            for key in ("isuUtama1", "isuUtama2", "isuUtama3"):
                for val in ex.get("issues") or []:
                    if isinstance(val, str) and val.strip():
                        seat_issues[val.strip()] += 1
            for key in ("isuUtama1", "isuUtama2", "isuUtama3"):
                val = ex.get(key)
                if val:
                    seat_issues[val.strip()] += 1
        if seat_issues:
            total = sum(seat_issues.values()) or 1
            colors = ["var(--amber)", "var(--purple)", "var(--cyan)", "var(--primary)"]
            items = []
            for i, (label, n) in enumerate(seat_issues.most_common(6)):
                items.append({"label": label, "pct": round(n / total * 100), "mentions": n, "color": colors[i % 4]})
            _normalize_pct(items)
            return items

    exports = load_json(SEATS_EXPORT, [])
    seat_issues: Counter = Counter()
    for ex in exports:
        for key in ("isuUtama1", "isuUtama2", "isuUtama3"):
            val = ex.get(key)
            if val:
                seat_issues[val.strip()] += 1
    total = sum(seat_issues.values()) or 1
    colors = ["var(--amber)", "var(--purple)", "var(--cyan)", "var(--primary)"]
    items = []
    for i, (label, n) in enumerate(seat_issues.most_common(6)):
        items.append({"label": label, "pct": round(n / total * 100), "mentions": n, "color": colors[i % 4]})
    _normalize_pct(items)
    return items or [
        {"label": "Kos Sara Hidup", "pct": 34, "color": "var(--amber)"},
        {"label": "Pendidikan / SJKT-SJKC", "pct": 22, "color": "var(--purple)"},
    ]


def _normalize_pct(items: list) -> None:
    if not items:
        return
    s = sum(i.get("pct", 0) for i in items) or 1
    for i in items:
        i["pct"] = max(1, round(i.get("pct", 0) / s * 100))
    delta = 100 - sum(i["pct"] for i in items)
    if delta and items:
        items[0]["pct"] += delta


def _pas_seat_role(ex: dict) -> tuple[str, str]:
    party = ex.get("party2023") or ""
    bloc = ex.get("winner2023") or ""
    if party == "PAS":
        return "pertahan_pas", "Pertahan PAS"
    if party == "Bersatu" or ex.get("isBersatuSeat") or (bloc == "PN" and ex.get("isPnSeat")):
        return "pertahan_pn", "Pertahan PN"
    return "sasaran_flip", "Sasaran Menang"


def _pas_target_entry(ex: dict, code: str, tier: str) -> dict:
    role, role_label = _pas_seat_role(ex)
    dpi = ex.get("dpi") or {}
    return {
        "code": code,
        "name": ex.get("name", ""),
        "pasTier": tier,
        "pasTierLabel": "Wajib" if tier == "wajib" else "Imbang",
        "seatRole": role,
        "seatRoleLabel": role_label,
        "winner2023": ex.get("winner2023"),
        "party2023": party if (party := ex.get("party2023")) else "",
        "winnerName2023": ex.get("winnerName", ""),
        "kategoriPas": ex.get("kategoriPas"),
        "kategoriPasLabel": ex.get("kategoriPasLabel"),
        "pasWinProb": ex.get("pasWinProb"),
        "challenger": ex.get("challenger"),
        "challengerParty": ex.get("challengerParty"),
        "dpi": {
            "bkcCula": dpi.get("bkcCula"),
            "culaPct": dpi.get("culaPct"),
            "skt51": dpi.get("skt51"),
        },
    }


def build_pas_target_23(exports: list) -> dict:
    by_code = {s.get("code"): s for s in exports}
    seats = []
    pas_2023 = pn_2023 = flip = 0
    for code in sorted(PAS_MUST_16, key=lambda c: int(c[1:])):
        ex = by_code.get(code, {})
        entry = _pas_target_entry(ex, code, "wajib")
        seats.append(entry)
        if entry["seatRole"] == "pertahan_pas":
            pas_2023 += 1
        elif entry["seatRole"] == "pertahan_pn":
            pn_2023 += 1
        else:
            flip += 1
    imbang_flip = 0
    for code in sorted(PAS_BALANCE_7, key=lambda c: int(c[1:])):
        ex = by_code.get(code, {})
        entry = _pas_target_entry(ex, code, "imbang")
        seats.append(entry)
        if entry["seatRole"] == "sasaran_flip":
            imbang_flip += 1
    return {
        "meta": {
            "title": "23 Kerusi Contest PAS (16 Wajib + 7 Imbang)",
            "source": "scripts/generate_prn_n9_mn_presentation.py PAS_MUST_16 + PAS_BALANCE_7",
            "count": 23,
            "wajibCount": 16,
            "imbangCount": 7,
            "pasIncumbent2023": pas_2023,
            "pnIncumbent2023": pn_2023,
            "flipTarget2023": flip,
            "imbangFlip2023": imbang_flip,
            "note": (
                f"16 wajib: {pas_2023} PAS + {pn_2023} PN + {flip} flip · "
                f"7 imbang: {imbang_flip} flip (semua BN/UMNO 2023)"
            ),
        },
        "codes": [s["code"] for s in seats],
        "seats": seats,
    }


def build_pas_target_16(exports: list) -> dict:
    full = build_pas_target_23(exports)
    seats = [s for s in full["seats"] if s["pasTier"] == "wajib"]
    m = full["meta"]
    return {
        "meta": {
            "title": "16 Kerusi Sasaran PAS (Wajib Bertanding)",
            "source": m["source"],
            "count": 16,
            "pasIncumbent2023": m["pasIncumbent2023"],
            "pnIncumbent2023": m["pnIncumbent2023"],
            "flipTarget2023": m["flipTarget2023"],
            "note": m["note"].split(" · ")[0],
        },
        "codes": [s["code"] for s in seats],
        "seats": seats,
    }


def pas_target_index(pas_target: dict) -> dict:
    return {s["code"]: s for s in (pas_target or {}).get("seats") or []}


def run_dosm_ingest() -> dict:
    script = ROOT / "scripts/ingest_dosm_census_warroom.py"
    if script.exists():
        subprocess.run([sys.executable, str(script)], check=False, cwd=str(ROOT))
    return load_json(DOSM_CENSUS_JSON, {})


def census_for_seat(census: dict, state_key: str, code: str, district: str | None = None) -> dict | None:
    by_dun = census.get("byDun") or {}
    key = f"{state_key}:{norm_code(code)}"
    row = by_dun.get(key)
    if not row:
        return None
    out = dict(row)
    states = census.get("states") or {}
    st = states.get(state_key) or {}
    dist_map = st.get("districts") or {}
    if district and district in dist_map:
        out["districtEthnicityPct"] = dist_map[district].get("ethnicityPct")
        out["districtPopulation"] = dist_map[district].get("population")
    return out


def merge_production_seats(
    exports: list,
    geo_list: list,
    socmed: dict | None,
    pas_target: dict | None,
    census: dict | None = None,
    scoresheet: dict | None = None,
    cula_poll: dict | None = None,
) -> list:
    geo = geo_index(geo_list)
    soc = (socmed or {}).get("byDun") or {}
    cula_by_dun = (cula_poll or {}).get("byDun") or {}
    pt = pas_target_index(pas_target)
    pas_lead_set = select_pas_solo_lead_seats(exports)
    contest_rank = rank_pas_solo_contest_27(exports)
    seats = []
    for ex in exports:
        code = norm_code(ex.get("code"))
        g = geo.get(code, {})
        dpi = ex.get("dpi") or {}
        sm = soc.get(code) or {}
        cula_dun = cula_by_dun.get(code) or {}
        cula_poll_seat = None
        if cula_dun.get("mnVsSolo") or cula_dun.get("pasLabu"):
            lead = cula_dun.get("pasLabu") or cula_dun.get("mnVsSolo") or {}
            cula_poll_seat = {
                "mnVsSolo": cula_dun.get("mnVsSolo"),
                "pasLabu": cula_dun.get("pasLabu"),
                "posts": len(cula_dun.get("posts") or []),
                "commentsReported": lead.get("commentsReported") or 0,
                "commentsKeyword": lead.get("commentsKeyword") or 0,
                "bucketsExpanded": lead.get("bucketsExpanded"),
                "bucketsKeyword": lead.get("buckets"),
                "insight": lead.get("insight"),
                "insightKeyword": lead.get("insightKeyword"),
            }
        maj = ex.get("majority") or 0
        pos_pct = sm.get("pos_pct") or 0
        neg_pct = sm.get("neg_pct") or 0
        sentiment = round(50 + (pos_pct - neg_pct) * 0.5, 0) if sm.get("mentions_total") else None
        t = pt.get(code) or {}
        socmed_meta = (socmed or {}).get("meta") or {}
        hl = build_display_headlines(
            {**ex, "stateKey": "N9"},
            crawl_headlines=ex.get("socialCrawlHeadlines"),
            socmed_snippet=sm.get("top_snippet"),
            socmed_snippet_date=sm.get("top_snippet_date"),
            ref_date=socmed_meta.get("window_end_utc"),
        )

        seat_row = {
            "id": code,
            "name": ex.get("name", ""),
            "district": ex.get("parlimen"),
            "status": KATEGORI_STATUS.get(ex.get("kategoriPas"), g.get("status", "battleground")),
            "pasTarget": code in pt,
            "pasTier": t.get("pasTier"),
            "pasTierLabel": t.get("pasTierLabel"),
            "seatRole": t.get("seatRole"),
            "seatRoleLabel": t.get("seatRoleLabel"),
            "incumbent": ex.get("winnerName") or ex.get("namaAdun"),
            "party": ex.get("party2023"),
            "party2023": ex.get("party2023"),
            "winner2023": ex.get("winner2023"),
            "majority": maj,
            "margin2023": f"+{maj:,}" if maj else g.get("margin2023"),
            "pasWinProb": ex.get("pasWinProb"),
            "kategoriPas": ex.get("kategoriPas"),
            "kategoriPasLabel": ex.get("kategoriPasLabel"),
            "predictionLabel": ex.get("predictionLabel"),
            "scenarioPasSolo": ex.get("scenarioPasSolo"),
            "scenarioPasMn": ex.get("scenarioPasMn"),
            "scenarioPasPn": ex.get("scenarioPasPn"),
            "sentiment": sentiment,
            "socmedMentions": sm.get("mentions_total", 0),
            "socmedMentions24h": sm.get("mentions_24h", 0),
            "socmedNegPct": sm.get("neg_pct"),
            "socmedDemoMix": sm.get("demo_mix") or {},
            "socmedDemoTop": sm.get("demo_top"),
            "socmedDemoInsight": sm.get("demo_insight"),
            "socmedNarrativeSplitPct": sm.get("narrative_split_pct"),
            "socmedEmotionTop": sm.get("emotion_top"),
            "issues": [x for x in [ex.get("isuUtama1"), ex.get("isuUtama2"), ex.get("isuUtama3")] if x],
            "demo": {
                "malay": dpi.get("pctMelayu") or ex.get("pctMelayu"),
                "chinese": dpi.get("pctCina"),
                "indian": dpi.get("pctIndia"),
            },
            "dpi": {
                "bkcCula": dpi.get("bkcCula"),
                "culaPct": dpi.get("culaPct"),
                "culaPasTotal": dpi.get("culaPasTotal"),
                "skt51": dpi.get("skt51"),
                "registeredVoters": dpi.get("registeredVotersDpi") or ex.get("registeredVoters"),
            },
            "lat": g.get("lat"),
            "lon": g.get("lon"),
            "confidence": g.get("confidence"),
            "geoNote": g.get("geoNote") or g.get("note"),
            "proxyLocation": g.get("proxyLocation"),
            "action": ex.get("strategicNote"),
            "newsMentions": ex.get("newsMentions"),
            "socialHeadlines": hl["headlines"],
            "headlineMeta": {
                "quality": hl["quality"],
                "source": hl["source"],
                "items": hl["items"],
            },
            "challenger": ex.get("challenger"),
            "challengerParty": ex.get("challengerParty"),
            "census": census_for_seat(census or {}, "N9", code, ex.get("parlimen")),
            "culaPoll": cula_poll_seat,
            "source": "production",
        }
        scen = predict_n9_seat_scenarios({**ex, **seat_row, "code": code}, sm, pas_lead_set, contest_rank)
        seat_row.update(scen)
        spr = (scoresheet or {}).get(code)
        if spr:
            seat_row["spr2023"] = spr
        seats.append(seat_row)
    return seats


def merge_johor_production_seats(geo_list: list, socmed: dict | None, census: dict | None = None) -> list:
    soc = (socmed or {}).get("byDun") or {}
    socmed_meta = (socmed or {}).get("meta") or {}
    seats = []
    for g in geo_list or []:
        code = norm_code(g.get("id") or g.get("code"))
        sm = soc.get(code) or {}
        pos_pct = sm.get("pos_pct") or 0
        neg_pct = sm.get("neg_pct") or 0
        sentiment = round(50 + (pos_pct - neg_pct) * 0.5, 0) if sm.get("mentions_total") else g.get("sentiment")
        seat_ctx = {
            "code": code,
            "name": g.get("name"),
            "incumbent": g.get("incumbent"),
            "stateKey": "Johor",
        }
        hl = build_display_headlines(
            seat_ctx,
            socmed_snippet=sm.get("top_snippet"),
            socmed_snippet_date=sm.get("top_snippet_date"),
            ref_date=socmed_meta.get("window_end_utc"),
        )
        seats.append({
            **g,
            "id": code,
            **predict_johor_seat(g, sm),
            "majority2022": g.get("majority2022") or g.get("majority"),
            "majority": g.get("majority") or g.get("majority2022"),
            "sentiment": sentiment,
            "socmedMentions": sm.get("mentions_total", 0),
            "socmedMentions24h": sm.get("mentions_24h", 0),
            "socmedNegPct": sm.get("neg_pct"),
            "socialHeadlines": hl["headlines"],
            "headlineMeta": {
                "quality": hl["quality"],
                "source": hl["source"],
                "items": hl["items"],
            },
            "census": census_for_seat(census or {}, "Johor", code, g.get("district")),
            "source": "production",
        })
    return seats


def _johor_party_bloc(party: str) -> str:
    p = (party or "").upper()
    if p in ("PN", "PAS", "BERSATU"):
        return "PN"
    if p == "PH":
        return "PH"
    return "BN"


def _estimate_johor_pas_prob(party: str, status: str, sm: dict) -> float:
    p = (party or "").upper()
    st = (status or "battleground").lower()
    base = {
        "PN": 68.0, "PAS": 72.0, "BERSATU": 65.0,
        "BN": 30.0, "UMNO": 32.0, "MCA": 28.0, "MIC": 26.0,
        "PH": 16.0, "DAP": 14.0, "PKR": 18.0, "AMANAH": 20.0,
        "MUDA": 22.0, "ALONE": 22.0,
    }.get(p, 25.0)
    if st == "stronghold":
        if p in ("PN", "PAS"):
            base = min(85.0, base + 10.0)
        else:
            base = max(12.0, base - 8.0)
    elif st == "battleground":
        if p == "BN":
            base = 38.0
        elif p == "PH":
            base = 22.0
        elif p == "PN":
            base = 62.0
    mentions = sm.get("mentions_total") or 0
    if mentions >= 3:
        neg = sm.get("neg_pct") or 0
        if p in ("PH", "BN") and neg >= 40:
            base += 4.0
        elif p in ("PN", "PAS") and (sm.get("pos_pct") or 0) >= 45:
            base += 3.0
    return round(min(88.0, max(10.0, base)), 1)


def build_johor_seat_exports(geo_list: list, socmed: dict | None = None) -> list:
    soc = (socmed or {}).get("byDun") or {}
    exports = []
    for g in geo_list or []:
        code = norm_code(g.get("id") or g.get("code"))
        party_detail = (g.get("party2022") or g.get("party2023") or g.get("semasaParti") or g.get("party") or "").upper()
        sm = soc.get(code) or {}
        pred = predict_johor_seat(g, sm)
        bloc = pred.get("predictedBloc") or g.get("winner2022") or g.get("winner2023") or _johor_party_bloc(party_detail)
        status = (g.get("status") or "battleground").lower()
        exports.append({
            "code": code,
            "name": g.get("name"),
            "party2023": party_detail,
            "party2022": g.get("party2022") or party_detail,
            "predictedBloc": bloc,
            "incumbent": g.get("incumbent"),
            "winnerName2022": g.get("winnerName2022") or g.get("incumbent"),
            "majority2022": g.get("majority2022") or g.get("majority"),
            **pred,
            "threeCornerRisk": "Sederhana" if status == "battleground" else "Rendah",
            "issues": g.get("issues") or [],
            "electionRef": g.get("electionRef"),
        })
    return exports


def build_johor_social_summary(
    exports: list,
    socmed: dict | None,
    issues: dict | None,
    formation: dict | None,
    master_analytics: dict | None,
) -> dict:
    soc = socmed or {}
    meta = soc.get("meta") or {}
    pos = neg = neu = 0
    for row in (soc.get("byDun") or {}).values():
        t = row.get("mentions_total") or 0
        if not t:
            continue
        neg += int(t * (row.get("neg_pct") or 0) / 100)
        pos += int(t * (row.get("pos_pct") or 0) / 100)
        neu += max(0, t - neg - pos)
    total_sent = pos + neg + neu or 1
    pn_projected = sum(1 for s in exports if (s.get("pasWinProb") or 0) >= 50)
    ma = master_analytics or {}
    coalition = (formation or {}).get("coalition") or []
    mb_insight = compute_johor_mb_insight(exports)

    return {
        "meta": {
            "generated": datetime.now(MYT).strftime("%Y-%m-%d %H:%M:%S"),
            "state": "Johor",
            "masterSource": meta.get("master_source") or ma.get("masterFile"),
            "johorPosts": ma.get("johorPosts") or meta.get("state_rows_scanned") or 0,
            "totalPosts": ma.get("totalPosts") or 0,
            "totalDataPoints": ma.get("totalDataPoints") or ma.get("totalPosts") or 0,
            "totalEngagement": ma.get("totalEngagement") or 0,
            "johorEngagement": ma.get("johorEngagement") or 0,
            "posPct": round(pos / total_sent * 100, 1) if total_sent else 0,
            "negPct": round(neg / total_sent * 100, 1) if total_sent else 0,
        },
        "analytics": ma,
        "seats": {
            "defend": sum(1 for s in exports if s.get("predictedBloc") == "PN"),
            "winnable": sum(1 for s in exports if 35 <= (s.get("pasWinProb") or 0) < 50),
            "pnProjected": pn_projected,
            "pasTarget": pn_projected,
            "total": len(exports) or TOTAL_JOHOR,
            "majority": MAJORITY_JOHOR,
        },
        "alerts": {"critical": 0, "warning": 0, "total": 0},
        "coalition": coalition,
        "coalitionFormation": formation or {},
        "coalitionContext": (formation or {}).get("disclaimer") or COALITION_JOHOR_NOTE,
        "mbInsight": mb_insight,
        "issues": issues or {},
    }


def build_johor_social_bundle(
    master_path: Path | None,
    master_analytics: dict | None,
) -> dict | None:
    geo_list = load_json(GEO_JOHOR, [])
    if not geo_list:
        return None
    socmed = load_json(PROTO_DATA / "socmed_by_dun_Johor.json", {})
    exports = build_johor_seat_exports(geo_list, socmed)
    issues = extract_issue_heatmap(master_path, socmed, JOHOR_PATTERN, exports)
    formation = compute_coalition_formation(
        exports,
        master_path,
        socmed,
        majority=MAJORITY_JOHOR,
        scope_pattern=JOHOR_PATTERN,
        state_label="Johor",
    )
    social = build_johor_social_summary(exports, socmed, issues, formation, master_analytics)
    OUT_SOCIAL_JOHOR.write_text(json.dumps(social, ensure_ascii=False, indent=2), encoding="utf-8")
    return social


def build_johor_production(census: dict | None) -> list:
    geo_list = load_json(GEO_JOHOR, [])
    socmed = load_json(PROTO_DATA / "socmed_by_dun_Johor.json", {})
    if not geo_list:
        return []
    seats = merge_johor_production_seats(geo_list, socmed, census)
    OUT_DUN_JOHOR.write_text(json.dumps(seats, ensure_ascii=False, indent=2), encoding="utf-8")
    bundle = {
        "meta": {
            "mode": "production",
            "state": "Johor",
            "generated": datetime.now(MYT).strftime("%Y-%m-%d %H:%M:%S"),
            "sources": {
                "geo": str(GEO_JOHOR.relative_to(ROOT)),
                "socmed": "prototype/data/socmed_by_dun_Johor.json",
            },
        },
        "seatCount": len(seats),
        "headlineSummary": {
            "verified": sum(1 for s in seats if (s.get("headlineMeta") or {}).get("quality") == "verified"),
            "weak": sum(1 for s in seats if (s.get("headlineMeta") or {}).get("quality") == "weak"),
            "none": sum(1 for s in seats if (s.get("headlineMeta") or {}).get("quality") == "none"),
        },
    }
    OUT_BUNDLE_JOHOR.write_text(json.dumps(bundle, ensure_ascii=False, indent=2), encoding="utf-8")
    return seats


def enrich_war_room_intel(war_room: dict, socmed: dict | None, issues: dict | None) -> dict:
    """Merge socmed signals into hari_ini items for intel cards."""
    soc = (socmed or {}).get("byDun") or {}
    intel = {
        "meta": war_room.get("meta", {}),
        "hari_ini": war_room.get("hari_ini", {}),
        "socmed_rollups": {},
    }
    sm_meta = (socmed or {}).get("meta") or {}
    rollup = (socmed or {}).get("rollup") or {}
    top_issues = (issues or {}).get("top") or []
    intel["socmed_rollups"] = {
        "mention_volume_24h": rollup.get("mentions_total_ns"),
        "neg_pct_avg": sm_meta.get("ns_neg_pct"),
        "top_issues": [{"label": i["label"], "pct": i["pct"]} for i in top_issues[:3]],
        "source": sm_meta.get("master_source", "PAS Break master crawl"),
    }
    items = []
    for item in intel.get("hari_ini", {}).get("items") or []:
        code = norm_code(item.get("kod_dun"))
        s = soc.get(code) or {}
        merged = dict(item)
        if s.get("mentions_24h"):
            merged["mentions"] = s["mentions_24h"]
        elif s.get("mentions_total"):
            merged["mentions"] = s["mentions_total"]
        if s.get("neg_pct") is not None:
            merged["neg_pct"] = s["neg_pct"]
        if s.get("alert_level"):
            merged["alert_level"] = s["alert_level"]
        items.append(merged)
    intel["hari_ini"]["items"] = items
    return intel


def build_social_summary(
    exports: list,
    socmed: dict | None,
    war_room: dict | None,
    issues: dict | None,
    coalition: list | None,
    coalition_formation: dict | None = None,
    master_analytics: dict | None = None,
    mn_insight: dict | None = None,
    demo_hybrid: dict | None = None,
    cula_poll_summary: dict | None = None,
) -> dict:
    soc = socmed or {}
    meta = soc.get("meta") or {}
    rollup = soc.get("rollup") or {}
    ns_total = rollup.get("mentions_total_ns") or 0
    pos = neg = neu = 0
    for row in (soc.get("byDun") or {}).values():
        t = row.get("mentions_total") or 0
        if not t:
            continue
        neg += int(t * (row.get("neg_pct") or 0) / 100)
        pos += int(t * (row.get("pos_pct") or 0) / 100)
        neu += max(0, t - neg - pos)
    total_sent = pos + neg + neu or 1
    pos_pct = round(pos / total_sent * 100, 1)

    defend = sum(1 for s in exports if s.get("kategoriPas") == "defend")
    winnable = sum(1 for s in exports if s.get("kategoriPas") == "winnable")
    pn_projected = sum(1 for s in exports if (s.get("pasWinProb") or 0) >= 50)

    triggers = (war_room or {}).get("triggers") or []
    critical = sum(1 for t in triggers if t.get("severity") == "critical")
    warning = sum(1 for t in triggers if t.get("severity") == "warning")

    ma = master_analytics or {}
    ns_posts = ma.get("nsPosts") or ns_total

    return {
        "meta": {
            "generated": datetime.now(MYT).strftime("%Y-%m-%d %H:%M:%S"),
            "masterSource": meta.get("master_source") or ma.get("masterFile"),
            "nsPosts": ns_posts,
            "totalPosts": ma.get("totalPosts") or 0,
            "totalDataPoints": ma.get("totalDataPoints") or ma.get("totalPosts") or 0,
            "totalEngagement": ma.get("totalEngagement") or 0,
            "nsEngagement": ma.get("nsEngagement") or 0,
            "prnScopedPosts": ma.get("prnScopedPosts") or 0,
            "posPct": pos_pct,
            "negPct": round(neg / total_sent * 100, 1) if total_sent else 0,
        },
        "analytics": ma,
        "seats": {
            "defend": defend,
            "winnable": winnable,
            "pnProjected": pn_projected,
            "pasTarget": 23,
            "pasWajib": 16,
            "pasImbang": 7,
            "total": len(exports),
            "majority": 19,
        },
        "alerts": {"critical": critical, "warning": warning, "total": len(triggers)},
        "coalition": coalition or [],
        "coalitionFormation": coalition_formation or {},
        "coalitionContext": (coalition_formation or {}).get("disclaimer") or COALITION_CONTEXT_NOTE,
        "mnInsight": mn_insight or {},
        "issues": issues or {},
        "demographics": {
            "stateDemoMix": rollup.get("state_demo") or {},
            "hybrid": demo_hybrid or (coalition_formation or {}).get("demographicHybrid") or {},
            "note": "DPI pengundi (SPR) vs proxy bahasa socmed — nudge ±2–3% pada senario MN/PAS/PH",
        },
        "culaPoll": cula_poll_summary or {},
    }


def run_socmed_build() -> None:
    script = ROOT / "scripts/build_warroom_socmed_by_dun.py"
    if script.exists():
        subprocess.run([sys.executable, str(script)], check=False, cwd=str(ROOT))


def run_cula_poll_build() -> None:
    script = ROOT / "scripts/build_cula_poll_by_dun_n9.py"
    if script.exists():
        subprocess.run([sys.executable, str(script)], check=False, cwd=str(ROOT))


def main() -> None:
    if not SEATS_EXPORT.exists():
        print(f"❌ Missing {SEATS_EXPORT}", file=sys.stderr)
        sys.exit(1)

    run_socmed_build()
    run_cula_poll_build()
    census = run_dosm_ingest()

    exports = load_json(SEATS_EXPORT, [])
    geo_list = load_json(GEO_MOCK, [])
    war_room = load_json(WAR_ROOM_JSON, {})
    socmed = load_json(PROTO_DATA / "socmed_by_dun_N9.json", {})
    cula_poll = load_json(OUT_CULA_POLL, {})
    cula_poll_summary = load_json(OUT_CULA_SUMMARY, {})
    dpi = load_json(DPI_JSON, {})

    if DPI_JSON.exists():
        shutil.copy2(DPI_JSON, PROTO_DATA / "n9_dpi_updates.json")

    pas_target = build_pas_target_23(exports)
    OUT_PAS_TARGET.write_text(json.dumps(pas_target, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_PAS_TARGET_16.write_text(
        json.dumps(build_pas_target_16(exports), ensure_ascii=False, indent=2), encoding="utf-8"
    )

    if not SCORESHEET_STREAMS.exists():
        parse_script = ROOT / "scripts/parse_n9_scoresheets_2023.py"
        if parse_script.exists():
            subprocess.run([sys.executable, str(parse_script)], check=False, cwd=str(ROOT))
    scoresheet_enrich = build_all_enrichment()
    OUT_SPR2023.write_text(
        json.dumps(scoresheet_enrich, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    spr_summary = summary_stats(scoresheet_enrich)

    production_seats = merge_production_seats(
        exports, geo_list, socmed, pas_target, census, scoresheet_enrich, cula_poll
    )
    mn_insight = compute_n9_mn_insight(production_seats)
    OUT_DUN.write_text(json.dumps(production_seats, ensure_ascii=False, indent=2), encoding="utf-8")

    master = find_master()
    master_analytics = compute_master_analytics(master)
    issues = extract_issue_heatmap(master, socmed)
    demo_hybrid = compute_state_demographic_hybrid(exports, socmed, dpi)
    formation = compute_coalition_formation(exports, master, socmed, demo_hybrid)
    coalition = formation.get("coalition") or []

    intel = enrich_war_room_intel(war_room, socmed, issues)
    OUT_INTEL.write_text(json.dumps(intel, ensure_ascii=False, indent=2), encoding="utf-8")

    social = build_social_summary(
        exports,
        socmed,
        war_room,
        issues,
        coalition,
        formation,
        master_analytics,
        mn_insight,
        demo_hybrid,
        cula_poll_summary,
    )
    OUT_SOCIAL.write_text(json.dumps(social, ensure_ascii=False, indent=2), encoding="utf-8")

    bundle = {
        "meta": {
            "mode": "production",
            "state": "N9",
            "generated": datetime.now(MYT).strftime("%Y-%m-%d %H:%M:%S"),
            "productionDashboard": "reports/dashboards/prn-negeri-sembilan-dashboard.html",
            "sources": {
                "seats": str(SEATS_EXPORT.relative_to(ROOT)),
                "warRoom": str(WAR_ROOM_JSON.relative_to(ROOT)) if WAR_ROOM_JSON.exists() else None,
                "dpi": str(DPI_JSON.relative_to(ROOT)) if DPI_JSON.exists() else None,
                "socmed": "prototype/data/socmed_by_dun_N9.json",
                "culaPoll": "prototype/data/cula_poll_by_dun_N9.json",
                "geo": str(GEO_MOCK.relative_to(ROOT)),
                "dosmCensus": str(DOSM_CENSUS_JSON.relative_to(ROOT)) if DOSM_CENSUS_JSON.exists() else None,
                "masterCrawl": master_analytics.get("masterFile") if master_analytics else None,
                "spr2023": str(SCORESHEET_STREAMS.relative_to(ROOT)) if SCORESHEET_STREAMS.exists() else None,
            },
            "spr2023Summary": spr_summary,
        },
        "analytics": master_analytics,
        "socialSummary": social,
        "seatCount": len(production_seats),
        "pasTarget23": pas_target["meta"],
        "pasTarget16": build_pas_target_16(exports)["meta"],
    }
    OUT_BUNDLE.write_text(json.dumps(bundle, ensure_ascii=False, indent=2), encoding="utf-8")

    print("✅ Production bundle synced for War Room prototype")
    print(f"   DUN seats:  {OUT_DUN.name} ({len(production_seats)} kerusi)")
    print(f"   Intel:      {OUT_INTEL.name}")
    print(f"   Social KPI: {OUT_SOCIAL.name}")
    print(f"   Manifest:   {OUT_BUNDLE.name}")
    print(f"   PN projected (pasWinProb≥50): {social['seats']['pnProjected']}/{social['seats']['total']}")
    ma = social.get("analytics") or {}
    if ma.get("totalPosts"):
        print(
            f"   Master crawl: {ma['totalPosts']:,} post · {ma['totalEngagement']:,} engagement · "
            f"N9: {ma.get('nsPosts', 0):,} post"
        )
    if coalition:
        top_c = max(coalition, key=lambda x: x["pct"])
        print(
            f"   Majoriti lead: {top_c['name']} — ~{top_c.get('expectedSeats', '?')}/36 kerusi · "
            f"peluang majoriti {top_c['pct']}%"
        )
    if issues.get("top"):
        print(f"   Top issue: {issues['top'][0]['label']} {issues['top'][0]['pct']}%")
    m = pas_target["meta"]
    print(f"   PAS target 23: {OUT_PAS_TARGET.name} ({m['wajibCount']} wajib + {m['imbangCount']} imbang)")

    johor_seats = build_johor_production(census)
    if johor_seats:
        js = bundle_johor_summary(johor_seats)
        johor_social = build_johor_social_bundle(master, master_analytics)
        print(f"   Johor DUN:  {OUT_DUN_JOHOR.name} ({len(johor_seats)} kerusi)")
        print(f"   Johor headlines: {js['verified']} disahkan · {js['none']} tiada terkini")
        if johor_social:
            print(f"   Johor social: {OUT_SOCIAL_JOHOR.name}")
            jcoal = johor_social.get("coalition") or []
            if jcoal:
                top_j = max(jcoal, key=lambda x: x.get("pct") or 0)
                print(
                    f"   Johor majoriti lead: {top_j['name']} — "
                    f"~{top_j.get('expectedSeats', '?')}/{TOTAL_JOHOR} kerusi · "
                    f"peluang {top_j.get('pct')}%"
                )
            jissues = (johor_social.get("issues") or {}).get("top") or []
            if jissues:
                print(f"   Johor top issue: {jissues[0]['label']} {jissues[0]['pct']}%")

    sync = ROOT / "scripts" / "build_n9_daily_ops_sync.py"
    if sync.exists():
        import subprocess

        py = ROOT / ".venv" / "bin" / "python"
        if not py.exists():
            py = Path(sys.executable)
        subprocess.run([str(py), str(sync)], check=False)


def bundle_johor_summary(seats: list) -> dict:
    return {
        "verified": sum(1 for s in seats if (s.get("headlineMeta") or {}).get("quality") == "verified"),
        "weak": sum(1 for s in seats if (s.get("headlineMeta") or {}).get("quality") == "weak"),
        "none": sum(1 for s in seats if (s.get("headlineMeta") or {}).get("quality") == "none"),
    }


if __name__ == "__main__":
    main()
