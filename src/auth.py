"""
Session helpers for Music Class Organizer.
get_session(environ) returns the current session dict or None.
create_session(...) builds a session payload; session persisted via signed cookie.
verify_teacher(email, password) -> teacher_id | None using teachers table.
verify_student_pin(teacher_id, pin) -> student_id | None; resolve_student_by_pin(pin) -> (teacher_id, student_id) | None.
create_parent_token(teacher_id, parent_id) -> token; consume_parent_token(token) -> (teacher_id, parent_id) | None.
"""

import os
import json
import base64
import hmac
import hashlib
import secrets
from datetime import datetime, timezone, timedelta

# Session cookie (signed)
SESSION_COOKIE_NAME = "mco_sid"


def _secret() -> bytes:
    raw = os.environ.get("SESSION_SECRET", "dev-secret-change-in-production")
    return raw.encode("utf-8")


def _encode_session(session: dict) -> str:
    payload = base64.urlsafe_b64encode(json.dumps(session, sort_keys=True).encode()).decode()
    sig = hmac.new(_secret(), payload.encode(), "sha256").hexdigest()[:16]
    return f"{payload}.{sig}"


def _decode_session(cookie_value: str) -> dict | None:
    if not cookie_value or "." not in cookie_value:
        return None
    payload, sig = cookie_value.rsplit(".", 1)
    expected = hmac.new(_secret(), payload.encode(), "sha256").hexdigest()[:16]
    if not hmac.compare_digest(sig, expected):
        return None
    try:
        return json.loads(base64.urlsafe_b64decode(payload.encode()).decode())
    except Exception:
        return None


def _get_cookie(handler, name: str) -> str | None:
    """Get first cookie value for name from Cookie header."""
    cookie_header = handler.headers.get("Cookie") or ""
    for part in cookie_header.split(";"):
        part = part.strip()
        if part.startswith(name + "="):
            return part[len(name) + 1 :].strip().strip('"')
    return None


def get_session(environ) -> dict | None:
    """
    Resolve current session from request (signed cookie).
    environ: request handler (BaseHTTPRequestHandler) with .headers.
    Returns session dict or None if no valid session.
    """
    cookie_value = _get_cookie(environ, SESSION_COOKIE_NAME)
    if not cookie_value:
        return None
    return _decode_session(cookie_value)


def create_session(role: str, teacher_id: int | None = None, **kwargs) -> dict:
    """
    Build a session payload for the given role and optional teacher_id.
    Use session_cookie_header_value(session) to get Set-Cookie value.
    """
    session = {"role": role, **kwargs}
    if teacher_id is not None:
        session["teacher_id"] = teacher_id
    return session


def session_cookie_header_value(session: dict) -> str:
    """Return value for Set-Cookie header (e.g. mco_sid=...; Path=/; HttpOnly)."""
    value = _encode_session(session)
    return f"{SESSION_COOKIE_NAME}={value}; Path=/; HttpOnly; SameSite=Lax"


def verify_teacher(email: str, password: str) -> int | None:
    """
    Check teachers table: if email exists and password matches, return teacher id else None.
    Passwords stored as SHA-256 hash (no salt) for minimal setup; upgrade to bcrypt later.
    """
    from db import get_connection

    email = (email or "").strip().lower()
    if not email or not password:
        return None
    password_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id, password_hash FROM teachers WHERE email = ?", (email,)
        ).fetchone()
        if not row or not hmac.compare_digest(row["password_hash"], password_hash):
            return None
        return row["id"]


def _pin_hash(pin: str) -> str:
    """SHA-256 hash of PIN for storage/comparison (no salt for minimal setup)."""
    return hashlib.sha256((pin or "").encode("utf-8")).hexdigest()


def verify_student_pin(teacher_id: int, pin: str) -> str | None:
    """
    Load PINs for teacher_id; if pin (hashed) matches any student's stored hash, return that student_id (name) else None.
    """
    import tenant_data
    pins = tenant_data.load_student_pins(teacher_id)
    if not pin or not pins:
        return None
    h = _pin_hash(pin)
    for student_id, stored in pins.items():
        if stored and hmac.compare_digest(stored, h):
            return student_id
    return None


def resolve_student_by_pin(pin: str) -> tuple[int, str] | None:
    """
    Resolve PIN to (teacher_id, student_id) by trying all tenants. Returns first match or None.
    """
    import tenant_data
    for tid in tenant_data.get_teacher_ids():
        sid = verify_student_pin(tid, pin)
        if sid is not None:
            return (tid, sid)
    return None


def set_student_pin(teacher_id: int, student_id: str, pin: str) -> bool:
    """
    Store hashed PIN for the given teacher and student. Returns True if saved.
    student_id is the student's name. Does not validate that student exists; caller should.
    """
    import tenant_data
    if not pin or not student_id:
        return False
    pins = tenant_data.load_student_pins(teacher_id)
    pins[student_id] = _pin_hash(pin)
    tenant_data.save_student_pins(teacher_id, pins)
    return True


def create_parent_token(teacher_id: int, parent_id: str) -> str:
    """
    Create a reusable magic-link token for a parent. parent_id is the parent name (string).
    Returns the token; store in parent_login_tokens with long expiry (1 year).
    Same link can be used multiple times until it expires.
    """
    from db import get_connection

    token = secrets.token_urlsafe(32)
    expires_at = (datetime.now(timezone.utc) + timedelta(days=365)).isoformat()
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO parent_login_tokens (token, teacher_id, parent_id, expires_at) VALUES (?, ?, ?, ?)",
            (token, teacher_id, parent_id, expires_at),
        )
        conn.commit()
    return token


def consume_parent_token(token: str) -> tuple[int, str] | None:
    """
    Validate a parent magic-link token (reusable). If valid and not expired,
    returns (teacher_id, parent_id); token is left in the table so the link can be used again.
    """
    from db import get_connection

    if not token or not token.strip():
        return None
    now = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        row = conn.execute(
            "SELECT teacher_id, parent_id FROM parent_login_tokens WHERE token = ? AND expires_at > ?",
            (token.strip(), now),
        ).fetchone()
        if not row:
            return None
        return (row["teacher_id"], row["parent_id"])
