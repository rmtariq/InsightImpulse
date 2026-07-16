#!/usr/bin/env python3
import pandas as pd

df = pd.read_csv('JITP_2026/processed_data/pas_bersatu_split_posts_corrected.csv')

print("="*80)
print("SEARCHING FOR YOUR SPECIFIC EXAMPLES")
print("="*80)

# Example 1: Muhyiddin desak PAS
print("\n1. Posts about 'Muhyiddin desak PAS':")
matches1 = df[df['clean_text'].str.contains('muhyiddin.*desak', case=False, na=False, regex=True) | 
               df['clean_text'].str.contains('desak.*pas', case=False, na=False, regex=True)]
print(f"   Found {len(matches1)} matches\n")
for i, row in matches1.head(5).iterrows():
    print(f"   Text: {row['clean_text'][:120]}...")
    print(f"   Original: {row['sentiment_label']} | Corrected: {row['sentiment_corrected']}")
    print()

# Example 2: Retak menanti belah
print("\n2. Posts with 'retak menanti belah':")
matches2 = df[df['clean_text'].str.contains('retak', case=False, na=False)]
print(f"   Found {len(matches2)} matches\n")
for i, row in matches2.head(5).iterrows():
    print(f"   Text: {row['clean_text'][:120]}...")
    print(f"   Original: {row['sentiment_label']} | Corrected: {row['sentiment_corrected']}")
    print()

# All "desak" posts
print("\n3. ALL posts with 'desak' keyword:")
desak = df[df['clean_text'].str.contains('desak', case=False, na=False)]
print(f"   Total: {len(desak)}\n")
print(f"   Original Sentiment:")
for s, c in desak['sentiment_label'].value_counts().items():
    pct = c/len(desak)*100
    print(f"      {s.upper():10}: {c:3} ({pct:4.1f}%)")
print(f"\n   Corrected Sentiment:")
for s, c in desak['sentiment_corrected'].value_counts().items():
    pct = c/len(desak)*100
    print(f"      {s.upper():10}: {c:3} ({pct:4.1f}%)")
