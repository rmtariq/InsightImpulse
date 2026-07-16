"""Load Indian narrative seed CSVs and build crawl queries / keyword lists."""
from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Dict, List, Set

ROOT = Path(__file__).resolve().parents[1]
SEEDS_DIR = ROOT / "n9_chinese_narrative_dashboard/data/indian_narrative_seeds"

STATES_FOCUS = ("Negeri Sembilan", "Melaka", "Johor")
STATES_N9_ONLY = ("Negeri Sembilan",)
P1_ISSUES = (
    "Kos sara hidup",
    "Pekerjaan dan gaji",
    "Bantuan dan kebajikan",
    "Pendidikan dan SJKT",
    "Kuil dan rumah ibadat",
    "Infrastruktur dan jalan",
    "Banjir dan air",
    "Perumahan",
    "Kesihatan",
    "Keselamatan dan jenayah",
    "Diskriminasi dan hak",
    "Maklumat salah dan penipuan",
)


def _read_csv(name: str) -> List[Dict[str, str]]:
    path = SEEDS_DIR / name
    if not path.exists():
        return []
    with path.open(encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def load_location_rows() -> List[Dict[str, str]]:
    rows = _read_csv("07_location_keywords.csv")
    return [r for r in rows if r.get("state") in STATES_FOCUS]


def load_issue_rows() -> List[Dict[str, str]]:
    rows = _read_csv("08_issue_keywords_multilingual.csv")
    return [r for r in rows if r.get("issue_category") in P1_ISSUES]


def location_aliases() -> List[str]:
    out: Set[str] = set()
    for row in load_location_rows():
        out.add(row["state"].lower())
        for alias in (row.get("state_aliases") or "").split("|"):
            if alias.strip():
                out.add(alias.strip().lower())
        out.add(row["district_or_cluster"].lower())
        for alias in (row.get("search_aliases") or "").split("|"):
            if alias.strip():
                out.add(alias.strip().lower())
    return sorted(out)


def issue_terms_flat() -> List[str]:
    terms: Set[str] = set()
    for row in load_issue_rows():
        for col in ("bm_terms", "english_terms", "tamil_terms", "romanised_or_mixed_terms"):
            for part in (row.get(col) or "").split("|"):
                p = part.strip()
                if p and len(p) >= 3:
                    terms.add(p.lower())
    return sorted(terms)


def _split_terms(cell: str) -> List[str]:
    return [p.strip() for p in (cell or "").split("|") if p.strip()]


def generate_google_queries(states: tuple[str, ...] | None = None) -> List[Dict[str, Any]]:
    """Build Google News RSS queries from seed location + issue keywords.

    states: default Negeri Sembilan only. Pass STATES_FOCUS for all 3 negeri.
    """
    focus = states or STATES_N9_ONLY
    queries: List[Dict[str, Any]] = []
    qn = 0

    def add(lang: str, query: str, note: str = "") -> None:
        nonlocal qn
        qn += 1
        queries.append({
            "id": f"IN{qn}",
            "lang": lang,
            "community": "india",
            "query": query,
            "note": note,
        })

    # Site-specific Tamil / Indian media
    for site, label in (
        ("makkalosai.com.my", "Makkal Osai"),
        ("varnam.my", "Varnam"),
        ("vanakkammalaysia.com.my", "Vanakkam"),
        ("tamilmalar.my", "Tamil Malar"),
    ):
        for state in focus:
            add("tamil", f'site:{site} "{state}" when:30d', label)
        add("tamil", f"site:{site} SJKT OR MIC OR Hindu when:30d", label)
        add("tamil", f"site:{site} Tamil Malaysia when:14d", label)

    # Per-district discovery — N9 first; include others only if requested
    priority_districts = [
        "Seremban", "Nilai", "Port Dickson", "Bahau", "Tampin", "Jempol", "Rembau", "Jelebu",
    ]
    if "Melaka" in focus:
        priority_districts.extend(["Melaka Tengah", "Jasin"])
    if "Johor" in focus:
        priority_districts.extend(["Johor Bahru", "Kluang", "Batu Pahat", "Muar"])
    for district in priority_districts:
        add(
            "tamil",
            f'"{district}" (Tamil OR Indian OR SJKT OR MIC OR Hindu) when:30d',
            district,
        )

    # Issue × state (P1)
    issue_rows = {r["issue_category"]: r for r in load_issue_rows()}
    issue_bm_snippets = {
        "Pendidikan dan SJKT": "SJKT OR sekolah Tamil",
        "Kuil dan rumah ibadat": "kuil OR temple OR Hindu",
        "Bantuan dan kebajikan": "bantuan OR kebajikan OR MITRA",
        "Pekerjaan dan gaji": "kerja OR pekerja OR pengangguran",
        "Kos sara hidup": "kos sara hidup OR harga barang",
        "Infrastruktur dan jalan": "jalan rosak OR longkang",
        "Banjir dan air": "banjir OR bekalan air",
        "Perumahan": "rumah OR PPR OR sewa",
        "Kesihatan": "klinik OR hospital",
        "Keselamatan dan jenayah": "jenayah OR keselamatan",
        "Diskriminasi dan hak": "diskriminasi OR hak",
        "Maklumat salah dan penipuan": "berita palsu OR fake news",
    }
    for state in focus:
        for cat, snippet in issue_bm_snippets.items():
            if cat not in issue_rows:
                continue
            add("bm", f'"{state}" {snippet} when:30d', cat)

    # Tamil-script issue terms (romanised) × N9
    tamil_roman = ["SJKT", "kovil", "velai", "bantuan", "Tamil palli"]
    for term in tamil_roman:
        add("tamil", f'"{term}" "Negeri Sembilan" when:30d', "romanised")

    # National Indian community + state filter
    for state in focus:
        add("bm", f'"komuniti India" OR "pengundi India" OR MIC "{state}" when:30d', "community")

    return queries


def state_keywords_for_filter() -> tuple[str, ...]:
    """Extended state/location aliases for dashboard relevance filter."""
    base = (
        "negeri sembilan", "seremban", "nilai", "bahau", "port dickson", "tampin",
        "kuala pilah", "jelebu", "rembau", "jempol", "森美兰", "芙蓉", "马口", "波德申",
        "johor", "melaka", "skudai", "batu pahat", "muar", "kluang", "iskandar",
        "pasir gudang", "kulai", "tangkak", "segamat", "pontian", "mersing",
        "alor gajah", "jasin", "hang tuah jaya", "malacca", "n9", "ns",
    )
    extra = [a for a in location_aliases() if len(a) >= 4]
    return tuple(dict.fromkeys([*base, *extra]))
