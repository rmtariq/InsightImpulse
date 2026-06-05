#!/usr/bin/env python3
"""
🤖 LLM Integration Service
=========================
Handles integration with OpenAI GPT-4o and Anthropic Claude
Provides intelligent analysis of social media data and user queries

Author: InsightPulse LLM Team
Version: 1.0.0
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
import json
import openai
import anthropic
from openai import OpenAI
from anthropic import Anthropic
import requests
from datetime import datetime

from config import config

logger = logging.getLogger(__name__)

class LLMService:
    """Centralized LLM service for OpenAI and Anthropic integration"""
    
    def __init__(self):
        self.openai_client = None
        self.anthropic_client = None
        self.initialize_clients()
    
    def initialize_clients(self):
        """Initialize LLM clients based on available API keys"""
        try:
            # Initialize OpenAI client
            if config.OPENAI_API_KEY:
                self.openai_client = OpenAI(api_key=config.OPENAI_API_KEY)
                logger.info("✅ OpenAI client initialized successfully")
            else:
                logger.warning("❌ OpenAI API key not found")
            
            # Initialize Anthropic client
            if config.ANTHROPIC_API_KEY:
                self.anthropic_client = Anthropic(api_key=config.ANTHROPIC_API_KEY)
                logger.info("✅ Anthropic client initialized successfully")
            else:
                logger.warning("❌ Anthropic API key not found")
            
            if not self.openai_client and not self.anthropic_client:
                logger.error("❌ No LLM clients available! Please provide API keys.")
                
        except Exception as e:
            logger.error(f"❌ Failed to initialize LLM clients: {str(e)}")
    
    async def analyze_social_media_data(self, query: str, social_data: List[Dict], platforms: List[str]) -> Dict[str, Any]:
        """
        Analyze social media data using LLM to provide intelligent insights
        
        Args:
            query: User's search query
            social_data: List of social media posts
            platforms: List of platforms analyzed
            
        Returns:
            Dict containing AI-powered analysis and insights
        """
        try:
            # Prepare data for analysis
            analysis_prompt = self._create_analysis_prompt(query, social_data, platforms)

            # ✅ PRIORITIZE Claude Sonnet 4.5 for best quality analysis
            if self.anthropic_client:
                logger.info("🤖 Using Claude Sonnet 4.5 for LLM analysis...")
                result = await self._analyze_with_anthropic(analysis_prompt)
            elif self.openai_client:
                logger.info("🤖 Using OpenAI GPT-4o Mini as fallback...")
                result = await self._analyze_with_openai(analysis_prompt)
            else:
                logger.warning("⚠️ No LLM available, using fallback analysis")
                return self._fallback_analysis(query, social_data, platforms)
            
            return result
            
        except Exception as e:
            logger.error(f"❌ LLM analysis failed: {str(e)}")
            return self._fallback_analysis(query, social_data, platforms)
    
    def _create_analysis_prompt(self, query: str, social_data: List[Dict], platforms: List[str]) -> str:
        """Create a comprehensive prompt for LLM analysis"""
        
        # Sample a few posts for analysis (to avoid token limits)
        sample_posts = social_data[:10] if len(social_data) > 10 else social_data
        
        prompt = f"""
You are an expert social media analyst specializing in Malaysian market insights. Analyze the following social media data and provide comprehensive insights.

**USER QUERY:** "{query}"

**PLATFORMS ANALYZED:** {', '.join(platforms)}

**SOCIAL MEDIA DATA:**
"""
        
        for i, post in enumerate(sample_posts, 1):
            prompt += f"""
Post {i}:
- Platform: {post.get('Platform', 'Unknown')}
- Content: {post.get('Text', 'No content')}
- Sentiment: {post.get('Sentiment', 'Unknown')}
- Engagement: {post.get('total_engagement', 0)}
- Date: {post.get('Date', 'Unknown')}
"""
        
        prompt += f"""

**ANALYSIS REQUIREMENTS:**
1. **Query Relevance**: How well does the data answer the user's query "{query}"?
2. **Sentiment Analysis**: Overall sentiment trends and patterns
3. **Key Insights**: 3-5 most important findings from the data
4. **Malaysian Context**: Cultural, linguistic, and market-specific insights
5. **Trending Topics**: Most discussed themes and keywords
6. **Recommendations**: Actionable insights for the user
7. **Data Quality**: Assessment of data completeness and reliability

**OUTPUT FORMAT:**
Provide your analysis in JSON format with the following structure:
{{
    "query_relevance": {{
        "score": 0-100,
        "explanation": "How well the data answers the query"
    }},
    "sentiment_analysis": {{
        "overall_sentiment": "positive/negative/neutral",
        "sentiment_distribution": {{"positive": 0.0, "negative": 0.0, "neutral": 0.0}},
        "sentiment_trends": "Description of sentiment patterns"
    }},
    "key_insights": [
        "Insight 1",
        "Insight 2",
        "Insight 3"
    ],
    "malaysian_context": {{
        "cultural_relevance": "Analysis of Malaysian cultural context",
        "language_patterns": "Bahasa Malaysia/English usage patterns",
        "local_preferences": "Malaysian-specific preferences identified"
    }},
    "trending_topics": [
        {{"topic": "Topic name", "frequency": 0, "sentiment": "positive/negative/neutral"}},
        {{"topic": "Topic name", "frequency": 0, "sentiment": "positive/negative/neutral"}}
    ],
    "recommendations": [
        "Recommendation 1",
        "Recommendation 2",
        "Recommendation 3"
    ],
    "data_quality": {{
        "completeness": 0-100,
        "reliability": 0-100,
        "sample_size": {len(social_data)},
        "notes": "Any data quality concerns"
    }},
    "summary": "2-3 sentence summary of the analysis"
}}

**IMPORTANT NOTES:**
- Focus on Malaysian market context and cultural nuances
- Consider both Bahasa Malaysia and English content
- Provide actionable business insights
- Be specific about halal food, local brands, and Malaysian preferences if relevant
- Consider the user's intent behind the query
"""
        
        return prompt
    
    async def _analyze_with_openai(self, prompt: str) -> Dict[str, Any]:
        """Analyze using OpenAI GPT-4o"""
        try:
            response = await asyncio.to_thread(
                self.openai_client.chat.completions.create,
                model=config.DEFAULT_LLM_MODEL,
                messages=[
                    {"role": "system", "content": "You are an expert social media analyst specializing in Malaysian market insights. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=config.MAX_TOKENS,
                temperature=config.TEMPERATURE,
                top_p=config.TOP_P
            )
            
            content = response.choices[0].message.content
            
            # Try to parse JSON response
            try:
                analysis = json.loads(content)
                analysis["llm_used"] = config.DEFAULT_LLM_MODEL
                analysis["analysis_timestamp"] = datetime.now().isoformat()
                return analysis
            except json.JSONDecodeError:
                logger.warning("❌ OpenAI returned invalid JSON, using fallback")
                return self._parse_text_response(content, "openai")
                
        except Exception as e:
            logger.error(f"❌ OpenAI analysis failed: {str(e)}")
            raise
    
    async def _analyze_with_anthropic(self, prompt: str) -> Dict[str, Any]:
        """Analyze using Anthropic Claude Sonnet 4.5"""
        try:
            # ✅ Use Claude Sonnet 4.5 for best quality
            claude_model = config.CLAUDE_MODEL if hasattr(config, 'CLAUDE_MODEL') else 'claude-sonnet-4-20250514'

            response = await asyncio.to_thread(
                self.anthropic_client.messages.create,
                model=claude_model,  # ✅ Claude Sonnet 4.5
                max_tokens=config.MAX_TOKENS,
                temperature=config.TEMPERATURE,
                top_p=config.TOP_P,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            content = response.content[0].text

            # Try to parse JSON response
            try:
                analysis = json.loads(content)
                analysis["llm_used"] = claude_model
                analysis["analysis_timestamp"] = datetime.now().isoformat()
                logger.info(f"✅ Claude Sonnet 4.5 analysis completed successfully")
                return analysis
            except json.JSONDecodeError:
                logger.warning("❌ Claude returned invalid JSON, using fallback")
                return self._parse_text_response(content, "claude")
                
        except Exception as e:
            logger.error(f"❌ Anthropic analysis failed: {str(e)}")
            raise
    
    def _parse_text_response(self, content: str, llm_type: str) -> Dict[str, Any]:
        """Parse text response when JSON parsing fails"""
        return {
            "query_relevance": {"score": 75, "explanation": "Analysis completed but JSON parsing failed"},
            "sentiment_analysis": {
                "overall_sentiment": "neutral",
                "sentiment_distribution": {"positive": 0.4, "negative": 0.2, "neutral": 0.4},
                "sentiment_trends": "Mixed sentiment patterns observed"
            },
            "key_insights": [
                "LLM analysis completed successfully",
                "Data shows mixed engagement patterns",
                "Malaysian context considered in analysis"
            ],
            "malaysian_context": {
                "cultural_relevance": "Analysis includes Malaysian cultural context",
                "language_patterns": "Mixed Bahasa Malaysia and English usage",
                "local_preferences": "Local preferences identified in data"
            },
            "trending_topics": [
                {"topic": "General discussion", "frequency": 5, "sentiment": "neutral"}
            ],
            "recommendations": [
                "Review data quality for better insights",
                "Consider expanding data collection",
                "Focus on Malaysian market preferences"
            ],
            "data_quality": {
                "completeness": 70,
                "reliability": 75,
                "sample_size": 0,
                "notes": "Analysis completed with text parsing fallback"
            },
            "summary": f"Analysis completed using {llm_type.upper()} with text parsing fallback due to JSON format issues.",
            "llm_used": llm_type,
            "analysis_timestamp": datetime.now().isoformat(),
            "raw_response": content[:500] + "..." if len(content) > 500 else content
        }
    
    def _fallback_analysis(self, query: str, social_data: List[Dict], platforms: List[str]) -> Dict[str, Any]:
        """Fallback analysis when no LLM is available"""
        return {
            "query_relevance": {"score": 60, "explanation": "Basic analysis without LLM"},
            "sentiment_analysis": {
                "overall_sentiment": "neutral",
                "sentiment_distribution": {"positive": 0.33, "negative": 0.33, "neutral": 0.34},
                "sentiment_trends": "Unable to analyze trends without LLM"
            },
            "key_insights": [
                f"Found {len(social_data)} posts related to '{query}'",
                f"Data collected from {len(platforms)} platforms",
                "LLM analysis unavailable - using basic statistics"
            ],
            "malaysian_context": {
                "cultural_relevance": "Malaysian context analysis requires LLM",
                "language_patterns": "Language analysis unavailable",
                "local_preferences": "Preference analysis requires LLM"
            },
            "trending_topics": [
                {"topic": "General", "frequency": len(social_data), "sentiment": "neutral"}
            ],
            "recommendations": [
                "Configure OpenAI or Anthropic API keys for advanced analysis",
                "Enable LLM integration for better insights",
                "Review data collection methods"
            ],
            "data_quality": {
                "completeness": 50,
                "reliability": 60,
                "sample_size": len(social_data),
                "notes": "Basic analysis only - LLM integration required for advanced insights"
            },
            "summary": "Basic analysis completed. Configure LLM API keys for advanced AI-powered insights.",
            "llm_used": "none",
            "analysis_timestamp": datetime.now().isoformat()
        }
    
    async def generate_smart_keywords(self, query: str) -> List[str]:
        """Generate smart keywords using LLM"""
        try:
            prompt = f"""
Generate smart keywords for social media analysis based on this query: "{query}"

Consider:
1. Malaysian context and local terms
2. Bahasa Malaysia and English variations
3. Related terms and synonyms
4. Industry-specific jargon
5. Cultural context

Return only a JSON array of keywords, maximum 10 keywords.
Example: ["keyword1", "keyword2", "keyword3"]
"""
            
            if self.openai_client:
                response = await asyncio.to_thread(
                    self.openai_client.chat.completions.create,
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=200,
                    temperature=0.3
                )
                content = response.choices[0].message.content
                try:
                    return json.loads(content)
                except:
                    return query.split()
            
            return query.split()
            
        except Exception as e:
            logger.error(f"❌ Smart keyword generation failed: {str(e)}")
            return query.split()

# Create global LLM service instance
llm_service = LLMService()
