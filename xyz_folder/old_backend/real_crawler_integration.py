#!/usr/bin/env python3
"""
🕷️ Real Crawler Integration for InsightPulse Web Backend
======================================================
Integrates your existing S_crawlers with the web backend
Provides real data collection from all 9 platforms

🎯 PLATFORMS SUPPORTED:
📱 Social Media (7): Facebook, Instagram, Twitter/X, TikTok, Google, News, Lowyat
🛒 E-commerce (2): Shopee, Lazada

Author: InsightPulse Integration Team
Version: Real Data Edition 1.0.0
"""

import asyncio
import subprocess
import json
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging
import sys
import os

# Use the actual data path in InsightPulse
INSIGHTPULSE_DATA_PATH = "/Users/rmtariq/Documents/InsightPulse/data/smart_crawlers"
S_CRAWLERS_PATH = "/Users/rmtariq/Documents/S_crawlers"  # Fallback if exists
sys.path.append(S_CRAWLERS_PATH)

logger = logging.getLogger(__name__)

class RealCrawlerManager:
    """Manages real data collection from all 9 platforms"""
    
    def __init__(self):
        # Use InsightPulse data directory first
        self.insightpulse_data_path = Path(INSIGHTPULSE_DATA_PATH)
        self.s_crawlers_path = Path(S_CRAWLERS_PATH)

        # Determine which data directory to use
        if self.insightpulse_data_path.exists():
            self.data_dir = self.insightpulse_data_path
            logger.info(f"Using InsightPulse data directory: {self.data_dir}")
        elif (self.s_crawlers_path / "data").exists():
            self.data_dir = self.s_crawlers_path / "data"
            logger.info(f"Using S_crawlers data directory: {self.data_dir}")
        else:
            logger.error("No data directory found!")
            self.data_dir = self.insightpulse_data_path  # Default

        # Set crawlers directory
        self.crawlers_dir = self.s_crawlers_path / "crawlers"

        # Verify paths exist
        if not self.data_dir.exists():
            logger.warning(f"Data directory not found: {self.data_dir}")
        if not self.crawlers_dir.exists():
            logger.warning(f"Crawlers directory not found: {self.crawlers_dir}")

    async def run_crawler(self, crawler_script: str, query: str, max_results: int) -> Dict[str, Any]:
        """Run a specific crawler script and return results"""
        
        crawler_path = self.crawlers_dir / crawler_script
        
        if not crawler_path.exists():
            logger.error(f"Crawler script not found: {crawler_path}")
            return {"error": f"Crawler script not found: {crawler_script}"}
        
        try:
            # Run the crawler script
            cmd = [
                "python", str(crawler_path),
                "--query", query,
                "--max_results", str(max_results),
                "--output_format", "json"
            ]
            
            logger.info(f"Running crawler: {' '.join(cmd)}")
            
            # Run crawler asynchronously
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.s_crawlers_path)
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                # Parse JSON output
                try:
                    result = json.loads(stdout.decode())
                    return result
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse crawler output: {e}")
                    return {"error": "Failed to parse crawler output"}
            else:
                logger.error(f"Crawler failed: {stderr.decode()}")
                return {"error": f"Crawler execution failed: {stderr.decode()}"}
                
        except Exception as e:
            logger.error(f"Error running crawler {crawler_script}: {e}")
            return {"error": str(e)}
    
    async def load_existing_data(self, platform: str, query: str) -> Dict[str, Any]:
        """Load existing data from S_crawlers data directory"""
        
        platform_data_dir = self.data_dir / platform
        
        if not platform_data_dir.exists():
            logger.warning(f"No data directory found for {platform}")
            return {"error": f"No data directory for {platform}"}
        
        # Find relevant CSV files
        csv_files = list(platform_data_dir.glob("*.csv"))
        
        if not csv_files:
            logger.warning(f"No CSV files found for {platform}")
            return {"error": f"No data files for {platform}"}
        
        try:
            # Load the most recent file
            latest_file = max(csv_files, key=lambda f: f.stat().st_mtime)
            
            logger.info(f"Loading data from: {latest_file}")
            
            # Read CSV data
            df = pd.read_csv(latest_file)
            
            # Filter data based on query if possible
            if 'content' in df.columns:
                # Simple text search in content
                mask = df['content'].str.contains(query, case=False, na=False)
                filtered_df = df[mask]
                
                if len(filtered_df) == 0:
                    # If no matches, return sample of all data
                    filtered_df = df.head(min(100, len(df)))
            else:
                # Return sample of data
                filtered_df = df.head(min(100, len(df)))
            
            # Convert to dictionary format
            data_records = filtered_df.to_dict('records')
            
            return {
                "platform": platform,
                "query": query,
                "data_points": len(data_records),
                "total_available": len(df),
                "data": data_records,
                "source_file": str(latest_file),
                "collected_at": datetime.fromtimestamp(latest_file.stat().st_mtime).isoformat(),
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Error loading data for {platform}: {e}")
            return {"error": str(e)}

# Initialize the crawler manager
crawler_manager = RealCrawlerManager()

# ===== PLATFORM-SPECIFIC COLLECTION FUNCTIONS =====

async def collect_facebook_data(query: str, max_results: int) -> Dict[str, Any]:
    """Collect real Facebook data"""
    logger.info(f"📘 Collecting Facebook data for: {query}")
    
    # Try to run the crawler first
    result = await crawler_manager.run_crawler("smart_facebook_crawler.py", query, max_results)
    
    if "error" not in result:
        return result
    
    # Fallback to existing data
    logger.info("📘 Falling back to existing Facebook data")
    existing_data = await crawler_manager.load_existing_data("facebook", query)
    
    if "error" not in existing_data:
        # Process the data for insights
        return process_social_media_data(existing_data, "facebook")
    
    return {"platform": "facebook", "error": "No data available", "data_points": 0}

async def collect_instagram_data(query: str, max_results: int) -> Dict[str, Any]:
    """Collect real Instagram data"""
    logger.info(f"📷 Collecting Instagram data for: {query}")
    
    result = await crawler_manager.run_crawler("smart_instagram_crawler.py", query, max_results)
    
    if "error" not in result:
        return result
    
    # Fallback to existing data
    existing_data = await crawler_manager.load_existing_data("instagram", query)
    
    if "error" not in existing_data:
        return process_social_media_data(existing_data, "instagram")
    
    return {"platform": "instagram", "error": "No data available", "data_points": 0}

async def collect_twitter_data(query: str, max_results: int) -> Dict[str, Any]:
    """Collect real Twitter/X data"""
    logger.info(f"🐦 Collecting Twitter data for: {query}")
    
    result = await crawler_manager.run_crawler("smart_x_crawler.py", query, max_results)
    
    if "error" not in result:
        return result
    
    # Fallback to existing data
    existing_data = await crawler_manager.load_existing_data("x", query)
    
    if "error" not in existing_data:
        return process_social_media_data(existing_data, "twitter")
    
    return {"platform": "twitter", "error": "No data available", "data_points": 0}

async def collect_tiktok_data(query: str, max_results: int) -> Dict[str, Any]:
    """Collect real TikTok data"""
    logger.info(f"🎵 Collecting TikTok data for: {query}")
    
    result = await crawler_manager.run_crawler("smart_tiktok_crawler.py", query, max_results)
    
    if "error" not in result:
        return result
    
    # Fallback to existing data
    existing_data = await crawler_manager.load_existing_data("tiktok", query)
    
    if "error" not in existing_data:
        return process_social_media_data(existing_data, "tiktok")
    
    return {"platform": "tiktok", "error": "No data available", "data_points": 0}

async def collect_google_data(query: str, max_results: int) -> Dict[str, Any]:
    """Collect real Google search data"""
    logger.info(f"🔍 Collecting Google data for: {query}")
    
    result = await crawler_manager.run_crawler("smart_google_crawler.py", query, max_results)
    
    if "error" not in result:
        return result
    
    # Fallback to existing data
    existing_data = await crawler_manager.load_existing_data("google", query)
    
    if "error" not in existing_data:
        return process_search_data(existing_data, "google")
    
    return {"platform": "google", "error": "No data available", "data_points": 0}

async def collect_news_data(query: str, max_results: int) -> Dict[str, Any]:
    """Collect real Malaysian news data"""
    logger.info(f"📰 Collecting News data for: {query}")
    
    result = await crawler_manager.run_crawler("smart_news_crawler.py", query, max_results)
    
    if "error" not in result:
        return result
    
    # Fallback to existing data
    existing_data = await crawler_manager.load_existing_data("news", query)
    
    if "error" not in existing_data:
        return process_news_data(existing_data, "news")
    
    return {"platform": "news", "error": "No data available", "data_points": 0}

async def collect_lowyat_data(query: str, max_results: int) -> Dict[str, Any]:
    """Collect real Lowyat forum data"""
    logger.info(f"💻 Collecting Lowyat data for: {query}")
    
    result = await crawler_manager.run_crawler("smart_lowyat_crawler.py", query, max_results)
    
    if "error" not in result:
        return result
    
    # Fallback to existing data
    existing_data = await crawler_manager.load_existing_data("lowyat", query)
    
    if "error" not in existing_data:
        return process_forum_data(existing_data, "lowyat")
    
    return {"platform": "lowyat", "error": "No data available", "data_points": 0}

async def collect_shopee_data(query: str, max_results: int) -> Dict[str, Any]:
    """Collect real Shopee e-commerce data"""
    logger.info(f"🛒 Collecting Shopee data for: {query}")
    
    result = await crawler_manager.run_crawler("smart_shopee_crawler.py", query, max_results)
    
    if "error" not in result:
        return result
    
    # Fallback to existing data
    existing_data = await crawler_manager.load_existing_data("shopee", query)
    
    if "error" not in existing_data:
        return process_ecommerce_data(existing_data, "shopee")
    
    return {"platform": "shopee", "error": "No data available", "data_points": 0}

async def collect_lazada_data(query: str, max_results: int) -> Dict[str, Any]:
    """Collect real Lazada e-commerce data"""
    logger.info(f"🛍️ Collecting Lazada data for: {query}")
    
    result = await crawler_manager.run_crawler("smart_lazada_crawler.py", query, max_results)
    
    if "error" not in result:
        return result
    
    # Fallback to existing data
    existing_data = await crawler_manager.load_existing_data("lazada", query)
    
    if "error" not in existing_data:
        return process_ecommerce_data(existing_data, "lazada")
    
    return {"platform": "lazada", "error": "No data available", "data_points": 0}

# ===== DATA PROCESSING FUNCTIONS =====

def process_social_media_data(data: Dict[str, Any], platform: str) -> Dict[str, Any]:
    """Process social media data for insights"""
    
    if "data" not in data or not data["data"]:
        return data
    
    records = data["data"]
    
    # Calculate basic metrics
    total_posts = len(records)
    
    # Try to extract engagement metrics
    total_engagement = 0
    sentiment_scores = []
    
    for record in records:
        # Extract engagement (likes, shares, comments)
        engagement = 0
        for field in ['likes', 'shares', 'comments', 'reactions', 'engagement']:
            if field in record and record[field]:
                try:
                    engagement += int(record[field])
                except (ValueError, TypeError):
                    pass
        total_engagement += engagement
        
        # Extract sentiment if available
        if 'sentiment' in record:
            try:
                sentiment_scores.append(float(record['sentiment']))
            except (ValueError, TypeError):
                pass
    
    # Calculate average sentiment
    avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0.5
    
    # Extract trending topics/hashtags
    trending_topics = []
    for record in records:
        if 'hashtags' in record and record['hashtags']:
            if isinstance(record['hashtags'], list):
                trending_topics.extend(record['hashtags'])
            elif isinstance(record['hashtags'], str):
                trending_topics.extend(record['hashtags'].split(','))
    
    # Get top trending topics
    from collections import Counter
    topic_counts = Counter(trending_topics)
    top_topics = [topic for topic, count in topic_counts.most_common(5)]
    
    # Update the data with processed insights
    data.update({
        "processed_insights": {
            "total_posts": total_posts,
            "total_engagement": total_engagement,
            "average_engagement": total_engagement / total_posts if total_posts > 0 else 0,
            "sentiment_score": avg_sentiment,
            "sentiment_label": "positive" if avg_sentiment > 0.6 else "negative" if avg_sentiment < 0.4 else "neutral",
            "trending_topics": top_topics,
            "engagement_rate": (total_engagement / total_posts) if total_posts > 0 else 0
        }
    })
    
    return data

def process_ecommerce_data(data: Dict[str, Any], platform: str) -> Dict[str, Any]:
    """Process e-commerce data for insights"""
    
    if "data" not in data or not data["data"]:
        return data
    
    records = data["data"]
    
    # Calculate e-commerce metrics
    total_products = len(records)
    prices = []
    ratings = []
    review_counts = []
    
    for record in records:
        # Extract price
        if 'price' in record and record['price']:
            try:
                price_str = str(record['price']).replace('RM', '').replace(',', '').strip()
                price = float(price_str)
                prices.append(price)
            except (ValueError, TypeError):
                pass
        
        # Extract rating
        if 'rating' in record and record['rating']:
            try:
                rating = float(record['rating'])
                ratings.append(rating)
            except (ValueError, TypeError):
                pass
        
        # Extract review count
        if 'reviews' in record and record['reviews']:
            try:
                reviews = int(record['reviews'])
                review_counts.append(reviews)
            except (ValueError, TypeError):
                pass
    
    # Calculate statistics
    avg_price = sum(prices) / len(prices) if prices else 0
    min_price = min(prices) if prices else 0
    max_price = max(prices) if prices else 0
    avg_rating = sum(ratings) / len(ratings) if ratings else 0
    total_reviews = sum(review_counts)
    
    # Update the data with processed insights
    data.update({
        "processed_insights": {
            "total_products": total_products,
            "price_analysis": {
                "average_price": round(avg_price, 2),
                "min_price": round(min_price, 2),
                "max_price": round(max_price, 2),
                "currency": "MYR"
            },
            "rating_analysis": {
                "average_rating": round(avg_rating, 2),
                "total_reviews": total_reviews,
                "rating_distribution": "positive" if avg_rating > 4.0 else "mixed" if avg_rating > 3.0 else "negative"
            },
            "market_insights": {
                "competition_level": "high" if total_products > 50 else "medium" if total_products > 20 else "low",
                "price_competitiveness": "competitive" if avg_price > 0 else "unknown"
            }
        }
    })
    
    return data

def process_search_data(data: Dict[str, Any], platform: str) -> Dict[str, Any]:
    """Process search engine data for insights"""
    
    if "data" not in data or not data["data"]:
        return data
    
    records = data["data"]
    
    # Process search results
    total_results = len(records)
    domains = []
    
    for record in records:
        if 'url' in record and record['url']:
            try:
                from urllib.parse import urlparse
                domain = urlparse(record['url']).netloc
                domains.append(domain)
            except:
                pass
    
    # Get top domains
    from collections import Counter
    domain_counts = Counter(domains)
    top_domains = [domain for domain, count in domain_counts.most_common(5)]
    
    data.update({
        "processed_insights": {
            "total_results": total_results,
            "top_domains": top_domains,
            "search_volume": "high" if total_results > 100 else "medium" if total_results > 50 else "low"
        }
    })
    
    return data

def process_news_data(data: Dict[str, Any], platform: str) -> Dict[str, Any]:
    """Process news data for insights"""
    return process_social_media_data(data, platform)  # Similar processing

def process_forum_data(data: Dict[str, Any], platform: str) -> Dict[str, Any]:
    """Process forum data for insights"""
    return process_social_media_data(data, platform)  # Similar processing

# Export functions for use in main app
__all__ = [
    'collect_facebook_data',
    'collect_instagram_data', 
    'collect_twitter_data',
    'collect_tiktok_data',
    'collect_google_data',
    'collect_news_data',
    'collect_lowyat_data',
    'collect_shopee_data',
    'collect_lazada_data',
    'RealCrawlerManager'
]
