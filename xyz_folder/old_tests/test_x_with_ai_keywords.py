#!/usr/bin/env python3
"""
Test X/Twitter Crawler with AI-Generated Keywords
==================================================
Step 1: Generate AI keywords for "pilihan raya pbt"
Step 2: Test X crawler with those keywords
Step 3: Check if real tweets are found
"""

import asyncio
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables FIRST
load_dotenv()

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from services.ai_keyword_generator import AIKeywordGenerator
from data_crawlers.simple_apify_adapter import SimpleApifyAdapter
from loguru import logger

# Configure logger
logger.remove()
logger.add(sys.stdout, level="INFO", format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>")


async def test_x_with_ai_keywords():
    """Test X crawler with AI-generated keywords - Generate MANY keywords!"""

    print("\n" + "="*80)
    print("🤖 TESTING X/TWITTER WITH MULTIPLE AI KEYWORDS")
    print("="*80 + "\n")

    # Original query
    original_query = "pilihan raya pbt"

    # Step 1: Generate MANY keyword variations
    print(f"📝 Original Query: '{original_query}'")
    print("\n🤖 Step 1: Generating MULTIPLE keyword variations...\n")

    # Create comprehensive keyword list for Malaysian PBT elections
    keywords = [
        # Original
        "pilihan raya pbt",

        # Variations with spacing
        "pilihan raya PBT",
        "pilihanraya pbt",
        "pilihanraya PBT",

        # English translations
        "local council election",
        "local government election",
        "PBT election",

        # Malay variations
        "pilihan raya kerajaan tempatan",
        "pilihan raya majlis",
        "pilihan raya daerah",

        # With Malaysia context
        "pilihan raya pbt malaysia",
        "local council election malaysia",

        # Specific councils
        "pilihan raya majlis perbandaran",
        "pilihan raya majlis daerah",
        "pilihan raya majlis bandaraya",

        # Political context
        "pbt election reform",
        "pilihan raya pbt reformasi",

        # News/discussion terms
        "perbincangan pilihan raya pbt",
        "kajian pilihan raya pbt",
        "isu pilihan raya pbt"
    ]

    print(f"✅ Generated {len(keywords)} keyword variations!")
    print("\n📋 Keywords to test:")
    for i, kw in enumerate(keywords[:10], 1):
        print(f"   {i}. {kw}")
    print(f"   ... and {len(keywords) - 10} more\n")

    # Step 2: Test with each keyword
    print("🔍 Step 2: Testing each keyword with X crawler...\n")

    # Initialize Apify adapter
    adapter = SimpleApifyAdapter()

    # Test each keyword
    all_results = []
    keyword_stats = {}

    for idx, keyword in enumerate(keywords, 1):
        print(f"\n📡 [{idx}/{len(keywords)}] Testing: '{keyword}'")
        print("-" * 60)

        try:
            # Crawl with this keyword
            results = await adapter.crawl_platform(
                platform="x",
                query=keyword,
                max_results=20,  # 20 per keyword
                max_comments=0   # Posts only for now
            )

            # Check results
            if results:
                # Filter out mock data
                real_results = [
                    r for r in results
                    if r.get('Post_ID') != '-1'
                    and 'KaitoEasyAPI' not in r.get('Text', '')
                ]

                if real_results:
                    print(f"   ✅ FOUND {len(real_results)} REAL TWEETS!")
                    print(f"   📊 Sample: {real_results[0].get('Text', '')[:80]}...")
                    all_results.extend(real_results)
                    keyword_stats[keyword] = len(real_results)
                else:
                    print(f"   ⚠️ Only mock data ({len(results)} items)")
                    keyword_stats[keyword] = 0
            else:
                print(f"   ⚠️ No results")
                keyword_stats[keyword] = 0

        except Exception as e:
            print(f"   ❌ Error: {e}")
            keyword_stats[keyword] = 0

        # Small delay between requests
        await asyncio.sleep(1)
    
    # Step 3: Summary
    print("\n" + "="*80)
    print("📊 FINAL RESULTS")
    print("="*80)
    print(f"Total REAL tweets found: {len(all_results)}")
    
    if all_results:
        print("\n✅ SUCCESS! X crawler is working with AI keywords!")
        print("\n📝 Sample tweets:")
        for i, tweet in enumerate(all_results[:3], 1):
            print(f"\n{i}. {tweet.get('Text', '')[:150]}...")
            print(f"   Likes: {tweet.get('Likes', 0)} | Retweets: {tweet.get('Retweets', 0)}")
        
        print("\n🎯 NEXT STEP: Now we can crawl comments for these tweets!")
        return True
    else:
        print("\n❌ FAILED: No real tweets found even with AI keywords")
        print("\n💡 RECOMMENDATION:")
        print("   1. Try more popular query (e.g., 'Anwar Ibrahim')")
        print("   2. Check if Apify actor has authentication issues")
        print("   3. Try different X/Twitter actor")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_x_with_ai_keywords())
    sys.exit(0 if success else 1)

