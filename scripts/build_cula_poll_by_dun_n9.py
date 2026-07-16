#!/usr/bin/env python3
"""Build Cula Digital poll aggregates (MN/Solo, Labu) per DUN for War Room."""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

PROTO_DATA = ROOT / "data/projects/political/PRN/PRN_N9/reports/war_room/prototype/data"
OUT_POLL = PROTO_DATA / "cula_poll_by_dun_N9.json"
OUT_SUMMARY = PROTO_DATA / "cula_poll_summary_N9.json"
MYT = timezone(timedelta(hours=8))


def _json_safe(obj):
    if isinstance(obj, dict):
        return {k: _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_json_safe(v) for v in obj]
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if pd.isna(obj):
        return None
    return obj


# Primary DUN per post (avoid double-count in byDun totals)
POST_PAGE_META = {
    "PASRembau": {
        "label": "PAS Rembau",
        "primary_dun": "N27",
        "related_duns": ["N26", "N28"],
        "district": "Rembau",
    },
    "pemudapasrembau": {
        "label": "Pemuda PAS Rembau",
        "primary_dun": "N27",
        "related_duns": ["N26"],
        "district": "Rembau",
    },
    "PASChembong": {
        "label": "PAS Chembong",
        "primary_dun": "N26",
        "related_duns": [],
        "district": "Rembau",
    },
    "PASDUNKota": {
        "label": "PAS DUN Kota",
        "primary_dun": "N28",
        "related_duns": [],
        "district": "Rembau",
    },
    "pasportdickson": {
        "label": "PAS Kawasan Port Dickson",
        "primary_dun": "N33",
        "related_duns": ["N29", "N30", "N31", "N32"],
        "district": "Port Dickson",
    },
    "paskawasanrasah": {
        "label": "PAS Kawasan Rasah (soalan Labu)",
        "primary_dun": "N20",
        "related_duns": [],
        "district": "Seremban",
    },
    "permalink.php": {
        "label": "Inche Curry",
        "primary_dun": "N26",
        "related_duns": ["N27"],
        "district": "Rembau",
    },
}

REPORT_BUCKETS_MN = ("MN", "Solo", "Pro-PAS", "Pro-PH")
REPORT_BUCKETS_LABU = ("Sokong PAS", "Tak Sokong PAS")
EXPANDED_BUCKETS_MN = REPORT_BUCKETS_MN + ("Masih Tidak Jelas",)
EXPANDED_BUCKETS_LABU = REPORT_BUCKETS_LABU + ("Masih Tidak Jelas",)

ASSUMPTION_MAP_MN = {
    "Assume→Soft Pro-PAS/Pro-post": "Pro-PAS",
    "Assume→Soft Kritik/Lawan": "Pro-PH",
    "Assume→Masih Tidak Jelas": "Masih Tidak Jelas",
}
ASSUMPTION_MAP_LABU = {
    "Assume→Condong Sokong PAS": "Sokong PAS",
    "Assume→Condong Tak Sokong/Kritik": "Tak Sokong PAS",
    "Assume→Masih Tidak Jelas": "Masih Tidak Jelas",
}


def _page_key(url: str) -> str:
    m = re.search(r"facebook\.com/([^/?]+)", str(url or ""))
    return m.group(1) if m else ""


def _demo_pct(series: pd.Series) -> dict[str, int]:
    if series.empty:
        return {}
    c = series.fillna("Unknown").value_counts()
    total = len(series)
    out: dict[str, int] = {}
    mapping = {
        "Malay/Bumiputera": "malay",
        "Chinese": "chinese",
        "Indian": "indian",
        "Mixed/Urban": "urban",
        "Unknown": "unknown",
    }
    for label, key in mapping.items():
        n = int(c.get(label, 0))
        if n:
            out[key] = round(n / total * 100)
    return out


def _effective_bucket(row: pd.Series, issue: str) -> str:
    bucket = str(row.get("cula_bucket", ""))
    if bucket != "Tidak Jelas":
        return bucket
    assumption = str(row.get("cula_assumption", ""))
    mapping = ASSUMPTION_MAP_LABU if issue == "PAS Labu" else ASSUMPTION_MAP_MN
    return mapping.get(assumption, "Masih Tidak Jelas")


def _bucket_counts(sub: pd.DataFrame, issue: str) -> dict:
    if sub.empty:
        return {}
    # Keyword/debat jelas sahaja — tanpa assumption
    if issue == "PAS Labu":
        keys = REPORT_BUCKETS_LABU
    else:
        keys = REPORT_BUCKETS_MN
    counts = {k: int((sub["cula_bucket"] == k).sum()) for k in keys}
    counts["reported_total"] = sum(counts.values())
    counts["tidakJelas"] = int((sub["cula_bucket"] == "Tidak Jelas").sum())
    return counts


def _bucket_counts_expanded(sub: pd.DataFrame, issue: str) -> dict:
    if sub.empty:
        return {}
    keys = EXPANDED_BUCKETS_LABU if issue == "PAS Labu" else EXPANDED_BUCKETS_MN
    expanded = sub.apply(lambda r: _effective_bucket(r, issue), axis=1)
    counts = {k: int((expanded == k).sum()) for k in keys}
    counts["reported_total"] = int(len(sub))
    counts["tidakJelasResolved"] = int((sub["cula_bucket"] == "Tidak Jelas").sum())
    return counts


def _pct_from_counts(counts: dict, keys: tuple[str, ...]) -> dict[str, float]:
    total = sum(counts.get(k, 0) for k in keys) or 1
    return {k: round(counts.get(k, 0) / total * 100, 1) for k in keys}


def _sentiment_mix(sub: pd.DataFrame) -> dict[str, int]:
    if sub.empty or "sentiment_label" not in sub.columns:
        return {}
    c = sub["sentiment_label"].fillna("neutral").value_counts()
    total = len(sub)
    return {k: round(v / total * 100) for k, v in c.items()}


def _emotion_top(sub: pd.DataFrame) -> str | None:
    if sub.empty or "emotion_primary" not in sub.columns:
        return None
    c = sub["emotion_primary"].fillna("").value_counts()
    return str(c.index[0]) if len(c) else None


def build_from_csv(csv_path: Path) -> dict:
    df = pd.read_csv(csv_path)
    type_col = "Type" if "Type" in df.columns else "type"
    posts = df[df[type_col].astype(str).str.lower() == "post"].copy()
    comments = df[df[type_col].astype(str).str.lower() == "comment"].copy()

    if "cula_bucket" not in comments.columns:
        raise SystemExit("CSV missing cula_bucket — run: python3 scripts/classify_cula_debate.py <csv>")

    by_post: list[dict] = []
    by_dun: dict[str, dict] = defaultdict(lambda: {"posts": [], "mnVsSolo": None, "pasLabu": None})

    for _, p in posts.iterrows():
        url = str(p.get("URL", ""))
        page = _page_key(url)
        meta = POST_PAGE_META.get(page)
        if not meta:
            continue
        sub = comments[comments["Parent_Post_URL"].fillna("") == url]
        issue = str(sub["cula_issue"].iloc[0]) if len(sub) else (
            "PAS Labu" if "Labu" in str(p.get("Text", "")) else "MN vs Solo"
        )
        buckets = _bucket_counts(sub, issue)
        bucketsExpanded = _bucket_counts_expanded(sub, issue)
        post_obj = {
            "postId": str(p.get("ID", "")),
            "page": meta["label"],
            "url": url,
            "primaryDun": meta["primary_dun"],
            "relatedDuns": meta["related_duns"],
            "district": meta["district"],
            "issue": issue,
            "question": str(p.get("Text", ""))[:280],
            "commentsCrawled": int(len(sub)),
            "engagement": int((p.get("total_engagement") or 0) + sub.get("total_engagement", pd.Series(dtype=float)).sum()),
            "likes": int(p.get("likes") or 0),
            "buckets": buckets,
            "bucketsExpanded": bucketsExpanded,
            "assumption": dict(sub["cula_assumption"].value_counts()) if "cula_assumption" in sub.columns else {},
            "demographic": _demo_pct(sub.get("author_demographic", pd.Series(dtype=str))),
            "sentiment": _sentiment_mix(sub),
            "emotionTop": _emotion_top(sub),
            "insight": _post_insight(issue, bucketsExpanded, expanded=True),
            "insightKeyword": _post_insight(issue, buckets, expanded=False),
        }
        by_post.append(post_obj)

        dun = meta["primary_dun"]
        slot = by_dun[dun]
        slot["posts"].append(post_obj)
        if issue == "PAS Labu":
            slot["pasLabu"] = _merge_issue(slot.get("pasLabu"), post_obj)
        else:
            slot["mnVsSolo"] = _merge_issue(slot.get("mnVsSolo"), post_obj)

    # State rollup (each post counted once)
    mn_posts = [p for p in by_post if p["issue"] == "MN vs Solo"]
    labu_posts = [p for p in by_post if p["issue"] == "PAS Labu"]

    def rollup(posts_list: list[dict], issue: str) -> dict:
        keys_kw = REPORT_BUCKETS_LABU if issue == "PAS Labu" else REPORT_BUCKETS_MN
        keys_ex = EXPANDED_BUCKETS_LABU if issue == "PAS Labu" else EXPANDED_BUCKETS_MN
        totals_kw = {k: sum(p["buckets"].get(k, 0) for p in posts_list) for k in keys_kw}
        totals_ex = {k: sum(p["bucketsExpanded"].get(k, 0) for p in posts_list) for k in keys_ex}
        total_kw = sum(totals_kw.values()) or 1
        total_ex = sum(totals_ex.get(k, 0) for k in keys_ex) or 1
        return {
            "posts": len(posts_list),
            "commentsTotal": int(sum(p["commentsCrawled"] for p in posts_list)),
            "commentsKeyword": sum(totals_kw.values()),
            "commentsReported": total_ex,
            "buckets": totals_kw,
            "bucketsExpanded": totals_ex,
            "pct": _pct_from_counts(totals_kw, keys_kw),
            "pctExpanded": _pct_from_counts(totals_ex, keys_ex),
            "tidakJelasResolved": sum(p["buckets"].get("tidakJelas", 0) for p in posts_list),
            "engagement": sum(p["engagement"] for p in posts_list),
            "insight": _post_insight(issue, totals_ex, expanded=True),
            "insightKeyword": _post_insight(issue, totals_kw, expanded=False),
        }

    payload = {
        "meta": {
            "generated": datetime.now(MYT).strftime("%Y-%m-%d %H:%M:%S"),
            "sourceCsv": str(csv_path.relative_to(ROOT)) if csv_path.is_relative_to(ROOT) else str(csv_path),
            "batch": "cula_digital_whatsapp_7posts_20260702",
            "totalRows": int(len(df)),
            "totalPosts": len(by_post),
            "totalComments": int(len(comments)),
            "totalEngagement": int(sum(p["engagement"] for p in by_post)),
            "note": "Semua komen termasuk Tidak Jelas — dipecahkan via cula_assumption (sentiment+emotion).",
            "labelling": "3-tier: Jelas + Debat→condong + Tidak Jelas→assumption",
        },
        "stateRollup": {
            "mnVsSolo": rollup(mn_posts, "MN vs Solo"),
            "pasLabu": rollup(labu_posts, "PAS Labu"),
        },
        "byPost": by_post,
        "byDun": {k: v for k, v in sorted(by_dun.items())},
    }
    return payload


def _merge_issue(existing: dict | None, post: dict) -> dict:
    if not existing:
        return {
            "posts": 1,
            "commentsReported": post["bucketsExpanded"].get("reported_total", 0),
            "commentsKeyword": post["buckets"].get("reported_total", 0),
            "buckets": dict(post["buckets"]),
            "bucketsExpanded": dict(post["bucketsExpanded"]),
            "engagement": post["engagement"],
            "insight": post["insight"],
            "insightKeyword": post.get("insightKeyword"),
        }
    buckets = dict(existing.get("buckets") or {})
    buckets_ex = dict(existing.get("bucketsExpanded") or {})
    for src, dest in ((post["buckets"], buckets), (post["bucketsExpanded"], buckets_ex)):
        for k, v in src.items():
            if k == "reported_total":
                continue
            dest[k] = dest.get(k, 0) + v
    buckets["reported_total"] = sum(buckets.get(k, 0) for k in buckets if k not in ("reported_total", "tidakJelas"))
    buckets_ex["reported_total"] = sum(
        buckets_ex.get(k, 0) for k in buckets_ex if k not in ("reported_total", "tidakJelasResolved")
    )
    issue = "PAS Labu" if "Sokong PAS" in buckets_ex else "MN vs Solo"
    return {
        "posts": existing["posts"] + 1,
        "commentsReported": buckets_ex["reported_total"],
        "commentsKeyword": buckets.get("reported_total", 0),
        "buckets": buckets,
        "bucketsExpanded": buckets_ex,
        "engagement": existing["engagement"] + post["engagement"],
        "insight": _post_insight(
            issue,
            {k: buckets_ex.get(k, 0) for k in buckets_ex if k not in ("reported_total", "tidakJelasResolved")},
            expanded=True,
        ),
        "insightKeyword": _post_insight(
            issue,
            {k: buckets.get(k, 0) for k in buckets if k not in ("reported_total", "tidakJelas")},
            expanded=False,
        ),
    }


def _post_insight(issue: str, buckets: dict, *, expanded: bool) -> str:
    suffix = "semua komen" if expanded else "keyword jelas+debat"
    if issue == "PAS Labu":
        s = buckets.get("Sokong PAS", 0)
        t = buckets.get("Tak Sokong PAS", 0)
        m = buckets.get("Masih Tidak Jelas", 0)
        total = s + t + (m if expanded else 0)
        if not total:
            return "Belum cukup jawapan."
        base = f"Sokong PAS {round(s/total*100)}% vs tak {round(t/total*100)}%"
        if expanded and m:
            return f"{base} · {m} masih tidak jelas ({suffix})."
        return f"{base} ({suffix})."
    mn = buckets.get("MN", 0)
    solo = buckets.get("Solo", 0)
    pp = buckets.get("Pro-PAS", 0)
    ph = buckets.get("Pro-PH", 0)
    m = buckets.get("Masih Tidak Jelas", 0)
    if expanded:
        total = mn + solo + pp + ph + m
        if not total:
            return "Tiada komen."
        return (
            f"MN {mn} · Solo {solo} · Pro-PAS {pp} · Pro-PH {ph}"
            + (f" · Masih {m}" if m else "")
            + f" ({suffix})."
        )
    total = mn + solo
    if not total:
        return f"Debat dominan · Pro-PAS {pp} · Pro-PH {ph} ({suffix})."
    return f"MN {round(mn/total*100)}% vs Solo {round(solo/total*100)}% ({suffix})."


def _headline_mn(rollup: dict) -> str:
    b = rollup.get("bucketsExpanded") or rollup.get("buckets") or {}
    return (
        f"MN {b.get('MN', 0)} · Solo {b.get('Solo', 0)} · Pro-PAS {b.get('Pro-PAS', 0)} · "
        f"Pro-PH {b.get('Pro-PH', 0)} · {rollup.get('posts', 0)} post · {rollup.get('commentsReported', 0)} komen"
    )


def _headline_labu(rollup: dict) -> str:
    b = rollup.get("bucketsExpanded") or rollup.get("buckets") or {}
    return (
        f"Sokong {b.get('Sokong PAS', 0)} · Tak {b.get('Tak Sokong PAS', 0)} · "
        f"Masih {b.get('Masih Tidak Jelas', 0)} · {rollup.get('posts', 0)} post"
    )


def build_summary(payload: dict) -> dict:
    mn = payload["stateRollup"]["mnVsSolo"]
    labu = payload["stateRollup"]["pasLabu"]
    return {
        "meta": payload["meta"],
        "mnVsSolo": {
            "headline": _headline_mn(mn),
            "headlineKeyword": f"MN {mn['buckets'].get('MN', 0)} · Solo {mn['buckets'].get('Solo', 0)} (keyword sahaja)",
            "pct": mn["pctExpanded"],
            "pctKeyword": mn["pct"],
            "bucketsExpanded": mn["bucketsExpanded"],
            "bucketsKeyword": mn["buckets"],
            "tidakJelasResolved": mn.get("tidakJelasResolved", 0),
            "insight": mn["insight"],
            "insightKeyword": mn.get("insightKeyword"),
            "engagement": mn["engagement"],
            "commentsTotal": mn.get("commentsTotal"),
        },
        "pasLabu": {
            "headline": _headline_labu(labu),
            "headlineKeyword": f"Sokong {labu['buckets'].get('Sokong PAS', 0)} · Tak {labu['buckets'].get('Tak Sokong PAS', 0)} (keyword sahaja)",
            "pct": labu["pctExpanded"],
            "pctKeyword": labu["pct"],
            "bucketsExpanded": labu["bucketsExpanded"],
            "bucketsKeyword": labu["buckets"],
            "tidakJelasResolved": labu.get("tidakJelasResolved", 0),
            "insight": labu["insight"],
            "insightKeyword": labu.get("insightKeyword"),
            "engagement": labu["engagement"],
            "commentsTotal": labu.get("commentsTotal"),
        },
        "dunsWithData": sorted(payload["byDun"].keys()),
    }


def find_default_csv() -> Path:
    candidates = [
        ROOT / "data/combined/Combined_facebook_20260702_204813.csv",
        ROOT / "data/projects/political/pas_break_2026/crawls/pas_break_social_20260702_204813.csv",
    ]
    for p in candidates:
        if p.exists():
            return p
    combined = sorted((ROOT / "data/combined").glob("Combined_facebook_*.csv"), reverse=True)
    if combined:
        return combined[0]
    raise SystemExit("No labelled Cula CSV found")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build cula_poll_by_dun_N9.json for War Room")
    parser.add_argument("csv_path", type=Path, nargs="?", default=None)
    args = parser.parse_args()
    csv_path = args.csv_path or find_default_csv()

    payload = build_from_csv(csv_path)
    summary = build_summary(payload)
    payload = _json_safe(payload)
    summary = _json_safe(summary)
    PROTO_DATA.mkdir(parents=True, exist_ok=True)
    OUT_POLL.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Saved: {OUT_POLL}")
    print(f"Saved: {OUT_SUMMARY}")
    print(f"Posts: {len(payload['byPost'])} | DUN with data: {', '.join(summary['dunsWithData'])}")
    print(f"MN vs Solo: {summary['mnVsSolo']['headline']}")
    print(f"Labu: {summary['pasLabu']['headline']}")


if __name__ == "__main__":
    main()
