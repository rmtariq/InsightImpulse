"""LinkedIn Posts crawler implementation for searching posts by keywords."""
from typing import Dict, Any, List
from datetime import datetime
from loguru import logger

from .base_crawler import BaseCrawler


class LinkedInPostsCrawler(BaseCrawler):
    """
    Crawler for LinkedIn posts search.

    Uses: apimaestro/linkedin-posts-search-scraper-no-cookies
    Cost: ~$2-3 per 1,000 results

    Features:
    - Search posts by keywords
    - No login/cookies required
    - Sort by relevance or date
    - Collect engagement metrics
    """

    def __init__(self):
        super().__init__("linkedin")
        self.default_actor_id = "apimaestro/linkedin-posts-search-scraper-no-cookies"

    def crawl(self, query: str, save_to_db: bool = True, actor_id: str = None, **kwargs):
        """Override crawl to use custom actor by default."""
        if actor_id is None:
            actor_id = self.default_actor_id
        return super().crawl(query, save_to_db, actor_id, **kwargs)
    
    def prepare_input(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Prepare input for LinkedIn Post Search actor.

        Args:
            query: Search keyword/phrase
            **kwargs: Additional options
                - max_results: Maximum posts to collect (default: 50)
                - sort_by: 'RELEVANCE' or 'DATE'

        Returns:
            Input configuration for Apify actor
        """
        max_results = kwargs.get("max_results", kwargs.get("max_items", 50))
        sort_by = kwargs.get("sort_by", "RELEVANCE").upper()

        logger.info(f"LinkedIn search: '{query}', max_results={max_results}, sort={sort_by}")

        return {
            "keywords": [query],
            "maxResults": max_results,
            "sortBy": sort_by,
        }
    
    def transform_data(self, raw_data: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Transform LinkedIn post data to database format.

        Args:
            raw_data: Raw data from Apify actor

        Returns:
            Dictionary with 'posts' list
        """
        posts = []

        for item in raw_data:
            # Generate unique post ID from activity_id or URL
            post_id = item.get("activity_id") or self._extract_post_id_from_url(item.get("post_url", ""))

            # Parse timestamp
            created_at = self._parse_date(item.get("posted_at") or item.get("timestamp"))

            # Extract author info
            author_name = item.get("author_name", "")
            author_id = item.get("author_profile_url", "").split("/")[-1] if item.get("author_profile_url") else ""
            author_username = author_id

            # Extract engagement metrics
            likes_count = item.get("num_likes", 0) or item.get("likes", 0) or 0
            comments_count = item.get("num_comments", 0) or item.get("comments", 0) or 0
            shares_count = item.get("num_shares", 0) or item.get("shares", 0) or 0

            post_data = {
                "platform": self.platform,
                "post_id": str(post_id),
                "author_id": str(author_id),
                "author_username": author_username,
                "author_name": author_name,
                "content": item.get("text") or item.get("post_text") or "",
                "url": item.get("post_url") or "",
                "created_at": created_at,
                "likes_count": likes_count,
                "comments_count": comments_count,
                "shares_count": shares_count,
                "views_count": 0,
                "hashtags": [],
                "mentions": [],
                "media_urls": item.get("images") or [],
                "metadata": {
                    "author_headline": item.get("author_headline", ""),
                    "author_profile_url": item.get("author_profile_url", ""),
                    "full_urn": item.get("full_urn", ""),
                }
            }
            posts.append(post_data)

        logger.info(f"Transformed {len(posts)} LinkedIn posts")
        return {"posts": posts}
    
    def _extract_post_id_from_url(self, url: str) -> str:
        """Extract post ID from LinkedIn URL."""
        if not url:
            return ""
        
        # LinkedIn post URLs: https://www.linkedin.com/posts/username_activity-1234567890-abcd
        if "activity-" in url:
            parts = url.split("activity-")
            if len(parts) > 1:
                return parts[1].split("-")[0]
        
        # Fallback: use hash of URL
        import hashlib
        return hashlib.md5(url.encode()).hexdigest()[:16]
    
    def _parse_date(self, date_str: str) -> datetime:
        """Parse date string to datetime object."""
        if not date_str:
            return None
        try:
            # Try ISO format
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except:
            try:
                # Try timestamp (milliseconds)
                timestamp = int(date_str) / 1000
                return datetime.fromtimestamp(timestamp)
            except:
                return None

