#!/usr/bin/env python3
"""
Step 2: Apply Boolean Filter (Document Specification)
Filter posts matching the exact Boolean query from specification
"""

import pandas as pd
import re
from pathlib import Path

INPUT_FILE = "JITP_2026/processed_data/pas_bersatu_split_posts_deduped.csv"
OUTPUT_DIR = Path("JITP_2026/processed_data")

def apply_boolean_filter(df):
    """
    Apply Boolean query from specification:
    ("PAS" OR "Parti Islam Se-Malaysia" OR "Parti Islam Se Malaysia")
    AND
    ("Bersatu" OR "PPBM" OR "Perikatan Nasional" OR "PN")
    AND
    ("kaji semula hubungan" OR "teliti semula hubungan" OR "putus kerjasama" OR 
     "perpecahan" OR "PAS bergerak solo" OR "PAS boleh bergerak solo")
    
    Plus variations:
    - pas kaji hubungan dengan bersatu
    - pas nilai semula kerjasama dengan bersatu
    - pas tidak tunduk kepada bersatu
    - retak menanti belah
    - pas solo
    - go solo (if PAS and Bersatu/PN present)
    """
    print("🔍 Applying Boolean filter...")
    
    # Convert to lowercase for matching
    df['text_lower'] = df['clean_text'].str.lower()
    
    # Group 1: PAS mentions
    pas_patterns = [
        r'\bpas\b',
        r'parti islam se-malaysia',
        r'parti islam se malaysia',
    ]
    has_pas = df['text_lower'].str.contains('|'.join(pas_patterns), regex=True, na=False)
    
    # Group 2: Bersatu/PN mentions
    bersatu_patterns = [
        r'\bbersatu\b',
        r'\bppbm\b',
        r'perikatan nasional',
        r'\bpn\b',
    ]
    has_bersatu = df['text_lower'].str.contains('|'.join(bersatu_patterns), regex=True, na=False)
    
    # Group 3: Issue keywords
    issue_patterns = [
        r'kaji semula hubungan',
        r'teliti semula hubungan',
        r'putus kerjasama',
        r'\bperpecahan\b',
        r'pas bergerak solo',
        r'pas boleh bergerak solo',
        # Variations
        r'pas kaji hubungan',
        r'pas nilai semula',
        r'pas tidak tunduk',
        r'retak menanti belah',
        r'\bretak\b',
        r'pas solo',
        r'go solo',
        r'\bsolo\b.*\bpas\b',
        r'\bpas\b.*\bsolo\b',
    ]
    has_issue = df['text_lower'].str.contains('|'.join(issue_patterns), regex=True, na=False)
    
    # Apply Boolean AND logic
    filtered = df[has_pas & has_bersatu & has_issue].copy()
    
    # Drop temporary column
    filtered = filtered.drop(columns=['text_lower'])
    df = df.drop(columns=['text_lower'])
    
    print(f"   ✅ Matched {len(filtered):,} / {len(df):,} rows ({len(filtered)/len(df)*100:.1f}%)")
    
    return filtered, df

def calculate_statistics(filtered_df, original_df):
    """Calculate match statistics"""
    stats = {
        'total_rows_original': len(original_df),
        'total_rows_matched': len(filtered_df),
        'match_rate': f"{len(filtered_df)/len(original_df)*100:.2f}%",
        'matched_posts': len(filtered_df[filtered_df['Type'] == 'post']),
        'matched_comments': len(filtered_df[filtered_df['Type'] == 'comment']),
        'platforms': filtered_df['Platform'].value_counts().to_dict(),
        'query_distribution': filtered_df['query_source'].value_counts().to_dict(),
    }
    return stats

def save_outputs(filtered_df, stats):
    """Save filtered dataset and statistics"""
    print("\n💾 Saving filtered data...")
    
    # Save filtered dataset
    output_file = OUTPUT_DIR / "pas_bersatu_filtered.csv"
    filtered_df.to_csv(output_file, index=False)
    print(f"   Saved: {output_file}")
    
    # Save statistics
    stats_file = OUTPUT_DIR / "step2_filter_statistics.txt"
    with open(stats_file, 'w') as f:
        for key, value in stats.items():
            f.write(f"{key}: {value}\n")
    print(f"   Saved: {stats_file}")

def main():
    print("=" * 80)
    print("JITP_2026 - STEP 2: BOOLEAN FILTER")
    print("=" * 80)
    
    # Load deduplicated data
    print(f"\n📥 Loading: {INPUT_FILE}")
    df = pd.read_csv(INPUT_FILE)
    print(f"   Total rows: {len(df):,}")
    
    # Apply filter
    filtered_df, original_df = apply_boolean_filter(df)
    
    # Calculate statistics
    stats = calculate_statistics(filtered_df, original_df)
    
    # Save
    save_outputs(filtered_df, stats)
    
    print("\n" + "=" * 80)
    print("✅ STEP 2 COMPLETE!")
    print("=" * 80)
    print(f"\n📊 Filter Results:")
    print(f"   Original: {stats['total_rows_original']:,} rows")
    print(f"   Matched: {stats['total_rows_matched']:,} rows ({stats['match_rate']})")
    print(f"   Posts: {stats['matched_posts']:,}")
    print(f"   Comments: {stats['matched_comments']:,}")
    print(f"\n   Next step: Run step3_feature_engineering.py")

if __name__ == "__main__":
    main()
