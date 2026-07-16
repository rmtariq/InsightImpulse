"""Strict Johor + N9 relevance filter for narrative intelligence."""
from __future__ import annotations

import re
from typing import Optional

import pandas as pd

STATES = ("Johor", "Negeri Sembilan")

OFF_TOPIC = re.compile(
    r"iran\b|nuclear|mindanao|beckham|paris:|london:|ukraine|gaza|"
    r"mushroom vape|lift accident|penang medical|penang.*hospital|"
    r"kota kinabalu|kuching|sarawak election|sabah election|"
    r"kelantan polls|pasir mas\b|tornado|earthquake|"
    r"world cup|premier league|celebrity gossip",
    re.I,
)

STATE_SIGNALS = {
    "Johor": re.compile(
        r"johor|柔佛|新山|士古来|skudai|stulang|muar|batu pahat|kluang|kulai|"
        r"pasir gudang|segamat|pontian|mersing|tangkak|nusajaya|gelang patah|"
        r"prn johor|pilihan raya johor|州选.*柔|柔佛州选",
        re.I,
    ),
    "Negeri Sembilan": re.compile(
        r"negeri sembilan|森美兰|森州|seremban|nilai|port dickson|bahau|"
        r"tampin|jempol|rembau|jelebu|mantin|lukut|prn n9|"
        r"pilihan raya negeri sembilan|森美兰.*州选",
        re.I,
    ),
}

POLITICAL_ACTIONABLE = re.compile(
    r"\bph\b|\bdap\b|pakatan|行动党|希盟|希联|"
    r"\bpas\b|伊党|parti islam|"
    r"\bpn\b|perikatan|国盟|gerakan|"
    r"\bbn\b|umno|国阵|巫统|muafakat|\bmn\b|巫伊|"
    r"boikot|boycott|不投票|abstain|"
    r"harakat|harakak|syurga|tak bau|天堂|shawn loh|罗盛年|"
    r"pengundi cina|komuniti cina|华人|华裔|"
    r"pengundi india|komuniti india|tamil|sjkt|mic\b|hindu|"
    r"prn|pilihan raya negeri|州选|dun n\d|calon|candidate|"
    r"kos sara hidup|cost of living|生活费|"
    r"sjkc|sjk c|华校|华小|"
    r"pekerjaan|employment|kilang|factory worker|gaji",
    re.I,
)

LOW_VALUE_OTHER = re.compile(
    r"^[\s\d\W]*$|breaking news alert|subscribe now|"
    r"click here for more|advertisement",
    re.I,
)

ACTIONABLE_CLUSTERS = {
    "Cost of Living",
    "Chinese Education",
    "SME and Business",
    "Local Government Services",
    "Water Supply",
    "Road and Traffic",
    "Employment",
    "Housing",
    "DAP Performance",
    "MCA Relevance",
    "Gerakan and PN",
    "PAS Factor",
    "PH-BN Relationship",
    "Candidate Performance",
    "Race and Religion",
    "Misinformation",
    "State Government Stability",
}


def _text(row: pd.Series) -> str:
    parts = [
        str(row.get("post_text") or ""),
        str(row.get("translated_text_bm") or ""),
        str(row.get("source_url") or ""),
        str(row.get("constituency") or ""),
        str(row.get("district") or ""),
    ]
    return " ".join(parts)


def detect_state(text: str, assigned: Optional[str]) -> Optional[str]:
    if assigned in STATES:
        if STATE_SIGNALS[assigned].search(text):
            return assigned
    scores = {s: len(STATE_SIGNALS[s].findall(text)) for s in STATES}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else None


def is_relevant_row(row: pd.Series) -> bool:
    text = _text(row)
    if not text.strip() or LOW_VALUE_OTHER.match(text[:80]):
        return False
    if OFF_TOPIC.search(text):
        # Allow if strong state + political signal overrides off-topic noise
        if not (POLITICAL_ACTIONABLE.search(text) and detect_state(text, row.get("state"))):
            return False

    state = detect_state(text, str(row.get("state") or ""))
    if not state:
        return False

    cluster = str(row.get("issue_cluster") or "Other")
    has_pol = bool(POLITICAL_ACTIONABLE.search(text))
    if cluster == "Other" and not has_pol:
        return False
    if cluster not in ACTIONABLE_CLUSTERS and not has_pol:
        return False

    return True


def filter_johor_n9(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()
    work = df[df["state"].isin(STATES)].copy() if "state" in df.columns else df.copy()
    mask = work.apply(is_relevant_row, axis=1)
    out = work[mask].copy()
    out["state"] = out.apply(lambda r: detect_state(_text(r), str(r.get("state") or "")), axis=1)
    return out.drop_duplicates(subset=["post_text", "platform", "published_at"], keep="first")
