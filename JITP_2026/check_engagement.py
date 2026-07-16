#!/usr/bin/env python3
import pandas as pd

# Load the deduplicated data
df = pd.read_csv('JITP_2026/processed_data/pas_bersatu_split_posts_deduped.csv')

print('=== ENGAGEMENT ANALYSIS ===\n')
print(f'Total records: {len(df):,}')

# Check engagement columns
engagement_cols = ['total_engagement', 'likes', 'shares', 'comments_count', 'views']
for col in engagement_cols:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        print(f'\n{col}:')
        print(f'  Total: {df[col].sum():,.0f}')
        print(f'  Max: {df[col].max():,.0f}')
        print(f'  Mean: {df[col].mean():,.1f}')
        print(f'  Non-zero: {(df[col] > 0).sum():,} records')

# Calculate ACTUAL total engagement manually
if all(col in df.columns for col in ['likes', 'shares', 'comments_count', 'views']):
    actual_total = df['likes'].sum() + df['shares'].sum() + df['comments_count'].sum() + df['views'].sum()
    print(f'\n=== MANUAL CALCULATION ===')
    print(f'Likes + Shares + Comments + Views = {actual_total:,.0f}')
    
# Check total_engagement column
if 'total_engagement' in df.columns:
    print(f'\ntotal_engagement column sum: {df["total_engagement"].sum():,.0f}')
    
# Sample top 10 posts
print(f'\n=== TOP 10 BY total_engagement ===')
top10 = df.nlargest(10, 'total_engagement')[['Platform', 'total_engagement', 'likes', 'shares', 'comments_count', 'views']]
for i, row in top10.iterrows():
    total_eng = row['total_engagement']
    likes = row['likes']
    shares = row['shares']
    comments = row['comments_count']
    views = row['views']
    platform = row['Platform']
    print(f'{total_eng:8,.0f} | L:{likes:6,.0f} S:{shares:5,.0f} C:{comments:5,.0f} V:{views:7,.0f} | {platform}')

# Check 90-day filter
df['Date'] = pd.to_datetime(df['Date'], utc=True)
end_date = pd.Timestamp('2026-05-30', tz='UTC')
start_date = end_date - pd.Timedelta(days=90)
df_90 = df[df['Date'] >= start_date]

print(f'\n=== 90-DAY FILTER (1 Mac - 30 Mei 2026) ===')
print(f'Records: {len(df_90):,}')
print(f'Total Engagement (90 days): {df_90["total_engagement"].sum():,.0f}')
