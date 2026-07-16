"""TikTok crawler implementation with versatile boolean query support."""
from typing import Dict, Any, List
from datetime import datetime
from loguru import logger

from .base_crawler import BaseCrawler
from utils.boolean_query_parser import BooleanQueryParser


class TikTokCrawler(BaseCrawler):
    """
    Versatile TikTok crawler with flexible input options.

    Supports:
    - Boolean queries: "PAS OR BN OR UMNO", "PAS AND election", "Najib NOT scandal"
    - Multiple input types: keywords, hashtags, profiles, URLs
    - Flexible data collection: comments, engagement, user details
    - Cost optimization: control what data to collect
    """

    def __init__(self):
        super().__init__("tiktok")
        self.query_parser = BooleanQueryParser()

    def prepare_input(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Prepare input for TikTok Apify actor with versatile options.

        Args:
            query: Search query (supports boolean operators)
            **kwargs: Additional options
                - search_type: 'keyword', 'hashtag', 'profile', 'url', 'auto' (default)
                - max_videos: Maximum videos to collect (default: 100)
                - get_comments: Collect comments (default: False)
                - comments_per_post: Comments per video (default: 50)
                - get_engagement: Collect engagement metrics (default: True)
                - get_user_details: Collect detailed user profiles (default: True)
                - download_videos: Download video files (default: False)
                - download_covers: Download cover images (default: False)

        Returns:
            Input configuration for Apify actor
        """
        search_type = kwargs.get("search_type", "auto")
        max_videos = kwargs.get("max_videos", kwargs.get("max_items", 100))

        # Auto-detect search type if not specified
        if search_type == "auto":
            search_type = self._detect_search_type(query)

        logger.info(f"TikTok search type: {search_type}, query: {query}")

        # Base configuration
        input_config = {
            "resultsPerPage": max_videos,
            "shouldDownloadVideos": kwargs.get("download_videos", False),
            "shouldDownloadCovers": kwargs.get("download_covers", False),
        }

        # Add search parameters based on type
        if search_type == "hashtag":
            # Hashtag search
            hashtags = self._extract_hashtags(query)
            input_config["hashtags"] = hashtags
            logger.info(f"Searching hashtags: {hashtags}")

        elif search_type == "profile":
            # Profile/user search
            profiles = self._extract_profiles(query)
            input_config["profiles"] = profiles
            logger.info(f"Searching profiles: {profiles}")

        elif search_type == "url":
            # Direct URL search
            urls = self._extract_urls(query)
            input_config["postURLs"] = urls
            logger.info(f"Searching URLs: {urls}")

        else:
            # Keyword search (default) - supports boolean queries
            search_queries = self._prepare_keyword_search(query)
            input_config["searchQueries"] = search_queries
            logger.info(f"Searching keywords: {search_queries}")

        # Comments configuration
        if kwargs.get("get_comments", False):
            input_config["commentsPerPost"] = kwargs.get("comments_per_post", 50)
            logger.info(f"Collecting up to {input_config['commentsPerPost']} comments per post")
        else:
            input_config["commentsPerPost"] = 0

        return input_config

    def crawl(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Enhanced crawl with boolean query support.

        Handles boolean queries by:
        1. Parsing the query for OR/AND/NOT operators
        2. Executing optimized searches
        3. Filtering and deduplicating results
        """
        # Check if query contains boolean operators
        if self._is_boolean_query(query):
            return self._crawl_with_boolean(query, **kwargs)
        else:
            # Standard crawl
            return super().crawl(query, **kwargs)

    def _crawl_with_boolean(self, query: str, **kwargs) -> Dict[str, Any]:
        """Execute crawl with boolean query support."""
        logger.info(f"Executing boolean query: {query}")

        # Parse boolean query
        parsed_query = self.query_parser.parse(query)
        search_queries = self.query_parser.generate_search_queries(parsed_query)

        logger.info(f"Parsed into {len(search_queries)} search queries")

        # Execute searches
        all_raw_data = []
        for search_query in search_queries:
            logger.info(f"Executing search: {search_query}")

            # Prepare input for this specific query
            input_data = self.prepare_input(search_query, **kwargs)

            # Run actor using the correct method signature
            # Increased timeout for large crawls with comments
            run = self.apify_client.run_actor(
                platform=self.platform,
                run_input=input_data,
                wait_for_finish=True,
                timeout_secs=kwargs.get("timeout", 1800)  # 30 minutes default
            )

            # Get dataset results
            raw_data = self.apify_client.get_run_dataset(run["id"])

            if raw_data:
                all_raw_data.extend(raw_data)

        # Filter results based on boolean logic
        filtered_data = self.query_parser.filter_results(all_raw_data, parsed_query)

        # Deduplicate
        unique_data = self.query_parser.deduplicate_results(filtered_data)

        logger.info(f"Boolean query returned {len(unique_data)} unique results")

        # Transform and save
        transformed_data = self.transform_data(unique_data)
        self.save_to_database(transformed_data)

        return {
            "platform": self.platform,
            "query": query,
            "items_collected": len(unique_data),
            "data": transformed_data
        }

    def transform_data(self, raw_data: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Transform TikTok data to database format with enhanced details."""
        posts = []
        comments = []
        profiles = []

        for item in raw_data:
            # Transform video/post
            post_data = {
                "platform": self.platform,
                "post_id": item.get("id", ""),
                "author_id": item.get("authorMeta", {}).get("id", ""),
                "author_username": item.get("authorMeta", {}).get("name", ""),
                "author_name": item.get("authorMeta", {}).get("nickName", ""),
                "content": item.get("text", ""),
                "url": item.get("webVideoUrl", ""),
                "created_at": self._parse_timestamp(item.get("createTime")),
                "likes_count": item.get("diggCount", 0),
                "comments_count": item.get("commentCount", 0),
                "shares_count": item.get("shareCount", 0),
                "views_count": item.get("playCount", 0),
                "hashtags": [tag.get("name") for tag in item.get("hashtags", [])],
                "mentions": item.get("mentions", []),
                "media_urls": [item.get("videoUrl", ""), item.get("covers", {}).get("default", "")],
                "metadata": {
                    "music": item.get("musicMeta", {}),
                    "duration": item.get("videoMeta", {}).get("duration", 0),
                    "is_ad": item.get("isAd", False),
                    "collected_count": item.get("collectCount", 0),
                    "forward_count": item.get("forwardCount", 0),
                }
            }
            posts.append(post_data)

            # Transform comments if available
            if "comments" in item and item["comments"]:
                for comment in item["comments"]:
                    comment_data = {
                        "platform": self.platform,
                        "comment_id": comment.get("id", ""),
                        "post_id": item.get("id", ""),
                        "author_id": comment.get("user", {}).get("id", ""),
                        "author_username": comment.get("user", {}).get("uniqueId", ""),
                        "author_name": comment.get("user", {}).get("nickname", ""),
                        "content": comment.get("text", ""),
                        "created_at": self._parse_timestamp(comment.get("createTime")),
                        "likes_count": comment.get("diggCount", 0),
                        "replies_count": comment.get("replyCommentTotal", 0),
                        "metadata": {
                            "is_author_digged": comment.get("isAuthorDigged", False),
                        }
                    }
                    comments.append(comment_data)

            # Transform author profile
            if "authorMeta" in item:
                author = item["authorMeta"]
                profile_data = {
                    "platform": self.platform,
                    "user_id": author.get("id", ""),
                    "username": author.get("name", ""),
                    "display_name": author.get("nickName", ""),
                    "bio": author.get("signature", ""),
                    "profile_url": f"https://tiktok.com/@{author.get('name', '')}",
                    "avatar_url": author.get("avatar", ""),
                    "verified": 1 if author.get("verified", False) else 0,
                    "followers_count": author.get("fans", 0),
                    "following_count": author.get("following", 0),
                    "posts_count": author.get("video", 0),
                    "metadata": {
                        "heart": author.get("heart", 0),
                    }
                }
                profiles.append(profile_data)

        result = {
            "posts": posts,
            "profiles": profiles
        }

        if comments:
            result["comments"] = comments

        return result

    def _is_boolean_query(self, query: str) -> bool:
        """Check if query contains boolean operators."""
        query_upper = query.upper()
        return ' OR ' in query_upper or ' AND ' in query_upper or ' NOT ' in query_upper or ',' in query

    def _detect_search_type(self, query: str) -> str:
        """Auto-detect search type from query."""
        # Check for URL
        if query.startswith('http://') or query.startswith('https://'):
            return "url"

        # Check for hashtag
        if query.startswith('#'):
            return "hashtag"

        # Check for profile (starts with @)
        if query.startswith('@'):
            return "profile"

        # Check if all terms are hashtags
        if all(term.strip().startswith('#') for term in query.split(',')):
            return "hashtag"

        # Default to keyword search
        return "keyword"

    def _extract_hashtags(self, query: str) -> List[str]:
        """Extract hashtags from query."""
        # Handle comma-separated hashtags
        if ',' in query:
            hashtags = [tag.strip().lstrip('#') for tag in query.split(',')]
        # Handle space-separated hashtags
        elif ' ' in query and all(term.startswith('#') for term in query.split()):
            hashtags = [tag.lstrip('#') for tag in query.split()]
        # Single hashtag
        else:
            hashtags = [query.lstrip('#')]

        return [tag for tag in hashtags if tag]

    def _extract_profiles(self, query: str) -> List[str]:
        """Extract profile usernames from query."""
        # Handle comma-separated profiles
        if ',' in query:
            profiles = [profile.strip().lstrip('@') for profile in query.split(',')]
        # Handle space-separated profiles
        elif ' ' in query and all(term.startswith('@') for term in query.split()):
            profiles = [profile.lstrip('@') for profile in query.split()]
        # Single profile
        else:
            profiles = [query.lstrip('@')]

        return [profile for profile in profiles if profile]

    def _extract_urls(self, query: str) -> List[str]:
        """Extract URLs from query."""
        # Handle comma-separated URLs
        if ',' in query:
            urls = [url.strip() for url in query.split(',')]
        # Handle space-separated URLs
        elif ' ' in query and all(term.startswith('http') for term in query.split()):
            urls = query.split()
        # Single URL
        else:
            urls = [query]

        return [url for url in urls if url.startswith('http')]

    def _prepare_keyword_search(self, query: str) -> List[str]:
        """Prepare keyword search queries."""
        # For boolean queries, parse and return search terms
        if self._is_boolean_query(query):
            parsed = self.query_parser.parse(query)
            return parsed.get("search_queries", [query])

        # Simple query
        return [query]

    def _parse_timestamp(self, timestamp: int) -> datetime:
        """Parse Unix timestamp to datetime object."""
        if not timestamp:
            return None
        try:
            return datetime.fromtimestamp(timestamp)
        except:
            return None

