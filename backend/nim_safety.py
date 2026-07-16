"""Optional Nemotron Content Safety enrichment.

This module is deliberately fail-open: if the safety NIM is unavailable, the
existing alert/action pipeline continues unchanged.
"""
from __future__ import annotations

import json
import os
from typing import Any

import pandas as pd
import requests


SAFETY_URL = os.getenv("NIM_SAFETY_URL", "http://localhost:8003")
SAFETY_MODEL = os.getenv("NIM_SAFETY_MODEL", "nemotron-content-safety")
SENSITIVE_CATEGORIES = {"racial", "religious", "hate", "violence", "self_harm", "harmful", "sexual"}


def safety_enabled() -> bool:
    return os.getenv("NIM_SAFETY_ENABLED", "").lower() in {"1", "true", "yes", "on"}


def classify_text(text: str, *, timeout: int = 30) -> dict[str, Any]:
    """Classify a text snippet with a NIM safety endpoint."""
    if not text.strip():
        return {"flagged": False, "categories": [], "severity": "low"}

    payload = {
        "model": SAFETY_MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "Classify political social media content safety. Return JSON only with: "
                    "flagged boolean, severity low|medium|high|critical, categories array, reason string."
                ),
            },
            {"role": "user", "content": text[:3000]},
        ],
        "temperature": 0,
        "response_format": {"type": "json_object"},
    }
    response = requests.post(f"{SAFETY_URL}/v1/chat/completions", json=payload, timeout=timeout)
    response.raise_for_status()
    raw = response.json()["choices"][0]["message"]["content"] or "{}"
    data = json.loads(raw)
    categories = [str(c).lower() for c in data.get("categories", [])]
    flagged = bool(data.get("flagged")) or bool(SENSITIVE_CATEGORIES.intersection(categories))
    return {
        "flagged": flagged,
        "categories": categories,
        "severity": str(data.get("severity") or ("high" if flagged else "low")).lower(),
        "reason": str(data.get("reason") or ""),
    }


def enrich_posts_with_safety(
    posts: pd.DataFrame,
    *,
    text_col: str = "post_text",
    max_rows: int = 200,
) -> pd.DataFrame:
    """Return posts with NIM safety columns added when enabled."""
    if posts is None or posts.empty or not safety_enabled() or text_col not in posts.columns:
        return posts

    out = posts.copy()
    for idx, row in out.head(max_rows).iterrows():
        if str(row.get("nim_safety_checked") or "").lower() == "true":
            continue
        try:
            result = classify_text(str(row.get(text_col) or ""))
            out.at[idx, "nim_safety_checked"] = True
            out.at[idx, "nim_safety_flagged"] = result["flagged"]
            out.at[idx, "nim_safety_severity"] = result["severity"]
            out.at[idx, "nim_safety_categories"] = ",".join(result["categories"])
            out.at[idx, "nim_safety_reason"] = result["reason"]
        except Exception as exc:
            out.at[idx, "nim_safety_checked"] = False
            out.at[idx, "nim_safety_error"] = str(exc)
    return out
