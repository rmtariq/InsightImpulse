#!/usr/bin/env python3
"""Generate PPT + PDF report from PRN N9 MN negotiation dashboard payload."""
from __future__ import annotations

import subprocess
import sys
from datetime import datetime
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import MSO_AUTO_SIZE, PP_ALIGN
from pptx.util import Inches, Pt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from prn_paths import reports, ensure_state_dirs  # noqa: E402
from generate_prn_n9_mn_presentation import build_payload  # noqa: E402

MAJORITY_N9 = 19
BERSAMA_SLIDER_PCT = 3

ensure_state_dirs("N9")
OUT_PPT = reports("N9") / "dashboards/prn-n9-mn-pas-bn-presentation.pptx"
OUT_PPT_COPY = ROOT / "JITP_2026/Master_File/N9/prn-n9-mn-pas-bn-presentation.pptx"
OUT_PDF = reports("N9") / "dashboards/prn-n9-mn-pas-bn-presentation.pdf"
OUT_PDF_COPY = ROOT / "JITP_2026/Master_File/N9/prn-n9-mn-pas-bn-presentation.pdf"
OUT_PRINT_HTML = reports("N9") / "dashboards/prn-n9-mn-pas-bn-print.html"
DESKTOP_DIR = Path.home() / "Desktop/N9"
DESKTOP_PPT = DESKTOP_DIR / "PRN_N9_MN_Justifikasi_36Kerusi.pptx"
DESKTOP_PDF = DESKTOP_DIR / "PRN_N9_MN_Justifikasi_36Kerusi.pdf"
DESKTOP_KIT_DIR = Path.home() / "Desktop/PRN_Johor_N9_Crawl_Update_Kit"
DESKTOP_KIT_PPT = DESKTOP_KIT_DIR / "PRN_N9_MN_Justifikasi_36Kerusi.pptx"

NAVY = RGBColor(0, 51, 102)
GREEN = RGBColor(26, 127, 90)
RED = RGBColor(200, 16, 46)
GREY = RGBColor(100, 116, 139)
WHITE = RGBColor(255, 255, 255)
SLATE = RGBColor(30, 41, 59)


def _blank(prs: Presentation):
    return prs.slides.add_slide(prs.slide_layouts[6])


def _header_bar(slide, title: str):
    bar = slide.shapes.add_shape(1, Inches(0), Inches(0), Inches(10), Inches(0.92))
    bar.fill.solid()
    bar.fill.fore_color.rgb = NAVY
    bar.line.fill.background()
    tb = slide.shapes.add_textbox(Inches(0.45), Inches(0.1), Inches(9.1), Inches(0.65))
    tf = tb.text_frame
    tf.text = title
    p = tf.paragraphs[0]
    p.font.size = Pt(24)
    p.font.bold = True
    p.font.color.rgb = WHITE


def _footer(slide, text: str = "InsightPulse · PRN Negeri Sembilan 2026 · Dalaman Muafakat"):
    foot = slide.shapes.add_textbox(Inches(0.4), Inches(7.05), Inches(9.2), Inches(0.35))
    tf = foot.text_frame
    tf.text = text
    p = tf.paragraphs[0]
    p.font.size = Pt(9)
    p.font.color.rgb = GREY


def _title_slide(prs: Presentation, meta: dict):
    s = _blank(prs)
    box = s.shapes.add_textbox(Inches(0.5), Inches(1.6), Inches(9), Inches(1.4))
    tf = box.text_frame
    tf.text = "Perbincangan Muafakat PAS + BN/UMNO"
    p = tf.paragraphs[0]
    p.font.size = Pt(36)
    p.font.bold = True
    p.font.color.rgb = NAVY
    p.alignment = PP_ALIGN.CENTER

    sub = s.shapes.add_textbox(Inches(0.5), Inches(2.9), Inches(9), Inches(0.7))
    st = sub.text_frame
    st.text = "PRN Negeri Sembilan 2026 — Justifikasi 36 Kerusi DUN"
    st.paragraphs[0].font.size = Pt(22)
    st.paragraphs[0].font.color.rgb = GREEN
    st.paragraphs[0].font.bold = True
    st.paragraphs[0].alignment = PP_ALIGN.CENTER

    meta_box = s.shapes.add_textbox(Inches(0.5), Inches(4.0), Inches(9), Inches(1.6))
    mt = meta_box.text_frame
    mt.text = f"PAS {meta['pasSeats']} kerusi · UMNO/BN {meta['umnoSeats']} kerusi · Majoriti 19"
    p2 = mt.add_paragraph()
    p2.text = "InsightPulse Analytics Platform"
    p3 = mt.add_paragraph()
    p3.text = meta.get("generated", datetime.now().strftime("%Y-%m-%d %H:%M"))
    for para in mt.paragraphs:
        para.font.size = Pt(16)
        para.font.color.rgb = GREY
        para.alignment = PP_ALIGN.CENTER


def _bullet_slide(prs: Presentation, title: str, bullets: list[str]):
    s = _blank(prs)
    _header_bar(s, title)
    body = s.shapes.add_textbox(Inches(0.55), Inches(1.15), Inches(8.9), Inches(5.7))
    tf = body.text_frame
    tf.word_wrap = True
    for i, text in enumerate(bullets):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = f"• {text}"
        p.font.size = Pt(18)
        p.font.color.rgb = SLATE
        p.space_after = Pt(10)
    _footer(s)


def _table_slide(
    prs: Presentation,
    title: str,
    headers: list[str],
    rows: list[list[str]],
    font_size: int = 9,
):
    s = _blank(prs)
    _header_bar(s, title)
    nrows = len(rows) + 1
    ncols = len(headers)
    height = min(5.8, 0.32 * nrows + 0.5)
    table = s.shapes.add_table(nrows, ncols, Inches(0.35), Inches(1.05), Inches(9.3), Inches(height)).table
    for ci, h in enumerate(headers):
        cell = table.cell(0, ci)
        cell.text = h
        cell.fill.solid()
        cell.fill.fore_color.rgb = RGBColor(241, 245, 249)
        for para in cell.text_frame.paragraphs:
            para.font.bold = True
            para.font.size = Pt(font_size + 1)
    for ri, row in enumerate(rows, start=1):
        for ci, val in enumerate(row):
            cell = table.cell(ri, ci)
            cell.text = val
            cell.text_frame.word_wrap = True
            cell.margin_left = Pt(3)
            cell.margin_right = Pt(3)
            for para in cell.text_frame.paragraphs:
                para.font.size = Pt(font_size)
    _footer(s)


def _fixed_textbox(slide, left: float, top: float, width: float, height: float, *, word_wrap: bool = True):
    """Textbox with fixed bounds — elak teks melimpah & bertindih."""
    box = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    tf = box.text_frame
    tf.word_wrap = word_wrap
    tf.auto_size = MSO_AUTO_SIZE.NONE
    tf.margin_left = Pt(4)
    tf.margin_right = Pt(4)
    tf.margin_top = Pt(2)
    tf.margin_bottom = Pt(2)
    return tf


def _add_para(
    tf,
    text: str,
    size: int = 9,
    bold: bool = False,
    color: RGBColor | None = None,
    space_after: int = 2,
    first: bool = False,
    align: PP_ALIGN | None = None,
):
    p = tf.paragraphs[0] if first else tf.add_paragraph()
    p.text = text
    p.font.size = Pt(size)
    p.font.bold = bold
    p.font.color.rgb = color or SLATE
    p.space_after = Pt(space_after)
    if align is not None:
        p.alignment = align
    return p


def _fit(text: str, limit: int) -> str:
    """Potong teks pada sempadan perkataan (tiada perkataan terpotong tengah)."""
    text = str(text or "").strip()
    if len(text) <= limit:
        return text
    cut = text[:limit].rstrip()
    sp = cut.rfind(" ")
    if sp > limit * 0.5:
        cut = cut[:sp].rstrip()
    return cut.rstrip(",;:·-") + "…"


def _hex_rgb(h: str) -> RGBColor:
    h = (h or "#64748b").lstrip("#")
    if len(h) != 6:
        return GREY
    return RGBColor(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def _coalition_majority_slide(prs: Presentation, scenarios: list[dict]):
    """Mirror dashboard — Peluang Majoriti Kerajaan N9."""
    s = _blank(prs)
    _header_bar(s, "Peluang Majoriti Kerajaan N9 — 7 Senario")
    sub = _fixed_textbox(s, 0.45, 0.98, 9.1, 0.38)
    _add_para(
        sub,
        f"P(capai ≥{MAJORITY_N9}/36 kerusi) · bukan % undi · 7-bloc SPR+model · "
        f"Bersama −{BERSAMA_SLIDER_PCT}% PH · #4 PN tanpa Bersatu · #7 PN + Bersatu",
        8, False, GREY, 0, first=True,
    )
    y0 = 1.42
    row_h = 0.58
    for i, c in enumerate(scenarios[:8]):
        y = y0 + i * row_h
        name = c.get("name") or "—"
        mp = c.get("majorityPct") or c.get("pct") or 0
        seats = c.get("seatLabel") or (f"~{c.get('expectedSeats')}/36" if c.get("expectedSeats") is not None else "—")
        color = _hex_rgb(c.get("color"))

        nl = _fixed_textbox(s, 0.45, y, 3.35, 0.22)
        _add_para(nl, _fit(name, 42), 9, "★" in name, NAVY if "★" not in name else RGBColor(168, 85, 247), 0, first=True)

        sl = _fixed_textbox(s, 3.85, y, 1.05, 0.22)
        _add_para(sl, str(seats), 8, False, GREY, 0, first=True)

        bar_bg = s.shapes.add_shape(1, Inches(4.95), Inches(y + 0.04), Inches(3.55), Inches(0.18))
        bar_bg.fill.solid()
        bar_bg.fill.fore_color.rgb = RGBColor(226, 232, 240)
        bar_bg.line.fill.background()
        bar_w = max(0.08, 3.55 * min(100, mp) / 100)
        bar = s.shapes.add_shape(1, Inches(4.95), Inches(y + 0.04), Inches(bar_w), Inches(0.18))
        bar.fill.solid()
        bar.fill.fore_color.rgb = color
        bar.line.fill.background()

        pl = _fixed_textbox(s, 8.58, y, 0.85, 0.22)
        _add_para(pl, f"{mp}%", 10, True, color, 0, first=True)
        pl.paragraphs[0].alignment = PP_ALIGN.RIGHT

    note = _fixed_textbox(s, 0.45, 6.55, 9.1, 0.45)
    _add_para(
        note,
        "★ #3 MN = senario HQ (elak pecah undi Melayu). Bar = P(capai 19 kerusi), bukan % popular vote.",
        8, False, GREY, 0, first=True,
    )
    _footer(s)


def _decision_guide_slide(prs: Presentation, scenarios: list[dict]):
    """Nasihat keputusan — bila pilih senario mana."""
    top = scenarios[0] if scenarios else {}
    mn = next((x for x in scenarios if x.get("blocId") == "mn"), {})
    pas = next((x for x in scenarios if x.get("blocId") == "pas_solo"), {})
    pn = next((x for x in scenarios if x.get("blocId") == "pn"), {})
    pn7 = next((x for x in scenarios if x.get("blocId") == "pn_plus"), {})
    hung = next((x for x in scenarios if x.get("blocId") == "hung"), {})

    _bullet_slide(prs, "Panduan Keputusan — Senario Terbaik?", [
        f"1️⃣ MUAFakat MN (#3) ★ — P(majoriti) {mn.get('majorityPct', '—')}% · {mn.get('seatLabel', '~20/36')} — "
        "DISYORKAN HQ: elak 3 penjuru, gabung undi PN+BN vs PH.",
        f"2️⃣ PAS Solo (#1) — {pas.get('majorityPct', '—')}% · hanya jika MN gagal dirunding; risiko pecah undi vs UMNO.",
        f"3️⃣ PN tanpa Bersatu (#4) — {pn.get('majorityPct', '—')}% · roster Team PN 2026 (PAS+Pejuang+Wawasan+Gerakan).",
        f"4️⃣ PN + Bersatu (#7) — {pn7.get('majorityPct', '—')}% · bloc SPR penuh; lebih kuat di N20/N34 (jentera Bersatu).",
        f"5️⃣ Risiko hung parliament — {hung.get('majorityPct', '—')}% · rundingan pasca-undi jika tiada bloc ≥19.",
        "RULE OF THUMB: Per kerusi — jika MN% > PAS solo% → contest muafakat; jika PH kuat (DAP) → UMNO/BN contest.",
        "Setiap slide DUN seterusnya papar 7 bar senario kerusi (model + SPR ✓) selari dashboard war room.",
    ])


def _scenario_short_label(label: str) -> str:
    short = {
        "#1 PAS Solo": "#1 PAS",
        "#2 UMNO Solo": "#2 UMNO",
        "#3 MN": "#3 MN",
        "#4 PN tanpa Bersatu": "#4 PN",
        "#7 PN + Bersatu": "#7 PN+",
        "#5 PH": "#5 PH",
        "#6 Bersama": "#6 split",
    }
    return short.get(label, _fit(label, 12))


def _format_scenario_pct(sc: dict) -> str:
    pct = sc.get("pct")
    if pct is None:
        return "—"
    label = str(sc.get("label") or "")
    if "Bersama" in label:
        return f"{float(pct):g}%*"
    val = float(pct)
    return f"{val:.1f}%" if abs(val - round(val)) > 0.05 else f"{int(round(val))}%"


def _spr_label_suffix(win, leader: bool, *, large: bool) -> str:
    """Guna teks ASCII sahaja — elak ○/▸ yang jadi 'o' dalam PowerPoint."""
    parts: list[str] = []
    if win is True:
        parts.append(" [SPR]" if large else "")
    if leader:
        parts.append(" LEAD" if large else "")
    return "".join(parts)


def _draw_seat_scenario_panel(
    slide, seat: dict, left: float, top: float, width: float, height: float,
    *, large: bool = False, show_insight: bool = True,
):
    """7 senario bar — compact (kanan slide kerusi) atau large (slide detail penuh)."""
    scenarios = seat.get("bloc7Scenarios") or []
    if not scenarios:
        return
    bg = slide.shapes.add_shape(1, Inches(left), Inches(top), Inches(width), Inches(height))
    bg.fill.solid()
    bg.fill.fore_color.rgb = RGBColor(255, 255, 255) if not large else RGBColor(248, 250, 252)
    bg.line.color.rgb = RGBColor(203, 213, 225)

    title = "7 SENARIO KERUSI — DETAIL" if large else "7 SENARIO (ringkas)"
    head_fs = 12 if large else 8
    head = _fixed_textbox(slide, left + 0.06, top + 0.03, width - 0.12, 0.2 if large else 0.16)
    _add_para(head, title, head_fs, True, NAVY, 0, first=True)
    if not large:
        sub = head.add_paragraph()
        sub.text = "→ Slide 2/2 penuh"
        sub.font.size = Pt(6)
        sub.font.color.rgb = GREY

    n = len(scenarios[:7])
    head_room = 0.38 if large else 0.28
    row_h = (height - head_room - (0.38 if large and show_insight else 0.06)) / max(n, 1)
    row_h = min(row_h, 0.72 if large else 0.26)
    bar_h = 0.22 if large else 0.09
    lbl_fs = 11 if large else 6
    pct_fs = 10 if large else 6
    pct_w = 0.58 if large else 0.46
    lbl_w = (2.55 if large else 0.98)
    pad = 0.06
    gap = 0.05
    bar_x_off = pad + lbl_w + gap
    bar_w = width - bar_x_off - pct_w - pad

    for i, sc in enumerate(scenarios[:7]):
        y = top + head_room + i * row_h
        raw_lbl = sc.get("label", "—")
        lbl = raw_lbl if large else _scenario_short_label(raw_lbl)
        pct = sc.get("pct") or 0
        win = sc.get("sprWin")
        leader = sc.get("leader")
        color = _hex_rgb(sc.get("color"))
        suffix = _spr_label_suffix(win, leader, large=large)

        tl = _fixed_textbox(slide, left + pad, y, lbl_w, row_h - 0.01, word_wrap=False)
        _add_para(
            tl, f"{lbl}{suffix}".strip(), lbl_fs, leader,
            color if leader else SLATE, 0, first=True,
        )

        bx = left + bar_x_off
        bar_y = y + (0.06 if large else 0.03)
        bar_bg = slide.shapes.add_shape(1, Inches(bx), Inches(bar_y), Inches(bar_w), Inches(bar_h))
        bar_bg.fill.solid()
        bar_bg.fill.fore_color.rgb = RGBColor(241, 245, 249)
        bar_bg.line.fill.background()
        fill_w = max(0.05 if large else 0.04, bar_w * min(100, float(pct)) / 100)
        bar = slide.shapes.add_shape(1, Inches(bx), Inches(bar_y), Inches(fill_w), Inches(bar_h))
        bar.fill.solid()
        bar.fill.fore_color.rgb = color
        bar.line.fill.background()

        pr = _fixed_textbox(
            slide, left + width - pct_w - pad, y, pct_w, row_h - 0.01, word_wrap=False,
        )
        _add_para(
            pr, _format_scenario_pct(sc), pct_fs, leader, color, 0, first=True,
            align=PP_ALIGN.RIGHT,
        )

    if show_insight and large:
        ins = seat.get("bloc7Insight") or ""
        if ins:
            foot_y = top + height - 0.34
            foot = _fixed_textbox(slide, left + 0.06, foot_y, width - 0.12, 0.3)
            _add_para(foot, _fit(ins, 160), 9, False, GREY, 0, first=True)


def _matrix_cell(sc: dict | None) -> str:
    if not sc:
        return "—"
    pct = sc.get("pct")
    if pct is None:
        return "—"
    win = sc.get("sprWin")
    leader = sc.get("leader")
    if "Bersama" in str(sc.get("label", "")):
        return f"{pct}s"
    p = int(pct) if isinstance(pct, (int, float)) and float(pct) == int(pct) else pct
    sfx = "✓" if win else ""
    star = "*" if leader else ""
    return f"{p}{sfx}{star}"


def _scenario_matrix_row(seat: dict) -> list[str]:
    scenarios = seat.get("bloc7Scenarios") or []
    leader = "—"
    for sc in scenarios:
        if sc.get("leader"):
            leader = _fit(sc.get("label", "—").replace("#", ""), 8)
            break
    cells = [_matrix_cell(sc) for sc in scenarios]
    while len(cells) < 7:
        cells.append("—")
    alloc = "PAS" if seat.get("allocation") == "PAS" else "UMNO"
    return [
        seat.get("code", "—"),
        _fit(seat.get("name", "—"), 11),
        alloc[:3],
        *cells[:7],
        leader,
    ]


MATRIX_HEADERS = ["DUN", "Nama", "Agih", "#1", "#2", "#3", "#4", "#7", "#5", "#6", "★Lead"]


def _scenario_matrix_legend_slide(prs: Presentation):
    _bullet_slide(prs, "Appendix — Matrix 36×7 Senario (Cara Baca)", [
        "Setiap sel = % model kerusi · ✓ = menang undi SPR 2023 · * = lead model terkuat",
        "#1 PAS Solo · #2 UMNO Solo · #3 MN · #4 PN tanpa Bersatu · #7 PN + Bersatu · #5 PH · #6 Bersama (split %)",
        "★Lead = senario model tertinggi untuk kerusi itu — banding dengan agihan MN (PAS/UMNO)",
        "Matrix merangkumi 36 DUN — 2 slide (N01–N18 · N19–N36). Detail penuh: 2 slide/kerusi selepas jadual agihan.",
    ])


def _scenario_matrix_slides(prs: Presentation, all_seats: list[dict]):
    sorted_seats = sorted(all_seats, key=lambda x: x.get("code", ""))
    mid = 18
    chunks = [("N01 – N18", sorted_seats[:mid]), ("N19 – N36", sorted_seats[mid:])]
    for title_suffix, chunk in chunks:
        if not chunk:
            continue
        _table_slide(
            prs,
            f"Ringkasan 36 Kerusi × 7 Senario ({title_suffix})",
            MATRIX_HEADERS,
            [_scenario_matrix_row(s) for s in chunk],
            font_size=6,
        )


def _seat_scenario_detail_slide(prs: Presentation, seat: dict):
    """Slide 2/kerusi — 7 senario penuh (besar, mudah dibaca)."""
    s = _blank(prs)
    code = seat["code"]
    name = seat["name"]
    alloc = seat["allocation"]
    inc = seat.get("incumbent") or {}
    is_pas = alloc == "PAS"
    accent = GREEN if is_pas else RED

    _header_bar(s, f"{code} {name} — 7 Senario (Detail)")

    hdr_meta = _fixed_textbox(s, 5.85, 0.12, 3.7, 0.72)
    _add_para(hdr_meta, alloc, 11, True, accent, 2, first=True)
    _add_para(hdr_meta, "Slide 2/2 · senario penuh", 8, False, GREY, 0)
    for p in hdr_meta.paragraphs:
        p.alignment = PP_ALIGN.RIGHT

    meta = _fixed_textbox(s, 0.45, 0.98, 9.1, 0.32)
    inc_lbl = inc.get("label", "—")
    winner = inc.get("winnerName", "")
    maj = seat.get("majority2023", 0)
    pm = seat.get("pctMelayu") or (seat.get("demographics") or {}).get("ethnicity", {}).get("melayu", {}).get("pct", "—")
    _add_para(
        meta,
        f"{inc_lbl} — {winner} · majoriti {maj:,} · Melayu {pm}%"
        + (" · ⚠ Perbincangan" if seat.get("negotiation") else ""),
        9, False, GREY, 0, first=True,
    )

    _draw_seat_scenario_panel(s, seat, 0.45, 1.38, 9.1, 5.35, large=True)

    leg = _fixed_textbox(s, 0.45, 6.82, 9.1, 0.22)
    _add_para(
        leg,
        "[SPR] = bloc menang SPR 2023 · LEAD = prob model tertinggi · * = % pecah undi PH (slider 3%)",
        7, False, GREY, 0, first=True,
    )
    _footer(s)


def _seat_report_slide(prs: Presentation, seat: dict):
    """Slide 1/2 — justifikasi hybrid · layout 2-kolum tanpa overlap."""
    s = _blank(prs)
    code = seat["code"]
    name = seat["name"]
    alloc = seat["allocation"]
    inc = seat.get("incumbent") or {}
    wp = seat.get("winPrediction") or {}
    demo = seat.get("demographics") or {}
    eth = demo.get("ethnicity") or {}
    age = demo.get("ageBands") or {}
    pred = seat.get("demographicPrediction") or {}
    args = (seat.get("arguments") or {}).get("forAllocation") or []
    evidence = (seat.get("arguments") or {}).get("evidence") or []
    score = (seat.get("hybridLayers") or {}).get("hybridPasScore", "—")
    is_pas = alloc == "PAS"
    accent = GREEN if is_pas else RED

    _header_bar(s, f"{code} {name} · Justifikasi MN")

    hdr_meta = _fixed_textbox(s, 5.85, 0.12, 3.7, 0.72)
    _add_para(hdr_meta, f"Skor {score}/100", 10, True, RGBColor(180, 140, 20), 2, first=True)
    _add_para(hdr_meta, alloc, 11, True, accent, 2)
    _add_para(hdr_meta, "Slide 1/2 · hybrid", 8, False, RGBColor(200, 220, 255), 0)
    for p in hdr_meta.paragraphs:
        p.alignment = PP_ALIGN.RIGHT

    pm = eth.get("melayu", {}).get("pct", seat.get("pctMelayu", "—"))
    pc = eth.get("cina", {}).get("pct", seat.get("pctCina", "—"))
    pi = eth.get("india", {}).get("pct", seat.get("pctIndia", "—"))
    muda = age.get("muda", {}).get("pct", "—")
    emas = age.get("tua", {}).get("pct", "—")
    pas_p = wp.get("pasWinProb", "—")
    umno_p = wp.get("umnoWinProb", "—")
    adv = wp.get("pasVsUmnoAdvantage", "—")
    compare = (
        f"PAS {pas_p}% vs UMNO {umno_p}% (+{adv}%)"
        if is_pas else f"UMNO {umno_p}% vs PAS {pas_p}% (+{adv}%)"
    )

    sub = _fixed_textbox(s, 0.45, 0.96, 9.1, 0.28)
    sub_txt = (
        f"{inc.get('label', '—')} — {inc.get('winnerName', '')} · maj {seat.get('majority2023', 0):,}"
        + (" · ⚠ Perbincangan" if seat.get("negotiation") else "")
    )
    _add_para(sub, sub_txt, 9, False, GREY, 0, first=True)

    # ── Demografi (5 kad) ──
    metrics = [
        ("Melayu", f"{pm}%"), ("Cina", f"{pc}%"), ("India", f"{pi}%"),
        ("Muda 18–25", f"{muda}%"), ("Emas 61+", f"{emas}%"),
    ]
    step = 9.1 / len(metrics)
    cw = step - 0.13
    for i, (lbl, val) in enumerate(metrics):
        x = 0.45 + i * step
        box = s.shapes.add_shape(1, Inches(x), Inches(1.28), Inches(cw), Inches(0.5))
        box.fill.solid()
        box.fill.fore_color.rgb = RGBColor(248, 250, 252)
        box.line.color.rgb = RGBColor(203, 213, 225)
        tb = _fixed_textbox(s, x + 0.06, 1.3, cw - 0.1, 0.46)
        _add_para(tb, lbl, 7, False, GREY, 0, first=True)
        _add_para(tb, val, 12, True, NAVY, 0)

    # ── Kolum kiri: strategi (1.88 – 4.05) ──
    strat_bg = s.shapes.add_shape(1, Inches(0.45), Inches(1.88), Inches(4.38), Inches(2.12))
    strat_bg.fill.solid()
    strat_bg.fill.fore_color.rgb = RGBColor(240, 253, 244) if is_pas else RGBColor(254, 242, 242)
    strat_bg.line.color.rgb = accent

    label = (wp.get("allocationLabel") or "—").replace("✅ ", "").replace("⚠ ", "")
    conf = wp.get("winConfidence") or "—"
    why = wp.get("whyReasons") or []
    must = wp.get("mustDo") or []

    strat = _fixed_textbox(s, 0.52, 1.92, 4.24, 2.04)
    _add_para(strat, label, 10, True, accent, 3, first=True)
    _add_para(strat, compare, 9, True, NAVY, 3)
    _add_para(strat, f"Keyakinan: {conf}", 8, False, GREY, 4)
    _add_para(strat, "Kerana:", 8, True, NAVY, 1)
    for w in why[:2]:
        _add_para(strat, f"• {_fit(w, 120)}", 7, False, SLATE, 1)
    _add_para(strat, "Mesti:", 8, True, NAVY, 1)
    for m in must[:2]:
        _add_para(strat, f"• {_fit(m, 120)}", 7, False, SLATE, 1)

    # ── Kolum kanan: 7 senario ringkas SAHAJA (tiada kohort/isyarat di sini) ──
    _draw_seat_scenario_panel(s, seat, 4.95, 1.88, 4.6, 2.12, large=False, show_insight=False)

    # ── Bar penuh: Kohort + Isyarat (4.08 – 4.48) ──
    cohorts = (wp.get("activeCohorts") or [])[:2]
    cohort_txt = " · ".join(_fit(c.get("label", "—"), 22) for c in cohorts) if cohorts else "—"
    local_ctx = seat.get("localContext") or seat.get("clusterKawasan") or "—"
    sm_m = seat.get("socmedMentions") or 0
    sm_eng = seat.get("socmedEngagement") or 0
    sm_neg = seat.get("socmedNegPct")
    sig_bg = s.shapes.add_shape(1, Inches(0.45), Inches(4.08), Inches(9.1), Inches(0.38))
    sig_bg.fill.solid()
    sig_bg.fill.fore_color.rgb = RGBColor(248, 250, 252)
    sig_bg.line.color.rgb = RGBColor(203, 213, 225)
    sig_box = _fixed_textbox(s, 0.52, 4.1, 8.96, 0.34)
    _add_para(sig_box, f"KOHORT SWING: {cohort_txt}", 7, True, GREY, 2, first=True)
    sm_line = f"Socmed: {sm_m:,} mention · {sm_eng:,} eng"
    if sm_neg is not None:
        sm_line += f" · neg {sm_neg}%"
    elif not sm_m:
        sm_line = "Socmed: tiada isyarat ketara"
    _add_para(sig_box, f"ISYARAT: {_fit(local_ctx, 55)} · {sm_line}", 7, False, NAVY, 0)

    # ── Konteks demografi / isu ──
    area = pred.get("areaType") or seat.get("areaType") or "—"
    lean = pred.get("demographicLean") or "—"
    dscore = pred.get("demographicPasScore", "—")
    issues = seat.get("issues") or []
    issue_txt = " · ".join(issues[:2]) if issues else "—"
    demo_bar = _fixed_textbox(s, 0.45, 4.52, 9.1, 0.28)
    _add_para(
        demo_bar,
        f"{area} · condong {lean} ({dscore}/100) · Isu: {_fit(issue_txt, 90)}",
        8, False, SLATE, 0, first=True,
    )

    # ── Mengapa | Bukti (4.85 – 6.78) ──
    sep = s.shapes.add_shape(1, Inches(4.95), Inches(4.85), Inches(0.02), Inches(1.88))
    sep.fill.solid()
    sep.fill.fore_color.rgb = RGBColor(203, 213, 225)
    sep.line.fill.background()

    why_box = _fixed_textbox(s, 0.45, 4.85, 4.4, 1.88)
    _add_para(why_box, f"Mengapa {alloc}?", 9, True, NAVY, 3, first=True)
    for a in args[:3]:
        _add_para(why_box, f"• {_fit(a, 145)}", 7, False, SLATE, 1)

    ev_box = _fixed_textbox(s, 5.1, 4.85, 4.45, 1.88)
    _add_para(ev_box, "Bukti Data", 9, True, NAVY, 3, first=True)
    for e in evidence[:3]:
        _add_para(ev_box, f"• {_fit(e, 145)}", 7, False, GREY, 1)
    if seat.get("socmedMentions"):
        _add_para(
            ev_box,
            f"• Socmed: {seat['socmedMentions']} mention · "
            f"{seat.get('socmedEngagement', 0):,} eng · neg {seat.get('socmedNegPct', '—')}%",
            7, False, GREY, 1,
        )
    demo_ins = seat.get("socmedDemoInsight")
    if demo_ins:
        _add_para(ev_box, f"• Demo hybrid: {_fit(demo_ins, 130)}", 7, False, GREY, 1)

    insight = seat.get("bloc7Insight") or (seat.get("arguments") or {}).get("insight") or ""
    if insight:
        ins = _fixed_textbox(s, 0.45, 6.78, 9.1, 0.2)
        _add_para(ins, _fit(insight, 170), 7, False, GREY, 0, first=True)

    _footer(s)


def _seat_detail_slide(prs: Presentation, seat: dict):
    _seat_report_slide(prs, seat)


def _data_point_total(ev: dict) -> int:
    return (
        int(ev.get("socmedRows") or 0)
        + int(ev.get("postRows") or 0)
        + int(ev.get("commentRows") or 0)
        + int(ev.get("newsCrawled") or 0)
    )


def _catalog_rows(ev: dict) -> list[tuple[str, str, str, str]]:
    """Flatten dataCatalog → (category, name, vol, use)."""
    rows: list[tuple[str, str, str, str]] = []
    for cat in ev.get("dataCatalog") or []:
        label = cat.get("category") or "—"
        for item in cat.get("items") or []:
            rows.append((
                label,
                item.get("name") or "—",
                item.get("vol") or "—",
                item.get("use") or "—",
            ))
    return rows


def _hybrid_model_bullets(ev: dict, meta: dict) -> list[str]:
    eco = ev.get("economic") or {}
    od = ev.get("openData") or {}
    demo = ev.get("hybridDemographic") or {}
    platforms = ", ".join(ev.get("socmedPlatforms") or [
        "Facebook", "Instagram", "TikTok", "X", "YouTube", "Threads",
    ])
    ns = ev.get("nsScopedPosts")
    ns_txt = f" · {ns:,} post N9-scoped" if ns else ""
    demo_txt = ""
    if demo.get("dpiMalay") is not None and demo.get("socmedMalay") is not None:
        demo_txt = (
            f" · DPI Melayu {demo['dpiMalay']}% vs socmed {demo['socmedMalay']}% "
            f"({demo.get('deltaMalay', 0):+.1f}pp)"
        )
    return [
        "HYBRID MODEL — gabungan data berstruktur + tidak berstruktur + ML/DL",
        f"Structured: SPR/DPI 36 DUN · DOSM MyCensus · ranking · PRN 2023 · cadangan MN · BNM OPR {eco.get('oprPct') or '2.75'}% · USD/MYR RM{eco.get('usdMyr') or '4.07'} · {od.get('endpointCount', 29)} API rasmi",
        f"Unstructured: {ev.get('socmedRows', 84071):,} socmed rows · {ev.get('postRows', 31111):,} posts · {ev.get('commentRows', 37892):,} komen · {ev.get('newsCrawled', 0):,} artikel media (BM/EN/CN/Tamil){ns_txt}",
        f"ML Pipeline: Apify crawl 6 platform ({platforms}) → HuggingFace ft-Malay-bert sentiment + emotion + demographic proxy",
        f"Fusion per-DUN: socmed_by_dun + DPI demo_mix nudge · 7-bloc coalition (MN default){demo_txt}",
        f"Output: Skor analitik per kerusi → ramalan PAS/PN 13 / UMNO/BN 23 · P(MN majoriti) ~68%",
        f"Jumlah titik data: {_data_point_total(ev):,}+ · engagement {ev.get('engagementMillions', 169.5)}M · bukan polling SPR",
    ]


def _seat_row(seat: dict) -> list[str]:
    inc = seat.get("incumbent") or {}
    wp = seat.get("winPrediction") or {}
    eth = (seat.get("demographics") or {}).get("ethnicity") or {}
    pm = eth.get("melayu", {}).get("pct", seat.get("pctMelayu", "—"))
    label = _fit(wp.get("allocationLabel") or wp.get("verdict") or "—", 42)
    return [
        seat["code"],
        _fit(seat["name"], 18),
        inc.get("label", "—"),
        f"{pm}%",
        label,
    ]


def build_ppt(data: dict) -> Presentation:
    meta = data["meta"]
    ev = data["evidence"]
    ib = data["incumbentBreakdown"]
    pas = data["pasSeats"]
    umno = data["umnoSeats"]
    totals = ib.get("prn2023Totals") or {}

    prs = Presentation()
    prs.slide_width = Inches(10)
    prs.slide_height = Inches(7.5)

    _title_slide(prs, meta)

    _bullet_slide(prs, "Agenda Perbincangan", [
        "Konteks PRN N9 2026 · Peluang Majoriti 7-bloc · Panduan senario terbaik",
        "Ringkasan MATRIX 36×7 (N01–N36) — semua kerusi satu pandangan",
        "Agihan MN: PAS/PN 13 · UMNO/BN 23",
        "Detail 36 kerusi × 2 slide: justifikasi hybrid + 7 senario penuh",
        "Kerusi ⚠ perbincangan · nota penafian",
    ])

    _bullet_slide(prs, "Konteks PRN Negeri Sembilan 2026", [
        "36 kerusi DUN · Majoriti untuk bentuk kerajaan: 19 kerusi",
        "Penamaan calon: 18 Julai 2026 · Undi awal: 28 Julai · Mengundi: 1 Ogos 2026",
        f"Cadangan muafakat: PAS contest {meta['pasSeats']} · UMNO/BN contest {meta['umnoSeats']}",
        "Objektif: elak pecah undi, maksimumkan peluang 1-vs-1 vs PH",
        "Bahan ini untuk perbincangan dalaman PAS–UMNO — bukan kenyataan awam",
    ])

    _bullet_slide(prs, "Landskap PRN 2023 — Penyandang Semasa", [
        f"PH (DAP/PKR/Amanah): {totals.get('PH', 17)} kerusi",
        f"BN (UMNO/MCA/MIC): {totals.get('BN', 14)} kerusi",
        f"PN (PAS/Bersatu): {totals.get('PN', 5)} kerusi",
        "Muafakat PAS+BN sasarkan flip kerusi PH + pertahan kerusi PN/BN",
        "Agihan MN 13+23 mengambil kira profil demografi & asal milik kerusi",
    ])

    pas_ib = ib.get("pas23") or {}
    umno_ib = ib.get("umno13") or {}
    _bullet_slide(prs, "Agihan MN — Ringkasan (PAS/PN 13 · UMNO/BN 23)", [
        f"PAS/PN 13 kerusi (9 wajib + 4 berhasrat): PN {pas_ib.get('byBloc', {}).get('PN', 0)} · "
        f"BN {pas_ib.get('byBloc', {}).get('BN', 0)} · PH {pas_ib.get('byBloc', {}).get('PH', 0)} (asal milik)",
        f"UMNO/BN 23 kerusi: PH {umno_ib.get('byBloc', {}).get('PH', 0)} · "
        f"BN {umno_ib.get('byBloc', {}).get('BN', 0)} · PN {umno_ib.get('byBloc', {}).get('PN', 0)} (asal milik)",
        f"Purata ramalan kemenangan PAS (13 kerusi PAS/PN): {data['pasWinSummary']['avgPasWinProb']}%",
        f"Purata ramalan kemenangan UMNO (23 kerusi UMNO/BN): {data['umnoWinSummary']['avgUmnoWinProb']}%",
        "Ramalan = perbandingan PAS vs UMNO dalam senario muafakat 1-vs-1 vs PH",
    ])

    _bullet_slide(prs, "Hybrid Model — Structured + Unstructured + ML/DL", _hybrid_model_bullets(ev, meta))

    demo = ev.get("hybridDemographic") or {}
    if demo.get("insight"):
        _bullet_slide(prs, "Demografi Hybrid — DPI vs Naratif Socmed", [
            demo.get("insight", ""),
            f"Melayu DPI {demo.get('dpiMalay')}% vs socmed {demo.get('socmedMalay')}% ({demo.get('deltaMalay', 0):+.1f}pp)",
            "Nudge diterapkan pada bar Peluang Majoriti (#1 PAS · #3 MN · #4/#7 PN · #5 PH)",
            *(demo.get("nudges") or [])[:3],
            f"Production bundle: {ev.get('productionGenerated') or meta.get('generated', '—')}",
        ])

    coalition = data.get("coalitionScenarios") or []
    if coalition:
        _coalition_majority_slide(prs, coalition)
        _decision_guide_slide(prs, coalition)

    eco = ev.get("economic") or {}
    od = ev.get("openData") or {}
    _bullet_slide(prs, "Skala Data & Pipeline Analitik", [
        f"{_data_point_total(ev):,}+ titik data digabungkan merentas 5 kategori sumber",
        f"Engagement: {ev.get('engagementMillions', 56.9)}M · Socmed posts: {ev.get('socmedRows', 69003):,} · Komen: {ev.get('commentRows', 37892):,}",
        f"Media: {ev.get('newsCrawled', 0):,} artikel crawled · {ev.get('newsAnalyzed', 0)} artikel ML Tier {ev.get('newsTier', 'A')} · neg {ev.get('mediaNegPct') or '40'}%",
        f"Pipeline: Crawl → ML Sentiment (HF) → Media NLP → DPI 36 DUN → Skor Analitik → Ramalan kerusi",
        f"Ekonomi: BNM OpenAPI · OpenDOSM · MIDA · Bursa — {od.get('endpointCount', 29)} endpoint registry",
        f"DPI: {meta.get('dpiAsOf', 'Dec 2025')} · Ranking: {meta.get('rankingAsOf', '10 Jun 2026')}",
    ])

    catalog = _catalog_rows(ev)
    if catalog:
        cat_headers = ["Kategori", "Sumber / Fail", "Skala", "Kegunaan"]
        mid = (len(catalog) + 1) // 2
        _table_slide(
            prs, "Senarai Data Digunakan (1/2)", cat_headers,
            [[r[0], _fit(r[1], 52), r[2], _fit(r[3], 72)] for r in catalog[:mid]],
            font_size=8,
        )
        _table_slide(
            prs, "Senarai Data Digunakan (2/2)", cat_headers,
            [[r[0], _fit(r[1], 52), r[2], _fit(r[3], 72)] for r in catalog[mid:]],
            font_size=8,
        )

    headers = ["DUN", "Nama", "Penyandang", "Melayu", "Ramalan"]
    pas_sorted = sorted(pas, key=lambda x: x["code"])
    umno_sorted = sorted(umno, key=lambda x: x["code"])
    umid = (len(umno_sorted) + 1) // 2
    _table_slide(prs, "PAS/PN 13 Kerusi — Senarai Penuh", headers, [_seat_row(s) for s in pas_sorted])
    _table_slide(prs, "UMNO/BN 23 Kerusi — Senarai Penuh (1/2)", headers, [_seat_row(s) for s in umno_sorted[:umid]])
    _table_slide(prs, "UMNO/BN 23 Kerusi — Senarai Penuh (2/2)", headers, [_seat_row(s) for s in umno_sorted[umid:]])

    all_sorted = sorted(data.get("allSeats") or pas + umno, key=lambda x: x["code"])
    _scenario_matrix_legend_slide(prs)
    _scenario_matrix_slides(prs, all_sorted)

    _bullet_slide(prs, "Justifikasi Terperinci — PAS/PN 13 Kerusi (2 slide/kerusi)", [
        "Slide 1: justifikasi hybrid · demografi · skor analitik · panel 7 senario ringkas",
        "Slide 2: 7 senario PENUH — bar besar · ✓ SPR · ▸ LEAD model",
        "9 wajib + 4 berhasrat — 26 slide seterusnya (13 × 2)",
    ])
    for seat in pas_sorted:
        _seat_report_slide(prs, seat)
        _seat_scenario_detail_slide(prs, seat)

    _bullet_slide(prs, "Justifikasi Terperinci — UMNO/BN 23 Kerusi (2 slide/kerusi)", [
        "Slide 1: contest strategik vs PH · profil muhibbah · panel ringkas",
        "Slide 2: 7 senario detail penuh per kerusi",
        "46 slide seterusnya (23 × 2)",
    ])
    for seat in umno_sorted:
        _seat_report_slide(prs, seat)
        _seat_scenario_detail_slide(prs, seat)

    cohort = data.get("cohortFramework") or []
    cohort_lines = [f"{c.get('id', '')}: {c.get('title', '')}" for c in cohort[:6]]
    _bullet_slide(prs, "Kohort Pengundi & Implikasi", cohort_lines or [
        "Muda bandar — isu ekonomi & pekerjaan",
        "Melayu luar bandar — naratif agama & kemudahan",
        "Pengundi Cina bandar — muhibbah vs PH",
    ])

    _bullet_slide(prs, "Nota Penting & Penafian", [
        meta.get("disclaimer", ""),
        "Ramalan peratus adalah anggaran analitik — bukan keputusan rasmi SPR",
        "Data socmed & media boleh berubah — kemas kini harian disyorkan",
        "Jangan kongsi formula dalaman atau skor war room di luar bilik mesyuarat",
        "Langkah seterusnya: finalisasi senarai calon · penamaan 18 Julai 2026",
    ])

    closing = _blank(prs)
    box = closing.shapes.add_textbox(Inches(0.5), Inches(2.8), Inches(9), Inches(1.2))
    tf = box.text_frame
    tf.text = "Terima Kasih"
    tf.paragraphs[0].font.size = Pt(40)
    tf.paragraphs[0].font.bold = True
    tf.paragraphs[0].font.color.rgb = NAVY
    tf.paragraphs[0].alignment = PP_ALIGN.CENTER
    sub = closing.shapes.add_textbox(Inches(0.5), Inches(4.0), Inches(9), Inches(0.8))
    sub.text_frame.text = "InsightPulse · Sokong Keputusan Muafakat dengan Data"
    sub.text_frame.paragraphs[0].font.size = Pt(18)
    sub.text_frame.paragraphs[0].font.color.rgb = GREEN
    sub.text_frame.paragraphs[0].alignment = PP_ALIGN.CENTER
    _footer(closing)

    return prs


def _render_catalog_html(ev: dict) -> str:
    blocks = []
    for cat in ev.get("dataCatalog") or []:
        rows = "".join(
            f"<tr><td><strong>{it.get('name', '—')}</strong></td>"
            f"<td>{it.get('vol', '—')}</td>"
            f"<td>{it.get('use', '—')}</td></tr>"
            for it in cat.get("items") or []
        )
        icon = cat.get("icon") or "📁"
        blocks.append(
            f"<div class='catalog-block'><h3>{icon} {cat.get('category', '—')}</h3>"
            f"<table><thead><tr><th>Sumber / Fail</th><th>Skala</th><th>Kegunaan</th></tr></thead>"
            f"<tbody>{rows}</tbody></table></div>"
        )
    return "".join(blocks) or "<p>Tiada katalog.</p>"


def _build_print_html(data: dict) -> str:
    meta = data["meta"]
    ev = data["evidence"]
    eco = ev.get("economic") or {}
    od = ev.get("openData") or {}
    total_pts = _data_point_total(ev)
    platforms = ", ".join(ev.get("socmedPlatforms") or [
        "Facebook", "Instagram", "TikTok", "X", "YouTube", "Threads",
    ])

    rows_html = []
    for seat in sorted(data["allSeats"], key=lambda x: x["code"]):
        inc = seat.get("incumbent") or {}
        wp = seat.get("winPrediction") or {}
        args = (seat.get("arguments") or {}).get("forAllocation") or []
        alloc_cls = "pas" if seat["allocation"] == "PAS" else "umno"
        bullets = "".join(f"<li>{a}</li>" for a in args[:3])
        rows_html.append(
            f"<tr class='{alloc_cls}'><td>{seat['code']}</td><td>{seat['name']}</td>"
            f"<td>{seat['allocation']}</td><td>{inc.get('label', '—')}</td>"
            f"<td>{wp.get('allocationLabel') or wp.get('verdict', '—')}</td>"
            f"<td><ul>{bullets}</ul></td></tr>"
        )

    catalog_html = _render_catalog_html(ev)

    return f"""<!DOCTYPE html>
<html lang="ms"><head><meta charset="utf-8">
<title>PRN N9 MN — Laporan PDF</title>
<style>
@page {{ size: A4 landscape; margin: 10mm; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; font-size: 9.5px; color: #1e293b; line-height: 1.35; }}
h1 {{ color: #003366; font-size: 22px; margin: 0 0 4px; }}
h2 {{ color: #1a7f5a; font-size: 13px; margin: 14px 0 6px; border-bottom: 2px solid #1a7f5a; padding-bottom: 3px; }}
h3 {{ color: #003366; font-size: 11px; margin: 8px 0 4px; }}
.meta {{ color: #64748b; margin-bottom: 10px; font-size: 10px; }}
.stats {{ display: grid; grid-template-columns: repeat(6, 1fr); gap: 8px; margin-bottom: 12px; }}
.stat {{ border-left: 3px solid #003366; padding: 8px 10px; background: #f8fafc; border-radius: 4px; }}
.stat.gold {{ border-left-color: #c8102e; }}
.stat strong {{ display: block; font-size: 16px; color: #003366; }}
.stat span {{ font-size: 9px; color: #64748b; }}
.trust {{ background: #eff6ff; border: 1px solid #bfdbfe; padding: 8px 12px; border-radius: 6px; margin-bottom: 12px; font-size: 10px; }}
.pipeline {{ display: flex; align-items: stretch; gap: 4px; margin-bottom: 14px; flex-wrap: wrap; }}
.pipe-step {{ flex: 1; min-width: 90px; background: #f1f5f9; border: 1px solid #cbd5e1; border-radius: 6px; padding: 6px 8px; text-align: center; font-size: 9px; }}
.pipe-step strong {{ display: block; color: #003366; font-size: 10px; }}
.pipe-arrow {{ align-self: center; color: #1a7f5a; font-weight: bold; }}
.hybrid-grid {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; margin-bottom: 14px; }}
.hybrid-card {{ border: 1px solid #cbd5e1; border-radius: 8px; padding: 10px; background: #fff; }}
.hybrid-card h3 {{ margin-top: 0; }}
.hybrid-card ul {{ margin: 4px 0 0; padding-left: 16px; }}
.hybrid-card li {{ margin-bottom: 3px; }}
.catalog-block {{ margin-bottom: 10px; page-break-inside: avoid; }}
.catalog-block table {{ width: 100%; border-collapse: collapse; margin-top: 4px; }}
table {{ width: 100%; border-collapse: collapse; }}
th, td {{ border: 1px solid #cbd5e1; padding: 3px 5px; vertical-align: top; }}
th {{ background: #f1f5f9; font-size: 8.5px; }}
tr.pas td:first-child {{ border-left: 3px solid #1a7f5a; }}
tr.umno td:first-child {{ border-left: 3px solid #c8102e; }}
ul {{ margin: 0; padding-left: 14px; }}
.disclaimer {{ margin-top: 12px; font-size: 8.5px; color: #64748b; }}
.page-break {{ page-break-before: always; }}
</style></head><body>

<h1>Perbincangan Muafakat PAS + BN/UMNO — PRN Negeri Sembilan 2026</h1>
<p class="meta">
  Dijana {meta.get('generated')} · PAS {meta['pasSeats']} kerusi · UMNO {meta['umnoSeats']} kerusi · Majoriti 19 ·
  DPI: {meta.get('dpiAsOf', 'Dec 2025')} · Ranking: {meta.get('rankingAsOf', '10 Jun 2026')}
</p>

<div class="stats">
  <div class="stat"><strong>{ev.get('engagementMillions', 56.9)}M</strong><span>Engagement Socmed</span></div>
  <div class="stat"><strong>{ev.get('socmedRows', 69003):,}</strong><span>Socmed Posts (Master)</span></div>
  <div class="stat"><strong>{ev.get('postRows', 31111):,}</strong><span>Posts · {ev.get('commentRows', 37892):,} Komen</span></div>
  <div class="stat"><strong>{ev.get('newsCrawled', 0):,}</strong><span>Artikel Media Crawled</span></div>
  <div class="stat"><strong>{ev.get('newsAnalyzed', 0)}</strong><span>Artikel ML Tier {ev.get('newsTier', 'A')}</span></div>
  <div class="stat gold"><strong>{ev.get('mediaNegPct') or '40'}%</strong><span>Media Negatif (ML)</span></div>
</div>

<div class="stats">
  <div class="stat"><strong>{total_pts:,}+</strong><span>Jumlah Titik Data</span></div>
  <div class="stat"><strong>36</strong><span>Kerusi DUN N9</span></div>
  <div class="stat"><strong>{od.get('endpointCount', 29)}</strong><span>API Rasmi (Open Data)</span></div>
  <div class="stat"><strong>6</strong><span>Platform Socmed</span></div>
  <div class="stat"><strong>OPR {eco.get('oprPct') or '2.75'}%</strong><span>BNM · USD/MYR RM{eco.get('usdMyr') or '4.07'}</span></div>
  <div class="stat"><strong>Hybrid</strong><span>Structured + Unstructured + ML/DL</span></div>
</div>

<div class="trust">
  <strong>{meta.get('disclaimer', '')}</strong>
</div>

<h2>Hybrid Model — Structured + Unstructured + ML/DL</h2>
<div class="hybrid-grid">
  <div class="hybrid-card">
    <h3>📊 Structured Data</h3>
    <ul>
      <li>Demografi pengundi N9 DPI Dec 2025 — 36 DUN (umur, jantina, bangsa, pengundi berdaftar)</li>
      <li>Data DUN ikut ranking · cadangan MN 10 Jun 2026</li>
      <li>PRN 2023 baseline — penyandang, majoriti, parti (SPR)</li>
      <li>n9_seats_analytics.json — isu utama & kategori per kerusi</li>
      <li>BNM OpenAPI · OpenDOSM · MIDA · Bursa — {od.get('endpointCount', 29)} endpoint</li>
    </ul>
  </div>
  <div class="hybrid-card">
    <h3>📱 Unstructured Data</h3>
    <ul>
      <li>PAS_Break_Master — {ev.get('socmedRows', 69003):,} rows · {ev.get('engagementMillions', 56.9)}M engagement</li>
      <li>Apify Actors: {ev.get('postRows', 31111):,} posts + {ev.get('commentRows', 37892):,} komen</li>
      <li>Platform: {platforms}</li>
      <li>Media BM · EN · Cina · Tamil — {ev.get('newsCrawled', 0):,} artikel crawled</li>
      <li>Sumber Tier A: Malay Mail · BH · Sin Chew · Oriental Daily · Harakah · FMT</li>
    </ul>
  </div>
  <div class="hybrid-card">
    <h3>🧠 ML + DL (Neural Network)</h3>
    <ul>
      <li>HuggingFace ft-Malay-bert — sentiment classifier (neg/pos/neu)</li>
      <li>Emotion classifier — multi-label neural analytics</li>
      <li>Media NLP Tier A — {ev.get('newsAnalyzed', 0)} artikel · mode {ev.get('analysisMode', 'ml_models')}</li>
      <li>Transformer BERT-family deep learning pada teks BM/EN/CN</li>
      <li>Fusion → Skor Analitik per kerusi → ramalan PAS vs UMNO</li>
    </ul>
  </div>
</div>

<div class="pipeline">
  <div class="pipe-step"><strong>1. Crawl</strong>{ev.get('socmedRows', 0):,} posts<br>Apify 6 platform</div>
  <div class="pipe-arrow">→</div>
  <div class="pipe-step"><strong>2. ML Sentiment</strong>HF ft-Malay-bert<br>Neural sentiment</div>
  <div class="pipe-arrow">→</div>
  <div class="pipe-step"><strong>3. Media DL</strong>{ev.get('newsCrawled', 0):,} artikel<br>Tier A NLP</div>
  <div class="pipe-arrow">→</div>
  <div class="pipe-step"><strong>4. Structured</strong>DPI 36 DUN<br>Ranking + MN</div>
  <div class="pipe-arrow">→</div>
  <div class="pipe-step"><strong>5. Hybrid Fusion</strong>Skor Analitik<br>Per kerusi DUN</div>
  <div class="pipe-arrow">→</div>
  <div class="pipe-step"><strong>6. Output</strong>PAS/PN 13 · UMNO/BN 23<br>Ramalan muafakat</div>
</div>

<h2>Senarai Data Digunakan — Katalog Penuh</h2>
<p class="meta">Semua sumber di bawah digunakan untuk ramalan, sentiment & insight per kerusi (selaras dashboard InsightPulse).</p>
{catalog_html}

<div class="page-break"></div>
<h2>36 Kerusi DUN — Justifikasi & Ramalan Muafakat</h2>
<table><thead><tr>
  <th>DUN</th><th>Nama</th><th>Peruntukan</th><th>Penyandang 2023</th><th>Ramalan Berbanding</th><th>Justifikasi</th>
</tr></thead><tbody>{''.join(rows_html)}</tbody></table>

<p class="disclaimer">{meta.get('disclaimer', '')}</p>
</body></html>"""


def _html_to_pdf(html_path: Path, pdf_path: Path) -> bool:
    chrome_paths = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    ]
    url = html_path.resolve().as_uri()
    for chrome in chrome_paths:
        if not Path(chrome).exists():
            continue
        cmd = [
            chrome,
            "--headless=new",
            "--disable-gpu",
            f"--print-to-pdf={pdf_path.resolve()}",
            "--no-pdf-header-footer",
            url,
        ]
        try:
            subprocess.run(cmd, check=True, capture_output=True, timeout=60)
            return pdf_path.exists() and pdf_path.stat().st_size > 1000
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError):
            continue
    return False


def main():
    data = build_payload()
    prs = build_ppt(data)

    for path in (OUT_PPT, OUT_PPT_COPY):
        path.parent.mkdir(parents=True, exist_ok=True)
        prs.save(str(path))

    html = _build_print_html(data)
    OUT_PRINT_HTML.parent.mkdir(parents=True, exist_ok=True)
    OUT_PRINT_HTML.write_text(html, encoding="utf-8")

    pdf_ok = _html_to_pdf(OUT_PRINT_HTML, OUT_PDF)
    if pdf_ok:
        OUT_PDF_COPY.parent.mkdir(parents=True, exist_ok=True)
        OUT_PDF_COPY.write_bytes(OUT_PDF.read_bytes())

    try:
        DESKTOP_KIT_DIR.mkdir(parents=True, exist_ok=True)
        DESKTOP_KIT_PPT.write_bytes(OUT_PPT.read_bytes())
        print(f"   Kit PPT:      {DESKTOP_KIT_PPT}")
    except OSError as exc:
        print(f"   ⚠ Kit PPT: {exc}")

    try:
        DESKTOP_DIR.mkdir(parents=True, exist_ok=True)
        DESKTOP_PPT.write_bytes(OUT_PPT.read_bytes())
        print(f"   Desktop PPT:  {DESKTOP_PPT}")
    except OSError as exc:
        print(f"   ⚠ Desktop PPT: {exc}")
    if pdf_ok:
        try:
            DESKTOP_DIR.mkdir(parents=True, exist_ok=True)
            DESKTOP_PDF.write_bytes(OUT_PDF.read_bytes())
            print(f"   Desktop PDF:  {DESKTOP_PDF}")
        except OSError as exc:
            print(f"   ⚠ Desktop PDF: {exc}")

    print(f"✅ PPT:  {OUT_PPT} ({len(prs.slides)} slides)")
    print(f"   Copy: {OUT_PPT_COPY}")
    if pdf_ok:
        print(f"✅ PDF:  {OUT_PDF}")
        print(f"   Copy: {OUT_PDF_COPY}")
    else:
        print(f"⚠ PDF:  Buka {OUT_PRINT_HTML} → Print → Save as PDF (Chrome headless tidak tersedia)")


if __name__ == "__main__":
    main()
