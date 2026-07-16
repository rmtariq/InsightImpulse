#!/usr/bin/env python3
"""
Script to update RAW files with sentiment data from PROCESSED files
"""
import pandas as pd
from pathlib import Path

def update_raw_with_sentiment():
    """Update RAW file with sentiment data from PROCESSED file"""
    
    # Files - UPDATE TO LATEST
    raw_file = Path("data/raw/x_raw_pilihan_raya_pbt_20260210_003839.csv")
    processed_file = Path("data/smart_crawlers/x/x_pilihan_raya_pbt_20260210.csv")
    
    print(f"📊 Loading files...")
    print(f"  RAW: {raw_file}")
    print(f"  PROCESSED: {processed_file}")
    
    # Load files
    raw_df = pd.read_csv(raw_file)
    proc_df = pd.read_csv(processed_file)
    
    print(f"\n📊 File info:")
    print(f"  RAW rows: {len(raw_df)} (posts + comments)")
    print(f"  PROCESSED rows: {len(proc_df)} (posts only)")
    
    # Sentiment columns to copy
    sentiment_cols = ['sentiment_label', 'sentiment_score', 'sentiment_confidence',
                     'emotion_primary', 'emotion_anger', 'emotion_fear', 
                     'emotion_happy', 'emotion_sadness', 'emotion_love', 'emotion_surprise']
    
    # Add sentiment columns to raw_df if they don't exist
    for col in sentiment_cols:
        if col not in raw_df.columns:
            if col == 'sentiment_label':
                raw_df[col] = 'neutral'
            elif col == 'emotion_primary':
                raw_df[col] = 'neutral'
            else:
                raw_df[col] = 0.0
    
    print(f"\n🔄 Updating sentiment data...")
    
    # Update sentiment data for posts (match by ID)
    updated_count = 0
    for idx, row in proc_df.iterrows():
        post_id = row.get('ID')
        if pd.notna(post_id):
            # Find matching row in raw_df
            mask = raw_df['ID'] == post_id
            if mask.any():
                # Update sentiment columns
                for col in sentiment_cols:
                    if col in proc_df.columns:
                        raw_df.loc[mask, col] = row[col]
                # Also update the original Sentiment column
                if 'sentiment_label' in proc_df.columns:
                    raw_df.loc[mask, 'Sentiment'] = row['sentiment_label']
                updated_count += 1
    
    print(f"✅ Updated {updated_count} posts with sentiment data")
    
    # Save updated RAW file
    raw_df.to_csv(raw_file, index=False, encoding='utf-8')
    print(f"\n💾 Saved updated RAW file: {raw_file}")
    print(f"💾 RAW file now has {len(raw_df)} rows and {len(raw_df.columns)} columns")
    
    # Verify sentiment distribution
    if 'sentiment_label' in raw_df.columns:
        print(f"\n✅ Sentiment distribution in RAW file (posts only):")
        sentiment_dist = raw_df[raw_df['Type'] == 'post']['sentiment_label'].value_counts()
        for label, count in sentiment_dist.items():
            print(f"  {label}: {count}")
        
        print(f"\n✅ Sentiment column distribution (all rows):")
        sentiment_dist_all = raw_df['Sentiment'].value_counts()
        for label, count in sentiment_dist_all.items():
            print(f"  {label}: {count}")
    
    print(f"\n🎉 DONE! RAW file updated successfully!")

if __name__ == "__main__":
    update_raw_with_sentiment()

