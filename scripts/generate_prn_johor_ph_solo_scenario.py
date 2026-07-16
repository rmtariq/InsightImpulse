#!/usr/bin/env python3
"""
PRN Johor 2026 — Senario "PH bertanding SOLO di semua 56 DUN".

Bandingkan dua konfigurasi pihak lawan:
  A) Muafakat PN+BN (1-lawan-1 vs PH)
  B) PN solo + BN solo (3 penjuru vs PH)

Sumber data (sedia ada, hybrid model PRN Johor):
  warroom_dun_Johor_production.json  (baseline PRN Johor 12 Mac 2022 + DOSM + socmed)
    pasMnWinProb  = kekuatan pembangkang BILA bersatu (muafakat)  -> Senario A
    pasSoloWinProb= kekuatan PN/PAS solo                          -> Senario B
    bnSoloWinProb = kekuatan BN solo                              -> Senario B
  PH base (1-vs-1) dianggar = 100 - pasMnWinProb.
  Senario B = plurality 3 penjuru: pemenang = max(PH, PN, BN).

NOTA: angka adalah ANGGARAN ANALITIK (model data-driven), bukan keputusan rasmi SPR.
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt

ROOT = Path(__file__).resolve().parents[1]
PROTO = ROOT / "data/projects/political/PRN/PRN_N9/reports/war_room/prototype/data"
SEATS_JSON = PROTO / "warroom_dun_Johor_production.json"
OUT_DIR = ROOT / "data/projects/political/PRN/PRN_Johor/reports/dashboards"
OUT_PPT = OUT_DIR / "prn-johor-ph-solo-56-scenario.pptx"
OUT_MD = OUT_DIR / "prn-johor-ph-solo-56-scenario.md"
OUT_JSON = OUT_DIR / "prn-johor-ph-solo-56-scenario.json"
DESKTOP_DIR = Path.home() / "Desktop/N9"
DESKTOP_PPT = DESKTOP_DIR / "PRN_Johor_PH_Solo_56_Senario.pptx"
DOWNLOADS_PPT = Path.home() / "Downloads/PRN_Johor_PH_Solo_56_Senario.pptx"

NAVY = RGBColor(0, 51, 102)
GREEN = RGBColor(26, 127, 90)
RED = RGBColor(200, 16, 46)
AMBER = RGBColor(180, 120, 10)
GREY = RGBColor(100, 116, 139)
WHITE = RGBColor(255, 255, 255)
SLATE = RGBColor(30, 41, 59)

FOOT = "InsightPulse · PRN Johor 2026 · Analitik Dalaman — Anggaran, bukan keputusan SPR"


# ── Naratif per-DUN (guna lapisan etnik) ───────────────────────────────────
def _narrative(r: dict) -> tuple[list[str], str]:
    m = r.get("malay") or 0
    c = r.get("chinese") or 0
    i = r.get("indian") or 0
    why: list[str] = []
    if r["scenA"] == "PH":
        why.append(f"Kubu PH: Cina {c:.0f}% · India {i:.0f}% · Melayu {m:.0f}% — base bandar/bukan-Melayu kuat.")
        why.append("Menang walau pembangkang berjaya muafakat 1-lawan-1.")
        action = "PERTAHAN — jentera padat, jaga keluar mengundi bandar."
    else:
        why.append(f"Melayu {m:.0f}%: undi Melayu dominan — sukar untuk PH dalam 1-lawan-1.")
        if r["scenB"] == "PN":
            why.append("3-penjuru: PN paling untung warisi undi Melayu konservatif.")
        elif r["scenB"] == "BN":
            why.append("3-penjuru: BN kekal kuat (legasi tempatan) — bukan medan PH.")
        else:
            why.append("3-penjuru: PH boleh muncul jika undi Melayu pecah tajam.")
        why.append(f"Anggaran: PH {r['phBase']:.0f}% · PN {r['pnSolo']:.0f}% · BN {r['bnSolo']:.0f}%.")
        action = ("STRETCH — boleh dicabar jika split tajam + naratif Madani pulih."
                  if r["gapB"] <= 12 else
                  "LAWAN KUAT — fokus naratif, jangan over-extend sumber.")
    return why, action


# ── Model senario ─────────────────────────────────────────────────────────
def compute(seats: list[dict]) -> dict:
    rows = []
    for s in seats:
        mn = float(s.get("pasMnWinProb") or 0)
        pn = float(s.get("pasSoloWinProb") or 0)
        bn = float(s.get("bnSoloWinProb") or 0)
        ph = round(100 - mn, 1)
        scen_a = "PH" if mn < 50 else "OPP"  # 1-vs-1 vs muafakat
        sc = {"PH": ph, "PN": pn, "BN": bn}
        scen_b = max(sc, key=sc.get)          # 3 penjuru plurality
        gap_b = round(sc[scen_b] - ph, 1)     # jarak PH di belakang pemenang 3-penjuru
        eth = (s.get("census") or {}).get("districtEthnicityPct") or {}
        r = {
            "id": s.get("id"), "name": s.get("name"), "district": s.get("district") or "—",
            "incumbent2022": s.get("winnerName2022") or s.get("incumbent"),
            "coalition2022": s.get("winner2022") or s.get("semasaKoalisi"),
            "majority2022": s.get("majority2022") or s.get("majority") or 0,
            "phBase": ph, "pnSolo": round(pn, 1), "bnSolo": round(bn, 1), "mnOpp": round(mn, 1),
            "scenA": scen_a, "scenB": scen_b, "gapB": gap_b,
            "malay": eth.get("malay"), "chinese": eth.get("chinese"),
            "indian": eth.get("indian"), "other": eth.get("other"),
            "socmedMentions": s.get("socmedMentions") or 0,
        }
        r["why"], r["action"] = _narrative(r)
        rows.append(r)
    a = Counter(r["scenA"] for r in rows)
    b = Counter(r["scenB"] for r in rows)
    ph_safe = [r for r in rows if r["scenA"] == "PH"]
    # Stretch targets: PH kalah muafakat, tapi paling rapat (gap terkecil) dalam 3 penjuru
    stretch = sorted([r for r in rows if r["scenA"] != "PH"], key=lambda r: r["gapB"])[:8]
    base22 = Counter(s.get("winner2022") for s in seats)
    byreg = defaultdict(lambda: Counter())
    for r in rows:
        byreg[r["district"]]["PH" if r["scenA"] == "PH" else "OPP"] += 1
    return {
        "rows": rows, "scenA": dict(a), "scenB": dict(b),
        "phSafe": ph_safe, "stretch": stretch, "baseline2022": dict(base22),
        "byRegion": {k: dict(v) for k, v in sorted(byreg.items())},
        "generated": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }


# ── PPTX helpers ──────────────────────────────────────────────────────────
def _blank(prs):
    return prs.slides.add_slide(prs.slide_layouts[6])


def _bar(slide, title):
    bar = slide.shapes.add_shape(1, Inches(0), Inches(0), Inches(13.333), Inches(0.95))
    bar.fill.solid(); bar.fill.fore_color.rgb = NAVY; bar.line.fill.background()
    tb = slide.shapes.add_textbox(Inches(0.5), Inches(0.12), Inches(12.3), Inches(0.7))
    p = tb.text_frame.paragraphs[0]; p.text = title
    p.font.size = Pt(26); p.font.bold = True; p.font.color.rgb = WHITE


def _foot(slide, text=FOOT):
    tb = slide.shapes.add_textbox(Inches(0.4), Inches(7.05), Inches(12.5), Inches(0.35))
    p = tb.text_frame.paragraphs[0]; p.text = text
    p.font.size = Pt(9); p.font.color.rgb = GREY


def _bullets(slide, items, top=1.25, left=0.6, width=12.1, size=15, gap=True):
    tb = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(5.4))
    tf = tb.text_frame; tf.word_wrap = True
    for i, it in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        if isinstance(it, tuple):
            txt, color, bold = it
        else:
            txt, color, bold = it, SLATE, False
        p.text = f"•  {txt}"; p.font.size = Pt(size); p.font.color.rgb = color
        p.font.bold = bold
        if gap:
            p.space_after = Pt(8)


def _table(slide, headers, data, top=1.2, left=0.5, width=12.3, col_w=None, fs=11):
    rows, cols = len(data) + 1, len(headers)
    h = min(5.5, 0.34 * rows + 0.1)
    gt = slide.shapes.add_table(rows, cols, Inches(left), Inches(top), Inches(width), Inches(h)).table
    if col_w:
        for ci, w in enumerate(col_w):
            gt.columns[ci].width = Inches(w)
    for ci, head in enumerate(headers):
        c = gt.cell(0, ci); c.text = head
        pr = c.text_frame.paragraphs[0]; pr.font.size = Pt(fs); pr.font.bold = True
        pr.font.color.rgb = WHITE; c.fill.solid(); c.fill.fore_color.rgb = NAVY
    for ri, drow in enumerate(data, start=1):
        for ci, val in enumerate(drow):
            c = gt.cell(ri, ci); c.text = str(val)
            pr = c.text_frame.paragraphs[0]; pr.font.size = Pt(fs - 1)
            pr.font.color.rgb = SLATE
            c.fill.solid(); c.fill.fore_color.rgb = RGBColor(243, 246, 250) if ri % 2 else WHITE


def _seat_slide(prs, r: dict):
    s = _blank(prs)
    _bar(s, f"{r['id']} {r['name']} — {r['district']}")
    _foot(s)
    is_ph = r["scenA"] == "PH"
    # Sub-header badge row
    tb = s.shapes.add_textbox(Inches(0.6), Inches(1.05), Inches(12.1), Inches(0.9))
    tf = tb.text_frame; tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = (f"PRN 2022: {r['coalition2022']} · majoriti {int(r['majority2022']):,}    |    "
              f"Etnik (daerah): Melayu {r['malay'] or 0:.0f}% · Cina {r['chinese'] or 0:.0f}% · "
              f"India {r['indian'] or 0:.0f}%")
    p.font.size = Pt(13); p.font.color.rgb = SLATE
    p2 = tf.add_paragraph()
    scen_b_label = {"PH": "PH", "PN": "PN", "BN": "BN"}[r["scenB"]]
    p2.text = (f"Senario A (1-vs-1): {'PH MENANG' if is_ph else 'Muafakat menang'}    ·    "
               f"Senario B (3-penjuru): {scen_b_label} teratas")
    p2.font.size = Pt(14); p2.font.bold = True
    p2.font.color.rgb = GREEN if is_ph else AMBER
    # Reasoning bullets
    items = [(w, SLATE, False) for w in r["why"]]
    items.append((f"Tindakan: {r['action']}", GREEN if is_ph else NAVY, True))
    _bullets(s, items, top=2.2, size=15)
    # Scenario mini-table
    _table(s,
        ["Bloc", "Anggaran %", "1-vs-1 (muafakat)", "3-penjuru"],
        [
            ["PH", f"{r['phBase']:.0f}", "MENANG" if is_ph else "kalah", "teratas" if r["scenB"] == "PH" else "—"],
            ["PN solo", f"{r['pnSolo']:.0f}", "—", "teratas" if r["scenB"] == "PN" else "—"],
            ["BN solo", f"{r['bnSolo']:.0f}", "—", "teratas" if r["scenB"] == "BN" else "—"],
            ["Muafakat PN+BN", f"{r['mnOpp']:.0f}", "MENANG" if not is_ph else "kalah", "(berpecah)"],
        ],
        top=4.7, left=0.6, width=8.8, col_w=[3.0, 1.8, 2.2, 1.8], fs=11)
    return s


def build_ppt(R: dict) -> Presentation:
    prs = Presentation()
    prs.slide_width = Inches(13.333); prs.slide_height = Inches(7.5)
    a, b = R["scenA"], R["scenB"]
    opp_a = a.get("OPP", 0); ph_a = a.get("PH", 0)

    # 1 — Title
    s = _blank(prs)
    box = s.shapes.add_shape(1, Inches(0), Inches(0), Inches(13.333), Inches(7.5))
    box.fill.solid(); box.fill.fore_color.rgb = NAVY; box.line.fill.background()
    t = s.shapes.add_textbox(Inches(0.8), Inches(2.2), Inches(11.7), Inches(3))
    tf = t.text_frame; tf.word_wrap = True
    p = tf.paragraphs[0]; p.text = "PRN Johor 2026"
    p.font.size = Pt(46); p.font.bold = True; p.font.color.rgb = WHITE
    p2 = tf.add_paragraph(); p2.text = "Senario: PH Bertanding SOLO di Semua 56 Kerusi DUN"
    p2.font.size = Pt(26); p2.font.color.rgb = RGBColor(186, 230, 253)
    p3 = tf.add_paragraph()
    p3.text = "Analisis 2 konfigurasi lawan: (A) Muafakat PN+BN 1-vs-1 · (B) PN solo + BN solo 3-penjuru"
    p3.font.size = Pt(15); p3.font.color.rgb = RGBColor(203, 213, 225)
    p4 = tf.add_paragraph(); p4.text = f"InsightPulse Analytics · {R['generated']}"
    p4.font.size = Pt(13); p4.font.color.rgb = GREY

    # 2 — Agenda
    s = _blank(prs); _bar(s, "Agenda"); _foot(s)
    _bullets(s, [
        "Konteks PRN Johor 2026 & baseline PRN 2022",
        "Andaian senario & metodologi (data-driven, bukan polling SPR)",
        "Senario A — PH solo vs Muafakat PN+BN (1 lawan 1)",
        "Senario B — PH solo vs PN solo + BN solo (3 penjuru)",
        "13 kerusi 'lantai' PH & sebab 3-penjuru tidak untungkan PH",
        "Implikasi strategik (PH & pihak lawan) + nota penting",
    ])

    # 3 — Konteks + baseline 2022
    s = _blank(prs); _bar(s, "Konteks PRN Johor 2026"); _foot(s)
    b22 = R["baseline2022"]
    _bullets(s, [
        "56 kerusi DUN · majoriti untuk bentuk kerajaan: 29 · Mengundi: 11 Julai 2026",
        (f"Baseline PRN Johor (12 Mac 2022): BN {b22.get('BN',0)} · PH {b22.get('PH',0)} · "
         f"PN {b22.get('PN',0)} · MUDA {b22.get('MUDA',0)}", NAVY, True),
        ("DISAHKAN (video rasmi Anwar Ibrahim, 22 Jun 2026): PH bertanding SOLO 56 kerusi — "
         "DAP 17, baki PKR + Amanah", GREEN, True),
        "PH solo bukan pilihan — pihak lawan tak mahu pakatan dengan PH",
        ("Lawan PH = UMNO/BN DAN PN (bertanding berasingan) → realistik 3 PENJURU", NAVY, True),
        ("Bahan ini analitik dalaman — anggaran model, bukan keputusan rasmi SPR", AMBER, True),
    ], size=14)

    # 4 — Metodologi
    s = _blank(prs); _bar(s, "Andaian & Metodologi"); _foot(s)
    _bullets(s, [
        "Hybrid model: baseline PRN 2022 (majoriti) + DOSM etnik + crawl socmed",
        "Kekuatan pembangkang BERSATU (muafakat) = pasMnWinProb → Senario A (1-vs-1)",
        "Kekuatan PN solo = pasSoloWinProb · BN solo = bnSoloWinProb → Senario B (3-penjuru)",
        "Base PH (1-vs-1) dianggar = 100 − kekuatan muafakat pembangkang",
        "Senario B = plurality 3 penjuru: pemenang = tertinggi antara PH / PN / BN",
        ("Semua peratus = anggaran analitik; sah untuk perbincangan, bukan ramalan muktamad", AMBER, True),
    ], size=14)

    # 5 — Scenario A
    s = _blank(prs); _bar(s, "Senario A — PH Solo vs Muafakat PN+BN (1 lawan 1)"); _foot(s)
    _bullets(s, [
        (f"PH menang ~{ph_a} kerusi  ·  Muafakat PN+BN ~{opp_a} kerusi", NAVY, True),
        "Undi pembangkang/Melayu BERSATU di belakang satu calon — paling sukar untuk PH",
        "PH hanya pertahankan kubu bandar / majoriti bukan-Melayu",
        f"Muafakat menyapu majoriti besar ({opp_a}/56) — jauh melepasi ambang 29",
        ("Risiko PH: kalah teruk jika pembangkang berjaya muafakat 1-vs-1", RED, True),
    ])

    # 6 — Scenario B
    s = _blank(prs); _bar(s, "Senario B — PH Solo vs PN Solo + BN Solo (3 Penjuru)"); _foot(s)
    _bullets(s, [
        ("★ KES ASAS REALISTIK — video rasmi: PH lawan BN DAN PN (bertanding berasingan)",
         GREEN, True),
        (f"Pemenang 3-penjuru: PN ~{b.get('PN',0)} · PH ~{b.get('PH',0)} · BN ~{b.get('BN',0)}",
         NAVY, True),
        "Pecahan undi berlaku di pihak LAWAN (PN vs BN), bukan memihak PH",
        "PH TIDAK menang tambahan — base Melayu PH terlalu rendah pasca-2022",
        "3-penjuru jadi pertarungan PN lwn BN untuk kerusi Melayu; PH kekal ~13",
        ("Insight: split lawan ialah masalah PN-BN, bukan durian runtuh untuk PH", GREEN, True),
    ], size=14)

    # 7 — Perbandingan
    s = _blank(prs); _bar(s, "Perbandingan Ringkas — 56 Kerusi"); _foot(s)
    _table(s,
        ["Senario", "PH", "PN", "BN", "Muafakat (PN+BN)", "Catatan"],
        [
            ["PRN 2022 (rasmi)", b22.get("PH", 0), b22.get("PN", 0), b22.get("BN", 0), "—", "BN dominan"],
            ["A · Muafakat 1-vs-1", ph_a, "—", "—", opp_a, "Lawan bersatu"],
            ["B · 3 penjuru", b.get("PH", 0), b.get("PN", 0), b.get("BN", 0), "—", "Lawan berpecah"],
        ],
        top=1.5, col_w=[2.6, 1.2, 1.2, 1.2, 2.6, 3.5], fs=13)
    tb = s.shapes.add_textbox(Inches(0.6), Inches(4.2), Inches(12), Inches(1.5))
    tf = tb.text_frame; tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = ("Kesimpulan: jumlah kerusi PH hampir sama (~%d) dalam kedua-dua senario. "
              "Perbezaan utama hanya pada PEMBAHAGIAN kerusi pembangkang." % ph_a)
    p.font.size = Pt(14); p.font.bold = True; p.font.color.rgb = NAVY

    # 8 — PH safe seats
    s = _blank(prs); _bar(s, f"{ph_a} Kerusi 'Lantai' PH (Menang Walau Lawan Bersatu)"); _foot(s)
    safe = R["phSafe"]
    data = [[r["id"], r["name"], r["district"], r["coalition2022"], f"{r['phBase']:.0f}%"]
            for r in safe]
    _table(s, ["DUN", "Nama", "Daerah", "2022", "PH base"], data,
           top=1.25, col_w=[1.1, 3.2, 2.6, 1.3, 1.6], fs=11)

    # 9 — Why 3-corner doesn't help + stretch
    s = _blank(prs); _bar(s, "Mengapa 3-Penjuru Tidak Untungkan PH"); _foot(s)
    _bullets(s, [
        "Di kerusi Melayu majoriti, base PH (anggaran 1-vs-1) lebih rendah daripada PN solo",
        "Walau lawan berpecah, undi PH masih tidak cukup untuk plurality",
        "Sebaliknya PN paling untung daripada split (warisi undi Melayu konservatif)",
        "Kerusi 'stretch' PH (paling rapat dalam 3-penjuru) — perlu Madani pulih + split tajam:",
    ], size=14, gap=True)
    stretch = R["stretch"]
    data = [[r["id"], r["name"], r["district"], f"PH {r['phBase']:.0f}",
             f"PN {r['pnSolo']:.0f}", f"BN {r['bnSolo']:.0f}", f"gap {r['gapB']:.0f}"]
            for r in stretch]
    _table(s, ["DUN", "Nama", "Daerah", "PH", "PN", "BN", "Gap"], data,
           top=3.7, col_w=[1.0, 2.8, 2.4, 1.3, 1.3, 1.3, 1.3], fs=10)

    # 10 — Strategic implications
    s = _blank(prs); _bar(s, "Implikasi Strategik"); _foot(s)
    _bullets(s, [
        ("UNTUK PH:", NAVY, True),
        "Solo 56 = berisiko tinggi; fokus PERTAHAN ~13 kubu bandar (JB, Kulai, Skudai, Muar bandar)",
        "Jangan over-extend sumber ke kerusi Melayu majoriti yang sukar 1-vs-1",
        "Harapan terbaik PH = pembangkang GAGAL muafakat (3-penjuru) + naratif Madani pulih",
        ("UNTUK PIHAK LAWAN (PN/BN):", NAVY, True),
        "Muafakat 1-vs-1 = pulangan maksimum (~%d kerusi) & elak pecah undi" % opp_a,
        "Gagal muafakat → PN vs BN saling makan; PN cenderung paling untung",
    ], size=13)

    # 11 — Regional
    s = _blank(prs); _bar(s, "Pecahan Ikut Daerah (Senario A)"); _foot(s)
    reg = R["byRegion"]
    data = [[k, v.get("PH", 0), v.get("OPP", 0)] for k, v in reg.items()]
    _table(s, ["Daerah", "PH lantai", "Lawan"], data,
           top=1.25, left=3.0, width=7.2, col_w=[3.4, 1.9, 1.9], fs=12)

    # 12 — Divider: per-DUN
    s = _blank(prs); _bar(s, "Justifikasi Terperinci — 56 DUN Johor"); _foot(s)
    _bullets(s, [
        "Satu slaid setiap DUN: baseline 2022 · etnik daerah · senario A & B · tindakan",
        ("Kubu PH (lantai) ditanda PERTAHAN; kerusi lawan ditanda STRETCH / LAWAN KUAT", NAVY, True),
        "Susunan ikut kod DUN (N01–N56)",
    ])

    # 13..68 — Per-DUN slides (ikut kod DUN)
    for r in sorted(R["rows"], key=lambda x: (x["id"] or "")):
        _seat_slide(prs, r)

    # Notes
    s = _blank(prs); _bar(s, "Nota Penting & Penafian"); _foot(s)
    _bullets(s, [
        ("DISAHKAN: PH solo 56 — video rasmi Anwar Ibrahim, 22 Jun 2026 (mengundi 11 Julai)",
         GREEN, True),
        "Angka = anggaran model hybrid (PRN 2022 + DOSM + socmed) — BUKAN keputusan SPR",
        "Base PH dianggar daripada kekuatan muafakat pembangkang; sensitif kepada gelombang Madani",
        "Jika sokongan PH pulih lebih kuat daripada andaian, siling PH boleh naik melepasi 13",
        "BN & PN bertanding berasingan → Senario B (3-penjuru) ialah kes asas realistik",
        "Konfigurasi calon penuh (penamaan 28 Jun) boleh laras dinamik per-DUN",
    ], size=13)

    # 13 — Thanks
    s = _blank(prs)
    box = s.shapes.add_shape(1, Inches(0), Inches(0), Inches(13.333), Inches(7.5))
    box.fill.solid(); box.fill.fore_color.rgb = NAVY; box.line.fill.background()
    t = s.shapes.add_textbox(Inches(0.8), Inches(3), Inches(11.7), Inches(2))
    p = t.text_frame.paragraphs[0]; p.text = "Terima Kasih"
    p.font.size = Pt(40); p.font.bold = True; p.font.color.rgb = WHITE
    p2 = t.text_frame.add_paragraph()
    p2.text = "InsightPulse · Sokong Keputusan dengan Data"
    p2.font.size = Pt(16); p2.font.color.rgb = RGBColor(186, 230, 253)
    return prs


def build_markdown(R: dict) -> str:
    a, b = R["scenA"], R["scenB"]; b22 = R["baseline2022"]
    lines = [
        "# PRN Johor 2026 — Senario PH Solo 56 DUN",
        f"_Dijana: {R['generated']} · Anggaran analitik, bukan keputusan SPR_\n",
        "## Baseline PRN Johor 2022",
        f"- BN {b22.get('BN',0)} · PH {b22.get('PH',0)} · PN {b22.get('PN',0)} · MUDA {b22.get('MUDA',0)} (majoriti kerajaan = 29)\n",
        "## Ringkasan Senario (56 kerusi)",
        f"- **A · Muafakat PN+BN (1-vs-1):** PH ~{a.get('PH',0)} | Muafakat ~{a.get('OPP',0)}",
        f"- **B · PN solo + BN solo (3-penjuru):** PN ~{b.get('PN',0)} · PH ~{b.get('PH',0)} · BN ~{b.get('BN',0)}",
        "- PH kekal ~%d kerusi dalam kedua-dua senario; 3-penjuru hanya agih kerusi pembangkang.\n" % a.get("PH", 0),
        "## Kerusi 'lantai' PH",
    ]
    for r in R["phSafe"]:
        lines.append(f"- {r['id']} {r['name']} ({r['district']}, 2022 {r['coalition2022']}) — PH base ~{r['phBase']:.0f}%")
    lines.append("\n## Kerusi 'stretch' PH (upside jika split tajam + Madani pulih)")
    for r in R["stretch"]:
        lines.append(f"- {r['id']} {r['name']} ({r['district']}) — PH {r['phBase']:.0f} | PN {r['pnSolo']:.0f} | BN {r['bnSolo']:.0f} (gap {r['gapB']:.0f})")
    lines += [
        "\n## Implikasi",
        "- **PH:** solo 56 berisiko; fokus pertahan ~13 kubu bandar; harap pembangkang gagal muafakat.",
        "- **Lawan:** muafakat 1-vs-1 = pulangan maksimum; gagal muafakat → PN paling untung daripada split.",
        "\n## Jadual penuh 56 DUN",
        "| DUN | Nama | Daerah | 2022 | Maj | Melayu% | Cina% | India% | PH% | PN% | BN% | Senario A | Senario B |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in sorted(R["rows"], key=lambda x: (x["id"] or "")):
        lines.append(
            f"| {r['id']} | {r['name']} | {r['district']} | {r['coalition2022']} | "
            f"{int(r['majority2022']):,} | {r['malay'] or 0:.0f} | {r['chinese'] or 0:.0f} | "
            f"{r['indian'] or 0:.0f} | {r['phBase']:.0f} | {r['pnSolo']:.0f} | {r['bnSolo']:.0f} | "
            f"{'PH' if r['scenA']=='PH' else 'Muafakat'} | {r['scenB']} |"
        )
    return "\n".join(lines)


def main() -> None:
    seats = json.loads(SEATS_JSON.read_text(encoding="utf-8"))
    R = compute(seats)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(R, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_MD.write_text(build_markdown(R), encoding="utf-8")
    prs = build_ppt(R)
    prs.save(str(OUT_PPT))
    for dest in (DESKTOP_PPT, DOWNLOADS_PPT):
        try:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(OUT_PPT.read_bytes())
            print(f"  copy → {dest}")
        except Exception as exc:  # noqa: BLE001
            print(f"  ⚠ copy gagal {dest}: {exc}")
    print(f"✅ PPT:  {OUT_PPT} ({len(prs.slides._sldIdLst)} slides)")
    print(f"✅ MD:   {OUT_MD}")
    print(f"✅ JSON: {OUT_JSON}")
    print(f"Senario A: {R['scenA']} | Senario B: {R['scenB']}")


if __name__ == "__main__":
    sys.exit(main())
