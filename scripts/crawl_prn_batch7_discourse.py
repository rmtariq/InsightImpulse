#!/usr/bin/env python3
"""
Batch 7 — discourse gap crawl (PAS implisit, UMDAP, anti-PH, Gen Z/Gen Y).

Hantar query satu persatu ke InsightPulse http://localhost:8001/analyze_async
Satu run siap → baru run seterusnya.

Usage:
  NEImpulse/bin/python3 scripts/crawl_prn_batch7_discourse.py
  NEImpulse/bin/python3 scripts/crawl_prn_batch7_discourse.py --run I --no-wait
  NEImpulse/bin/python3 scripts/crawl_prn_batch7_discourse.py --from-run C
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
API_BASE = "http://localhost:8001"
MYT = timezone(timedelta(hours=8))
LOG_PATH = ROOT / "data/projects/political/PRN/_shared/excel_intel/batch7_crawl_run.json"

SOCIAL = ["facebook", "tiktok"]  # jimat kos — FB kampung + TikTok Gen Z
NEWS = ["news"]
ALL = SOCIAL + NEWS

# id, label, query, platforms, dataset_size, date_range
RUNS = [
    (
        "A",
        "PAS implisit N9",
        '"suka pas" OR "pas terbaik" OR "all out pas" OR "teguh pas" OR "panah pas" OR #panahpas "Negeri Sembilan"',
        SOCIAL,
        1800,
        "7days",
    ),
    (
        "B",
        "PAS implisit Johor",
        '"suka pas" OR "pas terbaik" OR "all out pas" OR "teguh pas" OR "panah pas" OR #panahpas Johor PRN',
        SOCIAL,
        1800,
        "7days",
    ),
    (
        "C",
        "UMDAP N9",
        'umdap OR "umno dap" OR "umno dan dap" OR "kerajaan perpaduan" dap "Negeri Sembilan"',
        SOCIAL,
        1800,
        "7days",
    ),
    (
        "D",
        "UMDAP Johor",
        'umdap OR "umno dap" OR "umno dan dap" OR "kerajaan perpaduan" dap Johor PRN',
        SOCIAL,
        1800,
        "7days",
    ),
    (
        "E",
        "Anti-PH ekonomi N9",
        '("ekonomi" OR "harga barang" OR "minyak naik" OR "mahal hidup" OR "flip flop") ("Negeri Sembilan" OR PRNN9) (DAP OR PH OR Madani OR Anwar)',
        SOCIAL + NEWS,
        1800,
        "7days",
    ),
    (
        "F",
        "Media Cina N9",
        "site:chinapress.com.my OR site:sinchew.com.my (森美兰 OR 芙蓉 OR 选情) (行动党 OR 安华 OR 希盟 OR 经济 OR 物价)",
        NEWS,
        1500,
        "7days",
    ),
    (
        "G",
        "UMNO asal / Melayu Islam N9",
        '("umno asal" OR "umno lama" OR "melayu islam" OR "orang melayu") (umdap OR "umno dap" OR "umno dan dap") "Negeri Sembilan"',
        SOCIAL,
        1500,
        "7days",
    ),
    (
        "H",
        "Berita anti-PH N9",
        'site:malaysiakini.com OR site:thestar.com.my ("Negeri Sembilan" OR PRN) (economy OR inflation OR "cost of living" OR DAP OR Madani) when:7d',
        NEWS,
        1500,
        "7days",
    ),
    (
        "I",
        "Gen Z/Gen Y N9 — tiada parti / undi automatik",
        '("gen z" OR "gen y" OR "anak muda" OR "pengundi muda" OR "undi automatik" OR "swing voter" OR "tiada parti" OR "first time voter") ("Negeri Sembilan" OR PRNN9) PRN',
        SOCIAL,
        2000,
        "7days",
    ),
    (
        "J",
        "Gen Z/Gen Y Johor",
        '("gen z" OR "gen y" OR "anak muda" OR "pengundi muda" OR "undi automatik" OR "swing voter" OR "tiada parti") Johor PRN',
        SOCIAL,
        2000,
        "7days",
    ),
    (
        "K",
        "Gen Z TikTok discourse N9+Johor",
        '#prnn9 OR #prnjohor (anak muda OR fyp OR undi18 OR "undi automatik" OR "tiada parti" OR MUDA OR PSM)',
        ["tiktok"],
        2000,
        "7days",
    ),
    (
        "L",
        "Istana/adat N9 — Undang, YDPB, MB PH terpalit",
        '("Tuanku Muhriz" OR "Yang di-Pertuan Besar" OR "Undang Yang Empat" OR "Adat Perpatih" OR Undang OR "krisis perlembagaan" OR "istana Negeri Sembilan") ("Negeri Sembilan" OR PRNN9 OR Seremban) (DAP OR PKR OR "Menteri Besar" OR Aminuddin OR UMNO OR Harapan)',
        SOCIAL,
        2000,
        "7days",
    ),
]


def check_api(timeout: int = 120) -> None:
    try:
        requests.get(f"{API_BASE}/health", timeout=timeout).raise_for_status()
    except requests.RequestException as exc:
        raise SystemExit(
            f"❌ InsightPulse tidak jalan — buka http://localhost:8001 dulu\n"
            f"   cd {ROOT} && ./start_insightpulse.sh\n{exc}"
        )


def wait_backend_idle(max_min: int = 180, poll: int = 30) -> None:
    """Tunggu backend siap (health OK) sebelum submit run seterusnya."""
    end = time.time() + max_min * 60
    while time.time() < end:
        try:
            requests.get(f"{API_BASE}/health", timeout=90).raise_for_status()
            return
        except requests.RequestException:
            print("   … backend sibuk, tunggu...")
            time.sleep(poll)
    raise TimeoutError(f"Backend masih sibuk selepas {max_min} min")


def submit(query: str, platforms: list[str], dataset_size: int, date_range: str) -> dict:
    payload = {
        "query": query[:900],
        "platforms": platforms,
        "analysis_type": "social_listening",
        "date_range": date_range,
        "dataset_size": dataset_size,
        "use_crawl_strategy": True,
        "project_id": "pas_break_2026",
        "analysis_focus": "comprehensive",
        "comment_sampling": "smart",
        "crawl_mode": "keyword",
    }
    r = requests.post(f"{API_BASE}/analyze_async", json=payload, timeout=300)
    r.raise_for_status()
    return r.json()


def wait_task(task_id: str, label: str, poll: int = 25, max_min: int = 90) -> dict:
    end = time.time() + max_min * 60
    last = 0
    while time.time() < end:
        st = requests.get(f"{API_BASE}/task_status/{task_id}", timeout=120).json()
        logs = st.get("logs") or []
        for line in logs[last:]:
            print(f"      {line}")
        last = len(logs)
        status = st.get("status")
        pct = st.get("progress")
        prog = f" {pct}%" if pct is not None else ""
        print(f"   … {label}: {status}{prog}")
        if status == "completed":
            return st
        if status == "failed":
            raise RuntimeError(st.get("error") or "task failed")
        time.sleep(poll)
    raise TimeoutError(f"{label} timeout after {max_min} min")


def main() -> int:
    p = argparse.ArgumentParser(description="Batch 7 discourse + Gen Z crawl")
    p.add_argument("--run", help="Single run id e.g. A or I (default: all)")
    p.add_argument("--from-run", help="Start from run id (inclusive)")
    p.add_argument("--no-wait", action="store_true", help="Submit only, do not wait")
    p.add_argument("--max-min", type=int, default=90, help="Timeout per run (minutes)")
    args = p.parse_args()

    check_api()
    run_map = {r[0]: r for r in RUNS}
    selected = RUNS

    if args.run:
        if args.run.upper() not in run_map:
            raise SystemExit(f"❌ Unknown run {args.run}. Valid: {', '.join(run_map)}")
        selected = [run_map[args.run.upper()]]
    elif args.from_run:
        fid = args.from_run.upper()
        ids = [r[0] for r in RUNS]
        if fid not in ids:
            raise SystemExit(f"❌ Unknown --from-run {fid}")
        selected = RUNS[ids.index(fid) :]

    log = {
        "batch": "07_discourse_pas_umdap_ph_genz",
        "started": datetime.now(MYT).isoformat(),
        "api": API_BASE,
        "jobs": [],
    }

    print(f"📡 Batch 7 crawl · {len(selected)} run · {API_BASE}\n")

    for run_id, label, query, platforms, ds, dr in selected:
        if run_id != selected[0][0]:
            print(f"\n⏳ Tunggu backend idle sebelum Run {run_id}...")
            wait_backend_idle()
        print(f"\n{'='*64}")
        print(f"▶ Run {run_id}: {label}")
        print(f"   Query: {query[:90]}...")
        print(f"   Platform: {', '.join(platforms)} · dataset {ds} · {dr}")
        resp = submit(query, platforms, ds, dr)
        tid = resp.get("task_id")
        print(f"   🚀 task_id={tid}  → pantau http://localhost:8001")
        job = {
            "run_id": run_id,
            "label": label,
            "task_id": tid,
            "query": query,
            "platforms": platforms,
            "dataset_size": ds,
            "submitted": datetime.now(MYT).isoformat(),
        }
        if not args.no_wait:
            try:
                st = wait_task(tid, f"Run {run_id}", max_min=args.max_min)
                job["status"] = st.get("status")
                job["completed"] = datetime.now(MYT).isoformat()
            except (TimeoutError, RuntimeError) as exc:
                job["status"] = "error"
                job["error"] = str(exc)
                print(f"   ⚠️ {exc} — terus run seterusnya")
        log["jobs"].append(job)
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        LOG_PATH.write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n✅ Log: {LOG_PATH}")
    print("Selepas SEMUA siap → gabung master (rujuk PRN_CRAWL_UPDATE_JADUAL_2026.txt §G)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
