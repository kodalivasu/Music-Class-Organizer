"""One-off: update a teacher's email in the DB.
Run from repo root: python scripts/update_teacher_email.py
On Render (with persistent disk): DATA_DIR=/data python scripts/update_teacher_email.py
"""
import os
import sqlite3
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.getenv("DATA_DIR", str(BASE / "data")))
DB_PATH = DATA_DIR / "music_class.db"

OLD_EMAIL = "teacher@test.com"
NEW_EMAIL = "VaishnaviKondapalli@yahoo.com"


def main():
    if not DB_PATH.exists():
        print("DB not found:", DB_PATH)
        return
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "UPDATE teachers SET email = ? WHERE email = ?",
        (NEW_EMAIL, OLD_EMAIL),
    )
    conn.commit()
    n = conn.total_changes
    conn.close()
    print(f"Updated {n} row(s). Email {OLD_EMAIL} -> {NEW_EMAIL}")


if __name__ == "__main__":
    main()
