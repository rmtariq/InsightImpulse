#!/usr/bin/env python3
"""
Test Facebook crawl with 2-actor strategy
"""
import sys
import os
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add backend to path
sys.path.insert(0, 'backend')

from data_crawlers.simple_apify_adapter import SimpleApifyAdapter

async def test_facebook_crawl():
    """Test Facebook crawl with danek/facebook-search-ppr actor"""

    print("="*80)
    print("🧪 TESTING FACEBOOK CRAWL - 2-ACTOR STRATEGY")
    print("="*80)
    print()

    # Get Apify token from environment or settings
    apify_token = os.getenv('APIFY_TOKEN') or os.getenv('APIFY_API_TOKEN')

    # Try to import from settings if not in env
    if not apify_token:
        try:
            from data_crawlers.settings import APIFY_API_TOKEN
            apify_token = APIFY_API_TOKEN
        except Exception as e:
            print(f"⚠️ Could not import from settings: {e}")

    if not apify_token:
        print("❌ APIFY_TOKEN not found in environment or settings")
        print("💡 Make sure APIFY_API_TOKEN is set in .env file")
        return

    print(f"✅ Apify token: {apify_token[:10]}...")
    print()
    
    # Initialize adapter
    adapter = SimpleApifyAdapter(apify_token)
    
    # Test query
    query = "pilihan raya pbt"
    max_results = 5  # Small test
    
    print(f"📊 Test Parameters:")
    print(f"   Query: {query}")
    print(f"   Max Results: {max_results}")
    print()
    
    # Check actor mapping
    print(f"🎯 Actor Configuration:")
    print(f"   Main Actor: {adapter.actor_map.get('facebook')}")
    print(f"   Comments Actor: {adapter.comments_actor_map.get('facebook')}")
    print()
    
    # Test input preparation
    print(f"📝 Testing Input Preparation...")
    input_data = adapter._prepare_facebook_input(query, max_results)
    print(f"   Input Data: {input_data}")
    print(f"   ✅ Has 'query' parameter: {'query' in input_data}")
    print(f"   ✅ Query value: {input_data.get('query')}")
    print()
    
    # Test actual crawl
    print(f"🚀 Starting Facebook Crawl...")
    print(f"   This will use: {adapter.actor_map.get('facebook')}")
    print()
    
    try:
        results = await adapter.crawl_platform(
            platform='facebook',
            query=query,
            max_results=max_results,
            max_comments=5,
            comment_sampling='smart'
        )
        
        print()
        print("="*80)
        print("✅ CRAWL COMPLETED!")
        print("="*80)
        print(f"📊 Results: {len(results)} records")
        
        if results:
            # Count posts vs comments
            posts = [r for r in results if r.get('Type') == 'post']
            comments = [r for r in results if r.get('Type') == 'comment']
            
            print(f"   Posts: {len(posts)}")
            print(f"   Comments: {len(comments)}")
            print()
            
            # Show sample post
            if posts:
                print("📝 Sample Post:")
                sample = posts[0]
                print(f"   Text: {sample.get('Text', '')[:100]}...")
                print(f"   Likes: {sample.get('likes', 0)}")
                print(f"   Comments: {sample.get('comments_count', 0)}")
                print()
            
            # Show sample comment
            if comments:
                print("💬 Sample Comment:")
                sample = comments[0]
                print(f"   Text: {sample.get('Text', '')[:100]}...")
                print(f"   Likes: {sample.get('likes', 0)}")
                print()
        else:
            print("⚠️ No results returned")
        
        print("="*80)
        
    except Exception as e:
        print()
        print("="*80)
        print("❌ CRAWL FAILED!")
        print("="*80)
        print(f"Error: {e}")
        print()
        import traceback
        traceback.print_exc()
        print("="*80)

if __name__ == "__main__":
    asyncio.run(test_facebook_crawl())

