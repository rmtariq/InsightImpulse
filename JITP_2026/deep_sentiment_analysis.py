#!/usr/bin/env python3
"""
Deep Sentiment Analysis - Understanding TRUE sentiment about PAS-Bersatu split
"""
import json
import pandas as pd

# Load dashboard data
with open('static/pas_dashboard_data.json', 'r') as f:
    data = json.load(f)

print('='*80)
print('DEEP SENTIMENT ANALYSIS: PAS-BERSATU RELATIONSHIP')
print('='*80)

print('\n=== OVERALL SENTIMENT (All 5,906 posts) ===\n')
sentiment = data['sentiment']
total = sum(sentiment.values())
print(f'Total Posts: {total:,}\n')
for s, count in sorted(sentiment.items(), key=lambda x: x[1], reverse=True):
    pct = count/total*100
    bar = '█' * int(pct/2)
    print(f'{s.upper():10}: {count:4,} ({pct:5.1f}%) {bar}')

print('\n=== EMOTION ANALYSIS ===\n')
emotions = data['emotions']
for e, count in sorted(emotions.items(), key=lambda x: x[1], reverse=True):
    print(f'{e:20}: {count:4,}')

print('\n=== POLITICAL NARRATIVES ===\n')
narratives = data['narratives']
total_narrative = sum(narratives.values())
for n, count in narratives.items():
    pct = count/total_narrative*100
    print(f'{n:15}: {count:4,} ({pct:5.1f}%)')

# Now check the RAW data for deeper analysis
print('\n\n' + '='*80)
print('DEEP DIVE: CONTEXTUAL ANALYSIS')
print('='*80 + '\n')

df = pd.read_csv('JITP_2026/processed_data/pas_bersatu_split_posts_deduped.csv')

# Analyze posts mentioning conflict keywords
conflict_keywords = ['retak', 'perpecahan', 'gaduh', 'krisis', 'tegang', 'belah', 'bergaduh']
conflict_posts = df[df['clean_text'].str.lower().str.contains('|'.join(conflict_keywords), na=False, regex=True)]

print(f'Posts mentioning CONFLICT keywords ({", ".join(conflict_keywords)}):')
print(f'Total: {len(conflict_posts):,} posts ({len(conflict_posts)/len(df)*100:.1f}% of all data)\n')
print('Sentiment for conflict-related posts:')
for s, count in conflict_posts['sentiment_label'].value_counts().items():
    pct = count/len(conflict_posts)*100
    print(f'  {s.upper():10}: {count:4,} ({pct:5.1f}%)')

print('\nEmotions for conflict-related posts:')
for e, count in conflict_posts['emotion_primary'].value_counts().head(5).items():
    pct = count/len(conflict_posts)*100
    print(f'  {e:15}: {count:4,} ({pct:5.1f}%)')

# Analyze posts about Bersatu negative actions
bersatu_negative = df[df['clean_text'].str.lower().str.contains('bersatu', na=False) & 
                       df['clean_text'].str.lower().str.contains('tidak setia|pengkhianat|belot|kawan', na=False, regex=True)]

print(f'\n\nPosts about BERSATU with NEGATIVE keywords (tidak setia, pengkhianat, belot):')
print(f'Total: {len(bersatu_negative):,} posts\n')
if len(bersatu_negative) > 0:
    print('Sentiment distribution:')
    for s, count in bersatu_negative['sentiment_label'].value_counts().items():
        pct = count/len(bersatu_negative)*100
        print(f'  {s.upper():10}: {count:4,} ({pct:5.1f}%)')

# Sample some conflict posts
print('\n\n' + '='*80)
print('SAMPLE CONFLICT POSTS (Top 5 by engagement):')
print('='*80 + '\n')
conflict_posts['total_engagement'] = pd.to_numeric(conflict_posts['total_engagement'], errors='coerce').fillna(0)
for i, row in conflict_posts.nlargest(5, 'total_engagement').iterrows():
    print(f"{i+1}. [{row['sentiment_label'].upper()}] [{row['emotion_primary']}]")
    print(f"   Engagement: {row['total_engagement']:,.0f}")
    print(f"   {row['clean_text'][:200]}...")
    print()

print('\n' + '='*80)
print('CONCLUSION:')
print('='*80)
print("""
The high 'neutral' sentiment MAY be misleading because:
1. Many informational posts (news reports) are tagged as neutral
2. Emotional posts use indirect language that sentiment models miss
3. Context-dependent criticism might be classified as neutral

RECOMMENDATION: Look at EMOTION + NARRATIVE, not just sentiment:
- High 'love' emotion = Support for unity or individual parties
- 'anger' + 'negative' sentiment = Clear opposition to split
- 'fear' + conflict keywords = Worry about PN stability
""")
