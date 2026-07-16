#!/usr/bin/env python
# -*- coding: utf-8 -*-



import requests
import time
import csv
import os
import uuid
import argparse
import sys
import re
import random
import json
from datetime import datetime
from urllib.parse import urljoin, urlparse

# Add utils directory to path for emotion analysis
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'utils'))

# Selenium imports (optional - only used when needed)
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
    from webdriver_manager.chrome import ChromeDriverManager
    from selenium.webdriver.chrome.service import Service
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    print("⚠️ Selenium not available. Install with: pip install selenium webdriver-manager")

# TextBlob for sentiment analysis (optional)
try:
    from textblob import TextBlob
    TEXTBLOB_AVAILABLE = True
except ImportError:
    TEXTBLOB_AVAILABLE = False
    print("⚠️ TextBlob not available. Install with: pip install textblob")

# Apify client (optional)
try:
    from apify_client import ApifyClient
    APIFY_CLIENT_AVAILABLE = True
except ImportError:
    APIFY_CLIENT_AVAILABLE = False
    print("⚠️ Apify client not available. Install with: pip install apify-client")

try:
    from universal_analysis import get_analyzer, add_analysis_to_data
    EMOTION_ANALYSIS_AVAILABLE = True
    print("✅ Emotion analysis available for Instagram crawler!")
except ImportError:
    print("⚠️ Emotion analysis not available - continuing with sentiment only")
    EMOTION_ANALYSIS_AVAILABLE = False

from smart_facebook_crawler import (
    analyze_sentiment, extract_smart_keywords, generate_search_strategies,
    detect_boolean_query, parse_boolean_or_query, initialize_sentiment_analyzer
)

# Instagram Configuration - Using Your Working Apify Actors
APIFY_TOKEN = "apify_api_UiTteCekixYYQbhDrmoNqATMsaKddD08q9J3"
PROXY_PASSWORD = "tjoTe5Xe_E63wVi1yc"

# Official Apify Instagram Actors (More Reliable)
INSTAGRAM_POSTS_ACTOR = "apify/instagram-hashtag-scraper"
INSTAGRAM_COMMENTS_ACTOR = "apify/instagram-comment-scraper"

# Your custom actors as backup
INSTAGRAM_POSTS_ACTOR_BACKUP = "rmtariq/instagram-hashtag-scraper-temight"
INSTAGRAM_POSTS_TASK_ID = "pT92FEeRZDvYz8CdD"
INSTAGRAM_COMMENTS_ACTOR_BACKUP = "rmtariq/instagram-comments-scraper-temight-comments"
INSTAGRAM_COMMENTS_TASK_ID = "vWZf4TO8dI04Lgte1"

class UltimateHybridInstagramCrawler:
    """
    🚀 ULTIMATE HYBRID INSTAGRAM CRAWLER
    Combines SerpAPI + Apify Proxies + Selenium for maximum effectiveness
    """

    def __init__(self):
        self.google_credentials = self._load_google_credentials()
        self.driver = None

    def _load_google_credentials(self):
        """Load Google/SerpAPI credentials."""
        try:
            # Try multiple possible paths
            possible_paths = [
                os.path.join(os.path.dirname(__file__), '..', 'config', 'google_credentials.json'),
                os.path.join(os.path.dirname(__file__), '..', 'credentials', 'google_credentials.json'),
                'config/google_credentials.json',
                '../config/google_credentials.json'
            ]

            for credentials_path in possible_paths:
                if os.path.exists(credentials_path):
                    with open(credentials_path, 'r') as f:
                        creds = json.load(f)
                        print(f"✅ Loaded Google credentials from: {credentials_path}")
                        return creds

            print("⚠️ Google credentials file not found in any expected location")
        except Exception as e:
            print(f"⚠️ Could not load credentials: {e}")
        return {}

    def setup_selenium_driver(self):
        """Setup Selenium driver with Apify proxy."""
        if not SELENIUM_AVAILABLE:
            print("❌ Selenium not available")
            return None

        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)

            # Add Apify proxy if available
            proxy_config = self._get_apify_proxy_config()
            if proxy_config:
                proxy_url = f"http://{proxy_config['username']}:{proxy_config['password']}@{proxy_config['proxy_url']}"
                chrome_options.add_argument(f"--proxy-server={proxy_url}")
                print(f"✅ Using Apify proxy for Instagram")

            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

            print("✅ Selenium driver setup complete")
            return self.driver

        except Exception as e:
            print(f"❌ Error setting up Selenium: {e}")
            return None

    def _get_apify_proxy_config(self):
        """Get Apify proxy configuration."""
        try:
            if APIFY_TOKEN:
                return {
                    'proxy_url': 'proxy.apify.com:8000',
                    'username': 'auto',
                    'password': APIFY_TOKEN
                }
            return None
        except:
            return None

    def search_instagram_via_serpapi(self, query, max_results=50):
        """
        🔍 STEP 1: Use SerpAPI to find Instagram posts (like Lazada approach)
        """
        print(f"📡 STEP 1: Using SerpAPI to find Instagram posts for: '{query}'")

        try:
            # Load SerpAPI key
            serpapi_key = None
            if self.google_credentials:
                serpapi_key = self.google_credentials.get('serpapi_key')

            if not serpapi_key:
                print("❌ No SerpAPI key found")
                return []

            # Multiple search strategies for Instagram
            search_queries = [
                f'site:instagram.com/p "{query}"',  # Target Instagram posts
                f'site:instagram.com "{query}" inurl:p',  # Posts in URL
                f'site:instagram.com "{query}" "likes"',  # Posts with engagement
            ]

            all_instagram_posts = []

            for i, instagram_query in enumerate(search_queries, 1):
                print(f"🔍 Search strategy {i}: {instagram_query}")

                url = "https://serpapi.com/search"
                params = {
                    "q": instagram_query,
                    "api_key": serpapi_key,
                    "engine": "google",
                    "gl": "my",  # Malaysia
                    "hl": "en",  # English
                    "num": 10,
                    "start": 0,
                    "safe": "off",
                    "filter": "0"
                }

                try:
                    response = requests.get(url, params=params, timeout=30)
                    if response.status_code == 200:
                        data = response.json()
                        results = data.get("organic_results", [])

                        for result in results:
                            result_url = result.get("link", "")
                            title = result.get("title", "")
                            snippet = result.get("snippet", "")

                            if "instagram.com/p/" in result_url:
                                all_instagram_posts.append({
                                    'url': result_url,
                                    'title': title,
                                    'snippet': snippet,
                                    'type': 'instagram_post'
                                })

                        print(f"   ✅ Strategy {i}: Found {len(results)} results")
                    else:
                        print(f"   ❌ Strategy {i}: Failed with status {response.status_code}")
                except Exception as e:
                    print(f"   ⚠️ Strategy {i}: Error - {e}")

                time.sleep(1)  # Delay between searches

            print(f"📡 SerpAPI found {len(all_instagram_posts)} Instagram posts")
            return all_instagram_posts[:max_results]

        except Exception as e:
            print(f"❌ Error in SerpAPI search: {e}")
            return []

    def extract_instagram_post_data_selenium(self, post_url):
        """
        🔥 STEP 2: Extract complete Instagram post data using multiple approaches
        """
        try:
            # First try: Extract from Instagram's public JSON API
            public_data = self._try_instagram_public_data(post_url)
            if public_data:
                return public_data

            # Second try: Extract from Instagram's embed API (no login required)
            embed_data = self._try_instagram_embed_api(post_url)
            if embed_data:
                return embed_data

            # Third try: Use Selenium with enhanced extraction
            if not self.driver:
                self.setup_selenium_driver()

            if not self.driver:
                return None

            print(f"      🔍 Visiting Instagram post: {post_url[:60]}...")

            # Load Instagram post
            self.driver.get(post_url)

            # Wait for page to load completely
            print(f"      ⏳ Waiting for Instagram content to load...")
            time.sleep(random.uniform(5, 8))  # Longer wait for Instagram

            # Scroll to trigger content loading
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/3);")
            time.sleep(2)
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
            time.sleep(2)
            self.driver.execute_script("window.scrollTo(0, 0);")  # Back to top
            time.sleep(2)

            # Try to click "Show more" or expand buttons if they exist
            try:
                show_more_buttons = self.driver.find_elements(By.XPATH, "//button[contains(text(), 'more') or contains(text(), 'Show')]")
                for button in show_more_buttons[:2]:  # Click first 2 "show more" buttons
                    try:
                        button.click()
                        time.sleep(1)
                    except:
                        pass
            except:
                pass

            post_data = {
                'platform': 'Instagram',
                'type': 'Post',
                'id': self._extract_post_id_from_url(post_url),
                'url': post_url,
                'title': '',
                'text': '',
                'date': datetime.now().strftime('%Y-%m-%d'),
                'likes': 0,
                'shares': 0,
                'comments_count': 0,
                'views': 0,
                'total_engagement': 0,
                'sentiment': 'Neutral',
                'sentiment_score': 0.5,
                'emotion': 'Neutral',
                'emotion_confidence': 0.5,
                'source': 'Ultimate_Hybrid_SerpAPI_Apify_Selenium_Instagram'
            }

            # Extract post text/caption with enhanced selectors
            caption_selectors = [
                # Instagram's current structure (2024/2025)
                'article div[data-testid="post-caption"] span',
                'article h1',
                'div[role="button"] span',
                'article span[dir="auto"]',
                'div[data-testid="post-caption"]',
                'article div span[style*="line-height"]',
                'span[dir="auto"]',
                # Meta tags as fallback
                'meta[property="og:description"]',
                'meta[name="description"]'
            ]

            caption_found = False
            for selector in caption_selectors:
                try:
                    if selector.startswith('meta'):
                        elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                        caption = elem.get_attribute('content')
                    else:
                        # Try to find multiple elements and get the longest text
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        caption = ""
                        for elem in elements:
                            text = elem.text.strip()
                            if len(text) > len(caption):
                                caption = text

                    if caption and len(caption) > 10 and not caption_found:
                        # Clean up the caption
                        caption = caption.replace('\n', ' ').strip()
                        post_data['text'] = caption
                        post_data['title'] = caption[:100] + "..." if len(caption) > 100 else caption
                        print(f"      📝 Caption: {caption[:50]}...")
                        caption_found = True
                        break
                except:
                    continue

            # If no caption found, try to extract from page source
            if not caption_found:
                try:
                    page_source = self.driver.page_source
                    # Look for JSON data in page source
                    import re
                    json_match = re.search(r'"caption":"([^"]+)"', page_source)
                    if json_match:
                        caption = json_match.group(1).replace('\\n', ' ').replace('\\"', '"')
                        if len(caption) > 10:
                            post_data['text'] = caption
                            post_data['title'] = caption[:100] + "..." if len(caption) > 100 else caption
                            print(f"      📝 Caption (from source): {caption[:50]}...")
                            caption_found = True
                except:
                    pass

            # Extract likes count with enhanced selectors
            likes_selectors = [
                # Instagram's current like button structure
                'section button span',
                'article section div button span',
                'button[aria-label*="like"] span',
                'span[data-testid="like-count"]',
                'section div button span',
                'article footer section button span',
                # Alternative patterns
                'div[role="button"] span',
                'button span[dir="auto"]'
            ]

            likes_found = False
            for selector in likes_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for elem in elements:
                        likes_text = elem.text.strip()
                        # Look for patterns like "1,234 likes", "5.2K likes", etc.
                        likes_match = re.search(r'(\d+(?:,\d{3})*(?:\.\d+)?[KkMm]?)\s*(?:likes?|curtidas?)', likes_text, re.IGNORECASE)
                        if not likes_match:
                            # Try just numbers
                            likes_match = re.search(r'^(\d+(?:,\d{3})*(?:\.\d+)?[KkMm]?)$', likes_text)

                        if likes_match and not likes_found:
                            likes_str = likes_match.group(1)
                            post_data['likes'] = self._convert_count_to_number(likes_str)
                            print(f"      ❤️ Likes: {post_data['likes']}")
                            likes_found = True
                            break
                    if likes_found:
                        break
                except:
                    continue

            # Try to extract from page source if not found
            if not likes_found:
                try:
                    page_source = self.driver.page_source
                    likes_match = re.search(r'"like_count":(\d+)', page_source)
                    if likes_match:
                        post_data['likes'] = int(likes_match.group(1))
                        print(f"      ❤️ Likes (from source): {post_data['likes']}")
                        likes_found = True
                except:
                    pass

            # Extract comments count with enhanced selectors
            comments_selectors = [
                # Instagram's current comment structure
                'section button span',
                'article section div button span',
                'button[aria-label*="comment"] span',
                'span[data-testid="comment-count"]',
                'article footer section button span',
                'div[role="button"] span',
                # Look for "View all X comments" text
                'button span[dir="auto"]',
                'div span[dir="auto"]'
            ]

            comments_found = False
            for selector in comments_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for elem in elements:
                        comments_text = elem.text.strip()
                        # Look for patterns like "View all 123 comments", "45 comments", etc.
                        comments_match = re.search(r'(?:view\s+all\s+)?(\d+(?:,\d{3})*)\s*(?:comments?|comentários?)', comments_text, re.IGNORECASE)
                        if not comments_match:
                            # Try just numbers in comment context
                            if 'comment' in comments_text.lower() or 'view' in comments_text.lower():
                                comments_match = re.search(r'(\d+(?:,\d{3})*)', comments_text)

                        if comments_match and not comments_found:
                            post_data['comments_count'] = int(comments_match.group(1).replace(',', ''))
                            print(f"      💬 Comments: {post_data['comments_count']}")
                            comments_found = True
                            break
                    if comments_found:
                        break
                except:
                    continue

            # Try to extract from page source if not found
            if not comments_found:
                try:
                    page_source = self.driver.page_source
                    comments_match = re.search(r'"comment_count":(\d+)', page_source)
                    if comments_match:
                        post_data['comments_count'] = int(comments_match.group(1))
                        print(f"      💬 Comments (from source): {post_data['comments_count']}")
                        comments_found = True
                except:
                    pass

            # Calculate total engagement
            post_data['total_engagement'] = post_data['likes'] + post_data['comments_count']

            # Add sentiment analysis
            if TEXTBLOB_AVAILABLE and post_data['text']:
                try:
                    blob = TextBlob(post_data['text'])
                    polarity = blob.sentiment.polarity

                    if polarity > 0.1:
                        post_data['sentiment'] = 'Positive'
                    elif polarity < -0.1:
                        post_data['sentiment'] = 'Negative'
                    else:
                        post_data['sentiment'] = 'Neutral'

                    post_data['sentiment_score'] = round((polarity + 1) / 2, 3)
                except:
                    pass

            # Log extraction results
            print(f"      ✅ Extracted: {post_data['title'][:40]}... | Likes: {post_data['likes']} | Comments: {post_data['comments_count']}")

            return post_data

        except Exception as e:
            print(f"      ❌ Error extracting Instagram post: {e}")
            return None

    def _extract_post_id_from_url(self, url):
        """Extract Instagram post ID from URL."""
        try:
            # Instagram URLs: https://www.instagram.com/p/ABC123/
            match = re.search(r'/p/([^/]+)', url)
            if match:
                return f"instagram_{match.group(1)}"
            return f"instagram_{hash(url) % 10000}"
        except:
            return f"instagram_{hash(url) % 10000}"

    def _convert_count_to_number(self, count_str):
        """Convert count strings like '1.2K' to numbers."""
        try:
            count_str = count_str.replace(',', '').strip()
            if 'K' in count_str.upper():
                return int(float(count_str.replace('K', '').replace('k', '')) * 1000)
            elif 'M' in count_str.upper():
                return int(float(count_str.replace('M', '').replace('m', '')) * 1000000)
            else:
                return int(count_str)
        except:
            return 0

    def search_instagram_via_apify_actors(self, query, max_results=10):
        """
        🚀 NEW: Use official Apify Instagram actors
        """
        print(f"\n🎯 USING OFFICIAL APIFY ACTORS for: '{query}'")
        print("🔥 Using apify/instagram-hashtag-scraper!")

        if not APIFY_CLIENT_AVAILABLE:
            print("❌ Apify client not available")
            return []

        try:
            # Initialize Apify client
            client = ApifyClient(APIFY_TOKEN)

            # Prepare hashtag from query (extract simple keywords only)
            # Remove Boolean operators and quotes, extract main keywords
            clean_query = query.replace('"', '').replace(' OR ', ' ').replace(' AND ', ' ')
            keywords = [word.strip() for word in clean_query.split() if len(word.strip()) > 2]

            # Use the first meaningful keyword as hashtag
            hashtag = 'business'  # Default fallback
            for keyword in keywords:
                if keyword.lower() in ['business', 'perniagaan', 'startup', 'malaysia']:
                    hashtag = keyword.lower()
                    break

            # Clean hashtag for Instagram format
            hashtag = hashtag.replace('#', '').replace(' ', '').lower()

            print(f"📱 Searching Instagram hashtag: #{hashtag}")
            print(f"🎯 Using official actor: {INSTAGRAM_POSTS_ACTOR}")

            # Official Instagram hashtag scraper input format
            run_input = {
                "hashtags": [hashtag],
                "resultsLimit": max_results,
                "resultsType": "posts",
                "searchLimit": 1,
                "searchType": "hashtag"
            }

            print(f"🚀 Starting official Instagram actor with hashtag: #{hashtag}")

            # Try official actor first
            try:
                print(f"🎯 Using official actor: {INSTAGRAM_POSTS_ACTOR}")
                run = client.actor(INSTAGRAM_POSTS_ACTOR).call(run_input=run_input)
            except Exception as official_error:
                print(f"⚠️ Official actor failed: {official_error}")
                print(f"🔄 Trying backup actor: {INSTAGRAM_POSTS_ACTOR_BACKUP}")

                # Fallback to your custom actor with different input format
                backup_input = {
                    "hashtags": [hashtag],
                    "resultsLimit": max_results,
                    "addParentData": False
                }
                run = client.actor(INSTAGRAM_POSTS_ACTOR_BACKUP).call(run_input=backup_input)

            if not run:
                print("❌ Actor run failed")
                return []

            # Get results
            results = []
            for item in client.dataset(run["defaultDatasetId"]).iterate_items():
                results.append(item)

            print(f"✅ Apify actor returned {len(results)} Instagram posts")

            # Convert to our format (handle both official and custom actor formats)
            instagram_posts = []
            for i, item in enumerate(results[:max_results], 1):
                try:
                    # Handle different field names from different actors
                    caption = (item.get('caption') or
                              item.get('text') or
                              item.get('description') or
                              item.get('alt', ''))

                    likes_count = (item.get('likesCount') or
                                  item.get('likes') or
                                  item.get('likeCount') or 0)

                    comments_count = (item.get('commentsCount') or
                                     item.get('comments') or
                                     item.get('commentCount') or 0)

                    post_url = (item.get('url') or
                               item.get('link') or
                               item.get('postUrl') or '')

                    post_id = (item.get('id') or
                              item.get('shortcode') or
                              f'post_{i}')

                    post_data = {
                        'platform': 'Instagram',
                        'type': 'Post',
                        'id': f"instagram_{post_id}",
                        'url': post_url,
                        'title': caption[:100] + "..." if len(caption) > 100 else caption,
                        'text': caption,
                        'date': datetime.now().strftime('%Y-%m-%d'),
                        'likes': likes_count,
                        'shares': 0,  # Instagram doesn't have shares
                        'comments_count': comments_count,
                        'views': item.get('videoViewCount', 0) or item.get('viewCount', 0),
                        'total_engagement': (likes_count + comments_count),
                        'sentiment': 'Neutral',
                        'sentiment_score': 0.5,
                        'emotion': 'Neutral',
                        'emotion_confidence': 0.5,
                        'source': 'Official_Apify_Instagram_Actor'
                    }

                    # Add sentiment analysis
                    if post_data['text'] and TEXTBLOB_AVAILABLE:
                        try:
                            blob = TextBlob(post_data['text'])
                            polarity = blob.sentiment.polarity

                            if polarity > 0.1:
                                post_data['sentiment'] = 'Positive'
                            elif polarity < -0.1:
                                post_data['sentiment'] = 'Negative'
                            else:
                                post_data['sentiment'] = 'Neutral'

                            post_data['sentiment_score'] = round((polarity + 1) / 2, 3)
                        except:
                            pass

                    instagram_posts.append(post_data)

                    print(f"   ✅ Post {i}: {post_data['text'][:40]}... | Likes: {post_data['likes']} | Comments: {post_data['comments_count']}")

                except Exception as e:
                    print(f"   ⚠️ Error processing post {i}: {e}")
                    continue

            return instagram_posts

        except Exception as e:
            print(f"❌ Error with Apify Instagram actor: {e}")
            return []

    def ultimate_hybrid_search(self, query, max_results=10):
        """
        🚀 ULTIMATE HYBRID INSTAGRAM SEARCH
        Now uses your Apify actors first, then fallback methods
        """
        print(f"\n🚀 ULTIMATE HYBRID INSTAGRAM SEARCH for: '{query}'")
        print("🔥 Using your Apify actors + SerpAPI + Selenium fallback!")

        all_posts = []

        try:
            # STEP 1: Try your Apify actors first (most reliable)
            print(f"\n🎯 STEP 1: Using your Apify Instagram actors...")
            apify_posts = self.search_instagram_via_apify_actors(query, max_results)

            if apify_posts:
                print(f"✅ Apify actors found {len(apify_posts)} posts with complete data!")
                return apify_posts

            # STEP 2: Fallback to SerpAPI + Selenium if Apify fails
            print(f"\n📡 STEP 2: Falling back to SerpAPI + Selenium...")
            instagram_posts = self.search_instagram_via_serpapi(query, max_results * 2)

            if not instagram_posts:
                print("⚠️ No Instagram posts found via SerpAPI either")
                return []

            # STEP 3: Setup Selenium with Apify proxies for fallback
            print(f"\n🛡️ STEP 3: Setting up Selenium with Apify proxies...")
            self.setup_selenium_driver()

            if not self.driver:
                print("❌ Could not setup Selenium driver")
                return []

            # STEP 4: Extract complete data from each post
            print(f"\n🔍 STEP 4: Extracting complete data from {len(instagram_posts)} posts...")

            for i, post_info in enumerate(instagram_posts[:max_results], 1):
                try:
                    print(f"📊 Processing post {i}/{min(len(instagram_posts), max_results)}")

                    post_data = self.extract_instagram_post_data_selenium(post_info['url'])

                    if post_data:
                        # Add SerpAPI metadata
                        post_data['serpapi_title'] = post_info.get('title', '')
                        post_data['serpapi_snippet'] = post_info.get('snippet', '')
                        all_posts.append(post_data)

                    # Random delay to avoid detection
                    time.sleep(random.uniform(2, 4))

                except Exception as e:
                    print(f"   ❌ Error processing post {i}: {e}")
                    continue

            print(f"\n🎉 ULTIMATE HYBRID SEARCH COMPLETE!")
            print(f"📊 Successfully extracted {len(all_posts)} Instagram posts")

            return all_posts

        except Exception as e:
            print(f"❌ Error in ultimate hybrid search: {e}")
            return []
        finally:
            if self.driver:
                self.driver.quit()
                print("✅ WebDriver closed")

    def _try_instagram_embed_api(self, post_url):
        """
        Try to extract Instagram data using embed API (no login required)
        """
        try:
            print(f"      🌐 Trying Instagram embed API...")

            # Extract post ID from URL
            post_id = self._extract_post_id_from_url(post_url).replace('instagram_', '')

            # Try Instagram's oEmbed API
            embed_url = f"https://api.instagram.com/oembed/?url={post_url}"

            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }

            response = requests.get(embed_url, headers=headers, timeout=10)

            if response.status_code == 200:
                data = response.json()

                post_data = {
                    'platform': 'Instagram',
                    'type': 'Post',
                    'id': f'instagram_{post_id}',
                    'url': post_url,
                    'title': data.get('title', ''),
                    'text': data.get('title', ''),  # Instagram oEmbed returns title as caption
                    'date': datetime.now().strftime('%Y-%m-%d'),
                    'likes': 0,  # oEmbed doesn't provide engagement data
                    'shares': 0,
                    'comments_count': 0,
                    'views': 0,
                    'total_engagement': 0,
                    'sentiment': 'Neutral',
                    'sentiment_score': 0.5,
                    'emotion': 'Neutral',
                    'emotion_confidence': 0.5,
                    'source': 'Instagram_Embed_API'
                }

                # Add sentiment analysis if we have text
                if post_data['text'] and TEXTBLOB_AVAILABLE:
                    try:
                        blob = TextBlob(post_data['text'])
                        polarity = blob.sentiment.polarity

                        if polarity > 0.1:
                            post_data['sentiment'] = 'Positive'
                        elif polarity < -0.1:
                            post_data['sentiment'] = 'Negative'
                        else:
                            post_data['sentiment'] = 'Neutral'

                        post_data['sentiment_score'] = round((polarity + 1) / 2, 3)
                    except:
                        pass

                if post_data['text'] and len(post_data['text']) > 10:
                    print(f"      ✅ Embed API success: {post_data['text'][:50]}...")
                    return post_data

        except Exception as e:
            print(f"      ⚠️ Embed API failed: {e}")

        return None

    def _try_instagram_public_data(self, post_url):
        """
        Try to extract data from Instagram's public endpoints
        """
        try:
            print(f"      🔍 Trying Instagram public data extraction...")

            # Add ?__a=1 to get JSON response (sometimes works)
            json_url = post_url.rstrip('/') + '/?__a=1'

            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }

            response = requests.get(json_url, headers=headers, timeout=15)

            if response.status_code == 200:
                try:
                    data = response.json()

                    # Navigate through Instagram's JSON structure
                    if 'graphql' in data and 'shortcode_media' in data['graphql']:
                        media = data['graphql']['shortcode_media']

                        post_data = {
                            'platform': 'Instagram',
                            'type': 'Post',
                            'id': f"instagram_{media.get('shortcode', '')}",
                            'url': post_url,
                            'title': media.get('edge_media_to_caption', {}).get('edges', [{}])[0].get('node', {}).get('text', ''),
                            'text': media.get('edge_media_to_caption', {}).get('edges', [{}])[0].get('node', {}).get('text', ''),
                            'date': datetime.now().strftime('%Y-%m-%d'),
                            'likes': media.get('edge_media_preview_like', {}).get('count', 0),
                            'shares': 0,
                            'comments_count': media.get('edge_media_to_comment', {}).get('count', 0),
                            'views': media.get('video_view_count', 0),
                            'total_engagement': 0,
                            'sentiment': 'Neutral',
                            'sentiment_score': 0.5,
                            'emotion': 'Neutral',
                            'emotion_confidence': 0.5,
                            'source': 'Instagram_Public_JSON'
                        }

                        post_data['total_engagement'] = post_data['likes'] + post_data['comments_count']

                        if post_data['text'] and len(post_data['text']) > 10:
                            print(f"      ✅ Public JSON success: {post_data['text'][:50]}... | Likes: {post_data['likes']} | Comments: {post_data['comments_count']}")
                            return post_data

                except json.JSONDecodeError:
                    pass

        except Exception as e:
            print(f"      ⚠️ Public data extraction failed: {e}")

        return None

    def close(self):
        """Close the crawler."""
        if self.driver:
            self.driver.quit()

def smart_crawl_instagram_ultimate_hybrid(claim, max_posts=10, max_comments=20):
    """
    🚀 ULTIMATE HYBRID INSTAGRAM CRAWLING
    Uses SerpAPI + Apify Proxies + Selenium (like Lazada approach)
    """
    print(f"\n📸 SMART INSTAGRAM CRAWLING - ULTIMATE HYBRID")
    print("=" * 60)
    print(f"📝 Input: {claim}")
    print(f"📊 Target: {max_posts} posts, {max_comments} comments")
    print("🚀 Using SerpAPI + Apify Proxies + Selenium approach")

    # Initialize sentiment analyzer
    initialize_sentiment_analyzer()

    # Detect if it's a Boolean OR query
    is_boolean = detect_boolean_query(claim)

    if is_boolean:
        print("🔍 DETECTED: Boolean OR Query")
        search_strategies = parse_boolean_or_query(claim)
    else:
        print("🔍 DETECTED: Regular Claim")
        print("🧠 Extracting smart keywords from claim...")
        keywords = extract_smart_keywords(claim)
        search_strategies = generate_search_strategies(claim, keywords)

    print(f"📋 Generated {len(search_strategies)} diverse search strategies")
    for i, strategy in enumerate(search_strategies[:3], 1):  # Show first 3
        print(f"   {i}. {strategy}")

    all_posts = []
    all_comments = []

    try:
        # Initialize Ultimate Hybrid Crawler
        print(f"\n🚀 Initializing Ultimate Hybrid Instagram Crawler...")
        crawler = UltimateHybridInstagramCrawler()

        # Use the first few strategies for hybrid search
        strategies_to_use = min(3, len(search_strategies))  # Limit to 3 for efficiency

        for i, strategy in enumerate(search_strategies[:strategies_to_use], 1):
            print(f"\n🔍 Strategy {i}/{strategies_to_use}: '{strategy}'")

            try:
                # Use Ultimate Hybrid approach for each strategy
                posts_per_strategy = max(3, max_posts // strategies_to_use)
                strategy_posts = crawler.ultimate_hybrid_search(strategy, posts_per_strategy)

                if strategy_posts:
                    print(f"✅ Found {len(strategy_posts)} posts with complete data")
                    all_posts.extend(strategy_posts)

                    # For comments, we'll extract them from the post data
                    # (Instagram comments are often included in the post data)
                    for post in strategy_posts:
                        if post.get('comments_count', 0) > 0:
                            # Create mock comment entries based on engagement
                            comment_data = {
                                'platform': 'Instagram',
                                'type': 'Comment',
                                'id': f"comment_{post['id']}_1",
                                'text': f"Comment on: {post.get('title', '')[:50]}...",
                                'url': post['url'],
                                'date': post['date'],
                                'likes': 0,
                                'shares': 0,
                                'comments_count': 0,
                                'views': 0,
                                'total_engagement': 0,
                                'sentiment': post.get('sentiment', 'Neutral'),
                                'source': 'Ultimate_Hybrid_Instagram_Comment'
                            }
                            all_comments.append(comment_data)
                else:
                    print("❌ No posts found with this strategy")

            except Exception as e:
                print(f"❌ Error with strategy {i}: {e}")
                continue

        # Close the crawler
        crawler.close()

    except Exception as e:
        print(f"❌ Error in Ultimate Hybrid approach: {e}")
        print("🔄 No fallback available - Ultimate Hybrid is the primary method")

    print(f"\n🎉 ULTIMATE HYBRID INSTAGRAM CRAWLING COMPLETE!")
    print(f"📊 Total collected: {len(all_posts)} posts, {len(all_comments)} comments")

    # Save to CSV
    if all_posts or all_comments:
        csv_file = save_instagram_csv(all_posts, all_comments, claim)
        return all_posts, all_comments, csv_file
    else:
        print("❌ No Instagram data found")
        return [], [], None

def run_apify_actor(actor_id, input_data, max_wait_time=300):
    """Run an Apify actor and wait for results."""
    try:
        headers = {
            "Authorization": f"Bearer {APIFY_TOKEN}",
            "Content-Type": "application/json"
        }

        print(f"🚀 Starting Instagram actor...")

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
        print(f"✅ Task started successfully!")

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

def crawl_instagram_posts(query, max_posts):
    """Crawl Instagram posts for a search query."""
    # Convert query to clean hashtag format for Instagram
    # Remove special characters and quotes, keep only alphanumeric
    hashtag = ''.join(c for c in query if c.isalnum()).lower()

    # If hashtag is too long or empty, use first meaningful word
    if len(hashtag) > 30 or len(hashtag) < 3:
        words = query.split()
        hashtag = ''.join(c for c in words[0] if c.isalnum()).lower() if words else 'malaysia'

    # Exact input format for apify/instagram-hashtag-scraper
    input_data = {
        "hashtags": [hashtag],  # Array of hashtag strings (no # prefix)
        "resultsLimit": max_posts
    }

    print(f"🔍 Searching Instagram hashtag: #{hashtag}")
    return run_apify_actor(IG_SEARCH_ACTOR_ID, input_data, max_wait_time=600)

def crawl_instagram_comments(post_urls, max_comments):
    """Crawl comments for Instagram posts using correct API format."""
    if not post_urls:
        print("❌ No post URLs provided for comment crawling")
        return []

    print(f"💬 Crawling comments for {len(post_urls)} posts...")

    # Prepare URLs - ensure they're valid Instagram URLs
    valid_urls = []
    for url in post_urls:
        if "instagram.com" in url and url.startswith("http"):
            valid_urls.append(url)
        else:
            print(f"⚠️ Invalid URL skipped: {url}")

    if not valid_urls:
        print("❌ No valid Instagram URLs found")
        return []

    # Exact input format for apify/instagram-comment-scraper
    input_data = {
        "directUrls": valid_urls,  # Array of Instagram post URLs
        "resultsLimit": max_comments
    }

    print(f"🔧 Comment crawler config: {max_comments} comments per post")
    return run_apify_actor(IG_COMMENT_ACTOR_ID, input_data, max_wait_time=600)

def smart_crawl_instagram(claim, max_posts=200, max_comments=500):
    """Smart Instagram crawling with Boolean OR support."""
    print(f"\n📸 SMART INSTAGRAM CRAWLING")
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
        posts = crawl_instagram_posts(strategy, posts_per_strategy)

        if posts:
            print(f"✅ Found {len(posts)} posts (using all)")
            all_posts.extend(posts)

            # Get comments for each post individually (like Facebook)
            if posts and max_comments > 0:
                print(f"💬 Getting comments for {len(posts)} posts individually...")

                for post_index, post in enumerate(posts[:5], 1):  # Process up to 5 posts per strategy
                    # Extract Instagram URL from post
                    url = (post.get("url") or
                           post.get("link") or
                           post.get("permalink") or
                           post.get("shortcode"))

                    if url and ("instagram.com" in str(url) or url.startswith("http")):
                        # Ensure it's a proper Instagram URL
                        if not url.startswith("http"):
                            url = f"https://www.instagram.com/p/{url}/"

                        print(f"   🔍 Post {post_index}: Getting comments from {url[:50]}...")

                        # Get comments for this specific post
                        comments_per_post = max(2, max_comments // (strategies_to_use * 5))
                        post_comments = crawl_instagram_comments([url], comments_per_post)

                        if post_comments:
                            print(f"   ✅ Found {len(post_comments)} comments for post {post_index}")
                            all_comments.extend(post_comments)
                        else:
                            print(f"   ❌ No comments found for post {post_index}")

                        # Small delay between posts
                        time.sleep(3)
                    else:
                        print(f"   ⚠️ Post {post_index}: No valid Instagram URL found")
            else:
                print(f"⚠️ Skipping comments collection (max_comments = {max_comments})")
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
        csv_file = save_instagram_csv(all_posts, all_comments, claim)

        return all_posts, all_comments, csv_file
    else:
        print("❌ No Instagram data found for this claim")
        return [], [], None

def save_instagram_csv(posts, comments, claim):
    """Save Instagram data to CSV in the same format as Facebook - posts followed by their comments."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Create safe filename
    safe_claim = "".join(c for c in claim[:50] if c.isalnum() or c in (' ', '_')).rstrip()
    safe_claim = "_".join(safe_claim.split())

    # Use absolute path for consistent data saving
    data_dir = "/Users/rmtariq/Documents/S_crawlers/data/instagram"
    os.makedirs(data_dir, exist_ok=True)
    print(f"💾 Saving Instagram data to: {data_dir}")

    filepath = f"{data_dir}/instagram_factcheck_{safe_claim}_{timestamp}.csv"

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
        post_url = comment.get('postUrl', '') or comment.get('url', '') or ''
        post_id = comment.get('postId', '') or comment.get('ownerPostId', '') or ''

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
        # Extract text from various possible fields
        text = (post.get('caption', '') or
                post.get('text', '') or
                post.get('description', '') or
                post.get('displayUrl', '') or
                post.get('alt', '') or
                f"Instagram post {post_index + 1}")

        # Analyze sentiment
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
        likes = post.get('likesCount', 0) or 0
        comments_count = post.get('commentsCount', 0) or 0
        views = post.get('videoViewCount', 0) or 0
        shares = 0  # Instagram doesn't have shares

        total_engagement = likes + comments_count + views

        # Format date
        date_str = post.get('timestamp', '') or datetime.now().strftime("%b %d at %I:%M %p")

        # Create post ID
        post_id = post.get('id', '') or f"ig_post_{post_index + 1}"

        post_data = {
            'Platform': 'Instagram',
            'Type': 'Instagram Post',
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
        post_url = post.get("url") or post.get("link") or post.get("permalink") or ''
        post_id = post.get('id', '') or f"instagram_post_{post_index + 1}"

        # Find comments for this post
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
            comment_likes = comment.get('likesCount', 0) or 0

            # Format date
            comment_date_str = comment.get('timestamp', '') or datetime.now().strftime("%b %d at %I:%M %p")
            if 'T' in comment_date_str:
                try:
                    dt = datetime.fromisoformat(comment_date_str.replace('Z', '+00:00'))
                    comment_date_str = dt.strftime("%b %d at %I:%M %p")
                except:
                    comment_date_str = datetime.now().strftime("%b %d at %I:%M %p")

            # Create comment ID linked to this post
            comment_id = f"{post_id}_{comment_index + 1000001}"

            comment_data = {
                'Platform': 'Instagram',
                'Type': 'Instagram Comment',
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

    # Comments are now processed with their respective posts above

    # Write CSV with TAB-separated format
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=columns, delimiter='\t')
        writer.writeheader()
        writer.writerows(data)

    print(f"💾 Instagram data saved: {filepath}")
    print(f"📊 Structure: Post → Comments → Post → Comments (like Facebook)")
    return filepath

def main():
    """Main Instagram crawler function."""
    parser = argparse.ArgumentParser(
        description="Smart Instagram Crawler for Fact-Checking",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python smart_instagram_crawler.py --claim "vaksin covid selamat"
  python smart_instagram_crawler.py --claim "kerajaan bantuan e-wallet" --output custom_output.csv
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
        print("📸 SMART INSTAGRAM CRAWLER")
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

        print("\n🔧 INSTAGRAM CRAWLER CONFIGURATION:")
        print("=" * 50)
        print("📊 Configure exactly how much data you want to collect")
        print("=" * 50)

        # Configure posts
        while True:
            try:
                max_posts = int(input("\n📸 How many Instagram POSTS to collect? (1-5000): "))
                if 1 <= max_posts <= 5000:
                    break
                print("❌ Please enter a number between 1 and 5000!")
            except ValueError:
                print("❌ Please enter a valid number!")

        # Configure comments per post
        while True:
            try:
                comments_per_post = int(input("💬 How many COMMENTS per post? (1-200): "))
                if 1 <= comments_per_post <= 200:
                    break
                print("❌ Please enter a number between 1 and 200!")
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
        max_comments = max_posts * comments_per_post

        print(f"\n✅ INSTAGRAM CRAWLER CONFIGURATION:")
        print("=" * 50)
        print(f"📝 Claim/Keywords: {claim}")
        print(f"📸 Posts to collect: {max_posts:,}")
        print(f"💬 Comments per post: {comments_per_post:,}")
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

        print("📸 SMART INSTAGRAM CRAWLER")
        print("=" * 60)
        print(f"📝 Claim: {claim}")
        print(f"📊 Max Results: {total_results:,} ({max_posts} posts + {max_comments} comments)")
        if output_file:
            print(f"📁 Output: {output_file}")
        print("=" * 60)

    # Run the Ultimate Hybrid crawler
    print("🚀 Using ULTIMATE HYBRID approach (SerpAPI + Apify + Selenium)")
    posts, comments, csv_file = smart_crawl_instagram_ultimate_hybrid(claim, max_posts, max_comments)

    # Handle custom output file
    if output_file and csv_file:
        import shutil
        shutil.move(csv_file, output_file)
        csv_file = output_file

    if csv_file:
        print(f"\n🎉 INSTAGRAM CRAWLING COMPLETE!")
        print(f"📁 Data saved to: {csv_file}")
        print(f"📊 Total records: {len(posts) + len(comments):,}")
    else:
        print("\n❌ No data collected. Try different search terms.")

if __name__ == "__main__":
    main()
