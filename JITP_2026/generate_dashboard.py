#!/usr/bin/env python3
"""
Generate PAS Political Strategy Dashboard Data
Strategi Menang PAS untuk PRN dan PRU16
"""

import pandas as pd
import json
from pathlib import Path

INPUT_FILE = "JITP_2026/processed_data/pas_bersatu_split_posts_deduped.csv"
OUTPUT_JSON = "static/pas_dashboard_data.json"

def load_data():
    print("📥 Loading data...")
    df = pd.read_csv(INPUT_FILE)
    df['Date'] = pd.to_datetime(df['Date'], utc=True)

    # Fix numeric columns
    for col in ['total_engagement', 'likes', 'shares', 'comments_count', 'views']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # ORIGINAL RAW DATA = 8,351 (from step1 BEFORE deduplication)
    total_original_raw = 8351

    # Calculate FULL engagement before filtering
    total_engagement_full = int(df['total_engagement'].sum())

    # Filter to last 90 days (1 March 2026 - 30 May 2026) for temporal analysis
    end_date = pd.Timestamp('2026-05-30', tz='UTC')
    start_date = end_date - pd.Timedelta(days=90)
    df_90days = df[df['Date'] >= start_date].copy()

    print(f"   Total ORIGINAL RAW DATA: {total_original_raw:,} records (combined from all 6 queries)")
    print(f"   Total CLEAN DATA: {len(df):,} records (after deduplication)")
    print(f"   TOTAL ENGAGEMENT (ALL DATA): {total_engagement_full:,}")
    print(f"   Filtered (last 90 days): {len(df_90days):,} records")
    print(f"   Date range: {start_date.date()} to {end_date.date()}")

    return df, df_90days, total_original_raw, total_engagement_full

def analyze_narratives(df):
    print("🔍 Analyzing narratives...")
    df['text_lower'] = df['clean_text'].fillna('').str.lower()
    df['n_pas_solo'] = df['text_lower'].str.contains(r'pas solo|pas bergerak solo', regex=True, na=False)
    df['n_split'] = df['text_lower'].str.contains(r'perpecahan|retak|pecah', regex=True, na=False)
    df['n_hadi'] = df['text_lower'].str.contains(r'hadi awang|abdul hadi', regex=True, na=False)
    df['n_muhyiddin'] = df['text_lower'].str.contains(r'muhyiddin', regex=True, na=False)
    return df.drop(columns=['text_lower'])

def prepare_data(df_full, df_90days, total_original, total_engagement_full):
    print("📊 Preparing dashboard data...")
    data = {}

    # Count posts from 90-day period for temporal analysis
    posts_90days = df_90days[df_90days['Type'] == 'post']

    data['stats'] = {
        'total_original': total_original,  # Original raw data = 8,351
        'total_clean': len(df_full),  # Clean deduplicated data = 5,906
        'posts': len(posts_90days),  # Posts in last 90 days
        'engagement': total_engagement_full  # FULL engagement from all data (136M+)
    }
    
    # Temporal trends (use 90-day data for timeline)
    daily = df_90days.groupby(df_90days['Date'].dt.date).agg({'ID': 'count', 'total_engagement': 'sum'}).reset_index()
    daily.columns = ['date', 'posts', 'engagement']
    daily['date'] = daily['date'].astype(str)
    data['daily'] = daily.to_dict('records')

    # Platform distribution (use full data)
    platforms = df_full.groupby('Platform').agg({'ID': 'count', 'total_engagement': 'sum'}).reset_index()
    platforms.columns = ['platform', 'posts', 'engagement']
    data['platforms'] = platforms.to_dict('records')

    # Sentiment/emotions from full data
    data['sentiment'] = {k: int(v) for k, v in df_full['sentiment_label'].value_counts().to_dict().items()}
    data['emotions'] = {k: int(v) for k, v in df_full['emotion_primary'].value_counts().head(8).to_dict().items()}
    data['narratives'] = {
        'PAS Solo': int(df_full['n_pas_solo'].sum()),
        'Perpecahan': int(df_full['n_split'].sum())
    }

    # Top posts - FILTER for Malay/English and relevant content only (use FULL data)
    print("   Filtering top viral posts (Malay/English, PAS-Bersatu relevant only)...")

    # Keywords that indicate relevant PAS-Bersatu content
    relevant_keywords = [
        'pas', 'bersatu', 'perikatan', 'hadi', 'muhyiddin', 'pn',
        'solo', 'perpecahan', 'retak', 'coalition', 'alliance',
        'prn', 'pru', 'pilihanraya', 'politik', 'parti'
    ]

    # Common French/Indonesian/other language indicators to exclude
    exclude_patterns = [
        'wsh', 'mais', 'vous', 'pour', 'dans', 'avec', 'être',  # French
        'temenku', 'bapakku', 'kaya raya', 'gua', 'gw', 'aja',  # Indonesian slang
        'di sd', 'di smp', 'sekolah', 'teman sekolah',  # Indonesian school talk
        'ragebait', 'longueur de journée',  # French gaming
        'parc des princes', 'ldc', 'coupe',  # French sports
        'sénégal', 'maroc', 'tunisie', 'algérie'  # French African
    ]

    # Filter for relevant posts - STRICT Malaysian political context only
    def is_relevant_malaysian_politics(text):
        if pd.isna(text) or len(str(text).strip()) < 20:
            return False
        text_lower = str(text).lower()

        # HARD EXCLUDE: Non-political/non-Malay content
        if any(pattern in text_lower for pattern in exclude_patterns):
            return False

        # Score-based approach
        score = 0

        # HIGH VALUE: Explicit PAS/Bersatu party names (not just "pas" which is French)
        if 'parti islam semalaysia' in text_lower or 'parti islam' in text_lower:
            score += 5
        if 'bersatu' in text_lower:
            score += 5
        if 'perikatan nasional' in text_lower or 'perikatan' in text_lower:
            score += 5
        if 'hadi awang' in text_lower or 'abdul hadi' in text_lower or 'tuan guru' in text_lower:
            score += 5
        if 'muhyiddin' in text_lower or 'tan sri muhyiddin' in text_lower:
            score += 5
        if 'pas solo' in text_lower or 'pas bergerak solo' in text_lower:
            score += 5

        # MEDIUM VALUE: Malaysian political context
        malay_political = ['kerajaan', 'parlimen', 'menteri', 'parti', 'pilihan raya', 'prn', 'pru',
                          'politik', 'pengundi', 'kerusi', 'negara', 'malaysia', 'umno', 'dap', 'pkr']
        score += sum(1 for term in malay_political if term in text_lower)

        # MEDIUM VALUE: Coalition/split narrative
        coalition_terms = ['perpecahan', 'retak', 'gaduh', 'krisis', 'coalition', 'alliance', 'split']
        score += sum(2 for term in coalition_terms if term in text_lower)

        # Must score at least 5 to be considered relevant
        return score >= 5

    # Filter posts (use FULL data for viral posts)
    filtered_df = df_full[df_full['clean_text'].apply(is_relevant_malaysian_politics)].copy()

    if len(filtered_df) < 10:
        print(f"   ⚠️ Warning: Only {len(filtered_df)} relevant posts found. Relaxing filter slightly...")
        # Fallback: posts with Bersatu/Perikatan/Hadi/Muhyiddin (more reliable than "pas")
        filtered_df = df_full[df_full['clean_text'].str.lower().str.contains('bersatu|perikatan|hadi awang|muhyiddin', na=False, regex=True)].copy()

    # Get top posts with platform diversity
    top_posts_list = []
    platforms_seen = {}

    # Sort by engagement
    for _, row in filtered_df.nlargest(100, 'total_engagement').iterrows():
        platform = row['Platform']

        # Limit 5 posts per platform for diversity
        if platforms_seen.get(platform, 0) >= 5:
            continue

        # Handle NaT dates
        try:
            date_str = row['Date'].strftime('%d %b %Y') if pd.notna(row['Date']) else 'Unknown'
        except:
            date_str = 'Unknown'

        top_posts_list.append({
            'Platform': platform,
            'Date': date_str,
            'clean_text': str(row['clean_text'])[:300] + '...' if len(str(row['clean_text'])) > 300 else str(row['clean_text']),
            'total_engagement': int(row['total_engagement']),
            'sentiment_label': row['sentiment_label']
        })

        platforms_seen[platform] = platforms_seen.get(platform, 0) + 1

        # Stop at 20 posts
        if len(top_posts_list) >= 20:
            break

    data['top_posts'] = top_posts_list
    print(f"   ✅ Found {len(top_posts_list)} relevant viral posts across {len(platforms_seen)} platforms")

    return data

def main():
    df_full, df_90days, total_original, total_engagement_full = load_data()
    df_full = analyze_narratives(df_full)
    df_90days = analyze_narratives(df_90days)
    data = prepare_data(df_full, df_90days, total_original, total_engagement_full)
    
    Path(OUTPUT_JSON).parent.mkdir(exist_ok=True)
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"✅ Saved: {OUTPUT_JSON}")
    print(f"📊 Original: {data['stats']['total_original']:,} | Clean: {data['stats']['total_clean']:,} | Posts (90d): {data['stats']['posts']:,} | 🔥 ENGAGEMENT: {data['stats']['engagement']:,}")

if __name__ == "__main__":
    main()
