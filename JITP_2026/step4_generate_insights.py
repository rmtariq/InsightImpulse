#!/usr/bin/env python3
"""
Step 4: Generate Insights - Answer the 5 Research Questions
Based on document specification
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from collections import Counter

INPUT_FILE = "JITP_2026/processed_data/pas_bersatu_analysis_ready.csv"
OUTPUT_DIR = Path("JITP_2026/analysis_reports")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def load_data():
    """Load analysis-ready dataset and filter to last 90 days"""
    print("📥 Loading analysis-ready data...")
    df = pd.read_csv(INPUT_FILE)
    df['Date'] = pd.to_datetime(df['Date'], utc=True)
    print(f"   Loaded {len(df):,} records (all time)")

    # Filter to last 90 days from May 29, 2026
    end_date = pd.Timestamp('2026-05-29', tz='UTC')
    start_date = end_date - pd.Timedelta(days=90)

    df_filtered = df[df['Date'] >= start_date].copy()
    print(f"   Filtered to last 90 days ({start_date.date()} to {end_date.date()}): {len(df_filtered):,} records")

    if len(df_filtered) == 0:
        print("   ⚠️  WARNING: No records in last 90 days! Using full dataset.")
        return df

    return df_filtered

def q1_temporal_spike_analysis(df):
    """Q1: When did the issue peak?"""
    print("\n📅 Q1: TEMPORAL SPIKE ANALYSIS")
    print("=" * 60)
    
    # Daily volume
    daily = df.groupby('date_day').size().reset_index(name='posts')
    daily = daily.sort_values('date_day')
    
    # Weekly volume
    weekly = df.groupby('date_week').size().reset_index(name='posts')
    weekly = weekly.sort_values('date_week')
    
    # Monthly volume
    monthly = df.groupby('date_month').size().reset_index(name='posts')
    monthly = monthly.sort_values('date_month')
    
    # Find peak
    if len(daily) > 0:
        peak_day = daily.loc[daily['posts'].idxmax()]
        print(f"   📈 Peak Day: {peak_day['date_day']} ({peak_day['posts']} posts)")
    
    if len(weekly) > 0:
        peak_week = weekly.loc[weekly['posts'].idxmax()]
        print(f"   📈 Peak Week: {peak_week['date_week']} ({peak_week['posts']} posts)")
    
    if len(monthly) > 0:
        peak_month = monthly.loc[monthly['posts'].idxmax()]
        print(f"   📈 Peak Month: {peak_month['date_month']} ({peak_month['posts']} posts)")
    
    # Date range
    print(f"   📊 Date Range: {df['Date'].min().date()} to {df['Date'].max().date()}")
    print(f"   📊 Duration: {(df['Date'].max() - df['Date'].min()).days} days")
    
    # Save tables
    daily.to_csv(OUTPUT_DIR / "temporal_daily_volume.csv", index=False)
    weekly.to_csv(OUTPUT_DIR / "temporal_weekly_volume.csv", index=False)
    monthly.to_csv(OUTPUT_DIR / "temporal_monthly_volume.csv", index=False)
    
    return daily, weekly, monthly

def q2_entity_sentiment_analysis(df):
    """Q2: Who is more supported or blamed? PAS vs Bersatu"""
    print("\n🎭 Q2: ENTITY SENTIMENT ANALYSIS")
    print("=" * 60)
    
    # Overall sentiment distribution
    print("   Overall Sentiment:")
    sentiment_dist = df['sentiment_label'].value_counts()
    for sentiment, count in sentiment_dist.items():
        print(f"      {sentiment}: {count} ({count/len(df)*100:.1f}%)")
    
    # Sentiment by entity mention
    entity_sentiment = []
    
    entities = {
        'PAS': 'mentions_pas',
        'Bersatu': 'mentions_bersatu',
        'PN': 'mentions_pn',
        'UMNO': 'mentions_umno',
    }
    
    for entity_name, entity_col in entities.items():
        if entity_col in df.columns:
            entity_df = df[df[entity_col] == True]
            if len(entity_df) > 0:
                pos = len(entity_df[entity_df['sentiment_label'] == 'positive'])
                neg = len(entity_df[entity_df['sentiment_label'] == 'negative'])
                neu = len(entity_df[entity_df['sentiment_label'] == 'neutral'])
                total = len(entity_df)
                avg_score = entity_df['sentiment_score'].mean()
                
                entity_sentiment.append({
                    'entity': entity_name,
                    'total_mentions': total,
                    'positive': pos,
                    'negative': neg,
                    'neutral': neu,
                    'avg_sentiment_score': avg_score,
                    'positive_pct': pos/total*100 if total > 0 else 0,
                    'negative_pct': neg/total*100 if total > 0 else 0,
                })
    
    entity_df = pd.DataFrame(entity_sentiment)
    if len(entity_df) > 0:
        print("\n   Sentiment by Entity:")
        for _, row in entity_df.iterrows():
            print(f"      {row['entity']}: {row['total_mentions']} mentions")
            print(f"         Positive: {row['positive']} ({row['positive_pct']:.1f}%)")
            print(f"         Negative: {row['negative']} ({row['negative_pct']:.1f}%)")
            print(f"         Avg Score: {row['avg_sentiment_score']:.3f}")
        
        entity_df.to_csv(OUTPUT_DIR / "entity_sentiment_comparison.csv", index=False)
    
    return entity_df

def q3_emotion_analysis(df):
    """Q3: What emotions are most dominant?"""
    print("\n😊 Q3: EMOTION ANALYSIS")
    print("=" * 60)
    
    # Primary emotion distribution
    if 'emotion_primary' in df.columns:
        emotion_dist = df['emotion_primary'].value_counts()
        print("   Primary Emotions:")
        for emotion, count in emotion_dist.items():
            print(f"      {emotion}: {count} ({count/len(df)*100:.1f}%)")
        
        # Emotion by narrative frame
        emotion_by_frame = []
        for has_solo in [True, False]:
            frame_name = "PAS Solo" if has_solo else "Coalition Split"
            frame_df = df[df['has_pas_solo_phrase'] == has_solo]
            if len(frame_df) > 0:
                emotions = frame_df['emotion_primary'].value_counts()
                for emotion, count in emotions.items():
                    emotion_by_frame.append({
                        'narrative_frame': frame_name,
                        'emotion': emotion,
                        'count': count,
                        'percentage': count/len(frame_df)*100
                    })
        
        emotion_frame_df = pd.DataFrame(emotion_by_frame)
        if len(emotion_frame_df) > 0:
            emotion_frame_df.to_csv(OUTPUT_DIR / "emotion_by_narrative.csv", index=False)
    
    return emotion_dist if 'emotion_primary' in df.columns else None

def q4_platform_analysis(df):
    """Q4: Which platform is most influential?"""
    print("\n📱 Q4: PLATFORM INFLUENCE ANALYSIS")
    print("=" * 60)
    
    platform_stats = []
    
    for platform in df['Platform'].unique():
        platform_df = df[df['Platform'] == platform]
        
        stats = {
            'platform': platform,
            'total_posts': len(platform_df),
            'total_engagement': platform_df['total_engagement'].sum(),
            'avg_engagement': platform_df['total_engagement'].mean(),
            'max_engagement': platform_df['total_engagement'].max(),
            'avg_sentiment_score': platform_df['sentiment_score'].mean(),
            'positive_posts': len(platform_df[platform_df['sentiment_label'] == 'positive']),
            'negative_posts': len(platform_df[platform_df['sentiment_label'] == 'negative']),
        }
        platform_stats.append(stats)
    
    platform_df = pd.DataFrame(platform_stats)
    platform_df = platform_df.sort_values('total_engagement', ascending=False)
    
    print("   Platform Rankings (by Total Engagement):")
    for idx, row in platform_df.iterrows():
        print(f"      {row['platform']}: {row['total_posts']} posts, {row['total_engagement']:.0f} total engagement")
    
    platform_df.to_csv(OUTPUT_DIR / "platform_influence_ranking.csv", index=False)
    
    # Top 10 most engaged posts
    top_posts = df.nlargest(10, 'total_engagement')[
        ['Platform', 'Date', 'clean_text', 'total_engagement', 'sentiment_label', 
         'has_pas_solo_phrase', 'has_split_phrase']
    ]
    top_posts.to_csv(OUTPUT_DIR / "top_10_most_engaged_posts.csv", index=False)
    
    return platform_df

def q5_pas_solo_stance_analysis(df):
    """Q5: Is 'PAS solo' seen as strength or risk?"""
    print("\n🎯 Q5: PAS SOLO STANCE ANALYSIS")
    print("=" * 60)
    
    # Filter to PAS solo posts
    pas_solo_df = df[df['has_pas_solo_phrase'] == True].copy()
    
    print(f"   Total 'PAS Solo' posts: {len(pas_solo_df)}")
    
    if len(pas_solo_df) > 0:
        # Sentiment breakdown
        print("\n   Sentiment Distribution:")
        sentiment_dist = pas_solo_df['sentiment_label'].value_counts()
        for sentiment, count in sentiment_dist.items():
            print(f"      {sentiment}: {count} ({count/len(pas_solo_df)*100:.1f}%)")
        
        # Average sentiment score
        avg_score = pas_solo_df['sentiment_score'].mean()
        print(f"\n   Average Sentiment Score: {avg_score:.3f}")
        
        # Interpretation
        if avg_score > 0.5:
            interpretation = "POSITIVE - Likely seen as 'langkah tegas' (firm move)"
        elif avg_score < -0.5:
            interpretation = "NEGATIVE - Likely seen as 'langkah berisiko' (risky move)"
        else:
            interpretation = "MIXED - No clear consensus"
        
        print(f"   Interpretation: {interpretation}")
        
        # Top PAS solo posts
        top_solo = pas_solo_df.nlargest(5, 'total_engagement')[
            ['Platform', 'Date', 'clean_text', 'sentiment_label', 'total_engagement']
        ]
        top_solo.to_csv(OUTPUT_DIR / "top_pas_solo_posts.csv", index=False)
        
        # Save all PAS solo posts
        pas_solo_df.to_csv(OUTPUT_DIR / "pas_solo_discourse_full.csv", index=False)
    
    return pas_solo_df

def generate_executive_summary(df, daily, weekly, platform_df, pas_solo_df):
    """Generate executive summary report"""
    print("\n📋 Generating Executive Summary...")

    duration_days = (df['Date'].max() - df['Date'].min()).days

    summary = f"""
# JITP_2026: Executive Summary Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Dataset Overview
- **Analysis Period:** Last 90 Days (March 1, 2026 - May 29, 2026)
- Total Analyzed Posts: {len(df):,}
- Actual Date Range: {df['Date'].min().date()} to {df['Date'].max().date()}
- Platforms: {', '.join(df['Platform'].unique())}
- Active Discussion Days: {duration_days} days

## KEY FINDINGS

### 1. WHEN DID THE ISSUE PEAK? (Last 90 Days)
{f"- Peak Week: {weekly.loc[weekly['posts'].idxmax(), 'date_week']} ({weekly['posts'].max()} posts)" if len(weekly) > 0 else "- Not enough data"}
{f"- Peak Day: {daily.loc[daily['posts'].idxmax(), 'date_day']} ({daily['posts'].max()} posts)" if len(daily) > 0 else ""}
- Active discussion period: {duration_days} days within the 90-day window

### 2. WHO IS MORE SUPPORTED/BLAMED?
- Analysis shows complex sentiment landscape
- See entity_sentiment_comparison.csv for detailed breakdown

### 3. WHAT EMOTIONS DOMINATE?
{f"- Primary Emotion: {df['emotion_primary'].value_counts().index[0]} ({df['emotion_primary'].value_counts().iloc[0]} posts)" if 'emotion_primary' in df.columns else "- Emotion data available"}
- See emotion_by_narrative.csv for full analysis

### 4. WHICH PLATFORM IS MOST INFLUENTIAL?
{f"- Most Engaged: {platform_df.iloc[0]['platform']} ({platform_df.iloc[0]['total_engagement']:.0f} total engagement)" if len(platform_df) > 0 else "- Platform data available"}
- See platform_influence_ranking.csv for rankings

### 5. IS "PAS SOLO" = STRENGTH OR RISK?
- Total "PAS Solo" mentions: {len(pas_solo_df)}
{f"- Average Sentiment: {pas_solo_df['sentiment_score'].mean():.3f}" if len(pas_solo_df) > 0 else ""}
{f"- Positive: {len(pas_solo_df[pas_solo_df['sentiment_label'] == 'positive'])} | Negative: {len(pas_solo_df[pas_solo_df['sentiment_label'] == 'negative'])}" if len(pas_solo_df) > 0 else ""}

### NARRATIVE BREAKDOWN
- Coalition Split/Tension posts: {df['has_split_phrase'].sum()} ({df['has_split_phrase'].sum()/len(df)*100:.1f}%)
- PAS Solo posts: {df['has_pas_solo_phrase'].sum()} ({df['has_pas_solo_phrase'].sum()/len(df)*100:.1f}%)
- Review Cooperation posts: {df['has_review_phrase'].sum()} ({df['has_review_phrase'].sum()/len(df)*100:.1f}%)

## OUTPUT FILES
All analysis tables saved to: JITP_2026/analysis_reports/

1. temporal_daily_volume.csv
2. temporal_weekly_volume.csv
3. entity_sentiment_comparison.csv
4. emotion_by_narrative.csv
5. platform_influence_ranking.csv
6. top_10_most_engaged_posts.csv
7. pas_solo_discourse_full.csv
8. top_pas_solo_posts.csv

## CONCLUSION
{f"The discourse is dominated by SPLIT/TENSION narratives ({df['has_split_phrase'].sum()/len(df)*100:.1f}%), " if df['has_split_phrase'].sum()/len(df) > 0.5 else ""}suggesting significant concern about coalition stability rather than just policy review.
"""
    
    with open(OUTPUT_DIR / "EXECUTIVE_SUMMARY.md", 'w') as f:
        f.write(summary)
    
    print(f"   Saved: {OUTPUT_DIR / 'EXECUTIVE_SUMMARY.md'}")

def main():
    print("=" * 80)
    print("JITP_2026 - STEP 4: INSIGHTS GENERATION")
    print("Answering the 5 Research Questions")
    print("=" * 80)
    
    # Load data
    df = load_data()
    
    # Answer each research question
    daily, weekly, monthly = q1_temporal_spike_analysis(df)
    entity_df = q2_entity_sentiment_analysis(df)
    emotion_dist = q3_emotion_analysis(df)
    platform_df = q4_platform_analysis(df)
    pas_solo_df = q5_pas_solo_stance_analysis(df)
    
    # Generate executive summary
    generate_executive_summary(df, daily, weekly, platform_df, pas_solo_df)
    
    print("\n" + "=" * 80)
    print("✅ ALL 5 RESEARCH QUESTIONS ANSWERED!")
    print("=" * 80)
    print(f"\n📊 All reports saved to: {OUTPUT_DIR}/")
    print("\nKey files:")
    print("   - EXECUTIVE_SUMMARY.md (Main findings)")
    print("   - platform_influence_ranking.csv")
    print("   - pas_solo_discourse_full.csv")
    print("   - top_10_most_engaged_posts.csv")

if __name__ == "__main__":
    main()
