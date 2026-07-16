#!/usr/bin/env python3
"""
Quick script to create combined CSV from analyzed data
"""

import pandas as pd
from pathlib import Path
from datetime import datetime

print("🔄 Creating combined KDEBWM data file...")

# Find the 3 analyzed files from tonight
analyzed_dir = Path("data/analyzed")
files = [
    "Sentiment_Emotion_INSTAGRAM_20260524_232434.csv",
    "Sentiment_Emotion_X_20260524_232435.csv", 
    "Sentiment_Emotion_TIKTOK_20260524_232443.csv"
]

all_data = []

for filename in files:
    filepath = analyzed_dir / filename
    if filepath.exists():
        print(f"✅ Reading: {filename}")
        df = pd.read_csv(filepath)
        print(f"   {len(df)} records")
        all_data.append(df)
    else:
        print(f"⚠️  Not found: {filename}")

if all_data:
    # Combine all dataframes
    combined_df = pd.concat(all_data, ignore_index=True)
    
    # Create output file
    combined_dir = Path("data/combined")
    combined_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = combined_dir / f"Combined_instagram_x_tiktok_{timestamp}.csv"
    
    combined_df.to_csv(output_file, index=False, encoding='utf-8')
    
    print(f"\n✅ COMBINED FILE CREATED!")
    print(f"📁 Location: {output_file}")
    print(f"📊 Total records: {len(combined_df):,}")
    print(f"📊 Platforms: {combined_df['Platform'].unique().tolist()}")
    print(f"\n🎯 You can now use this file in the KDEBWM dashboard!")
    
else:
    print("❌ No data files found!")
