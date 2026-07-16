#!/usr/bin/env python3
"""Generate Cula Digital poll PPTX — insight operasi + cadangan tindakan PAS N9."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import MSO_AUTO_SIZE, PP_ALIGN
from pptx.util import Inches, Pt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

PROTO = ROOT / "data/projects/political/PRN/PRN_N9/reports/war_room/prototype/data"
POLL_JSON = PROTO / "cula_poll_by_dun_N9.json"
SUMMARY_JSON = PROTO / "cula_poll_summary_N9.json"
SOCIAL_JSON = PROTO / "n9_social_summary.json"
OUT_DIR = ROOT / "data/projects/political/PRN/PRN_N9/reports/cula_digital"
OUT_PPTX = OUT_DIR / "PRN_N9_WarRoom_Lengkap_Insight_Tindakan.pptx"
OUT_PPTX_CULA = OUT_DIR / "Cula_Digital_Poll_N9_Insight_Tindakan.pptx"

MYT = timezone(timedelta(hours=8))

NAVY = RGBColor(0, 51, 102)
GREEN = RGBColor(26, 127, 90)
PAS_GREEN = RGBColor(22, 163, 74)
RED = RGBColor(200, 16, 46)
AMBER = RGBColor(217, 119, 6)
GREY = RGBColor(100, 116, 139)
SLATE = RGBColor(30, 41, 59)
WHITE = RGBColor(255, 255, 255)
PURPLE = RGBColor(124, 58, 237)


def _blank(prs: Presentation):
    return prs.slides.add_slide(prs.slide_layouts[6])


def _header(slide, title: str):
    bar = slide.shapes.add_shape(1, Inches(0), Inches(0), Inches(10), Inches(0.88))
    bar.fill.solid()
    bar.fill.fore_color.rgb = NAVY
    bar.line.fill.background()
    tb = slide.shapes.add_textbox(Inches(0.45), Inches(0.12), Inches(9.1), Inches(0.62))
    tf = tb.text_frame
    tf.text = title
    p = tf.paragraphs[0]
    p.font.size = Pt(22)
    p.font.bold = True
    p.font.color.rgb = WHITE


def _footer(slide, note: str = "InsightPulse · Cula Digital N9 · Bukan polling SPR"):
    foot = slide.shapes.add_textbox(Inches(0.4), Inches(7.05), Inches(9.2), Inches(0.35))
    tf = foot.text_frame
    tf.text = note
    p = tf.paragraphs[0]
    p.font.size = Pt(9)
    p.font.color.rgb = GREY


def _box(slide, left, top, width, height):
    box = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    tf = box.text_frame
    tf.word_wrap = True
    tf.auto_size = MSO_AUTO_SIZE.NONE
    return tf


def _para(tf, text, *, size=16, bold=False, color=SLATE, first=False, space=8):
    p = tf.paragraphs[0] if first else tf.add_paragraph()
    p.text = text
    p.font.size = Pt(size)
    p.font.bold = bold
    p.font.color.rgb = color
    p.space_after = Pt(space)
    return p


def _kpi_card(slide, left, top, value, label, color=NAVY):
    card = slide.shapes.add_shape(1, Inches(left), Inches(top), Inches(2.15), Inches(1.05))
    card.fill.solid()
    card.fill.fore_color.rgb = RGBColor(248, 250, 252)
    card.line.color.rgb = RGBColor(226, 232, 240)
    tf = _box(slide, left + 0.12, top + 0.12, 1.9, 0.85)
    _para(tf, str(value), size=26, bold=True, color=color, first=True, space=2)
    _para(tf, label, size=10, color=GREY, space=0)


def _table_slide(prs, title, headers, rows, font_size=9):
    s = _blank(prs)
    _header(s, title)
    nrows, ncols = len(rows) + 1, len(headers)
    h = min(5.6, 0.34 * nrows + 0.4)
    table = s.shapes.add_table(nrows, ncols, Inches(0.35), Inches(1.05), Inches(9.3), Inches(h)).table
    for ci, htxt in enumerate(headers):
        cell = table.cell(0, ci)
        cell.text = htxt
        cell.fill.solid()
        cell.fill.fore_color.rgb = RGBColor(241, 245, 249)
        for para in cell.text_frame.paragraphs:
            para.font.bold = True
            para.font.size = Pt(font_size)
    for ri, row in enumerate(rows, 1):
        for ci, val in enumerate(row):
            cell = table.cell(ri, ci)
            cell.text = str(val)
            for para in cell.text_frame.paragraphs:
                para.font.size = Pt(font_size)
    _footer(s)


def _action_slide(prs, title, items: list[tuple[str, str, str]]):
    """items: (priority, action, owner/deadline)"""
    s = _blank(prs)
    _header(s, title)
    y = 1.05
    for pri, action, meta in items:
        badge = s.shapes.add_shape(1, Inches(0.4), Inches(y), Inches(0.75), Inches(0.32))
        badge.fill.solid()
        badge.fill.fore_color.rgb = RED if pri == "P1" else AMBER if pri == "P2" else GREEN
        badge.line.fill.background()
        bt = _box(s, 0.42, y + 0.04, 0.7, 0.28)
        _para(bt, pri, size=10, bold=True, color=WHITE, first=True, space=0)
        at = _box(s, 1.25, y, 5.9, 0.55)
        _para(at, action, size=13, bold=True, color=SLATE, first=True, space=2)
        _para(at, meta, size=10, color=GREY, space=0)
        y += 0.62
    _footer(s)


def _derive_insights(poll: dict, summary: dict) -> dict:
    mn = summary.get("mnVsSolo") or {}
    labu = summary.get("pasLabu") or {}
    be_mn = mn.get("bucketsExpanded") or {}
    posts = sorted(poll.get("byPost") or [], key=lambda p: p.get("engagement") or 0, reverse=True)
    hot = posts[0] if posts else {}

    # MN vs Solo among clear MN+Solo only
    mn_n, solo_n = be_mn.get("MN", 0), be_mn.get("Solo", 0)
    mn_solo_total = mn_n + solo_n or 1
    mn_pct_clear = round(mn_n / mn_solo_total * 100)

    return {
        "hot_post": hot.get("page", "—"),
        "hot_dun": hot.get("primaryDun", "—"),
        "hot_engagement": hot.get("engagement", 0),
        "hot_comments": hot.get("commentsCrawled", 0),
        "mn_pct_clear": mn_pct_clear,
        "pro_pas_pct": mn.get("pct", {}).get("Pro-PAS", 0),
        "pro_ph_pct": mn.get("pct", {}).get("Pro-PH", 0),
        "labu_sokong_pct": labu.get("pct", {}).get("Sokong PAS", 0),
        "posts": posts,
    }


def build_presentation(poll: dict, summary: dict) -> Presentation:
    meta = summary.get("meta") or poll.get("meta") or {}
    mn = summary.get("mnVsSolo") or {}
    labu = summary.get("pasLabu") or {}
    be_mn = mn.get("bucketsExpanded") or {}
    be_labu = labu.get("bucketsExpanded") or {}
    ins = _derive_insights(poll, summary)

    prs = Presentation()
    prs.slide_width = Inches(10)
    prs.slide_height = Inches(7.5)

    # 1 Title
    s = _blank(prs)
    tf = _box(s, 0.5, 1.4, 9, 1.2)
    _para(tf, "Cula Digital · Poll FB N9", size=34, bold=True, color=NAVY, first=True)
    _para(tf, "Insight Operasi & Cadangan Tindakan Momentum PAS", size=20, color=PAS_GREEN)
    tf2 = _box(s, 0.5, 3.0, 9, 1.4)
    _para(
        tf2,
        f"{meta.get('totalComments', 526)} komen · {meta.get('totalPosts', 7)} post · "
        f"{meta.get('totalEngagement', 2302):,} engagement",
        size=16,
        color=SLATE,
        first=True,
    )
    _para(tf2, meta.get("labelling", "3-tier labelling"), size=13, color=GREY)
    _para(tf2, f"Dijana: {meta.get('generated', datetime.now(MYT).strftime('%Y-%m-%d %H:%M'))}", size=12, color=GREY)
    _footer(s)

    # 2 Cara baca laporan
    s = _blank(prs)
    _header(s, "Cara Baca Laporan Ini")
    tf = _box(s, 0.5, 1.1, 9, 5.5)
    bullets = [
        "Data: 7 post WhatsApp (FB) — Rembau, Chembong, Kota, Port Dickson, Labu, Inche Curry.",
        "3 peringkat label: Jelas (A/B) · Debat→condong (keyword) · Tidak Jelas→assumption (sentiment+emosi).",
        "Angka UTAMA = semua 526 komen (Tidak Jelas sudah dipecahkan). Baris 'keyword' = tanpa assumption.",
        "Debat ≠ atas pagar — debat = condong naratif (Pro-PAS / Pro-PH / MN / Solo).",
        "Bukan polling SPR — petunjuk naratif digital untuk tindakan lapangan & socmed.",
    ]
    for i, b in enumerate(bullets):
        _para(tf, f"• {b}", size=15, first=(i == 0), space=12)
    _footer(s)

    # 3 KPI ringkas
    s = _blank(prs)
    _header(s, "Ringkasan Eksekutif")
    _kpi_card(s, 0.4, 1.05, meta.get("totalComments", 526), "Jumlah komen")
    _kpi_card(s, 2.65, 1.05, meta.get("totalPosts", 7), "Post FB")
    _kpi_card(s, 4.9, 1.05, f"{meta.get('totalEngagement', 2302):,}", "Engagement", PAS_GREEN)
    _kpi_card(s, 7.15, 1.05, f"{ins['pro_pas_pct']}%", "Pro-PAS (MN/Solo)", PAS_GREEN)

    tf = _box(s, 0.45, 2.35, 9, 4.2)
    _para(tf, "Temuan utama", size=18, bold=True, color=NAVY, first=True, space=10)
    findings = [
        f"Naratif Pro-PAS dominan ({ins['pro_pas_pct']}% drpd 458 komen MN/Solo) — momentum emosi positif/pro-PAS kuat walaupun jawapan A/B sedikit.",
        f"MN vs Solo (jawapan jelas A/B): MN {ins['mn_pct_clear']}% vs Solo {100 - ins['mn_pct_clear']}% — rakyat condong MN bila jawab terus.",
        f"Pro-PH / kritik ({ins['pro_ph_pct']}%) — perlu counter naratif tempatan, bukan debat agama semata.",
        f"Labu N20: Sokong PAS {ins['labu_sokong_pct']}% (68 komen) — isyarat kuat calon PAS diterima.",
        f"Post paling panas: {ins['hot_post']} ({ins['hot_dun']}) — {ins['hot_comments']} komen, {ins['hot_engagement']:,} engagement.",
    ]
    for i, f in enumerate(findings):
        _para(tf, f"• {f}", size=14, first=(i == 0), space=8)
    _footer(s)

    # 4 MN vs Solo
    s = _blank(prs)
    _header(s, "Soalan MN vs Solo — 458 Komen (6 Post)")
    tf = _box(s, 0.45, 1.0, 4.4, 2.2)
    _para(tf, "Semua komen (inc. assumption)", size=14, bold=True, color=NAVY, first=True)
    for k in ("MN", "Solo", "Pro-PAS", "Pro-PH", "Masih Tidak Jelas"):
        n = be_mn.get(k, 0)
        pct = mn.get("pct", {}).get(k, 0)
        _para(tf, f"{k}: {n} ({pct}%)", size=13, space=4)
    tf2 = _box(s, 5.0, 1.0, 4.5, 2.2)
    _para(tf2, "Keyword sahaja (rujukan)", size=14, bold=True, color=GREY, first=True)
    bk = mn.get("bucketsKeyword") or {}
    _para(tf2, f"MN {bk.get('MN', 0)} · Solo {bk.get('Solo', 0)} · Pro-PAS {bk.get('Pro-PAS', 0)} · Pro-PH {bk.get('Pro-PH', 0)}", size=13, space=6)
    _para(tf2, mn.get("insightKeyword", ""), size=12, color=AMBER)

    tf3 = _box(s, 0.45, 3.3, 9, 3.5)
    _para(tf3, "Maksud operasi", size=16, bold=True, color=PAS_GREEN, first=True)
    _para(
        tf3,
        "Ramai tidak jawab A/B — mereka DEBAT. Pro-PAS 220 = ruang untuk galvanize sokongan, "
        "bukan anggap sudah menang. Tugas: tukar debat → jawapan MN (A) dengan mesej ringkas.",
        size=14,
        space=8,
    )
    _para(
        tf3,
        f"Solo hanya {be_mn.get('Solo', 0)} ({mn.get('pct', {}).get('Solo', 0)}%) — ancaman pecah undi solo rendah; "
        f"fokus elakkan pecah dengan UMNO/BN melalui naratif MN.",
        size=14,
        space=8,
    )
    _footer(s)

    # 5 Labu
    s = _blank(prs)
    _header(s, "Soalan PAS Labu (N20) — 68 Komen")
    tf = _box(s, 0.45, 1.05, 9, 5.8)
    _para(tf, labu.get("insight", ""), size=18, bold=True, color=PAS_GREEN, first=True, space=12)
    _para(tf, f"Sokong PAS: {be_labu.get('Sokong PAS', 0)} · Tak sokong: {be_labu.get('Tak Sokong PAS', 0)} · Masih tidak jelas: {be_labu.get('Masih Tidak Jelas', 0)}", size=16, space=10)
    _para(tf, "Insight", size=16, bold=True, color=NAVY, space=8)
    for b in [
        "Labu = kerusi PAS wajib (N20) — naratif digital menyokong calon PAS.",
        "Tindakan: umum calon / calon shadow awal · program 'Labu for PAS' di lapangan.",
        "Balas 7 kritik dengan fakta perkhidmatan tempatan (bukan debat agama online).",
    ]:
        _para(tf, f"• {b}", size=14, space=6)
    _footer(s)

    # 6 Table posts
    post_rows = []
    for p in ins["posts"]:
        be = p.get("bucketsExpanded") or p.get("buckets") or {}
        post_rows.append([
            p.get("page", "")[:22],
            p.get("primaryDun", ""),
            str(p.get("commentsCrawled", 0)),
            str(p.get("engagement", 0)),
            f"MN{be.get('MN', 0)} S{be.get('Solo', 0)} PP{be.get('Pro-PAS', 0)}",
        ])
    _table_slide(
        prs,
        "Pecahan 7 Post — Semua Komen",
        ["Halaman", "DUN", "Komen", "Engagement", "MN·Solo·Pro-PAS"],
        post_rows,
        font_size=8,
    )

    # 7 DUN priority
    dun_rows = []
    for code in summary.get("dunsWithData") or []:
        dun = (poll.get("byDun") or {}).get(code) or {}
        slot = dun.get("pasLabu") or dun.get("mnVsSolo") or {}
        be = slot.get("bucketsExpanded") or slot.get("buckets") or {}
        if dun.get("pasLabu"):
            summary_txt = f"Sokong {be.get('Sokong PAS', 0)} / {slot.get('commentsReported', 0)}"
        else:
            summary_txt = f"Pro-PAS {be.get('Pro-PAS', 0)} · MN {be.get('MN', 0)}"
        dun_rows.append([code, dun.get("posts", [{}])[0].get("district", "—") if dun.get("posts") else "—", str(slot.get("commentsReported", 0)), summary_txt])
    _table_slide(prs, "Keutamaan DUN — Data Poll", ["DUN", "Daerah", "Komen", "Ringkasan"], dun_rows)

    # 8 Tindakan P1 (7 hari)
    _action_slide(
        prs,
        "Tindakan Segera — 7 Hari (P1)",
        [
            (
                "P1",
                f"Moderasi aktif post {ins['hot_post']} ({ins['hot_dun']}) — balas komen Pro-PH & tanya semula: 'A MN atau B Solo?'",
                "Admin FB + 2 sukarelawan · 2× sehari · KPI: 30 balasan berstruktur",
            ),
            (
                "P1",
                "Siarkan infographic 1-slide: MN = elak pecah undi Melayu · PH kalah = matlamat bersama.",
                "Media PAS N9 · hantar ke 6 page post · Jumaat petang",
            ),
            (
                "P1",
                "Labu N20: program mini ceramah + tanya pendapat penduduk (echo soalan poll) — kumpul nama sukarelawan.",
                "AJK DUN Labu · Sabtu/Ahad · sasaran 50 rumah",
            ),
            (
                "P1",
                "Whatsapp group kempen: hantar 3 contoh jawapan A (MN) untuk petugas copy-paste balas komen.",
                "Pemuda PAS Rembau + Chembong · hari ini",
            ),
        ],
    )

    # 9 Tindakan P2 (2-4 minggu)
    _action_slide(
        prs,
        "Tindakan Momentum — 2–4 Minggu (P2)",
        [
            (
                "P2",
                "Ulang poll format A/B di page rendah engagement (N28 Kota, N33 PD) — 1 post/minggu.",
                "Digital team · seed + crawl InsightPulse",
            ),
            (
                "P2",
                "Debat Pro-PH tinggi di Inche Curry / Rembau — siapkan 5 fakta rebut tempatan (kos sara hidup, perkhidmatan).",
                "Comms DUN N26/N27 · doc 1 muka surat",
            ),
            (
                "P2",
                "Solo narrative: jangan serang UMNO publicly — guna 'MN lebih cerah' (data: Solo <7%).",
                "Narrative lead · brief semua admin page",
            ),
            (
                "P2",
                "Cula lapangan + digital sync: petugas catat condong MN/Solo/Pro-PAS di borang Modul #7 War Room.",
                "HQ N9 · mingguan · banding poll vs ground",
            ),
        ],
    )

    # 10 Mesej disyorkan
    s = _blank(prs)
    _header(s, "Mesej Disyorkan — Ringkas & Boleh Copy")
    tf = _box(s, 0.45, 1.05, 9, 5.8)
    messages = [
        ("Balas komen debat", "Terima kasih pandangan. PRN ini yang penting PH kalah. Undi kami elak pecah — pilih MN (A). 💚"),
        ("Post susulan MN", "68% yang jawab terus pilih MN. Solo = risiko pecah undi. PH tetap jadi sasaran."),
        ("Labu", "Labu for PAS — naratif rakyat Labu sokong calon PAS. Fokus perkhidmatan, bukan fitnah."),
        ("Elak", "Jangan label 'atas pagar' — mereka debat. Ajak jawab A atau B."),
    ]
    for title, msg in messages:
        _para(tf, title, size=13, bold=True, color=NAVY, first=(title == messages[0][0]), space=4)
        _para(tf, f'"{msg}"', size=12, color=SLATE, space=10)
    _footer(s)

    # 11 Risiko
    s = _blank(prs)
    _header(s, "Risiko & Mitigasi")
    tf = _box(s, 0.45, 1.05, 9, 5.8)
    risks = [
        ("Pro-PAS tinggi ≠ undi diurn", "Galvanize: jemput komen → event/cula · tanda nama di lapangan"),
        ("Pro-PH 19% di debat", "Fakta tempatan · elak ad hominem · highlight perpaduan MN"),
        ("51+9 masih tidak jelas", "Follow-up comment dengan soalan closed: A atau B?"),
        ("Over-claim di media", "Sentiasa footnote: naratif socmed, bukan polling SPR"),
    ]
    for i, (r, m) in enumerate(risks):
        _para(tf, r, size=14, bold=True, color=RED if i < 2 else AMBER, first=(i == 0), space=4)
        _para(tf, f"→ {m}", size=13, color=SLATE, space=10)
    _footer(s)

    # 12 Next steps
    s = _blank(prs)
    _header(s, "Langkah Seterusnya & Dashboard")
    tf = _box(s, 0.45, 1.05, 9, 5.5)
    steps = [
        "Refresh War Room: localhost:8080 → Command Center → panel Cula Digital 204813.",
        "Drawer DUN (N20, N26–N28, N33) untuk pecahan per kerusi.",
        "Crawl susulan: 1 post/minggu per DUN target · jalankan classify + build bundle.",
        "Mesyuarat mingguan: banding poll digital vs cula lapangan (Modul #7).",
        f"Fail data: {POLL_JSON.relative_to(ROOT)}",
    ]
    for i, st in enumerate(steps):
        _para(tf, f"{i + 1}. {st}", size=14, first=(i == 0), space=10)
    _footer(s, "InsightPulse · PRN N9 War Room · Cula Digital Batch 20260702")

    return prs


def main() -> None:
    if not POLL_JSON.exists() or not SUMMARY_JSON.exists():
        raise SystemExit(
            "Run first: python3 scripts/build_cula_poll_by_dun_n9.py && "
            "python3 scripts/build_warroom_production_bundle.py"
        )
    poll = json.loads(POLL_JSON.read_text(encoding="utf-8"))
    summary = json.loads(SUMMARY_JSON.read_text(encoding="utf-8"))
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    prs = build_presentation(poll, summary)
    prs.save(str(OUT_PPTX))
    print(f"✅ Saved: {OUT_PPTX}")
    print(f"   Slides: {len(prs.slides)}")


if __name__ == "__main__":
    main()
