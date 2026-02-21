"""
One-off: add a teacher to the DB for login testing.
Usage: python src/add_teacher.py <email> <password> [display_name]
Password is stored as SHA-256 hash (same as verify_teacher).
"""
import sys
import hashlib

from db import get_connection


def main():
    if len(sys.argv) < 3:
        print("Usage: python src/add_teacher.py <email> <password> [display_name]")
        sys.exit(1)
    email = sys.argv[1].strip().lower()
    password = sys.argv[2]
    display_name = sys.argv[3].strip() if len(sys.argv) > 3 else None
    password_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO teachers (email, password_hash, display_name) VALUES (?, ?, ?)",
            (email, password_hash, display_name or ""),
        )
        conn.commit()
    print(f"Added teacher: {email}")


if __name__ == "__main__":
    main()
