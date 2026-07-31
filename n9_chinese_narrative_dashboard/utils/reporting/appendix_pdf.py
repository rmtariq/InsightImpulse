"""Analytical appendix — PDF writer."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from utils.report_formatting import pdf_page_template, pdf_styles, pdf_wrapped_table


def write_appendix_pdf(payload: dict[str, Any], path: Path) -> Path | None:
    try:
        from reportlab.lib.units import cm
        from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer
    except ImportError:
        return None

    st = pdf_styles()
    state = payload["state"]
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(str(path), pagesize=(595.27, 841.89),
                            rightMargin=2 * cm, leftMargin=2 * cm, topMargin=2.2 * cm, bottomMargin=2 * cm)
    story = []
    story.append(Paragraph(f"Lampiran Analitik — {state}", st["title"]))
    story.append(Paragraph(f"{payload['record_count']:,} rekod", st["subtitle"]))

    story.append(Paragraph("Metodologi", st["h1"]))
    for line in payload.get("methodology") or []:
        story.append(Paragraph(f"• {line}", st["bullet"]))

    story.append(Paragraph("Suara Komuniti", st["h1"]))
    for v in payload.get("voice_quotes") or []:
        story.append(Paragraph(f"<b>[{v['platform']}]</b> {v['original'][:180]}", st["body"]))

    for title, key in [("Sentimen", "sentiment"), ("Platform", "platform"), ("Isu", "issues")]:
        rows = payload.get("tables", {}).get(key) or []
        if rows:
            story.append(Paragraph(title, st["h2"]))
            story.append(pdf_wrapped_table([["Kategori", "Bil"]] + rows, [11 * cm, 6 * cm], st))

    story.append(PageBreak())
    story.append(Paragraph("Sampel Hantaran", st["h1"]))
    posts = payload.get("all_posts_sample") or []
    if posts:
        tbl = [["Platform", "Isu", "Sentimen", "Petikan"]] + [r[:4] for r in posts[:30]]
        story.append(pdf_wrapped_table(tbl, [2 * cm, 2.5 * cm, 1.5 * cm, 11 * cm], st))

    doc.build(story, onFirstPage=pdf_page_template(state, payload.get("meta", {}).get("short", "")),
              onLaterPages=pdf_page_template(state, payload.get("meta", {}).get("short", "")))
    return path
