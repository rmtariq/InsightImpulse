#!/usr/bin/env python3
"""Import PRN_N9_Johor_Melaka_Update_2026.xlsx → JSON manifest under PRN/_shared/."""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from prn_paths import SHARED, ensure_state_dirs  # noqa: E402

DEFAULT_XLSX = (
    ROOT / "JITP_2026/Master_File/Terkini_20062026_PRN_N9_Johor_Melaka_Update_2026.xlsx"
)
FALLBACK_XLSX = Path.home() / "Downloads/PRN_N9_Johor_Melaka_Update_2026.xlsx"
OUT_DIR = SHARED / "excel_intel"
MYT = timezone(timedelta(hours=8))

STATE_MAP = {
    "Negeri Sembilan": "N9",
    "Johor": "Johor",
    "Melaka": "Melaka",
}

# Known fix — Excel row N01 parlimen salah
PARLIMEN_FIX = {
    ("Negeri Sembilan", "N01"): {"parlimen_code": "P128", "parlimen_name": "Seremban"},
}


def _df_records(df: pd.DataFrame) -> list:
    df = df.where(pd.notna(df), None)
    return json.loads(df.to_json(orient="records", force_ascii=False))


def _cell(row, idx: int):
    if idx >= len(row):
        return None
    val = row[idx]
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    return val


def parse_overview_sheet(df: pd.DataFrame) -> dict:
    """Parse unstructured Overview sheet → KPIs, DUN/priority breakdown, notes."""
    rows = df.where(pd.notna(df), None).values.tolist()
    updated_label = None
    kpis: list[dict] = []
    dun_by_state: list[dict] = []
    dun_by_priority: list[dict] = []
    operational_notes: list[str] = []
    section = None
    seen_states: set[str] = set()
    seen_priorities: set[str] = set()

    for row in rows:
        c0 = _cell(row, 0)
        c1 = _cell(row, 1)
        c3 = _cell(row, 3)
        c4 = _cell(row, 4)
        c5 = _cell(row, 5)
        c6 = _cell(row, 6)

        if isinstance(c0, str) and "Updated and verified" in c0:
            updated_label = c0.strip()
            continue

        if c0 == "KPI" and c1 == "Value":
            section = "kpi"
            continue
        if c0 == "State" and c1 == "Status":
            section = "calendar"
            continue
        if c0 == "Operational Notes":
            section = "notes"
            continue

        if section == "kpi" and c0 and c1 is not None:
            metric = str(c0).strip()
            if metric in ("KPI", "Election Operations Calendar"):
                continue
            try:
                value = int(c1) if isinstance(c1, (int, float)) and float(c1).is_integer() else c1
            except (TypeError, ValueError):
                value = c1
            kpis.append({"metric": metric, "value": value})

            if isinstance(c3, str) and c3 in STATE_MAP and c3 not in seen_states:
                seen_states.add(c3)
                dun_by_state.append(
                    {
                        "state": c3,
                        "state_code": STATE_MAP[c3],
                        "dun_count": int(c4) if c4 is not None else 0,
                    }
                )
            if isinstance(c5, str) and c5 not in seen_priorities:
                seen_priorities.add(c5)
                dun_by_priority.append(
                    {"priority": str(c5).strip(), "dun_count": int(c6) if c6 is not None else 0}
                )
            continue

        if section == "notes" and c1 and str(c1).strip():
            note = str(c1).strip()
            if note not in operational_notes:
                operational_notes.append(note)

    return {
        "updated_label": updated_label,
        "kpis": kpis,
        "dun_by_state": dun_by_state,
        "dun_by_priority": dun_by_priority,
        "operational_notes": operational_notes,
    }


def import_workbook(xlsx: Path, copy_to_shared: bool = True) -> dict:
    if not xlsx.exists():
        raise FileNotFoundError(xlsx)

    SHARED.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for st in STATE_MAP.values():
        ensure_state_dirs(st)

    dest_xlsx = SHARED / xlsx.name
    if copy_to_shared and xlsx.resolve() != dest_xlsx.resolve():
        shutil.copy2(xlsx, dest_xlsx)

    xl = pd.ExcelFile(xlsx)
    sheets = {}
    for name in xl.sheet_names:
        sheets[name] = pd.read_excel(xlsx, sheet_name=name)

    dun = sheets["DUN Keywords"].copy()
    for (state, code), fix in PARLIMEN_FIX.items():
        mask = (dun["state"] == state) & (dun["dun_code"] == code)
        for k, v in fix.items():
            dun.loc[mask, k] = v

    overview = parse_overview_sheet(sheets["Overview"])
    qt = sheets["Query Templates"]
    lv = sheets["Local Voices"]
    local_by_state = {
        STATE_MAP[st]: int((lv["state"] == st).sum())
        for st in STATE_MAP
        if st in lv["state"].values
    }
    query_by_state = {
        STATE_MAP[st]: int((qt["state"] == st).sum())
        for st in STATE_MAP
        if st in qt["state"].values
    }

    manifest = {
        "meta": {
            "source_file": str(dest_xlsx),
            "imported_at": datetime.now(MYT).isoformat(timespec="seconds"),
            "sheets": list(xl.sheet_names),
            "dun_count": len(dun),
            "query_template_count": len(qt),
            "url_source_count": len(sheets["URL Sources"]),
            "fixes_applied": list(PARLIMEN_FIX.keys()),
        },
        "overview": overview,
        "election_calendar": _df_records(sheets["Election Calendar"]),
        "dun_keywords": _df_records(dun),
        "query_templates": _df_records(sheets["Query Templates"]),
        "url_sources": _df_records(sheets["URL Sources"]),
        "local_voices": _df_records(sheets["Local Voices"]),
        "narrative_watch": _df_records(sheets["Narrative Watch"]),
        "source_qa": _df_records(sheets["Source QA"]),
    }

    out_json = OUT_DIR / "prn_excel_intel_manifest.json"
    out_json.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    by_state = OUT_DIR / "by_state"
    by_state.mkdir(parents=True, exist_ok=True)
    for state_label, code in STATE_MAP.items():
        st_qt = qt[qt["state"] == state_label]
        st_dun = dun[dun["state"] == state_label]
        st_urls = sheets["URL Sources"]
        st_urls = st_urls[(st_urls["state"] == state_label) | (st_urls["state"] == "All")]
        payload = {
            "state_code": code,
            "state_label": state_label,
            "dun_count": len(st_dun),
            "query_templates": _df_records(st_qt),
            "dun_keywords": _df_records(st_dun),
            "url_sources": _df_records(st_urls),
        }
        (by_state / f"{code}_excel_intel.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        ref = ROOT / "data/projects/political/PRN" / f"PRN_{code if code != 'N9' else 'N9'}" / "reference"
        ref.mkdir(parents=True, exist_ok=True)
        (ref / "excel_intel_manifest.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    return {"manifest": out_json, "dest_xlsx": dest_xlsx, "stats": manifest["meta"]}


def resolve_xlsx(path: Path | None) -> Path:
    if path and path.exists():
        return path
    if DEFAULT_XLSX.exists():
        return DEFAULT_XLSX
    if FALLBACK_XLSX.exists():
        return FALLBACK_XLSX
    raise FileNotFoundError(f"Excel not found: {path or DEFAULT_XLSX}")


def main() -> int:
    p = argparse.ArgumentParser(description="Import PRN Excel intel workbook")
    p.add_argument("--xlsx", type=Path, default=None, help="Path to Terkini Excel (default: JITP_2026/Master_File/...)")
    p.add_argument("--no-copy", action="store_true")
    args = p.parse_args()
    xlsx = resolve_xlsx(args.xlsx)
    result = import_workbook(xlsx, copy_to_shared=not args.no_copy)
    print(f"✅ Manifest: {result['manifest']}")
    print(f"   Excel copy: {result['dest_xlsx']}")
    for k, v in result["stats"].items():
        print(f"   {k}: {v}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
