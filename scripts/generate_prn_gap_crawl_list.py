#!/usr/bin/env python3
"""
Build gap DUN list (N9 + Johor) for targeted crawl — strict DUN name/code match.

Usage:
  python3 scripts/generate_prn_gap_crawl_list.py
  python3 scripts/generate_prn_gap_crawl_list.py --csv data/combined/Combined_manual_stop_20260621_051322.csv
  python3 scripts/generate_prn_gap_crawl_list.py --strict-threshold 10

Output:
  data/projects/political/PRN/_shared/excel_intel/PRN_GAP_CRAWL_N9_JOHOR.json
  data/projects/political/PRN/_shared/excel_intel/PRN_GAP_CRAWL_QUERIES.txt
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

DEFAULT_CSV = ROOT / "data/combined/Combined_manual_stop_20260621_051322.csv"
DEFAULT_XLSX = ROOT / "JITP_2026/Master_File/Terkini_20062026_PRN_N9_Johor_Melaka_Update_2026.xlsx"
OUT_DIR = ROOT / "data/projects/political/PRN/_shared/excel_intel"
MYT = timezone(timedelta(hours=8))


def strict_mentions(df: pd.DataFrame, code: str, name: str) -> int:
    text_col = "Text" if "Text" in df.columns else "text"
    n = 0
    name_l = name.lower()
    pat = re.compile(rf"\b{re.escape(code.lower())}\b")
    for t in df[text_col].astype(str):
        tl = t.lower()
        if pat.search(tl) or name_l in tl:
            n += 1
    return n


def tier2_query(xlsx: Path, state: str, code: str) -> str:
    qt = pd.read_excel(xlsx, sheet_name="Query Templates")
    row = qt[(qt["state"] == state) & (qt["dun_code"] == code) & (qt["tier"] == "TIER2_DUN_LOCAL")]
    if row.empty:
        return ""
    return str(row.iloc[0].get("query") or "").strip()


def build_query(state: str, code: str, name: str, tier2: str) -> str:
    if tier2 and "when:" in tier2.lower():
        return tier2
    if tier2:
        return f"{tier2} when:7d"
    return f'"{code}" OR "{name}" OR "DUN {name}" OR "ADUN {name}" when:7d'


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    p.add_argument("--xlsx", type=Path, default=DEFAULT_XLSX)
    p.add_argument("--strict-threshold", type=int, default=10,
                   help="Seats with fewer strict mentions are gaps")
    args = p.parse_args()

    if not args.csv.exists():
        print(f"❌ CSV not found: {args.csv}", file=sys.stderr)
        return 1

    manifest = json.loads((OUT_DIR / "prn_excel_intel_manifest.json").read_text(encoding="utf-8"))
    df = pd.read_csv(args.csv, low_memory=False)

    gaps = {"Negeri Sembilan": [], "Johor": []}
    for state in ("Negeri Sembilan", "Johor"):
        duns = [d for d in manifest["dun_keywords"] if d["state"] == state]
        for d in sorted(duns, key=lambda x: x["dun_code"]):
            code, name = d["dun_code"], d["dun_name"]
            mentions = strict_mentions(df, code, name)
            if mentions >= args.strict_threshold:
                continue
            t2 = tier2_query(args.xlsx, state, code) if args.xlsx.exists() else ""
            q = build_query(state, code, name, t2)
            gaps[state].append({
                "dun_code": code,
                "dun_name": name,
                "strict_mentions": mentions,
                "gap_level": "zero" if mentions == 0 else "low",
                "local_issues": d.get("local_issues", ""),
                "query": q,
            })

    payload = {
        "generated": datetime.now(MYT).isoformat(),
        "source_csv": str(args.csv.relative_to(ROOT)),
        "strict_threshold": args.strict_threshold,
        "summary": {
            "N9_gaps": len(gaps["Negeri Sembilan"]),
            "Johor_gaps": len(gaps["Johor"]),
            "total_gaps": len(gaps["Negeri Sembilan"]) + len(gaps["Johor"]),
        },
        "gaps": gaps,
    }

    json_path = OUT_DIR / "PRN_GAP_CRAWL_N9_JOHOR.json"
    txt_path = OUT_DIR / "PRN_GAP_CRAWL_QUERIES.txt"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# PRN GAP CRAWL — one query per line (InsightPulse or crawl_prn_gap_seats.py)",
        f"# Generated {payload['generated']} | threshold strict mentions < {args.strict_threshold}",
        f"# N9 gaps: {payload['summary']['N9_gaps']} | Johor gaps: {payload['summary']['Johor_gaps']}",
        "",
    ]
    for state in ("Negeri Sembilan", "Johor"):
        lines.append(f"# === {state.upper()} ===")
        for g in gaps[state]:
            lines.append(f"# {g['dun_code']} {g['dun_name']} ({g['gap_level']}, n={g['strict_mentions']})")
            lines.append(g["query"])
            lines.append("")
    txt_path.write_text("\n".join(lines), encoding="utf-8")

    print(f"✅ {json_path}")
    print(f"✅ {txt_path}")
    print(f"   N9 gaps: {payload['summary']['N9_gaps']} | Johor gaps: {payload['summary']['Johor_gaps']}")
    for state in ("Negeri Sembilan", "Johor"):
        zero = [g["dun_code"] for g in gaps[state] if g["gap_level"] == "zero"]
        if zero:
            print(f"   {state} zero: {', '.join(zero)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
