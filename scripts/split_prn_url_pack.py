#!/usr/bin/env python3
"""Split PRN Johor+N9 URL pack into InsightPulse Direct URL Crawl batches."""
from __future__ import annotations

import argparse
import re
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SRC = Path.home() / "Downloads/PRN_JOHOR_N9_COPY_PASTE_URL_PACK (3)/PRN_JOHOR_N9_FULL_URLS_COPY_PASTE.txt"
OUT_DIR = ROOT / "data/projects/political/PRN/_shared/url_batches"

PARTY_OFFICIAL = {
    "facebook.com/amanahmalaysia",
    "facebook.com/partibersatumalaysia",
    "facebook.com/dapmalaysia",
    "facebook.com/mypasmalaysia",
    "facebook.com/pakatanharapanrasmi",
    "facebook.com/partikeadilanrakyat",
    "facebook.com/pnrasmi",
    "facebook.com/umno.org.my",
    "facebook.com/umnojohor",
    "facebook.com/amanahnegerisembilanofficial",
    "facebook.com/gerakanrasmi",
    "facebook.com/mcaofficial",
    "facebook.com/micparti",
    "facebook.com/mudamalaysia",
    "facebook.com/pemudapasnegeri9",
    "instagram.com/pnrasmi",
    "instagram.com/dapmalaysia",
    "instagram.com/umnoonline",
    "instagram.com/bersatuofficial",
    "instagram.com/mudamalaysia",
    "tiktok.com/@pasofficial",
    "tiktok.com/@umnoofficial",
    "tiktok.com/@bersatuofficial",
    "tiktok.com/@dapofficial",
    "tiktok.com/@umno_ns",
    "threads.net/@dapmalaysia",
    "threads.net/@umnoonline",
}

LEADER_HINTS = (
    "anwaribrahim", "ahmadzahid", "muhyiddin", "rafizi", "hadiawang", "hamzah",
    "saifuddin", "tuanibrahim", "tunmahathir", "lokesiewfook", "anthonyloke",
    "onnhafiz", "leetinghan", "khalednordin", "limkitsiang", "khairykj",
    "tokmat", "dsaminuddin", "jalaluddin", "muhyiddinyassin", "zahidhamidi",
)


def load_urls(path: Path) -> list[str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    return [l.strip() for l in lines if l.strip().startswith("http")]


def is_news(url: str) -> bool:
    u = url.lower()
    social = ("facebook.com", "instagram.com", "tiktok.com", "x.com", "twitter.com", "youtube.com", "threads.net", "linkedin.com")
    return not any(s in u for s in social)


def is_search_or_tag(url: str) -> bool:
    u = url.lower()
    if "/search" in u or "results?search_query" in u:
        return True
    if "/explore/tags/" in u or "/explore/search/" in u:
        return True
    if re.search(r"tiktok\.com/tag/", u):
        return True
    return False


def is_party_or_leader(url: str) -> bool:
    u = url.lower()
    for p in PARTY_OFFICIAL:
        if p in u:
            return True
    return any(h in u for h in LEADER_HINTS)


def platform(url: str) -> str:
    u = url.lower()
    if "facebook.com" in u or "fb.com" in u:
        return "facebook"
    if "instagram.com" in u:
        return "instagram"
    if "tiktok.com" in u:
        return "tiktok"
    if "x.com" in u or "twitter.com" in u:
        return "x"
    if "youtube.com" in u or "youtu.be" in u:
        return "youtube"
    if "threads.net" in u:
        return "threads"
    return "news"


def classify(url: str) -> str:
    if is_news(url):
        return "news"
    if is_party_or_leader(url):
        return "batch1"
    if is_search_or_tag(url):
        return "batch2"
    p = platform(url)
    if p == "facebook":
        return "batch3"
    if p in ("instagram", "tiktok", "x"):
        return "batch4"
    if p in ("youtube", "threads"):
        return "batch5"
    return "batch5"


BATCH_META = {
    "batch1": ("01_parti_rasmi_pemimpin.txt", "Parti rasmi + pemimpin (FB/IG/TikTok/X/Threads)"),
    "batch2": ("02_search_hashtag_queries.txt", "Search / hashtag / YouTube results queries"),
    "batch3": ("03_facebook_profil_halaman_kumpulan.txt", "Facebook profil, ADUN, halaman, kumpulan"),
    "batch4": ("04_instagram_tiktok_x_profil.txt", "Instagram + TikTok @ + X profil (bukan search)"),
    "batch5": ("05_youtube_threads.txt", "YouTube saluran + baki YouTube/Threads"),
    "news": ("06_BONUS_berita_guna_keyword_mode.txt", "Portal berita — guna Keyword+News, BUKAN Direct URL"),
}


def write_batch(out_dir: Path, key: str, urls: list[str]) -> Path:
    fname, title = BATCH_META[key]
    path = out_dir / fname
    header = f"""# {title}
# Generated: {datetime.now():%Y-%m-%d %H:%M}
# URLs: {len(urls)}
# InsightPulse: Direct URL Crawl | Date Range: Last 7 Days | Dataset: 1000-2000
#
"""
    path.write_text(header + "\n".join(urls) + "\n", encoding="utf-8")
    return path


def write_readme(out_dir: Path, counts: dict[str, int], src: Path) -> None:
    readme = f"""PRN Johor + N9 — URL Crawl Batches
================================
Source: {src.name}
Generated: {datetime.now():%Y-%m-%d %H:%M}
Total URLs split: {sum(counts.values())}

CARA GUNA (InsightPulse http://localhost:8001)
----------------------------------------------
1. Mod: Direct URL Crawl
2. Paste isi fail .txt (URL sahaja, abaikan baris #)
3. Date Range: Last 7 Days
4. Dataset Size: 1000 (batch kecil) atau 2000 (batch besar)
5. Analysis Type: Social Listening
6. Project: pas_break_2026 (atau projek PRN anda)

URUTAN DISYORKAN
----------------
"""
    order = ["batch1", "batch2", "batch3", "batch4", "batch5", "news"]
    for i, key in enumerate(order, 1):
        fname, title = BATCH_META[key]
        n = counts.get(key, 0)
        note = " ← guna Keyword Search + platform News" if key == "news" else ""
        readme += f"  {i}. {fname} ({n} URL) — {title}{note}\n"

    readme += """
NOTA PENTING
------------
- Batch 2 (search/hashtag): kadang kurang stabil di Direct URL — OK untuk cuba, backup guna Keyword mode
- Batch 6 berita: Direct URL TIDAK disokong — crawl berita via Keyword + tick News
- Jangan paste semua batch serentak — satu batch, tunggu siap, baru batch seterusnya
- Anggaran masa: 15-45 min per batch (bergantung saiz & platform)

LOKASI FAIL
-----------
"""
    readme += f"{out_dir}\n"
    (out_dir / "README.txt").write_text(readme, encoding="utf-8")


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--src", type=Path, default=DEFAULT_SRC)
    p.add_argument("--out", type=Path, default=OUT_DIR)
    args = p.parse_args()
    if not args.src.exists():
        raise SystemExit(f"Source not found: {args.src}")

    urls = load_urls(args.src)
    buckets: dict[str, list[str]] = {k: [] for k in BATCH_META}
    for url in urls:
        buckets[classify(url)].append(url)

    args.out.mkdir(parents=True, exist_ok=True)
    for key in BATCH_META:
        if buckets[key]:
            write_batch(args.out, key, buckets[key])

    write_readme(args.out, {k: len(v) for k, v in buckets.items()}, args.src)

    # Combined paste files for quick copy (URLs only, no comments)
    for key in ("batch1", "batch2", "batch3", "batch4", "batch5"):
        fname = BATCH_META[key][0]
        pure = args.out / fname.replace(".txt", "_PASTE_ONLY.txt")
        pure.write_text("\n".join(buckets[key]) + "\n", encoding="utf-8")

    print(f"✅ Split {len(urls)} URLs → {args.out}")
    for key in BATCH_META:
        print(f"   {BATCH_META[key][0]}: {len(buckets[key])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
