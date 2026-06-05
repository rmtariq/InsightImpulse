"""
Crawler Manager for InsightPulse - Integrates Smart Crawlers System
==================================================================

This module provides a unified interface for data collection across multiple platforms,
leveraging the existing smart_crawlers system with all its advanced features.

Key Features:
- Direct integration with smart_crawlers system
- Boolean OR query support
- Malay BERT sentiment analysis
- Multi-platform concurrent crawling
- Intelligent keyword extraction
- Malaysian content optimization

Author: InsightPulse Team
"""

import os
import sys
import asyncio
import json
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging
from pathlib import Path

# Import our smart crawler bridge
from .smart_crawler_bridge import SmartCrawlerBridge, multi_platform_crawl

logger = logging.getLogger(__name__)


class CrawlerManager:
    """
    Enhanced crawler manager that integrates the smart_crawlers system
    with InsightPulse AI-powered insights application.

    Features:
    - Direct integration with smart_crawlers
    - Advanced Boolean OR queries
    - Malay BERT sentiment analysis
    - Multi-platform concurrent crawling
    - Intelligent keyword extraction
    - Malaysian content optimization
    """

    def __init__(self):
        self.active_crawls = {}
        self.data_directory = Path("data/raw")
        self.data_directory.mkdir(parents=True, exist_ok=True)

        # Initialize smart crawler bridge
        try:
            self.smart_bridge = SmartCrawlerBridge()
            self.available_platforms = self.smart_bridge.get_available_platforms()
            logger.info(f"Smart crawler bridge initialized with platforms: {self.available_platforms}")
        except Exception as e:
            logger.error(f"Error initializing smart crawler bridge: {e}")
            self.smart_bridge = None
            self.available_platforms = []
            logger.warning("Falling back to mock mode for development")
    
    async def start_crawling(self, crawl_id: str, platforms: List[str],
                           keywords: List[str], date_range: Optional[Dict] = None,
                           max_results: int = 1000) -> Dict[str, Any]:
        """
        Start intelligent crawling process using smart_crawlers system

        Args:
            crawl_id: Unique identifier for this crawl session
            platforms: List of platforms to crawl (facebook, instagram, tiktok, etc.)
            keywords: Search keywords/queries (will be intelligently processed)
            date_range: Optional date range for historical data
            max_results: Maximum results per platform

        Returns:
            Dict with crawl status and comprehensive metadata
        """
        try:
            logger.info(f"Starting intelligent crawl {crawl_id} for platforms: {platforms}")

            # Validate platforms
            invalid_platforms = [p for p in platforms if p not in self.available_platforms]
            if invalid_platforms:
                logger.warning(f"Invalid platforms: {invalid_platforms}")
                platforms = [p for p in platforms if p in self.available_platforms]

            if not platforms:
                raise ValueError("No valid platforms specified")

            # Create intelligent search claim from keywords
            search_claim = self._create_search_claim(keywords)
            logger.info(f"Generated search claim: {search_claim}")

            # Initialize crawl session
            crawl_session = {
                'id': crawl_id,
                'platforms': platforms,
                'keywords': keywords,
                'search_claim': search_claim,
                'date_range': date_range,
                'max_results': max_results,
                'status': 'running',
                'started_at': datetime.now(),
                'results': {},
                'errors': [],
                'smart_crawler_results': {}
            }

            self.active_crawls[crawl_id] = crawl_session

            # Use smart crawler bridge for intelligent crawling
            if self.smart_bridge:
                logger.info("Using smart crawler system for enhanced data collection")

                # Execute smart crawlers with advanced features
                smart_results = await self.smart_bridge.batch_crawl(
                    platforms=platforms,
                    claim=search_claim,
                    max_results_per_platform=max_results
                )

                crawl_session['smart_crawler_results'] = smart_results

                # Process and integrate smart crawler results
                for platform, result in smart_results.get('results', {}).items():
                    if result['status'] == 'success':
                        # Copy data to InsightPulse data directory
                        platform_data_dir = self.data_directory / platform
                        copied_files = self.smart_bridge.copy_data_to_insightpulse(
                            platform, platform_data_dir
                        )

                        # Load and process the data
                        processed_data = await self._process_smart_crawler_data(
                            platform, copied_files
                        )

                        crawl_session['results'][platform] = {
                            'data': processed_data,
                            'file_count': len(copied_files),
                            'data_files': copied_files
                        }
                    else:
                        crawl_session['errors'].append({
                            'platform': platform,
                            'error': result.get('error', 'Unknown error')
                        })
            else:
                # Fallback to mock data for development
                logger.warning("Smart crawler bridge not available, using mock data")
                await self._generate_mock_data(crawl_session, platforms, keywords, max_results)

            # Update crawl status
            crawl_session['status'] = 'completed'
            crawl_session['completed_at'] = datetime.now()

            # Save crawl metadata
            await self._save_crawl_metadata(crawl_session)

            # Calculate summary statistics
            total_records = 0
            for platform_result in crawl_session['results'].values():
                if isinstance(platform_result, dict) and 'data' in platform_result:
                    total_records += len(platform_result['data'])

            return {
                'crawl_id': crawl_id,
                'status': 'completed',
                'platforms_crawled': len(crawl_session['results']),
                'total_records': total_records,
                'errors': crawl_session['errors'],
                'search_claim': search_claim,
                'execution_summary': smart_results.get('summary', {}) if self.smart_bridge else {}
            }

        except Exception as e:
            logger.error(f"Error in crawling process: {e}")
            if crawl_id in self.active_crawls:
                self.active_crawls[crawl_id]['status'] = 'failed'
                self.active_crawls[crawl_id]['error'] = str(e)
            raise
    
    def _create_search_claim(self, keywords: List[str]) -> str:
        """
        Create an intelligent search claim from keywords using smart crawler methodology
        """
        if not keywords:
            return "Malaysia trending topics"

        # Join keywords intelligently
        if len(keywords) == 1:
            return keywords[0]
        elif len(keywords) <= 3:
            return " ".join(keywords)
        else:
            # For multiple keywords, create a focused claim
            primary_keywords = keywords[:3]
            return " ".join(primary_keywords) + " Malaysia"

    async def _process_smart_crawler_data(self, platform: str, data_files: List[str]) -> List[Dict]:
        """
        Process data from smart crawler output files
        """
        processed_data = []

        for file_path in data_files:
            try:
                if file_path.endswith('.csv'):
                    df = pd.read_csv(file_path)
                    # Convert DataFrame to list of dictionaries
                    records = df.to_dict('records')
                    processed_data.extend(records)
                    logger.info(f"Processed {len(records)} records from {file_path}")
            except Exception as e:
                logger.error(f"Error processing file {file_path}: {e}")

        return processed_data

    async def _generate_mock_data(self, crawl_session: Dict, platforms: List[str],
                                keywords: List[str], max_results: int):
        """Generate mock data for development/testing"""
        logger.info("Generating mock data for development")

        for platform in platforms:
            mock_data = []
            for i in range(min(max_results, 20)):
                mock_data.append({
                    'platform': platform,
                    'type': 'post',
                    'id': f'{platform}_post_{i}',
                    'text': f'Sample {platform} post about {keywords[0] if keywords else "topic"} - {i}',
                    'sentiment': ['Positive', 'Neutral', 'Negative'][i % 3],
                    'sentiment_score': 0.5 + (i % 3 - 1) * 0.3,
                    'date': (datetime.now() - timedelta(hours=i)).isoformat(),
                    'engagement': 10 + i * 2,
                    'likes': 5 + i,
                    'shares': 1 + i // 2,
                    'comments_count': 2 + i // 3
                })

            crawl_session['results'][platform] = {
                'data': mock_data,
                'file_count': 1,
                'data_files': [f'mock_{platform}_data.csv']
            }
    
    def _adapt_keywords_for_platform(self, platform: str, keywords: List[str]) -> List[str]:
        """Adapt keywords for specific platform requirements"""
        # Platform-specific keyword adaptations
        adaptations = {
            'facebook': lambda k: [f'"{keyword}"' for keyword in k],  # Exact match
            'twitter': lambda k: [f"#{keyword.replace(' ', '')}" if ' ' not in keyword else keyword for keyword in k],
            'instagram': lambda k: [f"#{keyword.replace(' ', '')}" if ' ' not in keyword else keyword for keyword in k],
            'tiktok': lambda k: [f"#{keyword.replace(' ', '')}" if ' ' not in keyword else keyword for keyword in k],
            'google': lambda k: [f"{keyword} Malaysia" for keyword in k],
            'news': lambda k: [f"{keyword} Malaysia news" for keyword in k],
            'lowyat': lambda k: k  # No adaptation needed
        }
        
        adapter = adaptations.get(platform, lambda k: k)
        return adapter(keywords)
    
    async def _save_platform_data(self, crawl_id: str, platform: str, data: List[Dict]):
        """Save crawled data for a specific platform"""
        try:
            # Create platform directory
            platform_dir = self.data_directory / platform
            platform_dir.mkdir(exist_ok=True)
            
            # Save as CSV
            if data:
                df = pd.DataFrame(data)
                csv_path = platform_dir / f"{crawl_id}_{platform}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                df.to_csv(csv_path, index=False)
                
                # Save as JSON for backup
                json_path = platform_dir / f"{crawl_id}_{platform}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                
                logger.info(f"Saved {len(data)} records for {platform}")
            
        except Exception as e:
            logger.error(f"Error saving data for {platform}: {e}")
    
    async def _save_crawl_metadata(self, crawl_session: Dict):
        """Save crawl session metadata"""
        try:
            metadata_dir = self.data_directory / "metadata"
            metadata_dir.mkdir(exist_ok=True)
            
            metadata_path = metadata_dir / f"{crawl_session['id']}_metadata.json"
            
            # Convert datetime objects to strings for JSON serialization
            session_copy = crawl_session.copy()
            if 'started_at' in session_copy:
                session_copy['started_at'] = session_copy['started_at'].isoformat()
            if 'completed_at' in session_copy:
                session_copy['completed_at'] = session_copy['completed_at'].isoformat()
            
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(session_copy, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving crawl metadata: {e}")
    
    async def get_crawl_status(self, crawl_id: str) -> Dict[str, Any]:
        """Get status of a specific crawl"""
        if crawl_id in self.active_crawls:
            session = self.active_crawls[crawl_id]
            return {
                'crawl_id': crawl_id,
                'status': session['status'],
                'platforms': session['platforms'],
                'progress': self._calculate_progress(session),
                'results_count': sum(len(data) for data in session['results'].values()),
                'errors': session['errors']
            }
        else:
            # Try to load from metadata
            try:
                metadata_path = self.data_directory / "metadata" / f"{crawl_id}_metadata.json"
                if metadata_path.exists():
                    with open(metadata_path, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                    return {
                        'crawl_id': crawl_id,
                        'status': metadata.get('status', 'unknown'),
                        'platforms': metadata.get('platforms', []),
                        'results_count': sum(len(data) for data in metadata.get('results', {}).values()),
                        'errors': metadata.get('errors', [])
                    }
            except Exception as e:
                logger.error(f"Error loading crawl metadata: {e}")
            
            return {'crawl_id': crawl_id, 'status': 'not_found'}
    
    def _calculate_progress(self, session: Dict) -> float:
        """Calculate crawl progress percentage"""
        total_platforms = len(session['platforms'])
        completed_platforms = len(session['results'])
        return (completed_platforms / total_platforms) * 100 if total_platforms > 0 else 0
    
    async def get_available_data(self) -> Dict[str, Any]:
        """Get summary of available crawled data"""
        try:
            summary = {
                'platforms': {},
                'total_files': 0,
                'total_size_mb': 0,
                'date_range': {'earliest': None, 'latest': None}
            }
            
            for platform_dir in self.data_directory.iterdir():
                if platform_dir.is_dir() and platform_dir.name != 'metadata':
                    platform_name = platform_dir.name
                    files = list(platform_dir.glob('*.csv'))
                    
                    summary['platforms'][platform_name] = {
                        'file_count': len(files),
                        'latest_crawl': None
                    }
                    
                    if files:
                        # Get latest file
                        latest_file = max(files, key=lambda f: f.stat().st_mtime)
                        summary['platforms'][platform_name]['latest_crawl'] = datetime.fromtimestamp(
                            latest_file.stat().st_mtime
                        ).isoformat()
                    
                    summary['total_files'] += len(files)
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting data summary: {e}")
            return {'error': str(e)}


# Adapter classes for smart crawlers
class SmartCrawlerAdapter:
    """Base adapter class for smart crawlers"""
    
    def __init__(self, platform_name: str):
        self.platform_name = platform_name
    
    async def crawl(self, keywords: List[str], max_results: int = 1000) -> List[Dict]:
        """Override in subclasses"""
        raise NotImplementedError


class SmartFacebookAdapter(SmartCrawlerAdapter):
    """Adapter for smart Facebook crawler"""
    
    def __init__(self):
        super().__init__('facebook')
    
    async def crawl(self, keywords: List[str], max_results: int = 1000) -> List[Dict]:
        # Implementation would call the actual smart_facebook_crawler
        # For now, return mock data
        return await self._mock_crawl(keywords, max_results)
    
    async def _mock_crawl(self, keywords: List[str], max_results: int) -> List[Dict]:
        """Mock crawling for development"""
        return [
            {
                'platform': 'facebook',
                'type': 'post',
                'id': f'fb_post_{i}',
                'text': f'Sample Facebook post about {keywords[0] if keywords else "topic"}',
                'sentiment': 'Neutral',
                'date': datetime.now().isoformat(),
                'likes': 10 + i,
                'shares': 2 + i,
                'comments_count': 5 + i
            }
            for i in range(min(max_results, 10))
        ]


# Similar adapters for other platforms...
class SmartInstagramAdapter(SmartCrawlerAdapter):
    def __init__(self):
        super().__init__('instagram')
    
    async def crawl(self, keywords: List[str], max_results: int = 1000) -> List[Dict]:
        return await self._mock_crawl(keywords, max_results)
    
    async def _mock_crawl(self, keywords: List[str], max_results: int) -> List[Dict]:
        return [
            {
                'platform': 'instagram',
                'type': 'post',
                'id': f'ig_post_{i}',
                'text': f'Sample Instagram post about {keywords[0] if keywords else "topic"}',
                'sentiment': 'Positive',
                'date': datetime.now().isoformat(),
                'likes': 20 + i,
                'comments_count': 8 + i
            }
            for i in range(min(max_results, 10))
        ]


class MockCrawler:
    """Mock crawler for development/testing"""
    
    def __init__(self, platform_name: str):
        self.platform_name = platform_name
    
    async def crawl(self, keywords: List[str], max_results: int = 1000) -> List[Dict]:
        """Generate mock data for testing"""
        return [
            {
                'platform': self.platform_name,
                'type': 'post',
                'id': f'{self.platform_name}_post_{i}',
                'text': f'Sample {self.platform_name} post about {keywords[0] if keywords else "topic"} - {i}',
                'sentiment': ['Positive', 'Neutral', 'Negative'][i % 3],
                'date': (datetime.now() - timedelta(hours=i)).isoformat(),
                'engagement': 10 + i * 2
            }
            for i in range(min(max_results, 20))
        ]


# Additional adapter classes would be implemented similarly...
class SmartTikTokAdapter(SmartCrawlerAdapter):
    def __init__(self):
        super().__init__('tiktok')
    
    async def crawl(self, keywords: List[str], max_results: int = 1000) -> List[Dict]:
        return await MockCrawler('tiktok').crawl(keywords, max_results)


class SmartTwitterAdapter(SmartCrawlerAdapter):
    def __init__(self):
        super().__init__('twitter')
    
    async def crawl(self, keywords: List[str], max_results: int = 1000) -> List[Dict]:
        return await MockCrawler('twitter').crawl(keywords, max_results)


class SmartGoogleAdapter(SmartCrawlerAdapter):
    def __init__(self):
        super().__init__('google')
    
    async def crawl(self, keywords: List[str], max_results: int = 1000) -> List[Dict]:
        return await MockCrawler('google').crawl(keywords, max_results)


class SmartNewsAdapter(SmartCrawlerAdapter):
    def __init__(self):
        super().__init__('news')
    
    async def crawl(self, keywords: List[str], max_results: int = 1000) -> List[Dict]:
        return await MockCrawler('news').crawl(keywords, max_results)


class SmartLowyatAdapter(SmartCrawlerAdapter):
    def __init__(self):
        super().__init__('lowyat')
    
    async def crawl(self, keywords: List[str], max_results: int = 1000) -> List[Dict]:
        return await MockCrawler('lowyat').crawl(keywords, max_results)
