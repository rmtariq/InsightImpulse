#!/usr/bin/env python3
"""
Test individual platform crawlers one by one
"""
import sys
import asyncio
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.data_crawlers.simple_apify_adapter import SimpleApifyAdapter

async def test_platform(platform_name, query, target_size=100):
    """Test a single platform crawler"""
    
    print("=" * 80)
    print(f"🧪 TESTING: {platform_name.upper()}")
    print("=" * 80)
    print(f"Query: {query}")
    print(f"Target: {target_size} results")
    print()
    
    try:
        # Initialize adapter
        adapter = SimpleApifyAdapter()
        
        # Crawl the platform using the unified method
        print(f"🚀 Starting {platform_name} crawler...")

        results = await adapter.crawl_platform(
            platform=platform_name,
            query=query,
            max_results=target_size
        )
        
        # Check results
        if results and 'data' in results:
            data = results['data']
            print(f"\n✅ SUCCESS!")
            print(f"📊 Results: {len(data)} records")
            
            # Show sample
            if len(data) > 0:
                print(f"\n📝 Sample (first 3 records):")
                for i, item in enumerate(data[:3]):
                    text = item.get('Text', '')[:100]
                    print(f"  {i+1}. {text}...")
            
            return {
                'platform': platform_name,
                'success': True,
                'count': len(data),
                'data': data
            }
        else:
            print(f"\n❌ FAILED: No data returned")
            print(f"Response: {results}")
            return {
                'platform': platform_name,
                'success': False,
                'count': 0,
                'error': 'No data in response'
            }
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return {
            'platform': platform_name,
            'success': False,
            'count': 0,
            'error': str(e)
        }

async def main():
    # Your query
    query = '''("PAS" OR "Parti Islam Se-Malaysia" OR "Perikatan Nasional" OR "PN" OR hajihadi OR tuanguru OR "tuan guru" OR presidenpas OR "presiden pas")
AND
("Bersatu" OR "PPBM" OR "Muhyiddin" OR "parti sekutu" OR "komponen PN")'''
    
    # Platforms to test (Instagram excluded as it works)
    platforms = ["threads", "facebook", "tiktok", "x"]
    
    # Test each platform with small dataset first (100 results)
    results = []
    
    for platform in platforms:
        print("\n")
        result = await test_platform(platform, query, target_size=100)
        results.append(result)
        
        # Wait between tests to avoid rate limits
        if platform != platforms[-1]:
            print("\n⏳ Waiting 10 seconds before next test...")
            await asyncio.sleep(10)
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 FINAL SUMMARY")
    print("=" * 80)
    
    for result in results:
        platform = result['platform']
        if result['success']:
            print(f"✅ {platform:10} : {result['count']:4} records")
        else:
            print(f"❌ {platform:10} : FAILED - {result.get('error', 'Unknown error')}")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    asyncio.run(main())
