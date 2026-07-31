"""Data cleaning and enrichment for narrative posts."""
from __future__ import annotations

import re

import pandas as pd

from utils.keyword_classifier import classify_issue

POST_COLUMNS = [
    "state", "post_id", "platform", "account_name", "account_type", "source_category",
    "source_url", "published_at", "post_text", "translated_text_bm",
    "language_detected", "constituency", "dun_code", "district",
    "party_mentioned", "candidate_mentioned", "issue_cluster", "sentiment",
    "sentiment_score", "emotion", "likes", "comments", "shares", "views",
    "engagement_total", "stance_dap", "stance_mca", "stance_pn", "stance_bn",
    "ethnic_sensitive_flag", "religion_sensitive_flag", "misinformation_flag",
    "risk_level", "query_id", "jenis_suara", "weight_analisis",
]

NUMERIC_COLS = ["likes", "comments", "shares", "views", "engagement_total", "sentiment_score"]
BOOL_COLS = ["ethnic_sensitive_flag", "religion_sensitive_flag", "misinformation_flag"]


def _parse_published(val) -> pd.Timestamp:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return pd.NaT
    if isinstance(val, pd.Timestamp):
        return val
    s = str(val).strip()
    if not s or s.lower() in ("nan", "none"):
        return pd.NaT
    try:
        dt = pd.to_datetime(s, utc=True)
        return dt.tz_convert(None) if dt.tzinfo is not None else dt
    except Exception:
        return pd.to_datetime(s, errors="coerce")


def _date_from_url(url: str) -> pd.Timestamp:
    m = re.search(r"/(\d{4})/(\d{2})/(\d{2})/", str(url))
    if m:
        return pd.Timestamp(f"{m.group(1)}-{m.group(2)}-{m.group(3)}")
    return pd.NaT


def _safe_numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").fillna(0)


def clean_posts(df: pd.DataFrame) -> pd.DataFrame:
    """Clean posts: dedupe, fill numerics, compute engagement, classify issues."""
    if df is None or df.empty:
        return pd.DataFrame(columns=POST_COLUMNS)

    out = df.copy()

    # Ensure expected columns exist
    for col in POST_COLUMNS:
        if col not in out.columns:
            out[col] = None

    # Datetime — per-row parse (mixed sample vs RSS ISO+timezone)
    raw_dates = out["published_at"].copy()
    out["published_at"] = raw_dates.apply(_parse_published)
    na = out["published_at"].isna()
    if na.any() and "source_url" in out.columns:
        out.loc[na, "published_at"] = out.loc[na, "source_url"].map(_date_from_url)

    # Numerics
    for col in NUMERIC_COLS:
        if col in out.columns:
            out[col] = _safe_numeric(out[col])

    for col in BOOL_COLS:
        if col in out.columns:
            out[col] = out[col].astype(str).str.lower().isin(["true", "1", "yes", "y"])

    # Engagement
    out["likes"] = _safe_numeric(out["likes"])
    out["comments"] = _safe_numeric(out["comments"])
    out["shares"] = _safe_numeric(out["shares"])
    out["views"] = _safe_numeric(out["views"])
    out["engagement_total"] = out["likes"] + out["comments"] + out["shares"]

    # Engagement rate
    out["engagement_rate"] = 0.0
    mask = out["views"] > 0
    out.loc[mask, "engagement_rate"] = (
        out.loc[mask, "engagement_total"] / out.loc[mask, "views"] * 100
    ).round(2)

    # Issue cluster fallback
    out["issue_cluster"] = out.apply(
        lambda r: classify_issue(
            f"{r.get('post_text', '')} {r.get('translated_text_bm', '')}",
            r.get("issue_cluster"),
        ),
        axis=1,
    )

    # Dedupe exact post_text + platform + published_at
    if "post_text" in out.columns:
        out = out.drop_duplicates(subset=["post_text", "platform", "published_at"], keep="first")

    # Bersihkan placeholder terjemahan
    if "translated_text_bm" in out.columns:
        ph = out["translated_text_bm"].astype(str).str.match(r"^\[BM\]", na=False)
        out.loc[ph, "translated_text_bm"] = ""

    # Default risk
    out["risk_level"] = out["risk_level"].fillna("Low").astype(str)
    if "state" in out.columns:
        out["state"] = out["state"].fillna("Negeri Sembilan").astype(str)

    return out


def data_quality_report(df: pd.DataFrame) -> dict:
    """Return data quality metrics."""
    if df is None or df.empty:
        return {k: 0 for k in [
            "missing_post_text", "missing_published_at", "missing_platform",
            "missing_location", "missing_sentiment", "duplicates", "invalid_urls",
        ]}

    invalid_urls = 0
    if "source_url" in df.columns:
        invalid_urls = int(
            (~df["source_url"].astype(str).str.startswith("http", na=False)).sum()
        )

    missing_loc = 0
    if "district" in df.columns and "constituency" in df.columns:
        missing_loc = int(
            (df["district"].isna() & df["constituency"].isna()).sum()
        )

    return {
        "missing_post_text": int(df["post_text"].isna().sum()) if "post_text" in df.columns else 0,
        "missing_published_at": int(df["published_at"].isna().sum()) if "published_at" in df.columns else 0,
        "missing_platform": int(df["platform"].isna().sum()) if "platform" in df.columns else 0,
        "missing_location": missing_loc,
        "missing_sentiment": int(df["sentiment"].isna().sum()) if "sentiment" in df.columns else 0,
        "duplicates": 0,
        "invalid_urls": invalid_urls,
        "total_rows": len(df),
    }
