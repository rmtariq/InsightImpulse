#!/usr/bin/env python3
"""Lokasi pusat semua projek PRN negeri — N9, Johor, Melaka."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

ROOT = Path(__file__).resolve().parents[1]
POLITICAL = ROOT / "data/projects/political"
PRN_ROOT = POLITICAL / "PRN"
SHARED = PRN_ROOT / "_shared"

# Legacy — narrative PAS-Break merentasi negeri (socmed master)
PAS_BREAK = POLITICAL / "pas_break_2026"

STATES: Dict[str, Dict[str, Any]] = {
    "N9": {
        "id": "PRN_N9",
        "name": "Negeri Sembilan",
        "name_ms": "Negeri Sembilan",
        "code": "N9",
        "slug": "negeri-sembilan",
        "dun_seats": 36,
        "excel_spr": ROOT / "JITP_2026/Master_File/PRN2023_NegeriSembilan_v2.xlsx",
    },
    "Johor": {
        "id": "PRN_Johor",
        "name": "Johor",
        "name_ms": "Johor",
        "code": "JHR",
        "slug": "johor",
        "dun_seats": 56,
        "excel_spr": None,
        "legacy_dir": POLITICAL / "prn_johor_2026",
    },
    "Melaka": {
        "id": "PRN_Melaka",
        "name": "Melaka",
        "name_ms": "Melaka",
        "code": "MLK",
        "slug": "melaka",
        "dun_seats": 28,
        "excel_spr": None,
    },
}


def prn_dir(state: str = "N9") -> Path:
    """Root folder negeri: data/projects/political/PRN/PRN_N9/"""
    key = state if state in STATES else "N9"
    return PRN_ROOT / STATES[key]["id"]


def crawls(state: str = "N9", layer: str = "news") -> Path:
    """
    Layer crawl:
      news | news_analyzed | chinese_news | social | adun_seeds | archive
    """
    return prn_dir(state) / "crawls" / layer


def reference(state: str = "N9") -> Path:
    return prn_dir(state) / "reference"


def reports(state: str = "N9") -> Path:
    return prn_dir(state) / "reports"


def master(state: str = "N9") -> Path:
    return prn_dir(state) / "master"


def queries(state: str = "N9") -> Path:
    return reference(state) / "queries"


def metadata_path(state: str = "N9") -> Path:
    return prn_dir(state) / "metadata.json"


def ensure_state_dirs(state: str = "N9") -> Path:
    """Cipta semua subfolder standard untuk satu negeri."""
    base = prn_dir(state)
    for sub in (
        "crawls/news",
        "crawls/news_analyzed",
        "crawls/chinese_news",
        "crawls/indian_narrative",
        "crawls/social",
        "crawls/adun_seeds",
        "crawls/archive",
        "reference/queries",
        "reference/seeds",
        "master",
        "reports/seats",
        "reports/war_room",
        "reports/dashboards",
        "archive",
    ):
        (base / sub).mkdir(parents=True, exist_ok=True)
    SHARED.mkdir(parents=True, exist_ok=True)
    (SHARED / "spr").mkdir(parents=True, exist_ok=True)
    (SHARED / "templates").mkdir(parents=True, exist_ok=True)
    (SHARED / "chinese_narrative").mkdir(parents=True, exist_ok=True)
    return base


def latest_crawl(state: str = "N9", layer: str = "news", pattern: str = "*.csv") -> Path | None:
    folder = crawls(state, layer)
    if not folder.exists():
        return None
    files = sorted(folder.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0] if files else None


def resolve_existing(*candidates: Path) -> Path:
    """Guna path pertama yang wujud (sokong migrasi lama → baru)."""
    for p in candidates:
        if p.exists():
            return p
    return candidates[0]


# Legacy paths (pra-migrasi)
_LEGACY_N9 = POLITICAL / "pas_break_2026"
