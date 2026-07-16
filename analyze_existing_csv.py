#!/usr/bin/env python3
"""
Analyze Existing CSV Files
Run Universal Intelligence Analysis on previously collected data
No need to re-crawl - just analyze what you already have!
"""

import sys
from pathlib import Path
from backend.services.universal_intelligence_dashboard import UniversalIntelligenceDashboard

def main():
    print("\n" + "="*80)
    print("📊 UNIVERSAL INTELLIGENCE ANALYSIS - Existing CSV")
    print("="*80)
    
    # Check if CSV path provided
    if len(sys.argv) < 2:
        print("\n❌ Error: Please provide a CSV file path")
        print("\nUsage:")
        print("  python analyze_existing_csv.py <path_to_csv> [topic_name] [days_filter]")
        print("\nExample:")
        print("  python analyze_existing_csv.py data/combined/Combined_facebook_instagram_tiktok_x_20260524_004112.csv 'Mara Liner' 90")
        print("\nOr simply:")
        print("  python analyze_existing_csv.py data/combined/your_file.csv")
        sys.exit(1)
    
    csv_path = sys.argv[1]
    
    # Auto-detect topic name from filename if not provided
    if len(sys.argv) >= 3:
        topic_name = sys.argv[2]
    else:
        # Try to extract topic from filename
        # Example: Combined_facebook_instagram_tiktok_x_20260524_004112.csv
        filename = Path(csv_path).stem
        if 'Combined' in filename:
            # Extract brand name from combined filename or ask user
            topic_name = input("\n💡 Enter the brand/topic name to analyze: ")
        else:
            topic_name = filename.replace('_', ' ').replace('Combined', '').strip()
    
    # Filter days (default 90)
    filter_days = int(sys.argv[3]) if len(sys.argv) >= 4 else 90
    
    # Check if file exists
    if not Path(csv_path).exists():
        print(f"\n❌ Error: File not found: {csv_path}")
        sys.exit(1)
    
    print(f"\n📁 CSV File: {csv_path}")
    print(f"🎯 Topic: {topic_name}")
    print(f"📅 Filter: Last {filter_days} days")
    print(f"📂 Output: reports/universal_analysis_{topic_name.replace(' ', '_')}/")
    print("="*80 + "\n")
    
    # Run analysis
    try:
        analyzer = UniversalIntelligenceDashboard(csv_path, topic_name=topic_name)
        insights = analyzer.analyze(filter_days=filter_days)
        
        # Print summary
        print("\n")
        analyzer.print_summary()
        
        # Export results
        output_dir = Path(f"reports/universal_analysis_{topic_name.replace(' ', '_')}")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        print("\n" + "="*80)
        print("📤 EXPORTING RESULTS")
        print("="*80)
        
        analyzer.export_to_json(str(output_dir / "insights.json"))
        analyzer.export_cleaned_data(str(output_dir / "cleaned_data.csv"))
        
        print("\n" + "="*80)
        print("✅ ANALYSIS COMPLETE!")
        print("="*80)
        print(f"\n📁 Results saved to: {output_dir}")
        print("\n📄 Files generated:")
        print(f"  1. {output_dir}/insights.json - Complete analysis in JSON format")
        print(f"  2. {output_dir}/cleaned_data.csv - Cleaned, classified dataset")
        print("\n💡 Next steps:")
        print(f"  • Review insights.json for executive summary")
        print(f"  • Use cleaned_data.csv for custom analysis in Excel/Tableau")
        print(f"  • Share findings with stakeholders")
        print("="*80 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error during analysis: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
