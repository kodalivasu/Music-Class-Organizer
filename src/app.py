
"""
Music Class Organizer — Web UI (Phase 2)

Role-based web app for a Hindustani classical music class.

Teacher dashboard features:
  - In-browser audio recording (MediaRecorder API)
  - Browse & assign practice recordings to students
  - Mark attendance by date with student checklist
  - Create / schedule / share events
  - Full music library with drag-drop editing

Student/Parent dashboards: coming soon (Phase 2b)

Run: python src/app.py
Then open: http://localhost:8000
"""

import hashlib
import html
import json
import os
import sys
import base64
from pathlib import Path
from datetime import datetime, date
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

from auth import get_session, create_session, verify_teacher, session_cookie_header_value, resolve_student_by_pin, set_student_pin, consume_parent_token, create_parent_token, SESSION_COOKIE_NAME
import tenant_data
from db import get_connection, teacher_count

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Optional: Gemini AI for Phase 3 features
try:
    import google.generativeai as genai
    _api_key = os.getenv("GOOGLE_API_KEY")
    if _api_key:
        genai.configure(api_key=_api_key)
        AI_AVAILABLE = True
        AI_MODEL = "gemini-2.0-flash"
        print(f"[AI] Gemini API ready (model: {AI_MODEL})")
    else:
        AI_AVAILABLE = False
        print("[AI] GOOGLE_API_KEY not set — AI features disabled")
except ImportError:
    AI_AVAILABLE = False
    print("[AI] google-generativeai not installed — AI features disabled")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).parent.parent
_DATA_DIR_ENV = os.getenv("DATA_DIR")
_MEDIA_DIR_ENV = os.getenv("MEDIA_DIR")
DATA_DIR = Path(_DATA_DIR_ENV) if _DATA_DIR_ENV else BASE_DIR / "data"
MEDIA_DIR = Path(_MEDIA_DIR_ENV) if _MEDIA_DIR_ENV else BASE_DIR / "media"

# ---------------------------------------------------------------------------
# Data helpers
# ---------------------------------------------------------------------------

def _load_json(filename, default=None):
    path = DATA_DIR / filename
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return default if default is not None else {}

def _save_json(filename, data):
    path = DATA_DIR / filename
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def load_audio_categories():
    return _load_json("audio_categories.json", {})

def save_audio_categories(categories):
    _save_json("audio_categories.json", categories)

def load_people():
    return _load_json("people.json", {})

def load_attendance():
    return _load_json("attendance.json", {})

def save_attendance(data):
    _save_json("attendance.json", data)

def load_assignments():
    return _load_json("assignments.json", [])

def save_assignments(data):
    _save_json("assignments.json", data)

def load_scheduled_events():
    return _load_json("scheduled_events.json", [])

def save_scheduled_events(data):
    _save_json("scheduled_events.json", data)

def load_practice_log():
    """Load practice log, migrating old format if needed.
    Old format: { "Student": ["2026-01-01", ...] }
    New format: { "Student": [{"date": "2026-01-01", "duration": 30, "items": "Bhupali Bandish"}, ...] }
    """
    data = _load_json("practice_log.json", {})
    migrated = False
    for student, entries in data.items():
        if entries and isinstance(entries[0], str):
            data[student] = [{"date": d, "duration": 0, "items": ""} for d in entries]
            migrated = True
    if migrated:
        _save_json("practice_log.json", data)
    return data

def save_practice_log(data):
    _save_json("practice_log.json", data)

def get_practice_dates(entries):
    """Extract just date strings from practice log entries (works with both formats)."""
    if not entries:
        return []
    if isinstance(entries[0], str):
        return entries
    return [e["date"] for e in entries if isinstance(e, dict)]

def load_parent_profiles():
    return _load_json("parent_profiles.json", {})

def save_parent_profiles(data):
    _save_json("parent_profiles.json", data)

def get_parent_names(teacher_id=None):
    """Get list of parent names from people.json families."""
    people = tenant_data.load_people(teacher_id) if teacher_id is not None else load_people()
    return [f.get("parent", "Unknown") for f in people.get("families", [])]

# ---------------------------------------------------------------------------
# AI Query Helper
# ---------------------------------------------------------------------------

def build_music_context(teacher_id=None):
    """Build a summary of the music library for the AI to reference."""
    categories = tenant_data.load_audio_categories(teacher_id) if teacher_id is not None else load_audio_categories()
    if not categories:
        return "The music library is currently empty."

    # Summarise by raga
    by_raga = {}
    for filename, info in categories.items():
        raga = info.get("raga", "Unknown")
        by_raga.setdefault(raga, []).append(info | {"filename": filename})

    lines = [f"Music Library Summary — {len(categories)} recordings across {len(by_raga)} ragas:\n"]
    for raga, items in sorted(by_raga.items()):
        types = {}
        taals = set()
        paltaa_count = 0
        for it in items:
            ct = it.get("composition_type", "Unknown")
            types[ct] = types.get(ct, 0) + 1
            if it.get("taal"):
                taals.add(it["taal"])
            if it.get("paltaas"):
                paltaa_count += 1
        type_str = ", ".join(f"{v} {k}" for k, v in sorted(types.items()))
        taal_str = ", ".join(sorted(taals)) if taals else "none identified"
        lines.append(f"- Raga {raga}: {len(items)} recordings ({type_str}). Taals: {taal_str}. Paltaas: {paltaa_count}.")
    return "\n".join(lines)

def build_student_context(teacher_id=None):
    """Build context about students, attendance, practice for AI."""
    students = get_student_names(teacher_id)
    attendance = tenant_data.load_attendance(teacher_id) if teacher_id is not None else load_attendance()
    practice = tenant_data.load_practice_log(teacher_id) if teacher_id is not None else load_practice_log()
    assignments = tenant_data.load_assignments(teacher_id) if teacher_id is not None else load_assignments()

    lines = [f"Students: {', '.join(students)}"]
    lines.append(f"Total class dates on record: {len(attendance)}")
    if attendance:
        dates = sorted(attendance.keys())
        lines.append(f"Class date range: {dates[0]} to {dates[-1]}")
    active = [a for a in assignments if a.get("status") == "active"]
    if active:
        lines.append(f"Active practice assignments: {len(active)}")
    for s in students:
        dates = practice.get(s, [])
        if dates:
            lines.append(f"  {s}: {len(dates)} practice days logged")
    return "\n".join(lines)

def ask_ai(query, teacher_id=None):
    """Send a natural language query to Gemini with music library context."""
    if not AI_AVAILABLE:
        return {"answer": "AI features are not available. Please set GOOGLE_API_KEY in your .env file and install google-generativeai.", "sources": []}

    music_ctx = build_music_context(teacher_id)
    student_ctx = build_student_context(teacher_id)
    categories = tenant_data.load_audio_categories(teacher_id) if teacher_id is not None else load_audio_categories()

    system_prompt = f"""You are a helpful AI assistant for a Hindustani classical music class.
You help students, parents, and the teacher with questions about their music library, practice, and Hindustani classical music in general.

MUSIC LIBRARY DATA:
{music_ctx}

CLASS DATA:
{student_ctx}

HINDUSTANI MUSIC KNOWLEDGE:
- Ragas: melodic frameworks with specific ascending/descending note patterns, associated times of day and moods
- Composition Types: Alaap (slow improvised exploration), Bandish (composed song with lyrics), Taan (fast melodic runs)
- Paltaas/Sargam Exercises: practice patterns using note names (Sa Re Ga Ma Pa Dha Ni)
- Taals: rhythmic cycles — Teentaal (16 beats), Ektaal (12), Jhaptaal (10), Rupak (7), Dadra (6), Keherwa (8)

INSTRUCTIONS:
- Answer questions about the music library by referencing actual recordings in the data
- For music theory questions, provide clear, educational explanations suitable for students learning Hindustani classical music
- When a user asks about a raga, mention: its notes, time of day, mood, and any recordings in the library
- When suggesting YouTube or educational resources, provide specific search terms the user can use
- Keep answers concise but informative (2-4 paragraphs max)
- Use markdown formatting for readability
- If asked about recordings, reference actual filenames and their categorisation from the library data"""

    ai_models = ["gemini-2.0-flash", "gemini-2.5-flash"]
    last_error = ""
    for model_name in ai_models:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content([
                {"role": "user", "parts": [system_prompt + "\n\nUser question: " + query]}
            ])
            answer = response.text

            # Extract any raga names mentioned for resource links
            mentioned_ragas = []
            for filename, info in categories.items():
                raga = info.get("raga", "Unknown")
                if raga != "Unknown" and raga.lower() in answer.lower() and raga not in mentioned_ragas:
                    mentioned_ragas.append(raga)

            return {"answer": answer, "mentioned_ragas": mentioned_ragas}
        except Exception as e:
            last_error = str(e)
            continue  # Try next model

    return {"answer": f"Sorry, AI is temporarily unavailable (quota limit reached). Please try again in a minute.\n\nDetails: {last_error}", "mentioned_ragas": []}

def get_events(teacher_id=None):
    """Event media folders for the given teacher. When teacher_id is set, use media/events/{teacher_id}/."""
    if teacher_id is not None:
        events_dir = MEDIA_DIR / "events" / str(teacher_id)
    else:
        events_dir = MEDIA_DIR / "events"
    events = []
    if events_dir.exists():
        for d in sorted(events_dir.iterdir()):
            if d.is_dir():
                files = list(d.iterdir())
                photos = [f.name for f in files if f.suffix.lower() in {'.jpg', '.jpeg', '.png', '.gif', '.webp'}]
                videos = [f.name for f in files if f.suffix.lower() in {'.mp4', '.mov', '.avi', '.webm'}]
                events.append({
                    "folder": d.name,
                    "photos": photos,
                    "videos": videos,
                    "total": len(photos) + len(videos),
                })
    return events

def get_audio_files(teacher_id=None):
    """Audio file names for the given teacher. When teacher_id is set, use media/audio/{teacher_id}/."""
    if teacher_id is not None:
        audio_dir = MEDIA_DIR / "audio" / str(teacher_id)
    else:
        audio_dir = MEDIA_DIR / "audio"
    if audio_dir.exists():
        return sorted([
            f.name for f in audio_dir.iterdir()
            if f.suffix.lower() in {'.m4a', '.mp3', '.opus', '.wav', '.ogg', '.amr', '.webm'}
        ])
    return []

def get_student_names(teacher_id=None):
    """Get list of student names from people.json."""
    people = tenant_data.load_people(teacher_id) if teacher_id is not None else load_people()
    return people.get("students", [])

def add_student(name, teacher_id=None):
    """Add a student to people.json (tenant-scoped when teacher_id is set)."""
    if teacher_id is not None:
        people = tenant_data.load_people(teacher_id)
        students = people.get("students", [])
        if name not in students:
            students.append(name)
            people["students"] = students
            tenant_data.save_people(teacher_id, people)
            return True
        return False
    people = load_people()
    students = people.get("students", [])
    if name not in students:
        students.append(name)
        people["students"] = students
        _save_json("people.json", people)
        return True
    return False


def remove_student(name, teacher_id):
    """Remove a student from people and their PIN. Returns True if removed."""
    people = tenant_data.load_people(teacher_id)
    students = people.get("students", [])
    if name not in students:
        return False
    people["students"] = [s for s in students if s != name]
    tenant_data.save_people(teacher_id, people)
    pins = tenant_data.load_student_pins(teacher_id)
    if name in pins:
        del pins[name]
        tenant_data.save_student_pins(teacher_id, pins)
    return True

# ---------------------------------------------------------------------------
# HTML builders — shared
# ---------------------------------------------------------------------------

def build_events_html(events, teacher_id=None):
    """Build event gallery HTML. When teacher_id is set, media URLs use /media/events/{teacher_id}/..."""
    prefix = f"/media/events/{teacher_id}/" if teacher_id is not None else "/media/events/"
    html = ""
    for event in reversed(events):
        name = event["folder"].replace("_", " ").replace("-", " ")
        folder_path = prefix + event["folder"] + "/"
        html += f"""
        <div class="card">
            <div class="card-header" onclick="this.nextElementSibling.classList.toggle('collapsed')">
                <div class="card-header-left"><h3>{name}</h3></div>
                <span class="badge">{event['total']} files</span>
            </div>
            <div class="card-body">
                <div class="gallery">
        """
        for photo in event["photos"]:
            html += f'<img src="{folder_path}{photo}" loading="lazy" onclick="openLightbox(this.src)" alt="{photo}">'
        for video in event["videos"]:
            html += f'<video controls preload="none" src="{folder_path}{video}"></video>'
        html += "</div></div></div>"
    return html

def build_people_html(people, role=None, teacher_id=None):
    teacher = people.get("teacher", {})
    families = people.get("families", [])
    show_teacher_actions = role == "teacher"
    output = f"""
    <div class="card teacher-section">
        <div class="card-header"><div class="card-header-left"><h3>Teacher</h3></div></div>
        <div class="card-body">
            <div class="person teacher-card">
                <div class="person-avatar teacher-avatar">
                    <svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/></svg>
                </div>
                <div class="person-info">
                    <div class="person-name">{teacher.get('name', 'Unknown')}</div>
                    <div class="person-meta">{teacher.get('messages', 0)} messages</div>
                </div>
            </div>
        </div>
    </div>
    <div class="card">
        <div class="card-header"><div class="card-header-left"><h3>Families</h3></div>
            <span class="badge">{len(families)}</span></div>
        <div class="card-body">
    """
    if show_teacher_actions:
        output += """
        <div style="margin-bottom:12px;">
            <input type="text" id="add-contact-name" class="modal-input" placeholder="Parent / contact name" style="max-width:200px; margin-right:8px;">
            <button type="button" class="save-btn btn-add-contact">Add contact</button>
        </div>"""
    output += "<div class=\"people-grid\">"
    for person in families:
        name = person.get("parent", "Unknown")
        name_attr = html.escape(name, quote=True)
        initials = "".join(w[0].upper() for w in name.split() if w)[:2]
        person_role = person.get("role", "parent")
        msgs = person.get("messages", 0)
        link_btn = ""
        remove_btn = ""
        if show_teacher_actions:
            link_btn = f' <button type="button" class="btn-generate-parent-link save-btn" style="margin-left:8px; padding:6px 10px; font-size:12px;" data-parent="{name_attr}" title="Generate login link for this parent">Generate login link</button>'
            remove_btn = f' <button type="button" class="btn-remove-contact save-btn" style="margin-left:6px; padding:6px 10px; font-size:12px; background:#c44; border-color:#a33;" data-parent="{name_attr}" title="Remove contact">Remove</button>'
        output += f"""
            <div class="person person-contact" data-parent="{name_attr}">
                <div class="person-avatar {'student-avatar' if person_role == 'student' else ''}">{initials}</div>
                <div class="person-info">
                    <div class="person-name-wrap"><span class="person-name">{html.escape(name)}</span>{link_btn}{remove_btn}</div>
                    <div class="person-meta"><span class="role-badge {'student-badge' if person_role == 'student' else ''}">{person_role}</span> &middot; {msgs} msgs</div>
                </div>
            </div>
        """
    output += "</div></div></div>"
    return output

# ---------------------------------------------------------------------------
# HTML builder — Teacher Dashboard
# ---------------------------------------------------------------------------

def build_teacher_dashboard(categories, events, people, audio_files, teacher_id=None):
    total_audio = len(audio_files)
    categorized = len(categories)
    total_events = len(events)
    total_event_files = sum(e["total"] for e in events)
    families = people.get("families", [])
    ragas = sorted(set(v.get("raga", "Unknown") for v in categories.values() if v.get("raga") and v.get("raga") != "Unknown"))
    attendance = tenant_data.load_attendance(teacher_id) if teacher_id is not None else load_attendance()
    assignments = tenant_data.load_assignments(teacher_id) if teacher_id is not None else load_assignments()
    scheduled = tenant_data.load_scheduled_events(teacher_id) if teacher_id is not None else load_scheduled_events()

    today = date.today().strftime("%A, %B %d, %Y")

    # Count active assignments
    active_assignments = len([a for a in assignments if a.get("status", "active") == "active"])

    # Recent attendance
    att_dates = sorted(attendance.keys(), reverse=True)
    last_class = att_dates[0] if att_dates else "No records yet"

    teacher_info = people.get("teacher", {})
    teacher_venmo = teacher_info.get("venmo", "@Teacher")
    _default_class = "Hindustani Classical Music — " + (teacher_info.get("name", "Teacher") + "'s Music School")
    teacher_school_name = teacher_info.get("school_name") or _default_class

    students = people.get("students", [])
    student_pin_rows = ""
    for s in sorted(students):
        safe_name = html.escape(s, quote=True)
        student_pin_rows += f"""
                <div class="student-pin-row" data-student-name="{safe_name}" style="display:flex; gap:8px; align-items:center; margin-bottom:8px;">
                    <span class="student-pin-name" style="min-width:120px;">{html.escape(s)}</span>
                    <input type="password" class="modal-input pin-input" placeholder="PIN" inputmode="numeric" maxlength="8" autocomplete="off" style="width:80px;">
                    <button type="button" class="save-btn" onclick="setStudentPin(this)">Set PIN</button>
                    <button type="button" class="btn-remove-student save-btn" style="padding:6px 10px; font-size:12px; background:#c44; border-color:#a33;" data-student-name="{safe_name}" title="Remove student">Remove</button>
                </div>"""

    return f"""
    <div class="teacher-welcome">
        <div class="welcome-text">
            <h2>Welcome back, Teacher</h2>
            <p class="welcome-date">{today}</p>
        </div>
        <button class="settings-btn" onclick="toggleTeacherSettings()" title="Settings">
            <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor"><path d="M19.14 12.94c.04-.3.06-.61.06-.94 0-.32-.02-.64-.07-.94l2.03-1.58c.18-.14.23-.41.12-.61l-1.92-3.32c-.12-.22-.37-.29-.59-.22l-2.39.96c-.5-.38-1.03-.7-1.62-.94l-.36-2.54c-.04-.24-.24-.41-.48-.41h-3.84c-.24 0-.43.17-.47.41l-.36 2.54c-.59.24-1.13.57-1.62.94l-2.39-.96c-.22-.08-.47 0-.59.22L2.74 8.87c-.12.21-.08.47.12.61l2.03 1.58c-.05.3-.07.62-.07.94s.02.64.07.94l-2.03 1.58c-.18.14-.23.41-.12.61l1.92 3.32c.12.22.37.29.59.22l2.39-.96c.5.38 1.03.7 1.62.94l.36 2.54c.05.24.24.41.48.41h3.84c.24 0 .44-.17.47-.41l.36-2.54c.59-.24 1.13-.56 1.62-.94l2.39.96c.22.08.47 0 .59-.22l1.92-3.32c.12-.22.07-.47-.12-.61l-2.01-1.58zM12 15.6c-1.98 0-3.6-1.62-3.6-3.6s1.62-3.6 3.6-3.6 3.6 1.62 3.6 3.6-1.62 3.6-3.6 3.6z"/></svg>
        </button>
    </div>
    <div id="teacher-settings-panel" style="display:none">
        <div class="settings-card">
            <div class="modal-row">
                <label class="modal-label">Music class name</label>
                <div style="display:flex; gap:8px;">
                    <input type="text" id="school-name-input" class="modal-input" value="{html.escape(teacher_school_name)}" placeholder="e.g. Hindustani Classical Music — Vaishnavi Kondapalli's Music School">
                </div>
                <p style="font-size:11px; color:#6a5a4a; margin-top:4px;">Shown in the header for your class</p>
            </div>
            <div class="modal-row">
                <label class="modal-label">Venmo Handle</label>
                <div style="display:flex; gap:8px;">
                    <input type="text" id="venmo-input" class="modal-input" value="{teacher_venmo}" placeholder="@YourVenmo" autocomplete="off" inputmode="text" autocorrect="off" autocapitalize="off" spellcheck="false">
                    <button class="save-btn" style="padding:12px 18px; white-space:nowrap; touch-action:manipulation;" onclick="saveTeacherSettings()">Save</button>
                </div>
                <p style="font-size:11px; color:#6a5a4a; margin-top:4px;">Parents will see this as their payment link</p>
            </div>
            <div class="modal-row" style="margin-top:16px;">
                <h3 class="section-title">Students</h3>
                <p style="font-size:12px; color:#6a5a4a; margin-bottom:10px;">Add students and set PINs for login at /login/student</p>
                <div style="display:flex; gap:8px; align-items:center; margin-bottom:12px;">
                    <input type="text" id="settings-add-student-name" class="modal-input" placeholder="Student name" style="max-width:180px;">
                    <button type="button" class="save-btn" onclick="addStudentFromSettings()">Add student</button>
                </div>
                <div id="student-pins-list" class="student-pins-list">
{student_pin_rows}
                </div>
            </div>
        </div>
    </div>

    <div id="teacher-dash-main">
    <!-- Hero Action Cards -->
    <div class="action-cards">

        <!-- 1. Music & Practice -->
        <div class="action-card music-action-card">
            <div class="action-card-header">
                <div class="action-card-icon music-icon">
                    <svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 3v10.55c-.59-.34-1.27-.55-2-.55C7.79 13 6 14.79 6 17s1.79 4 4 4 4-1.79 4-4V7h4V3h-6z"/></svg>
                </div>
                <div class="action-card-title">
                    <h3>Music &amp; Practice</h3>
                    <p>Record, browse, and assign practice</p>
                </div>
            </div>
            <div class="action-card-stats">
                <span>{total_audio} recordings</span>
                <span class="dot">&middot;</span>
                <span>{len(ragas)} ragas</span>
                <span class="dot">&middot;</span>
                <span id="teacher-active-assignments-count">{active_assignments} assigned</span>
            </div>
            <div class="action-buttons">
                <button class="action-btn primary" onclick="openRecorder()">
                    <svg viewBox="0 0 24 24" fill="currentColor"><circle cx="12" cy="12" r="8"/></svg>
                    Record New
                </button>
                <button class="action-btn" onclick="document.querySelectorAll('nav button')[1].click()">
                    <svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 3v10.55c-.59-.34-1.27-.55-2-.55C7.79 13 6 14.79 6 17s1.79 4 4 4 4-1.79 4-4V7h4V3h-6z"/></svg>
                    Browse Library
                </button>
                <button class="action-btn" onclick="openAssignModal()">
                    <svg viewBox="0 0 24 24" fill="currentColor"><path d="M19 3h-4.18C14.4 1.84 13.3 1 12 1c-1.3 0-2.4.84-2.82 2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-7 0c.55 0 1 .45 1 1s-.45 1-1 1-1-.45-1-1 .45-1 1-1zm2 14H7v-2h7v2zm3-4H7v-2h10v2zm0-4H7V7h10v2z"/></svg>
                    Assign Practice
                </button>
                <button class="action-btn" onclick="openAssignmentsListModal()">
                    <svg viewBox="0 0 24 24" fill="currentColor"><path d="M3 13h2v-2H3v2zm0 4h2v-2H3v2zm0-8h2V7H3v2zm4 4h14v-2H7v2zm0 4h14v-2H7v2zM7 7v2h14V7H7z"/></svg>
                    View &amp; edit assignments
                </button>
            </div>
        </div>

        <!-- 2. Attendance & Progress -->
        <div class="action-card attendance-action-card">
            <div class="action-card-header">
                <div class="action-card-icon attendance-icon">
                    <svg viewBox="0 0 24 24" fill="currentColor"><path d="M19 3h-1V1h-2v2H8V1H6v2H5c-1.11 0-1.99.9-1.99 2L3 19c0 1.1.89 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm0 16H5V8h14v11zM9 10H7v2h2v-2zm4 0h-2v2h2v-2zm4 0h-2v2h2v-2z"/></svg>
                </div>
                <div class="action-card-title">
                    <h3>Attendance &amp; Progress</h3>
                    <p>Track who shows up and who practices</p>
                </div>
            </div>
            <div class="action-card-stats">
                <span>{len(families)} families</span>
                <span class="dot">&middot;</span>
                <span>{len(att_dates)} classes logged</span>
            </div>
            <div class="action-buttons">
                <button class="action-btn primary" onclick="openAttendance()">
                    <svg viewBox="0 0 24 24" fill="currentColor"><path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/></svg>
                    Mark Today's Attendance
                </button>
                <button class="action-btn" onclick="openAttendanceHistory()">
                    <svg viewBox="0 0 24 24" fill="currentColor"><path d="M13 3c-4.97 0-9 4.03-9 9H1l3.89 3.89.07.14L9 12H6c0-3.87 3.13-7 7-7s7 3.13 7 7-3.13 7-7 7c-1.93 0-3.68-.79-4.94-2.06l-1.42 1.42C8.27 19.99 10.51 21 13 21c4.97 0 9-4.03 9-9s-4.03-9-9-9zm-1 5v5l4.28 2.54.72-1.21-3.5-2.08V8H12z"/></svg>
                    View History
                </button>
            </div>
        </div>

        <!-- 3. Events -->
        <div class="action-card events-action-card">
            <div class="action-card-header">
                <div class="action-card-icon events-icon">
                    <svg viewBox="0 0 24 24" fill="currentColor"><path d="M17 10.5V7c0-.55-.45-1-1-1H4c-.55 0-1 .45-1 1v10c0 .55.45 1 1 1h12c.55 0 1-.45 1-1v-3.5l4 4v-11l-4 4z"/></svg>
                </div>
                <div class="action-card-title">
                    <h3>Events &amp; Memories</h3>
                    <p>Schedule events, share &amp; upload media</p>
                </div>
            </div>
            <div class="action-card-stats">
                <span>{total_events} events</span>
                <span class="dot">&middot;</span>
                <span>{total_event_files} photos &amp; videos</span>
                <span class="dot">&middot;</span>
                <span>{len(scheduled)} scheduled</span>
            </div>
            <div class="action-buttons">
                <button class="action-btn primary" onclick="openCreateEvent()">
                    <svg viewBox="0 0 24 24" fill="currentColor"><path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/></svg>
                    Create Event
                </button>
                <button class="action-btn" onclick="document.querySelectorAll('nav button')[2].click()">
                    <svg viewBox="0 0 24 24" fill="currentColor"><path d="M21 19V5c0-1.1-.9-2-2-2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2zM8.5 13.5l2.5 3.01L14.5 12l4.5 6H5l3.5-4.5z"/></svg>
                    View Events
                </button>
                <button class="action-btn" onclick="openUploadPhotos()">
                    <svg viewBox="0 0 24 24" fill="currentColor"><path d="M9 16h6v-6h4l-7-7-7 7h4zm-4 2h14v2H5z"/></svg>
                    Upload Photos
                </button>
            </div>
        </div>

        <!-- Practice Tracking -->
        <div style="margin-top:20px;">
            <h3 class="section-title">Practice Tracking</h3>
            <div id="teacher-practice-tracking"></div>
        </div>
    </div>
    </div>
    """


# ---------------------------------------------------------------------------
# Page builder
# ---------------------------------------------------------------------------

def build_page(teacher_id=None, role=None, student_id=None, parent_id=None):
    categories = tenant_data.load_audio_categories(teacher_id) if teacher_id is not None else load_audio_categories()
    events = get_events(teacher_id)
    people = tenant_data.load_people(teacher_id) if teacher_id is not None else load_people()
    audio_files = get_audio_files(teacher_id)
    student_names = get_student_names(teacher_id)

    # Music class name: per-tenant from people.teacher.school_name, else full default
    teacher_info = people.get("teacher", {})
    _default_class = "Hindustani Classical Music — " + (teacher_info.get("name") or "Teacher") + "'s Music School"
    school_name = teacher_info.get("school_name") or _default_class

    # Cache-bust CSS so edits always show (use file mtime as version)
    _css_path = BASE_DIR / "static" / "css" / "main.css"
    _css_v = int(_css_path.stat().st_mtime) if _css_path.exists() else 0

    teacher_dashboard_html = build_teacher_dashboard(categories, events, people, audio_files, teacher_id=teacher_id)
    events_html = build_events_html(events, teacher_id=teacher_id)
    people_html = build_people_html(people, role=role, teacher_id=teacher_id)

    # Scheduled events for the events tab
    scheduled = tenant_data.load_scheduled_events(teacher_id) if teacher_id is not None else load_scheduled_events()
    scheduled_html = ""
    if scheduled:
        scheduled_html = '<div class="card"><div class="card-header"><div class="card-header-left"><h3>Upcoming Events</h3></div></div><div class="card-body"><div class="scheduled-list">'
        for ev in sorted(scheduled, key=lambda x: x.get("date", "")):
            scheduled_html += f"""<div class="scheduled-event">
                <div class="se-date">{ev.get('date', '')}</div>
                <div class="se-info"><div class="se-name">{ev.get('name', '')}</div>
                <div class="se-meta">{ev.get('time', '')} {(' — ' + ev.get('location', '')) if ev.get('location') else ''}</div>
                {('<div class="se-desc">' + ev.get('description', '') + '</div>') if ev.get('description') else ''}
                </div></div>"""
        scheduled_html += '</div></div></div>'

    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="theme-color" content="#0a0a16">
<title>Music Class Organizer</title>
<link rel="stylesheet" href="/static/css/main.css?v={_css_v}">
</head>
<body>

<!-- ============ ROLE SELECTION ============ -->
<div id="role-overlay">
    <h1 class="role-title"><span>&#9835;</span> Music Class Organizer</h1>
    <p class="role-subtitle">Choose your role to get started</p>
    <div class="role-cards">
        <div class="role-card teacher" onclick="selectRole('teacher')">
            <div class="role-card-icon"><svg viewBox="0 0 24 24"><path d="M12 3v10.55c-.59-.34-1.27-.55-2-.55C7.79 13 6 14.79 6 17s1.79 4 4 4 4-1.79 4-4V7h4V3h-6z"/></svg></div>
            <div class="role-card-text"><h3>Teacher</h3><p>Record, assign, track attendance</p></div>
        </div>
        <div class="role-card student" onclick="selectRole('student')">
            <div class="role-card-icon"><svg viewBox="0 0 24 24"><path d="M5 13.18v4L12 21l7-3.82v-4L12 17l-7-3.82zM12 3L1 9l11 6 9-4.91V17h2V9L12 3z"/></svg></div>
            <div class="role-card-text"><h3>Student</h3><p>Practice recordings, track progress</p></div>
        </div>
        <div class="role-card parent" onclick="selectRole('parent')">
            <div class="role-card-icon"><svg viewBox="0 0 24 24"><path d="M16 11c1.66 0 2.99-1.34 2.99-3S17.66 5 16 5c-1.66 0-3 1.34-3 3s1.34 3 3 3zm-8 0c1.66 0 2.99-1.34 2.99-3S9.66 5 8 5C6.34 5 5 6.34 5 8s1.34 3 3 3zm0 2c-2.33 0-7 1.17-7 3.5V19h14v-2.5c0-2.33-4.67-3.5-7-3.5zm8 0c-.29 0-.62.02-.97.05 1.16.84 1.97 1.97 1.97 3.45V19h6v-2.5c0-2.33-4.67-3.5-7-3.5z"/></svg></div>
            <div class="role-card-text"><h3>Parent</h3><p>View events, progress, fees</p></div>
        </div>
    </div>
</div>

<!-- ============ MAIN APP ============ -->
<div id="app-container" style="display:none">

<button id="global-switch-btn" onclick="switchRole()" title="Switch profile">
    <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 3c1.66 0 3 1.34 3 3s-1.34 3-3 3-3-1.34-3-3 1.34-3 3-3zm0 14.2c-2.5 0-4.71-1.28-6-3.22.03-1.99 4-3.08 6-3.08 1.99 0 5.97 1.09 6 3.08-1.29 1.94-3.5 3.22-6 3.22z"/></svg>
    Switch
</button>

<header>
    <h1><span>&#9835;</span> Music Class Organizer</h1>
    <p id="header-school-name">{html.escape(school_name)}</p>
    <a href="/logout" class="header-logout">Log out</a>
</header>

<nav>
    <button class="active" onclick="showTab('dashboard', this)">
        <svg viewBox="0 0 24 24"><path d="M3 13h8V3H3v10zm0 8h8v-6H3v6zm10 0h8V11h-8v10zm0-18v6h8V3h-8z"/></svg>
        Home
    </button>
    <button onclick="showTab('music', this)">
        <svg viewBox="0 0 24 24"><path d="M12 3v10.55c-.59-.34-1.27-.55-2-.55C7.79 13 6 14.79 6 17s1.79 4 4 4 4-1.79 4-4V7h4V3h-6z"/></svg>
        Music
    </button>
    <button onclick="showTab('events', this)">
        <svg viewBox="0 0 24 24"><path d="M21 19V5c0-1.1-.9-2-2-2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2zM8.5 13.5l2.5 3.01L14.5 12l4.5 6H5l3.5-4.5z"/></svg>
        Events
    </button>
    <button onclick="showTab('people', this)">
        <svg viewBox="0 0 24 24"><path d="M16 11c1.66 0 2.99-1.34 2.99-3S17.66 5 16 5c-1.66 0-3 1.34-3 3s1.34 3 3 3zm-8 0c1.66 0 2.99-1.34 2.99-3S9.66 5 8 5C6.34 5 5 6.34 5 8s1.34 3 3 3zm0 2c-2.33 0-7 1.17-7 3.5V19h14v-2.5c0-2.33-4.67-3.5-7-3.5zm8 0c-.29 0-.62.02-.97.05 1.16.84 1.97 1.97 1.97 3.45V19h6v-2.5c0-2.33-4.67-3.5-7-3.5z"/></svg>
        People
    </button>
</nav>

<main>
    <div id="dashboard" class="tab active">
        <!-- Teacher dashboard (shown when role=teacher) -->
        <div id="teacher-dash">
        {teacher_dashboard_html}
        </div>

        <!-- Student dashboard (shown when role=student) -->
        <div id="student-dash" style="display:none">
            <!-- Name picker (first time) -->
            <div id="student-picker">
                <div class="picker-card">
                    <h2>Who are you?</h2>
                    <p class="picker-sub">Pick your name to see your practice assignments</p>
                    <div id="student-name-buttons"></div>
                </div>
            </div>
            <!-- Actual student home (after name picked) -->
            <div id="student-home" style="display:none">
                <div class="student-welcome">
                    <div class="welcome-left">
                        <h2>Hi, <span id="student-display-name"></span>!</h2>
                        <p class="welcome-date" id="student-date-display"></p>
                    </div>
                    <div class="streak-pill" id="streak-pill">
                        <span class="streak-fire">&#128293;</span>
                        <span id="streak-count">0</span> day streak
                    </div>
                </div>

                <!-- Practice calendar (last 14 days) -->
                <div class="practice-calendar" id="practice-calendar"></div>

                <!-- Today's assignments -->
                <h3 class="section-title">Today's Practice</h3>
                <div id="student-assignments">
                    <p class="empty-state">No assignments yet. Ask your teacher!</p>
                </div>

                <!-- Browse by raga (read-only) -->
                <h3 class="section-title" style="margin-top:20px">Browse Music</h3>
                <div id="student-music-browse"></div>

                <!-- switch role button moved to global header -->
            </div>
        </div>

        <!-- Parent dashboard (shown when role=parent) -->
        <div id="parent-dash" style="display:none">
            <!-- Step 1: Parent name picker -->
            <div id="parent-picker">
                <div class="picker-card">
                    <h2>Welcome, Parent!</h2>
                    <p class="picker-sub">Select your name to get started</p>
                    <div id="parent-name-buttons"></div>
                </div>
            </div>
            <!-- Step 2: Kid picker (shown after parent selected) -->
            <div id="kid-picker" style="display:none">
                <div class="picker-card">
                    <h2>Select your child(ren)</h2>
                    <p class="picker-sub">Check all that apply</p>
                    <div id="kid-checkboxes"></div>
                    <button class="save-btn" style="margin-top:16px; max-width:320px;" onclick="saveKidSelection()">Continue</button>
                </div>
            </div>
            <!-- Step 3: Actual parent home -->
            <div id="parent-home" style="display:none">
                <div class="parent-welcome">
                    <div class="welcome-left">
                        <h2 id="parent-welcome-name">Welcome!</h2>
                        <p class="welcome-date" id="parent-date-display"></p>
                    </div>
                    <!-- switch role button moved to global header -->
                </div>

                <!-- Child Practice Cards -->
                <h3 class="section-title">My Children's Practice</h3>
                <div id="parent-children-cards"></div>

                <!-- Fees & Payment -->
                <h3 class="section-title" style="margin-top:20px;">Fees &amp; Payment</h3>
                <div id="parent-fees-section"></div>

                <!-- Upcoming Events -->
                <h3 class="section-title" style="margin-top:20px;">Upcoming Events</h3>
                <div id="parent-events-section"></div>
            </div>
        </div>
    </div>

    <div id="music" class="tab">
        <h2>Music Library</h2>
        <div class="music-toolbar">
            <input type="text" class="search-bar" placeholder="Search by raga, type, taal, or filename..." oninput="filterMusic(this.value)" style="flex:1;">
            <button class="upload-audio-btn" onclick="document.getElementById('audio-upload-input').click()" title="Upload audio files">
                <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor"><path d="M9 16h6v-6h4l-7-7-7 7h4zm-4 2h14v2H5z"/></svg>
                Upload
            </button>
        </div>
        <input type="file" id="audio-upload-input" accept="audio/*,.m4a,.mp3,.opus,.ogg,.wav,.webm,.amr,.aac" multiple style="display:none" onchange="handleAudioUpload(this)">
        <div id="music-list"><p class="empty-state">Loading music library...</p></div>
    </div>

    <div id="events" class="tab">
        <h2>Events &amp; Memories</h2>
        {scheduled_html}
        {events_html}
    </div>

    <div id="people" class="tab">
        <h2>Class contacts</h2>
        {people_html}
    </div>
</main>

<!-- ============ MODALS ============ -->

<!-- Recorder Modal -->
<div id="recorder-modal" class="modal">
    <div class="modal-content">
        <div class="modal-header">
            <h3>Record Audio</h3>
            <button class="modal-close" onclick="closeModal('recorder-modal')">&times;</button>
        </div>
        <div class="modal-body">
            <div class="recorder-area">
                <div id="rec-timer">0:00</div>
                <div id="rec-status">Ready to record</div>
                <button id="rec-start" class="rec-btn record" onclick="startRecording()">
                    <svg viewBox="0 0 24 24" width="32" height="32"><circle cx="12" cy="12" r="8"/></svg>
                </button>
                <button id="rec-stop" class="rec-btn stop" onclick="stopRecording()" style="display:none">
                    <svg viewBox="0 0 24 24" width="28" height="28"><rect x="6" y="6" width="12" height="12" rx="2"/></svg>
                </button>
                <audio id="rec-preview" controls style="display:none"></audio>
                <div id="rec-save-section">
                    <input type="text" id="rec-name" class="modal-input" placeholder="Name this recording (e.g. Bhupali Bandish)">
                    <button id="rec-save-btn" class="save-btn" onclick="saveRecording()">Save Recording</button>
                </div>
            </div>
        </div>
    </div>
</div>

<!-- Attendance Modal -->
<div id="attendance-modal" class="modal">
    <div class="modal-content">
        <div class="modal-header">
            <h3>Mark Attendance</h3>
            <button class="modal-close" onclick="closeModal('attendance-modal')">&times;</button>
        </div>
        <div class="modal-body">
            <div class="att-controls">
                <input type="date" id="att-date" class="modal-input" onchange="onAttDateChange()">
            </div>
            <div class="att-actions">
                <button class="att-action-btn" onclick="selectAllStudents()">Select All</button>
                <button class="att-action-btn" onclick="deselectAllStudents()">Clear All</button>
                <button class="att-action-btn add-student-btn" onclick="showAddStudent()">+ Add Student</button>
            </div>
            <div id="add-student-row" style="display:none; margin-bottom:10px;">
                <div style="display:flex; gap:8px;">
                    <input type="text" id="new-student-name" class="modal-input" placeholder="Student name" style="flex:1">
                    <button class="save-btn" style="padding:10px 16px; white-space:nowrap;" onclick="addNewStudent()">Add</button>
                </div>
            </div>
            <div id="att-student-list"></div>
            <div class="modal-row" style="margin-top:12px">
                <label class="modal-label">Notes (optional)</label>
                <textarea id="att-notes" class="modal-input modal-textarea" placeholder="Class notes..."></textarea>
            </div>
            <button class="save-btn" onclick="saveAttendance()">Save Attendance</button>
        </div>
    </div>
</div>

<!-- Attendance History Modal -->
<div id="history-modal" class="modal">
    <div class="modal-content">
        <div class="modal-header">
            <h3>Attendance History</h3>
            <button class="modal-close" onclick="closeModal('history-modal')">&times;</button>
        </div>
        <div class="modal-body">
            <div id="history-list"><p class="empty-state">Loading...</p></div>
        </div>
    </div>
</div>

<!-- Assign Practice Modal -->
<div id="assign-modal" class="modal">
    <div class="modal-content">
        <div class="modal-header">
            <h3>Assign Practice</h3>
            <button class="modal-close" onclick="closeModal('assign-modal')">&times;</button>
        </div>
        <div class="modal-body">
            <div class="modal-row">
                <label class="modal-label">Recording</label>
                <select id="assign-recording" class="modal-input"></select>
            </div>
            <div class="modal-row">
                <label class="modal-label">Assign to</label>
                <div id="assign-students"></div>
            </div>
            <div class="modal-row">
                <label class="modal-label">Due date</label>
                <input type="date" id="assign-due" class="modal-input">
            </div>
            <div class="modal-row">
                <label class="modal-label">Notes (optional)</label>
                <textarea id="assign-notes" class="modal-input modal-textarea" placeholder="Practice instructions..."></textarea>
            </div>
            <button class="save-btn" onclick="saveAssignment()">Assign Practice</button>
        </div>
    </div>
</div>

<!-- Assigned practices list (teacher) -->
<div id="assignments-list-modal" class="modal">
    <div class="modal-content">
        <div class="modal-header">
            <h3>Assigned practices</h3>
            <button class="modal-close" onclick="closeModal('assignments-list-modal')">&times;</button>
        </div>
        <div class="modal-body">
            <div id="assignments-list"><p class="empty-state">Loading...</p></div>
        </div>
    </div>
</div>

<!-- Create Event Modal -->
<div id="event-modal" class="modal">
    <div class="modal-content">
        <div class="modal-header">
            <h3>Create Event</h3>
            <button class="modal-close" onclick="closeModal('event-modal')">&times;</button>
        </div>
        <div class="modal-body">
            <div class="modal-row">
                <label class="modal-label">Event Name</label>
                <input type="text" id="event-name" class="modal-input" placeholder="e.g. Spring Recital">
            </div>
            <div class="modal-row modal-row-inline">
                <div>
                    <label class="modal-label">Date</label>
                    <input type="date" id="event-date" class="modal-input">
                </div>
                <div>
                    <label class="modal-label">Time</label>
                    <input type="time" id="event-time" class="modal-input">
                </div>
            </div>
            <div class="modal-row">
                <label class="modal-label">Location</label>
                <input type="text" id="event-location" class="modal-input" placeholder="e.g. Community Center">
            </div>
            <div class="modal-row">
                <label class="modal-label">Description</label>
                <textarea id="event-description" class="modal-input modal-textarea" placeholder="Event details..."></textarea>
            </div>
            <button class="save-btn" onclick="saveEvent()">Create Event</button>
        </div>
    </div>
</div>

<!-- Hidden file input for photo upload -->
<input type="file" id="photo-upload-input" accept="image/*,video/*" multiple style="display:none" onchange="handlePhotoUpload(this)">

<!-- Share Modal -->
<div id="share-modal" class="modal" onclick="if(event.target===this)this.style.display='none'">
    <div class="modal-content" style="max-width:340px;">
        <div class="modal-header">
            <h3>Share Recording</h3>
            <button class="modal-close" onclick="document.getElementById('share-modal').style.display='none'">&times;</button>
        </div>
        <div class="modal-body" style="padding:16px;">
            <p id="share-title" style="font-weight:600; margin-bottom:14px; color:#2C1810;"></p>
            <div class="share-options">
                <a id="share-whatsapp-link" class="share-option-btn whatsapp" href="#" target="_blank">
                    <svg viewBox="0 0 24 24" width="22" height="22" fill="currentColor"><path d="M17.5 14.4l-2-1c-.3-.1-.5-.1-.7.1l-.9 1.1c-.2.2-.3.2-.6.1-1.7-.9-2.8-2-3.7-3.4-.2-.3-.1-.5.1-.7l.6-.7c.2-.2.2-.4.1-.6l-1-2.3c-.2-.6-.5-.5-.7-.5h-.6c-.2 0-.6.1-.9.4C6.4 7.7 6 8.7 6 9.8c0 1.3.5 2.5 1.1 3.4 1.2 1.8 2.7 3.3 4.6 4.3.6.3 1.1.5 1.5.6.6.2 1.2.2 1.7.1.5-.1 1.6-.7 1.8-1.3.2-.6.2-1.2.1-1.3-.1-.1-.3-.2-.5-.3zm-5.4 7.3c-1.8 0-3.5-.5-5-1.4l-.4-.2-3.5.9.9-3.4-.3-.4c-1-1.6-1.5-3.4-1.5-5.3C2.3 6.1 6.8 1.7 12.1 1.7c2.6 0 5 1 6.8 2.8 1.8 1.8 2.8 4.2 2.8 6.8 0 5.3-4.5 9.7-9.9 9.7l-.1-.3zm8.4-18C18.2.9 15.2 0 12.1 0 5.5 0 .1 5.3.1 11.9c0 2.1.6 4.1 1.6 5.9L0 24l6.3-1.6c1.7.9 3.7 1.4 5.7 1.4 6.6 0 12-5.3 12-11.9 0-3.2-1.3-6.1-3.4-8.2z"/></svg>
                    WhatsApp
                </a>
                <a id="share-sms-link" class="share-option-btn sms" href="#">
                    <svg viewBox="0 0 24 24" width="22" height="22" fill="currentColor"><path d="M20 2H4c-1.1 0-1.99.9-1.99 2L2 22l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zM9 11H7V9h2v2zm4 0h-2V9h2v2zm4 0h-2V9h2v2z"/></svg>
                    SMS
                </a>
                <button id="share-copy-url" class="share-option-btn copy" onclick="copyShareUrl(this)" data-url="">
                    <svg viewBox="0 0 24 24" width="22" height="22" fill="currentColor"><path d="M16 1H4c-1.1 0-2 .9-2 2v14h2V3h12V1zm3 4H8c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h11c1.1 0 2-.9 2-2V7c0-1.1-.9-2-2-2zm0 16H8V7h11v14z"/></svg>
                    Copy Link
                </button>
            </div>
        </div>
    </div>
</div>

<!-- Lightbox -->
<div id="lightbox" onclick="this.classList.remove('active')">
    <img id="lightbox-img" src="" alt="">
</div>

<div id="toast" class="toast"></div>

<button id="undo-fab" onclick="undoLastEdit()" title="Undo" style="display:none">
    <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M12.5 8c-2.65 0-5.05.99-6.9 2.6L2 7v9h9l-3.62-3.62c1.39-1.16 3.16-1.88 5.12-1.88 3.54 0 6.55 2.31 7.6 5.5l2.37-.78C21.08 11.03 17.15 8 12.5 8z"/></svg>
    Undo <span class="undo-count">0</span>
</button>

<!-- AI Chat Panel -->
<button id="ai-fab" onclick="toggleAiChat()" title="Ask AI about music">
    <svg viewBox="0 0 24 24" width="22" height="22" fill="currentColor"><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H5.17L4 17.17V4h16v12z"/><path d="M12 6c-1.93 0-3.5 1.57-3.5 3.5 0 1.58 1.05 2.9 2.5 3.33V15h2v-2.17c1.45-.43 2.5-1.75 2.5-3.33C15.5 7.57 13.93 6 12 6zm0 5c-.83 0-1.5-.67-1.5-1.5S11.17 8 12 8s1.5.67 1.5 1.5S12.83 11 12 11z"/></svg>
</button>
<div id="ai-chat-panel" style="display:none">
    <div class="ai-chat-header">
        <div class="ai-chat-title">
            <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor"><path d="M12 6c-1.93 0-3.5 1.57-3.5 3.5 0 1.58 1.05 2.9 2.5 3.33V15h2v-2.17c1.45-.43 2.5-1.75 2.5-3.33C15.5 7.57 13.93 6 12 6zm0 5c-.83 0-1.5-.67-1.5-1.5S11.17 8 12 8s1.5.67 1.5 1.5S12.83 11 12 11z"/></svg>
            Music AI Assistant
        </div>
        <button class="ai-chat-close" onclick="toggleAiChat()">&times;</button>
    </div>
    <div id="ai-chat-messages">
        <div class="ai-msg ai-bot">
            <div class="ai-msg-content">Hi! I can help you learn about Hindustani classical music, answer questions about your recordings, or find resources. Try asking:<br><br>
            <span class="ai-suggestion" onclick="askAiSuggestion(this)">What ragas are in our library?</span>
            <span class="ai-suggestion" onclick="askAiSuggestion(this)">Explain Raga Yaman</span>
            <span class="ai-suggestion" onclick="askAiSuggestion(this)">Find YouTube videos for Bhupali</span>
            </div>
        </div>
    </div>
    <div class="ai-chat-input-area">
        <input type="text" id="ai-chat-input" placeholder="Ask about music, ragas, practice..." onkeydown="if(event.key==='Enter')sendAiMessage()">
        <button class="ai-send-btn" onclick="sendAiMessage()">
            <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/></svg>
        </button>
    </div>
</div>

</div> <!-- /app-container -->
"""

# Bootstrap data for JS (one small inline script), then load external JS files
    parent_names = get_parent_names(teacher_id)
    teacher_venmo = people.get("teacher", {}).get("venmo", "@Teacher")

    page += "<script>\n"
    page += "const teacherId = " + json.dumps(teacher_id) + ";\n"
    page += "const sessionRole = " + json.dumps(role) + ";\n"
    page += "const sessionStudentId = " + json.dumps(student_id) + ";\n"
    page += "const sessionParentId = " + json.dumps(parent_id) + ";\n"
    page += "const mediaAudioBase = teacherId != null ? '/media/audio/' + teacherId + '/' : '/media/audio/';\n"
    page += "const schoolName = " + json.dumps(school_name) + ";\n"
    page += "let categories = " + json.dumps(categories) + ";\n"
    page += "const allAudioFiles = " + json.dumps(audio_files) + ";\n"
    page += "const studentNames = " + json.dumps(student_names) + ";\n"
    page += "const parentNames = " + json.dumps(parent_names) + ";\n"
    page += "let teacherVenmo = " + json.dumps(teacher_venmo) + ";\n"
    page += "</script>\n"
    page += f'<script src="/static/js/core.js?v={_css_v}"></script>\n'
    page += f'<script src="/static/js/music-editor.js?v={_css_v}"></script>\n'
    page += f'<script src="/static/js/teacher.js?v={_css_v}"></script>\n'
    page += f'<script src="/static/js/student.js?v={_css_v}"></script>\n'
    page += f'<script src="/static/js/parent.js?v={_css_v}"></script>\n'
    page += f'<script src="/static/js/ai-chat.js?v={_css_v}"></script>\n'
    page += "</body>\n</html>"   

    return page


def _login_wrapper(inner_html: str, title: str = "Login") -> str:
    """Wrap login content with app styles and layout."""
    return (
        "<!DOCTYPE html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
        f"<title>{title}</title>"
        "<link rel='stylesheet' href='/static/css/main.css'>"
        "<style>.login-page{min-height:100vh;background:#F5EDE4;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:20px;box-sizing:border-box}"
        ".login-card{background:#fff;border:1px solid #E0D5C8;border-radius:12px;padding:24px;max-width:360px;width:100%}"
        ".login-form .login-label{display:block;margin-bottom:12px}.login-form .modal-input{width:100%;margin-top:4px;box-sizing:border-box}"
        ".login-form .save-btn{margin-top:16px;width:100%}.login-link{margin-top:16px;font-size:14px;color:#6a5a4a}"
        ".login-link a{color:#d4913b}.login-error{color:#c00;font-size:14px;margin-top:12px}</style>"
        "</head><body class='login-page'><div class='login-card'>" + inner_html + "</div></body></html>"
    )


def _login_page(error_message: str = "") -> str:
    """Login form for teacher auth."""
    err = f'<p class="login-error">{error_message}</p>' if error_message else ""
    return _login_wrapper(
        "<h1>&#9835; Music Class Organizer</h1><h2>Teacher login</h2>"
        "<form method='post' action='/login' class='login-form'>"
        "<label class='login-label'>Email <input type='email' name='email' class='modal-input' required></label>"
        "<label class='login-label'>Password <input type='password' name='password' class='modal-input' required></label>"
        "<button type='submit' class='save-btn'>Log in</button></form>"
        "<p class='login-link'><a href='/login/student'>Student? Log in with name + PIN</a></p>"
        f"{err}",
        "Login",
    )


def _first_teacher_signup_page(error_message: str = "") -> str:
    """One-time form to create the first teacher when the DB has no teachers."""
    err = f'<p class="login-error">{error_message}</p>' if error_message else ""
    return _login_wrapper(
        "<h1>&#9835; Music Class Organizer</h1><h2>Create first teacher account</h2>"
        "<p style='font-size:14px;color:#6a5a4a;margin-bottom:16px;'>No teacher exists yet. Create an account to get started.</p>"
        "<form method='post' action='/signup' class='login-form'>"
        "<label class='login-label'>Email <input type='email' name='email' class='modal-input' required></label>"
        "<label class='login-label'>Password <input type='password' name='password' class='modal-input' required minlength='6' placeholder='At least 6 characters'></label>"
        "<label class='login-label'>Display name (optional) <input type='text' name='display_name' class='modal-input' placeholder='e.g. Vaishnavi'></label>"
        "<button type='submit' class='save-btn'>Create account</button></form>"
        f"{err}",
        "Create account",
    )


def _student_login_page(error_message: str = "") -> str:
    """Login form for student: name + PIN."""
    err = f'<p class="login-error">{error_message}</p>' if error_message else ""
    return _login_wrapper(
        "<h1>&#9835; Music Class Organizer</h1><h2>Student login</h2>"
        "<form method='post' action='/login/student' class='login-form'>"
        "<label class='login-label'>Your name <input type='text' name='student_name' class='modal-input' required autocomplete='name'></label>"
        "<label class='login-label'>PIN <input type='password' name='pin' class='modal-input' inputmode='numeric' autocomplete='off' required></label>"
        "<button type='submit' class='save-btn'>Log in</button></form>"
        "<p class='login-link'><a href='/login'>Teacher login</a></p>"
        f"{err}",
        "Student Login",
    )


def _parent_link_error_page() -> str:
    """Shown when parent magic link is invalid or expired."""
    return _login_wrapper(
        "<h1>&#9835; Music Class Organizer</h1>"
        "<p class='login-error'>Invalid or expired link.</p>"
        "<p class='login-link'><a href='/login'>Teacher login</a></p>",
        "Invalid link",
    )


# ---------------------------------------------------------------------------
# HTTP Handler
# ---------------------------------------------------------------------------

class AppHandler(SimpleHTTPRequestHandler):

    def require_session(self, api: bool = False):
        """Return session dict if valid (has teacher_id); else send 401 (api) or 302 to /login and return None."""
        session = get_session(self)
        if session is None or not session.get("teacher_id"):
            if api:
                self._send_json({"error": "Unauthorized"}, 401)
            else:
                self.send_response(302)
                self.send_header("Location", "/login")
                self.end_headers()
            return None
        return session

    def do_GET(self):
        parsed = urlparse(self.path)

        # Require teacher or student session for dashboard
        if parsed.path in ("/", "/index.html"):
            session = self.require_session()
            if session is None:
                return
            role = session.get("role", "teacher")
            teacher_id = session.get("teacher_id")
            student_id = session.get("student_id") if role == "student" else None
            parent_id = session.get("parent_id") if role == "parent" else None
            if not teacher_id:
                self.send_response(302)
                self.send_header("Location", "/login")
                self.end_headers()
                return
            if role == "student" and not student_id:
                self.send_response(302)
                self.send_header("Location", "/login/student")
                self.end_headers()
                return
            if role == "parent" and not parent_id:
                self.send_response(302)
                self.send_header("Location", "/login")
                self.end_headers()
                return
            html = build_page(teacher_id=teacher_id, role=role, student_id=student_id, parent_id=parent_id)
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
            self.send_header("Pragma", "no-cache")
            self.end_headers()
            self.wfile.write(html.encode("utf-8"))
            return

        if parsed.path == "/logout":
            clear_cookie = f"{SESSION_COOKIE_NAME}=; Path=/; HttpOnly; SameSite=Lax; Max-Age=0"
            self.send_response(302)
            self.send_header("Location", "/login")
            self.send_header("Set-Cookie", clear_cookie)
            self.end_headers()
            return

        if parsed.path == "/login/parent":
            qs = parse_qs(parsed.query)
            token = (qs.get("token") or [""])[0].strip()
            result = consume_parent_token(token) if token else None
            if result is not None:
                teacher_id, parent_id = result
                session = create_session("parent", teacher_id=teacher_id, parent_id=parent_id)
                self.send_response(302)
                self.send_header("Location", "/")
                self.send_header("Set-Cookie", session_cookie_header_value(session))
                self.end_headers()
                return
            html = _parent_link_error_page()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(html.encode("utf-8"))
            return

        if parsed.path == "/login/student":
            err = "Invalid name or PIN." if parse_qs(parsed.query).get("error") else ""
            html = _student_login_page(err)
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(html.encode("utf-8"))
            return

        if parsed.path == "/login":
            err = "Invalid email or password." if parse_qs(parsed.query).get("error") else ""
            if teacher_count() == 0:
                html = _first_teacher_signup_page()
            else:
                html = _login_page(err)
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(html.encode("utf-8"))
            return

        # Serve static files (CSS, JS) from project folder (not current working directory)
        if parsed.path.startswith("/static/"):
            try:
                rel = parsed.path.lstrip("/")
                file_path = BASE_DIR / rel
                if file_path.exists() and file_path.is_file():
                    self.send_response(200)
                    # Set content type based on file extension
                    if file_path.suffix == ".css":
                        self.send_header("Content-Type", "text/css; charset=utf-8")
                        self.send_header("Cache-Control", "no-cache, must-revalidate")
                    elif file_path.suffix == ".js":
                        self.send_header("Content-Type", "application/javascript; charset=utf-8")
                        self.send_header("Cache-Control", "no-cache, must-revalidate")
                    else:
                        self.send_header("Content-Type", "application/octet-stream")
                    self.end_headers()
                    self.wfile.write(file_path.read_bytes())
                    return
                else:
                    self.send_error(404, "File not found")
                    return
            except Exception as e:
                self.send_error(500, f"Error serving static file: {str(e)}")
                return

        if parsed.path == "/api/categories":
            session = self.require_session(api=True)
            if session is None:
                return
            self._send_json(tenant_data.load_audio_categories(session["teacher_id"]))
            return

        if parsed.path == "/api/attendance":
            session = self.require_session(api=True)
            if session is None:
                return
            self._send_json(tenant_data.load_attendance(session["teacher_id"]))
            return

        if parsed.path == "/api/assignments":
            session = self.require_session(api=True)
            if session is None:
                return
            self._send_json(tenant_data.load_assignments(session["teacher_id"]))
            return

        if parsed.path == "/api/events/scheduled":
            session = self.require_session(api=True)
            if session is None:
                return
            self._send_json(tenant_data.load_scheduled_events(session["teacher_id"]))
            return

        if parsed.path == "/api/practice-log":
            session = self.require_session(api=True)
            if session is None:
                return
            self._send_json(tenant_data.load_practice_log(session["teacher_id"]))
            return

        if parsed.path == "/api/ai-status":
            session = self.require_session(api=True)
            if session is None:
                return
            self._send_json({"available": AI_AVAILABLE, "model": AI_MODEL if AI_AVAILABLE else None})
            return

        if parsed.path == "/api/parent-profiles":
            session = self.require_session(api=True)
            if session is None:
                return
            profiles = tenant_data.load_parent_profiles(session["teacher_id"])
            if session.get("role") == "parent":
                parent_id = session.get("parent_id")
                profiles = {parent_id: profiles.get(parent_id, {"children": [], "payments": []})} if parent_id else {}
            self._send_json(profiles)
            return

        if parsed.path == "/api/parent-names":
            session = self.require_session(api=True)
            if session is None:
                return
            self._send_json(get_parent_names(session["teacher_id"]))
            return

        if parsed.path == "/api/parent-login-link":
            session = self.require_session(api=True)
            if session is None:
                return
            qs = parse_qs(parsed.query)
            parent_id = (qs.get("parent_id") or [""])[0].strip()
            if not parent_id:
                self._send_json({"error": "Missing parent_id"}, 400)
                return
            people = tenant_data.load_people(session["teacher_id"])
            families = people.get("families", [])
            if not any(p.get("parent") == parent_id for p in families):
                self._send_json({"error": "Parent not found"}, 404)
                return
            token = create_parent_token(session["teacher_id"], parent_id)
            host = self.headers.get("Host", "localhost:8000")
            base_url = f"http://{host}"
            url = f"{base_url}/login/parent?token={token}"
            self._send_json({"url": url})
            return

        # Serve media files (resolve under MEDIA_DIR so disk path works on Render)
        if parsed.path.startswith("/media/"):
            rel = parsed.path[7:].lstrip("/")  # path after "/media/"
            if not rel or ".." in rel:
                self.send_response(403)
                self.end_headers()
                return
            file_path = (MEDIA_DIR / rel).resolve()
            try:
                med = MEDIA_DIR.resolve()
                if not str(file_path).startswith(str(med)):
                    self.send_response(403)
                    self.end_headers()
                    return
            except (ValueError, OSError):
                self.send_response(400)
                self.end_headers()
                return

            if file_path.exists() and file_path.is_file():
                ext = file_path.suffix.lower()
                ct = {
                    '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png',
                    '.gif': 'image/gif', '.webp': 'image/webp',
                    '.mp4': 'video/mp4', '.mov': 'video/quicktime', '.webm': 'video/webm',
                    '.m4a': 'audio/mp4', '.mp3': 'audio/mpeg', '.opus': 'audio/opus',
                    '.wav': 'audio/wav', '.ogg': 'audio/ogg', '.amr': 'audio/amr',
                }.get(ext, "application/octet-stream")
                file_size = file_path.stat().st_size

                # --- Range request support (required for iOS Safari audio) ---
                range_header = self.headers.get("Range")
                if range_header:
                    try:
                        # Parse "bytes=START-END"
                        range_spec = range_header.replace("bytes=", "").strip()
                        parts = range_spec.split("-")
                        start = int(parts[0]) if parts[0] else 0
                        end = int(parts[1]) if parts[1] else file_size - 1
                        end = min(end, file_size - 1)
                        length = end - start + 1

                        self.send_response(206)
                        self.send_header("Content-Type", ct)
                        self.send_header("Content-Length", str(length))
                        self.send_header("Content-Range", f"bytes {start}-{end}/{file_size}")
                        self.send_header("Accept-Ranges", "bytes")
                        self.send_header("Cache-Control", "public, max-age=3600")
                        self.end_headers()

                        with open(file_path, "rb") as f:
                            f.seek(start)
                            self.wfile.write(f.read(length))
                        return
                    except (ValueError, IndexError):
                        pass  # Fall through to normal response

                # --- Normal full-file response ---
                self.send_response(200)
                self.send_header("Content-Type", ct)
                self.send_header("Content-Length", str(file_size))
                self.send_header("Accept-Ranges", "bytes")
                self.send_header("Cache-Control", "public, max-age=3600")
                self.end_headers()
                self.wfile.write(file_path.read_bytes())
                return

        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        parsed = urlparse(self.path)
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)

        # --- Login (form POST) ---
        if parsed.path == "/login":
            form = parse_qs(body.decode("utf-8", errors="replace"))
            email = (form.get("email") or [""])[0]
            password = (form.get("password") or [""])[0]
            teacher_id = verify_teacher(email, password)
            if teacher_id is not None:
                session = create_session("teacher", teacher_id=teacher_id)
                self.send_response(302)
                self.send_header("Location", "/")
                self.send_header("Set-Cookie", session_cookie_header_value(session))
                self.end_headers()
                return
            self.send_response(302)
            self.send_header("Location", "/login?error=1")
            self.end_headers()
            return

        # --- First-teacher signup (form POST) ---
        if parsed.path == "/signup":
            form = parse_qs(body.decode("utf-8", errors="replace"))
            email = (form.get("email") or [""])[0].strip().lower()
            password = (form.get("password") or [""])[0]
            display_name = (form.get("display_name") or [""])[0].strip() or ""
            if not email or not password:
                html = _first_teacher_signup_page("Email and password are required.")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(html.encode("utf-8"))
                return
            if len(password) < 6:
                html = _first_teacher_signup_page("Password must be at least 6 characters.")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(html.encode("utf-8"))
                return
            if teacher_count() != 0:
                self.send_response(302)
                self.send_header("Location", "/login")
                self.end_headers()
                return
            password_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()
            try:
                with get_connection() as conn:
                    conn.execute(
                        "INSERT INTO teachers (email, password_hash, display_name) VALUES (?, ?, ?)",
                        (email, password_hash, display_name),
                    )
                    conn.commit()
                    teacher_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            except Exception:
                html = _first_teacher_signup_page("That email may already be in use. Try logging in.")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(html.encode("utf-8"))
                return
            session = create_session("teacher", teacher_id=teacher_id)
            self.send_response(302)
            self.send_header("Location", "/")
            self.send_header("Set-Cookie", session_cookie_header_value(session))
            self.end_headers()
            return

        if parsed.path == "/login/student":
            form = parse_qs(body.decode("utf-8", errors="replace"))
            pin = (form.get("pin") or [""])[0].strip()
            student_name = (form.get("student_name") or [""])[0].strip()
            resolved = resolve_student_by_pin(pin)
            if resolved is not None:
                teacher_id, student_id = resolved
                if student_id.strip().lower() == student_name.strip().lower():
                    session = create_session("student", teacher_id=teacher_id, student_id=student_id)
                    self.send_response(302)
                    self.send_header("Location", "/")
                    self.send_header("Set-Cookie", session_cookie_header_value(session))
                    self.end_headers()
                    return
            self.send_response(302)
            self.send_header("Location", "/login/student?error=1")
            self.end_headers()
            return

        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            self._send_json({"ok": False, "error": "Invalid JSON"}, 400)
            return

        # --- Music editing endpoints ---
        if parsed.path == "/api/update-file":
            session = self.require_session(api=True)
            if session is None:
                return
            teacher_id = session["teacher_id"]
            categories = tenant_data.load_audio_categories(teacher_id)
            filename = data.get("filename")
            updates = data.get("updates", {})
            if not filename:
                self._send_json({"ok": False, "error": "Missing filename"}, 400)
                return
            if filename not in categories:
                categories[filename] = {"raga": "Unknown", "composition_type": "Unknown", "paltaas": False, "taal": "Unknown", "explanation": "Manually categorized"}
            categories[filename].update(updates)
            tenant_data.save_audio_categories(teacher_id, categories)
            self._send_json({"ok": True})

        elif parsed.path == "/api/restore":
            session = self.require_session(api=True)
            if session is None:
                return
            tenant_data.save_audio_categories(session["teacher_id"], data)
            self._send_json({"ok": True, "restored": len(data)})

        elif parsed.path == "/api/rename-raga":
            session = self.require_session(api=True)
            if session is None:
                return
            teacher_id = session["teacher_id"]
            categories = tenant_data.load_audio_categories(teacher_id)
            old_name, new_name = data.get("old_name"), data.get("new_name")
            if not old_name or not new_name:
                self._send_json({"ok": False, "error": "Missing names"}, 400)
                return
            count = 0
            for info in categories.values():
                if info.get("raga") == old_name:
                    info["raga"] = new_name
                    count += 1
            tenant_data.save_audio_categories(teacher_id, categories)
            self._send_json({"ok": True, "updated": count})

        # --- Recording upload ---
        elif parsed.path == "/api/upload-recording":
            session = self.require_session(api=True)
            if session is None:
                return
            teacher_id = session["teacher_id"]
            name = data.get("name", "Recording").strip() or "Recording"
            audio_data = base64.b64decode(data.get("audio_data", ""))
            ext = data.get("extension", ".webm")
            safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).strip().replace(' ', '-')
            today = datetime.now().strftime("%Y-%m-%d")
            filename = f"{today}_{safe_name}{ext}"
            audio_dir = MEDIA_DIR / "audio" / str(teacher_id)
            audio_dir.mkdir(parents=True, exist_ok=True)
            filepath = audio_dir / filename
            counter = 2
            while filepath.exists():
                filename = f"{today}_{safe_name}_{counter}{ext}"
                filepath = audio_dir / filename
                counter += 1
            filepath.write_bytes(audio_data)
            self._send_json({"ok": True, "filename": filename})

        # --- Audio file upload (from device) ---
        elif parsed.path == "/api/upload-audio-file":
            session = self.require_session(api=True)
            if session is None:
                return
            teacher_id = session["teacher_id"]
            filename = data.get("filename", "recording.mp3")
            audio_data = base64.b64decode(data.get("data", ""))
            audio_dir = MEDIA_DIR / "audio" / str(teacher_id)
            audio_dir.mkdir(parents=True, exist_ok=True)
            filepath = audio_dir / filename
            counter = 2
            base, ext = filename.rsplit('.', 1) if '.' in filename else (filename, 'mp3')
            while filepath.exists():
                filepath = audio_dir / f"{base}_{counter}.{ext}"
                counter += 1
            filepath.write_bytes(audio_data)
            self._send_json({"ok": True, "filename": filepath.name})

        # --- Attendance ---
        elif parsed.path == "/api/attendance/save":
            session = self.require_session(api=True)
            if session is None:
                return
            teacher_id = session["teacher_id"]
            attendance = tenant_data.load_attendance(teacher_id)
            date_str = data.get("date")
            students = data.get("students", [])
            notes = data.get("notes", "")
            if not date_str:
                self._send_json({"ok": False, "error": "Missing date"}, 400)
                return
            attendance[date_str] = {"students": students, "notes": notes}
            tenant_data.save_attendance(teacher_id, attendance)
            self._send_json({"ok": True, "date": date_str, "count": len(students)})

        # --- Assignments ---
        elif parsed.path == "/api/assignments/create":
            session = self.require_session(api=True)
            if session is None:
                return
            if session.get("role") != "teacher":
                self._send_json({"ok": False, "error": "Forbidden"}, 403)
                return
            teacher_id = session["teacher_id"]
            assignments = tenant_data.load_assignments(teacher_id)
            audio_file = data.get("audio_file")
            assigned_to = data.get("assigned_to", [])
            notes = data.get("notes", "")
            due_date = data.get("due_date", "")
            if not audio_file:
                self._send_json({"ok": False, "error": "Missing audio_file"}, 400)
                return
            assignment = {
                "id": f"a{len(assignments)+1}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "audio_file": audio_file,
                "assigned_to": assigned_to,
                "notes": notes,
                "due_date": due_date,
                "created": datetime.now().isoformat(),
                "status": "active"
            }
            assignments.append(assignment)
            tenant_data.save_assignments(teacher_id, assignments)
            self._send_json({"ok": True, "id": assignment["id"]})

        elif parsed.path == "/api/assignments/update":
            session = self.require_session(api=True)
            if session is None:
                return
            if session.get("role") != "teacher":
                self._send_json({"ok": False, "error": "Forbidden"}, 403)
                return
            teacher_id = session["teacher_id"]
            assignments = tenant_data.load_assignments(teacher_id)
            aid = data.get("id")
            if not aid:
                self._send_json({"ok": False, "error": "Missing id"}, 400)
                return
            found = next((a for a in assignments if a.get("id") == aid), None)
            if not found:
                self._send_json({"ok": False, "error": "Assignment not found"}, 404)
                return
            for key in ("audio_file", "assigned_to", "notes", "due_date", "status"):
                if key in data:
                    found[key] = data[key] if key != "assigned_to" else (data[key] if isinstance(data[key], list) else [])
            tenant_data.save_assignments(teacher_id, assignments)
            self._send_json({"ok": True})

        elif parsed.path == "/api/assignments/remove":
            session = self.require_session(api=True)
            if session is None:
                return
            if session.get("role") != "teacher":
                self._send_json({"ok": False, "error": "Forbidden"}, 403)
                return
            teacher_id = session["teacher_id"]
            assignments = tenant_data.load_assignments(teacher_id)
            aid = data.get("id")
            if not aid:
                self._send_json({"ok": False, "error": "Missing id"}, 400)
                return
            found = next((a for a in assignments if a.get("id") == aid), None)
            if not found:
                self._send_json({"ok": False, "error": "Assignment not found"}, 404)
                return
            found["status"] = "removed"
            tenant_data.save_assignments(teacher_id, assignments)
            self._send_json({"ok": True})

        # --- Events ---
        elif parsed.path == "/api/events/create":
            session = self.require_session(api=True)
            if session is None:
                return
            teacher_id = session["teacher_id"]
            events = tenant_data.load_scheduled_events(teacher_id)
            name = data.get("name", "").strip()
            event_date = data.get("date", "")
            time = data.get("time", "")
            location = data.get("location", "")
            description = data.get("description", "")
            if not name or not event_date:
                self._send_json({"ok": False, "error": "Missing name or date"}, 400)
                return
            event = {
                "id": f"e{len(events)+1}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "name": name,
                "date": event_date,
                "time": time,
                "location": location,
                "description": description,
                "created": datetime.now().isoformat(),
                "status": "upcoming"
            }
            events.append(event)
            tenant_data.save_scheduled_events(teacher_id, events)
            self._send_json({"ok": True, "id": event["id"]})

        # --- Practice log ---
        elif parsed.path == "/api/practice-log/mark":
            session = self.require_session(api=True)
            if session is None:
                return
            teacher_id = session["teacher_id"]
            log = tenant_data.load_practice_log(teacher_id)
            student = data.get("student", "")
            date_str = data.get("date", "")
            duration = data.get("duration", 0)
            items = data.get("items", "")
            if not student or not date_str:
                self._send_json({"ok": False, "error": "Missing student or date"}, 400)
                return
            if student not in log:
                log[student] = []
            # Check if already logged for this date
            existing_dates = [e["date"] for e in log[student] if isinstance(e, dict)]
            if date_str not in existing_dates:
                log[student].append({"date": date_str, "duration": duration, "items": items})
                log[student].sort(key=lambda e: e.get("date", ""))
            tenant_data.save_practice_log(teacher_id, log)
            self._send_json({"ok": True, "student": student, "date": date_str, "total_days": len(log[student])})

        elif parsed.path == "/api/practice-log/unmark":
            session = self.require_session(api=True)
            if session is None:
                return
            teacher_id = session["teacher_id"]
            log = tenant_data.load_practice_log(teacher_id)
            student = data.get("student", "")
            date_str = data.get("date", "")
            if student in log:
                log[student] = [e for e in log[student] if not (isinstance(e, dict) and e.get("date") == date_str)]
                tenant_data.save_practice_log(teacher_id, log)
            self._send_json({"ok": True})

        # --- Parent profile ---
        elif parsed.path == "/api/parent-profile/save":
            session = self.require_session(api=True)
            if session is None:
                return
            if session.get("role") == "parent" and data.get("parent", "") != session.get("parent_id"):
                self._send_json({"ok": False, "error": "Forbidden"}, 403)
                return
            teacher_id = session["teacher_id"]
            profiles = tenant_data.load_parent_profiles(teacher_id)
            parent_name = data.get("parent", "")
            children = data.get("children", [])
            if not parent_name:
                self._send_json({"ok": False, "error": "Missing parent name"}, 400)
                return
            if parent_name not in profiles:
                profiles[parent_name] = {"children": [], "payments": []}
            profiles[parent_name]["children"] = children
            tenant_data.save_parent_profiles(teacher_id, profiles)
            self._send_json({"ok": True})

        elif parsed.path == "/api/parent-profile/mark-payment":
            session = self.require_session(api=True)
            if session is None:
                return
            if session.get("role") == "parent" and data.get("parent", "") != session.get("parent_id"):
                self._send_json({"ok": False, "error": "Forbidden"}, 403)
                return
            teacher_id = session["teacher_id"]
            profiles = tenant_data.load_parent_profiles(teacher_id)
            parent_name = data.get("parent", "")
            amount = data.get("amount", "")
            note = data.get("note", "")
            if not parent_name:
                self._send_json({"ok": False, "error": "Missing parent name"}, 400)
                return
            if parent_name not in profiles:
                profiles[parent_name] = {"children": [], "payments": []}
            payment = {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "amount": amount,
                "note": note,
                "timestamp": datetime.now().isoformat()
            }
            profiles[parent_name].setdefault("payments", []).append(payment)
            tenant_data.save_parent_profiles(teacher_id, profiles)
            self._send_json({"ok": True, "payment": payment})

        # --- Add student ---
        elif parsed.path == "/api/students/add":
            session = self.require_session(api=True)
            if session is None:
                return
            name = data.get("name", "").strip()
            if not name:
                self._send_json({"ok": False, "error": "Missing name"}, 400)
                return
            added = add_student(name, session["teacher_id"])
            self._send_json({"ok": True, "added": added, "name": name})

        elif parsed.path == "/api/students/remove":
            session = self.require_session(api=True)
            if session is None:
                return
            name = (data.get("student_id") or data.get("name") or "").strip()
            if not name:
                self._send_json({"ok": False, "error": "Missing student_id"}, 400)
                return
            removed = remove_student(name, session["teacher_id"])
            self._send_json({"ok": removed, "removed": removed})

        elif parsed.path == "/api/families/add":
            session = self.require_session(api=True)
            if session is None:
                return
            parent = (data.get("parent") or data.get("name") or "").strip()
            if not parent:
                self._send_json({"ok": False, "error": "Missing parent name"}, 400)
                return
            people = tenant_data.load_people(session["teacher_id"])
            families = people.get("families", [])
            if any(p.get("parent") == parent for p in families):
                self._send_json({"ok": False, "error": "Already exists"}, 400)
                return
            families.append({"parent": parent, "role": "parent", "messages": 0})
            people["families"] = families
            tenant_data.save_people(session["teacher_id"], people)
            self._send_json({"ok": True, "added": parent})

        elif parsed.path == "/api/families/remove":
            session = self.require_session(api=True)
            if session is None:
                return
            parent = (data.get("parent") or data.get("name") or "").strip()
            if not parent:
                self._send_json({"ok": False, "error": "Missing parent name"}, 400)
                return
            people = tenant_data.load_people(session["teacher_id"])
            families = people.get("families", [])
            new_families = [p for p in families if p.get("parent") != parent]
            if len(new_families) == len(families):
                self._send_json({"ok": False, "error": "Not found"}, 404)
                return
            people["families"] = new_families
            tenant_data.save_people(session["teacher_id"], people)
            self._send_json({"ok": True, "removed": parent})

        elif parsed.path == "/api/student/set-pin":
            session = self.require_session(api=True)
            if session is None:
                return
            teacher_id = session["teacher_id"]
            student_id = (data.get("student_id") or "").strip()
            pin = (data.get("pin") or "").strip()
            if not student_id:
                self._send_json({"ok": False, "error": "Missing student_id"}, 400)
                return
            people = tenant_data.load_people(teacher_id)
            students = people.get("students", [])
            if student_id not in students:
                self._send_json({"ok": False, "error": "Student not found"}, 400)
                return
            set_student_pin(teacher_id, student_id, pin)
            self._send_json({"ok": True})

        # --- Teacher update settings (Venmo + school name) ---
        elif parsed.path == "/api/teacher/update-venmo":
            session = self.require_session(api=True)
            if session is None:
                return
            teacher_id = session["teacher_id"]
            venmo = (data.get("venmo") or "").strip()
            school_name = (data.get("school_name") or "").strip()
            if not venmo:
                self._send_json({"ok": False, "error": "Missing venmo"}, 400)
                return
            people = tenant_data.load_people(teacher_id)
            if "teacher" not in people:
                people["teacher"] = {}
            people["teacher"]["venmo"] = venmo
            if school_name:
                people["teacher"]["school_name"] = school_name
            tenant_data.save_people(teacher_id, people)
            self._send_json({"ok": True})

        # --- Delete recording ---
        elif parsed.path == "/api/delete-recording":
            session = self.require_session(api=True)
            if session is None:
                return
            teacher_id = session["teacher_id"]
            filename = data.get("filename", "").strip()
            if not filename:
                self._send_json({"ok": False, "error": "Missing filename"}, 400)
                return
            # Remove from categories
            cats = tenant_data.load_audio_categories(teacher_id)
            if filename in cats:
                del cats[filename]
                tenant_data.save_audio_categories(teacher_id, cats)
            # Remove actual file from tenant's audio dir
            audio_path = MEDIA_DIR / "audio" / str(teacher_id) / filename
            if audio_path.exists():
                audio_path.unlink()
            self._send_json({"ok": True})

        # --- AI query ---
        elif parsed.path == "/api/ai-query":
            session = self.require_session(api=True)
            if session is None:
                return
            teacher_id = session["teacher_id"]
            query = data.get("query", "").strip()
            if not query:
                self._send_json({"ok": False, "error": "Empty query"}, 400)
                return
            result = ask_ai(query, teacher_id=teacher_id)
            self._send_json({"ok": True, **result})

        # --- Photo upload ---
        elif parsed.path == "/api/upload-photo":
            session = self.require_session(api=True)
            if session is None:
                return
            teacher_id = session["teacher_id"]
            name = data.get("name", "photo.jpg")
            photo_data = base64.b64decode(data.get("data", ""))
            photos_dir = MEDIA_DIR / "photos" / str(teacher_id)
            photos_dir.mkdir(parents=True, exist_ok=True)
            today = datetime.now().strftime("%Y-%m-%d")
            safe_name = "".join(c for c in name if c.isalnum() or c in ('.', '-', '_', ' ')).strip().replace(' ', '-')
            filepath = photos_dir / f"{today}_{safe_name}"
            filepath.write_bytes(photo_data)
            self._send_json({"ok": True, "filename": filepath.name})

        else:
            self._send_json({"ok": False, "error": "Not found"}, 404)

    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

    def log_message(self, format, *args):
        if args and str(args[0]).startswith(("4", "5")):
            super().log_message(format, *args)

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

# Default SESSION_SECRET used in auth when not set (do not use on non-localhost)
_DEV_SESSION_SECRET = "dev-secret-change-in-production"


def main():
    host = os.getenv("HOST", "localhost")
    port = int(os.getenv("PORT", "8000"))
    session_secret = os.getenv("SESSION_SECRET", _DEV_SESSION_SECRET)
    is_dev_secret = session_secret == _DEV_SESSION_SECRET
    is_non_localhost = host in ("0.0.0.0",) or host not in ("localhost", "127.0.0.1")
    on_render = os.getenv("RENDER") == "true"
    if is_dev_secret and is_non_localhost and not on_render:
        print(
            "\n  Security: Refusing to bind to non-localhost with dev SESSION_SECRET.\n"
            "  Set SESSION_SECRET in .env (e.g. openssl rand -hex 32) for network access,\n"
            "  or use HOST=localhost / 127.0.0.1 for local-only dev.\n",
            file=sys.stderr,
        )
        sys.exit(1)
    if on_render and is_dev_secret:
        print(
            "\n  Warning: Running on Render with default SESSION_SECRET. Set SESSION_SECRET in Render Environment for production.\n",
            file=sys.stderr,
        )
    server = HTTPServer((host, port), AppHandler)
    print(f"\n  Music Class Organizer (Phase 2)")
    print(f"  http://{host}:{port}")
    print(f"\n  {len(get_audio_files())} audio files")
    print(f"  {len(load_audio_categories())} categorized")
    print(f"  {len(get_events())} events")
    print(f"  {len(get_student_names())} students")
    print(f"\n  Press Ctrl+C to stop.\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Stopped.")
        server.server_close()

if __name__ == "__main__":
    main()
