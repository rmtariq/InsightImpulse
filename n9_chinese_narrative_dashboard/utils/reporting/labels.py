"""Bahasa Melayu labels and issue display names."""
from __future__ import annotations

REPORT_VERSION = "2.0"
CLASSIFICATION = "UNTUK KEGUNAAN DALAMAN"
ORG_NAME = "InsightPulse"

UNCLASSIFIED = "Belum Diklasifikasikan"
OTHER_ALIASES = {"other", "Other", "OTHER", "lain", "Lain"}

ISSUE_BM: dict[str, str] = {
    "Cost of Living": "Kos Sara Hidup",
    "Chinese Education": "Pendidikan Cina",
    "SME and Business": "SME dan Perniagaan",
    "Local Government Services": "Perkhidmatan Kerajaan Tempatan",
    "Water Supply": "Bekalan Air",
    "Road and Traffic": "Jalan dan Trafik",
    "Flood and Drainage": "Banjir dan Perparitan",
    "Public Safety": "Keselamatan Awam",
    "Employment": "Peluang Pekerjaan",
    "Housing": "Perumahan",
    "Economic Development": "Pembangunan Ekonomi",
    "DAP Performance": "Prestasi DAP",
    "MCA Relevance": "Relevansi MCA",
    "Gerakan and PN": "Gerakan dan PN",
    "PAS Factor": "Faktor PAS",
    "PH-BN Relationship": "Hubungan PH–BN",
    "Candidate Performance": "Prestasi Calon",
    "State Government Stability": "Kestabilan Kerajaan Negeri",
    "Youth and Undi18": "Belia dan Undi18",
    "Race and Religion": "Kaum dan Agama",
    "Misinformation": "Maklumat Salah Disyaki",
    UNCLASSIFIED: UNCLASSIFIED,
}

STATUS_META = {
    "HIJAU": {"label": "Stabil", "color": "#22c55e"},
    "KUNING": {"label": "Perlu Pemantauan", "color": "#eab308"},
    "JINGGA": {"label": "Perlu Tindakan", "color": "#f97316"},
    "MERAH": {"label": "Keutamaan Tinggi", "color": "#dc2626"},
}

PRIORITY_LABELS = {
    1: "P1 — Hari Ini",
    2: "P2 — Dalam 48 Jam",
    3: "P3 — Dalam 7 Hari",
    4: "Pantau",
}

TREND_LABELS = {
    "up": "Meningkat",
    "down": "Menurun",
    "stable": "Stabil",
    "insufficient": "Data Tidak Mencukupi",
}

EVIDENCE_BM = {
    "verified": "Disahkan",
    "partial": "Sebahagian Disahkan",
    "needs_more": "Perlu Bukti Tambahan",
    "unverified": "Belum Disahkan",
}

ACTION_STATUS_BM = {
    "Baharu": "Baharu",
    "Dalam Semakan": "Dalam Semakan",
    "Sedang Dilaksanakan": "Sedang Dilaksanakan",
    "Menunggu Kelulusan": "Menunggu Kelulusan",
    "Selesai": "Selesai",
    "Pantau Sahaja": "Pantau Sahaja",
}


def normalize_issue(raw: str) -> str:
    s = str(raw or "").strip()
    if not s or s.lower() in ("nan", "none") or s in OTHER_ALIASES:
        return UNCLASSIFIED
    return ISSUE_BM.get(s, s)


def is_unclassified(raw: str) -> bool:
    return normalize_issue(raw) == UNCLASSIFIED
