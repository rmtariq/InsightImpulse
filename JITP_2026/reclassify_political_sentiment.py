#!/usr/bin/env python3
"""
Reclassify Political Sentiment - Context-Aware Malaysian Politics
Fixes misclassified "neutral" statements that are actually negative
"""
import pandas as pd
import re

INPUT_FILE = "JITP_2026/processed_data/pas_bersatu_split_posts_deduped.csv"
OUTPUT_FILE = "JITP_2026/processed_data/pas_bersatu_split_posts_reclassified.csv"

# Define political context patterns
NEGATIVE_PATTERNS = {
    'pressure_ultimatum': [
        r'desak.*nama',
        r'desak.*ganti',
        r'desak.*tukar',
        r'ultimatum',
        r'tuntut.*ganti',
        r'paksa.*tukar',
        r'minta.*letak jawatan'
    ],
    'crisis_conflict': [
        r'retak menanti belah',
        r'retak.*belah',
        r'krisis.*dalaman',
        r'pergaduhan',
        r'perpecahan',
        r'bergaduh',
        r'tegang',
        r'konflik.*terbuka',
        r'tidak harmoni'
    ],
    'betrayal_disloyalty': [
        r'tidak setia',
        r'pengkhianat',
        r'belot',
        r'tikam belakang',
        r'menipu',
        r'khianati',
        r'tidak amanah'
    ],
    'warning_threat': [
        r'jika tidak.*akibat',
        r'kesabaran ada batas',
        r'jangan.*menyesal',
        r'amaran keras',
        r'ancaman',
        r'akan.*tindakan'
    ],
    'criticism_attack': [
        r'gagal.*kepimpinan',
        r'lemah.*kuasa',
        r'tidak kompeten',
        r'khianat.*rakyat',
        r'bodoh.*keputusan',
        r'zalim.*tindakan'
    ]
}

POSITIVE_PATTERNS = {
    'unity_support': [
        r'bersatu.*kuat',
        r'kerjasama.*erat',
        r'sokong.*penuh',
        r'yakin.*kepimpinan',
        r'penyatuan ummah',
        r'harmoni.*parti',
        r'solid.*kerjasama'
    ],
    'praise_endorsement': [
        r'berani.*tegas',
        r'bijak.*keputusan',
        r'tepat.*tindakan',
        r'hebat.*strategi',
        r'komited.*rakyat',
        r'amanah.*tanggungjawab'
    ]
}

def reclassify_sentiment(row):
    """
    Reclassify sentiment based on political context
    """
    text = str(row['clean_text']).lower()
    current_sentiment = row['sentiment_label']
    
    # Only reclassify if currently NEUTRAL
    if current_sentiment != 'neutral':
        return current_sentiment
    
    # Check for NEGATIVE patterns
    for category, patterns in NEGATIVE_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, text):
                return f'negative_{category}'
    
    # Check for POSITIVE patterns
    for category, patterns in POSITIVE_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, text):
                return f'positive_{category}'
    
    # Stay neutral if no pattern matches
    return 'neutral'

def main():
    print("="*80)
    print("RECLASSIFYING POLITICAL SENTIMENT - CONTEXT AWARE")
    print("="*80)
    
    # Load data
    print("\n📥 Loading data...")
    df = pd.read_csv(INPUT_FILE)
    print(f"   Total records: {len(df):,}")
    
    # Original sentiment distribution
    print("\n📊 ORIGINAL Sentiment Distribution:")
    original_sentiment = df['sentiment_label'].value_counts()
    for s, count in original_sentiment.items():
        pct = count/len(df)*100
        print(f"   {s.upper():10}: {count:5,} ({pct:5.1f}%)")
    
    # Reclassify
    print("\n🔄 Reclassifying based on political context...")
    df['sentiment_reclassified'] = df.apply(reclassify_sentiment, axis=1)
    
    # New sentiment distribution
    print("\n✅ RECLASSIFIED Sentiment Distribution:")
    new_sentiment = df['sentiment_reclassified'].value_counts()
    for s, count in new_sentiment.items():
        pct = count/len(df)*100
        print(f"   {s.upper():30}: {count:5,} ({pct:5.1f}%)")
    
    # Show reclassification summary
    print("\n📈 RECLASSIFICATION SUMMARY:")
    reclassified = df[df['sentiment_label'] != df['sentiment_reclassified'].str.split('_').str[0]]
    print(f"   Total reclassified: {len(reclassified):,} posts ({len(reclassified)/len(df)*100:.1f}%)")
    
    # Show examples
    print("\n📝 EXAMPLES OF RECLASSIFIED POSTS:")
    print("\n" + "-"*80)
    for i, row in reclassified.head(10).iterrows():
        print(f"\nOriginal: {row['sentiment_label'].upper()}")
        print(f"New:      {row['sentiment_reclassified'].upper()}")
        print(f"Text:     {row['clean_text'][:150]}...")
        print("-"*80)
    
    # Save
    print(f"\n💾 Saving to: {OUTPUT_FILE}")
    df.to_csv(OUTPUT_FILE, index=False)
    print("✅ Done!")

if __name__ == "__main__":
    main()
