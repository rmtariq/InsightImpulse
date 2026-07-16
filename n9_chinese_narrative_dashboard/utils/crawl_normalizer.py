"""Normalize PRN crawl CSV rows into dashboard post schema."""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

import pandas as pd

from utils.keyword_classifier import classify_issue

STATES = ["Negeri Sembilan", "Johor", "Melaka"]
STATE_PREFIX = {
    "Negeri Sembilan": "NS",
    "Johor": "JHR",
    "Melaka": "MLK",
    "Semua": "ALL",
}

VOICE_TO_SOURCE = {
    "media_chinese": "Chinese Media",
    "media_india": "Indian Media",
    "community_india": "Indian Community",
    "adun_indian": "ADUN",
    "party_official": "Political Party",
    "proxy_about_chinese": "Public User",
    "seat_bandar": "Community Page",
    "leader_chinese": "ADUN",
}

INDIA_DOMAINS = ("nanban", "makkalosai", "makkal", "vanakkam", "varnam", "tamilmalar", "tamil")

LOCATION_HINTS = {
    "Negeri Sembilan": [
        ("Seremban", "NS-N21", "Seremban"), ("Nilai", "NS-N10", "Seremban"),
        ("Lobak", "NS-N11", "Seremban"), ("Port Dickson", "NS-N29", "Port Dickson"),
        ("Bahau", "NS-N08", "Jempol"), ("Tampin", "NS-N34", "Tampin"),
        ("Kuala Pilah", "NS-N15", "Kuala Pilah"), ("Jempol", "NS-N08", "Jempol"),
        ("Rembau", "NS-N26", "Rembau"), ("Jelebu", "NS-N13", "Jelebu"),
    ],
    "Johor": [
        ("Johor Bahru", "JHR-N48", "Johor Bahru"), ("Skudai", "JHR-N49", "Johor Bahru"),
        ("Iskandar Puteri", "JHR-N49", "Johor Bahru"), ("Pasir Gudang", "JHR-N40", "Pasir Gudang"),
        ("Kulai", "JHR-N50", "Kulai"), ("Kluang", "JHR-N09", "Kluang"),
        ("Batu Pahat", "JHR-N18", "Batu Pahat"), ("Muar", "JHR-N14", "Muar"),
        ("Tangkak", "JHR-N04", "Tangkak"), ("Segamat", "JHR-N01", "Segamat"),
        ("Pontian", "JHR-N52", "Pontian"), ("Kota Tinggi", "JHR-N31", "Kota Tinggi"),
        ("Mersing", "JHR-N33", "Mersing"), ("Yong Peng", "JHR-N19", "Batu Pahat"),
    ],
    "Melaka": [
        ("Melaka", "MLK-N16", "Melaka"), ("Bandar Hilir", "MLK-N16", "Melaka"),
        ("Bukit Katil", "MLK-N13", "Melaka"), ("Klebang", "MLK-N12", "Melaka"),
        ("Alor Gajah", "MLK-N01", "Alor Gajah"), ("Jasin", "MLK-N08", "Jasin"),
        ("Merlimau", "MLK-N09", "Jasin"), ("Ayer Keroh", "MLK-N13", "Melaka"),
        ("Hang Tuah Jaya", "MLK-N13", "Melaka"),
    ],
}

# State detection from post text (longer phrases first to reduce false positives)
_STATE_SIGNALS: dict[str, tuple[str, ...]] = {
    "Johor": (
        "johor bahru", "iskandar puteri", "pasir gudang", "batu pahat", "kota tinggi",
        "negeri johor", "柔佛", "johor", "skudai", "kluang", "muar", "kulai", "tangkak",
        "segamat", "pontian", "mersing", "nusajaya", "gelang patah", "yong peng",
        "permata jaya", "masai", "senai", "jb ",
    ),
    "Melaka": (
        "negeri melaka", "melaka tengah", "alor gajah", "hang tuah jaya", "马六甲",
        "melaka", "malacca", "jasin", "merlimau", "ayer keroh", "bukit katil",
    ),
    "Negeri Sembilan": (
        "negeri sembilan", "port dickson", "kuala pilah", "森美兰", "森州", "芙蓉",
        "seremban", "nilai", "bahau", "tampin", "jempol", "rembau", "jelebu", "mantin",
    ),
}


def _guess_state_from_text(text: str) -> str:
    t = f" {str(text).lower()} "
    scores = {state: 0 for state in STATES}
    for state, signals in _STATE_SIGNALS.items():
        for sig in signals:
            s = sig.lower()
            if len(s) <= 4:
                if re.search(rf"\b{re.escape(s)}\b", t, re.I):
                    scores[state] += 2 if len(s) <= 3 else 1
            elif s in t:
                scores[state] += 2 if " " in s else 1
    ranked = sorted(scores.items(), key=lambda x: (-x[1], x[0]))
    if ranked[0][1] > 0:
        return ranked[0][0]
    return ""


def _detect_language(text: str, lang_hint: str = "") -> str:
    t = str(text or "")
    if not t.strip():
        return "unknown"
    ta = len(re.findall(r"[\u0B80-\u0BFF]", t))
    if ta > max(3, len(t) * 0.08):
        return "ta"
    hint = str(lang_hint or "").lower()
    if hint in ("cina", "zh", "zh-cn", "zh-tw"):
        return "zh-CN"
    zh = len(re.findall(r"[\u4e00-\u9fff]", t))
    if zh > len(t) * 0.15:
        return "zh-CN"
    if re.search(r"\b(the|and|or|in|for)\b", t, re.I):
        return "en"
    return "ms"


def _crawl_community(row: pd.Series) -> str:
    for col in ("Community", "community", "PublisherGuess", "publisher_guess"):
        val = str(row.get(col) or "").strip().lower()
        if val in ("india", "cina", "chinese"):
            return "india" if val == "india" else "chinese"
    domain = str(row.get("PublisherDomain") or row.get("URL") or "").lower()
    if any(d in domain for d in INDIA_DOMAINS):
        return "india"
    lang = str(row.get("Lang") or row.get("lang") or "").lower()
    if lang in ("tamil", "ta"):
        return "india"
    return ""


def _voice_from_community(community: str, voice: str) -> str:
    if voice and voice not in ("nan", "none", ""):
        return voice
    if community == "india":
        return "media_india"
    return voice


def _infer_sentiment(text: str, score: float | None = None) -> tuple[str, float]:
    if score is not None and pd.notna(score) and float(score) != 0:
        s = float(score)
        if s > 0.2:
            return "positive", s
        if s < -0.2:
            return "negative", s
        return "neutral", s
    t = str(text).lower()
    neg = ["rosak", "banjir", "mahal", "complaint", "worst", "fail", "断水", "投诉", "困难"]
    pos = ["good", "support", "terima kasih", "感谢", "success", "baik"]
    if any(k in t for k in neg):
        return "negative", -0.4
    if any(k in t for k in pos):
        return "positive", 0.4
    return "neutral", 0.0


def _infer_risk(text: str, sentiment: str) -> str:
    t = str(text).lower()
    if any(k in t for k in ["假消息", "palsu", "fake news", "misinformation", "hoax"]):
        return "High"
    if any(k in t for k in ["race", "agama", "religion", "种族", "宗教", "perkauman"]):
        return "High"
    if sentiment == "negative" and any(k in t for k in ["critical", "crisis", " kritikal"]):
        return "Critical"
    if sentiment == "negative":
        return "Medium"
    return "Low"


def _normalize_date(val) -> str:
    """Consistent datetime string (no timezone) for mixed-source CSV."""
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return ""
    s = str(val).strip()
    if not s or s.lower() in ("nan", "none", ""):
        return ""
    try:
        dt = pd.to_datetime(s, utc=True)
        if hasattr(dt, "tz_convert"):
            dt = dt.tz_convert(None)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return ""


def prefix_dun(dun: str, state: str) -> str:
    if not dun or str(dun).lower() in ("nan", "none", ""):
        return ""
    d = str(dun).strip().upper()
    pref = STATE_PREFIX.get(state, "NS")
    if "-" in d and d.split("-")[0] in STATE_PREFIX.values():
        return d
    if d.startswith("N") and d[1:].isdigit():
        return f"{pref}-{d}"
    return d


def _guess_location(text: str, state: str) -> tuple[str, str, str]:
    hints = LOCATION_HINTS.get(state, [])
    t = str(text).lower()
    for loc, dun, district in hints:
        if len(loc) <= 5:
            if re.search(rf"\b{re.escape(loc.lower())}\b", t, re.I):
                return loc, dun, district
        elif loc.lower() in t:
            return loc, dun, district
    if hints:
        return hints[0]
    return "", "", ""


def normalize_crawl_row(row: pd.Series, default_state: str = "") -> dict:
    """Map one crawl row (news or socmed) to dashboard post dict."""
    text = str(row.get("Text") or row.get("post_text") or row.get("text") or "")
    url = str(row.get("URL") or row.get("source_url") or row.get("url") or "")
    explicit_state = str(row.get("Negeri") or row.get("state") or "").strip()
    if explicit_state and explicit_state.lower() not in ("nan", "none", "", "semua"):
        state = explicit_state
    else:
        state = _guess_state_from_text(text) or default_state or "Negeri Sembilan"
    pid = str(row.get("ID") or row.get("post_id") or "")
    if not pid:
        pid = hashlib.md5(f"{url}{text[:80]}".encode()).hexdigest()[:12]

    crawl_comm = _crawl_community(row)
    lang_hint = str(row.get("Lang") or row.get("lang") or "")

    platform = str(row.get("Platform") or row.get("platform") or "news")
    voice = str(row.get("Jenis_Suara") or row.get("jenis_suara") or "")
    voice = _voice_from_community(crawl_comm, voice)

    if platform.lower() == "news":
        if voice == "media_chinese" or crawl_comm == "chinese":
            platform = "Chinese online media"
        elif voice == "media_india" or crawl_comm == "india":
            platform = "Indian online media"
        elif platform.lower() == "news":
            platform = "news"

    source_cat = VOICE_TO_SOURCE.get(voice, str(row.get("source_category") or "Public User"))
    if crawl_comm == "india" and source_cat == "Public User":
        source_cat = "Indian Media"

    score = pd.to_numeric(row.get("sentiment_score"), errors="coerce")
    sentiment, sent_score = _infer_sentiment(text, score if pd.notna(score) else None)
    if str(row.get("Sentiment") or row.get("sentiment") or "").strip():
        sentiment = str(row.get("Sentiment") or row.get("sentiment")).lower()

    constituency, dun, district = _guess_location(text, state)
    if row.get("constituency"):
        constituency = row.get("constituency")
    if row.get("dun_code"):
        dun = prefix_dun(str(row.get("dun_code")), state)
    elif dun:
        dun = prefix_dun(dun, state)

    issue = classify_issue(text, row.get("issue_cluster"))
    misinfo = _infer_risk(text, sentiment) == "High" and "fake" in text.lower()

    likes = pd.to_numeric(row.get("likes", 0), errors="coerce") or 0
    comments = pd.to_numeric(row.get("comments_count", row.get("comments", 0)), errors="coerce") or 0
    shares = pd.to_numeric(row.get("shares", 0), errors="coerce") or 0
    views = pd.to_numeric(row.get("views", 0), errors="coerce") or 0

    return {
        "state": state,
        "post_id": f"{STATE_PREFIX.get(state, 'NS')}-{pid}",
        "platform": platform,
        "account_name": str(row.get("account_name") or row.get("Type") or ""),
        "account_type": str(row.get("account_type") or "Media"),
        "source_category": source_cat,
        "source_url": url,
        "published_at": _normalize_date(row.get("Date") or row.get("published_at")),
        "post_text": text,
        "translated_text_bm": str(row.get("translated_text_bm") or ""),
        "language_detected": _detect_language(text, lang_hint),
        "crawl_community": crawl_comm,
        "constituency": constituency,
        "dun_code": dun,
        "district": district or str(row.get("district") or ""),
        "party_mentioned": str(row.get("party_mentioned") or ""),
        "candidate_mentioned": str(row.get("candidate_mentioned") or ""),
        "issue_cluster": issue,
        "sentiment": sentiment,
        "sentiment_score": sent_score,
        "emotion": str(row.get("emotion") or "neutral"),
        "likes": int(likes),
        "comments": int(comments),
        "shares": int(shares),
        "views": float(views),
        "engagement_total": int(likes + comments + shares),
        "stance_dap": "",
        "stance_mca": "",
        "stance_pn": "",
        "stance_bn": "",
        "ethnic_sensitive_flag": bool(re.search(r"race|agama|宗教|种族|perkauman", text, re.I)),
        "religion_sensitive_flag": bool(re.search(r"agama|religion|宗教|islam|muslim", text, re.I)),
        "misinformation_flag": misinfo,
        "risk_level": _infer_risk(text, sentiment),
        "query_id": str(row.get("QueryID") or row.get("query_id") or ""),
        "jenis_suara": voice,
        "weight_analisis": str(row.get("Weight_Analisis") or row.get("weight_analisis") or ""),
    }


def normalize_crawl_df(df: pd.DataFrame, default_state: str = "") -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()
    rows = [normalize_crawl_row(df.iloc[i], default_state) for i in range(len(df))]
    return pd.DataFrame(rows)


def latest_crawl_file(directory: Path, pattern: str = "*.csv") -> Path | None:
    if not directory.exists():
        return None
    files = sorted(directory.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0] if files else None
