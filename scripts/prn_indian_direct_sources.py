"""Tamil / Indian community direct scrape sources — percuma, tiada API key."""
from __future__ import annotations

from typing import Any, Dict, List

from prn_indian_seeds_loader import location_aliases, issue_terms_flat

# Keywords shared across Tamil media feeds
_STATE_KW = list(dict.fromkeys([
    "Negeri Sembilan", "Seremban", "Nilai", "Bahau", "Port Dickson", "Tampin",
    "Kuala Pilah", "Jempol", "Rembau", "Jelebu", "Melaka", "Malacca", "Johor",
    "PRN", "MIC", "Indian", "pengundi India", "komuniti India", "Hindu", "Tamil",
    "SJKT", "MITRA", "kuil", "தமிழ்", "செராம்பன்", "நெகிரி", "森美兰", "芙蓉", "州选",
    *[a for a in location_aliases() if len(a) >= 4][:40],
]))

_ISSUE_KW = [t for t in issue_terms_flat() if len(t) >= 4][:30]

INDIAN_DIRECT_SOURCES: List[Dict[str, Any]] = [
    {
        "id": "MO_N9_FILTERED",
        "name": "Makkal Osai — N9/Melaka/Johor filter",
        "method": "wordpress_rss",
        "feed_url": "https://makkalosai.com.my/feed/",
        "community": "india",
        "lang": "tamil",
        "comments": False,
        "keywords": _STATE_KW,
    },
    {
        "id": "MO_TAMIL_ALL",
        "name": "Makkal Osai — all Tamil headlines",
        "method": "tamil_rss",
        "feed_url": "https://makkalosai.com.my/feed/",
        "community": "india",
        "lang": "tamil",
        "comments": False,
        "keywords": None,
        "require_tamil_script": True,
    },
    {
        "id": "VARNAM_FILTERED",
        "name": "Varnam Malaysia — local Indian issues",
        "method": "publisher_rss",
        "feed_url": "https://varnam.my/feed/",
        "community": "india",
        "lang": "en",
        "comments": False,
        "keywords": _STATE_KW + _ISSUE_KW,
    },
    {
        "id": "VARNAM_ALL",
        "name": "Varnam Malaysia — headline feed",
        "method": "publisher_rss",
        "feed_url": "https://varnam.my/feed/",
        "community": "india",
        "lang": "en",
        "comments": False,
        "keywords": None,
    },
    {
        "id": "VANAKKAM_FILTERED",
        "name": "Vanakkam Malaysia — N9/Melaka/Johor",
        "method": "wordpress_rss",
        "feed_url": "https://vanakkammalaysia.com.my/feed/",
        "community": "india",
        "lang": "tamil",
        "comments": False,
        "keywords": _STATE_KW,
    },
    {
        "id": "VANAKKAM_TAMIL",
        "name": "Vanakkam Malaysia — Tamil headlines",
        "method": "tamil_rss",
        "feed_url": "https://vanakkammalaysia.com.my/feed/",
        "community": "india",
        "lang": "tamil",
        "comments": False,
        "keywords": None,
        "require_tamil_script": True,
    },
]
