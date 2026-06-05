"""
Smart Crawler Bridge for InsightPulse
=====================================

This module provides a bridge between InsightPulse and the existing smart_crawlers system,
allowing seamless integration while maintaining the advanced features of smart_crawlers.

Author: InsightPulse Team
"""

import os
import sys
import json
import subprocess
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

# Smart crawlers path
SMART_CRAWLERS_PATH = "/Users/rmtariq/InsightPulse/data/smart_crawlers"

logger = logging.getLogger(__name__)


class SmartCrawlerBridge:
    """
    Bridge class that integrates the existing smart_crawlers system
    with InsightPulse, preserving all advanced features and configurations.
    """
    
    def __init__(self):
        self.smart_crawlers_path = Path(SMART_CRAWLERS_PATH)
        self.config_path = self.smart_crawlers_path / "config"
        self.crawlers_path = self.smart_crawlers_path / "crawlers"
        self.data_path = self.smart_crawlers_path / "data"
        
        # Verify smart_crawlers exists
        if not self.smart_crawlers_path.exists():
            raise FileNotFoundError(f"Smart crawlers not found at {SMART_CRAWLERS_PATH}")
        
        logger.info(f"Smart crawler bridge initialized: {SMART_CRAWLERS_PATH}")
    
    async def execute_crawler(self, platform: str, claim: str, 
                            max_results: int = 1000, 
                            config_override: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Execute a smart crawler for a specific platform
        
        Args:
            platform: Platform name (facebook, instagram, tiktok, etc.)
            claim: The claim/query to search for
            max_results: Maximum results to collect
            config_override: Optional configuration overrides
            
        Returns:
            Dict with execution results and data paths
        """
        try:
            # Map platform names to crawler files (ULTIMATE 9-PLATFORM INTEGRATION)
            crawler_map = {
                # Social Media Platforms (7) - Enhanced versions from S_crawlers
                'facebook': 'smart_facebook_crawler.py',
                'instagram': 'smart_instagram_crawler.py',
                'tiktok': 'smart_tiktok_crawler.py',
                'twitter': 'smart_x_crawler.py',
                'x': 'smart_x_crawler.py',
                'google': 'smart_google_crawler.py',
                'news': 'smart_news_crawler.py',
                'lowyat': 'smart_lowyat_crawler.py',

                # E-commerce Platforms (2) - NEW INTEGRATION
                'shopee': 'smart_shopee_crawler.py',
                'lazada': 'smart_lazada_crawler.py'
            }
            
            if platform not in crawler_map:
                raise ValueError(f"Unsupported platform: {platform}")
            
            crawler_file = crawler_map[platform]
            crawler_path = self.crawlers_path / crawler_file
            
            if not crawler_path.exists():
                raise FileNotFoundError(f"Crawler not found: {crawler_path}")
            
            # Prepare command
            cmd = [
                sys.executable,
                str(crawler_path),
                "--claim", claim,
                "--max-results", str(max_results)
            ]
            
            # Add configuration overrides if provided
            if config_override:
                # Create temporary config file
                temp_config = self._create_temp_config(platform, config_override)
                cmd.extend(["--config", str(temp_config)])
            
            logger.info(f"Executing crawler: {' '.join(cmd)}")
            
            # Execute crawler
            result = await self._run_crawler_async(cmd)
            
            # Get output data paths
            data_paths = self._get_crawler_output_paths(platform)
            
            return {
                'platform': platform,
                'status': 'success' if result['returncode'] == 0 else 'error',
                'returncode': result['returncode'],
                'stdout': result['stdout'],
                'stderr': result['stderr'],
                'data_paths': data_paths,
                'execution_time': result.get('execution_time', 0)
            }
            
        except Exception as e:
            logger.error(f"Error executing {platform} crawler: {e}")
            return {
                'platform': platform,
                'status': 'error',
                'error': str(e),
                'data_paths': []
            }
    
    async def _run_crawler_async(self, cmd: List[str]) -> Dict[str, Any]:
        """Run crawler command asynchronously"""
        import time
        start_time = time.time()
        
        try:
            # Change to smart_crawlers directory
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=str(self.smart_crawlers_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            return {
                'returncode': process.returncode,
                'stdout': stdout.decode('utf-8'),
                'stderr': stderr.decode('utf-8'),
                'execution_time': time.time() - start_time
            }
            
        except Exception as e:
            return {
                'returncode': -1,
                'stdout': '',
                'stderr': str(e),
                'execution_time': time.time() - start_time
            }
    
    def _create_temp_config(self, platform: str, config_override: Dict) -> Path:
        """Create temporary configuration file for crawler"""
        temp_config_path = self.config_path / f"temp_{platform}_config.json"
        
        # Load existing config if available
        existing_config = {}
        platform_config_path = self.config_path / f"{platform}_credentials.json"
        if platform_config_path.exists():
            with open(platform_config_path, 'r') as f:
                existing_config = json.load(f)
        
        # Merge with overrides
        merged_config = {**existing_config, **config_override}
        
        # Save temporary config
        with open(temp_config_path, 'w') as f:
            json.dump(merged_config, f, indent=2)
        
        return temp_config_path
    
    def _get_crawler_output_paths(self, platform: str) -> List[str]:
        """Get output data paths for a platform"""
        platform_data_dir = self.data_path / platform
        
        if not platform_data_dir.exists():
            return []
        
        # Get recent CSV files (last 24 hours)
        import time
        current_time = time.time()
        recent_files = []
        
        for file_path in platform_data_dir.glob("*.csv"):
            file_time = file_path.stat().st_mtime
            if current_time - file_time < 86400:  # 24 hours
                recent_files.append(str(file_path))
        
        return sorted(recent_files, key=lambda x: Path(x).stat().st_mtime, reverse=True)
    
    async def batch_crawl(self, platforms: List[str], claim: str, 
                         max_results_per_platform: int = 1000) -> Dict[str, Any]:
        """
        Execute multiple crawlers in parallel
        
        Args:
            platforms: List of platforms to crawl
            claim: The claim/query to search for
            max_results_per_platform: Max results per platform
            
        Returns:
            Dict with results for each platform
        """
        try:
            logger.info(f"Starting batch crawl for platforms: {platforms}")
            
            # Create tasks for each platform
            tasks = []
            for platform in platforms:
                task = asyncio.create_task(
                    self.execute_crawler(platform, claim, max_results_per_platform)
                )
                tasks.append((platform, task))
            
            # Execute all tasks concurrently
            results = {}
            for platform, task in tasks:
                try:
                    result = await task
                    results[platform] = result
                except Exception as e:
                    logger.error(f"Error in {platform} crawler: {e}")
                    results[platform] = {
                        'platform': platform,
                        'status': 'error',
                        'error': str(e)
                    }
            
            # Aggregate results
            successful_platforms = [p for p, r in results.items() if r['status'] == 'success']
            failed_platforms = [p for p, r in results.items() if r['status'] == 'error']
            
            return {
                'batch_status': 'completed',
                'total_platforms': len(platforms),
                'successful_platforms': successful_platforms,
                'failed_platforms': failed_platforms,
                'results': results,
                'summary': {
                    'success_count': len(successful_platforms),
                    'failure_count': len(failed_platforms),
                    'success_rate': len(successful_platforms) / len(platforms) * 100
                }
            }
            
        except Exception as e:
            logger.error(f"Error in batch crawl: {e}")
            return {
                'batch_status': 'error',
                'error': str(e),
                'results': {}
            }
    
    def get_smart_crawler_config(self, platform: str) -> Dict[str, Any]:
        """Get configuration for a specific smart crawler"""
        try:
            config_file = self.config_path / f"{platform}_credentials.json"
            if config_file.exists():
                with open(config_file, 'r') as f:
                    return json.load(f)
            else:
                logger.warning(f"Config file not found for {platform}")
                return {}
        except Exception as e:
            logger.error(f"Error loading config for {platform}: {e}")
            return {}
    
    def update_smart_crawler_config(self, platform: str, config: Dict[str, Any]) -> bool:
        """Update configuration for a specific smart crawler"""
        try:
            config_file = self.config_path / f"{platform}_credentials.json"
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            logger.info(f"Updated config for {platform}")
            return True
        except Exception as e:
            logger.error(f"Error updating config for {platform}: {e}")
            return False
    
    def get_available_platforms(self) -> List[str]:
        """Get list of available crawler platforms"""
        platforms = []
        crawler_files = {
            # Social Media Platforms (7)
            'smart_facebook_crawler.py': 'facebook',
            'smart_instagram_crawler.py': 'instagram',
            'smart_tiktok_crawler.py': 'tiktok',
            'smart_x_crawler.py': 'twitter',
            'smart_google_crawler.py': 'google',
            'smart_news_crawler.py': 'news',
            'smart_lowyat_crawler.py': 'lowyat',

            # E-commerce Platforms (2) - ULTIMATE INTEGRATION
            'smart_shopee_crawler.py': 'shopee',
            'smart_lazada_crawler.py': 'lazada'
        }
        
        for crawler_file, platform in crawler_files.items():
            if (self.crawlers_path / crawler_file).exists():
                platforms.append(platform)
        
        return platforms
    
    async def get_crawler_status(self) -> Dict[str, Any]:
        """Get status of smart crawler system"""
        try:
            available_platforms = self.get_available_platforms()
            
            # Check data directories
            data_status = {}
            for platform in available_platforms:
                platform_dir = self.data_path / platform
                if platform_dir.exists():
                    files = list(platform_dir.glob("*.csv"))
                    data_status[platform] = {
                        'data_files': len(files),
                        'latest_file': max(files, key=lambda f: f.stat().st_mtime).name if files else None
                    }
                else:
                    data_status[platform] = {'data_files': 0, 'latest_file': None}
            
            return {
                'status': 'operational',
                'smart_crawlers_path': str(self.smart_crawlers_path),
                'available_platforms': available_platforms,
                'data_status': data_status,
                'config_files': [f.name for f in self.config_path.glob("*.json")]
            }
            
        except Exception as e:
            logger.error(f"Error getting crawler status: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def copy_data_to_insightpulse(self, platform: str, target_dir: Path) -> List[str]:
        """
        Copy smart crawler data to InsightPulse data directory
        
        Args:
            platform: Platform name
            target_dir: Target directory in InsightPulse
            
        Returns:
            List of copied file paths
        """
        try:
            import shutil
            
            source_dir = self.data_path / platform
            if not source_dir.exists():
                return []
            
            target_dir.mkdir(parents=True, exist_ok=True)
            copied_files = []
            
            # Copy recent CSV files
            for csv_file in source_dir.glob("*.csv"):
                target_file = target_dir / csv_file.name
                shutil.copy2(csv_file, target_file)
                copied_files.append(str(target_file))
            
            logger.info(f"Copied {len(copied_files)} files from {platform}")
            return copied_files
            
        except Exception as e:
            logger.error(f"Error copying data for {platform}: {e}")
            return []


# Convenience functions for easy integration
async def quick_crawl(platform: str, claim: str, max_results: int = 1000) -> Dict[str, Any]:
    """Quick crawl function for single platform"""
    bridge = SmartCrawlerBridge()
    return await bridge.execute_crawler(platform, claim, max_results)


async def multi_platform_crawl(platforms: List[str], claim: str, 
                              max_results: int = 1000) -> Dict[str, Any]:
    """Multi-platform crawl function"""
    bridge = SmartCrawlerBridge()
    return await bridge.batch_crawl(platforms, claim, max_results)


def get_smart_crawler_data(platform: str) -> List[str]:
    """Get available data files for a platform"""
    bridge = SmartCrawlerBridge()
    return bridge._get_crawler_output_paths(platform)
