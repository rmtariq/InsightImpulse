#!/usr/bin/env python3
"""
Step 3: Feature Engineering
Add flags and temporal features as specified in document
"""

import pandas as pd
import re
from pathlib import Path

INPUT_FILE = "JITP_2026/processed_data/pas_bersatu_filtered.csv"
OUTPUT_DIR = Path("JITP_2026/processed_data")

def add_temporal_features(df):
    """Add date_day, date_week, date_month"""
    print("📅 Adding temporal features...")
    
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df['date_day'] = df['Date'].dt.date
    df['date_week'] = df['Date'].dt.to_period('W').astype(str)
    df['date_month'] = df['Date'].dt.to_period('M').astype(str)
    df['date_year'] = df['Date'].dt.year
    
    print(f"   ✅ Added temporal features")
    return df

def add_phrase_flags(df):
    """
    Add flags: has_pas_solo_phrase, has_split_phrase, has_review_phrase
    """
    print("🏷️  Adding phrase detection flags...")
    
    df['text_lower'] = df['clean_text'].str.lower()
    
    # PAS Solo phrases
    pas_solo_patterns = [
        r'pas bergerak solo',
        r'pas boleh bergerak solo',
        r'pas solo',
        r'pas gerak solo',
        r'\bsolo\b.*\bpas\b',
        r'\bpas\b.*\bsolo\b',
    ]
    df['has_pas_solo_phrase'] = df['text_lower'].str.contains('|'.join(pas_solo_patterns), regex=True, na=False)
    
    # Split phrases
    split_patterns = [
        r'\bperpecahan\b',
        r'\bberperah\b',
        r'retak menanti belah',
        r'\bretak\b',
        r'putus kerjasama',
        r'risky rift',
    ]
    df['has_split_phrase'] = df['text_lower'].str.contains('|'.join(split_patterns), regex=True, na=False)
    
    # Review/reconsider phrases
    review_patterns = [
        r'kaji semula hubungan',
        r'teliti semula hubungan',
        r'nilai semula kerjasama',
        r'kaji semula',
        r'nilai semula',
    ]
    df['has_review_phrase'] = df['text_lower'].str.contains('|'.join(review_patterns), regex=True, na=False)
    
    # Drop temporary column
    df = df.drop(columns=['text_lower'])
    
    solo_count = df['has_pas_solo_phrase'].sum()
    split_count = df['has_split_phrase'].sum()
    review_count = df['has_review_phrase'].sum()
    
    print(f"   ✅ PAS Solo phrases: {solo_count}")
    print(f"   ✅ Split phrases: {split_count}")
    print(f"   ✅ Review phrases: {review_count}")
    
    return df

def add_entity_mentions(df):
    """Add keyword hit entities"""
    print("🏢 Detecting entity mentions...")
    
    df['text_lower'] = df['clean_text'].str.lower()
    
    # Detect key entities
    df['mentions_pas'] = df['text_lower'].str.contains(r'\bpas\b', regex=True, na=False)
    df['mentions_bersatu'] = df['text_lower'].str.contains(r'\bbersatu\b|\bppbm\b', regex=True, na=False)
    df['mentions_pn'] = df['text_lower'].str.contains(r'perikatan nasional|\bpn\b', regex=True, na=False)
    df['mentions_umno'] = df['text_lower'].str.contains(r'\bumno\b', regex=True, na=False)
    df['mentions_ph'] = df['text_lower'].str.contains(r'pakatan harapan|\bph\b', regex=True, na=False)
    
    # Detect key figures
    df['mentions_muhyiddin'] = df['text_lower'].str.contains(r'muhyiddin|muhyddin|tsmy', regex=True, na=False)
    df['mentions_hadi'] = df['text_lower'].str.contains(r'hadi awang|abdul hadi|tghh', regex=True, na=False)
    df['mentions_hamzah'] = df['text_lower'].str.contains(r'hamzah', regex=True, na=False)
    
    df = df.drop(columns=['text_lower'])
    
    print(f"   ✅ Entity mentions detected")
    return df

def calculate_engagement_score(df):
    """Standardize engagement score calculation"""
    print("📊 Calculating engagement scores...")
    
    # Normalize by platform (different platforms have different scales)
    # Simple formula: weighted sum of interactions
    df['engagement_score'] = (
        df['likes'] * 1.0 +
        df['shares'] * 2.0 +  # Shares are more valuable
        df['comments_count'] * 3.0 +  # Comments even more
        df['views'] * 0.01  # Views are numerous but less valuable
    )
    
    print(f"   ✅ Engagement scores calculated")
    return df

def save_outputs(df):
    """Save feature-engineered dataset"""
    print("\n💾 Saving enriched data...")
    
    output_file = OUTPUT_DIR / "pas_bersatu_analysis_ready.csv"
    df.to_csv(output_file, index=False)
    print(f"   Saved: {output_file}")
    
    # Summary statistics
    summary = {
        'total_records': len(df),
        'pas_solo_mentions': df['has_pas_solo_phrase'].sum(),
        'split_mentions': df['has_split_phrase'].sum(),
        'review_mentions': df['has_review_phrase'].sum(),
        'date_range': f"{df['Date'].min()} to {df['Date'].max()}",
        'platforms': df['Platform'].value_counts().to_dict(),
    }
    
    summary_file = OUTPUT_DIR / "step3_feature_summary.txt"
    with open(summary_file, 'w') as f:
        for key, value in summary.items():
            f.write(f"{key}: {value}\n")
    print(f"   Saved: {summary_file}")

def main():
    print("=" * 80)
    print("JITP_2026 - STEP 3: FEATURE ENGINEERING")
    print("=" * 80)
    
    # Load filtered data
    print(f"\n📥 Loading: {INPUT_FILE}")
    df = pd.read_csv(INPUT_FILE)
    print(f"   Total rows: {len(df):,}")
    
    # Add features
    df = add_temporal_features(df)
    df = add_phrase_flags(df)
    df = add_entity_mentions(df)
    df = calculate_engagement_score(df)
    
    # Save
    save_outputs(df)
    
    print("\n" + "=" * 80)
    print("✅ STEP 3 COMPLETE!")
    print("=" * 80)
    print(f"\n📊 Dataset ready for analysis:")
    print(f"   Records: {len(df):,}")
    print(f"   Features added: temporal, phrase flags, entity mentions, engagement scores")
    print(f"\n   Output: JITP_2026/processed_data/pas_bersatu_analysis_ready.csv")
    print(f"\n   Next step: Analysis and reporting!")

if __name__ == "__main__":
    main()
