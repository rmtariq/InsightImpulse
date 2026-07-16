#!/usr/bin/env python3
"""
Panduan operasi N9 LENGKAP — copywriting socmed + prompt AI infografik/banner/video.
Satu DOCX mudah difahami · siap paste ke FB/X/IG/TikTok/Canva/ChatGPT/Midjourney.

Output:
  data/projects/political/PRN/reports/naratif_cina_india/N9_Operasi_Naratif_Tindakan.docx
  data/projects/political/PRN/reports/naratif_cina_india/N9_Operasi_Naratif_Tindakan.json
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data/projects/political/PRN/reports/naratif_cina_india"
OUT_DOCX = OUT_DIR / "N9_Operasi_Naratif_Tindakan.docx"
OUT_JSON = OUT_DIR / "N9_Operasi_Naratif_Tindakan.json"
MYT = timezone(timedelta(hours=8))

if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from naratif_action_plan_builder import (  # noqa: E402
    N9_CHINESE_MIXED,
    N9_CHINESE_URBAN,
    N9_INDIAN_BELT,
    _build_dun_matrix,
)

N9_TARGET_20 = {
    "N02", "N03", "N05", "N06", "N07", "N08", "N09", "N10", "N13", "N14",
    "N15", "N16", "N17", "N19", "N20", "N25", "N27", "N28", "N31", "N35",
}


def _strip_prefix(text: str) -> str:
    return re.sub(r"^\[N\d+\s+[^\]]+\]\s*", "", str(text or "")).strip()


def _ground_fokus(code: str) -> str:
    if code in N9_CHINESE_URBAN:
        return "Bandar Cina — counter dakwah DAP"
    if code in N9_CHINESE_MIXED:
        return "Campuran — peniaga + data exco"
    return "Melayu majoriti — ground utama"


def _channels(code: str, comm: str) -> str:
    if comm == "chinese":
        if code in N9_CHINESE_URBAN:
            return "FB Live · WA · TikTok 中文 · IG carousel"
        if code in N9_CHINESE_MIXED:
            return "FB · WA merchant · poster A3"
        return "WA ringkas · minimum"
    if code in N9_INDIAN_BELT:
        return "Kuil · WA ibu bapa · TikTok Tamil"
    return "Kuil/masjid · WA komuniti"


def _load_intel() -> Dict[str, Any]:
    p = OUT_DIR / "naratif_cina_india_johor_n9_analytics.json"
    if not p.exists():
        return {}
    data = json.loads(p.read_text(encoding="utf-8"))
    return {
        "n9": data.get("states", {}).get("N9", {}),
        "targets": {r["code"]: r for r in data.get("n9_target_duns", [])},
    }


def _socmed_pack_chinese() -> Dict[str, Any]:
    return {
        "x_thread": {
            "label": "X (Twitter) — Thread 3 tweet · Komuniti Cina",
            "tweets": [
                {
                    "tweet": 1,
                    "bm": "PRN N9: Isu sebenar pengundi Cina = kos hidup, SME, trafik Seremban/Nilai — bukan drama politik.",
                    "zh": "森州州选：华人选民真正关心生活成本、中小企业、芙蓉/汝来交通——不是政治口水战。",
                    "hashtags": "#PRNN9 #森美兰 #NegeriSembilan",
                },
                {
                    "tweet": 2,
                    "bm": "Dakwah 'gelombang hijau' untuk takutkan komuniti? Tanya DATA: bantuan peniaga kecil negeri masih aktif. Fakta > rumor WhatsApp.",
                    "zh": "用“绿色浪潮”吓唬华人？请用数据说话：州政府中小企业援助仍在进行。事实胜过谣言。",
                    "hashtags": "#事实 #中小企业",
                },
                {
                    "tweet": 3,
                    "bm": "Stabiliti N9 = perniagaan boleh merancang. Helaian bantuan BM+中文 — PM untuk salinan. Undi = perkhidmatan.",
                    "zh": "森州稳定，商家才能安心规划。中英援助清单——私信索取。投票要看服务。",
                    "hashtags": "#芙蓉 #汝来 #稳定",
                },
            ],
        },
        "facebook": [
            {
                "title": "POST 1 — Kos hidup & SME (utama)",
                "bm": (
                    "🏪 Kepada peniaga & komuniti Cina Negeri Sembilan\n\n"
                    "Kami dengar: kos sara hidup naik, trafik Seremban sesak, kilang Nilai bimbang kos operasi.\n\n"
                    "✅ Helaian bantuan SME & kos hidup (BM+中文) — disahkan exco negeri\n"
                    "✅ Tiada pakatan sulit — fokus kestabilan & perkhidmatan\n"
                    "✅ 'Gelombang hijau'? Itu dakwah politik. Kita jawab dengan FAKTA.\n\n"
                    "📩 PM 'BANTUAN' untuk salinan · Kongsi ke group merchant anda\n"
                    "#PRNN9 #森美兰 #芙蓉 #汝来 #中小企业"
                ),
                "zh": (
                    "🏪 致森美兰华商与华人社区\n\n"
                    "我们听到：生活成本上涨、芙蓉交通拥挤、汝来工厂担心营运成本。\n\n"
                    "✅ 中小企业及生活援助清单（中英对照）——州政府核实\n"
                    "✅ 没有秘密协议——专注稳定与服务\n"
                    "✅ “绿色浪潮”？那是政治宣传。我们用事实回应。\n\n"
                    "📩 私信「BANTUAN」索取 · 请转发到商家群"
                ),
                "cta": "PM 'BANTUAN' · Share group merchant Seremban/Nilai",
                "bila": "Isnin atau Selasa, 8:00–9:00 malam",
            },
            {
                "title": "POST 2 — Counter dakwah DAP",
                "bm": (
                    "❓ Soalan ramai: 'PAS ekstrem? Ada rasuah?'\n\n"
                    "Jawapan kami:\n"
                    "1️⃣ Kempen N9 fokus PERKHIDMATAN — bukan teologi\n"
                    "2️⃣ Tuduhan tanpa bukti = politik takut. Semak China Press / media berita\n"
                    "3️⃣ Bandingkan: apa negeri buat untuk peniaga & sekolah — bukan apa group WhatsApp kata\n\n"
                    "Stabiliti negeri > drama politik\n"
                    "#PRNN9 #事实 #稳定"
                ),
                "zh": (
                    "❓ 常见问题：「伊党极端？有贪污？」\n\n"
                    "我们的回答：\n"
                    "1️⃣ 森州选专注服务——不是宗教辩论\n"
                    "2️⃣ 没有证据的指控=恐吓政治。请查阅中国报等正规媒体\n"
                    "3️⃣ 比较：州政府为商家和学校做了什么——不是WhatsApp群说什么\n\n"
                    "州选稳定 > 政治口水"
                ),
                "cta": "Komen dengan soalan perkhidmatan — kami jawab fakta",
                "bila": "Rabu, 12:30 tengah hari",
            },
            {
                "title": "POST 3 — Trafik & perkhidmatan bandar",
                "bm": (
                    "🚗 Kesesakan Seremban & parking — isu berulang setiap PRN.\n\n"
                    "Pasukan negeri sedang susun:\n"
                    "· Mesyuarat MBSA + persatuan peniaga\n"
                    "· Kemas kini projek jalan & PBT\n\n"
                    "Kami tak janji magic — kami janji DENGAR & URUS dengan nombor rujukan.\n"
                    "#Seremban #交通 #芙蓉"
                ),
                "zh": "🚗 芙蓉塞车与停车问题——每次州选都出现。\n州团队正安排与市议会及商家开会。我们承诺听取与跟进，不是空口承诺。",
                "cta": "Tag kawan peniaga Seremban",
                "bila": "Jumaat petang",
            },
        ],
        "instagram_carousel": {
            "label": "Instagram — Carousel 5 slide (copy per slide)",
            "slides": [
                {"no": 1, "headline_bm": "PRN N9 · Apa isu sebenar?", "headline_zh": "森州选 · 真正议题？", "body": "Kos hidup · SME · Trafik — bukan rumor"},
                {"no": 2, "headline_bm": "Dakwah takut vs Fakta", "headline_zh": "恐吓宣传 vs 事实", "body": "'Gelombang hijau' = politik. Kita jawab data."},
                {"no": 3, "headline_bm": "3 Bantuan Disahkan", "headline_zh": "三项核实援助", "body": "1.SME 2.Kos hidup 3.PBT/trafik"},
                {"no": 4, "headline_bm": "Tiada pakatan sulit", "headline_zh": "没有秘密协议", "body": "Kestabilan negeri · elak pecah undi"},
                {"no": 5, "headline_bm": "PM 'BANTUAN' untuk helaian", "headline_zh": "私信索取清单", "body": "Undi = perkhidmatan · #PRNN9"},
            ],
        },
        "tiktok_30s": {
            "label": "TikTok / Reels — Script 30 saat",
            "hook": "0-3s: Teks overlay besar 'Dakwah takut atau fakta?' / '恐吓还是事实？'",
            "scene_1": "3-10s: Shot pasar Seremban / kilang Nilai. VO BM: 'Peniaga N9 tanya kos hidup.'",
            "scene_2": "10-20s: Infografik overlay 3 bullet bantuan SME. Subtitle 中文.",
            "scene_3": "20-27s: VO: 'Stabiliti = perniagaan boleh merancang. Bukan rumor WhatsApp.'",
            "cta": "27-30s: 'PM BANTUAN · Follow untuk fakta' + logo MN",
            "music": "Neutral upbeat · tiada lagu agama",
            "hashtags": "#PRNN9 #森州 #芙蓉 #factcheck #中小企业",
        },
        "tiktok_60s": {
            "label": "TikTok — Script 60s (counter DAP extended)",
            "script_bm": (
                "[0-10s] Hook: 'Kenapa DAP nak takutkan anda dengan gelombang hijau?'\n"
                "[10-25s] Isu sebenar: kos hidup Seremban, SME Nilai, parking bandar.\n"
                "[25-40s] 3 fakta exco: bantuan peniaga · projek PBT · helaian disahkan.\n"
                "[40-55s] 'PAS fokus perkhidmatan N9 — bukan debat syurga dalam kempen.'\n"
                "[55-60s] CTA: Simpan & kongsi ke group merchant."
            ),
            "script_zh": (
                "[0-10s] 为什么行动党要用绿色浪潮吓唬你？\n"
                "[10-25s] 真正问题：芙蓉生活成本、汝来中小企业。\n"
                "[25-40s] 三项州政府事实。\n"
                "[40-55s] 专注森州服务——不是宗教辩论。\n"
                "[55-60s] 收藏并转发到商家群。"
            ),
        },
        "whatsapp": {
            "label": "WhatsApp — Forward template",
            "text": (
                "📋 *PRN N9 — Helaian Bantuan SME & Kos Hidup (BM+中文)*\n\n"
                "Kepada rakan peniaga/komuniti Cina:\n"
                "✅ Senarai bantuan negeri *disahkan*\n"
                "✅ Fokus perkhidmatan — bukan drama politik\n"
                "✅ Soalan? Balas mesej ini\n\n"
                "Jangan kongsi rumor tanpa semak — tanya data.\n"
                "_PAS · PN · MN — Negeri Sembilan_"
            ),
        },
        "youtube_podcast": {
            "label": "YouTube / FB Live / Podcast — 15 min outline",
            "tajuk": "PRN N9: Fakta untuk Komuniti Cina — Bukan Dakwah Takut",
            "segments": [
                "0-2 min: Pembuka — 'Apa isu sebenar pengundi Cina N9?'",
                "2-6 min: Kos hidup & SME Seremban/Nilai — data exco",
                "6-10 min: Counter 'gelombang hijau' & tuduhan tanpa bukti",
                "10-13 min: Q&A live — jawab fakta sahaja",
                "13-15 min: CTA helaian bantuan + undi = perkhidmatan",
            ],
            "intro_script_bm": (
                "Selamat datang. Hari ini kita bincang PRN Negeri Sembilan untuk komuniti Cina — "
                "bukan ceramah panjang, tapi fakta: kos hidup, perniagaan kecil, perkhidmatan bandar. "
                "Kalau ada tuduhan 'gelombang hijau' — kita jawab dengan data, bukan emosi."
            ),
            "intro_script_zh": "欢迎。今天讨论森州选华人关心的实际问题：生活成本、中小企业、市区服务。用事实回应，不用情绪。",
        },
    }


def _socmed_pack_indian() -> Dict[str, Any]:
    return {
        "x_thread": {
            "label": "X — Thread 3 tweet · Komuniti India",
            "tweets": [
                {
                    "tweet": 1,
                    "bm": "PRN N9: Komuniti India fokus SJKT, pekerjaan & hospital — bukan teologi politik.",
                    "ta": "என்.செம்பிலான் தேர்தல்: SJKT, வேலை, மருத்துவம் — மத அரசியல் அல்ல.",
                    "hashtags": "#PRNN9 #SJKT #NegeriSembilan",
                },
                {
                    "tweet": 2,
                    "bm": "DAP guna ketakutan PAS untuk alih perhatian. Tanya: berapa guru SJKT? Status hospital Port Dickson? Fakta MITRA/pekerjaan.",
                    "ta": "பயமுறுத்தல் அல்ல — உறுதிப்படுத்தப்பட்ட தகவல்கள் மட்டும்.",
                    "hashtags": "#SJKT #PortDickson",
                },
                {
                    "tweet": 3,
                    "bm": "Nota BM+Tamil di kuil & group ibu bapa. Hotline khidmat negeri. #PRNN9",
                    "ta": "கோவில் & பெற்றோர் குழு — BM+தமிழ் விவரம்.",
                    "hashtags": "#Tamil #N9",
                },
            ],
        },
        "facebook": [
            {
                "title": "POST 1 — SJKT & pendidikan Tamil",
                "bm": (
                    "📚 Komuniti India N9 — SJKT kekal keutamaan\n\n"
                    "Isu guru, kemudahan & masa depan anak — ini isu sebenar, bukan politik agama.\n\n"
                    "✅ Kemas kini status pengisian guru (BM+Tamil)\n"
                    "✅ Group ibu bapa Port Dickson / Seremban / Paroi\n"
                    "✅ Fakta KPM — bukan rumor WhatsApp\n\n"
                    "#SJKT #PRNN9 #PortDickson"
                ),
                "ta": (
                    "📚 SJKT — எங்கள் கவனம்\n\n"
                    "ஆசிரியர் பற்றாக்குறை & கல்வி — உண்மையான பிரச்சினை.\n"
                    "BM+தமிழ் புதுப்பிப்பு விரைவில்."
                ),
                "cta": "Share group ibu bapa SJKT",
                "bila": "Selasa malam",
            },
            {
                "title": "POST 2 — Pekerjaan & kilang",
                "bm": (
                    "🏭 Pekerjaan komuniti India N9\n\n"
                    "Kilang, MITRA, kemahiran — nota BM+Tamil untuk pekerja & keluarga.\n"
                    "Sesi 15 min di kuil — bukan ceramah panjang, fakta sahaja.\n\n"
                    "#pekerjaan #N9 #MITRA"
                ),
                "ta": "🏭 வேலைவாய்ப்பு & திறன் — BM+தமிழ் குறிப்பு.",
                "cta": "Hubungi ketua kuil setempat",
                "bila": "Khamis",
            },
            {
                "title": "POST 3 — Hospital & kesihatan",
                "bm": (
                    "🏥 Kesihatan Port Dickson / Seremban\n\n"
                    "Aduan masa menunggu & kemudahan — kami rakam & susun jawapan fakta exco.\n"
                    "Elak politik agama — fokus perkhidmatan.\n"
                    "#hospital #N9"
                ),
                "ta": "🏥 மருத்துவம் — உறுதிப்படுத்தப்பட்ட பதில் விரைவில்.",
                "cta": "PM aduan dengan lokasi",
                "bila": "Sabtu pagi",
            },
        ],
        "instagram_carousel": {
            "label": "Instagram — Carousel 5 slide · India",
            "slides": [
                {"no": 1, "headline_bm": "SJKT · Masa depan anak", "headline_ta": "SJKT · எதிர்காலம்", "body": "Guru · kemudahan · fakta KPM"},
                {"no": 2, "headline_bm": "Pekerjaan & MITRA", "headline_ta": "வேலைவாய்ப்பு", "body": "Kilang · kemahiran · nota BM+Tamil"},
                {"no": 3, "headline_bm": "Hospital & kesihatan", "headline_ta": "சுகாதாரம்", "body": "Port Dickson · Seremban"},
                {"no": 4, "headline_bm": "Bukan politik agama", "headline_ta": "மத அரசியல் அல்ல", "body": "Perkhidmatan · bukan dakwah takut"},
                {"no": 5, "headline_bm": "Hotline khidmat N9", "headline_ta": "சேவை எண்", "body": "PM · kuil notice · #PRNN9"},
            ],
        },
        "tiktok_30s": {
            "label": "TikTok — Script 30s · India",
            "hook": "0-3s: 'SJKT & pekerjaan — fakta N9' (Tamil+BM subtitle)",
            "scene_1": "3-12s: B-roll kelas SJKT / kilang",
            "scene_2": "12-22s: 3 bullet: guru · MITRA · hospital",
            "scene_3": "22-27s: VO Tamil: perkhidmatan, bukan politik agama",
            "cta": "27-30s: Simpan · Share group ibu bapa",
            "hashtags": "#SJKT #PRNN9 #Tamil #NegeriSembilan",
        },
        "whatsapp": {
            "label": "WhatsApp — Forward · India",
            "text": (
                "📋 *PRN N9 — Nota SJKT & Pekerjaan (BM+Tamil)*\n\n"
                "✅ Status guru SJKT — fakta disahkan\n"
                "✅ Maklumat MITRA / pekerjaan\n"
                "✅ Hotline khidmat negeri\n\n"
                "Kongsi ke group ibu bapa & kuil.\n"
                "_PAS · PN · MN — Negeri Sembilan_"
            ),
        },
        "youtube_podcast": {
            "label": "Podcast / Live — 15 min · India",
            "tajuk": "PRN N9: SJKT, Pekerjaan & Kesihatan — Komuniti India",
            "segments": [
                "0-2 min: Pembuka Tamil+BM",
                "2-6 min: SJKT — data guru & kemudahan",
                "6-10 min: Pekerjaan MITRA & kilang",
                "10-13 min: Hospital Port Dickson — aduan & jawapan",
                "13-15 min: CTA hotline · elak politik agama",
            ],
            "intro_script_bm": "Sesi ini untuk komuniti India N9: SJKT, pekerjaan, hospital — fakta exco negeri, bukan spekulasi.",
            "intro_script_ta": "SJKT, வேலை, மருத்துவம் — உறுதிப்படுத்தப்பட்ட தகவல்கள் மட்டும்.",
        },
    }


def _ai_prompts() -> Dict[str, Any]:
    return {
        "cara_guna": (
            "Copy prompt di bawah → paste ke ChatGPT / Claude / Canva AI / Midjourney / DALL-E / Leonardo / Ideogram. "
            "Tukar [NAMA CALON] dan [NOMBOR WHATSAPP] sebelum publish."
        ),
        "infografik": [
            {
                "nama": "INFOGRAFIK 1 — Kos hidup & SME (Cina)",
                "tool": "Canva AI / ChatGPT / Midjourney",
                "aspect": "1080×1350 (IG/FB portrait)",
                "prompt": (
                    "Create a clean modern political infographic in Malay and Chinese for Negeri Sembilan state election. "
                    "Title: 'PRN N9 — Fakta Bantuan SME & Kos Hidup'. "
                    "Three bullet points with icons: (1) Small business aid list verified by state government "
                    "(2) Cost of living support programs (3) Traffic & municipal services Seremban/Nilai. "
                    "Footer: 'Stabiliti Negeri Sembilan · Fakta Bukan Rumor'. "
                    "Color scheme: navy blue and green, professional, no religious symbols, no aggressive imagery. "
                    "Include small text: PAS PN MN coalition. Flat vector style, high readability, bilingual BM+中文."
                ),
                "teks_overlay": "Tajuk BM: BANTUAN SME & KOS HIDUP N9\nTajuk 中文: 森州中小企业与生活成本援助\nFooter: Fakta disahkan exco negeri",
            },
            {
                "nama": "INFOGRAFIK 2 — Counter dakwah DAP (Cina)",
                "tool": "ChatGPT / Ideogram",
                "aspect": "1080×1080 (square FB)",
                "prompt": (
                    "Infographic comparing 'Fear propaganda' vs 'Verified facts' for Malaysian Chinese voters in Negeri Sembilan. "
                    "Left column red X: 'Gelombang hijau scare tactics, unverified WhatsApp rumors'. "
                    "Right column green check: 'State aid data, China Press fact-check, service delivery'. "
                    "Bilingual Malay and Chinese. Minimalist, trustworthy news-style design. No party logos except small footer MN. "
                    "Professional government communication aesthetic."
                ),
                "teks_overlay": "Kiri: Dakwah Takut\nKanan: Fakta Disahkan\nCTA: PM 'BANTUAN' untuk helaian",
            },
            {
                "nama": "INFOGRAFIK 3 — SJKT (India)",
                "tool": "Canva AI / Leonardo",
                "aspect": "1080×1350",
                "prompt": (
                    "Tamil education infographic for Negeri Sembilan PRN. Title in BM and Tamil: 'SJKT — Guru & Masa Depan Anak'. "
                    "Three sections: teacher placement status, school facilities, state education allocation. "
                    "Icons: school, teacher, book. Colors: purple and gold accents on white, dignified. "
                    "No religious political imagery. Include footer: verified facts from state exco. "
                    "Trilingual labels BM + Tamil + small English."
                ),
                "teks_overlay": "BM: STATUS SJKT N9\nTamil: SJKT நிலைப்பாடு\n3 fakta dengan nombor",
            },
            {
                "nama": "INFOGRAFIK 4 — Pekerjaan India",
                "tool": "ChatGPT / Canva",
                "aspect": "1080×1080",
                "prompt": (
                    "Employment infographic for Indian Malaysian community in Negeri Sembilan. "
                    "Headlines BM and Tamil. Show: MITRA programs, factory zones Nilai/Seremban, skills training. "
                    "Professional corporate style, blue tones, factory and temple subtle background (not dominant). "
                    "CTA: Hotline khidmat negeri. No communal conflict imagery."
                ),
                "teks_overlay": "PEKERJAAN & MITRA N9\nவேலைவாய்ப்பு · BM+Tamil",
            },
            {
                "nama": "INFOGRAFIK 5 — 3 Fakta 1 Muka (Universal)",
                "tool": "Mana-mana AI image tool",
                "aspect": "1080×1920 (TikTok/Story)",
                "prompt": (
                    "Vertical story infographic, Negeri Sembilan Malaysia state election. "
                    "Big number '3 FAKTA' at top. Three horizontal cards: Card1 Cost of living aid, "
                    "Card2 SJKT education, Card3 Jobs & health. Bilingual BM+中文+Tamil small text. "
                    "Modern gradient navy to teal. Swipe up CTA 'PM BANTUAN'. Clean sans-serif font."
                ),
                "teks_overlay": "Slide story IG/TikTok — 3 fakta exco negeri",
            },
        ],
        "banner_poster": [
            {
                "nama": "BANNER A3 — Pasar / ceramah bandar",
                "tool": "Midjourney / DALL-E / Canva",
                "aspect": "A3 portrait 297×420mm or 2480×3508px",
                "prompt": (
                    "Election banner design Negeri Sembilan Malaysia. Large headline Malay: 'N9 STABIL · BANTUAN SME · FAKTA BUKAN RUMOR'. "
                    "Chinese subtitle: '森州稳定 · 中小企业 · 事实为准'. "
                    "Subhead: Kos hidup · Perkhidmatan · Kestabilan negeri. "
                    "Photo style: Seremban market street blurred background. "
                    "Colors navy blue white green. Professional not aggressive. "
                    "Small footer: PAS PN MN. QR code placeholder bottom right. Print-ready 300dpi style."
                ),
            },
            {
                "nama": "BANNER — Kuil / komuniti India",
                "tool": "Canva AI",
                "aspect": "A3 landscape",
                "prompt": (
                    "Community notice banner for Tamil Malaysian voters Negeri Sembilan. "
                    "Headline BM: 'SJKT · PEKERJAAN · KESIHATAN'. Tamil: 'கல்வி · வேலை · சுகாதாரம்'. "
                    "Calm dignified design, temple architecture subtle watermark. "
                    "Contact hotline placeholder. Purple gold white palette. Service-focused not religious political."
                ),
            },
            {
                "nama": "POSTER WhatsApp — Helaian digital",
                "tool": "ChatGPT / Ideogram",
                "aspect": "1080×1920",
                "prompt": (
                    "Mobile-first poster for WhatsApp sharing. Title 'HELAIAN BANTUAN PRN N9'. "
                    "Checklist icon style 5 items: SME aid, cost of living, traffic, SJKT, hospital. "
                    "Big CTA button graphic 'PM BANTUAN'. BM and Chinese text. Clean flat design."
                ),
            },
        ],
        "video_ai": [
            {
                "nama": "VIDEO — CapCut AI / Runway · Pasar Seremban",
                "tool": "CapCut AI / Runway Gen-3 / Kling",
                "prompt": (
                    "30 second vertical video. Opening: busy morning Seremban market Malaysia, Chinese Malaysian shopkeepers. "
                    "Text overlay BM: 'Kos hidup memang isu sebenar'. Cut to infographic animation 3 aid bullets. "
                    "Chinese subtitles throughout. Closing text: 'Stabiliti N9 = perniagaan boleh merancang'. "
                    "Tone calm factual. No political attack faces. Upbeat neutral music."
                ),
            },
            {
                "nama": "VIDEO — SJKT B-roll · India",
                "tool": "CapCut / Pika",
                "prompt": (
                    "25 second video Tamil school classroom Malaysia, diverse Indian Malaysian students and teachers. "
                    "Tamil+BM subtitles: SJKT, pekerjaan, kesihatan. Warm lighting, documentary style. "
                    "End card: Hotline khidmat negeri. Respectful dignified tone."
                ),
            },
            {
                "nama": "VIDEO — Infografik animasi (motion graphic)",
                "tool": "ChatGPT (script) + Canva Video / After Effects",
                "prompt": (
                    "Motion graphic script: 40s animated infographic. Scene1 question mark 'Dakwah takut?'. "
                    "Scene2 split screen rumor vs fact. Scene3 three verified statistics animate in. "
                    "Scene4 map Negeri Sembilan highlight Seremban Nilai Port Dickson. "
                    "Voiceover BM with 中文 subtitles. Corporate blue green palette."
                ),
            },
        ],
    }


def _counter_qa() -> List[Dict[str, str]]:
    return [
        {
            "soalan": "PAS ekstrem? Takut hudud/syurga?",
            "jawapan_bm": "Kempen N9 fokus perkhidmatan & kestabilan — kos hidup, SME, SJKT. Bukan debat teologi. Tuduhan tanpa bukti = politik takut.",
            "jawapan_zh": "森州选专注服务与稳定——生活成本、中小企业、教育。不是宗教辩论。没有证据的指控是恐吓政治。",
            "jawapan_ta": "சேவை & நிலைத்தன்மை மட்டும் — மத விவாதம் அல்ல.",
            "saluran": "FB comment · TikTok reply · ceramah Q&A",
        },
        {
            "soalan": "Ada pakatan sulit PAS-BN?",
            "jawapan_bm": "Tiada pakatan tersembunyi. Ada Muafakat Nasional untuk kestabilan negeri & elak pecah undi. Fakta di meja — semak sendiri.",
            "jawapan_zh": "没有秘密协议。国阵合作是为了州选稳定，避免分裂投票。事实摆在桌面。",
            "jawapan_ta": "ரகசிய ஒப்பந்தம் இல்லை. நிலைத்தன்மை மட்டும்.",
            "saluran": "X thread · WA forward",
        },
        {
            "soalan": "Gelombang hijau bahaya komuniti Cina?",
            "jawapan_bm": "Itu label politik DAP untuk takutkan pengundi. Tanya: apa negeri buat untuk peniaga & sekolah? Banding data, bukan rumor.",
            "jawapan_zh": "那是行动党的政治标签。请问：州政府为商家和学校做了什么？用数据比较，不是谣言。",
            "jawapan_ta": "பயமுறுத்தல் அல்ல — தரவுகளை ஒப்பிடுங்கள்.",
            "saluran": "Podcast · IG carousel slide 2",
        },
        {
            "soalan": "SJKT dapat perhatian ke?",
            "jawapan_bm": "Ya — kemas kini BM+Tamil status guru & peruntukan. Group ibu bapa SJKT Port Dickson/Seremban. Fakta KPM.",
            "jawapan_zh": "",
            "jawapan_ta": "SJKT — BM+தமிழ் புதுப்பிப்பு. பெற்றோர் குழுவில் பகிருங்கள்.",
            "saluran": "FB India · kuil notice",
        },
        {
            "soalan": "Duduk rumah (tak keluar undi) boleh?",
            "jawapan_bm": "Duduk rumah = biarkan orang lain tentukan. Jika mahu perkhidmatan lebih baik — keluar undi, pilih kestabilan. (Bandar: counter abstention aktif.)",
            "jawapan_zh": "不投票等于让别人决定。要更好的服务，就出来投票，选择稳定。",
            "jawapan_ta": "வாக்களிப்பு = சேவைக்கான வாய்ப்பு.",
            "saluran": "Helaian bandar sahaja — jangan galak boikot",
        },
    ]


def _ceramah_script() -> Dict[str, str]:
    return {
        "label": "Ceramah — Segment 5 minit (selit dalam ceramah utama)",
        "bm": (
            "[MINIT 0-1] 'Saya nak cakap 5 minit untuk rakan-rakan komuniti Cina & India yang hadir.'\n"
            "[MINIT 1-2] Isu sebenar: kos hidup, SME, SJKT, pekerjaan — bukan teologi.\n"
            "[MINIT 2-3] Counter: tuduhan 'gelombang hijau' tanpa bukti — kita jawab fakta exco.\n"
            "[MINIT 3-4] 3 perkara negeri sedang urus: bantuan peniaga, trafik/PBT, SJKT.\n"
            "[MINIT 4-5] Edar helaian BM+中文 / nota Tamil di gerai. 'Undi = perkhidmatan.'"
        ),
        "zh": "5分钟：实际问题——生活成本、中小企业。事实回应，不是恐惧宣传。领取中英援助清单。",
        "ta": "5 நிமிடம்: SJKT, வேலை, சுகாதாரம் — உண்மைகள் மட்டும்.",
        "nota_ground": "Letak meja gerai dengan banner A3 + QR WhatsApp. Jangan lebih 5 minit — elak muak.",
    }


def _build_payload(intel: Dict[str, Any]) -> Dict[str, Any]:
    n9 = intel.get("n9", {})
    ch = n9.get("chinese", {})
    ind = n9.get("indian", {})
    targets = intel.get("targets", {})

    dun_rows: List[Dict[str, str]] = []
    for row in _build_dun_matrix("Negeri Sembilan"):
        code = row["dun_code"]
        crawl = targets.get(code, {})
        dun_rows.append({
            "code": code,
            "name": row["dun_name"],
            "priority": row["priority"],
            "sasaran_mn": "★" if code in N9_TARGET_20 else "",
            "fokus": _ground_fokus(code),
            "issue": row["primary_issue"],
            "crawl_cina": str(crawl.get("posts_chinese", "—")),
            "chinese_action": _strip_prefix(row["chinese_action"]),
            "indian_action": _strip_prefix(row["indian_action"]),
            "ch_channels": _channels(code, "chinese"),
            "in_channels": _channels(code, "indian"),
        })

    return {
        "generated_at": datetime.now(MYT).strftime("%Y-%m-%d %H:%M:%S"),
        "state": "Negeri Sembilan",
        "dun_count": len(dun_rows),
        "intel_summary": {
            "posts_cina": ch.get("posts", 0),
            "posts_india": ind.get("posts", 0),
            "neg_cina_pct": ch.get("neg_pct", 0),
            "top_issue_cina": (ch.get("issues") or [["—", 0]])[0][0],
        },
        "cara_guna_doc": [
            "1. Baca 'Ringkasan 1 halaman' (muka surat 2)",
            "2. Pilih komuniti: BAHAGIAN A (Cina) atau B (India)",
            "3. Copy post FB/X/IG/TikTok → paste terus",
            "4. Copy prompt AI infografik → paste ke Canva/ChatGPT/Midjourney",
            "5. Agihkan jadual 36 DUN kepada calon",
            "6. Minggu 1: buat 3 item 'Tindakan wajib' sahaja — jangan semua serentak",
        ],
        "socmed_chinese": _socmed_pack_chinese(),
        "socmed_indian": _socmed_pack_indian(),
        "ai_prompts": _ai_prompts(),
        "counter_qa": _counter_qa(),
        "ceramah": _ceramah_script(),
        "tindakan_wajib": [
            {"minggu": 1, "item": "POST FB Cina #1 + INFOGRAFIK 1 (prompt AI)", "siapa": "Operasi Cina HQ", "dun": "N10, N28"},
            {"minggu": 1, "item": "POST FB India #1 SJKT + INFOGRAFIK 3", "siapa": "Operasi India HQ", "dun": "N25, N31"},
            {"minggu": 1, "item": "TikTok 30s Cina + WA forward template", "siapa": "Media team", "dun": "Seremban/Nilai"},
            {"minggu": 2, "item": "IG Carousel 5 slide (kedua-dua komuniti)", "siapa": "Designer", "dun": "Bandar"},
            {"minggu": 2, "item": "FB Live 15 min (podcast outline)", "siapa": "Juruhebah Cina + exco", "dun": "N28"},
            {"minggu": 2, "item": "Banner A3 pasar + kuil", "siapa": "Ground team", "dun": "P1 DUN"},
        ],
        "dun_rows": dun_rows,
    }


def _add_copy_block(doc: Any, title: str, text: str, rgb: Any = None) -> None:
    from docx.shared import Pt, RGBColor

    doc.add_heading(title, level=3)
    p = doc.add_paragraph()
    r = p.add_run(text)
    r.font.size = Pt(10)
    if rgb:
        r.font.color.rgb = rgb


def _write_docx(payload: Dict[str, Any], out_path: Path) -> Path:
    from docx import Document
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.enum.section import WD_ORIENT
    from docx.shared import Pt, RGBColor

    doc = Document()
    navy = RGBColor(30, 58, 95)
    red = RGBColor(180, 40, 40)
    green = RGBColor(22, 101, 52)
    grey = RGBColor(100, 116, 139)

    # === COVER ===
    t = doc.add_paragraph()
    t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = t.add_run("PAS · PN · MN — Muafakat Nasional")
    r.bold = True
    r.font.size = Pt(13)
    r.font.color.rgb = navy

    doc.add_heading("Kit Operasi Lengkap PRN N9", level=0).alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub = doc.add_paragraph(
        "Copywriting Socmed · Prompt AI Infografik · 36 DUN\n"
        "Komuniti Cina & India — siap copy-paste"
    )
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER

    for line in [
        f"Dijana: {payload['generated_at']}",
        "⚠ INTERNAL — HQ & calon sahaja",
        "Cara guna: lihat senarai di halaman seterusnya",
    ]:
        p = doc.add_paragraph(line)
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER

    # === CARA GUNA ===
    doc.add_page_break()
    doc.add_heading("📖 CARA GUNA DOKUMEN INI (5 langkah)", level=1)
    for step in payload["cara_guna_doc"]:
        doc.add_paragraph(step, style="List Number")

    intel = payload["intel_summary"]
    doc.add_heading("📊 Intel ringkas", level=2)
    doc.add_paragraph(
        f"Cina: {intel['posts_cina']} posts · Neg {intel['neg_cina_pct']}% · Isu: {intel['top_issue_cina']}\n"
        f"India: {intel['posts_india']} posts"
    )

    doc.add_heading("✅ Tindakan wajib (jadual 2 minggu)", level=2)
    for t in payload["tindakan_wajib"]:
        doc.add_paragraph(
            f"Minggu {t['minggu']}: {t['item']} · {t['siapa']} · DUN: {t['dun']}",
            style="List Bullet",
        )

    # === BAHAGIAN A: CINA ===
    doc.add_page_break()
    doc.add_heading("🇨🇳 BAHAGIAN A — COPYWRITING KOMUNITI CINA", level=1)
    ch = payload["socmed_chinese"]

    doc.add_heading(ch["x_thread"]["label"], level=2)
    for tw in ch["x_thread"]["tweets"]:
        _add_copy_block(
            doc,
            f"Tweet {tw['tweet']}",
            f"BM:\n{tw['bm']}\n\n中文:\n{tw['zh']}\n\n{tw['hashtags']}",
        )

    doc.add_heading("Facebook — 3 Posts", level=2)
    for post in ch["facebook"]:
        _add_copy_block(
            doc,
            post["title"],
            f"🇲🇾 BM:\n{post['bm']}\n\n🇨🇳 中文:\n{post['zh']}\n\n📌 CTA: {post['cta']}\n⏰ {post['bila']}",
        )

    doc.add_heading(ch["instagram_carousel"]["label"], level=2)
    for sl in ch["instagram_carousel"]["slides"]:
        _add_copy_block(
            doc,
            f"Slide {sl['no']}",
            f"BM: {sl['headline_bm']}\n中文: {sl['headline_zh']}\n{sl['body']}",
        )

    tt = ch["tiktok_30s"]
    _add_copy_block(
        doc, tt["label"],
        f"Hook: {tt['hook']}\nScene1: {tt['scene_1']}\nScene2: {tt['scene_2']}\nScene3: {tt['scene_3']}\n"
        f"CTA: {tt['cta']}\nMusic: {tt['music']}\n{tt['hashtags']}",
    )
    t60 = ch["tiktok_60s"]
    _add_copy_block(doc, t60["label"], f"BM:\n{t60['script_bm']}\n\n中文:\n{t60['script_zh']}")

    _add_copy_block(doc, ch["whatsapp"]["label"], ch["whatsapp"]["text"])

    yt = ch["youtube_podcast"]
    doc.add_heading(yt["label"], level=2)
    doc.add_paragraph(f"Tajuk: {yt['tajuk']}")
    for seg in yt["segments"]:
        doc.add_paragraph(seg, style="List Bullet")
    _add_copy_block(doc, "Script pembuka", f"BM:\n{yt['intro_script_bm']}\n\n中文:\n{yt['intro_script_zh']}")

    # === BAHAGIAN B: INDIA ===
    doc.add_page_break()
    doc.add_heading("🇮🇳 BAHAGIAN B — COPYWRITING KOMUNITI INDIA", level=1)
    ind = payload["socmed_indian"]

    doc.add_heading(ind["x_thread"]["label"], level=2)
    for tw in ind["x_thread"]["tweets"]:
        ta = tw.get("ta", "")
        _add_copy_block(
            doc, f"Tweet {tw['tweet']}",
            f"BM:\n{tw['bm']}\n\nதமிழ்:\n{ta}\n\n{tw['hashtags']}",
        )

    doc.add_heading("Facebook — 3 Posts", level=2)
    for post in ind["facebook"]:
        _add_copy_block(
            doc, post["title"],
            f"BM:\n{post['bm']}\n\nதமிழ்:\n{post.get('ta', '')}\n\nCTA: {post['cta']} · {post['bila']}",
        )

    doc.add_heading(ind["instagram_carousel"]["label"], level=2)
    for sl in ind["instagram_carousel"]["slides"]:
        _add_copy_block(
            doc, f"Slide {sl['no']}",
            f"BM: {sl['headline_bm']}\nTamil: {sl.get('headline_ta', '')}\n{sl['body']}",
        )

    tt = ind["tiktok_30s"]
    _add_copy_block(
        doc, tt["label"],
        f"{tt['hook']}\n{tt['scene_1']}\n{tt['scene_2']}\n{tt['scene_3']}\nCTA: {tt['cta']}\n{tt['hashtags']}",
    )
    _add_copy_block(doc, ind["whatsapp"]["label"], ind["whatsapp"]["text"])

    yt = ind["youtube_podcast"]
    doc.add_heading(yt["label"], level=2)
    for seg in yt["segments"]:
        doc.add_paragraph(seg, style="List Bullet")
    _add_copy_block(
        doc, "Script pembuka",
        f"BM:\n{yt['intro_script_bm']}\n\nதமிழ்:\n{yt.get('intro_script_ta', '')}",
    )

    # === BAHAGIAN C: COUNTER Q&A ===
    doc.add_page_break()
    doc.add_heading("💬 BAHAGIAN C — Jawapan Pantas (komen / Q&A)", level=1)
    for qa in payload["counter_qa"]:
        doc.add_heading(qa["soalan"], level=3)
        doc.add_paragraph(f"🇲🇾 {qa['jawapan_bm']}")
        if qa.get("jawapan_zh"):
            doc.add_paragraph(f"🇨🇳 {qa['jawapan_zh']}")
        if qa.get("jawapan_ta"):
            doc.add_paragraph(f"🇮🇳 {qa['jawapan_ta']}")
        doc.add_paragraph(f"Saluran: {qa['saluran']}", style="Intense Quote")

    # === BAHAGIAN D: AI PROMPTS ===
    doc.add_page_break()
    doc.add_heading("🤖 BAHAGIAN D — PROMPT AI (copy-paste ke mana-mana tool)", level=1)
    ai = payload["ai_prompts"]
    doc.add_paragraph(ai["cara_guna"], style="Intense Quote")

    doc.add_heading("📊 Infografik (5 prompt)", level=2)
    for inf in ai["infografik"]:
        doc.add_heading(inf["nama"], level=3)
        doc.add_paragraph(f"Tool: {inf['tool']} · Saiz: {inf['aspect']}")
        _add_copy_block(doc, "⬇️ PROMPT (copy semua)", inf["prompt"], grey)
        _add_copy_block(doc, "Teks overlay (manual jika perlu)", inf["teks_overlay"])

    doc.add_heading("🖼️ Banner & Poster (3 prompt)", level=2)
    for ban in ai["banner_poster"]:
        doc.add_heading(ban["nama"], level=3)
        doc.add_paragraph(f"Tool: {ban['tool']} · {ban['aspect']}")
        _add_copy_block(doc, "⬇️ PROMPT", ban["prompt"], grey)

    doc.add_heading("🎬 Video AI (3 prompt)", level=2)
    for vid in ai["video_ai"]:
        doc.add_heading(vid["nama"], level=3)
        doc.add_paragraph(f"Tool: {vid['tool']}")
        _add_copy_block(doc, "⬇️ PROMPT", vid["prompt"], grey)

    # === BAHAGIAN E: CERAMAH ===
    doc.add_page_break()
    doc.add_heading("🎤 BAHAGIAN E — Ceramah (5 minit)", level=1)
    c = payload["ceramah"]
    _add_copy_block(doc, c["label"], c["bm"])
    _add_copy_block(doc, "中文 ringkas", c["zh"])
    _add_copy_block(doc, "தமிழ்", c["ta"])
    p = doc.add_paragraph(f"Nota ground: {c['nota_ground']}")
    for run in p.runs:
        run.font.color.rgb = green

    # === BAHAGIAN F: 36 DUN ===
    doc.add_page_break()
    section = doc.sections[-1]
    section.orientation = WD_ORIENT.LANDSCAPE
    section.page_width, section.page_height = section.page_height, section.page_width

    doc.add_heading("📋 BAHAGIAN F — 36 DUN Checklist", level=1)
    doc.add_paragraph("★ = 20 kerusi sasaran MN")

    cols = ["DUN", "Nama", "Pri", "★", "Fokus", "Tindakan Cina", "Saluran C", "Tindakan India", "Saluran I"]
    tbl = doc.add_table(rows=1, cols=len(cols))
    tbl.style = "Table Grid"
    for i, h in enumerate(cols):
        tbl.rows[0].cells[i].text = h
        for p in tbl.rows[0].cells[i].paragraphs:
            for run in p.runs:
                run.bold = True
                run.font.size = Pt(8)

    for row in payload["dun_rows"]:
        cells = tbl.add_row().cells
        vals = [
            row["code"], row["name"], row["priority"], row["sasaran_mn"],
            row["fokus"], row["chinese_action"], row["ch_channels"],
            row["indian_action"], row["in_channels"],
        ]
        for i, v in enumerate(vals):
            cells[i].text = v
            for p in cells[i].paragraphs:
                for run in p.runs:
                    run.font.size = Pt(7)

    doc.save(out_path)
    return out_path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--open", action="store_true")
    args = parser.parse_args()

    print("📄 Jana N9 Kit Operasi LENGKAP (DOCX)…")
    intel = _load_intel()
    payload = _build_payload(intel)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    out = _write_docx(payload, OUT_DOCX)

    n_fb = len(payload["socmed_chinese"]["facebook"]) + len(payload["socmed_indian"]["facebook"])
    n_ai = len(payload["ai_prompts"]["infografik"]) + len(payload["ai_prompts"]["banner_poster"]) + len(payload["ai_prompts"]["video_ai"])
    print(f"✅ JSON: {OUT_JSON}")
    print(f"✅ DOCX: {out}")
    print(f"   Copy socmed: X+FB+IG+TikTok+WA+Podcast (Cina+India)")
    print(f"   AI prompts: {n_ai} · Counter Q&A: {len(payload['counter_qa'])} · 36 DUN")

    if args.open:
        import subprocess
        subprocess.run(["open", str(out)], check=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
