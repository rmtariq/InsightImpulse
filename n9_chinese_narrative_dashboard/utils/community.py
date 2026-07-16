"""Community tagging for narrative streams."""
from __future__ import annotations

import pandas as pd

COMMUNITY_LABELS = {
    "chinese": "Naratif Cina",
    "indian": "Naratif India",
    "cross": "Merentas Komuniti",
    "general": "Umum",
}

COMMUNITY_COLORS = {
    "chinese": "#f43f5e",   # rose
    "indian": "#a855f7",    # purple
    "cross": "#06b6d4",     # cyan
    "general": "#64748b",   # slate
}

INDIA_TEXT_SIGNALS = (
    "indian", "tamil", "mic ", "hindu", "komuniti india", "pengundi india",
    "malaysia nanban", "makkal osai", "makkalosai", "varnam", "vanakkam", "sjkt",
)


def infer_community(row) -> str:
    # Explicit tag from crawl pipeline
    for col in ("crawl_community", "Community", "community"):
        val = str(row.get(col) or "").strip().lower()
        if val == "india":
            return "indian"
        if val in ("cina", "chinese"):
            return "chinese"

    lang = str(row.get("language_detected", "") or "").lower()
    plat = str(row.get("platform", "") or "").lower()
    jenis = str(row.get("jenis_suara", "") or "").lower()
    src = str(row.get("source_category", "") or "").lower()
    text = str(row.get("post_text", "") or "").lower()
    url = str(row.get("source_url", "") or "").lower()

    if any(x in lang for x in ("zh", "cn", "tw")) or "chinese" in plat or "cina" in jenis:
        return "chinese"

    if (
        any(x in lang for x in ("ta", "tamil"))
        or "india" in plat
        or "india" in jenis
        or "tamil" in src
        or "indian" in plat
        or any(d in url for d in ("nanban", "makkalosai", "makkal", "varnam", "vanakkam", "tamilmalar"))
        or (any(s in text for s in INDIA_TEXT_SIGNALS) and "media_india" in jenis)
    ):
        return "indian"

    if any(x in lang for x in ("ms", "en")) and "chinese" not in plat:
        return "cross"
    return "general"


def add_community_column(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return df
    out = df.copy()
    out["community"] = out.apply(infer_community, axis=1)
    return out


def filter_community(df: pd.DataFrame, community: str) -> pd.DataFrame:
    if df is None or df.empty or "community" not in df.columns:
        return df
    if community == "all":
        return df
    return df[df["community"] == community].copy()
