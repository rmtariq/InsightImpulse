"""Keyword-based issue cluster classifier for Chinese-language narratives."""
from __future__ import annotations

import re
from typing import Optional

ISSUE_CLUSTERS = [
    "Cost of Living",
    "Chinese Education",
    "Tamil Education",
    "SME and Business",
    "Local Government Services",
    "Water Supply",
    "Road and Traffic",
    "Flood and Drainage",
    "Public Safety",
    "Employment",
    "Healthcare",
    "Housing",
    "Economic Development",
    "DAP Performance",
    "MCA Relevance",
    "Gerakan and PN",
    "PAS Factor",
    "PH-BN Relationship",
    "Candidate Performance",
    "State Government Stability",
    "Youth and Undi18",
    "Race and Religion",
    "Misinformation",
    "Other",
]

# (cluster, keywords) — Chinese, Malay, English mixed
_KEYWORD_MAP: list[tuple[str, list[str]]] = [
    ("Cost of Living", ["物价", "生活费", "kos sara hidup", "harga barang", "cost of living", "通货膨胀", "விலைவாசி", "vilai vaasi", "selavu"]),
    ("Chinese Education", ["华校", "华小", "独中", "SJKC", "Chinese school", "华文教育", "董事会"]),
    ("Tamil Education", ["SJKT", "sekolah Tamil", "Tamil school", "guru Tamil", "Tamil teacher", "pendidikan Tamil", "தமிழ்ப்பள்ளி", "Tamil palli"]),
    ("SME and Business", ["商家", "小贩", "中小企业", "peniaga", "SME", "生意", "店铺"]),
    ("Local Government Services", ["市议会", "local council", "perkhidmatan awam", "垃圾", "停车位", "parking"]),
    ("Water Supply", ["水供", "断水", "water supply", "水务"]),
    ("Road and Traffic", ["塞车", "traffic", "道路", "交通", "停车位"]),
    ("Flood and Drainage", ["水灾", "淹水", "排水", "flood", "drainage"]),
    ("Public Safety", ["治安", "偷窃", "public safety", "keselamatan", "犯罪"]),
    ("Employment", ["就业", "工作", "employment", "pekerjaan", "失业", "velai", "வேலை", "pengangguran"]),
    ("Housing", ["房价", "housing", "perumahan", "可负担房屋", "PPR", "veedu", "sewa rumah"]),
    ("Economic Development", ["经济", "投资", "pelaburan", "economic development", "MIDA"]),
    ("DAP Performance", ["行动党", "DAP", "DAP Negeri Sembilan", "希盟表现"]),
    ("MCA Relevance", ["马华", "MCA", "MCA comeback", "MCA Negeri Sembilan"]),
    ("Gerakan and PN", ["民政党", "Gerakan", "国盟", "PN", "Bersatu"]),
    ("PAS Factor", ["伊党", "PAS", "Cina takut PAS", "伊斯兰", "绿潮"]),
    ("PH-BN Relationship", ["PH BN", "希盟", "国阵", "muafakat", "合作", "团结政府"]),
    ("Candidate Performance", ["候选人", "calon", "candidate", "ADUN", "议员"]),
    ("State Government Stability", ["州政府", "州政权", "state government", "稳定"]),
    ("Youth and Undi18", ["年轻人", "青年", "undi18", "youth", "首投"]),
    ("Race and Religion", ["种族", "宗教", "politik agama", "hak bukan Melayu", "race and religion", "华社", "kuil", "kovil", "கோவில்", "Hindu temple", "diskriminasi"]),
    ("Misinformation", ["假消息", "misinformation", "fake news", "谣言", "误导"]),
]

_COMPILED = [
    (cluster, re.compile("|".join(re.escape(k) for k in kws), re.IGNORECASE))
    for cluster, kws in _KEYWORD_MAP
]


def classify_issue(text: str, existing: Optional[str] = None) -> str:
    """Return issue_cluster from existing value or keyword fallback."""
    if existing and str(existing).strip() and str(existing).strip().lower() not in ("nan", "none", ""):
        val = str(existing).strip()
        if val in ISSUE_CLUSTERS:
            return val
    if not text or not str(text).strip():
        return "Other"
    combined = str(text)
    for cluster, pattern in _COMPILED:
        if pattern.search(combined):
            return cluster
    return "Other"


# Isu khusus komuniti India — elak label "Chinese Education" untuk SJKT/Tamil
_INDIAN_KEYWORD_MAP: list[tuple[str, list[str]]] = [
    ("Tamil Education", ["SJKT", "sekolah Tamil", "Tamil school", "guru Tamil", "Tamil teacher", "pendidikan Tamil", "தமிழ்", "Tamil palli", "MIC education"]),
    ("Employment", ["pekerjaan", "employment", "kilang", "factory", "gaji", "job", "velai", "வேலை", "pengangguran", "unemployment"]),
    ("Healthcare", ["hospital", "doctor", "doktor", "kesihatan", "health", "maruththuvam", "மருத்துவ", "clinic", "klinik"]),
    ("Housing", ["perumahan", "housing", "PPR", "rumah", "veedu", "sewa rumah"]),
    ("Local Government Services", ["local council", "majlis", "perkhidmatan", "sampah", "parking", "jalan"]),
    ("Race and Religion", ["kuil", "kovil", "கோவில்", "Hindu temple", "temple", "Deepavali", "Thaipusam"]),
    ("Cost of Living", ["kos sara hidup", "cost of living", "harga barang", "vilai vaasi", "விலைவாசி", "selavu", "inflation"]),
    ("Gerakan and PN", ["Gerakan", "国盟", "PN", "Perikatan", "Bersatu"]),
    ("PAS Factor", ["PAS", "伊党", "Parti Islam"]),
    ("DAP Performance", ["DAP", "行动党", "Pakatan Harapan", "PH"]),
    ("PH-BN Relationship", ["BN", "国阵", "UMNO", "muafakat", "kerajaan perpaduan"]),
    ("Candidate Performance", ["calon", "candidate", "ADUN", "pilihan raya", "PRN"]),
    ("Misinformation", ["fake news", "misinformation", "palsu", "谣言"]),
]

_INDIAN_COMPILED = [
    (cluster, re.compile("|".join(re.escape(k) for k in kws), re.IGNORECASE))
    for cluster, kws in _INDIAN_KEYWORD_MAP
]


def classify_issue_indian(text: str, existing: Optional[str] = None) -> str:
    """Klasifikasi isu untuk crawl komuniti India."""
    if existing and str(existing).strip() and str(existing).strip().lower() not in ("nan", "none", ""):
        val = str(existing).strip()
        if val == "Chinese Education":
            return classify_issue_indian(text, None)
        if val in ISSUE_CLUSTERS:
            return val
    if not text or not str(text).strip():
        return "Other"
    combined = str(text)
    for cluster, pattern in _INDIAN_COMPILED:
        if pattern.search(combined):
            return cluster
    return "Other"


def classify_issue_community(text: str, existing: Optional[str] = None, community: str = "chinese") -> str:
    if str(community).lower() == "indian":
        return classify_issue_indian(text, existing)
    return classify_issue(text, existing)
