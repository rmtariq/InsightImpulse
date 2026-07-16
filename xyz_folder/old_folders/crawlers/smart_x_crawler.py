#!/usr/bin/env python
# -*- coding: utf-8 -*-



import requests
import time
import csv
import os
import uuid
import argparse
import sys
from datetime import datetime
from smart_facebook_crawler import (
    analyze_sentiment, extract_smart_keywords, generate_search_strategies,
    detect_boolean_query, parse_boolean_or_query, initialize_sentiment_analyzer
)

# Load configuration
def load_config():
    try:
        with open('../config/api_credentials.json', 'r') as f:
            return json.load(f)
    except:
        return {}

config = load_config()
APIFY_TOKEN = config.get('apify', {}).get('token', "apify_api_UiTteCekixYYQbhDrmoNqATMsaKddD08q9J3")
# UPDATED: Use working X/Twitter actors
X_TWEET_SCRAPER_ACTOR = config.get('apify', {}).get('actors', {}).get('x_scraper', "kaitoeasyapi~twitter-x-data-tweet-scraper-pay-per-result-cheapest")
X_REPLIES_SCRAPER_ACTOR = config.get('apify', {}).get('actors', {}).get('x_replies', "kaitoeasyapi~twitter-x-data-tweet-scraper-pay-per-result-cheapest")
PROXY_PASSWORD = config.get('proxy', {}).get('apify_proxy', {}).get('password', "apify_proxy_vZKKP5iUM3VHc7vi_EGwVnbQyvhBm693b5YuR")

def run_apify_actor(actor_id, input_data, max_wait_time=300):
    """Run an Apify actor and wait for results."""
    try:
        headers = {
            "Authorization": f"Bearer {APIFY_TOKEN}",
            "Content-Type": "application/json"
        }

        print(f"🚀 Starting X/Twitter actor...")

        response = requests.post(
            f"https://api.apify.com/v2/acts/{actor_id}/runs",
            headers=headers,
            json=input_data
        )

        if response.status_code != 201:
            print(f"❌ Error starting actor: {response.status_code}")
            return []

        run_data = response.json()
        run_id = run_data["data"]["id"]
        print(f"✅ Actor started successfully!")

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
                    print("✅ Actor completed successfully!")
                    break
                elif status in ["FAILED", "ABORTED", "TIMED-OUT"]:
                    print(f"❌ Actor failed with status: {status}")
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
        print(f"❌ Error running actor: {e}")
        return []

def crawl_x_tweets(query, max_tweets):
    """Crawl X/Twitter tweets for a search query - Step 1: Get tweets and URLs."""
    print(f"🔍 Step 1: Searching for tweets with query: {query}")

    # Use correct input format based on working actor logs
    input_data = {
        "searchTerms": [query],
        "searchMode": "live",
        "maxTweets": max_tweets,
        "maxResults": max_tweets,
        "includeReplies": True,
        "includeRetweets": True,
        "includeUserInfo": True,
        "maxCrawlPages": 30,
        "maxRequestRetries": 8,
        "maxConcurrency": 10,
        "maxItems": max_tweets,
        "queryType": "Latest"
    }

    tweets = run_apify_actor(X_TWEET_SCRAPER_ACTOR, input_data, max_wait_time=600)

    if tweets:
        print(f"✅ Found {len(tweets)} tweets in Step 1")
        # Extract tweet URLs for Step 2
        tweet_urls = []
        for tweet in tweets:
            # Try different possible URL fields
            url = (tweet.get('url') or
                   tweet.get('tweetUrl') or
                   tweet.get('permalink') or
                   tweet.get('link'))

            if url:
                tweet_urls.append(url)
            elif tweet.get('id') or tweet.get('id_str'):
                # Construct URL from tweet ID if available
                tweet_id = tweet.get('id') or tweet.get('id_str')
                username = tweet.get('user', {}).get('screen_name', 'unknown')
                constructed_url = f"https://x.com/{username}/status/{tweet_id}"
                tweet_urls.append(constructed_url)

        print(f"📋 Extracted {len(tweet_urls)} tweet URLs for Step 2")

        # Step 2: Get replies for each tweet
        all_replies = []
        if tweet_urls:
            print(f"🔍 Step 2: Getting replies for {len(tweet_urls)} tweets...")
            all_replies = crawl_x_replies(tweet_urls[:10])  # Limit to first 10 tweets to avoid too many API calls

        # Combine tweets and replies
        combined_data = tweets + all_replies
        print(f"📊 Total data collected: {len(combined_data)} items ({len(tweets)} tweets + {len(all_replies)} replies)")

        return combined_data
    else:
        print("❌ No tweets found in Step 1")
        return []

def crawl_x_replies(tweet_urls):
    """Crawl X/Twitter replies for tweet URLs - Step 2: Get replies/retweets."""
    if not tweet_urls:
        return []

    print(f"🔍 Step 2: Getting replies for {len(tweet_urls)} tweet URLs")

    # Prepare input for replies scraper (based on working configuration)
    input_data = {
        "Post URLs": tweet_urls,
        "Results Limit": 20  # Limit replies per tweet to avoid too much data
    }

    replies = run_apify_actor(X_REPLIES_SCRAPER_ACTOR, input_data, max_wait_time=600)

    if replies:
        print(f"✅ Found {len(replies)} replies in Step 2")
        return replies
    else:
        print("❌ No replies found in Step 2")
        return []

def smart_crawl_x(claim, max_tweets=500, max_replies=1000):
    """Smart X/Twitter crawling with Boolean OR support."""
    print(f"\n🐦 SMART X/TWITTER CRAWLING")
    print("=" * 50)
    print(f"📝 Input: {claim}")
    print(f"📊 Target: {max_tweets} tweets (includes replies)")

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

    # Calculate tweets per strategy for better distribution
    strategies_to_use = min(len(search_strategies), 6)  # Use up to 6 strategies
    tweets_per_strategy = max(20, max_tweets // strategies_to_use)

    print(f"\n🎯 CRAWLING PLAN:")
    print(f"📊 Using {strategies_to_use} strategies")
    print(f"📈 ~{tweets_per_strategy} tweets per strategy")
    print(f"🎯 Target total: {max_tweets:,} tweets")

    all_tweets = []

    # Try each search strategy
    for i, strategy in enumerate(search_strategies[:strategies_to_use], 1):
        print(f"\n🔍 Strategy {i}/{strategies_to_use}: '{strategy}'")

        # Crawl tweets for this strategy
        tweets = crawl_x_tweets(strategy, tweets_per_strategy)

        if tweets:
            print(f"✅ Found {len(tweets)} tweets (using all)")
            all_tweets.extend(tweets)
        else:
            print("❌ No tweets found")

        # Avoid rate limiting between strategies
        time.sleep(5)

        # Progress update
        print(f"📊 Progress: {len(all_tweets)} tweets collected so far")

    # Process and save data
    if all_tweets:
        print(f"\n📋 FINAL RESULTS:")
        print(f"📊 Total tweets: {len(all_tweets)}")

        # Save to CSV
        csv_file = save_x_csv(all_tweets, claim)

        return all_tweets, csv_file
    else:
        print("❌ No X/Twitter data found for this claim")
        return [], None

def save_x_csv(tweets, claim):
    """Save X/Twitter data to CSV in the same format as Facebook."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Create safe filename
    safe_claim = "".join(c for c in claim[:50] if c.isalnum() or c in (' ', '_')).rstrip()
    safe_claim = "_".join(safe_claim.split())

    # Use a single consistent data directory structure
    # First determine the base directory (where smart_crawlers is located)
    if os.path.exists("data"):
        # We're in the smart_crawlers root
        base_dir = "data"
    elif os.path.exists("../data"):
        # We're in a subdirectory (like crawlers)
        base_dir = "../data"
    elif os.path.exists("../../data"):
        # We're in a sub-subdirectory
        base_dir = "../../data"
    else:
        # Create data directory in current location
        base_dir = "data"
        os.makedirs(base_dir, exist_ok=True)
    
    # Create platform-specific directory
    data_dir = f"{base_dir}/x"
    os.makedirs(data_dir, exist_ok=True)
        
    filepath = f"{data_dir}/x_factcheck_{safe_claim}_{timestamp}.csv"

    # Define columns in exact order
    columns = [
        'Platform', 'Type', 'ID', 'Text', 'Sentiment', 'Date',
        'likes', 'shares', 'comments_count', 'views', 'sentiment_score', 'total_engagement',
        'emotion', 'emotion_score'
    ]

    data = []

    # Process tweets and replies
    for item_index, item in enumerate(tweets):
        # Determine if this is a tweet or reply based on data structure
        is_reply_item = 'replyText' in item or 'replyId' in item

        if is_reply_item:
            # This is a reply from the replies scraper
            text = item.get('replyText', '') or ''
            item_id = item.get('replyId', '') or f"x_reply_{item_index + 1}"
            item_type = "X Reply"

            # Extract engagement metrics for replies
            likes = item.get('favouriteCount', 0) or 0
            shares = item.get('repostCount', 0) or 0
            comments_count = item.get('replyCount', 0) or 0
            views = item.get('viewsCount', 0) or 0

            # Format timestamp for replies
            timestamp = item.get('timestamp', 0)
            if timestamp:
                try:
                    dt = datetime.fromtimestamp(timestamp / 1000)  # Convert from milliseconds
                    date_str = dt.strftime("%b %d at %I:%M %p")
                except:
                    date_str = datetime.now().strftime("%b %d at %I:%M %p")
            else:
                date_str = datetime.now().strftime("%b %d at %I:%M %p")
        else:
            # This is a tweet from the main scraper
            text = item.get('text', '') or item.get('full_text', '') or ''
            item_id = item.get('id', '') or item.get('id_str', '') or f"x_tweet_{item_index + 1}"

            # Extract engagement metrics for tweets
            likes = item.get('likes', 0) or item.get('favorite_count', 0) or 0
            shares = item.get('retweets', 0) or item.get('retweet_count', 0) or 0
            comments_count = item.get('replies', 0) or item.get('reply_count', 0) or 0
            views = item.get('views', 0) or 0

            # Determine tweet type
            is_reply = item.get('isReply', False) or item.get('in_reply_to_status_id', None) is not None
            is_retweet = item.get('isRetweet', False) or item.get('retweeted_status', None) is not None

            if is_reply:
                item_type = "X Reply"
            elif is_retweet:
                item_type = "X Retweet"
            else:
                item_type = "X Tweet"

            # Format date for tweets
            date_str = item.get('created_at', '') or datetime.now().strftime("%b %d at %I:%M %p")
            if 'T' in date_str:
                try:
                    dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    date_str = dt.strftime("%b %d at %I:%M %p")
                except:
                    date_str = datetime.now().strftime("%b %d at %I:%M %p")

        # Analyze sentiment
        sentiment, sentiment_score = analyze_sentiment(text)

        # Add emotion analysis
        try:
            from universal_analysis import get_analyzer
            analyzer = get_analyzer()
            emotion_result = analyzer.analyze_text(text)
            emotion = emotion_result.get('emotion', 'neutral')
            emotion_score = emotion_result.get('emotion_score', 0.0)
        except:
            emotion = 'neutral'
            emotion_score = 0.0

        # Calculate total engagement
        total_engagement = likes + shares + comments_count + views

        item_data = {
            'Platform': 'X',
            'Type': item_type,
            'ID': item_id,
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

        data.append(item_data)

    # Write CSV with TAB-separated format
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=columns, delimiter='\t')
        writer.writeheader()
        writer.writerows(data)

    print(f"💾 X/Twitter data saved: {filepath}")
    return filepath

def main():
    """Main X/Twitter crawler function."""
    parser = argparse.ArgumentParser(
        description="Smart X/Twitter Crawler for Fact-Checking",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python smart_x_crawler.py --claim "vaksin covid selamat"
  python smart_x_crawler.py --claim "kerajaan bantuan e-wallet" --output custom_output.csv
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
        default=750,
        help="Maximum number of results to collect (default: 750)"
    )

    # Check if running with arguments or interactively
    if len(sys.argv) == 1:
        # Interactive mode
        print("🐦 SMART X/TWITTER CRAWLER")
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

        print("\n🔧 X/TWITTER CRAWLER CONFIGURATION:")
        print("=" * 50)
        print("📊 Configure exactly how much data you want to collect")
        print("=" * 50)

        # Configure tweets
        while True:
            try:
                max_tweets = int(input("\n🐦 How many TWEETS to collect? (1-8000): "))
                if 1 <= max_tweets <= 8000:
                    break
                print("❌ Please enter a number between 1 and 8000!")
            except ValueError:
                print("❌ Please enter a valid number!")

        # Configure replies per tweet
        while True:
            try:
                replies_per_tweet = int(input("↩️ How many REPLIES per tweet? (1-100): "))
                if 1 <= replies_per_tweet <= 100:
                    break
                print("❌ Please enter a number between 1 and 100!")
            except ValueError:
                print("❌ Please enter a valid number!")

        # Configure retweets per tweet
        while True:
            try:
                retweets_per_tweet = int(input("🔄 How many RETWEETS per tweet? (0-50): "))
                if 0 <= retweets_per_tweet <= 50:
                    break
                print("❌ Please enter a number between 0 and 50!")
            except ValueError:
                print("❌ Please enter a valid number!")

        # Configure search strategies
        while True:
            try:
                num_strategies = int(input("🎯 How many search STRATEGIES to use? (3-8): "))
                if 3 <= num_strategies <= 8:
                    break
                print("❌ Please enter a number between 3 and 8!")
            except ValueError:
                print("❌ Please enter a valid number!")

        # Calculate totals
        total_replies = max_tweets * replies_per_tweet
        total_retweets = max_tweets * retweets_per_tweet
        total_estimated = max_tweets + total_replies + total_retweets

        print(f"\n✅ X/TWITTER CRAWLER CONFIGURATION:")
        print("=" * 50)
        print(f"📝 Claim/Keywords: {claim}")
        print(f"🐦 Tweets to collect: {max_tweets:,}")
        print(f"↩️ Replies per tweet: {replies_per_tweet:,}")
        print(f"🔄 Retweets per tweet: {retweets_per_tweet:,}")
        print(f"🎯 Search strategies: {num_strategies}")
        print(f"📈 Total replies: {total_replies:,}")
        print(f"📈 Total retweets: {total_retweets:,}")
        print(f"🎉 TOTAL ESTIMATED RECORDS: {total_estimated:,}")
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
        max_tweets = args.max_results
        output_file = args.output

        print("🐦 SMART X/TWITTER CRAWLER")
        print("=" * 60)
        print(f"📝 Claim: {claim}")
        print(f"📊 Max Results: {max_tweets:,}")
        if output_file:
            print(f"📁 Output: {output_file}")
        print("=" * 60)

    # Run the crawler
    tweets, csv_file = smart_crawl_x(claim, max_tweets)

    # Handle custom output file
    if output_file and csv_file:
        import shutil
        shutil.move(csv_file, output_file)
        csv_file = output_file

    if csv_file:
        print(f"\n🎉 X/TWITTER CRAWLING COMPLETE!")
        print(f"📁 Data saved to: {csv_file}")
        print(f"📊 Total records: {len(tweets):,}")
    else:
        print("\n❌ No data collected. Try different search terms.")

if __name__ == "__main__":
    main()
