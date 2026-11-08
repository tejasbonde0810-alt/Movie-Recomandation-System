"""
SQLite database and cache service.
Provides thread-safe local caching for TMDB API queries and processed metadata.
"""
import sqlite3
import json
import time
import os
from pathlib import Path
from config import Config

def get_db_connection():
    """Create a connection to the SQLite cache database."""
    Config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(Config.DATABASE_PATH, timeout=10.0)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize SQLite database tables if not already present."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Table for raw API response caching
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS api_cache (
                cache_key TEXT PRIMARY KEY,
                url TEXT NOT NULL,
                response_json TEXT NOT NULL,
                created_at INTEGER NOT NULL,
                expires_at INTEGER NOT NULL
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_api_cache_expires ON api_cache(expires_at)")

        # Table for cached processed titles and metadata soups
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS title_metadata (
                media_type TEXT NOT NULL,
                id INTEGER NOT NULL,
                title TEXT NOT NULL,
                original_language TEXT,
                release_year TEXT,
                genre_names TEXT,
                vote_average REAL,
                overview TEXT,
                metadata_soup TEXT,
                updated_at INTEGER NOT NULL,
                PRIMARY KEY (media_type, id)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_title_lang ON title_metadata(original_language)")
        conn.commit()

def get_cached_api_response(cache_key: str):
    """Retrieve an unexpired cached API response."""
    now = int(time.time())
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT response_json FROM api_cache WHERE cache_key = ? AND expires_at > ?",
                (cache_key, now)
            )
            row = cursor.fetchone()
            if row:
                return json.loads(row["response_json"])
    except Exception:
        pass
    return None

def set_cached_api_response(cache_key: str, url: str, data: dict, ttl_seconds: int = Config.CACHE_EXPIRATION_SECONDS):
    """Store an API response in the local cache."""
    now = int(time.time())
    expires_at = now + ttl_seconds
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO api_cache (cache_key, url, response_json, created_at, expires_at)
                VALUES (?, ?, ?, ?, ?)
            """, (cache_key, url, json.dumps(data), now, expires_at))
            conn.commit()
    except Exception:
        pass

def save_title_metadata(media_type: str, item_id: int, title: str, original_language: str,
                        release_year: str, genre_names: str, vote_average: float,
                        overview: str, metadata_soup: str):
    """Persist structured title metadata for fast local access and recommender reuse."""
    now = int(time.time())
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO title_metadata 
                (media_type, id, title, original_language, release_year, genre_names, vote_average, overview, metadata_soup, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (media_type, item_id, title, original_language, release_year, genre_names, vote_average, overview, metadata_soup, now))
            conn.commit()
    except Exception:
        pass

def get_title_metadata(media_type: str, item_id: int):
    """Retrieve cached metadata for a title."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM title_metadata WHERE media_type = ? AND id = ?", (media_type, item_id))
            row = cursor.fetchone()
            if row:
                return dict(row)
    except Exception:
        pass
    return None

def get_cached_titles_count():
    """Return count of cached API queries and titles."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM api_cache")
            api_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM title_metadata")
            titles_count = cursor.fetchone()[0]
            return {"cached_api_responses": api_count, "cached_titles": titles_count}
    except Exception:
        return {"cached_api_responses": 0, "cached_titles": 0}
