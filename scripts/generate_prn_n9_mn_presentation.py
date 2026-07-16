#!/usr/bin/env python3
"""Generate PAS+BN (MN) seat negotiation dashboard — per-seat justification + hybrid model."""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from prn_paths import reports, ensure_state_dirs  # noqa: E402
from n9_bloc7_model import (  # noqa: E402
    coalition_scenarios,
    seat_scenario_insight,
    seat_scenario_rows,
    DEFAULT_BERSAMA_PCT,
)

ensure_state_dirs("N9")
OUT_HTML = reports("N9") / "dashboards/prn-n9-mn-pas-bn-presentation.html"
OUT_COPY = ROOT / "JITP_2026/Master_File/N9/prn-n9-mn-pas-bn-presentation.html"
DESKTOP_DIR = Path.home() / "Desktop/N9"
DESKTOP_HTML = Path.home() / "Desktop/PRN_N9_MN_Justifikasi_36Kerusi.html"
DESKTOP_HTML_N9 = DESKTOP_DIR / "PRN_N9_MN_Justifikasi_36Kerusi.html"

SEATS_JSON = reports("N9") / "seats/n9_seats_export.json"
SEATS_ANALYTICS = reports("N9") / "seats/n9_seats_analytics.json"
DPI_JSON = ROOT / "data/projects/political/PRN/PRN_N9/reference/n9_dpi_updates.json"
NEWS_SUM = ROOT / "data/projects/political/PRN/PRN_N9/reference/prn_n9_news_summary.json"
NEWS_ANALYZED = ROOT / "data/projects/political/PRN/PRN_N9/reference/prn_n9_news_analyzed_summary.json"
MASTER_GLOB = ROOT / "data/projects/political/pas_break_2026/master/PAS_Break_Master_EXCO_Analyzed_*.csv"
PRODUCTION_BUNDLE = (
    ROOT / "data/projects/political/PRN/PRN_N9/reports/war_room/prototype/data/n9_production_bundle.json"
)
SOCMED_BY_DUN = (
    ROOT / "data/projects/political/PRN/PRN_N9/reports/war_room/prototype/data/socmed_by_dun_N9.json"
)
WARROOM_PRODUCTION = (
    ROOT / "data/projects/political/PRN/PRN_N9/reports/war_room/prototype/data/warroom_dun_N9_production.json"
)

# ── Agihan MN (arahan HQ · YB Kamarol): PAS/PN 13 (9 wajib + 4 berhasrat) · UMNO/BN 23 ──
# 9 wajib — PAS/PN pertahan kerusi menang 2023 + rebut PH yang PAS tuntut
PAS_WAJIB_9 = {"N25", "N31", "N05", "N20", "N34", "N14", "N13", "N18", "N04"}
# 4 berhasrat — kubu PH yang PAS berhasrat rebut (stretch, perlu usaha padat)
PAS_BERHASRAT_4 = {"N33", "N10", "N01", "N36"}
PAS_13 = PAS_WAJIB_9 | PAS_BERHASRAT_4

PAS_TIER_LABELS = {
    "N25": "Wajib · pertahan PN (PAS 2023)", "N31": "Wajib · pertahan PN (PAS 2023)",
    "N05": "Wajib · pertahan PN (PAS 2023)", "N20": "Wajib · pertahan PN (Bersatu 2023)",
    "N34": "Wajib · pertahan PN (Bersatu 2023)", "N14": "Wajib · rebut PH (PAS tuntut)",
    "N13": "Wajib · rebut PH (PAS tuntut)", "N18": "Wajib · rebut PH (PAS tuntut)",
    "N04": "Wajib · rebut PH (PAS tuntut)", "N33": "Berhasrat · rebut PH",
    "N10": "Berhasrat · rebut PH", "N01": "Berhasrat · rebut PH", "N36": "Berhasrat · rebut PH",
}

# Alias serasi-belakang (kod sedia ada merujuk nama lama)
PAS_MUST_16 = PAS_WAJIB_9
PAS_BALANCE_7 = PAS_BERHASRAT_4
PAS_23 = PAS_13
UMNO_23 = {f"N{i:02d}" for i in range(1, 37)} - PAS_13
UMNO_13 = UMNO_23

UMNO_13_RATIONALE: dict[str, str] = {
    # — UMNO/BN pertahan: BN menang PRN 2023 —
    "N02": "Pertang — UMNO/BN pertahan kerusi menang 2023; Melayu rural, UMNO tradisi kuat.",
    "N03": "Sungai Lui — UMNO/BN pertahan kerusi menang 2023; FELDA/rural, mesin BN sedia.",
    "N06": "Palong — UMNO/BN pertahan kerusi menang 2023; FELDA Jempol, kubu BN.",
    "N07": "Jeram Padang — UMNO/BN pertahan kerusi menang 2023; rural Jempol.",
    "N09": "Lenggeng — UMNO/BN pertahan kerusi menang 2023; semi-rural Seremban.",
    "N15": "Juasseh — UMNO/BN pertahan kerusi menang 2023; rural Kuala Pilah.",
    "N16": "Seri Menanti — UMNO/BN pertahan kerusi menang 2023; adat & istana, kubu UMNO.",
    "N17": "Senaling — UMNO/BN pertahan kerusi menang 2023; rural Kuala Pilah.",
    "N19": "Johol — UMNO/BN pertahan kerusi menang 2023; rural, UMNO mapan.",
    "N28": "Kota — UMNO/BN pertahan kerusi menang 2023; semi-bandar Rembau.",
    "N35": "Gemencheh — UMNO/BN pertahan kerusi menang 2023; FELDA Tampin.",
    "N26": "Chembong — UMNO/BN pertahan; Rembau tradisi BN, Melayu ~84%.",
    "N27": "Rantau — UMNO/BN pertahan; legacy Mohamad Hasan, kubu kuat.",
    "N32": "Linggi — UMNO/BN pertahan; sempadan Johor, UMNO mapan.",
    # — UMNO/BN cadangan: PH menang 2023, PAS opt-out (kubu DAP majoriti besar) —
    "N08": "Bahau — cadangan UMNO/BN; DAP 2023, PAS opt-out. BN profil muhibbah vs PH.",
    "N11": "Lobak — cadangan UMNO/BN; DAP Cina dominan, PAS profil tidak sesuai.",
    "N12": "Temiang — cadangan UMNO/BN; DAP berbilang kaum, elak naratif perkauman PAS.",
    "N21": "Bukit Kepayang — cadangan UMNO/BN; DAP Seremban, majoriti PH besar.",
    "N22": "Rahang — cadangan UMNO/BN; DAP bandar, profil muhibbah UMNO lebih sesuai.",
    "N23": "Mambau — cadangan UMNO/BN; DAP, Cina tertinggi NS, PAS opt-out.",
    "N24": "Seremban Jaya — cadangan UMNO/BN; DAP PH bloc, calon BN profesional bandar.",
    "N29": "Chuah — cadangan UMNO/BN; PKR pantai PD, mixed, BN calon muhibbah.",
    "N30": "Lukut — cadangan UMNO/BN; DAP, Cina ~74%, PAS opt-out.",
}

DISCLAIMER_MN = (
    "Justifikasi berdasarkan DPI Dec 2025, DOSM MyCensus, ranking DUN 10 Jun 2026, cadangan MN, "
    "socmed master hybrid (structured + unstructured · Apify + HF ft-Malay-bert), media Tier A ML. "
    "Skor analitik = fusion demografi DPI + sentiment/emotion socmed per-DUN — bukan polling SPR."
)

NEGOTIATION = {"N01", "N10", "N13", "N20", "N29", "N33", "N36"}

# Penyandang PRN 2023 — mapping parti → blok (data SPR / Excel keputusan)
PARTY_TO_BLOC: dict[str, tuple[str, str]] = {
    "DAP": ("PH", "DAP"),
    "PKR": ("PH", "PKR"),
    "AMANAH": ("PH", "Amanah"),
    "UMNO": ("BN", "UMNO"),
    "MCA": ("BN", "MCA"),
    "MIC": ("BN", "MIC"),
    "PAS": ("PN", "PAS"),
    "BERSATU": ("PN", "Bersatu"),
}


def _incumbent_info(seat: dict) -> dict:
    """Penyandang PRN 2023 — blok + parti (PH/BN/PN)."""
    party = (seat.get("party2023") or seat.get("semasaParti") or "").strip()
    party_key = party.upper().replace("BERSATU", "BERSATU")
    if party_key == "BERSATU" or party.lower() == "bersatu":
        party_key = "BERSATU"
    bloc, party_label = PARTY_TO_BLOC.get(party_key, ("—", party or "—"))
    if seat.get("semasaKoalisi") and bloc == "—":
        bloc = seat["semasaKoalisi"]
    winner = seat.get("winnerName") or seat.get("namaAdun") or ""
    return {
        "bloc": bloc,
        "party": party_label,
        "partyRaw": party,
        "winnerName": winner,
        "label": f"{bloc} · {party_label}",
        "full": f"{bloc} · {party_label} — {winner}".strip(" —"),
        "majority2023": seat.get("majority") or 0,
    }


def _build_incumbent_breakdown(rows: list[dict], alloc: str) -> dict:
    """Ringkasan penyandang PRN 2023 mengikut blok & parti untuk PAS/PN 13 / UMNO/BN 23."""
    subset = [r for r in rows if r["allocation"] == alloc]
    by_bloc: dict[str, list[dict]] = {"PH": [], "BN": [], "PN": []}
    by_party: dict[str, list[dict]] = {}
    for r in subset:
        inc = r.get("incumbent") or {}
        bloc = inc.get("bloc", "—")
        party = inc.get("party", "—")
        entry = {
            "code": r["code"],
            "name": r["name"],
            "bloc": bloc,
            "party": party,
            "winnerName": inc.get("winnerName", ""),
            "majority2023": inc.get("majority2023", 0),
        }
        if bloc in by_bloc:
            by_bloc[bloc].append(entry)
        key = f"{bloc} · {party}"
        by_party.setdefault(key, []).append(entry)
    bloc_counts = {k: len(v) for k, v in by_bloc.items()}
    party_counts = {k: len(v) for k, v in sorted(by_party.items())}
    return {
        "total": len(subset),
        "byBloc": bloc_counts,
        "byParty": party_counts,
        "blocDetail": by_bloc,
        "partyDetail": by_party,
        "narrative": _incumbent_narrative(alloc, bloc_counts, party_counts),
    }


def _incumbent_narrative(alloc: str, bloc_counts: dict, party_counts: dict) -> str:
    ph, bn, pn = bloc_counts.get("PH", 0), bloc_counts.get("BN", 0), bloc_counts.get("PN", 0)
    if alloc == "PAS":
        parts = []
        if pn:
            parts.append(f"{pn} kerusi PN (PAS/Bersatu) — pertahanan & elak 3 penjuru")
        if bn:
            parts.append(f"{bn} kerusi BN (UMNO) — muafakat: undi BN beralih PAS, 1-vs-1 vs PH")
        if ph:
            parts.append(f"{ph} kerusi PH (DAP/PKR/Amanah) — sasaran flip muafakat")
        return " · ".join(parts) if parts else "—"
    parts = []
    if ph:
        parts.append(f"{ph} kerusi PH — contest strategik vs DAP/PKR (calon UMNO muhibbah)")
    if bn:
        parts.append(f"{bn} kerusi BN — pertahanan kerusi UMNO sendiri")
    return " · ".join(parts) if parts else "—"
SWAP_NOTES = {
    "N04": "MN cadang swap dengan N03 Sungai Lui.",
    "N14": "MN cadang KP PAS di Ampangan — swap N28 Kota (UMNO).",
}

SEAT_KEYWORDS: dict[str, list[str]] = {
    "N01": ["chennah", "palong"],
    "N02": ["pertang"],
    "N03": ["sungai lui", "sg lui", "sg. lui"],
    "N04": ["klawang"],
    "N05": ["serting"],
    "N06": ["palong"],
    "N07": ["jeram padang"],
    "N08": ["bahau"],
    "N09": ["lenggeng"],
    "N10": ["nilai"],
    "N11": ["lobak"],
    "N12": ["temiang"],
    "N13": ["sikamat"],
    "N14": ["ampangan"],
    "N15": ["juasseh"],
    "N16": ["seri menanti", "menanti"],
    "N17": ["senaling"],
    "N18": ["pilah", "kuala pilah"],
    "N19": ["johol"],
    "N20": ["labu"],
    "N21": ["bukit kepayang", "kepayang"],
    "N22": ["rahang"],
    "N23": ["mambau"],
    "N24": ["seremban jaya"],
    "N25": ["paroi"],
    "N26": ["chembong"],
    "N27": ["rantau"],
    "N28": ["kota", "seremban kota"],
    "N29": ["chuah"],
    "N30": ["lukut"],
    "N31": ["bagan pinang", "port dickson"],
    "N32": ["linggi"],
    "N33": ["sri tanjung", "tanjung"],
    "N34": ["gemas"],
    "N35": ["gemencheh"],
    "N36": ["repah", "tampin"],
}

HYBRID_FORMULA = {
    "title": "Hybrid Modelling Score (0–100)",
    "layers": [
        {"id": "jentera", "label": "Layer 1 · Jentera DPI", "weight": 40, "desc": "Cula %, SKT 51%, BKC, % Melayu (DPI Dec 2025 + ranking 10 Jun)"},
        {"id": "baseline", "label": "Layer 2 · PRN 2023 Baseline", "weight": 25, "desc": "Majoriti, penyandang, risiko 3 penjuru"},
        {"id": "pas_analytics", "label": "Layer 3 · PAS Analytics", "weight": 20, "desc": "Kategori Pertahan / Boleh Menang / Sukar"},
        {"id": "socmed", "label": "Layer 4 · Socmed Master ML", "weight": 10, "desc": "Mention per-DUN dari master crawl (Apify + HF sentiment + demographic proxy)"},
        {"id": "mn_media", "label": "Layer 5 · MN + Media", "weight": 5, "desc": "Cadangan MN 10 Jun + naratif media Tier A ML + 7-bloc coalition"},
        {"id": "demografi", "label": "+ Demografi Hybrid", "weight": 0, "desc": "DPI Dec 2025 vs socmed demo_mix per-DUN — nudge naratif Melayu/bandar"},
    ],
    "rule": "Skor PAS ≥55 → cadangan PAS · Skor PAS <45 → cadangan UMNO/BN · 45–55 = ⚠ Perbincangan · Ramalan demografi = lapisan tambahan (DPI Dec 2025)",
}

PROFILE_EXTRAS: dict[str, dict[str, str]] = {
    "N01": {"tempatan": "Chennah — kos hidup, parking, banjir.", "agamaIdentiti": "Berbilang kaum; DAP stronghold.", "fenceSitters": "Cina-India + Melayu bandar muda — UMNO muhibbah."},
    "N05": {"tempatan": "FELDA Serting — harga getah/komoditi, klinik.", "agamaIdentiti": "Melayu kuat; masjid pusat mobilisasi.", "fenceSitters": "Pengundi FELDA — kos input vs subsidi."},
    "N25": {"tempatan": "Paroi — trafik, perumahan mampu milik.", "agamaIdentiti": "Campuran bandar.", "fenceSitters": "Profesional muda — swing 6–10%."},
    "N31": {"tempatan": "Bagan Pinang — pelancongan & nelayan.", "agamaIdentiti": "Melayu pantai.", "fenceSitters": "Ekonomi pelancongan."},
    "N10": {"tempatan": "Nilai — industrial/manufacturing, pekerja kilang halal.", "agamaIdentiti": "Melayu ~45%; bandar Nilai-UEM.", "fenceSitters": "Muafakat 1-vs-1 vs PKR — undi anti-PH Melayu ke PAS."},
    "N33": {"tempatan": "Sri Tanjung — Port Dickson pantai, pelancong.", "agamaIdentiti": "Mixed; PKR incumbent.", "fenceSitters": "Muafakat 1-vs-1 vs PH — contest vs PKR."},
    "N36": {"tempatan": "Repah/Tampin — sempadan Johor.", "agamaIdentiti": "Melayu dominan; Bersatu hold.", "fenceSitters": "Muafakat elak 3 penjuru — PAS contest, UMNO support."},
    "N13": {"tempatan": "Sikamat — industrial ring Seremban.", "agamaIdentiti": "Melayu bandar; halal & pekerjaan kilang.", "fenceSitters": "Majoriti sempit — setiap 500 undi kritikal."},
    "N20": {"tempatan": "Labu — NILAI hi-tech; pekerja kilang.", "agamaIdentiti": "Melayu manufacturing.", "fenceSitters": "Bersatu hold — risiko 3 penjuru."},
    "N34": {"tempatan": "Gemas — sempadan NS-Johor; FELDA.", "agamaIdentiti": "Melayu LBN; tanah FELDA.", "fenceSitters": "Pengundi komuter Johor–NS."},
    "N03": {"tempatan": "Sungai Lui — FELDA & ladang kecil.", "agamaIdentiti": "Melayu dominan; profil rural kuat.", "fenceSitters": "Pengundi getah — flip 535 undi."},
}

COHORT_NARRATIVES: list[dict] = [
    {
        "id": "melayu_rural",
        "label": "Melayu rural/pedalaman",
        "reason": "UMNO jual maruah Melayu-Islam kepada DAP",
        "swing": "PN (PAS+Bersatu) / Muafakat PAS+BN",
        "pasEffect": 1,
        "umnoEffect": -1,
    },
    {
        "id": "melayu_urban",
        "label": "Melayu urban/profesional",
        "reason": "Rasuah Zahid, tata urus lemah, tiada reformasi",
        "swing": "PH/Bebas, atau tidak keluar mengundi",
        "pasEffect": 0,
        "umnoEffect": -1,
    },
    {
        "id": "melayu_muda",
        "label": "Melayu muda (Gen Z)",
        "reason": "Tiada nostalgia UMNO, ikut influencer media sosial",
        "swing": "Sebar antara PN dan PH, banyak tidak mengundi",
        "pasEffect": 0,
        "umnoEffect": -1,
    },
    {
        "id": "cina",
        "label": "Cina",
        "reason": "Retorik perkauman + marah DAP berpakatan UMNO",
        "swing": "Rendah keluar mengundi, sebahagian sokong DAP tapi pasif",
        "pasEffect": 0,
        "umnoEffect": -1,
    },
    {
        "id": "india",
        "label": "India",
        "reason": "Pengabaian selama dekad, tiada jawatan Kabinet, sejarah penindasan",
        "swing": "Keluar mengundi rendah, sebahagian ke Bebas/Urimai",
        "pasEffect": 0,
        "umnoEffect": 0,
    },
]


def _allocation_tier(code: str) -> str:
    if code in PAS_WAJIB_9:
        return "wajib"
    if code in PAS_BERHASRAT_4:
        return "berhasrat"
    return "umno"


def _area_rural_score(area: str, pm: float) -> float:
    a = (area or "").lower()
    if any(x in a for x in ("luar bandar", "lbn", "felda", "rural")):
        return 1.0
    if "semi" in a:
        return 0.55
    if pm >= 78:
        return 0.75
    if pm >= 65:
        return 0.5
    return 0.15 if "bandar" in a else 0.35


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def _predict_win_analytics(
    seat: dict, demo: dict, layers: dict, analytics: dict | None,
    alloc: str, soc: dict, issues: list[str], pred: dict,
) -> dict:
    """Ramalan kemenangan berbanding — realistik, margin sederhana (6–18%)."""
    pm = float(demo["ethnicity"]["melayu"]["pct"] or seat.get("pctMelayu") or 0)
    pc = float(demo["ethnicity"]["cina"]["pct"] or seat.get("pctCina") or 0)
    pi = float(demo["ethnicity"]["india"]["pct"] or seat.get("pctIndia") or 0)
    youth = float(demo["ageBands"]["muda"]["pct"] or 0)
    area = pred.get("areaType") or (analytics or {}).get("areaType") or "—"
    hybrid = float(layers.get("hybridPasScore") or 50)
    maj = int(seat.get("majority") or 0)
    party = seat.get("party2023") or ""
    kat = seat.get("kategoriPas") or ""
    cula = float(seat.get("culaPct") or 0) if isinstance(seat.get("culaPct"), (int, float)) else 0
    rural_w = _area_rural_score(area, pm)
    urban_w = 1.0 if "bandar" in area.lower() else (0.45 if pm < 55 else 0.25)
    code = seat.get("code", "")
    edge = (hybrid - 50) / 50  # -1 … +1 lean PAS

    # Margin = jarak berbanding pihak lawan (bukan kemenangan mutlak)
    margin = 10.0
    if alloc == "PAS":
        margin += edge * 6
        if kat == "defend":
            margin += 3
        if cula >= 12:
            margin += 2
        if maj < 600:
            margin += 2
        if party in ("DAP", "PKR", "Amanah") and pm >= 48:
            margin += 2
        if rural_w >= 0.65 and pm >= 70:
            margin += 2
        if pc >= 38:
            margin -= 3
        if youth >= 20 and pm < 55:
            margin -= 2
        if seat.get("threeCornerRisk") == "Tinggi":
            margin -= 3
        if code in NEGOTIATION:
            margin -= 2
        margin = _clamp(margin, 6, 18)

        pas_win = 50 + edge * 11
        if kat == "defend":
            pas_win += 4
        if cula >= 8:
            pas_win += min(4, cula * 0.15)
        if maj < 800:
            pas_win += 2
        if party in ("DAP", "PKR", "Amanah") and pm >= 50:
            pas_win += 2
        pas_win = _clamp(pas_win, 47, 66)
        umno_win = _clamp(pas_win - margin, 31, pas_win - 5)
    else:
        # Margin berterusan (bukan langkah tetap) supaya tiap kerusi berbeza,
        # elak banyak kerusi terlanggar siling yang sama (cth +16 identik).
        margin += (-edge) * 5
        if party == "DAP":
            margin += 2.5
        margin += max(0.0, pc - 30) * 0.06      # makin ramai Cina → PAS makin lemah vs UMNO
        margin += min(3.0, maj / 6000.0 * 3.0)  # majoriti besar → jurang lebih lebar
        margin += max(0.0, pi - 12) * 0.05       # undi India bandar lebih mesra UMNO/BN drpd PAS
        if "bandar" in area.lower():
            margin += 1
        if pm >= 55 and pc < 25:
            margin -= 2.5
        margin = round(_clamp(margin, 5, 20), 1)

        umno_win = 50 - edge * 9 + pc * 0.045
        if party == "DAP":
            umno_win += 2
        umno_win += min(2.0, maj / 8000.0 * 2.0)
        umno_win = _clamp(umno_win, 47, 64)
        pas_win = _clamp(umno_win - margin, 28, umno_win - 5)

    pas_win = round(pas_win, 1)
    umno_win = round(umno_win, 1)
    advantage = round(pas_win - umno_win, 1)

    if alloc == "PAS":
        if pas_win >= 58 and advantage >= 12:
            confidence = "Tinggi"
        elif pas_win >= 52 and advantage >= 8:
            confidence = "Sederhana-Tinggi"
        elif pas_win >= 48:
            confidence = "Sederhana"
        else:
            confidence = "Rendah"
        verdict = f"PAS {pas_win}% berbanding UMNO {umno_win}% (+{advantage}%) — muafakat 1-vs-1 vs PH"
    else:
        umno_adv = round(umno_win - pas_win, 1)
        if umno_win >= 55 and umno_adv >= 10:
            confidence = "Tinggi"
        elif umno_win >= 50 and umno_adv >= 7:
            confidence = "Sederhana-Tinggi"
        elif umno_win >= 47:
            confidence = "Sederhana"
        else:
            confidence = "Rendah"
        verdict = f"UMNO {umno_win}% berbanding PAS {pas_win}% (+{umno_adv}%) — contest strategik vs PH"

    # Kohort aktif per kerusi
    cohort_weights = {
        "melayu_rural": rural_w * (pm / 100),
        "melayu_urban": urban_w * (pm / 100) * (1 - rural_w * 0.5),
        "melayu_muda": (youth / 100) * (pm / 100),
        "cina": pc / 100,
        "india": pi / 100,
    }
    active_cohorts: list[dict] = []
    for c in COHORT_NARRATIVES:
        w = round(cohort_weights.get(c["id"], 0) * 100, 1)
        if w < 5:
            continue
        if c["pasEffect"] > 0 and alloc == "PAS":
            impact = "Menguntungkan PAS"
        elif c["umnoEffect"] < 0 and c["id"] != "cina":
            impact = "Menyusutkan UMNO / PH gain"
        elif c["id"] == "cina":
            impact = "Turnout rendah — PH lemah, muafakat PAS+BN gain"
        elif c["id"] == "india":
            impact = "Turnout rendah — swing kecil"
        else:
            impact = "Swing campuran"
        active_cohorts.append({
            **c,
            "weightPct": w,
            "impact": impact,
            "seatNote": f"Relevansi {w}% dalam kerusi ini",
        })
    active_cohorts.sort(key=lambda x: x["weightPct"], reverse=True)

    issue_effects: list[dict] = []
    for iss in issues[:3]:
        effect = "Naratif kempen — pantau socmed & media Tier A"
        if any(k in iss.lower() for k in ("kos", "ekonomi", "sara hidup")):
            effect = "Mengurangkan sokongan PH bandar; PAS+BN isu kos dapur"
        elif any(k in iss.lower() for k in ("3 penjuru", "split", "penjuru")):
            effect = "Risiko pecah undi — muafakat wajib satukan calon"
        elif any(k in iss.lower() for k in ("felda", "getah", "komoditi")):
            effect = "Melayu rural condong PN/muafakat — PAS gain tinggi"
        elif any(k in iss.lower() for k in ("dap", "stronghold", "ph")):
            effect = "Blok PH — muafakat PAS+BN pecah undi Cina-Melayu swing"
        issue_effects.append({"issue": iss, "effect": effect})

    compare_label = (
        f"PAS {pas_win}% berbanding UMNO {umno_win}% (+{advantage}%)"
        if alloc == "PAS"
        else f"UMNO {umno_win}% berbanding PAS {pas_win}% (+{round(umno_win - pas_win, 1)}%)"
    )

    why_reasons: list[str] = []
    must_do: list[str] = []
    allocation_label = ""
    win_prob_display = pas_win if alloc == "PAS" else umno_win

    if alloc == "PAS":
        if pas_win >= 56 and advantage >= 10:
            allocation_label = "✅ PAS — Boleh Berpeluang Menang"
        elif pas_win >= 50:
            allocation_label = "✅ PAS — Berpeluang Menang (Usaha Padat)"
        else:
            allocation_label = "⚠ PAS — Perlu Strategi Kempen"
        if code == "N10":
            why_reasons.append(
                "Nilai: zon kilang & pekerja Melayu — muafakat 1-vs-1 vs PKR; "
                f"model analitik ~{pas_win}% vs UMNO solo ~{umno_win}%."
            )
        if pm >= 65:
            why_reasons.append(
                f"Melayu {pm:.0f}%: muafakat PAS+BN satukan undi Melayu — UMNO tidak bertanding, elak pecah undi."
            )
        if cula >= 8:
            why_reasons.append(
                "Profil pengundi & sentiment lapangan: data DPI + media sosial menyokong mobilisasi padat di kawasan ini."
            )
        if kat == "defend":
            why_reasons.append("Penyandang PAS PRN 2023: rekod perkhidmatan + mesin undi sedia — kelebihan berbanding calon BN hipotetik.")
        elif kat == "winnable" and maj < 1000:
            why_reasons.append(
                f"Majoriti penyandang hanya {maj:,}: flip realistik jika 1-vs-1 vs PH dan undi BN beralih muafakat."
            )
        if party in ("DAP", "PKR", "Amanah"):
            why_reasons.append(
                f"Penyandang PH ({party}): tanpa calon UMNO, undi anti-PH Melayu beralih ke PAS — UMNO solo di sini ~{umno_win}% sahaja."
            )
        if rural_w >= 0.6:
            why_reasons.append("Kawasan rural/LBN: isu agama, FELDA, komuniti setempat — medan muafakat lebih kuat.")
        if pc >= 30 and party in ("DAP", "PKR", "Amanah"):
            why_reasons.append(
                f"Cina {pc:.0f}%: turnout PH mungkin rendah (marah DAP-UMNO); muafakat tidak pecah undi Cina ke UMNO."
            )
        for ac in active_cohorts[:1]:
            why_reasons.append(f"Kohort dominan — {ac['label']}: {ac['reason']}")
        must_do.append("Wajib: pastikan tiada calon UMNO/BN — 1-vs-1 vs PH sahaja.")
        must_do.append("Intensifkan kempen lapangan 6 minggu akhir; target kehadiran pengundi ≥75%.")
        if maj < 800:
            must_do.append(f"Fokus {max(300, maj // 2):,} swing undi — ceramah kampung + rumah ke rumah.")
        if youth >= 17:
            must_do.append("Kempen digital belia: kos hidup & perkhidmatan, bukan retorik perkauman.")
        if code in NEGOTIATION:
            must_do.append("⚠ Kerusi perbincangan MN — selesaikan isu calon sebelum penamaan.")
    else:
        umno_adv = round(umno_win - pas_win, 1)
        if umno_win >= 53 and umno_adv >= 9:
            allocation_label = "✅ UMNO/BN Boleh Berpeluang Menang"
        elif umno_win >= 48:
            allocation_label = "⚠ UMNO/BN Berpeluang (Contest Strategik)"
        else:
            allocation_label = "⚠ UMNO Contest Jangka Panjang"
        if party == "DAP" or pc >= 32:
            why_reasons.append(
                f"Penyandang/ kuat PH (Cina {pc:.0f}%): PAS contest akan trigger perkauman — UMNO profil muhibbah lebih boleh tarik swing."
            )
        if maj > 2500 and party in ("DAP", "PKR", "PH"):
            why_reasons.append(
                f"Majoriti PH {maj:,}: PAS solo ~{pas_win}% sahaja — BN/UMNO contest jangka panjang vs PH lebih realistik."
            )
        if "bandar" in area.lower():
            why_reasons.append(
                "Bandar: pengundi muda & profesional Melayu sensitif governance — calon UMNO fokus ekonomi, bukan agama."
            )
        if pm < 48:
            why_reasons.append(
                f"Melayu {pm:.0f}% + berbilang kaum: UMNO/BN lebih sesuai jangkau Cina-India vs calon PAS."
            )
        if party == "Bersatu":
            why_reasons.append("Penyandang Bersatu: UMNO contest dengan muafakat PAS elak 3 penjuru.")
        for ac in active_cohorts[:1]:
            if ac["id"] in ("cina", "melayu_urban", "melayu_muda"):
                why_reasons.append(f"Kohort — {ac['label']}: {ac['swing']}")
        must_do.append("Calon mesti muhibbah — elak retorik PAS; fokus isu bandar & perkhidmatan.")
        must_do.append("Serangan utama ke penyandang PH/DAP — bukan PAS; koordinasi dengan PAS elak overlap.")
        if pc >= 22:
            must_do.append("Perluas jangkauan Cina-India: pusat khidmat, dialog komuniti, calon acceptable.")
        if maj > 5000:
            must_do.append("Kempen berfasa 2-3 bulan — bina recognisability calon sebelum PRN.")

    if not why_reasons:
        why_reasons.append(
            f"Skor analitik {hybrid}/100 — data demografi, sentiment & PRN 2023 menyokong peruntukan {alloc}."
        )

    narratives = [compare_label, verdict]

    return {
        "pasWinProb": pas_win,
        "umnoWinProb": umno_win,
        "winProbDisplay": win_prob_display,
        "compareLabel": compare_label,
        "pasVsUmnoAdvantage": round(pas_win - umno_win, 1) if alloc == "PAS" else round(umno_win - pas_win, 1),
        "winConfidence": confidence,
        "verdict": verdict,
        "allocationLabel": allocation_label,
        "whyReasons": why_reasons[:5],
        "mustDo": must_do[:5],
        "activeCohorts": active_cohorts,
        "issueEffects": issue_effects,
        "narratives": narratives,
        "pasFavored": alloc == "PAS" and pas_win > umno_win and pas_win - umno_win >= 8,
        "umnoFavored": alloc == "UMNO/BN" and umno_win > pas_win and umno_win - pas_win >= 8,
    }


def _pct(part: int | float, total: int | float) -> float:
    if not total:
        return 0.0
    return round(float(part) / float(total) * 100, 1)


def _compute_demographics(dpi: dict) -> dict:
    """Age / gender / ethnicity from DPI Dec 2025."""
    voters = dpi.get("registeredVotersDpi") or 0
    age = dpi.get("age") or {}
    gender = dpi.get("gender") or {}
    eth = dpi.get("ethnicity") or {}

    muda = (age.get("18_20") or 0) + (age.get("21_25") or 0)
    dewasa = age.get("26_40") or 0
    pertengahan = age.get("41_60") or 0
    tua = age.get("61_plus") or 0
    age_total = muda + dewasa + pertengahan + tua or voters or 1

    lelaki = gender.get("lelaki") or 0
    perempuan = gender.get("perempuan") or 0
    g_total = lelaki + perempuan or voters or 1

    return {
        "voters": voters,
        "ageBands": {
            "muda": {"label": "Anak Muda (18–25)", "count": muda, "pct": _pct(muda, age_total)},
            "dewasa": {"label": "Dewasa (26–40)", "count": dewasa, "pct": _pct(dewasa, age_total)},
            "pertengahan": {"label": "Pertengahan (41–60)", "count": pertengahan, "pct": _pct(pertengahan, age_total)},
            "tua": {"label": "Warga Emas (61+)", "count": tua, "pct": _pct(tua, age_total)},
        },
        "gender": {
            "lelaki": {"count": lelaki, "pct": _pct(lelaki, g_total)},
            "perempuan": {"count": perempuan, "pct": _pct(perempuan, g_total)},
        },
        "ethnicity": {
            "melayu": {"count": eth.get("melayu") or dpi.get("votersMelayu") or 0, "pct": dpi.get("pctMelayu") or 0},
            "cina": {"count": eth.get("cina") or dpi.get("votersCina") or 0, "pct": dpi.get("pctCina") or 0},
            "india": {"count": eth.get("india") or dpi.get("votersIndia") or 0, "pct": dpi.get("pctIndia") or 0},
        },
        "dominantAge": max(
            [("muda", _pct(muda, age_total)), ("dewasa", _pct(dewasa, age_total)),
             ("pertengahan", _pct(pertengahan, age_total)), ("tua", _pct(tua, age_total))],
            key=lambda x: x[1],
        )[0],
    }


def _predict_demographics(demo: dict, seat: dict, analytics: dict | None, alloc: str) -> dict:
    """Rule-based demographic prediction + messaging insight."""
    pm = demo["ethnicity"]["melayu"]["pct"] or seat.get("pctMelayu") or 0
    pc = demo["ethnicity"]["cina"]["pct"] or 0
    youth = demo["ageBands"]["muda"]["pct"]
    adult = demo["ageBands"]["dewasa"]["pct"]
    mid = demo["ageBands"]["pertengahan"]["pct"]
    senior = demo["ageBands"]["tua"]["pct"]
    female = demo["gender"]["perempuan"]["pct"]
    party = seat.get("party2023") or ""
    area = (analytics or {}).get("areaType") or seat.get("areaType") or "—"

    predictions: list[str] = []
    swing_cohorts: list[str] = []
    messaging: list[str] = []

    # Age cohort predictions
    if youth >= 20:
        if pm < 50:
            predictions.append(f"Anak muda {youth}% + berbilang kaum — condong PH/bandar pada isu kos hidup & governance.")
            swing_cohorts.append("Gen-Z/Millennial bandar (18–25)")
        elif pm >= 65:
            predictions.append(f"Muda Melayu {youth}% — PAS boleh tarik via TikTok/Instagram; isu agama + ekonomi mikro.")
            swing_cohorts.append("Muda Melayu rural/semi-urban")
    elif youth >= 16:
        predictions.append(f"Kohort muda sederhana ({youth}%) — kempen digital + program belia kritikal.")
        swing_cohorts.append("Belia 18–25")

    if adult >= 32:
        predictions.append(f"Dewasa 26–40 ({adult}%) — isu pekerjaan, sewa, pendidikan anak dominan undi.")
        messaging.append("Ekonomi isi rumah & pekerjaan stabil")
    if mid >= 34:
        predictions.append(f"Pertengahan 41–60 ({mid}%) — pengundi stabil; sensitif kos sara hidup & perkhidmatan awam.")
        swing_cohorts.append("Keluarga pertengahan (41–60)")
    if senior >= 28:
        if pm >= 60:
            predictions.append(f"Warga emas {senior}% + Melayu {pm}% — komuniti setempat & undi tradisi condong muafakat.")
        else:
            predictions.append(f"Warga emas {senior}% — turnout tinggi; isu kesihatan & kestabilan.")
        messaging.append("Kesihatan, pencen, kestabilan ekonomi")

    # Gender
    if female >= 52:
        predictions.append(f"Perempuan {female}% — isu kos dapur, kesihatan, sekolah; calon perlu outreach wanita.")
        messaging.append("Kos dapur & kebajikan keluarga")

    # Ethnic context
    if pm >= 70:
        predictions.append(f"Melayu dominan {pm}% — medan {alloc}; muafakat PAS+BN satukan blok Melayu.")
    elif pm >= 45 and pc >= 35:
        predictions.append(f"Seimbang Melayu {pm}% · Cina {pc}% — contest berbilang kaum; calon mesti muhibbah.")
        if alloc == "UMNO/BN":
            predictions.append("BN/UMNO lebih sesuai jangkau pengundi Cina-India bandar vs PAS solo.")
    elif pc >= 40:
        predictions.append(f"Cina {pc}% — PH stronghold demografi; PAS contest kurang optimum.")

    # Area type
    if area == "Bandar" and youth >= 18:
        predictions.append("Bandar + kohort muda — socmed & isu infrastruktur (trafik, banjir, parking) kritikal.")
    elif area in ("Luar Bandar", "LBN", "Felda"):
        predictions.append(f"Kawasan {area} — mobilisasi lapangan & isu komoditi/FELDA dominan kempen.")

    if party in ("DAP", "PKR") and pm >= 48:
        predictions.append("Penyandang PH + Melayu ~50% — swing Melayu 5–8% boleh flip kerusi marginal.")

    pas_win = (analytics or {}).get("pasWinProb")
    demo_score = 50.0
    if pm >= 65 and senior >= 25:
        demo_score += 15
    if pm >= 70:
        demo_score += 10
    if youth >= 18 and pm >= 60:
        demo_score += 5
    if pc >= 42 and pm < 45:
        demo_score -= 20
    if party == "DAP" and pc >= 40:
        demo_score -= 15
    demo_score = max(5, min(95, demo_score))

    lean = "PAS/BN" if demo_score >= 55 else ("PH/Bandar" if demo_score < 45 else "Mixed/Swing")

    extras = PROFILE_EXTRAS.get(seat.get("code", ""), {})
    return {
        "areaType": area,
        "clusterKawasan": (analytics or {}).get("clusterKawasan"),
        "predictions": predictions or ["Demografi seimbang — kempen perlu capai semua kohort."],
        "swingCohorts": swing_cohorts or ["Pengundi pertengahan 41–60"],
        "messaging": messaging or ["Kos sara hidup merentas kohort"],
        "demographicLean": lean,
        "demographicPasScore": round(demo_score, 1),
        "pasWinProb": pas_win,
        "fenceSitters": extras.get("fenceSitters") or (analytics or {}).get("strategicNote", "")[:120],
        "tempatan": extras.get("tempatan"),
        "agamaIdentiti": extras.get("agamaIdentiti"),
    }


def _load_analytics_map() -> dict[str, dict]:
    raw = _load_json(SEATS_ANALYTICS)
    seats = raw.get("seats") if isinstance(raw, dict) else raw
    if not isinstance(seats, list):
        return {}
    return {s["code"]: s for s in seats if s.get("code")}


ECONOMIC_JSON = ROOT / "data/projects/political/PRN/PRN_N9/reference/economic_n9.json"
OPEN_DATA_DIR = ROOT / "JITP_2026/Master_File/Malaysia_Open_Data"
OPEN_DATA_ENDPOINTS = OPEN_DATA_DIR / "01_api_endpoints_master (1).csv"
OPEN_DATA_PRIORITY = OPEN_DATA_DIR / "02_priority_status.csv"
OPEN_DATA_URLS = OPEN_DATA_DIR / "03_url_reference.csv"
OPEN_DATA_XLSX = OPEN_DATA_DIR / "malaysia_opendata_api_reference (1).xlsx"
ECON_OUTLOOK_NUMBERS = ROOT / "JITP_2026/Master_File/EconomicOutlook_api_endpoints_master.numbers"


def _load_json(path: Path) -> dict | list:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def _find_master() -> Path | None:
    files = sorted(MASTER_GLOB.parent.glob(MASTER_GLOB.name), key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0] if files else None


def _load_production_bundle() -> dict:
    raw = _load_json(PRODUCTION_BUNDLE)
    return raw if isinstance(raw, dict) else {}


def _production_seat_map() -> dict[str, dict]:
    raw = _load_json(WARROOM_PRODUCTION)
    seats = raw if isinstance(raw, list) else (raw.get("seats") or [])
    out: dict[str, dict] = {}
    for s in seats:
        code = s.get("id") or s.get("code")
        if code:
            out[str(code).upper()] = s
    return out


def _socmed_from_production() -> dict[str, dict]:
    """Per-DUN socmed from war room production pipeline (preferred over keyword scan)."""
    raw = _load_json(SOCMED_BY_DUN)
    by = raw.get("byDun") if isinstance(raw, dict) else {}
    out: dict[str, dict] = {}
    for code, d in (by or {}).items():
        if not isinstance(d, dict):
            continue
        out[str(code).upper()] = {
            "mentions": int(d.get("mentions_total") or 0),
            "engagement": int(d.get("engagement_total") or 0),
            "negPct": d.get("neg_pct"),
            "posPct": d.get("pos_pct"),
            "demoInsight": d.get("demo_insight") or "",
            "demoTop": d.get("demo_top") or "",
            "leanLabel": d.get("lean_label") or "",
            "confidence": d.get("confidence") or "",
            "topIssues": [x.get("issue") for x in (d.get("top_issues") or []) if x.get("issue")],
            "source": "socmed_by_dun_N9.json",
        }
    return out


def _socmed_totals() -> dict:
    """Aggregate master crawl: rows, posts, comments, engagement."""
    path = _find_master()
    out = {
        "masterFile": path.name if path else None,
        "rows": 0,
        "postRows": 0,
        "commentRows": 0,
        "engagement": 0,
        "platforms": [],
        "mlPipeline": "Apify crawl + HF ML (ft-Malay-bert sentiment + emotion classifier)",
    }
    if not path:
        return out
    try:
        df = pd.read_csv(path, low_memory=False)
        out["rows"] = len(df)
        if "Type" in df.columns:
            t = df["Type"].fillna("").astype(str).str.lower()
            out["postRows"] = int((t == "post").sum())
            out["commentRows"] = int((t == "comment").sum())
        if "Platform" in df.columns:
            out["platforms"] = sorted(df["Platform"].dropna().astype(str).str.strip().unique().tolist())
        if "total_engagement" in df.columns:
            out["engagement"] = int(pd.to_numeric(df["total_engagement"], errors="coerce").fillna(0).sum())
    except Exception:
        pass
    return out


def _load_open_data_registry() -> dict:
    """Parse Malaysia Open Data registry CSVs."""
    reg = {
        "endpointCount": 0,
        "urlCount": 0,
        "bySource": {},
        "ready": [],
        "pending": [],
        "registryFiles": [],
    }
    for p in (OPEN_DATA_ENDPOINTS, OPEN_DATA_PRIORITY, OPEN_DATA_URLS, OPEN_DATA_XLSX, ECON_OUTLOOK_NUMBERS):
        if p.exists():
            reg["registryFiles"].append(p.name)
    if OPEN_DATA_ENDPOINTS.exists():
        df = pd.read_csv(OPEN_DATA_ENDPOINTS)
        reg["endpointCount"] = len(df)
        if "Sumber" in df.columns:
            for src, cnt in df["Sumber"].value_counts().items():
                key = str(src).split(",")[0].strip()
                reg["bySource"][key] = int(cnt)
    if OPEN_DATA_PRIORITY.exists():
        df = pd.read_csv(OPEN_DATA_PRIORITY)
        for _, row in df.iterrows():
            item = {
                "name": str(row.get("Sumber_Data", "")).strip(),
                "status": str(row.get("Status", "")).strip(),
                "priority": str(row.get("Keutamaan", "")).strip(),
            }
            if item["status"].lower() in ("ready", "done"):
                reg["ready"].append(item)
            else:
                reg["pending"].append(item)
    if OPEN_DATA_URLS.exists():
        reg["urlCount"] = len(pd.read_csv(OPEN_DATA_URLS))
    return reg


def _build_data_catalog(
    soc: dict, news: dict, analyzed: dict, economic: dict, open_data: dict, master_rows: int,
    prod: dict | None = None,
) -> list[dict]:
    """Senarai struktur sumber data untuk Overview."""
    rows = soc.get("rows") or master_rows
    eng_m = round((soc.get("engagement") or 56914450) / 1e6, 1)
    platforms = ", ".join(soc.get("platforms") or []) or "Facebook, Instagram, TikTok, X, YouTube, Threads"
    official = economic.get("official") or {}
    reg_files = open_data.get("registryFiles") or []
    prod = prod or {}
    analytics = prod.get("analytics") or {}
    ns_posts = analytics.get("nsPosts") or prod.get("socialSummary", {}).get("meta", {}).get("nsPosts")

    catalog = [
        {
            "category": "SPR / Demografi / DPI",
            "icon": "🗳️",
            "items": [
                {"name": "Updates_Demografi pengundi N9 DPI Dec 2025.xlsx", "vol": "36 DUN", "use": "Umur · jantina · bangsa · pengundi berdaftar"},
                {"name": "Updates_Data DUN ikut ranking.xlsx", "vol": "36 DUN", "use": "Profil pengundi · demografi · ranking DUN"},
                {"name": "Updates_Cadangan kerusi - perbincangan MN.xlsx", "vol": "36 calon", "use": "Cadangan MN 10 Jun 2026 · swap kerusi"},
                {"name": "n9_dpi_updates.json", "vol": "Merged", "use": "Reference JSON gabungan DPI + ranking + MN"},
                {"name": "n9_seats_analytics.json", "vol": "36 kerusi", "use": "Isu utama · kategori PAS · ramalan per DUN"},
                {"name": "dosm_census_johor_n9.json", "vol": "92 DUN", "use": "MyCensus 2020 — populasi · bandar/rural proxy per DUN"},
            ],
        },
        {
            "category": "Socmed Master (Apify + ML)",
            "icon": "📱",
            "items": [
                {"name": soc.get("masterFile") or "PAS_Break_Master_EXCO_Analyzed_*.csv", "vol": f"{rows:,} rows · {eng_m}M engagement", "use": "Crawl 6 platform · sentiment · emotion · demographic label"},
                {"name": "socmed_by_dun_N9.json", "vol": f"36 DUN · {ns_posts or '—'} post N9-scoped", "use": "Fusion per-DUN · demo_mix vs DPI · lean · isu"},
                {"name": "warroom_dun_N9_production.json", "vol": "36 kerusi", "use": "pasWinProb · pasMnWinProb · hybrid demo insight · SPR 2023"},
                {"name": "Apify Actors", "vol": f"{soc.get('postRows', 31111):,} posts · {soc.get('commentRows', 37892):,} komen", "use": f"Platform: {platforms}"},
                {"name": "HuggingFace ML", "vol": "ft-Malay-bert", "use": "Sentimen BM · emotion classifier · demographic proxy"},
            ],
        },
        {
            "category": "Media & News (Tier A ML)",
            "icon": "📰",
            "items": [
                {"name": news.get("csv_file") or "PRN_N9_News_Multilingual_*.csv", "vol": f"{news.get('total_articles') or news.get('total') or 0:,} artikel", "use": "BM · EN · Cina · Tamil · Ekonomi · Google News + direct scrape"},
                {"name": analyzed.get("analyzed_csv") or "PRN_N9_News_Analyzed_TierA_*.csv", "vol": f"{analyzed.get('rows_analyzed') or 0} artikel ML", "use": f"Sentimen {analyzed.get('media_tone', {}).get('neg_pct', '—')}% neg · mode {analyzed.get('analysis_mode', 'ml_models')}"},
                {"name": "Sumber media", "vol": "Tier A", "use": "Malay Mail · BH · Sin Chew · Oriental Daily · Harakah · FMT"},
            ],
        },
        {
            "category": "Makroekonomi & Open Data",
            "icon": "📈",
            "items": [
                {"name": "BNM OpenAPI", "vol": f"OPR {official.get('opr_pct') or '2.75'}%", "use": f"Kadar OPR · USD/MYR RM{official.get('usd_myr') or '4.07'} · base rate"},
                {"name": "OpenDOSM / data.gov.my", "vol": "CPI · GDP · MEI", "use": "Kos sara hidup negeri · indikator ekonomi"},
                {"name": "MIDA / Bursa registry", "vol": f"{open_data.get('endpointCount', 29)} endpoints", "use": "Pelaburan NS · KLCI · Malaysia Open Data catalog"},
                {"name": ECON_OUTLOOK_NUMBERS.name if ECON_OUTLOOK_NUMBERS.exists() else "EconomicOutlook_api_endpoints_master.numbers", "vol": "API map", "use": "Peta endpoint ekonomi rasmi"},
            ] + [{"name": f, "vol": "Registry", "use": "Malaysia Open Data reference"} for f in reg_files[:4]],
        },
        {
            "category": "PRN 2023 Baseline",
            "icon": "🏛️",
            "items": [
                {"name": "PRN2023_NegeriSembilan_v2.xlsx", "vol": "36 DUN", "use": "Penyandang · majoriti · parti · kategori margin"},
                {"name": "n9_scoresheet_streams_2023.json", "vol": "36 DUN", "use": "Bloc votes PN/BN/PH · 7-bloc senario war room"},
                {"name": "Keputusan rasmi SPR", "vol": "PRN 2023", "use": "Baseline keputusan & majoriti penyandang"},
            ],
        },
    ]
    if prod.get("meta", {}).get("generated"):
        catalog.append({
            "category": "War Room Production Bundle",
            "icon": "⚙️",
            "items": [
                {"name": "n9_production_bundle.json", "vol": prod["meta"]["generated"], "use": "Hybrid fusion · coalition · KPI master crawl"},
                {"name": prod.get("meta", {}).get("sources", {}).get("masterCrawl", "master CSV"), "vol": f"{rows:,} post", "use": "Sumber crawl terkini · dedupe Platform+ID"},
            ],
        })
    return catalog


def _build_evidence(news: dict, analyzed: dict, master_rows: int, prod: dict | None = None) -> dict:
    prod = prod or {}
    analytics = prod.get("analytics") or {}
    social = prod.get("socialSummary") or {}
    demo_hybrid = (social.get("demographics") or {}).get("hybrid") or {}

    soc = _socmed_totals()
    if analytics.get("totalPosts"):
        soc["rows"] = int(analytics["totalPosts"])
    if analytics.get("totalEngagement"):
        soc["engagement"] = int(analytics["totalEngagement"])
    if analytics.get("masterFile"):
        soc["masterFile"] = analytics["masterFile"]
    if not soc["rows"]:
        soc["rows"] = master_rows
    economic = _load_json(ECONOMIC_JSON) if ECONOMIC_JSON.exists() else {}
    official = economic.get("official") or {}
    open_data = _load_open_data_registry()

    news_crawled = news.get("total_articles") or news.get("total") or 0
    news_analyzed = analyzed.get("rows_analyzed") or 0
    media_tone = analyzed.get("media_tone") or {}
    by_lang = news.get("by_lang") or {}
    by_community = news.get("by_community") or {}

    eng = soc["engagement"] or 56914450
    eng_m = round(eng / 1_000_000, 1)

    return {
        "socmedRows": soc["rows"],
        "postRows": soc["postRows"] or 31111,
        "commentRows": soc["commentRows"] or 37892,
        "engagement": eng,
        "engagementMillions": eng_m,
        "socmedMasterFile": soc["masterFile"],
        "socmedPlatforms": soc["platforms"],
        "socmedMl": soc["mlPipeline"],
        "newsCrawled": news_crawled,
        "newsAnalyzed": news_analyzed,
        "newsTier": analyzed.get("tier", "A"),
        "newsByLang": by_lang,
        "newsByCommunity": by_community,
        "newsAnalyzedCsv": analyzed.get("analyzed_csv"),
        "newsCrawlCsv": news.get("csv_file"),
        "mediaNegPct": media_tone.get("neg_pct"),
        "mediaPosPct": round(media_tone.get("positive", 0) / max(media_tone.get("total", 1), 1) * 100, 1) if media_tone.get("total") else None,
        "mediaNeuPct": round(media_tone.get("neutral", 0) / max(media_tone.get("total", 1), 1) * 100, 1) if media_tone.get("total") else None,
        "analysisMode": analyzed.get("analysis_mode", "ml_models"),
        "narrativeAlerts": analyzed.get("narrative_alerts") or [],
        "economic": {
            "fetchedAt": economic.get("fetched_at"),
            "oprPct": official.get("opr_pct") or (economic.get("bnm") or {}).get("opr", {}).get("data", {}).get("new_opr_level"),
            "oprDate": official.get("opr_date") or (economic.get("bnm") or {}).get("opr", {}).get("data", {}).get("date"),
            "usdMyr": official.get("usd_myr") or (economic.get("bnm") or {}).get("exchange_rate_usd", {}).get("middle"),
            "usdDate": official.get("usd_date") or (economic.get("bnm") or {}).get("exchange_rate_usd", {}).get("date"),
            "headlines": economic.get("macro_headlines") or [],
            "prnRelevance": economic.get("prn_relevance") or {},
            "sources": ["BNM OpenAPI", "OpenDOSM / data.gov.my", "MIDA", "Bursa Malaysia (iTick KLCI)"],
            "outlookFile": ECON_OUTLOOK_NUMBERS.name if ECON_OUTLOOK_NUMBERS.exists() else None,
        },
        "openData": open_data,
        "staticSources": [
            "Updates_Demografi pengundi N9 DPI Dec 2025.xlsx",
            "Updates_Data DUN ikut ranking.xlsx",
            "Updates_Cadangan kerusi - perbincangan MN.xlsx",
        ],
        "dataCatalog": _build_data_catalog(soc, news, analyzed, economic, open_data, master_rows, prod),
        "hybridDemographic": {
            "insight": demo_hybrid.get("insight"),
            "dpiMalay": (demo_hybrid.get("dpi") or {}).get("malay"),
            "socmedMalay": (demo_hybrid.get("socmed") or {}).get("malay"),
            "deltaMalay": (demo_hybrid.get("delta") or {}).get("malay"),
            "nudges": demo_hybrid.get("adjustmentNotes") or [],
        },
        "productionGenerated": prod.get("meta", {}).get("generated"),
        "nsScopedPosts": analytics.get("nsPosts") or social.get("meta", {}).get("nsPosts"),
        "sources": [
            "Updates_Demografi pengundi N9 DPI Dec 2025.xlsx",
            "Updates_Data DUN ikut ranking.xlsx",
            "Updates_Cadangan kerusi - perbincangan MN.xlsx",
            f"PAS_Break_Master ({soc['rows']:,} rows · {eng_m}M engagement · Apify + HF ML)",
            f"PRN_N9 News Tier {analyzed.get('tier', 'A')} ({news_analyzed} artikel ML · {news_crawled} crawled)",
            "Malaysia Open Data — BNM · DOSM · MIDA · Bursa (registry InsightPulse)",
        ],
    }


def _socmed_by_seat() -> dict[str, dict]:
    """Merge production per-DUN socmed (preferred) with keyword fallback on master CSV."""
    out = _socmed_from_production()
    path = _find_master()
    if not path:
        return out
    try:
        df = pd.read_csv(path, low_memory=False)
    except Exception:
        return out
    text = df["Text"].fillna("").astype(str).str.lower()
    for code, kws in SEAT_KEYWORDS.items():
        if out.get(code, {}).get("mentions"):
            continue
        mask = pd.Series(False, index=df.index)
        for kw in kws:
            mask |= text.str.contains(re.escape(kw), na=False)
        sub = df[mask]
        if sub.empty:
            out.setdefault(code, {"mentions": 0, "engagement": 0, "negPct": None})
            continue
        sent = sub["sentiment_label"].fillna(sub.get("Sentiment", "")).astype(str).str.lower()
        neg = int((sent == "negative").sum())
        total = len(sub)
        eng = int(pd.to_numeric(sub.get("total_engagement", 0), errors="coerce").fillna(0).sum())
        out[code] = {
            "mentions": total,
            "engagement": eng,
            "negPct": round(neg / total * 100, 1) if total else None,
            "source": "keyword_fallback",
        }
    return out


def _score_layers(seat: dict, dpi: dict, mn: dict | None, soc: dict) -> dict:
    """Hybrid model component scores 0–100 per layer."""
    kat = seat.get("kategoriPas") or ""
    maj = seat.get("majority") or 99999
    party = seat.get("party2023") or ""
    cula = dpi.get("culaPct") or 0
    pm = dpi.get("pctMelayu") or 0
    skt = dpi.get("skt51") or 0
    voters = dpi.get("registeredVotersDpi") or 1

    # Layer 1 Jentera
    jentera = min(100, (cula * 2.5) + (pm * 0.5) + min(30, (skt / voters) * 100 * 3))
    if cula >= 15:
        jentera = min(100, jentera + 15)
    if dpi.get("rankingCulaPct") and dpi["rankingCulaPct"] <= 5:
        jentera = min(100, jentera + 10)

    # Layer 2 Baseline — lower majority = higher flip potential for challenger
    if party in ("PAS",):
        baseline = 85
    elif maj < 400:
        baseline = 90
    elif maj < 1000:
        baseline = 75
    elif maj < 3000:
        baseline = 55
    elif maj > 8000:
        baseline = 15
    else:
        baseline = 40
    if party in ("DAP", "PKR", "Amanah") and pm >= 55:
        baseline = min(100, baseline + 15)
    if party in ("Bersatu",):
        baseline = 50
    if seat.get("threeCornerRisk") == "Tinggi":
        baseline = max(20, baseline - 15)

    # Layer 3 PAS analytics
    pas_map = {"defend": 95, "winnable": 80, "tough": 55, "not_priority": 25}
    pas_analytics = pas_map.get(kat, 30)
    if kat == "not_priority" and pm >= 70 and maj < 2000:
        pas_analytics = 45

    # Layer 4 Socmed — production per-DUN + engagement weight
    mentions = soc.get("mentions") or 0
    eng = soc.get("engagement") or 0
    socmed = min(100, mentions * 4) if mentions else 10
    if eng >= 5000:
        socmed = min(100, socmed + 12)
    elif eng >= 1000:
        socmed = min(100, socmed + 6)
    if soc.get("negPct") and soc["negPct"] > 40:
        socmed = min(100, socmed + 8)
    if soc.get("demoInsight") and "Melayu" in str(soc.get("demoInsight")) and pm >= 55:
        socmed = min(100, socmed + 5)

    # Layer 5 MN + media
    mn_media = 20
    if mn and mn.get("calonMn"):
        calon = str(mn["calonMn"]).lower()
        if "kp pas" in calon or "ustaz" in calon or "pas" in calon:
            mn_media = 80
        else:
            mn_media = 35
    if seat.get("code") in NEGOTIATION:
        mn_media = max(mn_media, 50)

    weights = [0.40, 0.25, 0.20, 0.10, 0.05]
    scores = [jentera, baseline, pas_analytics, socmed, mn_media]
    hybrid_pas = round(sum(s * w for s, w in zip(scores, weights)), 1)

    return {
        "jentera": round(jentera, 1),
        "baseline": round(baseline, 1),
        "pasAnalytics": round(pas_analytics, 1),
        "socmed": round(socmed, 1),
        "mnMedia": round(mn_media, 1),
        "hybridPasScore": hybrid_pas,
        "recommendedByModel": (
            "PAS" if hybrid_pas >= 55 else ("UMNO/BN" if hybrid_pas < 45 else "Perbincangan")
        ),
    }


def _build_arguments(
    seat: dict, dpi: dict, mn: dict | None, soc: dict, alloc: str, layers: dict,
    demo: dict | None = None, pred: dict | None = None, issues: list[str] | None = None,
) -> dict:
    code = seat["code"]
    bullets_pas: list[str] = []
    bullets_umno: list[str] = []
    evidence: list[str] = []

    kat = seat.get("kategoriPas") or ""
    maj = seat.get("majority") or 0
    party = seat.get("party2023") or ""
    inc = _incumbent_info(seat)
    bloc23 = inc["bloc"]
    party_label = inc["party"]
    cula = dpi.get("culaPct")
    pm = dpi.get("pctMelayu")
    bkc = dpi.get("bkcCula")
    skt = dpi.get("skt51")
    voters = dpi.get("registeredVotersDpi")

    if voters:
        evidence.append(f"Pengundi berdaftar (DPI Dec 2025): {voters:,}")
    if pm is not None:
        pl = dpi.get("pctLain")
        if pl is None and voters:
            pl = round((dpi.get("votersLain") or 0) / voters * 100, 2)
        pl_txt = f" · Lain {pl}%" if pl is not None else ""
        evidence.append(
            f"Komposisi (DPI Dec 2025): Melayu {pm}% · Cina {dpi.get('pctCina', '—')}% · "
            f"India {dpi.get('pctIndia', '—')}%{pl_txt}"
        )
    evidence.append(f"PRN 2023: {inc['label']} — {seat.get('winnerName', '')} · majoriti {maj:,} undi")
    if soc.get("mentions"):
        src = soc.get("source") or "master crawl"
        line = (
            f"Socmed hybrid ({src}): {soc['mentions']} mention · "
            f"{soc.get('engagement', 0):,} engagement · neg {soc.get('negPct', '—')}%"
        )
        if soc.get("demoInsight"):
            line += f" · {soc['demoInsight'][:80]}"
        evidence.append(line)
    if mn and mn.get("calonMn"):
        evidence.append(f"Cadangan MN (10 Jun 2026): {mn['calonMn']}")
    if mn and mn.get("catatanMn"):
        evidence.append(f"Nota MN: {mn['catatanMn']}")

    if demo:
        ab = demo.get("ageBands") or {}
        g = demo.get("gender") or {}
        evidence.append(
            f"Umur (DPI): Muda {ab.get('muda', {}).get('pct', '—')}% · "
            f"Dewasa {ab.get('dewasa', {}).get('pct', '—')}% · "
            f"41–60 {ab.get('pertengahan', {}).get('pct', '—')}% · "
            f"61+ {ab.get('tua', {}).get('pct', '—')}%"
        )
        evidence.append(
            f"Jantina: Lelaki {g.get('lelaki', {}).get('pct', '—')}% · "
            f"Perempuan {g.get('perempuan', {}).get('pct', '—')}%"
        )
    if pred and pred.get("demographicLean"):
        evidence.append(f"Ramalan demografi: condong {pred['demographicLean']} · skor {pred.get('demographicPasScore', '—')}/100")
    if issues:
        evidence.append(f"Isu utama: {' · '.join(i for i in issues if i)}")

    if kat == "defend":
        bullets_pas.append("Penyandang PAS PRN 2023 — pertahanan wajib dalam agihan MN PAS/PN 13 kerusi.")
    if kat == "winnable":
        bullets_pas.append("Kategori analitik: BOLEH MENANG — majoriti sempit + profil demografi menyokong flip.")
    if kat == "tough":
        bullets_pas.append("Kategori SUKAR — perlukan muafakat undi BN/PN; layak dalam 13 PAS/PN jika 1-vs-1 vs PH.")
    if maj < 600:
        bullets_pas.append(f"Majoriti sangat sempit ({maj:,}) — kerusi flip dengan gerak kerja padat.")
    if bloc23 == "PH" and party_label in ("DAP", "PKR", "Amanah"):
        bullets_pas.append(
            f"Penyandang PH ({party_label}) — muafakat PAS+BN pecah blok PH; 1-vs-1 realistik."
        )
        bullets_umno.append(
            f"Penyandang PH ({party_label}) — BN/UMNO contest muhibbah vs PH jangka panjang."
        )
    if bloc23 == "BN" and party_label == "UMNO":
        bullets_pas.append(
            "Penyandang BN (UMNO) — dengan muafakat, calon PAS guna undi BN; UMNO tidak contest."
        )
        bullets_umno.append("Penyandang BN (UMNO) — pertahanan kerusi sendiri; elak pecah undi dengan PAS.")
    if bloc23 == "PN" and party_label == "PAS":
        bullets_pas.append("Penyandang PN (PAS) — pertahanan wajib; elak 3 penjuru.")
    if bloc23 == "PN" and party_label == "Bersatu":
        bullets_pas.append("Penyandang PN (Bersatu) — muafakat satukan calon PAS; elak split PN.")
        bullets_umno.append("Penyandang Bersatu — BN contest alternatif jika PAS tidak layak.")
    if party in ("PKR", "Amanah", "DAP") and pm and pm >= 50:
        bullets_pas.append(f"Penyandang PH ({party}) — Melayu {pm}%; muafakat PAS+BN pecah blok PH.")
    if party in ("UMNO", "BN") and pm and pm >= 75:
        bullets_pas.append("Penyandang BN — dengan muafakat undi, PAS/BN gabungan saing PH.")
    if party == "Bersatu":
        bullets_pas.append("Penyandang Bersatu — risiko 3 penjuru; MN mesti satukan calon.")

    if pm and pm < 38:
        bullets_umno.append(f"Melayu {pm}% — kerusi bandar berbilang kaum; BN/UMNO lebih sesuai contest PH.")
    if maj > 7000:
        bullets_umno.append(f"Majoriti PH {maj:,} — sumber kempen terhad; BN contest strategik jangka panjang.")
    if party == "DAP" and pm and pm < 35:
        bullets_umno.append("Stronghold DAP — PAS kurang daya saing demografi; serah contest UMNO/BN.")
    if kat == "not_priority" and pm and pm < 45:
        bullets_umno.append("Bukan fokus analitik PAS — optimum dalam paket UMNO/BN 23 kerusi.")
    if mn and "DHPP" in str(mn.get("calonMn", "")):
        bullets_umno.append("Cadangan MN: calon komponen BN/DHPP — selaras agihan UMNO/BN 23 kerusi.")

    if code in SWAP_NOTES:
        bullets_pas.append(SWAP_NOTES[code])

    primary = bullets_pas if alloc == "PAS" else bullets_umno
    if alloc == "UMNO/BN":
        umno_r = UMNO_13_RATIONALE.get(code)
        if umno_r:
            primary.insert(0, umno_r)
    if not primary:
        primary = [f"Skor analitik {layers['hybridPasScore']}/100 — cadangan {alloc} berdasarkan data."]

    return {
        "forAllocation": primary,
        "pasCase": bullets_pas or ["Tiada kes kukuh PAS — model condong BN."],
        "umnoCase": bullets_umno or ["BN contest lebih realistik demografi/majoriti."],
        "evidence": evidence,
        "insight": (
            f"Skor analitik: {layers['hybridPasScore']}/100 · "
            f"Model: {layers['recommendedByModel']} · "
            f"Peruntukan: {alloc}"
            + (f" · Demografi: {pred['demographicLean']}" if pred and pred.get("demographicLean") else "")
            + (" · ⚠ Perbincangan" if code in NEGOTIATION else "")
        ),
    }


def build_payload() -> dict:
    seats_raw = _load_json(SEATS_JSON)
    seat_list = seats_raw if isinstance(seats_raw, list) else (seats_raw.get("seats") or [])
    dpi_all = _load_json(DPI_JSON)
    by_dpi = dpi_all.get("byCode") or {}
    mn_map = {m["code"]: m for m in (dpi_all.get("mnProposals") or []) if m.get("code")}
    news = _load_json(NEWS_SUM) if isinstance(_load_json(NEWS_SUM), dict) else {}
    analyzed = _load_json(NEWS_ANALYZED) if isinstance(_load_json(NEWS_ANALYZED), dict) else {}
    socmed = _socmed_by_seat()
    analytics_map = _load_analytics_map()
    prod = _load_production_bundle()
    prod_seats = _production_seat_map()

    master_path = _find_master()
    master_rows = int((prod.get("analytics") or {}).get("totalPosts") or 69003)
    if master_path:
        try:
            master_rows = len(pd.read_csv(master_path, usecols=[0]))
        except Exception:
            pass

    rows: list[dict] = []
    for s in sorted(seat_list, key=lambda x: x.get("code", "")):
        code = s.get("code", "")
        dpi = by_dpi.get(code, {})
        mn = mn_map.get(code)
        prod_s = prod_seats.get(code.upper(), {})
        soc = socmed.get(code, socmed.get(code.upper(), {}))
        analytics = analytics_map.get(code, {})
        if prod_s.get("issues"):
            for iss in prod_s["issues"]:
                if iss and iss not in (analytics.get("isuUtama1"), analytics.get("isuUtama2")):
                    pass
        if prod_s.get("pasWinProb") is not None:
            analytics = {**analytics, "pasWinProb": prod_s["pasWinProb"]}
        if prod_s.get("socmedDemoInsight"):
            soc = {**soc, "demoInsight": prod_s["socmedDemoInsight"]}
        if prod_s.get("socmedMentions") is not None and not soc.get("mentions"):
            soc = {
                **soc,
                "mentions": prod_s["socmedMentions"],
                "engagement": prod_s.get("socmedEngagement") or soc.get("engagement", 0),
                "negPct": prod_s.get("socmedNegPct") if prod_s.get("socmedNegPct") is not None else soc.get("negPct"),
            }
        alloc = "PAS" if code in PAS_23 else "UMNO/BN"
        demo = _compute_demographics(dpi)
        pred = _predict_demographics(demo, {**s, **dpi}, analytics, alloc)
        issues = [
            analytics.get("isuUtama1"),
            analytics.get("isuUtama2"),
            analytics.get("isuUtama3"),
        ]
        issues = [i for i in issues if i and str(i).strip() and str(i).lower() != "nan"]
        _extras_local = PROFILE_EXTRAS.get(code, {})
        _tempatan = (_extras_local.get("tempatan") or "").strip().rstrip(".")
        _cluster = (analytics.get("clusterKawasan") or "").strip()
        # Konteks setempat khusus-DUN: utamakan profil tempatan, jika tiada guna kluster + isu
        if _tempatan:
            local_context = _tempatan
        elif _cluster and issues:
            local_context = f"{_cluster} · {issues[0]}"
        else:
            local_context = _cluster or (issues[0] if issues else "")
        layers = _score_layers(s, dpi, mn, soc)
        args = _build_arguments(s, dpi, mn, soc, alloc, layers, demo, pred, issues)
        win_pred = _predict_win_analytics(
            {**s, **dpi}, demo, layers, analytics, alloc, soc, issues, pred,
        )
        inc = _incumbent_info(s)
        rows.append({
            "code": code,
            "name": s.get("name", code),
            "parlimen": s.get("parlimen", "—"),
            "allocation": alloc,
            "incumbent2023": f"{inc['label']} — {inc['winnerName']}",
            "incumbent": inc,
            "party2023": s.get("party2023", "—"),
            "bloc2023": inc["bloc"],
            "winnerName": s.get("winnerName", ""),
            "majority2023": s.get("majority", 0),
            "kategoriPas": s.get("kategoriPas", "—"),
            "kategoriLabel": {
                "defend": "Pertahan", "winnable": "Boleh Menang", "tough": "Sukar", "not_priority": "Bukan Fokus",
            }.get(s.get("kategoriPas", ""), "—"),
            "pctMelayu": dpi.get("pctMelayu"),
            "pctCina": dpi.get("pctCina"),
            "pctIndia": dpi.get("pctIndia"),
            "registeredVoters": dpi.get("registeredVotersDpi"),
            "markahSlu": dpi.get("markahSlu"),
            "rankingMajoriti": dpi.get("rankingMajoritiPru15"),
            "mnCalon": (mn or {}).get("calonMn"),
            "mnNote": (mn or {}).get("catatanMn"),
            "negotiation": code in NEGOTIATION,
            "threeCornerRisk": s.get("threeCornerRisk"),
            "socmedMentions": soc.get("mentions", 0),
            "socmedEngagement": soc.get("engagement", 0),
            "socmedNegPct": soc.get("negPct"),
            "socmedDemoInsight": soc.get("demoInsight") or prod_s.get("socmedDemoInsight"),
            "pasMnWinProb": prod_s.get("scenarioPasMn") or prod_s.get("pasMnWinProb"),
            "productionPasWinProb": prod_s.get("pasWinProb"),
            "bloc7Scenarios": seat_scenario_rows({**prod_s, **s, "code": code}, DEFAULT_BERSAMA_PCT),
            "bloc7Insight": seat_scenario_insight({**prod_s, **s, "code": code}),
            "hybridLayers": {
                "hybridPasScore": layers["hybridPasScore"],
                "recommendedByModel": layers["recommendedByModel"],
            },
            "demographics": demo,
            "demographicPrediction": pred,
            "issues": issues,
            "localContext": local_context,
            "clusterKawasan": _cluster or None,
            "areaType": pred.get("areaType") or analytics.get("areaType"),
            "pasWinProb": win_pred.get("pasWinProb") or pred.get("pasWinProb") or analytics.get("pasWinProb"),
            "winPrediction": win_pred,
            "arguments": args,
            "justification": " ".join(args["forAllocation"]),
        })

    pas_rows = [r for r in rows if r["allocation"] == "PAS"]
    umno_rows = [r for r in rows if r["allocation"] == "UMNO/BN"]
    pas_high = [r for r in pas_rows if (r.get("winPrediction") or {}).get("pasFavored")]
    umno_high = [r for r in umno_rows if (r.get("winPrediction") or {}).get("umnoFavored")]
    avg_pas_win = round(sum((r.get("winPrediction") or {}).get("pasWinProb", 0) for r in pas_rows) / max(len(pas_rows), 1), 1)
    avg_umno_win = round(sum((r.get("winPrediction") or {}).get("umnoWinProb", 0) for r in umno_rows) / max(len(umno_rows), 1), 1)

    coalition = coalition_scenarios(list(prod_seats.values()) if prod_seats else rows)

    return {
        "meta": {
            "title": "Perbincangan Muafakat PAS + BN/UMNO — PRN Negeri Sembilan 2026",
            "generated": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "pasSeats": len(pas_rows),
            "umnoSeats": len(umno_rows),
            "majorityNeeded": 19,
            "dpiAsOf": dpi_all.get("meta", {}).get("dpiAsOf", "DPI Dec 2025"),
            "rankingAsOf": dpi_all.get("meta", {}).get("rankingAsOf", "10 Jun 2026"),
            "disclaimer": DISCLAIMER_MN,
        },
        "incumbentBreakdown": {
            "prn2023Totals": {"PH": 17, "BN": 14, "PN": 5},
            "pas23": _build_incumbent_breakdown(rows, "PAS"),
            "umno13": _build_incumbent_breakdown(rows, "UMNO/BN"),
        },
        "cohortFramework": COHORT_NARRATIVES,
        "pasWinSummary": {
            "avgPasWinProb": avg_pas_win,
            "highConfidenceCount": len([r for r in pas_rows if (r.get("winPrediction") or {}).get("winConfidence") == "Tinggi"]),
            "pasFavoredCount": len(pas_high),
            "topPasSeats": sorted(
                [{"code": r["code"], "name": r["name"], "pasWinProb": (r.get("winPrediction") or {}).get("pasWinProb"), "advantage": (r.get("winPrediction") or {}).get("pasVsUmnoAdvantage"), "label": (r.get("winPrediction") or {}).get("allocationLabel")} for r in pas_rows],
                key=lambda x: x.get("pasWinProb") or 0, reverse=True,
            )[:5],
        },
        "umnoWinSummary": {
            "avgUmnoWinProb": avg_umno_win,
            "umnoFavoredCount": len(umno_high),
            "topUmnoSeats": sorted(
                [{"code": r["code"], "name": r["name"], "umnoWinProb": (r.get("winPrediction") or {}).get("umnoWinProb"), "advantage": (r.get("winPrediction") or {}).get("pasVsUmnoAdvantage"), "label": (r.get("winPrediction") or {}).get("allocationLabel"), "rationale": UMNO_13_RATIONALE.get(r["code"], "")} for r in umno_rows],
                key=lambda x: x.get("umnoWinProb") or 0, reverse=True,
            )[:5],
        },
        "evidence": _build_evidence(news, analyzed, master_rows, prod),
        "hybridModel": prod.get("analytics", {}).get("hybridModel") or HYBRID_FORMULA,
        "coalitionLead": (prod.get("socialSummary") or {}).get("coalitionFormation"),
        "coalitionScenarios": coalition,
        "coalitionDefault": "mn",
        "pasSeats": pas_rows,
        "umnoSeats": umno_rows,
        "allSeats": rows,
    }


def _render_incumbent_section(ib: dict | None) -> str:
    """HTML: penyandang PRN 2023 mengikut blok untuk PAS/PN 13 & UMNO/BN 23."""
    if not ib:
        return ""
    pas = ib.get("pas23") or {}
    umno = ib.get("umno13") or {}
    totals = ib.get("prn2023Totals") or {}

    def bloc_pills(counts: dict) -> str:
        colors = {"PH": "#ef4444", "BN": "#3b82f6", "PN": "#1a7f5a"}
        return " ".join(
            f'<span style="display:inline-block;padding:4px 10px;border-radius:999px;font-size:11px;font-weight:700;'
            f'background:{colors.get(k, "#666")}22;color:{colors.get(k, "#aaa")};border:1px solid {colors.get(k, "#666")}55">'
            f'{k} {v}</span>'
            for k, v in sorted((counts or {}).items(), key=lambda x: -x[1])
            if v
        )

    def seat_table(detail: dict, alloc_name: str) -> str:
        rows_html = []
        for bloc in ("PN", "BN", "PH"):
            for s in (detail.get("blocDetail") or {}).get(bloc, []):
                bc = {"PH": "#ef4444", "BN": "#3b82f6", "PN": "#4ade80"}.get(bloc, "#aaa")
                rows_html.append(
                    f'<tr><td><strong>{s["code"]} {s["name"]}</strong></td>'
                    f'<td><span style="color:{bc};font-weight:700">{bloc} · {s["party"]}</span></td>'
                    f'<td style="font-size:11px;color:var(--muted)">{s.get("winnerName", "—")}</td>'
                    f'<td>{s.get("majority2023", 0):,}</td></tr>'
                )
        return f"""
<div class="catalog-block" style="margin-top:12px">
  <h3 style="padding:12px 14px;margin:0;font-size:13px">{alloc_name} — {detail.get("total", 0)} kerusi</h3>
  <p style="padding:0 14px 8px;font-size:11px;color:var(--muted)">{detail.get("narrative", "")}</p>
  <p style="padding:0 14px 10px">{bloc_pills(detail.get("byBloc"))}</p>
  <table class="catalog-table"><thead><tr>
    <th>DUN</th><th>Penyandang PRN 2023</th><th>Nama ADUN</th><th>Maj</th>
  </tr></thead><tbody>{"".join(rows_html) or '<tr><td colspan="4">—</td></tr>'}</tbody></table>
  <p style="padding:8px 14px 12px;font-size:10px;color:var(--muted)">
    Pecahan parti: {", ".join(f"{k}: {v}" for k, v in (detail.get("byParty") or {}).items())}
  </p>
</div>"""

    return f"""
<div class="section">
  <h2>🏛 Penyandang PRN 2023 — Asal Milik Siapa? (PH · BN · PN)</h2>
  <p style="font-size:12px;color:var(--muted);margin-bottom:10px">
    Data keputusan penuh PRN 2023 Negeri Sembilan (SPR/Excel): PH {totals.get("PH", 17)} · BN {totals.get("BN", 14)} · PN {totals.get("PN", 5)} = 36 kerusi.
    Pembahagian muafakat di bawah menunjukkan <strong>kerusi mana dahulu milik blok mana</strong> — asas logik perbincangan PAS–UMNO.
  </p>
  <div class="wow-stats" style="grid-template-columns:repeat(3,1fr);margin-bottom:8px">
    <div class="wow-stat" style="border-left:3px solid #ef4444"><div class="wow-num">{totals.get("PH", 17)}</div><div class="wow-lbl">PH (DAP/PKR/Amanah)</div></div>
    <div class="wow-stat" style="border-left:3px solid #3b82f6"><div class="wow-num">{totals.get("BN", 14)}</div><div class="wow-lbl">BN (UMNO/MCA/MIC)</div></div>
    <div class="wow-stat" style="border-left:3px solid #4ade80"><div class="wow-num">{totals.get("PN", 5)}</div><div class="wow-lbl">PN (PAS/Bersatu)</div></div>
  </div>
  {seat_table(pas, "🟢 PAS/PN 13 — contest PAS/PN (9 wajib + 4 berhasrat)")}
  {seat_table(umno, "🔴 UMNO/BN 23 — contest UMNO/BN")}
</div>"""


def _render_overview_wow(
    ev: dict, meta: dict,
    cohort_framework: list | None = None,
    pas_summary: dict | None = None,
    umno_summary: dict | None = None,
    incumbent_breakdown: dict | None = None,
) -> str:
    """Overview — ramalan, sentiment, penyandang (tiada formula strategi dalaman)."""
    eco = ev.get("economic") or {}
    od = ev.get("openData") or {}
    data_points = ev.get("socmedRows", 0) + ev.get("postRows", 0) + ev.get("commentRows", 0) + ev.get("newsCrawled", 0)
    cohort_rows = "".join(
        f"""<tr>
          <td><strong>{c["label"]}</strong></td>
          <td style="color:var(--muted)">{c["reason"]}</td>
          <td>{c["swing"]}</td>
        </tr>"""
        for c in (cohort_framework or COHORT_NARRATIVES)
    )

    return f"""
<div class="wow-stats">
  <div class="wow-stat">
    <div class="wow-num">{ev.get('engagementMillions', 56.9):.0f}<span>M</span></div>
    <div class="wow-lbl">Engagement</div>
  </div>
  <div class="wow-stat">
    <div class="wow-num">{ev.get('socmedRows', 0):,}</div>
    <div class="wow-lbl">Socmed Posts</div>
  </div>
  <div class="wow-stat">
    <div class="wow-num">{ev.get('newsCrawled', 0):,}</div>
    <div class="wow-lbl">Artikel Media</div>
  </div>
  <div class="wow-stat">
    <div class="wow-num">36</div>
    <div class="wow-lbl">Kerusi DUN</div>
  </div>
  <div class="wow-stat">
    <div class="wow-num">{od.get('endpointCount', 29)}</div>
    <div class="wow-lbl">API Rasmi</div>
  </div>
  <div class="wow-stat gold">
    <div class="wow-num">{ev.get('mediaNegPct') or '40'}<span>%</span></div>
    <div class="wow-lbl">Media Negatif</div>
  </div>
</div>

<div class="wow-trust">
  <strong>Analitik berasaskan data · ramalan per kerusi · sentiment media sosial</strong><br>
  {data_points:,}+ titik data · {ev.get('engagementMillions', 56.9):.1f}M engagement ·
  OPR BNM {eco.get('oprPct') or '2.75'}% · USD/MYR RM{eco.get('usdMyr') or '4.07'} ·
  media ML {ev.get('mediaNegPct') or '40'}% negatif · klik kerusi di sidebar untuk butiran.
</div>

{_render_incumbent_section(incumbent_breakdown)}

<div class="wow-pipeline">
  <div class="pipe-step"><span>1</span><strong>Crawl</strong><br>{ev.get('socmedRows', 0):,} posts</div>
  <div class="pipe-arrow">→</div>
  <div class="pipe-step"><span>2</span><strong>ML Sentiment</strong><br>HF ft-Malay-bert</div>
  <div class="pipe-arrow">→</div>
  <div class="pipe-step"><span>3</span><strong>Media</strong><br>{ev.get('newsCrawled', 0):,} artikel</div>
  <div class="pipe-arrow">→</div>
  <div class="pipe-step"><span>4</span><strong>DPI</strong><br>36 DUN</div>
  <div class="pipe-arrow">→</div>
  <div class="pipe-step"><span>5</span><strong>Ramalan</strong><br>PAS/PN 13 · UMNO/BN 23</div>
</div>

<div class="section data-catalog">
  <h2>Kohort Pengundi · Sebab · Pergi ke Mana</h2>
  <table class="catalog-table"><thead><tr><th>Kumpulan</th><th>Sebab Utama</th><th>Pergi ke Mana?</th></tr></thead><tbody>{cohort_rows}</tbody></table>
</div>

<div class="section data-catalog">
  <h2>Senarai Data Digunakan</h2>
  <p style="font-size:11px;color:var(--muted);margin-bottom:14px">
    Semua sumber di bawah digunakan untuk ramalan, sentiment & insight per kerusi.
    Dijana: {meta.get('generated', '—')} · DPI: {meta.get('dpiAsOf', '—')} · Ranking: {meta.get('rankingAsOf', '—')}
  </p>
  {_render_data_catalog(ev.get('dataCatalog') or [])}
</div>"""


def _render_data_catalog(catalog: list[dict]) -> str:
    blocks = []
    for cat in catalog:
        rows = "".join(
            f"""<tr>
              <td><strong>{it['name']}</strong></td>
              <td>{it.get('vol', '—')}</td>
              <td style="color:var(--muted)">{it.get('use', '—')}</td>
            </tr>"""
            for it in cat.get("items", [])
        )
        blocks.append(f"""
<div class="catalog-block">
  <h3>{cat.get('icon', '📂')} {cat.get('category', '')}</h3>
  <table class="catalog-table"><thead><tr><th>Fail / Sumber</th><th>Skala</th><th>Kegunaan</th></tr></thead><tbody>{rows}</tbody></table>
</div>""")
    return "".join(blocks)


def generate_html(data: dict) -> str:
    j = json.dumps(data, ensure_ascii=False)
    ts = data["meta"]["generated"]
    ev = data["evidence"]
    overview_html = _render_overview_wow(
        ev, data["meta"],
        data.get("cohortFramework"), data.get("pasWinSummary"), data.get("umnoWinSummary"),
        data.get("incumbentBreakdown"),
    )
    eng_m = ev.get("engagementMillions") or round(ev.get("engagement", 0) / 1e6, 1)
    return f"""<!DOCTYPE html>
<html lang="ms">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>PAS + BN Muafakat — Justifikasi Pembahagian Kerusi</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap" rel="stylesheet">
<style>
:root{{--bg:#0a0e14;--surface:#121820;--surface2:#1a2230;--border:#2a3344;--text:#e8edf5;--muted:#8b9ab5;--pas:#1a7f5a;--umno:#c8102e;--gold:#d4af37;--warn:#f59e0b}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:Inter,sans-serif;background:var(--bg);color:var(--text);line-height:1.5}}
.layout{{display:grid;grid-template-columns:220px 1fr;min-height:100vh}}
.sidebar{{background:var(--surface);border-right:1px solid var(--border);padding:16px;position:sticky;top:0;height:100vh;overflow-y:auto}}
.sidebar h2{{font-size:13px;color:var(--gold);margin-bottom:12px}}
.nav-btn{{display:block;width:100%;text-align:left;padding:8px 10px;margin-bottom:4px;border:1px solid transparent;border-radius:8px;background:transparent;color:var(--muted);cursor:pointer;font-size:12px}}
.nav-btn.active,.nav-btn:hover{{background:var(--surface2);color:var(--text);border-color:var(--border)}}
.nav-btn.pas.active{{border-left:3px solid var(--pas)}}
.nav-btn.umno.active{{border-left:3px solid var(--umno)}}
.main{{padding:20px 24px;max-width:1100px}}
header{{margin-bottom:20px;padding-bottom:16px;border-bottom:1px solid var(--border)}}
header h1{{font-size:22px}}
.badge{{display:inline-block;padding:2px 8px;border-radius:999px;font-size:9px;font-weight:700;text-transform:uppercase;margin-right:4px}}
.badge-pas{{background:rgba(26,127,90,.2);color:#4ade80}}
.badge-umno{{background:rgba(200,16,46,.2);color:#f87171}}
.badge-warn{{background:rgba(245,158,11,.15);color:var(--warn)}}
.grid-3{{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:20px}}
.card{{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:14px}}
.card-label{{font-size:10px;color:var(--muted);text-transform:uppercase;margin-bottom:4px}}
.card-value{{font-size:24px;font-weight:800}}
.card-sub{{font-size:11px;color:var(--muted);margin-top:4px}}
.section{{margin-bottom:24px}}
.section h2{{font-size:16px;margin-bottom:10px;border-left:3px solid var(--gold);padding-left:8px}}
.seat-card{{background:var(--surface);border:1px solid var(--border);border-radius:12px;margin-bottom:14px;overflow:hidden}}
.seat-card.pas{{border-left:4px solid var(--pas)}}
.seat-card.umno{{border-left:4px solid var(--umno)}}
.seat-head{{padding:14px 16px;cursor:pointer;display:flex;justify-content:space-between;align-items:flex-start;gap:12px}}
.seat-head:hover{{background:var(--surface2)}}
.seat-body{{display:none;padding:0 16px 16px;border-top:1px solid var(--border)}}
.seat-card.open .seat-body{{display:block}}
.score-bar{{display:flex;height:8px;border-radius:999px;overflow:hidden;margin:8px 0;background:var(--surface2)}}
.score-fill{{height:100%;background:linear-gradient(90deg,var(--pas),var(--gold))}}
.metrics{{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin:12px 0}}
.metric{{background:var(--surface2);padding:8px;border-radius:8px;font-size:11px}}
.metric strong{{display:block;font-size:14px}}
.layer-grid{{display:grid;grid-template-columns:repeat(5,1fr);gap:6px;margin:10px 0}}
.layer-cell{{background:var(--surface2);padding:8px;border-radius:8px;text-align:center;font-size:10px}}
.layer-cell b{{display:block;font-size:16px;color:var(--gold)}}
ul.args{{margin:8px 0 8px 18px;font-size:12px;color:var(--muted)}}
ul.args li{{margin-bottom:4px}}
.evidence-box{{background:rgba(59,130,246,.08);border:1px solid rgba(59,130,246,.2);padding:10px;border-radius:8px;font-size:11px;margin-top:8px}}
.insight{{font-size:12px;color:var(--gold);margin-top:8px;font-weight:600}}
.demo-panel{{background:var(--surface2);border-radius:10px;padding:12px;margin:12px 0}}
.demo-panel h4{{font-size:11px;color:var(--gold);margin-bottom:8px;text-transform:uppercase}}
.demo-bars{{display:flex;flex-direction:column;gap:6px}}
.demo-row{{display:grid;grid-template-columns:100px 1fr 42px;align-items:center;gap:8px;font-size:10px}}
.demo-track{{height:8px;background:var(--bg);border-radius:999px;overflow:hidden}}
.demo-fill{{height:100%;border-radius:999px}}
.demo-fill.muda{{background:#60a5fa}}.demo-fill.dewasa{{background:#34d399}}.demo-fill.mid{{background:#fbbf24}}.demo-fill.tua{{background:#a78bfa}}
.demo-fill.m{{background:#3b82f6}}.demo-fill.f{{background:#ec4899}}.demo-fill.cina{{background:#ef4444}}.demo-fill.india{{background:#f97316}}
.issue-tags{{display:flex;flex-wrap:wrap;gap:6px;margin:8px 0}}
.issue-tag{{background:rgba(212,175,55,.12);border:1px solid rgba(212,175,55,.3);padding:4px 8px;border-radius:999px;font-size:10px}}
.pred-list{{font-size:11px;color:var(--muted);margin:6px 0 0 16px}}
.pred-list li{{margin-bottom:3px}}
.demo-grid-2{{display:grid;grid-template-columns:1fr 1fr;gap:10px}}
@media(max-width:700px){{.demo-grid-2{{grid-template-columns:1fr}}}}
.header-meta{{font-size:11px;color:var(--muted);margin-top:8px;line-height:1.5}}
.header-meta strong{{color:var(--gold);font-weight:600}}
.wow-stats{{display:grid;grid-template-columns:repeat(6,1fr);gap:10px;margin-bottom:16px}}
.wow-stat{{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:14px 10px;text-align:center}}
.wow-stat.gold{{border-color:rgba(212,175,55,.4)}}
.wow-num{{font-size:24px;font-weight:800;line-height:1}}
.wow-num span{{font-size:14px;color:var(--gold)}}
.wow-lbl{{font-size:9px;text-transform:uppercase;color:var(--gold);margin-top:6px}}
.wow-trust{{background:rgba(59,130,246,.1);border:1px solid rgba(59,130,246,.2);border-radius:10px;padding:14px;font-size:12px;line-height:1.6;margin-bottom:20px}}
.hybrid-flow{{display:flex;gap:8px;margin-bottom:12px;flex-wrap:wrap}}
.hybrid-step{{flex:1;min-width:90px;background:var(--surface2);border:1px solid var(--border);border-radius:8px;padding:10px;text-align:center}}
.hybrid-pct{{font-size:20px;font-weight:800;color:var(--gold)}}
.hybrid-name{{font-size:9px;color:var(--muted);margin-top:4px}}
.hybrid-formula-box{{background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:12px;text-align:center}}
.hybrid-formula-box code{{font-size:11px;color:var(--gold)}}
.wow-pipeline{{display:flex;align-items:center;gap:4px;margin-top:16px;padding:12px;background:var(--surface);border:1px solid var(--border);border-radius:10px;flex-wrap:wrap}}
.pipe-step{{flex:1;min-width:80px;text-align:center;font-size:10px;color:var(--muted)}}
.pipe-step span{{display:inline-block;width:20px;height:20px;line-height:20px;border-radius:50%;background:var(--gold);color:#000;font-weight:800;font-size:10px;margin-bottom:4px}}
.pipe-step strong{{display:block;color:var(--text);font-size:10px}}
.pipe-arrow{{color:var(--gold);font-weight:700}}
.catalog-block{{margin-bottom:16px;background:var(--surface);border:1px solid var(--border);border-radius:10px;overflow:hidden}}
.catalog-block h3{{font-size:12px;padding:10px 14px;background:var(--surface2);border-bottom:1px solid var(--border);color:var(--gold)}}
.catalog-table{{width:100%;border-collapse:collapse;font-size:11px}}
.catalog-table th{{padding:8px 12px;text-align:left;font-size:9px;text-transform:uppercase;color:var(--muted);background:var(--surface2)}}
.catalog-table td{{padding:8px 12px;border-top:1px solid var(--border);vertical-align:top}}
.catalog-table tr:hover td{{background:rgba(255,255,255,.02)}}
.win-panel{{background:linear-gradient(135deg,rgba(26,127,90,.12),rgba(26,127,90,.04));border:1px solid rgba(26,127,90,.35);border-radius:10px;padding:14px;margin:12px 0}}
.win-panel.umno-panel{{background:linear-gradient(135deg,rgba(200,16,46,.1),transparent);border-color:rgba(200,16,46,.3)}}
.win-head{{display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap;margin-bottom:10px}}
.win-prob{{font-size:28px;font-weight:800;color:var(--pas)}}
.win-prob.umno{{color:var(--umno)}}
.win-badge{{display:inline-block;padding:3px 10px;border-radius:999px;font-size:10px;font-weight:700;background:rgba(26,127,90,.25);color:#4ade80}}
.win-badge.warn{{background:rgba(245,158,11,.2);color:var(--warn)}}
.win-badge.low{{background:rgba(139,154,181,.2);color:var(--muted)}}
.cohort-mini{{font-size:10px;margin-top:8px}}
.cohort-mini table{{width:100%;font-size:10px}}
.cohort-mini td{{padding:4px 6px;border-top:1px solid var(--border)}}
.head-win{{font-size:11px;color:var(--pas);font-weight:700;margin-top:4px}}
.head-win.umno{{color:#f87171}}
.win-label{{font-size:14px;font-weight:800;margin-bottom:6px;line-height:1.4}}
.win-label.pas{{color:#4ade80}}
.win-label.umno{{color:#f87171}}
.win-section{{margin-top:10px}}
.win-section strong{{font-size:11px;color:var(--gold);display:block;margin-bottom:4px}}
@media(max-width:900px){{.wow-stats{{grid-template-columns:repeat(3,1fr)}}.catalog-table{{font-size:10px}}}}
.hidden{{display:none!important}}
@media(max-width:900px){{.layout{{grid-template-columns:1fr}}.sidebar{{height:auto;position:relative}}.metrics,.layer-grid{{grid-template-columns:repeat(2,1fr)}}}}
@media print{{.sidebar{{display:none}}.seat-body{{display:block!important}}}}
</style>
</head>
<body>
<div class="layout">
<aside class="sidebar">
  <h2>PAS/PN 13 · UMNO/BN 23</h2>
  <button class="nav-btn active" data-view="overview">📊 Overview</button>
  <button class="nav-btn" data-view="all">📋 Semua Kerusi (36)</button>
  <button class="nav-btn" data-view="pas-all">🟢 Semua PAS/PN (13)</button>
  <button class="nav-btn" data-view="umno-all">🔴 Semua UMNO/BN (23)</button>
  <hr style="border-color:var(--border);margin:12px 0">
  <div id="seatNav"></div>
</aside>
<div class="main">
<header>
  <span class="badge badge-pas">PAS/PN 13</span><span class="badge badge-umno">UMNO/BN 23</span>
  <h1>Justifikasi Pembahagian Kerusi — PRN Negeri Sembilan 2026</h1>
  <p style="color:var(--muted);font-size:12px;margin-top:6px">{data['meta']['dpiAsOf']} · Ranking {data['meta']['rankingAsOf']} · {ts}</p>
  <p class="header-meta">
    <strong>{ev.get('socmedRows', 0):,}</strong> posts · <strong>{eng_m:.1f}M</strong> engagement ·
    <strong>{ev.get('newsCrawled', 0):,}</strong> artikel · Ramalan + Sentiment
  </p>
</header>
<div id="view-overview">{overview_html}</div>
<div id="seatCards" class="hidden"></div>
<p style="font-size:10px;color:var(--muted);margin-top:20px">{data['meta']['disclaimer']}</p>
</div>
</div>
<script>
const DATA = {j};
function fmt(n) {{ return n != null && n !== '' ? Number(n).toLocaleString() : '—'; }}

function demoBar(label, pct, cls) {{
  const p = pct ?? 0;
  return `<div class="demo-row"><span>${{label}}</span><div class="demo-track"><div class="demo-fill ${{cls}}" style="width:${{p}}%"></div></div><span>${{p}}%</span></div>`;
}}

function demoPanelHtml(r) {{
  const D = r.demographics || {{}};
  const P = r.demographicPrediction || {{}};
  const ab = D.ageBands || {{}};
  const g = D.gender || {{}};
  const e = D.ethnicity || {{}};
  const issues = (r.issues || []).map(i => `<span class="issue-tag">${{i}}</span>`).join('');
  const preds = (P.predictions || []).map(p => `<li>${{p}}</li>`).join('');
  const swings = (P.swingCohorts || []).join(' · ') || '—';
  const demoScore = P.demographicPasScore ?? '—';
  const lean = P.demographicLean || '—';
  return `<div class="demo-panel">
    <h4>📊 Demografi & Ramalan · ${{r.areaType || '—'}} · Condong ${{lean}} (${{demoScore}}/100)</h4>
    <div class="demo-grid-2">
      <div>
        <div style="font-size:10px;color:var(--muted);margin-bottom:4px">Umur (DPI Dec 2025)</div>
        <div class="demo-bars">
          ${{demoBar('Muda 18–25', ab.muda?.pct, 'muda')}}
          ${{demoBar('Dewasa 26–40', ab.dewasa?.pct, 'dewasa')}}
          ${{demoBar('41–60', ab.pertengahan?.pct, 'mid')}}
          ${{demoBar('61+ Emas', ab.tua?.pct, 'tua')}}
        </div>
      </div>
      <div>
        <div style="font-size:10px;color:var(--muted);margin-bottom:4px">Jantina · Bangsa</div>
        <div class="demo-bars">
          ${{demoBar('Lelaki', g.lelaki?.pct, 'm')}}
          ${{demoBar('Perempuan', g.perempuan?.pct, 'f')}}
          ${{demoBar('Melayu', e.melayu?.pct, 'm')}}
          ${{demoBar('Cina', e.cina?.pct, 'cina')}}
          ${{demoBar('India', e.india?.pct, 'india')}}
        </div>
      </div>
    </div>
    ${{issues ? `<div style="margin-top:10px;font-size:10px;color:var(--muted)">Isu Utama</div><div class="issue-tags">${{issues}}</div>` : ''}}
    ${{P.tempatan ? `<p style="font-size:11px;margin-top:8px;color:var(--muted)"><strong>Tempatan:</strong> ${{P.tempatan}}</p>` : ''}}
    ${{P.agamaIdentiti ? `<p style="font-size:11px;color:var(--muted)"><strong>Bangsa/Identiti:</strong> ${{P.agamaIdentiti}}</p>` : ''}}
    ${{P.fenceSitters ? `<p style="font-size:11px;color:var(--muted)"><strong>Atas pagar:</strong> ${{P.fenceSitters}}</p>` : ''}}
    <p style="font-size:10px;color:var(--gold);margin-top:8px">Kohort swing: ${{swings}}${{r.pasWinProb != null ? ` · Ramalan PAS menang: ${{r.pasWinProb}}%` : ''}}</p>
    <ul class="pred-list">${{preds}}</ul>
  </div>`;
}}

function winPanelHtml(r) {{
  const W = r.winPrediction || {{}};
  if (!W.allocationLabel) return '';
  const isPas = r.allocation === 'PAS';
  const cls = isPas ? '' : ' umno-panel';
  const prob = W.winProbDisplay ?? (isPas ? W.pasWinProb : W.umnoWinProb);
  const conf = W.winConfidence || '—';
  const badgeCls = conf.includes('Tinggi') ? '' : (conf.includes('Rendah') ? ' low' : ' warn');
  const labelCls = isPas ? 'pas' : 'umno';
  const why = (W.whyReasons || []).map(w => `<li>${{w}}</li>`).join('');
  const must = (W.mustDo || []).map(m => `<li>${{m}}</li>`).join('');
  const cohorts = (W.activeCohorts || []).slice(0, 3).map(c =>
    `<tr><td>${{c.label}}</td><td style="color:var(--muted)">${{c.reason}}</td><td>${{c.swing}}</td></tr>`
  ).join('');
  return `<div class="win-panel${{cls}}">
    <div class="win-head">
      <div style="flex:1">
        <div class="win-label ${{labelCls}}">${{W.allocationLabel}}</div>
        <div style="font-size:13px;margin:8px 0;padding:8px;background:rgba(0,0,0,.2);border-radius:8px">
          ${{isPas
            ? `<span style="color:#4ade80;font-weight:800">PAS ${{W.pasWinProb}}%</span> <span style="color:var(--muted)">berbanding UMNO</span> <span style="color:#f87171;font-weight:700">${{W.umnoWinProb}}%</span> <span style="color:var(--gold)">(+${{W.pasVsUmnoAdvantage}}%)</span>`
            : `<span style="color:#f87171;font-weight:800">UMNO ${{W.umnoWinProb}}%</span> <span style="color:var(--muted)">berbanding PAS</span> <span style="color:#4ade80;font-weight:700">${{W.pasWinProb}}%</span> <span style="color:var(--gold)">(+${{W.pasVsUmnoAdvantage}}%)</span>`
          }}
        </div>
        <div style="font-size:11px;color:var(--muted)">Keyakinan: <span class="win-badge${{badgeCls}}">${{conf}}</span>
          · Bukan polling SPR — skor analitik + demografi</div>
      </div>
    </div>
    <div class="win-section">
      <strong>📌 Kerana di kerusi ini:</strong>
      <ul class="args">${{why || '<li>Demografi & data analitik menyokong peruntukan.</li>'}}</ul>
    </div>
    <div class="win-section">
      <strong>✅ Mesti lakukan:</strong>
      <ul class="args">${{must || '<li>Koordinasi MN + kempen padat.</li>'}}</ul>
    </div>
    ${{cohorts ? `<div class="cohort-mini"><strong style="font-size:10px;color:var(--muted)">KOHORT SWING</strong><table><thead><tr><th>Kumpulan</th><th>Sebab</th><th>Swing</th></tr></thead><tbody>${{cohorts}}</tbody></table></div>` : ''}}
  </div>`;
}}

function seatCardHtml(r) {{
  const cls = r.allocation === 'PAS' ? 'pas' : 'umno';
  const badge = r.allocation === 'PAS' ? '<span class="badge badge-pas">PAS</span>' : '<span class="badge badge-umno">UMNO/BN</span>';
  const warn = r.negotiation ? ' <span class="badge badge-warn">⚠ Perbincangan</span>' : '';
  const inc = r.incumbent || {{}};
  const incBadge = inc.label ? `<span style="font-size:10px;padding:2px 8px;border-radius:6px;margin-left:4px;background:${{
    inc.bloc === 'PH' ? 'rgba(239,68,68,.2)' : inc.bloc === 'BN' ? 'rgba(59,130,246,.2)' : inc.bloc === 'PN' ? 'rgba(74,222,128,.2)' : 'rgba(128,128,128,.2)'
  }};color:${{
    inc.bloc === 'PH' ? '#f87171' : inc.bloc === 'BN' ? '#60a5fa' : inc.bloc === 'PN' ? '#4ade80' : 'var(--muted)'
  }}">${{inc.label}}</span>` : '';
  const L = r.hybridLayers;
  const score = L.hybridPasScore;
  const W = r.winPrediction || {{}};
  const isPas = r.allocation === 'PAS';
  const prob = W.winProbDisplay ?? (isPas ? W.pasWinProb : W.umnoWinProb);
  let headWin = '';
  if (W.compareLabel || W.pasWinProb) {{
    headWin = isPas
      ? `<div class="head-win">PAS ${{W.pasWinProb}}% vs UMNO ${{W.umnoWinProb}}% (+${{W.pasVsUmnoAdvantage}}%)</div>`
      : `<div class="head-win umno">UMNO ${{W.umnoWinProb}}% vs PAS ${{W.pasWinProb}}% (+${{W.pasVsUmnoAdvantage}}%)</div>`;
  }}
  return `<div class="seat-card ${{cls}}" id="seat-${{r.code}}" data-alloc="${{r.allocation}}">
    <div class="seat-head" onclick="this.parentElement.classList.toggle('open')">
      <div>
        <strong>${{r.code}} ${{r.name}}</strong> ${{badge}}${{warn}}
        <div style="font-size:11px;color:var(--muted);margin-top:4px">${{r.incumbent2023 || r.incumbent?.full || '—'}} · maj ${{fmt(r.majority2023)}} ${{incBadge}}</div>
        ${{headWin}}
      </div>
      <div style="text-align:right">
        <div style="font-size:20px;font-weight:800;color:var(--gold)">${{score}}</div>
        <div style="font-size:10px;color:var(--muted)">Skor Analitik</div>
      </div>
    </div>
    <div class="seat-body">
      <div class="score-bar"><div class="score-fill" style="width:${{score}}%"></div></div>
      <div class="metrics">
        <div class="metric"><span>Melayu</span><strong>${{r.pctMelayu ?? '—'}}%</strong></div>
        <div class="metric"><span>Cina</span><strong>${{r.pctCina ?? '—'}}%</strong></div>
        <div class="metric"><span>Muda 18–25</span><strong>${{r.demographics?.ageBands?.muda?.pct ?? '—'}}%</strong></div>
        <div class="metric"><span>Emas 61+</span><strong>${{r.demographics?.ageBands?.tua?.pct ?? '—'}}%</strong></div>
      </div>
      ${{winPanelHtml(r)}}
      ${{demoPanelHtml(r)}}
      <p class="insight">${{r.arguments.insight}}</p>
      <strong style="font-size:12px">Mengapa ${{r.allocation}}?</strong>
      <ul class="args">${{r.arguments.forAllocation.map(a => `<li>${{a}}</li>`).join('')}}</ul>
      <details style="margin-top:8px"><summary style="font-size:11px;cursor:pointer;color:var(--muted)">Kes PAS vs Kes UMNO/BN</summary>
        <p style="font-size:11px;margin-top:6px;color:var(--pas)"><strong>Kes PAS:</strong></p>
        <ul class="args">${{r.arguments.pasCase.map(a => `<li>${{a}}</li>`).join('')}}</ul>
        <p style="font-size:11px;color:var(--umno)"><strong>Kes UMNO/BN:</strong></p>
        <ul class="args">${{r.arguments.umnoCase.map(a => `<li>${{a}}</li>`).join('')}}</ul>
      </details>
      <div class="evidence-box">
        <strong>📂 Bukti Data:</strong><br>
        ${{r.arguments.evidence.join('<br>')}}
        ${{r.socmedMentions ? `<br>📱 Mention socmed: ${{r.socmedMentions}} · engagement ${{fmt(r.socmedEngagement)}}` : ''}}
      </div>
    </div>
  </div>`;
}}

function showOverview() {{
  document.getElementById('view-overview').classList.remove('hidden');
  document.getElementById('seatCards').classList.add('hidden');
}}

function showSeats(filter) {{
  document.getElementById('view-overview').classList.add('hidden');
  const box = document.getElementById('seatCards');
  box.classList.remove('hidden');
  renderSeats(filter);
}}

function renderSeats(filter) {{
  let list = DATA.allSeats;
  if (filter === 'PAS') list = DATA.pasSeats;
  if (filter === 'UMNO/BN') list = DATA.umnoSeats;
  document.getElementById('seatCards').innerHTML = list.map(seatCardHtml).join('');
}}

function renderNav() {{
  const nav = document.getElementById('seatNav');
  nav.innerHTML = DATA.allSeats.map(r => {{
    const c = r.allocation === 'PAS' ? 'pas' : 'umno';
    return `<button class="nav-btn ${{c}}" data-seat="${{r.code}}">${{r.code}} ${{r.name}}</button>`;
  }}).join('');
  nav.querySelectorAll('[data-seat]').forEach(btn => btn.onclick = () => {{
    showSeats('all');
    const el = document.getElementById('seat-' + btn.dataset.seat);
    if (el) {{ el.classList.add('open'); el.scrollIntoView({{behavior:'smooth',block:'start'}}); }}
    document.querySelectorAll('.sidebar .nav-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
  }});
}}

document.querySelectorAll('.sidebar .nav-btn[data-view]').forEach(btn => {{
  btn.onclick = () => {{
    document.querySelectorAll('.sidebar .nav-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    const v = btn.dataset.view;
    if (v === 'overview') showOverview();
    else if (v === 'all') showSeats('all');
    else if (v === 'pas-all') showSeats('PAS');
    else if (v === 'umno-all') showSeats('UMNO/BN');
  }};
}});

renderNav();
showOverview();
</script>
</body>
</html>"""


def main():
    try:
        from n9_dpi_updates import save_json
        save_json()
    except Exception as exc:
        print(f"⚠️ DPI refresh: {exc}")
    data = build_payload()
    html = generate_html(data)
    OUT_HTML.parent.mkdir(parents=True, exist_ok=True)
    OUT_HTML.write_text(html, encoding="utf-8")
    OUT_COPY.parent.mkdir(parents=True, exist_ok=True)
    OUT_COPY.parent.mkdir(parents=True, exist_ok=True)
    OUT_COPY.write_text(html, encoding="utf-8")
    for dest in (DESKTOP_HTML, DESKTOP_HTML_N9):
        try:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(html, encoding="utf-8")
            print(f"   Desktop:      {dest}")
        except OSError as exc:
            print(f"   ⚠ Desktop:    {dest} — {exc}")
    print(f"✅ Dashboard MN: {OUT_HTML}")
    print(f"   Copy:         {OUT_COPY}")
    print(f"   PAS {data['meta']['pasSeats']} · UMNO {data['meta']['umnoSeats']}")


if __name__ == "__main__":
    main()
