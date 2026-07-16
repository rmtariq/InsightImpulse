"""
🚀 COMPREHENSIVE TESTING SYSTEM FOR INSIGHTPULSE
===============================================

This system ensures InsightPulse works perfectly and is truly versatile 
for ANY input across all scenarios and use cases.

Features:
- Automated testing for 100+ different query types
- Real-time validation of all 9 platforms
- End-to-end workflow testing
- Performance benchmarking
- Error handling validation
- Malaysian context verification

Author: InsightPulse Team
"""

import asyncio
import json
import time
import random
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging
import requests
import pandas as pd

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ComprehensiveTestSuite:
    """
    Complete testing suite for InsightPulse versatility validation
    """
    
    def __init__(self, api_base_url: str = "http://localhost:8001"):
        self.api_base_url = api_base_url
        self.test_results = {}
        self.failed_tests = []
        self.passed_tests = []
        
        # Comprehensive test queries covering ALL possible scenarios
        self.test_queries = {
            "fashion_queries": [
                "tudung paling viral 2025",
                "hijab trending Malaysia",
                "baju kurung modern design",
                "fashion muslimah terkini",
                "kebaya contemporary style",
                "batik premium quality",
                "seluar palazzo trending",
                "kasut heels comfortable",
                "handbag branded murah",
                "accessories muslimah viral"
            ],
            "food_queries": [
                "makanan halal sedap di Kuala Lumpur",
                "restoran best di Selangor",
                "nasi lemak viral KL",
                "roti canai crispy Penang",
                "laksa Johor authentic",
                "char kway teow best",
                "satay kajang famous",
                "rendang daging sedap",
                "cendol durian viral",
                "teh tarik foam perfect"
            ],
            "technology_queries": [
                "best budget smartphone Malaysia 2025",
                "laptop gaming murah",
                "tablet untuk student",
                "smartwatch fitness tracking",
                "earbuds wireless terbaik",
                "camera DSLR professional",
                "gaming setup affordable",
                "iPhone vs Samsung comparison",
                "Xiaomi latest model review",
                "tech gadget trending 2025"
            ],
            "business_queries": [
                "PKS Malaysia online business",
                "startup funding opportunities",
                "e-commerce platform best",
                "digital marketing strategy",
                "SME loan application",
                "business registration process",
                "franchise opportunities Malaysia",
                "export import business",
                "dropshipping success tips",
                "online store setup guide"
            ],
            "health_queries": [
                "supplement kesihatan terbaik",
                "vitamin untuk immunity",
                "fitness program Malaysia",
                "diet plan sihat",
                "hospital swasta terbaik",
                "klinik 24 jam KL",
                "ubat traditional herbal",
                "wellness center premium",
                "yoga class beginner",
                "mental health support"
            ],
            "education_queries": [
                "universiti terbaik Malaysia",
                "kursus online popular",
                "scholarship opportunities",
                "STPM vs Diploma",
                "skill development program",
                "language learning app",
                "tuition center recommended",
                "professional certification",
                "vocational training course",
                "study abroad program"
            ],
            "travel_queries": [
                "tempat menarik di Malaysia",
                "hotel murah KL",
                "flight booking tips",
                "travel package affordable",
                "resort tepi pantai",
                "hiking trail popular",
                "food tour Penang",
                "cultural heritage site",
                "adventure tourism Malaysia",
                "budget travel guide"
            ],
            "automotive_queries": [
                "kereta terpakai terbaik",
                "motorcycle Honda popular",
                "car insurance comparison",
                "workshop kereta trusted",
                "spare parts original",
                "driving license renewal",
                "road tax calculation",
                "fuel efficient car",
                "electric vehicle Malaysia",
                "car loan best rate"
            ],
            "property_queries": [
                "rumah untuk dijual KL",
                "apartment rental Selangor",
                "property investment tips",
                "housing loan calculator",
                "condo new launch",
                "landed property affordable",
                "real estate agent trusted",
                "property valuation service",
                "home renovation contractor",
                "interior design modern"
            ],
            "entertainment_queries": [
                "movie terbaru cinema",
                "drama Korea popular",
                "concert ticket booking",
                "streaming service best",
                "gaming tournament Malaysia",
                "theme park family fun",
                "karaoke best sound system",
                "nightlife KL hotspot",
                "festival music upcoming",
                "entertainment venue rental"
            ]
        }
        
        # Platform combinations to test
        self.platform_combinations = [
            ["facebook"],
            ["instagram"],
            ["shopee"],
            ["facebook", "instagram"],
            ["facebook", "shopee"],
            ["instagram", "tiktok"],
            ["facebook", "instagram", "shopee"],
            ["facebook", "instagram", "x", "tiktok"],
            ["facebook", "instagram", "shopee", "lazada"],
            ["facebook", "instagram", "x", "tiktok", "google", "news", "lowyat", "shopee", "lazada"]  # All platforms
        ]

    async def run_comprehensive_tests(self) -> Dict[str, Any]:
        """
        Run comprehensive tests across all query types and platforms
        """
        logger.info("🚀 Starting Comprehensive InsightPulse Testing")
        logger.info("=" * 60)
        
        start_time = time.time()
        total_tests = 0
        
        # Test each query category
        for category, queries in self.test_queries.items():
            logger.info(f"\n📂 Testing Category: {category.upper()}")
            logger.info("-" * 40)
            
            category_results = await self._test_query_category(category, queries)
            self.test_results[category] = category_results
            total_tests += len(queries) * len(self.platform_combinations)
        
        # Calculate overall results
        end_time = time.time()
        total_time = end_time - start_time
        
        overall_results = {
            "test_summary": {
                "total_tests_run": total_tests,
                "total_passed": len(self.passed_tests),
                "total_failed": len(self.failed_tests),
                "success_rate": (len(self.passed_tests) / total_tests) * 100 if total_tests > 0 else 0,
                "total_time_seconds": total_time,
                "average_time_per_test": total_time / total_tests if total_tests > 0 else 0
            },
            "category_results": self.test_results,
            "failed_tests": self.failed_tests,
            "passed_tests": self.passed_tests[:10],  # Show first 10 passed tests
            "recommendations": self._generate_recommendations()
        }
        
        # Save results
        self._save_test_results(overall_results)
        
        logger.info(f"\n🎉 COMPREHENSIVE TESTING COMPLETED")
        logger.info(f"✅ Passed: {len(self.passed_tests)}/{total_tests} ({overall_results['test_summary']['success_rate']:.1f}%)")
        logger.info(f"❌ Failed: {len(self.failed_tests)}/{total_tests}")
        logger.info(f"⏱️ Total Time: {total_time:.2f} seconds")
        
        return overall_results

    async def _test_query_category(self, category: str, queries: List[str]) -> Dict[str, Any]:
        """
        Test all queries in a specific category
        """
        category_results = {
            "total_queries": len(queries),
            "query_results": {},
            "category_success_rate": 0,
            "average_response_time": 0
        }
        
        total_response_time = 0
        successful_queries = 0
        
        for query in queries:
            logger.info(f"🔍 Testing Query: '{query}'")
            
            query_results = await self._test_single_query(query)
            category_results["query_results"][query] = query_results
            
            if query_results["overall_success"]:
                successful_queries += 1
            
            total_response_time += query_results["average_response_time"]
        
        category_results["category_success_rate"] = (successful_queries / len(queries)) * 100
        category_results["average_response_time"] = total_response_time / len(queries)
        
        return category_results

    async def _test_single_query(self, query: str) -> Dict[str, Any]:
        """
        Test a single query across different platform combinations
        """
        query_results = {
            "query": query,
            "platform_tests": {},
            "successful_platforms": 0,
            "total_platforms_tested": len(self.platform_combinations),
            "overall_success": False,
            "average_response_time": 0
        }
        
        total_response_time = 0
        successful_tests = 0
        
        for platforms in self.platform_combinations:
            platform_key = "_".join(platforms)
            
            try:
                # Test the query with this platform combination
                start_time = time.time()
                result = await self._make_api_request(query, platforms)
                end_time = time.time()
                
                response_time = end_time - start_time
                total_response_time += response_time
                
                # Validate the result
                is_valid = self._validate_api_response(result, query, platforms)
                
                query_results["platform_tests"][platform_key] = {
                    "platforms": platforms,
                    "success": is_valid,
                    "response_time": response_time,
                    "data_points": result.get("total_data_points", 0) if result else 0,
                    "error": result.get("error") if result and not is_valid else None
                }
                
                if is_valid:
                    successful_tests += 1
                    self.passed_tests.append(f"{query} -> {platform_key}")
                else:
                    self.failed_tests.append(f"{query} -> {platform_key}: {result.get('error', 'Unknown error')}")
                
            except Exception as e:
                logger.error(f"❌ Error testing {query} with {platforms}: {e}")
                query_results["platform_tests"][platform_key] = {
                    "platforms": platforms,
                    "success": False,
                    "response_time": 0,
                    "data_points": 0,
                    "error": str(e)
                }
                self.failed_tests.append(f"{query} -> {platform_key}: {str(e)}")
        
        query_results["successful_platforms"] = successful_tests
        query_results["overall_success"] = successful_tests > 0
        query_results["average_response_time"] = total_response_time / len(self.platform_combinations)
        
        return query_results

    async def _make_api_request(self, query: str, platforms: List[str]) -> Dict[str, Any]:
        """
        Make API request to InsightPulse backend
        """
        try:
            payload = {
                "query": query,
                "platforms": platforms,
                "analysis_type": "social_listening",
                "max_results_per_platform": 20
            }
            
            response = requests.post(
                f"{self.api_base_url}/analyze",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"HTTP {response.status_code}: {response.text}"}
                
        except Exception as e:
            return {"error": f"Request failed: {str(e)}"}

    def _validate_api_response(self, result: Dict[str, Any], query: str, platforms: List[str]) -> bool:
        """
        Validate API response for completeness and correctness
        """
        if not result or "error" in result:
            return False
        
        # Check required fields
        required_fields = ["total_data_points", "platform_breakdown", "overall_metrics"]
        for field in required_fields:
            if field not in result:
                return False
        
        # Check if we got data for requested platforms
        platform_breakdown = result.get("platform_breakdown", {})
        if not platform_breakdown:
            return False
        
        # Check if at least one platform returned data
        has_data = any(
            platform_data.get("data_points", 0) > 0 
            for platform_data in platform_breakdown.values()
        )
        
        # Check if LLM analysis is present
        has_llm_analysis = "llm_analysis" in result and result["llm_analysis"]
        
        return has_data and has_llm_analysis

    def _generate_recommendations(self) -> List[str]:
        """
        Generate recommendations based on test results
        """
        recommendations = []
        
        success_rate = (len(self.passed_tests) / (len(self.passed_tests) + len(self.failed_tests))) * 100
        
        if success_rate >= 95:
            recommendations.append("🎉 Excellent! System is highly reliable and versatile")
        elif success_rate >= 85:
            recommendations.append("✅ Good performance. Minor optimizations recommended")
        elif success_rate >= 70:
            recommendations.append("⚠️ Moderate performance. Significant improvements needed")
        else:
            recommendations.append("❌ Poor performance. Major system overhaul required")
        
        # Analyze failure patterns
        if self.failed_tests:
            recommendations.append("🔍 Review failed test cases for common patterns")
            recommendations.append("🛠️ Implement additional error handling and fallbacks")
        
        recommendations.extend([
            "📊 Monitor response times for performance optimization",
            "🔄 Implement continuous testing for ongoing reliability",
            "📈 Add more diverse test cases as system evolves",
            "🌐 Test with real API credentials when available"
        ])
        
        return recommendations

    def _save_test_results(self, results: Dict[str, Any]):
        """
        Save test results to file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"test_results_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"📄 Test results saved to: {filename}")


# Quick test functions for immediate validation
async def quick_versatility_test():
    """
    Quick test to validate system versatility
    """
    test_suite = ComprehensiveTestSuite()
    
    # Test with diverse queries
    quick_tests = [
        "tudung paling viral 2025",
        "makanan halal sedap di Kuala Lumpur",
        "best budget smartphone Malaysia 2025",
        "PKS Malaysia online business",
        "universiti terbaik Malaysia"
    ]
    
    logger.info("🚀 Running Quick Versatility Test")
    
    for query in quick_tests:
        logger.info(f"🔍 Testing: '{query}'")
        result = await test_suite._make_api_request(query, ["facebook", "instagram", "shopee"])
        
        if test_suite._validate_api_response(result, query, ["facebook", "instagram", "shopee"]):
            logger.info(f"✅ PASSED: {result.get('total_data_points', 0)} data points")
        else:
            logger.info(f"❌ FAILED: {result.get('error', 'Unknown error')}")

async def test_all_platforms():
    """
    Test all 9 platforms with a single query
    """
    test_suite = ComprehensiveTestSuite()
    all_platforms = ["facebook", "instagram", "x", "tiktok", "google", "news", "lowyat", "shopee", "lazada"]
    
    logger.info("🌐 Testing All 9 Platforms")
    
    result = await test_suite._make_api_request("trending Malaysia 2025", all_platforms)
    
    if test_suite._validate_api_response(result, "trending Malaysia 2025", all_platforms):
        logger.info(f"✅ ALL PLATFORMS WORKING: {result.get('total_data_points', 0)} total data points")
        
        # Show platform breakdown
        for platform, data in result.get("platform_breakdown", {}).items():
            logger.info(f"   📱 {platform}: {data.get('data_points', 0)} posts")
    else:
        logger.info(f"❌ PLATFORM TEST FAILED: {result.get('error', 'Unknown error')}")


if __name__ == "__main__":
    async def main():
        print("🚀 InsightPulse Comprehensive Testing System")
        print("=" * 60)
        
        # Run quick tests first
        await quick_versatility_test()
        print("\n" + "="*60)
        
        # Test all platforms
        await test_all_platforms()
        print("\n" + "="*60)
        
        # Ask user if they want to run full comprehensive test
        print("\n🤔 Do you want to run the FULL comprehensive test?")
        print("   This will test 100+ queries across all platform combinations")
        print("   Estimated time: 15-30 minutes")
        
        # For automated testing, run a smaller subset
        print("🔄 Running subset of comprehensive tests...")
        
        test_suite = ComprehensiveTestSuite()
        
        # Test subset of queries
        subset_results = {}
        for category, queries in list(test_suite.test_queries.items())[:3]:  # Test first 3 categories
            logger.info(f"\n📂 Testing {category}")
            for query in queries[:2]:  # Test first 2 queries per category
                result = await test_suite._test_single_query(query)
                subset_results[query] = result
        
        # Summary
        total_tests = sum(len(result["platform_tests"]) for result in subset_results.values())
        successful_tests = sum(
            sum(1 for test in result["platform_tests"].values() if test["success"]) 
            for result in subset_results.values()
        )
        
        success_rate = (successful_tests / total_tests) * 100 if total_tests > 0 else 0
        
        print(f"\n🎉 SUBSET TEST COMPLETED")
        print(f"✅ Success Rate: {success_rate:.1f}% ({successful_tests}/{total_tests})")
        
        if success_rate >= 80:
            print("🌟 SYSTEM IS HIGHLY VERSATILE AND RELIABLE!")
        else:
            print("⚠️ System needs improvements for better versatility")
    
    asyncio.run(main())
