"""Classify Cula Digital poll comments: clear answers + debate lean labels."""
from __future__ import annotations

import re
from typing import Optional, Tuple

ISSUE_MN_SOLO = "MN vs Solo"
ISSUE_LABU = "PAS Labu"

TIER_JELAS = "Jelas"
TIER_DEBAT = "Debat"
TIER_NA = "N/A"

# --- MN vs Solo ---

def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def detect_issue_from_post_text(post_text: str) -> str:
    t = _norm(post_text)
    if "dun labu" in t or ("labu" in t and "pas" in t):
        return ISSUE_LABU
    if "go solo" in t or "mn (pn+bn)" in t or "muafakat" in t:
        return ISSUE_MN_SOLO
    return ISSUE_MN_SOLO


def classify_mn_solo(text: str) -> Tuple[str, str, str]:
    """
    Returns (tier, label, bucket).
    bucket: MN | Solo | Pro-PAS | Pro-PH | Tidak Jelas
    """
    raw = (text or "").strip()
    t = _norm(raw)

    if not t:
        return TIER_DEBAT, "Debat→Tidak Jelas", "Tidak Jelas"

    # Tier 1 — clear A/B
    if re.fullmatch(r"a[\s.!]*", t) or t in {"a", "a.", "option a"}:
        return TIER_JELAS, "Jelas→MN", "MN"
    if re.fullmatch(r"b[\s.!]*", t) or t in {"b", "b.", "option b"}:
        return TIER_JELAS, "Jelas→Solo", "Solo"
    if len(t) <= 120:
        if any(x in t for x in ("go solo", "solo lgi", "solo lagi", "pas solo", " b:", "b :")):
            return TIER_JELAS, "Jelas→Solo", "Solo"
        if any(x in t for x in ("mn terbaik", "muafakat", "pn+bn", "pn bn", "a pn+bn")):
            return TIER_JELAS, "Jelas→MN", "MN"

    # Tier 2 — debate lean (keyword scoring)
    solo_kw = (
        "go solo", "solo lgi", "solo lagi", "pas solo", "lawan semua seat",
        "syok sendiri", "bn nak join pn", "sendiri dulu", "solo dulu", "solo...",
        "solo dan lawan",
    )
    mn_kw = (
        "pas 13 kerusi", "tak mampu bentuk kerajaan", "mampu bentuk kerajaan",
        "bergabung jugak", "muafakat nasional", "pn+bn", "pn bn", "gabung bn",
        "gabung pn", "paspn", "pas pn", "kalau mn", "mn lps", "mn kompom",
        "perlu kerjasama", "tak cukup kerusi",
    )
    pro_pas_kw = (
        "pengkhianat", "47 kes", "zahid", "umdap", "lobai", "kafir harbi",
        "hina islam", "hina allah", "hina nabi", "walaun", "liberal", "refobasi",
        "pemfitnah", "penunggang agama", "parti sampah", "perosak", "hadi awang",
        "nozahid", "umno pun x hingin", "parti pengkhianat",
    )
    pro_ph_kw = (
        "ph kekal", "tetap bersama ph", "undi ph", "tok min", "penyelamat tunku",
        "pas perosak", "tak suka perkauman", "parti ajaran sesat", "mundur mcm sg4",
        "ph terbaik", "calon tebuk atap", "mb nya", "ph menang", "sokong ph",
        "ekstrem", "rasis", "bungkus", "pis pus", "pas mana nak minta ph menang",
        "bn dengan pn bungkus",
    )

    scores = {
        "Debat→Solo": sum(2 for kw in solo_kw if kw in t),
        "Debat→MN": sum(2 for kw in mn_kw if kw in t),
        "Debat→Pro-PAS": sum(2 for kw in pro_pas_kw if kw in t),
        "Debat→Pro-PH": sum(2 for kw in pro_ph_kw if kw in t),
    }
    best_label = max(scores, key=scores.get)
    best_score = scores[best_label]
    if best_score == 0:
        return TIER_DEBAT, "Debat→Tidak Jelas", "Tidak Jelas"

    top_two = sorted(scores.values(), reverse=True)
    if len(top_two) > 1 and top_two[0] == top_two[1]:
        return TIER_DEBAT, "Debat→Tidak Jelas", "Tidak Jelas"

    bucket_map = {
        "Debat→MN": "MN",
        "Debat→Solo": "Solo",
        "Debat→Pro-PAS": "Pro-PAS",
        "Debat→Pro-PH": "Pro-PH",
    }
    return TIER_DEBAT, best_label, bucket_map[best_label]


def classify_labu(text: str) -> Tuple[str, str, str]:
    """
    Returns (tier, label, bucket).
    bucket: Sokong PAS | Tak Sokong PAS | Tidak Jelas
    """
    raw = (text or "").strip()
    t = _norm(raw)

    if not t:
        return TIER_DEBAT, "Debat→Tidak Jelas", "Tidak Jelas"

    # Tier 1 — clear
    if re.search(r"\btak\s+(sokong|undi|boleh|menang)", t) or "undi ph" in t or "tak sokong pas" in t:
        return TIER_JELAS, "Jelas→Tak Sokong PAS", "Tak Sokong PAS"
    if any(
        x in t
        for x in (
            "labu for pas", "undi pas", "sokong pas", "mesti undi pas",
            "mestilah undi pas", "pas terbaik", "gelombang hijau", "letak ja",
            "takbir", "pas in sha",
        )
    ) or t in {"pas", "ya", "yes"}:
        return TIER_JELAS, "Jelas→Sokong PAS", "Sokong PAS"

    # Tier 2 — debate lean
    yes_kw = (
        "letak dulu", "letak ja", "tawakal", "tuan hirman", "norhirman", "calon yb",
        "calon ni", "gelombang hijau", "pas terbaik", "pas in sha", "takbir",
        "wakil pas", "undi pas", "sokong", "membantu penduduk", "tahniah",
        "insyaallah", "den undi", "yb labu", "calon untuk dun labu",
    )
    no_kw = (
        "tak sokong", "undi ph", "tak undi", "hina sahabat nabi", "puak liberal",
        "keliru", "tengok dulu", "tgk dulu", "tak pasti", "belum pasti",
    )

    yes_score = sum(1 for kw in yes_kw if kw in t)
    no_score = sum(1 for kw in no_kw if kw in t)

    if no_score > yes_score:
        return TIER_DEBAT, "Debat→Tak Sokong PAS", "Tak Sokong PAS"
    if yes_score > 0:
        return TIER_DEBAT, "Debat→Sokong PAS", "Sokong PAS"
    return TIER_DEBAT, "Debat→Tidak Jelas", "Tidak Jelas"


def classify_cula_comment(text: str, issue: str) -> Tuple[str, str, str, str]:
    """Returns (issue, tier, label, bucket)."""
    if issue == ISSUE_LABU:
        tier, label, bucket = classify_labu(text)
    else:
        tier, label, bucket = classify_mn_solo(text)
    return issue, tier, label, bucket


def classify_row(
    text: str,
    row_type: str,
    post_text_by_url: Optional[dict[str, str]] = None,
    parent_post_url: str = "",
) -> Tuple[str, str, str, str]:
    """Classify one CSV row. Posts return N/A labels."""
    if str(row_type or "").strip().lower() != "comment":
        return "", TIER_NA, "", ""

    post_text = ""
    if post_text_by_url and parent_post_url:
        post_text = post_text_by_url.get(str(parent_post_url), "")
    issue = detect_issue_from_post_text(post_text)
    issue, tier, label, bucket = classify_cula_comment(text, issue)
    return issue, tier, label, bucket
