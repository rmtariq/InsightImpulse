#!/usr/bin/env python3
"""Re-crawl a single Facebook post for more comments and merge with existing CSV (deduped)."""
from __future__ import annotations

import asyncio
import csv
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

POST_URL = "https://www.facebook.com/share/p/1ANZ8jR4YR/"
EXISTING_CSV = ROOT / "data/combined/Combined_facebook_20260714_221637.csv"
COMMENT_TARGET = 3000


def load_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def save_csv(rows: list[dict], path: Path) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def stats(rows: list[dict], label: str) -> None:
    posts = sum(1 for r in rows if (r.get("Type") or "").lower() == "post")
    comments = sum(1 for r in rows if (r.get("Type") or "").lower() == "comment")
    print(f"{label}: {len(rows)} total · {posts} post · {comments} komen")


async def recrawl_comments(existing_asmak: list[dict]) -> tuple[list[dict], dict]:
    from backend.data_crawlers.simple_apify_adapter import SimpleApifyAdapter
    from backend.utils.crawl_records import merge_crawl_records

    adapter = SimpleApifyAdapter()
    merged, pass_stats = await adapter._run_multipass_facebook_comments(
        POST_URL,
        comment_target=COMMENT_TARGET,
        comments_per_post=1000,
        include_nested=True,
        multipass=True,
        existing_comments=existing_asmak,
    )
    final, added, skipped = merge_crawl_records([], merged)
    pass_stats["added_total"] = added
    pass_stats["duplicates_skipped"] = skipped
    return final, pass_stats


async def main() -> None:
    from backend.utils.crawl_records import merge_crawl_records

    existing = load_csv(EXISTING_CSV)
    stats(existing, "Existing CSV")

    asmak_parent = "ustazahasmak"
    existing_asmak = [
        r for r in existing
        if asmak_parent in (r.get("Parent_Post_URL") or r.get("URL") or "").lower()
        or asmak_parent in (r.get("URL") or "").lower()
    ]
    existing_other = [r for r in existing if r not in existing_asmak]
    stats(existing_asmak, "Existing Post 1 (Asmak)")

    print(f"\n🔄 Re-crawling Post 1 — Ustazah Asmak (target {COMMENT_TARGET}, dedupe ON)...")
    merged_asmak, mp_stats = await recrawl_comments(existing_asmak)
    stats(merged_asmak, "Merged Post 1")
    print(
        f"   Multi-pass: +{mp_stats.get('added_total', 0)} new, "
        f"{mp_stats.get('duplicates_skipped', 0)} dupes skipped, "
        f"{mp_stats.get('passes_run', 0)} passes run"
    )

    final, _, _ = merge_crawl_records(existing_other, merged_asmak)
    stats(final, "Final merged (both posts)")

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = ROOT / f"data/combined/Combined_facebook_asmak_recrawl_{ts}.csv"
    save_csv(final, out)
    comment_count = sum(
        1 for r in merged_asmak if (r.get("Type") or "").lower() == "comment"
    )
    print(f"\n✅ Saved: {out}")
    print(f"   FB target ~3,610 komen · crawled {comment_count} unique komen Post 1")


if __name__ == "__main__":
    asyncio.run(main())
