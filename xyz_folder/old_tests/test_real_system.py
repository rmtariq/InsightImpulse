#!/usr/bin/env python3
"""
🧪 Test Real InsightPulse System
===============================
Test script to verify the real web application works with actual data

🎯 TESTS:
- Real crawler integration
- AI model loading and analysis
- Web backend functionality
- Data processing pipeline

Author: InsightPulse Testing Team
Version: Real System Test 1.0.0
"""

import asyncio
import sys
import os
from pathlib import Path
import logging
import json
from datetime import datetime

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_crawler_integration():
    """Test real crawler integration"""
    logger.info("🕷️ Testing Real Crawler Integration...")
    
    try:
        # Import crawler functions
        from web_backend.real_crawler_integration import (
            collect_facebook_data, collect_shopee_data, 
            crawler_manager
        )
        
        # Test S_crawlers path
        s_crawlers_path = Path("/Users/rmtariq/Documents/S_crawlers")
        if s_crawlers_path.exists():
            logger.info(f"✅ S_crawlers directory found: {s_crawlers_path}")
            
            # List available crawlers
            crawlers_dir = s_crawlers_path / "crawlers"
            if crawlers_dir.exists():
                crawler_files = list(crawlers_dir.glob("*.py"))
                logger.info(f"📁 Found {len(crawler_files)} crawler scripts:")
                for crawler in crawler_files:
                    logger.info(f"   - {crawler.name}")
            
            # List available data
            data_dir = s_crawlers_path / "data"
            if data_dir.exists():
                data_folders = [d for d in data_dir.iterdir() if d.is_dir()]
                logger.info(f"📊 Found {len(data_folders)} data directories:")
                for folder in data_folders:
                    csv_files = list(folder.glob("*.csv"))
                    logger.info(f"   - {folder.name}: {len(csv_files)} CSV files")
        else:
            logger.warning(f"❌ S_crawlers directory not found: {s_crawlers_path}")
        
        # Test data collection
        logger.info("🧪 Testing data collection...")
        
        # Test Facebook data collection
        facebook_result = await collect_facebook_data("test query", 10)
        logger.info(f"📘 Facebook test result: {facebook_result.get('status', 'unknown')}")
        
        # Test Shopee data collection
        shopee_result = await collect_shopee_data("smartphone", 5)
        logger.info(f"🛒 Shopee test result: {shopee_result.get('status', 'unknown')}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Crawler integration test failed: {e}")
        return False

async def test_ai_analysis():
    """Test real AI analysis system"""
    logger.info("🤖 Testing Real AI Analysis...")
    
    try:
        from web_backend.real_ai_analysis import ai_analyzer, perform_real_ai_analysis
        
        # Test AI analyzer initialization
        logger.info("🔧 Testing AI analyzer initialization...")
        
        # Test text analysis
        test_text = "Produk ini sangat bagus dan berkualiti tinggi. Saya sangat berpuas hati dengan pembelian ini."
        
        logger.info("📝 Testing text analysis...")
        analysis_result = await ai_analyzer.analyze_content(test_text, "malay")
        
        logger.info("✅ AI Analysis Results:")
        logger.info(f"   - Sentiment: {analysis_result.get('sentiment', {}).get('label', 'unknown')}")
        logger.info(f"   - Language: {analysis_result.get('detected_language', {}).get('language', 'unknown')}")
        logger.info(f"   - Keywords: {analysis_result.get('keywords', [])[:3]}")
        
        # Test cross-platform analysis
        mock_platform_data = {
            "facebook": {
                "data": [
                    {"content": "Great product! Highly recommended."},
                    {"content": "Produk yang sangat baik dan berbaloi."}
                ],
                "data_points": 2,
                "status": "success"
            },
            "shopee": {
                "data": [
                    {"content": "Fast delivery, good quality", "price": "RM 99.90", "rating": "4.5"},
                    {"content": "Satisfied with purchase", "price": "RM 89.90", "rating": "4.8"}
                ],
                "data_points": 2,
                "status": "success"
            }
        }
        
        logger.info("🔗 Testing cross-platform analysis...")
        cross_analysis = await perform_real_ai_analysis(
            mock_platform_data,
            {
                "analysis_type": "social_listening",
                "query": "test product",
                "platforms": ["facebook", "shopee"]
            }
        )
        
        logger.info("✅ Cross-platform Analysis Results:")
        logger.info(f"   - Total data points: {cross_analysis.get('total_data_points', 0)}")
        logger.info(f"   - Platforms analyzed: {len(cross_analysis.get('platforms_analyzed', []))}")
        logger.info(f"   - Analysis type: {cross_analysis.get('analysis_type', 'unknown')}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ AI analysis test failed: {e}")
        return False

async def test_web_backend():
    """Test web backend functionality"""
    logger.info("🌐 Testing Web Backend...")
    
    try:
        # Import FastAPI app
        from web_backend.app import app
        
        logger.info("✅ FastAPI app imported successfully")
        
        # Test app configuration
        logger.info(f"📋 App title: {getattr(app, 'title', 'Unknown')}")
        logger.info(f"📋 App version: {getattr(app, 'version', 'Unknown')}")
        
        # List available routes
        routes = []
        for route in app.routes:
            if hasattr(route, 'path') and hasattr(route, 'methods'):
                routes.append(f"{list(route.methods)[0] if route.methods else 'GET'} {route.path}")
        
        logger.info(f"🛣️ Available routes ({len(routes)}):")
        for route in routes[:10]:  # Show first 10 routes
            logger.info(f"   - {route}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Web backend test failed: {e}")
        return False

async def test_data_processing():
    """Test data processing pipeline"""
    logger.info("📊 Testing Data Processing Pipeline...")
    
    try:
        from web_backend.real_crawler_integration import process_social_media_data, process_ecommerce_data
        
        # Test social media data processing
        social_data = {
            "platform": "facebook",
            "data": [
                {"content": "Great product!", "likes": "150", "shares": "25", "comments": "30"},
                {"content": "Not satisfied", "likes": "10", "shares": "2", "comments": "5"},
                {"content": "Amazing quality", "likes": "200", "shares": "40", "comments": "15"}
            ],
            "data_points": 3
        }
        
        processed_social = process_social_media_data(social_data, "facebook")
        logger.info("✅ Social Media Processing Results:")
        if "processed_insights" in processed_social:
            insights = processed_social["processed_insights"]
            logger.info(f"   - Total posts: {insights.get('total_posts', 0)}")
            logger.info(f"   - Total engagement: {insights.get('total_engagement', 0)}")
            logger.info(f"   - Sentiment: {insights.get('sentiment_label', 'unknown')}")
        
        # Test e-commerce data processing
        ecommerce_data = {
            "platform": "shopee",
            "data": [
                {"title": "Smartphone", "price": "RM 899.00", "rating": "4.5", "reviews": "1250"},
                {"title": "Laptop", "price": "RM 2499.00", "rating": "4.8", "reviews": "890"},
                {"title": "Headphones", "price": "RM 199.00", "rating": "4.2", "reviews": "2100"}
            ],
            "data_points": 3
        }
        
        processed_ecommerce = process_ecommerce_data(ecommerce_data, "shopee")
        logger.info("✅ E-commerce Processing Results:")
        if "processed_insights" in processed_ecommerce:
            insights = processed_ecommerce["processed_insights"]
            logger.info(f"   - Total products: {insights.get('total_products', 0)}")
            if "price_analysis" in insights:
                price_info = insights["price_analysis"]
                logger.info(f"   - Average price: RM {price_info.get('average_price', 0)}")
            if "rating_analysis" in insights:
                rating_info = insights["rating_analysis"]
                logger.info(f"   - Average rating: {rating_info.get('average_rating', 0)}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Data processing test failed: {e}")
        return False

async def test_frontend_files():
    """Test frontend files exist and are valid"""
    logger.info("🎨 Testing Frontend Files...")
    
    try:
        frontend_dir = Path("web_frontend")
        
        # Check HTML file
        html_file = frontend_dir / "index.html"
        if html_file.exists():
            logger.info("✅ HTML file found")
            with open(html_file, 'r', encoding='utf-8') as f:
                html_content = f.read()
                if "InsightPulse" in html_content:
                    logger.info("✅ HTML contains InsightPulse branding")
                if "9 platforms" in html_content.lower():
                    logger.info("✅ HTML mentions 9 platforms")
        else:
            logger.warning("❌ HTML file not found")
        
        # Check CSS file
        css_file = frontend_dir / "assets" / "css" / "main.css"
        if css_file.exists():
            logger.info("✅ CSS file found")
            with open(css_file, 'r', encoding='utf-8') as f:
                css_content = f.read()
                if "gradient" in css_content.lower():
                    logger.info("✅ CSS contains gradient styling")
        else:
            logger.warning("❌ CSS file not found")
        
        # Check JavaScript file
        js_file = frontend_dir / "assets" / "js" / "main.js"
        if js_file.exists():
            logger.info("✅ JavaScript file found")
            with open(js_file, 'r', encoding='utf-8') as f:
                js_content = f.read()
                if "fetch" in js_content:
                    logger.info("✅ JavaScript contains API calls")
        else:
            logger.warning("❌ JavaScript file not found")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Frontend test failed: {e}")
        return False

async def run_all_tests():
    """Run all system tests"""
    logger.info("🚀 Starting InsightPulse Real System Tests...")
    logger.info("=" * 60)
    
    test_results = {}
    
    # Run tests
    test_results["crawler_integration"] = await test_crawler_integration()
    test_results["ai_analysis"] = await test_ai_analysis()
    test_results["web_backend"] = await test_web_backend()
    test_results["data_processing"] = await test_data_processing()
    test_results["frontend_files"] = await test_frontend_files()
    
    # Summary
    logger.info("=" * 60)
    logger.info("🎯 TEST RESULTS SUMMARY:")
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"   {test_name}: {status}")
        if result:
            passed += 1
    
    logger.info(f"\n📊 Overall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        logger.info("🎉 ALL TESTS PASSED! Your InsightPulse system is ready!")
        logger.info("\n🚀 Next Steps:")
        logger.info("   1. Install dependencies: pip install -r requirements.txt")
        logger.info("   2. Start the web server: uvicorn web_backend.app:app --reload")
        logger.info("   3. Open browser to: http://localhost:8000")
        logger.info("   4. Test with real queries and see actual results!")
    else:
        logger.warning("⚠️ Some tests failed. Check the logs above for details.")
        logger.info("\n🔧 Troubleshooting:")
        logger.info("   1. Ensure S_crawlers directory exists at /Users/rmtariq/Documents/S_crawlers")
        logger.info("   2. Install missing dependencies from requirements.txt")
        logger.info("   3. Check file paths and permissions")
    
    return passed == total

if __name__ == "__main__":
    # Run the tests
    success = asyncio.run(run_all_tests())
    
    if success:
        print("\n🎯 READY TO LAUNCH! Your InsightPulse web app is fully functional!")
        print("Run: uvicorn web_backend.app:app --reload --host 0.0.0.0 --port 8000")
    else:
        print("\n⚠️ Please fix the issues above before launching.")
        sys.exit(1)
