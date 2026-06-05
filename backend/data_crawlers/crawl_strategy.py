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
    
    @staticmethod
    def calculate_distribution(
        dataset_size: int,
        platforms_count: int = 1
    ) -> Dict[str, any]:
        """
        Calculate posts and comments distribution
        
        Args:
            dataset_size: Total results target (50, 1000, 5000, etc.)
            platforms_count: Number of platforms to crawl
        
        Returns:
            Dictionary with crawl strategy details
        """
        
        # Per platform allocation
        per_platform = dataset_size // platforms_count
        
        # 30:70 ratio (Posts:Comments)
        target_posts = int(per_platform * CrawlStrategy.POSTS_RATIO)
        target_comments = int(per_platform * CrawlStrategy.COMMENTS_RATIO)
        
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
            "posts_ratio": CrawlStrategy.POSTS_RATIO,
            "comments_ratio": CrawlStrategy.COMMENTS_RATIO
        }
        
        logger.info(f"📊 Crawl Strategy: {dataset_size} results across {platforms_count} platform(s)")
        logger.info(f"   Posts: {strategy['total_posts']} ({CrawlStrategy.POSTS_RATIO*100}%)")
        logger.info(f"   Comments: {strategy['total_comments']} ({CrawlStrategy.COMMENTS_RATIO*100}%)")
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
        
        # Calculate engagement score
        for post in posts:
            post['engagement_score'] = (
                post.get('likes', 0) +
                post.get('shares', 0) * 2 +  # Shares weighted more
                post.get('comments_count', 0) * 3 +  # Comments weighted most
                post.get('views', 0) * 0.001  # Views weighted less
            )
        
        # Filter quality posts
        quality_posts = [
            post for post in posts
            if len(post.get('text', '')) >= CrawlStrategy.MIN_POST_LENGTH  # Minimum length
            and post.get('id') != '-1'  # Not mock data
            and post.get('url')  # Has valid URL
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

