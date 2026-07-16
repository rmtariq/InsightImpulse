"""
Scrapling Adapter for InsightPulse
===================================

Free/low-cost crawling engine using Scrapling (https://scrapling.readthedocs.io)
for platforms where Apify is overkill or too expensive.

Coverage strategy (hybrid with SimpleApifyAdapter):
  - PRIMARY (replace Apify/SerpAPI):
      news  → Google News RSS (FREE, boolean search, 1000+ sources)
      google, youtube (metadata via yt-dlp), lazada, shopee  [future phases]
  - FALLBACK (used when Apify quota exceeded):
      tiktok (public hashtag pages)
  - NOT COVERED (auth-walled, keep Apify):
      facebook, instagram, twitter/x, linkedin

Output schema is 100% identical to all other platforms for downstream
sentiment/emotion analysis and combined CSV:
    Platform, Type, ID, Text, URL, Sentiment, Date,
    likes, shares, comments_count, views,
    sentiment_score, total_engagement

Author: InsightPulse Team
Date: 2026-05-16
"""

import os
import re
import asyncio
import hashlib
import logging
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from email.utils import parsedate_to_datetime
from urllib.parse import urlparse, parse_qs, unquote

import requests
import pandas as pd

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Optional heavy imports (loaded lazily so backend still starts if missing)
# ---------------------------------------------------------------------------
try:
    from scrapling.fetchers import Fetcher, StealthyFetcher
    SCRAPLING_AVAILABLE = True
    logger.info("✅ Scrapling fetchers loaded")
except ImportError as e:
    SCRAPLING_AVAILABLE = False
    logger.warning(f"⚠️ Scrapling not available: {e}")

try:
    import yt_dlp
    YT_DLP_AVAILABLE = True
    logger.info("✅ yt-dlp loaded")
except ImportError as e:
    YT_DLP_AVAILABLE = False
    logger.warning(f"⚠️ yt-dlp not available: {e}")


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Platforms this adapter handles
SUPPORTED_PLATFORMS = {
    "news",       # Phase 1 ✅  Google News RSS — FREE, boolean/phrase/site filters
    "google",     # Phase 2 🔜  StealthyFetcher on google.com/search
    "youtube",    # Phase 3 🔜  yt-dlp + Scrapling
    "lazada",     # Phase 4 🔜  StealthyFetcher with solve_cloudflare
    "shopee",     # Phase 5 🔜  StealthyFetcher with proxy rotation
    "tiktok",     # Phase 6 🔜  Public hashtag/profile pages (fallback only)
}

# Google News RSS base — Malaysian context, mixed EN+BM coverage
_GNEWS_RSS_BASE = "https://news.google.com/rss/search"
_GNEWS_PARAMS   = {"hl": "en-MY", "gl": "MY", "ceid": "MY:en"}

# Timeout for plain HTTP fetches (seconds)
_HTTP_TIMEOUT = 20

# Max articles per RSS call (Google caps at ~100 per query)
_GNEWS_MAX_PER_CALL = 100

# ---------------------------------------------------------------------------
# Malaysian newspaper RSS feeds (supplementary to Google News)
# These are *publisher feeds* — they do NOT support keyword search, so we
# fetch the latest items and filter client-side by keyword match.
#
# Only LIVE feeds (probed 2026-05-16). The Star, NST, The Edge, theSundaily,
# Guang Ming, See Hua, Nanyang, Sin Chew and other Chinese papers have all
# retired their public RSS feeds — coverage for those titles still comes
# from Google News RSS (which aggregates them).
# ---------------------------------------------------------------------------
MALAYSIAN_RSS_FEEDS: List[Dict[str, str]] = [
    # English ----------------------------------------------------------------
    {"name": "Malay Mail",          "lang": "en", "category": "general",  "url": "https://www.malaymail.com/feed/rss/malaysia"},
    {"name": "Borneo Post",         "lang": "en", "category": "regional", "url": "https://www.theborneopost.com/feed/"},
    {"name": "Malaysiakini",        "lang": "en", "category": "general",  "url": "https://www.malaysiakini.com/rss/en/news.rss"},
    {"name": "Free Malaysia Today", "lang": "en", "category": "general",  "url": "https://www.freemalaysiatoday.com/feed/"},
    {"name": "Malaysian Reserve",   "lang": "en", "category": "business", "url": "https://www.themalaysianreserve.com/feed/"},
    # Bahasa Melayu ----------------------------------------------------------
    {"name": "Berita Harian",       "lang": "ms", "category": "general",  "url": "https://www.bharian.com.my/feed"},
    {"name": "Harian Metro",        "lang": "ms", "category": "general",  "url": "https://www.hmetro.com.my/feed"},
    {"name": "Utusan Online",       "lang": "ms", "category": "general",  "url": "https://www.utusan.com.my/feed/"},
]


# ===========================================================================
# Main Adapter Class
# ===========================================================================

class ScraplingAdapter:
    """
    Scrapling-based crawler that mirrors SimpleApifyAdapter's public contract
    so it can be swapped in by crawl_strategy without any downstream changes.

    DATA SCHEMA (identical to every other platform in InsightPulse):
    ┌────────────────────┬─────────────────────────────────────────────────┐
    │ Column             │ News-specific meaning                           │
    ├────────────────────┼─────────────────────────────────────────────────┤
    │ Platform           │ "news"                                          │
    │ Type               │ "post"  (articles don't have reply threads)     │
    │ ID                 │ MD5 of the real article URL (unique & stable)   │
    │ Text               │ Headline + ". " + excerpt/snippet               │
    │                    │ → gives sentiment model rich signal             │
    │ URL                │ Real article URL (Google redirect decoded)      │
    │ Sentiment          │ "" — filled by downstream sentiment pipeline    │
    │ Date               │ Article publish date (ISO-8601)                 │
    │ likes              │ 0 — N/A for news articles                       │
    │ shares             │ 0 — N/A                                         │
    │ comments_count     │ 0 — N/A (comments live on the news site itself) │
    │ views              │ 0 — N/A                                         │
    │ sentiment_score    │ 0.0 — filled by sentiment pipeline              │
    │ total_engagement   │ 0 — N/A                                         │
    └────────────────────┴─────────────────────────────────────────────────┘

    WHY Text = Headline + Snippet?
      • Headline alone is too short for accurate sentiment detection.
      • Full article body takes 2–5 s per article (rate-limit risk).
      • Headline + snippet gives ~150–300 chars — ideal for models like
        multilingual-sentiment-latest used by InsightPulse.
    """

    def __init__(self, apify_fallback: Optional[Any] = None):
        """
        Args:
            apify_fallback: Optional SimpleApifyAdapter instance used as
                            last-resort fallback when Scrapling fails.
        """
        self.data_dir = Path("data/smart_crawlers")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.apify_fallback = apify_fallback
        self.proxy_url = os.getenv("SCRAPLING_PROXY_URL") or os.getenv("APIFY_PROXY_URL")

        logger.info("✅ Scrapling Adapter initialized")
        logger.info(f"   Scrapling available : {SCRAPLING_AVAILABLE}")
        logger.info(f"   yt-dlp available    : {YT_DLP_AVAILABLE}")
        logger.info(f"   Proxy configured    : {'✓' if self.proxy_url else '✗ (direct IP)'}")
        logger.info(f"   Apify fallback      : {'✓' if apify_fallback else '✗'}")

    # -----------------------------------------------------------------------
    # Public contract — identical signature to SimpleApifyAdapter.crawl_platform
    # -----------------------------------------------------------------------
    async def crawl_platform(
        self,
        platform: str,
        query: str,
        max_results: int = 100,
        max_comments: int = 50,
        comment_sampling: str = "smart",
        use_ai_keywords: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Route to the per-platform implementation.
        Returns a flat list of records matching the standard 13-column schema.
        """
        platform = (platform or "").lower()

        if platform not in SUPPORTED_PLATFORMS:
            logger.warning(f"⚠️ Scrapling does not handle '{platform}' — use Apify adapter")
            return []

        # ── Phase 1: News ──────────────────────────────────────────────────
        if platform == "news":
            return await self._crawl_news(query, max_results)

        # ── Future phases ──────────────────────────────────────────────────
        logger.warning(f"⚠️ Scrapling handler for '{platform}' not yet implemented")
        return []

    # =======================================================================
    # PHASE 1 — News  (Google News RSS)
    # =======================================================================

    async def _crawl_news(
        self,
        query: str,
        max_results: int = 100,
        decode_urls: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Crawl news articles using Google News RSS.

        Supports the FULL set of Google News boolean operators — users can
        pass the query string exactly as they would type it in Google:

          Phrase match   : "pilihan raya negeri"
          OR             : PRU15 OR "pilihan raya umum"
          AND (default)  : Anwar Ibrahim ekonomi
          Exclude        : Najib -1MDB
          Title filter   : intitle:rasuah
          Site filter    : site:thestar.com.my banjir
          Multi-site     : (site:thestar.com.my OR site:nst.com.my) banjir
          Time (relative): inflasi when:7d
          Time (absolute): bantuan after:2026-01-01 before:2026-03-31

        Data returned per article:
          Text  = Headline + ". " + Snippet  (rich enough for sentiment)
          URL   = decoded real article URL   (not Google redirect)
          Date  = RFC-2822 pubDate → ISO-8601
          ID    = MD5(URL)                   (stable, dedup-safe)
          likes / shares / views = 0        (N/A for news)
        """
        logger.info(f"📰 [news] Google News RSS query: '{query}' (max {max_results})")

        records: List[Dict[str, Any]] = []

        # ── Step 1: Initial fetch (Standard) ───────────────────────────
        # Google News RSS caps each call at ~100.
        # For larger requests, we use a multi-stage time-window strategy.
        time_windows = ["", "when:7d", "when:30d", "when:1y"]
        if "when:" in query or "after:" in query or "before:" in query:
            time_windows = [""] # Don't override user's time filters

        seen_ids: set = set()
        raw_records = []

        for window in time_windows:
            if len(seen_ids) >= max_results:
                break

            current_query = f"{query} {window}".strip()
            fetch_count = min(max_results - len(seen_ids) + 20, 100)

            logger.info(f"📰 [news] Fetching window '{window}' for query: '{query}'")
            try:
                items = await asyncio.get_event_loop().run_in_executor(
                    None, self._fetch_gnews_rss, current_query, fetch_count
                )

                # Parse metadata
                for item in items:
                    rec = self._parse_gnews_item_fast(item)
                    if rec and rec["ID"] not in seen_ids:
                        seen_ids.add(rec["ID"])
                        raw_records.append(rec)

                if not window: # If first pass got nothing, don't bother with windows
                    if not items: break
            except Exception as exc:
                logger.error(f"❌ [news] RSS fetch failed for window {window}: {exc}")
                continue

        # ── Optionally decode Google redirect URLs concurrently ──────────
        # decode_urls=False (default): Google redirect URLs are kept as-is.
        #   • Clickable links still work (Google redirects to real page).
        #   • No extra HTTP calls → fast crawl (ideal for sentiment analysis).
        # decode_urls=True: follow each redirect to get the real publisher URL.
        #   • ~1–2 s overhead per unique domain (concurrent, not sequential).
        if decode_urls:
            loop = asyncio.get_event_loop()

            async def decode_one(url: str) -> str:
                if "news.google.com" not in url:
                    return url
                return await loop.run_in_executor(None, self._decode_google_url, url)

            raw_urls = [r["URL"] for r in raw_records]
            decoded_urls = await asyncio.gather(*[decode_one(u) for u in raw_urls])
        else:
            decoded_urls = [r["URL"] for r in raw_records]

        # ── Assemble final records ───────────────────────────────────────
        seen_ids: set = set()
        for rec, real_url in zip(raw_records, decoded_urls):
            rec["URL"] = real_url
            rec["ID"] = hashlib.md5(real_url.encode()).hexdigest()[:16]
            if rec["ID"] not in seen_ids:
                seen_ids.add(rec["ID"])
                records.append(rec)
            if len(records) >= max_results:
                break

        logger.info(f"✅ [news] Google News RSS: {len(records)} articles for '{query}'")

        # ── Step 2: Supplement with Malaysian publisher RSS feeds ────────
        if len(records) < max_results:
            msia_records = await self._crawl_malaysian_feeds(
                query=query,
                max_results=max_results - len(records),
                existing_ids=seen_ids,
            )
            records.extend(msia_records)
            logger.info(
                f"✅ [news] Total after Malaysian feeds: {len(records)} "
                f"(+{len(msia_records)} from MY publishers)"
            )

        return records[:max_results]

    # -----------------------------------------------------------------------
    # Google News RSS helpers
    # -----------------------------------------------------------------------

    def _fetch_gnews_rss(self, query: str, max_results: int) -> list:
        """
        Synchronous RSS fetch — called via run_in_executor so it doesn't
        block the event loop.

        Returns a list of <item> ElementTree elements.
        """
        from urllib.parse import urlencode

        params = dict(_GNEWS_PARAMS)
        params["q"] = query

        url = f"{_GNEWS_RSS_BASE}?{urlencode(params)}"
        logger.info(f"   RSS URL: {url}")

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept": "application/rss+xml, application/xml, text/xml, */*",
            "Accept-Language": "en-MY,en;q=0.9,ms;q=0.8",
        }

        resp = requests.get(url, headers=headers, timeout=_HTTP_TIMEOUT)
        resp.raise_for_status()

        # Parse RSS XML
        root = ET.fromstring(resp.content)
        ns = {"media": "http://search.yahoo.com/mrss/"}

        channel = root.find("channel")
        if channel is None:
            logger.warning("⚠️ [news] RSS response has no <channel> element")
            return []

        items = channel.findall("item")
        logger.info(f"   Raw RSS items returned: {len(items)}")
        return items[:max_results]

    def _parse_gnews_item_fast(self, item) -> Optional[Dict[str, Any]]:
        """
        Fast parse of one RSS <item> — NO HTTP calls.
        URL is kept as Google redirect; real URL is decoded concurrently
        in _crawl_news() after all items are parsed.

        RSS fields used:
          <title>       — headline (strips trailing " - Publisher")
          <link>        — Google redirect URL (decoded later)
          <pubDate>     — RFC-2822 date → ISO-8601
          <source>      — publisher name (e.g. "The Star")
          <description> — HTML snippet → stripped to plain text
        """
        def get_text(tag: str) -> str:
            el = item.find(tag)
            return (el.text or "").strip() if el is not None else ""

        # ── Headline ────────────────────────────────────────────────────────
        raw_title = get_text("title")
        # Google appends " - Publisher Name" to titles; strip it
        title = re.sub(r'\s+-\s+[^-]+$', '', raw_title).strip() or raw_title

        # ── Raw URL (Google redirect — decoded later concurrently) ──────────
        raw_link = get_text("link")
        if not raw_link:
            return None

        # ── Publisher / source ──────────────────────────────────────────────
        source_el = item.find("source")
        publisher = (source_el.text or "").strip() if source_el is not None else ""

        # ── Snippet / description ────────────────────────────────────────────
        raw_desc = get_text("description")
        snippet = re.sub(r'<[^>]+>', '', raw_desc).strip()
        if not snippet and publisher:
            snippet = f"[{publisher}]"

        # ── Compose Text ─────────────────────────────────────────────────────
        # "Headline. Snippet" gives sentiment model ~150–300 chars
        text = f"{title}. {snippet}" if (snippet and snippet not in title) else title

        # ── Date → ISO-8601 ─────────────────────────────────────────────────
        date_iso = self._parse_rss_date(get_text("pubDate"))

        # ID is a placeholder — will be replaced with MD5(real_url) in caller
        return {
            "Platform":         "news",
            "Type":             "post",
            "ID":               hashlib.md5(raw_link.encode()).hexdigest()[:16],
            "Text":             text,
            "URL":              raw_link,   # Google redirect — decoded later
            "Sentiment":        "",
            "Date":             date_iso,
            "likes":            0,
            "shares":           0,
            "comments_count":   0,
            "views":            0,
            "sentiment_score":  0.0,
            "total_engagement": 0,
        }

    @staticmethod
    def _decode_google_url(google_url: str) -> str:
        """
        Decode a Google News redirect URL to the real article URL.

        Google News uses two redirect formats:
          1. https://news.google.com/rss/articles/...?oc=5
             → follow redirect to get Location header
          2. https://news.google.com/articles/...
             → same redirect mechanism

        For speed (no extra HTTP call), we try to extract `url` param first;
        fall back to following the redirect with a HEAD request.
        """
        if not google_url:
            return ""

        # Already a real URL (not a Google redirect)
        if "news.google.com" not in google_url:
            return google_url

        # Try to extract `url` query param (older format)
        parsed = urlparse(google_url)
        qs = parse_qs(parsed.query)
        if "url" in qs:
            return unquote(qs["url"][0])

        # Follow the redirect chain (GET with stream=True — no body download)
        # Google News /rss/articles/... redirects to the publisher's real URL.
        try:
            resp = requests.get(
                google_url,
                allow_redirects=True,
                timeout=10,
                stream=True,          # don't download body
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/124.0.0.0 Safari/537.36"
                    )
                },
            )
            resp.close()
            final = resp.url
            # Sanity check — must not still be google.com
            if "news.google.com" not in final:
                return final
        except Exception:
            pass

        # Last resort: return the Google redirect URL as-is (still clickable)
        return google_url

    @staticmethod
    def _parse_rss_date(pub_date_str: str) -> str:
        """
        Convert RFC-2822 pubDate (e.g. 'Fri, 16 May 2026 08:30:00 GMT')
        to ISO-8601 (e.g. '2026-05-16T08:30:00+00:00').
        Falls back to today's ISO timestamp on parse failure.
        """
        if not pub_date_str:
            return datetime.now().isoformat()
        try:
            dt = parsedate_to_datetime(pub_date_str)
            return dt.isoformat()
        except Exception:
            return datetime.now().isoformat()

    # =======================================================================
    # Malaysian publisher RSS feeds (supplementary to Google News)
    # =======================================================================

    async def _crawl_malaysian_feeds(
        self,
        query: str,
        max_results: int,
        existing_ids: set,
    ) -> List[Dict[str, Any]]:
        """
        Fetch the latest items from each Malaysian publisher RSS feed
        in parallel, then keep only items whose title+description
        contains the keyword (case-insensitive substring match).

        Publisher RSS feeds do NOT support server-side keyword search,
        so we filter client-side.

        Behavior with mixed-language feeds:
          • EN keyword → matches in English feeds + brand names in MS/ZH feeds
          • MS keyword → matches in Malay feeds + brand names in EN/ZH feeds
          • ZH keyword → matches in Chinese feeds only

        For multi-token boolean queries like 'foo OR bar' we extract the
        individual terms and match any of them (best-effort — full Google
        operators are not supported here).
        """
        terms = self._extract_match_terms(query)
        if not terms:
            return []

        logger.info(
            f"📰 [news] Searching {len(MALAYSIAN_RSS_FEEDS)} Malaysian RSS feeds "
            f"for terms: {terms}"
        )

        loop = asyncio.get_event_loop()
        tasks = [
            loop.run_in_executor(None, self._fetch_publisher_rss, feed)
            for feed in MALAYSIAN_RSS_FEEDS
        ]
        feed_results = await asyncio.gather(*tasks, return_exceptions=True)

        records: List[Dict[str, Any]] = []
        ascii_only_query = all(ord(c) < 128 for term in terms for c in term)

        for feed, result in zip(MALAYSIAN_RSS_FEEDS, feed_results):
            if isinstance(result, Exception):
                logger.warning(f"   ⚠️  {feed['name']}: {result}")
                continue

            items, raw_count = result
            matches = self._filter_items_by_terms(items, terms, feed)
            logger.info(
                f"   • {feed['name']:<25} [{feed['lang']}]: "
                f"{raw_count:>3} items → {len(matches):>2} matched"
            )

            if feed["lang"] == "zh" and ascii_only_query and not matches:
                # Soft notice — expected when ASCII query has no brand-name overlap
                pass

            for rec in matches:
                if rec["ID"] in existing_ids:
                    continue
                existing_ids.add(rec["ID"])
                records.append(rec)
                if len(records) >= max_results:
                    return records

        return records

    def _fetch_publisher_rss(self, feed: Dict[str, str]) -> tuple:
        """
        Synchronous fetch + parse of a standard RSS 2.0 / Atom feed.
        Returns (list_of_records, raw_item_count).
        """
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept": "application/rss+xml, application/xml, text/xml, */*",
        }
        resp = requests.get(feed["url"], headers=headers, timeout=_HTTP_TIMEOUT)
        resp.raise_for_status()

        # Some feeds return latin-1; let ET handle encoding via raw bytes
        root = ET.fromstring(resp.content)

        # RSS 2.0: <rss><channel><item>...</item></channel></rss>
        items = root.findall(".//item")
        # Atom fallback: <feed><entry>...</entry></feed>
        if not items:
            items = root.findall(".//{http://www.w3.org/2005/Atom}entry")

        records = []
        for it in items:
            rec = self._parse_publisher_item(it, feed)
            if rec:
                records.append(rec)
        return records, len(items)

    def _parse_publisher_item(self, item, feed: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """Parse one standard RSS <item> or Atom <entry> into our schema."""
        def _txt(tag: str) -> str:
            el = item.find(tag)
            if el is None:
                # Try Atom namespace
                el = item.find(f"{{http://www.w3.org/2005/Atom}}{tag}")
            return (el.text or "").strip() if el is not None and el.text else ""

        title = _txt("title")
        link  = _txt("link")
        if not link:
            link_el = item.find("{http://www.w3.org/2005/Atom}link")
            if link_el is not None:
                link = link_el.get("href", "")
        if not (title and link):
            return None

        desc_raw = _txt("description") or _txt("summary") or _txt("content")
        desc = re.sub(r"<[^>]+>", "", desc_raw).strip()

        pub_date = _txt("pubDate") or _txt("published") or _txt("updated")

        text = f"{title}. {desc}" if (desc and desc not in title) else title
        rec = self._record_template("news", "post")
        rec["ID"]   = hashlib.md5(link.encode()).hexdigest()[:16]
        rec["Text"] = text
        rec["URL"]  = link
        rec["Date"] = self._parse_rss_date(pub_date)
        return rec

    @staticmethod
    def _extract_match_terms(query: str) -> List[str]:
        """
        Extract searchable terms from a (possibly boolean) query string.
        Strips Google operators (when:, site:, intitle:, -exclusion).
        Splits on OR / whitespace; preserves "quoted phrases".
        """
        q = query.strip()
        # Drop Google-only operators
        q = re.sub(r"\b(when|after|before|site|intitle|inurl):[^\s]+", " ", q)
        # Drop negations
        q = re.sub(r"(^|\s)-\S+", " ", q)
        # Extract quoted phrases first
        phrases = re.findall(r'"([^"]+)"', q)
        q_no_quotes = re.sub(r'"[^"]+"', " ", q)
        # Then OR-separated bare terms
        bare = [t.strip() for t in re.split(r"\s+OR\s+|\s+", q_no_quotes) if t.strip()]
        terms = [t.lower() for t in (phrases + bare) if len(t) >= 2]
        # Deduplicate while preserving order
        seen, out = set(), []
        for t in terms:
            if t not in seen:
                seen.add(t)
                out.append(t)
        return out

    @staticmethod
    def _filter_items_by_terms(
        items: List[Dict[str, Any]],
        terms: List[str],
        feed: Dict[str, str],
    ) -> List[Dict[str, Any]]:
        """Return items whose Text contains ANY of the terms (case-insensitive)."""
        out = []
        for rec in items:
            haystack = rec["Text"].lower()
            if any(term in haystack for term in terms):
                out.append(rec)
        return out

    # =======================================================================
    # Shared helpers
    # =======================================================================

    @staticmethod
    def _record_template(platform: str, record_type: str = "post") -> Dict[str, Any]:
        """Return an empty dict matching the standard 13-column CSV schema."""
        return {
            "Platform":        platform,
            "Type":            record_type,
            "ID":              "",
            "Text":            "",
            "URL":             "",
            "Sentiment":       "",
            "Date":            "",
            "likes":           0,
            "shares":          0,
            "comments_count":  0,
            "views":           0,
            "sentiment_score": 0.0,
            "total_engagement": 0,
        }

    @staticmethod
    def is_available() -> bool:
        """Quick health-check — Scrapling must be importable."""
        return SCRAPLING_AVAILABLE
