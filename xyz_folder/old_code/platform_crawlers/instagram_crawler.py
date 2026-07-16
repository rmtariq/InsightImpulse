"""Instagram crawler implementation."""
from typing import Dict, Any, List
from datetime import datetime
from .base_crawler import BaseCrawler


class InstagramCrawler(BaseCrawler):
    """Crawler for Instagram platform."""
    
    def __init__(self):
        super().__init__("instagram")
    
    def prepare_input(self, query: str, **kwargs) -> Dict[str, Any]:
        """Prepare input for Instagram Apify actor."""
        return {
            "search": query,
            "searchType": kwargs.get("search_type", "hashtag"),  # hashtag, user, place
            "resultsLimit": kwargs.get("max_posts", 100),
            "addParentData": True,
            "scrapeComments": kwargs.get("scrape_comments", True),
            "maxComments": kwargs.get("max_comments", 50),
        }
    
    def transform_data(self, raw_data: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Transform Instagram data to database format."""
        posts = []
        profiles = []
        comments = []
        
        for item in raw_data:
            # Transform post
            post_data = {
                "platform": self.platform,
                "post_id": item.get("id") or item.get("shortCode", ""),
                "author_id": item.get("ownerId", ""),
                "author_username": item.get("ownerUsername", ""),
                "author_name": item.get("ownerFullName", ""),
                "content": item.get("caption", ""),
                "url": item.get("url", ""),
                "created_at": self._parse_timestamp(item.get("timestamp")),
                "likes_count": item.get("likesCount", 0),
                "comments_count": item.get("commentsCount", 0),
                "shares_count": 0,
                "views_count": item.get("videoViewCount", 0),
                "hashtags": item.get("hashtags", []),
                "mentions": item.get("mentions", []),
                "media_urls": [item.get("displayUrl", "")] + item.get("images", []),
                "metadata": {
                    "type": item.get("type", ""),
                    "is_video": item.get("isVideo", False),
                    "video_url": item.get("videoUrl", ""),
                    "location": item.get("locationName", ""),
                }
            }
            posts.append(post_data)
            
            # Transform owner profile
            profile_data = {
                "platform": self.platform,
                "user_id": item.get("ownerId", ""),
                "username": item.get("ownerUsername", ""),
                "display_name": item.get("ownerFullName", ""),
                "bio": "",
                "profile_url": f"https://instagram.com/{item.get('ownerUsername', '')}",
                "avatar_url": "",
                "verified": 1 if item.get("verified", False) else 0,
                "followers_count": 0,
                "following_count": 0,
                "posts_count": 0,
                "metadata": {}
            }
            profiles.append(profile_data)
        
        return {
            "posts": posts,
            "profiles": profiles,
            "comments": comments
        }
    
    def _parse_timestamp(self, timestamp: int) -> datetime:
        """Parse Unix timestamp to datetime object."""
        if not timestamp:
            return None
        try:
            return datetime.fromtimestamp(timestamp)
        except:
            return None

