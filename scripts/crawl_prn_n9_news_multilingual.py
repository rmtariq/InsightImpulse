#!/usr/bin/env python3
"""Crawl PRN N9 news — Google News RSS + direct scrape (percuma, tiada API key)."""
from __future__ import annotations

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import urlparse

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(ROOT))

from prn_n9_direct_news_sources import COMMENT_CAPABLE, DIRECT_NEWS_SOURCES
from prn_n9_news_queries import COMMUNITY_LABELS, QUERY_PACK, all_queries

from prn_paths import crawls, reference, ensure_state_dirs  # noqa: E402

ensure_state_dirs("N9")
CRAWL_DIR = crawls("N9", "news")
SUMMARY_JSON = reference("N9") / "prn_n9_news_multilingual_summary.json"
NEWS_JSON = reference("N9") / "prn_n9_news_summary.json"


def _domain(url: str) -> str:
    try:
        host = urlparse(str(url or "")).netloc.lower().replace("www.", "")
        return host or "unknown"
    except Exception:
        return "unknown"


def _classify_publisher(domain: str, text: str) -> str:
    d = domain.lower()
    t = text.lower()
    if any(x in d for x in ("chinapress", "sinchew", "oriental", "nanyang", "kwongwah", "guangming")):
        return "cina"
    if any(x in d for x in ("nanban", "makkalosai", "vanakkam")):
        return "india"
    if any(x in d for x in ("theedgemalaysia", "edgeprop")):
        return "ekonomi"
    if "harakah" in d or "harakah" in t:
        return "islam"
    if any(x in d for x in ("utusan", "bharian", "sinarharian", "bernama", "astroawani", "hmetro")):
        return "melayu"
    return ""


async def crawl_google_news(items: List[dict], max_per: int = 50) -> List[Dict[str, Any]]:
    from backend.data_crawlers.scrapling_adapter import ScraplingAdapter

    adapter = ScraplingAdapter()
    seen: set = set()
    rows: List[Dict[str, Any]] = []
    for item in items:
        comm = item.get("community", "umum")
        label = COMMUNITY_LABELS.get(comm, comm)
        print(f"📰 [{item['id']}] {label}: {item['query'][:70]}...")
        batch = await adapter._crawl_news(item["query"], max_results=max_per, decode_urls=False)
        if str(item.get("id", "")).startswith("ED"):
            batch = [
                r for r in batch
                if "theedgemalaysia" in _domain(r.get("URL", ""))
                or "edgeprop" in _domain(r.get("URL", ""))
                or "the edge" in str(r.get("Text", "")).lower()
            ]
        added = 0
        for r in batch:
            rid = r.get("ID") or r.get("URL")
            if rid in seen:
                continue
            seen.add(rid)
            domain = _domain(r.get("URL", ""))
            pub_guess = _classify_publisher(domain, str(r.get("Text", "")))
            rows.append({
                **r,
                "QueryID": item["id"],
                "Lang": item["lang"],
                "Community": comm,
                "CommunityLabel": label,
                "PublisherDomain": domain,
                "PublisherGuess": pub_guess or comm,
                "SeedQuery": item["query"],
                "CrawlMethod": "google_news_rss",
            })
            added += 1
        print(f"   → +{added} (total {len(rows)})")
    return rows


def crawl_direct(max_articles: int = 30, max_comments: int = 12) -> List[Dict[str, Any]]:
    from backend.data_crawlers.direct_news_scraper import DirectNewsScraper

    print(f"\n🔗 Direct scrape ({len(DIRECT_NEWS_SOURCES)} sumber, komen: {', '.join(COMMENT_CAPABLE)})...")
    scraper = DirectNewsScraper()
    raw = scraper.crawl_sources(
        DIRECT_NEWS_SOURCES,
        max_articles_per_source=max_articles,
        max_comments_per_article=max_comments,
    )
    rows: List[Dict[str, Any]] = []
    for r in raw:
        src = next((s for s in DIRECT_NEWS_SOURCES if s["id"] == r.get("SourceID")), {})
        comm = src.get("community", "umum")
        domain = _domain(r.get("URL", ""))
        pub_guess = _classify_publisher(domain, str(r.get("Text", "")))
        rows.append({
            **r,
            "QueryID": r.get("SourceID", "DIRECT"),
            "Lang": src.get("lang", "bm"),
            "Community": comm,
            "CommunityLabel": COMMUNITY_LABELS.get(comm, comm),
            "PublisherDomain": domain,
            "PublisherGuess": pub_guess or comm,
            "SeedQuery": f"direct:{r.get('SourceID', '')}",
            "CrawlMethod": "direct_scrape",
        })
    posts = sum(1 for r in rows if r.get("Type") == "post")
    comments = sum(1 for r in rows if r.get("Type") == "comment")
    print(f"   📊 Direct total: {len(rows)} ({posts} artikel, {comments} komen)")
    return rows


def _top_headlines(df: pd.DataFrame, community: str, limit: int = 5) -> List[dict]:
    if df.empty or "Community" not in df.columns:
        return []
    sub = df[df["Community"] == community]
    if "Type" in df.columns:
        sub = sub[sub["Type"] == "post"]
    out = []
    for _, row in sub.head(limit).iterrows():
        out.append({
            "text": str(row.get("Text", ""))[:220],
            "url": str(row.get("URL", "")),
            "community": community,
            "domain": str(row.get("PublisherDomain", "")),
            "date": str(row.get("Date", "")),
            "method": str(row.get("CrawlMethod", "")),
        })
    return out


def save(rows: List[Dict[str, Any]]) -> Path:
    CRAWL_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = CRAWL_DIR / f"PRN_N9_News_Multilingual_{ts}.csv"
    df = pd.DataFrame(rows)
    if df.empty:
        df = pd.DataFrame(columns=["Platform", "Text", "URL", "Lang", "Community", "Type"])
    df.to_csv(path, index=False, encoding="utf-8-sig")

    posts_df = df[df["Type"] == "post"] if "Type" in df.columns else df
    comments_df = df[df["Type"] == "comment"] if "Type" in df.columns else pd.DataFrame()

    by_lang = df.groupby("Lang").size().to_dict() if "Lang" in df.columns and not df.empty else {}
    by_community = posts_df.groupby("Community").size().to_dict() if "Community" in posts_df.columns and not posts_df.empty else {}
    by_method = df.groupby("CrawlMethod").size().to_dict() if "CrawlMethod" in df.columns and not df.empty else {}
    by_domain = (
        posts_df["PublisherDomain"].value_counts().head(20).to_dict()
        if "PublisherDomain" in posts_df.columns and not posts_df.empty
        else {}
    )

    community_headlines = {
        comm: _top_headlines(posts_df, comm, 5) for comm in QUERY_PACK.keys() if comm in by_community
    }

    fetched = datetime.now().isoformat(timespec="seconds")
    summary = {
        "fetched_at": fetched,
        "csv_file": str(path.relative_to(ROOT)),
        "total": len(posts_df),
        "total_articles": len(posts_df),
        "total_comments": len(comments_df),
        "by_lang": by_lang,
        "by_community": by_community,
        "by_crawl_method": by_method,
        "community_labels": COMMUNITY_LABELS,
        "top_domains": by_domain,
        "top_headlines": (
            _top_headlines(posts_df, "umum", 8)
            + _top_headlines(posts_df, "cina", 5)
            + _top_headlines(posts_df, "melayu", 5)
        ),
        "community_headlines": community_headlines,
        "queries_used": len(all_queries()),
        "direct_sources": [s["id"] for s in DIRECT_NEWS_SOURCES],
        "comment_sources": COMMENT_CAPABLE,
        "cost": "RM0 — Google News RSS + direct scrape (tiada API key)",
        "note": (
            "Komen percuma: China Press (Coral API), FMT (WordPress RSS). "
            "BH/HMetro/Utusan/Malaysiakini = artikel RSS. FB 森州人 perlu Apify."
        ),
    }
    SUMMARY_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    NEWS_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n💾 {path} ({len(posts_df)} artikel + {len(comments_df)} komen)")
    print(f"   Komuniti: {by_community}")
    print(f"   Kaedah: {by_method}")
    return path


def _dedupe_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen: set = set()
    out: List[Dict[str, Any]] = []
    for r in rows:
        key = r.get("ID") or r.get("URL")
        if key in seen:
            continue
        seen.add(key)
        out.append(r)
    return out


async def main_async() -> int:
    gnews = await crawl_google_news(all_queries())
    direct = crawl_direct()
    rows = _dedupe_rows(gnews + direct)
    save(rows)
    return 0


def main() -> int:
    return asyncio.run(main_async())


if __name__ == "__main__":
    raise SystemExit(main())
