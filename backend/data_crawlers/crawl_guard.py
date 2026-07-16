"""
Crawl cost & duration guards — prevent 56-keyword OR explosions.

Env:
  APIFY_MAX_OR_SPLIT=5       Max OR terms before using single combined query
  APIFY_MAX_KW_CONCURRENT=3  Parallel keyword jobs when split is allowed
  APIFY_THREADS_REPLY_POSTS=6  Max Threads posts for deep reply crawl
"""
from __future__ import annotations

import os
import re
from typing import List, Tuple

# Max OR fragments — above this, crawl ONE combined boolean query (fast + cheap)
MAX_OR_KEYWORD_SPLIT = int(os.getenv("APIFY_MAX_OR_SPLIT", "5"))
MAX_KEYWORD_BATCH_CONCURRENT = int(os.getenv("APIFY_MAX_KW_CONCURRENT", "3"))
THREADS_REPLY_POST_CAP = int(os.getenv("APIFY_THREADS_REPLY_POSTS", "6"))

WHEN_SUFFIX_RE = re.compile(r"\)\s*(when:\d+[dhm]?)\s*$", re.I)
WHEN_INLINE_RE = re.compile(r"\bwhen:\d+[dhm]?\b", re.I)


def extract_when_suffix(query: str) -> Tuple[str, str]:
    """Return (core_query, when_suffix e.g. 'when:7d')."""
    q = query.strip()
    m = WHEN_SUFFIX_RE.search(q)
    if m:
        when = m.group(1)
        core = q[: m.start()].strip()
        if core.startswith("(") and core.endswith(")"):
            core = core[1:-1].strip()
        return core, when
    inline = WHEN_INLINE_RE.search(q)
    if inline:
        when = inline.group(0)
        core = WHEN_INLINE_RE.sub("", q).strip()
        if core.startswith("(") and core.endswith(")"):
            core = core[1:-1].strip()
        return core, when
    return q, ""


def _split_top_level_or(query: str) -> List[str]:
    """Split on OR only outside quotes and parentheses."""
    parts: List[str] = []
    buf: List[str] = []
    depth = 0
    in_quote: str | None = None
    i = 0
    n = len(query)
    while i < n:
        ch = query[i]
        if in_quote:
            buf.append(ch)
            if ch == in_quote and (i == 0 or query[i - 1] != "\\"):
                in_quote = None
            i += 1
            continue
        if ch in "\"'":
            in_quote = ch
            buf.append(ch)
            i += 1
            continue
        if ch == "(":
            depth += 1
            buf.append(ch)
            i += 1
            continue
        if ch == ")" and depth > 0:
            depth -= 1
            buf.append(ch)
            i += 1
            continue
        if depth == 0 and query[i : i + 4].upper() == " OR ":
            part = "".join(buf).strip()
            if part:
                parts.append(part)
            buf = []
            i += 4
            continue
        buf.append(ch)
        i += 1
    tail = "".join(buf).strip()
    if tail:
        parts.append(tail)
    return parts


def split_or_keywords(query: str) -> List[str]:
    core, when = extract_when_suffix(query)
    parts = _split_top_level_or(core)
    if when:
        parts = [p if WHEN_INLINE_RE.search(p) else f"{p} {when}" for p in parts]
    return parts


def or_keyword_count(query: str) -> int:
    if " OR " not in query.upper():
        return 1
    return len(split_or_keywords(query))


def should_split_or_query(query: str) -> bool:
    """Only split short OR lists; long queries run as one Apify boolean search."""
    n = or_keyword_count(query)
    return n > 1 and n <= MAX_OR_KEYWORD_SPLIT


def guard_message(query: str) -> str:
    n = or_keyword_count(query)
    if n <= MAX_OR_KEYWORD_SPLIT:
        return f"OR query: {n} keyword(s) — OK"
    return (
        f"OR query has {n} terms (max split={MAX_OR_KEYWORD_SPLIT}). "
        f"Using SINGLE combined query — faster, lower Apify cost."
    )
