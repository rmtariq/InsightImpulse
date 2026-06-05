"""
Test script for Professional Report Generation System
Tests all 9 report outputs with sample data
"""

import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.services.report_generator import ProfessionalReportGenerator
from datetime import datetime, timedelta
import random

def generate_sample_data():
    """Generate realistic sample data for testing"""
    
    platforms = ['facebook', 'instagram', 'twitter', 'youtube', 'tiktok']
    
    # Generate sample posts
    sample_posts = []
    for i in range(100):
        platform = random.choice(platforms)
        sentiment_score = random.uniform(-1, 1)
        
        post = {
            'platform': platform,
            'text': f'Sample post {i+1} about Grab Malaysia service quality and pricing',
            'sentiment_score': sentiment_score,
            'emotion': random.choice(['joy', 'anger', 'sadness', 'neutral', 'surprise']),
            'engagement': {
                'total': random.randint(10, 10000),
                'likes': random.randint(5, 5000),
                'comments': random.randint(0, 500),
                'shares': random.randint(0, 1000)
            },
            'url': f'https://{platform}.com/post/{i+1}',
            'created_at': (datetime.now() - timedelta(days=random.randint(0, 7))).isoformat(),
            'comments': [
                {
                    'text': f'Comment {j+1} on post {i+1}',
                    'likes': random.randint(0, 100),
                    'replies': random.randint(0, 20),
                    'sentiment_score': random.uniform(-1, 1),
                    'created_at': (datetime.now() - timedelta(days=random.randint(0, 7))).isoformat()
                }
                for j in range(random.randint(0, 5))
            ]
        }
        sample_posts.append(post)
    
    # Calculate sentiment ratios
    positive_count = sum(1 for p in sample_posts if p['sentiment_score'] > 0.2)
    negative_count = sum(1 for p in sample_posts if p['sentiment_score'] < -0.2)
    neutral_count = len(sample_posts) - positive_count - negative_count
    
    # Prepare analysis data
    analysis_data = {
        'raw_data': sample_posts,
        'sentiment_analysis': {
            'positive_ratio': (positive_count / len(sample_posts)) * 100,
            'neutral_ratio': (neutral_count / len(sample_posts)) * 100,
            'negative_ratio': (negative_count / len(sample_posts)) * 100,
        },
        'platform_breakdown': {
            'facebook': {
                'total': sum(1 for p in sample_posts if p['platform'] == 'facebook'),
                'avg_sentiment': sum(p['sentiment_score'] for p in sample_posts if p['platform'] == 'facebook') / max(sum(1 for p in sample_posts if p['platform'] == 'facebook'), 1),
                'total_engagement': sum(p['engagement']['total'] for p in sample_posts if p['platform'] == 'facebook')
            },
            'instagram': {
                'total': sum(1 for p in sample_posts if p['platform'] == 'instagram'),
                'avg_sentiment': sum(p['sentiment_score'] for p in sample_posts if p['platform'] == 'instagram') / max(sum(1 for p in sample_posts if p['platform'] == 'instagram'), 1),
                'total_engagement': sum(p['engagement']['total'] for p in sample_posts if p['platform'] == 'instagram')
            },
            'twitter': {
                'total': sum(1 for p in sample_posts if p['platform'] == 'twitter'),
                'avg_sentiment': sum(p['sentiment_score'] for p in sample_posts if p['platform'] == 'twitter') / max(sum(1 for p in sample_posts if p['platform'] == 'twitter'), 1),
                'total_engagement': sum(p['engagement']['total'] for p in sample_posts if p['platform'] == 'twitter')
            },
            'youtube': {
                'total': sum(1 for p in sample_posts if p['platform'] == 'youtube'),
                'avg_sentiment': sum(p['sentiment_score'] for p in sample_posts if p['platform'] == 'youtube') / max(sum(1 for p in sample_posts if p['platform'] == 'youtube'), 1),
                'total_engagement': sum(p['engagement']['total'] for p in sample_posts if p['platform'] == 'youtube')
            },
            'tiktok': {
                'total': sum(1 for p in sample_posts if p['platform'] == 'tiktok'),
                'avg_sentiment': sum(p['sentiment_score'] for p in sample_posts if p['platform'] == 'tiktok') / max(sum(1 for p in sample_posts if p['platform'] == 'tiktok'), 1),
                'total_engagement': sum(p['engagement']['total'] for p in sample_posts if p['platform'] == 'tiktok')
            }
        },
        'insights': {
            'key_insights': [
                'Strong positive sentiment on Instagram and TikTok',
                'Pricing concerns mentioned frequently on Twitter',
                'Service quality praised on Facebook',
                'Driver behavior is a recurring topic',
                'Competition with other ride-hailing services discussed'
            ]
        },
        'critical_issues': [
            'High pricing during peak hours',
            'Driver cancellations reported',
            'App performance issues mentioned',
            'Customer service response time concerns'
        ],
        'recommendations': [
            'Address pricing transparency concerns',
            'Improve driver-passenger matching algorithm',
            'Enhance app stability and performance',
            'Strengthen customer service response',
            'Leverage positive testimonials in marketing'
        ]
    }
    
    return analysis_data

def main():
    """Run report generation test"""
    print("=" * 80)
    print("🧪 TESTING PROFESSIONAL REPORT GENERATION SYSTEM (11 Reports)")
    print("=" * 80)
    print()
    
    # Generate sample data
    print("📊 Generating sample data...")
    analysis_data = generate_sample_data()
    print(f"✅ Generated {len(analysis_data['raw_data'])} sample posts")
    print()
    
    # Initialize report generator
    print("🎯 Initializing report generator...")
    report_gen = ProfessionalReportGenerator(output_dir="reports_test")
    print("✅ Report generator initialized")
    print()
    
    # Generate all reports
    print("📝 Generating all 11 professional reports...")
    print("-" * 80)
    
    try:
        report_paths = report_gen.generate_all_reports(
            analysis_data=analysis_data,
            query="Grab Malaysia",
            analysis_type="brand_monitoring"
        )
        
        print()
        print("=" * 80)
        print("✅ REPORT GENERATION COMPLETE!")
        print("=" * 80)
        print()
        print("📁 Generated Reports:")
        print()
        
        for report_type, path in report_paths.items():
            if path:
                file_exists = "✅" if os.path.exists(path) else "❌"
                file_size = os.path.getsize(path) if os.path.exists(path) else 0
                print(f"  {file_exists} {report_type:25s} → {Path(path).name:40s} ({file_size:,} bytes)")
            else:
                print(f"  ⚠️  {report_type:25s} → Not generated (optional dependency missing)")
        
        print()
        print("=" * 80)
        print(f"📂 All reports saved to: {Path(report_paths.get('executive_summary', '')).parent}")
        print("=" * 80)
        
    except Exception as e:
        print()
        print("=" * 80)
        print(f"❌ ERROR: {e}")
        print("=" * 80)
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

