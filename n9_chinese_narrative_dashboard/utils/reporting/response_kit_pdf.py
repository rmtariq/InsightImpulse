"""Kit Respons Naratif — PDF writer."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from utils.report_formatting import pdf_page_template, pdf_styles, pdf_wrapped_table


def write_response_kit_pdf(payload: dict[str, Any], path: Path) -> Path | None:
    try:
        from reportlab.lib.units import cm
        from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer
    except ImportError:
        return None

    st = pdf_styles()
    state = payload["state"]
    short = payload.get("state_short", "")
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(path), pagesize=(595.27, 841.89),
        rightMargin=2 * cm, leftMargin=2 * cm, topMargin=2.2 * cm, bottomMargin=2 * cm,
    )
    story = []

    story.append(Paragraph(payload.get("org", "InsightPulse"), st["title"]))
    story.append(Paragraph(payload["title"], st["title"]))
    story.append(Paragraph(payload["subtitle"], st["subtitle"]))
    story.append(Paragraph(payload.get("tagline", ""), st["body"]))
    story.append(Paragraph(
        f"Dijana: {payload['generated_at']} | Versi {payload['version']} | {payload['classification']}",
        st["body"],
    ))
    story.append(Paragraph(payload.get("disclaimer", ""), st["body"]))
    story.append(PageBreak())

    story.append(Paragraph("Aliran: KESAN → FAHAMI → SAHKAN → TINDAK → UKUR", st["h1"]))
    for phase, detail in payload.get("workflow") or []:
        story.append(Paragraph(f"• <b>{phase}</b> — {detail}", st["bullet"]))

    for item in payload.get("items") or []:
        story.append(PageBreak())
        story.append(Paragraph(
            f"{item['priority']} — {item['issue']} ({item['location']})",
            st["h1"],
        ))

        story.append(Paragraph("1. Apa Isu", st["h2"]))
        story.append(Paragraph(f"Naratif: {item.get('narrative_summary', '—')[:300]}", st["body"]))
        story.append(Paragraph(f"Tindakan: {item.get('operational_action', '—')[:280]}", st["body"]))

        story.append(Paragraph("2. Copy Pos Utama", st["h2"]))
        story.append(Paragraph(f"<b>BM:</b> {item.get('copy_bm_social') or item.get('copy_bm_short', '')}", st["body"]))
        story.append(Paragraph(f"<b>中文:</b> {item.get('copy_zh_social') or item.get('copy_zh_short', '')}", st["body"]))

        cp = item.get("counter_plan") or {}
        story.append(Paragraph("3. Naratif Balas — Cara Balas & Edar", st["h2"]))

        story.append(Paragraph("<b>A. Langkah</b>", st["body"]))
        for i, step in enumerate(cp.get("steps") or [], 1):
            story.append(Paragraph(f"{i}. {step[:200]}", st["bullet"]))

        story.append(Paragraph("<b>B. Balas komen</b>", st["body"]))
        story.append(Paragraph(f"BM: {cp.get('reply_comment_bm', '—')[:350]}", st["body"]))
        story.append(Paragraph(f"中文: {cp.get('reply_comment_zh', '—')[:350]}", st["body"]))

        story.append(Paragraph("<b>C. Pos mengikut platform</b>", st["body"]))
        for pp in cp.get("platform_posts") or []:
            story.append(Paragraph(
                f"<b>{pp.get('platform', '')}</b> ({pp.get('timing', '')}): "
                f"{pp.get('copy', '')[:400]}",
                st["body"],
            ))

        story.append(Paragraph(f"<b>D. JANGAN:</b> {cp.get('dont', '—')[:200]}", st["body"]))
        story.append(Spacer(1, 0.15 * cm))

    doc.build(story, onFirstPage=pdf_page_template(state, short), onLaterPages=pdf_page_template(state, short))
    return path
