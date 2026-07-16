"""Direct scrape sources — percuma, tiada API key."""
from __future__ import annotations

from typing import Any, Dict, List

# Komen percuma: China Press (Coral API), FMT (WordPress comment RSS)
# Artikel sahaja: BH, HMetro, Utusan, Malaysiakini (RSS)

DIRECT_NEWS_SOURCES: List[Dict[str, Any]] = [
    {
        "id": "CP_N9",
        "name": "China Press 森州人 (n9.chinapress.com.my)",
        "method": "chinapress",
        "base_url": "https://n9.chinapress.com.my",
        "community": "cina",
        "lang": "cina",
        "comments": True,
        "listing_urls": [
            "https://n9.chinapress.com.my/category/%e6%94%bf%e6%b2%bb/",
            "https://n9.chinapress.com.my/category/%e7%a4%be%e4%bc%9a/",
            "https://n9.chinapress.com.my/category/%e7%a4%be%e5%9b%a2/",
            "https://n9.chinapress.com.my/%e6%9c%80%e7%83%ad%e6%96%b0%e9%97%bb/",
        ],
        "keywords": None,
    },
    {
        "id": "CP_MY",
        "name": "China Press (全国 — filter 森美兰)",
        "method": "chinapress",
        "base_url": "https://www.chinapress.com.my",
        "community": "cina",
        "lang": "cina",
        "comments": True,
        "listing_urls": [
            "https://www.chinapress.com.my/category/%e6%94%bf%e6%b2%bb/",
            "https://www.chinapress.com.my/category/%e7%a4%be%e4%bc%9a/",
        ],
        "keywords": [
            "森美兰", "森州", "芙蓉", "马口", "州选", "州选举", "PRN", "Negeri Sembilan", "Seremban",
        ],
    },
    {
        "id": "FMT",
        "name": "Free Malaysia Today",
        "method": "wordpress_rss",
        "feed_url": "https://www.freemalaysiatoday.com/feed/",
        "community": "melayu",
        "lang": "bm",
        "comments": True,
        "keywords": [
            "Negeri Sembilan", "Sembilan", "Seremban", "PRN", "Nilai", "Port Dickson", "Bahau",
        ],
    },
    {
        "id": "MKINI",
        "name": "Malaysiakini",
        "method": "publisher_rss",
        "feed_url": "https://www.malaysiakini.com/rss/en/news.rss",
        "community": "melayu",
        "lang": "bm",
        "comments": False,
        "keywords": [
            "Negeri Sembilan", "Sembilan", "Seremban", "PRN", "YOURSAY",
        ],
    },
    {
        "id": "BH",
        "name": "Berita Harian",
        "method": "publisher_rss",
        "feed_url": "https://www.bharian.com.my/feed",
        "community": "melayu",
        "lang": "bm",
        "comments": False,
        "keywords": [
            "Negeri Sembilan", "Sembilan", "Seremban", "PRN", "Nilai", "Port Dickson",
        ],
    },
    {
        "id": "HMETRO",
        "name": "Harian Metro",
        "method": "publisher_rss",
        "feed_url": "https://www.hmetro.com.my/feed",
        "community": "melayu",
        "lang": "bm",
        "comments": False,
        "keywords": [
            "Negeri Sembilan", "Sembilan", "Seremban", "PRN",
        ],
    },
    {
        "id": "UTUSAN",
        "name": "Utusan Malaysia",
        "method": "publisher_rss",
        "feed_url": "https://www.utusan.com.my/feed/",
        "community": "melayu",
        "lang": "bm",
        "comments": False,
        "keywords": [
            "Negeri Sembilan", "Sembilan", "Seremban", "PRN",
        ],
    },
    {
        "id": "SINCHEW",
        "name": "Sin Chew Daily 星洲日报",
        "method": "sinchew",
        "base_url": "https://www.sinchew.com.my",
        "community": "cina",
        "lang": "cina",
        "comments": False,
        "listing_urls": [
            "https://www.sinchew.com.my/tag/森美兰/",
            "https://www.sinchew.com.my/?s=州选",
            "https://www.sinchew.com.my/?s=PRN",
        ],
        "keywords": [
            "森美兰", "森州", "芙蓉", "州选", "州选举", "PRN", "Negeri Sembilan", "Seremban",
        ],
    },
    {
        "id": "ORIENTAL",
        "name": "Oriental Daily 东方日报",
        "method": "publisher_rss",
        "feed_url": "https://www.orientaldaily.com.my/feeds/rss",
        "community": "cina",
        "lang": "cina",
        "comments": False,
        "keywords": [
            "森美兰", "森州", "芙蓉", "州选", "州选举", "PRN", "Negeri Sembilan", "Seremban",
        ],
    },
    # ── Tamil / Indian community media ─────────────────────────────────────
    {
        "id": "MAKKAL_OSAI",
        "name": "Makkal Osai — N9 & PRN (Tamil RSS)",
        "method": "wordpress_rss",
        "feed_url": "https://makkalosai.com.my/feed/",
        "community": "india",
        "lang": "tamil",
        "comments": False,
        "keywords": [
            "Negeri Sembilan", "Seremban", "Nilai", "Bahau", "Port Dickson", "Tampin",
            "Kuala Pilah", "Jempol", "Rembau", "Jelebu", "Melaka", "Johor", "PRN",
            "MIC", "Indian", "pengundi India", "komuniti India", "Hindu", "Tamil",
            "செராம்பன்", "நெகிரி", "森美兰", "芙蓉", "州选",
        ],
    },
    {
        "id": "MAKKAL_OSAI_HEADLINES",
        "name": "Makkal Osai — headline Tamil feed",
        "method": "tamil_rss",
        "feed_url": "https://makkalosai.com.my/feed/",
        "community": "india",
        "lang": "tamil",
        "comments": False,
        "keywords": None,
        "require_tamil_script": True,
    },
]

COMMENT_CAPABLE = [s["id"] for s in DIRECT_NEWS_SOURCES if s.get("comments")]
