#!/usr/bin/env python3
"""
Enhanced Intelligence Analysis with OpenAI GPT-4
Provides strategic insights and recommendations for Mara Liner
"""

import os
import json
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import OpenAI
try:
    import openai
    openai.api_key = os.getenv('OPENAI_API_KEY')
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("⚠️ OpenAI not available. Install: pip install openai")


class EnhancedIntelligence:
    def __init__(self, df, topic_name):
        self.df = df
        self.topic_name = topic_name
        self.insights = {}
    
    def analyze_sentiment_breakdown(self):
        """Analyze sentiment distribution"""
        # Check for sentiment_label column (used by our sentiment analyzer)
        sentiment_col = 'sentiment_label' if 'sentiment_label' in self.df.columns else 'Sentiment'

        sentiment_counts = self.df[sentiment_col].value_counts().to_dict() if sentiment_col in self.df.columns else {}

        total = sum(sentiment_counts.values())
        sentiment_pct = {k: round(v/total*100, 1) for k, v in sentiment_counts.items()} if total > 0 else {}

        return {
            'counts': sentiment_counts,
            'percentages': sentiment_pct,
            'total': total
        }
    
    def analyze_emotion_breakdown(self):
        """Analyze emotion distribution"""
        # Check for emotion_primary column (used by our sentiment analyzer)
        emotion_col = 'emotion_primary' if 'emotion_primary' in self.df.columns else 'Emotion'

        emotion_counts = self.df[emotion_col].value_counts().to_dict() if emotion_col in self.df.columns else {}

        total = sum(emotion_counts.values())
        emotion_pct = {k: round(v/total*100, 1) for k, v in emotion_counts.items()} if total > 0 else {}

        return {
            'counts': emotion_counts,
            'percentages': emotion_pct,
            'total': total
        }
    
    def analyze_platform_breakdown(self):
        """Detailed platform analysis"""
        platform_stats = {}

        # Check for column names
        sentiment_col = 'sentiment_label' if 'sentiment_label' in self.df.columns else 'Sentiment'
        engagement_col = 'total_engagement' if 'total_engagement' in self.df.columns else 'Engagement'

        if 'Platform' in self.df.columns:
            for platform in self.df['Platform'].unique():
                platform_df = self.df[self.df['Platform'] == platform]

                platform_stats[platform] = {
                    'count': len(platform_df),
                    'sentiment': platform_df[sentiment_col].value_counts().to_dict() if sentiment_col in platform_df.columns else {},
                    'avg_engagement': platform_df[engagement_col].mean() if engagement_col in platform_df.columns else 0
                }

        return platform_stats
    
    def get_top_posts(self, n=5):
        """Get top posts by engagement"""
        engagement_col = 'total_engagement' if 'total_engagement' in self.df.columns else 'Engagement'
        sentiment_col = 'sentiment_label' if 'sentiment_label' in self.df.columns else 'Sentiment'

        if engagement_col not in self.df.columns:
            return []

        cols = ['Text', 'Platform', sentiment_col, engagement_col]
        top = self.df.nlargest(n, engagement_col)[cols].to_dict('records')
        # Rename columns for consistency
        top = [{**record, 'Sentiment': record.pop(sentiment_col, 'unknown'), 'Engagement': record.pop(engagement_col, 0)} for record in top]
        return top
    
    def get_sentiment_examples(self):
        """Get example posts for each sentiment"""
        examples = {}

        sentiment_col = 'sentiment_label' if 'sentiment_label' in self.df.columns else 'Sentiment'

        if sentiment_col in self.df.columns:
            for sentiment in ['positive', 'negative', 'neutral']:
                sentiment_df = self.df[self.df[sentiment_col] == sentiment]
                if len(sentiment_df) > 0:
                    sample = sentiment_df.head(3)[['Text', 'Platform']].to_dict('records')
                    examples[sentiment] = sample

        return examples
    
    async def generate_ai_insights(self):
        """Generate strategic insights using GPT-4"""
        if not OPENAI_AVAILABLE or not openai.api_key:
            return {
                'available': False,
                'message': 'OpenAI API not configured'
            }
        
        # Prepare data summary for GPT-4
        sentiment_breakdown = self.analyze_sentiment_breakdown()
        emotion_breakdown = self.analyze_emotion_breakdown()
        platform_breakdown = self.analyze_platform_breakdown()
        top_posts = self.get_top_posts()
        
        # Malaysian Social Media Market Context (2026 Data)
        market_context = """
KONTEKS PASARAN MALAYSIA 2026:
- TikTok adalah platform UTAMA di Malaysia dengan 30.7 juta pengguna (18+ tahun)
- TikTok mempunyai engagement TERTINGGI: 38 jam 49 minit sebulan per pengguna
- TikTok menjangkau 114.8% daripada semua dewasa Malaysia (multi-account)
- 60% Gen Z Malaysia bermula carian produk di TikTok/Instagram, BUKAN Google
- Facebook: 31.9M pengguna (terbesar tapi engagement rendah)
- Instagram: 16.9M pengguna (popular untuk visual content)
- X (Twitter): 10M+ pengguna (berita dan diskusi)

STRATEGI PLATFORM UNTUK SYARIKAT PENGANGKUTAN:
- TikTok: Konten video pendek, behind-the-scenes, customer stories, trending challenges
- Instagram: Visual branding, customer testimonials, route highlights
- Facebook: Customer service, announcements, group discussions
- X: Real-time updates, customer complaints, news sharing
"""

        prompt = f"""
Anda adalah pakar strategi perniagaan untuk syarikat pengangkutan Malaysia dengan kepakaran mendalam dalam pemasaran digital Malaysia.

{market_context}

ANALISIS DATA MEDIA SOSIAL UNTUK {self.topic_name}:

DATA SUMMARY:
- Total posts: {len(self.df)}
- Sentiment: {json.dumps(sentiment_breakdown['percentages'], indent=2)}
- Emotion: {json.dumps(emotion_breakdown['percentages'], indent=2)}
- Platform Breakdown: {json.dumps(platform_breakdown, indent=2)}

TOP ENGAGEMENT POSTS:
{json.dumps(top_posts[:3], indent=2)}

TUGASAN:
Berdasarkan data di atas DAN konteks pasaran Malaysia 2026, berikan analisis strategik dalam Bahasa Malaysia yang merangkumi:

1. RINGKASAN EKSEKUTIF (2-3 ayat)
   - WAJIB sebut platform dengan engagement tertinggi berdasarkan DATA
   - Jika TikTok ada dalam data, tekankan ia sebagai platform utama di Malaysia

2. ISU KRITIKAL (array of strings, jika ada isu negatif atau komplain)
   - Fokus kepada isu yang perlu tindakan segera

3. PELUANG PERNIAGAAN (array of strings)
   - Peluang berdasarkan trend platform dan sentimen positif

4. SENTIMENT & EMOSI PELANGGAN (string)
   - Analisis mendalam tentang perasaan pelanggan

5. CADANGAN STRATEGIK (array of strings - minimum 5 cadangan konkrit dan actionable)
   - Fokus kepada platform yang sesuai dengan pasaran Malaysia
   - Berikan cadangan spesifik untuk setiap platform

6. LANGKAH SETERUSNYA (object dengan high_priority, medium_priority, low_priority arrays)
   - high_priority: 3-4 tindakan SEGERA (fokus TikTok jika ada dalam data)
   - medium_priority: 3-4 tindakan jangka sederhana
   - low_priority: 2-3 tindakan jangka panjang

Format dalam JSON dengan keys: executive_summary, critical_issues, opportunities, customer_sentiment, strategic_recommendations, next_steps

CONTOH FORMAT next_steps:
{{
  "next_steps": {{
    "high_priority": ["Tindakan 1", "Tindakan 2", "Tindakan 3"],
    "medium_priority": ["Tindakan 1", "Tindakan 2"],
    "low_priority": ["Tindakan 1", "Tindakan 2"]
  }}
}}
"""
        
        try:
            from openai import OpenAI
            client = OpenAI(api_key=openai.api_key)

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Anda adalah pakar strategi perniagaan pengangkutan Malaysia yang berpengalaman. PENTING: Berikan response dalam format JSON yang sah sahaja, tanpa markdown atau teks tambahan."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000,
                response_format={"type": "json_object"}
            )

            content = response.choices[0].message.content

            # Remove markdown code blocks if present
            if content.strip().startswith('```'):
                # Extract JSON from markdown code block
                content = content.strip()
                if content.startswith('```json'):
                    content = content[7:]  # Remove ```json
                elif content.startswith('```'):
                    content = content[3:]  # Remove ```
                if content.endswith('```'):
                    content = content[:-3]  # Remove closing ```
                content = content.strip()

            ai_insights = json.loads(content)
            ai_insights['available'] = True

            return ai_insights

        except Exception as e:
            print(f"❌ OpenAI Error: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                'available': False,
                'error': str(e)
            }
    
    def generate_full_analysis(self):
        """Generate complete analysis"""
        return {
            'sentiment_breakdown': self.analyze_sentiment_breakdown(),
            'emotion_breakdown': self.analyze_emotion_breakdown(),
            'platform_breakdown': self.analyze_platform_breakdown(),
            'top_posts': self.get_top_posts(10),
            'sentiment_examples': self.get_sentiment_examples()
        }
