#!/usr/bin/env python3
"""
Crawl URL post cula digital — 36 DUN N9 (Direct URL → sentiment + emotion + komen).

Baca URL dari:
  data/projects/political/PRN/_shared/url_batches/cula_seeds_N9/Nxx_*.txt

Usage:
  python3 scripts/crawl_cula_seed_batches_n9.py --all-filled
  python3 scripts/crawl_cula_seed_batches_n9.py --code N10
  python3 scripts/crawl_cula_seed_batches_n9.py --dry-run
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from prn_paths import crawls, ensure_state_dirs  # noqa: E402

BATCH_DIR = ROOT / "data/projects/political/PRN/_shared/url_batches/cula_seeds_N9"
API_BASE = "http://localhost:8001"
MYT = timezone(timedelta(hours=8))
RUN_LOG = ROOT / "data/projects/political/PRN/PRN_N9/crawls/cula_seed_crawl_run.json"


def load_urls(code: str | None = None, all_filled: bool = False) -> list[dict]:
    if not BATCH_DIR.exists():
        raise SystemExit(f"Tiada folder batch — jalankan: python3 scripts/generate_cula_seed_batches_n9.py")

    items: list[dict] = []
    pattern = f"{code.upper()}_*.txt" if code else "N*.txt"
    for path in sorted(BATCH_DIR.glob(pattern)):
        if path.name.startswith("ALL_") or path.name == "manifest.json":
            continue
        m = re.match(r"(N\d{2})_(.+)_PASTE_ONLY\.txt", path.name)
        if not m:
            continue
        dun_code, name = m.group(1), m.group(2).replace("_", " ")
        for line in path.read_text(encoding="utf-8").splitlines():
            url = line.strip()
            if url.startswith("#") or not url.startswith("http"):
                continue
            items.append({"code": dun_code, "name": name, "url": url.split()[0]})

    if all_filled and not items:
        raise SystemExit("Tiada URL diisi dalam batch cula — paste URL post dulu (2–3 hari selepas seed)")
    return items


def api_alive() -> bool:
    try:
        return requests.get(f"{API_BASE}/health", timeout=5).status_code == 200
    except requests.RequestException:
        try:
            return requests.get(f"{API_BASE}/", timeout=5).status_code in (200, 404)
        except requests.RequestException:
            return False


def crawl_batch(items: list[dict], *, dataset_size: int, wait: bool, delay: int) -> list[dict]:
    by_dun: dict[str, list[str]] = {}
    for it in items:
        by_dun.setdefault(it["code"], []).append(it["url"])

    tasks: list[dict] = []
    total = len(by_dun)
    for i, (code, urls) in enumerate(sorted(by_dun.items()), 1):
        name = next(it["name"] for it in items if it["code"] == code)
        print(f"\n[{i}/{total}] {code} {name} — {len(urls)} URL")
        for u in urls:
            print(f"   · {u[:72]}...")

        payload = {
            "query": f"Cula seed {code} {name}",
            "platforms": ["facebook", "tiktok", "instagram", "x"],
            "analysis_type": "social_listening",
            "date_range": "7days",
            "dataset_size": dataset_size,
            "use_crawl_strategy": True,
            "project_id": "pas_break_2026",
            "analysis_focus": "comprehensive",
            "comment_sampling": "smart",
            "crawl_mode": "direct_url",
            "direct_urls": urls,
        }
        try:
            r = requests.post(f"{API_BASE}/analyze_async", json=payload, timeout=30)
            r.raise_for_status()
            data = r.json()
        except requests.RequestException as exc:
            print(f"   ❌ {exc}")
            continue

        task_id = data.get("task_id")
        print(f"   🚀 task={task_id}")
        tasks.append({
            "code": code,
            "name": name,
            "urls": urls,
            "task_id": task_id,
            "status": "queued",
        })

        if wait and task_id:
            while True:
                time.sleep(20)
                try:
                    st = requests.get(f"{API_BASE}/task_status/{task_id}", timeout=15).json()
                except requests.RequestException:
                    continue
                if st.get("status") == "completed":
                    tasks[-1]["status"] = "completed"
                    print(f"   ✅ {code} siap")
                    break
                if st.get("status") == "failed":
                    tasks[-1]["status"] = "failed"
                    tasks[-1]["error"] = st.get("error")
                    print(f"   ❌ {code} gagal")
                    break

        if i < total:
            time.sleep(delay)

    return tasks


def main() -> int:
    p = argparse.ArgumentParser(description="Crawl cula seed post URLs — 36 DUN N9")
    p.add_argument("--code", help="Satu DUN e.g. N10")
    p.add_argument("--all-filled", action="store_true", help="Crawl semua URL yang sudah diisi")
    p.add_argument("--dry-run", action="store_true", help="Senaraikan URL sahaja")
    p.add_argument("--dataset-size", type=int, default=1000)
    p.add_argument("--wait", action="store_true", help="Tunggu setiap task siap")
    p.add_argument("--delay", type=int, default=10)
    args = p.parse_args()

    if not args.code and not args.all_filled:
        args.all_filled = True  # default: crawl whatever is filled

    items = load_urls(code=args.code, all_filled=args.all_filled)
    if not items:
        print("ℹ️  Tiada URL untuk crawl. Isi URL post dalam:")
        print(f"   {BATCH_DIR.relative_to(ROOT)}/Nxx_*.txt")
        print("   Jalankan: python3 scripts/generate_cula_seed_batches_n9.py")
        return 0

    seats = len({it["code"] for it in items})
    print(f"📋 {len(items)} URL · {seats} kerusi")

    if args.dry_run:
        for it in items:
            print(f"  {it['code']} {it['name']}: {it['url']}")
        return 0

    if not api_alive():
        print("❌ Backend tidak hidup — ./start_full_app.sh", file=sys.stderr)
        return 1

    tasks = crawl_batch(items, dataset_size=args.dataset_size, wait=args.wait, delay=args.delay)

    summary = {
        "run_at": datetime.now(MYT).isoformat(timespec="seconds"),
        "urls_crawled": len(items),
        "seats": seats,
        "tasks": tasks,
        "next": [
            "tail -f backend.log",
            "python3 scripts/merge_prn_johor_n9_master.py",
            "python3 scripts/build_warroom_production_bundle.py",
        ],
    }
    ensure_state_dirs("N9")
    RUN_LOG.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n💾 Log: {RUN_LOG.relative_to(ROOT)}")
    print(f"✅ {len(tasks)} task dihantar · {seats} kerusi")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
