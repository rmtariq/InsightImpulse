"""Generate Executive Action + Response Kit reports per negeri."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
INSIGHT_ROOT = ROOT.parent
DEFAULT_OUT = INSIGHT_ROOT / "data/projects/political/pas_break_2026/reports/chinese_narrative"

STATES = ["Negeri Sembilan", "Johor", "Melaka"]

STATE_META: dict[str, dict[str, str]] = {
    "Negeri Sembilan": {"short": "N9", "slug": "negeri_sembilan"},
    "Johor": {"short": "Johor", "slug": "johor"},
    "Melaka": {"short": "Melaka", "slug": "melaka"},
}


def generate_state_reports(
    df: pd.DataFrame,
    output_dir: Path | None = None,
    states: list[str] | None = None,
    *,
    executive: bool = True,
    response_kit: bool = True,
    appendix: bool = False,
) -> dict[str, dict[str, str]]:
    from utils.reporting.analytical_appendix import build_appendix_payload
    from utils.reporting.appendix_docx import write_appendix_docx
    from utils.reporting.appendix_pdf import write_appendix_pdf
    from utils.reporting.executive_docx import write_executive_docx
    from utils.reporting.executive_payload import build_executive_payload
    from utils.reporting.executive_pdf import write_executive_pdf
    from utils.reporting.response_kit_docx import write_response_kit_docx
    from utils.reporting.response_kit_payload import build_response_kit_payload
    from utils.reporting.response_kit_pdf import write_response_kit_pdf

    out = output_dir or DEFAULT_OUT
    out.mkdir(parents=True, exist_ok=True)
    chosen = states or STATES
    results: dict[str, dict[str, str]] = {}

    for state in chosen:
        if state not in STATE_META:
            continue
        meta = STATE_META[state]
        slug = meta["slug"]
        sub = df[df["state"].astype(str) == state].copy() if "state" in df.columns else df.copy()
        if "published_at" in sub.columns:
            sub["published_at"] = pd.to_datetime(sub["published_at"], errors="coerce")

        chart_dir = out / "_charts" / slug
        exec_payload = build_executive_payload(df, state, meta, chart_dir=chart_dir)
        ts = exec_payload["generated_at_file"]
        paths: dict[str, str] = {"records": str(len(sub))}

        if executive:
            base_e = f"PRN_Executive_{slug}_{ts}"
            docx_e = out / f"{base_e}.docx"
            pdf_e = out / f"{base_e}.pdf"
            write_executive_docx(exec_payload, docx_e)
            pdf_ok = write_executive_pdf(exec_payload, pdf_e)
            paths["executive_docx"] = str(docx_e)
            paths["executive_pdf"] = str(pdf_e) if pdf_ok else ""
            paths["docx"] = paths["executive_docx"]
            paths["pdf"] = paths["executive_pdf"]

        if response_kit:
            kit_payload = build_response_kit_payload(df, state, meta)
            base_k = f"PRN_Respons_{slug}_{ts}"
            docx_k = out / f"{base_k}.docx"
            pdf_k = out / f"{base_k}.pdf"
            write_response_kit_docx(kit_payload, docx_k)
            pdf_ok_k = write_response_kit_pdf(kit_payload, pdf_k)
            paths["response_kit_docx"] = str(docx_k)
            paths["response_kit_pdf"] = str(pdf_k) if pdf_ok_k else ""

        if appendix:
            ap = build_appendix_payload(sub, state, meta)
            base_a = f"PRN_Lampiran_{slug}_{ts}"
            docx_a = out / f"{base_a}.docx"
            pdf_a = out / f"{base_a}.pdf"
            write_appendix_docx(ap, docx_a)
            pdf_ok_a = write_appendix_pdf(ap, pdf_a)
            paths["appendix_docx"] = str(docx_a)
            paths["appendix_pdf"] = str(pdf_a) if pdf_ok_a else ""

        results[state] = paths

    idx = [
        "# Laporan Naratif Cina PRN — Indeks",
        f"Dijana: {datetime.now():%Y-%m-%d %H:%M}",
        "",
        "## Format",
        "- **Laporan Tindakan Eksekutif** — maks. 4 muka surat + cover (PDF/DOCX)",
        "- **Kit Respons Naratif** — isu → platform → copy → naratif balas → kelulusan (PDF/DOCX)",
        "- **Lampiran Analitik** — data terperinci (opsyen, `--appendix-only`)",
        "",
    ]
    for state, p in results.items():
        idx.append(f"## {state} ({p['records']} rekod)")
        if p.get("executive_docx"):
            idx.append(f"- Eksekutif DOCX: `{p['executive_docx']}`")
        if p.get("executive_pdf"):
            idx.append(f"- Eksekutif PDF: `{p['executive_pdf']}`")
        if p.get("response_kit_docx"):
            idx.append(f"- Kit Respons DOCX: `{p['response_kit_docx']}`")
        if p.get("response_kit_pdf"):
            idx.append(f"- Kit Respons PDF: `{p['response_kit_pdf']}`")
        if p.get("appendix_docx"):
            idx.append(f"- Lampiran DOCX: `{p['appendix_docx']}`")
        if p.get("appendix_pdf"):
            idx.append(f"- Lampiran PDF: `{p['appendix_pdf']}`")
        idx.append("")
    (out / "README_LAPORAN.md").write_text("\n".join(idx), encoding="utf-8")
    return results
