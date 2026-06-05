"""
🚀 REAL-TIME CRAWLER SIMULATOR FOR INSIGHTPULSE
==============================================

This module integrates the synthetic data generator with the InsightPulse backend
to simulate the complete real-time crawling workflow:

1. User Input → Keyword Extraction
2. Platform Selection → Real-time Crawling Simulation  
3. Data Generation → AI Analysis
4. Professional Report → Dashboard Display

Author: InsightPulse Team
"""

import asyncio
import json
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

from synthetic_data_generator import SyntheticDataGenerator, quick_generate_data

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RealTimeCrawlerSimulator:
    """
    Simulates real-time crawling process for InsightPulse development
    """
    
    def __init__(self):
        self.generator = SyntheticDataGenerator()
        self.crawl_sessions = {}
        
    async def start_crawling_session(self, 
                                   query: str, 
                                   platforms: List[str], 
                                   posts_per_platform: int = 50,
                                   session_id: str = None) -> Dict[str, Any]:
        """
        Start a real-time crawling simulation session
        """
        if session_id is None:
            session_id = f"crawl_{int(time.time())}"
        
        logger.info(f"🚀 Starting crawling session: {session_id}")
        logger.info(f"🔍 Query: '{query}'")
        logger.info(f"📱 Platforms: {platforms}")
        logger.info(f"📊 Posts per platform: {posts_per_platform}")
        
        # Initialize session
        session = {
            "session_id": session_id,
            "query": query,
            "platforms": platforms,
            "posts_per_platform": posts_per_platform,
            "status": "initializing",
            "start_time": datetime.now().isoformat(),
            "progress": {},
            "results": {},
            "total_posts": 0
        }
        
        self.crawl_sessions[session_id] = session
        
        try:
            # Phase 1: Keyword Analysis
            session["status"] = "analyzing_keywords"
            logger.info("🧠 Phase 1: Analyzing keywords and context...")
            await asyncio.sleep(1)  # Simulate processing time
            
            keyword_data = self.generator.extract_keywords_from_query(query)
            session["keyword_analysis"] = keyword_data
            
            # Phase 2: Platform Crawling
            session["status"] = "crawling"
            logger.info("🕷️ Phase 2: Starting platform crawling...")
            
            for i, platform in enumerate(platforms):
                logger.info(f"📱 Crawling {platform}... ({i+1}/{len(platforms)})")
                
                # Update progress
                session["progress"][platform] = "crawling"
                
                # Simulate crawling time
                await asyncio.sleep(2)
                
                # Generate data
                df = self.generator.generate_platform_data(platform, query, posts_per_platform)
                
                # Save data
                self.generator.save_platform_data(platform, query, df)
                
                # Update results
                session["results"][platform] = {
                    "status": "completed",
                    "posts_found": len(df),
                    "avg_sentiment": float(df["sentiment_score"].mean()),
                    "total_engagement": int(df["total_engagement"].sum()),
                    "completion_time": datetime.now().isoformat()
                }
                
                session["progress"][platform] = "completed"
                session["total_posts"] += len(df)
                
                logger.info(f"✅ {platform}: {len(df)} posts collected")
            
            # Phase 3: Analysis
            session["status"] = "analyzing"
            logger.info("🤖 Phase 3: Running AI analysis...")
            await asyncio.sleep(2)
            
            # Phase 4: Complete
            session["status"] = "completed"
            session["end_time"] = datetime.now().isoformat()
            
            logger.info(f"🎉 Crawling session completed: {session_id}")
            logger.info(f"📊 Total posts collected: {session['total_posts']}")
            
            return session
            
        except Exception as e:
            logger.error(f"❌ Error in crawling session {session_id}: {e}")
            session["status"] = "error"
            session["error"] = str(e)
            return session
    
    def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """
        Get current status of a crawling session
        """
        return self.crawl_sessions.get(session_id, {"error": "Session not found"})
    
    def list_active_sessions(self) -> List[Dict[str, Any]]:
        """
        List all active crawling sessions
        """
        return [
            {
                "session_id": sid,
                "query": session["query"],
                "status": session["status"],
                "platforms": session["platforms"],
                "total_posts": session.get("total_posts", 0)
            }
            for sid, session in self.crawl_sessions.items()
        ]

class InsightPulseWorkflowSimulator:
    """
    Complete workflow simulator for InsightPulse development
    """
    
    def __init__(self):
        self.crawler_sim = RealTimeCrawlerSimulator()
    
    async def complete_analysis_workflow(self, 
                                       query: str, 
                                       platforms: List[str] = None,
                                       posts_per_platform: int = 50) -> Dict[str, Any]:
        """
        Simulate the complete InsightPulse analysis workflow
        """
        if platforms is None:
            platforms = self._auto_select_platforms(query)
        
        logger.info(f"🎯 Starting complete analysis workflow")
        logger.info(f"🔍 Query: '{query}'")
        logger.info(f"📱 Auto-selected platforms: {platforms}")
        
        # Step 1: Start crawling
        session = await self.crawler_sim.start_crawling_session(
            query, platforms, posts_per_platform
        )
        
        # Step 2: Prepare analysis results
        analysis_results = self._prepare_analysis_results(session)
        
        return analysis_results
    
    def _auto_select_platforms(self, query: str) -> List[str]:
        """
        Automatically select appropriate platforms based on query
        """
        query_lower = query.lower()
        
        # Base platforms
        platforms = ["facebook", "instagram"]
        
        # Fashion queries
        if any(term in query_lower for term in ["tudung", "hijab", "fashion", "baju", "style"]):
            platforms.extend(["tiktok", "shopee", "lazada"])
        
        # Food queries  
        elif any(term in query_lower for term in ["makanan", "food", "halal", "restaurant", "sedap"]):
            platforms.extend(["google", "news", "shopee"])
        
        # Technology queries
        elif any(term in query_lower for term in ["smartphone", "laptop", "tech", "gadget", "phone"]):
            platforms.extend(["x", "lowyat", "shopee", "lazada"])
        
        # General queries
        else:
            platforms.extend(["google", "news"])
        
        return platforms[:5]  # Limit to 5 platforms for efficiency
    
    def _prepare_analysis_results(self, session: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare analysis results in InsightPulse format
        """
        if session["status"] != "completed":
            return {"error": "Crawling session not completed", "session": session}
        
        # Calculate overall metrics
        total_posts = session["total_posts"]
        total_engagement = sum(
            result["total_engagement"] 
            for result in session["results"].values() 
            if result["status"] == "completed"
        )
        
        avg_sentiment = sum(
            result["avg_sentiment"] 
            for result in session["results"].values() 
            if result["status"] == "completed"
        ) / len([r for r in session["results"].values() if r["status"] == "completed"])
        
        # Prepare InsightPulse format
        analysis_results = {
            "query": session["query"],
            "analysis_timestamp": session["end_time"],
            "total_data_points": total_posts,
            "platforms_analyzed": list(session["results"].keys()),
            "overall_metrics": {
                "sentiment_score": avg_sentiment,
                "total_engagement": total_engagement,
                "reliability": {"score": 0.85}  # High reliability for synthetic data
            },
            "platform_breakdown": {},
            "key_insights": self._generate_insights(session),
            "recommendations": self._generate_recommendations(session),
            "llm_analysis": {
                "summary": self._generate_summary(session),
                "llm_used": "Synthetic Data Generator",
                "query_relevance": {"score": 95},
                "sentiment_analysis": {"overall_sentiment": "positive" if avg_sentiment > 0.6 else "negative" if avg_sentiment < 0.4 else "neutral"}
            },
            "sentiment_trends": self._generate_sentiment_trends(session)
        }
        
        # Add platform breakdown
        for platform, result in session["results"].items():
            if result["status"] == "completed":
                analysis_results["platform_breakdown"][platform] = {
                    "data_points": result["posts_found"],
                    "status": "success",
                    "processed_insights": {
                        "total_engagement": result["total_engagement"],
                        "custom_sentiment": {
                            "primary_sentiment": "positive" if result["avg_sentiment"] > 0.6 else "negative" if result["avg_sentiment"] < 0.4 else "neutral",
                            "confidence": 0.85
                        }
                    }
                }
        
        return analysis_results
    
    def _generate_insights(self, session: Dict[str, Any]) -> List[str]:
        """Generate key insights based on session results"""
        insights = []
        query = session["query"]
        domain = session.get("keyword_analysis", {}).get("domain", "general")
        
        if domain == "fashion":
            insights.extend([
                f"Strong interest in {query} across Malaysian social media platforms",
                "Fashion content shows high engagement on visual platforms like Instagram and TikTok",
                "E-commerce platforms show positive reviews and purchasing intent",
                "Malaysian consumers prefer local and international fashion brands"
            ])
        elif domain == "food":
            insights.extend([
                f"High demand for {query} information across multiple platforms",
                "Food content generates strong engagement and sharing behavior",
                "Location-based recommendations are highly valued by Malaysian users",
                "Halal certification is a key consideration for Malaysian consumers"
            ])
        elif domain == "technology":
            insights.extend([
                f"Active discussions about {query} in tech communities",
                "Price-performance ratio is a major consideration for Malaysian buyers",
                "Forum discussions provide detailed technical insights",
                "E-commerce reviews influence purchasing decisions significantly"
            ])
        else:
            insights.extend([
                f"Significant online discussion about {query} in Malaysia",
                "Cross-platform engagement indicates broad interest",
                "Positive sentiment suggests favorable market reception",
                "Malaysian context shows cultural relevance and local adaptation"
            ])
        
        return insights
    
    def _generate_recommendations(self, session: Dict[str, Any]) -> List[str]:
        """Generate strategic recommendations"""
        return [
            "Focus marketing efforts on high-engagement platforms identified",
            "Leverage positive sentiment for brand positioning and messaging",
            "Monitor trending topics for content marketing opportunities",
            "Engage with Malaysian cultural context for better market penetration",
            "Consider influencer partnerships on visual platforms for maximum reach"
        ]
    
    def _generate_summary(self, session: Dict[str, Any]) -> str:
        """Generate LLM-style summary"""
        query = session["query"]
        total_posts = session["total_posts"]
        platforms = len(session["results"])
        
        return f"Analysis of '{query}' reveals strong engagement across {platforms} platforms with {total_posts} data points collected. The Malaysian market shows positive reception with high engagement rates, particularly on visual and e-commerce platforms. Cultural relevance and local preferences are key factors driving consumer interest and purchasing decisions."
    
    def _generate_sentiment_trends(self, session: Dict[str, Any]) -> Dict[str, Any]:
        """Generate sentiment trends data"""
        return {
            "summary": {
                "trend_direction": "positive",
                "peak_sentiment_date": datetime.now().strftime("%Y-%m-%d"),
                "overall_stability": "stable"
            },
            "trend_analysis": {
                "direction": "upward",
                "strength": "moderate",
                "consistency": "high"
            }
        }


# Convenience functions for easy testing
async def test_tudung_analysis():
    """Test tudung analysis workflow"""
    simulator = InsightPulseWorkflowSimulator()
    return await simulator.complete_analysis_workflow(
        "tudung paling viral 2025",
        ["facebook", "instagram", "tiktok", "shopee", "lazada"],
        30
    )

async def test_food_analysis():
    """Test food analysis workflow"""
    simulator = InsightPulseWorkflowSimulator()
    return await simulator.complete_analysis_workflow(
        "makanan halal sedap di Kuala Lumpur",
        ["facebook", "instagram", "google", "news", "shopee"],
        30
    )

async def test_tech_analysis():
    """Test technology analysis workflow"""
    simulator = InsightPulseWorkflowSimulator()
    return await simulator.complete_analysis_workflow(
        "best budget smartphone Malaysia 2025",
        ["facebook", "x", "lowyat", "shopee", "lazada"],
        30
    )


if __name__ == "__main__":
    async def main():
        print("🚀 InsightPulse Real-Time Crawler Simulator")
        print("=" * 50)
        
        # Test different analysis types
        test_cases = [
            ("tudung paling viral 2025", test_tudung_analysis),
            ("makanan halal sedap di Kuala Lumpur", test_food_analysis),
            ("best budget smartphone Malaysia 2025", test_tech_analysis)
        ]
        
        for query, test_func in test_cases:
            print(f"\n🎯 Testing: '{query}'")
            result = await test_func()
            
            if "error" not in result:
                print(f"✅ Success: {result['total_data_points']} posts across {len(result['platforms_analyzed'])} platforms")
                print(f"📊 Sentiment: {result['overall_metrics']['sentiment_score']:.2f}")
                print(f"🤖 Summary: {result['llm_analysis']['summary'][:100]}...")
            else:
                print(f"❌ Error: {result['error']}")
        
        print(f"\n🎉 All tests completed!")
        print(f"📂 Data available in: data/smart_crawlers/")
    
    asyncio.run(main())
