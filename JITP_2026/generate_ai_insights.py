#!/usr/bin/env python3
"""
AI-Powered Strategic Insights Generator for PAS
Using OpenAI GPT-4 or Anthropic Claude to analyze political data
"""

import os
import json
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# File paths
INPUT_FILE = "JITP_2026/processed_data/pas_bersatu_split_posts_deduped.csv"
DASHBOARD_JSON = "static/pas_dashboard_data.json"
OUTPUT_FILE = "static/pas_ai_insights.json"

def load_dashboard_data():
    """Load dashboard data for AI analysis"""
    print("📥 Loading dashboard data...")
    with open(DASHBOARD_JSON, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"   ✅ Loaded dashboard stats")
    return data

def load_sample_posts():
    """Load top viral posts for AI context"""
    print("📥 Loading sample posts...")
    df = pd.read_csv(INPUT_FILE)
    
    # Get top 10 most engaged posts
    df['total_engagement'] = pd.to_numeric(df['total_engagement'], errors='coerce').fillna(0)
    top_posts = df.nlargest(10, 'total_engagement')[['clean_text', 'total_engagement', 'sentiment_label', 'emotion_primary']].to_dict('records')
    
    print(f"   ✅ Loaded {len(top_posts)} top posts")
    return top_posts

def create_analysis_prompt(dashboard_data, top_posts):
    """Create comprehensive prompt for AI analysis"""
    
    stats = dashboard_data['stats']
    sentiment = dashboard_data['sentiment']
    emotions = dashboard_data['emotions']
    narratives = dashboard_data['narratives']
    
    prompt = f"""Anda adalah pakar strategi politik Malaysia yang berpengalaman dalam analisis data media sosial. Berdasarkan data analisis pergolakan PAS-Bersatu dalam Perikatan Nasional, berikan STRATEGI MENANG untuk PAS bagi PRN dan PRU16.

## DATA ANALISIS (90 Hari Terakhir: 1 Mac - 30 Mei 2026)

### Statistik Utama:
- Total Data Dikumpul: {stats.get('total_original', 0):,} records (dari semua 6 query)
- Total Posts Dianalisis: {stats.get('posts', 0):,} posts (90 hari terakhir)
- **TOTAL ENGAGEMENT: 136.3 JUTA** (136,349,751) - MASSIVE viral reach!

### Sentimen Awam (RAW CRAWLED DATA):
- **Neutral: {sentiment.get('neutral', 0):,} (48.7%)** ← PELUANG! Rakyat belum decide
- Negative: {sentiment.get('negative', 0):,} (31.8%)
- Positive: {sentiment.get('positive', 0):,} (19.6%)

### Emosi Dominan (EMOTIONAL ATTACHMENT masih ada):
- **LOVE: 2,725 posts** ← Highest emotion! Unity narrative potential
{', '.join([f"{k}: {v}" for k, v in list(emotions.items())[1:5]])}

### Naratif Politik:
- **PAS Solo: {narratives.get('PAS Solo', 0)} mentions (65%)** ← Dominan! Rakyat tertarik dengan PAS autonomy
- Perpecahan/Split: {narratives.get('Perpecahan', 0)} mentions (35%)

### KEY INSIGHT - THE PARADOX:
**"Ramai SUKA idea PAS solo (prinsip teguh), TETAPI untuk MENANG PAS mesti bersatu dalam PN"**

- Query "PAS solo": 61.2% NEUTRAL (bukan penolakan!)
- Query "Perpecahan": 46.2% NEGATIVE (rakyat BENCI konflik)
- Posts dengan "desak": 77.8% NEGATIVE (pressure dari Bersatu dilihat negatif)

## TUGAS ANDA:

Berikan analisis strategik BERDASARKAN PARADOX ini: "PAS solo popular tetapi tidak praktikal untuk menang"

**FRAMEWORK STRATEGI:**
"PAS SOLO dalam PRINSIP, BERSATU dalam POLITIK"

Berikan cadangan yang ACTIONABLE dalam format berikut:

1. **THE WINNING FORMULA: "PAS KUAT, PN MENANG"**
   - Bagaimana PAS boleh maintain autonomy TETAPI remain dalam PN
   - Positioning: "PAS adalah nakhoda PN, bukan hamba"
   - Framing: "Prinsip teguh + Coalition strategik = Kemenangan"

2. **DUAL-TRACK MESSAGING STRATEGY**
   - **Track A (PAS Hardcore)**: "PAS berprinsip, tidak dikongkong"
   - **Track B (Moderates)**: "PN untuk semua - Melayu, Cina (GERAKAN), India"
   - Bagaimana balance kedua-dua messaging

3. **LEVERAGE 48.7% NEUTRAL SENTIMENT**
   - Ini adalah PELUANG EMAS (rakyat belum decide)
   - Strategi convert NEUTRAL → POSITIVE
   - AVOID triggering NEUTRAL → NEGATIVE (perpecahan narrative)

4. **PLATFORM-SPECIFIC EXECUTION**
   - TikTok (40%): Viral short content - "Kenapa PAS kuat dalam PN"
   - YouTube (30%): Longform explanation - Policy, history
   - X/Twitter (15%): Real-time response to attacks

5. **MULTIRACIAL PN STRATEGY**
   - Emphasize GERAKAN (Cina moderate), MIC (India)
   - Counter DAP's "PN = Melayu sahaja" narrative
   - Show "PN untuk semua rakyat Malaysia"

6. **30/60/90 DAY ACTION PLAN**
   - 30 hari: Crisis control, stop the bleeding
   - 60 hari: Rebuild trust, convert neutrals
   - 90 hari: Prepare for PRN, solidify as PN leader

7. **TOP 5 PRIORITY ACTIONS** (What PAS MUST do NOW)

Format response dalam Bahasa Malaysia yang PRAKTIKAL, BOLD, dan MUDAH dilaksanakan oleh team komunikasi PAS."""

    return prompt

def generate_insights_openai(prompt):
    """Generate insights using OpenAI GPT-4"""
    try:
        from openai import OpenAI
        
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        print("🤖 Generating insights with OpenAI GPT-4o...")
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Anda adalah pakar strategi politik Malaysia yang berpengalaman."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=4000
        )
        
        insights = response.choices[0].message.content
        print(f"   ✅ Generated {len(insights)} characters of insights")
        return insights, "OpenAI GPT-4o"
        
    except Exception as e:
        print(f"   ❌ OpenAI Error: {e}")
        return None, None

def generate_insights_anthropic(prompt):
    """Generate insights using Anthropic Claude"""
    try:
        import anthropic
        
        client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
        
        print("🤖 Generating insights with Anthropic Claude-3.5-Sonnet...")
        
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=4000,
            temperature=0.7,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        insights = response.content[0].text
        print(f"   ✅ Generated {len(insights)} characters of insights")
        return insights, "Anthropic Claude-3.5-Sonnet"
        
    except Exception as e:
        print(f"   ❌ Anthropic Error: {e}")
        return None, None

def main():
    print("=" * 80)
    print("AI-POWERED STRATEGIC INSIGHTS GENERATOR FOR PAS")
    print("=" * 80)
    
    # Load data
    dashboard_data = load_dashboard_data()
    top_posts = load_sample_posts()
    
    # Create prompt
    prompt = create_analysis_prompt(dashboard_data, top_posts)
    
    # Try OpenAI first, fallback to Anthropic
    insights, model_used = generate_insights_openai(prompt)
    
    if not insights:
        insights, model_used = generate_insights_anthropic(prompt)
    
    if not insights:
        print("❌ Failed to generate insights with both OpenAI and Anthropic")
        return
    
    # Save insights
    output_data = {
        "model_used": model_used,
        "generated_at": pd.Timestamp.now().isoformat(),
        "insights": insights,
        "data_summary": {
            "total_original": dashboard_data['stats'].get('total_original'),
            "total_posts": dashboard_data['stats'].get('posts'),
            "date_range": "1 Mac 2026 - 30 Mei 2026",
            "sentiment": dashboard_data['sentiment'],
            "narratives": dashboard_data['narratives']
        }
    }
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Insights saved to: {OUTPUT_FILE}")
    print(f"🤖 Model used: {model_used}")
    print(f"\n📊 Preview:\n{insights[:500]}...\n")

if __name__ == "__main__":
    main()
