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

from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect, UploadFile, File, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional, Set
import shutil
import asyncio
import logging
import re
import json
import time
import uuid
from datetime import datetime
from pathlib import Path
import pandas as pd
import numpy as np
import math
import os
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import torch
import warnings

# Suppress tokenizer length warnings for manual truncation
logging.getLogger("transformers.tokenization_utils_base").setLevel(logging.ERROR)
warnings.filterwarnings("ignore", message="Token indices sequence length is longer than")

# Load environment variables from .env (APIFY_API_TOKEN, SERPAPI_KEY, etc.)
try:
    from dotenv import load_dotenv
    _env_path = Path(__file__).resolve().parent.parent / ".env"
    load_dotenv(_env_path)
except ImportError:
    pass

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
_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT))
sys.path.insert(0, str(_REPO_ROOT / "backend" / "data_crawlers"))
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

# 🎯 TASK TRACKING SYSTEM - Store long-running analysis tasks
# This allows frontend to poll status instead of waiting for completion
analysis_tasks = {}  # task_id -> {"status": "running|completed|failed", "progress": {...}, "result": {...}, "error": str}

# 🎯 TASK LOG SYSTEM — captures real-time logs per task
_active_task_id: Optional[str] = None   # which task is currently running
MAX_TASK_LOGS = 120                      # keep last N log lines per task

def task_log(task_id: str, message: str):
    """Append a log line to a specific task's log buffer."""
    if task_id and task_id in analysis_tasks:
        logs = analysis_tasks[task_id].setdefault("logs", [])
        ts = datetime.now().strftime("%H:%M:%S")
        logs.append(f"[{ts}] {message}")
        if len(logs) > MAX_TASK_LOGS:
            logs.pop(0)

class TaskLogHandler(logging.Handler):
    """Custom logging handler that mirrors all log records into the active task's log buffer."""
    IMPORTANT_PREFIXES = (
        "Got ", "finished collecting", "Status: SUCCEED", "Status: RUNNING",
        "Batch ", "handling:", "ACTOR:", "runId:", "✅", "❌", "⚠️", "🕷️",
        "📘", "🐦", "🎵", "🎬", "📸", "📊", "📦", "📅", "Phase", "crawl", "Crawl",
        "sentiment", "Sentiment", "emotion", "Emotion", "keyword", "Keyword",
        "Apify", "apify", "strategy", "Strategy", "posts", "comments", "records",
        "merged", "Date filter",
    )

    def emit(self, record: logging.LogRecord):
        global _active_task_id
        if not _active_task_id:
            return
        msg = self.format(record)
        # Strip logger name prefix for cleaner display
        if " — " in msg:
            msg = msg.split(" — ", 1)[-1]
        # Only forward relevant/interesting lines (skip low-level noise)
        if any(p in msg for p in self.IMPORTANT_PREFIXES):
            task_log(_active_task_id, msg)

# Attach the handler to the root logger so it captures everything
_task_log_handler = TaskLogHandler()
_task_log_handler.setLevel(logging.INFO)
logging.getLogger().addHandler(_task_log_handler)

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

# Mount web_backend/static/ for KDEBWM dashboard and other tool pages
backend_static_path = Path(__file__).parent / "static"
if backend_static_path.exists():
    app.mount("/static", StaticFiles(directory=str(backend_static_path)), name="static")
else:
    backend_static_path.mkdir(parents=True, exist_ok=True)
    app.mount("/static", StaticFiles(directory=str(backend_static_path)), name="static")

# Mount web_frontend/ for legacy static files
frontend_static_path = Path(__file__).parent.parent / "web_frontend"
if frontend_static_path.exists():
    app.mount("/frontend", StaticFiles(directory=str(frontend_static_path)), name="frontend")

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
sentiment_tokenizers = {} # Dictionary to hold tokenizers for truncation
emotion_pipeline = None
emotion_tokenizer = None
batch_processor = None
MODEL_SAFE_MAX_TOKENS = 384  # Conservative limit avoids 512/514 position-embedding errors

def _safe_model_text(value: Any) -> str:
    """Normalize crawler/CSV values before sending them to language models."""
    try:
        if value is None or pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass

    text = str(value).strip()
    if text.lower() in {"", "nan", "none", "null"}:
        return ""
    return text

def _truncate_for_model(text: str, tokenizer=None, max_tokens: int = MODEL_SAFE_MAX_TOKENS) -> str:
    """Token-level truncation with a safe fallback for all Transformer models."""
    text = _safe_model_text(text)
    if not text:
        return ""
    try:
        if tokenizer:
            encoded = tokenizer.encode(
                text,
                add_special_tokens=False,
                truncation=True,
                max_length=max_tokens,
            )
            return tokenizer.decode(encoded, skip_special_tokens=True).strip()
    except Exception as te:
        logger.warning(f"⚠️ Token truncation failed: {te}")
    return text[:1500]

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

    # 🌐 DIRECT URL CRAWL MODE
    crawl_mode: str = "keyword"  # "keyword" or "direct_url"
    direct_urls: Optional[List[str]] = None  # e.g. ["https://facebook.com/PASJohor", "https://instagram.com/pasjohor"]
    direct_url_target: str = "auto"  # auto | page | post — post = keep full post + all comments (WhatsApp batch)
    comment_target_per_post: Optional[int] = None  # Post URL Batch: e.g. 3000 comments per post (multi-pass)
    multipass_comments: bool = True  # Run multiple Apify passes with dedupe (Facebook)
    include_nested_comments: bool = True  # Include reply threads in comment crawl

    # 📁 PROJECT STORAGE — promotes combined CSV to data/projects/{category}/{id}/
    project_id: Optional[str] = None  # e.g. "pas_break_2026", "smebank"
    processing: Optional[str] = None  # on-prem-nemotron | cloud-openai | cloud-super | rule-based
    multimodal: bool = False  # Enables media→text routing for runs that use the external router

    # 🔀 UNIFIED DATA PLATFORM — crawl + upload + external feeds
    data_source_mode: str = "social_crawl"  # social_crawl | upload | feed | hybrid
    upload_ids: Optional[List[str]] = None
    feed_ids: Optional[List[str]] = None
    dataset_type: Optional[str] = "generic_csv"
    skip_crawl: bool = False

class CreateProjectRequest(BaseModel):
    name: str
    client: str = ""
    category: str = "commercial"
    master_prefix: Optional[str] = None
    project_id: Optional[str] = None
    default_keywords: Optional[List[str]] = None

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
    global sentiment_pipelines, sentiment_tokenizers, emotion_pipeline, emotion_tokenizer, batch_processor

    try:
        logger.info("🤖 Initializing multilingual sentiment models...")

        # 🌍 Initialize MULTIPLE sentiment models for different languages
        for lang, model_name in SENTIMENT_MODELS.items():
            try:
                logger.info(f"📊 Loading {lang} sentiment model: {model_name}")

                # Load tokenizer for proper truncation
                try:
                    sentiment_tokenizers[lang] = AutoTokenizer.from_pretrained(
                        model_name,
                        token=HF_TOKEN if lang == 'malay' else None,
                        model_max_length=512
                    )
                except Exception as te:
                    logger.warning(f"⚠️ Failed to load tokenizer for {lang}: {te}")

                # Special handling for different models
                if lang == 'multilingual':
                    # nlptown model returns 1-5 stars, need different handling
                    sentiment_pipelines[lang] = pipeline(
                        "text-classification",
                        model=model_name,
                        tokenizer=sentiment_tokenizers.get(lang),
                        top_k=None
                    )
                else:
                    sentiment_pipelines[lang] = pipeline(
                        "text-classification",
                        model=model_name,
                        tokenizer=sentiment_tokenizers.get(lang),
                        token=HF_TOKEN if lang == 'malay' else None,  # Only Malay model needs token
                        top_k=None  # Return all scores
                    )
                logger.info(f"✅ {lang.capitalize()} sentiment model loaded!")
            except Exception as e:
                logger.warning(f"⚠️ Failed to load {lang} model: {e}")

        # Ensure at least Malay model is loaded
        if 'malay' not in sentiment_pipelines:
            raise Exception("Critical: Malay sentiment model failed to load!")

        logger.info(f"✅ Loaded {len(sentiment_pipelines)} sentiment models: {list(sentiment_pipelines.keys())}")

        # Initialize emotion model (rmtariq/multilingual-emotion-classifier)
        # NOTE: This is a SentencePiece (XLM-R) model. Converting its slow tokenizer
        # to a "fast" (Rust) tokenizer can segfault on some setups, killing the whole
        # process. Force use_fast=False to skip the conversion, and make the entire
        # emotion init non-fatal — emotion analysis has a graceful fallback if missing.
        logger.info(f"😊 Loading emotion model: {EMOTION_MODEL}")
        try:
            try:
                emotion_tokenizer = AutoTokenizer.from_pretrained(
                    EMOTION_MODEL,
                    token=HF_TOKEN,
                    model_max_length=512,
                    use_fast=False
                )
            except Exception as te:
                logger.warning(f"⚠️ Failed to load emotion tokenizer: {te}")
                emotion_tokenizer = None

            emotion_pipeline = pipeline(
                "text-classification",
                model=EMOTION_MODEL,
                tokenizer=emotion_tokenizer or EMOTION_MODEL,
                token=HF_TOKEN,
                top_k=None  # Return all scores
            )
            logger.info("✅ Emotion model loaded successfully!")
        except Exception as ee:
            emotion_pipeline = None
            logger.warning(f"⚠️ Emotion model unavailable — continuing without it: {ee}")

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
        text = _safe_model_text(text)
        if not text:
            return {
                "sentiment": "neutral",
                "confidence": 0.5,
                "scores": {"positive": 0.33, "neutral": 0.34, "negative": 0.33},
                "model": "empty_text_fallback",
                "detected_language": "unknown",
                "demographic": "Unknown"
            }
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

        tokenizer = sentiment_tokenizers.get(detected_model_key)
        truncated_text = _truncate_for_model(text, tokenizer)

        # 🤖 STEP 2: Get predictions from appropriate model (force token-level truncation)
        try:
            results = sentiment_pipeline(
                truncated_text,
                truncation=True,
                max_length=MODEL_SAFE_MAX_TOKENS,
            )
        except TypeError:
            # Older pipeline signature fallback
            results = sentiment_pipeline(_truncate_for_model(truncated_text, tokenizer, 256))

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
        text = _safe_model_text(text)
        if not text:
            return {
                "primary_emotion": "neutral",
                "confidence": 0.5,
                "emotions": {"joy": 0.2, "sadness": 0.2, "anger": 0.2, "fear": 0.2, "neutral": 0.2},
                "model": "empty_text_fallback"
            }

        truncated_text = _truncate_for_model(text, emotion_tokenizer)

        # Get predictions from custom emotion model (force token-level truncation)
        try:
            results = emotion_pipeline(
                truncated_text,
                truncation=True,
                max_length=MODEL_SAFE_MAX_TOKENS,
            )
        except TypeError:
            results = emotion_pipeline(_truncate_for_model(truncated_text, emotion_tokenizer, 256))

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

    text = _safe_model_text(text)
    if not text:
        return "malay"

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
        return "multilingual"  # Bilingual or unclear

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
    elif request.date_range in ("180days", "6months"):
        start_date = end_date - timedelta(days=180)
    elif request.date_range in ("365days", "1year"):
        start_date = end_date - timedelta(days=365)
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
    elif request.date_range in ("180days", "6months"):
        start_date = end_date - timedelta(days=180)
        days = 180
    elif request.date_range in ("365days", "1year"):
        start_date = end_date - timedelta(days=365)
        days = 365
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


def load_merged_platform_crawl_data(
    platform: str,
    in_memory_records: Optional[List[Dict[str, Any]]] = None,
    session_started_at: Optional[float] = None,
) -> pd.DataFrame:
    """
    Merge all crawl CSVs for a platform from the current session.
    Multi-keyword crawls save one file per keyword — must merge, not take latest only.
    """
    from backend.utils.crawl_records import flatten_crawl_records, parse_crawl_dates

    platform_lower = platform.lower()
    frames: List[pd.DataFrame] = []
    files_loaded = 0

    if in_memory_records:
        try:
            flat_records = flatten_crawl_records(in_memory_records)
            mem_df = pd.DataFrame(flat_records)
            if not mem_df.empty:
                frames.append(mem_df)
        except Exception as e:
            logger.warning(f"⚠️ Could not use in-memory crawl data for {platform}: {e}")

    smart_dir = Path("data/smart_crawlers") / platform_lower
    if smart_dir.exists():
        csv_files = list(smart_dir.glob(f"{platform_lower}_*.csv"))
        if session_started_at is not None:
            cutoff = session_started_at - 300  # 5 min buffer before crawl start
            csv_files = [f for f in csv_files if f.stat().st_mtime >= cutoff]
        else:
            cutoff = time.time() - 6 * 3600
            csv_files = [f for f in csv_files if f.stat().st_mtime >= cutoff]

        files_loaded = len(csv_files)
        for csv_path in csv_files:
            try:
                file_df = pd.read_csv(csv_path)
                if file_df.empty:
                    continue
                # Legacy files may still have nested comments column
                if "comments" in file_df.columns:
                    file_df = pd.DataFrame(flatten_crawl_records(file_df.to_dict(orient="records")))
                frames.append(file_df)
            except Exception as e:
                logger.warning(f"⚠️ Skipping unreadable crawl file {csv_path.name}: {e}")

    if not frames:
        return pd.DataFrame()

    merged = pd.concat(frames, ignore_index=True)
    id_col = next((c for c in ("ID", "id") if c in merged.columns), None)
    before_dedup = len(merged)
    if id_col:
        merged = merged.drop_duplicates(subset=[id_col], keep="first")
    else:
        merged = merged.drop_duplicates()

    if "Platform" not in merged.columns:
        merged["Platform"] = platform_lower

    if "Date" in merged.columns:
        merged["Date"] = parse_crawl_dates(merged["Date"])

    mem_note = " + in-memory" if in_memory_records else ""
    posts_n = (merged["Type"].str.lower() == "post").sum() if "Type" in merged.columns else "?"
    comments_n = (merged["Type"].str.lower() == "comment").sum() if "Type" in merged.columns else "?"
    logger.info(
        f"📦 {platform.upper()}: merged {files_loaded} crawl file(s){mem_note} "
        f"→ {before_dedup} rows → {len(merged)} unique ({posts_n} posts + {comments_n} comments)"
    )
    return merged


def apply_crawl_date_filter(df: pd.DataFrame, date_filter: Dict[str, Any]) -> pd.DataFrame:
    """Drop rows outside the user-selected date window after crawl merge."""
    if df.empty or "Date" not in df.columns:
        return df

    from backend.utils.crawl_records import parse_crawl_dates

    start = pd.Timestamp(date_filter["start_date"])
    end = pd.Timestamp(date_filter["end_date"])
    start = start.tz_localize("UTC") if start.tzinfo is None else start.tz_convert("UTC")
    end = end.tz_localize("UTC") if end.tzinfo is None else end.tz_convert("UTC")

    dates = parse_crawl_dates(df["Date"])
    mask = dates.notna() & (dates >= start) & (dates <= end)
    before = len(df)
    filtered = df.loc[mask].copy()
    posts_before = (df["Type"].str.lower() == "post").sum() if "Type" in df.columns else before
    posts_after = (filtered["Type"].str.lower() == "post").sum() if "Type" in filtered.columns else len(filtered)
    logger.info(
        f"📅 Date filter: {before} → {len(filtered)} records "
        f"({posts_before}→{posts_after} posts, "
        f"{date_filter['start_iso'][:10]} to {date_filter['end_iso'][:10]})"
    )
    return filtered


def apply_crawl_date_filter_for_request(
    df: pd.DataFrame,
    date_filter: Dict[str, Any],
    request: "AnalysisRequest",
) -> pd.DataFrame:
    """Apply date filter — keep post+comment bundles for keyword search and direct post URLs."""
    from backend.utils.crawl_records import (
        keep_direct_post_bundle_rows,
        keep_post_date_filtered_bundle_rows,
        resolve_direct_url_target,
        sanitize_direct_urls,
    )

    if df.empty:
        return df

    if request.crawl_mode == "direct_url" and request.direct_urls:
        cleaned = sanitize_direct_urls(request.direct_urls)
        target = resolve_direct_url_target(cleaned, request.direct_url_target or "auto")
        if target == "post":
            kept = keep_direct_post_bundle_rows(df)
            posts_n = (kept["Type"].str.lower() == "post").sum() if "Type" in kept.columns else 0
            comments_n = (kept["Type"].str.lower() == "comment").sum() if "Type" in kept.columns else 0
            logger.info(
                f"📅 Direct Post URL mode: {len(df)} → {len(kept)} rows "
                f"({posts_n} posts + {comments_n} comments, date filter skipped for explicit URLs)"
            )
            return kept

    # Keyword search (default): filter posts by date, retain linked comments
    if request.crawl_mode in (None, "keyword", "keyword_search"):
        before = len(df)
        kept = keep_post_date_filtered_bundle_rows(df, date_filter)
        posts_before = (df["Type"].str.lower() == "post").sum() if "Type" in df.columns else before
        posts_after = (kept["Type"].str.lower() == "post").sum() if "Type" in kept.columns else len(kept)
        comments_before = (df["Type"].str.lower() == "comment").sum() if "Type" in df.columns else 0
        comments_after = (kept["Type"].str.lower() == "comment").sum() if "Type" in kept.columns else 0
        logger.info(
            f"📅 Keyword bundle date filter: {before} → {len(kept)} records "
            f"({posts_before}→{posts_after} posts, {comments_before}→{comments_after} comments, "
            f"{date_filter['start_iso'][:10]} to {date_filter['end_iso'][:10]})"
        )
        return kept

    return apply_crawl_date_filter(df, date_filter)


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

    # No real data available — synthetic fallback intentionally disabled (real data only).
    logger.warning(f"⚠️ No real data found for '{query}' on {platform} (synthetic fallback disabled)")
    return _generate_synthetic_platform_data(platform, query, max_results, nlp_results)

def _generate_synthetic_platform_data(platform: str, query: str, max_results: int, nlp_results: Dict[str, Any] = None) -> Dict[str, Any]:
    """Synthetic data generation is disabled — return a clear no-data status (real data only)."""
    return {
        "platform": platform,
        "error": f"No real data available for {platform}",
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
        df = df.copy()
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df = df.dropna(subset=['Date'])

        # Coerce numeric columns — some platforms return engagement/score as strings,
        # which breaks numpy sum/mean with "int + str" TypeError. Force numeric.
        if 'sentiment_score' not in df.columns:
            df['sentiment_score'] = 0.0
        if 'total_engagement' not in df.columns:
            df['total_engagement'] = 0
        df['sentiment_score'] = pd.to_numeric(df['sentiment_score'], errors='coerce')
        df['total_engagement'] = pd.to_numeric(df['total_engagement'], errors='coerce').fillna(0)

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
        # Normalize and filter text safely (prevents NaN/float values entering models)
        df['Text'] = df['Text'].apply(_safe_model_text)
        valid_texts_mask = df['Text'].str.strip().str.len() > 0
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
        df['author_demographic'] = ''
        df['author_demo_confidence'] = 0.0
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
                text_demo = sentiment_result.get('demographic', 'Unknown')
                author = str(df.at[idx, 'author']) if 'author' in df.columns and pd.notna(df.at[idx, 'author']) else ''
                try:
                    from backend.utils.malaysian_name_demographics import merge_demographic
                    final_demo, author_demo, name_conf = merge_demographic(text_demo, author)
                    df.at[idx, 'demographic'] = final_demo
                    df.at[idx, 'author_demographic'] = author_demo
                    df.at[idx, 'author_demo_confidence'] = round(name_conf, 3)
                except Exception:
                    df.at[idx, 'demographic'] = text_demo

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
                        demo_engagement = int(
                            pd.to_numeric(demo_df['total_engagement'], errors='coerce').fillna(0).sum()
                        )

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
                "confidence": round(avg_emotions[primary_emotion], 3),
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
                <h2>📊 Analysis Tools</h2>
                <ul>
                    <li><a href="/analyze-csv-page" style="font-weight: bold; color: #667eea;">🔍 Analyze Existing CSV Files</a> - Run Universal Intelligence Analysis on collected data</li>
                </ul>
                <h2>🔧 System Endpoints</h2>
                <ul>
                    <li><a href="/platforms">/platforms</a> - View available platforms</li>
                    <li><a href="/health">/health</a> - System health check</li>
                    <li><a href="/docs">/docs</a> - API documentation</li>
                    <li><a href="/api/list-csvs">/api/list-csvs</a> - List available CSV files</li>
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


@app.get("/api/projects")
async def api_list_projects():
    """List all projects for UI dropdown (no manual _registry.json editing)."""
    try:
        from backend.storage.project_registry import load_registry, list_projects
        return {
            "success": True,
            "categories": load_registry().get("categories", []),
            "projects": list_projects(),
        }
    except Exception as e:
        logger.error(f"❌ list projects: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/projects")
async def api_create_project(body: CreateProjectRequest):
    """Create project from UI — auto updates registry + folders."""
    try:
        from backend.storage.project_registry import register_project
        project = register_project(
            name=body.name,
            client=body.client,
            category=body.category,
            master_prefix=body.master_prefix,
            project_id=body.project_id,
            default_keywords=body.default_keywords,
        )
        logger.info(f"📁 New project registered: {project['project_id']}")
        return {"success": True, "project": project}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"❌ create project: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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

# 🎯 NEW: Background task function for long-running analysis
async def run_unified_analysis_task(task_id: str, request: AnalysisRequest):
    """Process upload/feed/hybrid packages — optional social crawl merge."""
    global _active_task_id
    _active_task_id = task_id
    try:
        from backend.platform.unified_ingest import (
            build_unified_insights,
            load_feed_data,
            load_upload_meta,
        )

        analysis_tasks[task_id]["status"] = "running"
        task_log(task_id, f"🔀 Unified analysis mode: {request.data_source_mode}")

        upload_summaries = []
        for uid in request.upload_ids or []:
            meta = load_upload_meta(uid)
            if meta:
                upload_summaries.append(meta)
                task_log(task_id, f"📂 Upload loaded: {meta.get('filename')} ({meta.get('rows', 0)} rows)")

        feed_bundle = load_feed_data(request.feed_ids or [])
        if feed_bundle.get("feeds"):
            task_log(task_id, f"📈 Feeds attached: {', '.join(f['id'] for f in feed_bundle['feeds'])}")

        crawl_result = None
        run_crawl = (
            request.data_source_mode in ("social_crawl", "hybrid")
            and not request.skip_crawl
            and (request.query or request.direct_urls)
            and (
                request.platforms
                or (request.crawl_mode == "direct_url" and request.direct_urls)
            )
        )

        if run_crawl:
            task_log(task_id, "🕷️ Running social crawl as part of unified package...")
            crawl_result = await analyze_data_core(request, task_id)
        else:
            task_log(task_id, "⏭️ Skipping crawl — upload/feed only package")

        unified = build_unified_insights(
            analysis_type=request.analysis_type,
            data_source_mode=request.data_source_mode,
            upload_summaries=upload_summaries,
            feed_bundle=feed_bundle,
            crawl_result=crawl_result,
            project_id=request.project_id,
        )

        if crawl_result:
            result = {**crawl_result, **unified}
        else:
            result = {
                "analysis_type": request.analysis_type,
                "query": request.query or "Unified data package",
                "platforms": request.platforms or [],
                "total_data_points": sum(u.get("rows", 0) for u in upload_summaries),
                "summary": {
                    "total_records": sum(u.get("rows", 0) for u in upload_summaries),
                    "platforms_analyzed": len(request.platforms or []),
                },
                "key_insights": unified["key_insights"],
                "recommendations": unified["recommendations"],
                **unified,
            }

        analysis_tasks[task_id]["status"] = "completed"
        analysis_tasks[task_id]["result"] = result
        analysis_tasks[task_id]["progress"] = {"stage": "completed", "message": "Unified analysis completed"}
        task_log(task_id, "🎉 Unified analysis completed")

    except Exception as e:
        analysis_tasks[task_id]["status"] = "failed"
        analysis_tasks[task_id]["error"] = str(e)
        analysis_tasks[task_id]["progress"] = {"stage": "failed", "message": str(e)}
        task_log(task_id, f"❌ Unified analysis failed: {e}")
    finally:
        _active_task_id = None


def _uses_unified_pipeline(request: AnalysisRequest) -> bool:
    if request.data_source_mode != "social_crawl":
        return True
    if request.upload_ids or request.feed_ids:
        return True
    if request.skip_crawl:
        return True
    return False


async def run_analysis_task(task_id: str, request: AnalysisRequest):
    """
    Run analysis as a background task and update status in analysis_tasks dict
    """
    global _active_task_id
    try:
        # Update status to running
        analysis_tasks[task_id]["status"] = "running"
        analysis_tasks[task_id]["progress"] = {"stage": "starting", "message": "Initializing analysis..."}
        analysis_tasks[task_id]["logs"] = []

        # Activate log capture for this task
        _active_task_id = task_id
        task_log(task_id, f"🚀 Task started — query: {request.query[:80]}...")
        task_log(task_id, f"📋 Platforms: {', '.join(request.platforms).upper()}")
        _date_label = {
            "24h": "Last 24 hours", "7days": "Last 7 days", "30days": "Last 30 days",
            "90days": "Last 90 days", "180days": "Last 6 months", "6months": "Last 6 months",
            "365days": "Last 1 year", "1year": "Last 1 year", "custom": "Custom date range"
        }.get(request.date_range, request.date_range)
        task_log(task_id, f"📊 Dataset size: {request.dataset_size or request.max_results} results | {_date_label}")
        try:
            from backend.data_crawlers.crawl_guard import or_keyword_count, guard_message, MAX_OR_KEYWORD_SPLIT
            task_log(task_id, f"🛡️ {guard_message(request.query or '')}")
            if or_keyword_count(request.query or "") > MAX_OR_KEYWORD_SPLIT:
                task_log(
                    task_id,
                    f"💡 Long OR query → 1 combined crawl (~30-45 min). "
                    f"For per-DUN gaps use scripts/crawl_prn_gap_seats.py",
                )
        except Exception:
            pass

        # Call the actual analyze function
        result = await analyze_data_core(request, task_id)

        # Update status to completed
        analysis_tasks[task_id]["status"] = "completed"
        analysis_tasks[task_id]["result"] = result
        analysis_tasks[task_id]["progress"] = {"stage": "completed", "message": "Analysis completed successfully!"}
        task_log(task_id, "🎉 Analysis completed successfully!")

        logger.info(f"✅ Task {task_id} completed successfully")

    except Exception as e:
        # Update status to failed
        analysis_tasks[task_id]["status"] = "failed"
        analysis_tasks[task_id]["error"] = str(e)
        analysis_tasks[task_id]["progress"] = {"stage": "failed", "message": f"Analysis failed: {str(e)}"}
        task_log(task_id, f"❌ Failed: {str(e)}")
        logger.error(f"❌ Task {task_id} failed: {e}")

    finally:
        _active_task_id = None


@app.post("/analyze_async")
async def analyze_data_async(request: AnalysisRequest, background_tasks: BackgroundTasks):
    """
    🎯 NEW: Start analysis as a background task and return task_id immediately
    Frontend can poll /task_status/{task_id} to get progress

    This solves the "Failed to fetch" timeout issue for long-running analyses
    """
    # Generate unique task ID
    task_id = str(uuid.uuid4())

    # Initialize task tracking
    analysis_tasks[task_id] = {
        "status": "queued",
        "progress": {"stage": "queued", "message": "Analysis queued"},
        "result": None,
        "error": None,
        "created_at": datetime.now().isoformat(),
        "query": request.query,
        "platforms": request.platforms,
        "dataset_size": request.dataset_size or request.max_results
    }

    runner = run_unified_analysis_task if _uses_unified_pipeline(request) else run_analysis_task
    background_tasks.add_task(runner, task_id, request)

    logger.info(f"🎯 Analysis task {task_id} queued for query: {request.query} mode={request.data_source_mode}")
    logger.info(f"📊 Platforms: {request.platforms}, Dataset: {request.dataset_size or request.max_results}")

    # Return task_id immediately
    return {
        "task_id": task_id,
        "status": "queued",
        "message": "Analysis started. Poll /task_status/{task_id} for progress.",
        "estimated_time_minutes": len(request.platforms) * 3  # Rough estimate: 3 min per platform
    }


@app.get("/task_status/{task_id}")
async def get_task_status(task_id: str):
    """
    Get status of a running analysis task
    """
    if task_id not in analysis_tasks:
        raise HTTPException(status_code=404, detail="Task not found")

    task = analysis_tasks[task_id]

    return {
        "task_id": task_id,
        "status": task["status"],  # queued, running, completed, failed
        "progress": task["progress"],
        "result": task["result"] if task["status"] == "completed" else task.get("partial_result"),
        "error": task["error"] if task["status"] == "failed" else None,
        "created_at": task["created_at"],
        "logs": task.get("logs", [])[-40:]  # return last 40 log lines
    }


@app.post("/analyze")
async def analyze_data(request: AnalysisRequest):
    """
    Perform PERFECT analysis on selected platforms with:
    - Platform-optimized data collection
    - Smart comment sampling
    - Date range filtering
    - Analysis focus prioritization

    ⚠️ WARNING: This endpoint waits for completion (can take 10-15 minutes for large datasets)
    ✅ RECOMMENDED: Use /analyze_async instead for better UX
    """
    # Call the core function directly (no background task)
    return await analyze_data_core(request, task_id=None)


async def analyze_data_core(request: AnalysisRequest, task_id: Optional[str] = None):
    """
    Core analysis logic (extracted so it can be called from both sync and async endpoints)
    """

    # Helper function to update progress
    def update_progress(stage: str, message: str, platforms_done: int = 0):
        if task_id and task_id in analysis_tasks:
            analysis_tasks[task_id]["progress"] = {
                "stage": stage,
                "message": message,
                "platforms_total": len(request.platforms),
                "platforms_done": platforms_done
            }

    def update_partial_counts(posts: int = 0, comments: int = 0, platform: Optional[str] = None):
        """Expose live crawl counts to the polling UI before task completes."""
        if not task_id or task_id not in analysis_tasks:
            return
        partial = analysis_tasks[task_id].setdefault("partial_result", {
            "total_posts_analyzed": 0,
            "total_comments_analyzed": 0,
            "platform_breakdown": {},
        })
        if platform:
            pb = partial.setdefault("platform_breakdown", {})
            entry = pb.setdefault(platform, {"posts_count": 0, "comments_count": 0})
            entry["posts_count"] = posts
            entry["comments_count"] = comments
        partial["total_posts_analyzed"] = posts if platform is None else sum(
            p.get("posts_count", 0) for p in partial.get("platform_breakdown", {}).values()
        )
        partial["total_comments_analyzed"] = comments if platform is None else sum(
            p.get("comments_count", 0) for p in partial.get("platform_breakdown", {}).values()
        )

    logger.info(f"🔍 Starting PERFECT analysis for query: {request.query}")
    logger.info(f"📊 Platforms: {request.platforms}")
    logger.info(f"🎯 Analysis depth: {request.analysis_depth}")
    logger.info(f"🎯 Analysis focus: {request.analysis_focus}")
    logger.info(f"📅 Date range: {request.date_range}")
    logger.info(f"💬 Comment sampling: {request.comment_sampling}")
    multimodal_enabled = bool(request.multimodal or request.analysis_type == "multimodal_video_text")
    if request.analysis_type == "social_listening" and request.analysis_type != "multimodal_video_text":
        if multimodal_enabled:
            logger.info(
                "🎞️ Multimodal auto-disabled for Social Listening "
                "(use Analysis Type 'Multimodal Video + Text' to enable)"
            )
        multimodal_enabled = False
    if multimodal_enabled:
        logger.info("🎞️ Multimodal media routing enabled for this run")

    update_progress("initializing", f"Starting analysis for {len(request.platforms)} platforms...")

    # Get date range filter
    date_filter = get_date_range_filter(request)
    logger.info(f"📅 Filtering data from {date_filter['start_iso']} to {date_filter['end_iso']} ({date_filter['days']} days)")

    # Get analysis focus configuration
    focus_config = get_analysis_focus_config(request)
    logger.info(f"🎯 Analysis focus: {focus_config['description']}")

    # 🧠 Phase 1: Advanced NLP Processing & Keyword Extraction
    logger.info("🧠 Phase 1: Processing input with Advanced NLP...")
    update_progress("nlp_processing", "Processing keywords with NLP...")
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
    crawl_session_started_at = time.time()

    if APIFY_AVAILABLE:
        # 🤖 Initialize adapter with LLM service for AI keyword generation
        adapter = SimpleApifyAdapter(llm_service=llm_service if LLM_SERVICE_AVAILABLE else None)

        # 🎯 Determine dataset size (use dataset_size if provided, otherwise use max_results)
        effective_dataset_size = request.dataset_size if request.dataset_size else request.max_results

        # 🎯 ALWAYS use crawl strategy with comments (30:70 ratio)
        if request.use_crawl_strategy:
            logger.info(f"🎯 Using 30:70 Posts:Comments strategy with dataset size: {effective_dataset_size}")

            update_progress("crawling", f"Connecting to crawl actors for {len(request.platforms)} platform(s)...", 0)

            # Broadcast strategy status
            await manager.broadcast_status({
                "type": "system_status",
                "status": "calculating_strategy",
                "timestamp": datetime.now().isoformat(),
                "message": f"🎯 Calculating crawl strategy for {effective_dataset_size} results (30% posts + 70% comments)..."
            })

            start_time = time.time()

            try:
                # 🌐 DIRECT URL MODE — crawl specific pages/profiles
                if request.crawl_mode == "direct_url" and request.direct_urls:
                    from backend.utils.crawl_records import resolve_direct_url_target, sanitize_direct_urls

                    direct_urls_clean = sanitize_direct_urls(request.direct_urls)
                    direct_url_target = resolve_direct_url_target(
                        direct_urls_clean, request.direct_url_target or "auto"
                    )
                    direct_post_mode = direct_url_target == "post"
                    num_urls = max(1, len(direct_urls_clean))

                    comment_target = request.comment_target_per_post
                    if direct_post_mode and not comment_target:
                        comment_target = effective_dataset_size

                    if direct_post_mode:
                        if num_urls == 1:
                            per_post_budget = min(1000, max(500, comment_target or effective_dataset_size))
                        else:
                            per_post_budget = min(
                                1000,
                                max(100, (comment_target or effective_dataset_size) // num_urls),
                            )
                        crawl_max_comments = per_post_budget
                        crawl_since = None
                        crawl_until = None
                        logger.info(
                            f"📌 Direct Post URL batch: {num_urls} posts, "
                            f"target {comment_target or crawl_max_comments}/post, "
                            f"multipass={request.multipass_comments}, dedupe ON"
                        )
                    else:
                        crawl_max_comments = max(30, effective_dataset_size // 20)
                        crawl_since = date_filter["start_iso"][:10]
                        crawl_until = date_filter["end_iso"][:10]

                    update_progress("crawling", f"Crawling {len(direct_urls_clean)} direct URL(s)...", 0)
                    logger.info(f"🌐 Direct URL crawl mode ({direct_url_target}): {direct_urls_clean}")
                    strategy_result = await adapter.crawl_direct_urls(
                        urls=direct_urls_clean,
                        max_posts=max(50, effective_dataset_size // 10),
                        max_comments=crawl_max_comments,
                        since_date=crawl_since,
                        until_date=crawl_until,
                        direct_post_mode=direct_post_mode,
                        comment_target_per_post=comment_target if direct_post_mode else None,
                        multipass_comments=request.multipass_comments,
                        include_nested_comments=request.include_nested_comments,
                    )
                    request.direct_urls = direct_urls_clean
                else:
                    update_progress("crawling", f"Fetching data from {', '.join(request.platforms).upper()}...", 0)
                    # 🎯 Use new strategy-based crawling with comments
                    strategy_result = await adapter.crawl_with_strategy(
                        platforms=request.platforms,
                        query=request.query,
                        dataset_size=effective_dataset_size,
                        analysis_type=request.analysis_focus,
                        since_date=date_filter["start_iso"][:10],   # "YYYY-MM-DD"
                        until_date=date_filter["end_iso"][:10]
                    )

                elapsed_time = time.time() - start_time
                logger.info(f"⚡ Strategy-based crawl completed in {elapsed_time:.2f} seconds!")
                update_progress("crawling", f"Crawl complete in {elapsed_time:.0f}s — processing results...", len(request.platforms))

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
        from backend.utils.crawl_records import flatten_crawl_records
        for idx, (platform, results) in enumerate(real_time_data_dict.items(), start=1):
            update_progress(
                "crawling",
                f"Processing {platform.upper()} results ({idx}/{len(real_time_data_dict)})...",
                idx,
            )
            task_log(task_id, f"📦 Processing {platform.upper()} crawl results...")
            if results:
                flat = flatten_crawl_records(results)
                real_time_data[platform] = flat
                posts_n = sum(1 for r in flat if str(r.get("Type", "post")).lower() == "post")
                comments_n = sum(1 for r in flat if str(r.get("Type", "post")).lower() == "comment")
                update_partial_counts(posts_n, comments_n, platform)
                logger.info(
                    f"✅ Got {len(flat)} flat records from {platform} "
                    f"({posts_n} posts + {comments_n} comments)"
                )
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
    update_progress("sentiment_analysis", f"Running sentiment & emotion analysis on collected data...", len(request.platforms))
    platform_data = {}
    session_analyzed_files: Dict[str, Path] = {}

    for idx, platform in enumerate(request.platforms, start=1):
        logger.info(f"📱 Collecting data from {platform}...")
        update_progress(
            "sentiment_analysis",
            f"Analysing {platform.upper()} data — sentiment + emotions ({idx}/{len(request.platforms)})...",
            idx,
        )
        if task_id:
            task_log(task_id, f"💬 Sentiment analysis: {platform.upper()} ({idx}/{len(request.platforms)})")

        # Use real-time data if available, otherwise load from files
        if platform in real_time_data:
            logger.info(f"✅ Using real-time crawled data for {platform}")

            df = None
            processed_insights: Dict[str, Any] = {"error": "Processing did not run"}
            analyzed_filepath: Optional[Path] = None

            try:
                # 📂 STEP 1: Build DataFrame — merge ALL keyword crawl files from this session
                from pathlib import Path
                raw_dir = Path("data/raw")
                raw_filename = f"{platform.upper()}.csv"
                raw_filepath = raw_dir / raw_filename

                df = load_merged_platform_crawl_data(
                    platform,
                    in_memory_records=real_time_data.get(platform),
                    session_started_at=crawl_session_started_at,
                )

                # Avoid stale data/raw/*.csv from prior runs (e.g. wrong calon/query)
                use_raw_fallback = request.crawl_mode not in (None, "keyword", "keyword_search")
                if df.empty and use_raw_fallback and raw_filepath.exists():
                    logger.info(f"📂 Reading RAW data from: {raw_filepath}")
                    df = pd.read_csv(raw_filepath)
                    logger.info(f"📊 Loaded {len(df)} records from RAW file")
                elif df.empty and platform in real_time_data:
                    logger.info(f"📂 Using in-memory crawled records for {platform}")
                    df = pd.DataFrame(real_time_data[platform])
                    logger.info(f"📊 Loaded {len(df)} records from real-time crawl (in-memory)")

                if not df.empty:
                    df = apply_crawl_date_filter_for_request(df, date_filter, request)

                if multimodal_enabled and not df.empty:
                    try:
                        from scripts.multimodal_router import route_items  # noqa: WPS433

                        logger.info(f"🎞️ Routing {platform} media through Nemotron multimodal NIMs (background thread)...")
                        routed_records = await asyncio.to_thread(
                            route_items,
                            df.to_dict(orient="records"),
                            merge_text=True,
                            limit=int(os.getenv("NIM_MULTIMODAL_MAX_ROWS", "0") or 0),
                        )
                        df = pd.DataFrame(routed_records)
                        routed_ok = int(df.get("derived_text", pd.Series(dtype=str)).astype(str).str.len().gt(0).sum()) if "derived_text" in df.columns else 0
                        routed_err = int(df.get("derived_error", pd.Series(dtype=str)).astype(str).str.len().gt(0).sum()) if "derived_error" in df.columns else 0
                        logger.info(f"🎞️ Multimodal routing complete: {routed_ok} derived, {routed_err} errors")
                    except Exception as media_err:
                        logger.warning(f"⚠️ Multimodal routing skipped for {platform}: {media_err}")

                # Count posts and comments
                posts_count = len(df[df['Type'] == 'post']) if 'Type' in df.columns else len(df)
                comments_count = len(df[df['Type'] == 'comment']) if 'Type' in df.columns else 0
                update_partial_counts(posts_count, comments_count, platform)
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
                    session_analyzed_files[platform] = analyzed_filepath
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

            # Prefer the analyzed DataFrame so combined/project CSVs include sentiment + emotion.
            if isinstance(df, pd.DataFrame):
                data_payload = df.to_dict(orient="records")
            else:
                data_payload = real_time_data.get(platform, [])
            data = {
                "data_points": len(data_payload),
                "data": data_payload,
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
    
    # Calculate overall metrics from analyzed rows, not unweighted platform averages.
    # This keeps the live dashboard aligned with generated static reports.
    overall_sentiment_counts = {"positive": 0, "neutral": 0, "negative": 0}
    overall_sentiment_scores = []

    for record in all_data_for_trends:
        label = str(
            record.get("sentiment_label")
            or record.get("Sentiment")
            or record.get("sentiment")
            or ""
        ).strip().lower()

        raw_score = record.get("sentiment_score")
        try:
            score = float(raw_score) if raw_score is not None and str(raw_score).lower() != "nan" else None
        except (TypeError, ValueError):
            score = None

        if label not in overall_sentiment_counts and score is not None:
            label = "positive" if score > 0.6 else "negative" if score < 0.4 else "neutral"

        if label in overall_sentiment_counts:
            overall_sentiment_counts[label] += 1
            if score is None:
                score = 0.8 if label == "positive" else 0.2 if label == "negative" else 0.5
            overall_sentiment_scores.append(score)

    overall_sentiment_total = sum(overall_sentiment_counts.values())
    overall_sentiment_percentages = {
        label: round((count / overall_sentiment_total * 100), 1) if overall_sentiment_total else 0.0
        for label, count in overall_sentiment_counts.items()
    }
    avg_sentiment = (
        sum(overall_sentiment_scores) / len(overall_sentiment_scores)
        if overall_sentiment_scores
        else sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0.5
    )
    overall_sentiment_label = (
        max(overall_sentiment_counts, key=overall_sentiment_counts.get)
        if overall_sentiment_total
        else "positive" if avg_sentiment > 0.6 else "negative" if avg_sentiment < 0.4 else "neutral"
    )

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
        "processing": request.processing,
        "multimodal": request.multimodal,
        "crawl_mode": request.crawl_mode,
        "direct_url_target": getattr(request, "direct_url_target", "auto"),
        "direct_urls": request.direct_urls if request.crawl_mode == "direct_url" else None,
        "platforms_analyzed": request.platforms,
        "total_data_points": total_data_points,
        "analysis_timestamp": datetime.now().isoformat(),
        "overall_metrics": {
            "sentiment_score": round(avg_sentiment, 3),
            "sentiment_label": overall_sentiment_label,
            "sentiment_distribution": overall_sentiment_counts,
            "sentiment_percentages": overall_sentiment_percentages,
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
    update_progress("generating_insights", "Generating professional reports & insights...", len(request.platforms))
    report_paths = {}
    try:
        import sys
        from pathlib import Path
        # Add parent directory to path to import backend module
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from backend.services.report_generator import ProfessionalReportGenerator

        # Prepare analysis data for report generation from the same analyzed rows
        # used by the main dashboard.
        positive_ratio = overall_sentiment_percentages.get("positive", 0.0)
        neutral_ratio = overall_sentiment_percentages.get("neutral", 0.0)
        negative_ratio = overall_sentiment_percentages.get("negative", 0.0)

        def _report_number(value, default=0):
            try:
                if value is None or str(value).lower() == "nan":
                    return default
                return float(value)
            except (TypeError, ValueError):
                return default

        platform_report_breakdown = {}
        for record in all_data_for_trends:
            platform_name = str(record.get("Platform") or record.get("platform") or "Unknown").strip().lower()
            if not platform_name:
                platform_name = "unknown"
            stats = platform_report_breakdown.setdefault(platform_name, {
                "total": 0,
                "total_engagement": 0,
                "sentiment_sum": 0.0,
                "positive_count": 0,
                "negative_count": 0,
            })
            stats["total"] += 1
            stats["total_engagement"] += int(_report_number(record.get("total_engagement"), 0))
            label = str(record.get("sentiment_label") or record.get("Sentiment") or "neutral").lower()
            score = _report_number(record.get("sentiment_score"), 0.5)
            stats["sentiment_sum"] += score
            if label == "positive":
                stats["positive_count"] += 1
            elif label == "negative":
                stats["negative_count"] += 1

        platform_report_breakdown = {
            platform: {
                "total": stats["total"],
                "avg_sentiment": round(stats["sentiment_sum"] / stats["total"], 3) if stats["total"] else 0,
                "total_engagement": stats["total_engagement"],
                "positive_ratio": round(stats["positive_count"] / stats["total"] * 100, 1) if stats["total"] else 0,
                "negative_ratio": round(stats["negative_count"] / stats["total"] * 100, 1) if stats["total"] else 0,
            }
            for platform, stats in platform_report_breakdown.items()
        }

        report_data = {
            'raw_data': all_data_for_trends,  # All posts/comments
            'sentiment_analysis': {
                'positive_ratio': positive_ratio,
                'neutral_ratio': neutral_ratio,
                'negative_ratio': negative_ratio,
                'distribution': overall_sentiment_counts,
            },
            'platform_breakdown': platform_report_breakdown,
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

                # 📁 Promote to project folder if project_id set
                if request.project_id:
                    try:
                        from backend.storage.project_registry import get_project, promote_combined_to_project
                        proj = get_project(request.project_id)
                        if proj:
                            prefix = proj.get("master_prefix", request.project_id)
                            is_news = set(p.lower() for p in request.platforms) <= {"news", "google"}
                            label = f"{prefix}_{'News' if is_news else 'Social'}"
                            # Promote analyzed export when available (single-platform or combined w/ sentiment)
                            promote_analyzed: Optional[Path] = None
                            if "sentiment_label" in combined_df.columns:
                                promote_analyzed = combined_filepath
                            elif len(session_analyzed_files) == 1:
                                promote_analyzed = next(iter(session_analyzed_files.values()))
                            elif len(session_analyzed_files) > 1:
                                merged_analyzed = combined_df.copy()
                                promote_analyzed = combined_dir / combined_filename.replace(
                                    "Combined_", "Combined_Analyzed_"
                                )
                                merged_analyzed.to_csv(promote_analyzed, index=False, encoding="utf-8")
                            project_path = promote_combined_to_project(
                                request.project_id,
                                combined_filepath,
                                analyzed_filepath=promote_analyzed,
                                crawl_label=label,
                                platforms=request.platforms,
                                query=request.query,
                                date_range=request.date_range,
                                row_count=len(combined_df),
                            )
                            logger.info(f"📁 PROJECT DATA saved: {project_path}")
                            task_log(task_id, f"📁 Project crawl saved: {request.project_id} → {project_path.name}") if task_id else None
                        else:
                            logger.warning(f"⚠️ Unknown project_id: {request.project_id}")
                    except Exception as proj_err:
                        logger.error(f"❌ Project promote failed: {proj_err}")

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

# ============================================================================
# CSV ANALYSIS ENDPOINTS
# ============================================================================

@app.get("/api/list-csvs")
async def list_existing_csvs():
    """
    List all available CSV files in data/combined/
    """
    try:
        combined_dir = Path("data/combined")

        if not combined_dir.exists():
            return {"success": True, "count": 0, "csvs": []}

        csv_files = []
        for csv_file in combined_dir.glob("*.csv"):
            stats = csv_file.stat()
            csv_files.append({
                "filename": csv_file.name,
                "path": str(csv_file),
                "size": stats.st_size,
                "size_mb": round(stats.st_size / (1024 * 1024), 2),
                "modified_date": stats.st_mtime,
                "modified_date_str": datetime.fromtimestamp(stats.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
            })

        # Sort by modified date (newest first)
        csv_files.sort(key=lambda x: x["modified_date"], reverse=True)

        return {
            "success": True,
            "count": len(csv_files),
            "csvs": csv_files
        }

    except Exception as e:
        logger.error(f"Error listing CSVs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error listing CSVs: {str(e)}")

class AnalyzeCSVRequest(BaseModel):
    csv_path: str
    topic_name: str
    filter_days: Optional[int] = 90

@app.post("/api/analyze-csv")
async def analyze_csv_file(request: AnalyzeCSVRequest):
    """
    Analyze an existing CSV file with Universal Intelligence Dashboard
    """
    try:
        from backend.services.universal_intelligence_dashboard import UniversalIntelligenceDashboard

        csv_path = request.csv_path
        topic_name = request.topic_name
        filter_days = request.filter_days or 90

        logger.info(f"📊 Analyzing CSV: {csv_path} for topic: {topic_name}")

        # Validate CSV exists
        if not Path(csv_path).exists():
            raise HTTPException(status_code=404, detail=f"CSV file not found: {csv_path}")

        # Run analysis
        analyzer = UniversalIntelligenceDashboard(csv_path, topic_name=topic_name)
        insights = analyzer.analyze(filter_days=filter_days)

        # Export results
        output_dir = Path(f"reports/universal_analysis_{topic_name.replace(' ', '_')}")
        output_dir.mkdir(parents=True, exist_ok=True)

        analyzer.export_to_json(str(output_dir / "insights.json"))
        analyzer.export_cleaned_data(str(output_dir / "cleaned_data.csv"))

        logger.info(f"✅ Analysis complete! Results saved to: {output_dir}")

        return {
            "success": True,
            "message": "Analysis completed successfully",
            "topic": topic_name,
            "insights": insights,
            "output_dir": str(output_dir),
            "files": {
                "insights_json": str(output_dir / "insights.json"),
                "cleaned_csv": str(output_dir / "cleaned_data.csv")
            }
        }

    except Exception as e:
        logger.error(f"❌ Analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis error: {str(e)}")


class KDEBWMAnalysisRequest(BaseModel):
    csv_path: str
    filter_days: Optional[int] = 30
    export_results: Optional[bool] = True


@app.post("/api/kdebwm/analyze")
async def analyze_kdebwm_complaints(request: KDEBWMAnalysisRequest):
    """
    KDEBWM Complaint Monitoring Analytics
    =====================================
    Generate executive-level complaint analytics and insights for KDEBWM management.

    Returns:
    - Executive summary
    - Complaint volume analytics
    - Sentiment distribution
    - Theme classification
    - Hotspot area detection
    - Platform analytics
    - High-severity complaints
    - Management recommendations
    - CEO dashboard metrics
    """
    try:
        from backend.services.kdebwm_analytics import KDEBWMComplaintAnalytics

        csv_path = request.csv_path
        filter_days = request.filter_days or 30

        logger.info(f"🏢 KDEBWM Analysis - Processing: {csv_path}")
        logger.info(f"📅 Filter period: Last {filter_days} days")

        # Validate CSV exists
        if not Path(csv_path).exists():
            raise HTTPException(status_code=404, detail=f"CSV file not found: {csv_path}")

        # Run KDEBWM-specific analysis
        analyzer = KDEBWMComplaintAnalytics(csv_path)
        results = analyzer.analyze(filter_days=filter_days)

        # Export results if requested
        if request.export_results:
            output_dir = Path("reports/kdebwm_complaint_analytics")
            output_dir.mkdir(parents=True, exist_ok=True)

            # Save JSON
            analyzer.export_to_json(str(output_dir / f"kdebwm_analytics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"))

            # Save processed complaints CSV
            analyzer.export_complaints_csv(str(output_dir / f"kdebwm_complaints_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"))

            # Save executive summary
            with open(output_dir / f"executive_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt", 'w', encoding='utf-8') as f:
                f.write(results['executive_summary'])

            logger.info(f"📁 Results exported to: {output_dir}")

        logger.info("✅ KDEBWM complaint analysis complete!")

        return {
            "success": True,
            "message": "KDEBWM complaint analysis completed successfully",
            "results": results,
            "metadata": {
                "source_file": csv_path,
                "filter_days": filter_days,
                "total_records": results['metadata']['total_records'],
                "complaint_records": results['metadata']['complaint_records'],
                "generated_at": results['metadata']['generated_at']
            }
        }

    except Exception as e:
        logger.error(f"❌ KDEBWM Analysis error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"KDEBWM Analysis error: {str(e)}")


@app.get("/api/analysis/types")
async def api_analysis_types():
    from backend.platform.unified_ingest import list_analysis_types
    return {"success": True, "types": list_analysis_types()}


@app.get("/api/data/templates")
async def api_list_templates():
    from backend.platform.unified_ingest import list_templates
    return {"success": True, "templates": list_templates()}


@app.get("/api/data/templates/{template_id}")
async def api_download_template(template_id: str):
    from backend.platform.unified_ingest import template_path
    from fastapi.responses import FileResponse
    try:
        path = template_path(template_id)
        return FileResponse(path, filename=path.name, media_type="text/csv")
    except (ValueError, FileNotFoundError) as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/api/data/feeds")
async def api_list_feeds():
    from backend.platform.unified_ingest import list_feeds
    return {"success": True, "feeds": list_feeds()}


@app.get("/api/ml/predict/prn_n9")
async def api_ml_predict_prn_n9(refresh: bool = False):
    """Run SVM + Random Forest + Decision Tree on 36 N9 DUN seats."""
    from backend.ml.predictive_engine import run_prn_n9_ml, PRN_N9_ML_OUTPUT

    try:
        if not refresh and PRN_N9_ML_OUTPUT.exists():
            cached = json.loads(PRN_N9_ML_OUTPUT.read_text(encoding="utf-8"))
            cached["source"] = "cache"
            return {"success": True, "result": cached}

        result = run_prn_n9_ml(write_output=True)
        result["source"] = "fresh"
        return {"success": result.get("success", False), "result": result}
    except Exception as e:
        logger.error(f"ML PRN N9 error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ml/predict")
async def api_ml_predict(request: dict):
    """
    Generic ML predict — analysis_type + optional upload_ids.
    Body: { "analysis_type": "portfolio_intelligence", "upload_ids": ["abc123"], "project_id": "PRN_N9" }
    """
    from backend.platform.unified_ingest import load_upload_meta
    from backend.ml.predictive_engine import run_ml_analysis, run_prn_n9_ml, run_portfolio_ml, load_upload_rows

    analysis_type = request.get("analysis_type") or "social_listening"
    project_id = request.get("project_id")
    upload_ids = request.get("upload_ids") or []

    try:
        if analysis_type == "prn_n9" or (project_id and "N9" in str(project_id).upper()):
            result = run_prn_n9_ml(write_output=True)
            return {"success": True, "result": result}

        upload_summaries = []
        for uid in upload_ids:
            meta = load_upload_meta(uid)
            if meta:
                upload_summaries.append(meta)

        if analysis_type in ("portfolio_intelligence", "sme_insights") and upload_summaries:
            u = upload_summaries[0]
            result = run_portfolio_ml(load_upload_rows(u), u.get("columns"))
            return {"success": True, "result": result}

        result = run_ml_analysis(
            analysis_type=analysis_type,
            upload_summaries=upload_summaries,
            project_id=project_id,
        )
        return {"success": True, "result": result}
    except Exception as e:
        logger.error(f"ML predict error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/data/upload")
async def api_data_upload(
    file: UploadFile = File(...),
    dataset_type: str = "generic_csv",
    project_id: Optional[str] = None,
):
    from backend.platform.unified_ingest import save_upload
    try:
        content = await file.read()
        if not file.filename:
            raise HTTPException(status_code=400, detail="Filename required")
        ext = Path(file.filename).suffix.lower()
        if ext not in (".csv", ".json", ".xlsx", ".xls"):
            raise HTTPException(status_code=400, detail="Supported: CSV, JSON, Excel (save as CSV preferred)")
        meta = await save_upload(content, file.filename, dataset_type, project_id)
        return {"success": True, "upload": meta}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/upload-csv")
async def upload_csv_file(file: UploadFile = File(...)):
    """
    Upload a CSV file to data/combined/
    """
    try:
        # Validate file is CSV
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="Only CSV files are allowed")

        # Create directory if doesn't exist
        upload_dir = Path("data/combined")
        upload_dir.mkdir(parents=True, exist_ok=True)

        # Save file
        file_path = upload_dir / file.filename

        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        logger.info(f"✅ Uploaded CSV: {file_path} ({len(content)} bytes)")

        return {
            "success": True,
            "message": "File uploaded successfully",
            "filename": file.filename,
            "path": str(file_path),
            "size": len(content)
        }

    except Exception as e:
        logger.error(f"❌ Upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload error: {str(e)}")

@app.get("/analyze-csv-page")
async def analyze_csv_page():
    """Serve the CSV analysis page"""
    return FileResponse("web_backend/static/analyze_csv.html")


@app.get("/crawl-live")
async def crawl_live_page():
    """Live crawl monitor (Batch 7 / any task_id via ?task=...)"""
    path = Path(__file__).parent / "static" / "crawl_live.html"
    if not path.exists():
        raise HTTPException(status_code=404, detail="crawl_live.html not found")
    return FileResponse(path)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
