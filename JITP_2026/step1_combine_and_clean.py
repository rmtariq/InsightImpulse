#!/usr/bin/env python3
"""
Step 1: Combine and Clean JITP_2026 Data
Based on technical specification document requirements
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

# File paths - ALL 6 QUERIES
QUERY_1_FILE = "data/combined/Combined_facebook_instagram_threads_tiktok_x_youtube_20260529_150109.csv"
QUERY_2_FILE = "data/combined/Combined_facebook_instagram_threads_tiktok_x_youtube_20260529_153900.csv"
QUERY_3_FILE = "data/combined/Combined_facebook_instagram_threads_tiktok_x_youtube_20260529_162307.csv"
QUERY_4_FILE = "data/combined/Combined_facebook_threads_tiktok_20260529_185942.csv"
QUERY_5_FILE = "data/combined/Combined_facebook_threads_tiktok_20260529_192718.csv"
QUERY_6_FILE = "data/combined/Combined_facebook_threads_tiktok_20260529_194701.csv"

OUTPUT_DIR = Path("JITP_2026/processed_data")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def load_and_tag_data():
    """Load all 6 datasets and tag them with query source"""
    print("📥 Loading datasets (with multi-line text handling)...")

    # Load with query tags - IMPORTANT: quoting=1 handles multi-line text fields!
    df1 = pd.read_csv(QUERY_1_FILE, quoting=1, escapechar='\\', on_bad_lines='skip')
    df1['query_source'] = 'Q1_Coalition_General'
    print(f"   Q1: {len(df1):,} rows (PAS OR Bersatu OR PN)")

    df2 = pd.read_csv(QUERY_2_FILE, quoting=1, escapechar='\\', on_bad_lines='skip')
    df2['query_source'] = 'Q2_PAS_Solo'
    print(f"   Q2: {len(df2):,} rows (PAS bergerak solo)")

    df3 = pd.read_csv(QUERY_3_FILE, quoting=1, escapechar='\\', on_bad_lines='skip')
    df3['query_source'] = 'Q3_Coalition_Split'
    print(f"   Q3: {len(df3):,} rows (PAS Bersatu perpecahan)")

    df4 = pd.read_csv(QUERY_4_FILE, quoting=1, escapechar='\\', on_bad_lines='skip')
    df4['query_source'] = 'Q4_Broad_v2'
    print(f"   Q4: {len(df4):,} rows (PAS Bersatu hubungan)")

    df5 = pd.read_csv(QUERY_5_FILE, quoting=1, escapechar='\\', on_bad_lines='skip')
    df5['query_source'] = 'Q5_Tension'
    print(f"   Q5: {len(df5):,} rows (Tension/Crisis)")

    df6 = pd.read_csv(QUERY_6_FILE, quoting=1, escapechar='\\', on_bad_lines='skip')
    df6['query_source'] = 'Q6_Leaders'
    print(f"   Q6: {len(df6):,} rows (Hadi Awang/Muhyiddin)")

    # Combine all 6
    df = pd.concat([df1, df2, df3, df4, df5, df6], ignore_index=True)
    print(f"\n✅ Total combined: {len(df):,} rows")

    return df

def clean_and_normalize(df):
    """Step 1: Data cleaning and normalization per specification"""
    print("\n🧹 Cleaning and normalizing data...")
    
    # 1. Remove rows without meaningful text
    before = len(df)
    df = df[df['Text'].notna() & (df['Text'].str.strip() != '')]
    print(f"   Removed {before - len(df):,} rows without meaningful text")
    
    # 2. Standardize platform names
    platform_map = {
        'facebook': 'facebook',
        'instagram': 'instagram',
        'threads': 'threads',
        'tiktok': 'tiktok',
        'x': 'x',
        'youtube': 'youtube',
    }
    df['Platform'] = df['Platform'].str.lower().map(platform_map).fillna('other')
    
    # 3. Standardize type
    type_map = {
        'post': 'post',
        'comment': 'comment',
    }
    df['Type'] = df['Type'].str.lower().map(type_map).fillna('other')
    
    # 4. Create clean_text (remove extra whitespace)
    df['text_original'] = df['Text']
    df['clean_text'] = df['Text'].str.replace(r'\s+', ' ', regex=True).str.strip()
    
    # 5. Normalize datetime
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df['datetime_utc'] = df['Date']
    
    # 6. Calculate total_engagement if missing
    engagement_cols = ['likes', 'shares', 'comments_count', 'views']
    for col in engagement_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    if 'total_engagement' not in df.columns or df['total_engagement'].isna().all():
        df['total_engagement'] = df['likes'] + df['shares'] + df['comments_count']
    
    # 7. Create datetime buckets for deduplication
    df['datetime_bucket'] = df['datetime_utc'].dt.floor('1H')  # 1-hour buckets
    
    print(f"✅ Cleaned dataset: {len(df):,} rows")
    return df

def deduplicate_data(df):
    """
    Step 2: RELAXED Smart deduplication (keep more data!)
    - Posts: Remove only EXACT duplicates by ID
    - Comments: Remove only EXACT duplicates by ID
    - Keep near-duplicates (same text, different time/platform = different viral spread!)
    """
    print("\n🔄 RELAXED Smart deduplication (keeping more data)...")

    before = len(df)

    # Separate posts and comments
    posts = df[df['Type'] == 'post'].copy()
    comments = df[df['Type'] == 'comment'].copy()

    print(f"   Posts: {len(posts):,}")
    print(f"   Comments: {len(comments):,}")

    # POSTS: Remove ONLY exact ID duplicates
    posts_before = len(posts)
    posts = posts.drop_duplicates(subset=['ID'], keep='first')
    exact_removed = posts_before - len(posts)
    print(f"   ✅ Removed {exact_removed:,} duplicate posts (exact ID only)")
    print(f"   ✅ KEPT near-duplicates (same text, different context)")

    # COMMENTS: Keep ALL unique IDs
    comments_before = len(comments)
    comments = comments.drop_duplicates(subset=['ID'], keep='first')
    comments_removed = comments_before - len(comments)
    print(f"   ✅ Removed {comments_removed:,} duplicate comments (exact ID only)")
    print(f"   ✅ Kept ALL unique comments: {len(comments):,}")

    # Combine back
    df_deduped = pd.concat([posts, comments], ignore_index=True)
    df_deduped = df_deduped.drop(columns=['datetime_bucket'])

    total_removed = before - len(df_deduped)
    print(f"\n✅ Total removed: {total_removed:,} (ID duplicates only)")
    print(f"✅ Final dataset: {len(df_deduped):,} rows")
    print(f"   - Posts: {len(posts):,}")
    print(f"   - Comments: {len(comments):,}")

    print(f"\n💡 Strategy: Kept near-duplicates for viral tracking!")
    print(f"   Same post on different platforms = different audience reach")
    print(f"   Same text at different times = viral resurgence")

    return df_deduped

def save_outputs(df):
    """Save cleaned datasets"""
    print("\n💾 Saving outputs...")
    
    # Save raw combined
    raw_file = OUTPUT_DIR / "pas_bersatu_split_posts_raw.csv"
    df.to_csv(raw_file, index=False)
    print(f"   Saved: {raw_file}")
    
    # Save deduplicated
    dedup_file = OUTPUT_DIR / "pas_bersatu_split_posts_deduped.csv"
    df.to_csv(dedup_file, index=False)
    print(f"   Saved: {dedup_file}")
    
    # Save statistics
    stats = {
        'total_rows_combined': len(df),
        'total_posts': len(df[df['Type'] == 'post']),
        'total_comments': len(df[df['Type'] == 'comment']),
        'platforms': df['Platform'].value_counts().to_dict(),
        'query_distribution': df['query_source'].value_counts().to_dict(),
        'timestamp': datetime.now().isoformat()
    }
    
    stats_file = OUTPUT_DIR / "step1_statistics.txt"
    with open(stats_file, 'w') as f:
        for key, value in stats.items():
            f.write(f"{key}: {value}\n")
    print(f"   Saved: {stats_file}")

def main():
    print("=" * 80)
    print("JITP_2026 - STEP 1: DATA COMBINATION AND CLEANING")
    print("=" * 80)
    
    # Load data
    df = load_and_tag_data()
    
    # Clean and normalize
    df = clean_and_normalize(df)
    
    # Deduplicate
    df = deduplicate_data(df)
    
    # Save
    save_outputs(df)
    
    print("\n" + "=" * 80)
    print("✅ STEP 1 COMPLETE!")
    print("=" * 80)
    print(f"\n📊 Summary:")
    print(f"   Total records: {len(df):,}")
    print(f"   Posts: {len(df[df['Type'] == 'post']):,}")
    print(f"   Comments: {len(df[df['Type'] == 'comment']):,}")
    print(f"\n   Next step: Run step2_boolean_filter.py")

if __name__ == "__main__":
    main()
