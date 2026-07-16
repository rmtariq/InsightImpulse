#!/usr/bin/env python3
import pandas as pd
import sys

csv_file = 'data/combined/Combined_facebook_instagram_threads_tiktok_x_20260528_171241.csv'

try:
    df = pd.read_csv(csv_file)
    
    print("=" * 80)
    print("📊 DATA BREAKDOWN - PAS/BERSATU ANALYSIS")
    print("=" * 80)
    
    print(f"\n📈 TOTAL RECORDS: {len(df):,}")
    
    print("\n🔢 Records per Platform:")
    platform_counts = df['Platform'].value_counts()
    for platform, count in platform_counts.items():
        percentage = (count / len(df)) * 100
        print(f"  {platform:15} : {count:5,} records ({percentage:5.1f}%)")
    
    print("\n" + "=" * 80)
    
    # Check which platforms have very little data
    print("\n⚠️  PLATFORMS WITH LESS THAN 500 RECORDS:")
    has_low_data = False
    for platform, count in platform_counts.items():
        if count < 500:
            print(f"  ❌ {platform}: only {count:,} records (VERY LOW!)")
            has_low_data = True
    if not has_low_data:
        print("  ✅ All platforms have 500+ records")
    
    # Check if Threads exists
    print("\n🧵 THREADS DATA CHECK:")
    if 'Threads' in platform_counts.index or 'threads' in platform_counts.index:
        threads_count = platform_counts.get('Threads', 0) + platform_counts.get('threads', 0)
        if threads_count > 0:
            print(f"  ✅ Threads: {threads_count:,} records found")
        else:
            print(f"  ❌ Threads: 0 records")
    else:
        print(f"  ❌ Threads: NOT IN DATASET (crawler failed or no results)")
    
    print("\n" + "=" * 80)
    print("✅ Analysis complete!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
