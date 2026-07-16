"""Lowyat Forum crawler implementation using SerpAPI."""
from typing import Dict, Any, List
from datetime import datetime
import hashlib
import requests
import os
from loguru import logger

from .base_crawler import BaseCrawler


class LowyatCrawler(BaseCrawler):
    """
    Crawler for Lowyat Forum using SerpAPI Google Search.
    
    Lowyat.net is Malaysia's largest tech forum with discussions on:
    - Technology, gadgets, smartphones
    - Politics, current affairs
    - Malaysian issues and news
    
    Uses: SerpAPI Google Search with site:lowyat.net filter
    Cost: ~$0.005 per search (very cheap!)
    
    Features:
    - Search forum threads by keywords
    - Get thread metadata (title, URL, snippet)
    - Filter by Malaysian context
    - No Apify needed - uses SerpAPI directly
    """
    
    def __init__(self):
        super().__init__("lowyat")
        self.serpapi_key = os.getenv("SERPAPI_API_KEY") or os.getenv("SERPAPI_KEY")
        if not self.serpapi_key:
            logger.warning("SERPAPI_API_KEY or SERPAPI_KEY not found in environment")
    
    def prepare_input(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Prepare input for Lowyat forum search via SerpAPI.
        
        Args:
            query: Search query (e.g., "iPhone 15 review", "pilihan raya PBT")
            **kwargs: Additional parameters
                - max_results: Number of results (default: 100)
                - forum_section: Specific forum section (optional)
        """
        # Add site:lowyat.net to search only Lowyat forum
        search_query = f"site:lowyat.net {query}"
        
        # Add forum section filter if specified
        forum_section = kwargs.get("forum_section")
        if forum_section:
            search_query += f" inurl:{forum_section}"
        
        return {
            "engine": "google",
            "q": search_query,
            "num": kwargs.get("max_results", 100),
            "gl": "my",  # Malaysia
            "hl": "en",  # English interface
            "location": "Malaysia",
        }
    
    def crawl(self, query: str, **kwargs) -> List[Dict[str, Any]]:
        """
        Crawl Lowyat forum using SerpAPI.
        
        Returns:
            List of forum thread data
        """
        if not self.serpapi_key:
            logger.error("SERPAPI_API_KEY not configured")
            return []
        
        input_config = self.prepare_input(query, **kwargs)
        
        try:
            # Call SerpAPI
            response = requests.get(
                "https://serpapi.com/search",
                params={**input_config, "api_key": self.serpapi_key},
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            
            # Extract organic results
            results = data.get("organic_results", [])
            
            logger.info(f"✅ Lowyat: Found {len(results)} forum threads for '{query}'")
            return results
            
        except Exception as e:
            logger.error(f"❌ Lowyat crawl failed: {e}")
            return []
    
    def transform_data(self, raw_data: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Transform Lowyat forum data to database format.
        
        Lowyat threads are treated as "posts" with forum discussions as content.
        """
        posts = []
        
        for item in raw_data:
            # Generate unique post ID from URL
            url = item.get("link", "")
            post_id = hashlib.md5(url.encode()).hexdigest()[:16] if url else ""
            
            # Extract thread title and snippet
            title = item.get("title", "")
            snippet = item.get("snippet", "")
            content = f"{title}\n\n{snippet}"
            
            # Parse date if available
            date_str = item.get("date")
            created_at = self._parse_date(date_str) if date_str else datetime.now()
            
            # Create post data
            post_data = {
                "platform": self.platform,
                "post_id": post_id,
                "author_id": "lowyat_forum",
                "author_username": "Lowyat Forum",
                "author_name": "Lowyat Forum",
                "content": content,
                "url": url,
                "created_at": created_at,
                "likes_count": 0,  # Forum threads don't have likes
                "comments_count": 0,  # Would need to scrape thread to get reply count
                "shares_count": 0,
                "views_count": 0,
                "hashtags": [],
                "mentions": [],
                "media_urls": [],
                "metadata": {
                    "title": title,
                    "snippet": snippet,
                    "position": item.get("position", 0),
                }
            }
            posts.append(post_data)
        
        return {
            "posts": posts,
            "profiles": [],
            "comments": []
        }
    
    def _parse_date(self, date_str: str) -> datetime:
        """Parse date string to datetime."""
        try:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except:
            return datetime.now()

