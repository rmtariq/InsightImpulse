#!/usr/bin/env python3
"""
Clean CSV and Run Deep Analysis
Step 1: Clean the CSV file (remove duplicates, spam, bots, irrelevant content)
Step 2: Analyze the cleaned data for best insights
"""

import sys
from pathlib import Path
from backend.services.csv_cleaner import clean_csv
from backend.services.universal_intelligence_dashboard import UniversalIntelligenceDashboard

def main():
    print("\n" + "="*80)
    print("🚀 CLEAN & ANALYZE PIPELINE")
    print("="*80)
    
    # Get parameters
    if len(sys.argv) < 3:
        print("\n❌ Error: Missing parameters")
        print("\nUsage:")
        print("  python clean_and_analyze.py <csv_file> <topic_name> [days_filter]")
        print("\nExample:")
        print("  python clean_and_analyze.py data/combined/Combined_facebook_instagram_tiktok_x_20260524_004112.csv 'Mara Liner' 90")
        sys.exit(1)
    
    csv_path = sys.argv[1]
    topic_name = sys.argv[2]
    filter_days = int(sys.argv[3]) if len(sys.argv) >= 4 else 90
    
    # Validate file exists
    if not Path(csv_path).exists():
        print(f"\n❌ Error: File not found: {csv_path}")
        sys.exit(1)
    
    print(f"\n📊 Input File: {csv_path}")
    print(f"🎯 Topic: {topic_name}")
    print(f"📅 Filter: Last {filter_days} days")
    print("\n" + "="*80)
    
    # PHASE 1: CLEAN THE DATA
    print("\n🧹 PHASE 1: DEEP CLEANING")
    print("="*80)
    
    clean_path, clean_df = clean_csv(csv_path, topic_name, output_dir='data/cleanCSV')
    
    print(f"\n✅ Cleaned CSV saved to: {clean_path}")
    print(f"📊 Clean records: {len(clean_df)}")
    
    # PHASE 2: ANALYZE CLEANED DATA
    print("\n" + "="*80)
    print("📊 PHASE 2: INTELLIGENCE ANALYSIS")
    print("="*80)
    
    print(f"\n🔍 Analyzing cleaned data for: {topic_name}")
    
    analyzer = UniversalIntelligenceDashboard(clean_path, topic_name=topic_name)
    insights = analyzer.analyze(filter_days=filter_days)
    
    print("\n")
    analyzer.print_summary()
    
    # PHASE 3: EXPORT RESULTS
    print("\n" + "="*80)
    print("💾 PHASE 3: EXPORTING RESULTS")
    print("="*80)
    
    output_dir = Path(f"reports/clean_analysis_{topic_name.replace(' ', '_')}")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    analyzer.export_to_json(str(output_dir / "insights.json"))
    analyzer.export_cleaned_data(str(output_dir / "analyzed_data.csv"))
    
    print(f"\n✅ Results saved to: {output_dir}")
    print(f"\n📄 Files generated:")
    print(f"  1. {output_dir}/insights.json - Complete analysis")
    print(f"  2. {output_dir}/analyzed_data.csv - Analyzed dataset")
    print(f"  3. {clean_path} - Cleaned source data")
    
    # SUMMARY
    print("\n" + "="*80)
    print("✅ PIPELINE COMPLETE!")
    print("="*80)
    
    print(f"\n📊 Data Quality Journey:")
    print(f"  1. Original data: {csv_path}")
    print(f"  2. Cleaned data: {clean_path} ({len(clean_df)} records)")
    print(f"  3. Analysis results: {output_dir}")
    
    print(f"\n🎯 Key Insights:")
    if insights and 'business_priorities' in insights:
        priorities = insights['business_priorities']
        if priorities:
            print(f"  • Found {len(priorities)} business priority areas")
            for i, priority in enumerate(priorities[:3], 1):
                print(f"  {i}. {priority.get('category', 'Unknown')}: {priority.get('volume', 0)} mentions")
        else:
            print(f"  • No critical priorities detected (good news!)")
    
    print("\n💡 Next Steps:")
    print(f"  1. Review insights.json for executive summary")
    print(f"  2. Open analyzed_data.csv in Excel for detailed analysis")
    print(f"  3. Share {output_dir} with stakeholders")
    
    print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    main()
