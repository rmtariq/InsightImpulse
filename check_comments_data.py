import pandas as pd
from pathlib import Path
import json

print("=" * 80)
print("INVESTIGATING RAW CRAWLED DATA FOR COMMENTS")
print("=" * 80)

# Check Instagram raw data
ig_files = sorted(Path('data/smart_crawlers/instagram').glob('*.csv'), key=lambda p: p.stat().st_mtime, reverse=True)
if ig_files:
    print(f"\n📸 INSTAGRAM: {ig_files[0].name}")
    ig_df = pd.read_csv(ig_files[0])
    print(f"   Rows: {len(ig_df)}, Cols: {len(ig_df.columns)}")
    print(f"   Columns: {list(ig_df.columns)}")
    print(f"   Has 'comments' field? {'comments' in ig_df.columns}")
    if 'URL' in ig_df.columns:
        print(f"   Sample URL: {ig_df['URL'].iloc[0]}")
    
    # Check first row all columns
    print(f"\n   First row all data:")
    for col in ig_df.columns[:10]:
        val = ig_df[col].iloc[0]
        if isinstance(val, str) and len(str(val)) > 100:
            print(f"      {col}: {str(val)[:100]}...")
        else:
            print(f"      {col}: {val}")

# Check YouTube raw data
yt_files = sorted(Path('data/smart_crawlers/youtube').glob('*.csv'), key=lambda p: p.stat().st_mtime, reverse=True)
if yt_files:
    print(f"\n🎬 YOUTUBE: {yt_files[0].name}")
    yt_df = pd.read_csv(yt_files[0])
    print(f"   Rows: {len(yt_df)}, Cols: {len(yt_df.columns)}")
    print(f"   Columns: {list(yt_df.columns)}")
    print(f"   Has 'comments' field? {'comments' in yt_df.columns}")
    if 'URL' in yt_df.columns:
        print(f"   Sample URL: {yt_df['URL'].iloc[0]}")
    
    # Check first row all columns
    print(f"\n   First row all data:")
    for col in yt_df.columns[:10]:
        val = yt_df[col].iloc[0]
        if isinstance(val, str) and len(str(val)) > 100:
            print(f"      {col}: {str(val)[:100]}...")
        else:
            print(f"      {col}: {val}")
