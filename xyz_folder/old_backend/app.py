#!/usr/bin/env python3
"""
🚀 InsightPulse Web Backend - FastAPI Application
=================================================
Production-ready backend for 10-platform digital intelligence system.
Supports HTML/CSS/JavaScript frontend with RESTful APIs and WebSocket.

🎯 FEATURES:
- 10-Platform data collection (social, news, e-commerce)
- Google News RSS crawler (free, Boolean-search support)
- Real-time sentiment & emotion analysis (rmtariq/ft-Malay-bert + multilingual-emotion-classifier)
- WebSocket live status updates
- No external database dependencies — CSV-based data store
- Malay + English multilingual analysis

Start: uvicorn web_backend.app:app --host 0.0.0.0 --port 8001

Author: InsightPulse Team
Version: 2.0.0
"""

from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional, Set
import asyncio
import logging
import re
import json
import time
from datetime import datetime
from pathlib import Path
import pandas as pd
import numpy as np
import math
import os
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import torch
import os

# LLM Integration
import openai
from openai import OpenAI
import anthropic
import requests

# Configure logging first
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import Simple Apify Adapter
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "backend" / "data_crawlers"))
try:
    from simple_apify_adapter import SimpleApifyAdapter
    APIFY_AVAILABLE = True
    logger.info("✅ Simple Apify Adapter loaded successfully")
except Exception as e:
    APIFY_AVAILABLE = False
    logger.warning(f"⚠️ Simple Apify Adapter not available: {e}")

# Import configuration and services
try:
    from config import config
    from llm_service import llm_service
    LLM_SERVICE_AVAILABLE = True
    logger.info("✅ LLM Service loaded successfully")
except ImportError as e:
    LLM_SERVICE_AVAILABLE = False
    logger.warning(f"❌ LLM Service not available: {e}")
    config = None
    llm_service = None

# Import advanced NLP processor
try:
    from advanced_nlp_processor import process_user_input
    ADVANCED_NLP_AVAILABLE = True
    logger.info("✅ Advanced NLP Processor loaded successfully")
except ImportError as e:
    ADVANCED_NLP_AVAILABLE = False
    logger.warning(f"❌ Advanced NLP Processor not available: {e}")

    # Fallback function
    def process_user_input(user_input: str) -> Dict[str, Any]:
        return {
            'original_input': user_input,
            'keywords': {'combined': [(user_input, 1.0)]},
            'named_entities': {},
            'query_expansion': {'suggested_platforms': ['facebook', 'instagram']},
            'confidence_score': 0.5,
            'processing_notes': ['Using fallback processing - install advanced NLP dependencies']
        }

# Import Batch Sentiment Processor
sys.path.insert(0, str(Path(__file__).parent.parent / "backend" / "services"))
try:
    from batch_sentiment_processor import BatchSentimentProcessor
    BATCH_PROCESSOR_AVAILABLE = True
    logger.info("✅ Batch Sentiment Processor loaded successfully")
except ImportError as e:
    BATCH_PROCESSOR_AVAILABLE = False
    logger.warning(f"❌ Batch Sentiment Processor not available: {e}")

# Logging already configured above

# Create FastAPI app
app = FastAPI(
    title="InsightPulse - Simple Backend",
    description="Real social media and e-commerce analytics with your data",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== WEBSOCKET CONNECTION MANAGER =====
class ConnectionManager:
    """Manages WebSocket connections for real-time status updates"""

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"✅ WebSocket connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
        logger.info(f"❌ WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def broadcast_status(self, message: dict):
        """Broadcast status update to all connected clients"""
        disconnected = set()
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to client: {e}")
                disconnected.add(connection)

        # Remove disconnected clients
        for conn in disconnected:
            self.active_connections.discard(conn)

# Global connection manager
manager = ConnectionManager()

# Mount static files
static_path = Path(__file__).parent.parent / "web_frontend"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# Mount reports directory
reports_path = Path(__file__).parent.parent / "reports"
if reports_path.exists():
    app.mount("/reports", StaticFiles(directory=str(reports_path)), name="reports")
else:
    # Create reports directory if it doesn't exist
    reports_path.mkdir(parents=True, exist_ok=True)
    app.mount("/reports", StaticFiles(directory=str(reports_path)), name="reports")

# Data directory
DATA_DIR = Path(__file__).parent.parent / "data" / "smart_crawlers"

# ===== HUGGING FACE CONFIGURATION =====
# Token resolution order: HUGGINGFACE_API_TOKEN (canonical, set in .env) →
# HF_TOKEN / HUGGINGFACE_HUB_TOKEN (fallbacks for HF SDK conventions).
HF_TOKEN = (
    os.getenv("HUGGINGFACE_API_TOKEN")
    or os.getenv("HF_TOKEN")
    or os.getenv("HUGGINGFACE_HUB_TOKEN")
    or ""
)

# 🌍 MULTILINGUAL SENTIMENT MODELS
SENTIMENT_MODELS = {
    'malay': 'rmtariq/ft-Malay-bert',                              # Your fine-tuned Malay model (85% accuracy)
    'english': 'cardiffnlp/twitter-roberta-base-sentiment-latest', # Twitter-optimized English
    'chinese': 'uer/roberta-base-finetuned-chinanews-chinese',     # Chinese news sentiment
    'multilingual': 'nlptown/bert-base-multilingual-uncased-sentiment', # Fallback for mixed/other languages
}

EMOTION_MODEL = "rmtariq/multilingual-emotion-classifier"

# Language to Demographic Mapping (for Malaysian context)
LANGUAGE_TO_DEMOGRAPHIC = {
    'ms': 'Malay/Bumiputera',      # Malay
    'id': 'Malay/Bumiputera',      # Indonesian (similar to Malay)
    'en': 'Mixed/Urban',           # English (urban, educated, mixed race)
    'zh-cn': 'Chinese',            # Chinese Simplified
    'zh-tw': 'Chinese',            # Chinese Traditional
    'ta': 'Indian',                # Tamil
    'hi': 'Indian',                # Hindi
    'ar': 'Malay/Muslim',          # Arabic (Malay Muslims)
    'unknown': 'Unknown',          # Fallback
}

# Set Hugging Face token
os.environ["HUGGINGFACE_HUB_TOKEN"] = HF_TOKEN

# Global model variables (will be initialized on startup)
sentiment_pipelines = {}  # Dictionary to hold multiple sentiment models
emotion_pipeline = None
batch_processor = None

# ===== STARTUP EVENT =====
@app.on_event("startup")
async def startup_event():
    """Initialize models when the app starts"""
    await initialize_models()

# ===== PYDANTIC MODELS =====
class PlatformConfig(BaseModel):
    """Configuration for individual platform crawling"""
    platform: str
    max_posts: int = 50  # Number of posts to collect
    max_comments: int = 50  # Number of comments per post
    enabled: bool = True

class AnalysisRequest(BaseModel):
    query: str
    platforms: List[str]
    analysis_type: str = "social_listening"
    max_results: int = 5000  # Default to enterprise-level analysis (DEPRECATED - use platform_configs or dataset_size)
    include_sentiment: bool = True
    include_trends: bool = True
    malaysian_context: bool = True

    # ✅ Platform-specific configuration
    platform_configs: Optional[Dict[str, Dict[str, int]]] = None
    # Format: {"facebook": {"max_posts": 100, "max_comments": 50}, "instagram": {...}}

    # ✅ Analysis depth preset (optimized per platform)
    analysis_depth: str = "standard"  # quick, standard, deep, custom

    # ✅ NEW: Date range filtering
    date_range: str = "7days"  # 24h, 7days, 30days, 90days, custom
    custom_start_date: Optional[str] = None  # ISO format: "2024-01-01"
    custom_end_date: Optional[str] = None    # ISO format: "2024-01-31"

    # ✅ NEW: Analysis focus for intelligent prioritization
    analysis_focus: str = "comprehensive"  # engagement, sentiment, trends, comprehensive

    # ✅ NEW: Comment sampling strategy
    comment_sampling: str = "smart"  # smart (top+recent), top_only, recent_only, random

    # 🎯 NEW: Dataset size for 30:70 Posts:Comments strategy
    dataset_size: Optional[int] = None  # Total results (posts + comments). Options: 50, 1000, 5000, 10000, 25000, 50000, 100000
    use_crawl_strategy: bool = True  # Enable 30:70 Posts:Comments ratio strategy

class PlatformData(BaseModel):
    platform: str
    data_points: int
    sentiment_score: float
    total_engagement: int
    trending_topics: List[str]
    status: str

# ===== MODEL INITIALIZATION =====
async def initialize_models():
    """Initialize Hugging Face models on startup - MULTILINGUAL SUPPORT"""
    global sentiment_pipelines, emotion_pipeline, batch_processor

    try:
        logger.info("🤖 Initializing multilingual sentiment models...")

        # 🌍 Initialize MULTIPLE sentiment models for different languages
        for lang, model_name in SENTIMENT_MODELS.items():
            try:
                logger.info(f"📊 Loading {lang} sentiment model: {model_name}")

                # Special handling for different models
                if lang == 'multilingual':
                    # nlptown model returns 1-5 stars, need different handling
                    sentiment_pipelines[lang] = pipeline(
                        "text-classification",
                        model=model_name,
                        top_k=None
                    )
                else:
                    sentiment_pipelines[lang] = pipeline(
                        "text-classification",
                        model=model_name,
                        token=HF_TOKEN if lang == 'malay' else None,  # Only Malay model needs token
                        top_k=None  # Return all scores
                    )
                logger.info(f"✅ {lang.capitalize()} sentiment model loaded!")
            except Exception as e:
                logger.warning(f"⚠️ Failed to load {lang} model: {e}")
                # Continue loading other models even if one fails

        # Ensure at least Malay model is loaded
        if 'malay' not in sentiment_pipelines:
            raise Exception("Critical: Malay sentiment model failed to load!")

        logger.info(f"✅ Loaded {len(sentiment_pipelines)} sentiment models: {list(sentiment_pipelines.keys())}")

        # Initialize emotion model (rmtariq/multilingual-emotion-classifier)
        logger.info(f"😊 Loading emotion model: {EMOTION_MODEL}")
        emotion_pipeline = pipeline(
            "text-classification",
            model=EMOTION_MODEL,
            tokenizer=EMOTION_MODEL,
            token=HF_TOKEN,
            top_k=None  # Return all scores
        )
        logger.info("✅ Emotion model loaded successfully!")

        # Initialize Batch Sentiment Processor (using Malay model as primary)
        if BATCH_PROCESSOR_AVAILABLE:
            logger.info("🔧 Initializing Batch Sentiment Processor...")
            batch_processor = BatchSentimentProcessor(
                sentiment_analyzer=sentiment_pipelines.get('malay'),
                emotion_analyzer=emotion_pipeline
            )
            logger.info("✅ Batch Sentiment Processor initialized!")

        logger.info("🎉 All multilingual models initialized successfully!")

    except Exception as e:
        logger.error(f"❌ Error initializing models: {e}")
        # Fallback to basic sentiment analysis if models fail
        logger.warning("⚠️ Falling back to basic sentiment analysis")

def detect_language(text: str) -> str:
    """
    Detect language of text and return appropriate model key

    Returns: 'malay', 'english', 'chinese', or 'multilingual'
    """
    try:
        # Try to import langdetect (install with: pip install langdetect)
        try:
            import langdetect
            detected_lang = langdetect.detect(text)
        except ImportError:
            # Fallback: Simple heuristic-based detection
            logger.warning("⚠️ langdetect not installed. Using simple heuristic detection.")

            # Check for Chinese characters
            if any('\u4e00' <= char <= '\u9fff' for char in text):
                return 'chinese'

            # Check for common Malay words
            malay_words = ['yang', 'dan', 'ini', 'itu', 'untuk', 'dengan', 'adalah', 'pada', 'saya', 'tidak', 'akan', 'ada']
            text_lower = text.lower()
            malay_count = sum(1 for word in malay_words if word in text_lower)

            if malay_count >= 2:
                return 'malay'

            # Default to English for other cases
            return 'english'

        # Map detected language to model
        if detected_lang in ['ms', 'id']:  # Malay/Indonesian
            return 'malay'
        elif detected_lang == 'en':
            return 'english'
        elif detected_lang in ['zh-cn', 'zh-tw', 'zh']:
            return 'chinese'
        elif detected_lang in ['ta', 'hi', 'ar']:  # Tamil/Hindi/Arabic - use multilingual
            return 'multilingual'
        else:
            # Default to multilingual for unknown languages
            return 'multilingual'

    except Exception as e:
        logger.warning(f"⚠️ Language detection failed: {e}. Defaulting to Malay.")
        return 'malay'  # Default to Malay for Malaysia

def get_demographic_from_language(lang_code: str) -> str:
    """Map detected language to demographic group"""
    return LANGUAGE_TO_DEMOGRAPHIC.get(lang_code, 'Unknown')

def analyze_sentiment_with_custom_model(text: str) -> Dict[str, Any]:
    """
    🌍 MULTILINGUAL Sentiment Analysis

    Detects language and routes to appropriate sentiment model:
    - Malay: rmtariq/ft-Malay-bert (your fine-tuned model)
    - English: cardiffnlp/twitter-roberta-base-sentiment-latest
    - Chinese: uer/roberta-base-finetuned-chinanews-chinese
    - Others: nlptown/bert-base-multilingual-uncased-sentiment
    """

    if not sentiment_pipelines:
        # Fallback to basic sentiment
        return {
            "sentiment": "neutral",
            "confidence": 0.5,
            "scores": {"positive": 0.33, "neutral": 0.34, "negative": 0.33},
            "model": "fallback",
            "detected_language": "unknown",
            "demographic": "Unknown"
        }

    try:
        # 🌍 STEP 1: Detect language
        detected_model_key = detect_language(text)
        logger.debug(f"🌍 Detected language model: {detected_model_key}")

        # Get appropriate sentiment pipeline
        sentiment_pipeline = sentiment_pipelines.get(detected_model_key)

        if not sentiment_pipeline:
            # Fallback to Malay model if detected language model not available
            logger.warning(f"⚠️ {detected_model_key} model not available, using Malay model")
            sentiment_pipeline = sentiment_pipelines.get('malay')
            detected_model_key = 'malay'

        # Map model key to language code for demographic
        model_to_lang = {
            'malay': 'ms',
            'english': 'en',
            'chinese': 'zh-cn',
            'multilingual': 'unknown'
        }
        lang_code = model_to_lang.get(detected_model_key, 'unknown')
        demographic = get_demographic_from_language(lang_code)

        # Truncate text to avoid token length issues (max ~400 chars to stay under 512 tokens)
        truncated_text = text[:400] if len(text) > 400 else text

        # 🤖 STEP 2: Get predictions from appropriate model
        results = sentiment_pipeline(truncated_text)

        # 📊 STEP 3: Process results with label mapping
        if isinstance(results, list) and len(results) > 0:
            if isinstance(results[0], list):
                # Multiple results format
                results = results[0]

            scores = {}

            # Different label mappings for different models
            if detected_model_key == 'multilingual':
                # nlptown model returns 1-5 stars
                star_mapping = {
                    '1 star': 'negative',
                    '2 stars': 'negative',
                    '3 stars': 'neutral',
                    '4 stars': 'positive',
                    '5 stars': 'positive'
                }
                for result in results:
                    raw_label = result['label']
                    mapped_label = star_mapping.get(raw_label, 'neutral')
                    score = result['score']
                    if mapped_label in scores:
                        scores[mapped_label] += score
                    else:
                        scores[mapped_label] = score
            else:
                # Standard label mapping for Malay, English, Chinese models
                label_mapping = {
                    'label_0': 'negative',
                    'label_1': 'neutral',
                    'label_2': 'positive',
                    'negative': 'negative',
                    'neutral': 'neutral',
                    'positive': 'positive',
                    'label_negative': 'negative',
                    'label_neutral': 'neutral',
                    'label_positive': 'positive',
                }

                for result in results:
                    raw_label = result['label'].lower()
                    mapped_label = label_mapping.get(raw_label, raw_label)
                    score = result['score']
                    scores[mapped_label] = score

            # Determine primary sentiment
            primary_sentiment = max(scores.keys(), key=lambda k: scores[k])
            confidence = scores[primary_sentiment]

            return {
                "sentiment": primary_sentiment,
                "confidence": confidence,
                "scores": scores,
                "model": SENTIMENT_MODELS[detected_model_key],
                "detected_language": detected_model_key,
                "demographic": demographic
            }
        else:
            raise ValueError("Unexpected model output format")

    except Exception as e:
        logger.error(f"Error in sentiment analysis: {e}")
        return {
            "sentiment": "neutral",
            "confidence": 0.5,
            "scores": {"positive": 0.33, "neutral": 0.34, "negative": 0.33},
            "model": "error_fallback",
            "detected_language": "unknown",
            "demographic": "Unknown"
        }

def analyze_emotion_with_custom_model(text: str) -> Dict[str, Any]:
    """Analyze emotions using custom rmtariq/multilingual-emotion-classifier-demo model"""

    if not emotion_pipeline:
        # Fallback emotions
        return {
            "primary_emotion": "neutral",
            "confidence": 0.5,
            "emotions": {"joy": 0.2, "sadness": 0.2, "anger": 0.2, "fear": 0.2, "neutral": 0.2},
            "model": "fallback"
        }

    try:
        # Truncate text to avoid token length issues (max ~400 chars to stay under 512 tokens)
        truncated_text = text[:400] if len(text) > 400 else text

        # Get predictions from custom emotion model
        results = emotion_pipeline(truncated_text)

        # Handle different output formats
        if isinstance(results, list) and len(results) > 0:
            if isinstance(results[0], list):
                # Multiple results format
                results = results[0]

            # Process results
            emotions = {}
            for result in results:
                label = result['label'].lower()
                score = result['score']
                emotions[label] = score

            # Determine primary emotion
            primary_emotion = max(emotions.keys(), key=lambda k: emotions[k])
            confidence = emotions[primary_emotion]

            return {
                "primary_emotion": primary_emotion,
                "confidence": confidence,
                "emotions": emotions,
                "model": "rmtariq/multilingual-emotion-classifier"
            }
        else:
            raise ValueError("Unexpected model output format")

    except Exception as e:
        logger.error(f"Error in emotion analysis: {e}")
        return {
            "primary_emotion": "neutral",
            "confidence": 0.5,
            "emotions": {"joy": 0.2, "sadness": 0.2, "anger": 0.2, "fear": 0.2, "neutral": 0.2},
            "model": "error_fallback"
        }

# ===== HELPER FUNCTIONS =====
def clean_nan_values(obj):
    """Recursively clean NaN values from nested dictionaries and lists for JSON serialization"""
    if isinstance(obj, dict):
        return {key: clean_nan_values(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [clean_nan_values(item) for item in obj]
    elif isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return 0.0  # Replace NaN/inf with 0
        return obj
    elif pd.isna(obj):
        return None  # Replace pandas NaN with None
    else:
        return obj

def get_statistical_confidence(data_points: int) -> str:
    """Determine statistical confidence level based on data volume"""
    if data_points >= 50000:
        return "very_high"
    elif data_points >= 10000:
        return "high"
    elif data_points >= 5000:
        return "good"
    elif data_points >= 1000:
        return "moderate"
    elif data_points >= 500:
        return "low"
    else:
        return "very_low"

def get_reliability_score(data_points: int) -> Dict[str, Any]:
    """Calculate reliability metrics for insights"""
    if data_points >= 50000:
        return {
            "score": 0.95,
            "level": "Enterprise Grade",
            "description": "Highly reliable insights suitable for strategic business decisions",
            "margin_of_error": "±1-2%",
            "statistical_power": "Very High"
        }
    elif data_points >= 10000:
        return {
            "score": 0.85,
            "level": "Research Grade",
            "description": "Reliable insights suitable for market research and analysis",
            "margin_of_error": "±3-5%",
            "statistical_power": "High"
        }
    elif data_points >= 5000:
        return {
            "score": 0.75,
            "level": "Business Grade",
            "description": "Good insights for business monitoring and trend analysis",
            "margin_of_error": "±5-8%",
            "statistical_power": "Good"
        }
    elif data_points >= 1000:
        return {
            "score": 0.65,
            "level": "Standard",
            "description": "Moderate confidence for general insights and monitoring",
            "margin_of_error": "±8-12%",
            "statistical_power": "Moderate"
        }
    else:
        return {
            "score": 0.45,
            "level": "Limited",
            "description": "Limited confidence - use for preliminary analysis only",
            "margin_of_error": "±15-25%",
            "statistical_power": "Low"
        }

def detect_language(text: str) -> str:
    """Detect if text is primarily Malay or English - supports bilingual analysis"""

    # Common Malay words and patterns
    malay_indicators = [
        'yang', 'dan', 'untuk', 'dengan', 'adalah', 'ini', 'itu', 'tidak', 'ada', 'akan',
        'sudah', 'boleh', 'sangat', 'memang', 'bagus', 'baik', 'terbaik', 'murah', 'mahal',
        'harga', 'kualiti', 'produk', 'service', 'delivery', 'malaysia', 'malaysian',
        'ringgit', 'rm', 'sen', 'kedai', 'beli', 'jual', 'review', 'rating',
        'tapi', 'tetapi', 'atau', 'kalau', 'jika', 'bila', 'masa', 'tempat',
        'saya', 'kami', 'kita', 'mereka', 'dia', 'awak', 'anda'
    ]

    # Common English words
    english_indicators = [
        'the', 'and', 'for', 'with', 'this', 'that', 'not', 'have', 'will',
        'good', 'best', 'great', 'excellent', 'amazing', 'awesome', 'perfect',
        'price', 'quality', 'product', 'service', 'delivery', 'shipping',
        'but', 'however', 'or', 'if', 'when', 'where', 'how', 'what',
        'i', 'we', 'you', 'they', 'he', 'she', 'it'
    ]

    text_lower = text.lower()

    malay_count = sum(1 for word in malay_indicators if word in text_lower)
    english_count = sum(1 for word in english_indicators if word in text_lower)

    if malay_count > english_count:
        return "malay"
    elif english_count > malay_count:
        return "english"
    else:
        return "mixed"  # Bilingual or unclear

def parse_versatile_query(query: str) -> Dict[str, Any]:
    """Parse any format of query - natural language, claims, boolean, phrases, mixed - supports Malay & English"""

    if not query.strip():
        return {"type": "empty", "terms": [], "confidence": 0}

    import re

    # Detect language first
    detected_language = detect_language(query)

    # Initialize result structure
    result = {
        "original_query": query,
        "query_type": "mixed",
        "language": detected_language,
        "formats_detected": [],
        "components": {},
        "search_terms": [],
        "phrases": [],
        "boolean_operators": [],
        "claims": [],
        "natural_language": [],
        "confidence": 0.8
    }

    # 1. DETECT QUOTED PHRASES (Exact matches)
    phrases = re.findall(r'"([^"]*)"', query)
    if phrases:
        result["formats_detected"].append("quoted_phrases")
        result["phrases"] = phrases
        result["components"]["phrases"] = phrases

    # 2. DETECT BOOLEAN OPERATORS
    boolean_patterns = [
        (r'\b(AND|OR|NOT)\b', 'explicit_boolean'),
        (r'[@&]', 'symbol_and'),
        (r'\|', 'symbol_or'),
        (r'[!-](?=\w)', 'symbol_not')
    ]

    has_boolean = False
    for pattern, operator_type in boolean_patterns:
        if re.search(pattern, query, re.IGNORECASE):
            has_boolean = True
            result["formats_detected"].append(operator_type)
            result["boolean_operators"].append(operator_type)

    # 3. DETECT CLAIMS (Question-like or assertion patterns)
    claim_patterns = [
        r'\b(is|are|was|were|will|can|should|must|may|might)\b.*\?',  # Questions
        r'\b(true|false|fact|claim|alleged|reported|stated)\b',        # Fact-checking terms
        r'\b(according to|sources say|reports indicate)\b',            # Attribution
        r'\b(proven|disproven|verified|debunked|confirmed)\b',         # Verification terms
        r'^\s*[A-Z][^.!?]*[.!?]\s*$'                                  # Statement format
    ]

    for pattern in claim_patterns:
        if re.search(pattern, query, re.IGNORECASE):
            result["formats_detected"].append("claim_analysis")
            result["claims"].append(query.strip())
            break

    # 4. DETECT NATURAL LANGUAGE (Conversational patterns)
    natural_patterns = [
        r'\b(what|how|why|when|where|who)\b',                         # Question words
        r'\b(analyze|find|search|look for|show me|tell me)\b',        # Action requests
        r'\b(about|regarding|concerning|related to)\b',               # Topic indicators
        r'\b(sentiment|opinion|feedback|review|comment)\b'            # Analysis types
    ]

    for pattern in natural_patterns:
        if re.search(pattern, query, re.IGNORECASE):
            result["formats_detected"].append("natural_language")
            result["natural_language"].append(query.strip())
            break

    # 5. EXTRACT ALL MEANINGFUL TERMS
    # Remove quotes and boolean operators for term extraction
    clean_query = query
    for phrase in phrases:
        clean_query = clean_query.replace(f'"{phrase}"', phrase)

    # Remove boolean operators but keep the terms
    clean_query = re.sub(r'\b(AND|OR|NOT)\b', ' ', clean_query, flags=re.IGNORECASE)
    clean_query = re.sub(r'[@&|!-]', ' ', clean_query)

    # Extract meaningful terms (filter out common words)
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can'}

    terms = []
    words = re.findall(r'\b\w+\b', clean_query.lower())
    for word in words:
        if len(word) > 2 and word not in stop_words:
            terms.append(word)

    result["search_terms"] = list(set(terms))  # Remove duplicates

    # 6. DETERMINE PRIMARY QUERY TYPE
    if not result["formats_detected"]:
        result["query_type"] = "simple_keywords"
        result["formats_detected"] = ["simple_keywords"]
    elif len(result["formats_detected"]) == 1:
        result["query_type"] = result["formats_detected"][0]
    else:
        result["query_type"] = "mixed_format"

    # 7. SET CONFIDENCE LEVEL
    if has_boolean and phrases:
        result["confidence"] = 0.95  # High confidence for structured queries
    elif has_boolean or phrases:
        result["confidence"] = 0.85  # Good confidence for semi-structured
    elif result["claims"] or result["natural_language"]:
        result["confidence"] = 0.75  # Medium confidence for natural language
    else:
        result["confidence"] = 0.6   # Lower confidence for simple keywords

    return result

def match_versatile_query(text: str, query_info: Dict[str, Any]) -> Dict[str, Any]:
    """Advanced matching for any query format with detailed scoring"""

    if not text or not query_info:
        return {"match": False, "score": 0, "reasons": []}

    text_lower = text.lower()
    match_score = 0
    max_score = 0
    match_reasons = []

    # 1. EXACT PHRASE MATCHING (Highest priority)
    phrase_matches = 0
    if query_info.get("phrases"):
        for phrase in query_info["phrases"]:
            max_score += 10  # Each phrase worth 10 points
            if phrase.lower() in text_lower:
                phrase_matches += 1
                match_score += 10
                match_reasons.append(f"Exact phrase: '{phrase}'")

    # 2. BOOLEAN LOGIC MATCHING
    boolean_score = 0
    if "explicit_boolean" in query_info.get("formats_detected", []):
        max_score += 8
        # Simplified boolean evaluation
        original = query_info["original_query"]

        # Handle AND operations (@, AND)
        if " @ " in original or " AND " in original.upper():
            and_terms = re.split(r'\s+[@&]\s+|\s+AND\s+', original, flags=re.IGNORECASE)
            and_terms = [term.strip().strip('"') for term in and_terms]
            if all(term.lower() in text_lower for term in and_terms if term):
                boolean_score += 8
                match_reasons.append(f"Boolean AND match: {and_terms}")

        # Handle OR operations
        elif " OR " in original.upper():
            or_terms = re.split(r'\s+OR\s+', original, flags=re.IGNORECASE)
            or_terms = [term.strip().strip('"') for term in or_terms]
            matching_or_terms = [term for term in or_terms if term.lower() in text_lower]
            if matching_or_terms:
                boolean_score += 6
                match_reasons.append(f"Boolean OR match: {matching_or_terms}")

        match_score += boolean_score

    # 3. SEARCH TERMS MATCHING (Flexible)
    term_matches = 0
    if query_info.get("search_terms"):
        max_score += len(query_info["search_terms"]) * 2  # Each term worth 2 points
        for term in query_info["search_terms"]:
            if term.lower() in text_lower:
                term_matches += 1
                match_score += 2
                match_reasons.append(f"Keyword: '{term}'")

    # 4. CLAIM ANALYSIS MATCHING (Semantic)
    if query_info.get("claims"):
        max_score += 5
        claim = query_info["claims"][0].lower()

        # Extract key concepts from claim
        claim_words = re.findall(r'\b\w+\b', claim)
        claim_words = [w for w in claim_words if len(w) > 3]

        claim_matches = sum(1 for word in claim_words if word in text_lower)
        if claim_matches >= len(claim_words) * 0.3:  # 30% of claim words match
            match_score += 5
            match_reasons.append(f"Claim analysis match ({claim_matches}/{len(claim_words)} concepts)")

    # 5. NATURAL LANGUAGE MATCHING (Context-aware - Bilingual)
    if query_info.get("natural_language"):
        max_score += 3
        nl_query = query_info["natural_language"][0].lower()

        # Extract intent and subject (English & Malay)
        intent_words_en = ['analyze', 'find', 'search', 'show', 'tell', 'what', 'how', 'why', 'is', 'are', 'do', 'does']
        intent_words_my = ['analisis', 'cari', 'tunjuk', 'beritahu', 'apa', 'bagaimana', 'mengapa', 'kenapa', 'adakah', 'adalah']
        intent_words = intent_words_en + intent_words_my

        subject_words = [w for w in re.findall(r'\b\w+\b', nl_query) if w not in intent_words and len(w) > 2]

        subject_matches = sum(1 for word in subject_words if word in text_lower)
        if subject_matches > 0:
            match_score += min(3, subject_matches)
            match_reasons.append(f"Natural language match ({subject_matches} concepts) - {query_info.get('language', 'mixed')}")

    # 6. CALCULATE FINAL SCORE AND DECISION
    if max_score == 0:
        max_score = 1  # Prevent division by zero

    final_score = (match_score / max_score) * 100

    # Determine match based on query type and score
    is_match = False
    if query_info["query_type"] == "quoted_phrases" and phrase_matches > 0:
        is_match = True
    elif query_info["query_type"] in ["explicit_boolean", "symbol_and", "symbol_or"] and boolean_score > 0:
        is_match = True
    elif final_score >= 30:  # 30% threshold for general matching
        is_match = True
    elif term_matches >= 2:  # At least 2 keyword matches
        is_match = True

    return {
        "match": is_match,
        "score": round(final_score, 2),
        "raw_score": match_score,
        "max_score": max_score,
        "reasons": match_reasons,
        "phrase_matches": phrase_matches,
        "term_matches": term_matches,
        "query_type": query_info["query_type"]
    }

def filter_data_by_query_context(df: pd.DataFrame, query: str, nlp_results: Dict[str, Any] = None) -> pd.DataFrame:
    """
    Filter data based on query context and keywords for more relevant results
    """
    if df.empty:
        return df

    # Extract keywords and context from NLP results
    keywords = []
    industry_context = ''
    malaysian_context = []

    if nlp_results:
        keywords = [kw[0].lower() for kw in nlp_results.get('keywords', {}).get('combined', [])]
        industry_context = nlp_results.get('query_expansion', {}).get('industry_context', '')
        malaysian_context = nlp_results.get('query_expansion', {}).get('malaysian_context', [])

    # Add query words as keywords
    query_words = [word.lower() for word in query.split() if len(word) > 2]
    all_keywords = list(set(keywords + query_words))

    logger.info(f"🔍 Filtering data with keywords: {all_keywords}")
    logger.info(f"🏭 Industry context: {industry_context}")
    logger.info(f"🇲🇾 Malaysian context: {malaysian_context}")

    if not all_keywords:
        return df.head(50)  # Return first 50 if no keywords

    # Create relevance scores for each row
    df_copy = df.copy()
    df_copy['relevance_score'] = 0.0

    for idx, row in df_copy.iterrows():
        text = str(row.get('Text', '')).lower()
        score = 0.0

        # Score based on keyword matches
        for keyword in all_keywords:
            if keyword in text:
                score += 2.0  # Base score for keyword match

        # Bonus for industry context matches
        if industry_context == 'food':
            food_terms = ['makanan', 'makan', 'food', 'halal', 'sedap', 'restaurant', 'kedai', 'warung', 'mamak', 'delicious', 'taste', 'menu', 'dish', 'cuisine', 'nasi', 'mee', 'roti', 'laksa', 'rendang', 'satay']
            for term in food_terms:
                if term in text:
                    score += 1.5

        # Bonus for Malaysian context
        for context in malaysian_context:
            if context.lower() in text:
                score += 1.0

        # Bonus for location mentions
        kl_terms = ['kuala lumpur', 'kl', 'klang valley', 'selangor', 'petaling jaya', 'pj', 'shah alam', 'subang']
        for term in kl_terms:
            if term in text:
                score += 1.0

        df_copy.at[idx, 'relevance_score'] = score

    # Filter and sort by relevance
    relevant_df = df_copy[df_copy['relevance_score'] > 0].sort_values('relevance_score', ascending=False)

    if relevant_df.empty:
        logger.warning("⚠️ No relevant data found, returning random sample")
        return df.sample(min(20, len(df)))

    logger.info(f"✅ Found {len(relevant_df)} relevant posts out of {len(df)} total")
    return relevant_df.head(50)


def get_date_range_filter(request: AnalysisRequest) -> Dict[str, Any]:
    """
    Calculate date range for filtering crawled data

    Returns: {"start_date": datetime, "end_date": datetime, "days": int}
    """
    from datetime import datetime, timedelta

    end_date = datetime.now()

    # Parse date range
    if request.date_range == "custom" and request.custom_start_date and request.custom_end_date:
        try:
            start_date = datetime.fromisoformat(request.custom_start_date)
            end_date = datetime.fromisoformat(request.custom_end_date)
        except ValueError:
            logger.warning("⚠️ Invalid custom date format, using default 7 days")
            start_date = end_date - timedelta(days=7)
    elif request.date_range == "24h":
        start_date = end_date - timedelta(hours=24)
    elif request.date_range == "7days":
        start_date = end_date - timedelta(days=7)
    elif request.date_range == "30days":
        start_date = end_date - timedelta(days=30)
    elif request.date_range == "90days":
        start_date = end_date - timedelta(days=90)
    else:
        # Default to 7 days
        start_date = end_date - timedelta(days=7)

    days = (end_date - start_date).days

    return {
        "start_date": start_date,
        "end_date": end_date,
        "days": days,
        "start_iso": start_date.isoformat(),
        "end_iso": end_date.isoformat()
    }


def get_analysis_focus_config(request: AnalysisRequest) -> Dict[str, Any]:
    """
    Get configuration based on analysis focus

    Returns: {"sort_by": str, "filter_criteria": dict, "boost_factor": dict}
    """
    focus_configs = {
        "engagement": {
            "sort_by": "total_engagement",
            "description": "Prioritize highly engaging content (likes, shares, comments)",
            "min_engagement": 10,  # Filter out low engagement
            "boost_comments": 1.5,  # Boost posts with many comments
            "boost_viral": 2.0      # Boost viral content
        },
        "sentiment": {
            "sort_by": "comments_count",
            "description": "Prioritize content with rich discussions for sentiment analysis",
            "min_comments": 5,      # Need comments for sentiment
            "boost_comments": 2.0,  # Heavily prioritize commented posts
            "boost_controversial": 1.5  # Boost posts with mixed reactions
        },
        "trends": {
            "sort_by": "date",
            "description": "Prioritize recent content to identify emerging trends",
            "max_age_hours": 48,    # Focus on last 48 hours
            "boost_recent": 2.0,    # Heavily boost recent posts
            "boost_velocity": 1.5   # Boost rapidly growing posts
        },
        "comprehensive": {
            "sort_by": "relevance",
            "description": "Balanced sampling across all dimensions",
            "min_engagement": 1,
            "boost_comments": 1.0,
            "boost_recent": 1.0
        }
    }

    return focus_configs.get(request.analysis_focus, focus_configs["comprehensive"])


def get_date_range_filter(request: AnalysisRequest) -> Dict[str, Any]:
    """
    Get date range filter based on user configuration

    Returns: {
        "start_date": datetime,
        "end_date": datetime,
        "start_iso": str,
        "end_iso": str,
        "days": int
    }
    """
    from datetime import datetime, timedelta

    end_date = datetime.now()

    if request.date_range == "24h":
        start_date = end_date - timedelta(hours=24)
        days = 1
    elif request.date_range == "7days":
        start_date = end_date - timedelta(days=7)
        days = 7
    elif request.date_range == "30days":
        start_date = end_date - timedelta(days=30)
        days = 30
    elif request.date_range == "90days":
        start_date = end_date - timedelta(days=90)
        days = 90
    elif request.date_range == "custom":
        if request.custom_start_date and request.custom_end_date:
            start_date = datetime.fromisoformat(request.custom_start_date)
            end_date = datetime.fromisoformat(request.custom_end_date)
            days = (end_date - start_date).days
        else:
            # Fallback to 7 days
            start_date = end_date - timedelta(days=7)
            days = 7
    else:
        # Default to 7 days
        start_date = end_date - timedelta(days=7)
        days = 7

    return {
        "start_date": start_date,
        "end_date": end_date,
        "start_iso": start_date.isoformat(),
        "end_iso": end_date.isoformat(),
        "days": days
    }


def get_analysis_focus_config(request: AnalysisRequest) -> Dict[str, Any]:
    """
    Get analysis focus configuration for intelligent prioritization

    Returns: {
        "focus": str,
        "description": str,
        "sort_by": str,
        "filter_criteria": dict
    }
    """
    FOCUS_CONFIGS = {
        "engagement": {
            "focus": "engagement",
            "description": "Prioritize high-engagement posts (likes, shares, comments)",
            "sort_by": "total_engagement",
            "filter_criteria": {"min_engagement": 10}
        },
        "sentiment": {
            "focus": "sentiment",
            "description": "Prioritize posts with many comments for sentiment analysis",
            "sort_by": "comments_count",
            "filter_criteria": {"min_comments": 5}
        },
        "trends": {
            "focus": "trends",
            "description": "Prioritize recent posts (last 24-48h) for trend detection",
            "sort_by": "date",
            "filter_criteria": {"max_age_hours": 48}
        },
        "comprehensive": {
            "focus": "comprehensive",
            "description": "Balanced approach - mix of engagement, sentiment, and trends",
            "sort_by": "relevance",
            "filter_criteria": {}
        }
    }

    return FOCUS_CONFIGS.get(request.analysis_focus, FOCUS_CONFIGS["comprehensive"])


def get_platform_limits(request: AnalysisRequest, platform: str) -> Dict[str, int]:
    """
    Get platform-specific limits based on user configuration or preset

    Uses OPTIMIZED presets tailored to each platform's characteristics:
    - Twitter: High volume, short posts → MORE posts, FEWER comments
    - YouTube: Low volume, rich comments → FEWER videos, MORE comments
    - Facebook: Balanced engagement → Equal posts + comments
    - Instagram: Visual-first → More posts, moderate comments
    - TikTok: Viral content → Moderate posts, high comments
    - LinkedIn: Professional quality → Moderate posts + comments
    - News/Google: No comments → Many results, zero comments

    Returns: {"max_posts": int, "max_comments": int}
    """
    # ✅ OPTIMIZED PLATFORM-SPECIFIC PRESETS
    OPTIMIZED_PRESETS = {
        "quick": {
            # Fast overview - 1-2 minutes, ~200-300 data points
            "facebook": {"max_posts": 20, "max_comments": 10},
            "instagram": {"max_posts": 20, "max_comments": 10},
            "twitter": {"max_posts": 30, "max_comments": 5},    # Twitter = high volume
            "x": {"max_posts": 30, "max_comments": 5},
            "tiktok": {"max_posts": 15, "max_comments": 10},
            "youtube": {"max_posts": 10, "max_comments": 20},   # YouTube comments = gold
            "linkedin": {"max_posts": 10, "max_comments": 10},
            "google": {"max_posts": 20, "max_comments": 0},
            "news": {"max_posts": 30, "max_comments": 0},       # News = high volume
            "shopee": {"max_posts": 20, "max_comments": 0},
            "lazada": {"max_posts": 20, "max_comments": 0}
        },
        "standard": {
            # Balanced - 3-5 minutes, ~800-1200 data points (BEST for most cases)
            "facebook": {"max_posts": 100, "max_comments": 100},  # ⬆️ INCREASED from 50
            "instagram": {"max_posts": 100, "max_comments": 50},  # ⬆️ INCREASED from 50
            "twitter": {"max_posts": 200, "max_comments": 50},    # ⬆️ INCREASED from 100
            "x": {"max_posts": 200, "max_comments": 50},          # ⬆️ INCREASED from 100
            "tiktok": {"max_posts": 50, "max_comments": 100},     # ⬆️ INCREASED from 30
            "youtube": {"max_posts": 50, "max_comments": 100},    # ⬆️ INCREASED from 20
            "linkedin": {"max_posts": 50, "max_comments": 50},    # ⬆️ INCREASED from 30
            "google": {"max_posts": 100, "max_comments": 0},      # ⬆️ INCREASED from 50
            "news": {"max_posts": 200, "max_comments": 0},        # ⬆️ INCREASED from 100
            "shopee": {"max_posts": 100, "max_comments": 0},      # ⬆️ INCREASED from 50
            "lazada": {"max_posts": 100, "max_comments": 0}       # ⬆️ INCREASED from 50
        },
        "deep": {
            # Comprehensive - 5-10 minutes, ~2000-4000 data points
            "facebook": {"max_posts": 100, "max_comments": 100},
            "instagram": {"max_posts": 100, "max_comments": 100},
            "twitter": {"max_posts": 200, "max_comments": 50},
            "x": {"max_posts": 200, "max_comments": 50},
            "tiktok": {"max_posts": 50, "max_comments": 100},
            "youtube": {"max_posts": 50, "max_comments": 200},
            "linkedin": {"max_posts": 50, "max_comments": 50},
            "google": {"max_posts": 100, "max_comments": 0},
            "news": {"max_posts": 200, "max_comments": 0},
            "shopee": {"max_posts": 100, "max_comments": 0},
            "lazada": {"max_posts": 100, "max_comments": 0}
        },
        "custom": {
            # Fallback for custom mode - will be overridden by platform_configs
            "facebook": {"max_posts": 50, "max_comments": 50},
            "instagram": {"max_posts": 50, "max_comments": 30},
            "twitter": {"max_posts": 100, "max_comments": 20},
            "x": {"max_posts": 100, "max_comments": 20},
            "tiktok": {"max_posts": 30, "max_comments": 50},
            "youtube": {"max_posts": 20, "max_comments": 100},
            "linkedin": {"max_posts": 30, "max_comments": 30},
            "google": {"max_posts": 50, "max_comments": 0},
            "news": {"max_posts": 100, "max_comments": 0},
            "shopee": {"max_posts": 50, "max_comments": 0},
            "lazada": {"max_posts": 50, "max_comments": 0}
        }
    }

    # If user provided platform-specific config, use it (highest priority)
    if request.platform_configs and platform in request.platform_configs:
        config = request.platform_configs[platform]
        return {
            "max_posts": config.get("max_posts", 50),
            "max_comments": config.get("max_comments", 50)
        }

    # Otherwise, use optimized preset for this platform
    preset_name = request.analysis_depth if request.analysis_depth in OPTIMIZED_PRESETS else "standard"
    preset = OPTIMIZED_PRESETS[preset_name]

    # Get platform-specific limits, fallback to standard if platform not found
    if platform in preset:
        return preset[platform].copy()
    else:
        # Fallback for unknown platforms
        logger.warning(f"⚠️ Unknown platform '{platform}', using standard limits")
        return {"max_posts": 50, "max_comments": 50}


async def try_real_time_crawl(platform: str, query: str, max_results: int = 100, max_comments: int = 50, comment_sampling: str = "smart") -> Optional[List[Dict]]:
    """
    Attempt real-time crawling using Apify adapter with intelligent comment sampling
    Returns None if crawling fails or is not available

    Args:
        platform: Platform name (facebook, instagram, etc.)
        query: Search query
        max_results: Maximum number of posts to collect
        max_comments: Maximum number of comments per post
        comment_sampling: Comment sampling strategy ("smart", "top_only", "recent_only", "random")
    """
    if not APIFY_AVAILABLE:
        logger.info(f"⚠️ Apify not available, skipping real-time crawl for {platform}")
        return None

    try:
        logger.info(f"🚀 Attempting real-time Apify crawl for {platform}: '{query}'")
        logger.info(f"📊 Limits: {max_results} posts, {max_comments} comments per post")
        logger.info(f"🎯 Comment sampling: {comment_sampling}")

        adapter = SimpleApifyAdapter()
        # Pass max_results, max_comments, and comment_sampling to the adapter
        results = await adapter.crawl_platform(platform, query, max_results, max_comments, comment_sampling)

        if results and len(results) > 0:
            logger.info(f"✅ Real-time crawl successful: {len(results)} records from {platform}")
            return results
        else:
            logger.info(f"⚠️ Real-time crawl returned no results for {platform}")
            return None

    except Exception as e:
        logger.error(f"❌ Real-time crawl failed for {platform}: {e}")
        return None


def load_platform_data(platform: str, query: str = "", max_results: int = 100, nlp_results: Dict[str, Any] = None) -> Dict[str, Any]:
    """Load real data from platform CSV files with intelligent filtering and synthetic data generation"""

    platform_dir = DATA_DIR / platform

    # Try to find existing relevant data first
    if platform_dir.exists():
        csv_files = list(platform_dir.glob("*.csv"))

        # Look for query-relevant files
        query_clean = re.sub(r'[^\w\s-]', '', query.lower()).strip()
        query_words = query_clean.split()

        relevant_files = []
        for csv_file in csv_files:
            filename_lower = csv_file.name.lower()
            # Check if filename contains query keywords
            if any(word in filename_lower for word in query_words if len(word) > 2):
                relevant_files.append(csv_file)

        if relevant_files:
            logger.info(f"📁 Found {len(relevant_files)} relevant files for query '{query}' in {platform}")
            # Use the most recent relevant file
            latest_file = max(relevant_files, key=lambda f: f.stat().st_mtime)
            return _load_csv_data(latest_file, platform, query, max_results, nlp_results)

    # If no relevant data found, generate synthetic data
    logger.info(f"🎯 No relevant data found for '{query}' on {platform}. Generating synthetic data...")
    return _generate_synthetic_platform_data(platform, query, max_results, nlp_results)

def _generate_synthetic_platform_data(platform: str, query: str, max_results: int, nlp_results: Dict[str, Any] = None) -> Dict[str, Any]:
    """Generate synthetic data for platform when no relevant data exists"""
    try:
        # Import synthetic data generator
        import sys
        from pathlib import Path
        sys.path.append(str(Path(__file__).parent.parent))

        from synthetic_data_generator import SyntheticDataGenerator

        # Generate synthetic data
        generator = SyntheticDataGenerator()
        df = generator.generate_platform_data(platform, query, min(max_results, 50))

        # Save the generated data for future use
        generator.save_platform_data(platform, query, df)

        logger.info(f"✅ Generated {len(df)} synthetic posts for {platform}")

        # Process the synthetic data same as real data
        return _process_platform_dataframe(df, platform, query, max_results, nlp_results)

    except Exception as e:
        logger.error(f"❌ Error generating synthetic data for {platform}: {e}")
        return {
            "platform": platform,
            "error": f"No data available for {platform}",
            "data_points": 0,
            "status": "no_data"
        }

def _load_csv_data(csv_file: Path, platform: str, query: str, max_results: int, nlp_results: Dict[str, Any] = None) -> Dict[str, Any]:
    """Load and process CSV data from file"""
    try:
        logger.info(f"Loading data from: {csv_file}")

        # Read CSV data - try different separators
        try:
            # First try comma-separated (standard CSV)
            df = pd.read_csv(csv_file, sep=',', quotechar='"', skipinitialspace=True, on_bad_lines='skip')
            logger.info(f"CSV loaded with {len(df.columns)} columns: {list(df.columns)}")
            # Check if parsing was successful by verifying we have multiple columns
            if len(df.columns) == 1:
                raise ValueError("Only one column detected, trying other separators")
        except Exception as e:
            logger.warning(f"Comma-separated parsing failed: {e}")
            try:
                # Fallback to tab-separated
                df = pd.read_csv(csv_file, sep='\t', quotechar='"', skipinitialspace=True, on_bad_lines='skip')
                logger.info(f"Tab-separated CSV loaded with {len(df.columns)} columns: {list(df.columns)}")
            except Exception as e2:
                logger.warning(f"Tab-separated parsing failed: {e2}")
                # Last resort - let pandas auto-detect
                df = pd.read_csv(csv_file, sep=None, engine='python', quotechar='"', on_bad_lines='skip')
                logger.info(f"Auto-detected CSV loaded with {len(df.columns)} columns: {list(df.columns)}")

        return _process_platform_dataframe(df, platform, query, max_results, nlp_results)

    except Exception as e:
        logger.error(f"Error loading CSV data from {csv_file}: {e}")
        return {
            "platform": platform,
            "error": f"Error loading data: {str(e)}",
            "data_points": 0,
            "status": "error"
        }

def _process_platform_dataframe(df: pd.DataFrame, platform: str, query: str, max_results: int, nlp_results: Dict[str, Any] = None) -> Dict[str, Any]:
    """Process loaded dataframe with filtering and analysis"""

    # Filter data based on query and NLP context
    if query and 'Text' in df.columns:
        logger.info(f"🔍 Applying intelligent filtering for query: {query}")
        filtered_df = filter_data_by_query_context(df, query, nlp_results)

        # Fallback to versatile query if no results
        if len(filtered_df) == 0:
            logger.info("🔄 Falling back to versatile query matching")
            query_info = parse_versatile_query(query)
            def check_match(text):
                match_result = match_versatile_query(str(text), query_info)
                return match_result["match"]
            mask = df['Text'].apply(check_match)
            filtered_df = df[mask]

            if len(filtered_df) == 0:
                filtered_df = df.head(min(max_results, len(df)))
        filtered_df = df.head(min(max_results, len(df)))

    # Process the filtered data
    if len(filtered_df) == 0:
        logger.warning(f"No relevant data found for query: {query}")
        return {
            "platform": platform,
            "error": f"No relevant data found for query: {query}",
            "data_points": 0,
            "status": "no_relevant_data"
        }

    # Limit results
    final_df = filtered_df.head(max_results)

    logger.info(f"✅ Processed {len(final_df)} records for {platform}")

    # Process sentiment and engagement data
    processed_data = process_platform_data(final_df, platform, query)

    # Verify that sentiment columns were added
    logger.info(f"📊 DataFrame columns after sentiment analysis: {list(final_df.columns)}")
    # Note: File saving is now handled in the main /analyze endpoint
    # This function only processes and returns insights

    return {
        "platform": platform,
        "data_points": len(final_df),
        "status": "success",
        "processed_insights": processed_data,
        "raw_data": final_df.to_dict('records')[:10]  # Include sample of raw data
    }

def analyze_sentiment_trends_over_time(df: pd.DataFrame) -> Dict[str, Any]:
    """Analyze sentiment trends over time with hype detection"""

    if df.empty or 'Date' not in df.columns:
        return {"error": "No date data available for trend analysis"}

    try:
        # Convert Date column to datetime
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df = df.dropna(subset=['Date'])

        if len(df) < 2:
            return {"error": "Insufficient data for trend analysis"}

        # Sort by date
        df_sorted = df.sort_values('Date')

        # Group by date and calculate daily sentiment
        daily_sentiment = df_sorted.groupby(df_sorted['Date'].dt.date).agg({
            'sentiment_score': ['mean', 'count'],
            'total_engagement': 'sum'
        }).round(3)

        # Flatten column names
        daily_sentiment.columns = ['avg_sentiment', 'post_count', 'total_engagement']
        daily_sentiment = daily_sentiment.reset_index()

        # Calculate trend direction
        sentiment_values = daily_sentiment['avg_sentiment'].tolist()
        dates = daily_sentiment['Date'].tolist()

        # Trend analysis
        if len(sentiment_values) >= 3:
            # Calculate moving average for smoother trend
            window_size = min(3, len(sentiment_values))
            moving_avg = []
            for i in range(len(sentiment_values)):
                start_idx = max(0, i - window_size + 1)
                avg = sum(sentiment_values[start_idx:i+1]) / (i - start_idx + 1)
                moving_avg.append(round(avg, 3))

            # Determine overall trend
            first_half = moving_avg[:len(moving_avg)//2]
            second_half = moving_avg[len(moving_avg)//2:]

            first_avg = sum(first_half) / len(first_half)
            second_avg = sum(second_half) / len(second_half)

            trend_change = second_avg - first_avg

            if trend_change > 0.1:
                trend_direction = "📈 RISING"
                trend_status = "positive_trend"
                trend_description = "Sentiment is improving over time"
            elif trend_change < -0.1:
                trend_direction = "📉 DECLINING"
                trend_status = "negative_trend"
                trend_description = "Sentiment is declining over time"
            else:
                trend_direction = "➡️ STABLE"
                trend_status = "stable_trend"
                trend_description = "Sentiment remains relatively stable"
        else:
            trend_direction = "➡️ INSUFFICIENT DATA"
            trend_status = "insufficient_data"
            trend_description = "Need more data points for trend analysis"

        # Detect hype periods (high engagement + positive sentiment)
        hype_periods = []
        for _, row in daily_sentiment.iterrows():
            if row['total_engagement'] > daily_sentiment['total_engagement'].mean() * 1.5 and row['avg_sentiment'] > 0.7:
                hype_periods.append({
                    "date": row['Date'].strftime('%Y-%m-%d'),
                    "sentiment": row['avg_sentiment'],
                    "engagement": int(row['total_engagement']),
                    "posts": int(row['post_count']),
                    "hype_level": "HIGH" if row['total_engagement'] > daily_sentiment['total_engagement'].mean() * 2 else "MODERATE"
                })

        # Detect low periods (low engagement + negative sentiment)
        low_periods = []
        for _, row in daily_sentiment.iterrows():
            if row['total_engagement'] < daily_sentiment['total_engagement'].mean() * 0.5 and row['avg_sentiment'] < 0.4:
                low_periods.append({
                    "date": row['Date'].strftime('%Y-%m-%d'),
                    "sentiment": row['avg_sentiment'],
                    "engagement": int(row['total_engagement']),
                    "posts": int(row['post_count']),
                    "concern_level": "HIGH" if row['avg_sentiment'] < 0.3 else "MODERATE"
                })

        # Prepare time series data for visualization
        time_series = []
        for _, row in daily_sentiment.iterrows():
            time_series.append({
                "date": row['Date'].strftime('%Y-%m-%d'),
                "sentiment": row['avg_sentiment'],
                "engagement": int(row['total_engagement']),
                "posts": int(row['post_count'])
            })

        return {
            "trend_analysis": {
                "direction": trend_direction,
                "status": trend_status,
                "description": trend_description,
                "change_magnitude": round(trend_change, 3) if 'trend_change' in locals() else 0,
                "data_points": len(daily_sentiment)
            },
            "hype_periods": hype_periods,
            "low_periods": low_periods,
            "time_series": time_series,
            "summary": {
                "total_days": len(daily_sentiment),
                "avg_daily_sentiment": round(daily_sentiment['avg_sentiment'].mean(), 3),
                "avg_daily_engagement": int(daily_sentiment['total_engagement'].mean()),
                "peak_sentiment_date": daily_sentiment.loc[daily_sentiment['avg_sentiment'].idxmax(), 'Date'].strftime('%Y-%m-%d'),
                "peak_sentiment_score": daily_sentiment['avg_sentiment'].max(),
                "lowest_sentiment_date": daily_sentiment.loc[daily_sentiment['avg_sentiment'].idxmin(), 'Date'].strftime('%Y-%m-%d'),
                "lowest_sentiment_score": daily_sentiment['avg_sentiment'].min()
            }
        }

    except Exception as e:
        return {"error": f"Error in trend analysis: {str(e)}"}

def process_platform_data(df: pd.DataFrame, platform: str, query: str = "") -> Dict[str, Any]:
    """Process platform data for insights using custom Hugging Face models"""

    if df.empty:
        return {"error": "No data to process"}

    insights = {
        "total_posts": len(df),
        "platform": platform
    }

    # Enhanced sentiment analysis using custom models
    if 'Text' in df.columns:
        # Filter out empty text
        valid_texts_mask = df['Text'].astype(str).str.strip().str.len() > 0
        valid_indices = df[valid_texts_mask].index.tolist()
        valid_texts = df.loc[valid_indices, 'Text'].tolist()

        logger.info(f"🤖 Running custom sentiment & emotion analysis on {len(valid_texts)} valid texts (out of {len(df)} total records)...")

        sentiment_results = []
        emotion_results = []

        # Initialize new columns in DataFrame
        df['sentiment_label'] = 'neutral'
        df['sentiment_score'] = 0.5
        df['sentiment_confidence'] = 0.0
        df['detected_language'] = 'unknown'  # 🌍 NEW: Language detection
        df['demographic'] = 'Unknown'        # 🌍 NEW: Demographic group
        df['emotion_primary'] = 'neutral'
        df['emotion_anger'] = 0.0
        df['emotion_fear'] = 0.0
        df['emotion_happy'] = 0.0
        df['emotion_sadness'] = 0.0
        df['emotion_love'] = 0.0
        df['emotion_surprise'] = 0.0

        # Analyze each text with custom models
        for idx, text in zip(valid_indices, valid_texts):
            try:
                # 🌍 MULTILINGUAL Custom sentiment analysis
                sentiment_result = analyze_sentiment_with_custom_model(text)
                sentiment_results.append(sentiment_result)

                # Save sentiment to DataFrame - UPDATE BOTH COLUMNS!
                df.at[idx, 'sentiment_label'] = sentiment_result['sentiment']
                df.at[idx, 'Sentiment'] = sentiment_result['sentiment']  # ✅ FIX: Update original column too!
                df.at[idx, 'sentiment_confidence'] = sentiment_result['confidence']

                # 🌍 Save language and demographic info
                df.at[idx, 'detected_language'] = sentiment_result.get('detected_language', 'unknown')
                df.at[idx, 'demographic'] = sentiment_result.get('demographic', 'Unknown')

                # 🎯 HYBRID APPROACH (OPTION 3): Confidence-based scoring
                # Negative: 0.0 (high confidence) → 0.3 (low confidence)
                # Neutral: 0.5 (fixed)
                # Positive: 0.7 (low confidence) → 1.0 (high confidence)

                confidence = sentiment_result['confidence']

                if sentiment_result['sentiment'] == 'positive':
                    # Base score 0.7, add up to 0.3 based on confidence
                    # Range: 0.7 (low confidence) → 1.0 (high confidence)
                    df.at[idx, 'sentiment_score'] = 0.7 + (confidence * 0.3)

                elif sentiment_result['sentiment'] == 'negative':
                    # Base score 0.3, subtract up to 0.3 based on confidence
                    # Range: 0.3 (low confidence) → 0.0 (high confidence)
                    df.at[idx, 'sentiment_score'] = 0.3 - (confidence * 0.3)

                else:  # neutral
                    # Neutral stays at 0.5 (fixed)
                    df.at[idx, 'sentiment_score'] = 0.5

                # Custom emotion analysis
                emotion_result = analyze_emotion_with_custom_model(text)
                emotion_results.append(emotion_result)

                # Save emotions to DataFrame
                df.at[idx, 'emotion_primary'] = emotion_result['primary_emotion']
                for emotion, score in emotion_result['emotions'].items():
                    # Map emotion names to column names
                    emotion_col = f'emotion_{emotion.lower()}'
                    if emotion_col in df.columns:
                        df.at[idx, emotion_col] = score

            except Exception as e:
                logger.warning(f"⚠️ Error analyzing text at index {idx}: {e}")
                continue

        # Aggregate sentiment results
        if sentiment_results:
            avg_confidence = sum(r['confidence'] for r in sentiment_results) / len(sentiment_results)
            sentiment_counts = {}
            for result in sentiment_results:
                sentiment = result['sentiment']
                sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1

            primary_sentiment = max(sentiment_counts.keys(), key=lambda k: sentiment_counts[k])

            # Calculate average sentiment score from DataFrame
            avg_sentiment_score = df.loc[valid_indices, 'sentiment_score'].mean()

            insights["custom_sentiment"] = {
                "primary_sentiment": primary_sentiment,
                "confidence": round(avg_confidence, 3),
                "distribution": sentiment_counts,
                "model_used": sentiment_results[0]['model'],
                "average_score": round(avg_sentiment_score, 3)
            }

            # Also set as original_sentiment_score for compatibility
            insights["original_sentiment_score"] = round(avg_sentiment_score, 3)
            insights["original_sentiment_label"] = primary_sentiment

            # 🌍 NEW: Demographic Analytics based on detected language
            if 'demographic' in df.columns and 'detected_language' in df.columns:
                demographic_breakdown = {}

                for demographic in df['demographic'].unique():
                    if pd.isna(demographic) or demographic == 'Unknown':
                        continue

                    demo_df = df[df['demographic'] == demographic]

                    # Count posts vs comments
                    demo_posts = len(demo_df[demo_df['Type'] == 'post']) if 'Type' in demo_df.columns else len(demo_df)
                    demo_comments = len(demo_df[demo_df['Type'] == 'comment']) if 'Type' in demo_df.columns else 0

                    # Sentiment distribution for this demographic
                    demo_sentiment_counts = demo_df['sentiment_label'].value_counts().to_dict() if 'sentiment_label' in demo_df.columns else {}
                    total_demo = len(demo_df)
                    demo_sentiment_pct = {k: round(v/total_demo*100, 1) for k, v in demo_sentiment_counts.items()} if total_demo > 0 else {}

                    # Average engagement for this demographic
                    demo_engagement = 0
                    if 'total_engagement' in demo_df.columns:
                        demo_engagement = int(demo_df['total_engagement'].sum())

                    demographic_breakdown[demographic] = {
                        "total_posts": demo_posts,
                        "total_comments": demo_comments,
                        "total_records": total_demo,
                        "percentage": round(total_demo / len(df) * 100, 1),
                        "sentiment_distribution": demo_sentiment_pct,
                        "total_engagement": demo_engagement,
                        "avg_engagement_per_post": round(demo_engagement / demo_posts, 1) if demo_posts > 0 else 0
                    }

                insights["demographic_analytics"] = {
                    "breakdown": demographic_breakdown,
                    "total_demographics": len(demographic_breakdown),
                    "dominant_demographic": max(demographic_breakdown.keys(), key=lambda k: demographic_breakdown[k]['total_records']) if demographic_breakdown else "Unknown"
                }

                logger.info(f"🌍 Demographic breakdown: {list(demographic_breakdown.keys())}")

        # Aggregate emotion results
        if emotion_results:
            emotion_totals = {}
            for result in emotion_results:
                for emotion, score in result['emotions'].items():
                    emotion_totals[emotion] = emotion_totals.get(emotion, 0) + score

            # Average emotions
            avg_emotions = {emotion: score/len(emotion_results) for emotion, score in emotion_totals.items()}
            primary_emotion = max(avg_emotions.keys(), key=lambda k: avg_emotions[k])

            insights["custom_emotions"] = {
                "primary_emotion": primary_emotion,
                "emotion_distribution": {k: round(v, 3) for k, v in avg_emotions.items()},
                "model_used": emotion_results[0]['model']
            }

    # Fallback to original sentiment if available and not already set
    if 'sentiment_score' in df.columns and "original_sentiment_score" not in insights:
        sentiment_scores = pd.to_numeric(df['sentiment_score'], errors='coerce').dropna()
        if not sentiment_scores.empty:
            avg_sentiment = sentiment_scores.mean()
            insights["original_sentiment_score"] = round(avg_sentiment, 3)
            insights["original_sentiment_label"] = "positive" if avg_sentiment > 0.6 else "negative" if avg_sentiment < 0.4 else "neutral"
    
    # Process engagement if available
    engagement_cols = ['likes', 'shares', 'comments_count', 'total_engagement']
    total_engagement = 0
    
    for col in engagement_cols:
        if col in df.columns:
            engagement_values = pd.to_numeric(df[col], errors='coerce').fillna(0)
            total_engagement += engagement_values.sum()
    
    insights["total_engagement"] = int(total_engagement)
    insights["average_engagement"] = round(total_engagement / len(df), 2) if len(df) > 0 else 0
    
    # Extract trending topics from text
    if 'Text' in df.columns:
        # Smart contextual trending topics extraction
        query_lower = query.lower() if query else ""

        # Define category-specific terms and their related topics
        category_mappings = {
            # Fashion & Clothing
            'fashion': {
                'terms': ['tudung', 'hijab', 'baju', 'dress', 'fashion', 'style', 'pakaian', 'busana', 'outfit', 'trend'],
                'topics': ['fashion', 'style', 'trend', 'popular', 'cantik', 'murah', 'kualiti', 'brand', 'design', 'warna']
            },
            # Political
            'political': {
                'terms': ['perdana', 'menteri', 'pas', 'pru', 'politik', 'kerajaan', 'parti', 'pilihan', 'raya', 'rakyat', 'negara', 'pemimpin'],
                'topics': ['politik', 'kerajaan', 'rakyat', 'malaysia', 'kepimpinan', 'parti', 'demokrasi', 'pilihan_raya', 'sokongan', 'negara']
            },
            # Technology
            'technology': {
                'terms': ['iphone', 'samsung', 'xiaomi', 'phone', 'smartphone', 'gadget', 'tech', 'camera', 'spec', 'performance'],
                'topics': ['teknologi', 'kamera', 'performance', 'harga', 'spec', 'kualiti', 'bagus', 'terbaik', 'recommended', 'value']
            },
            # Food & Beverage
            'food': {
                'terms': ['makanan', 'makan', 'sedap', 'restaurant', 'cafe', 'food', 'rasa', 'menu', 'masak', 'resepi'],
                'topics': ['makanan', 'sedap', 'rasa', 'restaurant', 'menu', 'harga', 'service', 'recommended', 'popular', 'best']
            },
            # Beauty & Cosmetics
            'beauty': {
                'terms': ['makeup', 'skincare', 'beauty', 'cosmetic', 'lipstick', 'foundation', 'serum', 'cleanser', 'moisturizer'],
                'topics': ['beauty', 'makeup', 'skincare', 'cantik', 'brand', 'kualiti', 'harga', 'recommended', 'popular', 'best']
            },
            # Health & Wellness
            'health': {
                'terms': ['kesihatan', 'health', 'vitamin', 'supplement', 'ubat', 'medicine', 'hospital', 'doktor', 'rawatan'],
                'topics': ['kesihatan', 'health', 'rawatan', 'ubat', 'supplement', 'doktor', 'hospital', 'bagus', 'berkesan', 'recommended']
            }
        }

        # Detect query category
        detected_category = None
        for category, config in category_mappings.items():
            if any(term in query_lower for term in config['terms']):
                detected_category = category
                break

        if detected_category:
            # Generate contextual topics based on detected category
            base_topics = category_mappings[detected_category]['topics'].copy()

            # Add specific query keywords
            query_words = [word.strip('.,!?()[]{}":;').lower() for word in query_lower.split()
                          if len(word) > 3 and word not in ['yang', 'dan', 'untuk', 'dengan', 'adalah', 'dari', 'pada', 'dalam']]

            # Prioritize query words
            trending_topics = []
            for word in query_words:
                if word not in trending_topics:
                    trending_topics.append(word)

            # Add category-specific topics
            for topic in base_topics:
                if topic not in trending_topics and len(trending_topics) < 5:
                    trending_topics.append(topic)

            insights["trending_topics"] = trending_topics[:5]

        else:
            # Fallback: extract from actual text content
            all_text = ' '.join(df['Text'].astype(str))
            words = all_text.lower().split()

            # Enhanced stop words list
            common_words = {
                'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from', 'up', 'about', 'into', 'over', 'after',
                'yang', 'dan', 'atau', 'di', 'ke', 'untuk', 'dari', 'pada', 'dalam', 'dengan', 'adalah', 'ini', 'itu', 'tidak', 'ada', 'akan',
                'very', 'really', 'just', 'now', 'here', 'there', 'where', 'when', 'what', 'how', 'why', 'who', 'which', 'this', 'that',
                'sangat', 'memang', 'juga', 'sudah', 'telah', 'dapat', 'boleh', 'hanya', 'lebih', 'paling', 'satu', 'dua', 'tiga'
            }

            # Clean and filter words
            filtered_words = []
            for word in words:
                clean_word = word.strip('.,!?()[]{}":;').lower()
                if len(clean_word) > 3 and clean_word not in common_words:
                    filtered_words.append(clean_word)

            from collections import Counter
            word_counts = Counter(filtered_words)

            # Prioritize query-related words
            trending_topics = []
            if query:
                query_words = [word.lower() for word in query.split() if len(word) > 3]
                for word in query_words:
                    if word not in trending_topics:
                        trending_topics.append(word)

            # Add other frequent words
            for word, count in word_counts.most_common(10):
                if word not in trending_topics and len(trending_topics) < 5:
                    trending_topics.append(word)

            insights["trending_topics"] = trending_topics[:5] if trending_topics else ['produk', 'kualiti', 'harga', 'bagus', 'recommended']

    # Add sentiment trend analysis over time
    sentiment_trends = analyze_sentiment_trends_over_time(df)
    if "error" not in sentiment_trends:
        insights["sentiment_trends"] = sentiment_trends

    return insights

# ===== API ENDPOINTS =====

@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    """Serve the simple frontend page"""
    html_file = Path(__file__).parent.parent / "web_frontend" / "simple_index.html"

    if html_file.exists():
        with open(html_file, 'r', encoding='utf-8') as f:
            return HTMLResponse(content=f.read())
    else:
        return HTMLResponse(content="""
        <html>
            <head><title>InsightPulse</title></head>
            <body style="font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px;">
                <h1>InsightPulse</h1>
                <p>Social Media Analytics Platform</p>
                <p>Backend is running! API documentation available at <a href="/docs">/docs</a></p>
                <p>Available endpoints:</p>
                <ul>
                    <li><a href="/platforms">/platforms</a> - View available platforms</li>
                    <li><a href="/health">/health</a> - System health check</li>
                    <li><a href="/docs">/docs</a> - API documentation</li>
                </ul>
            </body>
        </html>
        """)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "data_directory": str(DATA_DIR),
        "data_available": DATA_DIR.exists()
    }

@app.websocket("/ws/analysis")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time analysis status updates

    Sends status updates for each platform during analysis:
    - queued: Platform added to crawl queue
    - crawling: Currently crawling platform
    - analyzing: Processing and analyzing data
    - complete: Platform analysis finished
    - error: Platform crawl/analysis failed
    """
    await manager.connect(websocket)
    try:
        # Keep connection alive and listen for client messages
        while True:
            try:
                # Wait for client ping/pong to keep connection alive
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                # Echo back to confirm connection is alive
                await websocket.send_json({"type": "pong", "timestamp": datetime.now().isoformat()})
            except asyncio.TimeoutError:
                # Send keepalive ping
                await websocket.send_json({"type": "ping", "timestamp": datetime.now().isoformat()})
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("Client disconnected from WebSocket")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

@app.get("/config/status")
async def config_status():
    """Configuration status endpoint"""
    if config:
        available_apis = config.get_available_apis()
        missing_keys = config.validate_required_keys()

        return {
            "status": "loaded",
            "environment": config.ENVIRONMENT,
            "debug": config.DEBUG,
            "available_apis": available_apis,
            "missing_required_keys": missing_keys,
            "llm_service_available": LLM_SERVICE_AVAILABLE,
            "advanced_nlp_available": ADVANCED_NLP_AVAILABLE,
            "openai_configured": bool(config.OPENAI_API_KEY),
            "anthropic_configured": bool(config.ANTHROPIC_API_KEY),
            "huggingface_configured": bool(config.HUGGINGFACE_API_TOKEN)
        }
    else:
        return {
            "status": "not_loaded",
            "error": "Configuration not available",
            "llm_service_available": LLM_SERVICE_AVAILABLE,
            "advanced_nlp_available": ADVANCED_NLP_AVAILABLE
        }

@app.get("/platforms")
async def get_available_platforms():
    """Get list of available platforms with data"""
    
    if not DATA_DIR.exists():
        return {"error": "Data directory not found", "platforms": []}
    
    platforms = []
    
    for platform_dir in DATA_DIR.iterdir():
        if platform_dir.is_dir():
            csv_files = list(platform_dir.glob("*.csv"))
            platforms.append({
                "name": platform_dir.name,
                "data_files": len(csv_files),
                "available": len(csv_files) > 0
            })
    
    return {
        "platforms": platforms,
        "total_platforms": len(platforms),
        "data_directory": str(DATA_DIR)
    }

@app.post("/nlp-process")
async def process_nlp_input(request: dict):
    """
    🧠 Advanced NLP Processing Endpoint

    Process user input with advanced keyword extraction:
    - KeyBERT + Word2Vec semantic understanding
    - TextRank with Word2Vec enhancement
    - TF-IDF hybrid with domain-specific weighting
    - Named Entity Recognition (NER)
    - Dynamic Query Expansion
    """
    try:
        user_input = request.get('query', '')
        if not user_input:
            raise HTTPException(status_code=400, detail="Query is required")

        logger.info(f"🔍 Processing NLP input: {user_input[:50]}...")

        # Process with advanced NLP
        nlp_results = process_user_input(user_input)

        # Add processing metadata
        nlp_results['processing_metadata'] = {
            'advanced_nlp_available': ADVANCED_NLP_AVAILABLE,
            'processing_time': datetime.now().isoformat(),
            'input_length': len(user_input),
            'methods_used': ['KeyBERT', 'TextRank', 'TF-IDF Hybrid', 'NER', 'Query Expansion'] if ADVANCED_NLP_AVAILABLE else ['Fallback']
        }

        logger.info(f"✅ NLP processing completed. Confidence: {nlp_results['confidence_score']:.2f}")

        return {
            'status': 'success',
            'nlp_results': nlp_results,
            'recommendations': {
                'suggested_keywords': [kw[0] for kw in nlp_results['keywords']['combined'][:5]],
                'suggested_platforms': nlp_results['query_expansion'].get('suggested_platforms', ['facebook', 'instagram']),
                'industry_context': nlp_results['query_expansion'].get('industry_context'),
                'malaysian_context': nlp_results['query_expansion'].get('malaysian_context', [])
            }
        }

    except Exception as e:
        logger.error(f"❌ NLP processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"NLP processing failed: {str(e)}")

@app.post("/analyze")
async def analyze_data(request: AnalysisRequest):
    """
    Perform PERFECT analysis on selected platforms with:
    - Platform-optimized data collection
    - Smart comment sampling
    - Date range filtering
    - Analysis focus prioritization
    """

    logger.info(f"🔍 Starting PERFECT analysis for query: {request.query}")
    logger.info(f"📊 Platforms: {request.platforms}")
    logger.info(f"🎯 Analysis depth: {request.analysis_depth}")
    logger.info(f"🎯 Analysis focus: {request.analysis_focus}")
    logger.info(f"📅 Date range: {request.date_range}")
    logger.info(f"💬 Comment sampling: {request.comment_sampling}")

    # Get date range filter
    date_filter = get_date_range_filter(request)
    logger.info(f"📅 Filtering data from {date_filter['start_iso']} to {date_filter['end_iso']} ({date_filter['days']} days)")

    # Get analysis focus configuration
    focus_config = get_analysis_focus_config(request)
    logger.info(f"🎯 Analysis focus: {focus_config['description']}")

    # 🧠 Phase 1: Advanced NLP Processing & Keyword Extraction
    logger.info("🧠 Phase 1: Processing input with Advanced NLP...")
    nlp_results = process_user_input(request.query)

    # Extract enhanced keywords for better data collection
    enhanced_keywords = [kw[0] for kw in nlp_results['keywords']['combined'][:5]]
    suggested_platforms = nlp_results['query_expansion'].get('suggested_platforms', request.platforms)

    logger.info(f"🔑 Enhanced keywords extracted: {enhanced_keywords}")
    logger.info(f"📱 Suggested platforms: {suggested_platforms}")
    logger.info(f"🏭 Industry context: {nlp_results['query_expansion'].get('industry_context', 'General')}")
    logger.info(f"🇲🇾 Malaysian context: {nlp_results['query_expansion'].get('malaysian_context', [])}")

    # 🚀 Phase 2: Try Real-Time Crawling First (if Apify available)
    logger.info("🚀 Phase 2: Attempting real-time data collection with AI-powered keywords...")
    logger.info(f"📊 Crawling {len(request.platforms)} platforms in PARALLEL for maximum speed...")
    real_time_data = {}

    if APIFY_AVAILABLE:
        # 🤖 Initialize adapter with LLM service for AI keyword generation
        adapter = SimpleApifyAdapter(llm_service=llm_service if LLM_SERVICE_AVAILABLE else None)

        # 🎯 Determine dataset size (use dataset_size if provided, otherwise use max_results)
        effective_dataset_size = request.dataset_size if request.dataset_size else request.max_results

        # 🎯 ALWAYS use crawl strategy with comments (30:70 ratio)
        if request.use_crawl_strategy:
            logger.info(f"🎯 Using 30:70 Posts:Comments strategy with dataset size: {effective_dataset_size}")

            # Broadcast strategy status
            await manager.broadcast_status({
                "type": "system_status",
                "status": "calculating_strategy",
                "timestamp": datetime.now().isoformat(),
                "message": f"🎯 Calculating crawl strategy for {effective_dataset_size} results (30% posts + 70% comments)..."
            })

            start_time = time.time()

            try:
                # 🎯 Use new strategy-based crawling with comments
                strategy_result = await adapter.crawl_with_strategy(
                    platforms=request.platforms,
                    query=request.query,
                    dataset_size=effective_dataset_size,
                    analysis_type=request.analysis_focus
                )

                elapsed_time = time.time() - start_time
                logger.info(f"⚡ Strategy-based crawl completed in {elapsed_time:.2f} seconds!")

                if "error" in strategy_result:
                    logger.error(f"❌ Strategy crawl failed: {strategy_result['error']}")
                    raise Exception(strategy_result['error'])

                # Extract results
                real_time_data_dict = strategy_result.get("results", {})
                strategy_info = strategy_result.get("strategy", {})
                summary = strategy_result.get("summary", {})

                logger.info(f"📊 Strategy Summary:")
                logger.info(f"   Total Posts: {summary.get('total_posts', 0)}")
                logger.info(f"   Total Comments: {summary.get('total_comments', 0)}")
                logger.info(f"   Total Results: {summary.get('total_results', 0)}")

            except Exception as e:
                import traceback
                logger.error(f"❌ Strategy-based crawl failed: {e}")
                logger.error(f"❌ Full traceback:\n{traceback.format_exc()}")
                logger.warning(f"⚠️ Falling back to traditional AI crawling...")
                request.use_crawl_strategy = False  # Disable and fallback

        # Traditional AI-powered crawling (fallback only if strategy explicitly disabled)
        if not request.use_crawl_strategy:
            # Get platform-specific limits for first platform (use as default)
            default_limits = get_platform_limits(request, request.platforms[0])
            max_posts = default_limits["max_posts"]
            max_comments = default_limits["max_comments"]

            logger.info(f"🤖 Using AI-powered keyword generation for all platforms...")
            logger.info(f"📊 Default limits: {max_posts} posts, {max_comments} comments/post")

            # Broadcast AI keyword generation status
            await manager.broadcast_status({
                "type": "system_status",
                "status": "generating_keywords",
                "timestamp": datetime.now().isoformat(),
                "message": "🤖 AI generating platform-optimized keywords..."
            })

            start_time = time.time()

            try:
                # 🤖 Use AI-powered multi-platform crawling
                real_time_data_dict = await adapter.crawl_multi_platform_with_ai(
                    platforms=request.platforms,
                    query=request.query,
                    max_results=max_posts,
                    max_comments=max_comments,
                    comment_sampling=request.comment_sampling,
                    analysis_type=request.analysis_focus
                )

                elapsed_time = time.time() - start_time
                logger.info(f"⚡ AI-powered parallel crawl completed in {elapsed_time:.2f} seconds!")

            except Exception as e:
                logger.error(f"❌ AI-powered crawl failed: {e}")
                logger.warning(f"⚠️ Falling back to traditional crawling...")
                real_time_data_dict = {}

        # Process results and broadcast status (for both strategy and traditional)
        for platform, results in real_time_data_dict.items():
            if results:
                real_time_data[platform] = results
                logger.info(f"✅ Got {len(results)} AI-optimized results from {platform}")
                await manager.broadcast_status({
                    "type": "platform_status",
                    "platform": platform,
                    "status": "analyzing",
                    "timestamp": datetime.now().isoformat(),
                    "data_points": len(results),
                    "message": f"Collected {len(results)} records from {platform} using AI keywords, now analyzing..."
                })
            else:
                logger.warning(f"⚠️ No results from {platform}")
                await manager.broadcast_status({
                    "type": "platform_status",
                    "platform": platform,
                    "status": "complete",
                    "timestamp": datetime.now().isoformat(),
                    "data_points": 0,
                    "message": f"No data found for {platform}"
                })

    # Fallback: If APIFY not available or no results, use traditional crawling
    if not APIFY_AVAILABLE or not real_time_data:
        if not APIFY_AVAILABLE:
            logger.warning("⚠️ Apify not available, using traditional crawling...")
        else:
            logger.warning("⚠️ No results from AI crawling, trying traditional crawling...")

        crawl_tasks = []
        platform_names = []

        for platform in request.platforms:
            # ✅ Get platform-specific limits
            limits = get_platform_limits(request, platform)
            max_posts = limits["max_posts"]
            max_comments = limits["max_comments"]

            logger.info(f"⏳ Queuing {platform} for parallel crawl...")
            logger.info(f"   📊 {platform}: {max_posts} posts, {max_comments} comments/post")

            # Broadcast queued status
            await manager.broadcast_status({
                "type": "platform_status",
                "platform": platform,
                "status": "queued",
                "timestamp": datetime.now().isoformat(),
                "message": f"Platform {platform} queued ({max_posts} posts, {max_comments} comments)",
                "config": {"max_posts": max_posts, "max_comments": max_comments}
            })

            # ✅ Pass platform-specific limits AND comment_sampling to crawl function
            task = try_real_time_crawl(platform, request.query, max_posts, max_comments, request.comment_sampling)
            crawl_tasks.append(task)
            platform_names.append(platform)

        # Execute ALL crawls in PARALLEL using asyncio.gather()
        logger.info(f"🚀 Starting PARALLEL crawl of {len(crawl_tasks)} platforms...")

        # Broadcast crawling started for all platforms
        for platform in platform_names:
            await manager.broadcast_status({
                "type": "platform_status",
                "platform": platform,
                "status": "crawling",
                "timestamp": datetime.now().isoformat(),
                "message": f"Crawling {platform}..."
            })

        start_time = time.time()

        try:
            # gather() runs all tasks concurrently and waits for all to complete
            results_list = await asyncio.gather(*crawl_tasks, return_exceptions=True)

            elapsed_time = time.time() - start_time
            logger.info(f"⚡ Parallel crawl completed in {elapsed_time:.2f} seconds!")

            # Process results and broadcast status
            for platform, results in zip(platform_names, results_list):
                if isinstance(results, Exception):
                    logger.error(f"❌ Real-time crawl error for {platform}: {results}")
                    await manager.broadcast_status({
                        "type": "platform_status",
                        "platform": platform,
                        "status": "error",
                        "timestamp": datetime.now().isoformat(),
                        "message": f"Error crawling {platform}: {str(results)[:100]}"
                    })
                elif results:
                    real_time_data[platform] = results
                    logger.info(f"✅ Got {len(results)} real-time results from {platform}")
                    await manager.broadcast_status({
                        "type": "platform_status",
                        "platform": platform,
                        "status": "analyzing",
                        "timestamp": datetime.now().isoformat(),
                        "data_points": len(results),
                        "message": f"Collected {len(results)} records from {platform}, now analyzing..."
                    })
                else:
                    logger.warning(f"⚠️ No results from {platform}")
                    await manager.broadcast_status({
                        "type": "platform_status",
                        "platform": platform,
                        "status": "complete",
                        "timestamp": datetime.now().isoformat(),
                        "data_points": 0,
                        "message": f"No data found for {platform}"
                    })

        except Exception as e2:
            logger.error(f"❌ Fallback parallel crawl also failed: {e2}")
            # Broadcast error for all platforms
            for platform in platform_names:
                await manager.broadcast_status({
                    "type": "platform_status",
                    "platform": platform,
                    "status": "error",
                    "timestamp": datetime.now().isoformat(),
                    "message": f"Crawl system error: {str(e2)[:100]}"
                })

    # 📂 Phase 3: Collect data from each platform (real-time or existing)
    logger.info("📂 Phase 3: Loading platform data...")
    platform_data = {}

    for platform in request.platforms:
        logger.info(f"📱 Collecting data from {platform}...")

        # Use real-time data if available, otherwise load from files
        if platform in real_time_data:
            logger.info(f"✅ Using real-time crawled data for {platform}")

            try:
                # 📂 STEP 1: Build DataFrame from RAW data
                # Prefer the legacy data/raw/{PLATFORM}.csv if it exists (compat with older flow),
                # otherwise use the in-memory records returned by the real-time crawler
                # (this is the only source for adapters that don't write data/raw/, e.g. news/Scrapling).
                import pandas as pd
                from pathlib import Path
                raw_dir = Path("data/raw")
                raw_filename = f"{platform.upper()}.csv"
                raw_filepath = raw_dir / raw_filename

                if raw_filepath.exists():
                    logger.info(f"📂 Reading RAW data from: {raw_filepath}")
                    df = pd.read_csv(raw_filepath)
                    logger.info(f"📊 Loaded {len(df)} records from RAW file")
                else:
                    logger.info(f"📂 No legacy RAW file at {raw_filepath} — using in-memory crawled records")
                    df = pd.DataFrame(real_time_data[platform])
                    logger.info(f"📊 Loaded {len(df)} records from real-time crawl (in-memory)")

                # Count posts and comments
                posts_count = len(df[df['Type'] == 'post']) if 'Type' in df.columns else len(df)
                comments_count = len(df[df['Type'] == 'comment']) if 'Type' in df.columns else 0
                logger.info(f"📊 RAW data: {posts_count} posts + {comments_count} comments")

                # 🤖 STEP 2: Process with sentiment/emotion analysis
                logger.info(f"🤖 Running sentiment & emotion analysis...")
                processed_insights = process_platform_data(df, platform, request.query)
                logger.info(f"✅ Sentiment analysis completed for {platform}")

                # 💾 STEP 3: Save analyzed data with unique timestamp
                try:
                    analyzed_dir = Path("data/analyzed")
                    analyzed_dir.mkdir(parents=True, exist_ok=True)

                    # Unique filename with timestamp: Sentiment_Emotion_FACEBOOK_20260211_125816.csv
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    analyzed_filename = f"Sentiment_Emotion_{platform.upper()}_{timestamp}.csv"
                    analyzed_filepath = analyzed_dir / analyzed_filename

                    # Save DataFrame with all sentiment/emotion columns
                    df.to_csv(analyzed_filepath, index=False, encoding='utf-8')
                    logger.info(f"💾 ANALYZED DATA saved: {analyzed_filepath}")
                    logger.info(f"💾 Saved {len(df)} rows with {len(df.columns)} columns")
                    logger.info(f"📊 This includes sentiment/emotion analysis for all posts and comments")

                    # Verify sentiment columns exist
                    if 'sentiment_label' in df.columns:
                        sentiment_dist = df[df['Type'] == 'post']['sentiment_label'].value_counts() if 'Type' in df.columns else df['sentiment_label'].value_counts()
                        logger.info(f"✅ Sentiment distribution: {sentiment_dist.to_dict()}")
                    else:
                        logger.warning(f"⚠️ sentiment_label column NOT FOUND in DataFrame!")
                except Exception as save_error:
                    logger.error(f"❌ Could not save analyzed CSV for {platform}: {save_error}")
                    import traceback
                    logger.error(traceback.format_exc())

            except Exception as e:
                logger.error(f"❌ Error processing {platform} data: {e}")
                logger.exception(e)  # Print full traceback
                processed_insights = {"error": str(e)}

            # Convert real-time data to the expected format
            data = {
                "data_points": len(real_time_data[platform]),
                "data": real_time_data[platform],
                "processed_insights": processed_insights,
                "source": "real_time_crawl",
                "timestamp": datetime.now().isoformat()
            }
        else:
            logger.info(f"📂 Loading existing data for {platform}")
            data = load_platform_data(platform, request.query, request.max_results, nlp_results)

        platform_data[platform] = data
    
    # Perform cross-platform analysis
    total_data_points = sum(data.get("data_points", 0) for data in platform_data.values())

    # Calculate overall sentiment
    sentiment_scores = []
    total_engagement = 0
    all_topics = []
    all_data_for_trends = []

    for platform, data in platform_data.items():
        if "processed_insights" in data:
            insights = data["processed_insights"]

            # Try to get sentiment score from multiple sources
            sentiment_score = None
            if "original_sentiment_score" in insights:
                sentiment_score = insights["original_sentiment_score"]
            elif "custom_sentiment" in insights and "confidence" in insights["custom_sentiment"]:
                # Convert sentiment label to score
                primary = insights["custom_sentiment"]["primary_sentiment"].lower()
                if primary == "positive":
                    sentiment_score = 0.8
                elif primary == "negative":
                    sentiment_score = 0.2
                else:  # neutral
                    sentiment_score = 0.5
            elif "sentiment_score" in insights:
                sentiment_score = insights["sentiment_score"]

            if sentiment_score is not None:
                sentiment_scores.append(sentiment_score)

            if "total_engagement" in insights:
                total_engagement += insights["total_engagement"]

            if "trending_topics" in insights:
                all_topics.extend(insights["trending_topics"])

        # Collect all data for sentiment trends analysis
        if "data" in data:
            all_data_for_trends.extend(data["data"])
    
    # Calculate overall metrics
    avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0.5

    # Get top trending topics across platforms with smart contextual awareness
    from collections import Counter

    query_lower = request.query.lower()

    # Define category-specific terms and their related topics (same as platform level)
    category_mappings = {
        'fashion': {
            'terms': ['tudung', 'hijab', 'baju', 'dress', 'fashion', 'style', 'pakaian', 'busana', 'outfit', 'trend'],
            'topics': ['fashion', 'style', 'trend', 'popular', 'cantik', 'murah', 'kualiti', 'brand', 'design', 'warna']
        },
        'political': {
            'terms': ['perdana', 'menteri', 'pas', 'pru', 'politik', 'kerajaan', 'parti', 'pilihan', 'raya', 'rakyat', 'negara', 'pemimpin'],
            'topics': ['politik', 'kerajaan', 'rakyat', 'malaysia', 'kepimpinan', 'parti', 'demokrasi', 'pilihan_raya', 'sokongan', 'negara']
        },
        'technology': {
            'terms': ['iphone', 'samsung', 'xiaomi', 'phone', 'smartphone', 'gadget', 'tech', 'camera', 'spec', 'performance'],
            'topics': ['teknologi', 'kamera', 'performance', 'harga', 'spec', 'kualiti', 'bagus', 'terbaik', 'recommended', 'value']
        },
        'food': {
            'terms': ['makanan', 'makan', 'sedap', 'restaurant', 'cafe', 'food', 'rasa', 'menu', 'masak', 'resepi'],
            'topics': ['makanan', 'sedap', 'rasa', 'restaurant', 'menu', 'harga', 'service', 'recommended', 'popular', 'best']
        },
        'beauty': {
            'terms': ['makeup', 'skincare', 'beauty', 'cosmetic', 'lipstick', 'foundation', 'serum', 'cleanser', 'moisturizer'],
            'topics': ['beauty', 'makeup', 'skincare', 'cantik', 'brand', 'kualiti', 'harga', 'recommended', 'popular', 'best']
        },
        'health': {
            'terms': ['kesihatan', 'health', 'vitamin', 'supplement', 'ubat', 'medicine', 'hospital', 'doktor', 'rawatan'],
            'topics': ['kesihatan', 'health', 'rawatan', 'ubat', 'supplement', 'doktor', 'hospital', 'bagus', 'berkesan', 'recommended']
        }
    }

    # Detect query category
    detected_category = None
    for category, config in category_mappings.items():
        if any(term in query_lower for term in config['terms']):
            detected_category = category
            break

    if detected_category:
        # Generate contextual topics based on detected category
        base_topics = category_mappings[detected_category]['topics'].copy()

        # Add specific query keywords
        query_words = [word.strip('.,!?()[]{}":;').lower() for word in query_lower.split()
                      if len(word) > 3 and word not in ['yang', 'dan', 'untuk', 'dengan', 'adalah', 'dari', 'pada', 'dalam']]

        # Prioritize query words
        top_topics = []
        for word in query_words:
            if word not in top_topics:
                top_topics.append(word)

        # Add category-specific topics
        for topic in base_topics:
            if topic not in top_topics and len(top_topics) < 5:
                top_topics.append(topic)

        top_topics = top_topics[:5]
    else:
        # Fallback: use actual topic counts from platform data
        topic_counts = Counter(all_topics)
        top_topics = [topic for topic, count in topic_counts.most_common(5)]

    # Generate sentiment trends analysis
    sentiment_trends = None
    if all_data_for_trends:
        import pandas as pd
        try:
            # Create DataFrame from all collected data
            df = pd.DataFrame(all_data_for_trends)

            # Generate synthetic dates if dates are missing
            if 'Date' not in df.columns or df['Date'].isna().all():
                logger.info("📅 Generating synthetic dates for sentiment trends...")
                # Generate dates over the last 30 days
                from datetime import timedelta
                end_date = datetime.now()
                start_date = end_date - timedelta(days=29)

                # Distribute data points across the date range
                date_range = pd.date_range(start=start_date, end=end_date, freq='D')
                df['Date'] = pd.Series(date_range).sample(n=len(df), replace=True).reset_index(drop=True)

            # Analyze sentiment trends
            sentiment_trends = analyze_sentiment_trends_over_time(df)
            logger.info(f"✅ Sentiment trends analysis completed: {len(sentiment_trends.get('time_series', []))} data points")

        except Exception as e:
            logger.error(f"❌ Error generating sentiment trends: {e}")
            sentiment_trends = {"error": f"Could not generate sentiment trends: {str(e)}"}

    # Calculate statistical confidence based on data volume
    confidence_level = get_statistical_confidence(total_data_points)
    reliability_score = get_reliability_score(total_data_points)
    
    # Generate insights based on analysis type
    key_insights = []
    recommendations = []
    
    if request.analysis_type == "social_listening":
        key_insights.extend([
            f"Analyzed {total_data_points:,} data points across {len(request.platforms)} platforms",
            f"Statistical confidence: {reliability_score['level']} ({reliability_score['score']:.0%})",
            f"Overall sentiment: {'Positive' if avg_sentiment > 0.6 else 'Negative' if avg_sentiment < 0.4 else 'Neutral'} (±{reliability_score['margin_of_error']})",
            f"Total engagement: {total_engagement:,} interactions",
            f"Top trending topics identified: {len(top_topics)} topics"
        ])

        # Data-size appropriate recommendations
        if total_data_points >= 10000:
            recommendations.extend([
                "High confidence insights - suitable for strategic business decisions",
                "Implement automated sentiment monitoring with these reliable baselines",
                "Use insights for executive reporting and market positioning",
                "Consider expanding analysis to additional platforms for comprehensive coverage"
            ])
        elif total_data_points >= 5000:
            recommendations.extend([
                "Good confidence level - suitable for tactical marketing decisions",
                "Monitor sentiment trends for brand reputation management",
                "Engage with high-engagement content to build community",
                "Consider increasing sample size for strategic decisions"
            ])
        elif total_data_points >= 1000:
            recommendations.extend([
                "Moderate confidence - good for trend monitoring and preliminary insights",
                "Increase data collection period for more reliable insights",
                "Focus on high-engagement platforms for better signal-to-noise ratio",
                "Use as directional guidance rather than definitive conclusions"
            ])
        else:
            recommendations.extend([
                "Limited sample size - use for preliminary analysis only",
                "Significantly increase data collection for reliable insights",
                "Consider this a pilot study requiring validation with larger datasets",
                "Combine with qualitative research for comprehensive understanding"
            ])
    
    elif request.analysis_type == "sme_insights":
        key_insights.extend([
            f"Market analysis completed across {len(request.platforms)} platforms",
            f"Customer sentiment analysis: {avg_sentiment:.2f} score",
            f"Market engagement level: {total_engagement:,} total interactions",
            "Competitive landscape insights generated"
        ])
        
        recommendations.extend([
            "Leverage positive customer feedback in marketing campaigns",
            "Address negative sentiment areas for product improvement",
            "Consider expanding presence on high-engagement platforms"
        ])
    
    # 🤖 Phase 2: LLM-Powered Intelligent Analysis
    llm_analysis = None
    if LLM_SERVICE_AVAILABLE and llm_service:
        try:
            logger.info("🤖 Phase 2: Running LLM-powered intelligent analysis...")

            # Prepare data for LLM analysis
            all_social_data = []
            for platform, data in platform_data.items():
                if "data" in data:
                    for post in data["data"][:5]:  # Sample 5 posts per platform for LLM
                        post_data = dict(post)
                        post_data["Platform"] = platform
                        all_social_data.append(post_data)

            # Run LLM analysis
            llm_analysis = await llm_service.analyze_social_media_data(
                query=request.query,
                social_data=all_social_data,
                platforms=request.platforms
            )

            # Enhance insights with LLM analysis
            if llm_analysis and "key_insights" in llm_analysis:
                key_insights.extend(llm_analysis["key_insights"])

            if llm_analysis and "recommendations" in llm_analysis:
                recommendations.extend(llm_analysis["recommendations"])

            logger.info(f"✅ LLM analysis completed using {llm_analysis.get('llm_used', 'unknown')} model")

        except Exception as e:
            logger.error(f"❌ LLM analysis failed: {str(e)}")
            llm_analysis = {"error": f"LLM analysis failed: {str(e)}"}

    # Final analysis results
    analysis_results = {
        "analysis_type": request.analysis_type,
        "query": request.query,
        "platforms_analyzed": request.platforms,
        "total_data_points": total_data_points,
        "analysis_timestamp": datetime.now().isoformat(),
        "overall_metrics": {
            "sentiment_score": round(avg_sentiment, 3),
            "sentiment_label": "positive" if avg_sentiment > 0.6 else "negative" if avg_sentiment < 0.4 else "neutral",
            "total_engagement": total_engagement,
            "trending_topics": top_topics[:5],
            "confidence_level": confidence_level,
            "reliability": reliability_score,
            "data_quality": {
                "sample_size": total_data_points,
                "platforms_analyzed": len(request.platforms),
                "statistical_significance": "high" if total_data_points >= 5000 else "moderate" if total_data_points >= 1000 else "low"
            }
        },
        "platform_breakdown": platform_data,
        "sentiment_trends": sentiment_trends,
        "key_insights": key_insights,
        "recommendations": recommendations,
        "llm_analysis": llm_analysis,  # Include LLM analysis results
        "status": "completed"
    }

    # Add sentiment trends to the first platform's processed_insights for frontend compatibility
    if sentiment_trends and not sentiment_trends.get("error"):
        for platform_name, platform_info in platform_data.items():
            if "processed_insights" in platform_info:
                platform_info["processed_insights"]["sentiment_trends"] = sentiment_trends
                break
    
    logger.info(f"✅ Analysis completed successfully!")

    # Broadcast completion status for all platforms
    for platform in request.platforms:
        await manager.broadcast_status({
            "type": "platform_status",
            "platform": platform,
            "status": "complete",
            "timestamp": datetime.now().isoformat(),
            "message": f"Analysis complete for {platform}"
        })

    # Broadcast overall completion
    await manager.broadcast_status({
        "type": "analysis_complete",
        "timestamp": datetime.now().isoformat(),
        "total_data_points": total_data_points,
        "platforms": request.platforms,
        "message": f"Analysis completed! Collected {total_data_points} data points across {len(request.platforms)} platforms"
    })

    # 📊 Phase 4: Generate Professional Reports
    logger.info("📊 Phase 4: Generating professional reports...")
    report_paths = {}
    try:
        import sys
        from pathlib import Path
        # Add parent directory to path to import backend module
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from backend.services.report_generator import ProfessionalReportGenerator

        # Prepare analysis data for report generation
        # Calculate sentiment percentages from INDIVIDUAL POSTS, not platform averages
        all_post_sentiments = []
        for post in all_data_for_trends:
            # Try to get sentiment_score from post
            if 'sentiment_score' in post and post['sentiment_score'] is not None:
                score = float(post['sentiment_score'])
                if score > 0:  # Only include valid scores
                    all_post_sentiments.append(score)
            elif 'Sentiment' in post:
                # Map sentiment label to score
                sentiment_label = str(post['Sentiment']).lower()
                if sentiment_label == 'positive':
                    all_post_sentiments.append(0.8)
                elif sentiment_label == 'negative':
                    all_post_sentiments.append(0.2)
                elif sentiment_label == 'neutral':
                    all_post_sentiments.append(0.5)

        # Calculate percentages from individual posts
        if all_post_sentiments:
            positive_count = sum(1 for s in all_post_sentiments if s > 0.6)
            neutral_count = sum(1 for s in all_post_sentiments if 0.4 <= s <= 0.6)
            negative_count = sum(1 for s in all_post_sentiments if s < 0.4)
            total_count = len(all_post_sentiments)

            positive_ratio = (positive_count / total_count * 100)
            neutral_ratio = (neutral_count / total_count * 100)
            negative_ratio = (negative_count / total_count * 100)
        else:
            # Fallback to platform averages if no individual post sentiments
            positive_ratio = (sum(1 for s in sentiment_scores if s > 0.6) / len(sentiment_scores) * 100) if sentiment_scores else 0
            neutral_ratio = (sum(1 for s in sentiment_scores if 0.4 <= s <= 0.6) / len(sentiment_scores) * 100) if sentiment_scores else 0
            negative_ratio = (sum(1 for s in sentiment_scores if s < 0.4) / len(sentiment_scores) * 100) if sentiment_scores else 0

        report_data = {
            'raw_data': all_data_for_trends,  # All posts/comments
            'sentiment_analysis': {
                'positive_ratio': positive_ratio,
                'neutral_ratio': neutral_ratio,
                'negative_ratio': negative_ratio,
            },
            'platform_breakdown': {
                platform: {
                    'total': data.get('data_points', 0),
                    'avg_sentiment': data.get('processed_insights', {}).get('sentiment_score', 0),
                    'total_engagement': data.get('processed_insights', {}).get('total_engagement', 0)
                }
                for platform, data in platform_data.items()
            },
            'insights': {
                'key_insights': key_insights
            },
            'critical_issues': [],  # TODO: Extract from negative posts
            'recommendations': recommendations
        }

        # 💾 SAVE COMBINED DATA: All platforms + sentiment + emotion + engagement
        if all_data_for_trends:
            try:
                combined_dir = Path("data/combined")
                combined_dir.mkdir(parents=True, exist_ok=True)

                # Create DataFrame from all platforms data
                combined_df = pd.DataFrame(all_data_for_trends)

                # Unique filename with timestamp
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                platforms_str = "_".join(sorted(request.platforms))[:50]  # Limit length
                combined_filename = f"Combined_{platforms_str}_{timestamp}.csv"
                combined_filepath = combined_dir / combined_filename

                # Save combined CSV
                combined_df.to_csv(combined_filepath, index=False, encoding='utf-8')

                logger.info(f"💾 COMBINED DATA saved: {combined_filepath}")
                logger.info(f"📊 {len(combined_df)} total records from {len(request.platforms)} platforms")
                logger.info(f"📋 Platforms: {', '.join(request.platforms)}")

            except Exception as e:
                logger.error(f"❌ Error saving combined data: {e}")

        # Generate all reports
        report_gen = ProfessionalReportGenerator(output_dir="reports")
        report_paths = report_gen.generate_all_reports(
            analysis_data=report_data,
            query=request.query,
            analysis_type=request.analysis_type
        )

        logger.info(f"✅ Professional reports generated: {len(report_paths)} files")

        # Broadcast report generation status
        await manager.broadcast_status({
            "type": "reports_generated",
            "timestamp": datetime.now().isoformat(),
            "report_count": len(report_paths),
            "message": f"Generated {len(report_paths)} professional reports"
        })

    except Exception as e:
        logger.error(f"⚠️ Report generation failed: {e}")
        report_paths = {"error": str(e)}

    # Add report paths to analysis results
    analysis_results['report_paths'] = report_paths

    # Clean NaN values before returning JSON response
    cleaned_results = clean_nan_values(analysis_results)
    return cleaned_results

@app.get("/sample-data/{platform}")
async def get_sample_data(platform: str, limit: int = 10):
    """Get sample data from a specific platform"""
    
    data = load_platform_data(platform, "", limit)
    
    if "error" in data:
        raise HTTPException(status_code=404, detail=data["error"])
    
    # Return just the sample data
    sample_data = data.get("data", [])[:limit]
    
    return {
        "platform": platform,
        "sample_data": sample_data,
        "total_available": data.get("total_available", 0),
        "source_file": data.get("source_file", "unknown")
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
