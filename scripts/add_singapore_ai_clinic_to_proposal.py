#!/usr/bin/env python3
"""Insert Singapore AI Discovery Clinic strategic addendum into InsightPulse proposal PDF."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Flowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
SRC = Path("/Users/rmtariq/Downloads/InsightPulse_Proposal_Strategik_2026_V3.0.pdf")
INSERT = ROOT / "tmp_singapore_ai_clinic_addendum.pdf"
OUT = Path("/Users/rmtariq/Downloads/InsightPulse_Proposal_Strategik_2026_V3.1_Singapore_AI_Clinic.pdf")

NAVY = colors.HexColor("#003366")
GREEN = colors.HexColor("#15803D")
SLATE = colors.HexColor("#1E293B")
GREY = colors.HexColor("#64748B")
LIGHT = colors.HexColor("#F8FAFC")
AMBER_BG = colors.HexColor("#FFF7ED")
GREEN_BG = colors.HexColor("#F0FDF4")


class HRule(Flowable):
    def __init__(self, width: float, color=colors.HexColor("#CBD5E1"), thickness: float = 0.8):
        super().__init__()
        self.width = width
        self.color = color
        self.thickness = thickness
        self.height = 0.2 * cm

    def draw(self):
        self.canv.setStrokeColor(self.color)
        self.canv.setLineWidth(self.thickness)
        self.canv.line(0, 0, self.width, 0)


def p(text: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(text, style)


def build_insert_pdf() -> None:
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="SmallMuted",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=10,
            textColor=GREY,
        )
    )
    styles.add(
        ParagraphStyle(
            name="BodyBM",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9.4,
            leading=12.5,
            textColor=SLATE,
            spaceAfter=6,
        )
    )
    styles.add(
        ParagraphStyle(
            name="HeadingBM",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=15,
            leading=18,
            textColor=NAVY,
            spaceAfter=8,
        )
    )
    styles.add(
        ParagraphStyle(
            name="SubheadBM",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=10.5,
            leading=13,
            textColor=GREEN,
            spaceBefore=4,
            spaceAfter=5,
        )
    )
    styles.add(
        ParagraphStyle(
            name="BoxText",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8.6,
            leading=11.2,
            textColor=SLATE,
        )
    )
    styles.add(
        ParagraphStyle(
            name="BoxTitle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=11,
            textColor=NAVY,
        )
    )

    doc = SimpleDocTemplate(
        str(INSERT),
        pagesize=A4,
        rightMargin=1.45 * cm,
        leftMargin=1.45 * cm,
        topMargin=1.15 * cm,
        bottomMargin=1.15 * cm,
    )

    story = []
    width = A4[0] - 2.9 * cm
    story.append(p("InsightPulse | Proposal Perkongsian Strategik 2026 | SULIT", styles["SmallMuted"]))
    story.append(p("Sisipan Strategik | Pembelajaran daripada Singapore AI Discovery Clinic", styles["SmallMuted"]))
    story.append(HRule(width))
    story.append(Spacer(1, 0.18 * cm))

    story.append(p("6.4 Pemerhatian Pasaran: Singapore AI Discovery Clinic", styles["HeadingBM"]))
    story.append(
        p(
            "Singapura melalui Singapore Artificial Intelligence Association (SAIA) dilaporkan melancarkan "
            "<b>AI Discovery Clinic</b> sebagai pendekatan baharu untuk membantu SME mengenal pasti bagaimana AI "
            "boleh digunakan dalam operasi sebenar. Pendekatan ini menarik kerana ia tidak bermula dengan geran "
            "atau pembelian tool, tetapi dengan <b>diagnosis pain point</b>, pemetaan use case dan cadangan tindakan.",
            styles["BodyBM"],
        )
    )
    story.append(
        p(
            "Isyarat pasaran ini penting: rantau ini sedang bergerak daripada model 'beli software dahulu' kepada "
            "model <b>diagnose dahulu, bina use case, kemudian deploy penyelesaian</b>. Ini selari dengan cara "
            "InsightPulse mahu dibawa ke ekosistem PMKS Malaysia.",
            styles["BodyBM"],
        )
    )

    rows = [
        [
            p("Model AI Discovery Clinic", styles["BoxTitle"]),
            p("Kedudukan InsightPulse", styles["BoxTitle"]),
        ],
        [
            p(
                "<b>Advisory / diagnosis</b><br/>Expert bantu SME kenal pasti masalah sebenar: invoice, customer query, "
                "lead generation, pemasaran, reputasi atau workflow.",
                styles["BoxText"],
            ),
            p(
                "<b>Advisory + platform sebenar</b><br/>InsightPulse bukan sekadar konsultasi. Selepas diagnosis, SME "
                "boleh terus menggunakan dashboard live, social listening, sentiment analysis dan laporan tindakan.",
                styles["BoxText"],
            ),
        ],
        [
            p(
                "<b>Use case mapping</b><br/>Hasil utama ialah cadangan use case AI yang sesuai dengan pain point SME.",
                styles["BoxText"],
            ),
            p(
                "<b>Use case + execution layer</b><br/>InsightPulse boleh menterjemah use case kepada monitoring sebenar: "
                "brand mention, competitor signal, customer feedback, risiko reputasi dan peluang viral.",
                styles["BoxText"],
            ),
        ],
        [
            p(
                "<b>Tiada platform nasional khusus</b><br/>Model clinic berfungsi sebagai front-end advisory kepada ekosistem.",
                styles["BoxText"],
            ),
            p(
                "<b>Platform Malaysia-ready</b><br/>InsightPulse boleh menjadi enjin teknologi di belakang program seumpama "
                "AI Discovery Clinic Malaysia untuk PMKS dan agensi pembangunan usahawan.",
                styles["BoxText"],
            ),
        ],
    ]

    table = Table(rows, colWidths=[8.7 * cm, 8.7 * cm], hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), AMBER_BG),
                ("BACKGROUND", (1, 0), (1, -1), GREEN_BG),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#CBD5E1")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )
    story.append(table)
    story.append(Spacer(1, 0.22 * cm))

    story.append(p("Strategic Play untuk Malaysia", styles["SubheadBM"]))
    bullets = [
        "<b>Jangan compete dengan konsep clinic</b> - InsightPulse boleh melengkapkan model itu sebagai platform selepas diagnosis.",
        "<b>Positioning baharu:</b> AI Discovery + Live Intelligence Platform untuk PMKS Malaysia.",
        "<b>Untuk agensi:</b> bukan hanya bengkel AI, tetapi sistem untuk pantau outcome selepas program.",
        "<b>Untuk SME:</b> mula dengan satu pain point sebenar, kemudian deploy dashboard yang boleh diukur.",
        "<b>Untuk Fiscal / InsightPulse:</b> masuk sebagai Technology Solution Provider (TSP), rakan clinic dan enjin analytics.",
    ]
    for b in bullets:
        story.append(p(f"&bull; {b}", styles["BodyBM"]))

    story.append(Spacer(1, 0.1 * cm))
    story.append(p("Cadangan Program Tambahan: AI Discovery + InsightPulse Pilot", styles["SubheadBM"]))
    pilot_rows = [
        [p("<b>Komponen</b>", styles["BoxTitle"]), p("<b>Output</b>", styles["BoxTitle"])],
        [p("1. Sesi diagnosis 60-90 minit bersama PMKS", styles["BoxText"]), p("Pain point sebenar + AI use case priority", styles["BoxText"])],
        [p("2. Setup InsightPulse dashboard mini", styles["BoxText"]), p("Pantau brand, pelanggan, pesaing dan isu industri", styles["BoxText"])],
        [p("3. Laporan tindakan 30 hari", styles["BoxText"]), p("Senarai tindakan pemasaran / reputasi / pelanggan", styles["BoxText"])],
        [p("4. Portfolio view untuk agensi", styles["BoxText"]), p("Agensi boleh ukur adoption, risiko dan outcome PMKS", styles["BoxText"])],
    ]
    pilot_table = Table(pilot_rows, colWidths=[8.0 * cm, 9.4 * cm], hAlign="LEFT")
    pilot_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), LIGHT),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#CBD5E1")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(pilot_table)
    story.append(Spacer(1, 0.2 * cm))
    story.append(
        p(
            "<b>Kesimpulan:</b> Jika Malaysia mengadaptasi model AI Discovery Clinic seperti Singapura, "
            "InsightPulse boleh diposisikan sebagai platform rujukan tempatan yang menukar sesi diagnosis "
            "kepada tindakan data-driven dan dashboard yang boleh dipantau oleh PMKS serta agensi.",
            styles["BodyBM"],
        )
    )
    story.append(Spacer(1, 0.15 * cm))
    story.append(
        p(
            f"Nota: Sisipan ini disediakan berdasarkan pemerhatian pasaran awam berkaitan AI Discovery Clinic SAIA. "
            f"Dijana: {datetime.now().strftime('%d %b %Y')}.",
            styles["SmallMuted"],
        )
    )

    doc.build(story)


def merge_pdf() -> None:
    build_insert_pdf()
    reader = PdfReader(str(SRC))
    insert = PdfReader(str(INSERT))
    writer = PdfWriter()

    # Insert after current page 6 (after section 6 benefits, before national alignment / implementation).
    for idx, page in enumerate(reader.pages):
        writer.add_page(page)
        if idx == 5:
            writer.add_page(insert.pages[0])

    with OUT.open("wb") as f:
        writer.write(f)
    INSERT.unlink(missing_ok=True)


if __name__ == "__main__":
    merge_pdf()
    print(f"Saved: {OUT}")
