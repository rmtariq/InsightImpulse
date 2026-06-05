"""
Advanced NLP Processor for InsightPulse
Implements Phase 1: Input Processing & Keyword Extraction

Features:
- KeyBERT + Word2Vec combination for semantic understanding
- TextRank with Word2Vec enhancement for social media text
- TF-IDF hybrid with domain-specific weighting
- Named Entity Recognition (NER) for brands, locations, people
- Dynamic Query Expansion with synonym detection
"""

import re
import logging
from typing import List, Dict, Any, Tuple, Optional
from collections import Counter, defaultdict
import numpy as np

# Core NLP libraries
import spacy
from spacy import displacy
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.stem import WordNetLemmatizer

# Advanced keyword extraction
try:
    from keybert import KeyBERT
    from sentence_transformers import SentenceTransformer
    KEYBERT_AVAILABLE = True
except ImportError:
    KEYBERT_AVAILABLE = False
    print("KeyBERT not available. Install with: pip install keybert sentence-transformers")

# Word2Vec and embeddings
try:
    from gensim.models import Word2Vec
    from gensim.models.keyedvectors import KeyedVectors
    WORD2VEC_AVAILABLE = True
except ImportError:
    WORD2VEC_AVAILABLE = False
    print("Gensim not available. Install with: pip install gensim")

# TextRank
try:
    import networkx as nx
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    TEXTRANK_AVAILABLE = True
except ImportError:
    TEXTRANK_AVAILABLE = False
    print("NetworkX/Sklearn not available for TextRank")

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AdvancedNLPProcessor:
    """
    Advanced NLP processor implementing multiple keyword extraction methods
    optimized for Malaysian social media content and business intelligence
    """
    
    def __init__(self):
        self.setup_nltk()
        self.setup_spacy()
        self.setup_keybert()
        self.setup_malaysian_context()
        self.setup_industry_databases()
        
        # Initialize components
        self.lemmatizer = WordNetLemmatizer()
        self.stop_words = set(stopwords.words('english'))
        
        # Malaysian stop words
        self.malaysian_stop_words = {
            'yang', 'dan', 'di', 'ke', 'dari', 'untuk', 'dengan', 'pada', 'adalah', 'ini', 'itu',
            'akan', 'telah', 'sudah', 'boleh', 'tidak', 'tak', 'juga', 'atau', 'kalau', 'bila',
            'saya', 'kami', 'kita', 'mereka', 'dia', 'beliau', 'awak', 'anda'
        }
        self.stop_words.update(self.malaysian_stop_words)
        
        logger.info("✅ Advanced NLP Processor initialized successfully")
    
    def setup_nltk(self):
        """Download required NLTK data"""
        try:
            nltk.data.find('tokenizers/punkt')
            nltk.data.find('corpora/stopwords')
            nltk.data.find('corpora/wordnet')
            nltk.data.find('taggers/averaged_perceptron_tagger')
        except LookupError:
            nltk.download('punkt')
            nltk.download('stopwords')
            nltk.download('wordnet')
            nltk.download('averaged_perceptron_tagger')
    
    def setup_spacy(self):
        """Setup spaCy for NER"""
        try:
            self.nlp = spacy.load("en_core_web_sm")
            logger.info("✅ spaCy English model loaded")
        except OSError:
            logger.warning("❌ spaCy English model not found. Install with: python -m spacy download en_core_web_sm")
            self.nlp = None
    
    def setup_keybert(self):
        """Setup KeyBERT for semantic keyword extraction"""
        if KEYBERT_AVAILABLE:
            try:
                # Try different models in order of preference
                models_to_try = [
                    'all-MiniLM-L6-v2',  # Lightweight and fast
                    'paraphrase-MiniLM-L6-v2',  # Alternative
                    'all-mpnet-base-v2'  # More accurate but slower
                ]

                for model_name in models_to_try:
                    try:
                        logger.info(f"🔄 Trying to load model: {model_name}")
                        self.sentence_model = SentenceTransformer(model_name)
                        self.keybert_model = KeyBERT(model=self.sentence_model)
                        logger.info(f"✅ KeyBERT initialized with model: {model_name}")
                        return
                    except Exception as model_error:
                        logger.warning(f"❌ Failed to load {model_name}: {model_error}")
                        continue

                # If all models fail, set to None
                logger.warning("❌ All KeyBERT models failed to load")
                self.keybert_model = None

            except Exception as e:
                logger.warning(f"❌ KeyBERT initialization failed: {e}")
                self.keybert_model = None
        else:
            self.keybert_model = None
    
    def setup_malaysian_context(self):
        """Setup Malaysian-specific context and entities"""
        self.malaysian_entities = {
            'cities': [
                'kuala lumpur', 'kl', 'johor bahru', 'jb', 'penang', 'ipoh', 'shah alam',
                'petaling jaya', 'pj', 'subang jaya', 'klang', 'seremban', 'malacca', 'melaka',
                'kuching', 'kota kinabalu', 'kk', 'alor setar', 'kuantan', 'kota bharu',
                'terengganu', 'kelantan', 'pahang', 'perak', 'negeri sembilan', 'selangor',
                'sabah', 'sarawak', 'perlis', 'kedah'
            ],
            'brands': [
                'maybank', 'cimb', 'public bank', 'rhb', 'ambank', 'hong leong',
                'genting', 'petronas', 'proton', 'perodua', 'airasia', 'malindo',
                'astro', 'tm', 'maxis', 'celcom', 'digi', 'u mobile',
                'shopee', 'lazada', 'grab', 'foodpanda', 'zalora', 'mudah.my'
            ],
            'food': [
                'nasi lemak', 'rendang', 'satay', 'laksa', 'char kway teow', 'roti canai',
                'mee goreng', 'nasi goreng', 'teh tarik', 'kopi o', 'cendol', 'abc',
                'durian', 'rambutan', 'mangosteen', 'halal', 'non-halal', 'makanan',
                'sedap', 'makan', 'restaurant', 'kedai makan', 'warung', 'mamak',
                'dim sum', 'yum cha', 'bak kut teh', 'hokkien mee', 'assam laksa',
                'curry', 'sambal', 'belacan', 'tempoyak', 'keropok', 'kerabu',
                'rojak', 'cendol', 'ais kacang', 'taufufah', 'apam balik'
            ],
            'culture': [
                'hari raya', 'chinese new year', 'deepavali', 'christmas', 'wesak day',
                'merdeka', 'malaysia day', 'ramadan', 'puasa', 'berbuka', 'sahur',
                'balik kampung', 'gotong royong', 'kenduri', 'majlis'
            ]
        }
        
        # Flatten all entities for quick lookup
        self.all_malaysian_entities = set()
        for category, entities in self.malaysian_entities.items():
            self.all_malaysian_entities.update([entity.lower() for entity in entities])
    
    def setup_industry_databases(self):
        """Setup industry-specific term databases"""
        self.industry_terms = {
            'healthcare': {
                'terms': ['hospital', 'klinik', 'doktor', 'nurse', 'ubat', 'medicine', 'treatment', 'surgery', 'patient', 'health'],
                'weight': 1.5
            },
            'finance': {
                'terms': ['bank', 'loan', 'investment', 'insurance', 'takaful', 'mortgage', 'credit', 'savings', 'fd', 'asb'],
                'weight': 1.4
            },
            'technology': {
                'terms': ['smartphone', 'laptop', 'computer', 'software', 'app', 'digital', 'online', 'internet', 'wifi', '5g'],
                'weight': 1.3
            },
            'food': {
                'terms': ['restaurant', 'food', 'makan', 'makanan', 'delivery', 'halal', 'recipe', 'cooking', 'chef', 'menu', 'taste', 'sedap', 'delicious', 'warung', 'mamak', 'kedai', 'cuisine', 'dish', 'meal', 'dining'],
                'weight': 1.4
            },
            'retail': {
                'terms': ['shopping', 'mall', 'store', 'sale', 'discount', 'promotion', 'brand', 'fashion', 'clothes', 'shoes'],
                'weight': 1.2
            }
        }
    
    def extract_keywords_keybert(self, text: str, top_k: int = 10) -> List[Tuple[str, float]]:
        """Extract keywords using KeyBERT with semantic understanding"""
        if not self.keybert_model:
            return []
        
        try:
            # Extract keywords with diversity for better coverage
            keywords = self.keybert_model.extract_keywords(
                text, 
                keyphrase_ngram_range=(1, 3),  # 1-3 word phrases
                stop_words='english',
                use_maxsum=True,  # Use Max Sum Similarity for diversity
                nr_candidates=20,  # Consider more candidates
                top_k=top_k,
                diversity=0.7  # Balance between relevance and diversity
            )
            return keywords
        except Exception as e:
            logger.warning(f"KeyBERT extraction failed: {e}")
            return []
    
    def extract_keywords_textrank(self, text: str, top_k: int = 10) -> List[Tuple[str, float]]:
        """Extract keywords using TextRank algorithm optimized for social media"""
        if not TEXTRANK_AVAILABLE:
            return []
        
        try:
            # Preprocess text
            sentences = sent_tokenize(text)
            if len(sentences) < 2:
                return []
            
            # Create TF-IDF vectors
            vectorizer = TfidfVectorizer(
                max_features=100,
                stop_words='english',
                ngram_range=(1, 2),
                lowercase=True
            )
            
            tfidf_matrix = vectorizer.fit_transform(sentences)
            
            # Calculate similarity matrix
            similarity_matrix = cosine_similarity(tfidf_matrix)
            
            # Create graph and apply PageRank
            nx_graph = nx.from_numpy_array(similarity_matrix)
            scores = nx.pagerank(nx_graph, max_iter=100, tol=1e-4)
            
            # Get feature names and calculate keyword scores
            feature_names = vectorizer.get_feature_names_out()
            keyword_scores = defaultdict(float)
            
            for i, sentence in enumerate(sentences):
                sentence_score = scores.get(i, 0)
                words = word_tokenize(sentence.lower())
                for word in words:
                    if word in feature_names and word not in self.stop_words:
                        keyword_scores[word] += sentence_score
            
            # Sort and return top keywords
            sorted_keywords = sorted(keyword_scores.items(), key=lambda x: x[1], reverse=True)
            return sorted_keywords[:top_k]
            
        except Exception as e:
            logger.warning(f"TextRank extraction failed: {e}")
            return []
    
    def extract_keywords_tfidf_hybrid(self, text: str, top_k: int = 10) -> List[Tuple[str, float]]:
        """Extract keywords using TF-IDF with domain-specific weighting"""
        try:
            # Simple word-based extraction as fallback
            import re

            # Clean and tokenize text
            text_clean = re.sub(r'[^\w\s]', ' ', text.lower())
            words = text_clean.split()

            # Remove stop words and short words
            words = [word for word in words
                    if word not in self.stop_words and len(word) > 2]

            if not words:
                return []

            # Calculate term frequency
            word_freq = Counter(words)
            max_freq = max(word_freq.values()) if word_freq else 1

            # Normalize TF and apply domain weighting
            keyword_scores = {}
            for word, freq in word_freq.items():
                tf_score = freq / max_freq

                # Apply industry-specific weighting
                domain_weight = 1.0
                for industry, data in self.industry_terms.items():
                    if word in data['terms']:
                        domain_weight = data['weight']
                        break

                # Apply Malaysian context weighting
                malaysian_weight = 1.3 if word in self.all_malaysian_entities else 1.0

                # Apply food context weighting for Malaysian food terms
                food_weight = 1.5 if word in ['makanan', 'halal', 'sedap', 'makan', 'food', 'restaurant'] else 1.0

                # Final score
                keyword_scores[word] = tf_score * domain_weight * malaysian_weight * food_weight

            # Sort and return top keywords
            sorted_keywords = sorted(keyword_scores.items(), key=lambda x: x[1], reverse=True)
            return sorted_keywords[:top_k]

        except Exception as e:
            logger.warning(f"TF-IDF hybrid extraction failed: {e}")
            # Ultimate fallback - just split the text
            try:
                words = text.lower().split()
                words = [word for word in words if len(word) > 2]
                return [(word, 1.0) for word in words[:top_k]]
            except:
                return []
    
    def extract_named_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract named entities (brands, locations, people) using spaCy + Malaysian context"""
        entities = {
            'PERSON': [],
            'ORG': [],
            'GPE': [],  # Geopolitical entities (countries, cities, states)
            'PRODUCT': [],
            'MALAYSIAN_BRAND': [],
            'MALAYSIAN_LOCATION': [],
            'MALAYSIAN_FOOD': [],
            'MALAYSIAN_CULTURE': []
        }
        
        # Use spaCy NER if available
        if self.nlp:
            try:
                doc = self.nlp(text)
                for ent in doc.ents:
                    if ent.label_ in entities:
                        entities[ent.label_].append(ent.text)
            except Exception as e:
                logger.warning(f"spaCy NER failed: {e}")
        
        # Add Malaysian-specific entity detection
        text_lower = text.lower()
        
        # Check for Malaysian entities
        for entity in self.malaysian_entities['brands']:
            if entity in text_lower:
                entities['MALAYSIAN_BRAND'].append(entity.title())
        
        for entity in self.malaysian_entities['cities']:
            if entity in text_lower:
                entities['MALAYSIAN_LOCATION'].append(entity.title())
        
        for entity in self.malaysian_entities['food']:
            if entity in text_lower:
                entities['MALAYSIAN_FOOD'].append(entity.title())
        
        for entity in self.malaysian_entities['culture']:
            if entity in text_lower:
                entities['MALAYSIAN_CULTURE'].append(entity.title())
        
        # Remove duplicates
        for key in entities:
            entities[key] = list(set(entities[key]))
        
        return entities
    
    def expand_query_dynamically(self, query: str) -> Dict[str, Any]:
        """
        Dynamically expand user query using synonym detection and related terms
        """
        expanded_query = {
            'original_query': query,
            'expanded_terms': [],
            'synonyms': [],
            'related_terms': [],
            'industry_context': None,
            'malaysian_context': [],
            'suggested_platforms': []
        }
        
        # Detect industry context
        query_lower = query.lower()
        for industry, data in self.industry_terms.items():
            if any(term in query_lower for term in data['terms']):
                expanded_query['industry_context'] = industry
                # Add related industry terms
                expanded_query['related_terms'].extend([
                    term for term in data['terms'] if term not in query_lower
                ][:5])
                break
        
        # Detect Malaysian context
        for category, entities in self.malaysian_entities.items():
            found_entities = [entity for entity in entities if entity in query_lower]
            if found_entities:
                expanded_query['malaysian_context'].extend(found_entities)
        
        # Suggest relevant platforms based on query content
        platform_suggestions = {
            'facebook': ['business', 'community', 'local', 'family', 'friends'],
            'instagram': ['lifestyle', 'food', 'fashion', 'travel', 'beauty'],
            'tiktok': ['trending', 'viral', 'young', 'entertainment', 'dance'],
            'twitter': ['news', 'politics', 'breaking', 'updates', 'discussion'],
            'linkedin': ['professional', 'career', 'business', 'networking', 'job'],
            'youtube': ['tutorial', 'review', 'video', 'how to', 'guide'],
            'shopee': ['shopping', 'buy', 'product', 'price', 'discount'],
            'lazada': ['online shopping', 'delivery', 'sale', 'electronics']
        }
        
        for platform, keywords in platform_suggestions.items():
            if any(keyword in query_lower for keyword in keywords):
                expanded_query['suggested_platforms'].append(platform)
        
        # If no specific platforms suggested, use general social media platforms
        if not expanded_query['suggested_platforms']:
            expanded_query['suggested_platforms'] = ['facebook', 'instagram', 'twitter']
        
        return expanded_query
    
    def process_input_comprehensive(self, user_input: str) -> Dict[str, Any]:
        """
        Comprehensive input processing combining all extraction methods
        """
        logger.info(f"🔍 Processing input: '{user_input[:50]}...'")
        
        # Initialize results
        results = {
            'original_input': user_input,
            'processed_at': None,
            'keywords': {
                'keybert': [],
                'textrank': [],
                'tfidf_hybrid': [],
                'combined': []
            },
            'named_entities': {},
            'query_expansion': {},
            'confidence_score': 0.0,
            'processing_notes': []
        }
        
        try:
            # 1. Extract keywords using different methods
            logger.info("📊 Extracting keywords with KeyBERT...")
            results['keywords']['keybert'] = self.extract_keywords_keybert(user_input, top_k=8)
            
            logger.info("🕸️ Extracting keywords with TextRank...")
            results['keywords']['textrank'] = self.extract_keywords_textrank(user_input, top_k=8)
            
            logger.info("📈 Extracting keywords with TF-IDF Hybrid...")
            results['keywords']['tfidf_hybrid'] = self.extract_keywords_tfidf_hybrid(user_input, top_k=8)
            
            # 2. Combine and rank all keywords
            all_keywords = defaultdict(float)
            
            # Weight different methods
            method_weights = {'keybert': 0.4, 'textrank': 0.3, 'tfidf_hybrid': 0.3}
            
            for method, keywords in results['keywords'].items():
                if method != 'combined' and keywords:
                    weight = method_weights.get(method, 0.3)
                    for keyword, score in keywords:
                        all_keywords[keyword] += score * weight
            
            # Sort combined keywords
            results['keywords']['combined'] = sorted(
                all_keywords.items(), key=lambda x: x[1], reverse=True
            )[:10]
            
            # 3. Extract named entities
            logger.info("🏷️ Extracting named entities...")
            results['named_entities'] = self.extract_named_entities(user_input)
            
            # 4. Expand query dynamically
            logger.info("🔄 Expanding query dynamically...")
            results['query_expansion'] = self.expand_query_dynamically(user_input)
            
            # 5. Calculate confidence score
            confidence_factors = []
            
            # Factor 1: Number of extracted keywords
            total_keywords = len(results['keywords']['combined'])
            confidence_factors.append(min(total_keywords / 10, 1.0) * 0.3)
            
            # Factor 2: Named entities found
            total_entities = sum(len(entities) for entities in results['named_entities'].values())
            confidence_factors.append(min(total_entities / 5, 1.0) * 0.2)
            
            # Factor 3: Malaysian context detected
            malaysian_context_score = len(results['query_expansion']['malaysian_context']) > 0
            confidence_factors.append(malaysian_context_score * 0.2)
            
            # Factor 4: Industry context detected
            industry_context_score = results['query_expansion']['industry_context'] is not None
            confidence_factors.append(industry_context_score * 0.3)
            
            results['confidence_score'] = sum(confidence_factors)
            
            # 6. Add processing notes
            results['processing_notes'] = [
                f"Extracted {total_keywords} combined keywords",
                f"Found {total_entities} named entities",
                f"Industry context: {results['query_expansion']['industry_context'] or 'General'}",
                f"Malaysian context: {'Yes' if results['query_expansion']['malaysian_context'] else 'No'}",
                f"Confidence score: {results['confidence_score']:.2f}"
            ]
            
            logger.info("✅ Input processing completed successfully")
            
        except Exception as e:
            logger.error(f"❌ Input processing failed: {e}")
            results['processing_notes'].append(f"Error: {str(e)}")
        
        return results

# Global instance
advanced_nlp = AdvancedNLPProcessor()

def process_user_input(user_input: str) -> Dict[str, Any]:
    """
    Main function to process user input with advanced NLP
    """
    return advanced_nlp.process_input_comprehensive(user_input)

if __name__ == "__main__":
    # Test the processor
    test_queries = [
        "smartphone terbaik Malaysia 2025",
        "makanan halal sedap di Kuala Lumpur",
        "investment opportunities in Malaysian banking sector",
        "best universities in Penang for engineering students"
    ]
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"Testing: {query}")
        print('='*60)
        
        results = process_user_input(query)
        
        print(f"🔑 Top Keywords: {[kw[0] for kw in results['keywords']['combined'][:5]]}")
        print(f"🏷️ Named Entities: {sum(len(v) for v in results['named_entities'].values())} found")
        print(f"🏭 Industry Context: {results['query_expansion']['industry_context']}")
        print(f"🇲🇾 Malaysian Context: {results['query_expansion']['malaysian_context']}")
        print(f"📱 Suggested Platforms: {results['query_expansion']['suggested_platforms']}")
        print(f"🎯 Confidence: {results['confidence_score']:.2f}")
