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

def load_news_credentials():
    """Load News API credentials from config file."""
    try:
        # Try different possible paths for the config file
        config_paths = [
            'config/news_credentials.json',  # From project root
            '../config/news_credentials.json',  # From crawlers directory
            os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'news_credentials.json')  # Absolute path
        ]

        config_file = None
        for path in config_paths:
            if os.path.exists(path):
                config_file = path
                break

        if not config_file:
            raise FileNotFoundError("news_credentials.json not found in any expected location")

        with open(config_file, 'r') as f:
            config = json.load(f)
            newsapi_key = config.get('newsapi_key')
            serpapi_key = config.get('serpapi_key')
            print(f"🔑 Loaded NewsAPI key: {newsapi_key[:20]}..." if newsapi_key else "❌ No NewsAPI key found")
            print(f"🔑 Loaded SerpAPI key: {serpapi_key[:20]}..." if serpapi_key else "❌ No SerpAPI key found")
            return newsapi_key, serpapi_key
    except Exception as e:
        print(f"❌ Error loading News credentials: {e}")
        return None, None

# Load API keys from config
NEWSAPI_KEY, SERPAPI_KEY = load_news_credentials()

# Malaysian news sources
MALAYSIAN_NEWS_SOURCES = [
    "the-star-malaysia", "new-straits-times", "malaysiakini", "bernama",
    "free-malaysia-today", "malaysia-chronicle", "the-edge-malaysia",
    "astro-awani", "sinar-harian", "utusan-malaysia", "berita-harian",
    "kosmo", "harian-metro", "the-sun-malaysia", "malay-mail"
]

def search_newsapi(query, num_results=100):
    """Search news using NewsAPI."""
    try:
        url = "https://newsapi.org/v2/everything"
        params = {
            "q": query,
            "apiKey": NEWSAPI_KEY,
            "language": "en",  # English for broader coverage
            "sortBy": "relevancy",
            "pageSize": min(num_results, 100),
            "sources": ",".join(MALAYSIAN_NEWS_SOURCES[:5])  # Top 5 sources
        }

        print(f"📰 Searching news via NewsAPI...")
        response = requests.get(url, params=params)

        if response.status_code == 200:
            data = response.json()
            articles = data.get("articles", [])
            print(f"✅ Found {len(articles)} news articles")
            return articles
        else:
            print(f"❌ NewsAPI error: {response.status_code}")
            return []

    except Exception as e:
        print(f"❌ Error with NewsAPI: {e}")
        return []

def search_google_news(query, num_results=100):
    """Search Google News using SerpAPI."""
    try:
        url = "https://serpapi.com/search"
        params = {
            "q": query,
            "api_key": SERPAPI_KEY,
            "engine": "google_news",
            "gl": "my",  # Malaysia
            "hl": "ms",  # Malay language
            "num": min(num_results, 100)
        }

        print(f"📰 Searching Google News via SerpAPI...")
        response = requests.get(url, params=params)

        if response.status_code == 200:
            data = response.json()
            results = data.get("news_results", [])
            print(f"✅ Found {len(results)} Google News results")
            return results
        else:
            print(f"❌ SerpAPI Google News error: {response.status_code}")
            return []

    except Exception as e:
        print(f"❌ Error with Google News: {e}")
        return []

def search_google_general_news(query, num_results=100):
    """Search Google general results for news using SerpAPI."""
    try:
        url = "https://serpapi.com/search"
        params = {
            "q": f"{query} news berita",  # Add news keywords
            "api_key": SERPAPI_KEY,
            "engine": "google",
            "gl": "my",  # Malaysia
            "hl": "ms",  # Malay language
            "num": min(num_results, 100),
            "tbm": "nws"  # News search
        }

        print(f"📰 Searching Google general news via SerpAPI...")
        response = requests.get(url, params=params)

        if response.status_code == 200:
            data = response.json()
            results = data.get("organic_results", []) or data.get("news_results", [])
            print(f"✅ Found {len(results)} Google general news results")
            return results
        else:
            print(f"❌ SerpAPI Google general news error: {response.status_code}")
            return []

    except Exception as e:
        print(f"❌ Error with Google general news: {e}")
        return []

def smart_crawl_news(claim, max_results=1000):
    """Smart News crawling with Boolean OR support."""
    print(f"\n📰 SMART NEWS CRAWLING")
    print("=" * 50)
    print(f"📝 Input: {claim}")
    print(f"📊 Target: {max_results} news articles")

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
    strategies_to_use = min(len(search_strategies), 6)  # Use up to 6 strategies
    results_per_strategy = max(50, max_results // strategies_to_use)

    print(f"\n🎯 CRAWLING PLAN:")
    print(f"📊 Using {strategies_to_use} strategies")
    print(f"📈 ~{results_per_strategy} articles per strategy")
    print(f"🎯 Target total: {max_results:,} news articles")

    all_articles = []

    # Try each search strategy
    for i, strategy in enumerate(search_strategies[:strategies_to_use], 1):
        print(f"\n🔍 Strategy {i}/{strategies_to_use}: '{strategy}'")

        # Try Google News methods
        articles = []

        # Try Google News engine first
        google_news_results = search_google_news(strategy, results_per_strategy // 2)
        if google_news_results:
            articles.extend(google_news_results)

        # Try Google general news search as backup
        google_general_results = search_google_general_news(strategy, results_per_strategy // 2)
        if google_general_results:
            articles.extend(google_general_results)

        if articles:
            print(f"✅ Found {len(articles)} articles total")
            all_articles.extend(articles)
        else:
            print("❌ No articles found")

        # Avoid rate limiting between strategies
        time.sleep(3)

        # Progress update
        print(f"📊 Progress: {len(all_articles)} articles collected so far")

    # Process and save data
    if all_articles:
        print(f"\n📋 FINAL RESULTS:")
        print(f"📊 Total articles: {len(all_articles)}")

        # Save to CSV
        csv_file = save_news_csv(all_articles, claim)

        return all_articles, csv_file
    else:
        print("❌ No news data found for this claim")
        return [], None

def save_news_csv(articles, claim):
    """Save news data to CSV in the same format as Facebook."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Create safe filename
    safe_claim = "".join(c for c in claim[:50] if c.isalnum() or c in (' ', '_')).rstrip()
    safe_claim = "_".join(safe_claim.split())

    # Determine the correct data directory
    if os.path.exists("../data/news"):
        # Running from crawlers directory
        data_dir = "../data/news"
    elif os.path.exists("data/news"):
        # Running from root directory
        data_dir = "data/news"
    else:
        # Create directory in parent location
        data_dir = "../data/news"
        os.makedirs(data_dir, exist_ok=True)

    filepath = f"{data_dir}/news_factcheck_{safe_claim}_{timestamp}.csv"

    # Define columns in exact order
    columns = [
        'Platform', 'Type', 'ID', 'Text', 'Sentiment', 'Date',
        'likes', 'shares', 'comments_count', 'views', 'sentiment_score', 'total_engagement',
        'emotion', 'emotion_score'
    ]

    data = []

    # Process articles
    for article_index, article in enumerate(articles):
        # Combine title and description for text analysis
        title = article.get('title', '') or ''
        description = article.get('description', '') or article.get('snippet', '') or ''
        content = article.get('content', '') or ''

        # Use title + description, or content if available
        if content and len(content) > len(description):
            text = f"{title}. {content}".strip()
        else:
            text = f"{title}. {description}".strip()

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

        # Extract source and URL
        source = article.get('source', {})
        if isinstance(source, dict):
            source_name = source.get('name', 'Unknown')
        else:
            source_name = str(source) if source else 'Unknown'

        url = article.get('url', '') or article.get('link', '') or ''

        # Format date
        date_str = article.get('publishedAt', '') or article.get('date', '') or ''
        if 'T' in date_str:
            try:
                dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                date_str = dt.strftime("%b %d at %I:%M %p")
            except:
                date_str = datetime.now().strftime("%b %d at %I:%M %p")
        elif not date_str:
            date_str = datetime.now().strftime("%b %d at %I:%M %p")

        # Create article ID
        article_id = f"news_article_{article_index + 1}"

        article_data = {
            'Platform': 'News',
            'Type': 'News Article',
            'ID': article_id,
            'Text': text,
            'Sentiment': sentiment,
            'Date': date_str,
            'likes': 0,  # News articles don't have engagement metrics
            'shares': 0,
            'comments_count': 0,
            'views': 0,
            'sentiment_score': f"{sentiment_score:.4f}",
            'total_engagement': 0,
            'emotion': emotion,
            'emotion_score': f"{emotion_score:.4f}"
        }

        data.append(article_data)

    # Write CSV with TAB-separated format
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=columns, delimiter='\t')
        writer.writeheader()
        writer.writerows(data)

    print(f"💾 News data saved: {filepath}")
    return filepath

def main():
    """Main News crawler function."""
    parser = argparse.ArgumentParser(
        description="Smart News Crawler for Fact-Checking",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python smart_news_crawler.py --claim "vaksin covid selamat"
  python smart_news_crawler.py --claim "kerajaan bantuan e-wallet" --output custom_output.csv
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
        default=800,
        help="Maximum number of results to collect (default: 800)"
    )

    # Check if running with arguments or interactively
    if len(sys.argv) == 1:
        # Interactive mode
        print("📰 SMART NEWS CRAWLER")
        print("=" * 60)
        print("🎯 Processes any claim with intelligent keyword extraction")
        print("🇲🇾 Optimized for Malaysian news sources and context")
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

        print("\n� NEWS CRAWLER CONFIGURATION:")
        print("=" * 50)
        print("📊 Configure exactly how much data you want to collect")
        print("=" * 50)

        # Configure articles
        while True:
            try:
                max_results = int(input("\n� How many NEWS ARTICLES to collect? (1-15000): "))
                if 1 <= max_results <= 15000:
                    break
                print("❌ Please enter a number between 1 and 15000!")
            except ValueError:
                print("❌ Please enter a valid number!")

        # Configure sources
        while True:
            try:
                num_sources = int(input("📡 How many NEWS SOURCES to search? (1-20): "))
                if 1 <= num_sources <= 20:
                    break
                print("❌ Please enter a number between 1 and 20!")
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
        articles_per_source = max_results // num_sources
        articles_per_strategy = max_results // num_strategies

        print(f"\n✅ NEWS CRAWLER CONFIGURATION:")
        print("=" * 50)
        print(f"📝 Claim/Keywords: {claim}")
        print(f"📰 Articles to collect: {max_results:,}")
        print(f"📡 News sources: {num_sources}")
        print(f"🎯 Search strategies: {num_strategies}")
        print(f"📈 Articles per source: {articles_per_source:,}")
        print(f"� Articles per strategy: {articles_per_strategy:,}")
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

        print("📰 SMART NEWS CRAWLER")
        print("=" * 60)
        print(f"📝 Claim: {claim}")
        print(f"📊 Max Results: {max_results:,}")
        if output_file:
            print(f"📁 Output: {output_file}")
        print("=" * 60)

    # Run the crawler
    articles, csv_file = smart_crawl_news(claim, max_results)

    # Handle custom output file
    if output_file and csv_file:
        import shutil
        shutil.move(csv_file, output_file)
        csv_file = output_file

    if csv_file:
        print(f"\n🎉 NEWS CRAWLING COMPLETE!")
        print(f"📁 Data saved to: {csv_file}")
        print(f"📊 Total records: {len(articles):,}")
    else:
        print("\n❌ No data collected. Try different search terms.")

if __name__ == "__main__":
    main()
