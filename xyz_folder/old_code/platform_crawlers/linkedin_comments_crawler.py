"""LinkedIn Comments crawler implementation."""
from typing import Dict, Any, List
from datetime import datetime
from loguru import logger

from .base_crawler import BaseCrawler


class LinkedInCommentsCrawler(BaseCrawler):
    """
    Crawler for LinkedIn post comments.

    Uses: harvestapi/linkedin-post-comments
    Cost: ~$2 per 1,000 comments

    Features:
    - Extract comments from LinkedIn posts
    - No login/cookies required
    - Get comment reactions and engagement data
    """

    def __init__(self):
        super().__init__("linkedin")
        self.default_actor_id = "harvestapi/linkedin-post-comments"

    def crawl(self, query: str, save_to_db: bool = True, actor_id: str = None, **kwargs):
        """Override crawl to use custom actor by default."""
        if actor_id is None:
            actor_id = self.default_actor_id
        return super().crawl(query, save_to_db, actor_id, **kwargs)

    def prepare_input(self, post_url: str, **kwargs) -> Dict[str, Any]:
        """
        Prepare input for LinkedIn Comments actor.

        Args:
            post_url: LinkedIn post URL
            **kwargs: Additional options
                - max_comments: Maximum comments to collect (default: 100)
                - posted_limit: Time filter (e.g., "24h", "week", "month", "any")
                - profile_mode: "short" or "main" (default: "short")

        Returns:
            Input configuration for Apify actor
        """
        max_comments = kwargs.get("max_comments", kwargs.get("max_items", 100))
        posted_limit = kwargs.get("posted_limit", "any")
        profile_mode = kwargs.get("profile_mode", "short")

        logger.info(f"LinkedIn comments for: {post_url}, max={max_comments}")

        input_data = {
            "posts": [post_url],
            "maxItems": max_comments,
            "profileScraperMode": profile_mode,
        }

        # Only add postedLimit if it's not "any"
        if posted_limit and posted_limit != "any":
            input_data["postedLimit"] = posted_limit

        return input_data
    
    def transform_data(self, raw_data: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Transform LinkedIn comment data to database format.

        Args:
            raw_data: Raw data from Apify actor (harvestapi/linkedin-post-comments)

        Returns:
            Dictionary with 'comments' list
        """
        comments = []

        for item in raw_data:
            # Extract comment ID
            comment_id = item.get("id") or item.get("comment_id") or item.get("urn") or ""

            # Extract post ID from postId field or linkedinUrl
            post_id = item.get("postId", "")
            if not post_id and item.get("linkedinUrl"):
                post_id = self._extract_post_id_from_url(item.get("linkedinUrl"))

            # Parse timestamp - harvestapi uses createdAt (ISO format) or createdAtTimestamp (milliseconds)
            created_at = None
            if item.get("createdAt"):
                created_at = self._parse_date(item.get("createdAt"))
            elif item.get("createdAtTimestamp"):
                created_at = self._parse_date(str(item.get("createdAtTimestamp")))

            # Extract author info from actor object
            actor = item.get("actor", {})
            author_name = actor.get("name", "")
            author_id = actor.get("id", "")
            author_username = actor.get("linkedinUrl", "").split("/")[-1] if actor.get("linkedinUrl") else author_id

            # Extract engagement metrics
            # reactionTypeCounts is an array of {type: "LIKE", count: 1}
            reaction_counts = item.get("reactionTypeCounts", [])
            likes_count = sum(r.get("count", 0) for r in reaction_counts)
            replies_count = item.get("numComments", 0) or item.get("num_replies", 0) or 0

            comment_data = {
                "platform": self.platform,
                "comment_id": str(comment_id),
                "post_id": str(post_id),
                "author_id": str(author_id),
                "author_username": author_username,
                "author_name": author_name,
                "content": item.get("commentary") or item.get("text") or item.get("comment_text") or "",
                "created_at": created_at,
                "likes_count": likes_count,
                "replies_count": replies_count,
                "metadata": {
                    "author_position": actor.get("position", ""),
                    "author_profile_url": actor.get("linkedinUrl", ""),
                    "author_picture_url": actor.get("pictureUrl", ""),
                    "linkedin_url": item.get("linkedinUrl", ""),
                    "reaction_types": reaction_counts,
                    "pinned": item.get("pinned", False),
                    "edited": item.get("edited", False),
                }
            }
            comments.append(comment_data)

        logger.info(f"Transformed {len(comments)} LinkedIn comments")
        return {"comments": comments}
    
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

