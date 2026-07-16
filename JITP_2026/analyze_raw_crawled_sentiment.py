#!/usr/bin/env python3
"""
Analyze sentiment from RAW crawled data (before processing)
This shows what ft-Malay-bert ACTUALLY predicted during crawling
"""
import pandas as pd
import csv

RAW_FILES = [
    "data/combined/Combined_facebook_instagram_threads_tiktok_x_youtube_20260529_150109.csv",  # Q1
    "data/combined/Combined_facebook_instagram_threads_tiktok_x_youtube_20260529_153900.csv",  # Q2
    "data/combined/Combined_facebook_instagram_threads_tiktok_x_youtube_20260529_162307.csv",  # Q3
    "data/combined/Combined_facebook_threads_tiktok_20260529_185942.csv",  # Q4
    "data/combined/Combined_facebook_threads_tiktok_20260529_192718.csv",  # Q5
    "data/combined/Combined_facebook_threads_tiktok_20260529_194701.csv",  # Q6
]

QUERY_NAMES = [
    "Q1: PAS OR Bersatu OR PN...",
    "Q2: PAS bergerak solo...",
    "Q3: PAS AND Bersatu (general)",
    "Q4: PAS solo gerak solo",
    "Q5: PAS Bersatu perpecahan",
    "Q6: Hadi Awang Bersatu"
]

def safe_read_csv(filepath):
    """Read CSV with robust error handling"""
    try:
        # Try with quoting=csv.QUOTE_ALL first
        df = pd.read_csv(filepath, quoting=csv.QUOTE_ALL, engine='python', on_bad_lines='skip')
        return df
    except:
        try:
            # Fallback
            df = pd.read_csv(filepath, on_bad_lines='skip')
            return df
        except Exception as e:
            print(f"   ❌ Error reading {filepath}: {e}")
            return None

print("="*80)
print("RAW CRAWLED DATA SENTIMENT ANALYSIS")
print("Checking sentiment predictions from ft-Malay-bert during crawling")
print("="*80)

all_data = []
total_records = 0

for i, filepath in enumerate(RAW_FILES):
    query_name = QUERY_NAMES[i]
    print(f"\n{'='*80}")
    print(f"{query_name}")
    print(f"File: {filepath}")
    print(f"{'='*80}")
    
    df = safe_read_csv(filepath)
    
    if df is None:
        continue
    
    print(f"\n📊 Total records: {len(df):,}")
    total_records += len(df)
    
    # Check columns
    if 'Sentiment' in df.columns:
        print(f"\n✅ Sentiment column found!")
        
        # Sentiment distribution
        sentiment_counts = df['Sentiment'].value_counts()
        print(f"\nSentiment Distribution:")
        for sent, count in sentiment_counts.items():
            pct = count/len(df)*100
            bar = '█' * int(pct/2)
            print(f"   {str(sent).upper():10}: {count:6,} ({pct:5.1f}%) {bar}")
        
        # Check for examples with "desak" or "retak"
        if 'Content' in df.columns or 'Text' in df.columns:
            content_col = 'Content' if 'Content' in df.columns else 'Text'
            
            desak_posts = df[df[content_col].str.contains('desak', case=False, na=False)]
            if len(desak_posts) > 0:
                print(f"\n🔍 Posts with 'desak': {len(desak_posts)}")
                desak_sentiment = desak_posts['Sentiment'].value_counts()
                for s, c in desak_sentiment.items():
                    print(f"      {str(s).upper():10}: {c:3}")
                
                print(f"\n   Sample 'desak' posts:")
                for j, row in desak_posts.head(3).iterrows():
                    print(f"   [{row['Sentiment'].upper()}] {row[content_col][:100]}...")
            
            retak_posts = df[df[content_col].str.contains('retak', case=False, na=False)]
            if len(retak_posts) > 0:
                print(f"\n🔍 Posts with 'retak': {len(retak_posts)}")
                retak_sentiment = retak_posts['Sentiment'].value_counts()
                for s, c in retak_sentiment.items():
                    print(f"      {str(s).upper():10}: {c:3}")
                
                print(f"\n   Sample 'retak' posts:")
                for j, row in retak_posts.head(3).iterrows():
                    print(f"   [{row['Sentiment'].upper()}] {row[content_col][:100]}...")
        
        # Store for aggregation
        all_data.append({
            'query': query_name,
            'records': len(df),
            'sentiment': sentiment_counts.to_dict()
        })
    else:
        print(f"\n⚠️  No 'Sentiment' column found")
        print(f"   Available columns: {list(df.columns[:10])}")

# AGGREGATE SUMMARY
print("\n\n" + "="*80)
print("AGGREGATE SUMMARY - ALL RAW DATA")
print("="*80)

print(f"\nTotal records across all files: {total_records:,}")

if all_data:
    # Combine all sentiment counts
    all_sentiment = {}
    for data in all_data:
        for sent, count in data['sentiment'].items():
            all_sentiment[sent] = all_sentiment.get(sent, 0) + count
    
    print(f"\n📊 OVERALL SENTIMENT (Raw Crawled Data):")
    total_sent = sum(all_sentiment.values())
    for sent in sorted(all_sentiment.keys(), key=lambda x: all_sentiment[x], reverse=True):
        count = all_sentiment[sent]
        pct = count/total_sent*100
        bar = '█' * int(pct/2)
        print(f"   {str(sent).upper():10}: {count:6,} ({pct:5.1f}%) {bar}")

print("\n" + "="*80)
