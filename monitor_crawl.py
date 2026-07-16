#!/usr/bin/env python3
"""
Real-time Crawling Activity Monitor for InsightPulse
Shows live logs as analysis runs
"""

import subprocess
import time
import sys
from pathlib import Path
from datetime import datetime

def monitor_logs(log_file="backend.log", follow_lines=50):
    """Monitor backend logs in real-time"""
    
    print("=" * 90)
    print("🔍 INSIGHTPULSE CRAWLING ACTIVITY MONITOR")
    print("=" * 90)
    print(f"Log file: {log_file}")
    print(f"Refreshing every 2 seconds...")
    print("Press Ctrl+C to stop\n")
    
    last_position = 0
    
    try:
        while True:
            log_path = Path(log_file)
            
            if not log_path.exists():
                print(f"⏳ Waiting for log file: {log_file}")
                time.sleep(2)
                continue
            
            # Read new content
            with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                f.seek(last_position)
                new_lines = f.readlines()
                last_position = f.tell()
            
            if new_lines:
                # Print new lines with timestamps
                for line in new_lines:
                    line = line.rstrip()
                    
                    # Color code by log level
                    if '✅' in line or 'SUCCESS' in line.upper():
                        print(f"✅ {line}")
                    elif '❌' in line or 'ERROR' in line.upper():
                        print(f"❌ {line}")
                    elif '⚠️' in line or 'WARNING' in line.upper():
                        print(f"⚠️  {line}")
                    elif '🔍' in line or 'CRAWL' in line.upper():
                        print(f"🔍 {line}")
                    elif '📊' in line or 'COMMENT' in line.upper():
                        print(f"📊 {line}")
                    elif '🚀' in line or 'RUNNING' in line.upper():
                        print(f"🚀 {line}")
                    else:
                        print(f"   {line}")
            
            time.sleep(2)
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Monitor stopped")
        sys.exit(0)

def monitor_files():
    """Monitor output files creation"""
    
    print("\n" + "=" * 90)
    print("📁 FILE CREATION MONITOR")
    print("=" * 90)
    
    watch_dirs = {
        'Raw Data': 'data/smart_crawlers',
        'Analyzed Data': 'data/analyzed',
        'Combined Data': 'data/combined',
        'Reports': 'reports'
    }
    
    file_counts = {}
    
    try:
        while True:
            print(f"\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("-" * 90)
            
            for label, directory in watch_dirs.items():
                path = Path(directory)
                if path.exists():
                    # Count CSV files
                    csv_files = list(path.rglob('*.csv'))
                    # Count all files in directory
                    all_files = list(path.rglob('*'))
                    all_files = [f for f in all_files if f.is_file()]
                    
                    count = len(all_files)
                    prev_count = file_counts.get(label, 0)
                    
                    if count > prev_count:
                        print(f"📈 {label}: {count} files (NEW: +{count - prev_count})")
                    else:
                        print(f"📁 {label}: {count} files")
                    
                    file_counts[label] = count
                    
                    # Show latest files
                    if all_files:
                        latest = sorted(all_files, key=lambda p: p.stat().st_mtime, reverse=True)[:2]
                        for f in latest:
                            size = f.stat().st_size / 1024  # KB
                            print(f"    └─ {f.name} ({size:.1f}KB)")
                else:
                    print(f"⏳ {label}: directory not found")
            
            time.sleep(5)
            
    except KeyboardInterrupt:
        print("\n⏹️  File monitor stopped")
        sys.exit(0)

def show_menu():
    """Show monitoring options"""
    print("\n" + "=" * 90)
    print("🎯 SELECT MONITORING MODE")
    print("=" * 90)
    print("1. Monitor Backend Logs (Real-time crawling activity)")
    print("2. Monitor Files (CSV, Reports creation)")
    print("3. Monitor Both (split view)")
    print("\nEnter choice (1-3): ", end="")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Monitor InsightPulse crawling activities")
    parser.add_argument('--mode', choices=['logs', 'files', 'both'], default='logs',
                       help='What to monitor: logs, files, or both')
    
    args = parser.parse_args()
    
    if args.mode == 'logs':
        monitor_logs()
    elif args.mode == 'files':
        monitor_files()
    else:
        # Both mode
        print("Starting dual monitoring (this requires two terminals)")
        print("Run in another terminal:")
        print("  python3 monitor_crawl.py --mode files")
        monitor_logs()
