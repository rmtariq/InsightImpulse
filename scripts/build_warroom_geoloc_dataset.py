#!/usr/bin/env python3
"""Build war room DUN geolocation datasets from the geoloc docx + PRN CSVs."""

from __future__ import annotations

import csv
import json
import re
import shutil
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
DOCX = Path(
    "/Users/rmtariq/Downloads/Laporan geolokasi kerusi pilihan raya "
    "Negeri Sembilan dan Melaka untuk war room.docx"
)
OUT_DIR = ROOT / "data/projects/political/PRN/PRN_N9/reports/war_room/prototype/data"
REACT_N9 = OUT_DIR / "n9_dun_seats.json"
JOhor_CSV = Path("/Users/rmtariq/Downloads/PRN2023_Johor_v2-4.csv")
JOhor_XLSX = Path("/Users/rmtariq/Downloads/prn_johor_geolokasi_war_room.xlsx")
MELAKA_CSV = Path("/Users/rmtariq/Downloads/PRN2023_Melaka_v2-3.csv")

X_NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}

W_NS = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
CONFIDENCE_TO_STATUS = {
    "Tinggi": "stronghold",
    "Sederhana": "battleground",
    "Rendah": "weak",
}


def normalize_code(code: str) -> str:
    code = code.strip().upper().replace(" ", "")
    m = re.match(r"N\.?(\d+)", code)
    if m:
        return f"N.{int(m.group(1)):02d}"
    return code


def parse_docx_table(path: Path) -> list[dict]:
    with zipfile.ZipFile(path) as zf:
        root = ET.fromstring(zf.read("word/document.xml"))

    rows: list[list[str]] = []
    for tr in root.iter(f"{W_NS}tr"):
        cells: list[str] = []
        for tc in tr.iter(f"{W_NS}tc"):
            texts = [t.text or "" for t in tc.iter(f"{W_NS}t")]
            cells.append("".join(texts).strip())
        if cells and any(cells):
            rows.append(cells)

    if not rows or rows[0][0] != "Negeri":
        raise ValueError("Expected geoloc table header 'Negeri' in docx")

    out: list[dict] = []
    for row in rows[1:]:
        if len(row) < 8 or row[1] in ("Kod", "Lat") or row[4] in ("Lat", ""):
            continue
        try:
            lat = float(row[4])
            lon = float(row[5])
        except ValueError:
            continue
        state_key = "N9" if row[0] == "Negeri Sembilan" else "Melaka"
        out.append(
            {
                "state": state_key,
                "stateLabel": row[0],
                "code": normalize_code(row[1]),
                "name": row[2],
                "proxyLocation": row[3],
                "lat": lat,
                "lon": lon,
                "confidence": row[6],
                "note": row[7],
                "status": CONFIDENCE_TO_STATUS.get(row[6], "battleground"),
            }
        )
    return out


def _xlsx_col_row(ref: str) -> tuple[str, int]:
    m = re.match(r"([A-Z]+)(\d+)", ref)
    if not m:
        return "", 0
    return m.group(1), int(m.group(2))


def parse_xlsx_sheet(path: Path, sheet: str = "xl/worksheets/sheet2.xml") -> list[dict[str, str]]:
    """Read one worksheet into list of row dicts keyed by column letter."""
    with zipfile.ZipFile(path) as zf:
        ss_root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
        strings: list[str] = []
        for si in ss_root.findall(".//m:si", X_NS):
            texts = [t.text or "" for t in si.iter(f"{X_NS['m']}t")]
            strings.append("".join(texts))

        sheet_root = ET.fromstring(zf.read(sheet))
        grid: dict[int, dict[str, str]] = {}
        for cell in sheet_root.findall(".//m:c", X_NS):
            ref = cell.attrib.get("r", "")
            col, row = _xlsx_col_row(ref)
            if not col:
                continue
            v = cell.find("m:v", X_NS)
            if v is None or v.text is None:
                continue
            val = strings[int(v.text)] if cell.attrib.get("t") == "s" else v.text
            grid.setdefault(row, {})[col] = val

    if not grid:
        return []

    header_row = min(grid)
    headers = grid[header_row]
    out: list[dict[str, str]] = []
    for row_num in sorted(n for n in grid if n > header_row):
        row = grid[row_num]
        if not any(row.values()):
            continue
        out.append({headers.get(col, col): row.get(col, "") for col in row})
    return out


def parse_johor_xlsx(path: Path) -> list[dict]:
    rows = parse_xlsx_sheet(path)
    if not rows:
        raise ValueError(f"No data rows in Johor xlsx: {path}")

    out: list[dict] = []
    for row in rows:
        code_raw = row.get("Kod_DUN") or row.get("Kod") or ""
        if not code_raw or code_raw == "Kod_DUN":
            continue
        try:
            lat = float(row.get("Latitud", ""))
            lon = float(row.get("Longitud", ""))
        except ValueError:
            continue
        conf = row.get("Tahap_Keyakinan", "Sederhana")
        out.append(
            {
                "state": "Johor",
                "stateLabel": row.get("Negeri", "Johor"),
                "code": normalize_code(code_raw),
                "name": row.get("Nama_Kerusi", ""),
                "district": row.get("Daerah_Proksi", ""),
                "proxyLocation": row.get("Lokasi_Proksi", ""),
                "lat": lat,
                "lon": lon,
                "confidence": conf,
                "note": row.get("Nota_QA") or row.get("Jenis_Titik", ""),
                "mapsUrl": row.get("Pautan_Semak_Peta", ""),
                "status": "battleground",
            }
        )
    return out


def load_react_n9_status() -> dict[str, dict]:
    if not REACT_N9.exists():
        return {}
    seats = json.loads(REACT_N9.read_text(encoding="utf-8"))
    return {normalize_code(s["id"]): s for s in seats}


def load_prn_csv(path: Path, state_key: str) -> list[dict]:
    if not path.exists():
        return []
    rows: list[dict] = []
    with path.open(newline="", encoding="utf-8-sig") as fh:
        for row in csv.DictReader(fh):
            code = normalize_code(row["seat_code"])
            rows.append(
                {
                    "id": code,
                    "state": state_key,
                    "stateLabel": row["state"],
                    "name": row["seat_name"],
                    "incumbent": row.get("winner_name") or "",
                    "party": row.get("winner_coalition") or row.get("winner_party") or "",
                    "margin2023": "",
                    "sentiment": 50,
                    "issues": ["PRN baseline"],
                    "action": "Pantau — data geolokasi belum dimuktamadkan",
                    "status": "battleground",
                    "proxyLocation": row["seat_name"],
                    "lat": None,
                    "lon": None,
                    "confidence": "Pending",
                    "geoNote": "Senarai kerusi PRN2023 — geo layer belum disertakan",
                }
            )
    return rows


def build_n9(geo_rows: list[dict], react_by_code: dict[str, dict]) -> list[dict]:
    seats: list[dict] = []
    for g in geo_rows:
        if g["state"] != "N9":
            continue
        react = react_by_code.get(g["code"], {})
        seats.append(
            {
                "id": g["code"],
                "name": g["name"],
                "status": react.get("status", g["status"]),
                "incumbent": react.get("incumbent", ""),
                "party": react.get("party", ""),
                "margin2023": react.get("margin2023", ""),
                "sentiment": react.get("sentiment", 50),
                "issues": react.get("issues", ["PRN"]),
                "demo": react.get("demo", {}),
                "action": react.get("action", g["note"]),
                "proxyLocation": g["proxyLocation"],
                "lat": g["lat"],
                "lon": g["lon"],
                "confidence": g["confidence"],
                "geoNote": g["note"],
            }
        )
    return seats


def build_melaka(geo_rows: list[dict], prn_rows: list[dict]) -> list[dict]:
    prn_by_code = {r["id"]: r for r in prn_rows}
    seats: list[dict] = []
    for g in geo_rows:
        if g["state"] != "Melaka":
            continue
        prn = prn_by_code.get(g["code"], {})
        seats.append(
            {
                "id": g["code"],
                "name": g["name"],
                "status": "battleground",
                "incumbent": prn.get("incumbent", ""),
                "party": prn.get("party", ""),
                "margin2023": prn.get("margin2023", ""),
                "sentiment": prn.get("sentiment", 48),
                "issues": prn.get("issues", ["PRN baseline"]),
                "demo": {},
                "action": "Semak semula koordinat JAPERUN sebelum routing lapangan",
                "proxyLocation": g["proxyLocation"],
                "lat": g["lat"],
                "lon": g["lon"],
                "confidence": g["confidence"],
                "geoNote": g["note"],
            }
        )
    return seats


def build_johor(geo_rows: list[dict], prn_rows: list[dict]) -> list[dict]:
    prn_by_code = {r["id"]: r for r in prn_rows}
    seats: list[dict] = []
    for g in geo_rows:
        prn = prn_by_code.get(g["code"], {})
        seats.append(
            {
                "id": g["code"],
                "name": g["name"],
                "status": "battleground",
                "incumbent": prn.get("incumbent", ""),
                "party": prn.get("party", ""),
                "margin2023": prn.get("margin2023", ""),
                "sentiment": prn.get("sentiment", 50),
                "issues": prn.get("issues", ["PRN baseline"]),
                "demo": {},
                "action": "Overlay GeoJohor + QA GIS sebelum dispatch jentera",
                "district": g.get("district", ""),
                "proxyLocation": g["proxyLocation"],
                "lat": g["lat"],
                "lon": g["lon"],
                "confidence": g["confidence"],
                "geoNote": g.get("note", ""),
                "mapsUrl": g.get("mapsUrl", ""),
            }
        )
    return seats


def main() -> None:
    if not DOCX.exists():
        raise SystemExit(f"Docx not found: {DOCX}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    source_copy = OUT_DIR / "source_geoloc_report.docx"
    if not source_copy.exists():
        shutil.copy2(DOCX, source_copy)

    geo_rows = parse_docx_table(DOCX)
    react_n9 = load_react_n9_status()
    johor_geo: list[dict] = []
    if JOhor_XLSX.exists():
        johor_geo = parse_johor_xlsx(JOhor_XLSX)
        johor_src = OUT_DIR / "source_prn_johor_geolokasi_war_room.xlsx"
        if not johor_src.exists() or johor_src.stat().st_mtime < JOhor_XLSX.stat().st_mtime:
            shutil.copy2(JOhor_XLSX, johor_src)
    johor_prn = load_prn_csv(JOhor_CSV, "Johor")

    n9_seats = build_n9(geo_rows, react_n9)
    melaka_seats = build_melaka(geo_rows, load_prn_csv(MELAKA_CSV, "Melaka"))
    johor_seats = build_johor(johor_geo, johor_prn) if johor_geo else johor_prn

    # Write combined CSV (N9 + Melaka from docx)
    csv_path = OUT_DIR / "prn_geoloc_n9_melaka.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "state",
                "stateLabel",
                "code",
                "name",
                "proxyLocation",
                "lat",
                "lon",
                "confidence",
                "note",
            ],
        )
        writer.writeheader()
        for g in geo_rows:
            writer.writerow({k: g[k] for k in writer.fieldnames if k in g})

    if johor_geo:
        johor_csv = OUT_DIR / "prn_geoloc_johor.csv"
        with johor_csv.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(
                fh,
                fieldnames=[
                    "state",
                    "code",
                    "name",
                    "district",
                    "proxyLocation",
                    "lat",
                    "lon",
                    "confidence",
                    "note",
                    "mapsUrl",
                ],
            )
            writer.writeheader()
            for g in johor_geo:
                writer.writerow(
                    {
                        "state": "Johor",
                        "code": g["code"],
                        "name": g["name"],
                        "district": g.get("district", ""),
                        "proxyLocation": g["proxyLocation"],
                        "lat": g["lat"],
                        "lon": g["lon"],
                        "confidence": g["confidence"],
                        "note": g.get("note", ""),
                        "mapsUrl": g.get("mapsUrl", ""),
                    }
                )

    for key, seats in [("N9", n9_seats), ("Melaka", melaka_seats), ("Johor", johor_seats)]:
        path = OUT_DIR / f"warroom_dun_{key}.json"
        path.write_text(json.dumps(seats, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Wrote {path.name}: {len(seats)} seats")

    meta = {
        "source": {
            "N9_Melaka": str(DOCX.name),
            "Johor": str(JOhor_XLSX.name) if JOhor_XLSX.exists() else "PRN2023 CSV only",
        },
        "generatedFrom": "build_warroom_geoloc_dataset.py",
        "counts": {"N9": len(n9_seats), "Melaka": len(melaka_seats), "Johor": len(johor_seats)},
        "notes": {
            "N9": "Geo rasmi/semi-rasmi + status war room React",
            "Melaka": "Geo JAPERUN (readiness layer) — bukan PRN diwartakan setakat Jun 2026",
            "Johor": "Geo proksi 56 kerusi (34 Tinggi, 21 Sederhana, 1 Rendah) — overlay GeoJohor sebelum lapangan",
        },
    }
    (OUT_DIR / "warroom_dun_meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("Done.", meta["counts"])


if __name__ == "__main__":
    main()
