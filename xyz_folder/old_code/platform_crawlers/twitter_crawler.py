"""Twitter/X crawler implementation."""
from typing import Dict, Any, List
from datetime import datetime
from .base_crawler import BaseCrawler


class TwitterCrawler(BaseCrawler):
    """Crawler for Twitter/X platform."""
    
    def __init__(self):
        super().__init__("twitter")
    
    def prepare_input(self, query: str, **kwargs) -> Dict[str, Any]:
        """Prepare input for Twitter Apify actor."""
        return {
            "searchTerms": [query],
            "maxTweets": kwargs.get("max_tweets", 100),
            "addUserInfo": True,
            "scrapeTweetReplies": kwargs.get("scrape_replies", True),
            "maxReplies": kwargs.get("max_replies", 50),
            "startUrls": kwargs.get("start_urls", []),
            "languageCode": kwargs.get("language", "en"),
        }
    
    def transform_data(self, raw_data: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Transform Twitter data to database format."""
        posts = []
        profiles = []
        comments = []
        
        for item in raw_data:
            # Get post ID and convert to string
            post_id = str(item.get("id") or item.get("tweetId", ""))

            # Skip invalid post IDs (empty, -1, or error messages)
            if not post_id or post_id == "-1" or post_id == "":
                continue

            # Skip if this looks like an API error message (no URL or author)
            if not item.get("url") and not item.get("author"):
                continue

            # Transform post/tweet
            post_data = {
                "platform": self.platform,
                "post_id": post_id,
                "author_id": str(item.get("author", {}).get("id", "")),
                "author_username": item.get("author", {}).get("userName", ""),
                "author_name": item.get("author", {}).get("name", ""),
                "content": item.get("text", ""),
                "url": item.get("url", ""),
                "created_at": self._parse_date(item.get("createdAt")),
                "likes_count": item.get("likeCount", 0),
                "comments_count": item.get("replyCount", 0),
                "shares_count": item.get("retweetCount", 0),
                "views_count": item.get("viewCount", 0),
                "hashtags": item.get("hashtags", []),
                "mentions": item.get("mentions", []),
                "media_urls": [media.get("url") for media in item.get("media", [])],
                "metadata": {
                    "is_retweet": item.get("isRetweet", False),
                    "is_quote": item.get("isQuote", False),
                    "quote_count": item.get("quoteCount", 0),
                    "bookmark_count": item.get("bookmarkCount", 0),
                }
            }
            posts.append(post_data)
            
            # Transform author profile
            if "author" in item:
                author = item["author"]
                profile_data = {
                    "platform": self.platform,
                    "user_id": author.get("id", ""),
                    "username": author.get("userName", ""),
                    "display_name": author.get("name", ""),
                    "bio": author.get("description", ""),
                    "profile_url": f"https://twitter.com/{author.get('userName', '')}",
                    "avatar_url": author.get("profilePicture", ""),
                    "verified": 1 if author.get("isVerified", False) else 0,
                    "followers_count": author.get("followers", 0),
                    "following_count": author.get("following", 0),
                    "posts_count": author.get("statusesCount", 0),
                    "account_created_at": self._parse_date(author.get("createdAt")),
                    "metadata": {
                        "location": author.get("location", ""),
                        "url": author.get("url", ""),
                    }
                }
                profiles.append(profile_data)
        
        return {
            "posts": posts,
            "profiles": profiles,
            "comments": comments
        }
    
    def _parse_date(self, date_str: str) -> datetime:
        """Parse date string to datetime object."""
        if not date_str:
            return None
        try:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except:
            return None

