# Music Class Organizer — Product Requirements Document

**Version:** 1.0
**Last updated:** February 2026
**Author:** Built with AI assistance (Cursor + Claude)
**Status:** MVP complete; Phase 2 (roles, auth, in-app recording) and Phase 3 (AI queries) done.

---

## 1. Product Vision

### What is it?
A mobile-friendly web app that organizes a children's Hindustani classical music class — turning scattered WhatsApp chats, audio recordings, photos, and videos into a structured, browsable music learning platform.

### Why does it matter?
The music class currently runs entirely through WhatsApp. Practice recordings, event photos, class schedules, and payment discussions are all buried in a single group chat. Parents can't find last week's bandish recording. The teacher can't track who attended. Nobody knows what raga that recording from three months ago was for.

This app turns chaos into organization — making it easy to find any recording, relive any event, and track any class.

### The big idea
**WhatsApp is the data source, not the product.** We extract everything valuable from chat exports and present it through purpose-built interfaces for teachers, students, and parents.

---

## 2. Target Users

### User 1: Teacher (Vaishnavi Kondapalli)
- **Role:** Primary content creator and class manager
- **Pain points:** Shares recordings via WhatsApp but they get buried; no easy way to track attendance or fees; re-records demonstrations because old ones are lost
- **Goal:** A single place to manage her music library, track classes, and communicate with families
- **Key metric:** Time to share a new recording drops from minutes (WhatsApp) to seconds (in-app)

### User 2: Students (Kids, ages 6–14)
- **Role:** Learners practicing Hindustani classical music
- **Pain points:** Can't find the recording teacher shared last week; don't know what to practice; no sense of progress
- **Goal:** A simple practice companion — find recordings, listen, track progress
- **Key metric:** Can find any practice recording in under 10 seconds

### User 3: Parents
- **Role:** Logistics, payments, and encouragement
- **Pain points:** Don't know when next class is; can't calculate fees owed; want to see kid's progress and event memories
- **Goal:** At-a-glance dashboard for class info, fees, and their child's journey
- **Key metric:** Know exactly what they owe and when the next class is, without asking

---

## 3. Current State (What We've Built)

### Data Pipeline — Complete
| Component | Status | Details |
|-----------|--------|---------|
| WhatsApp chat parser | Done | Handles multiple export formats, Unicode, multi-line messages |
| Multi-chat combiner | Done | Merges and deduplicates messages from multiple exports |
| Class date extractor | Done | Identifies class dates from teacher messages (keywords, links) |
| Media organizer | Done | Extracts and renames 55 audio, 2 video, 20 photo files with dates and context |
| Event grouper | Done | Groups media into 8 event folders (KHMC, Holi, Independence Day, etc.) |
| AI audio categorizer | Done | Google Gemini categorizes recordings by Raga, Composition Type, Paltaas, Taal |
| People directory | Done | 1 teacher + 21 families extracted from chat participants |

### Music Library — 50 recordings categorized
| Raga | Count | Notes |
|------|-------|-------|
| Bhupali | ~10 | Most practiced raga |
| Bilawal | ~7 | Foundational raga |
| Yaman | ~5 | Evening raga |
| Khamaj | ~4 | Light classical |
| Bhairavi | ~4 | Devotional mood |
| Brindavani Sarang | ~3 | Midday raga |
| Kafi | ~3 | Holi compositions |
| Hamsadhwani | ~2 | Pentatonic raga |
| Others | ~5 | Pilu, Shankarabharanam, Bhairav |
| Unknown | ~7 | Pending identification |

### Web UI — Live at localhost:8000
- Mobile-responsive design (bottom tab bar on phones, top nav on desktop)
- Four tabs: Dashboard, Music Library, Events & Memories, People
- **Interactive music editor:** drag-drop between ragas, rename ragas, edit composition type/taal/paltaas via dropdowns, undo last edit
- Event photo/video gallery with lightbox
- People directory
- Search and filter

---

## 4. Feature Specifications

### 4.1 Music Library (MVP — Done)

**What it does:** Browse, play, search, and edit categorized music recordings.

**User stories:**
- As a parent, I want to find the Bhupali bandish recording so my child can practice at home
- As a teacher, I want to correct a misidentified raga so students learn the right name
- As a student, I want to browse all recordings for the raga I'm learning

**Acceptance criteria:**
- [x] Recordings grouped by Raga with expandable sections
- [x] Each recording shows: filename, composition type, taal, paltaa status, audio player
- [x] Search bar filters across all fields
- [x] Drag and drop to move recordings between raga groups
- [x] Click raga name to rename (updates all recordings in that group)
- [x] Dropdown selectors for Composition Type and Taal
- [x] Toggle button for Paltaas
- [x] Undo button appears after each edit (up to 30 undos)
- [x] All changes persist to `audio_categories.json` immediately

### 4.2 Events & Memories (MVP — Done)

**What it does:** Browse photos and videos organized by cultural event.

**User stories:**
- As a parent, I want to find the KHMC Annual Day photos to share with grandparents
- As a student, I want to see videos from our Holi performance

**Acceptance criteria:**
- [x] Events listed newest-first with photo/video counts
- [x] Photo grid gallery with tap-to-enlarge lightbox
- [x] Video playback inline
- [x] 8 events organized: KHMC Annual Day, Holi, Independence Day, CMB Havan, Student Recital, Performance Day, Diwali Mela Prep, iTablaPro Setup

### 4.3 People Directory (MVP — Done)

**What it does:** View the class community — teacher and families.

**User stories:**
- As a new parent, I want to see who else is in the class

**Acceptance criteria:**
- [x] Teacher highlighted at top
- [x] Families listed with message count
- [x] Role badges (teacher/parent)

### 4.4 Dashboard (MVP — Done)

**What it does:** At-a-glance stats about the music library.

**Acceptance criteria:**
- [x] Total audio recordings count
- [x] Number of ragas identified
- [x] Number of events
- [x] Number of people

### 4.5 In-App Recording (Phase 2 — Done)

**What it does:** Teacher records music directly in the app, replacing WhatsApp audio messages. Implemented: MediaRecorder API in teacher.js, recorder modal (Record New → name → Save), POST /api/upload-recording saves to tenant media folder and categories.

**User stories:**
- As a teacher, I want to record a bandish demonstration and have it automatically tagged and available to students
- As a teacher, I want to record quick feedback for a specific student

**Recording flow:**
1. Tap "Record" button
2. Select metadata: Raga, Composition Type, Taal, Notes
3. Record audio (with waveform visualization)
4. Preview and re-record if needed
5. Save — immediately tagged, added to library, available to students

**Recording types:**
| Type | Use case |
|------|----------|
| Demonstration | Teacher sings the full piece for reference |
| Paltaa exercise | Specific sargam patterns to practice |
| Class recording | Record a live class session |
| Feedback | Voice note for a specific student |

### 4.6 Role-Based Access (Phase 2 — In progress)

**What it does:** Different interfaces for Teacher, Student, and Parent.

**Teacher auth (done):** Login page at GET /login; POST /login with email+password; session stored in signed cookie; GET / requires teacher session (redirects to /login otherwise). Teachers table in SQLite (src/db.py), verify_teacher in src/auth.py. When no teachers exist, GET /login shows a one-time "Create first teacher account" form; POST /signup creates the first teacher and logs them in (enables deployment without running add_teacher.py). Additional teachers can be added via `python src/add_teacher.py <email> <password>`. **Local setup:** To make the first teacher (linked to data under tenant id 1) log in with a fixed email/password, run once: `python scripts/seed_first_teacher.py` (see requirements.md § Local setup — first teacher).

**Student PIN auth (Phase 4 — done):** Students log in at GET /login/student with a PIN. Teacher sets each student's PIN from the dashboard ("Student login PINs" section). PINs stored hashed in tenant_data (student_pins.json). Session for student has role=student, teacher_id, student_id (student name). GET / is allowed for both teacher and student sessions; client receives sessionRole and sessionStudentId so the student sees the student dashboard without the role picker.

**Parent magic-link login (Phase 5 — done):** Teacher generates a one-time login link per parent from the People tab ("Generate login link"). GET /login/parent?token=... consumes the token (stored in parent_login_tokens table, 7-day expiry); on success session has role=parent, teacher_id, parent_id (parent name); redirect to /. Parent sees only their own profile and data; APIs filter by session parent_id when role=parent. Client receives sessionParentId and skips the parent name picker.

**Teacher view:** Full management — music library, class schedule, attendance, fees, recording, set student PINs, generate parent login links
**Student view:** Practice-focused — assignments, audio player, progress tracker, "I practiced" button (reached via PIN login or localStorage role)
**Parent view:** Oversight — dashboard, child's progress, fees, event memories (reached via magic link or localStorage role)

### 4.7 Tenant-scoped data (Phase 3 — Done)

**What it does:** All tenant data is keyed by `teacher_id`; the data layer returns only the current teacher’s data. Session holds `teacher_id` for the logged-in teacher.

**Implementation:**
- `src/tenant_data.py`: load/save functions per entity (attendance, practice_log, assignments, scheduled_events, people, audio_categories, parent_profiles), each taking `teacher_id`. JSON files use format `{ "1": data, "2": data, ... }`; legacy single-tenant content is treated as teacher_id 1.
- All relevant GET/POST handlers in `app.py` use `get_session(self)`, require `teacher_id`, and call `tenant_data.load_*` / `tenant_data.save_*` with `session["teacher_id"]`. Unauthenticated requests receive 401.
- Dashboard (`build_page(teacher_id)`) and AI context use tenant-scoped data so each teacher sees only their own classes, assignments, and people.
- **Media:** Audio files live under `media/audio/{teacher_id}/`, event galleries under `media/events/{teacher_id}/`, photo uploads under `media/photos/{teacher_id}/`. URLs include teacher_id (e.g. `/media/audio/1/file.opus`). Frontend gets `mediaAudioBase` from the page so music library and student views use the correct base. Optional migration: `python scripts/migrate_media_to_tenant_dirs.py` moves existing shared media into `.../1/` for the first tenant.
- **School name:** Stored in `people.teacher.school_name`; shown in the app header; editable via Teacher settings (same modal as Venmo). Defaults to `{teacher.name}'s Music School` if not set.

### 4.8 AI-Powered Features (Phase 3 — Done)

**What it does:** Natural language queries about music and learning. Implemented: Gemini (ask_ai in app.py), POST /api/ai-query, ai-chat.js FAB and chat panel with conversation history, suggested questions, markdown responses; multi-model fallback, graceful handling when API unavailable.

**Example queries:**
- "Show me all Brindavani Sarang recordings"
- "Explain the structure of Yaman"
- "Find YouTube videos of Kishori Amonkar singing this raga"
- "What should I practice before the next class?"
- "Which paltaas help with Yaman?"

### 4.9 Class & Practice Tracking (Phase 4 — Planned)

**What it does:** Calendar, attendance, fees, practice streaks.

**User stories:**
- As a parent, I want to know exactly how many classes my child attended and what I owe
- As a teacher, I want to see which students haven't practiced in a week
- As a student, I want to maintain my practice streak

---

## 5. Technical Architecture

### Tech Stack
| Layer | Technology | Notes |
|-------|-----------|-------|
| Language | Python 3.14 | All scripts and server |
| Web server | `http.server` (stdlib) | Simple, no framework dependencies |
| Frontend | Vanilla HTML/CSS/JS | Mobile-first, no build tools |
| AI | Google Gemini 2.5 Flash | Audio categorization via API |
| Data storage | JSON files + tenant layer | `tenant_data.py` loads/saves per `teacher_id`; files like `attendance.json` use `{ "teacher_id": data }` |
| Data source | WhatsApp chat exports (.zip) | Multiple format support |

**Server startup:** On startup, the app refuses to bind to non-localhost (e.g. `HOST=0.0.0.0`) when `SESSION_SECRET` is the dev default, to avoid exposing a weak cookie secret on the network. Set `SESSION_SECRET` in `.env` (e.g. `openssl rand -hex 32`) for network access.

### Project Structure
```
MusicClassOrganizer/
├── src/
│   ├── app.py                  # Web UI server (localhost:8000)
│   ├── tenant_data.py          # Tenant-scoped load/save (per teacher_id)
│   ├── parse_whatsapp.py       # WhatsApp chat parser
│   ├── combine_chats.py        # Multi-chat merger
│   ├── extract_classes.py      # Class date extractor
│   ├── organize_media.py       # Media file organizer
│   ├── organize_events.py      # Event grouper
│   └── categorize_audio.py     # AI audio categorizer (Gemini)
├── data/
│   ├── whatsapp-export/        # Raw WhatsApp exports (.zip)
│   ├── audio_categories.json   # AI-generated + manually edited tags
│   └── people.json             # People directory
├── media/
│   ├── audio/                  # 55 audio recordings
│   ├── video/                  # 2 video recordings
│   ├── photos/                 # 20 photos
│   └── events/                 # 8 event folders with grouped media
├── docs/
│   ├── requirements.md         # Feature requirements
│   ├── PRD.md                  # This document
│   └── parsed-data-ideas.md    # Brainstorming notes
├── .env                        # Google API key (not committed)
├── .env.example                # API key template
├── AGENTS.md                   # AI assistant instructions
└── requirements.txt            # Python dependencies
```

### Data Flow
```
WhatsApp .zip exports
        │
   parse_whatsapp.py  ──→  Structured messages
        │
   combine_chats.py   ──→  Merged + deduplicated
        │
   ├──→ extract_classes.py   ──→  Class dates & events
   ├──→ organize_media.py    ──→  media/audio, video, photos
   │         │
   │    organize_events.py   ──→  media/events/ (grouped)
   │
   └──→ categorize_audio.py  ──→  audio_categories.json (AI tags)

   app.py  ←── reads all of the above ──→  Web UI at localhost:8000
```

### API Endpoints
| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Main page (HTML) |
| GET | `/api/categories` | Current audio categories (JSON) |
| GET | `/media/*` | Serve audio, video, photo files |
| POST | `/api/update-file` | Update one file's categorization |
| POST | `/api/rename-raga` | Rename a raga across all files |
| POST | `/api/restore` | Undo — restore full categories snapshot |

---

## 6. Development Phases & Milestones

### Phase 1: Foundation & Data — COMPLETE
**Goal:** Extract, organize, and browse all data from WhatsApp exports.

| Milestone | Status | Date |
|-----------|--------|------|
| WhatsApp parser (multiple formats) | Done | Feb 2026 |
| Media extraction and organization | Done | Feb 2026 |
| AI audio categorization (Gemini) | Done (50/55) | Feb 2026 |
| Event photo/video grouping | Done | Feb 2026 |
| People directory | Done | Feb 2026 |
| Mobile-responsive web UI | Done | Feb 2026 |
| Editable categorization with undo | Done | Feb 2026 |

### Phase 2: User Roles & Core UI — Next
**Goal:** Separate experiences for Teacher, Student, and Parent.

| Milestone | Priority | Effort |
|-----------|----------|--------|
| In-app recording for teacher | High | Medium |
| Teacher dashboard | High | Medium |
| Student practice view | High | Medium |
| Parent dashboard with fees | Medium | Medium |
| Login / role-based access | Medium | High |

### Phase 3: AI-Powered Features
**Goal:** Natural language interaction with the music library.

| Milestone | Priority | Effort |
|-----------|----------|--------|
| Natural language queries | Medium | High |
| Public resource linking (YouTube, Spotify) | Low | Medium |
| Smart tagging suggestions | Low | Medium |
| Practice recommendations | Low | Medium |

### Phase 4: Tracking & Polish
**Goal:** Full class management and engagement features.

| Milestone | Priority | Effort |
|-----------|----------|--------|
| Class calendar & attendance | Medium | Medium |
| Fee calculator & payment tracking | Medium | Medium |
| Practice streaks & reminders | Low | Low |
| Push notifications | Low | High |
| Sharing & export | Low | Medium |

### Phase 5: Parent magic link — COMPLETE
**Goal:** Parents can log in via a one-time link generated by the teacher.

| Milestone | Status | Notes |
|-----------|--------|-------|
| Token store (create_parent_token, consume_parent_token) | Done | auth.py; parent_login_tokens table in db.py |
| GET /login/parent?token=... sets parent session | Done | Redirect to /; "Invalid or expired link" on failure |
| Teacher UI: Generate login link per parent | Done | People tab; GET /api/parent-login-link; Copy link in toast |
| Parent session sees only their data | Done | parent-profiles and save/mark-payment filtered by parent_id |

---

## 7. Risks & Open Questions

### Technical Risks
| Risk | Impact | Mitigation |
|------|--------|------------|
| Gemini API free tier quota limits | 5 files still uncategorized | Wait for quota reset; consider paid tier for production |
| No database (JSON files only) | Won't scale past ~100 users | Fine for MVP; migrate to SQLite or Postgres in Phase 2 |
| Teacher auth only (no Student/Parent login) | Students/parents use localStorage role | Teacher login done; Student PIN login done (Phase 4); Parent magic-link login done (Phase 5) |
| WhatsApp format changes | Parser may break with new exports | Parser handles 2 formats already; add more as needed |

### Open Questions
1. **Hosting:** Where will this run in production? (Local machine, cloud, Raspberry Pi?) See **docs/DEPLOYMENT.md** for HTTPS requirement, checklist, and PaaS + reverse-proxy options.
2. **Authentication:** Simple password per role, or full user accounts?
3. **SMS integration:** User mentioned iPhone SMS messages with recordings — how to import?
4. **Payment integration:** Just tracking, or actual payment processing (Venmo, Zelle)?
5. **Multi-class support:** Will Vaishnavi teach other groups? Should the app support multiple classes?
6. **Offline access:** Should students be able to download recordings for offline practice?

---

## 8. Success Metrics

| Metric | Target | How to measure |
|--------|--------|----------------|
| Recording findability | < 10 seconds to find any recording | User testing |
| Categorization accuracy | > 90% correct after AI + manual edits | Spot-check sample |
| Teacher recording time | < 30 seconds from tap to published | Stopwatch test |
| Fee accuracy | 100% match with manual count | Compare with teacher's records |
| Parent satisfaction | "I know what's going on" | Qualitative feedback |

---

## Appendix: Hindustani Music Taxonomy

### Ragas Identified in Our Library
| Raga | Time of Day | Mood | Recordings |
|------|-------------|------|------------|
| Bhupali | Evening | Devotional, serene | ~10 |
| Bilawal | Morning | Bright, uplifting | ~7 |
| Yaman | Evening | Romantic, peaceful | ~5 |
| Khamaj | Evening | Light, playful | ~4 |
| Bhairavi | Morning | Devotional, emotional | ~4 |
| Brindavani Sarang | Midday | Devotional, serene | ~3 |
| Kafi | Afternoon | Festive (Holi) | ~3 |
| Hamsadhwani | Anytime | Auspicious, bright | ~2 |
| Pilu | Anytime | Folk, light classical | ~1 |
| Bhairav | Early morning | Serious, meditative | ~1 |

### Composition Types
| Type | Description | In our library |
|------|-------------|----------------|
| **Bandish** | Fixed composition with lyrics, set to taal | Most common |
| **Alaap** | Slow, improvised exploration without rhythm | Several |
| **Taan** | Fast melodic runs and ornamentations | A few |
| **Sargam/Paltaa** | Practice exercises using note names | Common |
| **Tarana** | Rhythmic syllables (bols) composition | Rare |

### Taal (Rhythm Cycles)
| Taal | Beats | In our library |
|------|-------|----------------|
| Teentaal | 16 | Most common |
| Dadra | 6 | Very common |
| Keherwa | 8 | Several |
| Jhaptaal | 10 | A few |
| Ektaal | 12 | Rare |
