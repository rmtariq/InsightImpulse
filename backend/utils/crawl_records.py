"""
Shared helpers for normalizing crawl records across adapter + web backend.

Fixes:
- Nested ``comments`` lists stored as a column instead of flat rows
- Unix epoch seconds mis-parsed as nanoseconds in date filters
"""

from __future__ import annotations

import ast
import json
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union

import pandas as pd

# Markers for single-post / video URLs (all supported platforms)
POST_URL_MARKERS = (
    # Facebook
    "/posts/",
    "story.php",
    "pfbid",
    "photo.php",
    "/share/p/",
    "/share/v/",
    # Instagram
    "/p/",
    "/reel/",
    "/tv/",
    # X / Twitter
    "/status/",
    # TikTok
    "/video/",
    # YouTube
    "watch?v=",
    "youtu.be/",
    "/shorts/",
    # Threads
    "/post/",
    # LinkedIn
    "/feed/update/",
    "urn:li:activity",
    "/posts/",
)


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


def is_direct_post_url(url: str) -> bool:
    """True when URL points at a specific post/video, not a page profile."""
    u = (url or "").lower()
    if "instagram.com" in u and ("/p/" in u or "/reel/" in u or "/tv/" in u):
        return True
    if ("twitter.com" in u or "x.com" in u) and "/status/" in u:
        return True
    if "tiktok.com" in u and "/video/" in u:
        return True
    if ("youtube.com" in u or "youtu.be" in u) and (
        "watch?v=" in u or "youtu.be/" in u or "/shorts/" in u
    ):
        return True
    if "threads.net" in u and "/post/" in u:
        return True
    if "linkedin.com" in u and ("/feed/update/" in u or "urn:li:activity" in u):
        return True
    if "facebook.com" in u or "fb.com" in u:
        return any(
            m in u
            for m in (
                "/share/p/",
                "/share/v/",
                "story.php",
                "pfbid",
                "/posts/",
                "photo.php",
            )
        )
    return any(marker in u for marker in POST_URL_MARKERS)


def sanitize_direct_url(url: str) -> str:
    """Clean WhatsApp-pasted URLs (timestamps glued to query string, trailing junk)."""
    url = (url or "").strip()
    if not url or url.startswith("#"):
        return ""
    url = url.split()[0]
    # WhatsApp often glues "8:11AM" to mibextid=wwXlfr → wwXlfr8:11AM
    url = re.sub(
        r"(mibextid=[A-Za-z_]+)\d{0,2}:\d{1,2}\s*[APMapm]*.*$",
        r"\1",
        url,
        flags=re.I,
    )
    url = re.sub(r"(mibextid=[A-Za-z0-9_]+)[^A-Za-z0-9_&/?#].*$", r"\1", url, flags=re.I)
    return url.rstrip(".,;)")


def sanitize_direct_urls(urls: List[str]) -> List[str]:
    cleaned: List[str] = []
    seen = set()
    for raw in urls or []:
        u = sanitize_direct_url(raw)
        if u and u not in seen:
            seen.add(u)
            cleaned.append(u)
    return cleaned


def resolve_direct_url_target(urls: List[str], explicit: str = "auto") -> str:
    """Return 'post' for explicit post batches, else 'page' (profile/page crawl)."""
    if explicit in ("page", "post"):
        return explicit
    if urls and all(is_direct_post_url(u) for u in urls):
        return "post"
    return "page"


def keep_direct_post_bundle_rows(df: pd.DataFrame) -> pd.DataFrame:
    """
    Direct Post URL mode: keep every crawled post plus all comments tied to it.
    User pasted explicit post URLs — do not drop posts/comments by date window.
    """
    if df.empty or "Type" not in df.columns:
        return df

    posts = df[df["Type"].astype(str).str.lower() == "post"]
    post_ids = {str(x) for x in posts["ID"].tolist()} if "ID" in posts.columns else set()
    post_urls = {str(x) for x in posts["URL"].tolist()} if "URL" in posts.columns else set()

    def _linked_to_post(row) -> bool:
        t = str(row.get("Type", "post")).lower()
        if t == "post":
            return True
        pid = str(row.get("Parent_Post_ID", "") or "")
        purl = str(row.get("Parent_Post_URL", "") or "")
        if pid and pid in post_ids:
            return True
        for p_id in post_ids:
            if p_id and len(p_id) > 6 and p_id in purl:
                return True
        for pu in post_urls:
            if pu and len(pu) > 12 and (pu in purl or purl in pu):
                return True
        return False

    mask = df.apply(_linked_to_post, axis=1)
    return df.loc[mask].copy()


def keep_post_date_filtered_bundle_rows(
    df: pd.DataFrame,
    date_filter: Dict[str, Any],
) -> pd.DataFrame:
    """
    Keyword/direct-page crawl: filter posts by date window, keep all comments
    tied to posts that survived the filter (comments often lack reliable dates).
    """
    if df.empty or "Date" not in df.columns:
        return df

    from backend.utils.crawl_records import parse_crawl_dates  # noqa: WPS433

    start = pd.Timestamp(date_filter["start_date"])
    end = pd.Timestamp(date_filter["end_date"])
    start = start.tz_localize("UTC") if start.tzinfo is None else start.tz_convert("UTC")
    end = end.tz_localize("UTC") if end.tzinfo is None else end.tz_convert("UTC")

    dates = parse_crawl_dates(df["Date"])
    if "Type" not in df.columns:
        mask = dates.notna() & (dates >= start) & (dates <= end)
        return df.loc[mask].copy()

    type_lower = df["Type"].astype(str).str.lower()
    post_mask = type_lower == "post"
    in_range_posts = post_mask & dates.notna() & (dates >= start) & (dates <= end)
    posts_df = df.loc[in_range_posts]
    post_ids = {str(x) for x in posts_df["ID"].tolist()} if "ID" in posts_df.columns else set()
    post_urls = {str(x) for x in posts_df["URL"].tolist()} if "URL" in posts_df.columns else set()

    def _keep_row(row) -> bool:
        t = str(row.get("Type", "post")).lower()
        if t == "post":
            return bool(in_range_posts.loc[row.name])
        pid = str(row.get("Parent_Post_ID", "") or "")
        purl = str(row.get("Parent_Post_URL", "") or "")
        if pid and pid in post_ids:
            return True
        for p_id in post_ids:
            if p_id and len(p_id) > 6 and p_id in purl:
                return True
        for pu in post_urls:
            if pu and len(pu) > 12 and (pu in purl or purl in pu):
                return True
        return False

    kept = df.loc[df.apply(_keep_row, axis=1)].copy()
    return kept


def fasa2_post_cap(platform: str, post_count: int) -> int:
    """Max posts to deep-comment crawl per platform (timeout-safe)."""
    caps = {
        "facebook": 40,
        "instagram": 50,
        "x": 40,
        "twitter": 40,
        "youtube": 30,
        "tiktok": 30,
        "threads": 6,
    }
    return min(post_count, caps.get(platform.lower(), 30))


def crawl_record_key(row: Dict[str, Any]) -> str:
    """Stable dedupe key for post/comment rows across multi-pass crawls."""
    row_type = str(row.get("Type") or row.get("type") or "post").lower()
    for field in ("ID", "id", "comment_id", "Comment_ID", "commentId"):
        val = row.get(field)
        if val not in (None, "", "nan"):
            return f"{row_type}:id:{val}"
    url = str(row.get("URL") or row.get("url") or row.get("Post_URL") or "")
    parent = str(row.get("Parent_Post_URL") or row.get("parent_post_url") or "")
    text = str(row.get("Text") or row.get("text") or row.get("message") or "")[:160]
    author = str(row.get("Author") or row.get("author") or row.get("profileName") or "")
    if url:
        return f"{row_type}:url:{url}|{author}|{text}"
    if parent:
        return f"{row_type}:parent:{parent}|{author}|{text}"
    return f"{row_type}:fallback:{author}|{text}"


def dedupe_crawl_records(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Return records with duplicates removed (first occurrence wins)."""
    seen: set[str] = set()
    out: List[Dict[str, Any]] = []
    for row in records:
        if not isinstance(row, dict):
            continue
        key = crawl_record_key(row)
        if key in seen:
            continue
        seen.add(key)
        out.append(row)
    return out


def merge_crawl_records(
    existing: List[Dict[str, Any]],
    new_rows: List[Dict[str, Any]],
) -> tuple[List[Dict[str, Any]], int, int]:
    """
    Merge new crawl rows into existing without duplicates.
    Returns (merged_list, added_count, skipped_duplicate_count).
    """
    merged = dedupe_crawl_records(list(existing or []))
    seen = {crawl_record_key(r) for r in merged}
    added = 0
    skipped = 0
    for row in new_rows or []:
        if not isinstance(row, dict):
            continue
        key = crawl_record_key(row)
        if key in seen:
            skipped += 1
            continue
        seen.add(key)
        merged.append(row)
        added += 1
    return merged, added, skipped


def multipass_plan(comment_target: int, *, per_pass: int = 1000, max_passes: int = 5) -> int:
    """Number of Apify passes needed for a comment target."""
    target = max(1, int(comment_target or per_pass))
    return min(max_passes, max(1, (target + per_pass - 1) // per_pass))


def effective_comments_per_post(
    platform: str,
    max_comments: int,
    *,
    direct_post_mode: bool = False,
) -> int:
    """Per-post comment budget — avoid silently capping at 10 for all platforms."""
    platform = platform.lower()
    if platform in ("news", "google", "shopee", "lazada"):
        return 0
    if direct_post_mode:
        caps = {
            "facebook": 1000,
            "instagram": 500,
            "youtube": 500,
            "x": 500,
            "twitter": 500,
            "tiktok": 500,
            "threads": 200,
            "linkedin": 200,
        }
        cap = caps.get(platform, 500)
        return min(max(max_comments, 50), cap)
    if platform == "youtube":
        return min(max_comments, 50)
    if platform in ("facebook", "instagram"):
        return min(max(max_comments, 20), 30)
    if platform in ("x", "twitter"):
        return min(max(max_comments, 15), 30)
    if platform == "tiktok":
        return min(max_comments, 50)
    return min(max_comments, 30)
