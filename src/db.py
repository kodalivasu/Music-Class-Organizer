"""
SQLite DB for Music Class Organizer.
Initializes DB and teachers table (id, email, password_hash, display_name).
"""

import os
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
_DATA_DIR_ENV = os.getenv("DATA_DIR")
DATA_DIR = Path(_DATA_DIR_ENV) if _DATA_DIR_ENV else BASE_DIR / "data"
DB_PATH = DATA_DIR / "music_class.db"


def get_connection():
    """Return a connection to the SQLite DB, creating file and schema if needed."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    init_schema(conn)
    return conn


def teacher_count() -> int:
    """Return the number of teachers in the DB (for first-teacher signup)."""
    with get_connection() as conn:
        return conn.execute("SELECT COUNT(*) FROM teachers").fetchone()[0]


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
