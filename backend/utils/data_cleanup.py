"""
Data Cleanup Utility for InsightPulse

Automatically removes old CSV files to prevent disk space issues:
- Keeps last 30 days in data/smart_crawlers/
- Keeps last 7 days in data/analyzed/
- Always keeps latest in data/raw/
"""

from pathlib import Path
from datetime import datetime, timedelta
from loguru import logger
import os


class DataCleanup:
    """Cleanup old data files to manage disk space"""
    
    def __init__(self):
        self.base_dir = Path("data")
        self.smart_crawlers_dir = self.base_dir / "smart_crawlers"
        self.analyzed_dir = self.base_dir / "analyzed"
        self.raw_dir = self.base_dir / "raw"
    
    def cleanup_old_files(self, days_to_keep_smart: int = 30, days_to_keep_analyzed: int = 7):
        """
        Remove old CSV files based on retention policy
        
        Args:
            days_to_keep_smart: Days to keep files in smart_crawlers (default: 30)
            days_to_keep_analyzed: Days to keep files in analyzed (default: 7)
        """
        logger.info("🧹 Starting data cleanup...")
        
        total_deleted = 0
        total_size_freed = 0
        
        # Cleanup smart_crawlers (30 days)
        if self.smart_crawlers_dir.exists():
            deleted, size = self._cleanup_directory(
                self.smart_crawlers_dir, 
                days_to_keep_smart,
                recursive=True
            )
            total_deleted += deleted
            total_size_freed += size
            logger.info(f"✅ smart_crawlers: Deleted {deleted} files ({size / 1024 / 1024:.2f} MB)")
        
        # Cleanup analyzed (7 days)
        if self.analyzed_dir.exists():
            deleted, size = self._cleanup_directory(
                self.analyzed_dir,
                days_to_keep_analyzed,
                recursive=False
            )
            total_deleted += deleted
            total_size_freed += size
            logger.info(f"✅ analyzed: Deleted {deleted} files ({size / 1024 / 1024:.2f} MB)")
        
        # Never cleanup raw/ - always keep latest
        logger.info(f"✅ raw: Keeping all latest files (no cleanup)")
        
        logger.info(f"🧹 Cleanup complete: {total_deleted} files deleted, {total_size_freed / 1024 / 1024:.2f} MB freed")
        
        return {
            "files_deleted": total_deleted,
            "bytes_freed": total_size_freed,
            "mb_freed": total_size_freed / 1024 / 1024
        }
    
    def _cleanup_directory(self, directory: Path, days_to_keep: int, recursive: bool = False) -> tuple:
        """
        Cleanup files older than specified days
        
        Returns:
            (files_deleted, bytes_freed)
        """
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        files_deleted = 0
        bytes_freed = 0
        
        # Get all CSV files
        if recursive:
            csv_files = list(directory.rglob("*.csv"))
        else:
            csv_files = list(directory.glob("*.csv"))
        
        for csv_file in csv_files:
            try:
                # Get file modification time
                file_mtime = datetime.fromtimestamp(csv_file.stat().st_mtime)
                
                # Delete if older than cutoff
                if file_mtime < cutoff_date:
                    file_size = csv_file.stat().st_size
                    csv_file.unlink()
                    files_deleted += 1
                    bytes_freed += file_size
                    logger.debug(f"🗑️ Deleted: {csv_file.name} (age: {(datetime.now() - file_mtime).days} days)")
            
            except Exception as e:
                logger.error(f"❌ Error deleting {csv_file}: {e}")
        
        return files_deleted, bytes_freed
    
    def get_storage_stats(self) -> dict:
        """Get current storage statistics"""
        raw_stats = self._get_dir_stats(self.raw_dir)
        analyzed_stats = self._get_dir_stats(self.analyzed_dir)
        smart_stats = self._get_dir_stats(self.smart_crawlers_dir, recursive=True)

        stats = {
            "raw": raw_stats,
            "analyzed": analyzed_stats,
            "smart_crawlers": smart_stats,
            "total_files": raw_stats["file_count"] + analyzed_stats["file_count"] + smart_stats["file_count"],
            "total_size_mb": raw_stats["size_mb"] + analyzed_stats["size_mb"] + smart_stats["size_mb"]
        }

        return stats
    
    def _get_dir_stats(self, directory: Path, recursive: bool = False) -> dict:
        """Get statistics for a directory"""
        if not directory.exists():
            return {"file_count": 0, "size_bytes": 0, "size_mb": 0}
        
        if recursive:
            csv_files = list(directory.rglob("*.csv"))
        else:
            csv_files = list(directory.glob("*.csv"))
        
        total_size = sum(f.stat().st_size for f in csv_files)
        
        return {
            "file_count": len(csv_files),
            "size_bytes": total_size,
            "size_mb": total_size / 1024 / 1024
        }


# Convenience function
def cleanup_old_data(days_smart: int = 30, days_analyzed: int = 7):
    """Run cleanup with default settings"""
    cleaner = DataCleanup()
    return cleaner.cleanup_old_files(days_smart, days_analyzed)


def get_storage_info():
    """Get current storage information"""
    cleaner = DataCleanup()
    return cleaner.get_storage_stats()


if __name__ == "__main__":
    # Run cleanup when executed directly
    print("🧹 InsightPulse Data Cleanup")
    print("=" * 50)
    
    # Show current stats
    cleaner = DataCleanup()
    stats = cleaner.get_storage_stats()
    print(f"\n📊 Current Storage:")
    print(f"  Raw: {stats['raw']['file_count']} files ({stats['raw']['size_mb']:.2f} MB)")
    print(f"  Analyzed: {stats['analyzed']['file_count']} files ({stats['analyzed']['size_mb']:.2f} MB)")
    print(f"  Smart Crawlers: {stats['smart_crawlers']['file_count']} files ({stats['smart_crawlers']['size_mb']:.2f} MB)")
    print(f"  TOTAL: {stats['total_files']} files ({stats['total_size_mb']:.2f} MB)")
    
    # Run cleanup
    print(f"\n🧹 Running cleanup...")
    result = cleaner.cleanup_old_files(days_to_keep_smart=30, days_to_keep_analyzed=7)
    
    print(f"\n✅ Cleanup Complete!")
    print(f"  Files deleted: {result['files_deleted']}")
    print(f"  Space freed: {result['mb_freed']:.2f} MB")

