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
from bs4 import BeautifulSoup
# Removed ApifyClient - using Google search method instead
from smart_facebook_crawler import (
    analyze_sentiment, extract_smart_keywords, generate_search_strategies,
    detect_boolean_query, parse_boolean_or_query
)

# Load Google credentials for SerpAPI
def load_google_credentials():
    """Load Google API credentials from config file."""
    try:
        possible_paths = [
            'config/google_credentials.json',
            '../config/google_credentials.json',
            '../../config/google_credentials.json'
        ]

        config_file = None
        for path in possible_paths:
            if os.path.exists(path):
                config_file = path
                break

        if not config_file:
            print("❌ google_credentials.json not found")
            return None, None

        with open(config_file, 'r') as f:
            config = json.load(f)
            serpapi_key = config.get('serpapi_key')
            serper_key = config.get('serper_key')
            print(f"🔑 Loaded SerpAPI key for Lowyat search")
            return serpapi_key, serper_key
    except Exception as e:
        print(f"❌ Error loading Google credentials: {e}")
        return None, None

# Load API keys
SERPAPI_KEY, SERPER_KEY = load_google_credentials()

# Load Lowyat Actor configuration
def load_lowyat_actor_config():
    """Load Lowyat Python Actor configuration"""
    # Try different possible config paths
    possible_paths = [
        'config/lowyat_actor_config.json',
        '../config/lowyat_actor_config.json',
        '../../config/lowyat_actor_config.json',
        'smart_crawlers/config/lowyat_actor_config.json'
    ]

    for config_path in possible_paths:
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            continue

    print(f"❌ Configuration file not found in any of: {possible_paths}")
    return None

# Lowyat Forum Configuration
LOWYAT_BASE_URL = "https://forum.lowyat.net"
LOWYAT_SEARCH_URL = "https://forum.lowyat.net/search.php"

# ScraperAPI Configuration
SCRAPERAPI_KEY = "6af9ea2a3a21ed741fe7dd8b3421ecf2"
SCRAPERAPI_BASE_URL = "http://api.scraperapi.com"

def search_lowyat_via_serpapi(query, num_results=50):
    """Search for Lowyat forum posts using SerpAPI and extract content from search results."""
    try:
        # Create Lowyat-specific search query
        lowyat_query = f"site:forum.lowyat.net {query}"

        url = "https://serpapi.com/search"
        params = {
            "q": lowyat_query,
            "api_key": SERPAPI_KEY,
            "engine": "google",
            "gl": "my",  # Malaysia
            "hl": "ms",  # Malay language
            "num": min(num_results, 100),
            "start": 0,
            "safe": "off",
            "filter": "0"  # Include all results
        }

        print(f"🔍 Searching Lowyat via SerpAPI: {lowyat_query}")
        response = requests.get(url, params=params)

        if response.status_code == 200:
            data = response.json()
            results = data.get("organic_results", [])

            # Convert search results to forum posts
            lowyat_posts = []
            for i, result in enumerate(results):
                url = result.get("link", "")
                if "forum.lowyat.net" in url:
                    title = result.get("title", "")
                    snippet = result.get("snippet", "")

                    # Create a forum post from search result
                    if snippet and len(snippet) > 20:  # Only meaningful content
                        # Analyze sentiment of the snippet
                        sentiment, sentiment_score = analyze_sentiment(snippet)

                        post = {
                            'platform': 'Lowyat',
                            'type': 'Forum Post',
                            'id': f"lowyat_{i}_{hash(url) % 10000}",
                            'text': snippet,
                            'title': title,
                            'url': url,
                            'sentiment': sentiment,
                            'sentiment_score': sentiment_score,
                            'date': result.get("date", datetime.now().strftime('%Y-%m-%d')),
                            'likes': 0,  # Not available in search results
                            'shares': 0,
                            'comments_count': 0,
                            'views': 0,
                            'total_engagement': 0,
                            'source': 'SerpAPI Search Result'
                        }
                        lowyat_posts.append(post)

            print(f"✅ Extracted {len(lowyat_posts)} Lowyat posts from search results")
            return lowyat_posts
        else:
            print(f"❌ SerpAPI error: {response.status_code}")
            return []

    except Exception as e:
        print(f"❌ Error searching Lowyat via SerpAPI: {e}")
        return []

def crawl_lowyat_post(post_url):
    """Crawl a single Lowyat forum post and extract content."""
    try:
        print(f"🔍 Crawling Lowyat post: {post_url}")

        # Try direct request first with proper headers
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }

        response = requests.get(post_url, headers=headers, timeout=30)

        # If direct request fails, try ScraperAPI
        if response.status_code == 403:
            print("🔄 Direct request blocked, trying ScraperAPI...")
            scraperapi_url = f"{SCRAPERAPI_BASE_URL}?api_key={SCRAPERAPI_KEY}&url={post_url}&render=false&country_code=MY"
            response = requests.get(scraperapi_url, timeout=30)

        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')

            # Extract post title
            title_elem = soup.find('h1') or soup.find('title')
            title = title_elem.get_text().strip() if title_elem else "Unknown Title"

            # Extract posts/comments from the forum thread
            posts = []
            post_elements = soup.find_all(['div', 'td'], class_=lambda x: x and ('post' in x.lower() or 'message' in x.lower()))

            for i, post_elem in enumerate(post_elements[:10]):  # Limit to first 10 posts
                post_text = post_elem.get_text().strip()
                if len(post_text) > 50:  # Only meaningful posts
                    # Analyze sentiment
                    sentiment, sentiment_score = analyze_sentiment(post_text)

                    posts.append({
                        'platform': 'Lowyat',
                        'type': 'Forum Post' if i == 0 else 'Forum Reply',
                        'id': f"{post_url}#{i}",
                        'text': post_text[:1000],  # Limit text length
                        'title': title if i == 0 else "",
                        'url': post_url,
                        'sentiment': sentiment,
                        'sentiment_score': sentiment_score,
                        'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'likes': 0,  # Lowyat doesn't have likes
                        'shares': 0,
                        'comments_count': len(post_elements) - 1 if i == 0 else 0,
                        'views': 0,
                        'total_engagement': 0
                    })

            print(f"✅ Extracted {len(posts)} posts from Lowyat thread")
            return posts

        else:
            print(f"❌ Error accessing Lowyat post: {response.status_code}")
            return []

    except Exception as e:
        print(f"❌ Error crawling Lowyat post: {e}")
        return []

def get_scraperapi_url(target_url, render_js=True, country_code="MY", premium=True, session_number=1, screenshot=False, device_type="desktop"):
    """Generate ScraperAPI URL with official parameters from documentation."""
    params = {
        'api_key': SCRAPERAPI_KEY,
        'url': target_url,
        'country_code': country_code,
        'render': 'true' if render_js else 'false',
        'premium': 'true' if premium else 'false',
        'session_number': str(session_number),
        'device_type': device_type,
        'keep_headers': 'true',
        'follow_redirect': 'true'
    }

    # Add screenshot if requested (automatically enables JS rendering)
    if screenshot:
        params['screenshot'] = 'true'
        params['render'] = 'true'  # Screenshot requires JS rendering

    from urllib.parse import urlencode
    return f"{SCRAPERAPI_BASE_URL}?{urlencode(params)}"

def make_scraperapi_request(target_url, render_js=True, country_code="MY", premium=True, device_type="desktop"):
    """Make ScraperAPI request with official parameters and proper error handling."""
    try:
        scraperapi_url = get_scraperapi_url(
            target_url,
            render_js=render_js,
            country_code=country_code,
            premium=premium,
            device_type=device_type
        )

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }

        print(f"   🛡️ ScraperAPI: {target_url}")
        print(f"   🌍 Country: {country_code}, JS: {render_js}, Premium: {premium}, Device: {device_type}")

        # Use 70 seconds timeout as recommended in documentation
        response = requests.get(scraperapi_url, headers=headers, timeout=70)

        if response.status_code == 200:
            print(f"   ✅ ScraperAPI success: {len(response.content)} bytes")
            return response
        else:
            print(f"   ❌ ScraperAPI failed: {response.status_code}")
            return None

    except Exception as e:
        print(f"   ❌ ScraperAPI error: {e}")
        return None

def search_lowyat_with_python_actor(query, max_results=100):
    """Search Lowyat using Python Apify Actor."""
    try:
        print(f"🐍 Using Python Actor for Lowyat search...")

        # Load configuration
        config = load_lowyat_actor_config()
        if not config:
            print("❌ Failed to load Actor configuration, falling back to direct search")
            return search_lowyat_forum_direct(query, max_results)

        # Initialize Apify client (DISABLED - using Google search method)
        # client = ApifyClient(config['apify_token'])
        print("⚠️ Apify method disabled - using Google search instead")
        return []

        # Prepare Actor input
        run_input = {
            "searchQuery": query,
            "maxResults": max_results,
            "delayBetweenRequests": config.get('delay_between_requests', 3000),
            "proxyConfiguration": config.get('proxy_configuration', {"useApifyProxy": True})
        }

        print(f"🚀 Running Python Actor: {config['actor_id']}")
        print(f"🔍 Query: {query}")
        print(f"📊 Max Results: {max_results}")

        # Run the Python actor
        run = client.actor(config['actor_id']).call(run_input=run_input)

        if run['status'] == 'SUCCEEDED':
            print(f"✅ Actor completed successfully")

            # Get results from dataset
            results = []
            for item in client.dataset(run["defaultDatasetId"]).iterate_items():
                results.append({
                    'title': item.get('thread_title', 'Unknown Thread'),
                    'content': item.get('content', ''),
                    'author': item.get('username', 'Unknown'),
                    'date': item.get('timestamp', ''),
                    'url': item.get('url', ''),
                    'forum': 'Lowyat Forum',
                    'platform': 'lowyat'
                })

            print(f"✅ Collected {len(results)} forum posts from Python Actor")
            return results
        else:
            print(f"❌ Python Actor failed: {run.get('statusMessage')}")
            print("🔄 Falling back to direct search...")
            return search_lowyat_forum_direct(query, max_results)

    except Exception as e:
        print(f"❌ Error with Python Actor: {e}")
        print("🔄 Falling back to direct search...")
        return search_lowyat_forum_direct(query, max_results)

def search_lowyat_forum(query, max_results=100):
    """Main search function that tries Python Actor first, then falls back."""
    # Try Python Actor first
    config = load_lowyat_actor_config()
    if config and config.get('use_python_actor', True):
        return search_lowyat_with_python_actor(query, max_results)
    else:
        return search_lowyat_forum_direct(query, max_results)

def search_lowyat_forum_direct(query, max_results=100):
    """Search Lowyat Forum for posts and comments."""
    try:
        print(f"🔍 Searching Lowyat Forum...")

        # Prepare search parameters
        search_params = {
            'keywords': query,
            'terms': 'all',
            'author': '',
            'fid[]': '',  # All forums
            'sc': '1',  # Search in post content
            'sf': 'all',  # Search all fields
            'sr': 'posts',  # Search posts
            'sk': 't',  # Sort by time
            'sd': 'd',  # Descending order
            'st': '0',  # No time limit
            'ch': '300',  # Characters to show
            'start': '0'
        }

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        session = requests.Session()
        session.headers.update(headers)

        all_posts = []
        page = 0

        while len(all_posts) < max_results and page < 10:  # Max 10 pages
            search_params['start'] = str(page * 25)  # 25 results per page

            response = session.get(LOWYAT_SEARCH_URL, params=search_params, timeout=30)

            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')

                # Find search results
                posts = soup.find_all('div', class_='post')
                if not posts:
                    # Try alternative selectors
                    posts = soup.find_all('tr', class_='row1') + soup.find_all('tr', class_='row2')

                if not posts:
                    print(f"   No more results found on page {page + 1}")
                    break

                for post in posts:
                    if len(all_posts) >= max_results:
                        break

                    # Extract post data
                    post_data = extract_lowyat_post_data(post, session)
                    if post_data:
                        all_posts.append(post_data)

                print(f"   Page {page + 1}: Found {len(posts)} posts")
                page += 1
                time.sleep(2)  # Be respectful to the server

            else:
                print(f"❌ Error accessing Lowyat: {response.status_code}")
                break

        print(f"✅ Found {len(all_posts)} Lowyat posts")
        return all_posts

    except Exception as e:
        print(f"❌ Error searching Lowyat: {e}")
        return []

def extract_lowyat_post_data(post_element, session):
    """Extract data from a Lowyat post element."""
    try:
        post_data = {}

        # Extract title and link
        title_link = post_element.find('a', class_='topictitle') or post_element.find('a')
        if title_link:
            post_data['title'] = title_link.get_text(strip=True)
            post_data['url'] = LOWYAT_BASE_URL + '/' + title_link.get('href', '')
        else:
            return None

        # Extract author
        author_elem = post_element.find('span', class_='name') or post_element.find('b')
        if author_elem:
            post_data['author'] = author_elem.get_text(strip=True)

        # Extract date
        date_elem = post_element.find('span', class_='postdetails') or post_element.find('td', class_='row2')
        if date_elem:
            date_text = date_elem.get_text(strip=True)
            post_data['date'] = date_text

        # Extract post content/snippet
        content_elem = post_element.find('span', class_='postbody') or post_element.find('div', class_='content')
        if content_elem:
            post_data['content'] = content_elem.get_text(strip=True)[:500]  # Limit to 500 chars
        else:
            post_data['content'] = post_data.get('title', '')

        # Extract forum category
        forum_elem = post_element.find('span', class_='gensmall')
        if forum_elem:
            post_data['forum'] = forum_elem.get_text(strip=True)

        return post_data

    except Exception as e:
        print(f"⚠️ Error extracting post data: {e}")
        return None

def smart_crawl_lowyat(claim, max_results=50):
    """Smart Lowyat crawling using Google search + forum scraping."""
    print(f"\n💬 SMART LOWYAT FORUM CRAWLING (Google Search Method)")
    print("=" * 60)
    print(f"📝 Input: {claim}")
    print(f"📊 Target: {max_results} forum posts")
    print(f"🔍 Method: Google search → Lowyat forum scraping")
    print("=" * 60)

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
    print(f"📈 ~{results_per_strategy} posts per strategy")
    print(f"🎯 Target total: {max_results:,} forum posts")

    all_posts = []

    # Try each search strategy
    for i, strategy in enumerate(search_strategies[:strategies_to_use], 1):
        print(f"\n🔍 Strategy {i}/{strategies_to_use}: '{strategy}'")

        # Search Lowyat via SerpAPI (extract content from search results)
        posts = search_lowyat_via_serpapi(strategy, 20)  # Get 20 posts per strategy

        if posts:
            print(f"✅ Found {len(posts)} Lowyat posts")
            all_posts.extend(posts)
            print(f"📊 Progress: {len(all_posts)} posts collected so far")
        else:
            print("❌ No Lowyat posts found")

        # Avoid overwhelming the server
        time.sleep(3)

        # Progress update
        print(f"📊 Progress: {len(all_posts)} posts collected so far")

    # Process and save data
    if all_posts:
        print(f"\n📋 FINAL RESULTS:")
        print(f"📊 Total posts: {len(all_posts)}")

        # Save to CSV
        csv_file = save_lowyat_csv(all_posts, claim)

        return all_posts, csv_file
    else:
        print("❌ No Lowyat forum data found for this claim")
        return [], None

def save_lowyat_csv(posts, claim):
    """Save Lowyat data to CSV in the same format as Facebook."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Create safe filename
    safe_claim = "".join(c for c in claim[:50] if c.isalnum() or c in (' ', '_')).rstrip()
    safe_claim = "_".join(safe_claim.split())

    # Determine the correct data directory
    if os.path.exists("../data/lowyat"):
        # Running from scripts directory
        data_dir = "../data/lowyat"
    elif os.path.exists("smart_crawlers/data/lowyat"):
        # Running from main directory
        data_dir = "smart_crawlers/data/lowyat"
    else:
        # Fallback to original location
        data_dir = "data/lowyat"

    os.makedirs(data_dir, exist_ok=True)
    filepath = f"{data_dir}/lowyat_factcheck_{safe_claim}_{timestamp}.csv"

    # Define columns in exact order
    columns = [
        'Platform', 'Type', 'ID', 'Text', 'Sentiment', 'Date',
        'likes', 'shares', 'comments_count', 'views', 'sentiment_score', 'total_engagement',
        'emotion', 'emotion_score'
    ]

    data = []

    # Process posts
    for post_index, post in enumerate(posts):
        # Combine title and content for text analysis
        title = post.get('title', '') or ''
        content = post.get('content', '') or ''
        text = f"{title}. {content}".strip()

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

        # Extract metadata
        author = post.get('author', 'Unknown')
        forum = post.get('forum', 'General')
        url = post.get('url', '')

        # Format date
        date_str = post.get('date', '') or datetime.now().strftime("%b %d at %I:%M %p")

        # Create post ID
        post_id = f"lowyat_post_{post_index + 1}"

        post_data = {
            'Platform': 'Lowyat',
            'Type': 'Lowyat Post',
            'ID': post_id,
            'Text': text,
            'Sentiment': sentiment,
            'Date': date_str,
            'likes': 0,  # Lowyat doesn't have likes
            'shares': 0,
            'comments_count': 0,  # Would need separate crawling
            'views': 0,
            'sentiment_score': f"{sentiment_score:.4f}",
            'total_engagement': 0,
            'emotion': emotion,
            'emotion_score': f"{emotion_score:.4f}"
        }

        data.append(post_data)

    # Write CSV with TAB-separated format
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=columns, delimiter='\t')
        writer.writeheader()
        writer.writerows(data)

    print(f"💾 Lowyat data saved: {filepath}")
    return filepath

def main():
    """Main Lowyat crawler function."""
    parser = argparse.ArgumentParser(
        description="Smart Lowyat Forum Crawler for Fact-Checking",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python smart_lowyat_crawler.py --claim "vaksin covid selamat"
  python smart_lowyat_crawler.py --claim "kerajaan bantuan e-wallet" --output custom_output.csv
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
        default=600,
        help="Maximum number of results to collect (default: 600)"
    )

    # Check if running with arguments or interactively
    if len(sys.argv) == 1:
        # Interactive mode
        print("💬 SMART LOWYAT FORUM CRAWLER")
        print("=" * 60)
        print("🎯 Processes any claim with intelligent keyword extraction")
        print("🇲🇾 Optimized for Malaysian forum content and context")
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

        print("\n🔧 LOWYAT CRAWLER CONFIGURATION:")
        print("=" * 50)
        print("📊 Configure exactly how much data you want to collect")
        print("=" * 50)

        # Configure threads
        while True:
            try:
                max_threads = int(input("\n🧵 How many THREADS/TOPICS to collect? (1-2000): "))
                if 1 <= max_threads <= 2000:
                    break
                print("❌ Please enter a number between 1 and 2000!")
            except ValueError:
                print("❌ Please enter a valid number!")

        # Configure posts per thread
        while True:
            try:
                posts_per_thread = int(input("📝 How many POSTS per thread? (1-200): "))
                if 1 <= posts_per_thread <= 200:
                    break
                print("❌ Please enter a number between 1 and 200!")
            except ValueError:
                print("❌ Please enter a valid number!")

        # Configure search strategies
        while True:
            try:
                num_strategies = int(input("🎯 How many search STRATEGIES to use? (3-6): "))
                if 3 <= num_strategies <= 6:
                    break
                print("❌ Please enter a number between 3 and 6!")
            except ValueError:
                print("❌ Please enter a valid number!")

        # Calculate totals
        max_results = max_threads * posts_per_thread
        threads_per_strategy = max_threads // num_strategies

        print(f"\n✅ LOWYAT CRAWLER CONFIGURATION:")
        print("=" * 50)
        print(f"📝 Claim/Keywords: {claim}")
        print(f"🧵 Threads to collect: {max_threads:,}")
        print(f"📝 Posts per thread: {posts_per_thread:,}")
        print(f"🎯 Search strategies: {num_strategies}")
        print(f"📈 Threads per strategy: {threads_per_strategy:,}")
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

        print("💬 SMART LOWYAT FORUM CRAWLER")
        print("=" * 60)
        print(f"📝 Claim: {claim}")
        print(f"📊 Max Results: {max_results:,}")
        if output_file:
            print(f"📁 Output: {output_file}")
        print("=" * 60)

    # Run the crawler
    posts, csv_file = smart_crawl_lowyat(claim, max_results)

    # Handle custom output file
    if output_file and csv_file:
        import shutil
        shutil.move(csv_file, output_file)
        csv_file = output_file

    if csv_file:
        print(f"\n🎉 LOWYAT CRAWLING COMPLETE!")
        print(f"📁 Data saved to: {csv_file}")
        print(f"📊 Total records: {len(posts):,}")
    else:
        print("\n❌ No data collected. Try different search terms.")

if __name__ == "__main__":
    main()
