#!/usr/bin/env python3
"""Enrich PRN N9 seat data from Excel SPR + PAS analytics + win predictions."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from prn_paths import reference, reports, resolve_existing  # noqa: E402

EXCEL = ROOT / "JITP_2026/Master_File/PRN2023_NegeriSembilan_v2.xlsx"
OUT_JSON = reports("N9") / "seats/n9_seats_export.json"
OUT_ANALYTICS_JSON = reports("N9") / "seats/n9_seats_analytics.json"
OUT_CSV = reports("N9") / "seats/n9_seats_analytics.csv"
SOCIAL_SUMMARY_JSON = resolve_existing(
    reference("N9") / "prn_n9_adun_social_summary.json",
    ROOT / "data/projects/political/pas_break_2026/reference/prn_n9_adun_social_summary.json",
)

# Zon pertarungan — floor kebarangkalian (model analis, bukan polling)
WINNABLE_PROB_FLOOR: Dict[str, float] = {
    "N03": 51.0,
    "N09": 50.5,
}

# Rule awal — override manual (Raja / war room)
PAS_KATEGORI_OVERRIDE: Dict[str, str] = {
    "N05": "defend",
    "N25": "defend",
    "N31": "defend",
    "N03": "winnable",
    "N09": "winnable",
    "N18": "winnable",
    "N02": "tough",
    "N19": "tough",
    "N27": "tough",
    "N35": "tough",
}

CLUSTER_BY_PARLIMEN = {
    "P126 Jelebu": "LBN/Jelebu",
    "P127 Jempol": "FELDA/Jempol",
    "P128 Seremban": "Bandar Seremban",
    "P129 Kuala Pilah": "Adat/Pilah",
    "P130 Rasah": "Bandar Rasah/Nilai",
    "P131 Rembau": "Rembau/Tradisi",
    "P132 Port Dickson": "Pantai/PD",
    "P133 Tampin": "Sempadan Johor",
}

DUN_ISSUES: Dict[str, Dict[str, str]] = {
    "N05": {"isu1": "FELDA/getah", "isu2": "Akses klinik", "isu3": "Split PAS-PN"},
    "N25": {"isu1": "Kos sara hidup bandar", "isu2": "Trafik Seremban", "isu3": "Pertahan PAS post-split"},
    "N31": {"isu1": "Pelancongan PD", "isu2": "Nelayan", "isu3": "Perpaduan pantai"},
    "N03": {"isu1": "Majoriti sempit", "isu2": "Swing Melayu", "isu3": "3 penjuru"},
    "N09": {"isu1": "Bandar Lenggeng", "isu2": "Kos hidup", "isu3": "PAS vs UMNO"},
    "N18": {"isu1": "Pilah tradisi", "isu2": "PH marginal", "isu3": "PAS challenger kuat"},
    "N01": {"isu1": "Kos hidup bandar", "isu2": "Banjir/parking", "isu3": "DAP stronghold"},
    "N20": {"isu1": "NILAI manufacturing", "isu2": "Bersatu vs PAS", "isu3": "Split PN"},
    "N34": {"isu1": "FELDA Gemas", "isu2": "Komuter NS-Johor", "isu3": "Bersatu hold"},
}

DEMO_DEFAULT = "Melayu dominan LBN/FELDA; bandar muda meningkat di zon Seremban/Rasah."


def _clean_social(val: Any) -> str:
    s = str(val or "").strip()
    if not s or s.lower() in ("nan", "—", "-", "cari di fb", "cari di tiktok", "cari di x"):
        return ""
    return s


def kategori_margin(majoriti: int) -> str:
    m = int(majoriti or 0)
    if m <= 199:
        return "ultra_marginal"
    if m <= 499:
        return "super_marginal"
    if m <= 999:
        return "marginal"
    if m <= 2999:
        return "semi_safe"
    return "safe"


def kategori_margin_label(km: str) -> str:
    return {
        "ultra_marginal": "Ultra Marginal (0–199)",
        "super_marginal": "Super Marginal (200–499)",
        "marginal": "Marginal (500–999)",
        "semi_safe": "Semi Selamat (1K–3K)",
        "safe": "Selamat (3K+)",
    }.get(km, km)


def kategori_pas_label(kp: str) -> str:
    return {
        "defend": "Pertahan",
        "winnable": "Boleh Menang",
        "tough": "Sukar / Lawan Kuat",
        "not_priority": "Bukan Fokus",
    }.get(kp, kp)


def auto_kategori_pas(seat: dict) -> str:
    code = seat["code"]
    if code in PAS_KATEGORI_OVERRIDE:
        return PAS_KATEGORI_OVERRIDE[code]

    party = seat.get("party2023") or seat.get("parti_menang", "")
    chall = seat.get("challengerParty") or seat.get("parti_pencabar", "")
    maj = int(seat.get("majority") or seat.get("majoriti") or 0)
    winner = seat.get("winner2023") or seat.get("koalisi_menang", "")

    if party == "PAS":
        return "defend"
    if party == "Bersatu" and winner == "PN":
        return "tough"
    if chall == "PAS" and maj <= 999:
        return "winnable"
    if chall == "PAS" and maj <= 2999:
        return "tough"
    if party in ("DAP", "PKR", "Amanah") and maj >= 5000:
        return "not_priority"
    if party == "UMNO" and chall == "PAS" and maj < 700:
        return "winnable"
    if party == "UMNO" and chall == "PAS":
        return "tough"
    return "not_priority"


def predict_seat(seat: dict) -> dict:
    """Rule-based PRN 2026 prediction from PAS/PN war-room lens."""
    party = seat.get("party2023", "")
    winner = seat.get("winner2023", "")
    chall = seat.get("challengerParty", "")
    maj = int(seat.get("majority") or 0)
    kp = seat.get("kategori_pas", "not_priority")
    km = seat.get("kategori_margin", kategori_margin(maj))

    margin_base = {
        "ultra_marginal": 52,
        "super_marginal": 48,
        "marginal": 44,
        "semi_safe": 38,
        "safe": 28,
    }

    if party == "PAS":
        pas_prob = {"ultra_marginal": 58, "super_marginal": 64, "marginal": 70,
                    "semi_safe": 76, "safe": 82}.get(km, 65)
        pred_party, pred_bloc = "PAS", "PN"
    elif party == "Bersatu":
        pas_prob = 42 if km in ("semi_safe", "safe") else 38
        pred_party, pred_bloc = "Bersatu", "PN"
    elif chall == "PAS":
        pas_prob = margin_base.get(km, 35)
        if kp == "winnable":
            pas_prob = max(pas_prob, min(58, 46 + max(0, (1000 - maj) / 25)))
        elif kp == "tough":
            pas_prob += 4
        pred_party = "PAS" if pas_prob >= 50 else party
        pred_bloc = "PN" if pas_prob >= 50 else winner
    else:
        pas_prob = 15 if kp == "not_priority" else 22
        pred_party, pred_bloc = party, winner

    if kp == "defend" and party == "PAS":
        pas_prob = min(88, pas_prob + 6)

    code = seat.get("code", "")
    if code in WINNABLE_PROB_FLOOR and chall == "PAS":
        pas_prob = max(pas_prob, WINNABLE_PROB_FLOOR[code])
        pred_party = "PAS" if pas_prob >= 50 else party
        pred_bloc = "PN" if pas_prob >= 50 else winner
    elif kp == "winnable" and chall == "PAS" and km == "marginal":
        pas_prob = max(pas_prob, min(54, 48 + max(0, (1000 - maj) / 40)))

    solo = max(8, pas_prob - 10)
    pn = min(92, pas_prob + 5)
    mn = min(90, pas_prob + (8 if winner == "BN" or party == "UMNO" else 4))

    pas_prob = round(min(92, max(8, pas_prob)), 1)
    solo = round(solo, 1)
    pn = round(pn, 1)
    mn = round(mn, 1)

    if pas_prob >= 62:
        label, risk = "PAS/Kemungkinan Menang", "Rendah" if party == "PAS" else "Sederhana"
    elif pas_prob >= 48:
        label, risk = "PERTARUNGAN Sengit", "Tinggi"
    elif pas_prob >= 32:
        label, risk = "PAS Perlu Swing Besar", "Tinggi"
    else:
        label, risk = "Bukan Sasaran PAS", "Rendah"

    conf = "Tinggi" if abs(pas_prob - 50) > 22 else ("Sederhana" if abs(pas_prob - 50) > 10 else "Rendah")

    return {
        "pasWinProb": pas_prob,
        "predictedParty": pred_party,
        "predictedBloc": pred_bloc,
        "predictionLabel": label,
        "predictionConfidence": conf,
        "scenarioPasSolo": solo,
        "scenarioPasPn": pn,
        "scenarioPasMn": mn,
        "scenarioRisk": risk,
        "priorityMonitoring": kp in ("defend", "winnable") or km in ("ultra_marginal", "super_marginal"),
    }


def apply_social_crawl(seats: List[dict]) -> List[dict]:
    """Merge ADUN seed crawl summary into seat records."""
    if not SOCIAL_SUMMARY_JSON.exists():
        return seats
    try:
        summary = json.loads(SOCIAL_SUMMARY_JSON.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return seats
    by_code = {s["code"]: s for s in summary.get("per_seat", []) if s.get("code")}
    for seat in seats:
        soc = by_code.get(seat["code"], {})
        mentions = int(soc.get("newsMentions") or 0)
        seat["newsMentions"] = mentions
        seat["socialCrawlHeadlines"] = soc.get("topHeadlines") or []
        if mentions > 0:
            seat["statusSocialFb"] = "active" if seat.get("facebookUrl") else seat.get("statusSocialFb", "pending")
            seat["statusSocialTiktok"] = "active" if seat.get("tiktokHandle") else seat.get("statusSocialTiktok", "pending")
            seat["statusSocialX"] = "active" if seat.get("xHandle") else seat.get("statusSocialX", "pending")
        if soc.get("facebookUrl"):
            seat["facebookUrl"] = soc["facebookUrl"]
        if soc.get("tiktokHandle"):
            seat["tiktokHandle"] = soc["tiktokHandle"]
        if soc.get("xHandle"):
            seat["xHandle"] = soc["xHandle"]
    return seats


def load_excel_seats() -> List[dict]:
    if not EXCEL.exists():
        raise FileNotFoundError(f"Excel not found: {EXCEL}")

    df = pd.read_excel(EXCEL, sheet_name="Keputusan Penuh", header=2)
    df.columns = [re.sub(r"\s+", "_", str(c).strip().lower()) for c in df.columns]
    df = df.dropna(subset=["kod_dun"]).copy()
    df["kod_dun"] = df["kod_dun"].astype(str).str.strip()

    adun = pd.read_excel(EXCEL, sheet_name="ADUN Terpilih", header=1)
    adun.columns = [re.sub(r"[^a-z0-9_]", "_", str(c).strip().lower()) for c in adun.columns]
    adun = adun.dropna(subset=["kod_dun"]).copy()
    adun["kod_dun"] = adun["kod_dun"].astype(str).str.strip()
    social = adun.set_index("kod_dun")[["facebook", "tiktok", "x_twitter"]].to_dict("index")

    seats: List[dict] = []
    for _, r in df.iterrows():
        code = str(r["kod_dun"]).strip()
        parlimen = str(r.get("parlimen", "")).strip()
        par_key = parlimen if parlimen.startswith("P") else f"P{parlimen.split()[0][1:] if parlimen else ''}"
        # normalize parlimen like "P128 Seremban"
        if not parlimen.startswith("P") and " " in parlimen:
            par_key = parlimen
        else:
            par_key = parlimen

        party = str(r.get("parti", "")).strip()
        koalisi = str(r.get("koalisi_menang", "")).strip()
        chall_party = str(r.get("parti_pencabar", "")).strip()
        status = str(r.get("status_kerusi", "")).strip()
        maj = int(r.get("majoriti") or 0)
        soc = social.get(code, {})

        base = {
            "code": code,
            "name": str(r.get("kawasan_dun", "")).strip(),
            "parlimen": par_key,
            "registeredVoters": int(r.get("jml_pengundi") or 0),
            "winner2023": koalisi,
            "party2023": party,
            "winnerName": str(r.get("nama_pemenang", "")).strip(),
            "majority": maj,
            "votesWon": int(r.get("undi_menang") or 0),
            "challengerVotes": int(r.get("undi_pencabar") or 0),
            "status2023": status,
            "challenger": str(r.get("nama_pencabar", "")).strip(),
            "challengerParty": chall_party,
            "challengerBloc": str(r.get("koalisi_pencabar", "")).strip(),
            "penyandangLama": str(r.get("penyandang_lama", "")).strip(),
            "isPasSeat": party == "PAS",
            "isBersatuSeat": party == "Bersatu",
            "isPnSeat": koalisi == "PN" or party in ("PAS", "Bersatu"),
            "isMarginal200": maj <= 200,
            "isMarginal500": maj <= 500,
            "isMarginal1000": maj <= 1000,
            "isTukarTangan": "TUKAR" in status.upper(),
            "semasaKoalisi": koalisi,
            "semasaParti": party,
            "namaAdun": str(r.get("nama_pemenang", "")).strip(),
            "facebookUrl": _clean_social(soc.get("facebook")),
            "tiktokHandle": _clean_social(soc.get("tiktok")),
            "xHandle": _clean_social(soc.get("x_twitter")),
            "clusterKawasan": CLUSTER_BY_PARLIMEN.get(par_key, par_key),
            "keywordPrimary": f"PRN {code} {str(r.get('kawasan_dun', '')).strip()}",
            "keywordSecondary": f"PAS {str(r.get('kawasan_dun', '')).strip()} Negeri Sembilan",
            "keywordParlimen": par_key,
            "statusSocialFb": "seed" if _clean_social(soc.get("facebook")) else "pending",
            "statusSocialTiktok": "seed" if _clean_social(soc.get("tiktok")) else "pending",
            "statusSocialX": "seed" if _clean_social(soc.get("x_twitter")) else "pending",
        }

        km = kategori_margin(maj)
        base["kategoriMargin"] = km
        base["kategoriMarginLabel"] = kategori_margin_label(km)
        base["kategoriPas"] = auto_kategori_pas(base)
        base["kategoriPasLabel"] = kategori_pas_label(base["kategoriPas"])

        issues = DUN_ISSUES.get(code, {})
        base["demografiRingkas"] = DEMO_DEFAULT
        base["isuUtama1"] = issues.get("isu1", "Kos sara hidup / ekonomi mikro")
        base["isuUtama2"] = issues.get("isu2", "Infrastruktur & perkhidmatan awam")
        base["isuUtama3"] = issues.get("isu3", "Dinamik PAS-PN post-split")

        pred = predict_seat(base)
        base.update(pred)

        # Legacy fields for existing dashboard
        base["areaType"] = _area_type(code, par_key, maj)
        base["pasInterest"] = {
            "defend": "Pertahan",
            "winnable": "Sasaran",
            "tough": "Pantau",
            "not_priority": "Sasaran Jauh",
        }[base["kategoriPas"]]
        base["threeCornerRisk"] = "Tinggi" if km in ("ultra_marginal", "super_marginal", "marginal") else "Sederhana" if km == "semi_safe" else "Rendah"
        base["strategicNote"] = _strategic_note(base)
        base["notes"] = f"Rule: {base['kategoriPas']} · {base['kategoriMargin']} · Ramalan PAS {base['pasWinProb']}%"

        seats.append(base)

    seats.sort(key=lambda s: s["code"])
    return apply_social_crawl(seats)


def _area_type(code: str, parlimen: str, maj: int) -> str:
    urban = {"N01", "N09", "N10", "N11", "N12", "N13", "N14", "N21", "N22", "N23", "N24"}
    if code in urban:
        return "Bandar"
    if maj > 8000:
        return "Luar Bandar"
    return "Separuh Bandar"


def _strategic_note(seat: dict) -> str:
    kp = seat["kategoriPas"]
    km = seat["kategoriMarginLabel"]
    prob = seat["pasWinProb"]
    if kp == "defend":
        return f"Kerusi PAS — pertahan kritikal. {km}. Ramalan menang {prob}%."
    if kp == "winnable":
        return f"Sasaran menang — majoriti {seat['majority']:,}. {km}. Ramalan PAS {prob}%."
    if kp == "tough":
        return f"Lawan kuat — asas PN/PAS ada. {km}. Ramalan PAS {prob}%."
    return f"Bukan fokus utama PAS. Ramalan PAS {prob}%."


def build_analytics_summary(seats: List[dict]) -> dict:
    from collections import Counter

    kp = Counter(s["kategoriPas"] for s in seats)
    km = Counter(s["kategoriMargin"] for s in seats)
    pas_wins = sum(1 for s in seats if s["pasWinProb"] >= 50)
    pn_hold = sum(1 for s in seats if s["isPnSeat"])
    monitor = [s for s in seats if s.get("priorityMonitoring")]

    return {
        "totalSeats": len(seats),
        "kategoriPas": dict(kp),
        "kategoriMargin": dict(km),
        "predictedPasWins": pas_wins,
        "predictedPasSeats": [s["code"] for s in seats if s["pasWinProb"] >= 50],
        "pnBaseline2023": pn_hold,
        "defendSeats": [s["code"] for s in seats if s["kategoriPas"] == "defend"],
        "winnableSeats": [s["code"] for s in seats if s["kategoriPas"] == "winnable"],
        "toughSeats": [s["code"] for s in seats if s["kategoriPas"] == "tough"],
        "priorityMonitoring": [{"code": s["code"], "name": s["name"], "pasWinProb": s["pasWinProb"]} for s in monitor],
        "ultraMarginal": [s["code"] for s in seats if s["kategoriMargin"] == "ultra_marginal"],
        "source": str(EXCEL),
    }


def load_enriched_seats() -> List[dict]:
    if OUT_JSON.exists() and OUT_ANALYTICS_JSON.exists():
        try:
            data = json.loads(OUT_ANALYTICS_JSON.read_text(encoding="utf-8"))
            if data.get("seats") and data.get("meta", {}).get("excel") == str(EXCEL):
                return data["seats"]
        except (json.JSONDecodeError, KeyError):
            pass
    return enrich_and_save()


def enrich_and_save() -> List[dict]:
    seats = load_excel_seats()
    try:
        from n9_dpi_updates import apply_to_seats, save_json
        save_json()
        seats = apply_to_seats(seats)
    except Exception as exc:
        import sys
        print(f"⚠️ DPI updates skipped: {exc}", file=sys.stderr)
    summary = build_analytics_summary(seats)

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(seats, ensure_ascii=False, indent=2), encoding="utf-8")

    payload = {
        "meta": {
            "generated": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
            "excel": str(EXCEL),
            "summary": summary,
        },
        "seats": seats,
    }
    OUT_ANALYTICS_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    # Full CSV export matching requested schema
    rows = []
    for s in seats:
        rows.append({
            "kod_dun": s["code"],
            "parlimen": s["parlimen"],
            "kawasan_dun": s["name"],
            "jml_pengundi": s["registeredVoters"],
            "nama_pemenang": s["winnerName"],
            "koalisi_menang": s["winner2023"],
            "parti_menang": s["party2023"],
            "undi_menang": s["votesWon"],
            "nama_pencabar": s["challenger"],
            "koalisi_pencabar": s["challengerBloc"],
            "parti_pencabar": s["challengerParty"],
            "undi_pencabar": s["challengerVotes"],
            "majoriti": s["majority"],
            "status_kerusi": s["status2023"],
            "penyandang_lama": s["penyandangLama"],
            "nama_adun": s["namaAdun"],
            "semasa_koalisi": s["semasaKoalisi"],
            "semasa_parti": s["semasaParti"],
            "is_pas_seat": s["isPasSeat"],
            "is_bersatu_seat": s["isBersatuSeat"],
            "is_pn_seat": s["isPnSeat"],
            "is_marginal_200": s["isMarginal200"],
            "is_marginal_500": s["isMarginal500"],
            "is_marginal_1000": s["isMarginal1000"],
            "is_tukar_tangan": s["isTukarTangan"],
            "kategori_pas": s["kategoriPas"],
            "kategori_margin": s["kategoriMargin"],
            "pas_win_prob": s["pasWinProb"],
            "predicted_party": s["predictedParty"],
            "predicted_bloc": s["predictedBloc"],
            "prediction_label": s["predictionLabel"],
            "status_social_fb": s["statusSocialFb"],
            "status_social_tiktok": s["statusSocialTiktok"],
            "status_social_x": s["statusSocialX"],
            "facebook_url": s["facebookUrl"],
            "tiktok_handle": s["tiktokHandle"],
            "x_handle": s["xHandle"],
            "keyword_primary": s["keywordPrimary"],
            "keyword_secondary": s["keywordSecondary"],
            "keyword_parlimen": s["keywordParlimen"],
            "cluster_kawasan": s["clusterKawasan"],
            "demografi_ringkas": s["demografiRingkas"],
            "isu_utama_1": s["isuUtama1"],
            "isu_utama_2": s["isuUtama2"],
            "isu_utama_3": s["isuUtama3"],
            "scenario_pas_solo": s["scenarioPasSolo"],
            "scenario_pas_pn": s["scenarioPasPn"],
            "scenario_pas_mn": s["scenarioPasMn"],
            "scenario_risk": s["scenarioRisk"],
            "priority_monitoring": s["priorityMonitoring"],
            "notes": s["notes"],
        })
    pd.DataFrame(rows).to_csv(OUT_CSV, index=False, encoding="utf-8-sig")
    return seats


def main() -> None:
    seats = enrich_and_save()
    summary = build_analytics_summary(seats)
    print(f"Excel:  {EXCEL}")
    print(f"Seats:  {len(seats)}")
    print(f"JSON:   {OUT_JSON}")
    print(f"Full:   {OUT_ANALYTICS_JSON}")
    print(f"CSV:    {OUT_CSV}")
    print(f"PAS kategori: {summary['kategoriPas']}")
    print(f"Ramalan PAS menang (≥50%): {summary['predictedPasWins']} kerusi → {summary['predictedPasSeats']}")


if __name__ == "__main__":
    main()
