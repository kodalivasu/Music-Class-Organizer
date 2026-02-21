# Music Class Organizer — Technical Design Document

**Version:** 1.0
**Last updated:** February 2026
**Status:** MVP (Phase 1) complete

---

## 1. System Overview

The Music Class Organizer is a Python-based web application that extracts, organizes, and presents data from WhatsApp group chat exports for a Hindustani classical music class. It consists of a **data pipeline** (scripts that process raw exports) and a **web server** (a browser-based UI for browsing and editing the organized data).

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    DATA SOURCES                          │
│  WhatsApp .zip exports  │  Google Drive links  │  .env  │
└────────────┬────────────┴──────────────────────┴────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────┐
│                   DATA PIPELINE (Python scripts)         │
│                                                          │
│  parse_whatsapp.py ──→ combine_chats.py                  │
│       │                      │                           │
│       ├──→ extract_classes.py (class dates)               │
│       ├──→ organize_media.py  (audio/video/photos)        │
│       │         └──→ organize_events.py (event folders)   │
│       └──→ categorize_audio.py (AI tagging via Gemini)    │
└────────────┬────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────┐
│                    DATA STORE (JSON files)                │
│                                                          │
│  data/audio_categories.json  │  data/people.json         │
│  media/audio/  │  media/events/  │  media/photos/         │
└────────────┬────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────┐
│                    WEB SERVER (app.py)                    │
│                                                          │
│  HTTP Server (localhost:8000)                             │
│  ├── GET /              → HTML page (server-rendered)     │
│  ├── GET /api/categories → JSON data                      │
│  ├── GET /media/*       → Static files (audio/images)     │
│  ├── POST /api/update-file  → Edit one file's tags        │
│  ├── POST /api/rename-raga  → Rename raga across files    │
│  └── POST /api/restore      → Undo (restore snapshot)     │
│                                                          │
│  Frontend: Vanilla HTML/CSS/JS (mobile-first)             │
│  ├── Dashboard (server-rendered)                          │
│  ├── Music Library (client-rendered, interactive)         │
│  ├── Events & Memories (server-rendered)                  │
│  └── People (server-rendered)                             │
└─────────────────────────────────────────────────────────┘
```

---

## 2. Tech Stack

| Component | Technology | Version | Why |
|-----------|-----------|---------|-----|
| Language | Python | 3.14 | Simple, good for scripting and data work |
| Web server | `http.server` | stdlib | Zero dependencies, easy to understand |
| Frontend | HTML/CSS/JS | Vanilla | No build tools, mobile-first, no framework complexity |
| AI | Google Gemini | 2.0 Flash / 2.5 Flash | Multimodal audio analysis, free tier |
| AI SDK | `google-generativeai` | 0.8.6 | Python SDK for Gemini API |
| Env mgmt | `python-dotenv` | 1.2.1 | Loads `.env` file for API keys |
| Data format | JSON | — | Human-readable, easy to edit, no database needed |
| Package mgmt | pip | — | Standard Python package manager |

### Why no database?
JSON files are sufficient for the current scale (~55 audio files, ~20 families, ~8 events). The data is small enough to load entirely into memory. If the app grows past ~500 recordings or ~100 users, we would migrate to SQLite or PostgreSQL.

### Why no web framework?
Python's built-in `http.server` keeps the dependency count at 2 packages (`google-generativeai`, `python-dotenv`). For Phase 2 (user roles, authentication), we would likely switch to Flask or FastAPI.

---

## 3. Data Pipeline — Module Specifications

### 3.1 `parse_whatsapp.py` — Chat Parser

**Purpose:** Parse WhatsApp chat exports into structured `Message` objects.

**Input:** `.zip` file (containing `_chat.txt`) or plain `.txt` file

**Output:** `list[Message]` — each message has `time`, `date`, `sender`, `body`

**Key design decisions:**
- **Two regex patterns** handle WhatsApp's two known export formats:
  - Format A: `[TIME, DATE]` (e.g., `[5:55 PM, 2/8/2026]`) — time first, 4-digit year
  - Format B: `[DATE, TIME]` (e.g., `[7/17/23, 5:54:21 PM]`) — date first, 2-digit year, optional seconds
- **Unicode normalization** strips `\u202f` (narrow no-break space), `\u200e` (left-to-right mark), and `\r` that WhatsApp inserts
- **Multi-line messages** are handled by checking if a line starts with `[` — if not, it's appended to the previous message's body
- **Zip extraction** looks for `_chat.txt` first, falls back to any `.txt` file

**Data model:**
```python
@dataclass
class Message:
    time: str       # "5:55 PM"
    date: str       # "2/8/2026"
    sender: str     # "Vaishnavi  Kondapalli"
    body: str       # Full message text (may be multi-line)

    @property
    def datetime(self) -> datetime:
        # Parses both M/D/YYYY and M/D/YY formats
        # Strips seconds if present (5:54:21 PM → 5:54 PM)

    def is_from_teacher(self, teacher_name) -> bool
    def has_drive_link(self) -> bool
    def get_drive_links(self) -> list[str]
```

### 3.2 `combine_chats.py` — Multi-Chat Merger

**Purpose:** Merge messages from multiple WhatsApp export zip files.

**Input:** Multiple `.zip` file paths

**Output:** Deduplicated, chronologically sorted `list[Message]`

**Deduplication strategy:**
- Key: `(date, time, sender.lower(), body[:100])`
- First 100 characters of body used to avoid hash collisions on very long messages
- Case-insensitive sender matching

### 3.3 `extract_classes.py` — Class Date Extractor

**Purpose:** Identify class/event dates from teacher messages.

**Input:** `list[Message]`

**Output:** `list[ClassDate]` with date, time, type, and evidence

**Detection patterns:**
| Category | Patterns |
|----------|----------|
| Class indicators | "see the kiddos", "class at", "come by [time]", meeting links |
| Reschedule | "moved to", "rescheduled", "cancelled", "no class" |
| Events | "performance", "concert", "havan", "annual day" |

**Classification logic:**
1. Only teacher messages are examined
2. Message is matched against compiled regex patterns
3. Class type determined: `class`, `online`, `performance`, `cancelled`, `rescheduled`
4. Time extracted from message body if mentioned
5. Deduplicated by date (first mention wins, except cancellations)

### 3.4 `organize_media.py` — Media File Organizer

**Purpose:** Extract media from WhatsApp zips, rename with dates and context.

**Input:** Multiple `.zip` files + parsed messages

**Output:** Organized files in `media/audio/`, `media/video/`, `media/photos/`

**File classification by extension:**
| Type | Extensions |
|------|-----------|
| Audio | `.m4a`, `.opus`, `.mp3`, `.aac`, `.ogg`, `.wav` |
| Video | `.mp4`, `.mov`, `.avi`, `.webm`, `.3gp` |
| Photo | `.jpg`, `.jpeg`, `.png`, `.gif`, `.webp` |

**Naming strategy:**
1. Extract date/time from WhatsApp filename pattern: `NNNNNNNN-AUDIO-YYYY-MM-DD-HH-MM-SS.ext`
2. Search nearby teacher messages (within ±2 hours) for context keywords
3. Generate name: `YYYY-MM-DD_Context_HHMM.ext` (e.g., `2024-10-13_Bandish_1308.opus`)
4. Counter suffix for duplicates: `_2`, `_3`, etc.

### 3.5 `organize_events.py` — Event Grouper

**Purpose:** Move media files into event-specific folders.

**Input:** Files in `media/photos/`, `media/video/` + hardcoded event date map

**Output:** `media/events/YYYY-MM-DD_Event-Name/` folders

**Event mapping:** A dictionary mapping dates to event names, built from chat analysis:
```python
EVENTS = {
    '2024-07-21': 'Student-Recital-Jul2024',
    '2025-01-19': 'KHMC-Annual-Day',
    '2025-04-06': 'IAMV-Holi',
    '2026-02-08': 'CMB-Havan',
    # ... 14 events total
}
```

Files are **moved** (not copied) from their category folder into event folders, matched by the date prefix in the filename.

### 3.6 `categorize_audio.py` — AI Audio Categorizer

**Purpose:** Use Google Gemini to analyze audio files and identify Raga, Composition Type, Paltaas, and Taal.

**Input:** Audio files in `media/audio/`

**Output:** `data/audio_categories.json`

**AI interaction:**
1. Upload audio file to Gemini via `genai.upload_file()` with correct MIME type
2. Wait for server-side processing (`state == "PROCESSING"`)
3. Send audio + taxonomy prompt to model via `generate_content()`
4. Parse JSON response (with `_fix_json()` to handle markdown fences and formatting issues)
5. Normalize spelling (e.g., "Bhoopali" → "Bhupali")

**Rate limit handling:**
- **Multi-model fallback:** Tries `gemini-2.0-flash` first, falls back to `gemini-2.5-flash` (separate quota pools)
- **Retry logic:** 5 attempts with exponential backoff (60s, 120s, 180s, 240s, 300s)
- **Inter-file delay:** 60 seconds between files to stay within free tier (5 RPM)
- **Progress saving:** Writes to JSON after each file, so interrupted runs resume where they left off

**Taxonomy prompt:**
```
Identify for this Hindustani classical music audio:
1. Raga (melodic framework)
2. Composition Type (Alaap / Bandish / Taan)
3. Paltaas (is this a practice exercise? Yes/No)
4. Taal (rhythm cycle if audible)

Return ONLY valid JSON.
```

**JSON output per file:**
```json
{
  "raga": "Bhupali",
  "composition_type": "Bandish",
  "paltaas": true,
  "taal": "Teentaal",
  "explanation": "Brief reason for classification"
}
```

---

## 4. Web Server — `app.py`

### 4.1 Server Architecture

The server uses Python's `http.server.SimpleHTTPRequestHandler` with custom `do_GET` and `do_POST` methods. There is no routing framework — paths are matched with simple `if/elif` chains.

**Rendering strategy:**
| Tab | Rendering | Why |
|-----|-----------|-----|
| Dashboard | Server-rendered (f-string) | Static stats, no interactivity needed |
| Music Library | Client-rendered (JavaScript) | Needs drag-drop, inline editing, undo |
| Events | Server-rendered (f-string) | Static gallery, lightbox is simple JS |
| People | Server-rendered (f-string) | Static directory, no editing |

The app is **role-based**: the user chooses Teacher, Student, or Parent on first load. Each role has its own dashboard (teacher: recorder, attendance, events; student: practice log, assignments; parent: kids, fees, events). The Music Library tab is rendered entirely by JavaScript on the client side. Categories and other data are embedded as JSON in a `<script>` tag during page generation, so no additional API call is needed on initial load.

### 4.2 API Endpoints

#### `GET /` — Main Page
- Loads all data (categories, events, people, audio file list, student/parent names, etc.)
- Builds HTML with f-string templating for server-rendered sections
- Embeds JSON only in an inline `<script>` (e.g. `categories`, `allAudioFiles`, `studentNames`, `parentNames`, `teacherVenmo`)
- Links to one stylesheet: `static/css/main.css` (with cache-busting `?v=<mtime>`)
- Loads six external scripts in order: `core.js`, `music-editor.js`, `teacher.js`, `student.js`, `parent.js`, `ai-chat.js`
- Returns complete HTML page

#### `GET /static/*` — Static Assets
- Serves CSS and JavaScript from the project `static/` directory (e.g. `/static/css/main.css`, `/static/js/teacher.js`)
- Used for all front-end assets; no inline CSS or JS except the embedded data blob

#### `GET /api/categories` — Read Categories
- Returns `data/audio_categories.json` as JSON
- Used for programmatic access (not needed by the UI since data is embedded)

#### `GET /media/*` — Static Files
- Serves files from the `media/` directory
- Maps file extensions to MIME types (audio, video, image)
- Returns `404` for non-existent files

#### `POST /api/update-file` — Update Single File
- **Request:** `{ "filename": "file.m4a", "updates": { "raga": "Yaman", "taal": "Dadra" } }`
- Creates a new entry if the file isn't categorized yet (with defaults: raga=Unknown, etc.)
- Merges updates into existing entry
- Saves to disk immediately

#### `POST /api/rename-raga` — Rename Raga
- **Request:** `{ "old_name": "Bhoopali", "new_name": "Bhupali" }`
- Updates all files that have `raga == old_name`
- Returns count of updated files

#### `POST /api/restore` — Undo (Restore Snapshot)
- **Request:** Full categories object (the entire JSON)
- Overwrites `audio_categories.json` with the provided snapshot
- Used by the client-side undo system

#### `POST /api/upload-recording` — In-App Recording (Teacher)
- **Request:** `{ "name": "...", "audio_data": "<base64>", "extension": ".webm" }` (or from file upload)
- Saves audio to tenant `media/audio/{teacher_id}/` and adds entry to categories. Used by the recorder modal (MediaRecorder in teacher.js).

#### `POST /api/ai-query` — AI Natural Language Queries
- **Request:** `{ "query": "Explain Brindavani Sarang" }`
- Calls Gemini with music library context (`ask_ai` in app.py); returns `{ "ok": true, "answer": "...", "sources": [...] }`. Used by ai-chat.js (FAB and chat panel). Requires session.

### 4.3 Frontend Architecture

#### Page Structure
```
<body>
  <div#role-overlay>     — First screen: "Choose your role" (Teacher / Student / Parent)
  <div#app-container>    — Main app (hidden until role selected)
    <header>             — App title, sticky on scroll
    <nav>                — Tab bar (bottom on mobile, top on desktop)
    <main>
      <div#dashboard>   — Role-specific home (teacher-dash / student-dash / parent-dash)
      <div#music>       — Search bar + #music-list container (client-rendered)
      <div#events>      — Event cards with galleries (server-rendered)
      <div#people>      — People cards (server-rendered)
    </main>
    … modals, lightbox, toast, AI chat panel …
  </div>
  <script>              — Inline: categories, allAudioFiles, studentNames, parentNames, teacherVenmo
  <script src="core.js">         — Tab switching (showTab), lightbox (openLightbox)
  <script src="music-editor.js"> — Music library: raga/type/taal dropdowns, drag-drop, undo
  <script src="teacher.js">      — Recorder, attendance, events, role selection (selectRole, switchRole)
  <script src="student.js">     — Student dashboard: picker, practice log, assignments
  <script src="parent.js">      — Parent dashboard: picker, kids, fees, Venmo
  <script src="ai-chat.js">      — AI chat panel, FAB, /api/ai-query
</body>
```

#### Frontend JavaScript (external files)

All front-end logic lives in **external scripts** under `static/js/`, loaded after an inline script that injects `categories`, `allAudioFiles`, `studentNames`, `parentNames`, and `teacherVenmo`. The music editor and role-specific dashboards are implemented as follows:

| File | Responsibility |
|------|----------------|
| `core.js` | Tab switching (`showTab`), lightbox (`openLightbox`) — shared by all roles |
| `music-editor.js` | Music library: uses injected `categories`; raga/type/taal dropdowns, drag-drop, undo, search |
| `teacher.js` | In-browser recorder (MediaRecorder), attendance modal, events, **role selection** (`selectRole`, `switchRole`, `applyRole`) |
| `student.js` | Student picker, practice log, streak, calendar, assignments |
| `parent.js` | Parent picker, "my kids" setup, fees, Venmo, events |
| `ai-chat.js` | AI chat panel, FAB, calls `POST /api/ai-query`, formats responses |

**Music editor (in `music-editor.js`) — key components:**

| Component | Description |
|-----------|-------------|
| `renderMusicLibrary()` | Groups categories by raga, builds HTML, initializes drag-drop |
| `buildRagaGroup()` | Renders a collapsible card for one raga with all its recordings |
| `buildMusicItem()` | Renders one recording with drag handle, dropdowns, toggle, player |
| `buildSelect()` | Generates `<select>` dropdown for composition type or taal |
| `updateField()` | Saves a field change to local state + server |
| `togglePaltaa()` | Toggles paltaas boolean for a file |
| `startEditRaga()` | Replaces raga header with an input field for renaming |
| `initDragDrop()` | Attaches drag/drop event listeners to all items and groups |
| `undoStack` / `pushUndo()` / `undoLastEdit()` | Manages undo history (max 30 snapshots) |
| `showToast()` | Displays notification with optional Undo button |
| `filterMusic()` | Filters visible cards by text search |

**Undo system:**
- Before each edit, `pushUndo()` deep-copies the entire `categories` object
- Stack holds up to 30 snapshots (oldest dropped when full)
- Undo restores the snapshot to both local JS state and server via `POST /api/restore`
- Toast shows "Undo" button for 5 seconds after each save

**Drag and drop:**
- Each `.music-item` has `draggable="true"` and a visible drag handle (⠿)
- Each `.raga-group` is a drop target
- On drop: the dragged file's raga is updated via `updateField()`, triggering a re-render
- Visual feedback: dragged item goes semi-transparent, target group gets a purple border glow

### 4.4 CSS / Responsive Design

**Single stylesheet:** All styles live in **`static/css/main.css`** (~3000 lines). Section locations (e.g. header, nav, music items, modals, role overlay) are documented in **`learnings/CSS-Location-Map.md`** with approximate line numbers so you can jump to the right section when editing.

**Mobile-first approach:**
- Base styles target small screens (phones)
- `@media (min-width: 768px)` overrides for desktop

**Key responsive behaviors:**
| Element | Mobile | Desktop |
|---------|--------|---------|
| Nav bar | Fixed at bottom, icon + label vertical | Static at top, icon + label horizontal |
| Stats grid | 2 columns | 4 columns |
| Photo gallery | 3 columns | Auto-fill, min 160px |
| People grid | 2 columns | Auto-fill, min 200px |
| Body padding | 72px bottom (for nav) | 0 |

**Design system:**
| Token | Value | Usage |
|-------|-------|-------|
| Background | `#0f0f1a` | Page background |
| Card background | `#1a1a2e` | All card surfaces |
| Card inner | `#12122a` | Music items, people cards |
| Border | `#2a2a4a` | All borders |
| Accent | `#7c6ff7` | Active tab, highlights, edit focus |
| Comp type tag | `#5dade2` on `#1e3a5f` | Blue |
| Taal tag | `#a67cf7` on `#3a1e5f` | Purple |
| Paltaa tag | `#8ed25d` on `#2a4a1e` | Green |
| Text primary | `#e0e0e0` | Body text |
| Text secondary | `#888` / `#999` | Labels, filenames |

---

## 5. Data Schemas

### 5.1 `audio_categories.json`

```json
{
  "filename.m4a": {
    "raga": "Bhupali",
    "composition_type": "Bandish",
    "paltaas": true,
    "taal": "Teentaal",
    "explanation": "Brief reason for classification"
  }
}
```

| Field | Type | Values |
|-------|------|--------|
| `raga` | string | Raga name or "Unknown" |
| `composition_type` | string | Alaap, Bandish, Taan, Sargam, Tarana, Unknown |
| `paltaas` | boolean | `true` if this is a sargam/paltaa exercise |
| `taal` | string | Teentaal, Dadra, Keherwa, Jhaptaal, Ektaal, Rupak, Adi Tala, Unknown |
| `explanation` | string | AI-generated reasoning for the classification |

### 5.2 `people.json`

```json
{
  "teacher": {
    "name": "Vaishnavi Kondapalli",
    "role": "teacher",
    "chat_names": ["Vaishnavi  Kondapalli"],
    "messages": 672
  },
  "families": [
    {
      "parent": "Ankur Desai",
      "role": "parent",
      "chat_names": ["Ankur Desai"],
      "messages": 146
    }
  ]
}
```

### 5.3 Media Directory Structure

```
media/
├── audio/                              # 55 files
│   ├── 2024-05-12_Audio_1312.m4a
│   ├── 2024-06-09_Audio_0945.m4a
│   ├── Drive_Bhupali_Practice.m4a     # From Google Drive
│   └── ...
├── video/                              # 2 files
├── photos/                             # 20 files
└── events/                             # 8 event folders
    ├── 2024-07-21_Student-Recital-Jul2024/
    ├── 2025-01-19_KHMC-Annual-Day/
    ├── 2025-04-06_IAMV-Holi/
    ├── 2026-02-08_CMB-Havan/
    └── ...
```

---

## 6. Security Considerations

| Concern | Current state | Future mitigation |
|---------|--------------|-------------------|
| API key exposure | `.env` file, not committed; `.env.example` provided | Add `.env` to `.gitignore` |
| Authentication | All app routes and API endpoints require an authenticated session. Unauthenticated requests get **401** (for `/api/*`) or **302 redirect to /login** (for page requests). Auth methods: **(1) teacher password** (POST /login), **(2) student PIN** (POST /login/student), **(3) parent magic link** (GET /login/parent?token=...). | Add TLS for production |
| No input sanitization on API | JSON parsed but not validated | Add schema validation |
| XSS in music editor | `esc()` function escapes HTML entities | Sufficient for current use |
| File path traversal | `/media/*` routes resolve against `BASE_DIR` | Add explicit path containment check |
| No HTTPS | HTTP only (localhost) | Phase 2: Add TLS for production |

---

## 7. Performance Characteristics

| Metric | Current value | Notes |
|--------|--------------|-------|
| Page load (HTML size) | ~70 KB | Includes embedded categories JSON |
| Initial render | < 1 second | JS renders music library on DOMContentLoaded |
| API save latency | < 50ms | JSON file write is fast for small files |
| Audio categorization | ~1 min/file | Gemini API + 60s rate limit delay |
| Media serving | Direct file read | No caching headers; fine for localhost |

---

## 8. Known Limitations & Technical Debt

| Item | Impact | Remediation |
|------|--------|-------------|
| JSON file storage | No concurrent write safety | Switch to SQLite for Phase 2 |
| No caching | Page rebuilds on every request | Add ETag/Last-Modified headers |
| Hardcoded event dates in `organize_events.py` | New events require code change | Move to config file or auto-detect |
| No tests | Regressions possible | Add unit tests for parser, API |
| `google.generativeai` deprecated | FutureWarning on import | Migrate to `google.genai` package |
| Gemini free tier limits | 5 files still uncategorized | Consider paid tier or batch processing |
| Single-threaded server | One request at a time | Switch to threaded server or async framework |

---

## 9. Future Technical Decisions

### Phase 2: Framework Migration
When adding user roles and authentication, the app should migrate from `http.server` to a proper framework:

| Option | Pros | Cons |
|--------|------|------|
| **Flask** | Simple, familiar, huge community | Synchronous by default |
| **FastAPI** | Async, auto-docs, type safety | Steeper learning curve |
| **Django** | Batteries included (auth, ORM, admin) | Heavy for this use case |

**Recommendation:** Flask for simplicity, consistent with the "simple solutions" philosophy.

### Phase 2: Database Migration
Move from JSON files to a relational database:

| Option | Pros | Cons |
|--------|------|------|
| **SQLite** | Zero config, single file, built into Python | No concurrent writes |
| **PostgreSQL** | Full-featured, scalable | Requires separate server |

**Recommendation:** SQLite for Phase 2, PostgreSQL if multi-user concurrency becomes needed.

### Phase 2: Authentication
| Option | Pros | Cons |
|--------|------|------|
| **Simple password per role** | Easy to implement, good enough for a small class | Not scalable |
| **Flask-Login + sessions** | Standard approach, role-based | Requires user management |
| **OAuth (Google)** | Families likely have Google accounts | Complex setup |

**Recommendation:** Simple password per role (teacher/student/parent) for Phase 2, upgrade to sessions if needed.

---

## 10. Build principles for Phase 2 (auth & multi-tenancy)

These principles guide how auth and multi-tenancy are built so the codebase stays maintainable and edits stay small.

### 10.1 Separation of functions

One module (or small set) per concern: **auth** (sessions, login), **tenant/data access** (load/save scoped by `teacher_id`), and **HTTP** (routes, response). No auth logic inside route handlers beyond "get current session"; no SQL or PIN logic in the HTML builder. Clear boundaries make changes local and reduce token-heavy files.

### 10.2 Easy isolation of areas to improve

Auth method (password / PIN / magic link) lives behind a thin interface (e.g. "resolve credentials → session or None") so we can swap to OAuth or SMS later without touching routes. Data access lives behind functions that take `teacher_id` (and optional identity); storage can move from JSON to SQLite to PostgreSQL without changing callers. Small, focused files (e.g. `auth.py`, `tenant_data.py`) so improvements touch few lines.

### 10.3 Minimize tokens

Prefer many small modules over one large `app.py`. Reusable helpers live in dedicated files; the main server file stays a thin dispatcher: "get session → load tenant data → build response." Document "where to change X" in this TDD or a one-page map so edits are targeted and context stays small.

### 10.4 Phased build

Auth and multi-tenancy will be built in phases; each phase delivers a testable slice and keeps auth, data, and UI changes isolated. See **§5 Phased build plan** in `.cursor/plans/role-based_authorized_access_3b456b7d.plan.md` for the ordered phases and file layout.
