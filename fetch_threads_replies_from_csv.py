#!/usr/bin/env python3
"""
Fetch Threads replies for existing posts using Apify API

This script:
1. Reads a CSV file with Threads posts
2. Extracts post URLs
3. Fetches replies using futurizerush/threads-replies-scraper-api
4. Combines posts + replies into new CSV
"""

import os
import sys
import pandas as pd
from apify_client import ApifyClient
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

# Configuration
APIFY_API_TOKEN = os.getenv('APIFY_API_TOKEN')
THREADS_SESSION_ID = os.getenv('THREADS_SESSION_ID')
REPLIES_ACTOR = 'futurizerush/threads-replies-scraper-api'

def fetch_threads_replies(csv_file_path: str, max_replies_per_post: int = 50):
    """
    Fetch replies for Threads posts from CSV file
    
    Args:
        csv_file_path: Path to CSV file with posts
        max_replies_per_post: Maximum replies to fetch per post
    """
    
    # Initialize Apify client
    if not APIFY_API_TOKEN:
        print("❌ Error: APIFY_API_TOKEN not found in .env")
        return
    
    if not THREADS_SESSION_ID or THREADS_SESSION_ID == '66920257060...paste_the_full_value_here':
        print("❌ Error: THREADS_SESSION_ID not configured in .env")
        print("   Please add your Threads Session ID to .env file")
        return
    
    client = ApifyClient(APIFY_API_TOKEN)
    
    # Read CSV file
    print(f"📂 Reading CSV: {csv_file_path}")
    df = pd.read_csv(csv_file_path)
    print(f"✅ Loaded {len(df)} posts")
    
    # Filter for Threads posts only
    threads_posts = df[df['Platform'] == 'threads'].copy()
    print(f"🧵 Found {len(threads_posts)} Threads posts")
    
    if len(threads_posts) == 0:
        print("❌ No Threads posts found in CSV")
        return
    
    # Extract post URLs
    post_urls = threads_posts['URL'].dropna().tolist()
    print(f"📋 Extracted {len(post_urls)} post URLs")
    
    if len(post_urls) == 0:
        print("❌ No valid post URLs found")
        return
    
    # Show sample URLs
    print(f"\n📋 Sample URLs (first 3):")
    for i, url in enumerate(post_urls[:3], 1):
        print(f"   {i}. {url}")
    
    # Prepare input for replies actor
    # NOTE: Actor might need full cookie string, not just sessionid
    print(f"\n🔐 Using Session ID: {THREADS_SESSION_ID[:30]}...{THREADS_SESSION_ID[-20:]}")

    actor_input = {
        "postUrls": post_urls[:20],  # Limit to 20 posts to avoid timeout
        "sessionId": THREADS_SESSION_ID
    }
    
    print(f"\n🚀 Fetching replies for {len(actor_input['postUrls'])} posts...")
    print(f"   Actor: {REPLIES_ACTOR}")
    print(f"   Max replies per post: {max_replies_per_post}")
    
    try:
        # Run actor
        run = client.actor(REPLIES_ACTOR).call(run_input=actor_input)
        
        # Get results
        dataset_id = run.get("defaultDatasetId")
        if not dataset_id:
            print("❌ No dataset found in run")
            return
        
        # Fetch all replies
        replies = list(client.dataset(dataset_id).iterate_items(clean=True))
        print(f"✅ Fetched {len(replies)} total replies!")
        
        if len(replies) == 0:
            print("⚠️ No replies found")
            return
        
        # Show sample reply
        if replies:
            print(f"\n📝 Sample reply:")
            sample = replies[0]
            print(f"   Text: {sample.get('text', '')[:100]}...")
            print(f"   Author: {sample.get('username', 'Unknown')}")
            print(f"   Likes: {sample.get('likes', 0)}")
        
        # Convert replies to DataFrame
        replies_df = pd.DataFrame(replies)
        
        # Add metadata
        replies_df['Platform'] = 'threads'
        replies_df['Type'] = 'comment'
        
        # Combine with original posts
        combined_df = pd.concat([df, replies_df], ignore_index=True)
        
        # Save to new CSV
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f"data/combined/Combined_threads_WITH_REPLIES_{timestamp}.csv"
        
        # Create directory if not exists
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        combined_df.to_csv(output_file, index=False)
        print(f"\n✅ SAVED: {output_file}")
        print(f"📊 Total records: {len(combined_df)}")
        print(f"   Posts: {len(df)}")
        print(f"   Replies: {len(replies)}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Default to latest CSV file
    csv_file = "data/combined/Combined_threads_20260528_213808.csv"
    
    # Allow custom CSV file from command line
    if len(sys.argv) > 1:
        csv_file = sys.argv[1]
    
    print(f"🎯 Threads Replies Fetcher")
    print(f"=" * 50)
    
    fetch_threads_replies(csv_file, max_replies_per_post=50)
