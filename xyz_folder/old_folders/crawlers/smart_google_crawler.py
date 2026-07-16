#!/usr/bin/env python
# -*- coding: utf-8 -*-



import requests
import time
import csv
import os
import argparse
import sys
import json
from datetime import datetime
from smart_facebook_crawler import (
    analyze_sentiment, extract_smart_keywords, generate_search_strategies,
    detect_boolean_query, parse_boolean_or_query
)

# Add utils directory to path for emotion analysis
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'utils'))

try:
    from universal_analysis import get_analyzer, add_analysis_to_data
    EMOTION_ANALYSIS_AVAILABLE = True
    print("✅ Emotion analysis available for Google crawler!")
except ImportError:
    print("⚠️ Emotion analysis not available - continuing with sentiment only")
    EMOTION_ANALYSIS_AVAILABLE = False

def load_google_credentials():
    """Load Google API credentials from config file."""
    try:
        # Try different possible paths for the config file
        config_paths = [
            'config/google_credentials.json',  # From project root
            '../config/google_credentials.json',  # From crawlers directory
            os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'google_credentials.json')  # Absolute path
        ]

        config_file = None
        for path in config_paths:
            if os.path.exists(path):
                config_file = path
                break

        if not config_file:
            raise FileNotFoundError("google_credentials.json not found in any expected location")

        with open(config_file, 'r') as f:
            config = json.load(f)
            serpapi_key = config.get('serpapi_key')
            serper_key = config.get('serper_key')
            print(f"🔑 Loaded SerpAPI key: {serpapi_key[:20]}..." if serpapi_key else "❌ No SerpAPI key found")
            if serper_key:
                print(f"🔑 Loaded Serper key: {serper_key[:20]}...")
            else:
                print("ℹ️ No Serper key configured (using SerpAPI only)")
            return serpapi_key, serper_key
    except Exception as e:
        print(f"❌ Error loading Google credentials: {e}")
        return None, None

# Load API keys from config
SERPAPI_KEY, SERPER_KEY = load_google_credentials()

def search_google_serpapi(query, num_results=100):
    """Search Google using SerpAPI."""
    try:
        url = "https://serpapi.com/search"
        params = {
            "q": query,
            "api_key": SERPAPI_KEY,
            "engine": "google",
            "gl": "my",  # Malaysia
            "hl": "ms",  # Malay language
            "num": min(num_results, 100),  # Max 100 per request
            "start": 0
        }

        print(f"🔍 Searching Google via SerpAPI...")
        response = requests.get(url, params=params)

        if response.status_code == 200:
            data = response.json()
            results = data.get("organic_results", [])
            print(f"✅ Found {len(results)} Google results")
            return results
        else:
            print(f"❌ SerpAPI error: {response.status_code}")
            return []

    except Exception as e:
        print(f"❌ Error with SerpAPI: {e}")
        return []

def search_google_serper(query, num_results=100):
    """Search Google using Serper.dev API."""
    try:
        url = "https://google.serper.dev/search"
        headers = {
            "X-API-KEY": SERPER_KEY,
            "Content-Type": "application/json"
        }

        payload = {
            "q": query,
            "gl": "my",  # Malaysia
            "hl": "ms",  # Malay language
            "num": min(num_results, 100)
        }

        print(f"🔍 Searching Google via Serper...")
        response = requests.post(url, headers=headers, json=payload)

        if response.status_code == 200:
            data = response.json()
            results = data.get("organic", [])
            print(f"✅ Found {len(results)} Google results")
            return results
        else:
            print(f"❌ Serper error: {response.status_code}")
            return []

    except Exception as e:
        print(f"❌ Error with Serper: {e}")
        return []

def smart_crawl_google(claim, max_results=1000):
    """Smart Google crawling with Boolean OR support."""
    print(f"\n🔍 SMART GOOGLE SEARCH CRAWLING")
    print("=" * 50)
    print(f"📝 Input: {claim}")
    print(f"📊 Target: {max_results} search results")

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

    # Calculate results per strategy
    strategies_to_use = min(len(search_strategies), 8)  # Use up to 8 strategies
    results_per_strategy = max(50, max_results // strategies_to_use)

    print(f"\n🎯 CRAWLING PLAN:")
    print(f"📊 Using {strategies_to_use} strategies")
    print(f"📈 ~{results_per_strategy} results per strategy")
    print(f"🎯 Target total: {max_results:,} search results")

    all_results = []

    # Try each search strategy
    for i, strategy in enumerate(search_strategies[:strategies_to_use], 1):
        print(f"\n🔍 Strategy {i}/{strategies_to_use}: '{strategy}'")

        # Try SerpAPI first, fallback to Serper if available
        results = search_google_serpapi(strategy, results_per_strategy)
        if not results and SERPER_KEY:
            print("🔄 Trying Serper as fallback...")
            results = search_google_serper(strategy, results_per_strategy)
        elif not results and not SERPER_KEY:
            print("ℹ️ No Serper key available for fallback")

        if results:
            print(f"✅ Found {len(results)} results")
            all_results.extend(results)
        else:
            print("❌ No results found")

        # Avoid rate limiting between strategies
        time.sleep(2)

        # Progress update
        print(f"📊 Progress: {len(all_results)} results collected so far")

    # Process and save data
    if all_results:
        print(f"\n📋 FINAL RESULTS:")
        print(f"📊 Total results: {len(all_results)}")

        # Save to CSV
        csv_file = save_google_csv(all_results, claim)

        return all_results, csv_file
    else:
        print("❌ No Google search data found for this claim")
        return [], None

def save_google_csv(results, claim):
    """Save Google search data to CSV in the same format as Facebook."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Create safe filename
    safe_claim = "".join(c for c in claim[:50] if c.isalnum() or c in (' ', '_')).rstrip()
    safe_claim = "_".join(safe_claim.split())

    # Determine the correct data directory
    if os.path.exists("../data/google"):
        # Running from crawlers directory
        data_dir = "../data/google"
    elif os.path.exists("data/google"):
        # Running from root directory
        data_dir = "data/google"
    else:
        # Create directory in parent location
        data_dir = "../data/google"
        os.makedirs(data_dir, exist_ok=True)

    filepath = f"{data_dir}/google_factcheck_{safe_claim}_{timestamp}.csv"

    # Define columns in exact order
    columns = [
        'Platform', 'Type', 'ID', 'Text', 'Sentiment', 'Date',
        'likes', 'shares', 'comments_count', 'views', 'sentiment_score', 'total_engagement',
        'emotion', 'emotion_score'
    ]

    data = []

    # Process search results
    for result_index, result in enumerate(results):
        # Combine title and snippet for text analysis
        title = result.get('title', '') or ''
        snippet = result.get('snippet', '') or result.get('description', '') or ''
        text = f"{title}. {snippet}".strip()

        # Analyze sentiment
        sentiment, sentiment_score = analyze_sentiment(text)

        # Analyze emotion
        emotion = 'Neutral'
        emotion_score = 0.0
        if EMOTION_ANALYSIS_AVAILABLE and text.strip():
            try:
                analyzer = get_analyzer()
                emotion_result = analyzer.analyze_text(text)
                emotion = emotion_result['emotion']
                emotion_score = emotion_result['emotion_score']
            except Exception as e:
                print(f"⚠️ Emotion analysis failed for result {result_index + 1}: {e}")
                emotion = 'Neutral'
                emotion_score = 0.0

        # Extract URL and source
        url = result.get('link', '') or result.get('url', '') or ''
        source = result.get('source', '') or ''

        # Format date (Google doesn't provide dates for all results)
        date_str = result.get('date', '') or datetime.now().strftime("%b %d at %I:%M %p")

        # Create result ID
        result_id = f"google_result_{result_index + 1}"

        result_data = {
            'Platform': 'Google',
            'Type': 'Google Search Result',
            'ID': result_id,
            'Text': text,
            'Sentiment': sentiment,
            'Date': date_str,
            'likes': 0,  # Google search results don't have engagement metrics
            'shares': 0,
            'comments_count': 0,
            'views': 0,
            'sentiment_score': f"{sentiment_score:.4f}",
            'total_engagement': 0,
            'emotion': emotion,
            'emotion_score': f"{emotion_score:.4f}"
        }

        data.append(result_data)

    # Write CSV with TAB-separated format
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=columns, delimiter='\t')
        writer.writeheader()
        writer.writerows(data)

    print(f"💾 Google search data saved: {filepath}")
    return filepath

def main():
    """Main Google Search crawler function."""
    parser = argparse.ArgumentParser(
        description="Smart Google Search Crawler for Fact-Checking",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python smart_google_crawler.py --claim "vaksin covid selamat"
  python smart_google_crawler.py --claim "kerajaan bantuan e-wallet" --output custom_output.csv
  python smart_google_crawler.py --claim "Benarkah kerajaan akan memberikan bantuan RM500" --max-results 1000
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
        default=1000,
        help="Maximum number of results to collect (default: 1000)"
    )

    # Check if running with arguments or interactively
    if len(sys.argv) == 1:
        # Interactive mode
        print("🔍 SMART GOOGLE SEARCH CRAWLER")
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

        print("\n🔧 GOOGLE CRAWLER CONFIGURATION:")
        print("=" * 50)
        print("📊 Configure exactly how much data you want to collect")
        print("=" * 50)

        # Configure search results
        while True:
            try:
                max_results = int(input("\n🔍 How many SEARCH RESULTS to collect? (1-10000): "))
                if 1 <= max_results <= 10000:
                    break
                print("❌ Please enter a number between 1 and 10000!")
            except ValueError:
                print("❌ Please enter a valid number!")

        # Configure search strategies
        while True:
            try:
                num_strategies = int(input("🎯 How many search STRATEGIES to use? (3-10): "))
                if 3 <= num_strategies <= 10:
                    break
                print("❌ Please enter a number between 3 and 10!")
            except ValueError:
                print("❌ Please enter a valid number!")

        # Calculate totals
        results_per_strategy = max_results // num_strategies

        print(f"\n✅ GOOGLE CRAWLER CONFIGURATION:")
        print("=" * 50)
        print(f"📝 Claim/Keywords: {claim}")
        print(f"🔍 Search results to collect: {max_results:,}")
        print(f"🎯 Search strategies: {num_strategies}")
        print(f"📈 Results per strategy: {results_per_strategy:,}")
        print(f"🎉 TOTAL ESTIMATED RECORDS: {max_results:,}")
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
        max_results = args.max_results
        output_file = args.output

        print("🔍 SMART GOOGLE SEARCH CRAWLER")
        print("=" * 60)
        print(f"📝 Claim: {claim}")
        print(f"📊 Max Results: {max_results:,}")
        if output_file:
            print(f"📁 Output: {output_file}")
        print("=" * 60)

    # Run the crawler
    results, csv_file = smart_crawl_google(claim, max_results)

    # Handle custom output file
    if output_file and csv_file:
        import shutil
        shutil.move(csv_file, output_file)
        csv_file = output_file

    if csv_file:
        print(f"\n🎉 GOOGLE SEARCH CRAWLING COMPLETE!")
        print(f"📁 Data saved to: {csv_file}")
        print(f"📊 Total records: {len(results):,}")
    else:
        print("\n❌ No data collected. Try different search terms.")

if __name__ == "__main__":
    main()
