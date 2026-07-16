#!/usr/bin/env python3
"""
Jana laporan PDF + DOCX naratif Cina — ikut negeri (N9 · Johor · Melaka).

Usage:
  cd /Users/rmtariq/Documents/InsightPulse
  python3 scripts/generate_prn_chinese_narrative_reports.py
  python3 scripts/generate_prn_chinese_narrative_reports.py --negeri johor
  python3 scripts/generate_prn_chinese_narrative_reports.py --rebuild-data

Output:
  data/projects/political/pas_break_2026/reports/chinese_narrative/
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DASH = ROOT / "n9_chinese_narrative_dashboard"
sys.path.insert(0, str(DASH))

STATE_MAP = {
    "n9": "Negeri Sembilan",
    "negeri sembilan": "Negeri Sembilan",
    "ns": "Negeri Sembilan",
    "johor": "Johor",
    "melaka": "Melaka",
}


def load_data(rebuild: bool = False):
    import pandas as pd
    from utils.build_dataset import build_dataset

    csv_path = DASH / "data/prn_chinese_narrative_posts_3negeri.csv"
    if rebuild or not csv_path.exists():
        print("🔨 Bina semula dataset dashboard...")
        build_dataset()
    if not csv_path.exists():
        raise SystemExit(f"Dataset tidak dijumpai: {csv_path}")
    df = pd.read_csv(csv_path, low_memory=False)
    print(f"📂 Data: {csv_path} ({len(df):,} rekod)")
    if "state" in df.columns:
        print(df["state"].value_counts().to_string())
    return df


def main() -> int:
    parser = argparse.ArgumentParser(description="Jana laporan PDF/DOCX naratif Cina per negeri")
    parser.add_argument(
        "--negeri",
        choices=["all", "n9", "negeri sembilan", "johor", "melaka"],
        default="all",
        help="Negeri untuk laporan (default: all = 3 negeri)",
    )
    parser.add_argument("--rebuild-data", action="store_true", help="Bina semula CSV dashboard dahulu")
    parser.add_argument("--executive-only", action="store_true", help="Jana laporan eksekutif sahaja")
    parser.add_argument("--response-kit-only", action="store_true", help="Jana kit respons naratif sahaja")
    parser.add_argument("--appendix-only", action="store_true", help="Jana lampiran analitik sahaja (opsyen)")
    parser.add_argument("--with-appendix", action="store_true", help="Sertakan lampiran analitik")
    parser.add_argument("--output", help="Folder output (optional)")
    args = parser.parse_args()

    executive = not args.appendix_only and not args.response_kit_only
    response_kit = not args.executive_only and not args.appendix_only
    appendix = args.appendix_only or args.with_appendix
    if args.executive_only:
        response_kit = False
    if args.response_kit_only:
        executive = False

    try:
        from docx import Document  # noqa: F401
    except ImportError:
        print("⚠️  python-docx tidak dipasang. Jalankan: pip install python-docx")
        return 1

    df = load_data(rebuild=args.rebuild_data)

    from utils.state_report_generator import DEFAULT_OUT, STATES, generate_state_reports

    states = None
    if args.negeri != "all":
        states = [STATE_MAP[args.negeri.lower()]]

    out_dir = Path(args.output) if args.output else DEFAULT_OUT
    print(f"\n📄 Menjana laporan → {out_dir}\n")

    results = generate_state_reports(
        df, output_dir=out_dir, states=states,
        executive=executive, response_kit=response_kit, appendix=appendix,
    )

    for state, paths in results.items():
        print(f"✅ {state} ({paths['records']} rekod)")
        if paths.get("executive_docx"):
            print(f"   Eksekutif DOCX: {paths['executive_docx']}")
        if paths.get("executive_pdf"):
            print(f"   Eksekutif PDF:  {paths['executive_pdf']}")
        if paths.get("response_kit_docx"):
            print(f"   Kit Respons DOCX: {paths['response_kit_docx']}")
        if paths.get("response_kit_pdf"):
            print(f"   Kit Respons PDF:  {paths['response_kit_pdf']}")
        if paths.get("appendix_docx"):
            print(f"   Lampiran DOCX:  {paths['appendix_docx']}")
        if paths.get("appendix_pdf"):
            print(f"   Lampiran PDF:   {paths['appendix_pdf']}")

    print(f"\n📋 Indeks: {out_dir / 'README_LAPORAN.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
