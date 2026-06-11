"""
Crawling Strategy Calculator
=============================

Implements the 30:70 (Posts:Comments) ratio strategy with adaptive algorithms.

Author: InsightPulse Team
Date: 2026-02-09
"""

import logging
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)


class CrawlStrategy:
    """
    Calculate optimal posts and comments distribution based on dataset size
    """
    
    # Dataset size configurations
    DATASET_SIZES = {
        50: "Quick Test",
        1000: "Quick Analysis",
        5000: "Standard Analysis",
        10000: "Deep Analysis",
        25000: "Market Research",
        50000: "Enterprise Analysis",
        100000: "Big Data Insights"
    }
    
    # Ratio: 30% posts, 70% comments
    POSTS_RATIO = 0.30
    COMMENTS_RATIO = 0.70
    
    # Fallback rules
    MIN_POSTS_RATIO = 0.10  # Minimum 10% posts
    MAX_COMMENTS_PER_POST = 50  # Maximum 50 comments per post
    MIN_POST_LENGTH = 20  # Minimum 20 words for posts
    MIN_COMMENT_LENGTH = 10  # Minimum 10 words for comments

    # Platforms that do not have comments (should get 100% posts quota)
    NO_COMMENTS_PLATFORMS = ["news", "google", "shopee", "lazada"]

    @staticmethod
    def calculate_distribution(
        dataset_size: int,
        platforms_count: int = 1,
        platforms: List[str] = None
    ) -> Dict[str, any]:
        """
        Calculate posts and comments distribution

        Args:
            dataset_size: Total results target (50, 1000, 5000, etc.)
            platforms_count: Number of platforms to crawl
            platforms: List of platform names

        Returns:
            Dictionary with crawl strategy details
        """

        # Per platform allocation
        per_platform = dataset_size // platforms_count

        # Check if we are only crawling comment-less platforms
        all_no_comments = False
        if platforms:
            all_no_comments = all(p.lower() in CrawlStrategy.NO_COMMENTS_PLATFORMS for p in platforms)

        if all_no_comments:
            # 100% posts, 0% comments
            target_posts = per_platform
            target_comments = 0
            posts_ratio = 1.0
            comments_ratio = 0.0
        else:
            # 30:70 ratio (Posts:Comments)
            target_posts = int(per_platform * CrawlStrategy.POSTS_RATIO)
            target_comments = int(per_platform * CrawlStrategy.COMMENTS_RATIO)
            posts_ratio = CrawlStrategy.POSTS_RATIO
            comments_ratio = CrawlStrategy.COMMENTS_RATIO

        # Comments per post
        comments_per_post = target_comments // target_posts if target_posts > 0 else 0

        strategy = {
            "total_target": dataset_size,
            "platforms_count": platforms_count,
            "per_platform": per_platform,
            "posts_per_platform": target_posts,
            "comments_per_platform": target_comments,
            "comments_per_post": comments_per_post,
            "total_posts": target_posts * platforms_count,
            "total_comments": target_comments * platforms_count,
            "posts_ratio": posts_ratio,
            "comments_ratio": comments_ratio
        }

        logger.info(f"📊 Crawl Strategy: {dataset_size} results across {platforms_count} platform(s)")
        logger.info(f"   Posts: {strategy['total_posts']} ({posts_ratio*100}%)")
        logger.info(f"   Comments: {strategy['total_comments']} ({comments_ratio*100}%)")
        logger.info(f"   Comments/Post: {comments_per_post}")

        return strategy
    
    @staticmethod
    def adaptive_adjustment(
        posts_found: int,
        avg_comments_available: float,
        target_posts: int,
        target_comments: int
    ) -> Dict[str, any]:
        """
        Adaptive algorithm to handle edge cases
        
        Args:
            posts_found: Number of posts actually found
            avg_comments_available: Average comments per post available
            target_posts: Target number of posts (30% of dataset)
            target_comments: Target number of comments (70% of dataset)
        
        Returns:
            Adjusted strategy
        """
        
        # Scenario 1: Banyak posts, sikit comments
        if avg_comments_available < 3:
            # Maximize posts (up to 50% more)
            actual_posts = min(posts_found, int(target_posts * 1.5))
            comments_per_post = min(int(avg_comments_available), 2)
            actual_comments = actual_posts * comments_per_post
            scenario = "MAXIMIZE_POSTS"
            
            logger.info(f"🔄 Scenario 1: Banyak posts, sikit comments")
            logger.info(f"   Found: {posts_found} posts, avg {avg_comments_available:.1f} comments/post")
            logger.info(f"   Strategy: Maximize posts to {actual_posts}")
            
        # Scenario 2: Sikit posts, banyak comments
        elif posts_found < target_posts:
            # Maximize comments
            actual_posts = posts_found
            # Cap at 50 comments per post
            comments_per_post = min(target_comments // actual_posts, CrawlStrategy.MAX_COMMENTS_PER_POST)
            actual_comments = actual_posts * comments_per_post
            scenario = "MAXIMIZE_COMMENTS"
            
            logger.info(f"🔄 Scenario 2: Sikit posts, banyak comments")
            logger.info(f"   Found: {posts_found} posts (target: {target_posts})")
            logger.info(f"   Strategy: Maximize comments to {comments_per_post}/post")
            
        # Scenario 3: Normal (ideal case)
        else:
            # Follow 30:70 ratio
            actual_posts = target_posts
            comments_per_post = target_comments // actual_posts
            actual_comments = target_comments
            scenario = "NORMAL"
            
            logger.info(f"✅ Scenario 3: Normal distribution")
            logger.info(f"   Following 30:70 ratio")
        
        total_results = actual_posts + actual_comments
        
        adjustment = {
            "scenario": scenario,
            "posts": actual_posts,
            "comments_per_post": comments_per_post,
            "total_comments": actual_comments,
            "total_results": total_results,
            "posts_percentage": (actual_posts / total_results * 100) if total_results > 0 else 0,
            "comments_percentage": (actual_comments / total_results * 100) if total_results > 0 else 0
        }
        
        logger.info(f"   Result: {actual_posts} posts + {actual_comments} comments = {total_results}")
        
        return adjustment
    
    @staticmethod
    def filter_posts_by_engagement(
        posts: List[Dict],
        target_count: int
    ) -> List[Dict]:
        """
        Filter and rank posts by engagement
        
        Args:
            posts: List of post objects
            target_count: Number of posts to select
        
        Returns:
            Filtered and ranked list of posts
        """
        
        # Helper: schema-aware getter (records may use 'Text'/'ID'/'URL' or 'text'/'id'/'url')
        def _g(post, *keys, default=None):
            for k in keys:
                if k in post and post[k] not in (None, ""):
                    return post[k]
            return default

        # Calculate engagement score
        for post in posts:
            post['engagement_score'] = (
                int(_g(post, 'likes', default=0) or 0) +
                int(_g(post, 'shares', default=0) or 0) * 2 +  # Shares weighted more
                int(_g(post, 'comments_count', default=0) or 0) * 3 +  # Comments weighted most
                int(_g(post, 'views', default=0) or 0) * 0.001  # Views weighted less
            )

        # Filter quality posts (schema-aware: accepts both 'Text'/'text', 'ID'/'id', 'URL'/'url')
        # URL check is optional — some platforms (TikTok) may have empty URL in early stages
        quality_posts = [
            post for post in posts
            if len(str(_g(post, 'Text', 'text', default=''))) >= CrawlStrategy.MIN_POST_LENGTH
            and str(_g(post, 'ID', 'id', default='')) != '-1'
            and _g(post, 'Type', 'type', default='post') == 'post'  # Skip comment rows
        ]
        
        logger.info(f"🔍 Filtered {len(quality_posts)}/{len(posts)} quality posts")
        
        # Sort by engagement score
        ranked_posts = sorted(
            quality_posts,
            key=lambda x: x['engagement_score'],
            reverse=True
        )
        
        # Return top N posts
        selected = ranked_posts[:target_count]
        
        logger.info(f"✅ Selected top {len(selected)} posts by engagement")
        
        return selected

