#!/usr/bin/env python3
"""Strategic Monarki+Adat+Poll PPTX — insight operasi PAS/MN N9 (Job 1 + Job 2 + ML)."""
from __future__ import annotations

import csv
import json
import re
from collections import Counter
from datetime import datetime, timezone, timedelta
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import MSO_AUTO_SIZE
from pptx.util import Inches, Pt

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data/projects/political/PRN/PRN_N9/reports/cula_digital"
OUT_PPTX = OUT_DIR / "MN_N9_Strategic_Brief_Monarki_Poll_Insight_Tindakan.pptx"
OUT_PPTX_LEGACY = OUT_DIR / "Monarki_Adat_N9_Insight_Tindakan.pptx"
POLL_CSV = ROOT / "data/analyzed/Sentiment_Emotion_FACEBOOK_20260705_000328.csv"
ML_JSON = ROOT / "data/projects/political/PRN/PRN_N9/reports/war_room/prototype/data/n9_ml_predictions.json"
WR_JSON = ROOT / "data/projects/political/PRN/PRN_N9/reports/war_room/prototype/data/warroom_dun_N9_production.json"
MYT = timezone(timedelta(hours=8))

NAVY = RGBColor(0, 51, 102)
PAS_GREEN = RGBColor(22, 163, 74)
RED = RGBColor(200, 16, 46)
AMBER = RGBColor(217, 119, 6)
GREY = RGBColor(100, 116, 139)
SLATE = RGBColor(30, 41, 59)
WHITE = RGBColor(255, 255, 255)
GREEN = RGBColor(26, 127, 90)

KEYWORDS = [
    {"id": "K1", "label": "Monarki luas", "report_dir": ROOT / "reports/20260705_002927_tuanku muhriz OR yang di-pertuan besar OR undang y"},
    {"id": "K2", "label": "Mukhriz vs Undang", "report_dir": ROOT / "reports/20260705_004507_Mukhriz undang negeri sembilan"},
    {"id": "K3", "label": "Undang 4 vs MB", "report_dir": ROOT / "reports/20260705_005735_undang empat menteri besar aminuddin"},
    {"id": "K4", "label": "Adat + DAP", "report_dir": ROOT / "reports/20260705_010838_adat perpatih DAP negeri sembilan"},
    {"id": "K5", "label": "Batch C09", "report_dir": ROOT / "reports/20260705_015017_adat perpatih OR undang OR tuanku muhriz negeri se"},
]

# DUN zon Undang/adat — micro-target sahaja (bukan 32 DUN)
UNDANG_DUN = {
    "N03": ("Sungai Lui", "Jelebu", "TINGGI"),
    "N05": ("Serting", "Jelebu", "TINGGI"),
    "N06": ("Palong", "Jelebu", "SEDANG"),
    "N18": ("Pilah", "Johol", "TINGGI"),
    "N19": ("Johol", "Johol", "TINGGI"),
    "N25": ("Paroi", "Sungai Ujong", "SEDANG"),
    "N26": ("Chembong", "Rembau", "SEDANG"),
    "N27": ("Rantau", "Rembau", "SEDANG"),
    "N34": ("Gemas", "Tampin", "SEDANG"),
    "N35": ("Gemencheh", "Tampin", "SEDANG"),
}


def _blank(prs):
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


def _footer(slide, note: str = "InsightPulse · PAS/MN N9 · Bukan polling SPR · Sahkan lapangan"):
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


def _table_slide(prs, title, headers, rows, font_size=8):
    s = _blank(prs)
    _header(s, title)
    nrows, ncols = len(rows) + 1, len(headers)
    h = min(5.8, 0.32 * nrows + 0.45)
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


def _parse_summary(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")

    def pct(label: str) -> float:
        m = re.search(rf"\*\*{label}:\*\* ([\d.]+)%", text)
        return float(m.group(1)) if m else 0.0

    total_m = re.search(r"\*\*Total Data Points:\*\* ([\d,]+)", text)
    eng_m = re.search(r"Total engagement: ([\d,]+)", text)
    return {
        "total": int(total_m.group(1).replace(",", "")) if total_m else 0,
        "positive": pct("Positive"),
        "neutral": pct("Neutral"),
        "negative": pct("Negative"),
        "engagement": int(eng_m.group(1).replace(",", "")) if eng_m else 0,
    }


def _classify_vote(t: str) -> str:
    t = (t or "").strip().lower()
    if re.search(r"\(b\)|^b[\.\)\s,/]|^b$|tidak\s*sokong|tak\s*sokong|x\s*sokong|tak\s*setuju", t):
        return "B"
    if re.search(r"\(a\)|^a[\.\)\s,/]|^a$|a\s*sokong|sokong.*(umno|pas)|lawan.*(dap|ph|harapan)", t):
        return "A"
    if re.search(r"sokong.*(umno|pas)|lawan.*(dap|ph)|tolak.*(dap|ph)|bersatu.*melayu", t):
        return "A_soft"
    return "other"


def load_poll_stats() -> dict:
    with POLL_CSV.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    comments = [r for r in rows if str(r.get("Type", "")).lower() == "comment"]
    post = next((r for r in rows if str(r.get("Type", "")).lower() == "post"), {})
    votes = Counter(_classify_vote(r.get("Text", "")) for r in comments)
    a = votes["A"] + votes["A_soft"]
    b = votes["B"]
    decided = a + b or 1
    try:
        post_eng = int(float(post.get("total_engagement") or 0))
    except (TypeError, ValueError):
        post_eng = 0
    if post_eng <= 0:
        post_eng = int(float(post.get("likes") or 0)) + int(float(post.get("comments_count") or 0))
    demo = Counter(r.get("demographic") or "?" for r in comments)
    malay = demo.get("Malay/Bumiputera", 0)
    return {
        "comments": len(comments),
        "a_pct": round(a / decided * 100, 1),
        "b_pct": round(b / decided * 100, 1),
        "decided": decided,
        "post_engagement": post_eng,
        "malay_pct": round(malay / max(len(comments), 1) * 100),
    }


def load_mn20_ml() -> tuple[list[str], dict, dict]:
    ml = json.loads(ML_JSON.read_text(encoding="utf-8"))
    ml_map = {s["code"]: s for s in ml["seat_predictions"]}
    seats = json.loads(WR_JSON.read_text(encoding="utf-8"))
    mn20: list[str] = []
    for s in seats:
        bv = (s.get("spr2023") or {}).get("blocVotes") or {}
        if (bv.get("PN") or 0) + (bv.get("BN") or 0) > (bv.get("PH") or 0):
            code = s.get("id") or s.get("code")
            if code:
                mn20.append(code)
    mn20.sort(key=lambda c: int(c[1:]))
    return mn20, ml_map, ml


def load_keyword_stats() -> list[dict]:
    out = []
    for kw in KEYWORDS:
        s = _parse_summary(kw["report_dir"] / "EXECUTIVE_SUMMARY.md")
        s.update(kw)
        out.append(s)
    return out


def _strategic_dun_rows(mn20: list[str], ml_map: dict) -> list[list[str]]:
    rows = []
    for code in sorted(UNDANG_DUN.keys(), key=lambda c: int(c[1:])):
        name, zone, exposure = UNDANG_DUN[code]
        in_mn = "✓" if code in mn20 else "—"
        prob = ml_map.get(code, {}).get("pasWinProb", "—")
        if code in mn20:
            if exposure == "TINGGI" and isinstance(prob, (int, float)) and prob < 45:
                play = "MONITOR · soft adat · elak serang MB"
            elif exposure == "TINGGI":
                play = "SOFT · edukasi adat · hormat YDPB"
            else:
                play = "MONITOR · jangan over-play"
        else:
            play = "JANGAN main isu adat (luar MN20)"
        rows.append([code, name, zone, in_mn, str(prob), exposure, play[:42]])
    return rows


def build_presentation(kw_stats: list[dict], poll: dict, mn20: list[str], ml_map: dict, ml_meta: dict) -> Presentation:
    prs = Presentation()
    prs.slide_width = Inches(10)
    prs.slide_height = Inches(7.5)
    k3 = next(s for s in kw_stats if s["id"] == "K3")
    undang_in_mn = [c for c in UNDANG_DUN if c in mn20]

    # 1 Title
    s = _blank(prs)
    tf = _box(s, 0.45, 1.1, 9, 1.6)
    _para(tf, "Monarki, Adat & MN N9", size=34, bold=True, color=NAVY, first=True)
    _para(tf, "Brief Strategik PAS/MN — Insight + ML + Poll Pengundi Malaysia", size=19, color=PAS_GREEN)
    tf2 = _box(s, 0.45, 2.85, 9, 1.9)
    _para(tf2, "Gabungan Job 1 (poll MN) + Job 2 (5 keyword monarki) + model kerusi N9", size=15, color=SLATE, first=True)
    _para(tf2, f"Dijana {datetime.now(MYT).strftime('%Y-%m-%d %H:%M')} · Majoriti DUN = 19 · Sasaran operasi MN = 20 kerusi", size=13, color=GREY)
    _footer(s)

    # 2 Nasihat utama — MAIN atau TIDAK
    s = _blank(prs)
    _header(s, "Nasihat Strategik HQ — Main Isu Adat atau Tidak?")
    tf = _box(s, 0.45, 1.05, 9, 5.8)
    _para(tf, "Jawapan ringkas", size=18, bold=True, color=NAVY, first=True, space=8)
    _para(
        tf,
        "JANGAN jadikan krisis adat sebagai SENJATA SERANGAN terbuka terhadap MB/PH dalam ceramah.",
        size=15,
        bold=True,
        color=RED,
        space=10,
    )
    _para(
        tf,
        f"Sebab: K2–K3 negatif {kw_stats[1]['negative']:.0f}–{k3['negative']:.0f}% — audiens Melayu marah/confused; "
        "MN risiko dilihat mempolitikkan istana.",
        size=13,
        space=10,
    )
    _para(tf, "BOLEH & PATUT:", size=15, bold=True, color=PAS_GREEN, space=6)
    bullets = [
        "Naratif UTAMA kempen = MN lawan PH (Poll PM: ~89% sokong) — bukan lawan YDPB/Undang.",
        "Isu adat = naratif SEKUNDER, defensif: «hormati proses adat · stabil · jangan pecah Melayu».",
        "Micro-target ~10 DUN zon Undang sahaja — bukan 32 DUN.",
        "Edukasi 1-pager adat (bukan debat parti) · elak quote K3 negatif di media sosial rasmi.",
    ]
    for i, b in enumerate(bullets):
        _para(tf, f"• {b}", size=13, first=(i == 0), space=7)
    _footer(s)

    # 3 Poll Pengundi Malaysia (Job 1)
    s = _blank(prs)
    _header(s, "Job 1 — Poll Pengundi Malaysia (Gabung MN)")
    _kpi_card(s, 0.4, 1.05, f"{poll['a_pct']}%", "Sokong MN", PAS_GREEN)
    _kpi_card(s, 2.65, 1.05, f"{poll['b_pct']}%", "Tolak MN", RED)
    _kpi_card(s, 4.9, 1.05, f"{poll['post_engagement']:,}", "Engagement Post", NAVY)
    _kpi_card(s, 7.15, 1.05, f"{poll['malay_pct']}%", "Melayu (proxy)", AMBER)
    tf = _box(s, 0.45, 2.35, 9, 4.3)
    _para(tf, "Implikasi untuk PAS/MN", size=18, bold=True, color=NAVY, first=True, space=10)
    for line in [
        f"531 komen · {poll['decided']} jelas A/B → sokong UMNO+PAS lawan PH ~{poll['a_pct']}%.",
        "Audiens page pro-MN — bukan sampling N9 penuh, tapi signal digital kuat untuk naratif coalisi.",
        "GABUNG dengan monarki: «Sokong MN demi stabil N9» + «hormati adat» — SATU garis, bukan dua front.",
        "Jangan over-claim menang — galvanize debat → undi sebenar + cula lapangan.",
    ]:
        _para(tf, f"• {line}", size=13, space=7)
    _footer(s, "Rujuk: Pengundi_Malaysia_Poll_N9_Insight_Tindakan.pptx")

    # 4 Monarki K1–K5 ringkas
    kw_rows = [[s["id"], s["label"], f"{s['total']:,}", f"{s['negative']:.1f}%", f"{s['engagement']:,}"] for s in kw_stats]
    _table_slide(prs, "Job 2 — 5 Keyword Monarki/Adat", ["KW", "Frame", "Rekod", "Negatif", "Engagement"], kw_rows, font_size=9)

    # 5 20 vs 32 vs zon Undang (+ cadangan DO/DON'T)
    s = _blank(prs)
    _header(s, "Sasaran Geografi — 32 DUN vs 20 MN vs Zon Undang")
    tf = _box(s, 0.45, 1.05, 4.35, 5.9)
    _para(tf, "3 lapisan — isu adat = RISIKO, bukan peluang serangan", size=13, bold=True, color=NAVY, first=True, space=6)
    layers = [
        (
            "32 DUN (seluruh N9)",
            "Monitor sahaja · JANGAN siar isu adat negeri-wide.",
            "Elak jadikan krisis istana mesej ceramah seluruh negeri.",
        ),
        (
            "20 kerusi MN",
            f"Operasi MN standard · alert monarki · {len(mn20)} DUN (PN+BN>PH 2023).",
            f"Kempen: MN lawan PH (~{poll['a_pct']}%) · alert ≠ serang MB via adat.",
        ),
        (
            f"~{len(UNDANG_DUN)} DUN zon Undang",
            f"Micro-target · {len(undang_in_mn)} overlap MN20 · soft comms.",
            "Jelebu · Johol · Rembau · Tampin — hormat Tuanku, bukan lawan istana.",
        ),
    ]
    for title, desc, note in layers:
        _para(tf, title, size=11, bold=True, color=PAS_GREEN, space=2)
        _para(tf, desc, size=10, color=SLATE, space=2)
        _para(tf, f"→ {note}", size=9, color=GREY, space=6)

    tf2 = _box(s, 5.0, 1.05, 4.45, 5.2)
    _para(tf2, "Satu garis mesej", size=13, bold=True, color=NAVY, first=True, space=6)
    _para(tf2, "DO ✓", size=11, bold=True, color=PAS_GREEN, space=3)
    for line in [
        f"«MN lawan PH» — poll ~{poll['a_pct']}% sokong",
        "«Hormati adat» — soft, 10 DUN Undang sahaja",
        "Pertahan N05 (+843 tipis) — MN murni",
        "Edukasi adat — bukan debat parti",
    ]:
        _para(tf2, f"  • {line}", size=10, color=SLATE, space=3)
    _para(tf2, "DON'T ✗", size=11, bold=True, color=RED, space=6)
    for line in [
        "Serang MB guna «penderhaka Undang»",
        "Siar isu adat ke 32 DUN",
        "Politikkan istana di ceramah",
        "Over-claim menang dari poll sahaja",
    ]:
        _para(tf2, f"  • {line}", size=10, color=SLATE, space=3)

    tf3 = _box(s, 0.45, 6.15, 9.0, 0.75)
    _para(
        tf3,
        f"BOTTOM LINE: Naratif UTAMA = poll MN ({poll['a_pct']}%) · Isu adat = defensif + micro 10 DUN — bukan serangan negeri-wide.",
        size=11,
        bold=True,
        color=AMBER,
        first=True,
        space=0,
    )
    _footer(s)

    # 6 ML + kerusi sensitif — versi mudah faham
    s = _blank(prs)
    _header(s, "Kerusi Sensitif Adat — Apa Buat? (ML + Lapangan)")
    tf = _box(s, 0.45, 1.05, 9, 1.55)
    _para(tf, "Apa maksud slide ini?", size=14, bold=True, color=NAVY, first=True, space=6)
    for line in [
        "Model ML = ramalan kerusi dari data SPR + demografi + socmed — BUKAN undi rasmi.",
        f"MN dijangka ~22.9 kerusi (majoriti = 19) — isu adat TIDAK auto menambah kerusi.",
        "Isu adat = AMARAN: kalau mishandle, boleh RUGI kerusi tipis — bukan peluang serang.",
    ]:
        _para(tf, f"• {line}", size=11, color=SLATE, space=5)

    # Tindakan table — simple 3 columns
    headers = ["Kerusi", "Risiko", "Tindakan HQ / Ketua DUN"]
    rows = [
        [
            "N05 Serting",
            "🔴 TERTINGGI\nMenang tipis +843",
            "JANGAN sentuh isu adat\nKempen MN murni · pertahan",
        ],
        [
            "N19 Johol",
            "🟠 TINGGI\nZon Undang · ML 38%",
            "Monitor socmed 2× sehari\nSoft touch · elak provokasi",
        ],
        [
            "N03, N25",
            "🟡 SEDANG\nIstana neutral-pos",
            "Jangan buat isu\nTeruskan perkhidmatan",
        ],
        [
            "N14 Ampangan",
            "🟠 MB zone · ML 15%",
            "JANGAN serang via adat\nFokus flip muafakat",
        ],
        [
            "N01, N10, N33",
            "🟡 Kubu DAP",
            "Counter perkhidmatan\nBukan debat adat",
        ],
    ]
    nrows = len(rows) + 1
    table = s.shapes.add_table(nrows, 3, Inches(0.4), Inches(2.75), Inches(9.2), Inches(3.85)).table
    col_w = [1.4, 1.6, 6.2]
    for ci, w in enumerate(col_w):
        table.columns[ci].width = Inches(w)
    for ci, htxt in enumerate(headers):
        cell = table.cell(0, ci)
        cell.text = htxt
        cell.fill.solid()
        cell.fill.fore_color.rgb = RGBColor(241, 245, 249)
        for para in cell.text_frame.paragraphs:
            para.font.bold = True
            para.font.size = Pt(10)
    for ri, row in enumerate(rows, 1):
        for ci, val in enumerate(row):
            cell = table.cell(ri, ci)
            cell.text = val
            for para in cell.text_frame.paragraphs:
                para.font.size = Pt(9)
                if ci == 1 and "🔴" in val:
                    para.font.color.rgb = RED
                elif ci == 1:
                    para.font.color.rgb = AMBER

    tf3 = _box(s, 0.45, 6.72, 9.0, 0.55)
    _para(
        tf3,
        "RINGKAS: Isu adat = jaga kerusi tipis (N05) + pantau 10 DUN Undang — bukan serangan negeri-wide.",
        size=11,
        bold=True,
        color=PAS_GREEN,
        first=True,
    )
    _footer(s)

    # 7 DUN priority matrix
    dun_rows = _strategic_dun_rows(mn20, ml_map)
    _table_slide(
        prs,
        "Matriks DUN Zon Undang — Main / Monitor / Jangan",
        ["DUN", "Nama", "Zon", "MN20", "pasWinProb", "Exposure", "Cadangan"],
        dun_rows,
        font_size=7,
    )

    # 8 Gabungan naratif
    s = _blank(prs)
    _header(s, "Gabungan Naratif — Poll MN + Monarki")
    tf = _box(s, 0.45, 1.05, 9, 5.8)
    _para(tf, "Satu garis mesej (jangan pecah)", size=16, bold=True, color=NAVY, first=True, space=10)
    matrix = [
        ("DO ✓", PAS_GREEN, [
            f"«PRN N9: MN lawan PH — {poll['a_pct']}% sokong digital (Poll PM)»",
            "«Hormati Tuanku & proses adat — fokus kebajikan rakyat»",
            "«Elak pecah undi Melayu — pilih kerjasama»",
        ]),
        ("DON'T ✗", RED, [
            "Serang MB/PH guna «penderhaka Undang» di ceramah",
            "Share meme/video K3 negatif tanpa konteks",
            "Politikkan istana di kubu DAP (N01/N10/N33)",
            "Over-claim «menang» dari poll PM sahaja",
        ]),
    ]
    first = True
    for label, color, items in matrix:
        _para(tf, label, size=14, bold=True, color=color, first=first, space=6)
        first = False
        for it in items:
            _para(tf, f"  • {it}", size=12, space=4)
    _footer(s)

    # 9 P1
    _action_slide(
        prs,
        "Tindakan Segera — 7 Hari (P1)",
        [
            ("P1", "Brief ketua 20 kerusi MN: garis «poll MN + hormat adat» — doc 1 muka surat WhatsApp.", "Comms HQ · hari ini · Action Center"),
            ("P1", "Monitor K2/K3/K5 daily — spike >60% negatif → alert P1 Action Center (10 DUN Undang).", "Digital war room · 2× sehari"),
            ("P1", "Siap 1-pager fakta adat N9 (Undang 4, DKU, peranan YDPB) — edukasi bukan serangan.", "Comms + legal adat · 48 jam"),
            ("P1", "Echo poll PM (~89% sokong MN) di group kempen — pisahkan dari debat istana.", "Media PAS N9 · Jumaat"),
        ],
    )

    # 10 P2
    _action_slide(
        prs,
        "Tindakan Momentum — 2–4 Minggu (P2)",
        [
            ("P2", "Merge CSV K1–K5 + poll + ML → dashboard war room monarki (dedupe overlap).", "InsightPulse · script merge"),
            ("P2", "Cula lapangan 10 DUN Undang — banding signal digital vs ground (N05, N19 priority).", "HQ N9 · mingguan"),
            ("P2", "Update pasWinProb model dengan socmed_neg monarki per DUN (retrain ML).", "Data team · minggu 2"),
            ("P2", "Sedia rebut K4 (adat+DAP) — 5 fakta, elak sentuh sensitif agama.", "Comms · doc ringkas"),
        ],
    )

    # 11 Mesej
    s = _blank(prs)
    _header(s, "Mesej Disyorkan — Copy Paste")
    tf = _box(s, 0.45, 1.05, 9, 5.8)
    messages = [
        ("Utama (poll + MN)", f"PRN N9: Sokong MN lawan PH. Poll digital ~{poll['a_pct']}% sokong — elak pecah undi Melayu."),
        ("Adat (soft)", "N9 kuat tradisi adat — hormati Tuanku & Undang. Fokus perkhidmatan, bukan provokasi."),
        ("Ceramah", "Lawan DAP/PH — bukan lawan istana. MN demi stabil dan kebajihan."),
        ("Footnote", "Signal digital InsightPulse — bukan polling SPR. Sahkan dengan cula lapangan."),
    ]
    for i, (title, msg) in enumerate(messages):
        _para(tf, title, size=13, bold=True, color=NAVY, first=(i == 0), space=4)
        _para(tf, f'"{msg}"', size=12, color=SLATE, space=10)
    _footer(s)

    # 12 Risiko
    s = _blank(prs)
    _header(s, "Risiko & Mitigasi")
    tf = _box(s, 0.45, 1.05, 9, 5.8)
    risks = [
        (f"Politikkan istana (K3 {k3['negative']:.0f}% neg)", "Brief DUN · P1 doc · sanksi mesej provokatif"),
        (f"Over-rely poll {poll['a_pct']}% tanpa lapangan", "Cula + footnote sentiasa · jangan claim menang"),
        ("Main adat di 32 DUN", "Hadkan 10 DUN Undang · 20 MN operasi standard"),
        ("PH frame «MN anti-Melayu/adat»", "Edukasi + neutral tone · jangan feed K3 content"),
    ]
    for i, (r, m) in enumerate(risks):
        _para(tf, r, size=14, bold=True, color=RED if i < 2 else AMBER, first=(i == 0), space=4)
        _para(tf, f"→ {m}", size=13, color=SLATE, space=10)
    _footer(s)

    return prs


def main() -> None:
    import subprocess
    import sys

    kw_stats = load_keyword_stats()
    poll = load_poll_stats()
    mn20, ml_map, ml_meta = load_mn20_ml()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    prs = build_presentation(kw_stats, poll, mn20, ml_map, ml_meta)
    prs.save(str(OUT_PPTX))
    prs.save(str(OUT_PPTX_LEGACY))
    k5_copy = KEYWORDS[4]["report_dir"] / "MN_N9_Strategic_Brief_Monarki_Poll_Insight_Tindakan.pptx"
    prs.save(str(k5_copy))
    sync_script = ROOT / "scripts/sync_n9_jobs_dashboard.py"
    if sync_script.exists():
        subprocess.run([sys.executable, str(sync_script)], check=True, cwd=str(ROOT))
    print(f"✅ Saved: {OUT_PPTX}")
    print(f"✅ Saved: {OUT_PPTX_LEGACY}")
    print(f"✅ Saved: {k5_copy}")
    print(f"   Slides: {len(prs.slides)}")
    print(f"   Poll MN {poll['a_pct']}% | MN20 {len(mn20)} DUN | Undang zone {len(UNDANG_DUN)}")


if __name__ == "__main__":
    main()
