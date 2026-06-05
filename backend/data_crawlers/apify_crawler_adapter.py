"""
Apify Crawler Adapter for InsightPulse
======================================

Modern adapter that integrates 2026_Crawler Apify-based crawlers
with InsightPulse's analysis system.

Author: InsightPulse Team
Date: 2026-02-07
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import pandas as pd
import requests
import time

logger = logging.getLogger(__name__)


class ApifyCrawlerAdapter:
    """
    Modern crawler adapter using Apify API for real-time data collection
    """
    
    def __init__(self):
        self.apify_token = os.getenv('APIFY_API_TOKEN')
        self.serpapi_key = os.getenv('SERPAPI_KEY')
        self.data_dir = Path("data/smart_crawlers")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Platform to crawler mapping
        self.crawler_map = {
            'facebook': 'facebook_crawler',
            'instagram': 'instagram_crawler',
            'twitter': 'twitter_crawler',
            'x': 'twitter_crawler',
            'tiktok': 'tiktok_crawler',
            'youtube': 'youtube_crawler',
            'google': 'google_news_crawler',
            'news': 'google_news_crawler',
            'linkedin': 'linkedin_posts_crawler',
            'shopee': 'shopee_crawler',
            'lazada': 'lazada_crawler',
            'reddit': 'reddit_crawler',
            'lowyat': None  # Not in 2026_Crawler, will use fallback
        }
        
        logger.info(f"✅ Apify Crawler Adapter initialized")
        logger.info(f"✅ Apify Token: {'✓ Configured' if self.apify_token else '✗ Missing'}")
        logger.info(f"✅ SerpAPI Key: {'✓ Configured' if self.serpapi_key else '✗ Missing'}")
    
    async def crawl_platform(
        self,
        platform: str,
        query: str,
        max_results: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Crawl a specific platform using Apify-based crawlers
        
        Args:
            platform: Platform name (facebook, instagram, etc.)
            query: Search query
            max_results: Maximum results to collect
            
        Returns:
            List of collected data records
        """
        try:
            logger.info(f"🔍 Starting Apify crawl for {platform}: '{query}'")
            
            crawler_module = self.crawler_map.get(platform)
            
            if not crawler_module:
                logger.warning(f"⚠️ No Apify crawler for {platform}, using fallback")
                return []
            
            # Import the crawler dynamically
            try:
                crawler_class = self._import_crawler(crawler_module)
            except Exception as e:
                logger.error(f"❌ Failed to import {crawler_module}: {e}")
                return []
            
            # Initialize and run crawler
            crawler = crawler_class()
            
            # Execute crawl
            results = await self._execute_crawler(
                crawler, platform, query, max_results
            )
            
            # Save results
            if results:
                self._save_results(platform, query, results)
                logger.info(f"✅ Collected {len(results)} records from {platform}")
            else:
                logger.warning(f"⚠️ No results from {platform}")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Error crawling {platform}: {e}")
            return []
    
    def _import_crawler(self, module_name: str):
        """Dynamically import crawler class"""
        # Import from platform_crawlers directory
        full_module_path = f"platform_crawlers.{module_name}"
        module = __import__(full_module_path, fromlist=[module_name])

        # Get the crawler class (usually named after the platform)
        class_map = {
            'facebook_crawler': 'FacebookCrawler',
            'instagram_crawler': 'InstagramCrawler',
            'twitter_crawler': 'TwitterCrawler',
            'tiktok_crawler': 'TikTokCrawler',
            'youtube_crawler': 'YouTubeCrawler',
            'google_news_crawler': 'GoogleNewsCrawler',
            'linkedin_posts_crawler': 'LinkedInPostsCrawler',
            'shopee_crawler': 'ShopeeCrawler',
            'lazada_crawler': 'LazadaCrawler',
            'reddit_crawler': 'RedditCrawler'
        }
        
        class_name = class_map.get(module_name)
        if not class_name:
            raise ValueError(f"Unknown crawler module: {module_name}")
        
        return getattr(module, class_name)
    
    async def _execute_crawler(
        self,
        crawler,
        platform: str,
        query: str,
        max_results: int
    ) -> List[Dict]:
        """Execute the crawler and return results"""
        try:
            # Most 2026_Crawler crawlers have a 'crawl' or 'fetch' method
            if hasattr(crawler, 'crawl'):
                results = await crawler.crawl(query, max_results=max_results)
            elif hasattr(crawler, 'fetch'):
                results = await crawler.fetch(query, max_results=max_results)
            elif hasattr(crawler, 'search'):
                results = await crawler.search(query, max_results=max_results)
            else:
                logger.error(f"❌ Crawler has no crawl/fetch/search method")
                return []
            
            return results if results else []
            
        except Exception as e:
            logger.error(f"❌ Crawler execution failed: {e}")
            return []

    def _save_results(self, platform: str, query: str, results: List[Dict]):
        """Save crawl results to CSV"""
        try:
            platform_dir = self.data_dir / platform
            platform_dir.mkdir(parents=True, exist_ok=True)

            # Create filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d")
            safe_query = query.replace(" ", "_").replace("/", "_")[:50]
            filename = f"{platform}_{safe_query}_{timestamp}.csv"
            filepath = platform_dir / filename

            # Convert to DataFrame and save
            df = pd.DataFrame(results)
            df.to_csv(filepath, index=False, encoding='utf-8')

            logger.info(f"💾 Saved {len(results)} records to {filepath}")

        except Exception as e:
            logger.error(f"❌ Error saving results: {e}")

    async def batch_crawl(
        self,
        platforms: List[str],
        query: str,
        max_results_per_platform: int = 100
    ) -> Dict[str, Any]:
        """
        Crawl multiple platforms concurrently

        Args:
            platforms: List of platform names
            query: Search query
            max_results_per_platform: Max results per platform

        Returns:
            Dict with results for each platform
        """
        try:
            logger.info(f"🚀 Starting batch crawl for {len(platforms)} platforms")

            # Create tasks for concurrent crawling
            tasks = []
            for platform in platforms:
                task = asyncio.create_task(
                    self.crawl_platform(platform, query, max_results_per_platform)
                )
                tasks.append((platform, task))

            # Execute all tasks concurrently
            results = {}
            for platform, task in tasks:
                try:
                    data = await task
                    results[platform] = {
                        'status': 'success' if data else 'no_data',
                        'data': data,
                        'count': len(data)
                    }
                except Exception as e:
                    logger.error(f"❌ Error in {platform} crawl: {e}")
                    results[platform] = {
                        'status': 'error',
                        'error': str(e),
                        'data': [],
                        'count': 0
                    }

            # Calculate summary
            total_records = sum(r['count'] for r in results.values())
            successful = sum(1 for r in results.values() if r['status'] == 'success')

            logger.info(f"✅ Batch crawl complete: {total_records} total records from {successful}/{len(platforms)} platforms")

            return {
                'status': 'completed',
                'total_platforms': len(platforms),
                'successful_platforms': successful,
                'total_records': total_records,
                'results': results,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"❌ Batch crawl failed: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'results': {}
            }


# Convenience functions
async def quick_crawl(platform: str, query: str, max_results: int = 100) -> List[Dict]:
    """Quick single platform crawl"""
    adapter = ApifyCrawlerAdapter()
    return await adapter.crawl_platform(platform, query, max_results)


async def multi_platform_crawl(platforms: List[str], query: str, max_results: int = 100) -> Dict:
    """Multi-platform concurrent crawl"""
    adapter = ApifyCrawlerAdapter()
    return await adapter.batch_crawl(platforms, query, max_results)

