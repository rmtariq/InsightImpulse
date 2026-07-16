#!/usr/bin/env python3
"""Score and filter per-DUN news headlines for War Room display."""
from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from typing import Any

HEADLINE_MAX_AGE_DAYS = 90

N9_TERMS = re.compile(
    r"negeri\s*sembilan|n\.?\s*9\b|prn\s*n9|prn\s*negeri\s*sembilan|"
    r"seremban|nilai|port\s*dickson|jelebu|jempol|rembau|tampin|kuala\s*pilah|"
    r"rasah|aminuddin|anthony\s*loke|tuanku\s*muhriz|tunku\s*zain|"
    r"dun\s+\w+|adun",
    re.I,
)
JOHOR_TERMS = re.compile(
    r"\bjohor\b|prn\s*johor|johor\s*bahru|segamat|muar|batu\s*pahat|kluang|"
    r"kota\s*tinggi|kulai|pontian|mersing|tangkak|kempas|iskandar|pasir\s*gudang|"
    r"senai|skudai|onen\s*hafiz|bangsa\s*johor|dun\s+\w+|adun",
    re.I,
)
CROSS_STATE = {
    "N9": re.compile(
        r"\bjohor\b|prn\s*johor|johor\s*bahru|segamat|muar|batu\s*pahat|kluang|"
        r"kota\s*tinggi|kulai|pontian|mersing|tangkak|kempas|iskandar",
        re.I,
    ),
    "JOHOR": re.compile(
        r"negeri\s*sembilan|n\.?\s*9\b|prn\s*n9|seremban|nilai|port\s*dickson|"
        r"jelebu|jempol|rembau|tampin|kuala\s*pilah|aminuddin|anthony\s*loke",
        re.I,
    ),
}
IRRELEVANT = re.compile(
    r"gua\s*musang|kelantan|sabah|kota\s*kinabalu|penang|georgetown|butterworth|"
    r"kota\s*baharu|charlotte|london|prnewswire|world\s*cup|ansi\b|gsma|lendingtree|"
    r"universiti\s*alexandria|pulau\s*pinang|kota\s*tinggi|"
    r"johor(?!\s*baru)|melaka|selangor|singapore(?!\s*border)|"
    r"fire\s*congress|innovation\s*summit|"
    r"setiausaha\s*agung\s*(pas|bersatu|umno)|presiden\s*pas|pejabat\s*rasmi\s*pas",
    re.I,
)
DUN_CODE_IN_TEXT = re.compile(r"\bN\.?\s*0?[1-9][0-9]?\b", re.I)
AMBIGUOUS_SEAT_NAMES = {
    "nilai", "kota", "labu", "paloh", "tiram", "permas", "kukup", "tenang",
    "gambir", "bekok", "serom", "machap", "rengit", "kemas", "panti",
}
GENERIC_DIGEST = re.compile(r"#top10|berita popular|top\s*\d+\s*l\b|thread\s*🧵", re.I)


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip())


def count_dun_codes(text: str) -> int:
    return len(set(m.group(0).upper().replace(".", "").replace(" ", "") for m in DUN_CODE_IN_TEXT.finditer(text or "")))


def is_state_rollup(text: str, threshold: int = 4) -> bool:
    """Posts listing many DUN codes are state-wide, not seat-specific."""
    return count_dun_codes(text) >= threshold


def seat_specific_hits(text: str, seat: dict[str, Any]) -> list[str]:
    t = _clean(text)
    hits: list[str] = []
    name = seat.get("name") or seat.get("kawasan") or ""
    code = (seat.get("code") or seat.get("id") or "").upper().replace(".", "")
    adun = seat.get("winnerName") or seat.get("namaAdun") or seat.get("incumbent") or ""

    if name and re.search(rf"\b{re.escape(name)}\b", t, re.I):
        nm = name.lower()
        if nm in AMBIGUOUS_SEAT_NAMES:
            if re.search(
                rf"\b(dun|kerusi|prn|calon|adun)\b.{{0,40}}\b{re.escape(name)}\b|"
                rf"\b{re.escape(name)}\b.{{0,40}}\b(dun|kerusi|prn|calon|adun)\b",
                t,
                re.I,
            ):
                hits.append("dun_name")
        else:
            hits.append("dun_name")
    if code:
        dotted = f"N.{code[1:]}" if code.startswith("N") and len(code) > 1 else code
        if re.search(rf"\b{re.escape(code)}\b", t, re.I) or re.search(
            rf"\b{re.escape(dotted)}\b", t, re.I
        ):
            hits.append("dun_code")
    if adun:
        parts = [p for p in adun.split() if len(p) > 2]
        if any(re.search(rf"\b{re.escape(p)}\b", t, re.I) for p in parts[:2]):
            hits.append("adun")
    return hits


def _state_key(seat: dict[str, Any]) -> str:
    raw = (seat.get("stateKey") or seat.get("state") or "N9").upper()
    return "JOHOR" if raw in ("JOHOR", "JDT") else "N9"


def score_headline(text: str, seat: dict[str, Any]) -> tuple[str, list[str]]:
    """Return verdict: relevant | state_wide | weak | irrelevant."""
    t = _clean(text)
    if not t:
        return "irrelevant", []
    if IRRELEVANT.search(t):
        return "irrelevant", []
    if GENERIC_DIGEST.search(t):
        return "irrelevant", []

    st = _state_key(seat)
    cross = CROSS_STATE.get(st)
    state_terms = JOHOR_TERMS if st == "JOHOR" else N9_TERMS
    if cross and cross.search(t) and not state_terms.search(t):
        return "irrelevant", []

    specific = seat_specific_hits(t, seat)
    if specific and is_state_rollup(t):
        return "state_wide", specific

    hits = list(specific)
    if state_terms.search(t):
        hits.append(st.lower())

    if specific:
        return "relevant", hits
    if hits:
        return "state_wide", hits
    return "weak", hits


def filter_headlines(seat: dict[str, Any], headlines: list[str]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for raw in headlines or []:
        text = _clean(raw)
        if not text:
            continue
        verdict, hits = score_headline(text, seat)
        if verdict in ("irrelevant", "state_wide"):
            continue
        out.append({"text": text[:200], "verdict": verdict, "hits": hits})
    return out


def _parse_iso_date(raw: str | None) -> datetime | None:
    if not raw:
        return None
    try:
        dt = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        return None


def is_recent_headline(dt: datetime | None, ref: datetime | None = None, max_age_days: int = HEADLINE_MAX_AGE_DAYS) -> bool:
    if dt is None:
        return True
    ref = ref or datetime.now(timezone.utc)
    if ref.tzinfo is None:
        ref = ref.replace(tzinfo=timezone.utc)
    return (ref - dt) <= timedelta(days=max_age_days)


def build_display_headlines(
    seat: dict[str, Any],
    crawl_headlines: list[str] | None = None,
    socmed_snippet: str | None = None,
    socmed_snippet_date: str | None = None,
    ref_date: str | None = None,
    max_items: int = 3,
) -> dict[str, Any]:
    """Prefer recent seat-specific crawl headlines; fallback to recent socmed snippet."""
    ref_dt = _parse_iso_date(ref_date)
    verified = [h for h in filter_headlines(seat, crawl_headlines or []) if h["verdict"] == "relevant"]
    items = verified[:max_items]
    source = "news_crawl"

    snippet = _clean(socmed_snippet or "")
    snippet_dt = _parse_iso_date(socmed_snippet_date)
    if snippet and not is_recent_headline(snippet_dt, ref_dt):
        snippet = ""

    if snippet:
        sn_verdict, sn_hits = score_headline(snippet, seat)
        if sn_verdict == "relevant":
            sn_item = {
                "text": snippet[:200],
                "verdict": "relevant",
                "hits": sn_hits,
                "source": "socmed_master",
                "date": snippet_dt.isoformat() if snippet_dt else None,
            }
            if not items:
                items = [sn_item]
                source = "socmed_master"
                quality = "verified"
            elif snippet[:80] not in items[0]["text"]:
                items.append(sn_item)
                items = items[:max_items]
        elif sn_verdict == "weak" and not items:
            pass  # jangan papar snippet lemah — tiada kaitan kerusi

    items = [i for i in items if i.get("verdict") == "relevant"]
    quality = "verified" if items else "none"

    return {
        "quality": quality,
        "source": source if items else None,
        "items": items[:max_items],
        "headlines": [i["text"] for i in items[:max_items]],
    }
