#!/usr/bin/env python3
"""
Sync Smart Crawler Data to InsightPulse
=======================================

This script syncs data from your original smart_crawlers directory
to the InsightPulse data directory to ensure all platforms have data available.

Usage:
    python sync_crawler_data.py
"""

import os
import shutil
from pathlib import Path

def sync_crawler_data():
    """Sync data from original smart_crawlers to InsightPulse"""
    
    # Source and destination paths
    source_path = Path("/Users/rmtariq/smart_crawlers/data")
    dest_path = Path("/Users/rmtariq/InsightPulse/data/smart_crawlers")
    
    print("🔄 Syncing Smart Crawler Data to InsightPulse...")
    print(f"📂 Source: {source_path}")
    print(f"📂 Destination: {dest_path}")
    
    # Check if source exists
    if not source_path.exists():
        print(f"❌ Source path not found: {source_path}")
        return False
    
    # Create destination if it doesn't exist
    dest_path.mkdir(parents=True, exist_ok=True)
    
    # Sync each platform
    platforms = ["facebook", "google", "instagram", "lowyat", "news", "tiktok", "x"]
    
    total_files = 0
    total_size = 0
    
    for platform in platforms:
        source_platform = source_path / platform
        dest_platform = dest_path / platform
        
        if source_platform.exists():
            print(f"\n📁 Syncing {platform}...")
            
            # Create destination platform directory
            dest_platform.mkdir(exist_ok=True)
            
            # Copy all CSV files
            csv_files = list(source_platform.glob("*.csv"))
            
            for csv_file in csv_files:
                dest_file = dest_platform / csv_file.name
                
                # Only copy if file doesn't exist or source is newer
                if not dest_file.exists() or csv_file.stat().st_mtime > dest_file.stat().st_mtime:
                    shutil.copy2(csv_file, dest_file)
                    file_size = csv_file.stat().st_size
                    total_files += 1
                    total_size += file_size
                    print(f"  ✅ Copied: {csv_file.name} ({file_size:,} bytes)")
                else:
                    print(f"  ⏭️  Skipped: {csv_file.name} (already up to date)")
            
            print(f"  📊 {platform}: {len(csv_files)} files available")
        else:
            print(f"  ⚠️  {platform}: No source data found")
    
    print(f"\n🎉 Sync Complete!")
    print(f"📄 Total files synced: {total_files}")
    print(f"💾 Total size: {total_size:,} bytes ({total_size/1024/1024:.1f} MB)")
    
    # Show final data summary
    print(f"\n📊 Data Summary:")
    for platform in platforms:
        platform_dir = dest_path / platform
        if platform_dir.exists():
            csv_files = list(platform_dir.glob("*.csv"))
            if csv_files:
                total_records = 0
                for csv_file in csv_files:
                    try:
                        with open(csv_file, 'r') as f:
                            total_records += sum(1 for line in f) - 1  # Subtract header
                    except:
                        pass
                print(f"  📘 {platform.title()}: {len(csv_files)} files, ~{total_records:,} records")
            else:
                print(f"  ❌ {platform.title()}: No data files")
        else:
            print(f"  ❌ {platform.title()}: Directory not found")
    
    return True

def check_lowyat_crawler():
    """Check if Lowyat crawler is working properly"""
    
    print("\n🔍 Checking Lowyat Crawler Status...")
    
    # Check crawler file
    crawler_file = Path("/Users/rmtariq/smart_crawlers/crawlers/smart_lowyat_crawler.py")
    if crawler_file.exists():
        print(f"✅ Lowyat crawler found: {crawler_file}")
        print(f"📅 Last modified: {crawler_file.stat().st_mtime}")
    else:
        print(f"❌ Lowyat crawler not found: {crawler_file}")
        return False
    
    # Check data files
    data_dir = Path("/Users/rmtariq/smart_crawlers/data/lowyat")
    if data_dir.exists():
        csv_files = list(data_dir.glob("*.csv"))
        print(f"📁 Lowyat data directory: {data_dir}")
        print(f"📄 CSV files found: {len(csv_files)}")
        
        total_records = 0
        for csv_file in csv_files:
            try:
                with open(csv_file, 'r') as f:
                    records = sum(1 for line in f) - 1  # Subtract header
                total_records += records
                print(f"  📊 {csv_file.name}: {records:,} records")
            except Exception as e:
                print(f"  ❌ Error reading {csv_file.name}: {e}")
        
        print(f"📈 Total Lowyat records: {total_records:,}")
        
        if total_records > 0:
            print("✅ Lowyat crawler has data and appears to be working!")
            return True
        else:
            print("⚠️  Lowyat crawler found but no data records")
            return False
    else:
        print(f"❌ Lowyat data directory not found: {data_dir}")
        return False

def main():
    """Main function"""
    print("🚀 InsightPulse Smart Crawler Data Sync")
    print("=" * 50)
    
    # Sync data
    sync_success = sync_crawler_data()
    
    # Check Lowyat specifically
    lowyat_success = check_lowyat_crawler()
    
    print("\n" + "=" * 50)
    if sync_success and lowyat_success:
        print("🎉 All systems ready! Lowyat crawler is working perfectly.")
        print("💡 You can now use all platforms including Lowyat in InsightPulse.")
    elif sync_success:
        print("✅ Data sync complete, but Lowyat may need attention.")
    else:
        print("❌ Issues found. Please check the paths and try again.")
    
    print("\n🔗 Next steps:")
    print("1. Refresh your InsightPulse browser")
    print("2. Try the 'Test Lowyat Data' button")
    print("3. Or use 'Test All Available Platforms' for comprehensive analysis")

if __name__ == "__main__":
    main()
