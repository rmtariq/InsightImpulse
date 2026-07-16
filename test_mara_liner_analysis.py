#!/usr/bin/env python3
"""
Quick test to analyze Mara Liner data
"""
import pandas as pd
from pathlib import Path
from backend.services.csv_cleaner import clean_csv
from backend.services.universal_intelligence_dashboard import UniversalIntelligenceDashboard

# Analyze the CSV
csv_path = "data/combined/Combined_facebook_instagram_linkedin_news_tiktok_x_youtube_20260524_130444.csv"
topic_name = "Mara Liner"

print(f"📊 Analyzing: {csv_path}")
print(f"🎯 Topic: {topic_name}")
print("=" * 60)

# Step 1: Clean
print("\n🧹 STEP 1: Cleaning CSV...")
clean_path, clean_df = clean_csv(csv_path, topic_name, output_dir='data/cleanCSV')
print(f"✅ Clean records: {len(clean_df)}")

# Step 2: Analyze
print("\n📊 STEP 2: Running analysis...")
analyzer = UniversalIntelligenceDashboard(clean_path, topic_name=topic_name)
insights = analyzer.analyze(filter_days=90)

# Print results
print("\n" + "=" * 60)
print("📊 ANALYSIS RESULTS:")
print("=" * 60)

# Overview
overview = insights.get('overview', {})
print(f"\n📈 Overview:")
print(f"  Total records: {overview.get('total_records', 0)}")
print(f"  Relevant records: {overview.get('relevant_records', 0)}")
print(f"  Quality score: {overview.get('quality_score', 0):.1f}%")

# Platform breakdown
platform = insights.get('platform_breakdown', {})
print(f"\n📱 Platform Breakdown:")
for p, count in platform.items():
    print(f"  {p}: {count}")

# Sentiment
sentiment = insights.get('enhanced_analysis', {}).get('sentiment_breakdown', {})
if sentiment and 'percentages' in sentiment:
    print(f"\n😊 Sentiment:")
    for sent, pct in sentiment['percentages'].items():
        print(f"  {sent}: {pct:.1f}%")
else:
    print(f"\n😊 Sentiment: Not available")
    print(f"  enhanced_analysis keys: {list(insights.get('enhanced_analysis', {}).keys())}")

# Check if AI insights exist
ai = insights.get('ai_insights', {})
print(f"\n🤖 AI Insights:")
print(f"  Available: {ai.get('available', False)}")
if ai.get('error'):
    print(f"  Error: {ai.get('error')}")

print("\n" + "=" * 60)
print("✅ Test complete!")
print("=" * 60)
