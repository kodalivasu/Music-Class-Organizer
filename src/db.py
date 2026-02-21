"""
SQLite DB for Music Class Organizer.
Initializes DB and teachers table (id, email, password_hash, display_name).
"""

import sqlite3
from pathlib import Path

# DB file next to project data
BASE_DIR = Path(__file__).parent.parent
DB_PATH = BASE_DIR / "data" / "music_class.db"


def get_connection():
    """Return a connection to the SQLite DB, creating file and schema if needed."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    init_schema(conn)
    return conn


def init_schema(conn: sqlite3.Connection) -> None:
    """Create tables if they do not exist."""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS teachers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            display_name TEXT
        );
        CREATE TABLE IF NOT EXISTS parent_login_tokens (
            token TEXT PRIMARY KEY,
            teacher_id INTEGER NOT NULL,
            parent_id TEXT NOT NULL,
            expires_at TEXT NOT NULL
        );
    """)
    conn.commit()
