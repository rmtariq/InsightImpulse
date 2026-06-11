"""
Shared helpers for normalizing crawl records across adapter + web backend.

Fixes:
- Nested ``comments`` lists stored as a column instead of flat rows
- Unix epoch seconds mis-parsed as nanoseconds in date filters
"""

from __future__ import annotations

import ast
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union

import pandas as pd


def normalize_crawl_date(value: Any) -> str:
    """Return ISO-8601 UTC string for posts/comments from any actor format."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return datetime.now(timezone.utc).isoformat()

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        n = float(value)
        if n > 1e12:
            ts = n / 1000.0  # milliseconds
        elif n > 1e9:
            ts = n  # unix seconds
        else:
            return datetime.now(timezone.utc).isoformat()
        return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()

    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).isoformat()

    if isinstance(value, dict):
        for key in ("iso", "date", "timestamp", "createdAt", "created_at"):
            if value.get(key):
                return normalize_crawl_date(value[key])
        return datetime.now(timezone.utc).isoformat()

    text = str(value).strip()
    if not text or text.lower() in ("nan", "none", "nat"):
        return datetime.now(timezone.utc).isoformat()

    parsed = pd.to_datetime(text, errors="coerce", utc=True)
    if pd.notna(parsed):
        return parsed.isoformat()

    return text


def _parse_nested_comments(raw: Any) -> List[Dict[str, Any]]:
    if raw is None or (isinstance(raw, float) and pd.isna(raw)):
        return []
    if isinstance(raw, list):
        return [c for c in raw if isinstance(c, dict)]
    if isinstance(raw, str):
        text = raw.strip()
        if not text or text in ("[]", "nan"):
            return []
        try:
            parsed = ast.literal_eval(text)
        except (ValueError, SyntaxError):
            try:
                parsed = json.loads(text)
            except json.JSONDecodeError:
                return []
        if isinstance(parsed, list):
            return [c for c in parsed if isinstance(c, dict)]
    return []


def flatten_crawl_records(records: Union[List[Dict[str, Any]], Dict[str, List[Dict[str, Any]]]]) -> List[Dict[str, Any]]:
    """
    Expand posts that carry nested ``comments`` into flat post + comment rows.
    Accepts a platform list or a {platform: records} dict from strategy crawls.
    """
    if isinstance(records, dict):
        flat: List[Dict[str, Any]] = []
        for platform_records in records.values():
            flat.extend(flatten_crawl_records(platform_records))
        return flat

    if not records:
        return []

    flat_rows: List[Dict[str, Any]] = []
    for item in records:
        if not isinstance(item, dict):
            continue

        post_copy = dict(item)
        nested = post_copy.pop("comments", None)
        if post_copy.get("Date") is not None:
            post_copy["Date"] = normalize_crawl_date(post_copy["Date"])
        if not post_copy.get("Type"):
            post_copy["Type"] = "post"
        flat_rows.append(post_copy)

        for comment in _parse_nested_comments(nested):
            c = dict(comment)
            if c.get("Date") is not None:
                c["Date"] = normalize_crawl_date(c["Date"])
            if not c.get("Type"):
                c["Type"] = "comment"
            flat_rows.append(c)

    return flat_rows


def parse_crawl_dates(series: pd.Series) -> pd.Series:
    """Parse Date column handling unix seconds, ms, and ISO strings."""
    if series.empty:
        return pd.to_datetime(series, errors="coerce", utc=True)

    def _one(val: Any):
        if val is None or (isinstance(val, float) and pd.isna(val)):
            return pd.NaT
        if isinstance(val, (int, float)) and not isinstance(val, bool):
            n = float(val)
            if n > 1e12:
                return pd.to_datetime(n, unit="ms", utc=True, errors="coerce")
            if n > 1e9:
                return pd.to_datetime(n, unit="s", utc=True, errors="coerce")
        return pd.to_datetime(val, errors="coerce", utc=True)

    return series.map(_one)


def fasa2_post_cap(platform: str, post_count: int) -> int:
    """Max posts to deep-comment crawl per platform (timeout-safe)."""
    caps = {
        "facebook": 40,
        "instagram": 50,
        "x": 40,
        "twitter": 40,
        "youtube": 30,
        "tiktok": 30,
    }
    return min(post_count, caps.get(platform.lower(), 30))


def effective_comments_per_post(platform: str, max_comments: int) -> int:
    """Per-post comment budget — avoid silently capping at 10 for all platforms."""
    platform = platform.lower()
    if platform in ("news", "google", "shopee", "lazada"):
        return 0
    if platform == "youtube":
        return min(max_comments, 50)
    if platform in ("facebook", "instagram"):
        return min(max(max_comments, 20), 30)
    if platform in ("x", "twitter"):
        return min(max(max_comments, 15), 30)
    if platform == "tiktok":
        return min(max_comments, 50)
    return min(max_comments, 30)
