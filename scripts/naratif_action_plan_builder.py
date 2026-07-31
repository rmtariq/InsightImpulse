#!/usr/bin/env python3
"""Bina cadangan tindakan naratif Cina/India — terperinci, boleh laksana, per DUN."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data/projects/political/PRN/reports/naratif_cina_india"
MYT = timezone(timedelta(hours=8))

# Nama kerusi ringkas — rujuk scripts/dun_seat_keywords.py
JOHOR_DUNS = {
    f"N{i:02d}": name
    for i, name in enumerate(
        [
            "Buloh Kasap", "Jementah", "Pemanis", "Kemelah", "Tenang", "Bekok", "Bukit Kepong",
            "Bukit Pasir", "Gambir", "Tangkak", "Serom", "Bentayan", "Simpang Jeram", "Bukit Naning",
            "Maharani", "Sungai Balang", "Semarah", "Sri Medan", "Yong Peng", "Semarang",
            "Parit Yaani", "Parit Raja", "Penggaram", "Senggarang", "Rengit", "Machap",
            "Layang-Layang", "Mengkibol", "Mahkota", "Paloh", "Kahang", "Endau", "Tenggaroh",
            "Panti", "Pasir Raja", "Sedili", "Johor Lama", "Penawar", "Tanjung Surat", "Tiram",
            "Puteri Wangsa", "Johor Jaya", "Permas", "Larkin", "Stulang", "Perling", "Kempas",
            "Skudai", "Kota Iskandar", "Bukit Permai", "Bukit Batu", "Senai", "Benut",
            "Pulai Sebatang", "Pekan Nanas", "Kukup",
        ],
        start=1,
    )
}

N9_DUNS = {
    f"N{i:02d}": name
    for i, name in enumerate(
        [
            "Chennah", "Pertang", "Sungai Lui", "Klawang", "Serting", "Palong", "Jeram Padang",
            "Bahau", "Lenggeng", "Nilai", "Lobak", "Temiang", "Sikamat", "Ampangan", "Juasseh",
            "Seri Menanti", "Senaling", "Kuala Pilah", "Johol", "Labu", "Bukit Kepayang", "Rahang",
            "Mambau", "Seremban Jaya", "Paroi", "Chembong", "Rantau", "Seremban Kota", "Chuah",
            "Lukut", "Bagan Pinang", "Linggi", "Sri Tanjung", "Gemas", "Gemencheh", "Repah",
        ],
        start=1,
    )
}

# Profil sasaran komuniti per DUN (untuk cadangan automatik)
JOHOR_CHINESE_URBAN = {
    "N40", "N41", "N42", "N43", "N44", "N45", "N46", "N47", "N48", "N49", "N50", "N51", "N52",
}
JOHOR_CHINESE_MIXED = {"N12", "N15", "N18", "N19", "N23", "N28", "N29", "N09", "N10"}
JOHOR_INDIAN_BELT = {
    "N01", "N18", "N23", "N24", "N28", "N29", "N40", "N43", "N47", "N50",
}
N9_CHINESE_URBAN = {"N10", "N11", "N12", "N21", "N24", "N25", "N28", "N29", "N30"}
N9_CHINESE_MIXED = {"N06", "N08", "N13", "N14", "N27"}
N9_INDIAN_BELT = {"N10", "N13", "N25", "N31", "N32", "N33"}


def _action(
    aid: str,
    priority: str,
    title: str,
    what: str,
    why: str,
    how: List[str],
    message: Dict[str, str],
    channel: str,
    owner: str,
    deadline: str,
    kpi: str,
    duns: List[str],
    community: str,
    issue: str,
) -> Dict[str, Any]:
    return {
        "id": aid,
        "priority": priority,
        "title": title,
        "what": what,
        "why": why,
        "how_steps": how,
        "message": message,
        "channel": channel,
        "owner": owner,
        "deadline": deadline,
        "kpi": kpi,
        "duns": duns,
        "community": community,
        "issue": issue,
    }


def _johor_priority_actions() -> List[Dict[str, Any]]:
    return [
        _action(
            "JHR-P1-01", "P1 — MESTI DILAKSANAKAN MINGGU INI",
            "Jernihkan isu 巫伊 / Muafakat Nasional kepada komuniti Cina bandar",
            "Keluarkan helaian fakta BM+中文 yang menjelaskan kedudukan MN: tiada pakatan sulit, fokus kestabilan negeri dan elak pecah undi.",
            "Data crawl menunjukkan skeptisisme Cina Johor terhadap 'PAS dalam kotak BN'. Tanpa jawapan jelas, risiko abstention (duduk rumah) di kerusi bandar meningkat.",
            [
                "HQ koalisi sediakan 1-pager BM+中文 (tiada logo agama, fokus perkhidmatan).",
                "Calon DUN N45 Stulang, N48 Skudai, N46 Perling edar ke 10 group WhatsApp merchant utama.",
                "Juruhebah Cina (bukan calon Melayu) jawab komen di Sin Chew/FB — nada tenang, fakta sahaja.",
                "Elak debat syurga/Harakat — redirect ke China Press/Shawn Loh sebagai bukti semakan fakta.",
            ],
            {
                "bm": "Soalan komuniti Cina: adakah ada pakatan tersembunyi? Jawapan kami: kestabilan Johor & elak pecah undi. Fakta di meja — bukan rumor WhatsApp.",
                "zh": "华人社区关心：有没有“秘密协议”？我们的立场：柔佛州选稳定、避免分裂投票。事实摆在桌面，不是谣言。",
                "ta": "",
            },
            "FB Group merchant + WhatsApp forward + dialog peniaga",
            "Operasi Cina Johor + calon DUN bandar (Stulang/Skudai/Perling)",
            "48 jam selepas naratif negatif muncul",
            "≥5 group merchant kongsi helaian; sentimen negatif 巫伊 turun dalam crawl susulan",
            ["N45 Stulang", "N48 Skudai", "N46 Perling", "N44 Larkin", "N47 Kempas"],
            "chinese", "PH-BN Relationship / MN optics",
        ),
        _action(
            "JHR-P1-02", "P1 — MESTI DILAKSANAKAN MINGGU INI",
            "Respons kos hidup & trafik JB/Skudai dengan data bantuan negeri",
            "Terbitkan infografik 3-bullet: bantuan kos sara hidup aktif, status projek trafik Skudai/JB, nombor hotline aduan MBSA.",
            "Isu #1 naratif Cina Johor = kos hidup + trafik. Negatif tinggi jika hanya janji tanpa nombor dan tarikh.",
            [
                "Exco perkhidmatan bandar sahkan senarai bantuan (negeri + persekutuan) dalam 24 jam.",
                "Reka poster BM+中文 — 3 fakta, 1 CTA 'PM untuk helaian penuh'.",
                "Ground team lawat pasar Skudai & Stulang — kumpul 20 aduan bertulis untuk follow-up 7 hari.",
                "Pos FB pada waktu 8–10 malam (peak engagement komuniti Cina).",
            ],
            {
                "bm": "Kos sara hidup & trafik JB/Skudai memang isu sebenar. Kami dengar. Senarai bantuan negeri + perkhidmatan bandar dikemas kini. Stabiliti Johor = perniagaan boleh merancang.",
                "zh": "柔佛要稳定，小贩和中小企业才能安心做生意。州政府整理生活成本援助与市区交通服务清单。",
                "ta": "",
            },
            "FB + poster fizikal di pasar + TikTok 30s (pasar Skudai)",
            "Exco + Operasi Cina + calon N48/N45",
            "72 jam",
            "Infografik dikongsi ≥200 kali; ≥10 aduan merchant direkod & dijawab",
            ["N48 Skudai", "N45 Stulang", "N47 Kempas", "N44 Larkin", "N42 Johor Jaya"],
            "chinese", "Cost of Living / Road and Traffic",
        ),
        _action(
            "JHR-P1-03", "P1 — MESTI DILAKSANAKAN MINGGU INI",
            "Counter berita palsu Harakatdaily — tanpa masuk debat agama",
            "Siarkan nota ringkas: Harakatdaily disahkan palsu oleh China Press; arahkan komuniti semak sebelum kongsi.",
            "Crawl Harakat issue ada tapi komuniti Cina Johor kurang prihatin syurga — lebih prihatin kredibiliti & ekonomi. Counter mesti fakta media Cina, bukan fatwa.",
            [
                "Sediakan screenshot China Press + BM summary (bukan ayat provokasi).",
                "Admin group Cina pos sebagai 'Pengesanan Berita' — bukan 'Serangan PAS'.",
                "Calon elak quote ayat Quran/hadith dalam respons.",
            ],
            {
                "bm": "Berita palsu Harakatdaily disahkan media Cina (China Press). Jangan kongsi tanpa semak. Fokus kita: perkhidmatan & ekonomi Johor.",
                "zh": "Harakatdaily假新闻已被中国报澄清。请勿转发未经核实内容。我们关注柔佛经济与民生。",
                "ta": "",
            },
            "WhatsApp + FB Group Cina + kenyataan media",
            "Media team + juruhebah Cina",
            "24 jam apabila isu viral",
            "Penurunan share Harakat-themed posts dalam crawl",
            ["N45 Stulang", "N48 Skudai", "N46 Perling", "N49 Kota Iskandar"],
            "chinese", "Misinformation",
        ),
        _action(
            "JHR-P1-04", "P1 — MESTI DILAKSANAKAN MINGGU INI",
            "Fakta sheet kekurangan doktor Hospital Segamat — BM+Tamil",
            "Keluarkan kenyataan fakta: bilangan jawatan, tarikh pengisian, hotline pesakit — BM+Tamil.",
            "Komuniti India Johor pragmatik: hospital & pekerjaan > ideologi. Segamat (N01) muncul dalam crawl negatif kesihatan.",
            [
                "Dapatkan angka disahkan dari KKM negeri/JKN Johor.",
                "Edar ke group kilang Kluang/Batu Pahat + kuil/masjid komuniti India.",
                "Calon berjumpa ketua persatuan India Segamat — 30 minit, bawa fakta, bukan manifesto panjang.",
            ],
            {
                "bm": "Kekurangan doktor di Hospital Segamat dirakam. Pasukan negeri sedang susun jawapan fakta + langkah interim. Pekerjaan & kesihatan komuniti India kekal keutamaan.",
                "zh": "",
                "ta": "சிகாமாத் மருத்துவமனையில் மருத்துவர் பற்றாக்குறை குறித்து கேள்விகள் உள்ளன. மாநில அ팀் உறுதிப்படுத்தப்பட்ட தகவலுடன் பதிலளிக்கிறது.",
            },
            "FB Tamil pages + WhatsApp MIC/JPN + lawatan komuniti",
            "Calon N01 Buloh Kasap + exco kesihatan",
            "5 hari",
            "Kenyataan BM+Tamil diedar; ≥3 engagement komuniti India positif",
            ["N01 Buloh Kasap", "N28 Mengkibol", "N29 Mahkota"],
            "indian", "Local Government Services / Employment",
        ),
        _action(
            "JHR-P2-01", "P2 — SUSULAN 7–14 HARI",
            "Engagement pekerjaan kilang Johor selatan (India + Punjabi)",
            "Sesi dialog ringkas di kawasan kilang Kluang/Batu Pahat/Kulai: pekerjaan, OT, keselamatan, perubatan.",
            "India Johor kurang exposure PAS/PN — peluang menang trust melalui perkhidmatan konkrit, bukan ceramah politik.",
            [
                "Kenal pasti 3 kilang dengan majoriti pekerja India dalam DUN sasaran.",
                "Sediakan slot 15 minit 'Khidmat Pekerja' — bukan ceramah 2 jam.",
                "Edar kad hotline pejabat khidmat BM+Tamil+English (Punjabi).",
            ],
            {
                "bm": "Pekerja kilang Johor: isu gaji, OT & kesihatan. Pejabat khidmat negeri buka saluran aduan disahkan — BM, Tamil, English.",
                "zh": "",
                "ta": "தொழிலாளர்களின் வேலைவாய்ப்பு, ஊதியம் மற்றும் சுகாதாரம் — மாநில சேவை மையம் தகவலுடன் பதிலளிக்கிறது.",
            },
            "Lawatan kilang + WhatsApp JPN",
            "Calon N28/N29/N50 + JPN Johor",
            "14 hari",
            "≥2 sesi kilang; rekod aduan & follow-up",
            ["N28 Mengkibol", "N29 Mahkota", "N50 Bukit Permai", "N18 Sri Medan"],
            "indian", "Employment",
        ),
        _action(
            "JHR-P2-02", "P2 — SUSULAN 7–14 HARI",
            "Video TikTok 30s — pasar Skudai (Cina)",
            "Hasilkan video pendek: calon dengar peniaga → 3 bullet bantuan → CTA stabiliti.",
            "Video pendek outperform poster statik untuk komuniti Cina bandar bawah 45 tahun.",
            [
                "Guna prompt CapCut Template B (pasar walk).",
                "Subtitle BM + 中文 wajib.",
                "Post 7pm; boost RM50 jika engagement organik >100 dalam 2 jam.",
            ],
            {
                "bm": "Kami dengar isu kos & trafik di Skudai. Stabiliti Johor = perniagaan boleh merancang.",
                "zh": "我们听到士古来商家的心声。柔佛稳定，生意才能长远规划。",
                "ta": "",
            },
            "TikTok + FB Reels + IG",
            "Media calon N48 + sukarelawan Cina",
            "10 hari",
            "≥1,000 views organik; ≥50 simpan/kongsi",
            ["N48 Skudai", "N45 Stulang"],
            "chinese", "Cost of Living",
        ),
    ]


def _n9_priority_actions() -> List[Dict[str, Any]]:
    return [
        _action(
            "N9-P1-01", "P1 — MESTI DILAKSANAKAN MINGGU INI",
            "Jawab kos hidup & SME Seremban/Jelebu dengan data exco",
            "Terbitkan helaian bantuan aktif (negeri + persekutuan) BM+中文 dalam 48 jam — khusus peniaga Nilai, Seremban, Jelebu.",
            "N9 Cina = negatif tertinggi pada kos hidup/SME. Ini risiko abstention utama — bukan boycott eksplisit.",
            [
                "Exco ekonomi kumpul senarai bantuan SMI/peniaga kecil yang masih aktif.",
                "Poster A3 di persatuan peniaga Seremban + Nilai.",
                "Live FB 20 minit Q&A BM+中文 — exco atau calon dengan data, bukan slogan.",
            ],
            {
                "bm": "Aduan kos sara hidup & SME di Jelebu/Seremban kami rakam. Helaian bantuan aktif BM+中文 dalam 48 jam. Undi = perkhidmatan, bukan drama.",
                "zh": "芙蓉及汝来商家关注生活成本。48小时内发布中英对照援助清单。投票要看服务，不是口水战。",
                "ta": "",
            },
            "FB Live + poster persatuan peniaga + WhatsApp",
            "Exco + calon N10 Nilai, N28 Seremban Kota, N13 Sikamat",
            "48 jam",
            "Helaian diedar; ≥15 peniaga mendaftar follow-up",
            ["N10 Nilai", "N11 Lobak", "N28 Seremban Kota", "N13 Sikamat", "N06 Palong"],
            "chinese", "Cost of Living / SME and Business",
        ),
        _action(
            "N9-P1-02", "P1 — MESTI DILAKSANAKAN MINGGU INI",
            "Tindakan trafik & parking bandar Seremban",
            "Umumkan mesyuarat MBSA + peniaga minggu ini; pos kemas kini tarikh & tindakan interim.",
            "Trafik/parking berulang dalam crawl N9 — isu mudah difahami & boleh tunjuk 'kami urus'.",
            [
                "Dapatkan tarikh mesyuarat disahkan dari MBSA.",
                "Pos BM+中文: 'Kesesakan & parking — mesyuarat [tarikh]'.",
                "Kumpul foto lokasi parking bermasalah (3 titik) untuk laporan calon.",
            ],
            {
                "bm": "Kesesakan & parking di bandar Seremban isu berulang. Pasukan tempatan sedang susun mesyuarat dengan MBSA & peniaga — kemas kini minggu ini.",
                "zh": "芙蓉市区交通与停车问题，州团队本周与市议会及商家开会跟进。",
                "ta": "",
            },
            "FB Group merchant Seremban + poster premis",
            "Calon N28/N21 + MBSA liaison",
            "7 hari",
            "Mesyuarat dijalankan; minit ringkas diedar BM+中文",
            ["N28 Seremban Kota", "N21 Bukit Kepayang", "N24 Seremban Jaya", "N11 Lobak"],
            "chinese", "Road and Traffic",
        ),
        _action(
            "N9-P1-03", "P1 — MESTI DILAKSANAKAN MINGGU INI",
            "Kemas kini SJKT — status guru & peruntukan BM+Tamil",
            "Nota rasmi: bilangan kekosongan guru, tarikh pengisian, peruntukan tahun semasa — BM+Tamil.",
            "India N9 pragmatik: SJKT & pekerjaan. Jika PH/MN tunjuk delivery, sokongan kekal.",
            [
                "Dapatkan angka dari JPN N9 / exco pendidikan.",
                "Edar ke group ibu bapa SJKT Port Dickson, Seremban, Nilai.",
                "Elak politikkan agama — fokus bilik darjah & guru.",
            ],
            {
                "bm": "Isu guru SJKT & pendidikan Tamil masih panas di N9. Kami sediakan kemas kini BM+Tamil status pengisian & peruntukan — fakta sahaja.",
                "zh": "",
                "ta": "SJKT ஆசிரியர் பற்றாக்குறை — தமிழ்+BM அதிகாரப்பூர்வ புதுப்பிப்பு விரைவில்.",
            },
            "WhatsApp ibu bapa SJKT + FB Tamil",
            "Exco pendidikan + calon N25 Paroi, N31 Bagan Pinang",
            "5 hari",
            "Nota BM+Tamil diedar ke ≥10 group SJKT",
            ["N25 Paroi", "N31 Bagan Pinang", "N10 Nilai", "N13 Sikamat"],
            "indian", "Chinese Education / Employment",
        ),
        _action(
            "N9-P1-04", "P1 — MESTI DILAKSANAKAN MINGGU INI",
            "Pantau & counter strategi PN 'pecah undi' di kerusi campuran",
            "HQ sediakan skrip jawapan BM: Muafakat 1-vs-1 kerusi Melayu, fokus perkhidmatan di kerusi campuran.",
            "Crawl menyebut strategi PN — perlu jawapan awal sebelum frame DAP/PH menguasai naratif.",
            [
                "Monitor mention 'pecah undi' / '三分票' dalam group Cina.",
                "Skrip 3 ayat: stabil negeri, fakta, undi = perkhidmatan.",
                "Jangan serang peribadi calon PH — serang prestasi & penyelesaian.",
            ],
            {
                "bm": "Tiada pakatan sulit. Ada kestabilan negeri supaya undi tidak pecah. Fakta di meja — bukan rumor.",
                "zh": "没有秘密协议。只有州选稳定，避免分裂投票。事实为主。",
                "ta": "ரகசிய கூட்டணி இல்லை. நிலைத்தன்மை மற்றும் உண்மைகள் மட்டும்.",
            },
            "FB + WhatsApp + media Cina",
            "Operasi N9 + media team",
            "48 jam",
            "Counter-post dalam 24j selepas naratif PN viral",
            ["N10 Nilai", "N28 Seremban Kota", "N27 Rantau", "N06 Palong"],
            "chinese", "Gerakan and PN / PH-BN Relationship",
        ),
        _action(
            "N9-P2-01", "P2 — SUSULAN 7–14 HARI",
            "Lawatan DUN bandar Cina — N06 Palong, N10 Nilai",
            "Walkabout bertemu peniaga & persatuan — bawa helaian bantuan, rekod aduan 7 hari.",
            "Ground presence kurang naratif negatif abstention — 'mereka dengar'.",
            [
                "Agenda 2 jam: pasar + 3 kedai kecil + 1 persatuan.",
                "Setiap aduan dapat nombor rujukan.",
                "Pos foto BM+中文 dalam 24 jam selepas lawatan.",
            ],
            {
                "bm": "Lawatan perkhidmatan: kami dengar aduan peniaga Palong/Nilai. Setiap kes dapat nombor rujukan follow-up.",
                "zh": "服务走访：我们听取巴珑/芙蓉商家诉求。每个案件都有跟进编号。",
                "ta": "",
            },
            "Ground + FB post-event",
            "Calon N06 + N10 + sukarelawan",
            "14 hari",
            "≥20 aduan direkod; ≥50% dijawab dalam 7 hari",
            ["N06 Palong", "N10 Nilai"],
            "chinese", "DAP Performance / Local Government Services",
        ),
        _action(
            "N9-P2-02", "P2 — SUSULAN 7–14 HARI",
            "Pekerjaan & ekonomi Port Dickson — komuniti India",
            "Sesi ringkas pelancongan/pekerjaan PD: fakta peluang kerja, kemahiran, SJKT berhampiran.",
            "Port Dickson (N31) — India + pelancongan; isu pekerjaan muncul dalam crawl.",
            [
                "Jumpa persatuan nelayan/pekerja pelancongan BM+Tamil.",
                "Edar infografik pekerjaan 3 bullet.",
            ],
            {
                "bm": "Port Dickson: peluang pekerjaan & kemahiran untuk komuniti India. Fakta dari agensi negeri — bukan janji kosong.",
                "zh": "",
                "ta": "போர்ட் டிக்சன்: வேலைவாய்ப்பு & திறன் மேம்பாடு — அதிகாரப்பூர்வ தகவலுடன்.",
            },
            "Lawatan PD + FB Tamil",
            "Calon N31 + agensi kerja negeri",
            "14 hari",
            "≥1 sesi komuniti; infografik diedar",
            ["N31 Bagan Pinang", "N32 Linggi"],
            "indian", "Employment",
        ),
    ]


def _dun_row(
    code: str,
    name: str,
    state: str,
    chinese_action: str,
    indian_action: str,
    priority: str,
    issue: str,
) -> Dict[str, str]:
    return {
        "dun_code": code,
        "dun_name": name,
        "state": state,
        "chinese_action": chinese_action,
        "indian_action": indian_action,
        "priority": priority,
        "primary_issue": issue,
    }


def _template_chinese_johor(code: str, name: str) -> str:
    if code in JOHOR_CHINESE_URBAN:
        return (
            f"[{code} {name}] Edar helaian BM+中文 kos hidup & trafik; dialog peniaga; "
            "jawab isu MN/巫伊 dengan fakta kestabilan — bukan teologi."
        )
    if code in JOHOR_CHINESE_MIXED:
        return (
            f"[{code} {name}] Lawatan pasar/pekan Cina; poster 3 fakta perkhidmatan tempatan; "
            "elak debat agama; fokus PBT & ekonomi."
        )
    return (
        f"[{code} {name}] Jika ada peniaga/komuniti Cina: WhatsApp helaian ringkas BM+中文 "
        "bantuan negeri; ajak keluar undi untuk perkhidmatan, bukan boycott."
    )


def _template_indian_johor(code: str, name: str) -> str:
    if code in JOHOR_INDIAN_BELT:
        return (
            f"[{code} {name}] Edar nota BM+Tamil pekerjaan/kesihatan; sesi kilang atau kuil 15 minit; "
            "fakta hospital/OT — bukan ceramah panjang."
        )
    return (
        f"[{code} {name}] Hubungi ketua komuniti India setempat; edar hotline khidmat BM+Tamil; "
        "fokus pekerjaan & pendidikan anak."
    )


def _template_chinese_n9(code: str, name: str) -> str:
    if code in N9_CHINESE_URBAN:
        return (
            f"[{code} {name}] Helaian bantuan SME/kos hidup BM+中文; FB Live/Q&A 20 min; "
            "counter abstention: undi = perkhidmatan."
        )
    if code in N9_CHINESE_MIXED:
        return (
            f"[{code} {name}] Lawatan peniaga; poster trafik/perkhidmatan jika bandar; "
            "jawab DAP prestasi dengan data exco."
        )
    return (
        f"[{code} {name}] Komuniti Cina minoriti: edar helaian ringkas; ingatkan keluar undi "
        "untuk kestabilan perkhidmatan tempatan."
    )


def _template_indian_n9(code: str, name: str) -> str:
    if code in N9_INDIAN_BELT:
        return (
            f"[{code} {name}] Kemas kini SJKT/pekerjaan BM+Tamil; group ibu bapa & kilang; "
            "fakta guru/hospital — bukan politik agama."
        )
    return (
        f"[{code} {name}] Sambung komuniti India melalui kuil/masjid; edar nota pekerjaan BM+Tamil; "
        "rekod aduan 7 hari follow-up."
    )


def _build_dun_matrix(state_key: str) -> List[Dict[str, str]]:
    if state_key == "Johor":
        duns, tpl_c, tpl_i = JOHOR_DUNS, _template_chinese_johor, _template_indian_johor
        issue_map = {
            **{c: "Kos hidup / Trafik bandar" for c in JOHOR_CHINESE_URBAN},
            **{c: "Perkhidmatan campuran" for c in JOHOR_CHINESE_MIXED},
            **{c: "Pekerjaan / Kilang" for c in JOHOR_INDIAN_BELT},
        }
        st = "Johor"
    else:
        duns, tpl_c, tpl_i = N9_DUNS, _template_chinese_n9, _template_indian_n9
        issue_map = {
            **{c: "Kos hidup / SME" for c in N9_CHINESE_URBAN},
            **{c: "Perkhidmatan bandar" for c in N9_CHINESE_MIXED},
            **{c: "SJKT / Pekerjaan" for c in N9_INDIAN_BELT},
        }
        st = "Negeri Sembilan"

    rows: List[Dict[str, str]] = []
    for code, name in duns.items():
        pri = "P1" if code in issue_map else "P2"
        rows.append(
            _dun_row(
                code, name, st,
                tpl_c(code, name),
                tpl_i(code, name),
                pri,
                issue_map.get(code, "Outreach minoriti / keluar undi"),
            )
        )
    return rows


def build_action_plan(
    brief: Optional[Dict[str, Any]] = None,
    analytics: Optional[Dict[str, Any]] = None,
    focus: str = "n9",
) -> Dict[str, Any]:
    """Hasilkan pelan tindakan penuh untuk dashboard & DOCX.

    focus:
      - "n9" (default): Negeri Sembilan sahaja
      - "all": Johor + N9 (legacy)
    """
    focus_n9 = focus.lower() in ("n9", "negeri sembilan", "ns")
    purpose = (
        "Cadangan tindakan operasi untuk mengurus naratif komuniti Cina & India "
        "di Negeri Sembilan — setiap item menerangkan APA, MENGAPA, BAGAIMANA, "
        "dan MESEJ yang hendak disampaikan."
        if focus_n9
        else (
            "Cadangan tindakan operasi untuk mengurus naratif komuniti Cina & India "
            "di Johor dan Negeri Sembilan — setiap item menerangkan APA, MENGAPA, BAGAIMANA, "
            "dan MESEJ yang hendak disampaikan."
        )
    )
    plan: Dict[str, Any] = {
        "generated_at": datetime.now(MYT).strftime("%Y-%m-%d %H:%M:%S"),
        "coalition": "PAS · PN · MN (Muafakat Nasional)",
        "focus": "Negeri Sembilan" if focus_n9 else "Johor + Negeri Sembilan",
        "purpose": purpose,
        "tone_rules": [
            "Fokus perkhidmatan, ekonomi, kestabilan — bukan teologi atau agama.",
            "Jangan ulang isu syurga/Harakat — gunakan media Cina sebagai semakan fakta.",
            "Jawab kebimbangan 巫伊/MN dengan ketelusan: stabil negeri, bukan pakatan sulit.",
            "Setiap asset utama: BM + 中文 (Cina) dan/atau Tamil (India).",
            "Elak serangan perkauman; serang prestasi & penyelesaian konkrit.",
        ],
        "do_not_do": (brief or {}).get("do_not_do", [
            "Debat agama/syurga dengan komuniti Cina",
            "Biarkan DAP frame 'PAS-BN rahsia' tanpa jawapan",
            "Campur isu antarabangsa dalam messaging",
        ]),
        "coalition_priorities": (brief or {}).get("coalition_priorities", []),
        "executive_summary": (brief or {}).get("executive_summary_ms", ""),
        "n9": {
            "priority_actions": _n9_priority_actions(),
            "dun_matrix": _build_dun_matrix("Negeri Sembilan"),
            "stats_note": _stats_note(analytics, "N9"),
        },
        "filter_stats": {
            "filtered_rows": (analytics or {}).get("filtered_rows"),
            "raw_rows": (analytics or {}).get("raw_rows"),
        },
    }
    if not focus_n9:
        plan["johor"] = {
            "priority_actions": _johor_priority_actions(),
            "dun_matrix": _build_dun_matrix("Johor"),
            "stats_note": _stats_note(analytics, "Johor"),
        }
    return plan


def _stats_note(analytics: Optional[Dict[str, Any]], key: str) -> str:
    if not analytics:
        return ""
    st = analytics.get("states", {}).get(key, {})
    ch = st.get("chinese", {})
    ind = st.get("indian", {})
    return (
        f"Data tapis: Cina {ch.get('posts', 0)} posts ({ch.get('neg_pct', 0)}% negatif); "
        f"India {ind.get('posts', 0)} posts ({ind.get('neg_pct', 0)}% negatif)."
    )


def save_action_plan(plan: Dict[str, Any]) -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / "naratif_cadangan_tindakan.json"
    path.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
