"""YouTube crawler implementation using SerpAPI."""
from typing import Dict, Any, List
from datetime import datetime
import hashlib
import requests
import os
from loguru import logger

from .base_crawler import BaseCrawler


class YouTubeCrawler(BaseCrawler):
    """
    Crawler for YouTube videos using SerpAPI.
    
    Uses: SerpAPI YouTube Search
    Cost: ~$0.005 per search (very cheap!)
    
    Features:
    - Search videos by keywords
    - Get video metadata (title, description, views, etc.)
    - No Apify needed - uses SerpAPI directly
    """
    
    def __init__(self):
        super().__init__("youtube")
        self.serpapi_key = os.getenv("SERPAPI_API_KEY") or os.getenv("SERPAPI_KEY")
        if not self.serpapi_key:
            logger.warning("SERPAPI_API_KEY or SERPAPI_KEY not found in environment")
    
    def prepare_input(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Prepare input for YouTube search via SerpAPI.
        
        Args:
            query: Search keyword/phrase
            **kwargs: Additional options
                - max_results: Maximum videos to collect (default: 100)
        
        Returns:
            Input configuration for SerpAPI
        """
        max_results = kwargs.get("max_results", kwargs.get("max_items", 100))
        
        logger.info(f"YouTube search: '{query}', max_results={max_results}")
        
        return {
            "engine": "youtube",
            "search_query": query,
            "api_key": self.serpapi_key,
            "num": min(max_results, 100),  # SerpAPI max is 100 per request
        }
    
    def crawl(self, query: str, save_to_db: bool = True, **kwargs) -> Dict[str, Any]:
        """
        Override crawl to use SerpAPI instead of Apify.
        
        Args:
            query: Search query
            save_to_db: Whether to save to database
            **kwargs: Additional parameters
            
        Returns:
            Crawl results
        """
        try:
            logger.info(f"Starting YouTube crawl for: {query}")
            
            # Prepare search parameters
            params = self.prepare_input(query, **kwargs)
            
            # Make request to SerpAPI
            response = requests.get("https://serpapi.com/search", params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            video_results = data.get("video_results", [])
            
            logger.info(f"Found {len(video_results)} YouTube videos")
            
            # Transform data
            transformed_data = self.transform_data(video_results)
            
            # Save to database
            items_saved = 0
            if save_to_db:
                items_saved = self.save_to_database(transformed_data)
                logger.info(f"Saved {items_saved} items to database")
            
            return {
                "platform": self.platform,
                "status": "completed",
                "items_collected": items_saved,
                "raw_data": video_results,
                "transformed_data": transformed_data
            }
            
        except Exception as e:
            logger.error(f"Error during YouTube crawl: {e}")
            raise
    
    def transform_data(self, raw_data: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Transform YouTube video data to database format.
        
        Args:
            raw_data: Raw data from SerpAPI
            
        Returns:
            Dictionary with 'posts' list
        """
        posts = []
        
        for item in raw_data:
            # Extract video ID from link
            video_url = item.get("link", "")
            video_id = self._extract_video_id(video_url)
            
            # Parse published date
            published_date = item.get("published_date")
            created_at = self._parse_date(published_date) if published_date else None
            
            # Extract channel info
            channel = item.get("channel", {})
            channel_name = channel.get("name", "")
            channel_link = channel.get("link", "")
            
            post_data = {
                "platform": self.platform,
                "post_id": video_id,
                "author_id": self._extract_channel_id(channel_link),
                "author_username": channel_name,
                "author_name": channel_name,
                "content": f"{item.get('title', '')}\n\n{item.get('description', '')}",
                "url": video_url,
                "created_at": created_at,
                "likes_count": 0,  # Not available in search results
                "comments_count": 0,  # Not available in search results
                "shares_count": 0,
                "views_count": self._parse_views(item.get("views", 0)),
                "hashtags": [],
                "mentions": [],
                "media_urls": [item.get("thumbnail", {}).get("static", "")],
                "metadata": {
                    "title": item.get("title", ""),
                    "description": item.get("description", ""),
                    "duration": item.get("length", ""),
                    "thumbnail": item.get("thumbnail", {}).get("static", ""),
                }
            }
            posts.append(post_data)
        
        logger.info(f"Transformed {len(posts)} YouTube videos")
        return {"posts": posts}

    def _extract_video_id(self, url: str) -> str:
        """Extract video ID from YouTube URL."""
        if not url:
            return ""

        # YouTube URLs: https://www.youtube.com/watch?v=VIDEO_ID
        if "v=" in url:
            return url.split("v=")[1].split("&")[0]

        # Short URLs: https://youtu.be/VIDEO_ID
        if "youtu.be/" in url:
            return url.split("youtu.be/")[1].split("?")[0]

        # Fallback: use hash of URL
        return hashlib.md5(url.encode()).hexdigest()[:16]

    def _extract_channel_id(self, channel_url: str) -> str:
        """Extract channel ID from YouTube channel URL."""
        if not channel_url:
            return ""

        # Channel URLs: https://www.youtube.com/channel/CHANNEL_ID
        if "/channel/" in channel_url:
            return channel_url.split("/channel/")[1].split("/")[0]

        # User URLs: https://www.youtube.com/@username
        if "/@" in channel_url:
            return channel_url.split("/@")[1].split("/")[0]

        # Fallback: use hash of URL
        return hashlib.md5(channel_url.encode()).hexdigest()[:16]

    def _parse_views(self, views_str) -> int:
        """Parse view count from string or int."""
        if isinstance(views_str, int):
            return views_str

        if not views_str:
            return 0

        # Remove commas and convert to int
        try:
            return int(str(views_str).replace(",", "").replace(" views", ""))
        except:
            return 0

    def _parse_date(self, date_str: str) -> datetime:
        """Parse date string to datetime object."""
        if not date_str:
            return None
        try:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except:
            return None

