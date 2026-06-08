"""
KDEBWM Complaint Monitoring Analytics & Insights Module
========================================================
Executive-level analytics for KDEBWM waste collection complaint monitoring.
Generates CEO-ready insights, not technical NLP reports.

Author: InsightPulse Team
Version: 1.0.0
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import re
from collections import Counter
import json
from typing import Dict, List, Tuple, Any, Optional
import logging

logger = logging.getLogger(__name__)


class KDEBWMComplaintAnalytics:
    """
    KDEBWM-specific complaint analytics engine.
    Generates executive-level insights for waste management operations.
    """
    
    # Complaint theme classification keywords
    THEME_KEYWORDS = {
        'missed_collection': [
            'tak kutip', 'tidak dikutip', 'tidak ambil', 'tak datang', 'tak mai',
            'lambat ambil', 'tunggu lama', 'dah berapa hari', 'masih ada',
            'missed collection', 'not collected', 'skip', 'forgot'
        ],
        'late_collection': [
            'lambat', 'lewat', 'tertangguh', 'delay', 'late', 'slow',
            'tak tepat masa', 'tidak on time', 'pukul berapa'
        ],
        'overflowing_bin': [
            'penuh', 'melimpah', 'overflow', 'tong penuh', 'bin penuh',
            'longgokan', 'bertimbun', 'pile', 'heap'
        ],
        'foul_smell': [
            'bau', 'busuk', 'hancing', 'berbau', 'smell', 'stink', 'odor',
            'najis', 'kotor sangat'
        ],
        'dirty_road_or_area': [
            'jalan kotor', 'kawasan kotor', 'dirty road', 'dirty area',
            'kemas', 'bersih', 'cleanliness', 'clean up'
        ],
        'public_cleansing_issue': [
            'pembersihan awam', 'public cleansing', 'cleaning service',
            'sweep', 'sapu', 'cuci'
        ],
        'illegal_dumping': [
            'buang sampah', 'dump', 'illegal', 'haram', 'tak betul',
            'buang merata', 'tanpa izin'
        ],
        'general_complaint': [
            'aduan', 'complain', 'report', 'complaint', 'tidak puas hati',
            'kecewa', 'masalah', 'issue', 'problem'
        ],
        'praise_or_resolution': [
            'terima kasih', 'thanks', 'dah kutip', 'dah bersih', 'settled',
            'resolved', 'bagus', 'good job', 'appreciate', 'terbaik'
        ]
    }
    
    # Selangor districts / areas
    SELANGOR_AREAS = [
        'klang', 'kajang', 'petaling jaya', 'pj', 'subang jaya', 'selayang',
        'sepang', 'kuala selangor', 'kuala langat', 'hulu selangor',
        'sabak bernam', 'shah alam', 'bangi', 'seri kembangan',
        'ampang', 'cheras', 'puchong', 'sungai buloh', 'rawang',
        'gombak', 'batu caves', 'petaling', 'kota damansara'
    ]
    
    # High-severity urgency keywords
    URGENCY_KEYWORDS = [
        'teruk', 'bau busuk', 'tak datang', 'lambat', 'frust', 'viral',
        'marah', 'geram', 'dah lama', 'berapa hari', 'complaint',
        'aduan', 'serius', 'urgent', 'emergency', 'critical'
    ]
    
    def __init__(self, csv_path: str):
        """
        Initialize KDEBWM analytics with data file path.
        
        Args:
            csv_path: Path to CSV file containing social media data with sentiment/emotion
        """
        self.csv_path = Path(csv_path)
        self.df = None
        self.df_complaints = None
        self.analytics = {}
        self.insights = {}
        
        logger.info(f"📊 KDEBWM Analytics initialized for: {csv_path}")
    
    def load_data(self) -> 'KDEBWMComplaintAnalytics':
        """
        Load and validate CSV data.
        
        Returns:
            self for method chaining
        """
        try:
            self.df = pd.read_csv(self.csv_path)
            logger.info(f"✅ Loaded {len(self.df):,} total records")
            
            # Parse dates
            if 'Date' in self.df.columns:
                self.df['Date'] = pd.to_datetime(self.df['Date'], errors='coerce')
            
            # Ensure required columns exist
            required_cols = ['Text', 'Platform']
            missing_cols = [col for col in required_cols if col not in self.df.columns]
            if missing_cols:
                raise ValueError(f"Missing required columns: {missing_cols}")

            # Normalise sentiment_label — derive from available columns if missing
            if 'sentiment_label' not in self.df.columns:
                if 'Sentiment' in self.df.columns:
                    self.df['sentiment_label'] = self.df['Sentiment'].fillna('neutral').str.lower()
                elif 'sentiment_score' in self.df.columns:
                    def score_to_label(x):
                        try:
                            v = float(x)
                            if v > 0.1:  return 'positive'
                            if v < -0.1: return 'negative'
                            return 'neutral'
                        except: return 'neutral'
                    self.df['sentiment_label'] = self.df['sentiment_score'].apply(score_to_label)
                else:
                    self.df['sentiment_label'] = 'neutral'

            # Normalise total_engagement if missing
            if 'total_engagement' not in self.df.columns:
                eng_cols = ['likes', 'shares', 'comments_count']
                for col in eng_cols:
                    if col not in self.df.columns:
                        self.df[col] = 0
                self.df['total_engagement'] = (
                    self.df['likes'].fillna(0).astype(float) +
                    self.df['shares'].fillna(0).astype(float) +
                    self.df['comments_count'].fillna(0).astype(float)
                )

            return self
            
        except Exception as e:
            logger.error(f"❌ Error loading data: {e}")
            raise

    def filter_complaints(self) -> 'KDEBWMComplaintAnalytics':
        """
        Filter and identify actual KDEBWM-related complaints.

        Returns:
            self for method chaining
        """
        logger.info("🔍 Filtering KDEBWM-related complaints...")

        def is_kdebwm_complaint(row) -> bool:
            """Check if row is a KDEBWM-related complaint"""
            text = str(row.get('Text', '')).lower()

            if pd.isna(text) or len(text.strip()) < 10:
                return False

            # Must mention KDEBWM/KDEB or waste management (with/without space, hashtag variants)
            has_kdebwm = any(kw in text for kw in [
                'kdeb', 'kdebwm', 'waste management', 'wastemanagement',
                'waste mgmt', '#waste', 'kutipan sampah', 'pengangkutan sampah',
                'pengurusan sisa', 'solid waste', 'domestic waste', 'sampah selangor'
            ])

            # Must have complaint-related or waste-related keywords
            has_complaint = any(kw in text for kw in [
                'sampah', 'kutip', 'longgokan', 'bau', 'kotor', 'dirty',
                'complaint', 'aduan', 'problem', 'issue', 'lambat', 'late',
                'waste', 'trash', 'garbage', 'bin', 'recycle', 'daur semula',
                'tong', 'buang', 'penuh', 'overflow', 'kemas', 'bersih',
                'sweep', 'sapu', 'clean', 'rubbish', 'litter', 'dump'
            ])

            return has_kdebwm and has_complaint

        self.df['is_complaint'] = self.df.apply(is_kdebwm_complaint, axis=1)
        self.df_complaints = self.df[self.df['is_complaint']].copy()

        logger.info(f"✅ Found {len(self.df_complaints):,} KDEBWM complaints ({len(self.df_complaints)/len(self.df)*100:.1f}%)")

        return self

    def classify_themes(self) -> 'KDEBWMComplaintAnalytics':
        """
        Classify each complaint into primary theme.

        Returns:
            self for method chaining
        """
        logger.info("🏷️  Classifying complaint themes...")

        def get_primary_theme(text: str) -> str:
            """Determine primary complaint theme from text"""
            if pd.isna(text):
                return 'general_complaint'

            text_lower = text.lower()
            theme_scores = {}

            # Score each theme
            for theme, keywords in self.THEME_KEYWORDS.items():
                score = sum(1 for kw in keywords if kw in text_lower)
                if score > 0:
                    theme_scores[theme] = score

            # Return highest scoring theme
            if theme_scores:
                return max(theme_scores.items(), key=lambda x: x[1])[0]
            else:
                return 'general_complaint'

        self.df_complaints['complaint_theme'] = self.df_complaints['Text'].apply(get_primary_theme)

        theme_counts = self.df_complaints['complaint_theme'].value_counts()
        logger.info(f"✅ Theme distribution: {theme_counts.to_dict()}")

        return self

    def extract_areas(self) -> 'KDEBWMComplaintAnalytics':
        """
        Extract location/area mentions from complaint text.

        Returns:
            self for method chaining
        """
        logger.info("📍 Extracting location hotspots...")

        def extract_area(text: str) -> Optional[str]:
            """Extract area name from text"""
            if pd.isna(text):
                return None

            text_lower = text.lower()

            # Look for area mentions
            for area in self.SELANGOR_AREAS:
                if area in text_lower:
                    return area.title()

            return None

        self.df_complaints['area'] = self.df_complaints['Text'].apply(extract_area)

        area_counts = self.df_complaints['area'].value_counts()
        logger.info(f"✅ Found {len(area_counts)} hotspot areas")

        return self

    def detect_severity(self) -> 'KDEBWMComplaintAnalytics':
        """
        Detect high-severity complaints based on:
        - Strongly negative sentiment
        - High engagement
        - Urgency keywords

        Returns:
            self for method chaining
        """
        logger.info("⚠️  Detecting high-severity complaints...")

        def is_high_severity(row) -> bool:
            """Check if complaint is high severity"""
            text = str(row.get('Text', '')).lower()
            sentiment_label = str(row.get('sentiment_label', 'neutral')).lower()
            total_engagement = row.get('total_engagement', 0)

            # Strong negative sentiment
            is_negative = sentiment_label in ['negative', 'very negative']

            # High engagement (above median)
            median_engagement = self.df_complaints['total_engagement'].median()
            is_high_engagement = total_engagement > median_engagement

            # Has urgency keywords
            has_urgency = any(kw in text for kw in self.URGENCY_KEYWORDS)

            # High severity if: (negative AND urgency) OR (negative AND high engagement)
            return (is_negative and has_urgency) or (is_negative and is_high_engagement)

        self.df_complaints['is_high_severity'] = self.df_complaints.apply(is_high_severity, axis=1)

        severity_count = self.df_complaints['is_high_severity'].sum()
        logger.info(f"✅ Identified {severity_count} high-severity complaints")

        return self

    def generate_analytics(self, filter_days: int = 30) -> Dict[str, Any]:
        """
        Generate comprehensive complaint analytics.

        Args:
            filter_days: Number of days to analyze (default: 30)

        Returns:
            Dictionary containing all analytics sections
        """
        logger.info(f"📊 Generating analytics for last {filter_days} days...")

        # Filter by date range safely (handles tz-aware, tz-naive, and string dates)
        try:
            if 'Date' in self.df_complaints.columns:
                # Parse dates properly with utc=True to normalize all timezones
                dates_parsed = pd.to_datetime(self.df_complaints['Date'], errors='coerce', utc=True)
                self.df_complaints = self.df_complaints.copy()
                self.df_complaints['Date'] = dates_parsed

                cutoff_date = pd.Timestamp.now(tz='UTC') - pd.Timedelta(days=filter_days)
                df_period = self.df_complaints[self.df_complaints['Date'] >= cutoff_date].copy()

                # If too few records after filter, use all data
                if len(df_period) < 10:
                    logger.warning(f"⚠️ Only {len(df_period)} records in last {filter_days} days. Using all {len(self.df_complaints)} records instead.")
                    df_period = self.df_complaints.copy()
            else:
                df_period = self.df_complaints.copy()
        except Exception as e:
            logger.warning(f"⚠️ Date filtering failed ({e}), using all complaints.")
            df_period = self.df_complaints.copy()

        analytics = {}

        # A. Complaint Volume Analytics
        analytics['volume'] = self._analyze_volume(df_period, filter_days)

        # B. Sentiment Analytics
        analytics['sentiment'] = self._analyze_sentiment(df_period)

        # C. Theme Classification
        analytics['themes'] = self._analyze_themes(df_period)

        # D. Hotspot/Area Analytics
        analytics['hotspots'] = self._analyze_hotspots(df_period)

        # E. Platform Analytics
        analytics['platforms'] = self._analyze_platforms(df_period)

        # F. Engagement/Severity Analytics
        analytics['severity'] = self._analyze_severity(df_period)

        # G. CEO Dashboard Metrics
        analytics['dashboard'] = self._generate_dashboard_metrics(df_period)

        self.analytics = analytics
        logger.info("✅ Analytics generation complete")

        return analytics

    def _analyze_volume(self, df: pd.DataFrame, period_days: int) -> Dict[str, Any]:
        """Analyze complaint volume and trends"""
        total_complaints = len(df)

        # Daily counts
        if 'Date' in df.columns:
            df_with_date = df[df['Date'].notna()].copy()
            # Normalize tz-aware to date only
            try:
                df_with_date['date_only'] = pd.to_datetime(df_with_date['Date'], utc=True, errors='coerce').dt.date
            except Exception:
                df_with_date['date_only'] = pd.to_datetime(df_with_date['Date'], errors='coerce').dt.date
            daily_counts = df_with_date.groupby('date_only').size()

            # Peak dates
            if len(daily_counts) > 0:
                peak_date = daily_counts.idxmax()
                peak_count = daily_counts.max()
            else:
                peak_date = None
                peak_count = 0

            # Trend calculation
            if len(daily_counts) >= 7:
                recent_week = daily_counts.tail(7).mean()
                previous_week = daily_counts.iloc[-14:-7].mean() if len(daily_counts) >= 14 else recent_week
                trend_pct = ((recent_week - previous_week) / previous_week * 100) if previous_week > 0 else 0

                if trend_pct > 10:
                    trend_direction = "increasing"
                elif trend_pct < -10:
                    trend_direction = "decreasing"
                else:
                    trend_direction = "stable"
            else:
                trend_pct = 0
                trend_direction = "insufficient_data"
        else:
            daily_counts = pd.Series()
            peak_date = None
            peak_count = 0
            trend_pct = 0
            trend_direction = "no_date_data"

        # Convert daily_counts dict keys (date objects) to strings for JSON serialization
        daily_counts_dict = {str(k): int(v) for k, v in daily_counts.items()} if len(daily_counts) > 0 else {}

        return {
            'total_mentions': total_complaints,
            'daily_average': round(total_complaints / period_days, 1) if period_days > 0 else 0,
            'peak_date': str(peak_date) if peak_date else 'N/A',
            'peak_count': int(peak_count),
            'trend_direction': trend_direction,
            'trend_percentage': round(trend_pct, 1),
            'daily_counts': daily_counts_dict
        }

    def _analyze_sentiment(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze sentiment distribution"""
        if 'sentiment_label' not in df.columns:
            # Try to derive from Sentiment or sentiment_score
            if 'Sentiment' in df.columns:
                df = df.copy()
                df['sentiment_label'] = df['Sentiment'].fillna('neutral').str.lower()
            elif 'sentiment_score' in df.columns:
                df = df.copy()
                df['sentiment_label'] = df['sentiment_score'].apply(
                    lambda x: 'positive' if pd.notna(x) and float(x) > 0.1 else (
                        'negative' if pd.notna(x) and float(x) < -0.1 else 'neutral'))
            else:
                return {'error': 'No sentiment data available'}

        sentiment_counts = df['sentiment_label'].value_counts()
        total = len(df)

        negative_count = sentiment_counts.get('negative', 0) + sentiment_counts.get('very negative', 0)
        neutral_count = sentiment_counts.get('neutral', 0)
        positive_count = sentiment_counts.get('positive', 0) + sentiment_counts.get('very positive', 0)

        return {
            'negative_count': int(negative_count),
            'neutral_count': int(neutral_count),
            'positive_count': int(positive_count),
            'negative_percentage': round(negative_count / total * 100, 1) if total > 0 else 0,
            'neutral_percentage': round(neutral_count / total * 100, 1) if total > 0 else 0,
            'positive_percentage': round(positive_count / total * 100, 1) if total > 0 else 0,
            'sentiment_distribution': sentiment_counts.to_dict()
        }

    def _analyze_themes(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze complaint themes"""
        if 'complaint_theme' not in df.columns:
            return {'error': 'No theme classification available'}

        theme_counts = df['complaint_theme'].value_counts()
        total = len(df)

        # Get top 3 themes
        top_themes = theme_counts.head(3).to_dict()

        # Get examples for each theme
        theme_examples = {}
        for theme in theme_counts.index[:5]:  # Top 5 themes
            examples = df[df['complaint_theme'] == theme]['Text'].head(3).tolist()
            theme_examples[theme] = examples

        return {
            'theme_counts': theme_counts.to_dict(),
            'theme_percentages': {k: round(v/total*100, 1) for k, v in theme_counts.items()},
            'top_3_themes': list(top_themes.keys())[:3],
            'theme_examples': theme_examples
        }

    def _analyze_hotspots(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze complaint hotspot areas"""
        if 'area' not in df.columns:
            return {'error': 'No area data available'}

        # Filter out None/NaN areas
        df_with_area = df[df['area'].notna()].copy()

        if len(df_with_area) == 0:
            return {'error': 'No area mentions found', 'top_5_hotspots': []}

        area_counts = df_with_area['area'].value_counts()
        top_5 = area_counts.head(5).to_dict()

        return {
            'area_counts': area_counts.to_dict(),
            'top_5_hotspots': list(top_5.keys()),
            'hotspot_percentages': {k: round(v/len(df_with_area)*100, 1) for k, v in top_5.items()},
            'areas_with_complaints': len(area_counts)
        }

    def _analyze_platforms(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze platform distribution"""
        if 'Platform' not in df.columns:
            return {'error': 'No platform data available'}

        platform_counts = df['Platform'].value_counts()
        total = len(df)

        # Most complaint-heavy platform
        top_platform = platform_counts.index[0] if len(platform_counts) > 0 else 'N/A'

        # Calculate engagement by platform
        if 'total_engagement' in df.columns:
            platform_engagement = df.groupby('Platform')['total_engagement'].mean().to_dict()
            highest_engagement_platform = max(platform_engagement, key=platform_engagement.get) if platform_engagement else 'N/A'
        else:
            platform_engagement = {}
            highest_engagement_platform = 'N/A'

        return {
            'platform_counts': platform_counts.to_dict(),
            'platform_percentages': {k: round(v/total*100, 1) for k, v in platform_counts.items()},
            'most_complaint_heavy_platform': top_platform,
            'highest_engagement_platform': highest_engagement_platform,
            'platform_engagement_avg': platform_engagement
        }

    def _analyze_severity(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze engagement and severity"""
        if 'total_engagement' not in df.columns:
            return {'error': 'No engagement data available'}

        # Top complaints by engagement — use sentiment_label or fall back to Sentiment column
        if 'sentiment_label' not in df.columns:
            df = df.copy()
            if 'Sentiment' in df.columns:
                df['sentiment_label'] = df['Sentiment']
            elif 'sentiment_score' in df.columns:
                df['sentiment_label'] = df['sentiment_score'].apply(
                    lambda x: 'positive' if float(x) > 0.1 else ('negative' if float(x) < -0.1 else 'neutral')
                    if pd.notna(x) else 'neutral'
                )
            else:
                df['sentiment_label'] = 'neutral'

        top_cols = [c for c in ['Text', 'total_engagement', 'Platform', 'sentiment_label'] if c in df.columns]
        top_posts = df.nlargest(10, 'total_engagement')[top_cols].to_dict('records')

        # Average engagement
        avg_engagement = df['total_engagement'].mean()

        # High severity count
        if 'is_high_severity' in df.columns:
            high_severity_count = df['is_high_severity'].sum()
        else:
            high_severity_count = 0

        return {
            'top_complaint_posts': top_posts,
            'average_engagement': round(avg_engagement, 1),
            'high_severity_count': int(high_severity_count),
            'high_severity_percentage': round(high_severity_count / len(df) * 100, 1) if len(df) > 0 else 0
        }

    def _generate_dashboard_metrics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate CEO dashboard KPI metrics"""

        # Get key metrics
        total_complaints = len(df)

        # Negative sentiment %
        if 'sentiment_label' in df.columns:
            negative_pct = (df['sentiment_label'].isin(['negative', 'very negative']).sum() / total_complaints * 100) if total_complaints > 0 else 0
        else:
            negative_pct = 0

        # Top theme
        if 'complaint_theme' in df.columns:
            top_theme = df['complaint_theme'].value_counts().index[0] if len(df) > 0 else 'N/A'
        else:
            top_theme = 'N/A'

        # Top hotspot
        if 'area' in df.columns:
            areas = df[df['area'].notna()]['area']
            top_hotspot = areas.value_counts().index[0] if len(areas) > 0 else 'N/A'
        else:
            top_hotspot = 'N/A'

        # Peak date
        if 'Date' in df.columns:
            try:
                df_with_date = df[df['Date'].notna()].copy()
                if len(df_with_date) > 0:
                    df_with_date['date_only'] = pd.to_datetime(df_with_date['Date'], utc=True, errors='coerce').dt.date
                    daily_counts = df_with_date.groupby('date_only').size()
                    peak_date = str(daily_counts.idxmax()) if len(daily_counts) > 0 else 'N/A'
                else:
                    peak_date = 'N/A'
            except Exception:
                peak_date = 'N/A'
        else:
            peak_date = 'N/A'

        # Most complaint-heavy platform
        if 'Platform' in df.columns:
            top_platform = df['Platform'].value_counts().index[0] if len(df) > 0 else 'N/A'
        else:
            top_platform = 'N/A'

        # High severity count
        if 'is_high_severity' in df.columns:
            high_severity = df['is_high_severity'].sum()
        else:
            high_severity = 0

        # Unanswered % (placeholder - requires response detection)
        unanswered_pct = 100  # Assume all unanswered unless response detection implemented

        return {
            'total_complaints': int(total_complaints),
            'negative_sentiment_pct': round(negative_pct, 1),
            'top_complaint_theme': top_theme.replace('_', ' ').title(),
            'top_hotspot_area': top_hotspot,
            'peak_complaint_date': str(peak_date),
            'most_complaint_heavy_platform': top_platform,
            'high_severity_count': int(high_severity),
            'unanswered_complaint_pct': round(unanswered_pct, 1)
        }

    def generate_insights(self) -> Dict[str, List[str]]:
        """
        Generate executive-level insights from analytics.

        Returns:
            Dictionary containing insights and recommendations
        """
        if not self.analytics:
            raise ValueError("Analytics must be generated first. Call generate_analytics() first.")

        logger.info("💡 Generating executive insights...")

        insights = []
        recommendations = []

        # Volume Insight
        volume = self.analytics.get('volume', {})
        trend_dir = volume.get('trend_direction', 'stable')
        trend_pct = volume.get('trend_percentage', 0)
        peak_date = volume.get('peak_date', 'N/A')

        if trend_dir == 'increasing':
            insights.append(
                f"Complaint volume increased by {abs(trend_pct)}% compared to the previous period, "
                f"with the largest spike on {peak_date}. This suggests a possible service disruption, "
                f"delayed collection cycle, or event-related pressure."
            )
            recommendations.append("Investigate operational issues around peak complaint dates and implement contingency plans.")
        elif trend_dir == 'decreasing':
            insights.append(
                f"Complaint volume decreased by {abs(trend_pct)}%, indicating improvement in service delivery or reduced public dissatisfaction."
            )

        # Theme Insight
        themes = self.analytics.get('themes', {})
        top_themes = themes.get('top_3_themes', [])

        if top_themes:
            top_theme = top_themes[0].replace('_', ' ')
            insights.append(
                f"The largest complaint category is '{top_theme}', indicating this is a bigger public concern "
                f"than other service aspects. Reliability of service remains the primary reputational risk."
            )
            recommendations.append(f"Prioritize operational improvements for {top_theme} to address the most frequent complaint type.")

        # Area Insight
        hotspots = self.analytics.get('hotspots', {})
        top_areas = hotspots.get('top_5_hotspots', [])

        if top_areas:
            top_area = top_areas[0]
            insights.append(
                f"{top_area} recorded the highest complaint volume, making it a priority hotspot for "
                f"operational review and branch-level response. Consider targeted interventions in this area."
            )
            recommendations.append(f"Deploy additional resources or operational review in {top_area} to address hotspot complaints.")

        # Platform Insight
        platforms = self.analytics.get('platforms', {})
        top_platform = platforms.get('most_complaint_heavy_platform', 'N/A')
        high_engagement_platform = platforms.get('highest_engagement_platform', 'N/A')

        if top_platform != 'N/A':
            insights.append(
                f"{top_platform} generated the most complaint mentions. "
                + (f"{high_engagement_platform} showed higher engagement per complaint, meaning reputational risk may spread faster there."
                   if high_engagement_platform != top_platform else
                   "This platform requires active monitoring and rapid response.")
            )
            recommendations.append(f"Establish dedicated social media response team for {top_platform} to manage reputation proactively.")

        # Reputation-Response Insight
        dashboard = self.analytics.get('dashboard', {})
        unanswered_pct = dashboard.get('unanswered_complaint_pct', 0)

        if unanswered_pct > 50:
            insights.append(
                f"A significant share ({unanswered_pct}%) of complaints remain publicly unanswered, "
                f"creating a gap between operational resolution and visible reputation recovery. "
                f"This may damage public trust even if issues are being addressed internally."
            )
            recommendations.append("Implement systematic public response protocol to acknowledge complaints and communicate resolutions.")

        self.insights = {
            'insights': insights,
            'recommendations': recommendations
        }

        logger.info(f"✅ Generated {len(insights)} insights and {len(recommendations)} recommendations")

        return self.insights

    def generate_executive_summary(self) -> str:
        """
        Generate CEO-ready executive summary.

        Returns:
            Executive summary text
        """
        if not self.analytics:
            raise ValueError("Analytics must be generated first.")

        dashboard = self.analytics.get('dashboard', {})
        volume = self.analytics.get('volume', {})
        themes = self.analytics.get('themes', {})
        hotspots = self.analytics.get('hotspots', {})

        total = dashboard.get('total_complaints', 0)
        trend = volume.get('trend_direction', 'stable')
        top_themes = themes.get('top_3_themes', ['N/A', 'N/A', 'N/A'])[:3]
        top_areas = hotspots.get('top_5_hotspots', ['N/A', 'N/A', 'N/A'])[:3]

        insights_data = self.insights.get('recommendations', [])[:3] if self.insights else []

        summary = f"""
KDEBWM COMPLAINT MONITORING - EXECUTIVE SUMMARY
================================================

OVERVIEW:
- Total Complaint Mentions: {total:,}
- Trend: {trend.upper()}
- Negative Sentiment: {dashboard.get('negative_sentiment_pct', 0)}%
- High-Severity Complaints: {dashboard.get('high_severity_count', 0)}

TOP 3 COMPLAINT THEMES:
1. {top_themes[0].replace('_', ' ').title() if len(top_themes) > 0 else 'N/A'}
2. {top_themes[1].replace('_', ' ').title() if len(top_themes) > 1 else 'N/A'}
3. {top_themes[2].replace('_', ' ').title() if len(top_themes) > 2 else 'N/A'}

TOP 3 HOTSPOT AREAS:
1. {top_areas[0] if len(top_areas) > 0 else 'N/A'}
2. {top_areas[1] if len(top_areas) > 1 else 'N/A'}
3. {top_areas[2] if len(top_areas) > 2 else 'N/A'}

MAIN RECOMMENDATIONS:
"""

        for i, rec in enumerate(insights_data, 1):
            summary += f"{i}. {rec}\n"

        if not insights_data:
            summary += "- Generate insights first using generate_insights() method\n"

        return summary.strip()

    def analyze(self, filter_days: int = 30) -> Dict[str, Any]:
        """
        Run complete analysis pipeline.

        Args:
            filter_days: Number of days to analyze

        Returns:
            Complete analysis results with analytics, insights, and summary
        """
        logger.info("🚀 Starting KDEBWM complaint analysis pipeline...")

        # Load and process data
        self.load_data()
        self.filter_complaints()
        self.classify_themes()
        self.extract_areas()
        self.detect_severity()

        # Generate analytics
        analytics = self.generate_analytics(filter_days)

        # Generate insights
        insights = self.generate_insights()

        # Generate executive summary
        summary = self.generate_executive_summary()

        logger.info("✅ KDEBWM analysis complete!")

        return {
            'analytics': analytics,
            'insights': insights,
            'executive_summary': summary,
            'metadata': {
                'total_records': len(self.df),
                'complaint_records': len(self.df_complaints),
                'filter_days': filter_days,
                'generated_at': datetime.now().isoformat()
            }
        }

    def export_to_json(self, filepath: str) -> None:
        """
        Export complete analysis to JSON file.

        Args:
            filepath: Output JSON file path
        """
        if not self.analytics:
            raise ValueError("No analytics to export. Run analyze() first.")

        output = {
            'analytics': self.analytics,
            'insights': self.insights,
            'executive_summary': self.generate_executive_summary(),
            'metadata': {
                'total_records': len(self.df) if self.df is not None else 0,
                'complaint_records': len(self.df_complaints) if self.df_complaints is not None else 0,
                'generated_at': datetime.now().isoformat(),
                'source_file': str(self.csv_path)
            }
        }

        output_path = Path(filepath)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False, default=str)

        logger.info(f"💾 Exported analytics to: {filepath}")

    def export_complaints_csv(self, filepath: str) -> None:
        """
        Export processed complaints data to CSV.

        Args:
            filepath: Output CSV file path
        """
        if self.df_complaints is None or len(self.df_complaints) == 0:
            raise ValueError("No complaint data to export. Run analyze() first.")

        output_path = Path(filepath)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        self.df_complaints.to_csv(output_path, index=False, encoding='utf-8')

        logger.info(f"💾 Exported {len(self.df_complaints)} complaints to: {filepath}")


# Convenience function for quick analysis
def analyze_kdebwm_complaints(csv_path: str, filter_days: int = 30, output_dir: Optional[str] = None) -> Dict[str, Any]:
    """
    Quick function to analyze KDEBWM complaints from CSV file.

    Args:
        csv_path: Path to combined CSV file with sentiment/emotion data
        filter_days: Number of days to analyze (default: 30)
        output_dir: Optional directory to save results

    Returns:
        Complete analysis results

    Example:
        >>> results = analyze_kdebwm_complaints('data/combined/Combined_facebook_instagram_x_tiktok_20260524.csv')
        >>> print(results['executive_summary'])
    """
    analyzer = KDEBWMComplaintAnalytics(csv_path)
    results = analyzer.analyze(filter_days=filter_days)

    # Export if output directory specified
    if output_dir:
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)

        analyzer.export_to_json(str(out_path / 'kdebwm_analytics.json'))
        analyzer.export_complaints_csv(str(out_path / 'kdebwm_complaints_processed.csv'))

        # Save executive summary as text file
        with open(out_path / 'executive_summary.txt', 'w', encoding='utf-8') as f:
            f.write(results['executive_summary'])

        logger.info(f"📁 All results exported to: {output_dir}")

    return results
