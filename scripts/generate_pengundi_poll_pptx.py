#!/usr/bin/env python3
"""Generate Pengundi Malaysia poll PPTX — insight operasi + cadangan tindakan PRN N9."""
from __future__ import annotations

import csv
import re
from collections import Counter
from datetime import datetime, timezone, timedelta
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import MSO_AUTO_SIZE, PP_ALIGN
from pptx.util import Inches, Pt

ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "data/analyzed/Sentiment_Emotion_FACEBOOK_20260705_000328.csv"
REPORT_DIR = ROOT / "reports/20260705_000328_httpswwwfacebookcomstoryphpstory_fbid1579205333771"
OUT_DIR = ROOT / "data/projects/political/PRN/PRN_N9/reports/cula_digital"
OUT_PPTX = OUT_DIR / "Pengundi_Malaysia_Poll_N9_Insight_Tindakan.pptx"
OUT_PPTX_REPORT = REPORT_DIR / "Pengundi_Malaysia_Poll_N9_Insight_Tindakan.pptx"

POST_URL = "https://www.facebook.com/story.php?story_fbid=1579205333771288&id=100050455091322"
MYT = timezone(timedelta(hours=8))

NAVY = RGBColor(0, 51, 102)
GREEN = RGBColor(26, 127, 90)
PAS_GREEN = RGBColor(22, 163, 74)
RED = RGBColor(200, 16, 46)
AMBER = RGBColor(217, 119, 6)
GREY = RGBColor(100, 116, 139)
SLATE = RGBColor(30, 41, 59)
WHITE = RGBColor(255, 255, 255)


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


def _footer(slide, note: str = "InsightPulse · Pengundi Malaysia Poll N9 · Bukan polling SPR"):
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


def _num(row: dict, key: str, default: float = 0) -> float:
    try:
        return float(row.get(key) or default)
    except (TypeError, ValueError):
        return default


def _classify_vote(t: str) -> str:
    t = (t or "").strip().lower()
    if re.search(r"\(b\)|^b[\.\)\s,/]|^b$|tidak\s*sokong|tak\s*sokong|x\s*sokong|tak\s*setuju|no way", t):
        return "B"
    if re.search(r"\(a\)|^a[\.\)\s,/]|^a$|a\s*sokong|aaa\s*sokong|option\s*a", t):
        return "A"
    if re.search(
        r"sokong.*(umno|pas)|lawan.*(dap|ph|harapan)|tolak.*(dap|ph)|bersatu.*melayu|demi.*(melayu|islam|ummah)",
        t,
    ):
        return "A_soft"
    if re.search(r"tak\s*sokong|tidak\s*setuju|jgn\s*gabung|no way", t):
        return "B"
    return "other"


def analyze_csv(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    comments = [r for r in rows if str(r.get("Type", "")).lower() == "comment"]
    post = next((r for r in rows if str(r.get("Type", "")).lower() == "post"), {})

    votes = Counter()
    demo_votes: dict[str, Counter] = {}
    sent = Counter()
    emo = Counter()
    demo = Counter()
    top_comments: list[tuple[float, str, str]] = []

    for r in comments:
        text = r.get("Text", "")
        v = _classify_vote(text)
        votes[v] += 1
        d = r.get("demographic") or "Unknown"
        demo[d] += 1
        demo_votes.setdefault(d, Counter())[v] += 1
        sent[r.get("Sentiment", "")] += 1
        emo[r.get("emotion_primary", "")] += 1
        try:
            eng = float(r.get("total_engagement") or r.get("likes") or 0)
        except (TypeError, ValueError):
            eng = 0.0
        if text.strip():
            top_comments.append((eng, text.strip().replace("\n", " ")[:100], r.get("Sentiment", "")))

    top_comments.sort(key=lambda x: -x[0])
    a = votes["A"] + votes["A_soft"]
    b = votes["B"]
    decided = a + b or 1
    total_eng = sum(_num(r, "total_engagement") for r in comments)

    post_likes = int(_num(post, "likes"))
    post_shares = int(_num(post, "shares"))
    post_comments_fb = int(_num(post, "comments_count"))
    post_total_eng = int(_num(post, "total_engagement"))
    if post_total_eng <= 0:
        post_total_eng = post_likes + post_shares + post_comments_fb

    fb_comments = post_comments_fb or 781
    capture_pct = round(len(comments) / fb_comments * 100) if fb_comments else 0

    return {
        "generated": datetime.now(MYT).strftime("%Y-%m-%d %H:%M"),
        "post_url": POST_URL,
        "page": "Pengundi Malaysia",
        "question": "Adakah anda sokong kerjasama UMNO & PAS untuk lawan Pakatan Harapan di PRN Negeri Sembilan?",
        "total_rows": len(rows),
        "comments_crawled": len(comments),
        "fb_comments_reported": fb_comments,
        "post_likes": post_likes,
        "post_shares": post_shares,
        "post_comments_fb": post_comments_fb,
        "post_total_engagement": post_total_eng,
        "capture_pct": capture_pct,
        "engagement": int(total_eng),
        "votes": votes,
        "a_count": a,
        "b_count": b,
        "a_pct": round(a / decided * 100, 1),
        "b_pct": round(b / decided * 100, 1),
        "decided": decided,
        "other_pct": round(votes["other"] / len(comments) * 100, 1) if comments else 0,
        "sent": sent,
        "emo": emo,
        "demo": demo,
        "demo_votes": demo_votes,
        "top_comments": top_comments[:12],
        "post_text": (post.get("Text") or "")[:200],
    }


def build_presentation(stats: dict) -> Presentation:
    prs = Presentation()
    prs.slide_width = Inches(10)
    prs.slide_height = Inches(7.5)
    v = stats["votes"]

    # 1 Title
    s = _blank(prs)
    tf = _box(s, 0.5, 1.2, 9, 1.4)
    _para(tf, "Pengundi Malaysia · Poll FB N9", size=34, bold=True, color=NAVY, first=True)
    _para(tf, "Insight Operasi & Cadangan Tindakan — UMNO+PAS vs PH", size=20, color=PAS_GREEN)
    tf2 = _box(s, 0.5, 2.9, 9, 1.6)
    pe = stats["post_total_engagement"]
    _para(
        tf2,
        f"Engagement post: {pe:,} "
        f"(👍 {stats['post_likes']:,} · 💬 {stats['post_comments_fb']:,} · ↗ {stats['post_shares']:,})",
        size=16,
        color=SLATE,
        first=True,
    )
    _para(
        tf2,
        f"{stats['comments_crawled']} komen di crawl · {stats['engagement']:,} engagement komen (InsightPulse)",
        size=14,
        color=GREY,
    )
    _para(tf2, "Post URL Batch · InsightPulse Social Listening · Bukan polling SPR", size=13, color=GREY)
    _para(tf2, f"Dijana: {stats['generated']}", size=12, color=GREY)
    _footer(s)

    # 2 Cara baca
    s = _blank(prs)
    _header(s, "Cara Baca Laporan Ini")
    tf = _box(s, 0.5, 1.1, 9, 5.5)
    bullets = [
        f"Sumber: 1 post FB «Pengundi Malaysia» — engagement post {stats['post_total_engagement']:,} "
        f"(like {stats['post_likes']:,} + komen {stats['post_comments_fb']:,} + share {stats['post_shares']:,}).",
        f"Poll A/B via komen — {stats['fb_comments_reported']} komen di FB, {stats['comments_crawled']} captured ≈{stats['capture_pct']}%.",
        "Soalan: Sokong kerjasama UMNO & PAS lawan Pakatan Harapan di PRN Negeri Sembilan?",
        "Klasifikasi: (A) Sokong eksplisit · (A-soft) implisit pro-MN · (B) Tidak Sokong · Other = debat/nuansa.",
        f"Angka undi: {stats['a_pct']}% Sokong vs {stats['b_pct']}% Tolak (komen yang jelas ambil pihak, n={stats['decided']}).",
        "Sentimen & emosi = nuansa nada (boleh sokong coalisi tapi nada anti-DAP/PH).",
        "Demografi = proxy bahasa (BM/Cina/India/Urban) — bukan profil FB rasmi.",
    ]
    for i, b in enumerate(bullets):
        _para(tf, f"• {b}", size=14, first=(i == 0), space=10)
    _footer(s)

    # 3 Ringkasan eksekutif
    s = _blank(prs)
    _header(s, "Ringkasan Eksekutif")
    _kpi_card(s, 0.4, 1.05, f"{stats['post_total_engagement']:,}", "Engagement Post", NAVY)
    _kpi_card(s, 2.65, 1.05, stats["comments_crawled"], "Komen Crawl")
    _kpi_card(s, 4.9, 1.05, f"{stats['a_pct']}%", "Sokong (A)", PAS_GREEN)
    _kpi_card(s, 7.15, 1.05, f"{stats['b_pct']}%", "Tidak Sokong (B)", RED)

    tf = _box(s, 0.45, 2.35, 9, 4.2)
    _para(tf, "Temuan utama", size=18, bold=True, color=NAVY, first=True, space=10)
    findings = [
        f"Post viral: {stats['post_total_engagement']:,} engagement FB "
        f"({stats['post_likes']:,} like · {stats['post_comments_fb']:,} komen · {stats['post_shares']:,} share) — reach tinggi untuk N9.",
        f"Sokong UMNO+PAS lawan PH: ~{stats['a_pct']}% vs {stats['b_pct']}% tolak (komen jelas, n={stats['decided']}) — naratif MN condong kuat.",
        f"{stats['other_pct']}% komen = debat/nuansa (contoh: sokong tapi tolak gabung UMNO) — jangan over-claim kemenangan.",
        f"Sentimen: {stats['sent'].get('negative', 0)} neg ({stats['sent'].get('negative', 0)/max(stats['comments_crawled'],1)*100:.0f}%) · "
        f"{stats['sent'].get('positive', 0)} pos · {stats['sent'].get('neutral', 0)} neutral — sokong coalisi, nada sering anti-DAP/PH.",
        f"Emosi dominan: Love {stats['emo'].get('love', 0)} ({stats['emo'].get('love', 0)/max(stats['comments_crawled'],1)*100:.0f}%) — frame penyatuan ummah/Melayu.",
        f"Audiens: Melayu/Bumiputera {stats['demo'].get('Malay/Bumiputera', 0)} ({stats['demo'].get('Malay/Bumiputera', 0)/max(stats['comments_crawled'],1)*100:.0f}%) — selaras sasaran MN N9.",
        "Implikasi: naratif «lawan DAP/PH» resonan; elak over-celebrate — galvanize debat → jawapan A.",
    ]
    for i, f in enumerate(findings):
        _para(tf, f"• {f}", size=13, first=(i == 0), space=7)
    _footer(s)

    # 4 A vs B
    s = _blank(prs)
    _header(s, f"Soalan Poll A/B — {stats['comments_crawled']} Komen")
    tf = _box(s, 0.45, 1.0, 4.4, 2.5)
    _para(tf, "Pecahan undi (komen)", size=14, bold=True, color=NAVY, first=True)
    for label, key in [("(A) Sokong eksplisit", "A"), ("(A) Sokong implisit", "A_soft"), ("(B) Tidak Sokong", "B"), ("Debat / other", "other")]:
        n = v[key]
        pct = round(n / stats["comments_crawled"] * 100, 1)
        _para(tf, f"{label}: {n} ({pct}%)", size=13, space=4)
    tf2 = _box(s, 5.0, 1.0, 4.5, 2.5)
    _para(tf2, "Komen jelas ambil pihak", size=14, bold=True, color=PAS_GREEN, first=True)
    _para(tf2, f"Sokong (A): {stats['a_count']} ({stats['a_pct']}%)", size=16, bold=True, color=PAS_GREEN, space=6)
    _para(tf2, f"Tidak Sokong (B): {stats['b_count']} ({stats['b_pct']}%)", size=16, bold=True, color=RED, space=6)
    _para(
        tf2,
        f"Engagement post: {stats['post_total_engagement']:,} "
        f"(👍{stats['post_likes']:,} 💬{stats['post_comments_fb']:,} ↗{stats['post_shares']:,})",
        size=13,
        bold=True,
        color=NAVY,
        space=6,
    )
    _para(tf2, f"Crawl {stats['comments_crawled']}/{stats['fb_comments_reported']} komen ({stats['capture_pct']}%)", size=12, color=GREY)

    tf3 = _box(s, 0.45, 3.5, 9, 3.2)
    _para(tf3, "Maksud operasi", size=16, bold=True, color=PAS_GREEN, first=True)
    _para(
        tf3,
        "Page umum pro-MN — bukan sampling representatif seluruh N9. Gunakan sebagai signal digital, "
        "bukan angka undi rasmi.",
        size=14,
        space=8,
    )
    _para(
        tf3,
        f"Ramai ({stats['other_pct']}%) tidak jawab A/B terus — mereka DEBAT (anti-DAP, pro-Melayu, skeptikal UMNO). "
        "Tugas: tukar debat → sokong MN dengan mesej ringkas.",
        size=14,
        space=8,
    )
    _footer(s)

    # 5 Sentimen & emosi
    s = _blank(prs)
    _header(s, "Sentimen & Emosi — Nuansa Naratif")
    tf = _box(s, 0.45, 1.05, 4.3, 2.3)
    _para(tf, "Sentimen komen", size=14, bold=True, color=NAVY, first=True)
    total = stats["comments_crawled"] or 1
    for k in ("negative", "positive", "neutral"):
        n = stats["sent"].get(k, 0)
        _para(tf, f"{k.capitalize()}: {n} ({n/total*100:.1f}%)", size=13, space=4)
    tf2 = _box(s, 5.0, 1.05, 4.5, 2.3)
    _para(tf2, "Emosi dominan", size=14, bold=True, color=NAVY, first=True)
    for k, n in stats["emo"].most_common(5):
        if k:
            _para(tf2, f"{k}: {n} ({n/total*100:.1f}%)", size=13, space=4)
    tf3 = _box(s, 0.45, 3.4, 9, 3.5)
    _para(tf3, "Insight", size=16, bold=True, color=AMBER, first=True)
    _para(
        tf3,
        "Negatif tinggi ≠ tolak coalisi — kebanyakan negatif = hina DAP/PH/Aminuddin, bukan tolak PAS+UMNO.",
        size=14,
        space=8,
    )
    _para(
        tf3,
        "Love 53% = frame emosi «penyatuan ummah/Melayu» — guna dalam mesej kempen, bukan debat agama kasar.",
        size=14,
        space=8,
    )
    _footer(s)

    # 6 Demografi
    demo_rows = []
    for d, n in stats["demo"].most_common(6):
        pct = round(n / total * 100, 1)
        dv = stats["demo_votes"].get(d, Counter())
        a_d = dv["A"] + dv["A_soft"]
        b_d = dv["B"]
        dec = a_d + b_d
        split = f"A {a_d/dec*100:.0f}% / B {b_d/dec*100:.0f}%" if dec >= 10 else "—"
        demo_rows.append([d, str(n), f"{pct}%", split])
    _table_slide(prs, "Demografi Audiens (Proxy Bahasa)", ["Kumpulan", "Komen", "%", "Sokong/Tolak"], demo_rows)

    # 7 Top comments
    comment_rows = []
    for eng, text, sent in stats["top_comments"][:10]:
        vote = _classify_vote(text)
        vote_l = {"A": "A", "A_soft": "A*", "B": "B"}.get(vote, "—")
        comment_rows.append([str(int(eng)), vote_l, sent[:12], text[:70]])
    _table_slide(
        prs,
        "Top 10 Komen — Engagement Tertinggi",
        ["Eng", "Undi", "Sentimen", "Komen (ringkas)"],
        comment_rows,
        font_size=8,
    )

    # 8 P1
    _action_slide(
        prs,
        "Tindakan Segera — 7 Hari (P1)",
        [
            (
                "P1",
                "Monitor post Pengundi Malaysia — balas komen B/tolak & tanya semula: «A Sokong atau B Tidak Sokong?»",
                "Admin digital + 2 sukarelawan · 2× sehari · KPI: 20 balasan berstruktur",
            ),
            (
                "P1",
                "Siarkan infographic 1-slide: MN lawan PH · elak pecah undi Melayu · data poll ~89% sokong (komen jelas).",
                "Media PAS N9 · share ke group WhatsApp kempen · Jumaat petang",
            ),
            (
                "P1",
                "Echo naratif «lawan DAP/PH» di ceramah/konten — guna frasa top komen (Melayu Islam, tolak pengaruh DAP).",
                "Comms N9 · brief semua ketua DUN · hari ini",
            ),
            (
                "P1",
                "Masukkan signal poll ke War Room Pulse Digital → Action Center (kerusi MN priority).",
                "HQ digital · update dashboard · sebelum war room mingguan",
            ),
        ],
    )

    # 9 P2
    _action_slide(
        prs,
        "Tindakan Momentum — 2–4 Minggu (P2)",
        [
            (
                "P2",
                "Ulang poll format serupa di page lain (PAS Rembau, Chembong, dll.) — banding A/B across DUN.",
                "Digital team · Post URL Batch InsightPulse · 1 post/minggu",
            ),
            (
                "P2",
                "Sedia 5 fakta rebut Pro-PH/debat skeptikal (BN solo, gila jawatan) — doc 1 muka surat.",
                "Comms + narrative lead · minggu 2",
            ),
            (
                "P2",
                "Jalankan Kerja 2 crawl: krisis adat/monarki N9 (Tuanku Muhriz vs Undang 4) — keyword search.",
                "InsightPulse · query C09 · Facebook + X + News",
            ),
            (
                "P2",
                "Banding poll digital vs cula lapangan (Modul #7 War Room) — validasi signal vs ground truth.",
                "HQ N9 · mingguan",
            ),
        ],
    )

    # 10 Mesej
    s = _blank(prs)
    _header(s, "Mesej Disyorkan — Ringkas & Boleh Copy")
    tf = _box(s, 0.45, 1.05, 9, 5.8)
    messages = [
        ("Balas komen debat", "Terima kasih. PRN N9: PH kalah = matlamat bersama. Sokong A — UMNO+PAS elak pecah undi Melayu. 💚"),
        ("Post susulan", f"Poll Pengundi Malaysia: ~{stats['a_pct']}% sokong MN lawan PH. Bukan masa pecah — fokus lawan DAP."),
        ("Frame emosi", "Demi penyatuan ummah & tanah pusaka — pilih kerjasama, tolak pengaruh DAP."),
        ("Elak", "Jangan over-claim «menang» — galvanize debat → jawab A atau B. Footnote: bukan polling SPR."),
    ]
    for i, (title, msg) in enumerate(messages):
        _para(tf, title, size=13, bold=True, color=NAVY, first=(i == 0), space=4)
        _para(tf, f'"{msg}"', size=12, color=SLATE, space=10)
    _footer(s)

    # 11 Risiko
    s = _blank(prs)
    _header(s, "Risiko & Mitigasi")
    tf = _box(s, 0.45, 1.05, 9, 5.8)
    risks = [
        (f"Sokong {stats['a_pct']}% ≠ undi di urn", "Galvanize: debat → event/cula · tanda sokongan di lapangan"),
        (f"{stats['other_pct']}% debat/nuansa", "Follow-up: «A atau B?» · jangan label «atas pagar»"),
        ("Audiens page umum — bias pro-MN", "Footnote sentiasa: signal digital, bukan sampling N9 penuh"),
        ("Nada negatif 42% — risiko salah baca", "Negatif = anti-DAP/PH, bukan anti-coalisi — jangan ubah mesej"),
    ]
    for i, (r, m) in enumerate(risks):
        _para(tf, r, size=14, bold=True, color=RED if i < 2 else AMBER, first=(i == 0), space=4)
        _para(tf, f"→ {m}", size=13, color=SLATE, space=10)
    _footer(s)

    return prs


def main() -> None:
    if not CSV_PATH.exists():
        raise SystemExit(f"CSV not found: {CSV_PATH}")
    stats = analyze_csv(CSV_PATH)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    prs = build_presentation(stats)
    prs.save(str(OUT_PPTX))
    prs.save(str(OUT_PPTX_REPORT))
    print(f"✅ Saved: {OUT_PPTX}")
    print(f"✅ Saved: {OUT_PPTX_REPORT}")
    print(f"   Slides: {len(prs.slides)}")
    print(
        f"   Post engagement {stats['post_total_engagement']:,} | "
        f"Sokong {stats['a_pct']}% | Tolak {stats['b_pct']}% | Komen {stats['comments_crawled']}"
    )


if __name__ == "__main__":
    main()
