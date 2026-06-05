#!/usr/bin/env python3
"""
AI-Powered Keyword Generator for InsightPulse
Generates optimal search keywords for maximum data collection across platforms
"""

import streamlit as st
import json
import re
from typing import List, Dict, Set, Tuple
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import requests
from itertools import combinations

@dataclass
class KeywordSet:
    """Data structure for generated keywords"""
    primary_keywords: List[str]
    secondary_keywords: List[str]
    hashtags: List[str]
    malay_keywords: List[str]
    english_keywords: List[str]
    chinese_keywords: List[str]
    platform_specific: Dict[str, List[str]]
    generated_at: datetime
    claim_id: str

class AIKeywordGenerator:
    """Professional AI-powered keyword generation system"""
    
    def __init__(self):
        self.keywords_file = Path("data/keywords/generated_keywords.json")
        self.keywords_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Malaysian context keyword databases
        self.malay_synonyms = {
            'politik': ['politik', 'political', 'kerajaan', 'government', 'parti', 'party'],
            'agama': ['agama', 'religion', 'religious', 'islam', 'muslim', 'kristian', 'hindu', 'buddha'],
            'ekonomi': ['ekonomi', 'economy', 'economic', 'kewangan', 'finance', 'perniagaan', 'business'],
            'kesihatan': ['kesihatan', 'health', 'sihat', 'healthy', 'sakit', 'sick', 'hospital'],
            'pendidikan': ['pendidikan', 'education', 'sekolah', 'school', 'universiti', 'university'],
            'teknologi': ['teknologi', 'technology', 'digital', 'internet', 'komputer', 'computer'],
            'masyarakat': ['masyarakat', 'society', 'social', 'komuniti', 'community'],
            'alam': ['alam', 'environment', 'sekitar', 'nature', 'hijau', 'green'],
            'budaya': ['budaya', 'culture', 'tradisi', 'tradition', 'adat', 'custom'],
            'keselamatan': ['keselamatan', 'security', 'safety', 'polis', 'police']
        }
        
        # Platform-specific keyword patterns
        self.platform_patterns = {
            'Facebook': {
                'prefixes': ['', 'share', 'like if', 'comment'],
                'suffixes': ['malaysia', 'viral', 'trending', 'latest', 'breaking']
            },
            'Instagram': {
                'prefixes': ['#', '@', ''],
                'suffixes': ['malaysia', 'my', 'kl', 'viral', 'trending']
            },
            'Twitter/X': {
                'prefixes': ['#', '@', 'RT'],
                'suffixes': ['malaysia', 'my', 'breaking', 'news', 'viral']
            },
            'TikTok': {
                'prefixes': ['#', ''],
                'suffixes': ['malaysia', 'viral', 'fyp', 'trending', 'my']
            },
            'Google': {
                'prefixes': ['', 'latest', 'news', 'update'],
                'suffixes': ['malaysia', '2024', '2025', 'today', 'latest']
            },
            'News': {
                'prefixes': ['', 'breaking', 'latest', 'update'],
                'suffixes': ['malaysia', 'news', 'report', 'today', 'latest']
            },
            'Forums': {
                'prefixes': ['', 'discuss', 'opinion', 'what do you think'],
                'suffixes': ['malaysia', 'lowyat', 'forum', 'discussion']
            }
        }
    
    def extract_base_keywords(self, title: str, description: str) -> List[str]:
        """Extract base keywords from claim text"""
        text = (title + " " + description).lower()
        
        # Remove punctuation and extract words
        words = re.findall(r'\b\w{3,}\b', text)
        
        # Remove common stop words
        stop_words = {
            'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
            'yang', 'dan', 'atau', 'ini', 'itu', 'adalah', 'akan', 'telah', 'dari', 'ke',
            'this', 'that', 'these', 'those', 'they', 'them', 'their', 'there', 'where'
        }
        
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        return list(set(keywords))
    
    def expand_with_synonyms(self, keywords: List[str]) -> Tuple[List[str], List[str], List[str]]:
        """Expand keywords with Malay, English, and Chinese variations"""
        malay_keywords = []
        english_keywords = []
        chinese_keywords = []
        
        for keyword in keywords:
            # Check if keyword matches any synonym group
            for base_word, synonyms in self.malay_synonyms.items():
                if keyword in synonyms:
                    malay_keywords.extend([s for s in synonyms if 'malay' in s.lower() or s in ['politik', 'agama', 'ekonomi', 'kesihatan', 'pendidikan', 'teknologi', 'masyarakat', 'alam', 'budaya', 'keselamatan']])
                    english_keywords.extend([s for s in synonyms if s not in malay_keywords])
            
            # Add original keyword to appropriate language list
            if self.is_malay_word(keyword):
                malay_keywords.append(keyword)
            else:
                english_keywords.append(keyword)
        
        # Add some Chinese keywords for Malaysian context
        chinese_keywords = ['马来西亚', '政治', '宗教', '经济', '健康', '教育', '科技', '社会', '环境', '文化', '安全']
        
        return list(set(malay_keywords)), list(set(english_keywords)), list(set(chinese_keywords))
    
    def is_malay_word(self, word: str) -> bool:
        """Simple check if word is likely Malay"""
        malay_indicators = ['ng', 'ny', 'kh', 'sy', 'an', 'kan', 'lah', 'tah']
        return any(indicator in word.lower() for indicator in malay_indicators)
    
    def generate_hashtags(self, keywords: List[str]) -> List[str]:
        """Generate relevant hashtags"""
        hashtags = []
        
        # Direct hashtags
        for keyword in keywords[:10]:
            hashtags.append(f"#{keyword}")
            hashtags.append(f"#{keyword}Malaysia")
        
        # Malaysian context hashtags
        malaysian_hashtags = [
            '#Malaysia', '#MY', '#KualaLumpur', '#KL', '#Selangor', '#Johor',
            '#MalaysiaNews', '#MalaysiaTrending', '#MalaysiaViral', '#MalaysiaToday',
            '#NegaraKu', '#TanahAir', '#RakyatMalaysia', '#MalaysianLife'
        ]
        
        hashtags.extend(malaysian_hashtags[:10])
        return list(set(hashtags))
    
    def generate_platform_specific_keywords(self, base_keywords: List[str], platforms: List[str]) -> Dict[str, List[str]]:
        """Generate platform-specific keyword variations"""
        platform_keywords = {}
        
        for platform in platforms:
            if platform not in self.platform_patterns:
                continue
                
            patterns = self.platform_patterns[platform]
            keywords = []
            
            for keyword in base_keywords[:5]:  # Use top 5 keywords
                # Add prefix variations
                for prefix in patterns['prefixes']:
                    if prefix:
                        keywords.append(f"{prefix} {keyword}")
                    else:
                        keywords.append(keyword)
                
                # Add suffix variations
                for suffix in patterns['suffixes']:
                    keywords.append(f"{keyword} {suffix}")
                
                # Add combined variations
                for prefix in patterns['prefixes'][:2]:
                    for suffix in patterns['suffixes'][:2]:
                        if prefix:
                            keywords.append(f"{prefix} {keyword} {suffix}")
                        else:
                            keywords.append(f"{keyword} {suffix}")
            
            platform_keywords[platform] = list(set(keywords))[:20]  # Limit to 20 per platform
        
        return platform_keywords
    
    def generate_keyword_combinations(self, keywords: List[str]) -> List[str]:
        """Generate meaningful keyword combinations"""
        combinations_list = []
        
        # 2-word combinations
        for combo in combinations(keywords[:8], 2):
            combinations_list.append(" ".join(combo))
        
        # 3-word combinations (limited)
        for combo in combinations(keywords[:5], 3):
            combinations_list.append(" ".join(combo))
        
        return combinations_list[:15]  # Limit combinations
    
    def generate_comprehensive_keywords(self, claim_data: Dict) -> KeywordSet:
        """Generate comprehensive keyword set for a claim"""
        title = claim_data.get('title', '')
        description = claim_data.get('description', '')
        platforms = claim_data.get('target_platforms', [])
        claim_id = claim_data.get('id', '')
        
        # Extract base keywords
        base_keywords = self.extract_base_keywords(title, description)
        
        # Expand with language variations
        malay_keywords, english_keywords, chinese_keywords = self.expand_with_synonyms(base_keywords)
        
        # Generate hashtags
        hashtags = self.generate_hashtags(base_keywords)
        
        # Generate platform-specific keywords
        platform_specific = self.generate_platform_specific_keywords(base_keywords, platforms)
        
        # Generate keyword combinations
        combinations = self.generate_keyword_combinations(base_keywords)
        
        # Categorize primary and secondary keywords
        primary_keywords = base_keywords[:10] + combinations[:5]
        secondary_keywords = base_keywords[10:] + combinations[5:] + malay_keywords[:5] + english_keywords[:5]
        
        return KeywordSet(
            primary_keywords=primary_keywords,
            secondary_keywords=secondary_keywords,
            hashtags=hashtags,
            malay_keywords=malay_keywords,
            english_keywords=english_keywords,
            chinese_keywords=chinese_keywords,
            platform_specific=platform_specific,
            generated_at=datetime.now(),
            claim_id=claim_id
        )
    
    def save_keywords(self, keyword_set: KeywordSet) -> bool:
        """Save generated keywords to storage"""
        try:
            # Load existing keywords
            keywords_data = []
            if self.keywords_file.exists():
                with open(self.keywords_file, 'r', encoding='utf-8') as f:
                    keywords_data = json.load(f)
            
            # Add new keyword set
            keyword_dict = {
                'claim_id': keyword_set.claim_id,
                'primary_keywords': keyword_set.primary_keywords,
                'secondary_keywords': keyword_set.secondary_keywords,
                'hashtags': keyword_set.hashtags,
                'malay_keywords': keyword_set.malay_keywords,
                'english_keywords': keyword_set.english_keywords,
                'chinese_keywords': keyword_set.chinese_keywords,
                'platform_specific': keyword_set.platform_specific,
                'generated_at': keyword_set.generated_at.isoformat()
            }
            
            keywords_data.append(keyword_dict)
            
            # Save to file
            with open(self.keywords_file, 'w', encoding='utf-8') as f:
                json.dump(keywords_data, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            st.error(f"Error saving keywords: {e}")
            return False
    
    def render_keyword_generator(self, claim_data: Dict = None):
        """Render the keyword generation interface"""
        st.header("🧠 AI Keyword Generator")
        st.markdown("Generate optimal search keywords for maximum data collection")
        
        if claim_data:
            st.info(f"Generating keywords for claim: **{claim_data.get('title', 'Unknown')}**")
            
            # Generate keywords
            with st.spinner("🤖 AI is generating optimal keywords..."):
                keyword_set = self.generate_comprehensive_keywords(claim_data)
            
            # Display results
            st.success("✅ Keywords generated successfully!")
            
            # Primary Keywords
            with st.expander("🎯 Primary Keywords (High Priority)", expanded=True):
                st.write("These are the most important keywords for your search:")
                for i, keyword in enumerate(keyword_set.primary_keywords, 1):
                    st.write(f"{i}. **{keyword}**")
            
            # Language-specific keywords
            col1, col2, col3 = st.columns(3)
            
            with col1:
                with st.expander("🇲🇾 Bahasa Malaysia Keywords"):
                    for keyword in keyword_set.malay_keywords:
                        st.write(f"• {keyword}")
            
            with col2:
                with st.expander("🇬🇧 English Keywords"):
                    for keyword in keyword_set.english_keywords:
                        st.write(f"• {keyword}")
            
            with col3:
                with st.expander("🇨🇳 Chinese Keywords"):
                    for keyword in keyword_set.chinese_keywords:
                        st.write(f"• {keyword}")
            
            # Hashtags
            with st.expander("# Hashtags for Social Media"):
                hashtag_text = " ".join(keyword_set.hashtags)
                st.code(hashtag_text)
            
            # Platform-specific keywords
            with st.expander("📱 Platform-Specific Keywords"):
                for platform, keywords in keyword_set.platform_specific.items():
                    st.subheader(f"{platform}")
                    for keyword in keywords[:10]:
                        st.write(f"• {keyword}")
            
            # Save keywords
            if st.button("💾 Save Keywords", type="primary"):
                if self.save_keywords(keyword_set):
                    st.success("Keywords saved successfully!")
                else:
                    st.error("Failed to save keywords")
            
            return keyword_set
        else:
            st.info("Please submit a claim first to generate keywords")
            return None

def main():
    """Main function for testing the keyword generator"""
    st.set_page_config(
        page_title="InsightPulse - Keyword Generator",
        page_icon="🧠",
        layout="wide"
    )
    
    generator = AIKeywordGenerator()
    
    # Sample claim data for testing
    sample_claim = {
        'id': 'test-123',
        'title': 'Malaysia politik bantuan rakyat ekonomi',
        'description': 'Kerajaan Malaysia memberikan bantuan ekonomi kepada rakyat untuk mengatasi masalah kos sara hidup yang meningkat',
        'target_platforms': ['Facebook', 'Instagram', 'Twitter/X', 'News']
    }
    
    generator.render_keyword_generator(sample_claim)

if __name__ == "__main__":
    main()
