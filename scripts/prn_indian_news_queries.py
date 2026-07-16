"""Google News query pack for Indian / Tamil narrative crawl."""
from __future__ import annotations

from typing import Any, Dict, List

from prn_indian_seeds_loader import generate_google_queries

COMMUNITY_LABELS = {"india": "Komuniti India / Tamil"}


def all_queries() -> List[Dict[str, Any]]:
    return generate_google_queries()


def query_ids() -> set[str]:
    return {q["id"] for q in all_queries()}
