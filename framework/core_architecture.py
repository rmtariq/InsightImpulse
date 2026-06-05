"""
Universal Social Listening App - Core Architecture
Phase 1: Advanced NLP-Powered Input Processing & Keyword Extraction
"""

import asyncio
import logging
from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import re
from datetime import datetime

# Advanced NLP Libraries
try:
    from keybert import KeyBERT
    from sentence_transformers import SentenceTransformer
    import spacy
    from transformers import pipeline, AutoTokenizer, AutoModel
    import numpy as np
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
except ImportError as e:
    logging.warning(f"Some NLP libraries not installed: {e}")

class IndustryType(Enum):
    """Industry classification for context-aware processing"""
    SME_BUSINESS = "sme_business"
    HEALTHCARE = "healthcare"
    FINANCIAL_SERVICES = "financial_services"
    TECHNOLOGY = "technology"
    RETAIL_ECOMMERCE = "retail_ecommerce"
    FOOD_BEVERAGE = "food_beverage"
    TRAVEL_TOURISM = "travel_tourism"
    EDUCATION = "education"
    AUTOMOTIVE = "automotive"
    REAL_ESTATE = "real_estate"
    FASHION_BEAUTY = "fashion_beauty"
    GENERAL = "general"

class PlatformType(Enum):
    """Supported social media platforms"""
    FACEBOOK = "facebook"
    TWITTER = "twitter"
    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"
    LINKEDIN = "linkedin"
    YOUTUBE = "youtube"
    REDDIT = "reddit"
    DISCORD = "discord"
    SHOPEE = "shopee"
    LAZADA = "lazada"
    LOCAL_NEWS = "local_news"
    FORUMS = "forums"

@dataclass
class KeywordExtractionResult:
    """Result structure for keyword extraction"""
    primary_keywords: List[str]
    semantic_keywords: List[str]
    named_entities: Dict[str, List[str]]
    industry_terms: List[str]
    expanded_queries: List[str]
    confidence_scores: Dict[str, float]
    processing_time: float

@dataclass
class QueryContext:
    """Context information for query processing"""
    original_query: str
    detected_industry: IndustryType
    user_type: str
    language: str = "en"
    region: str = "malaysia"
    intent_type: str = "monitoring"
    urgency_level: str = "normal"

class UniversalNLPProcessor:
    """Enhanced Universal NLP processor with latest framework updates"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.initialize_enhanced_models()
        self.load_industry_databases()
        self.setup_crisis_detection()
        self.initialize_real_time_processing()
        
    def initialize_enhanced_models(self):
        """Initialize enhanced NLP models with latest framework updates"""
        try:
            # Enhanced KeyBERT + Word2Vec combination
            self.keybert_model = KeyBERT('distilbert-base-nli-mean-tokens')

            # Sentence transformer for semantic similarity
            self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')

            # Enhanced spaCy with NER for brands, locations, people
            try:
                self.nlp = spacy.load("en_core_web_sm")
                # Add custom NER patterns for Malaysian context
                self.setup_malaysian_ner()
            except OSError:
                self.logger.warning("spaCy English model not found. Using basic processing.")
                self.nlp = None

            # Multi-layered sentiment analysis
            self.sentiment_analyzer = pipeline(
                "sentiment-analysis",
                model="cardiffnlp/twitter-roberta-base-sentiment-latest"
            )

            # Emotion clustering model
            self.emotion_analyzer = pipeline(
                "text-classification",
                model="j-hartmann/emotion-english-distilroberta-base"
            )

            # Enhanced industry classification
            self.industry_classifier = pipeline(
                "zero-shot-classification",
                model="facebook/bart-large-mnli"
            )

            # Crisis detection model
            self.crisis_detector = pipeline(
                "text-classification",
                model="unitary/toxic-bert"
            )

            self.logger.info("Enhanced NLP models initialized successfully")

        except Exception as e:
            self.logger.error(f"Error initializing enhanced NLP models: {e}")
            self.use_fallback_models()
    
    def use_fallback_models(self):
        """Fallback to basic processing if advanced models fail"""
        self.keybert_model = None
        self.sentence_model = None
        self.nlp = None
        self.sentiment_analyzer = None
        self.industry_classifier = None
        self.logger.info("Using fallback processing methods")
    
    def load_industry_databases(self):
        """Load enhanced industry-specific databases with latest framework"""
        self.industry_terms = {
            IndustryType.SME_BUSINESS: {
                "keywords": ["business", "entrepreneur", "startup", "revenue", "profit", "customer",
                           "marketing", "sales", "growth", "competition", "market share", "ROI"],
                "sentiment_weights": {"trust": 2.0, "reliability": 1.8, "value": 1.6},
                "crisis_indicators": ["complaint", "fraud", "scam", "poor service", "overpriced"],
                "opportunity_signals": ["expansion", "new market", "partnership", "investment"]
            },
            IndustryType.HEALTHCARE: {
                "keywords": ["health", "medical", "doctor", "hospital", "treatment", "medicine",
                           "patient", "clinic", "diagnosis", "therapy", "wellness", "pharmaceutical"],
                "sentiment_weights": {"safety": 2.5, "effectiveness": 2.0, "care": 1.8},
                "crisis_indicators": ["adverse reaction", "medical error", "malpractice", "unsafe"],
                "opportunity_signals": ["breakthrough", "cure", "improvement", "recovery"]
            },
            IndustryType.TECHNOLOGY: {
                "keywords": ["software", "app", "digital", "AI", "machine learning", "cloud",
                           "cybersecurity", "data", "algorithm", "programming", "tech", "innovation"],
                "sentiment_weights": {"innovation": 2.0, "usability": 1.8, "security": 2.2},
                "crisis_indicators": ["bug", "crash", "hack", "data breach", "vulnerability"],
                "opportunity_signals": ["upgrade", "feature", "integration", "automation"]
            },
            IndustryType.RETAIL_ECOMMERCE: {
                "keywords": ["shopping", "retail", "ecommerce", "online store", "product", "brand",
                           "customer service", "delivery", "payment", "discount", "sale", "marketplace"],
                "sentiment_weights": {"quality": 2.0, "service": 1.9, "value": 1.7},
                "crisis_indicators": ["defective", "delayed", "poor quality", "bad service"],
                "opportunity_signals": ["trending", "popular", "bestseller", "recommended"]
            },
            IndustryType.FINANCIAL_SERVICES: {
                "keywords": ["bank", "loan", "investment", "insurance", "finance", "credit",
                           "mortgage", "savings", "trading", "portfolio", "wealth", "financial"],
                "sentiment_weights": {"trust": 2.5, "security": 2.3, "transparency": 2.0},
                "crisis_indicators": ["fraud", "scam", "hidden fees", "poor service", "loss"],
                "opportunity_signals": ["profit", "growth", "returns", "opportunity", "bonus"]
            }
        }
        
        # Malaysian-specific terms
        self.malaysian_terms = [
            "malaysia", "kuala lumpur", "kl", "selangor", "johor", "penang",
            "sabah", "sarawak", "ringgit", "rm", "malaysian", "local", "tempatan"
        ]
        
        # Platform-specific optimization terms
        self.platform_terms = {
            PlatformType.TIKTOK: ["viral", "trending", "challenge", "fyp", "duet"],
            PlatformType.INSTAGRAM: ["story", "reel", "post", "hashtag", "influencer"],
            PlatformType.LINKEDIN: ["professional", "career", "business", "networking"],
            PlatformType.YOUTUBE: ["video", "tutorial", "review", "subscribe", "channel"]
        }

        self.logger.info("Enhanced industry databases loaded successfully")

    def setup_malaysian_ner(self):
        """Setup Malaysian-specific Named Entity Recognition"""
        if self.nlp:
            # Add Malaysian brands, locations, and entities
            malaysian_entities = [
                ("Genting", "ORG"), ("Petronas", "ORG"), ("Maybank", "ORG"),
                ("Kuala Lumpur", "GPE"), ("Selangor", "GPE"), ("Johor", "GPE"),
                ("Penang", "GPE"), ("Sabah", "GPE"), ("Sarawak", "GPE"),
                ("Ringgit", "MONEY"), ("RM", "MONEY"), ("sen", "MONEY")
            ]

            # Add patterns to NER
            try:
                ruler = self.nlp.add_pipe("entity_ruler", before="ner")
                patterns = [{"label": label, "pattern": text} for text, label in malaysian_entities]
                ruler.add_patterns(patterns)
            except Exception as e:
                self.logger.warning(f"Could not setup Malaysian NER: {e}")

    def setup_crisis_detection(self):
        """Setup crisis detection system"""
        self.crisis_keywords = {
            "urgent": ["urgent", "emergency", "crisis", "critical", "immediate"],
            "negative_sentiment": ["hate", "angry", "furious", "disappointed", "terrible"],
            "brand_damage": ["boycott", "scandal", "controversy", "lawsuit", "investigation"],
            "service_issues": ["down", "broken", "not working", "failed", "error"]
        }

        self.crisis_thresholds = {
            "mention_spike": 5.0,  # 5x normal volume
            "negative_sentiment": 0.7,  # 70% negative
            "urgency_score": 0.8  # 80% urgency indicators
        }

    def initialize_real_time_processing(self):
        """Initialize real-time processing capabilities"""
        self.real_time_buffer = []
        self.processing_queue = []
        # Note: AlertSystem and TrendDetector would be implemented separately
        self.logger.info("Real-time processing initialized")

    async def process_query(self, query: str, user_context: Optional[Dict] = None) -> Tuple[KeywordExtractionResult, QueryContext]:
        """Main query processing pipeline"""
        start_time = datetime.now()
        
        # Step 1: Detect query context and industry
        context = await self.detect_query_context(query, user_context)
        
        # Step 2: Extract keywords using multiple methods
        extraction_result = await self.extract_keywords_comprehensive(query, context)
        
        # Step 3: Expand queries for maximum coverage
        expanded_queries = await self.expand_queries(query, extraction_result, context)
        extraction_result.expanded_queries = expanded_queries
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds()
        extraction_result.processing_time = processing_time
        
        return extraction_result, context
    
    async def detect_query_context(self, query: str, user_context: Optional[Dict] = None) -> QueryContext:
        """Detect industry and context from query"""
        
        # Industry detection using zero-shot classification
        industry_labels = [industry.value for industry in IndustryType]
        
        if self.industry_classifier:
            try:
                result = self.industry_classifier(query, industry_labels)
                detected_industry = IndustryType(result['labels'][0])
            except:
                detected_industry = IndustryType.GENERAL
        else:
            detected_industry = self.detect_industry_fallback(query)
        
        # Detect language (basic implementation)
        language = "ms" if any(word in query.lower() for word in ["dan", "atau", "untuk", "di", "ke"]) else "en"
        
        # Detect intent type
        intent_type = "monitoring"
        if any(word in query.lower() for word in ["crisis", "urgent", "problem", "complaint"]):
            intent_type = "crisis"
        elif any(word in query.lower() for word in ["trend", "popular", "viral", "new"]):
            intent_type = "trending"
        elif any(word in query.lower() for word in ["competitor", "competition", "vs", "compare"]):
            intent_type = "competitive"
        
        return QueryContext(
            original_query=query,
            detected_industry=detected_industry,
            user_type=user_context.get('user_type', 'general') if user_context else 'general',
            language=language,
            region=user_context.get('region', 'malaysia') if user_context else 'malaysia',
            intent_type=intent_type
        )
    
    def detect_industry_fallback(self, query: str) -> IndustryType:
        """Fallback industry detection using keyword matching"""
        query_lower = query.lower()
        
        for industry, terms in self.industry_terms.items():
            if any(term in query_lower for term in terms):
                return industry
        
        return IndustryType.GENERAL
    
    async def extract_keywords_comprehensive(self, query: str, context: QueryContext) -> KeywordExtractionResult:
        """Comprehensive keyword extraction using multiple methods"""
        
        # Method 1: KeyBERT for semantic keywords
        semantic_keywords = await self.extract_keybert_keywords(query)
        
        # Method 2: TextRank with Word2Vec enhancement
        textrank_keywords = await self.extract_textrank_keywords(query)
        
        # Method 3: TF-IDF with domain-specific weighting
        tfidf_keywords = await self.extract_tfidf_keywords(query, context)
        
        # Method 4: Named Entity Recognition
        named_entities = await self.extract_named_entities(query)
        
        # Method 5: Industry-specific term extraction
        industry_terms = await self.extract_industry_terms(query, context)
        
        # Combine and rank all keywords
        primary_keywords = self.combine_and_rank_keywords(
            semantic_keywords, textrank_keywords, tfidf_keywords
        )
        
        # Calculate confidence scores
        confidence_scores = self.calculate_confidence_scores(
            primary_keywords, semantic_keywords, named_entities
        )
        
        return KeywordExtractionResult(
            primary_keywords=primary_keywords[:15],  # Top 15 primary keywords
            semantic_keywords=semantic_keywords[:10],
            named_entities=named_entities,
            industry_terms=industry_terms,
            expanded_queries=[],  # Will be filled later
            confidence_scores=confidence_scores,
            processing_time=0.0  # Will be calculated later
        )
    
    async def extract_keybert_keywords(self, query: str) -> List[str]:
        """Extract keywords using KeyBERT"""
        if not self.keybert_model:
            return self.extract_keywords_fallback(query)
        
        try:
            keywords = self.keybert_model.extract_keywords(
                query, 
                keyphrase_ngram_range=(1, 3), 
                stop_words='english',
                top_k=10,
                use_mmr=True,
                diversity=0.5
            )
            return [kw[0] for kw in keywords]
        except Exception as e:
            self.logger.error(f"KeyBERT extraction failed: {e}")
            return self.extract_keywords_fallback(query)
    
    async def extract_textrank_keywords(self, query: str) -> List[str]:
        """Extract keywords using TextRank algorithm"""
        # Simplified TextRank implementation
        words = re.findall(r'\b\w+\b', query.lower())
        words = [w for w in words if len(w) > 2]
        
        # Remove duplicates while preserving order
        unique_words = []
        seen = set()
        for word in words:
            if word not in seen:
                unique_words.append(word)
                seen.add(word)
        
        return unique_words[:8]
    
    async def extract_tfidf_keywords(self, query: str, context: QueryContext) -> List[str]:
        """Extract keywords using TF-IDF with domain weighting"""
        # Basic TF-IDF implementation for single query
        words = re.findall(r'\b\w+\b', query.lower())
        words = [w for w in words if len(w) > 2]
        
        # Apply domain-specific weighting
        industry_terms = self.industry_terms.get(context.detected_industry, [])
        weighted_words = []
        
        for word in words:
            weight = 2.0 if word in industry_terms else 1.0
            weighted_words.extend([word] * int(weight))
        
        return list(set(weighted_words))[:10]
    
    async def extract_named_entities(self, query: str) -> Dict[str, List[str]]:
        """Extract named entities using spaCy"""
        if not self.nlp:
            return self.extract_entities_fallback(query)
        
        try:
            doc = self.nlp(query)
            entities = {
                "PERSON": [],
                "ORG": [],
                "GPE": [],  # Geopolitical entities
                "PRODUCT": [],
                "MONEY": [],
                "DATE": []
            }
            
            for ent in doc.ents:
                if ent.label_ in entities:
                    entities[ent.label_].append(ent.text)
            
            return {k: list(set(v)) for k, v in entities.items() if v}
        except Exception as e:
            self.logger.error(f"NER extraction failed: {e}")
            return self.extract_entities_fallback(query)
    
    def extract_entities_fallback(self, query: str) -> Dict[str, List[str]]:
        """Fallback entity extraction using pattern matching"""
        entities = {"ORG": [], "GPE": [], "MONEY": []}
        
        # Simple pattern matching for Malaysian context
        if "malaysia" in query.lower():
            entities["GPE"].append("Malaysia")
        
        # Money pattern matching
        money_pattern = r'rm\s*\d+(?:,\d{3})*(?:\.\d{2})?'
        money_matches = re.findall(money_pattern, query.lower())
        entities["MONEY"].extend(money_matches)
        
        return {k: v for k, v in entities.items() if v}
    
    async def extract_industry_terms(self, query: str, context: QueryContext) -> List[str]:
        """Extract industry-specific terms"""
        query_lower = query.lower()
        industry_terms = self.industry_terms.get(context.detected_industry, [])
        
        found_terms = [term for term in industry_terms if term in query_lower]
        
        # Add Malaysian-specific terms if relevant
        malaysian_found = [term for term in self.malaysian_terms if term in query_lower]
        found_terms.extend(malaysian_found)
        
        return list(set(found_terms))
    
    def extract_keywords_fallback(self, query: str) -> List[str]:
        """Fallback keyword extraction using basic methods"""
        words = re.findall(r'\b\w+\b', query.lower())
        
        # Filter out stop words and short words
        stop_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        keywords = [w for w in words if len(w) > 2 and w not in stop_words]
        
        return list(set(keywords))[:10]
    
    def combine_and_rank_keywords(self, *keyword_lists) -> List[str]:
        """Combine and rank keywords from multiple extraction methods"""
        keyword_scores = {}
        
        for i, keyword_list in enumerate(keyword_lists):
            weight = 1.0 / (i + 1)  # Higher weight for earlier methods
            for keyword in keyword_list:
                if keyword in keyword_scores:
                    keyword_scores[keyword] += weight
                else:
                    keyword_scores[keyword] = weight
        
        # Sort by score and return top keywords
        sorted_keywords = sorted(keyword_scores.items(), key=lambda x: x[1], reverse=True)
        return [kw[0] for kw in sorted_keywords]
    
    def calculate_confidence_scores(self, primary_keywords: List[str], 
                                  semantic_keywords: List[str], 
                                  named_entities: Dict[str, List[str]]) -> Dict[str, float]:
        """Calculate confidence scores for extracted keywords"""
        scores = {}
        
        for keyword in primary_keywords:
            score = 0.5  # Base score
            
            # Boost if found in semantic keywords
            if keyword in semantic_keywords:
                score += 0.3
            
            # Boost if it's a named entity
            for entity_list in named_entities.values():
                if keyword in entity_list:
                    score += 0.2
                    break
            
            scores[keyword] = min(score, 1.0)
        
        return scores
    
    async def expand_queries(self, original_query: str, 
                           extraction_result: KeywordExtractionResult,
                           context: QueryContext) -> List[str]:
        """Expand queries for maximum platform coverage"""
        expanded = []
        
        # Original query variations
        expanded.append(original_query)
        expanded.append(f'"{original_query}"')  # Exact match
        
        # Keyword combinations
        primary_kw = extraction_result.primary_keywords[:5]
        for i in range(len(primary_kw)):
            for j in range(i+1, len(primary_kw)):
                expanded.append(f"{primary_kw[i]} {primary_kw[j]}")
        
        # Industry-specific expansions
        industry_terms = extraction_result.industry_terms
        for term in industry_terms[:3]:
            expanded.append(f"{original_query} {term}")
        
        # Regional expansions
        if context.region == "malaysia":
            expanded.extend([
                f"{original_query} malaysia",
                f"{original_query} malaysian",
                f"{original_query} local"
            ])
        
        # Platform-specific expansions
        for platform, terms in self.platform_terms.items():
            for term in terms[:2]:
                expanded.append(f"{original_query} {term}")
        
        # Remove duplicates and return
        return list(set(expanded))[:25]  # Limit to 25 expanded queries

# Example usage and testing
async def main():
    processor = UniversalNLPProcessor()
    
    test_queries = [
        "best smartphone 2025 malaysia",
        "healthy food recipes for diabetes",
        "SME business loan requirements",
        "trending fashion brands in KL",
        "cybersecurity threats for small business"
    ]
    
    print("=== UNIVERSAL NLP PROCESSOR TESTING ===\n")
    
    for query in test_queries:
        print(f"🔍 PROCESSING: '{query}'")
        print("=" * 60)
        
        try:
            result, context = await processor.process_query(query)
            
            print(f"📊 DETECTED INDUSTRY: {context.detected_industry.value}")
            print(f"🌐 LANGUAGE: {context.language}")
            print(f"🎯 INTENT: {context.intent_type}")
            print(f"⏱️ PROCESSING TIME: {result.processing_time:.3f}s")
            
            print(f"\n🎯 PRIMARY KEYWORDS ({len(result.primary_keywords)}):")
            print(f"   {result.primary_keywords}")
            
            print(f"\n🧠 SEMANTIC KEYWORDS ({len(result.semantic_keywords)}):")
            print(f"   {result.semantic_keywords}")
            
            if result.named_entities:
                print(f"\n👤 NAMED ENTITIES:")
                for entity_type, entities in result.named_entities.items():
                    print(f"   {entity_type}: {entities}")
            
            if result.industry_terms:
                print(f"\n🏭 INDUSTRY TERMS: {result.industry_terms}")
            
            print(f"\n📈 EXPANDED QUERIES ({len(result.expanded_queries)}):")
            for i, expanded in enumerate(result.expanded_queries[:5]):
                print(f"   {i+1}. {expanded}")
            if len(result.expanded_queries) > 5:
                print(f"   ... and {len(result.expanded_queries) - 5} more")
            
            print(f"\n🎯 CONFIDENCE SCORES:")
            for keyword, score in list(result.confidence_scores.items())[:5]:
                print(f"   {keyword}: {score:.2f}")
            
        except Exception as e:
            print(f"❌ ERROR: {e}")
        
        print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    asyncio.run(main())
