#!/usr/bin/env python3
import pandas as pd

df = pd.read_csv('data/combined/Combined_instagram_x_tiktok_20260524_233229.csv')
print(f"Total rows: {len(df)}")
print(f"Platform counts:\n{df['Platform'].value_counts()}")
print(f"\nDate sample (first 5): {df['Date'].head().tolist()}")
print(f"\nDate dtype: {df['Date'].dtype}")

# Check KDEBWM keyword presence
df['text_lower'] = df['Text'].astype(str).str.lower()
kdeb = df['text_lower'].str.contains('kdeb|kdebwm|waste management', na=False)
print(f"\nKDEBWM keyword mentions: {kdeb.sum()}")

complaint_kw = df['text_lower'].str.contains('sampah|kutip|bau|kotor|longgokan|lambat|aduan|complaint|waste|dirty|clean', na=False)
print(f"Complaint keyword mentions: {complaint_kw.sum()}")
print(f"Both (KDEBWM + complaint): {(kdeb & complaint_kw).sum()}")

# Sample KDEBWM posts
print("\nSample KDEBWM mentions:")
for t in df[kdeb]['Text'].head(5).tolist():
    print(f"  - {str(t)[:120]}")
