"""Google News crawler implementation using SerpAPI."""
from typing import Dict, Any, List
from datetime import datetime
import hashlib
import requests
import os
from loguru import logger

from .base_crawler import BaseCrawler


class GoogleNewsCrawler(BaseCrawler):
    """
    Crawler for Google News articles using SerpAPI.
    
    Uses: SerpAPI Google News Search
    Cost: ~$0.005 per search (very cheap!)
    
    Features:
    - Search news articles by keywords
    - Get article metadata (title, source, date, etc.)
    - Filter by location and language
    - No Apify needed - uses SerpAPI directly
    """
    
    def __init__(self):
        super().__init__("google_news")
        self.serpapi_key = os.getenv("SERPAPI_API_KEY") or os.getenv("SERPAPI_KEY")
        if not self.serpapi_key:
            logger.warning("SERPAPI_API_KEY or SERPAPI_KEY not found in environment")
    
    def prepare_input(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Prepare input for Google News search via SerpAPI.
        
        Args:
            query: Search keyword/phrase
            **kwargs: Additional options
                - max_results: Maximum articles to collect (default: 100)
                - location: Country code (default: 'my' for Malaysia)
                - language: Language code (default: 'en')
        
        Returns:
            Input configuration for SerpAPI
        """
        max_results = kwargs.get("max_results", kwargs.get("max_items", 100))
        location = kwargs.get("location", "my")  # Malaysia
        language = kwargs.get("language", "en")  # English
        
        logger.info(f"Google News search: '{query}', max_results={max_results}, location={location}")
        
        return {
            "engine": "google_news",
            "q": query,
            "api_key": self.serpapi_key,
            "gl": location,
            "hl": language,
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
            logger.info(f"Starting Google News crawl for: {query}")
            
            # Prepare search parameters
            params = self.prepare_input(query, **kwargs)
            
            # Make request to SerpAPI
            response = requests.get("https://serpapi.com/search", params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            news_results = data.get("news_results", [])
            
            logger.info(f"Found {len(news_results)} Google News articles")
            
            # Transform data
            transformed_data = self.transform_data(news_results)
            
            # Save to database
            items_saved = 0
            if save_to_db:
                items_saved = self.save_to_database(transformed_data)
                logger.info(f"Saved {items_saved} items to database")
            
            return {
                "platform": self.platform,
                "status": "completed",
                "items_collected": items_saved,
                "raw_data": news_results,
                "transformed_data": transformed_data
            }
            
        except Exception as e:
            logger.error(f"Error during Google News crawl: {e}")
            raise
    
    def transform_data(self, raw_data: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Transform Google News article data to database format.
        
        Args:
            raw_data: Raw data from SerpAPI
            
        Returns:
            Dictionary with 'posts' list
        """
        posts = []
        
        for item in raw_data:
            # Generate unique article ID from URL
            article_url = item.get("link", "")
            article_id = hashlib.md5(article_url.encode()).hexdigest()
            
            # Parse published date
            date_str = item.get("date", "")
            created_at = self._parse_date(date_str) if date_str else None
            
            # Extract source info
            source = item.get("source", {})
            source_name = source.get("name", "") if isinstance(source, dict) else str(source)
            
            post_data = {
                "platform": self.platform,
                "post_id": article_id,
                "author_id": hashlib.md5(source_name.encode()).hexdigest()[:16],
                "author_username": source_name,
                "author_name": source_name,
                "content": f"{item.get('title', '')}\n\n{item.get('snippet', '')}",
                "url": article_url,
                "created_at": created_at,
                "likes_count": 0,
                "comments_count": 0,
                "shares_count": 0,
                "views_count": 0,
                "hashtags": [],
                "mentions": [],
                "media_urls": [item.get("thumbnail", "")],
                "metadata": {
                    "title": item.get("title", ""),
                    "snippet": item.get("snippet", ""),
                    "source": source_name,
                    "thumbnail": item.get("thumbnail", ""),
                }
            }
            posts.append(post_data)
        
        logger.info(f"Transformed {len(posts)} Google News articles")
        return {"posts": posts}

    def _parse_date(self, date_str: str) -> datetime:
        """Parse date string to datetime object."""
        if not date_str:
            return None

        try:
            # Try ISO format
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except:
            try:
                # Try common date formats
                from dateutil import parser
                return parser.parse(date_str)
            except:
                return None

