"""
Universal Intelligence Dashboard Generator
Transforms raw social listening data into executive-ready insights for ANY brand/topic
Designed to be clear, actionable, and suitable for all stakeholders from CEO to operations
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import re
from collections import Counter
import json
from typing import Dict, List, Tuple, Any

class UniversalIntelligenceDashboard:
    """
    Universal analytics engine that adapts to any brand/topic
    Provides clear, actionable insights suitable for all stakeholders
    """
    
    def __init__(self, csv_path: str, topic_name: str = "Brand"):
        self.csv_path = csv_path
        self.topic_name = topic_name
        self.df = None
        self.df_relevant = None
        self.insights = {}
        
    def load_data(self):
        """Load and validate dataset"""
        print(f"📊 Loading data for: {self.topic_name}")
        self.df = pd.read_csv(self.csv_path)
        
        # Parse dates
        if 'Date' in self.df.columns:
            self.df['Date'] = pd.to_datetime(self.df['Date'], errors='coerce')
        
        print(f"✅ Loaded {len(self.df)} total records")
        return self
    
    def detect_relevance(self):
        """Intelligently detect which content is actually about the topic"""
        print("\n🔍 Detecting relevant content...")
        
        # Auto-generate topic keywords from topic name
        topic_words = self.topic_name.lower().split()
        base_keywords = [self.topic_name.lower()]
        
        # Add variations without spaces
        base_keywords.append(''.join(topic_words))
        base_keywords.append('#' + ''.join(topic_words))
        base_keywords.append('@' + ''.join(topic_words))
        
        # Generic noise patterns (universal across all topics)
        noise_patterns = [
            'subscribe', 'follower', 'like and share', 'good morning', 'nice view',
            'content creator', 'upload', 'vlog', 'palm trees', 'tropics',
            'congrats', 'amazing shot', 'lucky charm', 'leading man', 'giveaway',
            'follow back', 'dm me', 'check my bio', 'link in bio', 'click here',
            'buy now', 'limited time', 'subscribe now', 'turn on notifications'
        ]
        
        def is_relevant(row):
            """Check if content is genuinely about the topic"""
            text = str(row.get('Text', ''))
            author = str(row.get('author', ''))
            
            if pd.isna(text) or len(text.strip()) < 10:
                return False
            
            text_lower = text.lower()
            author_lower = author.lower()
            
            # Check if topic is mentioned
            has_topic = any(kw in text_lower or kw in author_lower for kw in base_keywords)
            
            # Check for noise
            is_noise = any(pattern in text_lower for pattern in noise_patterns)
            
            # Check if it's just a generic social media post
            generic_post = len(text) < 50 and any(word in text_lower for word in ['good morning', 'hello', 'hi everyone'])
            
            return has_topic and not is_noise and not generic_post
        
        self.df['is_relevant'] = self.df.apply(is_relevant, axis=1)
        self.df_relevant = self.df[self.df['is_relevant']].copy()
        
        relevance_rate = len(self.df_relevant) / len(self.df) * 100 if len(self.df) > 0 else 0
        
        print(f"✅ Relevant: {len(self.df_relevant):,} ({relevance_rate:.1f}%)")
        print(f"🗑️  Filtered noise: {len(self.df) - len(self.df_relevant):,} ({100-relevance_rate:.1f}%)")
        
        return self
    
    def remove_duplicates(self):
        """Remove exact and near-duplicates"""
        print("\n🔍 Removing duplicates...")
        
        if len(self.df_relevant) == 0:
            print("⚠️  No relevant data")
            return self
        
        initial_count = len(self.df_relevant)
        
        # Remove exact text duplicates
        self.df_relevant = self.df_relevant.drop_duplicates(subset=['Text'], keep='first')
        
        duplicates_removed = initial_count - len(self.df_relevant)
        print(f"✅ Removed {duplicates_removed:,} duplicates")
        print(f"✅ Clean dataset: {len(self.df_relevant):,} unique records")
        
        return self
    
    def filter_date_range(self, days: int = 90):
        """Filter to recent data only - keeps records without dates"""
        print(f"\n📅 Filtering to last {days} days...")

        if len(self.df_relevant) == 0 or 'Date' not in self.df_relevant.columns:
            print("⚠️  No date filtering applied")
            return self

        initial_count = len(self.df_relevant)

        # Separate data with and without dates
        has_dates = self.df_relevant[self.df_relevant['Date'].notna()].copy()
        no_dates = self.df_relevant[self.df_relevant['Date'].isna()].copy()

        print(f"  📊 {len(has_dates)} records with dates, {len(no_dates)} without dates")

        if len(has_dates) == 0:
            print("⚠️  No data with valid dates - keeping all data")
            return self

        # Ensure Date column is datetime type
        if not pd.api.types.is_datetime64_any_dtype(has_dates['Date']):
            print("  🔄 Converting Date column to datetime...")
            has_dates['Date'] = pd.to_datetime(has_dates['Date'], errors='coerce')
            # Remove any rows where date conversion failed
            has_dates = has_dates[has_dates['Date'].notna()].copy()

        # Filter only the records with dates
        cutoff_date = pd.Timestamp(datetime.now() - timedelta(days=days))

        # Handle timezone-aware and timezone-naive dates
        try:
            recent_data = has_dates[has_dates['Date'] >= cutoff_date]
        except TypeError:
            # If timezone mismatch, make both timezone-aware or both naive
            try:
                if has_dates['Date'].dt.tz is not None:
                    cutoff_date = cutoff_date.tz_localize('UTC')
                else:
                    # Make cutoff_date timezone-naive
                    cutoff_date = cutoff_date.replace(tzinfo=None)
            except Exception as e:
                print(f"  ⚠️  Timezone handling warning: {e}")
                # Fallback: convert both to naive
                has_dates['Date'] = has_dates['Date'].dt.tz_localize(None) if has_dates['Date'].dt.tz is not None else has_dates['Date']
                cutoff_date = cutoff_date.replace(tzinfo=None)
            recent_data = has_dates[has_dates['Date'] >= cutoff_date]

        # Combine recent dated data + all undated data (like TikTok)
        self.df_relevant = pd.concat([recent_data, no_dates], ignore_index=True)

        filtered_count = initial_count - len(self.df_relevant)
        print(f"✅ Kept recent data: {len(self.df_relevant):,} records")
        print(f"   ({len(recent_data)} dated + {len(no_dates)} undated)")
        print(f"🗑️  Filtered old data: {filtered_count:,} records")

        return self

    def classify_content(self):
        """Universal content classification that adapts to any topic"""
        print("\n📋 Classifying content by business meaning...")

        if len(self.df_relevant) == 0:
            print("⚠️  No data to classify")
            return self

        # Vectorized classification using string contains (MUCH faster)
        text_lower = self.df_relevant['Text'].fillna('').str.lower()

        # Initialize all as general_mention
        self.df_relevant['category'] = 'general_mention'

        # 1. Complaints & Issues (HIGH PRIORITY) - check last (highest priority)
        complaint_pattern = 'delay|late|cancel|problem|issue|complaint|disappointed|angry|frustrated|terrible|worst|never again|refund|poor service|bad experience|not working|broken|failed'
        mask_complaint = text_lower.str.contains(complaint_pattern, regex=True, na=False)

        # 2. Praise & Positive Feedback
        praise_pattern = 'excellent|great|amazing|awesome|love|best|perfect|thank you|appreciate|recommend|satisfied|happy with|good service|well done|fantastic|outstanding'
        mask_praise = text_lower.str.contains(praise_pattern, regex=True, na=False)

        # 3. Questions & Requests
        question_pattern = r'\?|^how |^when |^where |^what |^which |can i |do you '
        mask_question = text_lower.str.contains(question_pattern, regex=True, na=False)

        # 4. Promotional Response
        promo_pattern = 'promo|discount|offer|sale|deal|campaign|%|free|win|contest|giveaway'
        mask_promo = text_lower.str.contains(promo_pattern, regex=True, na=False)

        # 5. Feature Request / Suggestion
        request_pattern = 'please add|suggest|would be nice|hope you|request|can you make|need|want|wish|should have'
        mask_request = text_lower.str.contains(request_pattern, regex=True, na=False)

        # Apply in reverse priority order
        self.df_relevant.loc[mask_request, 'category'] = 'feature_request'
        self.df_relevant.loc[mask_promo, 'category'] = 'promotional_response'
        self.df_relevant.loc[mask_question, 'category'] = 'question_request'
        self.df_relevant.loc[mask_praise, 'category'] = 'praise_positive'
        self.df_relevant.loc[mask_complaint, 'category'] = 'complaint_issue'  # Highest priority last

        # Content owner detection (vectorized)
        author_lower = self.df_relevant['author'].fillna('').str.lower()
        topic_words = '|'.join(self.topic_name.lower().split())

        mask_owned = author_lower.str.contains(topic_words, regex=True, na=False)
        mask_news = text_lower.str.contains('news|report|announcement|press|statement', regex=True, na=False)

        self.df_relevant['content_owner'] = 'public_earned'
        self.df_relevant.loc[mask_news, 'content_owner'] = 'news_media'
        self.df_relevant.loc[mask_owned, 'content_owner'] = 'owned'

        # Add sentiment-based priority (vectorized)
        engagement = self.df_relevant['total_engagement'].fillna(0)

        self.df_relevant['priority'] = 'low'

        # Apply priority rules (from low to high)
        mask_feature_req = self.df_relevant['category'] == 'feature_request'
        mask_question = self.df_relevant['category'] == 'question_request'
        mask_complaint = self.df_relevant['category'] == 'complaint_issue'
        mask_praise_high = (self.df_relevant['category'] == 'praise_positive') & (engagement > 100)
        mask_complaint_high = mask_complaint & (engagement > 10)

        self.df_relevant.loc[mask_feature_req, 'priority'] = 'medium'
        self.df_relevant.loc[mask_question, 'priority'] = 'medium'
        self.df_relevant.loc[mask_complaint, 'priority'] = 'high'
        self.df_relevant.loc[mask_praise_high, 'priority'] = 'opportunity'
        self.df_relevant.loc[mask_complaint_high, 'priority'] = 'critical'

        print(f"✅ Content classified into {self.df_relevant['category'].nunique()} categories")
        print(f"✅ Priority levels assigned")

        return self

    def generate_executive_snapshot(self):
        """Generate clear executive summary"""
        print("\n📸 Generating executive snapshot...")

        if len(self.df_relevant) == 0:
            self.insights['executive_snapshot'] = {'status': 'no_data'}
            return self

        snapshot = {
            'topic': self.topic_name,
            'analysis_date': datetime.now().strftime('%Y-%m-%d'),
            'data_quality': {
                'total_raw_records': len(self.df),
                'relevant_records': len(self.df_relevant),
                'noise_filtered': len(self.df) - len(self.df_relevant),
                'data_quality_score': f"{(len(self.df_relevant) / len(self.df) * 100):.1f}%"
            },
            'time_coverage': {
                'earliest_date': self.df_relevant['Date'].min().strftime('%Y-%m-%d') if 'Date' in self.df_relevant.columns else 'N/A',
                'latest_date': self.df_relevant['Date'].max().strftime('%Y-%m-%d') if 'Date' in self.df_relevant.columns else 'N/A',
                'days_covered': (self.df_relevant['Date'].max() - self.df_relevant['Date'].min()).days if 'Date' in self.df_relevant.columns else 0
            },
            'platform_breakdown': self.df_relevant['Platform'].value_counts().to_dict() if 'Platform' in self.df_relevant.columns else {},
            'content_mix': self.df_relevant['content_owner'].value_counts().to_dict() if 'content_owner' in self.df_relevant.columns else {}
        }

        self.insights['executive_snapshot'] = snapshot
        print("✅ Executive snapshot complete")

        return self

    def analyze_business_priorities(self):
        """Identify top business priorities from the data"""
        print("\n🎯 Analyzing business priorities...")

        if len(self.df_relevant) == 0:
            self.insights['priorities'] = []
            return self

        priorities = []

        # Group by category and analyze
        for category in self.df_relevant['category'].unique():
            cat_data = self.df_relevant[self.df_relevant['category'] == category]

            if len(cat_data) == 0:
                continue

            # Calculate metrics
            volume = len(cat_data)
            avg_sentiment = cat_data['sentiment_score'].mean() if 'sentiment_score' in cat_data.columns else 0.5
            total_engagement = cat_data['total_engagement'].sum() if 'total_engagement' in cat_data.columns else 0

            # Get top examples
            top_examples = cat_data.nlargest(3, 'total_engagement' if 'total_engagement' in cat_data.columns else 'likes')
            examples = []
            for _, row in top_examples.iterrows():
                examples.append({
                    'text': str(row['Text'])[:200],
                    'platform': row.get('Platform', 'unknown'),
                    'sentiment': row.get('sentiment_label', 'neutral'),
                    'engagement': int(row.get('total_engagement', 0))
                })

            # Determine severity/importance
            if category == 'complaint_issue':
                severity = 'critical' if avg_sentiment < 0.3 else 'high'
            elif category == 'question_request':
                severity = 'high' if volume > 10 else 'medium'
            elif category == 'feature_request':
                severity = 'medium'
            elif category == 'praise_positive':
                severity = 'opportunity'
            else:
                severity = 'low'

            priorities.append({
                'category': category.replace('_', ' ').title(),
                'volume': volume,
                'sentiment_avg': f"{avg_sentiment:.2f}",
                'engagement_total': int(total_engagement),
                'severity': severity,
                'examples': examples[:2]  # Top 2 examples
            })

        # Sort by severity then volume
        severity_order = {'critical': 4, 'high': 3, 'medium': 2, 'opportunity': 1, 'low': 0}
        priorities.sort(key=lambda x: (severity_order.get(x['severity'], 0), x['volume']), reverse=True)

        self.insights['business_priorities'] = priorities[:10]  # Top 10
        print(f"✅ Identified {len(priorities)} business priorities")

        return self

    def detect_issues_and_opportunities(self):
        """Detect critical issues and business opportunities"""
        print("\n🚨 Detecting issues and opportunities...")

        if len(self.df_relevant) == 0:
            self.insights['issues'] = []
            self.insights['opportunities'] = []
            return self

        # Critical Issues
        issues = self.df_relevant[
            (self.df_relevant['priority'] == 'critical') |
            (self.df_relevant['priority'] == 'high')
        ].copy()

        issue_list = []
        for _, row in issues.nlargest(10, 'total_engagement' if 'total_engagement' in issues.columns else 'likes').iterrows():
            issue_list.append({
                'text': str(row['Text'])[:300],
                'platform': row.get('Platform', 'unknown'),
                'date': row.get('Date', '').strftime('%Y-%m-%d') if pd.notna(row.get('Date')) else 'unknown',
                'engagement': int(row.get('total_engagement', 0)),
                'sentiment': row.get('sentiment_label', 'unknown'),
                'category': row.get('category', 'unknown')
            })

        # Opportunities
        opportunities = self.df_relevant[
            (self.df_relevant['priority'] == 'opportunity') |
            ((self.df_relevant['category'] == 'praise_positive') & (self.df_relevant['total_engagement'] > 50))
        ].copy()

        opp_list = []
        for _, row in opportunities.nlargest(10, 'total_engagement' if 'total_engagement' in opportunities.columns else 'likes').iterrows():
            opp_list.append({
                'text': str(row['Text'])[:300],
                'platform': row.get('Platform', 'unknown'),
                'date': row.get('Date', '').strftime('%Y-%m-%d') if pd.notna(row.get('Date')) else 'unknown',
                'engagement': int(row.get('total_engagement', 0)),
                'sentiment': row.get('sentiment_label', 'unknown')
            })

        self.insights['critical_issues'] = issue_list
        self.insights['opportunities'] = opp_list

        print(f"✅ Found {len(issue_list)} critical issues")
        print(f"✅ Found {len(opp_list)} opportunities")

        return self

    def generate_action_plan(self):
        """Generate clear, actionable recommendations"""
        print("\n📋 Generating action plan...")

        actions = {
            'immediate_24h': [],
            'short_term_7days': [],
            'medium_term_30days': []
        }

        # Immediate actions (24h) - based on critical issues
        if len(self.insights.get('critical_issues', [])) > 0:
            actions['immediate_24h'].append({
                'action': f"Review and respond to {len(self.insights['critical_issues'])} critical complaints",
                'reason': 'High engagement negative feedback requires immediate attention',
                'owner': 'Customer Service / PR Team'
            })

        # Short-term actions (7 days) - based on patterns
        priorities = self.insights.get('business_priorities', [])
        for p in priorities[:3]:
            if p['severity'] in ['critical', 'high']:
                actions['short_term_7days'].append({
                    'action': f"Address '{p['category']}' issues (Volume: {p['volume']})",
                    'reason': f"{p['volume']} mentions with {p['sentiment_avg']} avg sentiment",
                    'owner': 'Operations / Product Team'
                })

        # Medium-term actions (30 days)
        if len(self.insights.get('opportunities', [])) > 0:
            actions['medium_term_30days'].append({
                'action': f"Amplify {len(self.insights['opportunities'])} positive testimonials",
                'reason': 'Leverage satisfied customers for brand building',
                'owner': 'Marketing / Social Media Team'
            })

        self.insights['action_plan'] = actions
        print("✅ Action plan generated")

        return self

    def analyze(self, filter_days: int = 90):
        """Run complete universal analysis pipeline"""
        print("="*80)
        print(f"🎯 UNIVERSAL INTELLIGENCE ANALYSIS: {self.topic_name}")
        print("="*80)

        self.load_data()
        self.detect_relevance()
        self.remove_duplicates()
        self.filter_date_range(days=filter_days)
        self.classify_content()
        self.generate_executive_snapshot()
        self.analyze_business_priorities()
        self.detect_issues_and_opportunities()
        self.generate_action_plan()

        print("\n" + "="*80)
        print("✅ ANALYSIS COMPLETE")
        print("="*80)

        return self.insights

    def print_summary(self):
        """Print human-readable summary"""
        print("\n" + "="*80)
        print(f"📊 EXECUTIVE SUMMARY: {self.topic_name}")
        print("="*80)

        snapshot = self.insights.get('executive_snapshot', {})
        dq = snapshot.get('data_quality', {})

        print(f"\n📈 DATA QUALITY")
        print(f"  Total Records Collected: {dq.get('total_raw_records', 0):,}")
        print(f"  Relevant Content: {dq.get('relevant_records', 0):,}")
        print(f"  Noise Filtered Out: {dq.get('noise_filtered', 0):,}")
        print(f"  Quality Score: {dq.get('data_quality_score', 'N/A')}")

        tc = snapshot.get('time_coverage', {})
        print(f"\n📅 TIME PERIOD")
        print(f"  From: {tc.get('earliest_date', 'N/A')}")
        print(f"  To: {tc.get('latest_date', 'N/A')}")
        print(f"  Days Covered: {tc.get('days_covered', 0)}")

        print(f"\n🎯 TOP BUSINESS PRIORITIES")
        for i, priority in enumerate(self.insights.get('business_priorities', [])[:5], 1):
            print(f"  {i}. {priority['category']} ({priority['severity'].upper()})")
            print(f"     Volume: {priority['volume']} | Sentiment: {priority['sentiment_avg']} | Engagement: {priority['engagement_total']:,}")

        print(f"\n🚨 CRITICAL ISSUES: {len(self.insights.get('critical_issues', []))}")
        print(f"✨ OPPORTUNITIES: {len(self.insights.get('opportunities', []))}")

        print(f"\n📋 IMMEDIATE ACTIONS (24H)")
        for action in self.insights.get('action_plan', {}).get('immediate_24h', []):
            print(f"  • {action['action']}")
            print(f"    Owner: {action['owner']}")

    def export_to_json(self, output_path: str):
        """Export insights to JSON"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.insights, f, indent=2, ensure_ascii=False, default=str)
        print(f"✅ Exported insights to: {output_path}")

    def export_cleaned_data(self, output_path: str):
        """Export cleaned, classified data to CSV"""
        if self.df_relevant is not None and len(self.df_relevant) > 0:
            self.df_relevant.to_csv(output_path, index=False, encoding='utf-8')
            print(f"✅ Exported cleaned data ({len(self.df_relevant)} records) to: {output_path}")
        else:
            print("⚠️  No data to export")
