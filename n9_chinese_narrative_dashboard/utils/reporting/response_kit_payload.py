"""Kit Respons Naratif — isu → platform → copy → naratif balas."""
from __future__ import annotations

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from utils.reporting.executive_payload import _action_board, _top5_issues
from utils.reporting.labels import (
    CLASSIFICATION,
    ISSUE_BM,
    ORG_NAME,
    REPORT_VERSION,
    UNCLASSIFIED,
    normalize_issue,
)

ROOT = Path(__file__).resolve().parents[2]
PLAYBOOK_PATH = ROOT / "config" / "narrative_playbook.csv"

BM_TO_EN = {v: k for k, v in ISSUE_BM.items()}

PLATFORM_GUIDANCE: dict[str, dict[str, str]] = {
    "Chinese online media": {
        "format": "Nota media / repost komuniti dengan infografik BM–中文",
        "timing": "Pagi 9–11 pagi atau petang 4–6 petang",
        "audience": "Pembaca media Cina & forward WhatsApp",
        "tip": "Edar melalui halaman komuniti Cina NS; elak kempen overtone",
    },
    "Facebook": {
        "format": "Post + infografik (BM + Mandarin dalam imej)",
        "timing": "7–9 malam hari bekerja",
        "audience": "Komuniti tempatan 35+",
        "tip": "Pin post 24 jam; balas komen dengan FAQ ringkas",
    },
    "Community pages": {
        "format": "Post informatif + pautan helaian rasmi",
        "timing": "Petang",
        "audience": "Kumpulan kejiranan / persatuan",
        "tip": "Minta admin kongsi; jangan spam banyak group serentak",
    },
    "Instagram": {
        "format": "Carousel 3–5 slide (fakta + CTA hubungi)",
        "timing": "8–10 malam",
        "audience": "Belia & pekerja bandar",
        "tip": "Visual ringkas; pautan Link in bio ke helaian penuh",
    },
    "TikTok": {
        "format": "Video 30–45 saat (calon/pegawai terangkan bantuan)",
        "timing": "12–2 tengah hari atau 8–10 malam",
        "audience": "Undi18 & belia",
        "tip": "Elak debat politik emosi; fokus isu harian sahaja",
    },
    "YouTube": {
        "format": "Video penerangan 2–3 minit atau live singkat",
        "timing": "Hujung minggu petang",
        "audience": "Pengundi sedia maklumat mendalam",
        "tip": "Sesuai isu pendidikan / dasar; kurang sesuai isu sensitif",
    },
    "X": {
        "format": "Thread 3–5 tweet + pautan bukti",
        "timing": "Pagi berita aktif",
        "audience": "Media & opinion leader",
        "tip": "Fakta ringkas; elak balas provokasi",
    },
    "news": {
        "format": "Kenyataan media / press release",
        "timing": "Sebelum 12 tengah hari",
        "audience": "Media mainstream",
        "tip": "Hanya selepas fakta disahkan",
    },
}

COPY_BM: dict[str, dict[str, str]] = {
    "Cost of Living": {
        "short": (
            "Kerajaan Negeri Sembilan sedar kos sara hidup menjadi kebimbangan komuniti di {loc}. "
            "Senarai bantuan aktif (negeri + persekutuan), syarat kelayakan dan nombor pegawai "
            "disediakan dalam helaian BM–Mandarin. Maklumat disahkan agensi berkaitan."
        ),
        "long": (
            "Kenyataan — Kos Sara Hidup ({loc})\n\n"
            "Kami merakam kebimbangan awam berkaitan harga barang dan kemampuan isi rumah. "
            "Pasukan dasar negeri sedang mengemaskini senarai bantuan yang masih aktif termasuk "
            "syarat permohonan, pautan rasmi dan saluran aduan.\n\n"
            "Helaian BM–Mandarin akan diedar melalui saluran komuniti dalam 24–48 jam. "
            "Maklumat yang belum disahkan tidak akan dikongsi sebagai fakta."
        ),
    },
    "SME and Business": {
        "short": (
            "Aduan peniaga kecil di {loc} berkaitan maklumat bantuan dan promosi perniagaan "
            "tempatan dirakam. Infografik BM–Mandarin (syarat, pautan mohon, pegawai hubungi) "
            "akan disediakan dalam 24 jam."
        ),
        "long": (
            "Kenyataan — SME & Perniagaan ({loc})\n\n"
            "Kerajaan negeri mengambil serius maklum balas peniaga kecil dan PKS. "
            "Pasukan ekonomi negeri sedang mengesahkan bantuan aktif, geran dan saluran "
            "penyelesaian aduan lesen/perniagaan.\n\n"
            "Satu infografik BM–Mandarin dan FAQ akan diedar kepada persatuan peniaga dan "
            "halaman komuniti setempat."
        ),
    },
    "Chinese Education": {
        "short": (
            "Isu peruntukan dan dasar pendidikan Cina di {loc} dirakam. "
            "Nota fakta rasmi (peruntukan, projek, timeline) sedang disediakan BM–Mandarin "
            "selepas pengesahan agensi pendidikan."
        ),
        "long": (
            "Kenyataan — Pendidikan Cina ({loc})\n\n"
            "Kerajaan negeri komited kepada pendidikan Cina. Pasukan dasar sedang menyediakan "
            "nota fakta berdasarkan rekod peruntukan dan projek yang boleh disahkan.\n\n"
            "Sesi dialog komuniti akan dipertimbangkan jika diperlukan selepas semakan fakta."
        ),
    },
    "Local Government Services": {
        "short": (
            "Aduan perkhidmatan tempatan di {loc} dirakam. "
            "Pasukan operasi tempatan sedang menyemak status tindakan dan garis masa pembaikan."
        ),
        "long": (
            "Kemas Kini Perkhidmatan — {loc}\n\n"
            "Kerajaan tempatan sedang menyemak aduan yang dibangkitkan. "
            "Kemas kini status dan garis masa akan dikongsi apabila disahkan agensi berkaitan."
        ),
    },
    "DAP Performance": {
        "short": (
            "Prestasi pentadbiran dan perkhidmatan di {loc} menjadi perbincangan komuniti. "
            "Kami fokus kepada bukti deliverable — bukan slogan — dan akan kongsi tiga "
            "keputusan konkrit yang telah/sedang dilaksanakan."
        ),
        "long": (
            "Penjelasan — Prestasi Pentadbiran ({loc})\n\n"
            "Komuniti Cina menyuarakan pelbagai pandangan. Kedudukan rasmi: "
            "kerajaan negeri akan terus memberi perkhidmatan berdasarkan bukti dan rekod. "
            "Tiga contoh tindakan konkrit di {loc} akan dikongsi dalam format BM–Mandarin."
        ),
    },
    "PAS Factor": {
        "short": (
            "Kebimbangan komuniti berkaitan kestabilan dirakam. "
            "Kerajaan negeri menegaskan komitmen kepada pentadbiran stabil, perkhidmatan harian "
            "dan perpaduan — berdasarkan rekod, bukan spekulasi."
        ),
        "long": (
            "Penjelasan — Kestabilan & Perkhidmatan ({loc})\n\n"
            "Kami faham kebimbangan awam. Respons kami: fakta pentadbiran negeri, "
            "perkhidmatan harian dan rekod kestabilan — bukan debat sensitif agama/kaum."
        ),
    },
    "PH-BN Relationship": {
        "short": (
            "Perbincangan koalisi di {loc} dirakam. "
            "Satu mesej rasmi koalisi (BM–Mandarin) akan diselaraskan dan diedar "
            "supaya semua calon menggunakan naratif yang konsisten."
        ),
        "long": (
            "Penjelasan — Koalisi ({loc})\n\n"
            "Kerajaan negeri menegaskan kestabilan koalisi dan fokus perkhidmatan rakyat. "
            "Mesej rasmi akan diselaraskan Communications + Management sebelum edaran."
        ),
    },
    "Race and Religion": {
        "short": (
            "Naratif sensitif dirakam. Tiada respons serta-merta tanpa semakan fakta "
            "(min. 2 sumber). Kelulusan Legal/Management wajib sebelum sebarang kenyataan."
        ),
        "long": (
            "NOTA DALAMAN — Isu Sensitif ({loc})\n\n"
            "JANGAN respons emosi. Wajib: Fact Checking → Legal Review → Management. "
            "Hanya pembetulan berasaskan bukti; elak serangan peribadi atau kaum."
        ),
    },
    "Misinformation": {
        "short": (
            "Dakwaan belum disahkan dirakam. Jangan kongsi atau balas sebelum "
            "Fact Checking mengesahkan. Pembetulan fakta sahaja selepas bukti lengkap."
        ),
        "long": (
            "NOTA FACT CHECK — {loc}\n\n"
            "Dakwaan memerlukan pengesahan min. 2 sumber bebas. "
            "Pembetulan akan menggunakan format 'Fakta Disahkan' vs 'Dakwaan Belum Disahkan'."
        ),
    },
}

COPY_ZH: dict[str, dict[str, str]] = {
    "Cost of Living": {
        "short": (
            "{loc}地区华人社区关注生活费问题。森州政府已整理目前可申请的实际援助清单、"
            "申请条件及联络方式（国文与华文版本）。资料经相关机构核实，供社区参考。"
        ),
        "long": (
            "声明——生活费（{loc}）\n\n"
            "我们重视社区对生活成本的关切。州政府团队正在更新各项援助计划、"
            "申请资格及官方查询渠道。国文与华文资料将在24–48小时内通过社区渠道发布。"
            "未经核实的信息不会当作事实传播。"
        ),
    },
    "SME and Business": {
        "short": (
            "我们收到{loc}小贩及中小企业对援助资讯不清晰的反馈。"
            "州政府将发布国文与华文信息图，列明申请条件、链接及联络方式。"
        ),
        "long": (
            "声明——中小企业（{loc}）\n\n"
            "州政府重视商家意见，正在核实各项援助与执照资讯。"
            "信息图与常见问题解答将通过社区及商团渠道发布。"
        ),
    },
    "Chinese Education": {
        "short": (
            "华社关注独中拨款及华文教育政策（{loc}）。"
            "官方说明文件（国文与华文）正在核实中，将以事实与数据为依据。"
        ),
        "long": (
            "声明——华文教育（{loc}）\n\n"
            "州政府持续支持华文教育。我们将发布经核实的拨款与项目时间表，"
            "必要时安排社区对话。"
        ),
    },
    "Local Government Services": {
        "short": "{loc}地方服务投诉已记录。相关部门正在核实处理进度及预计完成时间。",
        "long": "服务更新——{loc}\n\n地方政府正在跟进投诉，核实后将公布处理状态。",
    },
    "DAP Performance": {
        "short": (
            "{loc}地区讨论州政府表现。我们将以三项具体成果（非口号）回应社区，"
            "国文与华文同步发布。"
        ),
        "long": "说明——行政表现（{loc}）\n\n我们将以可核实的施政记录回应，避免人身攻击或空泛承诺。",
    },
    "PAS Factor": {
        "short": "我们理解社区对稳定的关注。州政府强调以施政记录与日常服务回应，不进行宗教或种族辩论。",
        "long": "说明——稳定与施政\n\n以事实与公共服务记录回应，避免煽动性言论。",
    },
    "PH-BN Relationship": {
        "short": "联盟相关讨论已记录。官方信息将统一口径后发布（国文与华文）。",
        "long": "说明——联盟稳定\n\n强调施政稳定与服务人民，信息经Communications及管理层协调后发布。",
    },
    "Race and Religion": {
        "short": "敏感议题——暂缓对外回应，须完成事实核查及Legal/Management批准。",
        "long": "内部通知——敏感议题\n\n禁止情绪化回应。须Fact Checking → Legal → Management。",
    },
    "Misinformation": {
        "short": "未经核实的说法请勿转发。事实核查完成后才发布更正。",
        "long": "事实核查说明\n\n至少两个独立来源核实后，才发布「已核实事实」与「未核实说法」对比。",
    },
}

COUNTER_DEFAULT = {
    "dont": "Jangan salahkan mana-mana kaum, agama atau kumpulan; jangan janji tanpa bukti; jangan serang individu.",
    "tone": "Tenang · berasaskan bukti · orientasi tindakan",
}

# Langkah + copy balas komen + variasi pos mengikut platform
COUNTER_PLAN: dict[str, dict[str, Any]] = {
    "Cost of Living": {
        "steps": [
            "Sahkan senarai bantuan aktif (negeri + persekutuan) dengan agensi — siapkan helaian BM–中文.",
            "Pos infografik di Facebook & halaman komuniti {loc} (7–9 malam); pin 24 jam.",
            "Edar helaian ke admin media Cina / WhatsApp persatuan peniaga untuk forward.",
            "Balas komen negatif dengan pautan helaian + nombor pegawai (jangan debat panjang).",
            "Pantau sentimen 24–72 jam; rekod bilangan pertanyaan/hotline.",
        ],
        "reply_bm": (
            "Terima kasih maklum balas. Senarai bantuan kos sara hidup yang masih aktif untuk {loc} "
            "telah dikemaskini (BM–Mandarin): [pautan helaian]. Syarat kelayakan & nombor pegawai "
            "tertera di helaian. Sila hubungi talian rasmi jika perlu bantuan permohonan."
        ),
        "reply_zh": (
            "感谢您的反馈。{loc}地区生活费援助清单（国文与华文）已更新：[链接]。"
            "申请条件及联络方式见单张。如需协助申请请致电官方热线。"
        ),
        "post_facebook": (
            "📋 Bantuan Kos Sara Hidup {loc} — Senarai Terkini (BM–中文)\n\n"
            "Kerajaan Negeri Sembilan sedar isu harga barang & beban isi rumah. "
            "Helaian ini senaraikan bantuan AKTIF, syarat kelayakan, cara mohon & nombor pegawai.\n\n"
            "🔗 [pautan] | 📞 [hotline]\n#NegeriSembilan #生活费"
        ),
        "post_community": (
            "Perkongsian untuk komuniti {loc}: helaian bantuan kos sara hidup (BM–Mandarin) "
            "disahkan agensi. Sila kongsi dalam group ahli keluarga & jiran. [pautan]"
        ),
        "post_media_chinese": (
            "供媒体/社区转载：森州{loc}生活费援助清单已核实更新（国文与华文版）。"
            "含申请资格、官方链接及联络方式。[链接]"
        ),
    },
    "SME and Business": {
        "steps": [
            "Semak bantuan PKS/SME aktif + nombor pegawai MBNS/ekonomi negeri.",
            "Hasilkan infografik BM–中文 (syarat, QR pautan mohon, 3 langkah permohonan).",
            "Pos di Facebook halaman {loc} + hantar kepada persatuan peniaga Cina tempatan.",
            "Forward infografik ke WhatsApp group hawker associations (minta admin kongsi).",
            "Balas aduan enforcement PBT dengan status semakan + saluran aduan rasmi.",
        ],
        "reply_bm": (
            "Kami faham kebimbangan peniaga di {loc}. Infografik bantuan SME/PKS (BM–Mandarin) "
            "disertakan: [pautan]. Termasuk syarat, pautan permohonan & pegawai hubungi. "
            "Untuk isu PBT/enforcement, sila emel/WhatsApp [saluran aduan]."
        ),
        "reply_zh": (
            "我们理解{loc}商家关切。中小企业援助信息图（国文与华文）:[链接]。"
            "含申请条件与联络方式。市议会执法投诉请联络：[渠道]。"
        ),
        "post_facebook": (
            "🏪 Bantuan Peniaga & PKS — {loc}\n\n"
            "Infografik BM–中文: bantuan aktif, cara mohon, nombor pegawai ekonomi negeri.\n"
            "🔗 [pautan] #森州 #马口"
        ),
        "post_community": (
            "Peniaga {loc}: infografik bantuan SME (BM–中文) — sila simpan & kongsi. [pautan]"
        ),
        "post_media_chinese": (
            "{loc}小贩及中小企业援助资讯（国文与华文信息图）已发布，欢迎社区转载。[链接]"
        ),
    },
    "Chinese Education": {
        "steps": [
            "Kumpul data peruntukan sekolah Cina (disahkan agensi pendidikan).",
            "Sediakan nota fakta BM–中文 (angka, projek, timeline — bukan janji baru).",
            "Pos carousel Instagram/Facebook; edar ke media Cina & persatuan PTA.",
            "Jika perlu, jadual sesi dialog FB Live 30 minit dengan calon/ADUN.",
            "Elak debat 'parti vs parti' — fokus fakta peruntukan sahaja.",
        ],
        "reply_bm": (
            "Terima kasih. Nota fakta peruntukan pendidikan Cina (BM–Mandarin) untuk {loc}: [pautan]. "
            "Angka & projek berdasarkan rekod rasmi. Sesi dialog akan diumumkan jika diperlukan."
        ),
        "reply_zh": (
            "感谢关注。{loc}华文教育拨款事实说明（国文与华文）:[链接]。"
            "数据来自官方记录。如需对话会另行通知。"
        ),
        "post_facebook": (
            "📚 Pendidikan Cina {loc} — Nota Fakta Rasmi (BM–中文)\n"
            "Peruntukan · projek · timeline (disahkan)\n🔗 [pautan] #华文教育"
        ),
        "post_community": "Nota fakta pendidikan Cina {loc} (BM–中文) untuk ibu bapa & PTA. [pautan]",
        "post_media_chinese": "森州{loc}华文教育拨款官方说明（国文与华文）供社区参考。[链接]",
    },
    "Local Government Services": {
        "steps": [
            "Semak status aduan dengan PBT/agensi; dapatkan tarikh siap yang boleh diumumkan.",
            "Pos kemas kini perkhidmatan di Facebook group {loc}.",
            "Balas setiap komen aduan dengan nombor rujukan + status (jika ada).",
            "Edar ke community pages setempat.",
        ],
        "reply_bm": (
            "Aduan {loc} dirakam. Status semakan: [status]. Rujukan: [no]. "
            "Tarikh siap dijangka: [tarikh] (jika disahkan). Hubungi: [hotline PBT]."
        ),
        "reply_zh": "您的{loc}投诉已记录。处理状态：[status]。联络：[hotline]。",
        "post_facebook": "📢 Kemas Kini Perkhidmatan {loc}\nStatus aduan & saluran hubungi: [pautan/hotline]",
        "post_community": "Kemas kini perkhidmatan tempatan {loc}. [butiran]",
        "post_media_chinese": "{loc}地方服务更新（国文与华文）。[链接]",
    },
    "DAP Performance": {
        "steps": [
            "Kenal pasti 3 bukti deliverable di {loc} (projek siap / peruntukan / perkhidmatan).",
            "Pos '3 Fakta' carousel BM–中文 — bukan serangan calon lawan.",
            "Edar melalui Facebook + media Cina; elak TikTok debat emosi.",
            "Balas naratif negatif dengan fakta spesifik + gambar/bukti.",
        ],
        "reply_bm": (
            "Terima kasih pandangan. Tiga tindakan konkrit di {loc}: (1) [fakta] (2) [fakta] (3) [fakta]. "
            "Butiran: [pautan]. Kami fokus perkhidmatan, bukan politik divisif."
        ),
        "reply_zh": "感谢意见。{loc}三项具体成果：(1)[事实](2)[事实](3)[事实]。详情：[链接]",
        "post_facebook": "✅ 3 Fakta — Perkhidmatan {loc} (BM–中文)\n1. … 2. … 3. …\n🔗 [pautan]",
        "post_community": "3 bukti deliverable {loc} untuk rujukan komuniti. [pautan]",
        "post_media_chinese": "{loc}施政三项具体成果说明（国文与华文）。[链接]",
    },
    "PAS Factor": {
        "steps": [
            "Jangan amplify ketakutan — elak tajuk sensasi.",
            "Pos mesej kestabilan + rekod perkhidmatan negeri (BM–中文).",
            "Platform: Facebook & YouTube (panjang), bukan X debat.",
            "Balas dengan fakta pentadbiran, bukan debat agama.",
        ],
        "reply_bm": (
            "Kerajaan Negeri Sembilan komited kepada kestabilan & perkhidmatan harian di {loc}. "
            "Rekod pentadbiran: [pautan nota fakta]. Kami fokus selesaikan isu rakyat."
        ),
        "reply_zh": "森州政府致力于{loc}地区稳定与日常施政。施政记录：[链接]。我们聚焦民生。",
        "post_facebook": "🏛️ Kestabilan & Perkhidmatan Negeri Sembilan — {loc}\nFakta pentadbiran (BM–中文): [pautan]",
        "post_community": "Mesej kestabilan & perkhidmatan {loc}. [pautan]",
        "post_media_chinese": "森州{loc}施政稳定与服务说明（国文与华文）。[链接]",
    },
    "PH-BN Relationship": {
        "steps": [
            "Selaraskan satu mesej koalisi (BM–中文) — semua calon guna naratif sama.",
            "Pos serentak Facebook calon + page rasmi negeri.",
            "Elak perbezaan mesej antara calon.",
        ],
        "reply_bm": "Mesej rasmi koalisi negeri: fokus perkhidmatan & kestabilan {loc}. [pautan kenyataan]",
        "reply_zh": "州政府联盟官方信息：聚焦{loc}民生与稳定。[链接]",
        "post_facebook": "🤝 Mesej Koalisi Negeri Sembilan — {loc} (BM–中文)\n[pautan]",
        "post_community": "Mesej rasmi koalisi untuk {loc}. [pautan]",
        "post_media_chinese": "森州{loc}联盟官方说明（国文与华文）。[链接]",
    },
}

DEFAULT_COUNTER = {
    "steps": [
        "Sahkan fakta isu dengan agensi berkaitan.",
        "Sediakan nota/helaian BM–中文.",
        "Pos di Facebook & halaman komuniti {loc} (petang).",
        "Balas komen dengan pautan rasmi — jangan debat emosi.",
        "Pantau sentimen 48 jam.",
    ],
    "reply_bm": "Terima kasih maklum balas berkaitan {issue} di {loc}. Maklumat rasmi: [pautan]. Hubungi: [hotline].",
    "reply_zh": "感谢有关{loc}{issue}的反馈。官方信息：[链接]。",
    "post_facebook": "📢 {issue} — {loc}\nMaklumat rasmi (BM–中文): [pautan]",
    "post_community": "Kongsi komuniti {loc}: maklumat {issue}. [pautan]",
    "post_media_chinese": "{loc}{issue}官方信息（国文与华文）。[链接]",
}

POLITICAL_ISSUES = {
    "DAP Performance", "MCA Relevance", "PAS Factor", "PH-BN Relationship",
    "Gerakan and PN", "Candidate Performance", "Race and Religion",
}


def _load_playbook() -> pd.DataFrame:
    if PLAYBOOK_PATH.exists():
        return pd.read_csv(PLAYBOOK_PATH)
    return pd.DataFrame()


def _playbook_row(issue_en: str, pb: pd.DataFrame) -> dict[str, str]:
    if pb.empty:
        return {}
    ic = issue_en
    if ic in POLITICAL_ISSUES:
        match = pb[pb["issue_cluster"] == "Political Party Narratives"]
        if not match.empty:
            return match.iloc[0].to_dict()
    match = pb[pb["issue_cluster"].astype(str) == ic]
    if match.empty and ic == "Misinformation":
        match = pb[pb["issue_cluster"] == "Misinformation"]
    if match.empty:
        return {}
    return match.iloc[0].to_dict()


def _issue_en(issue_bm: str, issue_key: str) -> str:
    return BM_TO_EN.get(issue_bm) or BM_TO_EN.get(issue_key) or issue_key


def _loc_from_action(action: dict, sub: pd.DataFrame, issue_en: str) -> str:
    loc = action.get("issue_location", "").split("—")[-1].strip() if "—" in action.get("issue_location", "") else "Negeri Sembilan"
    if loc in ("—", "", "nan"):
        if not sub.empty and "constituency" in sub.columns:
            grp = sub[sub["issue_cluster"].astype(str) == issue_en] if issue_en in sub["issue_cluster"].astype(str).values else sub
            if not grp.empty:
                vc = grp["constituency"].astype(str).value_counts()
                loc = str(vc.index[0]) if len(vc) else "Negeri Sembilan"
        else:
            loc = "Negeri Sembilan"
    return loc


def _platform_recommendations(sub: pd.DataFrame, issue_en: str, top_n: int = 3) -> list[dict[str, Any]]:
    grp = sub[sub["issue_cluster"].astype(str) == issue_en] if issue_en and "issue_cluster" in sub.columns else sub
    if grp.empty:
        grp = sub
    if grp.empty or "platform" not in grp.columns:
        defaults = ["Facebook", "Chinese online media", "Community pages"]
        return [_platform_entry(p, 0, len(defaults)) for p in defaults[:top_n]]

    vc = grp["platform"].astype(str).value_counts()
    total = max(len(grp), 1)
    out = []
    for plat, cnt in vc.head(top_n).items():
        out.append(_platform_entry(str(plat), cnt, total))
    if len(out) < top_n:
        for p in ["Facebook", "Chinese online media"]:
            if p not in [x["platform"] for x in out]:
                out.append(_platform_entry(p, 0, total))
            if len(out) >= top_n:
                break
    return out[:top_n]


def _platform_entry(platform: str, count: int, total: int) -> dict[str, Any]:
    g = PLATFORM_GUIDANCE.get(platform, {
        "format": "Post informatif + pautan rasmi",
        "timing": "Petang",
        "audience": "Komuniti tempatan",
        "tip": "Pastikan fakta disahkan sebelum pos",
    })
    pct = round(count / total * 100, 1) if count else 0
    return {
        "platform": platform,
        "data_share_pct": pct,
        "format": g["format"],
        "timing": g["timing"],
        "audience": g["audience"],
        "tip": g["tip"],
    }


def _review_level(issue_en: str, pb_row: dict) -> str:
    level = str(pb_row.get("review_level", "Normal") or "Normal")
    if issue_en in ("Race and Religion", "Misinformation"):
        return "Critical"
    if issue_en in POLITICAL_ISSUES:
        return "High" if level == "Normal" else level
    return level if level in ("Normal", "High", "Critical") else "Normal"


def _fmt(text: str, **kwargs) -> str:
    try:
        return text.format(**kwargs)
    except (KeyError, ValueError):
        return text


def _platform_post_key(platform: str) -> str:
    p = platform.lower()
    if "facebook" in p:
        return "post_facebook"
    if "chinese" in p or "media" in p:
        return "post_media_chinese"
    if "community" in p:
        return "post_community"
    if "instagram" in p:
        return "post_facebook"
    if "tiktok" in p:
        return "post_facebook"
    return "post_community"


def _build_counter_plan(
    issue_en: str,
    issue_bm: str,
    loc: str,
    platforms: list[dict],
    pb_row: dict,
    review_level: str,
) -> dict[str, Any]:
    plan = COUNTER_PLAN.get(issue_en, DEFAULT_COUNTER)
    loc = loc or "Negeri Sembilan"
    issue = issue_bm or normalize_issue(issue_en)

    steps = [_fmt(s, loc=loc, issue=issue) for s in plan.get("steps", DEFAULT_COUNTER["steps"])]
    reply_bm = _fmt(plan.get("reply_bm", DEFAULT_COUNTER["reply_bm"]), loc=loc, issue=issue)
    reply_zh = _fmt(plan.get("reply_zh", DEFAULT_COUNTER["reply_zh"]), loc=loc, issue=issue)

    prohibited = str(pb_row.get("prohibited_approach", "") or "")
    dont = prohibited if prohibited and prohibited != "nan" else COUNTER_DEFAULT["dont"]
    if review_level == "Critical" or issue_en in ("Race and Religion", "Misinformation"):
        steps = [
            "JANGAN pos segera — wajib fact check (min. 2 sumber).",
            "Sediakan grafik 'Fakta Disahkan vs Dakwaan' BM–中文.",
            "Hantar pembetulan ke platform asal + media Cina (bukan serangan balik).",
            "Elak saluran TikTok/X untuk isu sensitif.",
        ]
        reply_bm = (
            "Terima kasih. Dakwaan ini sedang disemak. Hanya maklumat disahkan akan dikongsi. "
            "Pembetulan rasmi akan diterbitkan di [saluran rasmi] selepas semakan selesai."
        )
        reply_zh = "感谢关注。相关内容正在核实，仅发布经确认的信息。更正声明将稍后发布。"

    platform_posts: list[dict[str, str]] = []
    for plat in platforms:
        key = _platform_post_key(plat.get("platform", ""))
        raw = plan.get(key) or plan.get("post_facebook") or DEFAULT_COUNTER.get(key, "")
        copy = _fmt(str(raw), loc=loc, issue=issue)
        platform_posts.append({
            "platform": plat.get("platform", ""),
            "timing": plat.get("timing", ""),
            "format": plat.get("format", ""),
            "data_share_pct": str(plat.get("data_share_pct", 0)),
            "copy": copy,
        })

    return {
        "steps": steps,
        "reply_comment_bm": reply_bm,
        "reply_comment_zh": reply_zh,
        "platform_posts": platform_posts,
        "dont": dont,
        "tone": COUNTER_DEFAULT["tone"],
    }


def _copy_for_issue(issue_en: str, loc: str, narrative: str, action: str) -> dict[str, str]:
    loc = loc or "Negeri Sembilan"
    bm = COPY_BM.get(issue_en, {})
    zh = COPY_ZH.get(issue_en, {})
    short_bm = bm.get("short", draft_fallback_bm(issue_en, loc, action)).format(loc=loc)
    long_bm = bm.get("long", short_bm).format(loc=loc)
    short_zh = zh.get("short", "（华文版本请经Communications审核后发布）").format(loc=loc)
    long_zh = zh.get("long", short_zh).format(loc=loc)
    if narrative and len(narrative) > 20:
        long_bm = f"{long_bm}\n\nNaratif diperhatikan: {narrative[:180]}…"
    return {
        "copy_bm_short": short_bm,
        "copy_bm_long": long_bm,
        "copy_zh_short": short_zh,
        "copy_zh_long": long_zh,
        "hashtags": _hashtags(loc, issue_en),
    }


def draft_fallback_bm(issue_en: str, loc: str, action: str) -> str:
    issue_bm = normalize_issue(issue_en)
    return (
        f"Kerajaan Negeri Sembilan sedar kebimbangan berkaitan {issue_bm} di {loc}. "
        f"{action or 'Pasukan berkaitan sedang menyemak maklumat.'} "
        "Maklumat rasmi akan dikemas kini apabila fakta disahkan."
    )


def _hashtags(loc: str, issue_en: str) -> list[str]:
    tags = ["#PRN2026", "#NegeriSembilan", "#森州"]
    loc_tags = {
        "Seremban": "#芙蓉", "Bahau": "#马口", "Nilai": "#汝来",
        "Port Dickson": "#波德申", "Jempol": "#仁保",
    }
    for k, v in loc_tags.items():
        if k.lower() in loc.lower():
            tags.append(v)
            break
    if issue_en == "Cost of Living":
        tags.append("#生活费")
    elif issue_en == "Chinese Education":
        tags.append("#华文教育")
    return tags[:5]


def _source_for_issue(sub: pd.DataFrame, issue_en: str) -> dict[str, str]:
    if sub.empty or "issue_cluster" not in sub.columns:
        return {"url": "—", "platform": "—", "text": "—"}
    grp = sub[sub["issue_cluster"].astype(str) == issue_en]
    if grp.empty:
        grp = sub
    if "engagement_total" in grp.columns:
        row = grp.nlargest(1, "engagement_total").iloc[0]
    else:
        row = grp.iloc[0]
    url = str(row.get("source_url") or row.get("post_url") or "—")
    if "example.com" in url:
        url = url + " (sampel — ganti dengan URL crawl sebenar)"
    return {
        "url": url,
        "platform": str(row.get("platform", "—")),
        "text": str(row.get("post_text", row.get("translated_text_bm", "")))[:200],
    }


def _maybe_llm_enhance(item: dict, sub: pd.DataFrame) -> dict[str, str]:
    """Optional LLM copy polish using playbook + post context (fallback: unchanged)."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return {}
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        ctx = {
            "issue": item.get("issue"),
            "location": item.get("location"),
            "narrative": item.get("narrative_summary"),
            "platforms": [p["platform"] for p in item.get("platforms", [])],
        }
        prompt = f"""Anda penulis komunikasi PRN Negeri Sembilan (komuniti Cina).
Context: {json.dumps(ctx, ensure_ascii=False)[:2500]}

Hasilkan JSON sahaja dengan keys:
copy_bm_short, copy_zh_short, copy_bm_social, copy_zh_social,
reply_comment_bm (balas komen FB, max 250 aksara),
reply_comment_zh (balas komen, max 250 aksara),
post_facebook (post FB penuh, max 400 aksara BM).

Peraturan: bukan polling; jangan serang kaum/agama; orientasi tindakan konkrit."""
        resp = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[{"role": "user", "content": prompt}],
            temperature=0.35,
            max_tokens=900,
        )
        text = resp.choices[0].message.content or ""
        m = re.search(r"\{.*\}", text, re.S)
        if m:
            return json.loads(m.group())
    except Exception:
        pass
    return {}


def _kit_item(
    action: dict,
    sub: pd.DataFrame,
    pb: pd.DataFrame,
    idx: int,
) -> dict[str, Any]:
    issue_bm = action.get("issue_key") or action.get("issue_location", "").split("—")[0].strip()
    issue_en = _issue_en(issue_bm, issue_bm)
    loc = _loc_from_action(action, sub, issue_en)
    pb_row = _playbook_row(issue_en, pb)
    review_level = _review_level(issue_en, pb_row)

    platforms = _platform_recommendations(sub, issue_en)
    counter_plan = _build_counter_plan(issue_en, issue_bm, loc, platforms, pb_row, review_level)
    copies = _copy_for_issue(issue_en, loc, action.get("what_happened", ""), action.get("action", ""))
    source = _source_for_issue(sub, issue_en)

    item = {
        "rank": idx,
        "priority": action.get("priority", "P2 — Dalam 48 Jam"),
        "issue": issue_bm,
        "issue_en": issue_en,
        "location": loc,
        "narrative_summary": action.get("what_happened") or action.get("action", "")[:200],
        "operational_action": action.get("action", ""),
        "output": action.get("output", ""),
        "kpi": action.get("kpi", ""),
        "platforms": platforms,
        "copy_bm_short": copies["copy_bm_short"],
        "copy_bm_long": copies["copy_bm_long"],
        "copy_zh_short": copies["copy_zh_short"],
        "copy_zh_long": copies["copy_zh_long"],
        "copy_bm_social": copies["copy_bm_short"],
        "copy_zh_social": copies["copy_zh_short"],
        "hashtags": copies["hashtags"],
        "counter_plan": counter_plan,
        "source": source,
        "copy_source": "template+playbook",
    }
    llm = _maybe_llm_enhance(item, sub)
    if llm:
        for k, v in llm.items():
            if v and k.startswith("copy_"):
                item[k] = v
            elif v and k.startswith("reply_comment"):
                item["counter_plan"][k] = v
            elif v and k == "post_facebook" and item["counter_plan"].get("platform_posts"):
                item["counter_plan"]["platform_posts"][0]["copy"] = v
        item["copy_source"] = "llm+playbook"
    return item


def build_response_kit_payload(
    df: pd.DataFrame,
    state: str,
    meta: dict[str, str],
) -> dict[str, Any]:
    sub = df[df["state"].astype(str) == state].copy() if "state" in df.columns else df.copy()
    ts = datetime.now()
    pb = _load_playbook()
    top5 = _top5_issues(sub)
    actions = _action_board(sub, top5)
    items = [_kit_item(a, sub, pb, i + 1) for i, a in enumerate(actions[:6])]

    return {
        "report_type": "response_kit",
        "version": REPORT_VERSION,
        "classification": CLASSIFICATION,
        "org": ORG_NAME,
        "state": state,
        "state_short": meta.get("short", ""),
        "title": "Kit Respons Naratif",
        "subtitle": f"Pemantauan Naratif Berbahasa Cina — PRN {state}",
        "tagline": "Apa isu → Pos di mana → Copy apa → Naratif balas",
        "generated_at": ts.strftime("%d %B %Y, %H:%M"),
        "generated_at_file": ts.strftime("%Y%m%d_%H%M%S"),
        "record_count": len(sub),
        "items": items,
        "workflow": [
            ("1. KESAN", "Kenal pasti isu P1/P2 dari crawl & laporan eksekutif."),
            ("2. FAHAMI", "Baca naratif asal, lokasi, platform dominan."),
            ("3. SAHKAN", "Fact check bukti; jangan pos tanpa kelulusan."),
            ("4. TINDAK", "Pos mengikut platform + copy BM/中文 yang diluluskan."),
            ("5. UKUR", "Pantau sentimen & interaksi 24–72 jam; tutup atau escalate."),
        ],
        "disclaimer": (
            "Semua copy adalah draf untuk semakan manusia sebelum pos. Bukan polling undi. "
            "Ganti [pautan], [hotline], [fakta] dengan maklumat disahkan."
        ),
    }
