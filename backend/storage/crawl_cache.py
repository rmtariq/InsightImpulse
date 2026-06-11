import sqlite3
import json
import logging
import os
from datetime import datetime
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

DB_PATH = os.path.join("data", "insightpulse.db")

def init_db():
    """Initialize the SQLite database with required tables"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Table for crawl history (to track when we last crawled what)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS crawl_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        query TEXT,
        platform TEXT,
        last_crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        item_count INTEGER,
        UNIQUE(query, platform)
    )
    ''')
    
    # Table for posts (the main data)
    # Using a composite of platform and post_id as a unique key might be tricky
    # because different scrapers use different ID formats. 
    # We'll use a unique hash or just rely on platform-specific IDs.
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS posts (
        platform TEXT,
        post_id TEXT,
        query TEXT,
        text TEXT,
        url TEXT,
        published_at TIMESTAMP,
        sentiment TEXT,
        sentiment_score REAL,
        emotion TEXT,
        likes INTEGER,
        shares INTEGER,
        comments_count INTEGER,
        views INTEGER,
        raw_data TEXT,
        PRIMARY KEY (platform, post_id)
    )
    ''')
    
    # Table for comments
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS comments (
        comment_id TEXT,
        post_id TEXT,
        platform TEXT,
        text TEXT,
        sentiment TEXT,
        sentiment_score REAL,
        raw_data TEXT,
        PRIMARY KEY (platform, comment_id)
    )
    ''')
    
    conn.commit()
    conn.close()
    logger.info(f"🗄️ Database initialized at {DB_PATH}")

def get_last_crawl_time(query: str, platform: str) -> Optional[datetime]:
    """Get the timestamp of the last successful crawl for a query/platform pair"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT last_crawled_at FROM crawl_history WHERE query = ? AND platform = ?",
        (query.lower(), platform.lower())
    )
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return datetime.fromisoformat(result[0])
    return None

def save_crawl_result(query: str, platform: str, posts: List[Dict[str, Any]]):
    """Save/Update crawled posts in the database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Update crawl history
    now = datetime.now().isoformat()
    cursor.execute('''
    INSERT OR REPLACE INTO crawl_history (query, platform, last_crawled_at, item_count)
    VALUES (?, ?, ?, ?)
    ''', (query.lower(), platform.lower(), now, len(posts)))
    
    # Helpers to coerce values into SQLite-compatible scalars
    def _scalar_str(v, default=''):
        if v is None:
            return default
        if isinstance(v, (dict, list)):
            try:
                return json.dumps(v, ensure_ascii=False, default=str)
            except Exception:
                return str(v)
        return str(v)

    def _scalar_int(v, default=0):
        try:
            if isinstance(v, bool):
                return int(v)
            if isinstance(v, (dict, list)):
                return default
            return int(v or 0)
        except (ValueError, TypeError):
            return default

    def _scalar_float(v, default=0.0):
        try:
            if isinstance(v, (dict, list)):
                return default
            return float(v or 0.0)
        except (ValueError, TypeError):
            return default

    # Save posts
    for post in posts:
        if not isinstance(post, dict):
            continue

        # Helper to get field with fallback
        def _g(k1, k2=None, default=None):
            val = post.get(k1, post.get(k2))
            return val if val is not None else default

        platform_name = _scalar_str(_g('Platform', 'platform', platform), platform)
        post_id = _g('ID', 'Post_ID', 'id')
        if not post_id or post_id == '-1':
            # Generate a stable ID from URL or Text if missing
            post_id = str(hash(_scalar_str(_g('URL', 'url', '')) + _scalar_str(_g('Text', 'text', ''))[:50]))

        try:
            cursor.execute('''
            INSERT OR REPLACE INTO posts (
                platform, post_id, query, text, url, published_at,
                sentiment, sentiment_score, emotion,
                likes, shares, comments_count, views, raw_data
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                platform_name,
                str(post_id),
                query.lower(),
                _scalar_str(_g('Text', 'text', '')),
                _scalar_str(_g('URL', 'url', '')),
                _scalar_str(_g('Date', 'date', now), now),
                _scalar_str(_g('Sentiment', 'sentiment'), ''),
                _scalar_float(_g('sentiment_score', 'score')),
                _scalar_str(_g('emotion_primary', 'emotion'), ''),
                _scalar_int(_g('likes', default=0)),
                _scalar_int(_g('shares', default=0)),
                _scalar_int(_g('comments_count', default=0)),
                _scalar_int(_g('views', default=0)),
                json.dumps(post, ensure_ascii=False, default=str)
            ))
        except Exception as e:
            logger.warning(f"⚠️ Skipping post insert ({platform_name}/{post_id}): {e}")
            continue

        # Save comments if present
        comments = post.get('comments', [])
        if not isinstance(comments, list):
            comments = []
        for comment in comments:
            if not isinstance(comment, dict):
                continue
            c_id = comment.get('id', str(hash(_scalar_str(comment.get('text', ''))[:100])))
            try:
                cursor.execute('''
                INSERT OR REPLACE INTO comments (
                    comment_id, post_id, platform, text, sentiment, sentiment_score, raw_data
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    str(c_id),
                    str(post_id),
                    platform_name,
                    _scalar_str(comment.get('text', '')),
                    _scalar_str(comment.get('sentiment'), ''),
                    _scalar_float(comment.get('sentiment_score')),
                    json.dumps(comment, ensure_ascii=False, default=str)
                ))
            except Exception as e:
                logger.warning(f"⚠️ Skipping comment insert ({platform_name}/{c_id}): {e}")
                continue

    conn.commit()
    conn.close()
    logger.info(f"✅ Saved {len(posts)} posts for {platform} into cache")

def get_cached_posts(query: str, platform: str, limit: int = 1000) -> List[Dict[str, Any]]:
    """Retrieve cached posts for a query/platform pair"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT raw_data FROM posts 
    WHERE query = ? AND platform = ?
    ORDER BY published_at DESC
    LIMIT ?
    ''', (query.lower(), platform.lower(), limit))
    
    rows = cursor.fetchall()
    conn.close()
    
    results = []
    for row in rows:
        results.append(json.loads(row['raw_data']))
        
    return results
