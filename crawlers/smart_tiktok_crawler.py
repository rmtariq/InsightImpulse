#!/usr/bin/env python
# -*- coding: utf-8 -*-



import requests
import time
import csv
import json
import os
import uuid
import argparse
import sys
from datetime import datetime
# Add utils directory to path for emotion analysis
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'utils'))

try:
    from universal_analysis import get_analyzer, add_analysis_to_data
    EMOTION_ANALYSIS_AVAILABLE = True
    print("✅ Emotion analysis available for TikTok crawler!")
except ImportError:
    print("⚠️ Emotion analysis not available - continuing with sentiment only")
    EMOTION_ANALYSIS_AVAILABLE = False

from smart_facebook_crawler import (
    analyze_sentiment, extract_smart_keywords, generate_search_strategies,
    detect_boolean_query, parse_boolean_or_query, initialize_sentiment_analyzer
)

# Load configuration
def load_config():
    """Load configuration from config file."""
    try:
        with open('config/api_credentials.json', 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        return {}

config = load_config()
APIFY_TOKEN = config.get('apify', {}).get('token', "apify_api_UiTteCekixYYQbhDrmoNqATMsaKddD08q9J3")
# UPDATED: Use your working TikTok actor IDs
TIKTOK_SCRAPER_ID = config.get('apify', {}).get('actors', {}).get('tiktok_scraper', "OtzYfK1ndEGdwWFKQ")
TIKTOK_COMMENTS_ID = config.get('apify', {}).get('actors', {}).get('tiktok_comments', "BDec00yAmCm1QbMEI")
TIKTOK_HASHTAG_ID = config.get('apify', {}).get('actors', {}).get('tiktok_hashtag', "f1ZeP0K58iwlqG2pY")
TIKTOK_PROFILE_ID = config.get('apify', {}).get('actors', {}).get('tiktok_profile', "0FXVyOXXEmdGcV88a")
TIKTOK_SEARCH_ID = config.get('apify', {}).get('actors', {}).get('tiktok_search', "if12dqi9gDL3GUpcq")
PROXY_CONFIG = config.get('proxy', {}).get('apify_proxy', {})
PROXY_PASSWORD = PROXY_CONFIG.get('password', "apify_proxy_vZKKP5iUM3VHc7vi_EGwVnbQyvhBm693b5YuR")

def run_apify_actor(actor_id, input_data, max_wait_time=300):
    """Run an Apify actor and wait for results."""
    try:
        headers = {
            "Authorization": f"Bearer {APIFY_TOKEN}",
            "Content-Type": "application/json"
        }

        print(f"🚀 Starting TikTok actor: {actor_id}")

        response = requests.post(
            f"https://api.apify.com/v2/acts/{actor_id}/runs",
            headers=headers,
            json=input_data
        )

        if response.status_code != 201:
            print(f"❌ Error starting actor: {response.status_code}")
            print(f"   Response: {response.text}")
            return []

        run_data = response.json()
        run_id = run_data["data"]["id"]
        print(f"✅ Actor started successfully! Run ID: {run_id}")

        # Wait for completion
        print("⏳ Waiting for results...")
        start_time = time.time()
        while time.time() - start_time < max_wait_time:
            status_response = requests.get(
                f"https://api.apify.com/v2/actor-runs/{run_id}",
                headers=headers
            )

            if status_response.status_code == 200:
                status = status_response.json()["data"]["status"]

                if status == "SUCCEEDED":
                    print("✅ Task completed successfully!")
                    break
                elif status in ["FAILED", "ABORTED", "TIMED-OUT"]:
                    print(f"❌ Task failed with status: {status}")
                    return []

            time.sleep(10)

        # Get results
        results_response = requests.get(
            f"https://api.apify.com/v2/actor-runs/{run_id}/dataset/items",
            headers=headers
        )

        if results_response.status_code == 200:
            results = results_response.json()
            print(f"📊 Retrieved {len(results)} items")
            return results
        else:
            print(f"❌ Error getting results: {results_response.status_code}")
            return []

    except Exception as e:
        print(f"❌ Error running task: {e}")
        return []

def crawl_tiktok_posts(query, max_posts):
    """Crawl TikTok posts for a search query."""
    input_data = {
        "searchQueries": [query],
        "resultsPerPage": max_posts,
        "shouldDownloadCovers": False,
        "shouldDownloadSlideshowImages": False,
        "shouldDownloadSubtitles": False,
        "shouldDownloadVideos": False,
        "proxyConfiguration": {
            "useApifyProxy": True,
            "apifyProxyGroups": ["RESIDENTIAL"],
            "countryCode": "MY",
            "password": PROXY_PASSWORD,
            "useChrome": True,
            "sessionId": f"tiktok-posts-{uuid.uuid4().hex[:8]}"
        }
    }

    return run_apify_actor(TIKTOK_SCRAPER_ID, input_data, max_wait_time=600)

def crawl_tiktok_comments(post_urls, max_comments):
    """Crawl comments for TikTok posts."""
    if not post_urls:
        print("❌ No post URLs provided for comment crawling")
        return []

    print(f"💬 Crawling comments for {len(post_urls)} posts...")

    # Prepare URLs - ensure they're valid TikTok URLs
    valid_urls = []
    for url in post_urls:
        if "tiktok.com" in url and url.startswith("http"):
            valid_urls.append(url)
        else:
            print(f"⚠️ Invalid URL skipped: {url}")

    if not valid_urls:
        print("❌ No valid TikTok URLs found")
        return []

    input_data = {
        "postURLs": valid_urls,
        "commentsPerPost": max_comments * 2,
        "proxyConfiguration": {
            "useApifyProxy": True,
            "apifyProxyGroups": ["RESIDENTIAL"],
            "countryCode": "MY",
            "password": PROXY_PASSWORD,
            "useChrome": True,
            "sessionId": f"tiktok-comments-{uuid.uuid4().hex[:8]}"
        }
    }

    print(f"🔧 Comment crawler config: {max_comments * 2} comments")
    return run_apify_actor(TIKTOK_COMMENTS_ID, input_data, max_wait_time=600)

def smart_crawl_tiktok(claim, max_posts=200, max_comments=500):
    """Smart TikTok crawling with Boolean OR support."""
    print(f"\n🎵 SMART TIKTOK CRAWLING")
    print("=" * 50)
    print(f"📝 Input: {claim}")
    print(f"📊 Target: {max_posts} posts, {max_comments} comments")

    # Check if input is a Boolean OR query
    if detect_boolean_query(claim):
        print("🎯 DETECTED: Boolean OR Query")
        print("🔧 Converting to effective search strategies...")
        search_strategies = parse_boolean_or_query(claim)
    else:
        print("🔍 DETECTED: Regular Claim")
        # Extract smart keywords
        keywords = extract_smart_keywords(claim)
        # Generate search strategies
        search_strategies = generate_search_strategies(claim, keywords)

    # Calculate posts per strategy for better distribution
    strategies_to_use = min(len(search_strategies), 6)  # Use up to 6 strategies
    posts_per_strategy = max(10, max_posts // strategies_to_use)

    print(f"\n🎯 CRAWLING PLAN:")
    print(f"📊 Using {strategies_to_use} strategies")
    print(f"📈 ~{posts_per_strategy} posts per strategy")
    print(f"🎯 Target total: {max_posts:,} posts + {max_comments:,} comments")

    all_posts = []
    all_comments = []

    # Try each search strategy
    for i, strategy in enumerate(search_strategies[:strategies_to_use], 1):
        print(f"\n🔍 Strategy {i}/{strategies_to_use}: '{strategy}'")

        # Crawl posts for this strategy
        posts = crawl_tiktok_posts(strategy, posts_per_strategy)

        if posts:
            print(f"✅ Found {len(posts)} posts (using all)")
            all_posts.extend(posts)

            # Get comments for each post individually
            if posts:
                print(f"💬 Getting comments for {len(posts)} posts individually...")

                for post_index, post in enumerate(posts[:5], 1):  # Process up to 5 posts per strategy
                    url = post.get("webVideoUrl") or post.get("videoUrl")
                    if url and "tiktok.com" in url:
                        print(f"   🔍 Post {post_index}: Getting comments...")

                        # Get comments for this specific post
                        comments_per_post = max(5, max_comments // (strategies_to_use * 5))
                        post_comments = crawl_tiktok_comments([url], comments_per_post)

                        if post_comments:
                            print(f"   ✅ Found {len(post_comments)} comments for post {post_index}")
                            all_comments.extend(post_comments)
                        else:
                            print(f"   ❌ No comments found for post {post_index}")

                        # Small delay between posts
                        time.sleep(3)
                    else:
                        print(f"   ⚠️ Post {post_index}: Invalid URL")
        else:
            print("❌ No posts found")

        # Avoid rate limiting between strategies
        time.sleep(5)

        # Progress update
        print(f"📊 Progress: {len(all_posts)} posts, {len(all_comments)} comments collected so far")

    # Process and save data
    if all_posts or all_comments:
        print(f"\n📋 FINAL RESULTS:")
        print(f"📊 Total posts: {len(all_posts)}")
        print(f"💬 Total comments: {len(all_comments)}")

        # Save to CSV
        csv_file = save_tiktok_csv(all_posts, all_comments, claim)

        return all_posts, all_comments, csv_file
    else:
        print("❌ No TikTok data found for this claim")
        return [], [], None

def save_tiktok_csv(posts, comments, claim):
    """Save TikTok data to CSV in the same format as Facebook."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Create safe filename
    safe_claim = "".join(c for c in claim[:50] if c.isalnum() or c in (' ', '_')).rstrip()
    safe_claim = "_".join(safe_claim.split())

    # Determine the correct data directory
    if os.path.exists("../data/tiktok"):
        # Running from crawlers directory
        data_dir = "../data/tiktok"
    elif os.path.exists("data/tiktok"):
        # Running from root directory
        data_dir = "data/tiktok"
    else:
        # Create directory in parent location
        data_dir = "../data/tiktok"
        os.makedirs(data_dir, exist_ok=True)
        
    filepath = f"{data_dir}/tiktok_factcheck_{safe_claim}_{timestamp}.csv"

    # Define columns in exact order (now includes emotion analysis)
    columns = [
        'Platform', 'Type', 'ID', 'Text', 'Sentiment', 'Date',
        'likes', 'shares', 'comments_count', 'views', 'sentiment_score', 'total_engagement',
        'emotion', 'emotion_score'
    ]

    data = []

    # Group comments by post URL/ID for proper linking
    comments_by_post = {}
    for comment in comments:
        post_url = comment.get('postUrl', '') or comment.get('videoUrl', '') or ''
        post_id = comment.get('postId', '') or ''

        # Use post_url as key, fallback to post_id
        key = post_url if post_url else post_id
        if key:
            if key not in comments_by_post:
                comments_by_post[key] = []
            comments_by_post[key].append(comment)

    print(f"📊 Organizing data: {len(posts)} posts, {len(comments)} comments")
    print(f"🔗 Comments grouped by {len(comments_by_post)} posts")

    # Process each post followed immediately by its comments (like Facebook)
    for post_index, post in enumerate(posts):
        # Process the post first
        text = post.get('text', '') or post.get('desc', '') or ''
        sentiment, sentiment_score = analyze_sentiment(text)

        # Add emotion analysis
        emotion = 'neutral'
        emotion_score = 0.0
        if EMOTION_ANALYSIS_AVAILABLE and text.strip():
            try:
                analyzer = get_analyzer()
                emotion_result = analyzer.analyze_text(text)
                emotion = emotion_result.get('emotion', 'neutral')
                emotion_score = emotion_result.get('emotion_score', 0.0)
            except Exception as e:
                print(f"⚠️ Emotion analysis failed for post {post_index + 1}: {e}")
                emotion = 'neutral'
                emotion_score = 0.0

        # Extract engagement metrics
        likes = post.get('diggCount', 0) or 0
        shares = post.get('shareCount', 0) or 0
        comments_count = post.get('commentCount', 0) or 0
        views = post.get('playCount', 0) or 0

        total_engagement = likes + shares + comments_count + views

        # Format date
        date_str = post.get('createTimeISO', '') or datetime.now().strftime("%b %d at %I:%M %p")
        if 'T' in date_str:
            try:
                dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                date_str = dt.strftime("%b %d at %I:%M %p")
            except:
                date_str = datetime.now().strftime("%b %d at %I:%M %p")

        # Create post ID
        post_id = post.get('id', '') or f"tiktok_post_{post_index + 1}"
        post_url = post.get('webVideoUrl', '') or post.get('videoUrl', '') or ''

        post_data = {
            'Platform': 'TikTok',
            'Type': 'TikTok Post',
            'ID': post_id,
            'Text': text,
            'Sentiment': sentiment,
            'Date': date_str,
            'likes': likes,
            'shares': shares,
            'comments_count': comments_count,
            'views': views,
            'sentiment_score': f"{sentiment_score:.4f}",
            'total_engagement': total_engagement,
            'emotion': emotion,
            'emotion_score': f"{emotion_score:.4f}"
        }

        data.append(post_data)

        # Add comments for this post immediately after the post (like Facebook)
        post_comments = comments_by_post.get(post_url, [])
        if not post_comments and post_id:
            post_comments = comments_by_post.get(post_id, [])

        # If no specific comments found, distribute comments evenly across posts
        if not post_comments and comments:
            # Calculate how many comments this post should get
            comments_per_post = len(comments) // len(posts)
            start_index = post_index * comments_per_post
            end_index = start_index + comments_per_post

            # For the last post, take remaining comments
            if post_index == len(posts) - 1:
                end_index = len(comments)

            post_comments = comments[start_index:end_index]
            print(f"📊 Distributing comments {start_index}-{end_index} to post {post_index + 1}")

        # Process comments for this post
        for comment_index, comment in enumerate(post_comments):
            # Analyze sentiment
            comment_text = comment.get('text', '') or ''
            comment_sentiment, comment_sentiment_score = analyze_sentiment(comment_text)

            # Add emotion analysis for comments
            comment_emotion = 'neutral'
            comment_emotion_score = 0.0
            if EMOTION_ANALYSIS_AVAILABLE and comment_text.strip():
                try:
                    analyzer = get_analyzer()
                    emotion_result = analyzer.analyze_text(comment_text)
                    comment_emotion = emotion_result.get('emotion', 'neutral')
                    comment_emotion_score = emotion_result.get('emotion_score', 0.0)
                except Exception as e:
                    print(f"⚠️ Emotion analysis failed for comment {comment_index + 1}: {e}")
                    comment_emotion = 'neutral'
                    comment_emotion_score = 0.0

            # Extract engagement metrics
            comment_likes = comment.get('diggCount', 0) or 0

            # Format date
            comment_date_str = comment.get('createTimeISO', '') or datetime.now().strftime("%b %d at %I:%M %p")
            if 'T' in comment_date_str:
                try:
                    dt = datetime.fromisoformat(comment_date_str.replace('Z', '+00:00'))
                    comment_date_str = dt.strftime("%b %d at %I:%M %p")
                except:
                    comment_date_str = datetime.now().strftime("%b %d at %I:%M %p")

            # Create comment ID linked to this post
            comment_id = f"{post_id}_{comment_index + 2000001}"

            comment_data = {
                'Platform': 'TikTok',
                'Type': 'TikTok Comment',
                'ID': comment_id,
                'Text': comment_text,
                'Sentiment': comment_sentiment,
                'Date': comment_date_str,
                'likes': comment_likes,
                'shares': 0,
                'comments_count': 0,
                'views': 0,
                'sentiment_score': f"{comment_sentiment_score:.4f}",
                'total_engagement': comment_likes,
                'emotion': comment_emotion,
                'emotion_score': f"{comment_emotion_score:.4f}"
            }

            data.append(comment_data)

    # Write CSV with TAB-separated format
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=columns, delimiter='\t')
        writer.writeheader()
        writer.writerows(data)

    print(f"💾 TikTok data saved: {filepath}")
    print(f"📊 Structure: Post → Comments → Post → Comments (like Facebook)")
    return filepath

def main():
    """Main TikTok crawler function."""
    parser = argparse.ArgumentParser(
        description="Smart TikTok Crawler for Fact-Checking",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python smart_tiktok_crawler.py --claim "vaksin covid selamat"
  python smart_tiktok_crawler.py --claim "kerajaan bantuan e-wallet" --output custom_output.csv
        """
    )

    parser.add_argument(
        "--claim",
        required=True,
        help="The claim to fact-check"
    )

    parser.add_argument(
        "--output",
        help="Output CSV file path (optional, auto-generated if not provided)"
    )

    parser.add_argument(
        "--max-results",
        type=int,
        default=700,
        help="Maximum number of results to collect (default: 700)"
    )

    # Check if running with arguments or interactively
    if len(sys.argv) == 1:
        # Interactive mode
        print("🎵 SMART TIKTOK CRAWLER")
        print("=" * 60)
        print("🎯 Processes any claim with intelligent keyword extraction")
        print("🇲🇾 Optimized for Malaysian content and context")
        print("🔍 Supports Boolean OR queries and thousands of data")
        print("=" * 60)

        # Get user input
        print("\n📝 ENTER YOUR INPUT:")
        print("-" * 30)
        print("💡 You can enter:")
        print("   1️⃣ Regular claim: 'Benarkah kerajaan akan...'")
        print("   2️⃣ Boolean OR query: '\"rafizi letak jawatan\" OR rafizi OR menteri'")
        print()

        while True:
            claim = input("🔍 Enter claim or Boolean OR query: ").strip()
            if claim:
                break
            print("❌ Please enter a valid input!")

        print(f"\n✅ Claim/Keywords: {claim}")

        print("\n🔧 TIKTOK CRAWLER CONFIGURATION:")
        print("=" * 50)
        print("📊 Configure exactly how much data you want to collect")
        print("=" * 50)

        # Configure videos
        while True:
            try:
                max_posts = int(input("\n🎬 How many TikTok VIDEOS to collect? (1-3000): "))
                if 1 <= max_posts <= 3000:
                    break
                print("❌ Please enter a number between 1 and 3000!")
            except ValueError:
                print("❌ Please enter a valid number!")

        # Configure comments per video
        while True:
            try:
                comments_per_video = int(input("💬 How many COMMENTS per video? (1-300): "))
                if 1 <= comments_per_video <= 300:
                    break
                print("❌ Please enter a number between 1 and 300!")
            except ValueError:
                print("❌ Please enter a valid number!")

        # Configure search strategies
        while True:
            try:
                num_strategies = int(input("🎯 How many search STRATEGIES to use? (3-7): "))
                if 3 <= num_strategies <= 7:
                    break
                print("❌ Please enter a number between 3 and 7!")
            except ValueError:
                print("❌ Please enter a valid number!")

        # Calculate totals
        max_comments = max_posts * comments_per_video

        print(f"\n✅ TIKTOK CRAWLER CONFIGURATION:")
        print("=" * 50)
        print(f"📝 Claim/Keywords: {claim}")
        print(f"🎬 Videos to collect: {max_posts:,}")
        print(f"💬 Comments per video: {comments_per_video:,}")
        print(f"🎯 Search strategies: {num_strategies}")
        print(f"📈 Total comments: {max_comments:,}")
        print(f"🎉 TOTAL ESTIMATED RECORDS: {max_posts + max_comments:,}")
        print("=" * 50)

        # Confirm configuration
        confirm = input("\n✅ Proceed with this configuration? (y/n, default: y): ").strip().lower()
        if confirm and confirm not in ['y', 'yes']:
            print("❌ Configuration cancelled!")
            return

        output_file = None
    else:
        # Command-line mode
        args = parser.parse_args()
        claim = args.claim
        total_results = args.max_results
        output_file = args.output

        # Split results between posts and comments
        max_posts = total_results // 3
        max_comments = total_results - max_posts

        print("🎵 SMART TIKTOK CRAWLER")
        print("=" * 60)
        print(f"📝 Claim: {claim}")
        print(f"📊 Max Results: {total_results:,} ({max_posts} posts + {max_comments} comments)")
        if output_file:
            print(f"📁 Output: {output_file}")
        print("=" * 60)

    # Run the crawler
    posts, comments, csv_file = smart_crawl_tiktok(claim, max_posts, max_comments)

    # Handle custom output file
    if output_file and csv_file:
        import shutil
        shutil.move(csv_file, output_file)
        csv_file = output_file

    if csv_file:
        print(f"\n🎉 TIKTOK CRAWLING COMPLETE!")
        print(f"📁 Data saved to: {csv_file}")
        print(f"📊 Total records: {len(posts) + len(comments):,}")
    else:
        print("\n❌ No data collected. Try different search terms.")

if __name__ == "__main__":
    main()
