"""Configuration settings for the social media crawler."""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Apify Configuration
APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN", "")
APIFY_PROXY_PASSWORD = os.getenv("APIFY_PROXY_PASSWORD", "")
APIFY_PROXY_URL = os.getenv("APIFY_PROXY_URL", "")

# Database Configuration
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 5432)),
    "database": os.getenv("DB_NAME", "social_media_crawler"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", ""),
}

DATABASE_URL = f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"

# Storage Configuration
CSV_OUTPUT_DIR = Path(os.getenv("CSV_OUTPUT_DIR", "./data/csv"))
JSON_OUTPUT_DIR = Path(os.getenv("JSON_OUTPUT_DIR", "./data/json"))

# Create directories if they don't exist
CSV_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
JSON_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Crawler Configuration
MAX_CONCURRENT_CRAWLERS = int(os.getenv("MAX_CONCURRENT_CRAWLERS", 5))
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", 30))
RETRY_ATTEMPTS = int(os.getenv("RETRY_ATTEMPTS", 3))

# Platform-specific Apify Actor IDs
APIFY_ACTORS = {
    "twitter": "kaitoeasyapi/twitter-x-data-tweet-scraper-pay-per-result-cheapest",  # $0.25/1K tweets - Posts only
    "twitter_comments": "scraper_one/x-post-replies-scraper",  # $0.0025/reply - Comments/replies
    "instagram": "apify/instagram-scraper",
    "linkedin": "harvestapi/linkedin-post-search",  # LinkedIn posts search
    "linkedin_comments": "datadoping/linkedin-profile-comments-scraper",  # $1.20/1K comments
    "facebook": "danek/facebook-search-ppr",  # ✅ Search POSTS by keyword - $2.99/1K results (PPR = Pay Per Result)
    "facebook_comments": "apify/facebook-comments-scraper",  # ✅ Official Apify - $0.004 start + $0.0017/comment
    "reddit": "apify/reddit-scraper",
    "tiktok": "clockworks/tiktok-scraper",  # Updated to best actor
    "tiktok_comments": "clockworks/tiktok-comments-scraper",  # Dedicated comments scraper
    "shopee": "apify/shopee-scraper",
    "lazada": "apify/lazada-scraper",
}

# TikTok-specific configuration
TIKTOK_CONFIG = {
    "default_max_videos": 100,
    "default_comments_per_post": 50,
    "max_comments_per_post": 200,
    "enable_comments": True,
    "enable_engagement": True,
    "enable_user_details": True,
    "download_videos": False,  # Set to True if you want video files
    "download_covers": False,  # Set to True if you want cover images
}

# Logging Configuration
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

