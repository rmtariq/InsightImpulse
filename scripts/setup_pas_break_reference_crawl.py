#!/usr/bin/env python3
"""Import Politik Excel, add PRN sheet, extract crawl URL lists for Direct URL mode."""

import json
import re
import shutil
from datetime import datetime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC_XLSX = Path("/Users/rmtariq/Downloads/Politik_Malaysia_SocMed_2026.xlsx")
REF_DIR = ROOT / "data/projects/political/pas_break_2026/reference"
EVENT_CSV = ROOT / "data/projects/political/pas_break_2026/master/PAS_Break_Master_EventWindow_Jun9-10_20260610_232442.csv"
METADATA = ROOT / "data/projects/political/pas_break_2026/metadata.json"

POLITICAL_KW = re.compile(
    r"parti islam|pas\b|bersatu|perikatan nasional|muafakat nasional|muhyiddin|hadi awang|"
    r"prn johor|prn melaka|negeri sembilan|putus|berpisah|perpecahan|pas solo|gerak solo",
    re.I,
)
NOISE = re.compile(
    r"gradur|indonesia|ojk|sptrakori|kyungho|wet world|skutahub|recehan|sénégal|#fypシ",
    re.I,
)

# PRN state accounts — verified where noted in Nota column
PRN_ROWS = [
    # Negeri Sembilan
    ("PN/PH", "PH", "Aminuddin Harun", "MB Negeri Sembilan", "Facebook", "facebook.com/aminuddinharun", "Pemimpin Negeri", "NS"),
    ("PN", "PAS", "PAS Negeri Sembilan", "Parti Negeri", "Facebook", "facebook.com/pasnegeri9", "Parti Negeri — verified dari crawl", "NS"),
    ("PN", "PAS", "PAS Negeri Sembilan", "Parti Negeri", "Instagram", "@pasnegeri9", "Parti Negeri", "NS"),
    ("PN", "PAS", "Pemuda PAS NS", "Wing Pemuda", "Facebook", "facebook.com/pemudapasns", "Wing Negeri", "NS"),
    ("BN", "UMNO", "UMNO Negeri Sembilan", "Parti Negeri", "Facebook", "facebook.com/umnonegerisembilan", "Parti Negeri", "NS"),
    ("PH", "DAP", "DAP Negeri Sembilan", "Parti Negeri", "Facebook", "facebook.com/dapnegerisembilan", "Parti Negeri", "NS"),
    # Johor
    ("BN", "UMNO", "Onn Hafiz Ghazi", "MB Johor", "Facebook", "facebook.com/OnnHafizGhazi", "Pemimpin Negeri", "Johor"),
    ("BN", "UMNO", "Onn Hafiz Ghazi", "MB Johor", "Instagram", "@onnhafizghazi", "Pemimpin Negeri", "Johor"),
    ("PN", "PAS", "PAS Johor", "Parti Negeri", "Facebook", "facebook.com/PASJohor", "Parti Negeri", "Johor"),
    ("PN", "PAS", "PAS Johor", "Parti Negeri", "Instagram", "@pas_johor", "Parti Negeri", "Johor"),
    ("PN", "PAS", "PAS Johor", "Parti Negeri", "TikTok", "@pasjohor", "Parti Negeri", "Johor"),
    ("BN", "UMNO", "UMNO Johor", "Parti Negeri", "Facebook", "facebook.com/UMNOJohor", "Parti Negeri", "Johor"),
    ("PN", "Bersatu", "Bersatu Johor", "Parti Negeri", "Facebook", "facebook.com/bersatujohor", "Parti Negeri", "Johor"),
    # Melaka
    ("PH", "PKR", "Kerajaan Melaka (PH)", "Kerajaan Negeri", "Facebook", "facebook.com/kerajaanmelaka", "Parti/Kerajaan", "Melaka"),
    ("PN", "PAS", "PAS Melaka", "Parti Negeri", "Facebook", "facebook.com/pasmelaka", "Parti Negeri", "Melaka"),
    ("BN", "UMNO", "UMNO Melaka", "Parti Negeri", "Facebook", "facebook.com/UMNOMelaka", "Parti Negeri", "Melaka"),
    ("PN", "Bersatu", "Bersatu Melaka", "Parti Negeri", "Facebook", "facebook.com/bersatumelaka", "Parti Negeri", "Melaka"),
]


def normalize_url(handle: str, platform: str) -> str | None:
    if pd.isna(handle) or str(handle).strip() in ("—", "-", "", "nan"):
        return None
    h = str(handle).strip()
    if h.startswith("http"):
        return h.split("?")[0].rstrip("/")
    if h.startswith("facebook.") or "facebook.com" in h:
        h = h if h.startswith("www.") or h.startswith("facebook.") else h
        if not h.startswith("http"):
            h = "https://www." + h.lstrip("www.")
        return h.rstrip("/")
    if "x.com" in h or "twitter.com" in h:
        return ("https://" + h.lstrip("https://").lstrip("http://")).rstrip("/")
    if h.startswith("@"):
        user = h[1:]
        p = platform.lower()
        if "tiktok" in p:
            return f"https://www.tiktok.com/@{user}"
        if "instagram" in p:
            return f"https://www.instagram.com/{user}/"
        if "x" in p or "twitter" in p:
            return f"https://x.com/{user}"
    return None


def load_crawler_reference(xlsx: Path) -> pd.DataFrame:
    df = pd.read_excel(xlsx, sheet_name="Crawler Reference", header=1)
    df.columns = ["Koalisi", "Parti", "Nama", "Platform", "Handle_URL", "Jenis"]
    df["Full_URL"] = df.apply(lambda r: normalize_url(r["Handle_URL"], r["Platform"]), axis=1)
    df["Negeri"] = "Nasional"
    df["Sumber"] = "Crawler Reference"
    return df


def build_prn_df() -> pd.DataFrame:
    rows = []
    for koalisi, parti, nama, jawatan, platform, handle, jenis, negeri in PRN_ROWS:
        url = normalize_url(handle, platform)
        rows.append({
            "Koalisi": koalisi,
            "Parti": parti,
            "Nama": nama,
            "Platform": platform,
            "Handle_URL": handle,
            "Jenis": jenis,
            "Negeri": negeri,
            "Full_URL": url,
            "Sumber": "PRN Negeri (added)",
        })
    return pd.DataFrame(rows)


def is_political_row(row) -> bool:
    text = str(row.get("Text", ""))
    if NOISE.search(text):
        return False
    if str(row.get("mentions_pas", "")).lower() == "true":
        return True
    if str(row.get("mentions_bersatu", "")).lower() == "true":
        return True
    if str(row.get("narrative_split", "")).lower() == "true":
        return True
    if str(row.get("narrative_solo", "")).lower() == "true":
        return True
    return bool(POLITICAL_KW.search(text))


def extract_viral_posts(csv_path: Path, n=30) -> pd.DataFrame:
    df = pd.read_csv(csv_path, low_memory=False)
    df["eng"] = pd.to_numeric(df.get("total_engagement", 0), errors="coerce").fillna(0)
    df = df[df.apply(is_political_row, axis=1)].copy()
    df = df[df["eng"] > 500]
    # Prefer post rows; for comments use parent URL
    posts = df[df["Type"].astype(str).str.lower() == "post"].copy()
    posts = posts.sort_values("eng", ascending=False).drop_duplicates(subset=["URL"])
    rows = []
    for _, r in posts.head(n).iterrows():
        url = str(r.get("URL", "")).strip()
        if not url.startswith("http"):
            continue
        rows.append({
            "Platform": r.get("Platform"),
            "Engagement": int(r["eng"]),
            "Text": str(r.get("Text", ""))[:120],
            "Full_URL": url.split("?")[0],
            "Negeri": "Viral",
            "Sumber": "Event Window Top Posts",
            "Nama": "Viral Post",
            "Parti": "Rakyat/Organik",
        })
    # Also top parent post URLs from high-engagement comments
    comments = df[df["Type"].astype(str).str.lower() == "comment"].copy()
    if "Parent_Post_URL" in comments.columns:
        parent = (
            comments[comments["Parent_Post_URL"].notna()]
            .groupby("Parent_Post_URL")
            .agg(eng=("eng", "sum"), n=("eng", "count"))
            .reset_index()
            .sort_values("eng", ascending=False)
        )
        seen = {r["Full_URL"] for r in rows}
        for _, r in parent.head(15).iterrows():
            url = str(r["Parent_Post_URL"]).split("?")[0]
            if url.startswith("http") and url not in seen:
                rows.append({
                    "Platform": "facebook" if "facebook" in url else "mixed",
                    "Engagement": int(r["eng"]),
                    "Text": f"Parent post ({int(r['n'])} comments in dataset)",
                    "Full_URL": url,
                    "Negeri": "Viral",
                    "Sumber": "High-comment Parent Posts",
                    "Nama": "Viral Thread",
                    "Parti": "Rakyat/Organik",
                })
                seen.add(url)
    return pd.DataFrame(rows)


def write_url_file(path: Path, urls: list[str], header: str):
    lines = [f"# {header}", f"# Generated: {datetime.now():%Y-%m-%d %H:%M}", f"# Count: {len(urls)}", ""]
    lines.extend(urls)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    REF_DIR.mkdir(parents=True, exist_ok=True)
    dest_xlsx = REF_DIR / "Politik_Malaysia_SocMed_2026.xlsx"
    shutil.copy2(SRC_XLSX, dest_xlsx)

    official = load_crawler_reference(dest_xlsx)
    prn = build_prn_df()
    viral = extract_viral_posts(EVENT_CSV, n=25)

    # Append PRN to excel
    prn_excel = prn[["Koalisi", "Parti", "Nama", "Platform", "Handle_URL", "Jenis"]].copy()
    prn_excel.insert(0, "Negeri PRN", prn["Negeri"])

    with pd.ExcelWriter(dest_xlsx, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
        prn_excel.to_excel(writer, sheet_name="PRN Negeri", index=False)
        # Combined master for crawl
        combined = pd.concat([
            official[["Koalisi", "Parti", "Nama", "Platform", "Handle_URL", "Jenis", "Negeri", "Full_URL", "Sumber"]],
            prn[["Koalisi", "Parti", "Nama", "Platform", "Handle_URL", "Jenis", "Negeri", "Full_URL", "Sumber"]],
        ], ignore_index=True)
        combined = combined[combined["Full_URL"].notna()].drop_duplicates(subset=["Full_URL"])
        combined.to_excel(writer, sheet_name="Crawl URL Master", index=False)
        viral.to_excel(writer, sheet_name="Viral Posts URLs", index=False)

    # URL list files for UI paste
    official_urls = official["Full_URL"].dropna().unique().tolist()
    prn_urls = prn["Full_URL"].dropna().unique().tolist()
    pas_bersatu = official[
        official["Parti"].astype(str).str.contains("PAS|Bersatu", case=False, na=False)
    ]["Full_URL"].dropna().unique().tolist()
    prn_ns = prn[prn["Negeri"] == "NS"]["Full_URL"].dropna().unique().tolist()
    prn_johor = prn[prn["Negeri"] == "Johor"]["Full_URL"].dropna().unique().tolist()
    prn_melaka = prn[prn["Negeri"] == "Melaka"]["Full_URL"].dropna().unique().tolist()
    viral_urls = viral["Full_URL"].dropna().unique().tolist()

    write_url_file(REF_DIR / "crawl_urls_01_official_all.txt", sorted(official_urls),
                   "Crawl 3A — Akaun rasmi & pemimpin (82 URLs) — paste ke Direct URL Crawl")
    write_url_file(REF_DIR / "crawl_urls_02_pas_bersatu.txt", sorted(pas_bersatu),
                   "Crawl 3B — PAS + Bersatu sahaja (18 URLs) — Suara Elit")
    write_url_file(REF_DIR / "crawl_urls_03_prn_negeri.txt", sorted(prn_urls),
                   "Crawl 3C — PRN NS/Johor/Melaka (17 URLs) — Akaun negeri")
    write_url_file(REF_DIR / "crawl_urls_04_viral_posts.txt", viral_urls,
                   "Crawl 3D — Top viral post URLs (25+) — Deep comment crawl")
    write_url_file(REF_DIR / "crawl_urls_05_prn_ns_only.txt", sorted(prn_ns),
                   "Crawl 3E — Negeri Sembilan sahaja")
    write_url_file(REF_DIR / "crawl_urls_06_prn_johor_only.txt", sorted(prn_johor),
                   "Crawl 3F — Johor sahaja")

    # CSV for reference
    pd.DataFrame({"url": viral_urls}).to_csv(REF_DIR / "viral_post_urls.csv", index=False)
    combined.to_csv(REF_DIR / "crawl_url_master.csv", index=False)

    # README
    readme = f"""PAS Break 2026 — Reference & Crawl URL Lists
Generated: {datetime.now():%Y-%m-%d %H:%M}

FILES:
  Politik_Malaysia_SocMed_2026.xlsx  — Direktori + sheet baru PRN Negeri
  crawl_urls_01_official_all.txt     — {len(official_urls)} akaun rasmi/pemimpin
  crawl_urls_02_pas_bersatu.txt      — {len(pas_bersatu)} PAS + Bersatu (suara elit)
  crawl_urls_03_prn_negeri.txt       — {len(prn_urls)} PRN NS/Johor/Melaka
  crawl_urls_04_viral_posts.txt      — {len(viral_urls)} post viral (deep komen)
  crawl_url_master.csv               — Master gabungan

CARA GUNA (InsightPulse UI):
  1. Buka http://localhost:8001
  2. Mod Crawl → Direct URL Crawl
  3. Copy-paste URL dari fail .txt (satu URL per baris, abaikan baris #)
  4. Project: pas_break_2026
  5. Dataset: 2000-3000 (fokus komen)

CADANGAN URUTAN CRAWL:
  Crawl 3B (PAS+Bersatu) → suara elit post-split
  Crawl 3D (viral posts) → komen rakyat deep-dive
  Crawl 3E (NS only)     → fokus EXCO Negeri Sembilan
"""
    (REF_DIR / "README.txt").write_text(readme, encoding="utf-8")

    # Update metadata
    if METADATA.exists():
        meta = json.loads(METADATA.read_text(encoding="utf-8"))
        meta.setdefault("reference", {})
        meta["reference"] = {
            "excel": "reference/Politik_Malaysia_SocMed_2026.xlsx",
            "updated": datetime.now().isoformat(),
            "official_urls": len(official_urls),
            "prn_urls": len(prn_urls),
            "viral_post_urls": len(viral_urls),
            "pending_crawl": "crawl3_direct_url",
        }
        meta.setdefault("pending", [])
        if "crawl3_direct_url" not in meta["pending"]:
            meta["pending"].append("crawl3_direct_url")
        meta["updated_at"] = datetime.now().isoformat()
        METADATA.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"✅ Excel: {dest_xlsx}")
    print(f"✅ Official URLs: {len(official_urls)}")
    print(f"✅ PAS+Bersatu: {len(pas_bersatu)}")
    print(f"✅ PRN negeri: {len(prn_urls)}")
    print(f"✅ Viral posts: {len(viral_urls)}")
    print(f"✅ README: {REF_DIR / 'README.txt'}")


if __name__ == "__main__":
    main()
