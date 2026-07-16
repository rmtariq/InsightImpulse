#!/usr/bin/env python3
"""
Apply Political Context Layer - Override ft-Malay-bert mistakes
This runs AFTER the base sentiment model to fix political misclassifications
"""
import pandas as pd
import re

INPUT_FILE = "JITP_2026/processed_data/pas_bersatu_split_posts_deduped.csv"
OUTPUT_FILE = "JITP_2026/processed_data/pas_bersatu_split_posts_corrected.csv"

# Political context overrides - these patterns should ALWAYS be negative
FORCE_NEGATIVE = {
    'political_pressure': [
        r'desak.*nama',
        r'desak.*ganti',
        r'desak.*tukar',
        r'desak pas',
        r'tuntut.*ganti',
        r'minta.*letak jawatan',
        r'suruh.*undur'
    ],
    'crisis_warning': [
        r'retak menanti belah',
        r'kesabaran ada batas',
        r'krisis.*dalam',
        r'perpecahan.*semakin',
        r'tegang.*hubungan',
        r'konflik terbuka'
    ],
    'betrayal': [
        r'tidak setia',
        r'pengkhianat',
        r'belot',
        r'tikam belakang'
    ]
}

# Should be positive
FORCE_POSITIVE = {
    'support_unity': [
        r'sokong.*kuat',
        r'penyatuan.*ummah',
        r'bersatu.*teguh',
        r'kerjasama.*erat'
    ]
}

def apply_political_context(row):
    """
    Override sentiment if political context detected
    Returns: (new_sentiment, override_reason)
    """
    text = str(row['clean_text']).lower()
    current_sentiment = row['sentiment_label']
    
    # Check NEGATIVE patterns
    for category, patterns in FORCE_NEGATIVE.items():
        for pattern in patterns:
            if re.search(pattern, text):
                return 'negative', f'political_context_{category}'
    
    # Check POSITIVE patterns
    for category, patterns in FORCE_POSITIVE.items():
        for pattern in patterns:
            if re.search(pattern, text):
                return 'positive', f'political_context_{category}'
    
    # No override needed
    return current_sentiment, 'original_model'

def main():
    print("="*80)
    print("APPLYING POLITICAL CONTEXT LAYER")
    print("Fixing ft-Malay-bert misclassifications for political content")
    print("="*80)
    
    # Load
    print(f"\n📥 Loading: {INPUT_FILE}")
    df = pd.read_csv(INPUT_FILE)
    print(f"   Total: {len(df):,} records")
    
    # Original sentiment
    print("\n📊 ORIGINAL SENTIMENT (from ft-Malay-bert):")
    for s, count in df['sentiment_label'].value_counts().items():
        pct = count/len(df)*100
        print(f"   {s.upper():10}: {count:5,} ({pct:5.1f}%)")
    
    # Apply political context
    print("\n🔄 Applying political context overrides...")
    results = df.apply(apply_political_context, axis=1, result_type='expand')
    df['sentiment_corrected'] = results[0]
    df['override_reason'] = results[1]
    
    # New sentiment
    print("\n✅ CORRECTED SENTIMENT:")
    for s, count in df['sentiment_corrected'].value_counts().items():
        pct = count/len(df)*100
        print(f"   {s.upper():10}: {count:5,} ({pct:5.1f}%)")
    
    # Show changes
    changed = df[df['sentiment_label'] != df['sentiment_corrected']]
    print(f"\n📈 OVERRIDES APPLIED: {len(changed):,} posts ({len(changed)/len(df)*100:.1f}%)")
    
    if len(changed) > 0:
        print("\nBreakdown by reason:")
        for reason, count in changed['override_reason'].value_counts().items():
            print(f"   {reason:30}: {count:4,}")
        
        print("\n📝 SAMPLE CORRECTIONS (First 5):")
        print("-"*80)
        for i, row in changed.head(5).iterrows():
            print(f"\nOriginal: {row['sentiment_label'].upper():8} → Corrected: {row['sentiment_corrected'].upper():8}")
            print(f"Reason:   {row['override_reason']}")
            print(f"Text:     {row['clean_text'][:200]}...")
            print("-"*80)
    
    # Save
    print(f"\n💾 Saving to: {OUTPUT_FILE}")
    df.to_csv(OUTPUT_FILE, index=False)
    
    print("\n✅ DONE!")
    print(f"\nNow use this file for dashboard generation:")
    print(f"   {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
