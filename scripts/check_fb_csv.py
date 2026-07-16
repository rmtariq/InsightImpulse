import pandas as pd, glob, os

af = max(glob.glob('data/analyzed/Sentiment_Emotion_FACEBOOK_*.csv'), key=os.path.getmtime)
cf = max(glob.glob('data/combined/Combined_facebook_*.csv'), key=os.path.getmtime)
for label, f in [('ANALYZED', af), ('COMBINED', cf)]:
    df = pd.read_csv(f)
    print(f"\n--- {label}: {f} ---")
    print(f"rows: {len(df)}  cols: {len(df.columns)}")
    if 'Type' in df.columns:
        print(f"Type: {df['Type'].value_counts(dropna=False).to_dict()}")
    for c in ['sentiment_label', 'emotion_primary']:
        if c in df.columns:
            print(f"{c}: {df[c].value_counts(dropna=False).to_dict()}")
        else:
            print(f"{c}: MISSING")
    if 'Type' in df.columns and 'sentiment_label' in df.columns and 'emotion_primary' in df.columns:
        for t in df['Type'].dropna().unique():
            sub = df[df['Type'] == t]
            sent_filled = sub['sentiment_label'].notna().sum()
            emo_filled = sub['emotion_primary'].notna().sum()
            print(f"  {t}: {len(sub)} rows | sentiment_label filled={sent_filled} | emotion_primary filled={emo_filled}")
