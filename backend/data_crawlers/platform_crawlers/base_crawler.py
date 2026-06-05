"""Base crawler class for all platform crawlers."""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime
from loguru import logger

from utils.apify_client import apify_crawler
from database.db_handler import db_handler
from database.repository import (
    PostRepository, CommentRepository, UserProfileRepository,
    ProductRepository, CrawlJobRepository
)


class BaseCrawler(ABC):
    """Abstract base class for platform crawlers."""
    
    def __init__(self, platform: str):
        """Initialize crawler."""
        self.platform = platform
        self.apify_client = apify_crawler
        logger.info(f"Initialized {platform} crawler")
    
    @abstractmethod
    def prepare_input(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Prepare input configuration for Apify actor.
        
        Args:
            query: Search query or target
            **kwargs: Additional parameters
            
        Returns:
            Input configuration dictionary
        """
        pass
    
    @abstractmethod
    def transform_data(self, raw_data: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Transform raw Apify data to database format.
        
        Args:
            raw_data: Raw data from Apify
            
        Returns:
            Dictionary with categorized data (posts, comments, profiles, products)
        """
        pass
    
    def crawl(
        self,
        query: str,
        save_to_db: bool = True,
        actor_id: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute crawl operation.
        
        Args:
            query: Search query or target
            save_to_db: Whether to save results to database
            actor_id: Optional custom actor ID
            **kwargs: Additional parameters for the crawler
            
        Returns:
            Crawl results
        """
        job_id = None
        
        try:
            # Create crawl job
            with db_handler.get_session() as session:
                job_repo = CrawlJobRepository(session)
                job = job_repo.create_job(
                    platform=self.platform,
                    job_type=kwargs.get("job_type", "search"),
                    query=query,
                    extra_data=kwargs
                )
                job_id = job.id
                logger.info(f"Created crawl job {job_id} for {self.platform}")
            
            # Update job status to running
            with db_handler.get_session() as session:
                job_repo = CrawlJobRepository(session)
                job_repo.update_status(job_id, "running")
            
            # Prepare input
            run_input = self.prepare_input(query, **kwargs)
            logger.info(f"Prepared input for {self.platform}: {run_input}")
            
            # Run Apify actor
            # Default timeout increased to 30 minutes for large crawls
            run = self.apify_client.run_actor(
                platform=self.platform,
                run_input=run_input,
                actor_id=actor_id,
                wait_for_finish=True,
                timeout_secs=kwargs.get("timeout", 1800)  # 30 minutes default
            )
            
            # Get results
            raw_data = self.apify_client.get_run_dataset(run["id"])
            logger.info(f"Retrieved {len(raw_data)} items from {self.platform}")
            
            # Transform data
            transformed_data = self.transform_data(raw_data)
            
            # Save to database
            items_saved = 0
            if save_to_db:
                items_saved = self.save_to_database(transformed_data)
                logger.info(f"Saved {items_saved} items to database")
            
            # Update job status to completed
            with db_handler.get_session() as session:
                job_repo = CrawlJobRepository(session)
                job_repo.update_status(job_id, "completed", items_collected=items_saved)
            
            return {
                "platform": self.platform,
                "job_id": job_id,
                "status": "completed",
                "items_collected": items_saved,
                "raw_data": raw_data,
                "transformed_data": transformed_data
            }
            
        except Exception as e:
            logger.error(f"Error during crawl for {self.platform}: {e}")
            
            # Update job status to failed
            if job_id:
                with db_handler.get_session() as session:
                    job_repo = CrawlJobRepository(session)
                    job_repo.update_status(job_id, "failed", error_message=str(e))
            
            raise
    
    def save_to_database(self, data: Dict[str, List[Dict[str, Any]]]) -> int:
        """
        Save transformed data to database.
        
        Args:
            data: Transformed data dictionary
            
        Returns:
            Number of items saved
        """
        items_saved = 0
        
        with db_handler.get_session() as session:
            # Save posts
            if "posts" in data:
                post_repo = PostRepository(session)
                for post_data in data["posts"]:
                    post_repo.upsert(post_data)
                    items_saved += 1
            
            # Save comments
            if "comments" in data:
                comment_repo = CommentRepository(session)
                for comment_data in data["comments"]:
                    comment_repo.create(**comment_data)
                    items_saved += 1
            
            # Save user profiles
            if "profiles" in data:
                profile_repo = UserProfileRepository(session)
                for profile_data in data["profiles"]:
                    profile_repo.upsert(profile_data)
                    items_saved += 1
            
            # Save products
            if "products" in data:
                product_repo = ProductRepository(session)
                for product_data in data["products"]:
                    product_repo.upsert(product_data)
                    items_saved += 1
        
        return items_saved

