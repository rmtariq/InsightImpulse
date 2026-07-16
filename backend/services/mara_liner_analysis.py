"""
Mara Liner Executive Intelligence Dashboard Generator
Transforms raw social listening data into decision-ready management intelligence
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import re
from collections import Counter
import json

class MaraLinerAnalyzer:
    """Executive-grade social listening analysis for Mara Liner management"""
    
    def __init__(self, csv_path):
        self.csv_path = csv_path
        self.df = None
        self.df_relevant = None
        self.analysis = {}
        
    def load_data(self):
        """Load and prepare dataset"""
        print("📊 Loading dataset...")
        self.df = pd.read_csv(self.csv_path)
        print(f"✅ Loaded {len(self.df)} total records")
        return self
        
    def detect_relevance(self):
        """Detect and filter content actually about Mara Liner bus operations"""
        print("\n🔍 Detecting relevance...")
        
        # Mara Liner relevant keywords
        mara_keywords = [
            'mara liner', 'maraliner', 'mara corp', 'maracorp',
            'bas mara', 'bas ekspres', 'mara sdn bhd',
            'naik bas', 'ticket', 'tiket', 'tempahan', 'booking',
            'route', 'laluan', 'perjalanan', 'journey',
            'driver', 'pemandu', 'customer service', 'delay', 'lewat',
            'cancel', 'batal', 'breakdown', 'rosak', 'accident', 'kemalangan',
            'terminal', 'hentian', 'stop', 'schedule', 'jadual',
            'fare', 'harga', 'promo', 'diskaun', 'discount',
            'kl-kt', 'kuala lumpur', 'terengganu', 'kelantan',
            'comfort', 'selesa', 'clean', 'bersih', 'aircond', 'toilet'
        ]
        
        def is_relevant(text):
            """Check if text is about Mara Liner services"""
            if pd.isna(text):
                return False
            text_lower = str(text).lower()
            
            # Must mention Mara Liner explicitly or be in context
            has_mara = any(kw in text_lower for kw in ['mara liner', 'maraliner', '#maraliner', '@maraliner'])
            has_bus_context = any(kw in text_lower for kw in ['bas', 'bus', 'express', 'ekspres', 'ticket', 'tiket'])
            
            # Filter out obvious noise
            noise_patterns = [
                'subscribe', 'follower', 'like and share', 'good morning', 'nice view',
                'content creator', 'views', 'upload', 'vlog', 'palm trees', 'tropics',
                'congrats', 'amazing shot', 'gabon', 'lucky charm', 'leading man'
            ]
            is_noise = any(pattern in text_lower for pattern in noise_patterns)
            
            return (has_mara or has_bus_context) and not is_noise
        
        self.df['is_relevant'] = self.df['Text'].apply(is_relevant)
        self.df_relevant = self.df[self.df['is_relevant']].copy()
        
        relevance_rate = len(self.df_relevant) / len(self.df) * 100
        print(f"✅ Relevant: {len(self.df_relevant)} ({relevance_rate:.1f}%)")
        print(f"❌ Noise: {len(self.df) - len(self.df_relevant)} ({100-relevance_rate:.1f}%)")
        
        return self
        
    def detect_duplicates(self):
        """Detect duplicate and near-duplicate content"""
        print("\n🔍 Detecting duplicates...")
        
        if len(self.df_relevant) == 0:
            print("⚠️ No relevant data to check for duplicates")
            self.df_relevant['is_duplicate'] = False
            return self
        
        # Mark exact duplicates
        self.df_relevant['is_duplicate'] = self.df_relevant.duplicated(subset=['Text'], keep='first')
        
        dup_count = self.df_relevant['is_duplicate'].sum()
        dup_rate = dup_count / len(self.df_relevant) * 100 if len(self.df_relevant) > 0 else 0
        
        print(f"✅ Duplicates found: {dup_count} ({dup_rate:.1f}%)")
        
        # Remove duplicates for analysis
        self.df_relevant = self.df_relevant[~self.df_relevant['is_duplicate']].copy()
        print(f"✅ Unique relevant records: {len(self.df_relevant)}")
        
        return self
        
    def classify_content(self):
        """Classify content into business-relevant categories"""
        print("\n📋 Classifying content...")
        
        if len(self.df_relevant) == 0:
            print("⚠️ No relevant data to classify")
            self.df_relevant['category'] = 'unknown'
            self.df_relevant['content_type'] = 'unknown'
            return self
        
        def categorize(text):
            """Assign business category"""
            if pd.isna(text):
                return 'unknown'
            text_lower = str(text).lower()
            
            # Priority order matters
            if any(kw in text_lower for kw in ['delay', 'lewat', 'late', 'tunggu', 'wait']):
                return 'service_complaint_delay'
            if any(kw in text_lower for kw in ['cancel', 'batal', 'breakdown', 'rosak', 'problem']):
                return 'service_complaint_cancellation'
            if any(kw in text_lower for kw in ['customer service', 'call', 'hotline', 'respond', 'reply']):
                return 'customer_service_issue'
            if any(kw in text_lower for kw in ['accident', 'kemalangan', 'safety', 'unsafe', 'dangerous']):
                return 'safety_incident'
            if any(kw in text_lower for kw in ['comfortable', 'selesa', 'clean', 'bersih', 'good service', 'excellent']):
                return 'service_praise'
            if any(kw in text_lower for kw in ['promo', 'discount', 'diskaun', 'rm43', 'malaysia10', 'offer']):
                return 'promotional_campaign'
            if any(kw in text_lower for kw in ['route', 'laluan', 'new service', 'bila ada bas', 'when will']):
                return 'route_demand'
            if any(kw in text_lower for kw in ['holiday', 'cuti', 'balik', 'raya', 'family']):
                return 'promotional_seasonal'
            
            return 'general_mention'
        
        def detect_content_type(row):
            """Detect if owned, earned, or news content"""
            author = str(row.get('author', '')).lower() if 'author' in row else ''
            text = str(row.get('Text', '')).lower()
            
            if 'maraliner' in author or 'mara liner' in author:
                return 'owned'
            elif any(kw in text for kw in ['news', 'announcement', 'press', 'media']):
                return 'news'
            else:
                return 'earned_public'
        
        self.df_relevant['category'] = self.df_relevant['Text'].apply(categorize)
        self.df_relevant['content_type'] = self.df_relevant.apply(detect_content_type, axis=1)
        
        print(f"✅ Content classified into {self.df_relevant['category'].nunique()} categories")
        print(f"✅ Content types: {self.df_relevant['content_type'].value_counts().to_dict()}")

        return self

    def generate_executive_snapshot(self):
        """Generate executive snapshot section"""
        print("\n📸 Generating executive snapshot...")

        if len(self.df) == 0:
            return {
                'total_mentions': 0,
                'relevant_mentions': 0,
                'noise_rate': 0,
                'duplicate_rate': 0,
                'message': 'No data available'
            }

        snapshot = {
            'total_raw_mentions': len(self.df),
            'total_relevant_mentions': len(self.df_relevant),
            'irrelevant_noise_rate': f"{((len(self.df) - len(self.df_relevant)) / len(self.df) * 100):.1f}%",
            'duplicate_rate': f"{(self.df_relevant['is_duplicate'].sum() / len(self.df) * 100):.1f}%" if len(self.df_relevant) > 0 else "0%",
            'platform_distribution': self.df_relevant['Platform'].value_counts().to_dict() if len(self.df_relevant) > 0 else {},
            'content_type_split': self.df_relevant['content_type'].value_counts().to_dict() if len(self.df_relevant) > 0 else {},
            'time_period': f"{self.df['Date'].min()} to {self.df['Date'].max()}" if 'Date' in self.df.columns and not self.df['Date'].isna().all() else "Date range unavailable",
            'language_mix': self.df_relevant['detected_language'].value_counts().to_dict() if 'detected_language' in self.df_relevant.columns and len(self.df_relevant) > 0 else {}
        }

        self.analysis['executive_snapshot'] = snapshot
        return self

    def generate_management_signals(self):
        """Generate top management signal summary"""
        print("\n🎯 Generating management signals...")

        if len(self.df_relevant) == 0:
            self.analysis['management_signals'] = []
            return self

        # Group by category and analyze
        category_analysis = []

        for category in self.df_relevant['category'].unique():
            cat_data = self.df_relevant[self.df_relevant['category'] == category]

            if len(cat_data) == 0:
                continue

            # Calculate metrics
            volume = len(cat_data)
            avg_sentiment = cat_data['sentiment_score'].mean() if 'sentiment_score' in cat_data.columns else 0.5
            total_engagement = cat_data['total_engagement'].sum() if 'total_engagement' in cat_data.columns else 0

            # Get example posts (top 3 by engagement)
            examples = cat_data.nlargest(3, 'total_engagement' if 'total_engagement' in cat_data.columns else 'likes')[['Text', 'Platform', 'sentiment_label']].to_dict('records') if len(cat_data) > 0 else []

            # Determine severity based on category and sentiment
            severity = 'medium'
            if 'complaint' in category or 'issue' in category or 'safety' in category:
                severity = 'high' if avg_sentiment < 0.4 else 'medium'
            elif 'praise' in category:
                severity = 'low'

            category_analysis.append({
                'theme': category.replace('_', ' ').title(),
                'volume': volume,
                'engagement': int(total_engagement),
                'sentiment': f"{avg_sentiment:.2f}",
                'severity': severity,
                'trend': 'stable',  # Would need time series for actual trend
                'examples': examples[:2]  # Top 2 examples
            })

        # Sort by business relevance (severity + volume)
        severity_weight = {'high': 3, 'medium': 2, 'low': 1}
        category_analysis.sort(key=lambda x: (severity_weight[x['severity']], x['volume']), reverse=True)

        self.analysis['management_signals'] = category_analysis[:5]  # Top 5
        return self

    def analyze(self):
        """Run complete analysis pipeline"""
        print("="*60)
        print("🎯 MARA LINER EXECUTIVE INTELLIGENCE ANALYSIS")
        print("="*60)

        self.load_data()
        self.detect_relevance()
        self.detect_duplicates()
        self.classify_content()
        self.generate_executive_snapshot()
        self.generate_management_signals()

        print("\n✅ Analysis complete!")
        return self.analysis

    def print_executive_snapshot(self):
        """Print executive snapshot in readable format"""
        snapshot = self.analysis.get('executive_snapshot', {})

        print("\n" + "="*60)
        print("📊 EXECUTIVE SNAPSHOT")
        print("="*60)
        print(f"Total Raw Mentions: {snapshot.get('total_raw_mentions', 0):,}")
        print(f"Relevant Mentions: {snapshot.get('total_relevant_mentions', 0):,}")
        print(f"Noise Rate: {snapshot.get('irrelevant_noise_rate', '0%')}")
        print(f"Duplicate Rate: {snapshot.get('duplicate_rate', '0%')}")
        print(f"\nPlatform Distribution:")
        for platform, count in snapshot.get('platform_distribution', {}).items():
            print(f"  {platform}: {count}")
        print(f"\nContent Type Split:")
        for ctype, count in snapshot.get('content_type_split', {}).items():
            print(f"  {ctype}: {count}")
        print(f"\nTime Period: {snapshot.get('time_period', 'N/A')}")

    def print_management_signals(self):
        """Print management signals in readable format"""
        signals = self.analysis.get('management_signals', [])

        print("\n" + "="*60)
        print("🎯 TOP MANAGEMENT SIGNALS")
        print("="*60)

        for i, signal in enumerate(signals, 1):
            print(f"\n{i}. {signal['theme']}")
            print(f"   Volume: {signal['volume']} | Engagement: {signal['engagement']} | Sentiment: {signal['sentiment']}")
            print(f"   Severity: {signal['severity'].upper()} | Trend: {signal['trend']}")
            if signal.get('examples'):
                print(f"   Examples:")
                for ex in signal['examples'][:1]:  # Just first example
                    text_preview = ex['Text'][:100] + "..." if len(ex['Text']) > 100 else ex['Text']
                    print(f"     - [{ex['Platform']}] {text_preview}")
