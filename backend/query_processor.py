"""
InsightPulse - Intelligent Query Processor
Automatically detects tudung queries and routes to appropriate database sections
"""

import json
import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

@dataclass
class QueryResult:
    """Structure for query processing results"""
    is_tudung_query: bool
    confidence: float
    matched_categories: List[str]
    required_data: List[str]
    crawl_targets: List[str]
    search_keywords: List[str]
    expected_platforms: List[str]

class TudungQueryProcessor:
    def __init__(self, db_path: str = "database/tudung_database.json"):
        """Initialize with tudung database"""
        self.db_path = db_path
        self.tudung_db = self._load_database()
        self.query_patterns = self._build_query_patterns()
        
    def _load_database(self) -> Dict:
        """Load tudung database"""
        try:
            with open(self.db_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Database not found: {self.db_path}")
            return {}
    
    def _build_query_patterns(self) -> Dict[str, Dict]:
        """Build intelligent query patterns for tudung detection"""
        return {
            # Jenis Tudung Patterns
            "jenis_tudung": {
                "patterns": [
                    r"jenis.*tudung", r"tudung.*jenis", r"type.*hijab",
                    r"tudung.*popular", r"popular.*tudung", r"macam.*tudung"
                ],
                "keywords": ["jenis", "type", "macam", "popular", "pilihan"],
                "db_categories": ["jenisUtama"],
                "crawl_focus": ["product_types", "categories", "popular_items"],
                "platforms": ["facebook", "instagram", "tiktok", "shopee", "lazada"]
            },
            
            # Harga Tudung Patterns  
            "harga_tudung": {
                "patterns": [
                    r"harga.*tudung", r"tudung.*murah", r"tudung.*mahal",
                    r"budget.*hijab", r"price.*hijab", r"rm.*tudung"
                ],
                "keywords": ["harga", "murah", "mahal", "budget", "price", "rm"],
                "db_categories": ["segmenHarga"],
                "crawl_focus": ["pricing", "promotions", "deals"],
                "platforms": ["shopee", "lazada", "facebook", "instagram"]
            },
            
            # Material Tudung Patterns
            "material_tudung": {
                "patterns": [
                    r"tudung.*chiffon", r"tudung.*cotton", r"tudung.*lycra",
                    r"bahan.*tudung", r"material.*hijab", r"kain.*tudung"
                ],
                "keywords": ["chiffon", "cotton", "lycra", "satin", "jersey", "bahan", "material"],
                "db_categories": ["materials"],
                "crawl_focus": ["material_reviews", "fabric_quality", "comfort"],
                "platforms": ["facebook", "instagram", "youtube", "blog"]
            },
            
            # Trend Tudung Patterns
            "trend_tudung": {
                "patterns": [
                    r"trend.*tudung", r"tudung.*viral", r"tudung.*terkini",
                    r"latest.*hijab", r"new.*tudung", r"fashion.*hijab"
                ],
                "keywords": ["trend", "viral", "terkini", "latest", "new", "fashion"],
                "db_categories": ["trenModen"],
                "crawl_focus": ["trending_posts", "viral_content", "fashion_updates"],
                "platforms": ["tiktok", "instagram", "facebook", "twitter"]
            },
            
            # Fungsi Tudung Patterns
            "fungsi_tudung": {
                "patterns": [
                    r"tudung.*kerja", r"tudung.*sukan", r"tudung.*formal",
                    r"hijab.*office", r"hijab.*sport", r"tudung.*harian"
                ],
                "keywords": ["kerja", "sukan", "formal", "harian", "office", "sport", "casual"],
                "db_categories": ["fungsi"],
                "crawl_focus": ["usage_reviews", "lifestyle_content", "work_fashion"],
                "platforms": ["facebook", "instagram", "linkedin", "blog"]
            },
            
            # Brand Tudung Patterns
            "brand_tudung": {
                "patterns": [
                    r"naelofar.*tudung", r"duck.*tudung", r"ariani.*hijab",
                    r"brand.*tudung", r"jenama.*tudung"
                ],
                "keywords": ["naelofar", "duck", "ariani", "vanilla", "brand", "jenama"],
                "db_categories": ["jenisUtama"],  # brands are in jenisUtama
                "crawl_focus": ["brand_mentions", "brand_reviews", "brand_comparison"],
                "platforms": ["facebook", "instagram", "shopee", "lazada", "youtube"]
            },
            
            # Warna Tudung Patterns
            "warna_tudung": {
                "patterns": [
                    r"warna.*tudung", r"tudung.*hitam", r"tudung.*putih",
                    r"color.*hijab", r"tudung.*nude", r"tudung.*pastel"
                ],
                "keywords": ["warna", "color", "hitam", "putih", "nude", "pastel", "dusty"],
                "db_categories": ["corak"],
                "crawl_focus": ["color_trends", "color_reviews", "styling_tips"],
                "platforms": ["instagram", "pinterest", "facebook", "tiktok"]
            }
        }
    
    def process_query(self, query: str) -> QueryResult:
        """Main function to process and route tudung queries"""
        query_lower = query.lower().strip()
        
        # Step 1: Detect if it's a tudung query
        is_tudung, confidence = self._detect_tudung_query(query_lower)
        
        if not is_tudung:
            return QueryResult(
                is_tudung_query=False,
                confidence=confidence,
                matched_categories=[],
                required_data=[],
                crawl_targets=[],
                search_keywords=[],
                expected_platforms=[]
            )
        
        # Step 2: Match to specific categories
        matched_categories = self._match_categories(query_lower)
        
        # Step 3: Determine required data from DB
        required_data = self._get_required_data(matched_categories)
        
        # Step 4: Determine crawling targets
        crawl_targets = self._get_crawl_targets(matched_categories)
        
        # Step 5: Generate search keywords
        search_keywords = self._generate_search_keywords(query_lower, matched_categories)
        
        # Step 6: Determine platforms to crawl
        expected_platforms = self._get_expected_platforms(matched_categories)
        
        return QueryResult(
            is_tudung_query=True,
            confidence=confidence,
            matched_categories=matched_categories,
            required_data=required_data,
            crawl_targets=crawl_targets,
            search_keywords=search_keywords,
            expected_platforms=expected_platforms
        )
    
    def _detect_tudung_query(self, query: str) -> Tuple[bool, float]:
        """Detect if query is related to tudung/hijab"""
        tudung_indicators = [
            "tudung", "hijab", "selendang", "shawl", "headscarf",
            "naelofar", "duck", "ariani", "chiffon", "bawal"
        ]
        
        matches = sum(1 for indicator in tudung_indicators if indicator in query)
        confidence = min(matches * 0.3, 1.0)
        
        return matches > 0, confidence
    
    def _match_categories(self, query: str) -> List[str]:
        """Match query to specific tudung categories"""
        matched = []
        
        for category, config in self.query_patterns.items():
            # Check patterns
            pattern_match = any(re.search(pattern, query) for pattern in config["patterns"])
            
            # Check keywords
            keyword_match = any(keyword in query for keyword in config["keywords"])
            
            if pattern_match or keyword_match:
                matched.append(category)
        
        return matched if matched else ["jenis_tudung"]  # Default fallback
    
    def _get_required_data(self, categories: List[str]) -> List[str]:
        """Determine what data is needed from database"""
        required = set()
        
        for category in categories:
            if category in self.query_patterns:
                db_categories = self.query_patterns[category]["db_categories"]
                required.update(db_categories)
        
        return list(required)
    
    def _get_crawl_targets(self, categories: List[str]) -> List[str]:
        """Determine what to focus on when crawling"""
        targets = set()
        
        for category in categories:
            if category in self.query_patterns:
                crawl_focus = self.query_patterns[category]["crawl_focus"]
                targets.update(crawl_focus)
        
        return list(targets)
    
    def _generate_search_keywords(self, query: str, categories: List[str]) -> List[str]:
        """Generate optimized search keywords for crawling"""
        base_keywords = ["tudung", "hijab"]
        
        # Add category-specific keywords
        for category in categories:
            if category in self.query_patterns:
                base_keywords.extend(self.query_patterns[category]["keywords"])
        
        # Add Malaysian context
        malaysian_context = ["malaysia", "kl", "shah alam", "johor", "penang"]
        
        # Combine and deduplicate
        all_keywords = list(set(base_keywords + malaysian_context))
        
        return all_keywords[:15]  # Limit to top 15 keywords
    
    def _get_expected_platforms(self, categories: List[str]) -> List[str]:
        """Determine which platforms to prioritize for crawling"""
        platforms = set()
        
        for category in categories:
            if category in self.query_patterns:
                category_platforms = self.query_patterns[category]["platforms"]
                platforms.update(category_platforms)
        
        return list(platforms)
    
    def get_database_subset(self, required_data: List[str]) -> Dict:
        """Extract relevant subset from database"""
        subset = {}
        
        for data_type in required_data:
            if data_type in self.tudung_db:
                subset[data_type] = self.tudung_db[data_type]
        
        return subset

# Example usage and testing
if __name__ == "__main__":
    processor = TudungQueryProcessor()
    
    # Test queries
    test_queries = [
        "jenis tudung popular di malaysia",
        "tudung murah untuk kerja",
        "trend tudung viral 2025",
        "tudung chiffon terbaik",
        "harga tudung naelofar",
        "warna tudung popular",
        "tudung sukan untuk gym"
    ]
    
    print("=== TUDUNG QUERY PROCESSING RESULTS ===\n")
    
    for query in test_queries:
        result = processor.process_query(query)
        print(f"Query: '{query}'")
        print(f"Is Tudung Query: {result.is_tudung_query}")
        print(f"Confidence: {result.confidence:.2f}")
        print(f"Categories: {result.matched_categories}")
        print(f"Required DB Data: {result.required_data}")
        print(f"Crawl Targets: {result.crawl_targets}")
        print(f"Search Keywords: {result.search_keywords[:5]}...")  # Show first 5
        print(f"Platforms: {result.expected_platforms}")
        print("-" * 50)
