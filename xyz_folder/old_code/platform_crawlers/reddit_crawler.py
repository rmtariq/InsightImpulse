"""Reddit crawler implementation."""
from typing import Dict, Any, List
from datetime import datetime
from .base_crawler import BaseCrawler


class RedditCrawler(BaseCrawler):
    """Crawler for Reddit platform."""
    
    def __init__(self):
        super().__init__("reddit")
    
    def prepare_input(self, query: str, **kwargs) -> Dict[str, Any]:
        """Prepare input for Reddit Apify actor."""
        return {
            "searches": [query],
            "maxItems": kwargs.get("max_posts", 100),
            "maxPostCount": kwargs.get("max_posts", 100),
            "maxComments": kwargs.get("max_comments", 50),
            "scrapeComments": kwargs.get("scrape_comments", True),
            "searchType": kwargs.get("search_type", "posts"),  # posts, subreddits, users
        }
    
    def transform_data(self, raw_data: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Transform Reddit data to database format."""
        posts = []
        profiles = []
        comments = []
        
        for item in raw_data:
            # Transform post
            post_data = {
                "platform": self.platform,
                "post_id": item.get("id", ""),
                "author_id": item.get("authorId", ""),
                "author_username": item.get("author", ""),
                "author_name": item.get("author", ""),
                "content": item.get("selftext", "") or item.get("title", ""),
                "url": item.get("url", ""),
                "created_at": self._parse_timestamp(item.get("created_utc")),
                "likes_count": item.get("ups", 0),
                "comments_count": item.get("num_comments", 0),
                "shares_count": 0,
                "views_count": 0,
                "hashtags": [],
                "mentions": [],
                "media_urls": [item.get("thumbnail", "")] if item.get("thumbnail") else [],
                "metadata": {
                    "subreddit": item.get("subreddit", ""),
                    "title": item.get("title", ""),
                    "flair": item.get("link_flair_text", ""),
                    "is_video": item.get("is_video", False),
                    "upvote_ratio": item.get("upvote_ratio", 0),
                    "awards": item.get("total_awards_received", 0),
                }
            }
            posts.append(post_data)
        
        return {
            "posts": posts,
            "profiles": profiles,
            "comments": comments
        }
    
    def _parse_timestamp(self, timestamp: float) -> datetime:
        """Parse Unix timestamp to datetime object."""
        if not timestamp:
            return None
        try:
            return datetime.fromtimestamp(timestamp)
        except:
            return None

