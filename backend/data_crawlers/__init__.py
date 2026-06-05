"""
Data Crawlers Module for InsightPulse
====================================

This module provides intelligent data crawling capabilities by integrating
with the existing smart_crawlers system, offering:

- Multi-platform data collection (Facebook, Instagram, TikTok, Twitter, Google, News, Lowyat)
- Advanced Boolean OR query support
- Malay BERT sentiment analysis
- Intelligent keyword extraction
- Malaysian content optimization
- Concurrent crawling across platforms

Author: InsightPulse Team
"""

from .crawler_manager import CrawlerManager
from .smart_crawler_bridge import SmartCrawlerBridge, quick_crawl, multi_platform_crawl

__all__ = [
    'CrawlerManager',
    'SmartCrawlerBridge', 
    'quick_crawl',
    'multi_platform_crawl'
]

__version__ = "1.0.0"
