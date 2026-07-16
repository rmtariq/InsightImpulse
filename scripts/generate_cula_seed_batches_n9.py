#!/usr/bin/env python3
"""
Jana batch cula digital — 36 DUN N9 (satu fail per kerusi).

Setiap fail: template seed post santai + ruang paste URL post tempatan.
Selepas 2–3 hari biar komen masuk → isi URL → crawl via Direct URL mode.

Usage:
  python3 scripts/generate_cula_seed_batches_n9.py
  python3 scripts/generate_cula_seed_batches_n9.py --code N10
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

QUERIES_JSON = ROOT / "data/projects/political/PRN/PRN_N9/reference/n9_36dun_crawl_queries.json"
MANIFEST_JSON = ROOT / "data/projects/political/PRN/PRN_N9/reports/war_room/prototype/insightpulse/prn-monitoring/data/prn_excel_intel_manifest.json"
OUT_DIR = ROOT / "data/projects/political/PRN/_shared/url_batches/cula_seeds_N9"
MYT = timezone(timedelta(hours=8))

# Contoh gaya post santai — variasi ikut tier
SEED_TEMPLATES = {
    "WAJIB-PAS23": [
        'agaknya di {name} ni PAS menang ok ke? tengok ramai bincang pasal {issue} je',
        'korang area {landmark} — undi kali ni ikut parti ke ikut calon?',
        'siapa lagi kat {name} rasa {issue} makin susah ni?',
    ],
    "IMBANG": [
        'area {name} — BN ke PAS ke PH yg lebih sesuai kali ni?',
        'tengok {landmark}, ramai bincang pasal {issue}. korang macam mana?',
        'agaknya kerusi {name} flip ke kali ni?',
    ],
    "LAWAN": [
        'korang {name} — kestabilan ke perubahan yg korang nak?',
        'tengok isu {issue} kat {landmark}, ada calon yg boleh selesaikan ke?',
        'PRN kali ni {name} — sokong status quo ke nak perubahan?',
    ],
}


def load_dun_intel() -> dict[str, dict]:
    if not MANIFEST_JSON.exists():
        return {}
    data = json.loads(MANIFEST_JSON.read_text(encoding="utf-8"))
    out: dict[str, dict] = {}
    for row in data.get("dun_keywords", []):
        if row.get("state") != "Negeri Sembilan":
            continue
        code = str(row.get("dun_code", "")).upper()
        if code:
            out[code] = row
    return out


def first_landmark(intel: dict) -> str:
    raw = str(intel.get("local_landmarks") or intel.get("dun_name") or "")
    part = raw.split(";")[0].strip()
    return part or intel.get("dun_name", "kawasan ni")


def first_issue(intel: dict) -> str:
    raw = str(intel.get("local_issues") or intel.get("service_keywords") or "kos hidup")
    part = raw.split(";")[0].strip()
    return part or "kos hidup"


def seed_examples(seat: dict, intel: dict) -> list[str]:
    tier = seat.get("tier") or "LAWAN"
    name = seat["name"]
    landmark = first_landmark(intel) if intel else name
    issue = first_issue(intel) if intel else "kos hidup"
    templates = SEED_TEMPLATES.get(tier, SEED_TEMPLATES["LAWAN"])
    return [t.format(name=name, landmark=landmark, issue=issue) for t in templates]


def build_file_content(seat: dict, intel: dict) -> str:
    code = seat["code"]
    name = seat["name"]
    tier = seat.get("tier", "")
    district = str(intel.get("district") or "")
    landmarks = str(intel.get("local_landmarks") or name)
    issues = str(intel.get("local_issues") or "kos hidup; perkhidmatan")
    examples = seed_examples(seat, intel)

    lines = [
        f"# CULA DIGITAL — {code} {name} (seed post URLs)",
        "# " + "=" * 58,
        f"# Tier: {tier} · Daerah: {district or '—'}",
        "#",
        "# ALIRAN (sama semua 36 DUN):",
        f"#   1. Post santai di kumpulan/halaman TEMATAN {name} (bukan page parti rasmi)",
        "#   2. Biar 2–3 hari — biar komen organik masuk",
        "#   3. Salin URL post (bukan profil) ke bawah",
        f"#   4. Crawl: python3 scripts/crawl_cula_seed_batches_n9.py --code {code}",
        "#      atau InsightPulse Direct URL → paste URL dari fail ini",
        "#",
        f"# LOKASI / LANDMARK: {landmarks}",
        f"# ISU TEMPATAN: {issues}",
        "#",
        "# CONTOH GAYA POST (santai, bukan formal):",
    ]
    for ex in examples:
        lines.append(f'#   "{ex}"')
    lines.extend([
        "#",
        "# KRITERIA URL TEMATAN:",
        f"#   • Kumpulan FB / TikTok / Threads warga {name} atau {landmarks.split(';')[0].strip()}",
        f"#   • Post sebut {name} atau isu tempatan dalam teks/komen",
        "#   • Bukan URL profil/halaman — hanya URL POST spesifik",
        "#",
        "# LOG SEED (pasukan isi bila hantar):",
        "# seed_date | platform | group/page | post_url | nota",
        "#",
        "# PASTE URL POST DI BAWAH:",
    ])
    return "\n".join(lines) + "\n"


def collect_filled_urls() -> list[tuple[str, str, str]]:
    """Return (code, name, url) for all non-comment http lines across batch files."""
    filled: list[tuple[str, str, str]] = []
    if not OUT_DIR.exists():
        return filled
    for path in sorted(OUT_DIR.glob("N*.txt")):
        m = re.match(r"(N\d{2})_(.+)_PASTE_ONLY\.txt", path.name)
        if not m:
            continue
        code, name_part = m.group(1), m.group(2).replace("_", " ")
        for line in path.read_text(encoding="utf-8").splitlines():
            s = line.strip()
            if s.startswith("#") or not s.startswith("http"):
                continue
            filled.append((code, name_part, s.split()[0]))
    return filled


def write_combined_paste(filled: list[tuple[str, str, str]]) -> Path:
    combined = OUT_DIR / "ALL_FILLED_URLS_PASTE_ONLY.txt"
    lines = [
        "# Gabungan URL cula seed yang sudah diisi — 36 DUN N9",
        f"# Generated: {datetime.now(MYT).strftime('%Y-%m-%d %H:%M')}",
        f"# Total URLs: {len(filled)}",
        "# Crawl semua: python3 scripts/crawl_cula_seed_batches_n9.py --all-filled",
        "",
    ]
    for code, name, url in filled:
        lines.append(f"# {code} {name}")
        lines.append(url)
        lines.append("")
    combined.write_text("\n".join(lines), encoding="utf-8")
    return combined


def main() -> int:
    p = argparse.ArgumentParser(description="Generate cula seed batch files for 36 DUN N9")
    p.add_argument("--code", help="Single DUN e.g. N10")
    args = p.parse_args()

    seats = json.loads(QUERIES_JSON.read_text(encoding="utf-8"))["seats"]
    if args.code:
        seats = [s for s in seats if s["code"].upper() == args.code.upper()]
        if not seats:
            raise SystemExit(f"Tiada kerusi {args.code}")

    intel_map = load_dun_intel()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    manifest_seats = []
    for seat in seats:
        code = seat["code"]
        intel = intel_map.get(code.upper(), {})
        fname = f"{code}_{seat['name'].replace(' ', '_')}_PASTE_ONLY.txt"
        out_path = OUT_DIR / fname
        content = build_file_content(seat, intel)
        if out_path.exists():
            # Preserve pasted URLs — only refresh header if file has URLs
            existing = out_path.read_text(encoding="utf-8")
            url_lines = [l for l in existing.splitlines() if l.strip().startswith("http")]
            if url_lines:
                content = content + "\n".join(url_lines) + "\n"
        out_path.write_text(content, encoding="utf-8")
        manifest_seats.append({
            "code": code,
            "name": seat["name"],
            "tier": seat.get("tier"),
            "file": fname,
            "district": intel.get("district"),
            "local_landmarks": intel.get("local_landmarks"),
            "local_issues": intel.get("local_issues"),
            "seed_examples": seed_examples(seat, intel),
            "urls_filled": sum(
                1 for l in out_path.read_text(encoding="utf-8").splitlines()
                if l.strip().startswith("http")
            ),
        })
        print(f"  ✅ {fname}")

    filled = collect_filled_urls()
    combined_path = write_combined_paste(filled)

    manifest = {
        "title": "Cula Digital — 36 DUN N9 seed post URL batches",
        "generated_at": datetime.now(MYT).isoformat(timespec="seconds"),
        "count": len(manifest_seats),
        "out_dir": str(OUT_DIR.relative_to(ROOT)),
        "combined_paste": combined_path.name,
        "total_urls_filled": len(filled),
        "seats_with_urls": len({c for c, _, _ in filled}),
        "workflow": [
            "Post santai per DUN di kumpulan tempatan (2–3 hari tunggu)",
            "Paste URL post ke fail Nxx_*.txt",
            "python3 scripts/crawl_cula_seed_batches_n9.py --all-filled",
            "python3 scripts/merge_prn_johor_n9_master.py",
            "python3 scripts/build_warroom_production_bundle.py",
        ],
        "seats": manifest_seats,
    }
    (OUT_DIR / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"\n📋 {len(manifest_seats)} fail → {OUT_DIR.relative_to(ROOT)}")
    print(f"   URL diisi: {len(filled)} ({manifest['seats_with_urls']} kerusi)")
    print(f"   Combined: {combined_path.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
