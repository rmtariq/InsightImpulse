#!/usr/bin/env python3
"""
🤖 AI-Powered Keyword Generator Service
========================================
Generates platform-optimized search keywords using LLM intelligence

Author: InsightPulse AI Team
Version: 1.0.0
"""

import asyncio
import logging
import json
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import hashlib

logger = logging.getLogger(__name__)

class AIKeywordGenerator:
    """AI-powered keyword generator for multi-platform social media search"""
    
    def __init__(self, llm_service=None):
        """
        Initialize AI Keyword Generator
        
        Args:
            llm_service: LLM service instance (OpenAI/Anthropic)
        """
        self.llm_service = llm_service
        self.cache = {}  # Simple in-memory cache
        self.cache_ttl = timedelta(hours=24)  # Cache for 24 hours
        logger.info("✅ AI Keyword Generator initialized")
    
    def _get_cache_key(self, query: str, platforms: List[str]) -> str:
        """Generate cache key for query and platforms"""
        key_str = f"{query}_{','.join(sorted(platforms))}"
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def _is_cache_valid(self, cache_entry: Dict) -> bool:
        """Check if cache entry is still valid"""
        if not cache_entry:
            return False
        timestamp = cache_entry.get('timestamp')
        if not timestamp:
            return False
        age = datetime.now() - timestamp
        return age < self.cache_ttl
    
    async def generate_platform_keywords(
        self,
        query: str,
        platforms: List[str],
        analysis_type: str = "general"
    ) -> Dict[str, List[str]]:
        """
        Generate platform-optimized keywords using AI
        
        Args:
            query: User's search query
            platforms: List of platforms to generate keywords for
            analysis_type: Type of analysis (general, sentiment, etc.)
            
        Returns:
            Dict mapping platform names to lists of optimized keywords
        """
        try:
            # Check cache first
            cache_key = self._get_cache_key(query, platforms)
            if cache_key in self.cache and self._is_cache_valid(self.cache[cache_key]):
                logger.info(f"🎯 Using cached keywords for query: '{query}'")
                return self.cache[cache_key]['keywords']
            
            # Generate keywords using LLM
            logger.info(f"🤖 Generating AI-powered keywords for: '{query}'")
            keywords = await self._generate_with_llm(query, platforms, analysis_type)
            
            # Cache the results
            self.cache[cache_key] = {
                'keywords': keywords,
                'timestamp': datetime.now()
            }
            
            # Log generated keywords
            self._log_generated_keywords(query, keywords)
            
            return keywords
            
        except Exception as e:
            logger.error(f"❌ AI keyword generation failed: {e}")
            # Fallback to simple keywords
            return self._fallback_keywords(query, platforms)
    
    async def _generate_with_llm(
        self,
        query: str,
        platforms: List[str],
        analysis_type: str
    ) -> Dict[str, List[str]]:
        """Generate keywords using LLM"""
        
        if not self.llm_service:
            logger.warning("⚠️ No LLM service available, using fallback")
            return self._fallback_keywords(query, platforms)
        
        # Create prompt for LLM
        prompt = self._create_keyword_prompt(query, platforms, analysis_type)
        
        # Call LLM
        try:
            if hasattr(self.llm_service, 'anthropic_client') and self.llm_service.anthropic_client:
                response = await self._call_anthropic(prompt)
            elif hasattr(self.llm_service, 'openai_client') and self.llm_service.openai_client:
                response = await self._call_openai(prompt)
            else:
                logger.warning("⚠️ No LLM client available")
                return self._fallback_keywords(query, platforms)
            
            # Parse response
            keywords = self._parse_llm_response(response, platforms)
            return keywords
            
        except Exception as e:
            logger.error(f"❌ LLM call failed: {e}")
            return self._fallback_keywords(query, platforms)
    
    def _create_keyword_prompt(self, query: str, platforms: List[str], analysis_type: str) -> str:
        """Create prompt for LLM keyword generation"""
        return f"""Generate optimized search keywords for social media platforms.

USER QUERY: "{query}"
ANALYSIS TYPE: {analysis_type}
PLATFORMS: {', '.join(platforms)}

For each platform, generate 2-4 MOST EFFECTIVE search terms that will maximize relevant results:

FACEBOOK (supports text search, OR operators):
- Generate 2-3 variations of the query
- Include common misspellings/variations
- Consider Bahasa Malaysia and English mix

INSTAGRAM (hashtag-focused):
- Generate 2-4 relevant hashtags
- Mix of specific and broad hashtags
- Consider trending variations
- Format: #hashtag (with # symbol)

X/TWITTER (supports hashtags + text):
- Mix of hashtags and text queries
- Include abbreviations
- Consider trending formats

TIKTOK (keyword + hashtag mix):
- Popular keyword variations
- Trending formats
- Mix of text and hashtags

NEWS (formal search):
- Professional terminology
- Alternative phrasings
- Formal language

YOUTUBE (keyword search):
- Video-friendly keywords
- Popular search terms

LINKEDIN (professional context):
- Professional terminology
- Industry-specific terms

Return ONLY valid JSON in this exact format (no markdown, no code blocks):
{{
  "facebook": ["keyword1", "keyword2", "keyword3"],
  "instagram": ["#hashtag1", "#hashtag2", "#hashtag3"],
  "twitter": ["keyword1", "#hashtag1", "keyword2"],
  "x": ["keyword1", "#hashtag1", "keyword2"],
  "tiktok": ["keyword1", "#hashtag1", "keyword2"],
  "news": ["keyword1", "keyword2"],
  "youtube": ["keyword1", "keyword2"],
  "linkedin": ["keyword1", "keyword2"]
}}

IMPORTANT:
- Return ONLY the JSON object, no other text
- Instagram keywords MUST start with #
- Keep keywords concise and relevant
- Consider Malaysian context (Bahasa Malaysia + English)
- Focus on keywords that will get REAL results"""

    async def _call_anthropic(self, prompt: str) -> str:
        """Call Anthropic Claude for keyword generation"""
        try:
            response = await asyncio.to_thread(
                self.llm_service.anthropic_client.messages.create,
                model="claude-sonnet-4-20250514",
                max_tokens=1000,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f"❌ Anthropic call failed: {e}")
            raise

    async def _call_openai(self, prompt: str) -> str:
        """Call OpenAI GPT for keyword generation"""
        try:
            response = await asyncio.to_thread(
                self.llm_service.openai_client.chat.completions.create,
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a social media keyword optimization expert. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.3
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"❌ OpenAI call failed: {e}")
            raise

    def _parse_llm_response(self, response: str, platforms: List[str]) -> Dict[str, List[str]]:
        """Parse LLM response to extract keywords"""
        try:
            # Clean response (remove markdown code blocks if present)
            cleaned = response.strip()
            if cleaned.startswith('```'):
                # Remove markdown code blocks
                lines = cleaned.split('\n')
                cleaned = '\n'.join(line for line in lines if not line.startswith('```'))

            # Parse JSON
            keywords_dict = json.loads(cleaned)

            # Validate and filter for requested platforms
            result = {}
            for platform in platforms:
                platform_lower = platform.lower()
                if platform_lower in keywords_dict:
                    result[platform_lower] = keywords_dict[platform_lower]
                else:
                    # Fallback for this platform
                    result[platform_lower] = self._fallback_keywords_for_platform(platform_lower, "")

            return result

        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse LLM response as JSON: {e}")
            logger.error(f"Response was: {response[:200]}")
            return self._fallback_keywords("", platforms)

    def _fallback_keywords(self, query: str, platforms: List[str]) -> Dict[str, List[str]]:
        """Generate fallback keywords when AI is unavailable"""
        result = {}
        for platform in platforms:
            platform_lower = platform.lower()
            result[platform_lower] = self._fallback_keywords_for_platform(platform_lower, query)
        return result

    def _fallback_keywords_for_platform(self, platform: str, query: str) -> List[str]:
        """Generate simple fallback keywords for a specific platform"""
        if not query:
            return [query] if query else []

        keywords = []

        if platform == 'instagram':
            # Instagram: Convert to hashtags
            words = query.strip().split()
            if words:
                # Main hashtag (last word)
                main_word = words[-1]
                keywords.append(f"#{main_word}")
                # Combined hashtag (no spaces)
                if len(words) > 1:
                    combined = ''.join(words)
                    keywords.append(f"#{combined}")

        elif platform in ['facebook', 'twitter', 'x', 'tiktok', 'news', 'youtube', 'linkedin']:
            # Text-based platforms: Use original query
            keywords.append(query)
            # Add variation without spaces for TikTok
            if platform == 'tiktok' and ' ' in query:
                keywords.append(query.replace(' ', ''))

        else:
            # Default: original query
            keywords.append(query)

        return keywords

    def _log_generated_keywords(self, query: str, keywords: Dict[str, List[str]]):
        """Log generated keywords for transparency"""
        logger.info(f"\n{'='*60}")
        logger.info(f"🤖 AI GENERATED KEYWORDS FOR: '{query}'")
        logger.info(f"{'='*60}")

        platform_emojis = {
            'facebook': '📘',
            'instagram': '📸',
            'twitter': '🐦',
            'x': '🐦',
            'tiktok': '🎵',
            'news': '📰',
            'youtube': '📺',
            'linkedin': '💼',
            'google': '🔍',
            'shopee': '🛍️',
            'lazada': '🛒'
        }

        for platform, kw_list in keywords.items():
            emoji = platform_emojis.get(platform, '📱')
            keywords_str = ' OR '.join(f'"{kw}"' for kw in kw_list)
            logger.info(f"{emoji} {platform.upper()}: {keywords_str}")

        logger.info(f"{'='*60}\n")


# Global instance (will be initialized with LLM service)
ai_keyword_generator = None

def initialize_ai_keyword_generator(llm_service):
    """Initialize global AI keyword generator with LLM service"""
    global ai_keyword_generator
    ai_keyword_generator = AIKeywordGenerator(llm_service)
    logger.info("✅ Global AI Keyword Generator initialized")
    return ai_keyword_generator

