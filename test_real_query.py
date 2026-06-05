#!/usr/bin/env python3
"""
Test script for real business query with all 10 platforms
Query: "PKS Malaysia online business"
"""
import asyncio
import sys
import os
from pathlib import Path
from dotenv import load_dotenv
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment
load_dotenv()

# Add backend to path
sys.path.insert(0, str(Path('.').absolute() / 'backend' / 'data_crawlers'))

from simple_apify_adapter import SimpleApifyAdapter


async def test_real_query():
    """Test all 10 platforms with real business query"""
    
    query = "PKS Malaysia online business"
    max_results = 10
    
    platforms = [
        'facebook', 'instagram', 'twitter', 'tiktok', 
        'youtube', 'google', 'news', 'linkedin',
        'shopee', 'lazada'
    ]
    
    adapter = SimpleApifyAdapter()
    results_summary = {}
    
    print("="*80)
    print(f"🔍 TESTING REAL BUSINESS QUERY")
    print("="*80)
    print(f"📝 Query: {query}")
    print(f"📊 Max Results per Platform: {max_results}")
    print(f"🌐 Platforms: {len(platforms)}")
    print("="*80)
    print()
    
    for i, platform in enumerate(platforms, 1):
        print(f"\n[{i}/{len(platforms)}] Testing {platform.upper()}...")
        print("-" * 60)
        
        try:
            results = await adapter.crawl_platform(platform, query, max_results)
            results_summary[platform] = {
                'status': 'success' if results else 'no_data',
                'count': len(results),
                'sample': results[0] if results else None
            }
            
            if results:
                print(f"✅ SUCCESS: {len(results)} records collected")
                # Show sample
                sample = results[0]
                print(f"\n📄 Sample Record:")
                print(f"   Platform: {sample.get('Platform', 'N/A')}")
                print(f"   Type: {sample.get('Type', 'N/A')}")
                print(f"   Text: {sample.get('Text', '')[:100]}...")
            else:
                print(f"⚠️  WARNING: No results returned")
                
        except Exception as e:
            logger.error(f"Error testing {platform}: {e}")
            results_summary[platform] = {
                'status': 'error',
                'count': 0,
                'error': str(e)
            }
            print(f"❌ ERROR: {e}")
        
        # Small delay between platforms
        if i < len(platforms):
            await asyncio.sleep(2)
    
    # Print summary
    print("\n" + "="*80)
    print("📊 FINAL SUMMARY")
    print("="*80)
    
    total_records = sum(r['count'] for r in results_summary.values())
    successful = sum(1 for r in results_summary.values() if r['status'] == 'success')
    
    print(f"\n✅ Successful Platforms: {successful}/{len(platforms)}")
    print(f"📈 Total Records Collected: {total_records}")
    print(f"\n📋 Detailed Results:")
    
    for platform, result in results_summary.items():
        status_icon = "✅" if result['status'] == 'success' else "❌"
        print(f"   {platform:15} {status_icon} {result['count']:4} records")
    
    print("="*80)
    
    return results_summary


if __name__ == "__main__":
    asyncio.run(test_real_query())

