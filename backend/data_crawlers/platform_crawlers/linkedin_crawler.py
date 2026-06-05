"""LinkedIn crawler implementation."""
from typing import Dict, Any, List
from datetime import datetime
from .base_crawler import BaseCrawler


class LinkedInCrawler(BaseCrawler):
    """Crawler for LinkedIn platform."""
    
    def __init__(self):
        super().__init__("linkedin")
    
    def prepare_input(self, query: str, **kwargs) -> Dict[str, Any]:
        """Prepare input for LinkedIn Apify actor."""
        return {
            "startUrls": kwargs.get("start_urls", [{"url": query}]),
            "maxResults": kwargs.get("max_results", 100),
        }
    
    def transform_data(self, raw_data: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Transform LinkedIn data to database format."""
        posts = []
        profiles = []
        
        for item in raw_data:
            # Check if it's a profile or post
            if "firstName" in item or "lastName" in item:
                # Transform profile
                profile_data = {
                    "platform": self.platform,
                    "user_id": item.get("publicIdentifier", ""),
                    "username": item.get("publicIdentifier", ""),
                    "display_name": f"{item.get('firstName', '')} {item.get('lastName', '')}".strip(),
                    "bio": item.get("summary", ""),
                    "profile_url": f"https://linkedin.com/in/{item.get('publicIdentifier', '')}",
                    "avatar_url": item.get("photoUrl", ""),
                    "verified": 0,
                    "followers_count": item.get("followersCount", 0),
                    "following_count": 0,
                    "posts_count": 0,
                    "metadata": {
                        "headline": item.get("headline", ""),
                        "location": item.get("location", ""),
                        "industry": item.get("industry", ""),
                        "connections": item.get("connectionsCount", 0),
                    }
                }
                profiles.append(profile_data)
            else:
                # Transform post
                post_data = {
                    "platform": self.platform,
                    "post_id": item.get("postId", ""),
                    "author_id": item.get("authorId", ""),
                    "author_username": item.get("authorName", ""),
                    "author_name": item.get("authorName", ""),
                    "content": item.get("text", ""),
                    "url": item.get("url", ""),
                    "created_at": self._parse_date(item.get("postedAt")),
                    "likes_count": item.get("likesCount", 0),
                    "comments_count": item.get("commentsCount", 0),
                    "shares_count": item.get("sharesCount", 0),
                    "views_count": 0,
                    "hashtags": [],
                    "mentions": [],
                    "media_urls": item.get("images", []),
                    "metadata": {}
                }
                posts.append(post_data)
        
        return {
            "posts": posts,
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

