#!/usr/bin/env python3
"""
Test script to verify all 9 platform crawlers one by one.
Tests with small limits: 5-10 posts and 5-10 comments per platform.
"""

import asyncio
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend" / "data_crawlers"))

from simple_apify_adapter import SimpleApifyAdapter

# Test configuration
TEST_QUERY = "Malaysia"
MAX_POSTS = 10
PLATFORMS = [
    'facebook',
    'instagram', 
    'twitter',
    'tiktok',
    'youtube',
    'google',
    'news',
    'linkedin',
    'shopee',
    'lazada'
]

async def test_platform(adapter: SimpleApifyAdapter, platform: str, query: str, max_results: int):
    """Test a single platform crawler"""
    print(f"\n{'='*80}")
    print(f"🧪 TESTING: {platform.upper()}")
    print(f"{'='*80}")
    print(f"📝 Query: {query}")
    print(f"📊 Max Results: {max_results}")
    print(f"💬 Max Comments: 10")
    print(f"⏰ Starting test...")
    
    try:
        results = await adapter.crawl_platform(platform, query, max_results)
        
        if results and len(results) > 0:
            print(f"✅ SUCCESS: Collected {len(results)} records from {platform}")
            
            # Show sample data
            if len(results) > 0:
                print(f"\n📄 Sample Record:")
                sample = results[0]
                for key, value in list(sample.items())[:5]:
                    if isinstance(value, str) and len(value) > 100:
                        value = value[:100] + "..."
                    print(f"   {key}: {value}")
            
            return True
        else:
            print(f"⚠️  WARNING: No results returned from {platform}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {platform} test failed - {str(e)}")
        return False

async def main():
    """Run tests for all platforms"""
    print("="*80)
    print("🚀 STARTING CRAWLER TESTS FOR ALL 9 PLATFORMS")
    print("="*80)
    print(f"📝 Test Query: {TEST_QUERY}")
    print(f"📊 Max Posts per Platform: {MAX_POSTS}")
    print(f"💬 Max Comments per Post: 10")
    print("="*80)
    
    # Initialize adapter
    adapter = SimpleApifyAdapter()
    
    # Track results
    results = {}
    
    # Test each platform
    for platform in PLATFORMS:
        success = await test_platform(adapter, platform, TEST_QUERY, MAX_POSTS)
        results[platform] = success
        
        # Wait between tests to avoid rate limiting
        if platform != PLATFORMS[-1]:
            print(f"\n⏳ Waiting 5 seconds before next test...")
            await asyncio.sleep(5)
    
    # Summary
    print(f"\n{'='*80}")
    print("📊 TEST SUMMARY")
    print(f"{'='*80}")
    
    successful = sum(1 for v in results.values() if v)
    failed = len(results) - successful
    
    print(f"\n✅ Successful: {successful}/{len(PLATFORMS)}")
    print(f"❌ Failed: {failed}/{len(PLATFORMS)}")
    
    print(f"\n📋 Detailed Results:")
    for platform, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {platform:15} {status}")
    
    print(f"\n{'='*80}")
    
    if successful == len(PLATFORMS):
        print("🎉 ALL TESTS PASSED!")
    elif successful > 0:
        print(f"⚠️  PARTIAL SUCCESS: {successful}/{len(PLATFORMS)} platforms working")
    else:
        print("❌ ALL TESTS FAILED")
    
    print(f"{'='*80}\n")

if __name__ == "__main__":
    asyncio.run(main())

