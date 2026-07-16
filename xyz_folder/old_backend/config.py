#!/usr/bin/env python3
"""
🔐 InsightPulse Configuration Manager
====================================
Centralized configuration management using environment variables
Handles all API keys, database connections, and feature flags

Author: InsightPulse Configuration Team
Version: 1.0.0
"""

import os
from typing import Optional, List, Dict
from dotenv import load_dotenv
import logging

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

class Config:
    """Centralized configuration management"""
    
    # =============================================================================
    # 🤖 AI/LLM Configuration
    # =============================================================================
    
    # OpenAI Configuration
    OPENAI_API_KEY: Optional[str] = os.getenv('OPENAI_API_KEY')
    DEFAULT_LLM_MODEL: str = os.getenv('DEFAULT_LLM_MODEL', 'gpt-4o-mini')  # Cost-effective OpenAI model
    FALLBACK_LLM_MODEL: str = os.getenv('FALLBACK_LLM_MODEL', 'claude-sonnet-4-20250514')  # ✅ UPGRADED to Sonnet 4.5

    # Anthropic Claude Configuration (PRIMARY LLM)
    ANTHROPIC_API_KEY: Optional[str] = os.getenv('ANTHROPIC_API_KEY')
    CLAUDE_MODEL: str = os.getenv('CLAUDE_MODEL', 'claude-sonnet-4-20250514')  # ✅ Claude Sonnet 4.5 - Best quality
    
    # Hugging Face Configuration
    HUGGINGFACE_API_TOKEN: Optional[str] = os.getenv('HUGGINGFACE_API_TOKEN')
    SENTIMENT_MODEL: str = os.getenv('SENTIMENT_MODEL', 'rmtariq/ft-Malay-bert')
    EMOTION_MODEL: str = os.getenv('EMOTION_MODEL', 'rmtariq/multilingual-emotion-classifier')
    CLASSIFICATION_MODEL: str = os.getenv('CLASSIFICATION_MODEL', 'rmtariq/malay_claim_classifier_v2')
    
    # Model Parameters
    MAX_TOKENS: int = int(os.getenv('MAX_TOKENS', '4000'))
    TEMPERATURE: float = float(os.getenv('TEMPERATURE', '0.7'))
    TOP_P: float = float(os.getenv('TOP_P', '0.9'))
    
    # =============================================================================
    # 🌐 Social Media APIs
    # =============================================================================
    
    # Facebook/Meta
    FACEBOOK_ACCESS_TOKEN: Optional[str] = os.getenv('FACEBOOK_ACCESS_TOKEN')
    FACEBOOK_APP_ID: Optional[str] = os.getenv('FACEBOOK_APP_ID')
    FACEBOOK_APP_SECRET: Optional[str] = os.getenv('FACEBOOK_APP_SECRET')
    
    # Instagram
    INSTAGRAM_ACCESS_TOKEN: Optional[str] = os.getenv('INSTAGRAM_ACCESS_TOKEN')
    INSTAGRAM_CLIENT_ID: Optional[str] = os.getenv('INSTAGRAM_CLIENT_ID')
    INSTAGRAM_CLIENT_SECRET: Optional[str] = os.getenv('INSTAGRAM_CLIENT_SECRET')
    
    # Twitter/X
    TWITTER_BEARER_TOKEN: Optional[str] = os.getenv('TWITTER_BEARER_TOKEN')
    TWITTER_API_KEY: Optional[str] = os.getenv('TWITTER_API_KEY')
    TWITTER_API_SECRET: Optional[str] = os.getenv('TWITTER_API_SECRET')
    TWITTER_ACCESS_TOKEN: Optional[str] = os.getenv('TWITTER_ACCESS_TOKEN')
    TWITTER_ACCESS_TOKEN_SECRET: Optional[str] = os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
    
    # TikTok
    TIKTOK_CLIENT_KEY: Optional[str] = os.getenv('TIKTOK_CLIENT_KEY')
    TIKTOK_CLIENT_SECRET: Optional[str] = os.getenv('TIKTOK_CLIENT_SECRET')
    TIKTOK_ACCESS_TOKEN: Optional[str] = os.getenv('TIKTOK_ACCESS_TOKEN')
    
    # YouTube
    YOUTUBE_API_KEY: Optional[str] = os.getenv('YOUTUBE_API_KEY')
    
    # LinkedIn
    LINKEDIN_CLIENT_ID: Optional[str] = os.getenv('LINKEDIN_CLIENT_ID')
    LINKEDIN_CLIENT_SECRET: Optional[str] = os.getenv('LINKEDIN_CLIENT_SECRET')
    LINKEDIN_ACCESS_TOKEN: Optional[str] = os.getenv('LINKEDIN_ACCESS_TOKEN')
    
    # Reddit
    REDDIT_CLIENT_ID: Optional[str] = os.getenv('REDDIT_CLIENT_ID')
    REDDIT_CLIENT_SECRET: Optional[str] = os.getenv('REDDIT_CLIENT_SECRET')
    REDDIT_USER_AGENT: str = os.getenv('REDDIT_USER_AGENT', 'InsightPulse/1.0')
    
    # =============================================================================
    # 🛒 E-commerce APIs (Malaysian Focus)
    # =============================================================================
    
    # Shopee
    SHOPEE_PARTNER_ID: Optional[str] = os.getenv('SHOPEE_PARTNER_ID')
    SHOPEE_PARTNER_KEY: Optional[str] = os.getenv('SHOPEE_PARTNER_KEY')
    SHOPEE_ACCESS_TOKEN: Optional[str] = os.getenv('SHOPEE_ACCESS_TOKEN')
    
    # Lazada
    LAZADA_APP_KEY: Optional[str] = os.getenv('LAZADA_APP_KEY')
    LAZADA_APP_SECRET: Optional[str] = os.getenv('LAZADA_APP_SECRET')
    LAZADA_ACCESS_TOKEN: Optional[str] = os.getenv('LAZADA_ACCESS_TOKEN')
    
    # Grab
    GRAB_CLIENT_ID: Optional[str] = os.getenv('GRAB_CLIENT_ID')
    GRAB_CLIENT_SECRET: Optional[str] = os.getenv('GRAB_CLIENT_SECRET')
    GRAB_ACCESS_TOKEN: Optional[str] = os.getenv('GRAB_ACCESS_TOKEN')
    
    # =============================================================================
    # 🗞️ News & Media APIs
    # =============================================================================
    
    NEWS_API_KEY: Optional[str] = os.getenv('NEWS_API_KEY')
    GOOGLE_NEWS_API_KEY: Optional[str] = os.getenv('GOOGLE_NEWS_API_KEY')
    
    # =============================================================================
    # 🔍 Search & Analytics APIs
    # =============================================================================
    
    GOOGLE_SEARCH_API_KEY: Optional[str] = os.getenv('GOOGLE_SEARCH_API_KEY')
    GOOGLE_SEARCH_ENGINE_ID: Optional[str] = os.getenv('GOOGLE_SEARCH_ENGINE_ID')
    BING_SEARCH_API_KEY: Optional[str] = os.getenv('BING_SEARCH_API_KEY')
    
    # =============================================================================
    # 📊 Database Configuration
    # =============================================================================
    
    DATABASE_URL: Optional[str] = os.getenv('DATABASE_URL')
    DB_HOST: str = os.getenv('DB_HOST', 'localhost')
    DB_PORT: int = int(os.getenv('DB_PORT', '5432'))
    DB_NAME: str = os.getenv('DB_NAME', 'insightpulse')
    DB_USER: str = os.getenv('DB_USER', 'username')
    DB_PASSWORD: str = os.getenv('DB_PASSWORD', 'password')
    
    # Redis
    REDIS_URL: Optional[str] = os.getenv('REDIS_URL')
    REDIS_HOST: str = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT: int = int(os.getenv('REDIS_PORT', '6379'))
    REDIS_PASSWORD: Optional[str] = os.getenv('REDIS_PASSWORD')
    
    # Vector Database
    PINECONE_API_KEY: Optional[str] = os.getenv('PINECONE_API_KEY')
    PINECONE_ENVIRONMENT: Optional[str] = os.getenv('PINECONE_ENVIRONMENT')
    
    # =============================================================================
    # 🚀 Server Configuration
    # =============================================================================
    
    ENVIRONMENT: str = os.getenv('ENVIRONMENT', 'development')
    DEBUG: bool = os.getenv('DEBUG', 'true').lower() == 'true'
    HOST: str = os.getenv('HOST', '0.0.0.0')
    PORT: int = int(os.getenv('PORT', '8001'))
    
    # CORS
    CORS_ORIGINS: List[str] = os.getenv('CORS_ORIGINS', 'http://localhost:3000,http://localhost:8000,http://localhost:8001').split(',')
    
    # =============================================================================
    # 🔐 Security Configuration
    # =============================================================================
    
    JWT_SECRET_KEY: str = os.getenv('JWT_SECRET_KEY', 'your-super-secret-jwt-key-here-change-this-in-production')
    RATE_LIMIT_PER_MINUTE: int = int(os.getenv('RATE_LIMIT_PER_MINUTE', '100'))
    
    # =============================================================================
    # 📧 Email & Notifications
    # =============================================================================
    
    SMTP_HOST: Optional[str] = os.getenv('SMTP_HOST')
    SMTP_PORT: int = int(os.getenv('SMTP_PORT', '587'))
    SMTP_USERNAME: Optional[str] = os.getenv('SMTP_USERNAME')
    SMTP_PASSWORD: Optional[str] = os.getenv('SMTP_PASSWORD')
    SMTP_FROM_EMAIL: Optional[str] = os.getenv('SMTP_FROM_EMAIL')
    
    SLACK_WEBHOOK_URL: Optional[str] = os.getenv('SLACK_WEBHOOK_URL')
    
    # =============================================================================
    # 🇲🇾 Malaysian-Specific Configuration
    # =============================================================================
    
    TIMEZONE: str = os.getenv('TIMEZONE', 'Asia/Kuala_Lumpur')
    DEFAULT_LANGUAGE: str = os.getenv('DEFAULT_LANGUAGE', 'bahasa_malaysia')
    DEFAULT_CURRENCY: str = os.getenv('DEFAULT_CURRENCY', 'MYR')
    
    # =============================================================================
    # 📈 Analytics & Monitoring
    # =============================================================================
    
    GOOGLE_ANALYTICS_ID: Optional[str] = os.getenv('GOOGLE_ANALYTICS_ID')
    SENTRY_DSN: Optional[str] = os.getenv('SENTRY_DSN')
    
    # =============================================================================
    # 🔧 Feature Flags
    # =============================================================================
    
    ENABLE_REAL_TIME_CRAWLING: bool = os.getenv('ENABLE_REAL_TIME_CRAWLING', 'true').lower() == 'true'
    ENABLE_AI_ANALYSIS: bool = os.getenv('ENABLE_AI_ANALYSIS', 'true').lower() == 'true'
    ENABLE_SENTIMENT_ANALYSIS: bool = os.getenv('ENABLE_SENTIMENT_ANALYSIS', 'true').lower() == 'true'
    ENABLE_TREND_DETECTION: bool = os.getenv('ENABLE_TREND_DETECTION', 'true').lower() == 'true'
    ENABLE_CRISIS_DETECTION: bool = os.getenv('ENABLE_CRISIS_DETECTION', 'true').lower() == 'true'
    ENABLE_MALAYSIAN_CONTEXT: bool = os.getenv('ENABLE_MALAYSIAN_CONTEXT', 'true').lower() == 'true'
    
    @classmethod
    def validate_required_keys(cls) -> List[str]:
        """Validate that required API keys are present"""
        missing_keys = []
        
        # Check for at least one LLM API key
        if not cls.OPENAI_API_KEY and not cls.ANTHROPIC_API_KEY:
            missing_keys.append("At least one LLM API key (OPENAI_API_KEY or ANTHROPIC_API_KEY)")
        
        # Check for Hugging Face token if using custom models
        if not cls.HUGGINGFACE_API_TOKEN:
            logger.warning("HUGGINGFACE_API_TOKEN not found. Custom models may not work.")
        
        return missing_keys
    
    @classmethod
    def get_available_apis(cls) -> Dict[str, bool]:
        """Get status of available APIs"""
        return {
            "openai": bool(cls.OPENAI_API_KEY),
            "anthropic": bool(cls.ANTHROPIC_API_KEY),
            "huggingface": bool(cls.HUGGINGFACE_API_TOKEN),
            "facebook": bool(cls.FACEBOOK_ACCESS_TOKEN),
            "instagram": bool(cls.INSTAGRAM_ACCESS_TOKEN),
            "twitter": bool(cls.TWITTER_BEARER_TOKEN),
            "tiktok": bool(cls.TIKTOK_CLIENT_KEY),
            "youtube": bool(cls.YOUTUBE_API_KEY),
            "linkedin": bool(cls.LINKEDIN_CLIENT_ID),
            "reddit": bool(cls.REDDIT_CLIENT_ID),
            "shopee": bool(cls.SHOPEE_PARTNER_ID),
            "lazada": bool(cls.LAZADA_APP_KEY),
            "grab": bool(cls.GRAB_CLIENT_ID),
            "news_api": bool(cls.NEWS_API_KEY),
            "google_search": bool(cls.GOOGLE_SEARCH_API_KEY),
            "bing_search": bool(cls.BING_SEARCH_API_KEY),
        }
    
    @classmethod
    def log_configuration_status(cls):
        """Log the current configuration status"""
        missing_keys = cls.validate_required_keys()
        available_apis = cls.get_available_apis()
        
        logger.info("🔐 InsightPulse Configuration Status:")
        logger.info(f"   Environment: {cls.ENVIRONMENT}")
        logger.info(f"   Debug Mode: {cls.DEBUG}")
        logger.info(f"   Server: {cls.HOST}:{cls.PORT}")
        
        if missing_keys:
            logger.warning("❌ Missing Required Configuration:")
            for key in missing_keys:
                logger.warning(f"   - {key}")
        else:
            logger.info("✅ All required configuration present")
        
        logger.info("📊 Available APIs:")
        for api, available in available_apis.items():
            status = "✅" if available else "❌"
            logger.info(f"   {status} {api.upper()}")

# Create global config instance
config = Config()

# Validate configuration on import
if __name__ == "__main__":
    config.log_configuration_status()
