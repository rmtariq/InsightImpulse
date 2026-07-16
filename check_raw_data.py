from pathlib import Path
import pandas as pd

print("=== RAW CRAWLED DATA ===\n")

ig_files = sorted(Path('data/smart_crawlers/instagram').glob('*.csv'), key=lambda p: p.stat().st_mtime, reverse=True)
if ig_files:
    print(f"Latest IG: {ig_files[0].name}")
    ig_raw = pd.read_csv(ig_files[0])
    print(f"Rows: {len(ig_raw)}, Cols: {len(ig_raw.columns)}")
    print(f"Columns: {list(ig_raw.columns)}")
    has_comments = any(c in ig_raw.columns for c in ['comments', 'comments_count', 'commentCount'])
    print(f"Has comments? {has_comments}\n")

yt_files = sorted(Path('data/smart_crawlers/youtube').glob('*.csv'), key=lambda p: p.stat().st_mtime, reverse=True)
if yt_files:
    print(f"Latest YT: {yt_files[0].name}")
    yt_raw = pd.read_csv(yt_files[0])
    print(f"Rows: {len(yt_raw)}, Cols: {len(yt_raw.columns)}")
    print(f"Columns: {list(yt_raw.columns)}")
    has_comments = any(c in yt_raw.columns for c in ['comments', 'comments_count', 'commentCount'])
    print(f"Has comments? {has_comments}")
