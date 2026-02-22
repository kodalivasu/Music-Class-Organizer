"""Ensure the first teacher (id=1) exists with a fixed email and password.

All tenant data (students, contacts, media, music) is keyed by teacher_id 1.
Run this once so the teacher linked to that data can log in.

Run from repo root: python scripts/seed_first_teacher.py
With custom data dir: DATA_DIR=/data python scripts/seed_first_teacher.py
"""
import os
import hashlib
import sqlite3
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.getenv("DATA_DIR", str(BASE / "data")))
DB_PATH = DATA_DIR / "music_class.db"

EMAIL = "vaishnavikondapalli@yahoo.com"
PASSWORD = "Vaishnavi"
DISPLAY_NAME = "Vaishnavi Kondapalli"


def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    # Ensure teachers table exists (match db.py schema)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS teachers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            display_name TEXT
        );
    """)
    conn.commit()

    password_hash = hashlib.sha256(PASSWORD.encode("utf-8")).hexdigest()

    row = conn.execute("SELECT id, email FROM teachers WHERE id = 1").fetchone()
    if row:
        conn.execute(
            "UPDATE teachers SET email = ?, password_hash = ?, display_name = ? WHERE id = 1",
            (EMAIL, password_hash, DISPLAY_NAME),
        )
        conn.commit()
        print(f"Updated teacher id=1: email={EMAIL}, password=({len(PASSWORD)} chars)")
    else:
        # Insert with explicit id=1 so this teacher owns data under key "1" in JSON files
        try:
            conn.execute(
                "INSERT INTO teachers (id, email, password_hash, display_name) VALUES (1, ?, ?, ?)",
                (EMAIL, password_hash, DISPLAY_NAME),
            )
            conn.commit()
            print(f"Created teacher id=1: email={EMAIL}, password=({len(PASSWORD)} chars)")
        except sqlite3.IntegrityError as e:
            if "UNIQUE" in str(e):
                # id=1 taken by another insert race; try update again
                conn.execute(
                    "UPDATE teachers SET email = ?, password_hash = ?, display_name = ? WHERE id = 1",
                    (EMAIL, password_hash, DISPLAY_NAME),
                )
                conn.commit()
                print(f"Updated teacher id=1: email={EMAIL}, password=({len(PASSWORD)} chars)")
            else:
                raise

    conn.close()
    print("Done. Log in at /login with the email and password above.")


if __name__ == "__main__":
    main()
