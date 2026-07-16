"""
Direct news scrape — percuma, tiada API key.

Sumber:
  - China Press (n9 + utama): listing HTML + Coral comment API
  - WordPress RSS (FMT): artikel + komen via /feed comment RSS
  - Publisher RSS (BH, HMetro, Utusan, Malaysiakini): artikel filter keyword NS
"""
from __future__ import annotations

import hashlib
import json
import logging
import re
import xml.etree.ElementTree as ET
from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import Any, Dict, List, Optional, Set
from urllib.parse import urljoin, urlparse

import requests

logger = logging.getLogger(__name__)

_HTTP_TIMEOUT = 20
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-MY,en;q=0.9,ms;q=0.8,zh-CN;q=0.7",
}

# Elak proxy Apify/env mempengaruhi scrape berita langsung
_SESSION = requests.Session()
_SESSION.trust_env = False


def _record(platform: str, rtype: str, text: str, url: str, date: str = "", **extra) -> Dict[str, Any]:
    rid = hashlib.md5(f"{rtype}:{url}:{text[:80]}".encode()).hexdigest()[:16]
    rec = {
        "Platform": platform,
        "Type": rtype,
        "ID": rid,
        "Text": text,
        "URL": url,
        "Sentiment": "",
        "Date": date or datetime.now().isoformat(),
        "likes": 0,
        "shares": 0,
        "comments_count": extra.pop("comments_count", 0),
        "views": 0,
        "sentiment_score": 0.0,
        "total_engagement": 0,
    }
    rec.update(extra)
    return rec


def _parse_rss_date(pub_date_str: str) -> str:
    if not pub_date_str:
        return datetime.now().isoformat()
    try:
        return parsedate_to_datetime(pub_date_str).isoformat()
    except Exception:
        return datetime.now().isoformat()


def _matches_keywords(text: str, keywords: Optional[List[str]]) -> bool:
    if not keywords:
        return True
    hay = text.lower()
    return any(k.lower() in hay for k in keywords)


def _fetch(url: str) -> str:
    resp = _SESSION.get(url, headers=_HEADERS, timeout=_HTTP_TIMEOUT)
    resp.raise_for_status()
    return resp.text


def _fetch_json(url: str) -> Any:
    resp = _SESSION.get(
        url,
        headers={**_HEADERS, "Accept": "application/json"},
        timeout=_HTTP_TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json()


def _meta_content(html: str, prop: str) -> str:
    m = re.search(
        rf'<meta\s+(?:property|name)="{re.escape(prop)}"\s+content="([^"]*)"',
        html,
        re.I,
    )
    return m.group(1).strip() if m else ""


def _strip_html(raw: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", raw or "")).strip()


class DirectNewsScraper:
    """Scrape Malaysian news publishers directly (RM0)."""

    def crawl_sources(
        self,
        sources: List[Dict[str, Any]],
        max_articles_per_source: int = 25,
        max_comments_per_article: int = 15,
    ) -> List[Dict[str, Any]]:
        rows: List[Dict[str, Any]] = []
        seen: Set[str] = set()

        for src in sources:
            method = src.get("method", "")
            sid = src.get("id", "?")
            try:
                if method == "chinapress":
                    batch = self._crawl_chinapress(src, max_articles_per_source, max_comments_per_article)
                elif method == "wordpress_rss":
                    batch = self._crawl_wordpress_rss(src, max_articles_per_source, max_comments_per_article)
                elif method == "publisher_rss":
                    batch = self._crawl_publisher_rss(src, max_articles_per_source)
                elif method == "sinchew":
                    batch = self._crawl_sinchew(src, max_articles_per_source)
                elif method == "tamil_rss":
                    batch = self._crawl_tamil_rss(src, max_articles_per_source)
                else:
                    logger.warning("Unknown direct source method: %s", method)
                    continue
            except Exception as exc:
                logger.error("Direct scrape failed [%s]: %s", sid, exc)
                print(f"   ⚠️  [{sid}] gagal: {exc}")
                continue

            added = 0
            for rec in batch:
                key = rec.get("ID") or rec.get("URL")
                if key in seen:
                    continue
                seen.add(key)
                rec.setdefault("SourceID", sid)
                rec.setdefault("CrawlMethod", "direct_scrape")
                rows.append(rec)
                added += 1
            print(f"   ✅ [{sid}] +{added} ({src.get('name', sid)})")

        return rows

    # ── China Press ───────────────────────────────────────────────────────

    def _crawl_chinapress(
        self,
        src: Dict[str, Any],
        max_articles: int,
        max_comments: int,
    ) -> List[Dict[str, Any]]:
        base = src["base_url"].rstrip("/")
        keywords = src.get("keywords")
        require_kw = bool(keywords)
        rows: List[Dict[str, Any]] = []
        article_urls: List[str] = []

        for listing in src.get("listing_urls", []):
            if len(article_urls) >= max_articles:
                break
            html = _fetch(listing)
            found = re.findall(
                rf'href="({re.escape(base)}/\d{{8}}/[^"]+)"',
                html,
            )
            for u in found:
                u = u.split("#")[0].rstrip("/") + "/"
                if u not in article_urls:
                    article_urls.append(u)
                if len(article_urls) >= max_articles:
                    break

        for url in article_urls[:max_articles]:
            try:
                html = _fetch(url)
            except Exception:
                continue

            title = _meta_content(html, "og:title") or _meta_content(html, "twitter:title")
            desc = _meta_content(html, "og:description") or _meta_content(html, "description")
            if not title:
                continue
            text = f"{title}. {desc}" if desc and desc not in title else title
            if require_kw and not _matches_keywords(text, keywords):
                continue

            pid_m = re.search(r'data-pid="(\d+)"', html)
            pid = pid_m.group(1) if pid_m else ""
            date_m = re.search(r"/(\d{8})/", url)
            date_iso = ""
            if date_m:
                try:
                    date_iso = datetime.strptime(date_m.group(1), "%Y%m%d").isoformat()
                except ValueError:
                    pass

            article = _record(
                "news",
                "post",
                text[:500],
                url,
                date_iso,
                SourceName=src.get("name"),
                PublisherDomain=urlparse(base).netloc,
                PostID=pid,
            )
            rows.append(article)

            if src.get("comments") and pid:
                comments = self._fetch_chinapress_comments(base, pid, max_comments)
                article["comments_count"] = len(comments)
                for c in comments:
                    body = _strip_html(str(c.get("body", "")))
                    author = (c.get("author") or {}).get("username", "anon")
                    ctext = f"{author}: {body}"
                    rows.append(
                        _record(
                            "news",
                            "comment",
                            ctext[:500],
                            url,
                            c.get("createdAt", date_iso),
                            ParentURL=url,
                            ParentTitle=title[:200],
                            CommentID=str(c.get("id", "")),
                            Author=author,
                            SourceName=src.get("name"),
                        )
                    )
        return rows

    def _fetch_chinapress_comments(self, base: str, post_id: str, limit: int) -> List[dict]:
        url = (
            f"{base}/comment/api/retrieval"
            f"?postid={post_id}&offset=0&limit={limit}&pagenum=1&order_by=CREATED_AT_DESC"
        )
        try:
            data = _fetch_json(url)
        except Exception:
            return []
        if not isinstance(data, list):
            return []
        comments = []
        for item in data:
            if isinstance(item, dict) and "total_result" in item:
                continue
            if isinstance(item, dict) and item.get("body"):
                comments.append(item)
        return comments[:limit]

    # ── Sin Chew Daily (星洲日报) ─────────────────────────────────────────

    def _crawl_sinchew(self, src: Dict[str, Any], max_articles: int) -> List[Dict[str, Any]]:
        base = src["base_url"].rstrip("/")
        keywords = src.get("keywords")
        require_kw = bool(keywords)
        rows: List[Dict[str, Any]] = []
        article_urls: List[str] = []

        for listing in src.get("listing_urls", []):
            if len(article_urls) >= max_articles:
                break
            try:
                html = _fetch(listing)
            except Exception:
                continue
            found = re.findall(
                rf'href="({re.escape(base)}/news/\d{{8}}/[^"]+)"',
                html,
            )
            for u in found:
                u = u.split("#")[0].rstrip("/")
                if u not in article_urls:
                    article_urls.append(u)
                if len(article_urls) >= max_articles:
                    break

        for url in article_urls[:max_articles]:
            try:
                html = _fetch(url)
            except Exception:
                continue

            title = _meta_content(html, "og:title") or _meta_content(html, "twitter:title")
            desc = _meta_content(html, "og:description") or _meta_content(html, "description")
            if not title:
                continue
            text = f"{title}. {desc}" if desc and desc not in title else title
            if require_kw and not _matches_keywords(text, keywords):
                continue

            date_m = re.search(r"/news/(\d{8})/", url)
            date_iso = ""
            if date_m:
                try:
                    date_iso = datetime.strptime(date_m.group(1), "%Y%m%d").isoformat()
                except ValueError:
                    pass

            rows.append(
                _record(
                    "news",
                    "post",
                    text[:500],
                    url,
                    date_iso,
                    SourceName=src.get("name"),
                    PublisherDomain=urlparse(base).netloc,
                )
            )
        return rows

    # ── WordPress RSS + comment feed ──────────────────────────────────────

    def _crawl_wordpress_rss(
        self,
        src: Dict[str, Any],
        max_articles: int,
        max_comments: int,
    ) -> List[Dict[str, Any]]:
        feed_url = src["feed_url"]
        keywords = src.get("keywords", [])
        rows: List[Dict[str, Any]] = []

        root = ET.fromstring(_fetch(feed_url).encode("utf-8", errors="replace"))
        ns = {
            "content": "http://purl.org/rss/1.0/modules/content/",
            "dc": "http://purl.org/dc/elements/1.1/",
            "wfw": "http://wellformedweb.org/CommentAPI/",
            "slash": "http://purl.org/rss/1.0/modules/slash/",
        }
        count = 0
        for item in root.findall(".//item"):
            if count >= max_articles:
                break
            title_el = item.find("title")
            link_el = item.find("link")
            if title_el is None or link_el is None:
                continue
            title = (title_el.text or "").strip()
            link = (link_el.text or "").strip()
            if not title or not link:
                continue
            desc_el = item.find("description")
            desc = _strip_html(desc_el.text if desc_el is not None else "")
            text = f"{title}. {desc}" if desc else title
            if not _matches_keywords(text, keywords):
                continue

            pub = item.find("pubDate")
            date_iso = _parse_rss_date(pub.text if pub is not None else "")

            slash_el = item.find("slash:comments", ns)
            comment_count = int((slash_el.text or "0").strip() or 0) if slash_el is not None else 0

            article = _record(
                "news",
                "post",
                text[:500],
                link,
                date_iso,
                SourceName=src.get("name"),
                PublisherDomain=urlparse(link).netloc,
                comments_count=comment_count,
            )
            rows.append(article)
            count += 1

            if src.get("comments") and comment_count > 0:
                comment_feed = None
                wfw_el = item.find("wfw:commentRss", ns)
                if wfw_el is not None and wfw_el.text:
                    comment_feed = wfw_el.text.strip()
                if not comment_feed:
                    comment_feed = link.rstrip("/") + "/feed"
                rows.extend(
                    self._fetch_wp_comments(comment_feed, link, title, max_comments, src.get("name"))
                )
        return rows

    def _fetch_wp_comments(
        self,
        comment_feed_url: str,
        article_url: str,
        article_title: str,
        limit: int,
        source_name: Optional[str],
    ) -> List[Dict[str, Any]]:
        rows: List[Dict[str, Any]] = []
        try:
            root = ET.fromstring(_fetch(comment_feed_url).encode("utf-8", errors="replace"))
        except Exception:
            return rows

        ns = {"dc": "http://purl.org/dc/elements/1.1/"}
        for item in root.findall(".//item")[:limit]:
            title_el = item.find("title")
            desc_el = item.find("description")
            link_el = item.find("link")
            pub_el = item.find("pubDate")
            creator_el = item.find("dc:creator", ns)

            body = _strip_html(desc_el.text if desc_el is not None else "")
            if not body:
                continue
            author = (creator_el.text or "").strip() if creator_el is not None else "anon"
            if author.lower().startswith("comments on:"):
                author = "reader"
            ctext = f"{author}: {body}"
            rows.append(
                _record(
                    "news",
                    "comment",
                    ctext[:500],
                    (link_el.text or article_url).strip() if link_el is not None else article_url,
                    _parse_rss_date(pub_el.text if pub_el is not None else ""),
                    ParentURL=article_url,
                    ParentTitle=article_title[:200],
                    Author=author,
                    SourceName=source_name,
                )
            )
        return rows

    # ── Tamil RSS (Makkal Osai etc.) ───────────────────────────────────────

    def _crawl_tamil_rss(self, src: Dict[str, Any], max_articles: int) -> List[Dict[str, Any]]:
        """WordPress RSS — keep Tamil-script items; optional keyword filter."""
        feed_url = src["feed_url"]
        keywords = src.get("keywords")
        require_tamil = bool(src.get("require_tamil_script", True))
        rows: List[Dict[str, Any]] = []

        root = ET.fromstring(_fetch(feed_url).encode("utf-8", errors="replace"))
        ns = {
            "content": "http://purl.org/rss/1.0/modules/content/",
            "dc": "http://purl.org/dc/elements/1.1/",
        }
        count = 0
        for item in root.findall(".//item"):
            if count >= max_articles:
                break
            title_el = item.find("title")
            link_el = item.find("link")
            if title_el is None or link_el is None:
                continue
            title = (title_el.text or "").strip()
            link = (link_el.text or "").strip()
            if not title or not link:
                continue

            desc_el = item.find("description")
            content_el = item.find("content:encoded", ns)
            desc = _strip_html(
                (content_el.text if content_el is not None else "")
                or (desc_el.text if desc_el is not None else "")
            )
            text = f"{title}. {desc[:300]}" if desc else title

            if require_tamil and not re.search(r"[\u0B80-\u0BFF]", text):
                continue
            if keywords and not _matches_keywords(text, keywords):
                continue

            pub = item.find("pubDate")
            rows.append(
                _record(
                    "news",
                    "post",
                    text[:500],
                    link.split("#")[0],
                    _parse_rss_date(pub.text if pub is not None else ""),
                    SourceName=src.get("name"),
                    PublisherDomain=urlparse(link).netloc,
                    Jenis_Suara="media_india",
                )
            )
            count += 1
        return rows

    # ── Generic publisher RSS (BH, HMetro, Utusan, MKini) ─────────────────

    def _crawl_publisher_rss(self, src: Dict[str, Any], max_articles: int) -> List[Dict[str, Any]]:
        feed_url = src["feed_url"]
        keywords = src.get("keywords", [])
        rows: List[Dict[str, Any]] = []

        root = ET.fromstring(_fetch(feed_url).encode("utf-8", errors="replace"))
        ns = {"content": "http://purl.org/rss/1.0/modules/content/"}
        count = 0
        for item in root.findall(".//item"):
            if count >= max_articles:
                break
            title_el = item.find("title")
            link_el = item.find("link")
            if title_el is None or link_el is None:
                continue
            title = _strip_html(title_el.text or "")
            link = (link_el.text or "").strip()
            if not title or not link:
                continue

            desc_el = item.find("description")
            content_el = item.find("content:encoded", ns)
            desc = _strip_html(
                (content_el.text if content_el is not None else "")
                or (desc_el.text if desc_el is not None else "")
            )
            text = f"{title}. {desc[:300]}" if desc else title
            if not _matches_keywords(text, keywords):
                continue

            pub = item.find("pubDate")
            rows.append(
                _record(
                    "news",
                    "post",
                    text[:500],
                    link.split("#")[0],
                    _parse_rss_date(pub.text if pub is not None else ""),
                    SourceName=src.get("name"),
                    PublisherDomain=urlparse(link).netloc,
                )
            )
            count += 1
        return rows
