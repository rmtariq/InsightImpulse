#!/usr/bin/env python3
"""
Test Universal Intelligence Dashboard
Run this to analyze ANY brand/topic data
"""

from backend.services.universal_intelligence_dashboard import UniversalIntelligenceDashboard
from pathlib import Path

def main():
    # Configuration
    csv_file = "data/combined/Combined_facebook_instagram_tiktok_x_20260524_004112.csv"
    topic_name = "Mara Liner"
    filter_recent_days = 90  # Only analyze last 90 days
    
    # Output paths
    output_dir = Path(f"reports/universal_analysis_{topic_name.replace(' ', '_')}")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("\n" + "="*80)
    print("🚀 UNIVERSAL INTELLIGENCE DASHBOARD")
    print("="*80)
    print(f"Topic: {topic_name}")
    print(f"Data Source: {csv_file}")
    print(f"Time Filter: Last {filter_recent_days} days")
    print(f"Output: {output_dir}")
    print("="*80 + "\n")
    
    # Run analysis
    analyzer = UniversalIntelligenceDashboard(csv_file, topic_name=topic_name)
    insights = analyzer.analyze(filter_days=filter_recent_days)
    
    # Print summary
    analyzer.print_summary()
    
    # Export results
    print("\n" + "="*80)
    print("📤 EXPORTING RESULTS")
    print("="*80)
    
    analyzer.export_to_json(str(output_dir / "insights.json"))
    analyzer.export_cleaned_data(str(output_dir / "cleaned_data.csv"))
    
    print("\n" + "="*80)
    print("✅ ANALYSIS COMPLETE!")
    print("="*80)
    print(f"\nResults saved to: {output_dir}")
    print("\nFiles generated:")
    print(f"  1. insights.json - Complete analysis in JSON format")
    print(f"  2. cleaned_data.csv - Cleaned, classified dataset")
    print("\nNext steps:")
    print(f"  • Review insights.json for executive summary")
    print(f"  • Use cleaned_data.csv for custom analysis in Excel/Tableau")
    print(f"  • Share findings with stakeholders")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()
