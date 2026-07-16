#!/usr/bin/env python3
"""Generate EXCO presentation — PRN Negeri Sembilan 2026 + budget proposal."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "JITP_2026/Master_File/PRN_N9_EXCO_Presentation_20260612.pptx"

NAVY = RGBColor(0, 51, 102)
RED = RGBColor(200, 16, 46)
GREY = RGBColor(100, 116, 139)
WHITE = RGBColor(255, 255, 255)


def _blank(prs: Presentation):
    return prs.slides.add_slide(prs.slide_layouts[6])


def _title_slide(prs: Presentation):
    s = _blank(prs)
    box = s.shapes.add_textbox(Inches(0.6), Inches(1.8), Inches(8.8), Inches(1.2))
    tf = box.text_frame
    tf.text = "PRN Negeri Sembilan 2026"
    p = tf.paragraphs[0]
    p.font.size = Pt(44)
    p.font.bold = True
    p.font.color.rgb = NAVY
    p.alignment = PP_ALIGN.CENTER

    sub = s.shapes.add_textbox(Inches(0.6), Inches(3.0), Inches(8.8), Inches(0.8))
    st = sub.text_frame
    st.text = "Intelligence Dashboard & War Room — Briefing EXCO"
    st.paragraphs[0].font.size = Pt(26)
    st.paragraphs[0].font.color.rgb = RED
    st.paragraphs[0].alignment = PP_ALIGN.CENTER

    meta = s.shapes.add_textbox(Inches(0.6), Inches(4.2), Inches(8.8), Inches(1.2))
    mt = meta.text_frame
    mt.text = "InsightPulse Analytics Platform"
    p2 = mt.add_paragraph()
    p2.text = "12 Jun 2026 · Keputusan SPR · Dalaman EXCO"
    p2 = mt.add_paragraph()
    p2.text = "DUN 36 kerusi · Majoriti 19"
    for para in mt.paragraphs:
        para.font.size = Pt(16)
        para.font.color.rgb = GREY
        para.alignment = PP_ALIGN.CENTER


def _bullet_slide(prs: Presentation, title: str, bullets: list[tuple[str, int]]):
    s = _blank(prs)
    bar = s.shapes.add_shape(1, Inches(0), Inches(0), Inches(10), Inches(1.0))
    bar.fill.solid()
    bar.fill.fore_color.rgb = NAVY
    bar.line.fill.background()
    tb = s.shapes.add_textbox(Inches(0.5), Inches(0.15), Inches(9), Inches(0.7))
    tb.text_frame.text = title
    tb.text_frame.paragraphs[0].font.size = Pt(28)
    tb.text_frame.paragraphs[0].font.bold = True
    tb.text_frame.paragraphs[0].font.color.rgb = WHITE

    body = s.shapes.add_textbox(Inches(0.6), Inches(1.2), Inches(8.8), Inches(5.8))
    tf = body.text_frame
    tf.word_wrap = True
    for i, (text, level) in enumerate(bullets):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = text
        p.level = level
        p.font.size = Pt(20 if level == 0 else 17)
        p.font.color.rgb = NAVY if level == 0 else RGBColor(30, 41, 59)
        p.space_after = Pt(8)


def _content_slide(
    prs: Presentation,
    title: str,
    lines: list[tuple[str, int, bool]],
    slide_no: int | None = None,
):
    """Dense content slide: (text, level, monospace)."""
    s = _blank(prs)
    bar = s.shapes.add_shape(1, Inches(0), Inches(0), Inches(10), Inches(0.95))
    bar.fill.solid()
    bar.fill.fore_color.rgb = NAVY
    bar.line.fill.background()
    tb = s.shapes.add_textbox(Inches(0.5), Inches(0.12), Inches(9), Inches(0.65))
    tb.text_frame.text = title
    tb.text_frame.paragraphs[0].font.size = Pt(22)
    tb.text_frame.paragraphs[0].font.bold = True
    tb.text_frame.paragraphs[0].font.color.rgb = WHITE

    body = s.shapes.add_textbox(Inches(0.45), Inches(1.05), Inches(9.1), Inches(6.0))
    tf = body.text_frame
    tf.word_wrap = True
    for i, (text, level, mono) in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = text
        p.level = level
        if mono:
            p.font.name = "Courier New"
            p.font.size = Pt(11 if level > 0 else 12)
            p.font.color.rgb = RGBColor(15, 23, 42)
        else:
            p.font.size = Pt(18 if level == 0 else 14 if level == 1 else 12)
            p.font.color.rgb = NAVY if level == 0 else RGBColor(30, 41, 59)
        p.space_after = Pt(4 if mono else 6)

    if slide_no is not None:
        foot = s.shapes.add_textbox(Inches(8.2), Inches(7.05), Inches(1.5), Inches(0.35))
        foot.text_frame.text = f"Slide {slide_no}"
        foot.text_frame.paragraphs[0].font.size = Pt(10)
        foot.text_frame.paragraphs[0].font.color.rgb = GREY
        foot.text_frame.paragraphs[0].alignment = PP_ALIGN.RIGHT


def _table_slide(prs: Presentation, title: str, headers: list[str], rows: list[list[str]], col_widths=None):
    s = _blank(prs)
    bar = s.shapes.add_shape(1, Inches(0), Inches(0), Inches(10), Inches(0.9))
    bar.fill.solid()
    bar.fill.fore_color.rgb = NAVY
    bar.line.fill.background()
    tb = s.shapes.add_textbox(Inches(0.5), Inches(0.12), Inches(9), Inches(0.6))
    tb.text_frame.text = title
    tb.text_frame.paragraphs[0].font.size = Pt(24)
    tb.text_frame.paragraphs[0].font.bold = True
    tb.text_frame.paragraphs[0].font.color.rgb = WHITE

    nrows = len(rows) + 1
    ncols = len(headers)
    table = s.shapes.add_table(nrows, ncols, Inches(0.4), Inches(1.1), Inches(9.2), Inches(0.42 * nrows)).table

    if col_widths:
        for ci, w in enumerate(col_widths):
            table.columns[ci].width = Inches(w)

    for ci, h in enumerate(headers):
        cell = table.cell(0, ci)
        cell.text = h
        cell.fill.solid()
        cell.fill.fore_color.rgb = RGBColor(241, 245, 249)
        for para in cell.text_frame.paragraphs:
            para.font.bold = True
            para.font.size = Pt(11)

    for ri, row in enumerate(rows, start=1):
        for ci, val in enumerate(row):
            cell = table.cell(ri, ci)
            cell.text = val
            for para in cell.text_frame.paragraphs:
                para.font.size = Pt(10)


def build() -> Path:
    prs = Presentation()
    prs.slide_width = Inches(10)
    prs.slide_height = Inches(7.5)

    _title_slide(prs)

    _bullet_slide(prs, "Agenda Malam Ini", [
        ("Keputusan SPR & garis masa PRN NS", 0),
        ("Apa yang sudah siap — InsightPulse Dashboard", 0),
        ("Kerusi strategik & War Room Hari Ini", 0),
        ("Formulasi ML/DL — analitik, ramalan & insight (Slide 17–22)", 0),
        ("Operasi harian & automasi (cadangan)", 0),
        ("Pelan cloud hosting dashboard", 0),
        ("Cadangan belanjawan — teknologi + perkhidmatan pakar", 0),
        ("Langkah seterusnya & kelulusan", 0),
    ])

    _bullet_slide(prs, "Keputusan SPR — 12 Jun 2026", [
        ("PRN Negeri Sembilan (DISAHKAN)", 0),
        ("Penamaan calon: 18 Julai 2026 (36 hari)", 1),
        ("Undi awal: 28 Julai 2026", 1),
        ("Hari mengundi: 1 Ogos 2026 (50 hari)", 1),
        ("PRN Johor (rujuk): mengundi 11 Julai 2026", 0),
        ("Implikasi: ~5 minggu pre-penamaan + ~2 minggu kempen penuh", 0),
    ])

    _bullet_slide(prs, "Objektif — Intelligence untuk EXCO", [
        ("BUKAN polling — social listening & naratif masa nyata", 0),
        ("Pantau isu, sentimen & crisis sebelum ia viral", 0),
        ("Fokus 6 kerusi kritikal: Pertahan + Boleh Menang", 0),
        ("Arahan harian ke petugas via WhatsApp (War Room Lite)", 0),
        ("Sokong keputusan EXCO dengan data, bukan andaian", 0),
    ])

    _bullet_slide(prs, "Apa Sudah Siap (Proof of Concept)", [
        ("Dashboard PRN NS — 10 tab intel (kerusi, sentimen, scenario)", 0),
        ("Master data: 69,000+ posts (PAS-Break + PRN NS crawl)", 0),
        ("831 mention NS · sentiment ikut platform (FB/TikTok/X/News)", 0),
        ("36 kerusi — kategori Pertahan / Menang / Sukar / Bukan Fokus", 0),
        ("War Room Hari Ini — 6 tindakan + Copy WhatsApp", 0),
        ("Tarikh SPR, countdown & garis masa — auto-update", 0),
    ])

    _table_slide(
        prs,
        "Kerusi Strategik — Fokus Operasi",
        ["Kategori", "DUN", "Kawasan", "Tindakan"],
        [
            ["PERTAHAN", "N05", "Serting", "Jaga base FELDA · socmed harian"],
            ["PERTAHAN", "N25", "Paroi", "Bandar Seremban · kos hidup"],
            ["PERTAHAN", "N31", "Bagan Pinang", "PD · pelancongan/nelayan"],
            ["BOLEH MENANG", "N03", "Sungai Lui", "Majoriti 535 · swing"],
            ["BOLEH MENANG", "N09", "Lenggeng", "Majoriti 685 · bandar"],
            ["BOLEH MENANG", "N18", "Pilah", "Majoriti 1,079 · rebut"],
        ],
        col_widths=[1.4, 0.7, 1.5, 5.6],
    )

    _bullet_slide(prs, "10 Modul Kempen — Status Sistem", [
        ("✅ Data pengundi & isu tempatan (Excel SPR + profil DUN)", 0),
        ("✅ Sentimen socmed AI (master crawl + dashboard)", 0),
        ("✅ Segmentasi kerusi (Pertahan / Menang / Sukar)", 0),
        ("🟡 Draf kandungan & jadual post (semi-auto + WhatsApp)", 0),
        ("✅ Pantau isu & counter-narrative (trigger War Room)", 0),
        ("✅ Tugasan jentera (Hari Ini + template petugas)", 0),
        ("🟡 Cloud dashboard — perlu deploy (cadangan budget)", 0),
        ("⬜ Laporan prestasi mingguan — fasa 2", 0),
    ])

    _bullet_slide(prs, "Operasi Harian (Ringkas — 20 min/hari)", [
        ("STEP 1: Crawl berita BM + Cina + Tamil + ekonomi (script auto)", 0),
        ("STEP 2: Crawl socmed via InsightPulse (keyword siap by DUN)", 0),
        ("STEP 3: Regenerate dashboard + War Room Hari Ini", 0),
        ("STEP 4: Copy WhatsApp → Koordinator → group petugas DUN", 0),
        ("Cadangan: cron 2×/hari + dashboard cloud untuk EXCO akses 24/7", 0),
    ])

    _bullet_slide(prs, "Pelan Cloud — Dashboard untuk EXCO", [
        ("Masalah sekarang: fail HTML tempatan — sukar kongsi & update", 0),
        ("Cadangan: Static dashboard di cloud (AWS S3 / Azure / Vercel)", 0),
        ("URL khusus EXCO (contoh: prn-ns.insightpulse.my) — password", 0),
        ("Auto-regenerate 2×/hari selepas crawl", 0),
        ("Backend crawl kekal secure (bukan public)", 0),
        ("Kos: RM 300–800/bulan (hosting + domain + SSL)", 0),
    ])

    _table_slide(
        prs,
        "Cadangan Belanjawan — Teknologi (7 minggu: 12 Jun – 1 Ogo)",
        ["Item", "Fungsi", "Anggaran (RM)", "Nota"],
        [
            ["Apify Crawling API", "FB, TikTok, X, IG — socmed", "12,000 – 18,000", "Proxy included · 2×/hari kempen"],
            ["OpenAI / LLM API", "Briefing, draf counter-narrative", "2,500 – 4,000", "Human-in-the-loop"],
            ["SerpAPI / News API", "Backup berita premium", "800 – 1,500", "Optional — RSS percuma ada"],
            ["Cloud hosting", "Dashboard EXCO + storage", "2,100 – 2,500", "3 bulan × ~RM700/bulan"],
            ["Domain + SSL + CDN", "URL rasmi dashboard", "500 – 800", "One-time + renewal"],
            ["Setup & deploy cloud", "CI/CD, security, backup", "5,000 – 8,000", "One-time"],
            ["SUB-JUMLAH TEKNOLOGI", "", "23,000 – 35,000", ""],
        ],
        col_widths=[2.0, 2.8, 1.5, 2.9],
    )

    _table_slide(
        prs,
        "Cadangan Belanjawan — Perkhidmatan Pakar (Upah)",
        ["Peranan", "Skop", "Anggaran (RM)", "Tempoh"],
        [
            ["Ketua Analis / Consultant", "Dashboard, crawl, briefing EXCO, War Room", "28,000 – 35,000", "12 Jun – 1 Ogo"],
            ["Sokongan teknikal (part-time)", "Crawl, merge data, cloud maintenance", "8,000 – 12,000", "7 minggu"],
            ["Latihan petugas (1 hari)", "WhatsApp workflow + dashboard", "3,000 – 5,000", "One-time"],
            ["SUB-JUMLAH PERKHIDMATAN", "", "39,000 – 52,000", "Boleh invois formal"],
        ],
        col_widths=[2.2, 3.2, 1.5, 2.3],
    )

    _table_slide(
        prs,
        "Ringkasan — 2 Pakej untuk Kelulusan EXCO",
        ["Pakej", "Skop", "Jumlah (RM)", "Sesuai untuk"],
        [
            ["PAKEJ A — ASAS", "Crawl harian + dashboard cloud + War Room + briefing/minggu", "55,000 – 65,000", "Pre-penamaan"],
            ["PAKEJ B — OPTIMUM ★", "Pakej A + crawl 2×/hari + LLM + latihan + sokongan kempen", "85,000 – 95,000", "EXCO full intel"],
            ["Contingency (10%)", "Crisis spike / crawl extra", "+ 8,000", "Optional"],
            ["JUMLAH CADANGAN", "Pakej B + contingency", "≈ RM 93,000 – 103,000", "7 minggu operasi"],
        ],
        col_widths=[1.8, 3.8, 1.5, 2.1],
    )

    _bullet_slide(prs, "Nilai kepada EXCO — ROI", [
        ("1 crisis elak sebelum viral: nilai reputasi >> RM 100,000", 0),
        ("Fokus sumber 6 kerusi vs tabur 36 — efisiensi kempen", 0),
        ("Keputusan berasaskan data (sentimen, isu, scenario S1–S5)", 0),
        ("Arahan petugas terstruktur — kurang silap komunikasi", 0),
        ("Dashboard cloud — EXCO & war room akses sama masa", 0),
    ])

    _content_slide(prs, "Formula Keputusan Analitik — Dari Data ke Arahan EXCO", [
        ("Pipeline 5 Lapisan InsightPulse", 0, False),
        ("[1] CRAWL  →  Apify + RSS (FB, TikTok, X, IG, Berita BM/Cina/Tamil)", 1, True),
        ("[2] NLP/DL →  BERT/RoBERTa: Sentimen + Emosi (per post)", 1, True),
        ("[3] CONTEXT → Override naratif politik (regex + domain rules)", 1, True),
        ("[4] AGREGASI → Skor kerusi, % negatif, engagement, isu trending", 1, True),
        ("[5] KEPUTUSAN → Ramalan kerusi + Scenario S1–S5 + War Room Hari Ini", 1, True),
        ("Formula agregat sentimen (per DUN):", 0, False),
        ("Negatif% = (post negatif / jumlah mention DUN) × 100", 1, True),
        ("Positive% = (positif / total) × 100   |   Neutral% = (neutral / total) × 100", 1, True),
        ("NOTA EXCO: BUKAN polling undi — early warning naratif + prioriti 6 kerusi kritikal", 0, False),
    ], slide_no=17)

    _content_slide(prs, "Formulasi Deep Learning — Sentimen & Emosi Multibahasa", [
        ("Model DL (auto-route ikut bahasa):", 0, False),
        ("Melayu → rmtariq/ft-Malay-bert (BERT)  |  English → twitter-roberta-sentiment", 1, True),
        ("Cina → roberta-chinanews-chinese  |  Fallback → bert-multilingual-sentiment", 1, True),
        ("Emosi → multilingual-emotion-classifier (XLM-RoBERTa, 8 kelas, Σ=1.0)", 1, True),
        ("Arkitektur: Input x → Tokenizer → BERT/RoBERTa → Softmax → P(kelas)", 0, True),
        ("P(y=c|x) = exp(z_c) / Σⱼ exp(z_j)   |   label = argmax(P)   |   confidence = P(label)", 1, True),
        ("Routing: detect_language(x) → Model[lang](truncate(x, max=384 tokens))", 0, True),
        ("Emosi_dominan = argmax(e)   |   Keyakinan = max(e)   |   Multi-emosi jika selisih < 0.15", 1, True),
    ], slide_no=18)

    _content_slide(prs, "Formulasi ML — Skor Hibrid, Context Layer & Engagement", [
        ("1. Label + keyakinan (output DL):", 0, False),
        ("label = argmax(P+)   |   confidence = P(label)", 1, True),
        ("2. Skor numerik hibrid (0.0 – 1.0):", 0, False),
        ("POSITIF:  score = 0.7 + (confidence × 0.3)   → 0.70 – 1.00", 1, True),
        ("NEGATIF:  score = 0.3 − (confidence × 0.3)   → 0.00 – 0.30", 1, True),
        ("NEUTRAL:  score = 0.5 (tetap)", 1, True),
        ("3. Political Context Layer: regex {desak ganti, pengkhianat…} → override NEGATIF", 0, True),
        ("Impak: ketepatan 70% → 85% (+15%) · F1 Negative 0.56 → 0.73", 1, False),
        ("4. Engagement: total = likes + shares + comments + (views ÷ 100)", 0, True),
        ("5. AvgSentiment = (1/N) × Σ sentiment_score(post_i)", 1, True),
    ], slide_no=19)

    _content_slide(prs, "Formulasi Prediction — Kerusi DUN & Scenario Engine", [
        ("Kategori margin: Ultra ≤199 | Super 200–499 | Marginal 500–999 | Semi 1K–3K | Selamat ≥3K", 0, True),
        ("Base pasWinProb (PAS pencabar): Ultra 52% | Super 48% | Marginal 44% | Semi 38% | Safe 28%", 0, True),
        ("Defend (kerusi PAS): pas_prob = lookup(margin) + 6%  (max 88%)", 1, True),
        ("Winnable: pas_prob = max(base, min(58, 46 + (1000 − majoriti)/25))", 1, True),
        ("Floor: N03 ≥ 51% · N09 ≥ 50.5%  |  Clamp: pas_prob ∈ [8%, 92%]", 1, True),
        ("Senario: Solo = pas_prob−10  |  +PN = pas_prob+5  |  +MN = pas_prob+8", 0, True),
        ("Scenario Engine: S1 PN 35% | S2 Solo 20% | S3 PAS-UMNO 15% | S4 Clash 20% | S5 Fragment 10%", 0, True),
        ("Swing target: TargetSwing = max(200, ⌊majoriti÷2⌋ + 200)", 1, True),
    ], slide_no=20)

    _content_slide(prs, "Formula Insight & Keputusan War Room — Hari Ini", [
        ("Alert sentimen per DUN:", 0, False),
        ("neg_pct = (post negatif / mention DUN) × 100", 1, True),
        ("neg_pct ≥ 25% → KRITIKAL  |  ≥ 15% → AMARAN  |  mention≥10 & ≥10% → PANTAU", 1, True),
        ("Trigger automatik:", 0, False),
        ("defend + neg_pct>20% → jaga base FELDA + socmed harian", 1, True),
        ("winnable + majoriti≤500 → door-to-door + 2 ceramah/minggu", 1, True),
        ("threeCornerRisk=Tinggi → elak pecah undi, selaraskan mesej", 1, True),
        ("TopIssues = sort(TermScore, desc)[:8]  |  Briefing = f(neg%, isu, pasWinProb, scenario)", 0, True),
        ("Contoh: \"N25 Paroi: 18% negatif · kos hidup · PAS prob 64% · S1 aktif\"", 1, False),
    ], slide_no=21)

    _content_slide(prs, "Jaminan Metodologi & Had Model", [
        ("Ketepatan model (validated):", 0, False),
        ("Sentimen politik: 70% → 85%  |  F1 Negative: 0.56 → 0.73  |  Emosi: 83%", 1, True),
        ("Had yang perlu diterangkan ke EXCO:", 0, False),
        ("• Bukan polling undi — tiada sampel pengundi representatif", 1, False),
        ("• DL silap pada sarkasme → mitigasi: context layer + semakan manusia", 1, False),
        ("• Ramalan kerusi = rule-based + PRN 2023, bukan Monte Carlo survey", 1, False),
        ("Prinsip operasi:", 0, False),
        ("Data → DL/ML → Rules → Human Review → Arahan Lapangan", 1, True),
        ("Auto crawl 2×/hari  →  Dashboard cloud  →  WhatsApp petugas DUN", 1, True),
    ], slide_no=22)

    _bullet_slide(prs, "Langkah Seterusnya — Mohon Kelulusan", [
        ("1. Kelulusan prinsip belanjawan Pakej B (~RM 90k)", 0),
        ("2. Deploy dashboard cloud dalam 48 jam (URL EXCO)", 0),
        ("3. Top-up Apify + cloud subscription", 0),
        ("4. Briefing petugas — template WhatsApp (1 sesi)", 0),
        ("5. Crawl intensif bermula 18 Jul (penamaan)", 0),
        ("6. Laporan EXCO mingguan setiap Isnin pagi", 0),
    ])

    s = _blank(prs)
    box = s.shapes.add_textbox(Inches(1), Inches(2.5), Inches(8), Inches(2))
    tf = box.text_frame
    tf.text = "Terima Kasih"
    tf.paragraphs[0].font.size = Pt(48)
    tf.paragraphs[0].font.bold = True
    tf.paragraphs[0].font.color.rgb = NAVY
    tf.paragraphs[0].alignment = PP_ALIGN.CENTER
    p = tf.add_paragraph()
    p.text = "Soal Jawab"
    p.font.size = Pt(32)
    p.font.color.rgb = RED
    p.alignment = PP_ALIGN.CENTER
    p2 = tf.add_paragraph()
    p2.text = "InsightPulse · PRN Negeri Sembilan 2026"
    p2.font.size = Pt(18)
    p2.font.color.rgb = GREY
    p2.alignment = PP_ALIGN.CENTER

    OUT.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(OUT))
    return OUT


if __name__ == "__main__":
    path = build()
    size_kb = path.stat().st_size // 1024
    print(f"✅ Presentation saved: {path}")
    print(f"   Slides: {len(Presentation(str(path)).slides)} · Size: {size_kb} KB")
    print(f"   Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
