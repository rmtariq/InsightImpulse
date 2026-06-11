#!/usr/bin/env python3
"""One-time migration of existing political (and related) data into data/projects/."""

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.storage.project_registry import import_file_to_project, load_metadata, save_metadata

COMBINED = ROOT / "data" / "combined"
JITP = ROOT / "JITP_2026" / "processed_data"
PAS_BREAK = ROOT / "JITP_2026" / "PAS_Break_2026" / "processed_data"


def row_count(path: Path) -> int:
    try:
        return len(pd.read_csv(path))
    except Exception:
        return 0


def migrate():
    migrations = [
        # pas_break_2026 — Crawl 1 Jun 10
        (
            "pas_break_2026",
            COMBINED / "Combined_facebook_instagram_tiktok_x_youtube_20260610_213913.csv",
            "crawls",
            "PAS_Break_Social_Crawl1_20260610_213913.csv",
            {
                "id": "crawl1_social",
                "label": "Crawl 1 — Social (FB+IG+X+TikTok+YouTube)",
                "platforms": ["facebook", "instagram", "x", "tiktok", "youtube"],
                "date_range": "7days",
                "rows": 630,
                "note": "UI combined output (pre-merge-fix)",
            },
            False,
        ),
        (
            "pas_break_2026",
            PAS_BREAK / "PAS_Break_Master_MERGED_20260610_214334.csv",
            "master",
            "PAS_Break_Master_Social_MERGED_20260610.csv",
            {
                "id": "crawl1_social_merged",
                "label": "Crawl 1 — Full merge (all 12 keywords)",
                "platforms": ["facebook", "instagram", "x", "tiktok", "youtube"],
                "rows": 7395,
                "note": "Manual merge of all smart_crawler files",
            },
            True,
        ),
        # pas_bersatu_baseline — JITP May 2026
        (
            "pas_bersatu_baseline",
            JITP / "pas_bersatu_split_posts_deduped.csv",
            "master",
            "PAS_Bersatu_Baseline_Deduped_May2026.csv",
            {
                "id": "jitp_baseline_deduped",
                "label": "JITP baseline — deduped posts",
                "date_range": "90days",
                "rows": row_count(JITP / "pas_bersatu_split_posts_deduped.csv"),
            },
            True,
        ),
        (
            "pas_bersatu_baseline",
            JITP / "pas_bersatu_split_posts_reclassified.csv",
            "crawls",
            "PAS_Bersatu_Baseline_Reclassified_May2026.csv",
            {
                "id": "jitp_baseline_reclassified",
                "label": "JITP — political reclassification layer",
                "rows": row_count(JITP / "pas_bersatu_split_posts_reclassified.csv"),
            },
            False,
        ),
        (
            "pas_bersatu_baseline",
            JITP / "Combined_facebook_instagram_threads_tiktok_x_youtube_20260529_162307.csv",
            "crawls",
            "PAS_Bersatu_Combined_Crawl_May2026.csv",
            {
                "id": "jitp_combined_may29",
                "label": "JITP combined crawl 29 May 2026",
                "platforms": ["facebook", "instagram", "threads", "tiktok", "x", "youtube"],
                "rows": row_count(JITP / "Combined_facebook_instagram_threads_tiktok_x_youtube_20260529_162307.csv"),
            },
            False,
        ),
        # prn_johor_2026
        (
            "prn_johor_2026",
            COMBINED / "Combined_dashboard_PRN_Johor_FULL_20260606_102357.csv",
            "master",
            "PRN_Johor_Master_FULL_20260606.csv",
            {
                "id": "prn_johor_full",
                "label": "PRN Johor full dashboard dataset",
                "rows": row_count(COMBINED / "Combined_dashboard_PRN_Johor_FULL_20260606_102357.csv"),
            },
            True,
        ),
        # smebank
        (
            "smebank",
            COMBINED / "SMEBank_AllData_Master_20260609_160119.csv",
            "master",
            "SMEBank_Master_20260609.csv",
            {
                "id": "smebank_master",
                "label": "SME Bank EWS master",
                "rows": row_count(COMBINED / "SMEBank_AllData_Master_20260609_160119.csv"),
            },
            True,
        ),
        # kdebwm
        (
            "kdebwm",
            COMBINED / "KDEBWM_Combined_AllPlatforms_20260608.csv",
            "master",
            "KDEBWM_Master_20260608.csv",
            {
                "id": "kdebwm_master",
                "label": "KDEBWM combined all platforms",
                "rows": row_count(COMBINED / "KDEBWM_Combined_AllPlatforms_20260608.csv"),
            },
            True,
        ),
    ]

    for project_id, src, subfolder, dest_name, crawl_meta, as_master in migrations:
        if not src.exists():
            print(f"SKIP (missing): {src}")
            continue
        if crawl_meta and "rows" not in crawl_meta:
            crawl_meta["rows"] = row_count(src)
        crawl_meta = {**crawl_meta, "file": f"{subfolder}/{dest_name}", "migrated_at": "2026-06-10"}
        dest = import_file_to_project(
            project_id, src, subfolder=subfolder, dest_name=dest_name,
            crawl_meta=crawl_meta, as_master=as_master,
        )
        print(f"OK {project_id}: {dest.name} ({crawl_meta.get('rows', '?')} rows)")

    # Enrich pas_break metadata
    meta = load_metadata("pas_break_2026")
    meta["event"] = {
        "declaration": "2026-06-09",
        "description": "PAS & Bersatu split declaration (Monday night)",
        "analysis_window": "2026-06-09 to 2026-06-10",
    }
    meta["pending"] = ["crawl2_news"]
    save_metadata("pas_break_2026", meta)
    print("\nDone. See data/projects/")


if __name__ == "__main__":
    migrate()
