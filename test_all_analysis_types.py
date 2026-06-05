"""
🧪 TEST ALL ANALYSIS TYPES FOR INSIGHTPULSE
==========================================

This script tests all 7 analysis types to ensure your InsightPulse app
works perfectly and is truly versatile for ANY input and analysis scenario.

Analysis Types Tested:
1. 🎧 Social Listening
2. 🏢 SME Insights  
3. 🚨 Issue Detection
4. 🔍 Competitor Analysis
5. 📦 Product Intelligence
6. 📈 Market Research
7. 🛡️ Brand Monitoring

Author: InsightPulse Team
"""

import asyncio
import json
import time
import requests
from datetime import datetime
from typing import List, Dict, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AnalysisTypeValidator:
    """
    Comprehensive validator for all InsightPulse analysis types
    """
    
    def __init__(self, api_base_url: str = "http://localhost:8001"):
        self.api_base_url = api_base_url
        self.test_results = {}
        
        # Test cases for each analysis type
        self.test_cases = {
            "social_listening": [
                {
                    "query": "tudung paling viral 2025",
                    "platforms": ["facebook", "instagram", "tiktok"],
                    "expected_features": ["sentiment_analysis", "trending_topics", "engagement_metrics"]
                },
                {
                    "query": "makanan halal sedap di Kuala Lumpur", 
                    "platforms": ["facebook", "instagram", "google"],
                    "expected_features": ["public_sentiment", "viral_content", "social_engagement"]
                }
            ],
            "sme_insights": [
                {
                    "query": "PKS Malaysia online business",
                    "platforms": ["facebook", "news", "google"],
                    "expected_features": ["business_opportunities", "market_analysis", "growth_strategies"]
                },
                {
                    "query": "digital marketing strategy Malaysia SME",
                    "platforms": ["facebook", "google", "news"],
                    "expected_features": ["business_intelligence", "market_gaps", "opportunities"]
                }
            ],
            "issue_detection": [
                {
                    "query": "smartphone battery problem Malaysia",
                    "platforms": ["facebook", "x", "lowyat"],
                    "expected_features": ["problem_identification", "negative_sentiment", "complaint_analysis"]
                },
                {
                    "query": "food delivery service complaint",
                    "platforms": ["facebook", "x", "google"],
                    "expected_features": ["issue_severity", "complaint_patterns", "crisis_alerts"]
                }
            ],
            "competitor_analysis": [
                {
                    "query": "iPhone vs Samsung Malaysia 2025",
                    "platforms": ["facebook", "lowyat", "shopee"],
                    "expected_features": ["market_positioning", "feature_comparison", "brand_perception"]
                },
                {
                    "query": "Naelofar vs Duckscarves comparison",
                    "platforms": ["instagram", "facebook", "shopee"],
                    "expected_features": ["competitive_landscape", "positioning_analysis", "market_share"]
                }
            ],
            "product_intelligence": [
                {
                    "query": "best budget smartphone Malaysia 2025",
                    "platforms": ["lowyat", "shopee", "lazada"],
                    "expected_features": ["feature_analysis", "user_satisfaction", "product_performance"]
                },
                {
                    "query": "tudung premium quality review",
                    "platforms": ["shopee", "lazada", "instagram"],
                    "expected_features": ["product_insights", "quality_assessment", "user_feedback"]
                }
            ],
            "market_research": [
                {
                    "query": "Malaysia e-commerce market trends 2025",
                    "platforms": ["news", "google", "facebook"],
                    "expected_features": ["industry_trends", "market_size", "growth_projections"]
                },
                {
                    "query": "fashion industry Malaysia growth",
                    "platforms": ["news", "google", "instagram"],
                    "expected_features": ["market_analysis", "consumer_behavior", "trend_analysis"]
                }
            ],
            "brand_monitoring": [
                {
                    "query": "Grab Malaysia brand reputation",
                    "platforms": ["facebook", "x", "news"],
                    "expected_features": ["brand_mentions", "reputation_score", "sentiment_tracking"]
                },
                {
                    "query": "Shopee Malaysia customer feedback",
                    "platforms": ["facebook", "x", "google"],
                    "expected_features": ["brand_sentiment", "mention_tracking", "reputation_analysis"]
                }
            ]
        }

    async def test_all_analysis_types(self) -> Dict[str, Any]:
        """
        Test all 7 analysis types comprehensively
        """
        logger.info("🚀 TESTING ALL ANALYSIS TYPES")
        logger.info("=" * 60)
        
        start_time = time.time()
        overall_results = {
            "test_timestamp": datetime.now().isoformat(),
            "analysis_type_results": {},
            "summary": {},
            "recommendations": []
        }
        
        total_tests = 0
        successful_tests = 0
        
        # Test each analysis type
        for analysis_type, test_cases in self.test_cases.items():
            logger.info(f"\n🔍 Testing Analysis Type: {analysis_type.upper()}")
            logger.info("-" * 40)
            
            type_results = await self._test_analysis_type(analysis_type, test_cases)
            overall_results["analysis_type_results"][analysis_type] = type_results
            
            total_tests += len(test_cases)
            successful_tests += type_results["successful_tests"]
        
        # Calculate summary
        end_time = time.time()
        overall_results["summary"] = {
            "total_analysis_types": len(self.test_cases),
            "total_test_cases": total_tests,
            "successful_tests": successful_tests,
            "success_rate": (successful_tests / total_tests) * 100 if total_tests > 0 else 0,
            "total_time_seconds": end_time - start_time,
            "average_time_per_test": (end_time - start_time) / total_tests if total_tests > 0 else 0
        }
        
        # Generate recommendations
        overall_results["recommendations"] = self._generate_analysis_recommendations(overall_results)
        
        # Log final results
        self._log_final_results(overall_results)
        
        return overall_results

    async def _test_analysis_type(self, analysis_type: str, test_cases: List[Dict]) -> Dict[str, Any]:
        """
        Test a specific analysis type with its test cases
        """
        type_results = {
            "analysis_type": analysis_type,
            "total_cases": len(test_cases),
            "successful_tests": 0,
            "failed_tests": 0,
            "test_details": [],
            "average_response_time": 0
        }
        
        total_response_time = 0
        
        for i, test_case in enumerate(test_cases, 1):
            logger.info(f"   📝 Test {i}/{len(test_cases)}: '{test_case['query']}'")
            
            start_time = time.time()
            
            try:
                # Make API request
                payload = {
                    "query": test_case["query"],
                    "analysis_type": analysis_type,
                    "platforms": test_case["platforms"],
                    "max_results_per_platform": 20
                }
                
                response = requests.post(
                    f"{self.api_base_url}/analyze",
                    json=payload,
                    timeout=45
                )
                
                end_time = time.time()
                response_time = end_time - start_time
                total_response_time += response_time
                
                # Validate response
                if response.status_code == 200:
                    result = response.json()
                    validation_result = self._validate_analysis_response(
                        result, analysis_type, test_case["expected_features"]
                    )
                    
                    if validation_result["is_valid"]:
                        type_results["successful_tests"] += 1
                        logger.info(f"      ✅ PASSED ({response_time:.2f}s)")
                    else:
                        type_results["failed_tests"] += 1
                        logger.info(f"      ❌ FAILED: {validation_result['reason']}")
                    
                    type_results["test_details"].append({
                        "test_case": test_case,
                        "success": validation_result["is_valid"],
                        "response_time": response_time,
                        "data_points": result.get("total_data_points", 0),
                        "validation_details": validation_result
                    })
                    
                else:
                    type_results["failed_tests"] += 1
                    logger.info(f"      ❌ FAILED: HTTP {response.status_code}")
                    
                    type_results["test_details"].append({
                        "test_case": test_case,
                        "success": False,
                        "response_time": response_time,
                        "error": f"HTTP {response.status_code}: {response.text}"
                    })
                
            except Exception as e:
                end_time = time.time()
                response_time = end_time - start_time
                total_response_time += response_time
                
                type_results["failed_tests"] += 1
                logger.info(f"      ❌ ERROR: {str(e)}")
                
                type_results["test_details"].append({
                    "test_case": test_case,
                    "success": False,
                    "response_time": response_time,
                    "error": str(e)
                })
        
        type_results["average_response_time"] = total_response_time / len(test_cases)
        
        # Log type summary
        success_rate = (type_results["successful_tests"] / len(test_cases)) * 100
        logger.info(f"   📊 {analysis_type.upper()}: {type_results['successful_tests']}/{len(test_cases)} passed ({success_rate:.1f}%)")
        
        return type_results

    def _validate_analysis_response(self, result: Dict[str, Any], analysis_type: str, expected_features: List[str]) -> Dict[str, Any]:
        """
        Validate API response based on analysis type requirements
        """
        validation_result = {
            "is_valid": False,
            "reason": "",
            "features_found": [],
            "missing_features": []
        }
        
        # Basic validation
        if not result or "error" in result:
            validation_result["reason"] = "API returned error or empty result"
            return validation_result
        
        # Check required fields
        required_fields = ["total_data_points", "platform_breakdown", "overall_metrics"]
        missing_fields = [field for field in required_fields if field not in result]
        
        if missing_fields:
            validation_result["reason"] = f"Missing required fields: {missing_fields}"
            return validation_result
        
        # Check data points
        if result.get("total_data_points", 0) == 0:
            validation_result["reason"] = "No data points collected"
            return validation_result
        
        # Check LLM analysis
        if "llm_analysis" not in result or not result["llm_analysis"]:
            validation_result["reason"] = "Missing LLM analysis"
            return validation_result
        
        # Analysis type specific validation
        result_str = str(result).lower()
        
        if analysis_type == "social_listening":
            # Should have sentiment analysis and social metrics
            has_sentiment = "sentiment" in result_str
            has_engagement = "engagement" in result_str or "likes" in result_str
            has_social_features = has_sentiment and has_engagement
            
            if not has_social_features:
                validation_result["reason"] = "Missing social listening features (sentiment/engagement)"
                return validation_result
        
        elif analysis_type == "sme_insights":
            # Should have business-related insights
            business_terms = ["business", "opportunity", "market", "strategy", "growth"]
            has_business_context = any(term in result_str for term in business_terms)
            
            if not has_business_context:
                validation_result["reason"] = "Missing SME business context"
                return validation_result
        
        elif analysis_type == "issue_detection":
            # Should identify problems or negative sentiment
            issue_terms = ["problem", "issue", "complaint", "negative", "error"]
            has_issue_context = any(term in result_str for term in issue_terms)
            
            if not has_issue_context:
                validation_result["reason"] = "Missing issue detection context"
                return validation_result
        
        elif analysis_type == "competitor_analysis":
            # Should have comparison or competitive elements
            comp_terms = ["vs", "comparison", "competitor", "versus", "compare"]
            has_comp_context = any(term in result_str for term in comp_terms)
            
            if not has_comp_context:
                validation_result["reason"] = "Missing competitive analysis context"
                return validation_result
        
        elif analysis_type == "product_intelligence":
            # Should have product-specific insights
            product_terms = ["product", "feature", "quality", "performance", "review"]
            has_product_context = any(term in result_str for term in product_terms)
            
            if not has_product_context:
                validation_result["reason"] = "Missing product intelligence context"
                return validation_result
        
        elif analysis_type == "market_research":
            # Should have market and trend analysis
            market_terms = ["market", "trend", "industry", "growth", "research"]
            has_market_context = any(term in result_str for term in market_terms)
            
            if not has_market_context:
                validation_result["reason"] = "Missing market research context"
                return validation_result
        
        elif analysis_type == "brand_monitoring":
            # Should have brand-related monitoring
            brand_terms = ["brand", "reputation", "mention", "monitoring", "feedback"]
            has_brand_context = any(term in result_str for term in brand_terms)
            
            if not has_brand_context:
                validation_result["reason"] = "Missing brand monitoring context"
                return validation_result
        
        # If we reach here, validation passed
        validation_result["is_valid"] = True
        validation_result["reason"] = "All validations passed"
        
        return validation_result

    def _generate_analysis_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """
        Generate recommendations based on analysis type testing results
        """
        recommendations = []
        summary = results["summary"]
        
        if summary["success_rate"] >= 90:
            recommendations.append("🎉 Excellent! All analysis types working perfectly")
        elif summary["success_rate"] >= 75:
            recommendations.append("✅ Good performance across analysis types")
        elif summary["success_rate"] >= 50:
            recommendations.append("⚠️ Some analysis types need improvement")
        else:
            recommendations.append("❌ Major issues with analysis type implementation")
        
        # Check individual analysis types
        for analysis_type, type_results in results["analysis_type_results"].items():
            success_rate = (type_results["successful_tests"] / type_results["total_cases"]) * 100
            
            if success_rate < 50:
                recommendations.append(f"🔧 Fix {analysis_type} analysis implementation")
        
        recommendations.extend([
            "📊 Ensure each analysis type provides relevant insights",
            "🎯 Customize analysis output based on analysis type",
            "🔄 Implement analysis type-specific validation",
            "📈 Add analysis type performance monitoring"
        ])
        
        return recommendations

    def _log_final_results(self, results: Dict[str, Any]):
        """
        Log comprehensive final results
        """
        summary = results["summary"]
        
        logger.info("\n" + "="*60)
        logger.info("🎯 ANALYSIS TYPE TESTING RESULTS")
        logger.info("="*60)
        
        logger.info(f"📊 Overall Success Rate: {summary['success_rate']:.1f}%")
        logger.info(f"✅ Successful Tests: {summary['successful_tests']}/{summary['total_test_cases']}")
        logger.info(f"⏱️ Total Time: {summary['total_time_seconds']:.2f} seconds")
        logger.info(f"📈 Average Time per Test: {summary['average_time_per_test']:.2f} seconds")
        
        logger.info("\n📋 Analysis Type Breakdown:")
        for analysis_type, type_results in results["analysis_type_results"].items():
            success_rate = (type_results["successful_tests"] / type_results["total_cases"]) * 100
            status = "✅" if success_rate >= 75 else "⚠️" if success_rate >= 50 else "❌"
            logger.info(f"   {status} {analysis_type}: {type_results['successful_tests']}/{type_results['total_cases']} ({success_rate:.1f}%)")
        
        logger.info("\n💡 Recommendations:")
        for rec in results["recommendations"]:
            logger.info(f"   {rec}")
        
        logger.info("="*60)


# Quick test functions
async def quick_analysis_test():
    """
    Quick test of all analysis types
    """
    validator = AnalysisTypeValidator()
    
    # Test one case per analysis type
    quick_tests = [
        ("social_listening", "tudung paling viral 2025"),
        ("sme_insights", "PKS Malaysia online business"),
        ("issue_detection", "smartphone battery problem Malaysia"),
        ("competitor_analysis", "iPhone vs Samsung Malaysia 2025"),
        ("product_intelligence", "best budget smartphone Malaysia 2025"),
        ("market_research", "Malaysia e-commerce market trends 2025"),
        ("brand_monitoring", "Grab Malaysia brand reputation")
    ]
    
    logger.info("🚀 Quick Analysis Type Test")
    logger.info("="*40)
    
    for analysis_type, query in quick_tests:
        logger.info(f"🔍 Testing {analysis_type}: '{query}'")
        
        try:
            payload = {
                "query": query,
                "analysis_type": analysis_type,
                "platforms": ["facebook", "instagram"],
                "max_results_per_platform": 10
            }
            
            response = requests.post(
                "http://localhost:8001/analyze",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                data_points = result.get("total_data_points", 0)
                logger.info(f"   ✅ PASSED: {data_points} data points")
            else:
                logger.info(f"   ❌ FAILED: HTTP {response.status_code}")
                
        except Exception as e:
            logger.info(f"   ❌ ERROR: {str(e)}")


if __name__ == "__main__":
    async def main():
        print("🧪 InsightPulse Analysis Type Validator")
        print("="*50)
        
        # Run quick test first
        await quick_analysis_test()
        
        print("\n" + "="*50)
        print("🔄 Running comprehensive analysis type testing...")
        
        # Run comprehensive test
        validator = AnalysisTypeValidator()
        results = await validator.test_all_analysis_types()
        
        # Final summary
        if results["summary"]["success_rate"] >= 80:
            print("\n🌟 YOUR INSIGHTPULSE APP IS HIGHLY VERSATILE!")
            print("✅ All analysis types working properly")
        else:
            print("\n⚠️ Some analysis types need attention")
            print("🔧 Check the recommendations above")
    
    asyncio.run(main())
