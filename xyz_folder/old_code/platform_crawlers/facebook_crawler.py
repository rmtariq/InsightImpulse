"""Facebook crawler implementation."""
from typing import Dict, Any, List
from datetime import datetime
from .base_crawler import BaseCrawler


class FacebookCrawler(BaseCrawler):
    """Crawler for Facebook platform using danek/facebook-search-ppr.

    This actor searches for Facebook POSTS by keyword and returns post details
    including content, engagement metrics, author info, etc.

    Pricing: $2.99 per 1,000 results (Pay Per Result model)
    """

    def __init__(self):
        super().__init__("facebook")

    def prepare_input(self, query: str, **kwargs) -> Dict[str, Any]:
        """Prepare input for Facebook Search PPR actor.

        Args:
            query: Search keyword (e.g., "mendulang emas Kelantan")
            **kwargs: Additional parameters
                - max_posts: Number of posts to scrape (default: 100)
                - search_type: Type of search - "posts", "pages", or "places" (default: "posts")
                - recent_posts: Whether to get recent posts only (default: False)
                - location: Location filter (optional)
                - start_date: Date from which to scrape posts (optional)
                - end_date: Date to which to scrape posts (optional)
        """
        input_config = {
            "query": query,  # Search keyword
            "search_type": kwargs.get("search_type", "posts"),  # posts, pages, or places
            "max_posts": kwargs.get("max_posts", 100),  # Max results
            "recent_posts": kwargs.get("recent_posts", False),  # Recent posts filter
        }

        # Add optional filters
        if "location" in kwargs:
            input_config["location"] = kwargs["location"]
        if "start_date" in kwargs:
            input_config["start_date"] = kwargs["start_date"]
        if "end_date" in kwargs:
            input_config["end_date"] = kwargs["end_date"]

        return input_config
    
    def transform_data(self, raw_data: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Transform Facebook Search PPR data to database format.

        This actor returns Facebook POST data with engagement metrics, author info, etc.
        """
        posts = []
        comments = []
        profiles = []

        for item in raw_data:
            # Extract post ID and URL
            post_id = item.get("post_id", "")
            post_url = item.get("url", "")

            # Extract post content
            message = item.get("message", "")

            # Extract timestamp
            timestamp = item.get("timestamp")
            created_at = self._parse_date(timestamp) if timestamp else None

            # Extract engagement metrics
            comments_count = int(item.get("comments_count", 0))
            reactions_count = int(item.get("reactions_count", 0))
            shares_count = int(item.get("shares_count", 0) if item.get("shares_count") else 0)

            # Extract author information
            author = item.get("author", {})
            if isinstance(author, dict):
                author_name = author.get("name", "")
                author_url = author.get("url", "")
                author_id = author_url.split("/")[-1] if author_url else ""
            else:
                author_name = str(author) if author else ""
                author_url = ""
                author_id = ""

            # Extract media
            image = item.get("image", "")
            video = item.get("video", "")
            media_urls = []
            if image:
                media_urls.append(image)
            if video:
                media_urls.append(video)

            # Extract attached post URL (if any)
            attached_post_url = item.get("attached_post_url", "")

            # Transform post data
            post_data = {
                "platform": self.platform,
                "post_id": post_id,
                "author_id": author_id,
                "author_username": author_name,
                "author_name": author_name,
                "content": message,
                "url": post_url,
                "created_at": created_at,
                "likes_count": reactions_count,  # Facebook uses "reactions" instead of "likes"
                "comments_count": comments_count,
                "shares_count": shares_count,
                "views_count": 0,  # Not provided by this actor
                "hashtags": [],  # Could extract from message if needed
                "mentions": [],  # Could extract from message if needed
                "media_urls": media_urls,
                "extra_data": {
                    "author_url": author_url,
                    "attached_post_url": attached_post_url,
                    "has_image": bool(image),
                    "has_video": bool(video),
                }
            }
            posts.append(post_data)

        return {
            "posts": posts,
            "comments": comments,
            "profiles": profiles
        }
    
    def _parse_date(self, date_str: str) -> datetime:
        """Parse date string to datetime object."""
        if not date_str:
            return None
        try:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except:
            return None

