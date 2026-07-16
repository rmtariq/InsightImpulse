#!/usr/bin/env python3
"""
Pull succeeded Apify actor runs (yesterday/today) → Combined CSV for war room.

Requires APIFY_API_TOKEN in .env (same token InsightPulse uses).

Usage:
  python3 scripts/import_apify_recent_runs.py
  python3 scripts/import_apify_recent_runs.py --since 2026-06-19 --until 2026-06-21
  python3 scripts/import_apify_recent_runs.py --run-id eQE18vbMaLXnuzgOO

Then:
  python3 scripts/analyze_prn_excel_dun_insights.py
  python3 scripts/build_warroom_production_bundle.py
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

MYT = timezone(timedelta(hours=8))
OUT_DIR = ROOT / "data/combined"
API = "https://api.apify.com/v2"


def load_token() -> str:
    token = os.getenv("APIFY_API_TOKEN", "")
    env_path = ROOT / ".env"
    if not token and env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            if line.startswith("APIFY_API_TOKEN="):
                token = line.split("=", 1)[1].strip().strip('"').strip("'")
                break
    if not token:
        raise SystemExit("❌ APIFY_API_TOKEN not found in env or .env")
    return token


def api_get(token: str, path: str, params: dict | None = None) -> dict:
    r = requests.get(f"{API}{path}", params=params or {}, auth=(token, ""), timeout=60)
    r.raise_for_status()
    return r.json()


def list_runs(token: str, since: datetime, until: datetime, limit: int = 100) -> list:
    runs = []
    offset = 0
    while len(runs) < limit:
        data = api_get(token, "/actor-runs", {
            "desc": "true",
            "limit": min(50, limit - len(runs)),
            "offset": offset,
        })
        items = data.get("data", {}).get("items", [])
        if not items:
            break
        for run in items:
            started = run.get("startedAt") or run.get("createdAt") or ""
            if not started:
                continue
            dt = datetime.fromisoformat(started.replace("Z", "+00:00"))
            if dt < since:
                return runs
            if dt <= until and run.get("status") == "SUCCEEDED":
                runs.append(run)
        offset += len(items)
    return runs


def fetch_dataset_items(token: str, dataset_id: str, max_items: int = 10000) -> list:
    items = []
    offset = 0
    page = 500
    while len(items) < max_items:
        data = api_get(token, f"/datasets/{dataset_id}/items", {
            "limit": min(page, max_items - len(items)),
            "offset": offset,
        })
        if not data:
            break
        if isinstance(data, list):
            batch = data
        else:
            batch = data.get("items", data.get("data", []))
        if not batch:
            break
        items.extend(batch)
        if len(batch) < page:
            break
        offset += len(batch)
    return items


def guess_platform(run: dict, item: dict) -> str:
    act = (run.get("actId") or run.get("actorId") or "").lower()
    name = (run.get("actorName") or "").lower()
    url = str(item.get("url") or item.get("postUrl") or item.get("webVideoUrl") or "")
    if "facebook" in act or "facebook" in name or "facebook.com" in url:
        return "facebook"
    if "instagram" in act or "instagram" in name or "instagram.com" in url:
        return "instagram"
    if "tiktok" in act or "tiktok" in name or "tiktok.com" in url:
        return "tiktok"
    if "twitter" in act or "x-post" in act or "x.com" in url or "twitter.com" in url:
        return "x"
    if "google" in act or "news" in name:
        return "news"
    return "unknown"


def item_to_row(platform: str, item: dict) -> dict | None:
    text = (
        item.get("text") or item.get("caption") or item.get("content")
        or item.get("fullText") or item.get("title") or item.get("message") or ""
    )
    if not str(text).strip():
        return None
    url = item.get("url") or item.get("postUrl") or item.get("webVideoUrl") or item.get("link") or ""
    rid = item.get("id") or item.get("postId") or item.get("tweetId") or url or str(hash(text))[:16]
    date = item.get("createdAt") or item.get("timestamp") or item.get("date") or item.get("time") or ""
    return {
        "Platform": platform,
        "Type": "comment" if item.get("parentPostId") or item.get("inReplyTo") else "post",
        "ID": rid,
        "Text": str(text)[:8000],
        "URL": url,
        "Date": date,
        "likes": item.get("likes") or item.get("likeCount") or item.get("diggCount") or 0,
        "comments_count": item.get("commentsCount") or item.get("commentCount") or 0,
        "shares": item.get("shares") or item.get("shareCount") or 0,
        "views": item.get("views") or item.get("playCount") or item.get("viewCount") or 0,
    }


def main() -> int:
    p = argparse.ArgumentParser(description="Import Apify runs to Combined CSV")
    p.add_argument("--since", default=(datetime.now(MYT) - timedelta(days=2)).strftime("%Y-%m-%d"))
    p.add_argument("--until", default=(datetime.now(MYT) + timedelta(days=1)).strftime("%Y-%m-%d"))
    p.add_argument("--run-id", action="append", default=[], help="Specific Apify run ID(s)")
    p.add_argument("--max-runs", type=int, default=30)
    p.add_argument("--max-items-per-run", type=int, default=5000)
    args = p.parse_args()

    token = load_token()
    since = datetime.fromisoformat(args.since).replace(tzinfo=MYT)
    until = datetime.fromisoformat(args.until).replace(tzinfo=MYT)

    if args.run_id:
        runs = []
        for rid in args.run_id:
            run = api_get(token, f"/actor-runs/{rid}").get("data", {})
            if run.get("status") == "SUCCEEDED":
                runs.append(run)
    else:
        print(f"📡 Fetching Apify runs {args.since} → {args.until} ...")
        runs = list_runs(token, since, until, limit=args.max_runs)

    if not runs:
        print("❌ No succeeded runs found in date range.")
        print("   Apify Console → Runs → open run → Export dataset")
        return 1

    print(f"✅ Found {len(runs)} succeeded run(s)")
    all_rows = []
    manifest = []

    for run in runs:
        rid = run.get("id")
        ds = run.get("defaultDatasetId")
        started = run.get("startedAt", "")[:19]
        if not ds:
            print(f"   skip {rid} — no dataset")
            continue
        print(f"   📥 {rid} ({started}) dataset={ds[:12]}...")
        items = fetch_dataset_items(token, ds, max_items=args.max_items_per_run)
        added = 0
        for item in items:
            plat = guess_platform(run, item)
            row = item_to_row(plat, item)
            if row:
                row["ApifyRunId"] = rid
                all_rows.append(row)
                added += 1
        manifest.append({"run_id": rid, "started": started, "items": added, "dataset_id": ds})
        print(f"      → {added} rows")

    if not all_rows:
        print("❌ Runs found but no text rows extracted.")
        return 1

    df = pd.DataFrame(all_rows).drop_duplicates(subset=["Platform", "ID", "Text"], keep="first")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(MYT).strftime("%Y%m%d_%H%M%S")
    plats = "_".join(sorted(df["Platform"].unique())[:6])
    out = OUT_DIR / f"Combined_apify_import_{plats}_{ts}.csv"
    df.to_csv(out, index=False, encoding="utf-8")

    meta = OUT_DIR / f"Combined_apify_import_{ts}_manifest.json"
    meta.write_text(json.dumps({"runs": manifest, "rows": len(df), "csv": str(out.name)}, indent=2))

    print(f"\n💾 Saved: {out}")
    print(f"   Rows: {len(df)}")
    print(f"   Platforms: {df['Platform'].value_counts().to_dict()}")
    print("\nNext:")
    print("  python3 scripts/analyze_prn_excel_dun_insights.py")
    print("  python3 scripts/build_warroom_production_bundle.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
