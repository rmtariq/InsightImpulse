#!/usr/bin/env python3
"""
Test script to verify X/Twitter posts + comments crawling
Tests the 2-actor approach:
1. Posts Actor: kaitoeasyapi/twitter-x-data-tweet-scraper-pay-per-result-cheapest
2. Comments Actor: scraper_one/x-post-replies-scraper
"""

import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from data_crawlers.simple_apify_adapter import SimpleApifyAdapter

async def test_x_crawl():
    """Test X/Twitter crawling with posts + comments"""
    
    print("=" * 80)
    print("🧪 TESTING X/TWITTER POSTS + COMMENTS CRAWLING")
    print("=" * 80)
    
    # Initialize adapter
    adapter = SimpleApifyAdapter()
    
    # Test parameters - POPULAR KEYWORDS for more comments
    platform = "x"
    # query = "pilihan raya pbt"  # Low engagement
    # query = "Anwar Ibrahim"  # High profile
    query = "Malaysia"  # Very popular, should have many comments
    max_posts = 5  # Small number for testing (actor limit)
    max_comments = 20  # Comments per post (increase to get more)
    
    print(f"\n📊 Test Parameters:")
    print(f"   Platform: {platform}")
    print(f"   Query: {query}")
    print(f"   Max Posts: {max_posts}")
    print(f"   Max Comments per Post: {max_comments}")
    print(f"   Total Expected: {max_posts} posts + ~{max_posts * max_comments} comments")
    
    print("\n" + "=" * 80)
    print("🚀 PHASE 1: CRAWLING POSTS")
    print("=" * 80)
    
    try:
        # Crawl posts
        posts = await adapter.crawl_platform(
            platform=platform,
            query=query,
            max_results=max_posts,
            max_comments=0,  # Don't crawl comments yet
            comment_sampling="smart"
        )
        
        print(f"\n✅ Posts crawled: {len(posts)}")
        
        if posts:
            print(f"\n📝 Sample post:")
            sample = posts[0]
            print(f"   ID: {sample.get('ID', 'N/A')}")
            print(f"   Text: {sample.get('Text', 'N/A')[:100]}...")
            print(f"   URL: {sample.get('URL', 'N/A')}")
            print(f"   Type: {sample.get('Type', 'N/A')}")
        
    except Exception as e:
        print(f"\n❌ Error crawling posts: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("\n" + "=" * 80)
    print("🚀 PHASE 2: CRAWLING COMMENTS FOR POSTS")
    print("=" * 80)
    
    try:
        # Crawl comments for posts
        posts_with_comments = await adapter._crawl_comments_for_posts(
            platform=platform,
            posts=posts,
            comments_per_post=max_comments
        )
        
        # Count comments
        total_comments = 0
        posts_with_comments_count = 0
        
        for post in posts_with_comments:
            comments = post.get('comments', [])
            if comments:
                total_comments += len(comments)
                posts_with_comments_count += 1
        
        print(f"\n✅ Comments crawled: {total_comments}")
        print(f"   Posts with comments: {posts_with_comments_count}/{len(posts)}")
        
        if total_comments > 0:
            # Find first post with comments
            for post in posts_with_comments:
                if post.get('comments'):
                    print(f"\n📝 Sample post with comments:")
                    print(f"   Post ID: {post.get('ID', 'N/A')}")
                    print(f"   Post Text: {post.get('Text', 'N/A')[:80]}...")
                    print(f"   Comments: {len(post.get('comments', []))}")
                    
                    if post.get('comments'):
                        comment = post['comments'][0]
                        print(f"\n   📌 Sample comment:")
                        print(f"      Text: {comment.get('Text', 'N/A')[:80]}...")
                        print(f"      Type: {comment.get('Type', 'N/A')}")
                    break
        
    except Exception as e:
        print(f"\n❌ Error crawling comments: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("\n" + "=" * 80)
    print("📊 FINAL RESULTS")
    print("=" * 80)
    print(f"✅ Total Posts: {len(posts)}")
    print(f"✅ Total Comments: {total_comments}")
    print(f"✅ Posts with Comments: {posts_with_comments_count}")
    print(f"✅ Average Comments per Post: {total_comments / len(posts) if posts else 0:.1f}")
    
    print("\n" + "=" * 80)
    print("🎉 TEST COMPLETED!")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(test_x_crawl())

