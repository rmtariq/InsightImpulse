"""Generate realistic sample data for MVP dashboard."""
from __future__ import annotations

import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from utils.keyword_classifier import ISSUE_CLUSTERS, classify_issue

DATA_DIR = ROOT / "data"

LOCATIONS = [
    ("Seremban", "N21", "Seremban"),
    ("Rasah", "N22", "Seremban"),
    ("Nilai", "N10", "Seremban"),
    ("Lobak", "N11", "Seremban"),
    ("Temiang", "N12", "Seremban"),
    ("Bukit Kepayang", "N21", "Seremban"),
    ("Rahang", "N22", "Seremban"),
    ("Mambau", "N23", "Seremban"),
    ("Seremban Jaya", "N24", "Seremban"),
    ("Chennah", "N02", "Jelebu"),
    ("Bahau", "N08", "Jempol"),
    ("Lukut", "N30", "Port Dickson"),
    ("Port Dickson", "N29", "Port Dickson"),
    ("Tampin", "N34", "Tampin"),
    ("Repah", "N36", "Jempol"),
    ("Rembau", "N26", "Rembau"),
    ("Kuala Pilah", "N18", "Kuala Pilah"),
    ("Jempol", "N08", "Jempol"),
    ("Jelebu", "N02", "Jelebu"),
]

PLATFORMS = ["Facebook", "TikTok", "X", "Instagram", "YouTube", "Chinese online media", "Community pages"]
SOURCE_CATS = [
    "ADUN", "MP", "Political Party", "Chinese Media", "Community Page",
    "Government Agency", "Influencer", "Public User",
]
ACCOUNT_TYPES = ["Individual", "Organisation", "Media", "Political", "Community"]
LANGUAGES = ["zh-CN", "zh-TW", "ms", "en", "mixed"]
SENTIMENTS = ["positive", "neutral", "negative"]
EMOTIONS = ["trust", "anger", "fear", "joy", "sadness", "surprise", "neutral"]
PARTIES = ["DAP", "MCA", "Gerakan", "PH", "BN", "PN", "PAS", "UMNO", "PKR", "Amanah", "Bersatu", ""]
RISK_LEVELS = ["Low", "Medium", "High", "Critical"]

POSTS_ZH = [
    "森美兰州选临近，芙蓉市区塞车问题又严重了，停车位不够。",
    "汝来工厂区物价上涨，中小企业老板叫苦。华社关注生活费。",
    "马口小贩反映市议会执法太严，生意难做。",
    "波德申旅游季，本地商家希望州政府多宣传。",
    "芦骨华人区水供不稳定，居民投诉多次。",
    "行动党在森州的表现，华社有不同看法。",
    "马华能否在州选中重新获得代表性？",
    "年轻首投族更关注就业和房价。",
    "独中拨款和华文教育仍是热点。",
    "假消息说某候选人退选，请勿转发。",
    "PH和BN合作讨论，网上议论纷纷。",
    "伊党因素让部分选民担忧。",
]

POSTS_ZH_BM = {
    POSTS_ZH[0]: "PRN Negeri Sembilan hampir, kesesakan trafik di bandar Seremban semakin teruk, tempat letak kereta tidak mencukupi.",
    POSTS_ZH[1]: "Kawasan kilang Nilai — harga barang naik, pemilik PKS merungut. Komuniti Cina prihatin kos sara hidup.",
    POSTS_ZH[2]: "Penjaja di Bahau keluh penguatkuasaan majlis perbandaran terlalu ketat, sukar berniaga.",
    POSTS_ZH[3]: "Musim pelancongan Port Dickson — peniaga tempatan harap kerajaan negeri lebih promosi.",
    POSTS_ZH[4]: "Kawasan Cina Lukut — bekalan air tidak stabil, penduduk adu berkali-kali.",
    POSTS_ZH[5]: "Prestasi DAP di Negeri Sembilan — komuniti Cina ada pelbagai pandangan.",
    POSTS_ZH[6]: "Bolehkah MCA regain representasi dalam PRN negeri?",
    POSTS_ZH[7]: "Pengundi muda first-time lebih fokus pekerjaan dan harga rumah.",
    POSTS_ZH[8]: "Peruntukan sekolah Cina independen dan pendidikan Cina masih isu panas.",
    POSTS_ZH[9]: "Maklumat palsu kata calon tarik diri — jangan kongsi.",
    POSTS_ZH[10]: "Perbincangan kerjasama PH dan BN — perdebatan sengit online.",
    POSTS_ZH[11]: "Faktor PAS membuat sebahagian pengundi bimbang.",
}

POSTS_MS = [
    "PRN Negeri Sembilan: pengundi Cina di Seremban bincang isu kos sara hidup.",
    "DAP Negeri Sembilan perlu fokus perkhidmatan tempatan di Lobak.",
    "MCA Negeri Sembilan adakan program dialog komuniti Cina.",
    "Keselamatan di Nilai perlu dipertingkat — warga bimbang.",
    "Politik agama jangan jadi isu utama PRN NS.",
]

POSTS_EN = [
    "Chinese community in Negeri Sembilan discusses local council performance.",
    "SME owners in Nilai worry about rising costs ahead of state election.",
    "Chinese school funding remains a key narrative online.",
    "Traffic congestion in Seremban city centre frustrates residents.",
]

ACCOUNTS = [
    "NS华人资讯站", "Seremban Voice", "DAP NS Updates", "MCA N9 Community",
    "N9 Biz Watch", "芙蓉街坊", "Port Dickson Talk", "Nilai Residents",
    "Harakah Digital", "Sin Chew NS", "Public User_4821", "Influencer_Amy",
]

JOhor_LOCATIONS = [
    ("Johor Bahru", "JHR-N48", "Johor Bahru"),
    ("Stulang", "JHR-N48", "Johor Bahru"),
    ("Skudai", "JHR-N49", "Johor Bahru"),
    ("Kulai", "JHR-N50", "Kulai"),
    ("Batu Pahat", "JHR-N18", "Batu Pahat"),
    ("Muar", "JHR-N14", "Muar"),
    ("Kluang", "JHR-N09", "Kluang"),
    ("Pontian", "JHR-N52", "Pontian"),
    ("Segamat", "JHR-N04", "Segamat"),
]

MELAKA_LOCATIONS = [
    ("Bandar Hilir", "MLK-N16", "Melaka"),
    ("Bukit Katil", "MLK-N13", "Melaka"),
    ("Klebang", "MLK-N12", "Melaka"),
    ("Alor Gajah", "MLK-N01", "Alor Gajah"),
    ("Jasin", "MLK-N08", "Jasin"),
    ("Hang Tuah Jaya", "MLK-N14", "Melaka"),
]

STATE_CONFIG = {
    "Negeri Sembilan": {
        "prefix": "NS",
        "locations": LOCATIONS,
        "posts_zh": POSTS_ZH,
        "posts_ms": POSTS_MS,
        "posts_en": POSTS_EN,
        "accounts": ACCOUNTS,
        "query_tpl": "森美兰 {loc} OR PRN Negeri Sembilan {loc}",
    },
    "Johor": {
        "prefix": "JHR",
        "locations": JOhor_LOCATIONS,
        "posts_zh": [
            "柔佛州选临近，新山市区塞车严重。",
            "士古来工厂区物价上涨，商家叫苦。",
            "华文教育拨款仍是热点。",
            "Stulang 区水供不稳定，居民投诉。",
            "DAP Johor perlu fokus perkhidmatan bandar.",
        ],
        "posts_ms": [
            "PRN Johor: komuniti Cina bincang kos sara hidup di JB.",
            "Kerajaan Johor perlu tangani isu trafik Skudai.",
        ],
        "posts_en": [
            "Chinese community in Johor discusses local council performance.",
            "SME owners in Kulai worry about rising costs.",
        ],
        "accounts": ["Sin Chew Johor", "JB Community Voice", "DAP Johor", "MCA Johor", "Skudai Residents"],
        "query_tpl": "柔佛 {loc} OR PRN Johor {loc}",
    },
    "Melaka": {
        "prefix": "MLK",
        "locations": MELAKA_LOCATIONS,
        "posts_zh": [
            "马六甲州选，古城旅游区商家希望州政府多宣传。",
            "Bandar Hilir 停车位不足，居民投诉。",
            "独中拨款和华文教育仍是热点。",
        ],
        "posts_ms": [
            "PRN Melaka: pengundi Cina bincang isu pelancongan dan kos sara hidup.",
            "Kerajaan Melaka perlu fokus perkhidmatan Bandar Hilir.",
        ],
        "posts_en": [
            "Chinese community in Melaka discusses heritage tourism and local services.",
        ],
        "accounts": ["Sin Chew Melaka", "Melaka Heritage Talk", "DAP Melaka", "Melaka Biz Watch"],
        "query_tpl": "马六甲 {loc} OR PRN Melaka {loc}",
    },
}


def _rand_date(start: datetime, end: datetime) -> datetime:
    delta = end - start
    return start + timedelta(seconds=random.randint(0, int(delta.total_seconds())))


CANDIDATES = ["", "Anthony Loke", "Local ADUN", "Calon BN", "Calon PH", "Calon PN", "Liew Chin Tong", "Khoo Poay Tiong"]


def _generate_posts_core(n: int, state: str, seed: int = 42) -> pd.DataFrame:
    cfg = STATE_CONFIG[state]
    random.seed(seed)
    start = datetime(2026, 5, 1)
    end = datetime(2026, 6, 13)
    prefix = cfg["prefix"]
    rows = []
    for i in range(n):
        loc, dun, district = random.choice(cfg["locations"])
        lang = random.choice(LANGUAGES)
        if lang.startswith("zh"):
            text = random.choice(cfg["posts_zh"]) + f" #{loc.split()[0]}"
        elif lang == "ms":
            text = random.choice(cfg["posts_ms"]) + f" ({loc})"
        elif lang == "en":
            text = random.choice(cfg["posts_en"]) + f" — {loc}"
        else:
            text = random.choice(cfg["posts_zh"][:2]) + " " + random.choice(cfg["posts_ms"][:1])

        sentiment = random.choices(SENTIMENTS, weights=[0.25, 0.35, 0.40])[0]
        issue = classify_issue(text)
        party = random.choice(PARTIES)
        likes = random.randint(0, 5000)
        comments = random.randint(0, 800)
        shares = random.randint(0, 400)
        views = random.randint(500, 50000) if random.random() > 0.2 else None
        eng = likes + comments + shares
        eth_sens = random.random() < 0.08
        rel_sens = random.random() < 0.06
        misinfo = issue == "Misinformation" or random.random() < 0.05
        if misinfo or eth_sens or (sentiment == "negative" and eng > 3000):
            risk = random.choice(["High", "Critical", "Medium"])
        elif sentiment == "negative":
            risk = random.choice(["Medium", "Low"])
        else:
            risk = random.choice(["Low", "Medium"])

        bm = text if lang in ("ms", "en") else f"[BM] {text[:100]} ({loc})"
        pub = _rand_date(start, end)
        rows.append({
            "state": state,
            "post_id": f"{prefix}CN-{i+1:05d}",
            "platform": random.choice(PLATFORMS),
            "account_name": random.choice(cfg["accounts"]),
            "account_type": random.choice(ACCOUNT_TYPES),
            "source_category": random.choice(SOURCE_CATS),
            "source_url": f"https://example.com/{prefix.lower()}/post/{i+1}",
            "published_at": pub.strftime("%Y-%m-%d %H:%M:%S"),
            "post_text": text,
            "translated_text_bm": bm,
            "language_detected": lang,
            "constituency": loc,
            "dun_code": dun,
            "district": district,
            "party_mentioned": party,
            "candidate_mentioned": random.choice(CANDIDATES),
            "issue_cluster": issue,
            "sentiment": sentiment,
            "sentiment_score": round(random.uniform(-1, 1) if sentiment == "negative" else random.uniform(-0.3, 1), 2),
            "emotion": random.choice(EMOTIONS),
            "likes": likes,
            "comments": comments,
            "shares": shares,
            "views": views,
            "engagement_total": eng,
            "stance_dap": random.choice(["support", "neutral", "oppose", ""]),
            "stance_mca": random.choice(["support", "neutral", "oppose", ""]),
            "stance_pn": random.choice(["support", "neutral", "oppose", ""]),
            "stance_bn": random.choice(["support", "neutral", "oppose", ""]),
            "ethnic_sensitive_flag": eth_sens,
            "religion_sensitive_flag": rel_sens,
            "misinformation_flag": misinfo,
            "risk_level": risk,
            "query_id": "",
            "jenis_suara": "media_chinese",
            "weight_analisis": "Tinggi",
        })
    return pd.DataFrame(rows)


def generate_posts_for_state(state: str, n: int = 80, seed: int = 42) -> pd.DataFrame:
    return _generate_posts_core(n, state, seed)


def generate_posts(n: int = 180, seed: int = 42) -> pd.DataFrame:
    return _generate_posts_core(n, "Negeri Sembilan", seed)


def generate_seed_list(n: int = 40, seed: int = 42, state: str = "Negeri Sembilan") -> pd.DataFrame:
    cfg = STATE_CONFIG.get(state, STATE_CONFIG["Negeri Sembilan"])
    random.seed(seed)
    rows = []
    types = ["ADUN", "MP", "Political Party", "Media", "Community Page"]
    parties = ["DAP", "MCA", "UMNO", "PAS", "PKR", "Amanah", "Gerakan", "BN", ""]
    slug = cfg["prefix"].lower()
    for i in range(n):
        loc, dun, district = random.choice(cfg["locations"])
        verified = random.choice(["Verified", "Unverified", "Pending"])
        rows.append({
            "state": state,
            "record_id": f"SEED-{cfg['prefix']}-{i+1:04d}",
            "account_name": f"{state} Account_{i+1}",
            "person_name": f"Person {i+1}",
            "account_type": random.choice(types),
            "coalition": random.choice(["PH", "BN", "PN", "Independent", ""]),
            "political_party": random.choice(parties),
            "parliament": f"P{random.randint(120, 160)}",
            "dun_code": dun,
            "dun_name": loc,
            "district": district,
            "facebook": f"https://facebook.com/{slug}{i+1}" if random.random() > 0.3 else "",
            "tiktok": f"https://tiktok.com/@{slug}{i+1}" if random.random() > 0.5 else "",
            "x_twitter": f"https://x.com/{slug}{i+1}" if random.random() > 0.5 else "",
            "instagram": f"https://instagram.com/{slug}{i+1}" if random.random() > 0.4 else "",
            "youtube": f"https://youtube.com/@{slug}{i+1}" if random.random() > 0.6 else "",
            "website": "",
            "priority": random.choice(["High", "Medium", "Low"]),
            "verification_status": verified,
            "issue_cluster": random.choice(ISSUE_CLUSTERS[:10]),
            "suggested_search_query": cfg["query_tpl"].format(loc=loc),
        })
    return pd.DataFrame(rows)


def ensure_sample_data() -> tuple[Path, Path]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    posts_path = DATA_DIR / "sample_n9_chinese_narrative_posts.csv"
    seed_path = DATA_DIR / "n9_prn_social_media_crawler_seed_list.csv"
    johor_seed = DATA_DIR / "johor_prn_social_media_crawler_seed_list.csv"
    melaka_seed = DATA_DIR / "melaka_prn_social_media_crawler_seed_list.csv"
    if not posts_path.exists():
        generate_posts(180).to_csv(posts_path, index=False)
    if not seed_path.exists():
        generate_seed_list(40, state="Negeri Sembilan").to_csv(seed_path, index=False)
    if not johor_seed.exists():
        generate_seed_list(35, seed=43, state="Johor").to_csv(johor_seed, index=False)
    if not melaka_seed.exists():
        generate_seed_list(28, seed=44, state="Melaka").to_csv(melaka_seed, index=False)
    return posts_path, seed_path


if __name__ == "__main__":
    ensure_sample_data()
    print("Sample data generated in data/")
