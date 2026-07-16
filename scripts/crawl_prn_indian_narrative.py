#!/usr/bin/env python3
"""Crawl PRN Indian/Tamil narrative — Google News + Tamil RSS (percuma)."""
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

from prn_indian_direct_sources import INDIAN_DIRECT_SOURCES
from prn_indian_news_queries import COMMUNITY_LABELS, all_queries
from prn_paths import crawls, ensure_state_dirs, reference  # noqa: E402

ensure_state_dirs("N9")
ensure_state_dirs("Johor")
ensure_state_dirs("Melaka")
CRAWL_DIR = crawls("N9", "indian_narrative")
CRAWL_DIR_JOHOR = crawls("Johor", "indian_narrative")
CRAWL_DIR_MELAKA = crawls("Melaka", "indian_narrative")
SUMMARY_JSON = reference("N9") / "prn_indian_narrative_summary.json"
SUMMARY_JOHOR = reference("Johor") / "prn_indian_narrative_summary.json"

INDIA_DOMAINS = (
    "makkalosai", "nanban", "malaysiannanban", "varnam", "vanakkam",
    "tamilmalar", "astroulagam", "bernama.com/tam", "mitra.gov",
)


def _domain(url: str) -> str:
    try:
        return urlparse(str(url or "")).netloc.lower().replace("www.", "") or "unknown"
    except Exception:
        return "unknown"


def _classify_publisher(domain: str, text: str) -> str:
    d = domain.lower()
    if any(x in d for x in INDIA_DOMAINS):
        return "india"
    t = text.lower()
    if any(x in t for x in ("makkal osai", "nanban", "tamil", "mic ", "hindu", "sjkt")):
        return "india"
    return "india"


async def crawl_google_news(items: List[dict], max_per: int = 40) -> List[Dict[str, Any]]:
    from backend.data_crawlers.scrapling_adapter import ScraplingAdapter

    adapter = ScraplingAdapter()
    seen: set = set()
    rows: List[Dict[str, Any]] = []
    for item in items:
        label = COMMUNITY_LABELS.get(item.get("community", "india"), "India")
        print(f"📰 [{item['id']}] {label}: {item['query'][:72]}...")
        batch = await adapter._crawl_news(item["query"], max_results=max_per, decode_urls=False)
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
                "Community": "india",
                "CommunityLabel": label,
                "PublisherDomain": domain,
                "PublisherGuess": pub_guess,
                "SeedQuery": item["query"],
                "CrawlMethod": "google_news_rss",
                "CrawlPipeline": "indian_narrative",
            })
            added += 1
        print(f"   → +{added} (total {len(rows)})")
    return rows


def crawl_direct(max_articles: int = 45) -> List[Dict[str, Any]]:
    from backend.data_crawlers.direct_news_scraper import DirectNewsScraper

    print(f"\n🔗 Tamil direct RSS ({len(INDIAN_DIRECT_SOURCES)} sumber)...")
    scraper = DirectNewsScraper()
    raw = scraper.crawl_sources(
        INDIAN_DIRECT_SOURCES,
        max_articles_per_source=max_articles,
        max_comments_per_article=0,
    )
    rows: List[Dict[str, Any]] = []
    for r in raw:
        src = next((s for s in INDIAN_DIRECT_SOURCES if s["id"] == r.get("SourceID")), {})
        domain = _domain(r.get("URL", ""))
        pub_guess = _classify_publisher(domain, str(r.get("Text", "")))
        rows.append({
            **r,
            "QueryID": r.get("SourceID", "DIRECT"),
            "Lang": src.get("lang", "tamil"),
            "Community": "india",
            "CommunityLabel": COMMUNITY_LABELS["india"],
            "PublisherDomain": domain,
            "PublisherGuess": pub_guess,
            "SeedQuery": f"direct:{r.get('SourceID', '')}",
            "CrawlMethod": "direct_scrape",
            "CrawlPipeline": "indian_narrative",
            "Jenis_Suara": r.get("Jenis_Suara") or "media_india",
        })
    posts = sum(1 for r in rows if r.get("Type") == "post")
    print(f"   📊 Direct total: {len(rows)} ({posts} artikel)")
    return rows


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


def _state_from_row(row: Dict[str, Any]) -> str:
    seed = str(row.get("SeedQuery") or row.get("seed_query") or "").lower()
    text = str(row.get("Text") or row.get("post_text") or "").lower()
    blob = f"{seed} {text}"
    if "johor" in blob or "柔佛" in blob or "johor bahru" in blob or "kluang" in blob:
        return "Johor"
    if "melaka" in blob or "马六甲" in blob:
        return "Melaka"
    if "negeri sembilan" in blob or "sembilan" in blob or "seremban" in blob:
        return "Negeri Sembilan"
    return "Negeri Sembilan"


def save(rows: List[Dict[str, Any]]) -> Path:
    CRAWL_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = CRAWL_DIR / f"PRN_Indian_Narrative_{ts}.csv"
    df = pd.DataFrame(rows)
    if df.empty:
        df = pd.DataFrame(columns=["Platform", "Text", "URL", "Lang", "Community", "Type"])
    df.to_csv(path, index=False, encoding="utf-8-sig")

    posts_df = df[df["Type"] == "post"] if "Type" in df.columns else df
    by_method = df.groupby("CrawlMethod").size().to_dict() if "CrawlMethod" in df.columns and not df.empty else {}
    by_domain = (
        posts_df["PublisherDomain"].value_counts().head(15).to_dict()
        if "PublisherDomain" in posts_df.columns and not posts_df.empty
        else {}
    )
    summary = {
        "fetched_at": datetime.now().isoformat(timespec="seconds"),
        "csv_file": str(path.relative_to(ROOT)),
        "total_articles": len(posts_df),
        "by_crawl_method": by_method,
        "top_domains": by_domain,
        "queries_used": len(all_queries()),
        "direct_sources": [s["id"] for s in INDIAN_DIRECT_SOURCES],
        "cost": "RM0 — Google News RSS + Tamil RSS (tiada API key)",
    }
    SUMMARY_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n💾 {path} ({len(posts_df)} artikel)")
    print(f"   Kaedah: {by_method}")
    print(f"   Domain: {list(by_domain.keys())[:8]}")

    for state_key, out_dir, sum_path in (
        ("Johor", CRAWL_DIR_JOHOR, SUMMARY_JOHOR),
        ("Melaka", CRAWL_DIR_MELAKA, reference("Melaka") / "prn_indian_narrative_summary.json"),
    ):
        out_dir.mkdir(parents=True, exist_ok=True)
        sub_rows = [r for r in rows if _state_from_row(r) == state_key]
        if not sub_rows:
            continue
        sub_path = out_dir / f"PRN_Indian_Narrative_{state_key}_{ts}.csv"
        pd.DataFrame(sub_rows).to_csv(sub_path, index=False, encoding="utf-8-sig")
        sub_posts = [r for r in sub_rows if str(r.get("Type", "post")).lower() == "post"]
        sum_path.parent.mkdir(parents=True, exist_ok=True)
        sum_path.write_text(
            json.dumps(
                {
                    **summary,
                    "state_focus": state_key,
                    "csv_file": str(sub_path.relative_to(ROOT)),
                    "total_articles": len(sub_posts),
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        print(f"   ↳ {state_key}: {sub_path.name} ({len(sub_posts)} artikel)")

    return path


async def main_async(negeri: str = "negeri sembilan") -> int:
    from prn_indian_seeds_loader import STATES_FOCUS, STATES_N9_ONLY, generate_google_queries

    negeri_l = (negeri or "negeri sembilan").strip().lower()
    if negeri_l in ("all", "semua", "3negeri"):
        states = STATES_FOCUS
        label = "3 negeri"
    elif negeri_l in ("johor",):
        states = ("Johor",)
        label = "Johor"
    elif negeri_l in ("melaka",):
        states = ("Melaka",)
        label = "Melaka"
    else:
        states = STATES_N9_ONLY
        label = "Negeri Sembilan"

    queries = generate_google_queries(states=states)
    print(f"🎯 Indian narrative crawl · {label} — {len(queries)} Google queries + {len(INDIAN_DIRECT_SOURCES)} RSS")
    gnews = await crawl_google_news(queries)
    direct = crawl_direct()
    rows = _dedupe_rows(gnews + direct)
    # Keep only rows matching focus when N9-only
    if states == STATES_N9_ONLY:
        rows = [r for r in rows if _state_from_row(r) == "Negeri Sembilan"]
        print(f"   Filter N9: {len(rows)} rows kekal")
    save(rows)
    return 0


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Crawl Indian/Tamil narrative (default: N9 only)")
    parser.add_argument(
        "--negeri",
        default="negeri sembilan",
        help="negeri sembilan | johor | melaka | all",
    )
    args = parser.parse_args()
    return asyncio.run(main_async(args.negeri))


if __name__ == "__main__":
    raise SystemExit(main())
