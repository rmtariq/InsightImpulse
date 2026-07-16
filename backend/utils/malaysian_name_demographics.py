"""Infer Malaysian author demographic buckets from display names (heuristic)."""
from __future__ import annotations

import re
import unicodedata
from typing import Tuple

DEMO_MALAY = "Malay/Bumiputera"
DEMO_CHINESE = "Chinese"
DEMO_INDIAN = "Indian"
DEMO_URBAN = "Mixed/Urban"
DEMO_UNKNOWN = "Unknown"

CHINESE_SURNAMES = frozenset({
    "tan", "lim", "lee", "wong", "ong", "ng", "teh", "yap", "goh", "chin", "chen", "chan",
    "ho", "lau", "leong", "liew", "khoo", "yeoh", "chong", "chua", "yee", "toh", "sim",
    "koh", "ang", "hew", "tye", "tay", "ting", "teng", "sia", "siew", "foong", "heng",
    "khor", "kwan", "low", "loo", "mok", "pang", "phua", "quah", "saw", "seah", "soh",
    "soon", "tai", "tham", "wee", "yeap", "yuen", "cheah", "chee", "choo", "choy",
    "gan", "hooi", "kuek", "lam", "lian", "liang", "ling", "loke", "lye", "moy",
    "neo", "peh", "poay", "quek", "seng", "soo", "swee", "teo", "thong", "tong",
    "wai", "weng", "yeo", "yew", "yong", "yu", "yuan", "voo", "huang", "hu", "han",
    "su", "lie", "li", "lin", "fang", "feng", "hsu", "hsieh", "xie", "zhou", "zhu",
})

INDIAN_SURNAMES = frozenset({
    "kumar", "devi", "raj", "raja", "singh", "kaur", "nair", "menon", "pillai", "iyer",
    "subramaniam", "ramasamy", "murugan", "krishnan", "sharma", "patel", "nathan",
    "anbalagan", "muniandy", "suppiah", "sinniah", "samy", "velu", "arul", "gopal",
    "chandran", "perumal", "sundram", "thangavelu", "balakrishnan",
    "govindasamy", "govindaraju", "gunasekaran", "ethirmanasingham", "sivanesan",
    "sivam", "sivalingam", "parthiban", "maniam", "munusamy", "raman",
    "selvam", "sothi", "tamil", "vijay", "vicknes", "anand", "priya", "kavitha", "latha",
    "malar", "malini", "meena", "rani", "shanti", "sumathi", "vani", "vijayalakshmi",
    "khan", "haider", "salim", "naidu", "naicker", "thevar", "mudaliar", "chettiar",
    "jeyaraj", "jeyasingam", "sinnadurai", "durai", "pandian", "marimuthu", "sundaram",
    "ramachandran", "narayanan", "santhanam", "thiagarajan", "muthu", "samy", "velu",
})

INDIAN_HONORIFICS = frozenset({"inche", "muniammah", "muniandy"})

MALAY_HONORIFICS = frozenset({
    "atok", "mat", "wak", "pak", "mak", "ujang", "angah", "abang", "acik", "bang",
    "paksu", "pakcik", "makcik", "tok", "wan", "che", "putera", "putra", "ibnu", "ibni",
    "abu", "awang", "dayang", "panglima",
    "encik", "cik", "kak", "adik", "haji", "hajah", "ustaz", "ustazah", "nik", "ku",
    "tengku", "ungku", "syed", "sharifah", "dato", "datuk", "datin", "tokwan",
})

MALAY_NICKNAME_PREFIXES = (
    "mat", "wak", "pak", "paksu", "tok", "ujang", "angah", "acik", "bang", "atok",
)

MALAY_GIVEN = frozenset({
    "mohd", "muhammad", "mohamad", "ahmad", "abdul", "ab", "nur", "siti", "fatimah",
    "wan", "che", "mat", "haji", "hajah", "tengku", "ungku", "syed", "sharifah",
    "ismail", "ibrahim", "ali", "omar", "hassan", "hussein", "zainal", "zulkifli",
    "rosli", "rosman", "azman", "azmi", "aziz", "azizan", "faizal", "firdaus", "hafiz",
    "hamid", "harun", "hasan", "idris", "kamal", "khalid", "latiff", "mahmud", "mamat",
    "nordin", "rahman", "ramli", "razak", "ridzuan", "saad", "salleh", "shamsul",
    "sulaiman", "yusof", "yusuf", "zulkarnain", "amir", "amirul", "farid",
    "faridah", "halim", "halimah", "jamal", "jamaluddin", "kamariah", "khairul",
    "norshida", "noraini", "norazlina", "rohani", "roslan", "shahrul", "shamsiah",
    "zulkiflee", "adnan", "amin", "aminah", "anuar", "ashraf", "asri", "azlan",
    # Common names seen in N9 social crawl
    "hashim", "azam", "azan", "azhar", "bahar", "fauzi", "fuad", "johari", "kamaruddin",
    "kamarul", "mazlan", "mokhtar", "nasir", "nazri", "razali", "zakaria", "zainuddin",
    "amran", "aminuddin", "kassim", "solehudin", "suhaimi", "sharifuddin", "zaidi",
    "zahari", "zamri", "sabri", "ridzuan", "reduan", "shamsir", "shamsul", "shukri",
    "zulkifli", "zulkarnain", "zul", "zulkepli", "zaid", "zainal", "zaini", "zaki",
    "afif", "afifah", "alias", "aman", "amat", "amad", "anid", "asri", "azli", "azmil",
    "azral", "azroii", "badr", "deen", "din", "fazil", "fazli", "faresh", "fariza",
    "hakim", "hamizi", "hasri", "idah", "idah", "idris", "ilan", "irfan", "izani",
    "jalil", "jamilah", "juan", "kamal", "kamar", "khairil", "malik", "marz", "mas",
    "mihad", "munirah", "murad", "muzani", "nasruddin", "nazeri", "nazir", "noor",
    "norrimah", "norsham", "nuar", "nurul", "onn", "qaseh", "rafidah", "rahim", "razali",
    "raziman", "razman", "roha", "rossedi", "sharip", "sharkawi", "sobri", "supar",
    "syahrunnizat", "usairi", "waleed", "yusoff", "zack", "zai", "zakey", "zalli",
    "zeck", "zolkifli", "zumari", "abdurrahim", "takdir", "waleed", "faqrul", "salehan",
    "samah", "mahamud", "azharisyam", "drebar", "rembau", "zeral", "saufi", "nadzri",
    "bob", "mizi", "azrak", "maat", "khalil", "wahid", "noraidah", "baharin", "fazila",
    "syamil", "naain", "ludin", "rahmat", "muhamed", "katan", "mahurie", "majidbanting",
    "bob", "mtjohari", "khaider", "putera", "iskandar", "zulkefle", "fayyadh", "repahie",
    "berd", "gemilang", "shah", "anan", "kajang", "daud", "musa", "aiman", "hekals",
    "zainudin", "ramly", "tamit", "minos", "aqashah", "faisal", "jol", "zuba", "saari",
})

ORG_MARKERS = (
    "official", "page", "media", "fan page", "pemud", "pas ", " pas", "umno", "daps",
    "news", "tv", "radio", "channel", "team", "group", "community", "kawasan",
    "nasi lemak", "insuran", "kambing aqiqah", "johor dt", "leader lie", "lubuk rezeki",
)

_JAWI_RE = re.compile(r"[\u0600-\u06FF]")
_CJK_RE = re.compile(r"[\u4e00-\u9fff]")
_TAMIL_RE = re.compile(r"[\u0B80-\u0BFF]")
_MD_PREFIX_RE = re.compile(r"^(md|mohd|muhd|mohamad|muhammad|mohdnor|muhdnaim)")


def _norm(name: str) -> str:
    name = unicodedata.normalize("NFKC", (name or "").strip())
    name = re.sub(r"[^\w\s\-'/]", " ", name, flags=re.UNICODE)
    return re.sub(r"\s+", " ", name).strip().lower()


def _tokens(name: str) -> list[str]:
    return [t for t in _norm(name).split() if t]


def _malay_nickname_token(tok: str) -> bool:
    if tok in MALAY_HONORIFICS:
        return True
    if _MD_PREFIX_RE.match(tok):
        return True
    return any(tok.startswith(prefix) and len(tok) > len(prefix) for prefix in MALAY_NICKNAME_PREFIXES)


def classify_author_name(name: str) -> Tuple[str, float]:
    """
    Return (demographic_label, confidence 0-1).
    Heuristic only — not identity verification.
    """
    raw = (name or "").strip()
    if not raw or len(raw) < 2:
        return DEMO_UNKNOWN, 0.0

    low = raw.lower()
    if any(m in low for m in ORG_MARKERS) or low.endswith(" pas") or low.startswith("pas "):
        return DEMO_UNKNOWN, 0.2

    if _CJK_RE.search(raw):
        return DEMO_CHINESE, 0.95
    if _TAMIL_RE.search(raw):
        return DEMO_INDIAN, 0.9
    if _JAWI_RE.search(raw):
        return DEMO_MALAY, 0.85

    parts = _tokens(raw)
    if not parts:
        return DEMO_UNKNOWN, 0.0

    # Chinese: surname match (any token; first/last weighted higher in MY)
    for tok in parts:
        if tok in CHINESE_SURNAMES:
            if tok in (parts[0], parts[-1]):
                return DEMO_CHINESE, 0.82
            return DEMO_CHINESE, 0.76

    # Indian: surname / common names
    for tok in parts:
        if tok in INDIAN_SURNAMES:
            return DEMO_INDIAN, 0.85

    if parts[0] in INDIAN_HONORIFICS:
        return DEMO_INDIAN, 0.72

    # Malay: bin/binti/a/l/a/p patterns
    joined = " " + " ".join(parts) + " "
    if re.search(r"\b(bin|binti|bt|bte|b\.)\b", joined):
        return DEMO_MALAY, 0.88
    if re.search(r"\ba/l\b|\ba/p\b|\banak lelaki\b|\banak perempuan\b", joined):
        return DEMO_INDIAN, 0.75

    # Malay nicknames / honorifics (Atok, Wak, Mat*, Pak, Ujang, Abu, Putera, etc.)
    if parts[0] in MALAY_HONORIFICS:
        return DEMO_MALAY, 0.74
    if any(t in MALAY_HONORIFICS for t in parts[1:]):
        return DEMO_MALAY, 0.68
    if any(_malay_nickname_token(t) for t in parts):
        return DEMO_MALAY, 0.72

    malay_hits = sum(1 for t in parts if t in MALAY_GIVEN)
    if malay_hits >= 2:
        return DEMO_MALAY, 0.8
    if malay_hits == 1 and len(parts) <= 4:
        return DEMO_MALAY, 0.65

    # Single-token surnames / names
    if len(parts) == 1:
        tok = parts[0]
        if tok in CHINESE_SURNAMES:
            return DEMO_CHINESE, 0.62
        if tok in INDIAN_SURNAMES:
            return DEMO_INDIAN, 0.62
        if tok in MALAY_GIVEN:
            return DEMO_MALAY, 0.58
        if len(tok) <= 5:
            return DEMO_UNKNOWN, 0.15

    # Romanized Chinese-style: two short tokens, no Malay/Indian signal
    if len(parts) == 2 and all(2 <= len(t) <= 8 for t in parts):
        if parts[-1] in CHINESE_SURNAMES or parts[0] in CHINESE_SURNAMES:
            return DEMO_CHINESE, 0.7

    return DEMO_UNKNOWN, 0.25


def merge_demographic(
    text_demo: str,
    author_name: str,
    *,
    min_name_confidence: float = 0.6,
) -> Tuple[str, str, float]:
    """
    Combine text-language demographic with author-name inference.
    Returns (final_demographic, author_demographic, name_confidence).
    """
    author_demo, conf = classify_author_name(author_name)
    text_demo = (text_demo or DEMO_UNKNOWN).strip() or DEMO_UNKNOWN

    if conf >= min_name_confidence and author_demo != DEMO_UNKNOWN:
        return author_demo, author_demo, conf
    if text_demo not in (DEMO_UNKNOWN, ""):
        return text_demo, author_demo, conf
    if author_demo != DEMO_UNKNOWN:
        return author_demo, author_demo, conf
    return DEMO_UNKNOWN, author_demo, conf
