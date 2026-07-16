#!/usr/bin/env python3
"""
Analyze raw data from all 6 queries
Check actual counts and deduplication logic
"""

import pandas as pd

files = {
    'Q1': 'data/combined/Combined_facebook_instagram_threads_tiktok_x_youtube_20260529_150109.csv',
    'Q2': 'data/combined/Combined_facebook_instagram_threads_tiktok_x_youtube_20260529_153900.csv',
    'Q3': 'data/combined/Combined_facebook_instagram_threads_tiktok_x_youtube_20260529_162307.csv',
    'Q4': 'data/combined/Combined_facebook_threads_tiktok_20260529_185942.csv',
    'Q5': 'data/combined/Combined_facebook_threads_tiktok_20260529_192718.csv',
    'Q6': 'data/combined/Combined_facebook_threads_tiktok_20260529_194701.csv',
}

print("=" * 80)
print("DETAILED RAW DATA ANALYSIS - ALL 6 QUERIES")
print("=" * 80)

all_data = []
total = 0

for query, file in files.items():
    df = pd.read_csv(file)
    count = len(df)
    total += count
    
    df['query_source'] = query
    all_data.append(df)
    
    posts = len(df[df['Type'] == 'post'])
    comments = len(df[df['Type'] == 'comment'])
    platforms = df['Platform'].value_counts().to_dict()
    
    print(f"\n{query}: {count:,} records")
    print(f"   Posts: {posts:,} | Comments: {comments:,}")
    print(f"   Platforms: {', '.join([f'{k}({v})' for k, v in platforms.items()])}")

print(f"\n{'=' * 80}")
print(f"TOTAL RAW RECORDS: {total:,}")
print(f"{'=' * 80}")

# Combine all
all_df = pd.concat(all_data, ignore_index=True)
print(f"\nCombined dataset: {len(all_df):,} rows")

# Check duplicates
unique_ids = all_df['ID'].nunique()
duplicate_ids = len(all_df) - unique_ids
print(f"Unique IDs: {unique_ids:,}")
print(f"Duplicate IDs across queries: {duplicate_ids:,}")

# Posts vs Comments
total_posts = len(all_df[all_df['Type'] == 'post'])
total_comments = len(all_df[all_df['Type'] == 'comment'])
print(f"\nTotal Posts: {total_posts:,}")
print(f"Total Comments: {total_comments:,}")

# After deduplication
unique_posts = all_df[all_df['Type'] == 'post']['ID'].nunique()
unique_comments = all_df[all_df['Type'] == 'comment']['ID'].nunique()
print(f"\nAfter ID deduplication:")
print(f"Unique Posts: {unique_posts:,}")
print(f"Unique Comments: {unique_comments:,}")
print(f"Total Unique: {unique_posts + unique_comments:,}")

print("\n" + "=" * 80)
print("QUERY OVERLAP ANALYSIS")
print("=" * 80)
for q1 in list(files.keys()):
    for q2 in list(files.keys()):
        if q1 < q2:
            df1 = all_df[all_df['query_source'] == q1]
            df2 = all_df[all_df['query_source'] == q2]
            overlap = len(set(df1['ID']) & set(df2['ID']))
            if overlap > 0:
                pct = (overlap / min(len(df1), len(df2))) * 100
                print(f"{q1} ∩ {q2}: {overlap:,} duplicates ({pct:.1f}%)")
