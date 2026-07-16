#!/usr/bin/env python3
"""
Test script for KDEBWM Complaint Analytics Module
Run this to verify the module works correctly
"""

import pandas as pd
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.services.kdebwm_analytics import KDEBWMComplaintAnalytics, analyze_kdebwm_complaints


def create_sample_data():
    """Create sample KDEBWM complaint data for testing"""
    
    sample_data = [
        {
            'Platform': 'facebook',
            'Type': 'post',
            'Text': 'KDEBWM sampah tak kutip dah 3 hari di Klang. Bau busuk sangat! Aduan saya masih tak selesai.',
            'Date': '2026-05-20',
            'sentiment_label': 'negative',
            'sentiment_score': 0.15,
            'total_engagement': 45,
            'likes': 30,
            'comments_count': 10,
            'shares': 5
        },
        {
            'Platform': 'instagram',
            'Type': 'comment',
            'Text': 'Kawasan Subang Jaya longgokan sampah penuh. KDEB Waste Management lambat sangat!',
            'Date': '2026-05-21',
            'sentiment_label': 'negative',
            'sentiment_score': 0.2,
            'total_engagement': 23,
            'likes': 20,
            'comments_count': 3,
            'shares': 0
        },
        {
            'Platform': 'x',
            'Type': 'post',
            'Text': 'KDEBWM terima kasih! Sampah di Kajang dah dikutip. Bagus service korang 👍',
            'Date': '2026-05-22',
            'sentiment_label': 'positive',
            'sentiment_score': 0.85,
            'total_engagement': 12,
            'likes': 10,
            'comments_count': 2,
            'shares': 0
        },
        {
            'Platform': 'tiktok',
            'Type': 'post',
            'Text': 'KDEB Waste jalan kotor tepi kawasan Petaling Jaya. Public cleansing issue teruk!',
            'Date': '2026-05-23',
            'sentiment_label': 'negative',
            'sentiment_score': 0.25,
            'total_engagement': 67,
            'likes': 50,
            'comments_count': 12,
            'shares': 5
        },
        {
            'Platform': 'facebook',
            'Type': 'post',
            'Text': 'KDEBWM Selayang missed collection lagi. Dah complaint berkali-kali. Frustrating!',
            'Date': '2026-05-23',
            'sentiment_label': 'very negative',
            'sentiment_score': 0.1,
            'total_engagement': 89,
            'likes': 60,
            'comments_count': 20,
            'shares': 9
        },
        {
            'Platform': 'instagram',
            'Type': 'post',
            'Text': 'Klang area bau busuk dari tong sampah penuh. KDEB please help!',
            'Date': '2026-05-24',
            'sentiment_label': 'negative',
            'sentiment_score': 0.18,
            'total_engagement': 34,
            'likes': 25,
            'comments_count': 7,
            'shares': 2
        }
    ]
    
    # Create DataFrame
    df = pd.DataFrame(sample_data)
    
    # Save to temporary CSV
    test_csv_path = Path('test_kdebwm_sample_data.csv')
    df.to_csv(test_csv_path, index=False, encoding='utf-8')
    
    print(f"✅ Created sample data: {test_csv_path}")
    print(f"   {len(df)} sample complaints")
    
    return test_csv_path


def test_analytics_module():
    """Test the KDEBWM analytics module"""
    
    print("\n" + "="*60)
    print("KDEBWM COMPLAINT ANALYTICS MODULE - TEST")
    print("="*60 + "\n")
    
    # Create sample data
    csv_path = create_sample_data()
    
    # Run analysis
    print("\n🔍 Running KDEBWM complaint analysis...")
    
    try:
        results = analyze_kdebwm_complaints(
            csv_path=str(csv_path),
            filter_days=30,
            output_dir='test_kdebwm_output'
        )
        
        print("\n✅ Analysis Complete!")
        
        # Display results
        print("\n" + "="*60)
        print("EXECUTIVE SUMMARY")
        print("="*60)
        print(results['executive_summary'])
        
        print("\n" + "="*60)
        print("KEY INSIGHTS")
        print("="*60)
        for i, insight in enumerate(results['insights']['insights'], 1):
            print(f"{i}. {insight}\n")
        
        print("="*60)
        print("MANAGEMENT RECOMMENDATIONS")
        print("="*60)
        for i, rec in enumerate(results['insights']['recommendations'], 1):
            print(f"{i}. {rec}\n")
        
        print("="*60)
        print("CEO DASHBOARD METRICS")
        print("="*60)
        dashboard = results['analytics']['dashboard']
        for key, value in dashboard.items():
            print(f"  {key.replace('_', ' ').title()}: {value}")
        
        print("\n" + "="*60)
        print("FILES GENERATED")
        print("="*60)
        output_dir = Path('test_kdebwm_output')
        if output_dir.exists():
            for file in output_dir.glob('*'):
                print(f"  ✓ {file}")
        
        print("\n✅ TEST PASSED! Module is working correctly.\n")
        
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_analytics_module()
    sys.exit(0 if success else 1)
