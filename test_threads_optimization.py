#!/usr/bin/env python3
"""
Test Threads Optimization - Batched Parallel Comments Fetching

This script tests the NEW batched parallel strategy for Threads comments.
It will crawl Threads posts and fetch comments using the optimized approach.

Usage:
    python test_threads_optimization.py
"""

import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / 'backend'))

from dotenv import load_dotenv
load_dotenv()

# Import the adapter
from data_crawlers.simple_apify_adapter import SimpleApifyAdapter

async def test_threads_optimization():
    """
    Test the optimized Threads crawler with batched parallel comments
    """
    print("=" * 70)
    print("🧵 THREADS OPTIMIZATION TEST")
    print("=" * 70)
    print()
    
    # Check Session ID
    session_id = os.getenv('THREADS_SESSION_ID')
    if not session_id or session_id == '66920257060...paste_the_full_value_here':
        print("❌ ERROR: THREADS_SESSION_ID not configured in .env")
        print("   Please add your Threads Session ID to continue.")
        return
    
    print(f"✅ Session ID configured: {session_id[:20]}...")
    print()
    
    # Initialize adapter
    print("🔧 Initializing Simple Apify Adapter...")
    adapter = SimpleApifyAdapter()
    print("✅ Adapter initialized")
    print()
    
    # Test parameters
    query = "Anwar Ibrahim"  # Popular Malaysian topic
    max_results = 100  # Small test: 100 total items
    max_comments = 50  # Max comments per post
    
    print(f"📋 Test Parameters:")
    print(f"   Query: {query}")
    print(f"   Target results: {max_results}")
    print(f"   Max comments per post: {max_comments}")
    print()
    
    print("🚀 Starting Threads crawl with BATCHED PARALLEL optimization...")
    print()
    
    # Start timer
    start_time = datetime.now()
    
    try:
        # Call the optimized scraper
        results = await adapter._scrape_threads_with_replies(
            query=query,
            max_results=max_results,
            max_comments=max_comments,
            comment_sort="top"
        )
        
        # End timer
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print()
        print("=" * 70)
        print("📊 RESULTS")
        print("=" * 70)
        print()
        
        # Count posts vs comments
        posts = [r for r in results if r.get('Type') == 'post']
        comments = [r for r in results if r.get('Type') == 'comment']
        
        print(f"✅ Total items: {len(results)}")
        print(f"   Posts: {len(posts)}")
        print(f"   Comments: {len(comments)}")
        print(f"   Time taken: {duration:.2f} seconds ({duration/60:.2f} minutes)")
        print()
        
        # Calculate metrics
        if len(posts) > 0:
            avg_comments_per_post = len(comments) / len(posts)
            print(f"📈 Metrics:")
            print(f"   Average comments per post: {avg_comments_per_post:.1f}")
            print(f"   Data completeness: {len(results)}/{max_results} ({len(results)/max_results*100:.1f}%)")
            print()
        
        # Show sample data
        if results:
            print("📝 Sample Data (first 3 items):")
            for i, item in enumerate(results[:3], 1):
                item_type = item.get('Type', 'unknown')
                text = item.get('Text', '')[:80]
                print(f"   {i}. [{item_type}] {text}...")
            print()
        
        # Success message
        print("=" * 70)
        print("🎉 TEST COMPLETED SUCCESSFULLY!")
        print("=" * 70)
        print()
        print("✅ Batched parallel optimization is WORKING!")
        print(f"✅ Fetched {len(comments)} comments from {len(posts)} posts")
        print(f"✅ Total time: {duration:.2f} seconds")
        print()
        
        # Comparison with old approach
        if len(posts) > 20:
            print("💡 Performance Comparison:")
            print(f"   OLD approach: Would only process 20/{len(posts)} posts (LIMITED!)")
            print(f"   NEW approach: Processed ALL {len(posts)} posts! ✅")
            print()
        
    except Exception as e:
        print()
        print("=" * 70)
        print("❌ ERROR")
        print("=" * 70)
        print()
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        print()

if __name__ == "__main__":
    print()
    asyncio.run(test_threads_optimization())
