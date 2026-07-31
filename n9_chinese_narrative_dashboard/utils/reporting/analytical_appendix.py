"""Build analytical appendix payload (detailed data moved out of executive report)."""
from __future__ import annotations

from typing import Any

import pandas as pd

from utils.brief_generator import generate_brief
from utils.reporting.labels import normalize_issue
from utils.reporting.report_validation import sentiment_counts


def _safe(val, limit=200):
    s = str(val or "").strip()
    if not s or s.lower() in ("nan", "none"):
        return "—"
    return s[:limit] + ("…" if len(s) > limit else "")


def build_appendix_payload(sub: pd.DataFrame, state: str, meta: dict) -> dict[str, Any]:
    sc = sentiment_counts(sub)
    posts = sub
    if not sub.empty and "engagement_total" in sub.columns:
        posts = sub.sort_values("engagement_total", ascending=False).head(50)

    voice = []
    for _, r in posts.head(15).iterrows():
        voice.append({
            "platform": _safe(r.get("platform"), 30),
            "issue": normalize_issue(r.get("issue_cluster")),
            "sentiment": _safe(r.get("sentiment"), 12),
            "original": _safe(r.get("post_text"), 300),
            "translation_bm": _safe(r.get("translated_text_bm"), 300),
            "url": _safe(r.get("source_url"), 120),
            "engagement": str(int(r.get("engagement_total", 0) or 0)),
        })

    tables = {}
    for key, col in [("sentiment", "sentiment"), ("platform", "platform"), ("issues", "issue_cluster"), ("languages", "language_detected")]:
        if col in sub.columns and not sub.empty:
            if col == "issue_cluster":
                vc = sub[col].apply(normalize_issue).value_counts().head(20)
            else:
                vc = sub[col].value_counts().head(20)
            tables[key] = [[str(k), str(v)] for k, v in vc.items()]
        else:
            tables[key] = []

    risk_rows = []
    if "risk_level" in sub.columns:
        hi = sub[sub["risk_level"].astype(str).isin(["High", "Critical"])]
        for _, r in hi.head(20).iterrows():
            risk_rows.append([_safe(r.get("risk_level")), normalize_issue(r.get("issue_cluster")), _safe(r.get("post_text"), 120)])

    return {
        "report_type": "appendix",
        "state": state,
        "meta": meta,
        "record_count": len(sub),
        "sentiment_detail": sc,
        "voice_quotes": voice,
        "tables": tables,
        "risk_rows": risk_rows,
        "all_posts_sample": [
            [_safe(r.get("platform"), 20), normalize_issue(r.get("issue_cluster")),
             _safe(r.get("sentiment"), 10), _safe(r.get("post_text"), 100), _safe(r.get("source_url"), 80)]
            for _, r in posts.iterrows()
        ],
        "brief": generate_brief(sub, pd.DataFrame(), pd.DataFrame(), state=state),
        "methodology": [
            "Sumber: crawl berita dan media sosial awam (InsightPulse).",
            "Sentimen: model analitik — bukan polling undi.",
            "Isu: pengelasan keyword + semakan manusia digalakkan.",
            "Other ditukar kepada Belum Diklasifikasikan dalam laporan eksekutif.",
        ],
    }
