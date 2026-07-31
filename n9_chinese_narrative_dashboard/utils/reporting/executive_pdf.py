"""Executive 4-page report — PDF writer."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from utils.report_formatting import pdf_page_template, pdf_styles, pdf_wrapped_table


def write_executive_pdf(payload: dict[str, Any], path: Path) -> Path | None:
    try:
        from reportlab.lib.units import cm
        from reportlab.platypus import Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table
    except ImportError:
        return None

    st = pdf_styles()
    state = payload["state"]
    short = payload.get("state_short", "")
    w = 17 * cm
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(str(path), pagesize=(595.27, 841.89),
                            rightMargin=2 * cm, leftMargin=2 * cm, topMargin=2.2 * cm, bottomMargin=2 * cm)
    story = []

    # Cover
    story.append(Paragraph(payload.get("org", "InsightPulse"), st["title"]))
    story.append(Paragraph(payload["title"], st["title"]))
    story.append(Paragraph(payload["subtitle"], st["subtitle"]))
    for line in [
        f"Tempoh: {payload['data_period']}",
        f"Dijana: {payload['generated_at']} | Versi {payload['version']}",
        payload["classification"],
    ]:
        story.append(Paragraph(line, st["body"]))
    story.append(PageBreak())

    # Page 1
    story.append(Paragraph("Ringkasan Eksekutif — Baca Dalam 60 Saat", st["h1"]))
    s = payload["status"]
    story.append(Paragraph(f"<b>{s['code']} — {s['label']}</b>: {s['sentence']}", st["body"]))
    kpi_rows = [["Petunjuk", "Nilai"]] + list(payload["kpis"].items())
    story.append(pdf_wrapped_table(kpi_rows[:5], [8 * cm, 9 * cm], st))
    story.append(Spacer(1, 0.15 * cm))
    kpi_rows2 = [["Petunjuk", "Nilai"]] + list(payload["kpis"].items())[4:8]
    story.append(pdf_wrapped_table(kpi_rows2, [8 * cm, 9 * cm], st))
    if payload["sentiment"].get("warning"):
        story.append(Paragraph(payload["sentiment"]["warning"], st["body"]))
    charts = payload.get("charts") or {}
    if charts.get("sentiment") and charts.get("issues"):
        story.append(Table(
            [[Image(charts["sentiment"], width=8 * cm, height=5.5 * cm),
              Image(charts["issues"], width=8 * cm, height=5.5 * cm)]],
            colWidths=[8.5 * cm, 8.5 * cm],
        ))
    for title, key in [("A. Apa Sedang Berlaku", "happening"), ("B. Mengapa Ia Penting", "important"),
                       ("C. Keputusan Diperlukan Hari Ini", "decisions")]:
        story.append(Paragraph(title, st["h2"]))
        for item in payload["bullets"].get(key, []):
            story.append(Paragraph(f"• {item}", st["bullet"]))
    story.append(PageBreak())

    # Page 2
    story.append(Paragraph("Lima Isu Utama", st["h1"]))
    rows = payload.get("top5_issues") or []
    if rows:
        tbl = [["#", "Isu", "Lokasi", "Hantaran", "%Neg", "Interaksi", "Trend", "Prioriti"]]
        for r in rows:
            tbl.append([str(r["rank"]), r["issue"], r["location"], str(r["count"]),
                        f"{r['neg_pct']}%", f"{r['engagement']:,}", r["trend"], r["priority"]])
        story.append(pdf_wrapped_table(tbl, [0.8 * cm, 3 * cm, 2 * cm, 1.5 * cm, 1.2 * cm, 2 * cm, 1.8 * cm, 2.7 * cm], st))
        for r in rows:
            story.append(Paragraph(f"<i>{r['issue']}:</i> {r['why']}", st["body"]))
    story.append(PageBreak())

    # Page 3
    story.append(Paragraph("Papan Tindakan 24 Jam hingga 7 Hari", st["h1"]))
    for act in payload.get("action_board") or []:
        story.append(Paragraph(f"<b>{act['priority']} — {act['issue_location']}</b>", st["h2"]))
        for lbl, key in [("Tindakan", "action"), ("Hasil", "output"), ("Pasukan", "team"),
                         ("Tarikh", "deadline"), ("Bukti", "evidence"), ("KPI", "kpi")]:
            story.append(Paragraph(f"{lbl}: {act.get(key, '—')}", st["body"]))
        story.append(Spacer(1, 0.1 * cm))
    story.append(PageBreak())

    # Page 4
    story.append(Paragraph("Risiko, Pengesahan dan Susulan", st["h1"]))
    story.append(Paragraph("A. Risiko Utama", st["h2"]))
    for r in payload.get("top_risks") or []:
        story.append(Paragraph(f"• {r['reason']} ({r['location']})", st["bullet"]))
    story.append(Paragraph("B. Dakwaan Memerlukan Pengesahan", st["h2"]))
    for c in payload.get("claims") or []:
        url = c.get("url", "")
        link = f'<link href="{url}">{url[:60]}</link>' if url.startswith("http") else url
        story.append(Paragraph(f"• {c['summary'][:120]} — {link}", st["body"]))
    story.append(Paragraph("C. Pelan Masa", st["h2"]))
    for phase, detail in payload.get("timeline") or []:
        story.append(Paragraph(f"• <b>{phase}</b> — {detail}", st["bullet"]))
    nx = payload.get("next_report") or {}
    story.append(Paragraph(f"D. Laporan seterusnya: {nx.get('datetime', '—')}", st["h2"]))
    for field in payload.get("signoff") or []:
        story.append(Paragraph(f"{field}: _______________", st["body"]))

    doc.build(story, onFirstPage=pdf_page_template(state, short), onLaterPages=pdf_page_template(state, short))
    return path
