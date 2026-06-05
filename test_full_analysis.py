#!/usr/bin/env python3
"""
Full end-to-end test with all 10 platforms
Tests the complete flow: Query → Crawling → Analysis → Insights
"""
import requests
import json
import time

# Test configuration
API_URL = "http://localhost:8001"
TEST_QUERY = "PKS Malaysia online business"
ANALYSIS_TYPE = "sme_insights"
USER_ROLE = "sme_owner"

# All 10 platforms
PLATFORMS = [
    'facebook', 'instagram', 'twitter', 'tiktok',
    'youtube', 'google', 'news', 'linkedin',
    'shopee', 'lazada'
]

def test_full_analysis():
    """Test complete analysis with all 10 platforms"""
    
    print("="*80)
    print("🧪 FULL END-TO-END ANALYSIS TEST")
    print("="*80)
    print(f"📝 Query: {TEST_QUERY}")
    print(f"🎯 Analysis Type: {ANALYSIS_TYPE}")
    print(f"👤 User Role: {USER_ROLE}")
    print(f"🌐 Platforms: {len(PLATFORMS)}")
    print("="*80)
    print()
    
    # Prepare request
    payload = {
        "query": TEST_QUERY,
        "analysis_type": ANALYSIS_TYPE,
        "user_role": USER_ROLE,
        "platforms": PLATFORMS,
        "max_results_per_platform": 10
    }
    
    print("📤 Sending analysis request...")
    print(f"   Endpoint: {API_URL}/analyze")
    print(f"   Payload: {json.dumps(payload, indent=2)}")
    print()
    
    # Send request
    start_time = time.time()
    
    try:
        response = requests.post(
            f"{API_URL}/analyze",
            json=payload,
            timeout=600  # 10 minutes timeout
        )
        
        elapsed_time = time.time() - start_time
        
        print(f"⏱️  Response Time: {elapsed_time:.2f} seconds")
        print(f"📊 Status Code: {response.status_code}")
        print()
        
        if response.status_code == 200:
            data = response.json()
            
            # Print summary
            print("="*80)
            print("✅ ANALYSIS SUCCESSFUL!")
            print("="*80)
            print()
            
            # Data collection summary
            if 'data_collection' in data:
                dc = data['data_collection']
                print("📊 DATA COLLECTION SUMMARY:")
                print(f"   Total Records: {dc.get('total_records', 0)}")
                print(f"   Platforms Used: {len(dc.get('platforms_used', []))}")
                print(f"   Time Range: {dc.get('time_range', 'N/A')}")
                print()
                
                # Platform breakdown
                if 'platform_breakdown' in dc:
                    print("   Platform Breakdown:")
                    for platform, count in dc['platform_breakdown'].items():
                        print(f"      {platform:15} {count:4} records")
                    print()
            
            # Sentiment analysis
            if 'sentiment_analysis' in data:
                sa = data['sentiment_analysis']
                print("😊 SENTIMENT ANALYSIS:")
                print(f"   Overall: {sa.get('overall_sentiment', 'N/A')}")
                if 'distribution' in sa:
                    dist = sa['distribution']
                    print(f"   Positive: {dist.get('positive', 0):.1f}%")
                    print(f"   Neutral:  {dist.get('neutral', 0):.1f}%")
                    print(f"   Negative: {dist.get('negative', 0):.1f}%")
                print()
            
            # Key insights
            if 'key_insights' in data:
                insights = data['key_insights']
                print("💡 KEY INSIGHTS:")
                for i, insight in enumerate(insights[:5], 1):
                    print(f"   {i}. {insight}")
                print()
            
            # Recommendations
            if 'recommendations' in data:
                recs = data['recommendations']
                print("🎯 RECOMMENDATIONS:")
                for i, rec in enumerate(recs[:5], 1):
                    print(f"   {i}. {rec}")
                print()
            
            # Save full response
            with open('test_full_analysis_response.json', 'w') as f:
                json.dump(data, f, indent=2)
            print("💾 Full response saved to: test_full_analysis_response.json")
            print()
            
            print("="*80)
            print("🎉 TEST COMPLETED SUCCESSFULLY!")
            print("="*80)
            
            return True
            
        else:
            print(f"❌ ERROR: {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return False
            
    except Exception as e:
        print(f"❌ EXCEPTION: {e}")
        return False


if __name__ == "__main__":
    success = test_full_analysis()
    exit(0 if success else 1)

