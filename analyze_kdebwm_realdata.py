#!/usr/bin/env python3
"""
Analyze real KDEBWM complaint data
"""

from backend.services.kdebwm_analytics import analyze_kdebwm_complaints

print("=" * 70)
print("KDEBWM REAL DATA ANALYSIS")
print("=" * 70)

results = analyze_kdebwm_complaints(
    csv_path='data/combined/Combined_instagram_x_tiktok_20260524_233229.csv',
    filter_days=30,
    output_dir='reports/kdebwm_realdata_analysis'
)

print("\n" + "=" * 70)
print(results['executive_summary'])
print("\n" + "=" * 70)
print("KEY INSIGHTS:")
print("=" * 70)
for i, insight in enumerate(results['insights']['insights'], 1):
    print(f"{i}. {insight}\n")
    
print("=" * 70)
print("MANAGEMENT RECOMMENDATIONS:")
print("=" * 70)
for i, rec in enumerate(results['insights']['recommendations'], 1):
    print(f"{i}. {rec}\n")

print("=" * 70)
print("CEO DASHBOARD METRICS:")
print("=" * 70)
dashboard = results['analytics']['dashboard']
for key, value in dashboard.items():
    print(f"  - {key.replace('_', ' ').title()}: {value}")

print("\n" + "=" * 70)
print(f"RESULTS SAVED TO: reports/kdebwm_realdata_analysis/")
print(f"Processed {results['metadata']['complaint_records']} KDEBWM complaints")
print(f"Out of {results['metadata']['total_records']} total records")
print("=" * 70)
