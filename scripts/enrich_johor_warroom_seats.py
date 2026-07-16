#!/usr/bin/env python3
"""Enrich warroom_dun_Johor.json with PRN Johor 2022 incumbent + scenario probabilities."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from johor_seat_analytics import predict_johor_seat  # noqa: E402

GEO = ROOT / "data/projects/political/PRN/PRN_N9/reports/war_room/prototype/data/warroom_dun_Johor.json"
PROD = ROOT / "data/projects/political/PRN/PRN_N9/reports/war_room/prototype/data/warroom_dun_Johor_production.json"

SCENARIO_KEYS = (
    "pasWinProb", "pasSoloWinProb", "pasMnWinProb", "bnSoloWinProb", "phWinProb",
    "scenarioPasSolo", "scenarioPasMn", "scenarioPasPn", "predictedBloc",
    "predictionLabel", "kategoriMargin", "pasSoloVsBn", "pasSoloBnGapPct", "modelConfidence",
)

# PRN Johor 12 Mac 2022 — pemenang rasmi (parti sebenar + bloc)
PRN2022: dict[str, dict] = {
    "N01": {"winner": "Zahari bin Sarip", "party": "UMNO", "bloc": "BN"},
    "N02": {"winner": "Ng Kor Sim", "party": "DAP", "bloc": "PH"},
    "N03": {"winner": "Anuar bin Abdul Manap", "party": "UMNO", "bloc": "BN"},
    "N04": {"winner": "Saraswati a/p Nallathamby", "party": "MIC", "bloc": "BN"},
    "N05": {"winner": "Haslinda binti Salleh", "party": "UMNO", "bloc": "BN"},
    "N06": {"winner": "Tan Chong", "party": "MCA", "bloc": "BN"},
    "N07": {"winner": "Sahruddin bin Jamal", "party": "Bersatu", "bloc": "PN"},
    "N08": {"winner": "Mohamad Fazli bin Mohamad Salleh", "party": "UMNO", "bloc": "BN"},
    "N09": {"winner": "Sahrihan bin Jani", "party": "UMNO", "bloc": "BN"},
    "N10": {"winner": "Ee Chin Li", "party": "DAP", "bloc": "PH"},
    "N11": {"winner": "Khairin-Nisa binti Ismail", "party": "UMNO", "bloc": "BN"},
    "N12": {"winner": "Ng Yak Howe", "party": "DAP", "bloc": "PH"},
    "N13": {"winner": "Salahuddin bin Ayub", "party": "Amanah", "bloc": "PH"},
    "N14": {"winner": "Mohd Fuad bin Tukirin", "party": "UMNO", "bloc": "BN"},
    "N15": {"winner": "Abdul Aziz bin Talib", "party": "PAS", "bloc": "PN"},
    "N16": {"winner": "Selamat bin Takim", "party": "UMNO", "bloc": "BN"},
    "N17": {"winner": "Mohd Fared bin Mohd Khalid", "party": "UMNO", "bloc": "BN"},
    "N18": {"winner": "Zulkurnain bin Kamisan", "party": "UMNO", "bloc": "BN"},
    "N19": {"winner": "Ling Tian Soon", "party": "MCA", "bloc": "BN"},
    "N20": {"winner": "Samsolbari bin Jamali", "party": "UMNO", "bloc": "BN"},
    "N21": {"winner": "Mohamad Najib bin Samuri", "party": "UMNO", "bloc": "BN"},
    "N22": {"winner": "Rashidah binti Ramli", "party": "UMNO", "bloc": "BN"},
    "N23": {"winner": "Gan Peck Cheng", "party": "DAP", "bloc": "PH"},
    "N24": {"winner": "Mohd Yusla bin Ismail", "party": "UMNO", "bloc": "BN"},
    "N25": {"winner": "Mohd Puad bin Zarkashi", "party": "UMNO", "bloc": "BN"},
    "N26": {"winner": "Onn Hafiz bin Ghazi", "party": "UMNO", "bloc": "BN"},
    "N27": {"winner": "Abd Mutalip bin Abd Rahim", "party": "UMNO", "bloc": "BN"},
    "N28": {"winner": "Chew Chong Sin", "party": "DAP", "bloc": "PH"},
    "N29": {"winner": "Sharifah Azizah binti Syed Zain", "party": "UMNO", "bloc": "BN"},
    "N30": {"winner": "Lee Ting Han", "party": "MCA", "bloc": "BN"},
    "N31": {"winner": "R. Vidyananthan", "party": "MIC", "bloc": "BN"},
    "N32": {"winner": "Alwiyah binti Talib", "party": "Bersatu", "bloc": "PN"},
    "N33": {"winner": "Raven Kumar a/l Krishnasamy", "party": "MIC", "bloc": "BN"},
    "N34": {"winner": "Hahasrin bin Hashim", "party": "UMNO", "bloc": "BN"},
    "N35": {"winner": "Rashidah binti Ismail", "party": "UMNO", "bloc": "BN"},
    "N36": {"winner": "Muszaide bin Makmor", "party": "UMNO", "bloc": "BN"},
    "N37": {"winner": "Norlizah binti Noh", "party": "UMNO", "bloc": "BN"},
    "N38": {"winner": "Fauziah binti Misri", "party": "UMNO", "bloc": "BN"},
    "N39": {"winner": "Aznan bin Tamin", "party": "UMNO", "bloc": "BN"},
    "N40": {"winner": "Azizul bin Bachok", "party": "UMNO", "bloc": "BN"},
    "N41": {"winner": "Amira Aisya binti Abd Aziz", "party": "MUDA", "bloc": "MUDA"},
    "N42": {"winner": "Liow Cai Tung", "party": "DAP", "bloc": "PH"},
    "N43": {"winner": "Baharudin bin Mohamed Taib", "party": "UMNO", "bloc": "BN"},
    "N44": {"winner": "Mohd Hairi bin Mad Shah", "party": "UMNO", "bloc": "BN"},
    "N45": {"winner": "Andrew Chen Kah Eng", "party": "DAP", "bloc": "PH"},
    "N46": {"winner": "Liew Chin Tong", "party": "DAP", "bloc": "PH"},
    "N47": {"winner": "Ramlee bin Bohani", "party": "UMNO", "bloc": "BN"},
    "N48": {"winner": "Marina binti Ibrahim", "party": "DAP", "bloc": "PH"},
    "N49": {"winner": "Pandak bin Ahmad", "party": "UMNO", "bloc": "BN"},
    "N50": {"winner": "Mohd Jafni bin Md Shukor", "party": "UMNO", "bloc": "BN"},
    "N51": {"winner": "Arthur Chiong Sen Sern", "party": "PKR", "bloc": "PH"},
    "N52": {"winner": "Wong Bor Yang", "party": "DAP", "bloc": "PH"},
    "N53": {"winner": "Hasni bin Mohammad", "party": "UMNO", "bloc": "BN"},
    "N54": {"winner": "Hasrunizah binti Hassan", "party": "UMNO", "bloc": "BN"},
    "N55": {"winner": "Tan Eng Meng", "party": "MCA", "bloc": "BN"},
    "N56": {"winner": "Jefridin bin Atan", "party": "UMNO", "bloc": "BN"},
}

# Majoriti undi rasmi PRN Johor 2022 (Harakah/SPR)
MAJORITIES_2022: dict[str, int] = {
    "N01": 5377, "N02": 714, "N03": 4187, "N04": 1611, "N05": 1736, "N06": 3569,
    "N07": 710, "N08": 198, "N09": 3146, "N10": 372, "N11": 699, "N12": 7476,
    "N13": 2399, "N14": 1535, "N15": 1037, "N16": 2293, "N17": 4041, "N18": 6274,
    "N19": 2741, "N20": 5846, "N21": 294, "N22": 4219, "N23": 9956, "N24": 3912,
    "N25": 1920, "N26": 6543, "N27": 2815, "N28": 10107, "N29": 5166, "N30": 3176,
    "N31": 6698, "N32": 3041, "N33": 1356, "N34": 5854, "N35": 4888, "N36": 5679,
    "N37": 6039, "N38": 7505, "N39": 5903, "N40": 5281, "N41": 7114, "N42": 1922,
    "N43": 7926, "N44": 6178, "N45": 2866, "N46": 3347, "N47": 3514, "N48": 13943,
    "N49": 4360, "N50": 4755, "N51": 137, "N52": 5921, "N53": 5859, "N54": 6325,
    "N55": 4835, "N56": 8201,
}


def norm_code(code: str) -> str:
    if not code:
        return ""
    s = str(code).strip().upper().replace(" ", "")
    m = re.match(r"N\.?0*(\d+)", s)
    return f"N{int(m.group(1)):02d}" if m else s


def enrich_seat(seat: dict) -> dict:
    code = norm_code(seat.get("id") or seat.get("code"))
    ref = PRN2022.get(code)
    if not ref:
        return seat
    out = dict(seat)
    out["party"] = ref["bloc"]
    out["incumbent"] = ref["winner"]
    out["winnerName2022"] = ref["winner"]
    out["party2022"] = ref["party"]
    out["winner2022"] = ref["bloc"]
    out["party2023"] = ref["party"]
    out["winner2023"] = ref["bloc"]
    out["semasaParti"] = ref["party"]
    out["semasaKoalisi"] = ref["bloc"]
    out["electionRef"] = "PRN Johor 12 Mac 2022"
    out["margin2023"] = seat.get("margin2023") or ""
    maj = MAJORITIES_2022.get(code)
    if maj is not None:
        out["majority2022"] = maj
        out["majority"] = maj
    if ref["party"] == "PAS" and maj and maj >= 800:
        out["status"] = "stronghold"
    elif ref["party"] == "Bersatu" and maj and maj >= 2500:
        out["status"] = "stronghold"
    else:
        out["status"] = seat.get("status") or "battleground"
    out.update(predict_johor_seat(out))
    return out


def main() -> None:
    seats = json.loads(GEO.read_text(encoding="utf-8"))
    enriched = [enrich_seat(s) for s in seats]
    GEO.write_text(json.dumps(enriched, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ Updated {GEO.name} ({len(enriched)} kerusi)")

    if PROD.exists():
        prod = json.loads(PROD.read_text(encoding="utf-8"))
        by_id = {norm_code(s.get("id") or s.get("code")): s for s in enriched}
        merged = []
        for p in prod:
            code = norm_code(p.get("id") or p.get("code"))
            base = by_id.get(code) or {}
            merged.append({**p, **{k: base[k] for k in (
                "party", "incumbent", "winnerName2022", "party2022", "winner2022",
                "party2023", "winner2023", "semasaParti", "semasaKoalisi", "electionRef",
                "majority2022", "majority", "status", "scenarioBase", "scenarioMeta", *SCENARIO_KEYS,
            ) if k in base}})
        PROD.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"✅ Updated {PROD.name}")

    from collections import Counter
    c = Counter(s["party2022"] for s in enriched)
    print("Pecahan parti PRN 2022:", dict(sorted(c.items(), key=lambda x: -x[1])))
    solo50 = sum(1 for s in enriched if (s.get("pasSoloWinProb") or 0) >= 50)
    mn50 = sum(1 for s in enriched if (s.get("pasMnWinProb") or 0) >= 50)
    print(f"Kerusi PAS solo ≥50%: {solo50}/56 · MN bloc ≥50%: {mn50}/56")


if __name__ == "__main__":
    main()
