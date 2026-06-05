"""
Simple Apify API Adapter for InsightPulse
==========================================

Direct Apify REST API integration without complex dependencies.
Uses simple HTTP requests to call Apify actors and collect data.

Author: InsightPulse Team
Date: 2026-02-07
"""

import os
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


class SimpleApifyAdapter:
    """
    Simplified Apify adapter using direct REST API calls
    """
    
    def __init__(self, llm_service=None):
        self.apify_token = os.getenv('APIFY_API_TOKEN')
        self.apify_proxy_password = os.getenv('APIFY_PROXY_PASSWORD')
        self.serpapi_key = os.getenv('SERPAPI_KEY')
        self.data_dir = Path("data/smart_crawlers")
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Initialize Apify client
        self.client = ApifyClient(self.apify_token)

        # Platform to Apify Actor ID mapping (from 2026_Crawler settings.py)
        self.actor_map = {
            'facebook': 'danek/facebook-search-ppr',  # ✅ Search-capable actor for posts
            'instagram': 'apify/instagram-scraper',
            'twitter': 'kaitoeasyapi/twitter-x-data-tweet-scraper-pay-per-result-cheapest',
            'x': 'kaitoeasyapi/twitter-x-data-tweet-scraper-pay-per-result-cheapest',
            'tiktok': 'clockworks/tiktok-scraper',
            'youtube': 'streamers/youtube-scraper',  # ✅ UPDATED: Apify YouTube scraper with comments
            'google': 'apify/google-search-scraper',
            'news': 'serpapi',  # News articles (no comments by nature)
            'linkedin': 'testdepth/linkedin-post-search',  # ✅ UPDATED: LinkedIn posts with comments
            'shopee': 'ecomscrape/shopee-scraper',  # ✅ UPDATED: Shopee products with reviews
            'lazada': 'ecomscrape/lazada-reviews-scraper'  # ✅ UPDATED: Lazada products with reviews
        }

        # 🎯 2-ACTOR STRATEGY: Separate comments actors for platforms that need it
        self.comments_actor_map = {
            'x': 'scraper_one/x-post-replies-scraper',
            'twitter': 'scraper_one/x-post-replies-scraper',
            'facebook': 'apify/facebook-comments-scraper'  # ✅ NEW: Facebook comments actor
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
        🎯 2-ACTOR STRATEGY: This actor gets POSTS only, comments will be fetched separately
        """
        input_data = {
            "query": query,  # Search query
            "search_type": "posts",  # Search for posts (not pages/groups)
            "max_posts": max_results,  # ✅ FIXED: Actor expects 'max_posts' not 'maxResults'
            "language": "ms",  # Malaysian context
            "proxy": {
                "useApifyProxy": True,
                "apifyProxyGroups": ["RESIDENTIAL"],
                "apifyProxyCountry": "MY"
            }
        }
        return input_data

    def _prepare_instagram_input(self, query: str, max_results: int, max_comments: int = 100, comment_sort: str = "top") -> Dict[str, Any]:
        """Prepare input for Instagram actor - SMART hashtag detection"""
        # Instagram works BEST with hashtags!
        # SMART LOGIC:
        # 1. If user types "#hashtag" → use as-is ✅
        # 2. If user types "word1 word2 word3" → auto-convert to "#word3" (last word) ✅

        search_query = query.strip()

        # Check if user already provided a hashtag
        if '#' in search_query:
            # User provided hashtag - use as-is!
            # Extract the hashtag (first one if multiple)
            hashtag = [word for word in search_query.split() if word.startswith('#')][0]
            logger.info(f"📸 Instagram: User provided hashtag '{hashtag}' - using as-is")
        else:
            # No hashtag - auto-convert last word to hashtag
            words = search_query.split()
            main_keyword = words[-1] if words else search_query  # Get last word (e.g., "PBT")
            hashtag = f"#{main_keyword}"
            logger.info(f"📸 Instagram: Auto-converted '{search_query}' → '{hashtag}'")

        return {
            "search": hashtag,  # Use hashtag (user-provided or auto-generated)
            "searchType": "hashtag",  # ✅ Hashtag search works best for Instagram
            "resultsLimit": max_results,
            "addParentData": True,
            "scrapeComments": True,  # ✅ Comments enabled
            "maxComments": max_comments,  # ✅ Dynamic comment limit
            "commentSort": comment_sort  # ✅ "top_comments" or "recent"
        }

    def _prepare_twitter_input(self, query: str, max_results: int, max_comments: int = 50, comment_sort: str = "top") -> Dict[str, Any]:
        """Prepare input for Twitter actor with smart reply sampling"""
        return {
            "searchTerms": [query],  # ✅ FIX: Actor expects "searchTerms" array, not "search" string
            "max_tweets": max_results,
            "queryType": "Top",  # ✅ Get TOP posts (most engagement) instead of Latest
            "include_replies": True,  # ✅ Replies enabled (Twitter's version of comments)
            "max_replies": max_comments,  # ✅ Dynamic reply limit
            "reply_sort": comment_sort,  # ✅ "top" (most liked/retweeted) or "recent"
            "include_retweets": True,  # ✅ Track retweets (shares)
            "include_likes": True,  # ✅ Track likes (reactions)
            "filter:has_engagement": True,  # ✅ Only posts with engagement
            "min_replies": 1  # ✅ Only posts with at least 1 reply
        }

    def _prepare_tiktok_input(self, query: str, max_results: int, max_comments: int = 100, comment_sort: str = "top") -> Dict[str, Any]:
        """Prepare input for TikTok actor with smart comment sampling"""
        # clockworks/tiktok-scraper expects a single search query, not multiple
        # We'll handle multiple keywords at a higher level

        return {
            "searchQueries": [query],  # Single query (multiple handled by crawl_platform_with_ai_keywords)
            "resultsPerPage": max_results,  # ✅ FIX: Use resultsPerPage instead of maxVideos
            "maxVideos": max_results,  # Keep for compatibility
            "shouldDownloadVideos": False,
            "shouldDownloadCovers": False,
            "shouldDownloadSlideshowImages": False,
            "getComments": True,  # ✅ Comments enabled
            "commentsPerPost": max_comments,  # ✅ Dynamic comment limit
            "commentSort": comment_sort,  # ✅ "top" (most liked) or "recent"
            "getEngagement": True,  # ✅ Get likes, shares, views
            "getUserDetails": True
        }

    def _prepare_youtube_input(self, query: str, max_results: int, max_comments: int = 50, comment_sort: str = "top") -> Dict[str, Any]:
        """Prepare input for YouTube actor (streamers/youtube-scraper) with comments + engagement"""
        return {
            "searchKeywords": query,  # ✅ Search query
            "maxResults": max_results,  # ✅ Max videos
            "scrapeComments": True,  # ✅ Enable comments
            "maxComments": max_comments,  # ✅ Comments per video
            "sortCommentsBy": comment_sort,  # ✅ "top" or "time" (recent)
            "scrapeChannelInfo": True,  # ✅ Get channel details
            "scrapeVideoStats": True,  # ✅ Get views, likes, etc.
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

    def _prepare_linkedin_input(self, query: str, max_results: int, max_comments: int = 50, comment_sort: str = "top") -> Dict[str, Any]:
        """
        Prepare input for LinkedIn actor (testdepth/linkedin-post-search)
        STRATEGY: Search LinkedIn posts + scrape comments + engagement
        """
        return {
            "searchQuery": query,  # ✅ Search query
            "maxPosts": max_results,  # ✅ Max posts to scrape
            "scrapeComments": True,  # ✅ Enable comments
            "maxCommentsPerPost": max_comments,  # ✅ Comments per post
            "sortBy": "RELEVANCE",  # ✅ Sort by relevance
            "scrapeReactions": True,  # ✅ Get reactions (like, celebrate, support, love, insightful, curious)
            "scrapeEngagement": True,  # ✅ Get likes, shares, comments count
            "proxy": {
                "useApifyProxy": True,
                "apifyProxyGroups": ["RESIDENTIAL"]
            }
        }

    def _prepare_shopee_input(self, query: str, max_results: int, max_comments: int = 50, comment_sort: str = "top") -> Dict[str, Any]:
        """
        Prepare input for Shopee scraper (ecomscrape/shopee-scraper)
        Scrapes products + reviews (Shopee's version of comments) + ratings
        """
        return {
            "searchKeyword": query,  # ✅ Search query
            "maxProducts": max_results,  # ✅ Max products
            "country": "MY",  # ✅ Malaysia
            "scrapeReviews": True,  # ✅ Enable reviews (comments)
            "maxReviewsPerProduct": max_comments,  # ✅ Reviews per product
            "sortReviewsBy": comment_sort,  # ✅ "top" (most helpful) or "recent"
            "scrapeRatings": True,  # ✅ Get star ratings
            "scrapeSales": True,  # ✅ Get sales count (engagement)
            "proxy": {
                "useApifyProxy": True,
                "apifyProxyGroups": ["RESIDENTIAL"],
                "apifyProxyCountry": "MY"
            }
        }

    def _prepare_lazada_input(self, query: str, max_results: int, max_comments: int = 50, comment_sort: str = "top") -> Dict[str, Any]:
        """
        Prepare input for Lazada scraper (ecomscrape/lazada-reviews-scraper)
        Scrapes products + reviews (Lazada's version of comments) + ratings
        """
        return {
            "searchKeyword": query,  # ✅ Search query
            "maxProducts": max_results,  # ✅ Max products
            "country": "MY",  # ✅ Malaysia
            "scrapeReviews": True,  # ✅ Enable reviews (comments)
            "maxReviewsPerProduct": max_comments,  # ✅ Reviews per product
            "sortReviewsBy": comment_sort,  # ✅ "top" (most helpful) or "recent"
            "scrapeRatings": True,  # ✅ Get star ratings
            "scrapeSales": True,  # ✅ Get sales count (engagement)
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
            'linkedin': self._prepare_linkedin_input,
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

    async def _run_apify_actor(self, actor_id: str, actor_input: Dict[str, Any]) -> List[Dict]:
        """
        Run an Apify actor and wait for results

        Args:
            actor_id: Apify actor ID (e.g., 'danek/facebook-search-ppr')
            actor_input: Input configuration for the actor

        Returns:
            List of results from the actor
        """
        try:
            logger.info(f"🚀 Running Apify actor: {actor_id}")

            # Add proxy configuration if not present
            if "proxy" not in actor_input:
                actor_input["proxy"] = self._get_proxy_config()

            # Run the actor using official client
            run = self.client.actor(actor_id).call(
                run_input=actor_input,
                timeout_secs=300  # 5 minutes
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
                post_url = item.get('url') or item.get('twitterUrl') or item.get('URL') or item.get('link') or ''

                # ===== CREATE POST RECORD =====
                post_record = {
                    'Platform': platform,
                    'Type': 'post',
                    'ID': post_id,
                    'Text': text_content,
                    'URL': post_url,  # ✅ Add URL field for comments crawling
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
                total_posts += 1

                # ===== EXTRACT COMMENTS =====
                comments = self._extract_comments(platform, item, post_id, max_comments)
                transformed.extend(comments)
                total_comments += len(comments)

            except Exception as e:
                logger.warning(f"⚠️ Error transforming result: {e}")
                continue

        logger.info(f"📊 Transformed {total_posts} posts + {total_comments} comments = {len(transformed)} total records")
        return transformed

    def _extract_text_content(self, platform: str, item: Dict) -> str:
        """Extract text content based on platform-specific field names"""
        # Try multiple field names in order of priority
        text_fields = [
            'text', 'content', 'caption', 'description', 'message',
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

    def _fetch_comments_from_dataset(self, platform: str, dataset_ref: str, post_id: str, max_comments: int = 500) -> List[Dict]:
        """
        Fetch comments from a separate Apify dataset

        Args:
            platform: Platform name (facebook, tiktok, instagram, etc.)
            dataset_ref: Dataset URL or ID
            post_id: Post ID for reference
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

    def _extract_comments(self, platform: str, item: Dict, post_id: str, max_comments: int = 500) -> List[Dict]:
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
                comments_from_dataset = self._fetch_comments_from_dataset(platform, dataset_url or dataset_id, post_id, max_comments)
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
        """Save crawl results to CSV (RAW data without sentiment) - Posts and Comments in ONE file"""
        try:
            # Save to data/raw directory
            raw_dir = Path("data/raw")
            raw_dir.mkdir(parents=True, exist_ok=True)

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

            # Save everything in ONE file with simple naming: X.csv
            if all_records:
                # Simple filename: platform.csv (e.g., X.csv, facebook.csv)
                filename = f"{platform.upper()}.csv"
                filepath = raw_dir / filename
                df = pd.DataFrame(all_records)
                df.to_csv(filepath, index=False, encoding='utf-8')

                # Count posts and comments
                posts_count = len([r for r in all_records if r.get('Type') == 'post'])
                comments_count = len([r for r in all_records if r.get('Type') == 'comment'])

                logger.info(f"💾 RAW DATA saved: {posts_count} posts + {comments_count} comments = {len(all_records)} total records")
                logger.info(f"💾 File: {filepath}")
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

        if platform.lower() in ['x', 'twitter', 'facebook'] and all_results:
            logger.info(f"🔍 [{platform}] Auto-crawling comments for {len(all_results)} posts...")
            try:
                posts_with_comments = await self._crawl_comments_for_posts(
                    platform=platform.lower(),
                    posts=all_results,
                    comments_per_post=min(max_comments, 10)  # Limit to 10 comments per post
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

            # Map comment sampling to sort strategy
            comment_sort_map = {
                "smart": "top",      # Get top comments (most liked/replied)
                "top_only": "top",   # Only top comments
                "recent_only": "recent",  # Only recent comments
                "random": "top"      # Default to top for random
            }
            comment_sort = comment_sort_map.get(comment_sampling, "top")

            # Get the actor/engine for this platform
            actor_id = self.actor_map.get(platform)

            if not actor_id:
                logger.warning(f"⚠️ No actor configured for {platform}")
                return []

            # Check if using SerpAPI
            if actor_id == 'serpapi':
                # Prepare SerpAPI input with max_comments and comment_sort
                actor_input = self._prepare_actor_input(platform, query, max_results, max_comments, comment_sort)

                # Run SerpAPI
                results = await self._run_serpapi(
                    actor_input.get('engine'),
                    actor_input
                )
            else:
                # Prepare Apify input with max_comments and comment_sort
                actor_input = self._prepare_actor_input(platform, query, max_results, max_comments, comment_sort)

                # Run Apify actor
                results = await self._run_apify_actor(actor_id, actor_input)

            # Transform to standard format
            # ✅ OPTIMIZATION: Pass max_comments to enable dynamic comment limit
            transformed = self._transform_results(platform, results, max_comments)

            # ⚠️ DON'T save here - will be saved later after comments are attached
            if transformed:
                logger.info(f"✅ Collected {len(transformed)} records from {platform}")

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
                    platforms_count=len(platforms)
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

            # Crawl each platform with its AI-generated keywords
            results = {}
            for platform in platforms:
                platform_lower = platform.lower()
                keywords = ai_keywords.get(platform_lower, [query])

                if len(keywords) > 1:
                    # Multiple keywords: use combined search
                    platform_results = await self.crawl_platform_with_ai_keywords(
                        platform=platform_lower,
                        query=query,
                        ai_keywords=keywords,
                        max_results=posts_target,  # 🎯 Use posts target
                        max_comments=comments_per_post,  # 🎯 Use calculated comments per post
                        comment_sampling=comment_sampling
                    )
                else:
                    # Single keyword: use direct search
                    platform_results = await self.crawl_platform(
                        platform=platform_lower,
                        query=keywords[0] if keywords else query,
                        max_results=posts_target,  # 🎯 Use posts target
                        max_comments=comments_per_post,  # 🎯 Use calculated comments per post
                        comment_sampling=comment_sampling
                    )

                # 🎯 STEP 2: Filter and rank posts by engagement (if strategy available)
                if CRAWL_STRATEGY_AVAILABLE and platform_results:
                    filtered_results = CrawlStrategy.filter_posts_by_engagement(
                        posts=platform_results,
                        target_count=posts_target
                    )
                    results[platform_lower] = filtered_results

                    logger.info(f"✅ [{platform_lower}] Filtered to {len(filtered_results)} top posts")
                else:
                    results[platform_lower] = platform_results

                # 🎯 STEP 3: AUTOMATICALLY CRAWL COMMENTS for 2-actor platforms (X/Twitter, Facebook)
                if platform_lower in ['x', 'twitter', 'facebook'] and platform_results:
                    logger.info(f"🔍 [{platform_lower}] Auto-crawling comments for {len(platform_results)} posts...")
                    try:
                        posts_with_comments = await self._crawl_comments_for_posts(
                            platform=platform_lower,
                            posts=platform_results,
                            comments_per_post=min(comments_per_post, 10)  # Limit to 10 comments per post
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
        analysis_type: str = "general"
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

            # 🎯 STEP 1: Calculate strategy
            strategy = CrawlStrategy.calculate_distribution(
                dataset_size=dataset_size,
                platforms_count=len(platforms)
            )

            logger.info(f"📊 Strategy: {strategy['total_posts']} posts + {strategy['total_comments']} comments")

            # 🎯 STEP 2: Crawl posts AND comments for all platforms
            logger.info(f"🔍 Phase 1: Crawling posts with automatic comments...")
            try:
                posts_results = await self.crawl_multi_platform_with_ai(
                    platforms=platforms,
                    query=query,
                    max_results=strategy['posts_per_platform'],
                    max_comments=strategy['comments_per_post'],  # ✅ Enable automatic comments crawling
                    analysis_type=analysis_type
                )
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
            if platform not in ['x', 'twitter', 'facebook']:
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
                else:
                    reply_count = 0

                # 🎯 For Facebook: Crawl comments even if count is 0 (actor might not report accurate counts)
                should_crawl = False
                if platform == 'facebook':
                    # Always try to crawl comments for Facebook posts
                    should_crawl = True
                elif reply_count > 0:
                    should_crawl = True

                if should_crawl:
                    if platform in ['x', 'twitter']:
                        url = post.get('URL') or post.get('url') or post.get('twitterUrl')
                    elif platform == 'facebook':
                        url = post.get('URL') or post.get('url') or post.get('Post_URL')
                    else:
                        url = None

                    if url:
                        # 🎯 FILTER: Skip Facebook Reels URLs (comments actor can't scrape them)
                        if platform == 'facebook' and '/reel/' in url:
                            logger.debug(f"⏭️ Skipping Facebook Reel URL: {url}")
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
            if platform in ['x', 'twitter']:
                # X/Twitter comments actor
                run_input = {
                    "postUrls": post_urls[:5],  # ✅ Limit to 5 posts (actor constraint)
                    "maxRepliesPerPost": comments_per_post,
                    "sortBy": "top",
                    "proxy": {
                        "useApifyProxy": True,
                        "apifyProxyGroups": ["RESIDENTIAL"],
                        "apifyProxyCountry": "MY"
                    }
                }
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
            else:
                logger.error(f"❌ Unknown platform: {platform}")
                return posts

            logger.info(f"🚀 Running comments actor: {actor_id}")
            logger.info(f"   Posts: {len(post_urls[:10])}, Comments/post: {comments_per_post}")

            # 🎯 Log sample URLs for debugging
            if post_urls:
                logger.info(f"📋 Sample post URLs (first 3):")
                for i, url in enumerate(post_urls[:3], 1):
                    logger.info(f"   {i}. {url}")

            # Run the actor
            run = self.client.actor(actor_id).call(run_input=run_input)

            # Get results
            all_records = []
            for item in self.client.dataset(run["defaultDatasetId"]).iterate_items():
                all_records.append(item)

            logger.info(f"✅ Retrieved {len(all_records)} total records from actor")

            # 🎯 FILTER: Remove error records (only keep successful comments)
            comments_data = []
            error_count = 0
            for item in all_records:
                # Check if this is an error record
                if item.get('error') or item.get('errorDescription'):
                    error_count += 1
                    logger.debug(f"⚠️ Skipping error record: {item.get('error', 'Unknown error')}")
                    continue
                # Check if this has actual comment data
                if item.get('text') or item.get('profileName'):
                    comments_data.append(item)
                else:
                    logger.debug(f"⚠️ Skipping record with no comment data: {list(item.keys())[:5]}")

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

            for comment_item in comments_data:
                try:
                    # Extract parent post URL - platform-specific field names
                    if platform in ['x', 'twitter']:
                        parent_url = (comment_item.get('parentTweetUrl') or
                                     comment_item.get('tweetUrl') or
                                     comment_item.get('url') or
                                     comment_item.get('postUrl'))
                    elif platform == 'facebook':
                        # Facebook comments actor returns 'facebookUrl' as the parent post URL
                        parent_url = (comment_item.get('facebookUrl') or
                                     comment_item.get('postUrl') or
                                     comment_item.get('url') or
                                     comment_item.get('topLevelUrl'))
                    else:
                        parent_url = comment_item.get('url')

                    if not parent_url:
                        logger.warning(f"⚠️ [{platform}] Comment has no parent URL: {list(comment_item.keys())[:10]}")
                        continue

                    if parent_url not in url_to_comments:
                        url_to_comments[parent_url] = []

                    # Transform comment to standard format - platform-specific
                    if platform in ['x', 'twitter']:
                        comment_record = {
                            'Platform': platform,
                            'Type': 'comment',
                            'ID': comment_item.get('id', ''),
                            'Text': comment_item.get('text', ''),
                            'Sentiment': 'neutral',
                            'Date': comment_item.get('createdAt', datetime.now().isoformat()),
                            'likes': comment_item.get('likeCount', 0),
                            'shares': comment_item.get('retweetCount', 0),
                            'comments_count': comment_item.get('replyCount', 0),
                            'views': comment_item.get('viewCount', 0),
                            'sentiment_score': 0.0,
                            'total_engagement': (
                                comment_item.get('likeCount', 0) +
                                comment_item.get('retweetCount', 0) * 2 +
                                comment_item.get('replyCount', 0) * 3
                            ),
                            'author': comment_item.get('author', {}).get('userName', ''),
                            'author_followers': comment_item.get('author', {}).get('followers', 0)
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
                    else:
                        comment_record = {
                            'Platform': platform,
                            'Type': 'comment',
                            'ID': comment_item.get('id', ''),
                            'Text': comment_item.get('text', ''),
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


# Convenience function
async def quick_crawl(platform: str, query: str, max_results: int = 100, max_comments: int = 50) -> List[Dict]:
    """Quick single platform crawl"""
    adapter = SimpleApifyAdapter()
    return await adapter.crawl_platform(platform, query, max_results, max_comments)


