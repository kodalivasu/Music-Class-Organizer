"""
Tenant-scoped data layer for Music Class Organizer (Phase 3).

All load/save functions take teacher_id and operate only on that tenant's data.
JSON files use format: { "teacher_id": data, ... } so one file holds all tenants.
Legacy single-tenant files are treated as teacher_id 1 on first read.
"""

import json
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"


def _load_raw(filename, default=None):
    path = DATA_DIR / filename
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return default if default is not None else {}


def _save_raw(filename, data):
    path = DATA_DIR / filename
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _is_tenant_key(k):
    """True if key looks like a teacher id (numeric string)."""
    return isinstance(k, str) and k.isdigit()


def _migrate_attendance_legacy(raw):
    """If raw is legacy { date: {...} }, return { "1": raw } else return raw."""
    if not raw or not isinstance(raw, dict):
        return raw
    # Legacy: top-level keys are dates (e.g. "2026-02-09"), not teacher ids
    first = next(iter(raw.keys()), None)
    if first and not _is_tenant_key(first):
        return {"1": raw}
    return raw


# ---------------------------------------------------------------------------
# Attendance
# ---------------------------------------------------------------------------

def load_attendance(teacher_id):
    """
    Load attendance for the given teacher.
    Returns dict of date -> { "students": [...], "notes": "..." }.
    """
    if teacher_id is None:
        return {}
    raw = _load_raw("attendance.json", {})
    raw = _migrate_attendance_legacy(raw)
    return raw.get(str(teacher_id), {})


def save_attendance(teacher_id, data):
    """Save attendance for the given teacher. Merges into file by teacher key."""
    if teacher_id is None:
        return
    raw = _load_raw("attendance.json", {})
    raw = _migrate_attendance_legacy(raw)
    raw[str(teacher_id)] = data
    _save_raw("attendance.json", raw)


# ---------------------------------------------------------------------------
# Practice log
# ---------------------------------------------------------------------------

def _migrate_practice_log_legacy(raw):
    """If raw is legacy { student: entries }, return { "1": raw } else return raw."""
    if not raw or not isinstance(raw, dict):
        return raw
    first = next(iter(raw.keys()), None)
    if first and not _is_tenant_key(first):
        return {"1": raw}
    return raw


def load_practice_log(teacher_id):
    """
    Load practice log for the given teacher.
    Returns dict of student name -> list of { "date", "duration", "items" }.
    Migrates old string-date format to entry dicts on read and saves once.
    """
    if teacher_id is None:
        return {}
    raw = _load_raw("practice_log.json", {})
    raw = _migrate_practice_log_legacy(raw)
    data = raw.get(str(teacher_id), {})
    out = {}
    migrated = False
    for student, entries in list(data.items()):
        if entries and isinstance(entries[0], str):
            out[student] = [{"date": d, "duration": 0, "items": ""} for d in entries]
            migrated = True
        else:
            out[student] = entries
    if migrated:
        save_practice_log(teacher_id, out)
        return out
    return data


def save_practice_log(teacher_id, data):
    """Save practice log for the given teacher."""
    if teacher_id is None:
        return
    raw = _load_raw("practice_log.json", {})
    raw = _migrate_practice_log_legacy(raw)
    raw[str(teacher_id)] = data
    _save_raw("practice_log.json", raw)


# ---------------------------------------------------------------------------
# Assignments
# ---------------------------------------------------------------------------

def _migrate_assignments_legacy(raw):
    """If raw is a list (legacy), return { "1": raw } else return raw."""
    if isinstance(raw, list):
        return {"1": raw}
    return raw if raw else {}


def load_assignments(teacher_id):
    """Load assignments for the given teacher. Returns list of assignment dicts."""
    if teacher_id is None:
        return []
    raw = _load_raw("assignments.json", [])
    raw = _migrate_assignments_legacy(raw)
    return raw.get(str(teacher_id), [])


def save_assignments(teacher_id, data):
    """Save assignments for the given teacher."""
    if teacher_id is None:
        return
    raw = _load_raw("assignments.json", [])
    raw = _migrate_assignments_legacy(raw)
    raw[str(teacher_id)] = data
    _save_raw("assignments.json", raw)


# ---------------------------------------------------------------------------
# Scheduled events
# ---------------------------------------------------------------------------

def _migrate_events_legacy(raw):
    """If raw is a list (legacy), return { "1": raw } else return raw."""
    if isinstance(raw, list):
        return {"1": raw}
    return raw if raw else {}


def load_scheduled_events(teacher_id):
    """Load scheduled events for the given teacher. Returns list of event dicts."""
    if teacher_id is None:
        return []
    raw = _load_raw("scheduled_events.json", [])
    raw = _migrate_events_legacy(raw)
    return raw.get(str(teacher_id), [])


def save_scheduled_events(teacher_id, data):
    """Save scheduled events for the given teacher."""
    if teacher_id is None:
        return
    raw = _load_raw("scheduled_events.json", [])
    raw = _migrate_events_legacy(raw)
    raw[str(teacher_id)] = data
    _save_raw("scheduled_events.json", raw)


# ---------------------------------------------------------------------------
# People (teacher, students, families)
# ---------------------------------------------------------------------------

def _migrate_people_legacy(raw):
    """If raw has keys like teacher/students/families (not tenant ids), return { "1": raw }."""
    if not raw or not isinstance(raw, dict):
        return raw
    first = next(iter(raw.keys()), None)
    if first and not _is_tenant_key(first):
        return {"1": raw}
    return raw


def load_people(teacher_id):
    """Load people (teacher, students, families) for the given teacher."""
    if teacher_id is None:
        return {}
    raw = _load_raw("people.json", {})
    raw = _migrate_people_legacy(raw)
    return raw.get(str(teacher_id), {})


def save_people(teacher_id, data):
    """Save people for the given teacher."""
    if teacher_id is None:
        return
    raw = _load_raw("people.json", {})
    raw = _migrate_people_legacy(raw)
    raw[str(teacher_id)] = data
    _save_raw("people.json", raw)


def get_teacher_ids():
    """Return list of teacher ids that have data in people.json (for PIN lookup across tenants)."""
    raw = _load_raw("people.json", {})
    raw = _migrate_people_legacy(raw)
    return [int(k) for k in raw.keys() if _is_tenant_key(k)]


# ---------------------------------------------------------------------------
# Student PINs (for student login)
# ---------------------------------------------------------------------------

def _migrate_student_pins_legacy(raw):
    """If raw has non-tenant keys, return { "1": raw } else return raw."""
    if not raw or not isinstance(raw, dict):
        return raw
    first = next(iter(raw.keys()), None)
    if first and not _is_tenant_key(first):
        return {"1": raw}
    return raw


def load_student_pins(teacher_id):
    """Load student PIN hashes for the given teacher. Returns dict student_name -> pin_hash."""
    if teacher_id is None:
        return {}
    raw = _load_raw("student_pins.json", {})
    raw = _migrate_student_pins_legacy(raw)
    return raw.get(str(teacher_id), {})


def save_student_pins(teacher_id, data):
    """Save student PIN hashes for the given teacher. data: dict student_name -> pin_hash."""
    if teacher_id is None:
        return
    raw = _load_raw("student_pins.json", {})
    raw = _migrate_student_pins_legacy(raw)
    raw[str(teacher_id)] = data
    _save_raw("student_pins.json", raw)


# ---------------------------------------------------------------------------
# Audio categories (music library metadata)
# ---------------------------------------------------------------------------

def _migrate_categories_legacy(raw):
    """If raw has non-numeric top-level keys (filenames), return { "1": raw }."""
    if not raw or not isinstance(raw, dict):
        return raw
    first = next(iter(raw.keys()), None)
    if first and not _is_tenant_key(first):
        return {"1": raw}
    return raw


def load_audio_categories(teacher_id):
    """Load audio categories for the given teacher."""
    if teacher_id is None:
        return {}
    raw = _load_raw("audio_categories.json", {})
    raw = _migrate_categories_legacy(raw)
    return raw.get(str(teacher_id), {})


def save_audio_categories(teacher_id, data):
    """Save audio categories for the given teacher."""
    if teacher_id is None:
        return
    raw = _load_raw("audio_categories.json", {})
    raw = _migrate_categories_legacy(raw)
    raw[str(teacher_id)] = data
    _save_raw("audio_categories.json", raw)


# ---------------------------------------------------------------------------
# Parent profiles
# ---------------------------------------------------------------------------

def _migrate_parent_profiles_legacy(raw):
    """If raw has non-numeric top-level keys (parent names), return { "1": raw }."""
    if not raw or not isinstance(raw, dict):
        return raw
    first = next(iter(raw.keys()), None)
    if first and not _is_tenant_key(first):
        return {"1": raw}
    return raw


def load_parent_profiles(teacher_id):
    """Load parent profiles for the given teacher."""
    if teacher_id is None:
        return {}
    raw = _load_raw("parent_profiles.json", {})
    raw = _migrate_parent_profiles_legacy(raw)
    return raw.get(str(teacher_id), {})


def save_parent_profiles(teacher_id, data):
    """Save parent profiles for the given teacher."""
    if teacher_id is None:
        return
    raw = _load_raw("parent_profiles.json", {})
    raw = _migrate_parent_profiles_legacy(raw)
    raw[str(teacher_id)] = data
    _save_raw("parent_profiles.json", raw)
