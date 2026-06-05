"""
InsightPulse - Advanced Keyword Breakdown Engine
Breaks down search queries into multiple variations for maximum crawler coverage
"""

import re
import json
from typing import List, Dict, Set, Tuple
from dataclasses import dataclass
from itertools import combinations

@dataclass
class KeywordBreakdown:
    """Structure for keyword breakdown results"""
    original_query: str
    single_keywords: List[str]
    two_word_phrases: List[str]
    three_word_phrases: List[str]
    full_phrases: List[str]
    variations: List[str]
    crawler_optimized: Dict[str, List[str]]
    total_search_terms: int

class KeywordBreakdownEngine:
    def __init__(self):
        """Initialize universal keyword breakdown engine"""
        self.stop_words = self._get_stop_words()
        self.synonyms = self._build_universal_synonyms()
        self.crawler_preferences = self._define_crawler_preferences()
        
    def _get_stop_words(self) -> Set[str]:
        """Define common stop words to filter out"""
        return {
            'dan', 'atau', 'untuk', 'di', 'ke', 'dari', 'pada', 'dengan', 'oleh',
            'adalah', 'akan', 'telah', 'sudah', 'belum', 'tidak', 'bukan',
            'yang', 'ini', 'itu', 'tersebut', 'seperti', 'antara', 'dalam',
            'the', 'and', 'or', 'for', 'in', 'to', 'from', 'on', 'with', 'by',
            'is', 'are', 'was', 'were', 'will', 'have', 'has', 'had', 'not'
        }
    
    def _build_universal_synonyms(self) -> Dict[str, List[str]]:
        """Build universal synonym dictionary for keyword expansion"""
        return {
            'popular': ['trending', 'viral', 'famous', 'terkenal', 'hot'],
            'murah': ['cheap', 'affordable', 'budget', 'jimat', 'ekonomi'],
            'mahal': ['expensive', 'premium', 'luxury', 'mewah', 'eksklusif'],
            'bagus': ['good', 'great', 'excellent', 'quality', 'berkualiti'],
            'terbaik': ['best', 'top', 'excellent', 'premium', 'pilihan'],
            'trend': ['trending', 'fashion', 'style', 'fesyen', 'gaya'],
            'harga': ['price', 'cost', 'rate', 'value', 'pricing'],
            'jenis': ['type', 'kind', 'style', 'category', 'macam'],
            'brand': ['jenama', 'label', 'trademark', 'nama'],
            'malaysia': ['malaysian', 'local', 'tempatan', 'negara']
        }
    
    def _define_crawler_preferences(self) -> Dict[str, Dict]:
        """Define what each crawler platform prefers"""
        return {
            'facebook': {
                'preferred_length': 'medium',  # 2-4 words
                'hashtag_friendly': True,
                'local_context': True,
                'brand_mentions': True
            },
            'instagram': {
                'preferred_length': 'short',  # 1-2 words
                'hashtag_friendly': True,
                'visual_keywords': True,
                'trend_focused': True
            },
            'tiktok': {
                'preferred_length': 'short',  # 1-3 words
                'hashtag_friendly': True,
                'viral_terms': True,
                'youth_language': True
            },
            'twitter': {
                'preferred_length': 'short',  # 1-2 words
                'hashtag_friendly': True,
                'real_time': True,
                'news_related': True
            },
            'youtube': {
                'preferred_length': 'long',  # 3-6 words
                'hashtag_friendly': False,
                'tutorial_focused': True,
                'review_keywords': True
            },
            'shopee': {
                'preferred_length': 'medium',  # 2-4 words
                'hashtag_friendly': False,
                'product_focused': True,
                'price_sensitive': True
            },
            'lazada': {
                'preferred_length': 'medium',  # 2-4 words
                'hashtag_friendly': False,
                'product_focused': True,
                'brand_focused': True
            }
        }
    
    def breakdown_query(self, query: str) -> KeywordBreakdown:
        """Main function to break down query into multiple search variations"""
        
        # Clean and normalize query
        cleaned_query = self._clean_query(query)
        words = self._extract_words(cleaned_query)
        
        # Generate different phrase combinations
        single_keywords = self._generate_single_keywords(words)
        two_word_phrases = self._generate_two_word_phrases(words)
        three_word_phrases = self._generate_three_word_phrases(words)
        full_phrases = self._generate_full_phrases(cleaned_query)
        
        # Generate variations with synonyms
        variations = self._generate_variations(single_keywords + two_word_phrases)
        
        # Optimize for each crawler
        crawler_optimized = self._optimize_for_crawlers(
            single_keywords, two_word_phrases, three_word_phrases, full_phrases
        )
        
        # Calculate total search terms
        total_terms = len(set(
            single_keywords + two_word_phrases + three_word_phrases + 
            full_phrases + variations
        ))
        
        return KeywordBreakdown(
            original_query=query,
            single_keywords=single_keywords,
            two_word_phrases=two_word_phrases,
            three_word_phrases=three_word_phrases,
            full_phrases=full_phrases,
            variations=variations,
            crawler_optimized=crawler_optimized,
            total_search_terms=total_terms
        )
    
    def _clean_query(self, query: str) -> str:
        """Clean and normalize the query"""
        # Convert to lowercase
        query = query.lower().strip()
        
        # Remove special characters but keep spaces and hyphens
        query = re.sub(r'[^\w\s\-]', ' ', query)
        
        # Normalize multiple spaces
        query = re.sub(r'\s+', ' ', query)
        
        return query
    
    def _extract_words(self, query: str) -> List[str]:
        """Extract meaningful words from query"""
        words = query.split()
        
        # Filter out stop words but keep important ones
        meaningful_words = []
        for word in words:
            if len(word) > 2 and word not in self.stop_words:
                meaningful_words.append(word)
        
        return meaningful_words
    
    def _generate_single_keywords(self, words: List[str]) -> List[str]:
        """Generate single keyword variations"""
        keywords = []
        
        for word in words:
            keywords.append(word)
            
            # Add synonyms
            if word in self.synonyms:
                keywords.extend(self.synonyms[word])
        
        return list(set(keywords))  # Remove duplicates
    
    def _generate_two_word_phrases(self, words: List[str]) -> List[str]:
        """Generate two-word phrase combinations"""
        phrases = []
        
        # Adjacent pairs
        for i in range(len(words) - 1):
            phrases.append(f"{words[i]} {words[i+1]}")
        
        # Non-adjacent meaningful combinations
        for combo in combinations(words, 2):
            phrase = f"{combo[0]} {combo[1]}"
            if phrase not in phrases:
                phrases.append(phrase)
        
        return phrases
    
    def _generate_three_word_phrases(self, words: List[str]) -> List[str]:
        """Generate three-word phrase combinations"""
        phrases = []
        
        # Adjacent triplets
        for i in range(len(words) - 2):
            phrases.append(f"{words[i]} {words[i+1]} {words[i+2]}")
        
        # Selected meaningful combinations
        if len(words) >= 3:
            for combo in combinations(words, 3):
                phrase = f"{combo[0]} {combo[1]} {combo[2]}"
                if phrase not in phrases:
                    phrases.append(phrase)
        
        return phrases[:10]  # Limit to top 10 to avoid explosion
    
    def _generate_full_phrases(self, query: str) -> List[str]:
        """Generate full phrase variations"""
        phrases = [query]
        
        # Add quoted version for exact search
        phrases.append(f'"{query}"')
        
        # Add with common prefixes/suffixes
        common_additions = [
            f"{query} malaysia",
            f"{query} 2025",
            f"{query} terkini",
            f"{query} review",
            f"best {query}",
            f"popular {query}"
        ]
        
        phrases.extend(common_additions)
        
        return phrases
    
    def _generate_variations(self, base_terms: List[str]) -> List[str]:
        """Generate variations using synonyms and context"""
        variations = []
        
        for term in base_terms[:15]:  # Limit to prevent explosion
            # Add with Malaysian context
            variations.extend([
                f"{term} malaysia",
                f"{term} kl",
                f"{term} online",
                f"{term} murah",
                f"{term} terbaik"
            ])
            
            # Add hashtag versions for social media
            hashtag_term = term.replace(' ', '')
            variations.append(f"#{hashtag_term}")
        
        return list(set(variations))
    
    def _optimize_for_crawlers(self, single: List[str], two: List[str], 
                              three: List[str], full: List[str]) -> Dict[str, List[str]]:
        """Optimize keyword selection for each crawler platform"""
        optimized = {}
        
        for platform, prefs in self.crawler_preferences.items():
            platform_keywords = []
            
            if prefs['preferred_length'] == 'short':
                platform_keywords.extend(single[:8])
                platform_keywords.extend(two[:5])
                
            elif prefs['preferred_length'] == 'medium':
                platform_keywords.extend(single[:5])
                platform_keywords.extend(two[:8])
                platform_keywords.extend(three[:3])
                
            elif prefs['preferred_length'] == 'long':
                platform_keywords.extend(two[:5])
                platform_keywords.extend(three[:5])
                platform_keywords.extend(full[:3])
            
            # Add hashtag versions if platform supports it
            if prefs['hashtag_friendly']:
                hashtag_terms = [f"#{term.replace(' ', '')}" for term in platform_keywords[:5]]
                platform_keywords.extend(hashtag_terms)
            
            # Add platform-specific terms
            if prefs.get('local_context'):
                platform_keywords.extend([f"{term} malaysia" for term in single[:3]])
            
            if prefs.get('price_sensitive'):
                platform_keywords.extend([f"{term} harga" for term in single[:3]])
            
            optimized[platform] = list(set(platform_keywords))[:15]  # Limit per platform
        
        return optimized
    
    def generate_search_strategy(self, breakdown: KeywordBreakdown) -> Dict:
        """Generate comprehensive search strategy"""
        return {
            'total_search_terms': breakdown.total_search_terms,
            'search_phases': {
                'phase_1_broad': breakdown.single_keywords[:10],
                'phase_2_targeted': breakdown.two_word_phrases[:10],
                'phase_3_specific': breakdown.three_word_phrases[:5],
                'phase_4_exact': breakdown.full_phrases[:3]
            },
            'platform_distribution': {
                platform: len(terms) for platform, terms in breakdown.crawler_optimized.items()
            },
            'estimated_coverage': self._estimate_coverage(breakdown),
            'crawling_priority': self._determine_crawling_priority(breakdown)
        }
    
    def _estimate_coverage(self, breakdown: KeywordBreakdown) -> Dict:
        """Estimate search coverage potential"""
        return {
            'high_volume_terms': len([t for t in breakdown.single_keywords if len(t) < 8]),
            'medium_volume_terms': len(breakdown.two_word_phrases),
            'low_volume_terms': len(breakdown.three_word_phrases),
            'exact_match_terms': len(breakdown.full_phrases),
            'total_potential_results': breakdown.total_search_terms * 100  # Estimated
        }
    
    def _determine_crawling_priority(self, breakdown: KeywordBreakdown) -> List[Dict]:
        """Determine crawling priority order"""
        priorities = []
        
        # High priority: Single keywords + two-word phrases
        priorities.append({
            'priority': 'HIGH',
            'terms': breakdown.single_keywords[:5] + breakdown.two_word_phrases[:5],
            'platforms': ['facebook', 'instagram', 'tiktok'],
            'reason': 'High volume, broad reach'
        })
        
        # Medium priority: Three-word phrases + variations
        priorities.append({
            'priority': 'MEDIUM',
            'terms': breakdown.three_word_phrases[:5] + breakdown.variations[:10],
            'platforms': ['youtube', 'shopee', 'lazada'],
            'reason': 'Targeted, specific results'
        })
        
        # Low priority: Full phrases + exact matches
        priorities.append({
            'priority': 'LOW',
            'terms': breakdown.full_phrases,
            'platforms': ['twitter'],
            'reason': 'Exact matches, niche results'
        })
        
        return priorities

# Example usage and testing
if __name__ == "__main__":
    engine = KeywordBreakdownEngine()

    # Test queries - EMPTY for universal testing
    test_queries = []

    # Get user input
    print("=== UNIVERSAL KEYWORD BREAKDOWN ENGINE ===")
    print("Enter your search queries (press Enter with empty query to exit):")

    while True:
        query = input("\n🔍 Enter query: ").strip()
        if not query:
            break
        test_queries.append(query)
    
    print("=== KEYWORD BREAKDOWN ENGINE RESULTS ===\n")
    
    for query in test_queries:
        print(f"🔍 QUERY: '{query}'")
        print("=" * 50)
        
        breakdown = engine.breakdown_query(query)
        strategy = engine.generate_search_strategy(breakdown)
        
        print(f"📊 TOTAL SEARCH TERMS: {breakdown.total_search_terms}")
        print(f"🎯 SINGLE KEYWORDS ({len(breakdown.single_keywords)}): {breakdown.single_keywords[:5]}...")
        print(f"🎯 TWO-WORD PHRASES ({len(breakdown.two_word_phrases)}): {breakdown.two_word_phrases[:3]}...")
        print(f"🎯 THREE-WORD PHRASES ({len(breakdown.three_word_phrases)}): {breakdown.three_word_phrases[:2]}...")
        
        print(f"\n🕷️ CRAWLER OPTIMIZATION:")
        for platform, terms in breakdown.crawler_optimized.items():
            print(f"  {platform.upper()}: {len(terms)} terms - {terms[:3]}...")
        
        print(f"\n📈 ESTIMATED COVERAGE: {strategy['estimated_coverage']['total_potential_results']} potential results")
        print(f"🎯 CRAWLING PHASES: {len(strategy['search_phases'])} phases planned")
        
        print("\n" + "="*70 + "\n")
