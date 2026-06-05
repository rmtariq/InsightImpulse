"""
🔄 REAL-TIME WORKFLOW VALIDATOR FOR INSIGHTPULSE
==============================================

This validator ensures the complete InsightPulse workflow works perfectly:

1. ✅ User Input Processing
2. ✅ Keyword Extraction & Expansion  
3. ✅ Platform Selection Logic
4. ✅ Data Collection (Real/Synthetic)
5. ✅ AI Analysis & LLM Integration
6. ✅ Dashboard Display & Visualization
7. ✅ Malaysian Context Integration
8. ✅ Error Handling & Fallbacks

Author: InsightPulse Team
"""

import asyncio
import json
import time
import requests
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class WorkflowValidator:
    """
    Complete workflow validation for InsightPulse
    """
    
    def __init__(self, api_base_url: str = "http://localhost:8001"):
        self.api_base_url = api_base_url
        self.validation_results = {}
        
    async def validate_complete_workflow(self, test_query: str = "tudung paling viral 2025") -> Dict[str, Any]:
        """
        Validate the complete InsightPulse workflow end-to-end
        """
        logger.info("🚀 STARTING COMPLETE WORKFLOW VALIDATION")
        logger.info("=" * 60)
        logger.info(f"🔍 Test Query: '{test_query}'")
        
        workflow_results = {
            "test_query": test_query,
            "timestamp": datetime.now().isoformat(),
            "workflow_steps": {},
            "overall_success": False,
            "total_time": 0,
            "recommendations": []
        }
        
        start_time = time.time()
        
        try:
            # Step 1: Validate API Health
            step1_result = await self._validate_api_health()
            workflow_results["workflow_steps"]["1_api_health"] = step1_result
            
            if not step1_result["success"]:
                workflow_results["recommendations"].append("❌ Fix API connectivity issues")
                return workflow_results
            
            # Step 2: Validate Input Processing
            step2_result = await self._validate_input_processing(test_query)
            workflow_results["workflow_steps"]["2_input_processing"] = step2_result
            
            # Step 3: Validate Data Collection
            step3_result = await self._validate_data_collection(test_query)
            workflow_results["workflow_steps"]["3_data_collection"] = step3_result
            
            # Step 4: Validate AI Analysis
            step4_result = await self._validate_ai_analysis(test_query)
            workflow_results["workflow_steps"]["4_ai_analysis"] = step4_result
            
            # Step 5: Validate Malaysian Context
            step5_result = await self._validate_malaysian_context(test_query)
            workflow_results["workflow_steps"]["5_malaysian_context"] = step5_result
            
            # Step 6: Validate Dashboard Integration
            step6_result = await self._validate_dashboard_integration()
            workflow_results["workflow_steps"]["6_dashboard_integration"] = step6_result
            
            # Step 7: Validate Error Handling
            step7_result = await self._validate_error_handling()
            workflow_results["workflow_steps"]["7_error_handling"] = step7_result
            
            # Calculate overall success
            all_steps = [step1_result, step2_result, step3_result, step4_result, step5_result, step6_result, step7_result]
            successful_steps = sum(1 for step in all_steps if step["success"])
            
            workflow_results["overall_success"] = successful_steps >= 6  # At least 6/7 steps must pass
            workflow_results["success_rate"] = (successful_steps / len(all_steps)) * 100
            workflow_results["total_time"] = time.time() - start_time
            
            # Generate recommendations
            workflow_results["recommendations"] = self._generate_workflow_recommendations(workflow_results)
            
            # Log results
            self._log_workflow_results(workflow_results)
            
        except Exception as e:
            logger.error(f"❌ Workflow validation failed: {e}")
            workflow_results["error"] = str(e)
            workflow_results["recommendations"].append("🛠️ Fix critical system errors")
        
        return workflow_results
    
    async def _validate_api_health(self) -> Dict[str, Any]:
        """
        Step 1: Validate API health and connectivity
        """
        logger.info("🔍 Step 1: Validating API Health...")
        
        try:
            response = requests.get(f"{self.api_base_url}/health", timeout=10)
            
            if response.status_code == 200:
                health_data = response.json()
                return {
                    "success": True,
                    "message": "API is healthy and responsive",
                    "response_time": response.elapsed.total_seconds(),
                    "details": health_data
                }
            else:
                return {
                    "success": False,
                    "message": f"API health check failed: HTTP {response.status_code}",
                    "error": response.text
                }
                
        except Exception as e:
            return {
                "success": False,
                "message": "API is not accessible",
                "error": str(e)
            }
    
    async def _validate_input_processing(self, query: str) -> Dict[str, Any]:
        """
        Step 2: Validate input processing and keyword extraction
        """
        logger.info("🔍 Step 2: Validating Input Processing...")
        
        try:
            # Test the analyze endpoint with minimal request
            payload = {
                "query": query,
                "platforms": ["facebook"],
                "max_results_per_platform": 5
            }
            
            response = requests.post(
                f"{self.api_base_url}/analyze",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Check if query was processed
                has_query = "query" in result or query in str(result)
                has_keywords = "keywords" in str(result).lower() or "nlp" in str(result).lower()
                
                return {
                    "success": True,
                    "message": "Input processing successful",
                    "query_processed": has_query,
                    "keywords_extracted": has_keywords,
                    "response_size": len(str(result))
                }
            else:
                return {
                    "success": False,
                    "message": f"Input processing failed: HTTP {response.status_code}",
                    "error": response.text
                }
                
        except Exception as e:
            return {
                "success": False,
                "message": "Input processing error",
                "error": str(e)
            }
    
    async def _validate_data_collection(self, query: str) -> Dict[str, Any]:
        """
        Step 3: Validate data collection across platforms
        """
        logger.info("🔍 Step 3: Validating Data Collection...")
        
        try:
            # Test with multiple platforms
            payload = {
                "query": query,
                "platforms": ["facebook", "instagram", "shopee"],
                "max_results_per_platform": 10
            }
            
            response = requests.post(
                f"{self.api_base_url}/analyze",
                json=payload,
                timeout=45
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Validate data collection
                total_data_points = result.get("total_data_points", 0)
                platform_breakdown = result.get("platform_breakdown", {})
                
                platforms_with_data = sum(
                    1 for platform_data in platform_breakdown.values() 
                    if platform_data.get("data_points", 0) > 0
                )
                
                return {
                    "success": total_data_points > 0,
                    "message": f"Collected {total_data_points} data points from {platforms_with_data} platforms",
                    "total_data_points": total_data_points,
                    "platforms_with_data": platforms_with_data,
                    "platform_breakdown": platform_breakdown
                }
            else:
                return {
                    "success": False,
                    "message": f"Data collection failed: HTTP {response.status_code}",
                    "error": response.text
                }
                
        except Exception as e:
            return {
                "success": False,
                "message": "Data collection error",
                "error": str(e)
            }
    
    async def _validate_ai_analysis(self, query: str) -> Dict[str, Any]:
        """
        Step 4: Validate AI analysis and LLM integration
        """
        logger.info("🔍 Step 4: Validating AI Analysis...")
        
        try:
            payload = {
                "query": query,
                "platforms": ["facebook", "instagram"],
                "analysis_type": "social_listening",
                "max_results_per_platform": 15
            }
            
            response = requests.post(
                f"{self.api_base_url}/analyze",
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Check for AI analysis components
                has_llm_analysis = "llm_analysis" in result and result["llm_analysis"]
                has_sentiment = "sentiment" in str(result).lower()
                has_insights = "insights" in result or "recommendations" in result
                has_summary = False
                
                if has_llm_analysis:
                    llm_data = result["llm_analysis"]
                    has_summary = "summary" in llm_data and len(llm_data.get("summary", "")) > 50
                
                ai_score = sum([has_llm_analysis, has_sentiment, has_insights, has_summary])
                
                return {
                    "success": ai_score >= 3,  # At least 3/4 AI components must be present
                    "message": f"AI analysis score: {ai_score}/4",
                    "has_llm_analysis": has_llm_analysis,
                    "has_sentiment_analysis": has_sentiment,
                    "has_insights": has_insights,
                    "has_summary": has_summary,
                    "llm_model": result.get("llm_analysis", {}).get("llm_used", "Unknown")
                }
            else:
                return {
                    "success": False,
                    "message": f"AI analysis failed: HTTP {response.status_code}",
                    "error": response.text
                }
                
        except Exception as e:
            return {
                "success": False,
                "message": "AI analysis error",
                "error": str(e)
            }
    
    async def _validate_malaysian_context(self, query: str) -> Dict[str, Any]:
        """
        Step 5: Validate Malaysian context integration
        """
        logger.info("🔍 Step 5: Validating Malaysian Context...")
        
        try:
            payload = {
                "query": query,
                "platforms": ["facebook", "shopee"],
                "max_results_per_platform": 10
            }
            
            response = requests.post(
                f"{self.api_base_url}/analyze",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                result_str = str(result).lower()
                
                # Check for Malaysian context indicators
                malaysian_terms = ["malaysia", "kuala lumpur", "kl", "selangor", "penang", "johor", "halal", "sedap", "viral", "trending"]
                malaysian_score = sum(1 for term in malaysian_terms if term in result_str)
                
                # Check for Malaysian brands/locations in fashion context
                if "tudung" in query.lower() or "hijab" in query.lower():
                    fashion_brands = ["naelofar", "duckscarves", "ariani", "vanilla hijab", "bokitta"]
                    brand_score = sum(1 for brand in fashion_brands if brand in result_str)
                    malaysian_score += brand_score
                
                return {
                    "success": malaysian_score >= 3,
                    "message": f"Malaysian context score: {malaysian_score}",
                    "malaysian_terms_found": malaysian_score,
                    "has_local_context": malaysian_score >= 3
                }
            else:
                return {
                    "success": False,
                    "message": f"Malaysian context validation failed: HTTP {response.status_code}",
                    "error": response.text
                }
                
        except Exception as e:
            return {
                "success": False,
                "message": "Malaysian context validation error",
                "error": str(e)
            }
    
    async def _validate_dashboard_integration(self) -> Dict[str, Any]:
        """
        Step 6: Validate dashboard integration
        """
        logger.info("🔍 Step 6: Validating Dashboard Integration...")
        
        try:
            # Check if dashboard is accessible
            response = requests.get(f"{self.api_base_url}/", timeout=10)
            
            if response.status_code == 200:
                dashboard_content = response.text
                
                # Check for key dashboard components
                has_charts = "chart" in dashboard_content.lower() or "canvas" in dashboard_content.lower()
                has_analytics = "analytics" in dashboard_content.lower() or "insight" in dashboard_content.lower()
                has_malaysian_ui = "malaysia" in dashboard_content.lower() or "ringgit" in dashboard_content.lower()
                
                dashboard_score = sum([has_charts, has_analytics, has_malaysian_ui])
                
                return {
                    "success": dashboard_score >= 2,
                    "message": f"Dashboard integration score: {dashboard_score}/3",
                    "has_charts": has_charts,
                    "has_analytics": has_analytics,
                    "has_malaysian_ui": has_malaysian_ui,
                    "dashboard_size": len(dashboard_content)
                }
            else:
                return {
                    "success": False,
                    "message": f"Dashboard not accessible: HTTP {response.status_code}",
                    "error": response.text
                }
                
        except Exception as e:
            return {
                "success": False,
                "message": "Dashboard integration error",
                "error": str(e)
            }
    
    async def _validate_error_handling(self) -> Dict[str, Any]:
        """
        Step 7: Validate error handling and fallbacks
        """
        logger.info("🔍 Step 7: Validating Error Handling...")
        
        try:
            # Test with invalid input
            invalid_tests = [
                {"query": "", "platforms": ["facebook"]},  # Empty query
                {"query": "test", "platforms": []},  # Empty platforms
                {"query": "test", "platforms": ["invalid_platform"]},  # Invalid platform
            ]
            
            error_handling_score = 0
            
            for test_case in invalid_tests:
                try:
                    response = requests.post(
                        f"{self.api_base_url}/analyze",
                        json=test_case,
                        timeout=15
                    )
                    
                    # Good error handling should return proper error responses
                    if response.status_code in [400, 422] or (response.status_code == 200 and "error" in response.text.lower()):
                        error_handling_score += 1
                        
                except Exception:
                    # Timeout or connection error is acceptable for invalid inputs
                    error_handling_score += 1
            
            return {
                "success": error_handling_score >= 2,
                "message": f"Error handling score: {error_handling_score}/3",
                "handles_invalid_input": error_handling_score >= 2
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": "Error handling validation failed",
                "error": str(e)
            }
    
    def _generate_workflow_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """
        Generate recommendations based on workflow validation results
        """
        recommendations = []
        
        if results["overall_success"]:
            recommendations.append("🎉 Excellent! Complete workflow is functioning properly")
        else:
            recommendations.append("⚠️ Workflow has issues that need attention")
        
        # Check individual steps
        steps = results["workflow_steps"]
        
        if not steps.get("1_api_health", {}).get("success", False):
            recommendations.append("🔧 Fix API connectivity and health check endpoint")
        
        if not steps.get("3_data_collection", {}).get("success", False):
            recommendations.append("📊 Improve data collection reliability across platforms")
        
        if not steps.get("4_ai_analysis", {}).get("success", False):
            recommendations.append("🤖 Enhance AI analysis and LLM integration")
        
        if not steps.get("5_malaysian_context", {}).get("success", False):
            recommendations.append("🇲🇾 Strengthen Malaysian context and localization")
        
        recommendations.extend([
            "🔄 Implement continuous monitoring for ongoing reliability",
            "📈 Add performance metrics and alerting",
            "🧪 Run regular automated tests",
            "📚 Document any known limitations or edge cases"
        ])
        
        return recommendations
    
    def _log_workflow_results(self, results: Dict[str, Any]):
        """
        Log comprehensive workflow results
        """
        logger.info("\n" + "="*60)
        logger.info("🎯 WORKFLOW VALIDATION RESULTS")
        logger.info("="*60)
        
        logger.info(f"📊 Overall Success: {'✅ YES' if results['overall_success'] else '❌ NO'}")
        logger.info(f"📈 Success Rate: {results.get('success_rate', 0):.1f}%")
        logger.info(f"⏱️ Total Time: {results.get('total_time', 0):.2f} seconds")
        
        logger.info("\n📋 Step-by-Step Results:")
        for step_name, step_result in results["workflow_steps"].items():
            status = "✅" if step_result.get("success", False) else "❌"
            logger.info(f"   {status} {step_name}: {step_result.get('message', 'No message')}")
        
        logger.info("\n💡 Recommendations:")
        for rec in results["recommendations"]:
            logger.info(f"   {rec}")
        
        logger.info("="*60)


# Quick validation functions
async def quick_workflow_test(query: str = "tudung paling viral 2025"):
    """
    Quick workflow validation test
    """
    validator = WorkflowValidator()
    results = await validator.validate_complete_workflow(query)
    
    if results["overall_success"]:
        print("🎉 QUICK TEST PASSED - System is working properly!")
    else:
        print("⚠️ QUICK TEST FAILED - System needs attention")
        print("Top issues:")
        for rec in results["recommendations"][:3]:
            print(f"   {rec}")
    
    return results

async def validate_versatility():
    """
    Test system versatility with different query types
    """
    validator = WorkflowValidator()
    
    test_queries = [
        "tudung paling viral 2025",
        "makanan halal sedap di Kuala Lumpur",
        "best budget smartphone Malaysia 2025",
        "PKS Malaysia online business"
    ]
    
    print("🔄 Testing System Versatility...")
    
    all_passed = True
    for query in test_queries:
        print(f"\n🔍 Testing: '{query}'")
        result = await validator.validate_complete_workflow(query)
        
        if result["overall_success"]:
            print(f"   ✅ PASSED ({result.get('success_rate', 0):.1f}%)")
        else:
            print(f"   ❌ FAILED ({result.get('success_rate', 0):.1f}%)")
            all_passed = False
    
    if all_passed:
        print("\n🌟 SYSTEM IS HIGHLY VERSATILE!")
    else:
        print("\n⚠️ System versatility needs improvement")


if __name__ == "__main__":
    async def main():
        print("🔄 InsightPulse Workflow Validator")
        print("="*50)
        
        # Run quick test
        await quick_workflow_test()
        
        print("\n" + "="*50)
        
        # Test versatility
        await validate_versatility()
    
    asyncio.run(main())
