#!/usr/bin/env python3
"""
Susun semula data PRN ke folder negeri sistematik.

Sebelum: semua dalam pas_break_2026/ + data/analyzed/PRN_N9_*
Selepas: data/projects/political/PRN/PRN_N9|Johor|Melaka/

Jalankan sekali:
  NEImpulse/bin/python scripts/migrate_prn_folder_structure.py
  NEImpulse/bin/python scripts/migrate_prn_folder_structure.py --dry-run
"""
from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OLD = ROOT / "data/projects/political/pas_break_2026"
ANALYZED_GLOBAL = ROOT / "data/analyzed"
JOhor_LEGACY = ROOT / "data/projects/political/prn_johor_2026"

import sys
sys.path.insert(0, str(ROOT / "scripts"))
from prn_paths import (  # noqa: E402
    PRN_ROOT,
    SHARED,
    STATES,
    ensure_state_dirs,
    prn_dir,
    crawls,
    reference,
    reports,
    master,
)


def _move(src: Path, dst: Path, dry_run: bool) -> bool:
    if not src.exists():
        return False
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        print(f"   ⏭  skip (wujud): {dst.relative_to(ROOT)}")
        return False
    print(f"   → {src.relative_to(ROOT)}")
    print(f"     {dst.relative_to(ROOT)}")
    if not dry_run:
        shutil.move(str(src), str(dst))
    return True


def migrate_n9(dry_run: bool) -> int:
    ensure_state_dirs("N9")
    n = 0
    print("\n📁 PRN_N9 — berita & analitik")

    news_patterns = ("PRN_N9_News_*.csv", "PRN_N9_StagingCombine_*.csv")
    for pat in news_patterns:
        for f in sorted(OLD.glob(f"crawls/{pat}")):
            if _move(f, crawls("N9", "news") / f.name, dry_run):
                n += 1

    for f in sorted(OLD.glob("crawls/PRN_Chinese_News_*.csv")):
        if _move(f, crawls("N9", "chinese_news") / f.name, dry_run):
            n += 1
    for f in sorted(OLD.glob("crawls/N9_Chinese_News_*.csv")):
        if _move(f, crawls("N9", "chinese_news") / f.name, dry_run):
            n += 1

    for f in sorted(OLD.glob("crawls/PRN_N9_ADUN_*.csv")):
        if _move(f, crawls("N9", "adun_seeds") / f.name, dry_run):
            n += 1

    if ANALYZED_GLOBAL.exists():
        for f in sorted(ANALYZED_GLOBAL.glob("PRN_N9_News_Analyzed_TierA_*.csv")):
            if _move(f, crawls("N9", "news_analyzed") / f.name, dry_run):
                n += 1

    ref_map = {
        "prn_n9_news_summary.json": "prn_n9_news_summary.json",
        "prn_n9_news_multilingual_summary.json": "prn_n9_news_multilingual_summary.json",
        "prn_n9_news_analyzed_summary.json": "prn_n9_news_analyzed_summary.json",
        "prn_n9_adun_social_summary.json": "prn_n9_adun_social_summary.json",
        "prn_chinese_news_summary.json": "prn_chinese_news_summary.json",
        "n9_chinese_news_summary.json": "n9_chinese_news_summary.json",
        "economic_n9.json": "economic_n9.json",
        "n9_dpi_updates.json": "n9_dpi_updates.json",
    }
    for src_name, dst_name in ref_map.items():
        if _move(OLD / "reference" / src_name, reference("N9") / dst_name, dry_run):
            n += 1

    query_files = (
        "PRN_N9_NEWS_KOMUNITI_QUERIES.txt",
        "PRN_N9_NEWS_QUERIES_SIAP_GUNA.txt",
        "PRN_N9_SOCMED_QUERIES_SIAP_GUNA.txt",
        "PRN_N9_WHATSAPP_TEMPLATES.txt",
        "N9_Chinese_Narrative_queries.txt",
        "N9_Chinese_Narrative_CARA_GUNA.txt",
    )
    for q in query_files:
        if _move(OLD / "reference" / q, reference("N9") / "queries" / q, dry_run):
            n += 1

    seed_files = ("N9_Chinese_Narrative_Seeds.xlsx",)
    for s in seed_files:
        if _move(OLD / "reference" / s, reference("N9") / "seeds" / s, dry_run):
            n += 1

    if _move(OLD / "reference" / "spr_prn_dates_2026.json", SHARED / "spr" / "spr_prn_dates_2026.json", dry_run):
        n += 1

    report_map = {
        "n9_seats_export.json": "reports/seats/n9_seats_export.json",
        "n9_seats_analytics.json": "reports/seats/n9_seats_analytics.json",
        "n9_seats_analytics.csv": "reports/seats/n9_seats_analytics.csv",
        "n9_war_room.json": "reports/war_room/n9_war_room.json",
        "n9_war_room_briefing.json": "reports/war_room/n9_war_room_briefing.json",
        "n9_hari_ini_whatsapp.txt": "reports/war_room/n9_hari_ini_whatsapp.txt",
        "prn-negeri-sembilan-dashboard.html": "reports/dashboards/prn-negeri-sembilan-dashboard.html",
    }
    for src_name, rel in report_map.items():
        if _move(OLD / "reports" / src_name, prn_dir("N9") / rel, dry_run):
            n += 1

    war_csv = ROOT / "JITP_2026/Master_File/n9_war_room_actions.csv"
    if war_csv.exists():
        if _move(war_csv, reports("N9") / "war_room" / "n9_war_room_actions.csv", dry_run):
            n += 1

    return n


def migrate_johor(dry_run: bool) -> int:
    ensure_state_dirs("Johor")
    n = 0
    print("\n📁 PRN_Johor — dari prn_johor_2026")
    if not JOhor_LEGACY.exists():
        print("   (tiada folder legacy)")
        return 0
    for f in JOhor_LEGACY.glob("master/*.csv"):
        if _move(f, master("Johor") / f.name, dry_run):
            n += 1
    meta = JOhor_LEGACY / "metadata.json"
    if meta.exists() and not (prn_dir("Johor") / "metadata.json").exists():
        if _move(meta, prn_dir("Johor") / "metadata.json", dry_run):
            n += 1
    return n


def migrate_melaka(dry_run: bool) -> int:
    ensure_state_dirs("Melaka")
    print("\n📁 PRN_Melaka — skeleton siap")
    return 0


def write_registry(dry_run: bool) -> None:
    reg = {
        "updated_at": datetime.now().isoformat(),
        "root": "data/projects/political/PRN",
        "states": {
            k: {
                "id": v["id"],
                "name": v["name_ms"],
                "path": f"data/projects/political/PRN/{v['id']}",
                "dun_seats": v["dun_seats"],
            }
            for k, v in STATES.items()
        },
        "shared": {
            "spr_dates": "data/projects/political/PRN/_shared/spr/spr_prn_dates_2026.json",
            "templates": "data/projects/political/PRN/_shared/templates",
            "chinese_narrative": "data/projects/political/PRN/_shared/chinese_narrative",
        },
        "pas_break_narrative": "data/projects/political/pas_break_2026",
        "note": "N9/Johor/Melaka = data negeri. pas_break_2026 = narrative PAS-Bersatu merentasi negeri.",
    }
    path = PRN_ROOT / "_registry.json"
    print(f"\n📝 Registry: {path.relative_to(ROOT)}")
    if not dry_run:
        PRN_ROOT.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(reg, ensure_ascii=False, indent=2), encoding="utf-8")


def write_n9_metadata(dry_run: bool) -> None:
    meta = {
        "state_id": "PRN_N9",
        "name": "PRN Negeri Sembilan 2026",
        "migrated_from": "pas_break_2026",
        "migrated_at": datetime.now().isoformat(),
        "folders": {
            "crawls/news": "Berita RSS + direct scrape",
            "crawls/news_analyzed": "Tier A ML sentiment",
            "crawls/chinese_news": "Berita Cina 3 negeri (filter NS)",
            "crawls/adun_seeds": "ADUN social seed crawl",
            "reference": "JSON ringkasan + queries",
            "reports/dashboards": "Dashboard HTML",
            "reports/war_room": "War Room + WhatsApp",
            "reports/seats": "Analitik 36 kerusi SPR",
        },
        "daily_pipeline": "bash scripts/run_prn_n9_daily.sh",
    }
    path = prn_dir("N9") / "metadata.json"
    if not path.exists() and not dry_run:
        path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Migrate PRN data to state folders")
    parser.add_argument("--dry-run", action="store_true", help="Papar sahaja, jangan pindah")
    args = parser.parse_args()

    print("=" * 60)
    print("PRN Folder Migration")
    print("=" * 60)
    if args.dry_run:
        print("🔍 DRY RUN — tiada fail dipindah")

    total = migrate_n9(args.dry_run) + migrate_johor(args.dry_run) + migrate_melaka(args.dry_run)
    write_registry(args.dry_run)
    write_n9_metadata(args.dry_run)

    print(f"\n✅ Selesai — {total} fail {'akan dipindah' if args.dry_run else 'dipindah'}")
    print(f"   Root: {PRN_ROOT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
