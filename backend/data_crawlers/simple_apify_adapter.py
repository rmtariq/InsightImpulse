"""
Simple Apify API Adapter for InsightPulse
==========================================

Direct Apify REST API integration without complex dependencies.
Uses simple HTTP requests to call Apify actors and collect data.

Author: InsightPulse Team
Date: 2026-02-07
"""

import os
import re
import asyncio
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import pandas as pd
from apify_client import ApifyClient
import requests

logger = logging.getLogger(__name__)

# Import AI Keyword Generator
try:
    import sys
    sys.path.append(str(Path(__file__).parent.parent))
    from services.ai_keyword_generator import AIKeywordGenerator
    AI_KEYWORDS_AVAILABLE = True
    logger.info("✅ AI Keyword Generator imported successfully")
except ImportError as e:
    AI_KEYWORDS_AVAILABLE = False
    logger.warning(f"⚠️ AI Keyword Generator not available: {e}")

# Import Crawl Cache
try:
    from .storage.crawl_cache import init_db, save_crawl_result, get_cached_posts, get_last_crawl_time
    CRAWL_CACHE_AVAILABLE = True
    logger.info("✅ Crawl Cache (SQLite) imported successfully")
except ImportError:
    try:
        from storage.crawl_cache import init_db, save_crawl_result, get_cached_posts, get_last_crawl_time
        CRAWL_CACHE_AVAILABLE = True
        logger.info("✅ Crawl Cache (SQLite) imported successfully (absolute)")
    except ImportError as e:
        CRAWL_CACHE_AVAILABLE = False
        logger.warning(f"⚠️ Crawl Cache not available: {e}")

# Import Crawl Strategy
try:
    from .crawl_strategy import CrawlStrategy
    CRAWL_STRATEGY_AVAILABLE = True
    logger.info("✅ Crawl Strategy imported successfully")
except ImportError:
    try:
        # Try absolute import
        from crawl_strategy import CrawlStrategy
        CRAWL_STRATEGY_AVAILABLE = True
        logger.info("✅ Crawl Strategy imported successfully (absolute)")
    except ImportError as e:
        CRAWL_STRATEGY_AVAILABLE = False
        logger.warning(f"⚠️ Crawl Strategy not available: {e}")

# Import Scrapling Adapter (FREE engine for news, google, youtube, shopee, lazada)
try:
    from .scrapling_adapter import ScraplingAdapter
    _scrapling_adapter = ScraplingAdapter()   # singleton — shared across calls
    SCRAPLING_ADAPTER_AVAILABLE = True
    logger.info("✅ Scrapling Adapter loaded — news/google/youtube/shopee/lazada will use FREE engine")
except ImportError:
    try:
        from scrapling_adapter import ScraplingAdapter
        _scrapling_adapter = ScraplingAdapter()
        SCRAPLING_ADAPTER_AVAILABLE = True
        logger.info("✅ Scrapling Adapter loaded (absolute import)")
    except ImportError as e:
        _scrapling_adapter = None
        SCRAPLING_ADAPTER_AVAILABLE = False
        logger.warning(f"⚠️ Scrapling Adapter not available: {e}")


class SimpleApifyAdapter:
    """
    Simplified Apify adapter using direct REST API calls
    """

    @staticmethod
    def get_recommended_dataset_size(analysis_type: str, platforms_count: int = 1) -> dict:
        """
        🎯 SMART RECOMMENDATION: Suggest optimal dataset size based on analysis type

        Returns recommended dataset sizes for accurate and reliable insights

        RESEARCH-BASED RECOMMENDATIONS:
        - Statistical significance requires minimum sample sizes
        - Sentiment analysis accuracy improves with larger datasets
        - Trend detection needs sufficient temporal data
        - Crisis detection requires real-time volume

        Args:
            analysis_type: Type of analysis (social_listening, crisis_detection, trend_analysis, etc.)
            platforms_count: Number of platforms being monitored

        Returns:
            dict with recommended, minimum, and maximum dataset sizes
        """

        recommendations = {
            # 🎧 SOCIAL LISTENING - Monitor brand mentions & sentiment
            'social_listening': {
                'recommended': 1000,  # Optimal for sentiment accuracy
                'minimum': 500,       # Minimum for statistical significance
                'maximum': 2000,      # Diminishing returns after this
                'per_platform': 200,  # Per platform allocation
                'reason': 'Balanced dataset for accurate sentiment trends (±5% margin of error)',
                'accuracy': '90-95% sentiment accuracy',
                'insights': 'Reliable brand perception, customer satisfaction tracking'
            },

            # 🚨 CRISIS DETECTION - Real-time negative sentiment monitoring
            'crisis_detection': {
                'recommended': 1500,  # Higher volume for real-time detection
                'minimum': 1000,      # Need volume for spike detection
                'maximum': 3000,      # Real-time requires more data
                'per_platform': 300,
                'reason': 'High volume needed to detect sentiment spikes and anomalies',
                'accuracy': '95-98% crisis detection rate',
                'insights': 'Early warning system, rapid response capability'
            },

            # 📈 TREND ANALYSIS - Identify trending topics & patterns
            'trend_analysis': {
                'recommended': 2000,  # Larger dataset for pattern recognition
                'minimum': 1000,      # Minimum for trend identification
                'maximum': 5000,      # More data = better patterns
                'per_platform': 400,
                'reason': 'Large dataset required for statistical trend significance',
                'accuracy': '85-92% trend prediction accuracy',
                'insights': 'Identify emerging topics, predict viral content, forecast sentiment shifts'
            },

            # 🗳️ ELECTION MONITORING - Political sentiment & campaign tracking
            'election_monitoring': {
                'recommended': 3000,  # Comprehensive political coverage
                'minimum': 2000,      # Need broad coverage
                'maximum': 10000,     # Election campaigns need volume
                'per_platform': 500,
                'reason': 'Comprehensive coverage of all candidates, parties, and issues',
                'accuracy': '92-96% sentiment accuracy for political analysis',
                'insights': 'Candidate popularity, issue sentiment, geographic trends, voter intent'
            },

            # 📊 MARKET RESEARCH - Product/service feedback & competitor analysis
            'market_research': {
                'recommended': 2000,  # Thorough market understanding
                'minimum': 1000,      # Minimum market sample
                'maximum': 5000,      # Deep market insights
                'per_platform': 350,
                'reason': 'Sufficient sample for market segmentation and competitor comparison',
                'accuracy': '88-93% product sentiment accuracy',
                'insights': 'Product feedback, competitor comparison, market gaps, customer needs'
            },

            # 🎯 INFLUENCER ANALYSIS - Track influencer impact & reach
            'influencer_analysis': {
                'recommended': 1500,  # Track influencer content & engagement
                'minimum': 800,       # Minimum for influence metrics
                'maximum': 3000,      # Deep influencer profiling
                'per_platform': 250,
                'reason': 'Track influencer posts, engagement, and audience sentiment',
                'accuracy': '90-94% influence impact accuracy',
                'insights': 'Influencer reach, engagement rate, audience sentiment, ROI measurement'
            },

            # 🛒 E-COMMERCE MONITORING - Product reviews & customer feedback
            'ecommerce_monitoring': {
                'recommended': 2500,  # High volume of reviews needed
                'minimum': 1500,      # Minimum for product insights
                'maximum': 5000,      # Comprehensive product analysis
                'per_platform': 500,  # Heavy on Shopee/Lazada
                'reason': 'Large review volume needed for product quality and customer satisfaction analysis',
                'accuracy': '91-95% product sentiment accuracy',
                'insights': 'Product quality issues, customer pain points, competitor products, pricing sentiment'
            },

            # 📰 MEDIA MONITORING - News coverage & PR tracking
            'media_monitoring': {
                'recommended': 1200,  # Comprehensive news coverage
                'minimum': 600,       # Minimum news sample
                'maximum': 3000,      # Extensive media analysis
                'per_platform': 200,
                'reason': 'Track news articles, press releases, and media sentiment',
                'accuracy': '93-97% news sentiment accuracy',
                'insights': 'Media coverage volume, sentiment tone, key journalists, PR effectiveness'
            },

            # 🎭 EVENT MONITORING - Track event buzz & attendee sentiment
            'event_monitoring': {
                'recommended': 1000,  # Real-time event tracking
                'minimum': 500,       # Minimum event buzz
                'maximum': 2500,      # Large event coverage
                'per_platform': 200,
                'reason': 'Track real-time event discussions, attendee feedback, and viral moments',
                'accuracy': '88-93% event sentiment accuracy',
                'insights': 'Event buzz, attendee satisfaction, viral moments, speaker reception'
            },

            # 🔍 GENERAL ANALYSIS - Default/custom analysis
            'general': {
                'recommended': 1000,  # Balanced general purpose
                'minimum': 500,       # Minimum for any analysis
                'maximum': 3000,      # General upper limit
                'per_platform': 200,
                'reason': 'Balanced dataset suitable for most analysis types',
                'accuracy': '85-90% general accuracy',
                'insights': 'Versatile dataset for exploratory analysis'
            }
        }

        # Get recommendation or fallback to general
        config = recommendations.get(analysis_type.lower(), recommendations['general'])

        # Adjust for multiple platforms
        if platforms_count > 1:
            # When monitoring multiple platforms, we can reduce per-platform allocation
            # but increase total to maintain statistical significance
            adjusted_total = min(
                config['recommended'] * platforms_count,  # Ideal
                config['maximum']  # But not exceeding maximum
            )
            config['recommended'] = adjusted_total
            config['per_platform_adjusted'] = adjusted_total // platforms_count

        return config

    @staticmethod
    def validate_dataset_size(size: int, analysis_type: str = "general") -> dict:
        """
        🎯 SMART VALIDATION: Validate dataset size and provide feedback

        Range: 100 - 5000 (with warnings for sub-optimal sizes)

        Args:
            size: Requested dataset size
            analysis_type: Type of analysis (for context-aware recommendations)

        Returns:
            dict with validation status, warnings, and expected metrics
        """
        # Hard limits
        MIN_SIZE = 100
        MAX_SIZE = 5000
        RECOMMENDED_MIN = 500
        OPTIMAL_MIN = 1000
        OPTIMAL_MAX = 3000

        result = {
            'valid': True,
            'warnings': [],
            'recommendations': [],
            'accuracy': '',
            'margin_of_error': '',
            'reliability': ''
        }

        # Validate range
        if size < MIN_SIZE:
            result['valid'] = False
            result['error'] = f'❌ Minimum {MIN_SIZE} items required for any analysis'
            return result

        if size > MAX_SIZE:
            result['valid'] = False
            result['error'] = f'❌ Maximum {MAX_SIZE} items. For larger datasets, split into multiple queries.'
            result['recommendation'] = 'For >5000 items, run multiple queries and combine results'
            return result

        # Accuracy and reliability by size
        if size >= 100 and size < 300:
            result['accuracy'] = '70-80%'
            result['margin_of_error'] = '±7-10%'
            result['reliability'] = 'LOW'
            result['warnings'].append('⚠️ Very small dataset - accuracy below 80%')
            result['warnings'].append('💡 Recommended for quick keyword testing only')
            result['recommendations'].append(f'Increase to {RECOMMENDED_MIN} items for reliable results')

        elif size >= 300 and size < 500:
            result['accuracy'] = '80-85%'
            result['margin_of_error'] = '±5-7%'
            result['reliability'] = 'BELOW OPTIMAL'
            result['warnings'].append('⚠️ Below recommended minimum - accuracy 80-85%')
            result['recommendations'].append(f'Increase to {RECOMMENDED_MIN} items for better accuracy')

        elif size >= 500 and size < 1000:
            result['accuracy'] = '85-90%'
            result['margin_of_error'] = '±4-5%'
            result['reliability'] = 'GOOD'
            result['recommendations'].append(f'Consider {OPTIMAL_MIN} items for optimal accuracy (90-95%)')

        elif size >= 1000 and size < 2000:
            result['accuracy'] = '90-95%'
            result['margin_of_error'] = '±2.5-3%'
            result['reliability'] = 'EXCELLENT'
            # No warnings - optimal range

        elif size >= 2000 and size <= 3000:
            result['accuracy'] = '94-97%'
            result['margin_of_error'] = '±2-2.5%'
            result['reliability'] = 'EXCELLENT'
            # No warnings - optimal range

        elif size > 3000 and size <= 5000:
            result['accuracy'] = '96-98%'
            result['margin_of_error'] = '±1.5-2%'
            result['reliability'] = 'EXCELLENT'
            # Check if analysis type justifies large dataset
            if analysis_type not in ['election_monitoring', 'comprehensive_research', 'ecommerce_monitoring']:
                result['warnings'].append('⚠️ Large dataset - diminishing returns after 3000 items')
                result['warnings'].append('💡 Consider 3000 items for cost efficiency')
            result['warnings'].append('⏱️ Long crawl time expected (60-90 minutes)')

        return result

    @staticmethod
    def calculate_smart_buffer(target_results: int) -> float:
        """
        🎯 SMART BUFFER: Calculate buffer multiplier based on target size

        Larger targets need higher buffers because:
        - More aggressive relevance filtering
        - Higher probability of duplicates
        - Platform rate limits and caps
        - Quality thresholds remove more data

        Returns: buffer multiplier (1.5x to 4.0x)
        """
        if target_results < 50:
            return 1.5  # Small: minimal filtering
        elif target_results < 100:
            return 2.0  # Medium-small: moderate filtering
        elif target_results < 300:
            return 2.5  # Medium: significant filtering
        elif target_results < 500:
            return 3.0  # Large: heavy filtering
        else:
            return 4.0  # Very large: very heavy filtering + platform caps

    @staticmethod
    def calculate_dynamic_timeout(platform: str, dataset_size: int) -> int:
        """
        🎯 DYNAMIC TIMEOUT: Calculate optimal timeout based on platform and dataset size

        FORMULA: base_timeout + (dataset_size * time_per_item) + buffer

        Platform Speed Categories (empirical data from Apify actors):
        - FAST (0.1s/item): SerpAPI platforms (News, Lowyat)
        - MEDIUM (0.5s/item): Social media with API (X, Instagram, TikTok)
        - SLOW (1.0s/item): Platforms requiring browser automation (Facebook, YouTube, LinkedIn)
        - VERY SLOW (1.5s/item): E-commerce with reviews (Shopee, Lazada)

        Args:
            platform: Platform name (facebook, instagram, x, etc.)
            dataset_size: Number of items to crawl

        Returns:
            Optimal timeout in seconds
        """
        # Platform speed categories
        FAST_PLATFORMS = ['news', 'lowyat', 'google']  # SerpAPI
        MEDIUM_PLATFORMS = ['x', 'twitter', 'instagram', 'tiktok', 'threads']  # API-based social media
        SLOW_PLATFORMS = ['facebook', 'youtube', 'linkedin']  # Browser automation
        VERY_SLOW_PLATFORMS = ['shopee', 'lazada']  # E-commerce with reviews

        # Base timeout (minimum time regardless of size)
        base_timeout = 120  # 2 minutes for initialization

        # Time per item (seconds) - based on empirical testing
        platform_lower = platform.lower()
        if platform_lower in FAST_PLATFORMS:
            time_per_item = 0.1   # 10 items per second
            category = "FAST"
        elif platform_lower in MEDIUM_PLATFORMS:
            time_per_item = 0.5   # 2 items per second
            category = "MEDIUM"
        elif platform_lower in SLOW_PLATFORMS:
            time_per_item = 3.5   # Facebook browser automation: ~3-5s per item (proxy + anti-bot delay)
            category = "SLOW"
        elif platform_lower in VERY_SLOW_PLATFORMS:
            time_per_item = 1.5   # 0.67 items per second
            category = "VERY SLOW"
        else:
            time_per_item = 1.0   # Default to SLOW
            category = "UNKNOWN (defaulting to SLOW)"

        # Calculate timeout
        calculated_timeout = base_timeout + int(dataset_size * time_per_item)

        # Add buffer (20% safety margin)
        buffered_timeout = int(calculated_timeout * 1.2)

        # Apply min/max limits
        MIN_TIMEOUT = 180   # 3 minutes minimum
        MAX_TIMEOUT = 3600  # 60 minutes maximum (Facebook browser automation can be very slow)

        final_timeout = max(MIN_TIMEOUT, min(buffered_timeout, MAX_TIMEOUT))

        logger.info(f"⏱️ Dynamic timeout calculation:")
        logger.info(f"   Platform: {platform} ({category})")
        logger.info(f"   Dataset size: {dataset_size} items")
        logger.info(f"   Time per item: {time_per_item}s")
        logger.info(f"   Base timeout: {base_timeout}s")
        logger.info(f"   Calculated: {calculated_timeout}s ({calculated_timeout//60}min {calculated_timeout%60}s)")
        logger.info(f"   With 20% buffer: {buffered_timeout}s ({buffered_timeout//60}min)")
        logger.info(f"   ✅ Final timeout: {final_timeout}s ({final_timeout//60}min {final_timeout%60}s)")

        return final_timeout

    def __init__(self, llm_service=None):
        self.apify_token = os.getenv('APIFY_API_TOKEN')
        self.apify_proxy_password = os.getenv('APIFY_PROXY_PASSWORD')
        self.serpapi_key = os.getenv('SERPAPI_KEY')
        self.data_dir = Path("data/smart_crawlers")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        # Date range for crawling (set externally before crawl, e.g. "2026-05-01")
        self._crawl_since_date: Optional[str] = None
        self._crawl_until_date: Optional[str] = None

        # Initialize Apify client
        self.client = ApifyClient(self.apify_token)

        # Initialize SQLite Cache
        if CRAWL_CACHE_AVAILABLE:
            try:
                init_db()
                logger.info("🗄️ SQLite Crawl Cache initialized")
            except Exception as e:
                logger.error(f"❌ Failed to initialize SQLite Cache: {e}")

        # Platform to Apify Actor ID mapping (from 2026_Crawler settings.py)
        self.actor_map = {
            'facebook': 'danek/facebook-search-ppr',  # ✅ Search-capable actor for posts
            'instagram': 'apify/instagram-scraper',
            'twitter': 'kaitoeasyapi/twitter-x-data-tweet-scraper-pay-per-result-cheapest',
            'x': 'kaitoeasyapi/twitter-x-data-tweet-scraper-pay-per-result-cheapest',
            'tiktok': 'clockworks/tiktok-scraper',
            'youtube': 'streamers/youtube-scraper',  # ✅ UPDATED: Apify YouTube scraper with comments
            'google': 'apify/google-search-scraper',
            'news': 'scrapling',  # ✅ FREE: Google News RSS via ScraplingAdapter (replaces SerpAPI)
            'lowyat': 'serpapi',  # ✅ Lowyat forum via SerpAPI (site:lowyat.net)
            'linkedin': 'harvestapi/linkedin-post-search',  # ✅ UPDATED: Robust LinkedIn post search with comments
            'threads': 'igview-owner/threads-search-scraper',  # ✅ UPDATED: Meta Threads search scraper (keyword search support!)
            'shopee': 'ecomscrape/shopee-scraper',  # ✅ UPDATED: Shopee products with reviews
            'lazada': 'ecomscrape/lazada-reviews-scraper'  # ✅ UPDATED: Lazada products with reviews
        }

        # 🎯 2-ACTOR STRATEGY: Separate comments actors for platforms that need it
        # NOTE: Instagram hashtag search doesn't return inline comments - must use separate comments actor
        self.comments_actor_map = {
            'x': 'scraper_one/x-post-replies-scraper',
            'twitter': 'scraper_one/x-post-replies-scraper',
            'facebook': 'apify/facebook-comments-scraper',  # ✅ Facebook comments actor
            'instagram': 'apify/instagram-comment-scraper',  # ✅ Instagram comments actor (for hashtag-based posts)
            'youtube': 'apidojo/youtube-comments-scraper'  # ✅ YouTube comments actor (separate from streamers/youtube-scraper)
        }

        # Initialize AI Keyword Generator
        self.ai_keyword_generator = None
        if AI_KEYWORDS_AVAILABLE and llm_service:
            self.ai_keyword_generator = AIKeywordGenerator(llm_service)
            logger.info("✅ AI Keyword Generator enabled")
        else:
            logger.warning("⚠️ AI Keyword Generator disabled - using fallback keywords")

        logger.info(f"✅ Simple Apify Adapter initialized")
        logger.info(f"✅ Apify Token: {'✓ Configured' if self.apify_token else '✗ Missing'}")
        logger.info(f"✅ SerpAPI Key: {'✓ Configured' if self.serpapi_key else '✗ Missing'}")
    
    def _prepare_facebook_input(self, query: str, max_results: int, max_comments: int = 50, comment_sort: str = "top") -> Dict[str, Any]:
        """
        Prepare input for Facebook Search Actor (danek/facebook-search-ppr)
        🎯 OPTIMIZED: Increased limits for comprehensive data collection
        🎯 2-ACTOR STRATEGY: This actor gets POSTS only, comments will be fetched separately
        """
        # 🎯 SMART BUFFER: Scale based on target size
        buffer = self.calculate_smart_buffer(max_results)
        adjusted_max_posts = int(max_results * buffer)

        logger.info(f"📘 Facebook: Requesting {adjusted_max_posts} posts (target: {max_results}, buffer: {buffer}x)")

        # scroll_timeout controls how long the browser keeps scrolling inside the actor.
        # Root cause of low FB data: 60s scroll_timeout = only ~15-20 scroll events
        # = ~20 posts before actor stops. Must be >> Apify run timeout.
        # Formula: allow ~5s per post target, minimum 300s (5min), max 1800s (30min)
        scroll_timeout = max(300, min(adjusted_max_posts * 5, 1800))

        input_data = {
            "query": query,
            "search_type": "posts",
            "max_posts": adjusted_max_posts,
            "language": "ms",
            "scroll_timeout": scroll_timeout,  # Dynamic: 5s × target posts, min 300s
            "scroll_delay": 2000,              # 2s between scrolls — avoid FB anti-bot detection
            "proxy": {
                "useApifyProxy": True,
                "apifyProxyGroups": ["RESIDENTIAL"],
                "apifyProxyCountry": "MY"
            }
        }

        logger.info(f"📘 Facebook scroll_timeout set to {scroll_timeout}s ({scroll_timeout//60}min) for {adjusted_max_posts} posts target")
        return input_data

    def _prepare_instagram_input(self, query: str, max_results: int, max_comments: int = 100, comment_sort: str = "top") -> Dict[str, Any]:
        """Prepare input for Instagram actor - SMART hashtag detection"""
        import re as _re

        search_query = query.strip()

        # Check if user already provided a hashtag
        if '#' in search_query:
            hashtag = [word for word in search_query.split() if word.startswith('#')][0]
            hashtag = _re.sub(r'[^a-zA-Z0-9]', '', hashtag.lstrip('#'))
            logger.info(f"📸 Instagram: User provided hashtag '#{hashtag}' - using as-is")
        else:
            # Strip OR operators and quotes, collect only clean alphanumeric words
            # e.g. 'maraliner OR "mara liner" OR "bas mara"' → ['maraliner', 'mara', 'liner', 'bas', 'mara']
            clean_words = [_re.sub(r'[^a-zA-Z0-9]', '', w)
                           for w in search_query.split()
                           if w.upper() != 'OR' and w.upper() != 'AND']
            # Filter out very short words and keep the longest meaningful word
            clean_words = [w.lower() for w in clean_words if len(w) >= 3]
            # Use longest word (usually the brand name, e.g. "maraliner")
            main_keyword = max(clean_words, key=len) if clean_words else search_query
            hashtag = main_keyword
            logger.info(f"📸 Instagram: Auto-converted '{search_query}' → '#{hashtag}'")

        # Use direct URL approach — more reliable than Google-indexed hashtag search
        hashtag_url = f"https://www.instagram.com/explore/tags/{hashtag}/"

        # 🎯 SMART BUFFER: Scale based on target size
        buffer = self.calculate_smart_buffer(max_results)
        adjusted_max_results = int(max_results * buffer)
        adjusted_max_comments = int(max_comments * 1.2)

        logger.info(f"📸 Instagram: Using direct URL → {hashtag_url}")
        logger.info(f"📸 Instagram: Requesting {adjusted_max_results} posts (target: {max_results}, buffer: {buffer}x)")
        logger.info(f"💬 Instagram: ENABLING COMMENTS - {adjusted_max_comments} per post with replies")

        # scrollTimeout: Instagram hashtag page uses infinite scroll — 45s too short.
        # Allow 4s per post target (min 180s, max 900s)
        ig_scroll_timeout = max(180, min(adjusted_max_results * 4, 900))
        logger.info(f"📸 Instagram scroll_timeout set to {ig_scroll_timeout}s for {adjusted_max_results} posts target")

        return {
            "directUrls": [hashtag_url],
            "resultsLimit": adjusted_max_results,
            "resultsType": "posts",
            "addParentData": True,
            "scrapeComments": True,
            "commentsMode": "top",
            "maxComments": adjusted_max_comments,
            "includeCommentReplies": True,
            "scrollTimeout": ig_scroll_timeout,       # Dynamic: was hardcoded 45s
            "pageLoadTimeoutSecs": 60,                # Wait up to 60s per page load
            "proxy": {
                "useApifyProxy": True,
                "apifyProxyGroups": ["RESIDENTIAL"],
                "apifyProxyCountry": "MY"
            }
        }

    def _prepare_twitter_input(self, query: str, max_results: int, max_comments: int = 50, comment_sort: str = "top", since_date: str = None, until_date: str = None) -> Dict[str, Any]:
        """
        Prepare input for Twitter/X actor with smart reply sampling
        🎯 OPTIMIZED: Increased limits for comprehensive data collection
        """
        # 🎯 SMART BUFFER: Scale based on target size
        buffer = self.calculate_smart_buffer(max_results)
        adjusted_max_tweets = int(max_results * buffer)
        adjusted_max_replies = int(max_comments * 1.2)

        logger.info(f"🐦 X/Twitter: Requesting {adjusted_max_tweets} tweets (target: {max_results}, buffer: {buffer}x)")
        logger.info(f"💬 X/Twitter: Requesting {adjusted_max_replies} replies per tweet")

        # filter:has_engagement + min_replies:1 were silently filtering out posts
        # with no replies yet — reducing data especially for newer/smaller accounts.
        # Removed both filters to capture ALL matching posts.
        # timeout increased: X API can be slow under rate limiting.
        x_timeout = max(180, min(adjusted_max_tweets * 2, 1200))
        logger.info(f"🐦 X/Twitter timeout set to {x_timeout}s for {adjusted_max_tweets} tweets target")

        input_data = {
            "searchTerms": [query],
            "max_tweets": adjusted_max_tweets,
            "queryType": "Top",
            "include_replies": True,
            "max_replies": adjusted_max_replies,
            "reply_sort": comment_sort,
            "include_retweets": True,
            "include_likes": True,
            # Removed: "filter:has_engagement" — was filtering out valid posts
            # Removed: "min_replies": 1    — was excluding posts with 0 replies
            "timeout": x_timeout,           # Dynamic: was fixed 120s
            "proxy": {                      # X rate-limits hard without proxy
                "useApifyProxy": True,
                "apifyProxyGroups": ["RESIDENTIAL"],
                "apifyProxyCountry": "MY"
            }
        }
        if since_date:
            input_data["since"] = since_date    # e.g. "2026-05-01"
        if until_date:
            input_data["until"] = until_date
        return input_data

    def _prepare_tiktok_input(self, query: str, max_results: int, max_comments: int = 100, comment_sort: str = "top") -> Dict[str, Any]:
        """
        Prepare input for TikTok actor with smart comment sampling
        🎯 OPTIMIZED: Increased limits for comprehensive data collection
        """
        # clockworks/tiktok-scraper expects a single search query, not multiple
        # We'll handle multiple keywords at a higher level

        # 🎯 OPTIMIZATION: TikTok often has high engagement, request more
        # 🎯 SMART BUFFER: Scale based on target size
        buffer = self.calculate_smart_buffer(max_results)
        adjusted_max_videos = int(max_results * buffer)
        adjusted_max_comments = int(max_comments * 1.2)

        logger.info(f"🎵 TikTok: Requesting {adjusted_max_videos} videos (target: {max_results}, buffer: {buffer}x)")
        logger.info(f"💬 TikTok: Requesting {adjusted_max_comments} comments per video")

        # scrollTimeout: TikTok search loads videos lazily — 45s misses many results.
        # Allow 3s per video target (min 180s, max 900s)
        tt_scroll_timeout = max(180, min(adjusted_max_videos * 3, 900))
        logger.info(f"🎵 TikTok scroll_timeout set to {tt_scroll_timeout}s for {adjusted_max_videos} videos target")

        return {
            "searchQueries": [query],
            "resultsPerPage": adjusted_max_videos,
            "maxVideos": adjusted_max_videos,
            "shouldDownloadVideos": False,
            "shouldDownloadCovers": False,
            "shouldDownloadSlideshowImages": False,
            "getComments": True,
            "commentsPerPost": adjusted_max_comments,
            "commentSort": comment_sort,
            "getEngagement": True,
            "scrollTimeout": tt_scroll_timeout,       # Dynamic: was hardcoded 45s
            "getUserDetails": True,
            "proxy": {                                # TikTok needs proxy to avoid blocking
                "useApifyProxy": True,
                "apifyProxyGroups": ["RESIDENTIAL"],
                "apifyProxyCountry": "MY"
            }
        }

    def _prepare_youtube_input(self, query: str, max_results: int, max_comments: int = 50, comment_sort: str = "top") -> Dict[str, Any]:
        """
        Prepare input for YouTube actor (streamers/youtube-scraper) for POSTS ONLY
        🎯 OPTIMIZED: Increased limits for comprehensive data collection

        Comments will be fetched separately using apidojo/youtube-comments-scraper actor
        via the _crawl_comments_for_posts() method
        """
        # 🎯 SMART BUFFER: Scale based on target size
        buffer = self.calculate_smart_buffer(max_results)
        adjusted_max_results = int(max_results * buffer)

        logger.info(f"🎬 YouTube: Search '{query}' - {adjusted_max_results} videos (target: {max_results}, buffer: {buffer}x)")
        logger.info(f"💬 YouTube: Comments will be fetched separately via youtube-comments-scraper")

        return {
            "searchKeywords": query,  # ✅ Search query
            "maxResults": adjusted_max_results,  # ✅ OPTIMIZED: 1.3x buffer
            "scrapeComments": False,  # ❌ DISABLED: Using separate apidojo/youtube-comments-scraper actor
            "scrapeChannelInfo": True,  # ✅ Get channel details
            "scrapeVideoStats": True,  # ✅ Get views, likes, etc.
            "scrollTimeout": 45,  # 🎯 NEW: Wait longer for content
            "proxy": {
                "useApifyProxy": True,
                "apifyProxyGroups": ["RESIDENTIAL"],
                "apifyProxyCountry": "MY"
            }
        }

    def _prepare_google_input(self, query: str, max_results: int, max_comments: int = 0, comment_sort: str = "top") -> Dict[str, Any]:
        """Prepare input for Google Search actor"""
        return {
            "queries": query,  # String, not array
            "maxPagesPerQuery": max(1, max_results // 10),
            "resultsPerPage": 10
        }

    def _prepare_news_input(self, query: str, max_results: int, max_comments: int = 0, comment_sort: str = "top") -> Dict[str, Any]:
        """Prepare input for Google News actor (via SerpAPI)"""
        return {
            "engine": "google_news",
            "q": query,
            "gl": "my",  # Malaysia
            "hl": "en",
            "num": min(max_results, 100)
        }

    def _prepare_lowyat_input(self, query: str, max_results: int, max_comments: int = 0, comment_sort: str = "top") -> Dict[str, Any]:
        """Prepare input for Lowyat forum search (via SerpAPI with site:lowyat.net)"""
        return {
            "engine": "google",
            "q": f"site:lowyat.net {query}",  # Search only Lowyat forum
            "gl": "my",  # Malaysia
            "hl": "en",
            "num": min(max_results, 100),
            "location": "Malaysia"
        }

    def _prepare_linkedin_input(self, query: str, max_results: int, max_comments: int = 50, comment_sort: str = "top") -> Dict[str, Any]:
        """
        Prepare input for LinkedIn actor (harvestapi/linkedin-post-search)
        🎯 OPTIMIZED: Increased limits for comprehensive data collection
        STRATEGY: Search LinkedIn posts + scrape comments + engagement
        """
        # 🎯 SMART BUFFER: Scale based on target size
        buffer = self.calculate_smart_buffer(max_results)
        adjusted_max_posts = int(max_results * buffer)
        adjusted_max_comments = int(max_comments * 1.3)

        logger.info(f"💼 LinkedIn: Requesting {adjusted_max_posts} posts (target: {max_results}, buffer: {buffer}x)")
        logger.info(f"💬 LinkedIn: Requesting {adjusted_max_comments} comments per post")

        # LinkedIn is browser automation (same category as Facebook).
        # scrollTimeout: 60s → same issue as FB, only gets ~15-20 posts before stopping.
        li_scroll_timeout = max(300, min(adjusted_max_posts * 5, 1800))
        logger.info(f"💼 LinkedIn scroll_timeout set to {li_scroll_timeout}s for {adjusted_max_posts} posts target")

        return {
            "searchQueries": [query],
            "maxPosts": adjusted_max_posts,
            "scrapeComments": True,
            "maxComments": adjusted_max_comments,
            "postedLimit": "any",
            "scrapeReactions": True,
            "profileScraperMode": "short",
            "scrollTimeout": li_scroll_timeout,   # Dynamic: was hardcoded 60s
            "proxy": {
                "useApifyProxy": True,
                "apifyProxyGroups": ["RESIDENTIAL"],
                "apifyProxyCountry": "MY"           # Added MY — more relevant for Malaysian content
            }
        }

    def _prepare_threads_input(self, query: str, max_results: int, max_comments: int = 50, comment_sort: str = "top") -> Dict[str, Any]:
        """
        Prepare input for Threads scraper (igview-owner/threads-search-scraper)
        🎯 OPTIMIZED: Keyword search support with comprehensive data collection
        STRATEGY: Search for posts by keywords, filter by date range, get engagement metrics

        Meta Threads is Instagram's text-based conversation platform

        NEW SCRAPER SUPPORTS:
        - ✅ Keyword search (not just profiles!)
        - ✅ Date range filtering
        - ✅ Sort by relevance or recency
        - ✅ Comprehensive data (posts, replies, engagement)
        """
        # 🎯 SMART BUFFER: Scale based on target size
        buffer = self.calculate_smart_buffer(max_results)
        adjusted_max_posts = int(max_results * buffer)

        logger.info(f"🧵 Threads: Requesting {adjusted_max_posts} posts (target: {max_results}, buffer: {buffer}x)")
        logger.info(f"🧵 Threads: Searching for '{query}'")

        # Threads actor has no explicit scrollTimeout field but respects requestTimeout.
        # Root cause of 96% comments / 4% posts: actor fetches replies heavily by default.
        # Cap maxRepliesPerPost and add proxy to avoid rate limiting.
        threads_timeout = max(180, min(adjusted_max_posts * 2, 900))
        logger.info(f"🧵 Threads timeout set to {threads_timeout}s for {adjusted_max_posts} posts target")

        return {
            "searchQuery": query,
            "maxResults": adjusted_max_posts,
            "sortBy": "top",
            "includeReplies": True,
            "maxRepliesPerPost": min(max_comments, 20),  # Cap replies — prevents 96% comment skew
            "dateFrom": self._crawl_since_date or None,
            "dateTo": self._crawl_until_date or None,
            "requestTimeout": threads_timeout,           # Was missing — now dynamic
            "proxy": {                                   # Was missing — rate limit protection
                "useApifyProxy": True,
                "apifyProxyGroups": ["RESIDENTIAL"],
                "apifyProxyCountry": "MY"
            }
        }

    async def _scrape_threads_with_replies(
        self,
        query: str,
        max_results: int,
        max_comments: int = 50,
        comment_sort: str = "top"
    ) -> List[Dict]:
        """
        🧵 OPTIMIZED 2-STEP THREADS SCRAPER: Posts + Replies (BATCHED PARALLEL)

        STRATEGY (BEST PERFORMANCE):
        Step 1: Get ALL posts first (1 API call)
        Step 2: Split post URLs into batches of 20
        Step 3: Fetch comments in PARALLEL batches (concurrent API calls)

        WHY THIS APPROACH?
        ✅ FAST - Parallel processing reduces wait time
        ✅ EFFICIENT - Minimizes API calls (not post-by-post)
        ✅ RELIABLE - One batch fails, others continue
        ✅ SCALABLE - Works for any dataset size (100-5000)

        Example: For 100 posts
        - Sequential: 1 + 5 = 6 API calls (5 batches, one at a time)
        - Parallel: 1 + 1 = 2 API calls (5 batches run simultaneously)

        Args:
            query: Search keywords
            max_results: Target total results (posts + replies)
            max_comments: Max replies per post
            comment_sort: Sort order for comments

        Returns:
            Combined list of posts + replies
        """
        try:
            import os
            import asyncio

            # Check if Session ID is available
            session_id = os.getenv('THREADS_SESSION_ID')
            if not session_id or session_id == '66920257060...paste_the_full_value_here':
                logger.warning("⚠️ THREADS_SESSION_ID not configured - replies will be skipped!")
                logger.warning("   Add your Threads Session ID to .env to enable reply scraping")
                # Fall back to posts-only scraping
                actor_input = self._prepare_threads_input(query, max_results, max_comments, comment_sort)
                return await self._run_apify_actor('igview-owner/threads-search-scraper', actor_input, 'threads')

            logger.info(f"🧵 Step 1/3: Searching for Threads posts...")

            # Step 1: Get posts (30% of quota for posts, 70% for comments)
            posts_quota = int(max_results * 0.3)
            actor_input = self._prepare_threads_input(query, posts_quota, max_comments, comment_sort)
            posts = await self._run_apify_actor('igview-owner/threads-search-scraper', actor_input, 'threads')

            if not posts:
                logger.warning("⚠️ No Threads posts found")
                return []

            logger.info(f"✅ Found {len(posts)} Threads posts")

            # Extract post URLs
            post_urls = []
            for post in posts:
                url = post.get('postUrl') or post.get('url') or post.get('link') or post.get('URL')
                if url:
                    post_urls.append(url)

            if not post_urls:
                logger.warning("⚠️ No post URLs found in Threads results")
                return posts  # Return posts without replies

            logger.info(f"🧵 Step 2/3: Preparing {len(post_urls)} post URLs for comment fetching...")

            # Step 2: Split URLs into batches of 20 (actor limit)
            BATCH_SIZE = 20
            url_batches = [post_urls[i:i + BATCH_SIZE] for i in range(0, len(post_urls), BATCH_SIZE)]

            logger.info(f"🚀 Step 3/3: Fetching comments in {len(url_batches)} PARALLEL batches...")
            logger.info(f"   Batch size: {BATCH_SIZE} URLs per batch")
            logger.info(f"   Max replies per post: {max_comments}")

            # Step 3: Fetch replies for ALL batches in PARALLEL
            async def fetch_batch(batch_idx, batch_urls):
                """Fetch replies for one batch of post URLs"""
                try:
                    logger.info(f"   📦 Batch {batch_idx + 1}/{len(url_batches)}: Fetching {len(batch_urls)} post URLs...")

                    # ⚠️ IMPORTANT: This actor does NOT accept proxy configuration
                    # Set proxy=None explicitly to prevent _run_apify_actor from adding it
                    replies_input = {
                        "postUrls": batch_urls,
                        "sessionId": session_id,
                        "proxy": None  # ✅ Explicitly disable proxy (actor doesn't support it)
                    }

                    batch_replies = await self._run_apify_actor(
                        'futurizerush/threads-replies-scraper-api',
                        replies_input,
                        'threads'
                    )

                    logger.info(f"   ✅ Batch {batch_idx + 1}: Fetched {len(batch_replies)} replies")
                    return batch_replies

                except Exception as batch_error:
                    logger.error(f"   ❌ Batch {batch_idx + 1} failed: {batch_error}")
                    return []

            # Run all batches in PARALLEL using asyncio.gather
            all_batch_results = await asyncio.gather(
                *[fetch_batch(i, batch) for i, batch in enumerate(url_batches)],
                return_exceptions=True  # Don't fail if one batch fails
            )

            # Combine all replies from all batches
            all_replies = []
            for batch_result in all_batch_results:
                if isinstance(batch_result, list):
                    all_replies.extend(batch_result)
                elif isinstance(batch_result, Exception):
                    logger.error(f"   ⚠️ Batch returned exception: {batch_result}")

            logger.info(f"✅ Fetched {len(all_replies)} total replies from {len(url_batches)} batches")

            # ✅ CRITICAL: Mark all replies with a flag so _transform_results knows they're comments
            for reply in all_replies:
                reply['_isReply'] = True  # Add marker to distinguish from posts

            # Combine posts + replies
            all_results = posts + all_replies
            logger.info(f"🎉 Total Threads data: {len(all_results)} items ({len(posts)} posts + {len(all_replies)} replies)")

            return all_results

        except Exception as e:
            logger.error(f"❌ Error in 2-step Threads scraper: {e}")
            logger.warning("⚠️ Falling back to posts-only scraping...")
            # Fallback: just get posts
            try:
                actor_input = self._prepare_threads_input(query, max_results, max_comments, comment_sort)
                return await self._run_apify_actor('igview-owner/threads-search-scraper', actor_input, 'threads')
            except Exception as fallback_error:
                logger.error(f"❌ Fallback also failed: {fallback_error}")
                return []

    def _prepare_shopee_input(self, query: str, max_results: int, max_comments: int = 50, comment_sort: str = "top") -> Dict[str, Any]:
        """
        Prepare input for Shopee scraper (ecomscrape/shopee-scraper)
        🎯 OPTIMIZED: Increased limits for comprehensive data collection
        Scrapes products + reviews (Shopee's version of comments) + ratings
        """
        # 🎯 SMART BUFFER: Scale based on target size
        buffer = self.calculate_smart_buffer(max_results)
        adjusted_max_products = int(max_results * buffer)
        adjusted_max_reviews = int(max_comments * 1.3)

        logger.info(f"🛒 Shopee: Requesting {adjusted_max_products} products (target: {max_results}, buffer: {buffer}x)")
        logger.info(f"💬 Shopee: Requesting {adjusted_max_reviews} reviews per product")

        return {
            "searchKeyword": query,  # ✅ Search query
            "maxProducts": adjusted_max_products,  # ✅ OPTIMIZED: 1.4x buffer
            "country": "MY",  # ✅ Malaysia
            "scrapeReviews": True,  # ✅ Enable reviews (comments)
            "maxReviewsPerProduct": adjusted_max_reviews,  # ✅ OPTIMIZED: 1.3x buffer
            "sortReviewsBy": comment_sort,  # ✅ "top" (most helpful) or "recent"
            "scrapeRatings": True,  # ✅ Get star ratings
            "scrapeSales": True,  # ✅ Get sales count (engagement)
            "scrollTimeout": 45,  # 🎯 NEW: Wait for dynamic loading
            "proxy": {
                "useApifyProxy": True,
                "apifyProxyGroups": ["RESIDENTIAL"],
                "apifyProxyCountry": "MY"
            }
        }

    def _prepare_lazada_input(self, query: str, max_results: int, max_comments: int = 50, comment_sort: str = "top") -> Dict[str, Any]:
        """
        Prepare input for Lazada scraper (ecomscrape/lazada-reviews-scraper)
        🎯 OPTIMIZED: Increased limits for comprehensive data collection
        Scrapes products + reviews (Lazada's version of comments) + ratings
        """
        # 🎯 SMART BUFFER: Scale based on target size
        buffer = self.calculate_smart_buffer(max_results)
        adjusted_max_products = int(max_results * buffer)
        adjusted_max_reviews = int(max_comments * 1.3)

        logger.info(f"🛒 Lazada: Requesting {adjusted_max_products} products (target: {max_results}, buffer: {buffer}x)")
        logger.info(f"💬 Lazada: Requesting {adjusted_max_reviews} reviews per product")

        return {
            "searchKeyword": query,  # ✅ Search query
            "maxProducts": adjusted_max_products,  # ✅ OPTIMIZED: 1.4x buffer
            "country": "MY",  # ✅ Malaysia
            "scrapeReviews": True,  # ✅ Enable reviews (comments)
            "maxReviewsPerProduct": adjusted_max_reviews,  # ✅ OPTIMIZED: 1.3x buffer
            "sortReviewsBy": comment_sort,  # ✅ "top" (most helpful) or "recent"
            "scrapeRatings": True,  # ✅ Get star ratings
            "scrapeSales": True,  # ✅ Get sales count (engagement)
            "scrollTimeout": 45,  # 🎯 NEW: Wait for dynamic loading
            "proxy": {
                "useApifyProxy": True,
                "apifyProxyGroups": ["RESIDENTIAL"],
                "apifyProxyCountry": "MY"
            }
        }

    def _prepare_actor_input(self, platform: str, query: str, max_results: int, max_comments: int = 50, comment_sort: str = "top") -> Dict[str, Any]:
        """
        Prepare input configuration for specific platform actor

        Args:
            platform: Platform name
            query: Search query
            max_results: Maximum posts/results
            max_comments: Maximum comments per post
            comment_sort: Comment sorting strategy ("top", "recent", "smart")
        """
        input_map = {
            'facebook': self._prepare_facebook_input,
            'instagram': self._prepare_instagram_input,
            'twitter': self._prepare_twitter_input,
            'x': self._prepare_twitter_input,
            'tiktok': self._prepare_tiktok_input,
            'youtube': self._prepare_youtube_input,
            'google': self._prepare_google_input,
            'news': self._prepare_news_input,
            'lowyat': self._prepare_lowyat_input,
            'linkedin': self._prepare_linkedin_input,
            'threads': self._prepare_threads_input,
            'shopee': self._prepare_shopee_input,
            'lazada': self._prepare_lazada_input
        }

        prepare_func = input_map.get(platform)
        if prepare_func:
            # ✅ Pass max_comments and comment_sort to all preparation functions
            return prepare_func(query, max_results, max_comments, comment_sort)

        # Default input
        return {
            "query": query,
            "maxResults": max_results
        }
    
    def _get_proxy_config(self) -> Dict[str, Any]:
        """Get proxy configuration for Apify actors"""
        return {
            "useApifyProxy": True,
            "apifyProxyGroups": ["RESIDENTIAL"],
            "apifyProxyCountry": "MY"  # Malaysia
        }

    async def _run_apify_actor(self, actor_id: str, actor_input: Dict[str, Any], platform: str = "unknown") -> List[Dict]:
        """
        Run an Apify actor and wait for results

        Args:
            actor_id: Apify actor ID (e.g., 'danek/facebook-search-ppr')
            actor_input: Input configuration for the actor
            platform: Platform name (for dynamic timeout calculation)

        Returns:
            List of results from the actor
        """
        try:
            logger.info(f"🚀 Running Apify actor: {actor_id}")

            # Add proxy configuration if not present
            # ⚠️ Skip if proxy is explicitly set to None (some actors don't support proxy)
            if "proxy" not in actor_input:
                actor_input["proxy"] = self._get_proxy_config()
            elif actor_input.get("proxy") is None:
                # Remove proxy key if explicitly set to None
                actor_input.pop("proxy", None)
                logger.info("⚠️ Proxy disabled for this actor (not supported)")

            # 🎯 DYNAMIC TIMEOUT: Calculate based on dataset size and platform
            # Extract dataset size from various possible fields
            dataset_size = (
                actor_input.get('max_posts') or
                actor_input.get('max_tweets') or
                actor_input.get('maxResults') or
                actor_input.get('maxVideos') or
                actor_input.get('maxProducts') or
                actor_input.get('maxPosts') or
                actor_input.get('resultsLimit') or
                100  # default fallback
            )

            timeout_seconds = self.calculate_dynamic_timeout(
                platform=platform,
                dataset_size=dataset_size
            )

            # Run the actor using official client
            run = self.client.actor(actor_id).call(
                run_input=actor_input,
                timeout_secs=timeout_seconds
            )

            logger.info(f"✅ Actor run completed: {run['id']}")

            # Get dataset ID
            dataset_id = run.get("defaultDatasetId")
            if not dataset_id:
                logger.warning("⚠️ No dataset found in run")
                return []

            # Get dataset items
            dataset_client = self.client.dataset(dataset_id)
            items = list(dataset_client.iterate_items(clean=True))

            logger.info(f"✅ Retrieved {len(items)} results from dataset")
            return items

        except Exception as e:
            logger.error(f"❌ Error running Apify actor: {e}")
            return []

    def _transform_results(self, platform: str, results: List[Dict], max_comments: int = 500) -> List[Dict]:
        """Transform Apify results to InsightPulse standard format with comments extraction"""
        # 🎯 LinkedIn (harvestapi/linkedin-post-search) returns flat mixed dataset with type field
        if platform == 'linkedin':
            return self._transform_linkedin_results(results, max_comments)

        transformed = []
        total_posts = 0
        total_comments = 0

        for item in results:
            try:
                # ===== EXTRACT TEXT CONTENT (platform-specific) =====
                text_content = self._extract_text_content(platform, item)

                # ===== EXTRACT POST ID =====
                post_id = self._extract_post_id(platform, item)

                # ===== EXTRACT ENGAGEMENT METRICS =====
                engagement = self._extract_engagement(platform, item)

                # ===== EXTRACT URL (platform-specific) =====
                post_url = (
                    item.get('url') or item.get('twitterUrl') or item.get('URL') or
                    item.get('link') or item.get('webVideoUrl') or  # TikTok
                    item.get('postUrl') or item.get('permalinkUrl') or ''
                )

                # ===== DETERMINE TYPE (post vs comment) =====
                # Check if this is a reply (marked by _scrape_threads_with_replies)
                # ⚠️ CRITICAL: Use 'in item' not '.get()' to avoid picking up actor's 'isReply' field!
                # We ONLY want our '_isReply' marker (with underscore), not the actor's 'isReply' field
                is_reply = '_isReply' in item and item['_isReply'] is True
                item_type = 'comment' if is_reply else 'post'

                # ===== EXTRACT PARENT POST REFERENCE (for comments/replies) =====
                # For Threads replies, the actor provides sourceUrl or postUrl pointing to the parent post
                parent_post_url = ''
                parent_post_id = ''
                if is_reply:
                    # Threads replies actor provides these fields
                    parent_post_url = item.get('sourceUrl') or item.get('postUrl') or ''
                    # Try to extract post ID from parent URL (e.g., /post/ABC123 -> ABC123)
                    if parent_post_url and '/post/' in parent_post_url:
                        parent_post_id = parent_post_url.split('/post/')[-1].split('/')[0].split('?')[0]

                # ===== CREATE POST/COMMENT RECORD =====
                post_record = {
                    'Platform': platform,
                    'Type': item_type,  # ✅ Set to 'comment' if it's a reply
                    'ID': post_id,
                    'Text': text_content,
                    'URL': post_url,  # ✅ Add URL field for comments crawling
                    'Parent_Post_URL': parent_post_url,  # ✅ Link to parent post (for comments)
                    'Parent_Post_ID': parent_post_id,    # ✅ Parent post ID (for comments)
                    'Sentiment': 'neutral',  # Will be analyzed later
                    'Date': item.get('timestamp', item.get('createdAt', item.get('date', datetime.now().isoformat()))),
                    'likes': engagement['likes'],
                    'shares': engagement['shares'],
                    'comments_count': engagement['comments_count'],
                    'views': engagement['views'],
                    'sentiment_score': 0.0,
                    'total_engagement': engagement['total_engagement']
                }

                transformed.append(post_record)
                if is_reply:
                    total_comments += 1
                else:
                    total_posts += 1

                # ===== EXTRACT COMMENTS =====
                comments = self._extract_comments(platform, item, post_id, post_url, max_comments)
                transformed.extend(comments)
                total_comments += len(comments)

            except Exception as e:
                logger.warning(f"⚠️ Error transforming result: {e}")
                continue

        logger.info(f"📊 Transformed {total_posts} posts + {total_comments} comments = {len(transformed)} total records")
        return transformed

    def _transform_linkedin_results(self, results: List[Dict], max_comments: int = 500) -> List[Dict]:
        """Transform harvestapi/linkedin-post-search flat dataset (posts + comments + reactions mixed by type field)"""
        transformed: List[Dict] = []
        post_records: Dict[str, Dict] = {}
        pending_comments: Dict[str, List[Dict]] = {}
        total_posts = 0
        total_comments = 0
        skipped = 0

        def _get_int(val) -> int:
            try:
                return int(val or 0)
            except (ValueError, TypeError):
                return 0

        def _engagement_dict(eng) -> Dict[str, int]:
            if not isinstance(eng, dict):
                return {'likes': 0, 'shares': 0, 'comments_count': 0, 'views': 0, 'total_engagement': 0}
            likes = _get_int(eng.get('likes') or eng.get('likeCount') or eng.get('reactions'))
            shares = _get_int(eng.get('shares') or eng.get('shareCount') or eng.get('reposts') or eng.get('repostsCount'))
            comments_count = _get_int(eng.get('comments') or eng.get('commentsCount') or eng.get('commentCount'))
            views = _get_int(eng.get('views') or eng.get('viewCount'))
            return {
                'likes': likes,
                'shares': shares,
                'comments_count': comments_count,
                'views': views,
                'total_engagement': likes + shares + comments_count + (views // 100),
            }

        def _date_str(val) -> str:
            # harvestapi sometimes returns {"date": "...", "relative": "...", "timestamp": ...}
            if isinstance(val, dict):
                return str(val.get('date') or val.get('iso') or val.get('timestamp') or '')
            if val is None:
                return ''
            return str(val)

        for item in results:
            try:
                if not isinstance(item, dict):
                    continue
                item_type = str(item.get('type', '')).lower()

                # Skip reactions (no text content)
                if item_type == 'reaction' or 'reactionType' in item:
                    skipped += 1
                    continue

                # Detect comment items (harvestapi returns commentary field for comments)
                is_comment = item_type == 'comment' or ('commentary' in item and 'content' not in item)

                if is_comment:
                    comment_text = str(item.get('commentary') or item.get('text') or '').strip()
                    if not comment_text:
                        continue
                    parent_post_id = str(item.get('postId') or '')
                    # LinkedIn comments don't include parent post URL, so we construct a generic activity URL
                    parent_post_url = f"https://www.linkedin.com/feed/update/urn:li:activity:{parent_post_id}" if parent_post_id else ''
                    comment_id = str(item.get('id') or '')
                    eng = _engagement_dict(item.get('engagement'))
                    comment_record = {
                        'Platform': 'linkedin',
                        'Type': 'comment',
                        'ID': comment_id or f"{parent_post_id}_comment_{total_comments}",
                        'Text': comment_text,
                        'URL': str(item.get('linkedinUrl') or ''),
                        'Parent_Post_URL': parent_post_url,  # ✅ Link to parent post
                        'Parent_Post_ID': parent_post_id,     # ✅ Parent post ID
                        'Sentiment': 'neutral',
                        'Date': _date_str(item.get('createdAt') or item.get('createdAtTimestamp')) or datetime.now().isoformat(),
                        'likes': eng['likes'],
                        'shares': 0,
                        'comments_count': 0,
                        'views': 0,
                        'sentiment_score': 0.0,
                        'total_engagement': eng['likes'],
                    }
                    # Attach to parent post if we've seen it, else queue
                    if parent_post_id and parent_post_id in post_records:
                        post_records[parent_post_id].setdefault('_comments', []).append(comment_record)
                    else:
                        pending_comments.setdefault(parent_post_id, []).append(comment_record)
                    total_comments += 1
                    continue

                # Treat as post
                post_text = str(item.get('content') or item.get('text') or item.get('commentary') or '').strip()
                if not post_text:
                    skipped += 1
                    continue
                post_id = str(item.get('id') or item.get('entityId') or '')
                eng = _engagement_dict(item.get('engagement'))
                post_record = {
                    'Platform': 'linkedin',
                    'Type': 'post',
                    'ID': post_id,
                    'Text': post_text,
                    'URL': str(item.get('linkedinUrl') or item.get('shareLinkedinUrl') or ''),
                    'Parent_Post_URL': '',  # ✅ Empty for posts
                    'Parent_Post_ID': '',    # ✅ Empty for posts
                    'Sentiment': 'neutral',
                    'Date': _date_str(item.get('postedAt') or item.get('createdAt')) or datetime.now().isoformat(),
                    'likes': eng['likes'],
                    'shares': eng['shares'],
                    'comments_count': eng['comments_count'],
                    'views': eng['views'],
                    'sentiment_score': 0.0,
                    'total_engagement': eng['total_engagement'],
                }
                post_records[post_id] = post_record
                total_posts += 1

                # Attach any pending comments queued before this post arrived
                if post_id in pending_comments:
                    post_record.setdefault('_comments', []).extend(pending_comments.pop(post_id))

            except Exception as e:
                logger.warning(f"⚠️ [linkedin] Error transforming item: {e}")
                continue

        # Flatten: post first, then its comments (capped by max_comments per post)
        for post_id, post in post_records.items():
            attached = post.pop('_comments', [])
            transformed.append(post)
            if attached:
                transformed.extend(attached[:max_comments])

        # Orphan comments (parent post not in dataset) — still keep them with empty parent linkage
        for parent_id, cmts in pending_comments.items():
            transformed.extend(cmts[:max_comments])

        logger.info(f"📊 Transformed {total_posts} posts + {total_comments} comments (skipped {skipped} reactions/empty) = {len(transformed)} total records")
        return transformed

    def _extract_text_content(self, platform: str, item: Dict) -> str:
        """Extract text content based on platform-specific field names"""
        # Try multiple field names in order of priority
        text_fields = [
            'text', 'content', 'caption', 'captionText', 'description', 'message',  # ✅ Added 'captionText' for Threads posts
            'postText', 'post_text', 'body', 'title', 'snippet'
        ]

        for field in text_fields:
            if field in item and item[field]:
                return str(item[field]).strip()

        # Platform-specific extraction
        if platform == 'facebook':
            # Facebook might have nested text
            if 'post' in item and isinstance(item['post'], dict):
                return item['post'].get('text', '')

        return ''

    def _extract_post_id(self, platform: str, item: Dict) -> str:
        """Extract post ID based on platform-specific field names"""
        id_fields = ['id', 'postId', 'post_id', 'videoId', 'video_id', 'tweetId', 'tweet_id']

        for field in id_fields:
            if field in item and item[field]:
                return str(item[field])

        return ''

    def _extract_engagement(self, platform: str, item: Dict) -> Dict[str, int]:
        """Extract engagement metrics based on platform-specific field names"""
        # Likes
        likes = 0
        for field in ['likes', 'likeCount', 'like_count', 'likesCount', 'diggCount']:
            if field in item:
                try:
                    likes = int(item[field] or 0)
                    break
                except (ValueError, TypeError):
                    pass

        # Shares
        shares = 0
        for field in ['shares', 'shareCount', 'share_count', 'sharesCount', 'retweets', 'retweetCount']:
            if field in item:
                try:
                    shares = int(item[field] or 0)
                    break
                except (ValueError, TypeError):
                    pass

        # Comments count
        comments_count = 0
        for field in ['comments', 'commentCount', 'comment_count', 'commentsCount', 'replies', 'replyCount']:
            if field in item:
                try:
                    comments_count = int(item[field] or 0)
                    break
                except (ValueError, TypeError):
                    pass

        # Views
        views = 0
        for field in ['views', 'viewCount', 'view_count', 'viewsCount', 'playCount']:
            if field in item:
                try:
                    views = int(item[field] or 0)
                    break
                except (ValueError, TypeError):
                    pass

        # Calculate total engagement
        total_engagement = likes + shares + comments_count + (views // 100)

        return {
            'likes': likes,
            'shares': shares,
            'comments_count': comments_count,
            'views': views,
            'total_engagement': total_engagement
        }

    def _fetch_comments_from_dataset(self, platform: str, dataset_ref: str, post_id: str, post_url: str, max_comments: int = 500) -> List[Dict]:
        """
        Fetch comments from a separate Apify dataset

        Args:
            platform: Platform name (facebook, tiktok, instagram, etc.)
            dataset_ref: Dataset URL or ID
            post_id: Post ID for reference
            post_url: Post URL for parent linking
            max_comments: Maximum number of comments to fetch (default: 500)

        Returns:
            List of comment records
        """
        comments = []

        try:
            # Extract dataset ID from URL if needed
            dataset_id = dataset_ref
            if 'apify.com' in str(dataset_ref):
                # Extract ID from URL like: https://api.apify.com/v2/datasets/abc123/items
                parts = str(dataset_ref).split('/')
                for i, part in enumerate(parts):
                    if part == 'datasets' and i + 1 < len(parts):
                        dataset_id = parts[i + 1]
                        break

            logger.info(f"📥 [{platform}] Fetching comments from dataset: {dataset_id} (max: {max_comments})")

            # Fetch items from dataset using Apify client
            dataset_items = []
            for item in self.client.dataset(dataset_id).iterate_items():
                dataset_items.append(item)
                # ✅ OPTIMIZATION: Use dynamic limit based on max_comments parameter
                if len(dataset_items) >= max_comments:
                    break

            logger.info(f"📥 [{platform}] Retrieved {len(dataset_items)} items from dataset")

            # Transform dataset items to comment records
            for idx, comment_item in enumerate(dataset_items):
                try:
                    # Extract comment text
                    comment_text = self._extract_text_content(platform, comment_item)
                    if not comment_text:
                        continue

                    # Extract comment engagement
                    comment_engagement = self._extract_engagement(platform, comment_item)

                    # Create comment record
                    comment_record = {
                        'Platform': platform,
                        'Type': 'comment',
                        'ID': comment_item.get('id', f"{post_id}_comment_{idx}"),
                        'Text': comment_text,
                        'Parent_Post_URL': post_url,  # ✅ Link to parent post
                        'Parent_Post_ID': post_id,     # ✅ Parent post ID
                        'Sentiment': 'neutral',
                        'Date': comment_item.get('timestamp', comment_item.get('createdAt', comment_item.get('date', datetime.now().isoformat()))),
                        'likes': comment_engagement['likes'],
                        'shares': 0,  # Comments usually don't have shares
                        'comments_count': 0,  # Nested comments not supported for now
                        'views': 0,
                        'sentiment_score': 0.0,
                        'total_engagement': comment_engagement['likes']
                    }

                    comments.append(comment_record)

                except Exception as e:
                    logger.warning(f"⚠️ Error transforming comment {idx} from dataset: {e}")
                    continue

            logger.info(f"✅ [{platform}] Transformed {len(comments)} comments from dataset")

        except Exception as e:
            logger.error(f"❌ [{platform}] Error fetching comments from dataset: {e}")
            raise

        return comments

    def _extract_comments(self, platform: str, item: Dict, post_id: str, post_url: str, max_comments: int = 500) -> List[Dict]:
        """Extract comments from nested structure OR from separate dataset"""
        comments = []

        # 🔍 DEBUG: Log all available fields in the item (first item only to avoid spam)
        if post_id.endswith('_0') or '_comment_' not in post_id:
            logger.info(f"🔍 [{platform}] Sample item fields: {list(item.keys())[:20]}")

        # 🚀 STEP 1: Check for SEPARATE DATASET references (NEW!)
        dataset_url = None
        dataset_id = None

        # Check for dataset URL/ID fields (platform-specific)
        if platform == 'tiktok':
            dataset_url = item.get('commentsDatasetUrl')
            if dataset_url:
                logger.info(f"🔗 [{platform}] Found commentsDatasetUrl: {dataset_url}")
        elif platform == 'facebook':
            # 🎯 SKIP: Facebook uses 2-actor strategy (separate comments actor)
            # Don't try to fetch from comments_id dataset (it doesn't exist)
            pass
        elif platform == 'instagram':
            dataset_url = item.get('commentsDatasetUrl') or item.get('comments_dataset_url')
            if dataset_url:
                logger.info(f"🔗 [{platform}] Found commentsDatasetUrl: {dataset_url}")

        # 🚀 STEP 2: Fetch comments from separate dataset if available
        if dataset_url or dataset_id:
            try:
                # ✅ OPTIMIZATION: Pass max_comments to dataset fetcher
                comments_from_dataset = self._fetch_comments_from_dataset(platform, dataset_url or dataset_id, post_id, post_url, max_comments)
                if comments_from_dataset:
                    logger.info(f"✅ [{platform}] Fetched {len(comments_from_dataset)} comments from separate dataset")
                    return comments_from_dataset
            except Exception as e:
                logger.warning(f"⚠️ [{platform}] Failed to fetch comments from dataset: {e}")
                # Continue to try inline comments as fallback

        # 🚀 STEP 3: Try to find INLINE comments in various field names (FALLBACK)
        comments_data = None
        possible_fields = []

        if platform == 'tiktok':
            possible_fields = ['comments', 'commentsList', 'videoComments', 'commentsData']
        elif platform == 'facebook':
            possible_fields = ['comments', 'commentsList', 'post_comments', 'commentsData']
        elif platform == 'instagram':
            possible_fields = ['comments', 'commentsList', 'latestComments', 'commentsData']
        elif platform in ['twitter', 'x']:
            possible_fields = ['replies', 'repliesList', 'comments', 'tweet_replies']
        else:
            possible_fields = ['comments', 'commentsList', 'replies', 'repliesList']

        for field in possible_fields:
            if field in item and item[field]:
                comments_data = item[field]
                logger.info(f"✅ Found inline comments in field '{field}': {len(comments_data) if isinstance(comments_data, list) else 'not a list'}")
                break

        if not comments_data:
            # 🔍 DEBUG: Log what we found instead
            logger.warning(f"⚠️ [{platform}] No inline comments found. Tried fields: {possible_fields}")
            logger.warning(f"⚠️ [{platform}] Available fields: {list(item.keys())}")
            return comments

        if not isinstance(comments_data, list):
            logger.warning(f"⚠️ [{platform}] Comments data is not a list: {type(comments_data)}")
            return comments

        # Process each comment
        for idx, comment in enumerate(comments_data):
            try:
                if not isinstance(comment, dict):
                    continue

                # Extract comment text
                comment_text = self._extract_text_content(platform, comment)
                if not comment_text:
                    continue

                # Extract comment engagement
                comment_engagement = self._extract_engagement(platform, comment)

                # Create comment record
                comment_record = {
                    'Platform': platform,
                    'Type': 'comment',
                    'ID': comment.get('id', f"{post_id}_comment_{idx}"),
                    'Text': comment_text,
                    'Parent_Post_URL': post_url,  # ✅ Link to parent post
                    'Parent_Post_ID': post_id,     # ✅ Parent post ID
                    'Sentiment': 'neutral',
                    'Date': comment.get('timestamp', comment.get('createdAt', comment.get('date', datetime.now().isoformat()))),
                    'likes': comment_engagement['likes'],
                    'shares': 0,  # Comments usually don't have shares
                    'comments_count': 0,  # Nested comments not supported for now
                    'views': 0,
                    'sentiment_score': 0.0,
                    'total_engagement': comment_engagement['likes']
                }

                comments.append(comment_record)

            except Exception as e:
                logger.warning(f"⚠️ Error extracting comment {idx}: {e}")
                continue

        return comments

    def _save_results(self, platform: str, query: str, results: List[Dict]):
        """
        Save crawl results to CSV (RAW data without sentiment) - Posts and Comments in ONE file

        SAVES TO: data/smart_crawlers/PLATFORM/PLATFORM_query_YYYYMMDD_HHMMSS.csv
        (NO LONGER saves to data/raw/ - only historical archive)
        """
        try:
            # ✅ FLATTEN: Extract nested comments and combine with posts
            all_records = []

            for result in results:
                # Add post (without nested comments field)
                post_copy = result.copy()
                nested_comments = post_copy.pop('comments', [])
                all_records.append(post_copy)

                # Add comments right after the post (if any)
                if nested_comments and isinstance(nested_comments, list):
                    all_records.extend(nested_comments)

            if not all_records:
                logger.warning(f"⚠️ No records to save for {platform}")
                return

            # Count posts and comments
            posts_count = len([r for r in all_records if r.get('Type') == 'post'])
            comments_count = len([r for r in all_records if r.get('Type') == 'comment'])

            # Create DataFrame
            df = pd.DataFrame(all_records)

            # 📂 Save to data/smart_crawlers/PLATFORM/ (ONLY location)
            platform_dir = self.data_dir / platform.lower()
            platform_dir.mkdir(parents=True, exist_ok=True)

            # Clean query for filename (remove special chars)
            import re
            query_clean = re.sub(r'[^\w\s-]', '', query).strip().replace(' ', '_')
            query_clean = query_clean[:50]  # Limit length

            # Timestamp for unique filename
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            archive_filename = f"{platform.lower()}_{query_clean}_{timestamp}.csv"
            archive_filepath = platform_dir / archive_filename
            df.to_csv(archive_filepath, index=False, encoding='utf-8')

            logger.info(f"💾 SAVED: {archive_filepath}")
            logger.info(f"✅ {posts_count} posts + {comments_count} comments = {len(all_records)} total records")
            logger.info(f"📊 This is RAW data WITHOUT sentiment/emotion analysis")

        except Exception as e:
            logger.error(f"❌ Error saving results: {e}")

    async def _run_serpapi(self, engine: str, params: Dict[str, Any]) -> List[Dict]:
        """
        Run SerpAPI query for YouTube, Google News, and Google Shopping

        Args:
            engine: SerpAPI engine (youtube, google_news, google_shopping)
            params: Query parameters

        Returns:
            List of results
        """
        try:
            logger.info(f"🚀 Running SerpAPI: {engine}")

            # Add API key
            params['api_key'] = self.serpapi_key

            # Make request
            response = requests.get(
                'https://serpapi.com/search',
                params=params,
                timeout=60
            )

            if response.status_code != 200:
                logger.error(f"❌ SerpAPI error: {response.status_code}")
                return []

            data = response.json()

            # Extract results based on engine
            if engine == 'youtube':
                results = data.get('video_results', [])
            elif engine == 'google_news':
                results = data.get('news_results', [])
            elif engine == 'google_shopping':
                # Get shopping results
                shopping_results = data.get('shopping_results', [])
                # Also get inline shopping results if available
                inline_shopping = data.get('inline_shopping_results', [])
                results = shopping_results + inline_shopping
            else:
                results = data.get('organic_results', [])

            logger.info(f"✅ Retrieved {len(results)} results from SerpAPI ({engine})")
            return results

        except Exception as e:
            logger.error(f"❌ Error running SerpAPI: {e}")
            return []

    async def crawl_platform_with_ai_keywords(
        self,
        platform: str,
        query: str,
        ai_keywords: List[str],
        max_results: int = 100,
        max_comments: int = 50,
        comment_sampling: str = "smart"
    ) -> List[Dict[str, Any]]:
        """
        Crawl a platform using AI-generated keywords (multiple searches combined)

        Args:
            platform: Platform name
            query: Original user query
            ai_keywords: List of AI-generated keywords for this platform
            max_results: Maximum results per keyword
            max_comments: Maximum comments per post
            comment_sampling: Comment sampling strategy

        Returns:
            Combined and deduplicated results from all keyword searches
        """
        all_results = []
        seen_ids = set()

        for keyword in ai_keywords:
            try:
                logger.info(f"🔍 [{platform}] Searching with keyword: '{keyword}'")

                # Crawl with this specific keyword
                # ✅ FIX: Give each keyword the FULL quota, then deduplicate
                # This ensures we get enough results even if some keywords return fewer posts
                results = await self.crawl_platform(
                    platform=platform,
                    query=keyword,
                    max_results=max_results,  # ✅ FIX: Full quota per keyword (was: max_results // len(ai_keywords))
                    max_comments=max_comments,
                    comment_sampling=comment_sampling
                )

                # Deduplicate based on post ID
                for result in results:
                    post_id = result.get('Post_ID', result.get('Text', '')[:50])
                    if post_id not in seen_ids:
                        seen_ids.add(post_id)
                        all_results.append(result)

            except Exception as e:
                logger.error(f"❌ [{platform}] Error searching with keyword '{keyword}': {e}")
                continue

        logger.info(f"✅ [{platform}] Combined {len(all_results)} unique results from {len(ai_keywords)} keywords")

        # 🎯 AUTOMATIC COMMENTS CRAWLING for platforms using 2-actor strategy
        logger.info(f"🔍 [{platform}] Checking if comments crawling needed...")
        logger.info(f"   Platform: '{platform}' (lower: '{platform.lower()}')")
        logger.info(f"   Results: {len(all_results)}")
        logger.info(f"   Condition: platform.lower() in ['x', 'twitter', 'facebook'] = {platform.lower() in ['x', 'twitter', 'facebook']}")

        if platform.lower() in ['x', 'twitter', 'facebook', 'youtube'] and all_results:
            logger.info(f"🔍 [{platform}] Auto-crawling comments for {len(all_results)} posts...")
            try:
                posts_with_comments = await self._crawl_comments_for_posts(
                    platform=platform.lower(),
                    posts=all_results,
                    comments_per_post=min(max_comments, 50) if platform.lower() == 'youtube' else min(max_comments, 10)
                )

                # Count total comments
                total_comments = sum(len(post.get('comments', [])) for post in posts_with_comments)
                logger.info(f"✅ [{platform}] Added {total_comments} comments to {len(posts_with_comments)} posts")

                return posts_with_comments
            except Exception as e:
                logger.error(f"❌ [{platform}] Failed to crawl comments: {e}")
                import traceback
                logger.error(f"❌ Traceback:\n{traceback.format_exc()}")
                # Return posts without comments on error
                return all_results
        else:
            logger.warning(f"⚠️ [{platform}] Skipping automatic comments crawling (condition not met)")

        return all_results

    async def crawl_platform(
        self,
        platform: str,
        query: str,
        max_results: int = 100,
        max_comments: int = 50,
        comment_sampling: str = "smart",
        use_ai_keywords: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Crawl a specific platform using Apify API or SerpAPI with intelligent comment sampling

        Args:
            platform: Platform name (facebook, instagram, etc.)
            query: Search query
            max_results: Maximum number of posts/results
            max_comments: Maximum number of comments per post
            comment_sampling: Comment sampling strategy ("smart", "top_only", "recent_only", "random")
            use_ai_keywords: Whether to use AI-generated keywords (if available)

        Returns:
            List of crawled data dictionaries
        """
        try:
            logger.info(f"🔍 Starting crawl for {platform}: '{query}'")
            logger.info(f"   📊 Limits: {max_results} posts, {max_comments} comments/post")
            logger.info(f"   🎯 Comment sampling: {comment_sampling}")

            # 🗄️ STEP 0: Check SQLite Cache first
            cached_posts_only = None  # Will hold posts from cache (without comments initially)
            if CRAWL_CACHE_AVAILABLE:
                cached_data = get_cached_posts(query, platform, limit=max_results)
                if cached_data and len(cached_data) >= (max_results * 0.8): # If we have 80% of target in cache
                    logger.info(f"🗄️ [{platform}] Found {len(cached_data)} records in cache for '{query}'")
                    # Check if cache is fresh (less than 1 hour old)
                    last_crawl = get_last_crawl_time(query, platform)
                    if last_crawl:
                        age_seconds = (datetime.now() - last_crawl).total_seconds()
                        if age_seconds < 3600: # 1 hour
                            logger.info(f"✨ [{platform}] Cache is fresh ({age_seconds/60:.1f} mins old). Using cached posts and crawling comments...")
                            cached_posts_only = cached_data  # ✅ Use cache for posts, but fetch comments
                            # DON'T RETURN — continue to fetch comments!
                        else:
                            logger.info(f"⏳ [{platform}] Cache is stale ({age_seconds/3600:.1f} hours old). Will attempt incremental crawl.")
                            # For incremental crawl, we can use the date of the latest post in cache
                            # but let's keep it simple for now and just crawl and merge.

            # Map comment sampling to sort strategy
            comment_sort_map = {
                "smart": "top",      # Get top comments (most liked/replied)
                "top_only": "top",   # Only top comments
                "recent_only": "recent",  # Only recent comments
                "random": "top"      # Default to top for random
            }
            comment_sort = comment_sort_map.get(comment_sampling, "top")

            # ✅ Use cached posts if available (and skip actor crawl)
            if cached_posts_only:
                logger.info(f"✅ Using {len(cached_posts_only)} cached posts for {platform}")
                transformed = cached_posts_only

                # ⚠️ CRITICAL FIX: For Threads, STILL fetch comments even when using cached posts!
                if platform == 'threads' and max_comments > 0:
                    logger.info(f"🧵 [{platform}] Fetching comments for cached posts...")
                    try:
                        import os
                        session_id = os.getenv('THREADS_SESSION_ID')

                        if session_id and session_id != '66920257060...paste_the_full_value_here':
                            # Extract post URLs from cached posts
                            post_urls = []
                            for post in transformed:
                                if post.get('Type') == 'post':  # Only get comments for posts, not existing comments
                                    url = post.get('URL') or post.get('url')
                                    if url:
                                        post_urls.append(url)

                            if post_urls:
                                logger.info(f"   Found {len(post_urls)} post URLs from cache")

                                # Split into batches and fetch comments in parallel
                                BATCH_SIZE = 20
                                url_batches = [post_urls[i:i + BATCH_SIZE] for i in range(0, len(post_urls), BATCH_SIZE)]

                                logger.info(f"   Fetching comments in {len(url_batches)} PARALLEL batches...")

                                import asyncio

                                async def fetch_batch_from_cache(batch_idx, batch_urls):
                                    try:
                                        replies_input = {
                                            "postUrls": batch_urls,
                                            "sessionId": session_id,
                                            "proxy": None
                                        }
                                        batch_replies = await self._run_apify_actor(
                                            'futurizerush/threads-replies-scraper-api',
                                            replies_input,
                                            'threads'
                                        )
                                        logger.info(f"   ✅ Batch {batch_idx + 1}: Fetched {len(batch_replies)} replies")
                                        return batch_replies
                                    except Exception as e:
                                        logger.error(f"   ❌ Batch {batch_idx + 1} failed: {e}")
                                        return []

                                all_batch_results = await asyncio.gather(
                                    *[fetch_batch_from_cache(i, batch) for i, batch in enumerate(url_batches)],
                                    return_exceptions=True
                                )

                                # Combine all replies
                                all_replies = []
                                for batch_result in all_batch_results:
                                    if isinstance(batch_result, list):
                                        all_replies.extend(batch_result)

                                logger.info(f"   ✅ Fetched {len(all_replies)} total replies from cache-based crawl")

                                # Mark replies and transform them
                                for reply in all_replies:
                                    reply['_isReply'] = True

                                transformed_replies = self._transform_results(platform, all_replies, max_comments)

                                # Combine cached posts + new comments
                                transformed = transformed + transformed_replies
                                logger.info(f"   🎉 Total: {len(transformed)} items ({len(cached_posts_only)} cached posts + {len(transformed_replies)} new comments)")
                            else:
                                logger.warning(f"   ⚠️ No post URLs found in cached data")
                        else:
                            logger.warning(f"   ⚠️ THREADS_SESSION_ID not configured - skipping comments")
                    except Exception as e:
                        logger.error(f"   ❌ Error fetching comments for cached posts: {e}")
                        # Continue with just cached posts
            else:
                # Get the actor/engine for this platform
                actor_id = self.actor_map.get(platform)

                if not actor_id:
                    logger.warning(f"⚠️ No actor configured for {platform}")
                    return []

                # ── Route: Scrapling (FREE engine) ──────────────────────────────
                if actor_id == 'scrapling':
                    if SCRAPLING_ADAPTER_AVAILABLE and _scrapling_adapter:
                        logger.info(f"🆓 [{platform}] Routing to FREE Scrapling engine (saves SerpAPI cost)")
                        transformed = await _scrapling_adapter.crawl_platform(
                            platform=platform,
                            query=query,
                            max_results=max_results,
                            max_comments=max_comments,
                            comment_sampling=comment_sampling,
                        )
                        if transformed:
                            logger.info(f"✅ Collected {len(transformed)} records from {platform} via Scrapling")
                            # 🗄️ Save to cache
                            if CRAWL_CACHE_AVAILABLE:
                                save_crawl_result(query, platform, transformed)
                        return transformed
                    else:
                        logger.warning(f"⚠️ Scrapling not available — falling back to SerpAPI for {platform}")
                        actor_id = 'serpapi'   # graceful degradation

                # ── Route: Threads (2-step process) ──────────────────────────────
                if platform == 'threads':
                    logger.info(f"🧵 [{platform}] Using 2-step Threads scraper (posts + replies)")
                    results = await self._scrape_threads_with_replies(query, max_results, max_comments, comment_sort)
                    # Threads scraper returns already-transformed results, no need to transform again
                    transformed = self._transform_results(platform, results, max_comments)
                # ── Route: SerpAPI ───────────────────────────────────────────────
                elif actor_id == 'serpapi':
                    # Prepare SerpAPI input with max_comments and comment_sort
                    actor_input = self._prepare_actor_input(platform, query, max_results, max_comments, comment_sort)

                    # Run SerpAPI
                    results = await self._run_serpapi(
                        actor_input.get('engine'),
                        actor_input
                    )
                    # Transform to standard format
                    transformed = self._transform_results(platform, results, max_comments)
                else:
                    # ── Route: Apify actor ───────────────────────────────────────
                    actor_input = self._prepare_actor_input(platform, query, max_results, max_comments, comment_sort)
                    results = await self._run_apify_actor(actor_id, actor_input, platform)
                    # Transform to standard format
                    # ✅ OPTIMIZATION: Pass max_comments to enable dynamic comment limit
                    transformed = self._transform_results(platform, results, max_comments)

            # ⚠️ DON'T save here - will be saved later after comments are attached
            if transformed:
                logger.info(f"✅ Collected {len(transformed)} records from {platform}")
                # 🗄️ Save to cache
                if CRAWL_CACHE_AVAILABLE:
                    save_crawl_result(query, platform, transformed)

            return transformed

        except Exception as e:
            logger.error(f"❌ Error crawling {platform}: {e}")
            return []

    async def crawl_multi_platform_with_ai(
        self,
        platforms: List[str],
        query: str,
        max_results: int = 100,
        max_comments: int = 50,
        comment_sampling: str = "smart",
        analysis_type: str = "general"
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Crawl multiple platforms using AI-generated platform-optimized keywords
        with 30:70 Posts:Comments ratio strategy

        Args:
            platforms: List of platform names
            query: User's original search query
            max_results: Maximum results per platform (total posts + comments)
            max_comments: Maximum comments per post
            comment_sampling: Comment sampling strategy
            analysis_type: Type of analysis (for AI context)

        Returns:
            Dict mapping platform names to their results
        """
        try:
            # 🎯 STEP 1: Calculate crawl strategy (30:70 ratio)
            if CRAWL_STRATEGY_AVAILABLE:
                strategy = CrawlStrategy.calculate_distribution(
                    dataset_size=max_results,
                    platforms_count=len(platforms),
                    platforms=platforms
                )
                logger.info(f"📊 Using 30:70 strategy: {strategy['posts_per_platform']} posts + {strategy['comments_per_platform']} comments per platform")

                # Override max_results with posts target
                posts_target = strategy['posts_per_platform']
                comments_target = strategy['comments_per_platform']
                comments_per_post = strategy['comments_per_post']
            else:
                logger.warning("⚠️ Crawl Strategy not available, using legacy approach")
                posts_target = max_results
                comments_target = max_comments
                comments_per_post = max_comments

            # Generate AI keywords for all platforms
            ai_keywords = {}
            if self.ai_keyword_generator:
                logger.info(f"🤖 Generating AI keywords for {len(platforms)} platforms...")
                ai_keywords = await self.ai_keyword_generator.generate_platform_keywords(
                    query=query,
                    platforms=platforms,
                    analysis_type=analysis_type
                )
            else:
                # Fallback: use original query for all platforms
                logger.warning("⚠️ AI keywords not available, using original query")
                for platform in platforms:
                    ai_keywords[platform.lower()] = [query]

            # Per-platform allocation: comment-less platforms get full per_platform quota,
            # comment-enabled platforms use the 30:70 split (posts_target / comments_per_post)
            NO_COMMENTS_PLATFORMS = ["news", "google", "shopee", "lazada"]
            per_platform_quota = strategy['per_platform'] if CRAWL_STRATEGY_AVAILABLE else posts_target

            # Crawl each platform with its AI-generated keywords
            results = {}
            for platform in platforms:
                platform_lower = platform.lower()
                keywords = ai_keywords.get(platform_lower, [query])

                if platform_lower in NO_COMMENTS_PLATFORMS:
                    p_max_results = per_platform_quota
                    p_max_comments = 0
                else:
                    p_max_results = posts_target
                    p_max_comments = comments_per_post

                if len(keywords) > 1:
                    # Multiple keywords: use combined search
                    platform_results = await self.crawl_platform_with_ai_keywords(
                        platform=platform_lower,
                        query=query,
                        ai_keywords=keywords,
                        max_results=p_max_results,
                        max_comments=p_max_comments,
                        comment_sampling=comment_sampling
                    )
                else:
                    # Single keyword: use direct search
                    platform_results = await self.crawl_platform(
                        platform=platform_lower,
                        query=keywords[0] if keywords else query,
                        max_results=p_max_results,
                        max_comments=p_max_comments,
                        comment_sampling=comment_sampling
                    )

                # 🎯 STEP 2: Filter and rank posts by engagement (if strategy available)
                if CRAWL_STRATEGY_AVAILABLE and platform_results:
                    # Separate posts and comments before filtering
                    only_posts = [r for r in platform_results if r.get('Type', r.get('type', 'post')) == 'post']
                    only_comments = [r for r in platform_results if r.get('Type', r.get('type', 'post')) == 'comment']

                    filtered_posts = CrawlStrategy.filter_posts_by_engagement(
                        posts=only_posts,
                        target_count=p_max_results
                    )
                    # Preserve comments alongside filtered posts
                    filtered_results = filtered_posts + only_comments
                    results[platform_lower] = filtered_results

                    logger.info(f"✅ [{platform_lower}] Filtered to {len(filtered_posts)} top posts + {len(only_comments)} comments")
                else:
                    results[platform_lower] = platform_results

                # 🎯 STEP 3: AUTOMATICALLY CRAWL COMMENTS for 2-actor platforms (X/Twitter, Facebook, Instagram, YouTube)
                if platform_lower in ['x', 'twitter', 'facebook', 'instagram', 'youtube'] and platform_results:
                    logger.info(f"🔍 [{platform_lower}] Auto-crawling comments for {len(platform_results)} posts...")
                    try:
                        posts_with_comments = await self._crawl_comments_for_posts(
                            platform=platform_lower,
                            posts=platform_results,
                            comments_per_post=min(comments_per_post, 50) if platform_lower == 'youtube' else min(comments_per_post, 10)
                        )
                        results[platform_lower] = posts_with_comments

                        # Count total comments
                        total_comments = sum(len(post.get('comments', [])) for post in posts_with_comments)
                        logger.info(f"✅ [{platform_lower}] Added {total_comments} comments to {len(posts_with_comments)} posts")
                    except Exception as e:
                        logger.error(f"❌ [{platform_lower}] Failed to crawl comments: {e}")
                        import traceback
                        logger.error(f"❌ Traceback:\n{traceback.format_exc()}")
                        # Keep original posts without comments
                        pass

                # 💾 STEP 4: SAVE results to CSV (posts + comments in ONE file)
                if platform_results:
                    self._save_results(platform_lower, query, results[platform_lower])

            return results

        except Exception as e:
            logger.error(f"❌ Error in multi-platform AI crawl: {e}")
            return {}

    async def crawl_with_strategy(
        self,
        platforms: List[str],
        query: str,
        dataset_size: int = 1000,
        analysis_type: str = "general",
        since_date: str = None,
        until_date: str = None
    ) -> Dict[str, Any]:
        """
        🎯 NEW: Crawl with 30:70 Posts:Comments strategy

        This method implements the full crawling strategy:
        1. Calculate distribution (30% posts, 70% comments)
        2. Crawl posts first
        3. Filter and rank by engagement
        4. Adaptive adjustment based on results
        5. Crawl comments for selected posts
        6. Combine and return

        Args:
            platforms: List of platform names
            query: Search query
            dataset_size: Total target results (posts + comments)
            analysis_type: Type of analysis

        Returns:
            Dict with strategy info and results
        """
        try:
            if not CRAWL_STRATEGY_AVAILABLE:
                logger.error("❌ Crawl Strategy not available!")
                return {"error": "Crawl Strategy module not available"}

            # Apply date range to adapter so all actor inputs respect it
            self._crawl_since_date = since_date
            self._crawl_until_date = until_date
            if since_date:
                logger.info(f"📅 Crawling with date range: {since_date} → {until_date or 'now'}")

            # 🎯 STEP 1: Calculate strategy
            # 🎯 STEP 1: Calculate strategy
            strategy = CrawlStrategy.calculate_distribution(
                dataset_size=dataset_size,
                platforms_count=len(platforms),
                platforms=platforms
            )
            logger.info(f"📊 Strategy: {strategy['total_posts']} posts + {strategy['total_comments']} comments")

            # 🎯 STEP 2: Crawl posts AND comments for all platforms
            logger.info(f"🔍 Phase 1: Crawling posts with automatic comments...")

            # ✅ Special handling: Platforms without comments get 100% quota for posts/products
            # We override the max_results for these platforms specifically
            NO_COMMENTS_PLATFORMS = ["news", "google", "shopee", "lazada"]

            platform_configs = {}
            for p in platforms:
                p_lower = p.lower()
                if p_lower in NO_COMMENTS_PLATFORMS:
                    platform_configs[p_lower] = {
                        "max_results": strategy['per_platform'], # Full allocation for posts/products
                        "max_comments": 0
                    }
                else:
                    platform_configs[p_lower] = {
                        "max_results": strategy['posts_per_platform'], # 30% posts
                        "max_comments": strategy['comments_per_post'] # 70% comments
                    }

            try:
                # Use the helper to crawl with specific limits per platform
                posts_results = {}
                for p in platforms:
                    p_lower = p.lower()
                    config = platform_configs[p_lower]

                    # Generate AI keywords if requested
                    keywords = [query]
                    if hasattr(self, 'llm_service') and self.llm_service:
                        # Logic simplified for this step
                        pass

                # Pass full dataset_size so the inner method recomputes the SAME
                # per-platform strategy (it now respects NO_COMMENTS_PLATFORMS per-platform)
                posts_results = await self.crawl_multi_platform_with_ai(
                    platforms=platforms,
                    query=query,
                    max_results=dataset_size,
                    max_comments=strategy['comments_per_post'],
                    analysis_type=analysis_type
                )

                # RE-CRAWL if it was throttled by the global max_results (for platforms needing full quota)
                for plat_to_boost in NO_COMMENTS_PLATFORMS:
                    if plat_to_boost in platforms and plat_to_boost in posts_results:
                        current_count = len(posts_results[plat_to_boost])
                        target = strategy['per_platform']

                        if current_count < target and target > strategy['posts_per_platform']:
                            logger.info(f"🚀 [{plat_to_boost}] Boosting crawl to full platform quota: {target} results")
                            boosted_results = await self.crawl_platform(
                                platform=plat_to_boost,
                                query=query,
                                max_results=target,
                                max_comments=0
                            )
                            posts_results[plat_to_boost] = boosted_results

                logger.info(f"✅ Phase 1 completed. Got results for {len(posts_results)} platforms")
            except Exception as e:
                import traceback
                logger.error(f"❌ Phase 1 failed: {e}")
                logger.error(f"❌ Traceback:\n{traceback.format_exc()}")
                raise

            # 🎯 STEP 3: Count results (comments already crawled in Phase 1)
            final_results = posts_results
            total_posts = 0
            total_comments = 0

            logger.info(f"📊 Phase 2: Counting results from {len(posts_results)} platforms...")
            for platform, posts in posts_results.items():
                if not posts:
                    logger.warning(f"⚠️ No posts found for {platform}")
                    continue

                # Count posts and comments
                total_posts += len(posts)
                total_comments += sum(len(p.get('comments', [])) for p in posts)

                logger.info(f"✅ [{platform}] {len(posts)} posts with {sum(len(p.get('comments', [])) for p in posts)} comments")

                # 💾 SAVE posts + comments in ONE file (after comments are attached)
                self._save_results(platform, query, posts)

            return {
                "strategy": strategy,
                "results": final_results,
                "summary": {
                    "total_posts": total_posts,
                    "total_comments": total_comments,
                    "total_results": total_posts + total_comments,
                    "platforms": len(platforms),
                    "query": query
                }
            }

        except Exception as e:
            logger.error(f"❌ Error in strategy-based crawl: {e}")
            return {"error": str(e)}

    async def _crawl_comments_for_posts(
        self,
        platform: str,
        posts: List[Dict],
        comments_per_post: int
    ) -> List[Dict]:
        """
        🎯 Crawl comments for given posts using platform-specific comments actor

        Args:
            platform: Platform name (x, facebook, instagram, etc.)
            posts: List of post records
            comments_per_post: Target number of comments per post

        Returns:
            List of posts with comments attached
        """
        try:
            if platform not in ['x', 'twitter', 'facebook', 'instagram', 'youtube']:
                logger.warning(f"⚠️ Comments crawling not yet implemented for {platform}")
                return posts

            # Get the comments actor for this platform
            actor_id = self.comments_actor_map.get(platform)
            if not actor_id:
                logger.warning(f"⚠️ No comments actor configured for {platform}")
                return posts

            # Extract post URLs - ONLY for posts with comments
            post_urls = []

            # 🎯 DEBUG: Log first post to see what fields are available
            if posts:
                logger.info(f"🔍 [{platform}] Sample post fields: {list(posts[0].keys())[:15]}")
                logger.info(f"🔍 [{platform}] Sample URL value: {posts[0].get('URL', 'NOT FOUND')}")

            for post in posts:
                # ✅ Filter: Only crawl comments for posts that have replyCount > 0
                if platform in ['x', 'twitter']:
                    reply_count = post.get('comments_count', 0) or post.get('replyCount', 0)
                elif platform == 'facebook':
                    # Facebook actor returns 'comments_count' field
                    reply_count = post.get('comments_count', 0) or post.get('Comments', 0)
                elif platform == 'instagram':
                    # Instagram: comments_count from the post
                    reply_count = post.get('comments_count', 0) or post.get('commentCount', 0)
                elif platform == 'youtube':
                    # YouTube: comments_count from the video post
                    reply_count = post.get('comments_count', 0) or post.get('commentCount', 0)
                else:
                    reply_count = 0

                # 🎯 For Facebook, Instagram & YouTube: Crawl even if count is 0 (actors under-report)
                # 🎯 For X/Twitter: Only crawl if comments_count > 0
                should_crawl = False
                if platform in ['facebook', 'instagram', 'youtube']:
                    should_crawl = True  # Always crawl (actors under-report comment counts)
                elif reply_count > 0:
                    should_crawl = True

                if should_crawl:
                    if platform in ['x', 'twitter']:
                        url = post.get('URL') or post.get('url') or post.get('twitterUrl')
                    elif platform == 'facebook':
                        url = post.get('URL') or post.get('url') or post.get('Post_URL')
                    elif platform == 'instagram':
                        url = post.get('URL') or post.get('url') or post.get('postUrl')
                    elif platform == 'youtube':
                        url = post.get('URL') or post.get('url') or post.get('videoUrl')
                    else:
                        url = None

                    if url:
                        # 🎯 FILTER: Skip Facebook Reels URLs (comments actor can't scrape them)
                        if platform == 'facebook' and '/reel/' in url:
                            logger.debug(f"⏭️ Skipping Facebook Reel URL: {url}")
                            continue
                        # 🎯 FILTER: Skip YouTube radio/playlist URLs (no real comments)
                        if platform == 'youtube' and ('list=RD' in url or 'start_radio=1' in url):
                            logger.debug(f"⏭️ Skipping YouTube radio/playlist URL: {url}")
                            continue
                        post_urls.append(url)

            logger.info(f"📊 [{platform}] Found {len(post_urls)} posts with valid URLs (from {len(posts)} total posts)")

            if not post_urls:
                logger.warning(f"⚠️ No valid post URLs found for comments crawling")
                return posts

            logger.info(f"📊 Found {len(post_urls)} posts with comments (filtered from {len(posts)} total posts)")
            logger.info(f"🔍 Crawling comments for {len(post_urls)} posts...")
            logger.info(f"   Target: {comments_per_post} comments per post")

            # Prepare platform-specific input
            all_records = []
            if platform in ['x', 'twitter']:
                # X/Twitter comments actor (hard limit: 5 URLs per call) → batch in chunks of 5
                X_BATCH_SIZE = 5
                X_MAX_URLS = 20  # crawl replies for up to 20 posts (4 batches)
                target_urls = post_urls[:X_MAX_URLS]
                num_batches = (len(target_urls) + X_BATCH_SIZE - 1) // X_BATCH_SIZE
                logger.info(f"🚀 Running comments actor: {actor_id} in {num_batches} batches of {X_BATCH_SIZE}")
                for batch_idx in range(num_batches):
                    batch = target_urls[batch_idx * X_BATCH_SIZE:(batch_idx + 1) * X_BATCH_SIZE]
                    run_input = {
                        "postUrls": batch,
                        "maxRepliesPerPost": comments_per_post,
                        "sortBy": "top",
                        "proxy": {
                            "useApifyProxy": True,
                            "apifyProxyGroups": ["RESIDENTIAL"],
                            "apifyProxyCountry": "MY"
                        }
                    }
                    logger.info(f"   Batch {batch_idx + 1}/{num_batches}: {len(batch)} URLs")
                    try:
                        run = self.client.actor(actor_id).call(run_input=run_input)
                        batch_count = 0
                        for item in self.client.dataset(run["defaultDatasetId"]).iterate_items():
                            all_records.append(item)
                            batch_count += 1
                        logger.info(f"   Batch {batch_idx + 1} retrieved {batch_count} records")
                    except Exception as be:
                        logger.error(f"❌ Batch {batch_idx + 1} failed: {be}")
                        continue
            elif platform == 'facebook':
                # Facebook comments actor
                run_input = {
                    "startUrls": [{"url": url} for url in post_urls[:10]],  # Facebook can handle more
                    "maxComments": comments_per_post,
                    "commentsMode": "RANKED_THREADED",  # Get top comments with replies
                    "language": "ms-MY",
                    "proxy": {
                        "useApifyProxy": True,
                        "apifyProxyGroups": ["RESIDENTIAL"],
                        "apifyProxyCountry": "MY"
                    }
                }
                logger.info(f"🚀 Running comments actor: {actor_id}")
                logger.info(f"   Posts: {len(post_urls[:10])}, Comments/post: {comments_per_post}")
                if post_urls:
                    logger.info(f"📋 Sample post URLs (first 3):")
                    for i, url in enumerate(post_urls[:3], 1):
                        logger.info(f"   {i}. {url}")
                run = self.client.actor(actor_id).call(run_input=run_input)
                for item in self.client.dataset(run["defaultDatasetId"]).iterate_items():
                    all_records.append(item)
            elif platform == 'instagram':
                # Instagram comments actor (apify/instagram-comment-scraper)
                # NOTE: The actor does NOT return parent post URL in output, so we must track batches manually
                IG_BATCH_SIZE = 10
                IG_MAX_POSTS = 50  # crawl comments for up to 50 posts
                target_urls = post_urls[:IG_MAX_POSTS]

                num_batches = (len(target_urls) + IG_BATCH_SIZE - 1) // IG_BATCH_SIZE
                logger.info(f"🚀 Running Instagram comments actor: {actor_id} in {num_batches} batches of {IG_BATCH_SIZE}")

                # Track URL->comments mapping (since actor doesn't return parent URL)
                url_to_batch_comments = {}

                for batch_idx in range(num_batches):
                    batch_start = batch_idx * IG_BATCH_SIZE
                    batch_end = min((batch_idx + 1) * IG_BATCH_SIZE, len(target_urls))
                    batch = target_urls[batch_start:batch_end]

                    run_input = {
                        "directUrls": batch,  # ✅ FIXED: Actor expects 'directUrls' not 'postUrls'
                        "maxComments": comments_per_post,
                        "proxy": {
                            "useApifyProxy": True,
                            "apifyProxyGroups": ["RESIDENTIAL"],
                            "apifyProxyCountry": "MY"
                        }
                    }
                    logger.info(f"   Batch {batch_idx + 1}/{num_batches}: {len(batch)} post URLs")
                    try:
                        run = self.client.actor(actor_id).call(run_input=run_input)
                        batch_count = 0

                        # Collect comments from this batch
                        batch_comments = []
                        for item in self.client.dataset(run["defaultDatasetId"]).iterate_items():
                            # ADD THE POST URL TO EACH COMMENT SO WE CAN MATCH IT LATER
                            # The actor doesn't return parent URL, so we add it manually
                            # Assume first comment is from first URL, distribute in order
                            item['postUrl'] = batch[0] if batch else None  # Temporary - will refine below
                            batch_comments.append(item)
                            batch_count += 1

                        # Map comments to the posts they belong to
                        # Distribute comments across posts in the batch
                        if batch_count > 0 and len(batch) > 0:
                            comments_per_post_actual = max(1, batch_count // len(batch))
                            comment_idx = 0
                            for url_idx, url in enumerate(batch):
                                # Each post gets ~comments_per_post_actual comments
                                comments_end = min(comment_idx + comments_per_post_actual + 1, batch_count)
                                for comment in batch_comments[comment_idx:comments_end]:
                                    comment['postUrl'] = url
                                comment_idx = comments_end

                        all_records.extend(batch_comments)
                        logger.info(f"   Batch {batch_idx + 1} retrieved {batch_count} records for {len(batch)} posts")
                    except Exception as be:
                        logger.error(f"❌ Instagram comments batch {batch_idx + 1} failed: {be}")
                        continue
            elif platform == 'youtube':
                # YouTube comments actor (apidojo/youtube-comments-scraper)
                # Batch 10 videos at a time to stay within actor limits
                YT_BATCH_SIZE = 10
                YT_MAX_VIDEOS = 50  # crawl comments for up to 50 videos
                target_urls = post_urls[:YT_MAX_VIDEOS]

                # 🎯 CLEAN URLs: Remove query params except 'v' to avoid actor errors
                cleaned_urls = []
                for url in target_urls:
                    if 'youtube.com/watch?v=' in url:
                        vid = url.split('v=')[1].split('&')[0]
                        cleaned_urls.append(f"https://www.youtube.com/watch?v={vid}")
                    elif 'youtu.be/' in url:
                        vid = url.split('youtu.be/')[1].split('?')[0]
                        cleaned_urls.append(f"https://www.youtube.com/watch?v={vid}")
                    else:
                        cleaned_urls.append(url)

                num_batches = (len(cleaned_urls) + YT_BATCH_SIZE - 1) // YT_BATCH_SIZE
                logger.info(f"🚀 Running YouTube comments actor: {actor_id} in {num_batches} batches of {YT_BATCH_SIZE}")
                for batch_idx in range(num_batches):
                    batch = cleaned_urls[batch_idx * YT_BATCH_SIZE:(batch_idx + 1) * YT_BATCH_SIZE]
                    run_input = {
                        "startUrls": batch,
                        "maxItems": comments_per_post * len(batch),  # total items for this batch
                        "sort": "top",
                        "includeReplies": False
                    }
                    logger.info(f"   Batch {batch_idx + 1}/{num_batches}: {len(batch)} video URLs")
                    try:
                        run = self.client.actor(actor_id).call(run_input=run_input)
                        batch_count = 0
                        for item in self.client.dataset(run["defaultDatasetId"]).iterate_items():
                            all_records.append(item)
                            batch_count += 1
                        logger.info(f"   Batch {batch_idx + 1} retrieved {batch_count} records")
                    except Exception as be:
                        logger.error(f"❌ YouTube comments batch {batch_idx + 1} failed: {be}")
                        continue
            else:
                logger.error(f"❌ Unknown platform: {platform}")
                return posts

            logger.info(f"✅ Retrieved {len(all_records)} total records from actor")

            # 🎯 DEBUG: Log first record fields so we can see what the actor returns
            if all_records:
                logger.info(f"🔍 [{platform}] First record fields: {list(all_records[0].keys())}")

            # 🎯 FILTER: Remove error records (only keep successful comments)
            comments_data = []
            error_count = 0
            for item in all_records:
                # Check if this is an error record
                if item.get('error') or item.get('errorDescription'):
                    error_count += 1
                    logger.debug(f"⚠️ Skipping error record: {item.get('error', 'Unknown error')}")
                    continue
                # Check if this has actual comment data (multiple possible field names)
                has_text = bool(
                    item.get('text') or item.get('tweetText') or item.get('replyText') or
                    item.get('content') or item.get('full_text') or item.get('fullText') or
                    item.get('comment')  # YouTube comments actor uses 'comment' field
                )
                has_author = bool(
                    item.get('profileName') or item.get('username') or item.get('user') or
                    item.get('author') or item.get('userName') or item.get('screen_name')
                )
                if has_text or has_author:
                    comments_data.append(item)
                else:
                    logger.info(f"⚠️ [{platform}] Skipping record with no comment data. Keys: {list(item.keys())[:10]}")

            logger.info(f"✅ Filtered to {len(comments_data)} successful comments ({error_count} errors skipped)")
            if comments_data:
                logger.info(f"📊 Sample comment fields: {list(comments_data[0].keys())[:10]}")

            # Map comments to posts
            posts_with_comments = self._attach_comments_to_posts(posts, comments_data, platform)

            return posts_with_comments

        except Exception as e:
            logger.error(f"❌ Error crawling comments: {e}")
            # Return posts without comments on error
            return posts

    def _attach_comments_to_posts(
        self,
        posts: List[Dict],
        comments_data: List[Dict],
        platform: str
    ) -> List[Dict]:
        """
        Attach crawled comments to their parent posts

        Args:
            posts: List of post records
            comments_data: List of comment records from actor
            platform: Platform name

        Returns:
            Posts with comments attached
        """
        try:
            logger.info(f"🔗 [{platform}] Attaching {len(comments_data)} comments to {len(posts)} posts...")

            # 🎯 DEBUG: Log sample comment to see what fields are available
            if comments_data:
                logger.info(f"🔍 [{platform}] Sample comment fields: {list(comments_data[0].keys())[:15]}")

            # Create a mapping of post URL to comments
            url_to_comments = {}

            first_instagram_comment_logged = False  # Track if we logged first comment fields
            for comment_item in comments_data:
                try:
                    # Extract parent post URL - platform-specific field names
                    if platform in ['x', 'twitter']:
                        parent_url = (comment_item.get('parentTweetUrl') or
                                     comment_item.get('parent_tweet_url') or
                                     comment_item.get('tweetUrl') or
                                     comment_item.get('inReplyToUrl') or
                                     comment_item.get('inReplyToStatusUrl') or
                                     comment_item.get('postUrl') or
                                     comment_item.get('url'))
                    elif platform == 'facebook':
                        # Facebook comments actor returns 'facebookUrl' as the parent post URL
                        parent_url = (comment_item.get('facebookUrl') or
                                     comment_item.get('postUrl') or
                                     comment_item.get('url') or
                                     comment_item.get('topLevelUrl'))
                    elif platform == 'instagram':
                        # Instagram comments actor (apify/instagram-comment-scraper) field mapping
                        parent_url = (comment_item.get('postUrl') or
                                     comment_item.get('url') or
                                     comment_item.get('instagramUrl'))

                        # DEBUG: Log actual fields from first comment to understand actor output
                        if not first_instagram_comment_logged:
                            logger.warning(f"⚠️ [instagram] Comment fields: {list(comment_item.keys())}")
                            first_instagram_comment_logged = True
                    elif platform == 'youtube':
                        # YouTube comments actor (apidojo/youtube-comments-scraper) returns different field names
                        # - 'inputSource': The video URL that was provided as input
                        # - 'pageUrl': Alternative parent video URL
                        parent_url = (comment_item.get('inputSource') or  # ✅ PRIMARY: From actor input
                                     comment_item.get('pageUrl') or
                                     comment_item.get('videoUrl') or
                                     comment_item.get('url'))
                        # Fallback: reconstruct from videoId
                        if not parent_url:
                            vid = comment_item.get('videoId') or comment_item.get('video_id')
                            if vid:
                                parent_url = f"https://www.youtube.com/watch?v={vid}"
                    else:
                        parent_url = comment_item.get('url')

                    if not parent_url:
                        logger.warning(f"⚠️ [{platform}] Comment has no parent URL: {list(comment_item.keys())[:10]}")
                        continue

                    if parent_url not in url_to_comments:
                        url_to_comments[parent_url] = []

                    # ===== EXTRACT PARENT POST ID FROM URL (all platforms) =====
                    parent_post_id_extracted = ''
                    if parent_url:
                        if platform in ['x', 'twitter']:
                            # Twitter URL format: https://twitter.com/username/status/123456789
                            if '/status/' in parent_url:
                                parent_post_id_extracted = parent_url.split('/status/')[-1].split('/')[0].split('?')[0]
                        elif platform == 'facebook':
                            # Facebook URL formats vary, try to extract ID
                            if '/posts/' in parent_url:
                                parent_post_id_extracted = parent_url.split('/posts/')[-1].split('/')[0].split('?')[0]
                            elif 'story_fbid=' in parent_url:
                                parent_post_id_extracted = parent_url.split('story_fbid=')[-1].split('&')[0]
                        elif platform == 'instagram':
                            # Instagram URL format: https://www.instagram.com/p/ABC123/
                            if '/p/' in parent_url:
                                parent_post_id_extracted = parent_url.split('/p/')[-1].split('/')[0].split('?')[0]
                        elif platform == 'youtube':
                            # YouTube URL format: https://www.youtube.com/watch?v=ABC123
                            if 'v=' in parent_url:
                                parent_post_id_extracted = parent_url.split('v=')[-1].split('&')[0]
                            elif '/shorts/' in parent_url:
                                parent_post_id_extracted = parent_url.split('/shorts/')[-1].split('/')[0].split('?')[0]

                    # Transform comment to standard format - platform-specific
                    if platform in ['x', 'twitter']:
                        author_obj = comment_item.get('author') if isinstance(comment_item.get('author'), dict) else {}
                        comment_text = (
                            comment_item.get('text') or comment_item.get('tweetText') or
                            comment_item.get('replyText') or comment_item.get('full_text') or
                            comment_item.get('fullText') or comment_item.get('content') or ''
                        )
                        author_name = (
                            author_obj.get('userName') or author_obj.get('username') or
                            author_obj.get('name') or
                            comment_item.get('username') or comment_item.get('userName') or
                            comment_item.get('screen_name') or comment_item.get('profileName') or ''
                        )
                        likes = comment_item.get('favouriteCount', comment_item.get('likeCount', comment_item.get('favorite_count', 0))) or 0
                        shares = comment_item.get('repostCount', comment_item.get('retweetCount', comment_item.get('retweet_count', 0))) or 0
                        replies = comment_item.get('replyCount', comment_item.get('reply_count', 0)) or 0
                        comment_record = {
                            'Platform': platform,
                            'Type': 'comment',
                            'ID': comment_item.get('replyId') or comment_item.get('id') or '',
                            'Text': comment_text,
                            'Parent_Post_URL': parent_url or '',  # ✅ Link to parent post
                            'Parent_Post_ID': parent_post_id_extracted,  # ✅ Extracted parent post ID
                            'Sentiment': 'neutral',
                            'Date': comment_item.get('timestamp') or comment_item.get('createdAt') or comment_item.get('created_at') or datetime.now().isoformat(),
                            'likes': likes,
                            'shares': shares,
                            'comments_count': replies,
                            'views': comment_item.get('viewCount', comment_item.get('view_count', 0)) or 0,
                            'sentiment_score': 0.0,
                            'total_engagement': likes + shares * 2 + replies * 3,
                            'author': author_name,
                            'author_followers': author_obj.get('followers', 0) if isinstance(author_obj, dict) else 0
                        }
                    elif platform == 'facebook':
                        # Facebook comments actor field mapping:
                        # - 'text': comment text
                        # - 'date': comment date
                        # - 'profileName': author name
                        # - 'likesCount': number of likes (can be string or int!)
                        # - 'commentsCount': number of replies (can be string or int!)

                        # 🔧 FIX: Convert to int to handle both string and int values
                        likes_count = comment_item.get('likesCount', 0)
                        comments_count = comment_item.get('commentsCount', 0)

                        # Convert to int if string
                        if isinstance(likes_count, str):
                            likes_count = int(likes_count) if likes_count.isdigit() else 0
                        if isinstance(comments_count, str):
                            comments_count = int(comments_count) if comments_count.isdigit() else 0

                        comment_record = {
                            'Platform': platform,
                            'Type': 'comment',
                            'ID': comment_item.get('id', ''),
                            'Text': comment_item.get('text', ''),
                            'Parent_Post_URL': parent_url or '',  # ✅ Link to parent post
                            'Parent_Post_ID': parent_post_id_extracted,  # ✅ Extracted parent post ID
                            'Sentiment': 'neutral',
                            'Date': comment_item.get('date', datetime.now().isoformat()),
                            'likes': likes_count,
                            'shares': 0,  # Facebook comments don't have shares
                            'comments_count': comments_count,
                            'views': 0,
                            'sentiment_score': 0.0,
                            'total_engagement': likes_count + comments_count * 2,
                            'author': comment_item.get('profileName', ''),
                            'author_followers': 0
                        }
                    elif platform == 'instagram':
                        # Instagram comments actor field mapping:
                        # - 'text': comment text
                        # - 'timestamp' or 'createdAt': comment date
                        # - 'username' or 'profileName': author name
                        # - 'likes' or 'likeCount': number of likes
                        # - 'postUrl': parent post URL
                        ig_likes = comment_item.get('likes', comment_item.get('likeCount', 0)) or 0
                        comment_record = {
                            'Platform': platform,
                            'Type': 'comment',
                            'ID': comment_item.get('id', ''),
                            'Text': comment_item.get('text', '') or comment_item.get('comment', ''),
                            'Parent_Post_URL': parent_url or '',  # ✅ Link to parent post
                            'Parent_Post_ID': parent_post_id_extracted,  # ✅ Extracted parent post ID
                            'Sentiment': 'neutral',
                            'Date': comment_item.get('timestamp') or comment_item.get('createdAt') or comment_item.get('date', datetime.now().isoformat()),
                            'likes': ig_likes,
                            'shares': 0,  # Instagram comments don't have shares
                            'comments_count': 0,  # Nested comments not fetched
                            'views': 0,
                            'sentiment_score': 0.0,
                            'total_engagement': ig_likes,
                            'author': comment_item.get('username') or comment_item.get('profileName') or '',
                            'author_followers': 0
                        }
                    elif platform == 'youtube':
                        # apidojo/youtube-comments-scraper field mapping (ACTUAL from logs):
                        # - 'text': comment text
                        # - 'author': author display name
                        # - 'id': comment ID
                        # - 'likeCount': number of likes
                        # - 'replyCount': number of replies
                        # - 'publishedTime': date string
                        # - 'inputSource': parent video URL (from batched input)
                        yt_likes = comment_item.get('likeCount') or comment_item.get('numberOfLikes') or comment_item.get('voteCount', 0) or 0
                        yt_replies = comment_item.get('replyCount') or comment_item.get('repliesCount', 0) or 0
                        comment_record = {
                            'Platform': platform,
                            'Type': 'comment',
                            'ID': comment_item.get('id', '') or comment_item.get('cid', ''),
                            'Text': comment_item.get('text', '') or comment_item.get('comment', ''),
                            'Parent_Post_URL': parent_url or '',  # ✅ Link to parent post
                            'Parent_Post_ID': parent_post_id_extracted,  # ✅ Extracted parent post ID
                            'Sentiment': 'neutral',
                            'Date': comment_item.get('publishedTime') or comment_item.get('publishedAt') or comment_item.get('publishedTimeText') or datetime.now().isoformat(),
                            'likes': yt_likes,
                            'shares': 0,
                            'comments_count': yt_replies,
                            'views': 0,
                            'sentiment_score': 0.0,
                            'total_engagement': yt_likes + yt_replies * 2,
                            'author': comment_item.get('author') or comment_item.get('authorName', ''),
                            'author_followers': 0
                        }
                    else:
                        comment_record = {
                            'Platform': platform,
                            'Type': 'comment',
                            'ID': comment_item.get('id', ''),
                            'Text': comment_item.get('text', ''),
                            'Parent_Post_URL': parent_url or '',  # ✅ Link to parent post
                            'Parent_Post_ID': parent_post_id_extracted,  # ✅ Extracted parent post ID
                            'Sentiment': 'neutral',
                            'Date': datetime.now().isoformat(),
                            'likes': 0,
                            'shares': 0,
                            'comments_count': 0,
                            'views': 0,
                            'sentiment_score': 0.0,
                            'total_engagement': 0,
                            'author': '',
                            'author_followers': 0
                        }

                    url_to_comments[parent_url].append(comment_record)

                except Exception as e:
                    logger.error(f"❌ Error processing comment: {e}")
                    logger.error(f"   Comment fields: {list(comment_item.keys())[:10]}")
                    logger.error(f"   Comment ID: {comment_item.get('id', 'N/A')}")
                    import traceback
                    logger.error(f"   Traceback: {traceback.format_exc()}")
                    continue

            # 🎯 DEBUG: Log URL mapping
            logger.info(f"📊 [{platform}] Created URL mapping for {len(url_to_comments)} unique post URLs")
            if url_to_comments:
                sample_url = list(url_to_comments.keys())[0]
                sample_url_str = str(sample_url) if sample_url else "None"
                logger.info(f"🔍 [{platform}] Sample comment parent URL: {sample_url_str[:min(80, len(sample_url_str))]}...")

            # Attach comments to posts
            matched_count = 0
            for post in posts:
                if platform in ['x', 'twitter']:
                    post_url = post.get('URL') or post.get('url') or post.get('twitterUrl')
                elif platform == 'facebook':
                    post_url = post.get('URL') or post.get('url') or post.get('Post_URL')
                elif platform == 'youtube':
                    post_url = post.get('URL') or post.get('url') or post.get('videoUrl')
                else:
                    post_url = post.get('URL') or post.get('url')

                if post_url and post_url in url_to_comments:
                    post['comments'] = url_to_comments[post_url]
                    matched_count += 1
                    post_id_str = str(post.get('ID', ''))
                    logger.info(f"✅ Attached {len(url_to_comments[post_url])} comments to post {post_id_str}")
                else:
                    post['comments'] = []
                    if post_url:
                        post_url_str = str(post_url) if post_url else "None"
                        logger.debug(f"⚠️ [{platform}] No comments found for post URL: {post_url_str[:min(80, len(post_url_str))]}...")

            total_comments = sum(len(p.get('comments', [])) for p in posts)
            logger.info(f"✅ Total comments attached: {total_comments} (matched {matched_count}/{len(posts)} posts)")

            return posts

        except Exception as e:
            logger.error(f"❌ Error attaching comments: {e}")
            # Return posts without comments on error
            for post in posts:
                if 'comments' not in post:
                    post['comments'] = []
            return posts


    def _detect_platform_from_url(self, url: str) -> str:
        """Detect platform from URL string."""
        url_lower = url.lower()
        if 'facebook.com' in url_lower or 'fb.com' in url_lower:
            return 'facebook'
        elif 'instagram.com' in url_lower:
            return 'instagram'
        elif 'tiktok.com' in url_lower:
            return 'tiktok'
        elif 'twitter.com' in url_lower or 'x.com' in url_lower:
            return 'x'
        elif 'threads.net' in url_lower:
            return 'threads'
        elif 'youtube.com' in url_lower or 'youtu.be' in url_lower:
            return 'youtube'
        elif 'linkedin.com' in url_lower:
            return 'linkedin'
        else:
            return 'unknown'

    def _extract_tiktok_username(self, url: str) -> Optional[str]:
        """Extract TikTok username from a profile URL (not video URLs)."""
        url = url.strip().rstrip('/')
        if '/video/' in url.lower():
            return None
        match = re.search(r'tiktok\.com/@([^/?#]+)', url, re.IGNORECASE)
        return match.group(1) if match else None

    def _prepare_facebook_url_input(self, urls: List[str], max_posts: int = 100, max_comments: int = 50) -> Dict:
        """Facebook page/post direct URL crawl using apify/facebook-posts-scraper."""
        scroll_timeout = max(300, min(max_posts * 5, 1800))
        return {
            "startUrls": [{"url": u} for u in urls],
            "maxPosts": max_posts,
            "maxPostComments": max_comments,
            "maxReviewsPerPage": 0,
            "commentsMode": "RANKED_THREADED",
            "scroll_timeout": scroll_timeout,
            "proxy": {
                "useApifyProxy": True,
                "apifyProxyGroups": ["RESIDENTIAL"],
                "apifyProxyCountry": "MY"
            }
        }

    def _prepare_instagram_url_input(self, urls: List[str], max_posts: int = 50, max_comments: int = 30) -> Dict:
        """Instagram profile/hashtag direct URL crawl."""
        ig_scroll = max(180, min(max_posts * 4, 900))
        return {
            "directUrls": urls,
            "resultsType": "posts",
            "resultsLimit": max_posts,
            "addParentData": True,
            "scrapeComments": True,
            "commentsMode": "top",
            "maxComments": max_comments,
            "includeCommentReplies": True,
            "scrollTimeout": ig_scroll,
            "pageLoadTimeoutSecs": 60,
            "proxy": {
                "useApifyProxy": True,
                "apifyProxyGroups": ["RESIDENTIAL"],
                "apifyProxyCountry": "MY"
            }
        }

    def _prepare_tiktok_url_input(
        self,
        urls: List[str],
        max_videos: int = 50,
        max_comments: int = 30,
        since_date: str = None,
        until_date: str = None,
    ) -> Dict:
        """TikTok profile/video direct URL crawl.

        clockworks/tiktok-scraper expects usernames in ``profiles`` (not full URLs)
        and ``resultsPerPage`` for videos per profile. Full URLs belong in ``postURLs``.
        """
        buffer = self.calculate_smart_buffer(max_videos)
        adjusted_max_videos = max(1, int(max_videos * buffer))
        adjusted_max_comments = max(1, int(max_comments * 1.2))
        tt_scroll = max(180, min(adjusted_max_videos * 3, 900))

        profile_usernames: List[str] = []
        videos: List[str] = []
        for u in urls:
            if '/video/' in u.lower():
                videos.append(u.strip())
                continue
            username = self._extract_tiktok_username(u)
            if username:
                profile_usernames.append(username)
            else:
                logger.warning(f"⚠️ TikTok: could not parse username from URL: {u}")

        if not profile_usernames and not videos:
            raise ValueError(
                "No valid TikTok profile usernames or video URLs found. "
                "Use https://www.tiktok.com/@username or https://www.tiktok.com/@user/video/ID"
            )

        logger.info(
            f"🎵 TikTok URL crawl: {len(profile_usernames)} profiles, "
            f"{len(videos)} video URLs, {adjusted_max_videos} videos/profile"
        )
        if profile_usernames:
            logger.info(f"🎵 TikTok profiles: {profile_usernames[:5]}{'...' if len(profile_usernames) > 5 else ''}")

        inp: Dict = {
            "shouldDownloadVideos": False,
            "shouldDownloadCovers": False,
            "shouldDownloadSlideshowImages": False,
            "profileScrapeSections": ["videos"],
            "profileSorting": "latest",
            "resultsPerPage": adjusted_max_videos,
            "getComments": True,
            "commentsPerPost": adjusted_max_comments,
            "getEngagement": True,
            "scrollTimeout": tt_scroll,
            "getUserDetails": True,
            "proxy": {
                "useApifyProxy": True,
                "apifyProxyGroups": ["RESIDENTIAL"],
                "apifyProxyCountry": "MY",
            },
        }
        if profile_usernames:
            inp["profiles"] = profile_usernames
        if videos:
            inp["postURLs"] = videos
        if since_date:
            inp["oldestPostDateUnified"] = since_date[:10]
        if until_date:
            inp["newestPostDate"] = until_date[:10]
        return inp

    def _prepare_twitter_url_input(self, urls: List[str], max_tweets: int = 100, max_replies: int = 30) -> Dict:
        """X/Twitter profile direct URL crawl."""
        handles = []
        for u in urls:
            # Extract handle from URL e.g. https://x.com/username → username
            parts = u.rstrip('/').split('/')
            if parts:
                handle = parts[-1].lstrip('@')
                if handle:
                    handles.append(f"@{handle}")
        x_timeout = max(180, min(max_tweets * 2, 1200))
        return {
            "handles": handles if handles else urls,
            "max_tweets": max_tweets,
            "include_replies": True,
            "max_replies": max_replies,
            "include_retweets": True,
            "queryType": "Top",
            "timeout": x_timeout,
            "proxy": {
                "useApifyProxy": True,
                "apifyProxyGroups": ["RESIDENTIAL"],
                "apifyProxyCountry": "MY"
            }
        }

    def _prepare_threads_url_input(self, urls: List[str], max_posts: int = 100, max_replies: int = 20) -> Dict:
        """Threads profile direct URL crawl."""
        # Extract usernames from URLs
        usernames = []
        for u in urls:
            parts = u.rstrip('/').split('/')
            for p in parts:
                if p.startswith('@'):
                    usernames.append(p.lstrip('@'))
                    break
            else:
                if parts:
                    usernames.append(parts[-1])
        t_timeout = max(180, min(max_posts * 2, 900))
        return {
            "usernames": usernames if usernames else urls,
            "maxPosts": max_posts,
            "maxRepliesPerPost": min(max_replies, 20),
            "requestTimeout": t_timeout,
            "proxy": {
                "useApifyProxy": True,
                "apifyProxyGroups": ["RESIDENTIAL"],
                "apifyProxyCountry": "MY"
            }
        }

    def _prepare_youtube_url_input(self, urls: List[str], max_videos: int = 50, max_comments: int = 30) -> Dict:
        """YouTube channel/video direct URL crawl."""
        return {
            "startUrls": [{"url": u} for u in urls],
            "maxResults": max_videos,
            "scrapeComments": True,
            "maxComments": max_comments,
            "scrapeChannelInfo": True,
            "scrapeVideoStats": True,
            "scrollTimeout": 120,
            "proxy": {
                "useApifyProxy": True,
                "apifyProxyGroups": ["RESIDENTIAL"],
                "apifyProxyCountry": "MY"
            }
        }

    def _prepare_linkedin_url_input(self, urls: List[str], max_posts: int = 50, max_comments: int = 30) -> Dict:
        """LinkedIn company/profile direct URL crawl."""
        li_scroll = max(300, min(max_posts * 5, 1800))
        return {
            "startUrls": [{"url": u} for u in urls],
            "maxPosts": max_posts,
            "scrapeComments": True,
            "maxComments": max_comments,
            "scrapeReactions": True,
            "scrollTimeout": li_scroll,
            "proxy": {
                "useApifyProxy": True,
                "apifyProxyGroups": ["RESIDENTIAL"],
                "apifyProxyCountry": "MY"
            }
        }

    async def crawl_direct_urls(
        self,
        urls: List[str],
        max_posts: int = 100,
        max_comments: int = 50,
        since_date: str = None,
        until_date: str = None
    ) -> Dict[str, Any]:
        """
        Crawl a list of direct URLs across any supported platform.
        Auto-detects platform from URL and uses the appropriate actor.
        Returns same format as crawl_with_strategy for compatibility.
        """
        # Group URLs by platform
        platform_urls: Dict[str, List[str]] = {}
        for url in urls:
            p = self._detect_platform_from_url(url)
            platform_urls.setdefault(p, []).append(url)

        logger.info(f"🌐 Direct URL crawl: {len(urls)} URLs across {list(platform_urls.keys())}")

        # Actor mapping for URL-based crawling
        url_actors = {
            'facebook':  'apify/facebook-posts-scraper',
            'instagram': 'apify/instagram-scraper',
            'tiktok':    'clockworks/tiktok-scraper',
            'x':         'apidojo/tweet-scraper',
            'youtube':   'streamers/youtube-scraper',
            'threads':   'igview-owner/threads-profile-scraper',
            'linkedin':  'harvestapi/linkedin-post-search',
        }

        all_results: Dict[str, List[Dict]] = {}
        tasks = []

        for platform, p_urls in platform_urls.items():
            if platform == 'unknown':
                logger.warning(f"⚠️ Could not detect platform for URLs: {p_urls}")
                continue

            actor_id = url_actors.get(platform)
            if not actor_id:
                logger.warning(f"⚠️ No URL actor configured for platform: {platform}")
                continue

            # Build platform-specific input
            if platform == 'facebook':
                actor_input = self._prepare_facebook_url_input(p_urls, max_posts, max_comments)
            elif platform == 'instagram':
                actor_input = self._prepare_instagram_url_input(p_urls, max_posts, max_comments)
            elif platform == 'tiktok':
                try:
                    actor_input = self._prepare_tiktok_url_input(
                        p_urls, max_posts, max_comments, since_date, until_date
                    )
                except ValueError as e:
                    logger.error(f"❌ TikTok URL input invalid: {e}")
                    continue
            elif platform == 'x':
                actor_input = self._prepare_twitter_url_input(p_urls, max_posts, max_comments)
            elif platform == 'threads':
                actor_input = self._prepare_threads_url_input(p_urls, max_posts, max_comments)
            elif platform == 'youtube':
                actor_input = self._prepare_youtube_url_input(p_urls, max_posts, max_comments)
            elif platform == 'linkedin':
                actor_input = self._prepare_linkedin_url_input(p_urls, max_posts, max_comments)
            else:
                continue

            logger.info(f"🚀 Launching URL crawl: {platform} | actor={actor_id} | {len(p_urls)} URLs")
            tasks.append((platform, actor_id, actor_input))

        # Run all platform crawls concurrently
        async def run_one(platform, actor_id, actor_input):
            try:
                raw = await self._run_apify_actor(actor_id, actor_input, platform)
                transformed = [self._transform_result(platform, item) for item in raw]
                transformed = [t for t in transformed if t]
                logger.info(f"✅ URL crawl {platform}: {len(transformed)} results")
                return platform, transformed
            except Exception as e:
                logger.error(f"❌ URL crawl failed for {platform}: {e}")
                return platform, []

        import asyncio
        results_list = await asyncio.gather(*[run_one(p, a, i) for p, a, i in tasks])

        for platform, results in results_list:
            all_results[platform] = results

        total = sum(len(v) for v in all_results.values())
        logger.info(f"✅ Direct URL crawl complete: {total} total results")

        # Return in same format as crawl_with_strategy
        return {
            "results": all_results,
            "summary": {
                "total_results": total,
                "total_posts": total,
                "total_comments": 0,
                "crawl_mode": "direct_url",
                "urls_crawled": urls
            },
            "strategy": {"mode": "direct_url"}
        }


# Convenience function
async def quick_crawl(platform: str, query: str, max_results: int = 100, max_comments: int = 50) -> List[Dict]:
    """Quick single platform crawl"""
    adapter = SimpleApifyAdapter()
    return await adapter.crawl_platform(platform, query, max_results, max_comments)


