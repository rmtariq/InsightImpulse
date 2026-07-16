#!/usr/bin/env python3
"""Load PRN N9 DPI Dec 2025 + ranking updates from Master_File/N9 Excel."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from prn_paths import reference, ensure_state_dirs  # noqa: E402

ensure_state_dirs("N9")
N9_DIR = ROOT / "JITP_2026/Master_File/N9"
RANKING_XLSX = N9_DIR / "Updates_Data DUN ikut ranking.xlsx"
DEMO_XLSX = N9_DIR / "Updates_Demografi pengundi N9 DPI Dec 2025.xlsx"
MN_XLSX = N9_DIR / "Updates_Cadangan kerusi - perbincangan MN.xlsx"
OUT_JSON = reference("N9") / "n9_dpi_updates.json"


def _norm_code(val: Any) -> Optional[str]:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    s = str(val).strip().upper()
    m = re.search(r"\bN(\d{2})\b", s)
    if m:
        return f"N{m.group(1)}"
    if re.fullmatch(r"N\d{2}", s):
        return s
    return None


def _num(val: Any, default: float = 0.0) -> float:
    try:
        if val is None or (isinstance(val, float) and pd.isna(val)):
            return default
        return float(val)
    except (TypeError, ValueError):
        return default


def _int(val: Any, default: int = 0) -> int:
    return int(round(_num(val, default)))


def _pct(val: Any) -> Optional[float]:
    v = _num(val, -1)
    if v < 0:
        return None
    return round(v * 100 if v <= 1 else v, 2)


def _read_sheet(path: Path, sheet: str, header: int = 3) -> pd.DataFrame:
    df = pd.read_excel(path, sheet_name=sheet, header=header)
    df.columns = [str(c).strip() for c in df.columns]
    return df


def _col(df: pd.DataFrame, *names: str) -> Optional[str]:
    for n in names:
        for c in df.columns:
            if c == n or n.lower() in c.lower():
                return c
    return None


def load_ranking_compile() -> Dict[str, dict]:
    df = _read_sheet(RANKING_XLSX, "Compile", header=3)
    kod = _col(df, "Kod")
    out: Dict[str, dict] = {}
    for _, row in df.iterrows():
        code = _norm_code(row.get(kod) if kod else None)
        if not code:
            continue
        slu = str(row.get("Markah SLU", "") or "").strip()
        if slu.lower() in ("", "nan", "none"):
            slu = None
        out[code] = {
            "rankingMajoritiPru15": _int(row.get("Ranking PRU15", 0)) or None,
            "markahSlu": slu,
            "pctMelayuCompile": _pct(row.get("Peratus Pengundi Melayu")),
        }
    return out


def load_melayu_ranking() -> Dict[str, dict]:
    df = _read_sheet(RANKING_XLSX, "(2) Pengundi & % Melayu", header=3)
    kod = _col(df, "Kod")
    out: Dict[str, dict] = {}
    for _, row in df.iterrows():
        code = _norm_code(row.get(kod) if kod else None)
        if not code:
            continue
        total = _int(row.get("Jumlah Pengundi (DPI Dis 2025)", 0))
        melayu = _int(row.get("Bil Pengundi Melayu", 0))
        cina = _int(row.get("Bil Pengundi Cina", 0))
        india = _int(row.get("Bil Pengundi India", 0))
        lain = _int(row.get("Bil Pengundi Lain-Lain", 0) or row.get("Bil Pengundi Lain-lain", 0))
        out[code] = {
            "registeredVotersDpi": total,
            "rankingPengundi": _int(row.get("Ranking bik pengundi", 0)) or None,
            "rankingPctMelayu": _int(row.get("Ranking % pengundi melayu", 0)) or None,
            "votersMelayu": melayu,
            "votersCina": cina,
            "votersIndia": india,
            "votersLain": lain,
            "pctMelayu": _pct(row.get("% Pengundi Melayu")),
            "pctCina": _pct(row.get("% Pengundi Cina")),
            "pctIndia": _pct(row.get("% Pengundi India")),
            "pctLain": _pct(row.get("% Pengundi Lain-lain") or row.get("% Pengundi Lain-Lain")),
        }
    return out


def load_skt_bkc() -> Dict[str, dict]:
    skt_df = _read_sheet(RANKING_XLSX, "(3) SKT 51%", header=3)
    bkc_df = _read_sheet(RANKING_XLSX, "(4) BKC vs modal PRU15", header=3)
    cula_skt_df = pd.read_excel(RANKING_XLSX, sheet_name="(7) Cula vs SKT", header=0)
    cula_skt_df.columns = [str(c).strip() for c in cula_skt_df.columns]

    out: Dict[str, dict] = {}
    for _, row in skt_df.iterrows():
        code = _norm_code(row.get("Kod"))
        if not code:
            continue
        out[code] = {
            "skt51": _int(row.get("SKT 51%", 0)),
            "toc68": _int(row.get("Anggaran TOC 68%", 0)),
            "rankingSkt51": _int(row.get("Ranking SKT 51%", 0)) or None,
        }
    for _, row in bkc_df.iterrows():
        code = _norm_code(row.get("Kod"))
        if not code:
            continue
        out.setdefault(code, {})
        out[code].update({
            "undiPnPru15": _int(row.get("Undi PN PRU15", 0)),
            "bkcModal": _int(row.get("BKC", 0)),
            "rankingBkcModal": _int(row.get("Ranking", 0)) or None,
        })
    kod_c = _col(cula_skt_df, "Kod")
    for _, row in cula_skt_df.iterrows():
        code = _norm_code(row.get(kod_c) if kod_c else None)
        if not code:
            continue
        out.setdefault(code, {})
        out[code].update({
            "culaPasTotal": _int(row.get("Jumlah Pengundi PAS (cula)", 0)),
            "bkcCula": _int(row.get("Baki Kena Cari (BKC)", 0)),
            "rankingBkcCula": _int(row.get("Ranking", 0)) or None,
        })
    return out


def load_cula() -> Dict[str, dict]:
    df = _read_sheet(RANKING_XLSX, "(5) Cula", header=3)
    out: Dict[str, dict] = {}
    for _, row in df.iterrows():
        code = _norm_code(row.get("Kod"))
        if not code:
            continue
        pas_total = row.get("Jumlah Pengundi PAS (B+C+H)")
        if pas_total is None or (isinstance(pas_total, float) and pd.isna(pas_total)):
            continue
        dun = str(row.get("DUN", "") or "").strip()
        if not dun or dun.lower() == "nan" or re.fullmatch(r"[\d.\s%-]+", dun):
            continue
        out[code] = {
            "culaBulans": _int(row.get("B - BULAN", 0)),
            "culaCondong": _int(row.get("C - CONDONG BULAN", 0)),
            "culaLuar": _int(row.get("H - BULAN LUAR KAWASAN", 0)),
            "culaAtasPagar": _int(row.get("A - ATAS PAGAR", 0)),
            "culaDacing": _int(row.get("D - DACING", 0)),
            "culaPasTotal": _int(row.get("Jumlah Pengundi PAS (B+C+H)", 0)),
            "culaPct": _pct(row.get("% cula pengundi PAS")),
            "rankingCulaPct": _int(row.get("Ranking % cula", 0)) or None,
        }
    return out


def load_voter_diff() -> Dict[str, dict]:
    df = _read_sheet(RANKING_XLSX, "(6) Perbezaan pengundi", header=3)
    out: Dict[str, dict] = {}
    for _, row in df.iterrows():
        code = _norm_code(row.get("Kod"))
        if not code:
            continue
        out[code] = {
            "votersPru15": _int(row.get("Jumlah Pengundi (PRU15)", 0)),
            "voterDiff": _int(row.get("Perbezaan", 0)),
            "rankingVoterGrowth": _int(row.get("Ranking Perbezaan", 0)) or None,
        }
    return out


def load_demografi() -> Dict[str, dict]:
    df = pd.read_excel(DEMO_XLSX, sheet_name="Demogradi semua DUN", header=1)
    df.columns = [str(c).strip() for c in df.columns]
    out: Dict[str, dict] = {}
    for _, row in df.iterrows():
        code = _norm_code(row.get("Unnamed: 1") or row.iloc[1] if len(row) > 1 else None)
        if not code:
            continue
        total = _int(row.get("Unnamed: 3") if "Unnamed: 3" in df.columns else row.iloc[3])
        out[code] = {
            "registeredVotersDpi": total,
            "majoritiPru15Signed": _int(row.get("Unnamed: 4") if "Unnamed: 4" in df.columns else row.iloc[4]),
            "gender": {
                "lelaki": _int(row.get("Lelaki", 0)),
                "perempuan": _int(row.get("Perempuan", 0)),
            },
            "age": {
                "18_20": _int(row.get("18-20 Thn", 0)),
                "21_25": _int(row.get("21-25 Thn", 0)),
                "26_40": _int(row.get("26-40 Thn", 0)),
                "41_60": _int(row.get("41-60 Thn", 0)),
                "61_plus": _int(row.get("61-999 Thn", 0)),
            },
            "ethnicity": {
                "melayu": _int(row.get("MELAYU", 0)),
                "cina": _int(row.get("CINA", 0)),
                "india": _int(row.get("INDIA", 0)),
                "lain": _int(row.get("LAIN-LAIN", 0)),
            },
        }
        eth = out[code]["ethnicity"]
        if total > 0:
            out[code]["pctMelayu"] = round(eth["melayu"] / total * 100, 2)
            out[code]["pctCina"] = round(eth["cina"] / total * 100, 2)
            out[code]["pctIndia"] = round(eth["india"] / total * 100, 2)
    return out


DUN_NAME_TO_CODE = {
    "chennah": "N01", "pertang": "N02", "sungai lui": "N03", "klawang": "N04",
    "serting": "N05", "palong": "N06", "jeram padang": "N07", "bahau": "N08",
    "lenggeng": "N09", "nilai": "N10", "chua": "N11", "temiang": "N12",
    "sikamat": "N13", "ampangan": "N14", "juasseh": "N15", "seri menanti": "N16",
    "senaling": "N17", "pilah": "N18", "johol": "N19", "labu": "N20",
    "bukit kepayang": "N21", "rahah": "N22", "mambau": "N23", "rantiau": "N24",
    "paroi": "N25", "negri sembilan": "N26", "ranta": "N27", "kota": "N28",
    "chua": "N29", "bagan pinang": "N31", "sri tanjung": "N32", "rim": "N33",
    "gemas": "N34", "repah": "N36",
}


def load_mn_proposals(seats_name_map: Optional[Dict[str, str]] = None) -> List[dict]:
    if not MN_XLSX.exists():
        return []
    seats_name_map = seats_name_map or {}
    df = pd.read_excel(MN_XLSX, sheet_name="Sheet1", header=2)
    df.columns = [str(c).strip() for c in df.columns]
    rows: List[dict] = []
    current_parlimen = ""
    for _, row in df.iterrows():
        bil = row.get("Bil")
        parlimen = str(row.get("Parlimen", "") or "").strip()
        dun = str(row.get("Kerusi DUN Bertanding", "") or "").strip()
        calon = str(row.get("Bakal Calon", "") or "").strip()
        catatan = str(row.get("Catatan", "") or "").strip()
        if parlimen and parlimen.lower() != "nan":
            current_parlimen = parlimen
        if not dun or dun.lower() in ("nan", "petunjuk", "kerusi pas menang pru 15"):
            continue
        if pd.isna(bil) and not calon:
            continue
        code = None
        for token in dun.split():
            c = _norm_code(token)
            if c:
                code = c
                break
        if not code:
            m = re.search(r"\b(\d{2})\b", dun)
            if m:
                code = f"N{m.group(1)}"
        if not code:
            key = dun.lower().strip()
            code = seats_name_map.get(key) or DUN_NAME_TO_CODE.get(key)
        rows.append({
            "bil": _int(bil) if not pd.isna(bil) else len(rows) + 1,
            "parlimen": current_parlimen,
            "dunName": dun,
            "code": code,
            "calonMn": calon if calon.lower() != "nan" else "",
            "catatanMn": catatan if catatan.lower() != "nan" else "",
        })
    return rows


def merge_dpi_by_code() -> Dict[str, dict]:
    merged: Dict[str, dict] = {}
    sources = [
        load_ranking_compile(),
        load_melayu_ranking(),
        load_skt_bkc(),
        load_voter_diff(),
        load_demografi(),
        load_cula(),  # after skt — cula sheet is authoritative for cula breakdown
    ]
    for src in sources:
        for code, data in src.items():
            merged.setdefault(code, {}).update({k: v for k, v in data.items() if v is not None})
    return merged


def jentera_status(seat: dict) -> str:
    """Operational label from BKC cula vs SKT."""
    bkc = seat.get("bkcCula")
    cula_pct = seat.get("culaPct") or 0
    if bkc is not None and bkc < 0:
        if bkc >= -500:
            return "Hampir capai SKT"
        if cula_pct >= 20:
            return "Asas cula kuat — perlu undi"
        return "Jentera perlu diperkukuh"
    if bkc is not None and bkc >= 0:
        return "Melebihi SKT (modal ada)"
    return "Belum dinilai"


def build_payload(seats_name_map: Optional[Dict[str, str]] = None) -> dict:
    by_code = merge_dpi_by_code()
    mn = load_mn_proposals(seats_name_map)
    mn_by_code = {r["code"]: r for r in mn if r.get("code")}

    seats = []
    for code in sorted(by_code.keys()):
        row = by_code[code]
        row["code"] = code
        row["jenteraStatus"] = jentera_status(row)
        if code in mn_by_code:
            row["mnProposal"] = mn_by_code[code]
        seats.append(row)

    top_cula = sorted(
        [s for s in seats if s.get("culaPct")],
        key=lambda x: x.get("culaPct", 0),
        reverse=True,
    )[:8]
    top_bkc_need = sorted(
        [s for s in seats if s.get("bkcCula") is not None],
        key=lambda x: x.get("bkcCula", 0),
        reverse=True,
    )[:10]
    top_growth = sorted(
        [s for s in seats if s.get("voterDiff")],
        key=lambda x: x.get("voterDiff", 0),
        reverse=True,
    )[:8]

    return {
        "meta": {
            "generated": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
            "dpiAsOf": "Disember 2025 (SPR DPI)",
            "rankingAsOf": "10 Jun 2026",
            "sources": [
                str(RANKING_XLSX.relative_to(ROOT)),
                str(DEMO_XLSX.relative_to(ROOT)),
                str(MN_XLSX.relative_to(ROOT)) if MN_XLSX.exists() else None,
            ],
            "totalSeats": len(seats),
        },
        "byCode": {s["code"]: s for s in seats},
        "mnProposals": mn,
        "highlights": {
            "topCulaPct": [{"code": s["code"], "culaPct": s.get("culaPct"), "culaPasTotal": s.get("culaPasTotal")} for s in top_cula],
            "topBkcCulaNeed": [{"code": s["code"], "bkcCula": s.get("bkcCula"), "skt51": s.get("skt51")} for s in top_bkc_need],
            "topVoterGrowth": [{"code": s["code"], "voterDiff": s.get("voterDiff"), "registeredVotersDpi": s.get("registeredVotersDpi")} for s in top_growth],
        },
    }


def apply_to_seats(seats: List[dict]) -> List[dict]:
    name_map = {str(s.get("name", "")).lower().strip(): s["code"] for s in seats if s.get("name")}
    payload = build_payload(name_map)
    by_code = payload["byCode"]
    for seat in seats:
        code = seat.get("code")
        dpi = by_code.get(code, {})
        if not dpi:
            continue
        seat["dpi"] = dpi
        if dpi.get("registeredVotersDpi"):
            seat["registeredVotersDpi"] = dpi["registeredVotersDpi"]
            seat["registeredVoters"] = dpi["registeredVotersDpi"]
        for key in (
            "pctMelayu", "pctCina", "pctIndia", "rankingMajoritiPru15",
            "markahSlu", "skt51", "bkcModal", "bkcCula", "culaPct",
            "culaPasTotal", "rankingCulaPct", "voterDiff", "jenteraStatus",
            "culaBulans", "culaAtasPagar", "rankingMajoritiPru15",
        ):
            if key in dpi:
                seat[key] = dpi[key]
        if dpi.get("gender"):
            seat["genderLelaki"] = dpi["gender"]["lelaki"]
            seat["genderPerempuan"] = dpi["gender"]["perempuan"]
        if dpi.get("age"):
            seat["ageBands"] = dpi["age"]
        if dpi.get("mnProposal"):
            seat["mnCalon"] = dpi["mnProposal"].get("calonMn")
            seat["mnCatatan"] = dpi["mnProposal"].get("catatanMn")
        eth = dpi.get("ethnicity") or {}
        if eth:
            seat["demografiRingkas"] = (
                f"Melayu {dpi.get('pctMelayu', 0):.1f}% · Cina {dpi.get('pctCina', 0):.1f}% · "
                f"India {dpi.get('pctIndia', 0):.1f}% · DPI Dec 2025"
            )
    return seats


def save_json(seats_name_map: Optional[Dict[str, str]] = None) -> Path:
    payload = build_payload(seats_name_map)
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return OUT_JSON


def main() -> None:
    path = save_json()
    payload = json.loads(path.read_text(encoding="utf-8"))
    print(f"✅ DPI updates saved: {path}")
    print(f"   Kerusi: {payload['meta']['totalSeats']}")
    print(f"   MN proposals: {len(payload['mnProposals'])}")
    print(f"   Top cula: {payload['highlights']['topCulaPct'][:3]}")


if __name__ == "__main__":
    main()
