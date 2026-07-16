#!/usr/bin/env python3
"""
Enhanced Multi-Platform Data Collection Framework
Latest Universal Social Listening Framework Implementation
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import aiohttp
import json
from datetime import datetime, timedelta
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PlatformType(Enum):
    """Enhanced platform types with latest additions"""
    # Core Social Platforms
    FACEBOOK = "facebook"
    TWITTER = "twitter"
    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"
    LINKEDIN = "linkedin"
    YOUTUBE = "youtube"
    
    # Extended Sources
    REDDIT = "reddit"
    DISCORD = "discord"
    TELEGRAM = "telegram"
    
    # Malaysian-specific platforms
    LOWYAT = "lowyat"
    MALAYSIAN_NEWS = "malaysian_news"
    
    # E-commerce platforms
    SHOPEE = "shopee"
    LAZADA = "lazada"
    
    # Web3 & Niche Communities
    BLOCKCHAIN_FORUMS = "blockchain_forums"
    INDUSTRY_FORUMS = "industry_forums"
    
    # News and Review Sites
    NEWS_OUTLETS = "news_outlets"
    REVIEW_SITES = "review_sites"

@dataclass
class CollectionResult:
    """Enhanced collection result with crisis detection"""
    platform: PlatformType
    query: str
    data: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    collection_time: datetime
    success: bool
    error_message: Optional[str] = None
    crisis_indicators: List[str] = None
    sentiment_summary: Dict[str, float] = None
    engagement_metrics: Dict[str, int] = None

class EnhancedDataCollector:
    """Enhanced universal data collector with latest framework features"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.session = None
        self.rate_limits = {}
        self.crisis_detector = CrisisDetector()
        self.real_time_processor = RealTimeProcessor()
        
        # Enhanced platform configurations
        self.platform_configs = {
            PlatformType.FACEBOOK: {
                "base_url": "https://graph.facebook.com/v18.0",
                "rate_limit": 200,  # requests per hour
                "data_fields": ["message", "created_time", "likes", "comments", "shares"],
                "crisis_monitoring": True
            },
            PlatformType.TWITTER: {
                "base_url": "https://api.twitter.com/2",
                "rate_limit": 300,
                "data_fields": ["text", "created_at", "public_metrics", "context_annotations"],
                "crisis_monitoring": True
            },
            PlatformType.INSTAGRAM: {
                "base_url": "https://graph.instagram.com",
                "rate_limit": 200,
                "data_fields": ["caption", "timestamp", "like_count", "comments_count"],
                "crisis_monitoring": True
            },
            PlatformType.TIKTOK: {
                "base_url": "https://open-api.tiktok.com",
                "rate_limit": 100,
                "data_fields": ["desc", "create_time", "statistics"],
                "crisis_monitoring": True
            },
            PlatformType.SHOPEE: {
                "base_url": "https://shopee.com.my/api/v4",
                "rate_limit": 150,
                "data_fields": ["name", "price", "rating", "review_count"],
                "crisis_monitoring": False
            },
            PlatformType.LAZADA: {
                "base_url": "https://www.lazada.com.my/api",
                "rate_limit": 150,
                "data_fields": ["title", "price", "rating", "reviews"],
                "crisis_monitoring": False
            },
            PlatformType.REDDIT: {
                "base_url": "https://www.reddit.com/api/v1",
                "rate_limit": 60,
                "data_fields": ["title", "selftext", "score", "num_comments"],
                "crisis_monitoring": True
            },
            PlatformType.LOWYAT: {
                "base_url": "https://forum.lowyat.net/api",
                "rate_limit": 100,
                "data_fields": ["title", "content", "replies", "views"],
                "crisis_monitoring": True
            }
        }
        
        # Industry-specific collection strategies
        self.industry_strategies = {
            "healthcare": {
                "priority_platforms": [PlatformType.FACEBOOK, PlatformType.REDDIT, PlatformType.NEWS_OUTLETS],
                "keywords_boost": ["patient", "treatment", "medical", "health"],
                "crisis_sensitivity": "high"
            },
            "financial": {
                "priority_platforms": [PlatformType.LINKEDIN, PlatformType.REDDIT, PlatformType.NEWS_OUTLETS],
                "keywords_boost": ["investment", "banking", "finance", "money"],
                "crisis_sensitivity": "very_high"
            },
            "retail": {
                "priority_platforms": [PlatformType.INSTAGRAM, PlatformType.TIKTOK, PlatformType.SHOPEE, PlatformType.LAZADA],
                "keywords_boost": ["product", "shopping", "review", "quality"],
                "crisis_sensitivity": "medium"
            }
        }
    
    async def initialize(self):
        """Initialize enhanced data collector"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={
                'User-Agent': 'InsightPulse-Enhanced/2.0 (Universal Social Listening)',
                'Accept': 'application/json'
            }
        )
        self.logger.info("Enhanced data collector initialized")
    
    async def collect_universal_data(
        self, 
        query: str, 
        platforms: List[PlatformType],
        industry_context: Optional[str] = None,
        crisis_monitoring: bool = True,
        real_time: bool = False
    ) -> Dict[PlatformType, CollectionResult]:
        """Enhanced universal data collection with latest framework features"""
        
        if not self.session:
            await self.initialize()
        
        # Apply industry-specific strategies
        if industry_context and industry_context in self.industry_strategies:
            strategy = self.industry_strategies[industry_context]
            platforms = self._optimize_platforms_for_industry(platforms, strategy)
            query = self._enhance_query_for_industry(query, strategy)
        
        # Collect data from all platforms concurrently
        tasks = []
        for platform in platforms:
            task = self._collect_from_platform(
                platform, query, crisis_monitoring, real_time
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results and detect cross-platform trends
        processed_results = {}
        for platform, result in zip(platforms, results):
            if isinstance(result, Exception):
                self.logger.error(f"Error collecting from {platform}: {result}")
                processed_results[platform] = CollectionResult(
                    platform=platform,
                    query=query,
                    data=[],
                    metadata={},
                    collection_time=datetime.now(),
                    success=False,
                    error_message=str(result)
                )
            else:
                processed_results[platform] = result
        
        # Cross-platform crisis detection
        if crisis_monitoring:
            await self._detect_cross_platform_crisis(processed_results)
        
        return processed_results
    
    async def _collect_from_platform(
        self, 
        platform: PlatformType, 
        query: str,
        crisis_monitoring: bool,
        real_time: bool
    ) -> CollectionResult:
        """Enhanced platform-specific data collection"""
        
        start_time = datetime.now()
        
        try:
            # Check rate limits
            if not self._check_rate_limit(platform):
                raise Exception(f"Rate limit exceeded for {platform}")
            
            # Get platform configuration
            config = self.platform_configs.get(platform, {})
            
            # Collect data based on platform type
            if platform in [PlatformType.FACEBOOK, PlatformType.INSTAGRAM]:
                data = await self._collect_meta_platforms(platform, query, config)
            elif platform == PlatformType.TWITTER:
                data = await self._collect_twitter(query, config)
            elif platform == PlatformType.TIKTOK:
                data = await self._collect_tiktok(query, config)
            elif platform in [PlatformType.SHOPEE, PlatformType.LAZADA]:
                data = await self._collect_ecommerce(platform, query, config)
            elif platform == PlatformType.REDDIT:
                data = await self._collect_reddit(query, config)
            elif platform == PlatformType.LOWYAT:
                data = await self._collect_lowyat(query, config)
            else:
                data = await self._collect_generic_platform(platform, query, config)
            
            # Process collected data
            processed_data = self._process_collected_data(data, platform)
            
            # Crisis detection for this platform
            crisis_indicators = []
            if crisis_monitoring and config.get("crisis_monitoring", False):
                crisis_indicators = await self.crisis_detector.analyze_platform_data(
                    processed_data, platform
                )
            
            # Calculate sentiment summary
            sentiment_summary = self._calculate_sentiment_summary(processed_data)
            
            # Calculate engagement metrics
            engagement_metrics = self._calculate_engagement_metrics(processed_data, platform)
            
            return CollectionResult(
                platform=platform,
                query=query,
                data=processed_data,
                metadata={
                    "collection_duration": (datetime.now() - start_time).total_seconds(),
                    "total_items": len(processed_data),
                    "platform_config": config
                },
                collection_time=start_time,
                success=True,
                crisis_indicators=crisis_indicators,
                sentiment_summary=sentiment_summary,
                engagement_metrics=engagement_metrics
            )
            
        except Exception as e:
            self.logger.error(f"Error collecting from {platform}: {e}")
            return CollectionResult(
                platform=platform,
                query=query,
                data=[],
                metadata={},
                collection_time=start_time,
                success=False,
                error_message=str(e)
            )

class CrisisDetector:
    """Crisis detection system for social listening"""
    
    def __init__(self):
        self.crisis_patterns = [
            "urgent", "emergency", "crisis", "scandal", "boycott",
            "lawsuit", "investigation", "fraud", "scam", "dangerous"
        ]
    
    async def analyze_platform_data(self, data: List[Dict], platform: PlatformType) -> List[str]:
        """Analyze platform data for crisis indicators"""
        indicators = []
        
        for item in data:
            text = item.get('text', '') or item.get('content', '') or item.get('message', '')
            text_lower = text.lower()
            
            for pattern in self.crisis_patterns:
                if pattern in text_lower:
                    indicators.append(f"Crisis keyword '{pattern}' detected")
        
        return indicators

class RealTimeProcessor:
    """Real-time data processing system"""
    
    def __init__(self):
        self.processing_queue = []
        self.active_streams = {}
    
    async def start_real_time_monitoring(self, query: str, platforms: List[PlatformType]):
        """Start real-time monitoring for specified platforms"""
        # Implementation for real-time streaming would go here
        pass

# Helper functions would be implemented here
# _collect_meta_platforms, _collect_twitter, etc.
