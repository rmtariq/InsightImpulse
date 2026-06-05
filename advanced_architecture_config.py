#!/usr/bin/env python3
"""
InsightPulse Advanced Agentic Architecture Configuration
Enterprise-grade configuration for Agent + RAG + Vector DB + MCP system
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
import os

class ModelProvider(Enum):
    NVIDIA_NEMO = "nvidia_nemo"
    HUGGINGFACE = "huggingface"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"

class VectorDBProvider(Enum):
    NVIDIA_CUVS = "nvidia_cuvs"
    CHROMA = "chroma"
    PINECONE = "pinecone"
    WEAVIATE = "weaviate"

class PlatformType(Enum):
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    TWITTER = "twitter"
    TIKTOK = "tiktok"
    GOOGLE = "google"
    NEWS = "news"
    FORUMS = "forums"

@dataclass
class VectorDBConfig:
    """Vector Database Configuration"""
    provider: VectorDBProvider = VectorDBProvider.NVIDIA_CUVS
    dimension: int = 1024  # Embedding dimension
    similarity_metric: str = "cosine"
    index_type: str = "IVF_FLAT"
    nlist: int = 1024  # Number of clusters for IVF
    nprobe: int = 64   # Number of clusters to search
    batch_size: int = 1000
    max_connections: int = 100
    
    # NVIDIA cuVS specific settings
    gpu_memory_fraction: float = 0.8
    enable_gpu_acceleration: bool = True
    
    # Storage settings
    persist_directory: str = "data/vector_db"
    backup_enabled: bool = True
    backup_interval_hours: int = 6

@dataclass
class RAGConfig:
    """RAG Pipeline Configuration"""
    # Retrieval settings
    top_k_retrieval: int = 20
    top_k_rerank: int = 10
    similarity_threshold: float = 0.7
    
    # NeMo Retriever settings
    retriever_model: str = "nvidia/nemo-retriever-v1"
    reranker_model: str = "nvidia/nemo-reranker-v1"
    
    # Context generation
    max_context_length: int = 8192
    context_overlap: int = 200
    chunk_size: int = 1000
    
    # Embedding model
    embedding_model: str = "nvidia/nemo-embed-v1"
    embedding_batch_size: int = 32

@dataclass
class AgentConfig:
    """Agentic Reasoning Configuration"""
    # Core reasoning model
    reasoning_model: str = "nvidia/llama-nemo-70b"
    planning_model: str = "nvidia/llama-nemo-70b"
    reflection_model: str = "nvidia/llama-nemo-70b"
    
    # Reasoning parameters
    max_reasoning_steps: int = 10
    reflection_threshold: float = 0.8
    planning_depth: int = 3
    
    # Temperature settings
    planning_temperature: float = 0.3
    reasoning_temperature: float = 0.5
    reflection_temperature: float = 0.2
    
    # Context management
    max_context_tokens: int = 32768
    memory_window: int = 10  # Number of previous interactions to remember

@dataclass
class MCPConfig:
    """Model Context Protocol Configuration"""
    # Tool calling settings
    max_tool_calls: int = 5
    tool_timeout: int = 30
    parallel_tools: bool = True
    
    # Available tools
    enabled_tools: List[str] = field(default_factory=lambda: [
        "web_search",
        "fact_checker",
        "sentiment_analyzer",
        "trend_detector",
        "report_generator",
        "data_visualizer"
    ])
    
    # External API configurations
    tavily_api_key: Optional[str] = None
    serp_api_key: Optional[str] = None
    
    # Memory management
    context_memory_size: int = 1000
    session_timeout: int = 3600  # 1 hour

@dataclass
class CrawlerConfig:
    """Multi-Platform Crawler Configuration"""
    # Platform-specific settings
    platforms: Dict[PlatformType, Dict[str, Any]] = field(default_factory=lambda: {
        PlatformType.FACEBOOK: {
            "enabled": True,
            "rate_limit": 100,  # requests per hour
            "max_posts": 1000,
            "include_comments": True,
            "max_comments_per_post": 100
        },
        PlatformType.INSTAGRAM: {
            "enabled": True,
            "rate_limit": 200,
            "max_posts": 500,
            "include_stories": True,
            "story_retention_hours": 24
        },
        PlatformType.TWITTER: {
            "enabled": True,
            "rate_limit": 300,
            "max_tweets": 1000,
            "include_replies": True,
            "max_replies_per_tweet": 50
        },
        PlatformType.TIKTOK: {
            "enabled": True,
            "rate_limit": 50,
            "max_videos": 200,
            "include_comments": True,
            "max_comments_per_video": 100
        },
        PlatformType.GOOGLE: {
            "enabled": True,
            "rate_limit": 1000,
            "max_results": 100,
            "search_depth": 3
        },
        PlatformType.NEWS: {
            "enabled": True,
            "rate_limit": 500,
            "max_articles": 200,
            "sources": ["malaysiakini", "thestar", "nst", "bernama"]
        },
        PlatformType.FORUMS: {
            "enabled": True,
            "rate_limit": 200,
            "max_threads": 100,
            "forums": ["lowyat", "cari", "reddit"]
        }
    })
    
    # General crawler settings
    concurrent_workers: int = 10
    retry_attempts: int = 3
    retry_delay: int = 5
    user_agent_rotation: bool = True
    proxy_enabled: bool = True
    
    # Data processing
    real_time_processing: bool = True
    batch_processing_interval: int = 300  # 5 minutes
    data_retention_days: int = 365

@dataclass
class ReportingConfig:
    """Report Generation Configuration"""
    # Output models
    report_generator_model: str = "meta/llama-3.3-70b"
    visualization_engine: str = "plotly"
    
    # Report types
    supported_formats: List[str] = field(default_factory=lambda: [
        "pdf", "html", "json", "excel", "powerpoint"
    ])
    
    # Visualization settings
    chart_types: List[str] = field(default_factory=lambda: [
        "timeline", "sentiment_trend", "platform_distribution",
        "engagement_metrics", "viral_content", "influence_network"
    ])
    
    # Malaysian-specific settings
    language_support: List[str] = field(default_factory=lambda: [
        "malay", "english", "chinese", "tamil"
    ])
    
    timezone: str = "Asia/Kuala_Lumpur"
    currency: str = "MYR"

@dataclass
class InsightPulseConfig:
    """Master Configuration for InsightPulse Advanced Architecture"""
    
    # Core components
    vector_db: VectorDBConfig = field(default_factory=VectorDBConfig)
    rag: RAGConfig = field(default_factory=RAGConfig)
    agent: AgentConfig = field(default_factory=AgentConfig)
    mcp: MCPConfig = field(default_factory=MCPConfig)
    crawler: CrawlerConfig = field(default_factory=CrawlerConfig)
    reporting: ReportingConfig = field(default_factory=ReportingConfig)
    
    # System settings
    environment: str = "production"
    debug_mode: bool = False
    log_level: str = "INFO"
    
    # Performance settings
    max_concurrent_requests: int = 100
    request_timeout: int = 30
    cache_enabled: bool = True
    cache_ttl: int = 3600
    
    # Security settings
    api_key_required: bool = True
    rate_limiting_enabled: bool = True
    data_encryption: bool = True
    
    # Malaysian compliance
    data_localization: bool = True
    pdpa_compliance: bool = True
    
    @classmethod
    def load_from_env(cls) -> 'InsightPulseConfig':
        """Load configuration from environment variables"""
        config = cls()
        
        # Load API keys from environment
        config.mcp.tavily_api_key = os.getenv('TAVILY_API_KEY')
        config.mcp.serp_api_key = os.getenv('SERP_API_KEY')
        
        # Load other environment-specific settings
        config.environment = os.getenv('ENVIRONMENT', 'production')
        config.debug_mode = os.getenv('DEBUG_MODE', 'false').lower() == 'true'
        
        return config
    
    def validate(self) -> List[str]:
        """Validate configuration and return list of issues"""
        issues = []
        
        # Check required API keys
        if not self.mcp.tavily_api_key:
            issues.append("TAVILY_API_KEY not set")
        
        # Check vector DB settings
        if self.vector_db.dimension <= 0:
            issues.append("Vector dimension must be positive")
        
        # Check crawler settings
        total_rate_limit = sum(
            platform_config.get('rate_limit', 0) 
            for platform_config in self.crawler.platforms.values()
        )
        if total_rate_limit > 10000:
            issues.append("Total rate limit too high, may cause API issues")
        
        return issues

# Default configuration instance
DEFAULT_CONFIG = InsightPulseConfig.load_from_env()
