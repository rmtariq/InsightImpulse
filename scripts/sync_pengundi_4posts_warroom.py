#!/usr/bin/env python3
"""Sync Mac1+Mac2 Pengundi 4-post batch into War Room JSON (visible in dashboard)."""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTO = ROOT / "data/projects/political/PRN/PRN_N9/reports/war_room/prototype/data"
ANALYSIS_JSON = PROTO / "n9_pengundi_4posts_analysis.json"
MASTER_GLOB = "Combined_facebook_MAC1_MAC2_master_*.csv"


def _latest_master() -> Path | None:
    combined = ROOT / "data/combined"
    files = sorted(combined.glob(MASTER_GLOB), key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0] if files else None


def _load_analysis() -> dict:
    if ANALYSIS_JSON.exists():
        return json.loads(ANALYSIS_JSON.read_text(encoding="utf-8"))
    raise FileNotFoundError(f"Missing {ANALYSIS_JSON} — run merge first")


def _load_insight_report() -> dict | None:
    p = ROOT / "data/projects/political/PRN/PRN_N9/reports/pengundi_4posts/pengundi_4posts_insight_latest.json"
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return None


def _build_warroom_block(analysis: dict, insight_report: dict | None = None) -> dict:
    posts = analysis.get("posts_analyzed") or []
    total_likes = sum(int(p.get("likes") or 0) for p in posts)
    total_shares = sum(int(p.get("shares") or 0) for p in posts)
    total_comments = sum(int(p.get("crawled_comments") or 0) for p in posts)
    total_engagement = total_likes + total_shares + total_comments
    post3 = next((p for p in posts if p.get("id") == "POST-3"), {})
    vote = post3.get("vote_signal") or {}

    summaries = []
    insight_map = {}
    if insight_report:
        insight_map = {p["id"]: p for p in insight_report.get("posts", [])}

    for p in posts:
        pid = p.get("id")
        ext = insight_map.get(pid) or {}
        insight = ""
        if p.get("vote_signal"):
            vs = p["vote_signal"]
            insight = f"BN+PN {vs.get('B_pct_of_decided')}% vs PH {vs.get('A_pct_of_decided')}% (komen A/B)"
        elif p.get("cooperation_signal"):
            sig = sum((p.get("cooperation_signal") or {}).get(k, 0) for k in ("setuju", "tidak_setuju", "bimbang"))
            pct = p.get("setuju_pct_of_signal")
            insight = f"Setuju ~{pct}% (signal {sig} komen)" if pct else ""
        if ext.get("insight_ringkas"):
            insight = ext["insight_ringkas"]
        summaries.append({
            "id": pid,
            "title": p.get("question"),
            "url": p.get("post_url"),
            "crawled_comments": p.get("crawled_comments"),
            "fb_comments_meta": p.get("fb_comments_meta"),
            "coverage_pct": p.get("coverage_pct"),
            "likes": p.get("likes"),
            "shares": p.get("shares"),
            "negative_pct": p.get("negative_pct"),
            "positive_pct": p.get("positive_pct"),
            "analytics_line": ext.get("analytics_line") or "",
            "insight": insight,
            "insight_exco": (ext.get("llm") or {}).get("insight_executive") or "",
            "tindakan_72j": ext.get("tindakan_disyorkan") or [],
            "tema_komen": ext.get("tema_komen_top") or "",
            "impak_bloc": ext.get("impak_bloc") or "",
        })

    return {
        "updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "label": "Pengundi Malaysia · Post URL Batch (Mac1+Mac2 · Jul 2026)",
        "master_csv": analysis.get("master_csv"),
        "source_files": [
            "Mac1: Combined_facebook_20260714_221637.csv, 232031.csv",
            "Mac2: Combined_facebook_20260714_231140.csv, 20260715_011605.csv, 013927.csv",
        ],
        "summary": {
            "total_posts": len(posts),
            "total_comments_crawled": total_comments,
            "total_likes": total_likes,
            "total_shares": total_shares,
            "total_engagement": total_engagement,
            "total_data_points": analysis.get("total_master_rows") or (len(posts) + total_comments),
        },
        "posts": summaries,
        "post3_poll": {
            "sokong_bn_pn_pct": vote.get("B_pct_of_decided"),
            "sokong_ph_pct": vote.get("A_pct_of_decided"),
            "decided_ab": (vote.get("A_PH_explicit") or 0) + (vote.get("B_BN_PN_explicit") or 0),
        },
        "strategic_headline": (
            f"4 post viral · {total_comments:,} komen · {total_engagement:,} engagement · "
            f"Poll PH vs BN+PN: B {vote.get('B_pct_of_decided', '—')}%"
        ),
        "insight_docx": str(
            (ROOT / "data/projects/political/PRN/PRN_N9/reports/pengundi_4posts/pengundi_4posts_insight_latest.json").relative_to(ROOT)
        ) if insight_report else None,
        "insight_docx_file": insight_report.get("insight_docx") if insight_report else None,
        "kesimpulan_gabungan": (insight_report or {}).get("kesimpulan_gabungan"),
    }


def _patch_json(path: Path, key: str, block: dict) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    data[key] = block
    if key == "pengundiMacPosts" and isinstance(data.get("meta"), dict):
        data["meta"]["pengundiMacSync"] = block["updated"]
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _patch_actions(block: dict) -> None:
    path = PROTO / "n9_actions_v2.json"
    if not path.exists():
        return
    data = json.loads(path.read_text(encoding="utf-8"))
    s = block["summary"]
    post3 = block.get("post3_poll") or {}
    data.setdefault("meta", {})["pengundiMacSync"] = block["updated"]

    data["jobCrawlMetrics"] = data.get("jobCrawlMetrics") or {}
    data["jobCrawlMetrics"]["pengundiMac4Posts"] = {
        "posts": s["total_posts"],
        "comments": s["total_comments_crawled"],
        "engagement": s["total_engagement"],
        "likes": s["total_likes"],
        "shares": s["total_shares"],
        "sokong_bn_pn_pct": post3.get("sokong_bn_pn_pct"),
        "master_csv": block.get("master_csv"),
        "updated": block["updated"],
    }

    exercises = [e for e in (data.get("jobExercises") or []) if e.get("id") != "JOB-N9-PENGUNDI-4"]
    exercises.insert(0, {
        "id": "JOB-N9-PENGUNDI-4",
        "title": "Pengundi MY · 4 Post URL Batch (Mac1+Mac2)",
        "status": "siap",
        "stats": {
            "posts": s["total_posts"],
            "comments": s["total_comments_crawled"],
            "engagement": s["total_engagement"],
            "likes": s["total_likes"],
            "sokong_bn_pn_pct": post3.get("sokong_bn_pn_pct"),
        },
        "insight": block["strategic_headline"],
        "posts": block["posts"],
    })
    data["jobExercises"] = exercises
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    analysis = _load_analysis()
    insight_report = _load_insight_report()
    master = _latest_master()
    if master:
        analysis["master_csv"] = str(master.relative_to(ROOT))

    block = _build_warroom_block(analysis, insight_report)
    ANALYSIS_JSON.write_text(json.dumps(analysis, ensure_ascii=False, indent=2), encoding="utf-8")

    for name in ("n9_social_summary.json", "n9_production_bundle.json"):
        p = PROTO / name
        if p.exists():
            _patch_json(p, "pengundiMacPosts", block)
            if name == "n9_production_bundle.json":
                bundle = json.loads(p.read_text(encoding="utf-8"))
                if bundle.get("socialSummary"):
                    bundle["socialSummary"]["pengundiMacPosts"] = block
                    p.write_text(json.dumps(bundle, ensure_ascii=False, indent=2), encoding="utf-8")

    _patch_actions(block)

    s = block["summary"]
    print("✅ Pengundi 4-post synced to War Room")
    print(f"   Posts: {s['total_posts']} · Comments: {s['total_comments_crawled']:,} · Engagement: {s['total_engagement']:,}")
    print(f"   Master: {block.get('master_csv')}")
    print(f"   JSON: {ANALYSIS_JSON.relative_to(ROOT)}")
    print(f"   Refresh: http://localhost:8080/ (Cmd+Shift+R)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
