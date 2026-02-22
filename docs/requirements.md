# Music Class Organizer — Requirements

## Problem statement

My kids' music class uses WhatsApp as the sole communication channel. This creates challenges:
- Recordings to practice are scattered across chat history
- No organization by raga, composition type, or learning progression
- Hard to understand what each recording is (alaap? bandish? sargam practice?)
- Photos and videos from events are hard to find later
- No clear record of which classes were attended
- Difficult to reconcile attendance with fees owed to the teacher

## Solution

An app that organizes Hindustani classical music learning by parsing WhatsApp exports and structuring information around four main areas.

---

## Four Main Entities

### 1. Music We Are Learning
Practice recordings, demonstrations, and reference material organized by the Hindustani music system.

### 2. Events & Memories
Photos and videos from cultural events, performances, and celebrations.

### 3. Class & Practice Tracking
Attendance records, fee calculations, and practice reminders.

### 4. People & Contacts
Teacher, parents, and students in the music class community.

---

## Entity 1: Music We Are Learning

### Categories

| Category | Description | Examples |
|----------|-------------|----------|
| **Raga** | Melodic framework | Brindavani Sarang, Yaman, Bhairav |
| **Composition Type** | What kind of piece | Alaap, Bandish, Taan |
| **Paltaas** | Sargam exercises | Basic, Alankar, Raga-specific |
| **Taal** | Rhythm cycle | Teentaal (16), Ektaal (12), Jhaptaal (10) |

### Content types
- Audio recordings (practice demos from teacher)
- Video demonstrations
- Google Drive links to reference material
- Notes and instructions from chat

### Features
- [x] Categorize recordings by Raga, Composition Type, Paltaas, Taal
- [x] Display organized music library with metadata
- [x] Search and filter by any category or date
- [x] **Editable categorization** — adjust AI-generated tags directly in the UI:
  - Drag and drop recordings between raga groups to re-classify
  - Click raga name to rename it (updates all recordings in that group)
  - Dropdown selectors for Composition Type and Taal
  - Toggle button for Paltaas (yes/no)
  - All changes saved immediately to `audio_categories.json`
  - Undo last edit button (appears in toast notification after each save, up to 30 edits)
- [x] AI-powered queries ("Explain Brindavani Sarang", "Find famous recordings")
- [ ] Link to public resources (YouTube, Spotify, educational sites)

---

## Entity 2: Events & Memories

### Event types

| Event | Description |
|-------|-------------|
| **Concerts & Performances** | Kids performing at venues (KHMC Annual Day, CMB Havan) |
| **Diwali** | Celebrations and performances for the festival of lights |
| **Holi** | Spring festival celebrations |
| **Independence Day** | August 15th celebrations and patriotic songs |
| **Class Milestones** | First bandish learned, group photos |
| **Recitals** | Teacher's concerts, guest performances |

### Content types
- Photos from events
- Videos of performances
- Event flyers and announcements
- Location and date information

### Features
- [x] Organize media by event name and date
- [x] Auto-detect event type from chat context
- [x] Timeline/gallery view of memories
- [ ] Tag people in photos
- [ ] Share collections with other parents

---

## Entity 3: Class & Practice Tracking

### What to track

| Item | Description |
|------|-------------|
| **Class dates** | When classes were held (in-person, online) |
| **Attendance** | Who attended each class |
| **Fees** | Classes attended × fee per class |
| **Practice log** | What was practiced, when |
| **Assignments** | What teacher asked to practice |

### Features
- [ ] Calendar view of past and upcoming classes
- [x] Attendance tracking (manual marking via teacher dashboard)
- [ ] Fee calculator with payment tracking
- [ ] Practice reminders ("You haven't practiced the bandish in 5 days")
- [ ] Progress tracking by raga/composition
- [x] Practice assignment creation (teacher assigns recordings to students)

---

## Entity 4: People & Contacts

### Roles

| Role | Description |
|------|-------------|
| **Teacher** | Vaishnavi Kondapalli |
| **Parents** | Adults in the WhatsApp group |
| **Students** | Kids taking the class |

### Information to store
- Name and phone number
- Which student(s) belong to which parent
- Payment history
- Attendance record per student

### Features
- [ ] Contact directory
- [x] Link parents to students (parent selects children in parent dashboard)
- [x] Per-student attendance and progress view (parent sees child practice streaks)
- [x] Payment history per family (parents can record and view payments)

---

## User Groups & UI

### Three user groups with different needs:

### 1. Teacher (Vaishnavi)

The primary content creator and class manager.

**Dashboard:**
- Upcoming classes and schedule management
- Student roster and attendance overview
- Fee tracker (who owes what)

**Music Library (manage):**
- Browse all recordings by Raga, Composition Type, Paltaas, Taal
- **Record directly in the app** (replaces sending audio via WhatsApp)
  - One-tap recording with auto-tagging (select Raga, Type, Taal before recording)
  - Record demonstrations, bandishes, and paltaa exercises
  - Recordings auto-categorized and immediately available to students
- Upload existing recordings
- Edit/correct AI-generated tags
- Add notes and instructions to recordings

**Class Management:**
- Create/edit class schedule
- Mark attendance
- Send practice assignments to students
- View per-student progress

**Events:**
- Create events (concerts, recitals, celebrations)
- Share event details with parents
- Upload event photos/videos

---

### 2. Students (Kids)

A simple, focused interface for practice and learning.

**My Practice:**
- Today's assignments from teacher
- Audio player with recordings organized by Raga
- Practice timer / streak tracker
- "I practiced today" button

**Music Library (browse):**
- Browse recordings by Raga, Composition Type, Paltaas, Taal
- Play teacher demonstrations
- AI assistant: "Explain this raga", "Show me famous recordings"

**My Progress:**
- Which ragas I'm learning
- Practice streaks and history
- Upcoming classes

**Memories:**
- Photos and videos from events I participated in

---

### 3. Parents

Overview of their child's progress, fees, and logistics.

**Dashboard:**
- Next class date, time, location
- Outstanding fees
- Child's recent practice activity

**My Child's Progress:**
- Attendance history
- Ragas being learned
- Practice log (from student's "I practiced" button)
- Teacher's notes and assignments

**Fees & Payments:**
- Classes attended × fee per class
- Payment history
- Mark payments as made

**Events & Memories:**
- Event calendar
- Photo/video gallery organized by event
- Share memories with other parents

**Music Library (listen):**
- Browse practice recordings (same as student view)
- Play recordings to help child practice at home

---

### In-App Recording (Teacher Feature)

A key feature to replace WhatsApp audio messages.

**Recording Flow:**
1. Teacher taps "Record" button
2. Selects metadata before recording:
   - Raga (from saved list or type new)
   - Composition Type (Alaap / Bandish / Taan / Paltaa)
   - Taal (from saved list)
   - Notes (optional, e.g. "Focus on the taan section")
3. Records audio (with waveform visualization)
4. Preview and re-record if needed
5. Save — recording is immediately:
   - Tagged with metadata
   - Added to the music library
   - Available to all students
   - Optionally pushed as a practice assignment

**Recording types:**
| Type | Use case |
|------|----------|
| **Demonstration** | Teacher sings the full piece for reference |
| **Paltaa exercise** | Specific sargam patterns to practice |
| **Class recording** | Record a live class session |
| **Feedback** | Voice note for a specific student |

---

## Phases

### MVP (Phase 1) — Foundation & Data
- [x] Parse WhatsApp chat export files (multiple formats)
- [x] Extract and organize media files (audio, video, photos)
- [x] Categorize music recordings (Raga, Composition Type, Paltaas, Taal)
- [x] Organize event photos/videos by event name and date
- [x] Basic people directory from chat participants
- [x] Simple web UI to browse music library and events
- [x] Editable categorization (drag-drop between ragas, rename ragas, edit tags)

### Phase 2 — User Roles & Core UI
- [x] Role selection screen (Teacher / Student / Parent)
- [x] Teacher dashboard with 3 action areas:
  - [x] Music & Practice: Record, browse library, assign practice
  - [x] Attendance & Progress: Mark attendance, view history
  - [x] Events: Create/schedule events, view gallery, upload photos
- [x] **In-app recording for teacher** (MediaRecorder API, record + name + save)
- [x] Attendance tracking with student checklist and date selection
- [x] Practice assignment creation (select recording + students + due date)
- [x] Event scheduling (name, date, time, location, description)
- [x] Photo/media upload from teacher dashboard
- [x] Student practice dashboard:
  - [x] Student name picker (remembered in browser)
  - [x] Daily "I practiced today" button per assignment
  - [x] Practice streak counter (consecutive days)
  - [x] 14-day practice calendar visualization
  - [x] Read-only music library browse (grouped by raga)
  - [x] Practice log stored per student per date
  - [x] Assignments practiced every day between classes
- [x] Parent dashboard with fees and progress:
  - [x] Parent self-identification from list
  - [x] Select child(ren) from student list
  - [x] View children's practice streaks and 7-day calendar
  - [x] Classes since last payment counter
  - [x] Last payment date display
  - [x] Venmo link for payment to teacher
  - [x] Record payment (amount + note)
  - [x] Payment history
  - [x] Upcoming events view
- [x] **Teacher login:** GET /login shows form; POST /login with email+password calls verify_teacher; on success set session cookie and redirect to /. GET / redirects to /login when no session. Session from signed cookie (auth.py, db teachers table).
- [x] **First-teacher signup:** When no teachers exist in the DB, GET /login shows a one-time "Create first teacher account" form (email, password, optional display name); POST /signup creates the teacher and logs them in. After the first teacher exists, /login shows normal teacher login. Enables deployment (e.g. Render) without running add_teacher.py by hand.
- [x] **Student PIN login (Phase 4):** GET /login/student shows PIN form; POST /login/student verifies PIN via verify_student_pin/resolve_student_by_pin; on success session has role=student, teacher_id, student_id (student name). PINs stored hashed in tenant_data (student_pins.json). GET / allowed when session is teacher or student (with teacher_id and student_id). Teacher dashboard has "Student login PINs" section: one input + Set PIN button per student; POST /api/student/set-pin stores PIN for that student. Client uses sessionRole/sessionStudentId from server to skip role overlay and show student dashboard.
- [x] **Parent magic-link login (Phase 5):** Token store in auth.py: create_parent_token(teacher_id, parent_id) and consume_parent_token(token); tokens stored in DB table parent_login_tokens with expiry (7 days), one-time use. GET /login/parent?token=... consumes token; on success session has role=parent, teacher_id, parent_id (parent name); redirect to /. Invalid/expired link shows "Invalid or expired link" page. Teacher People tab: "Generate login link" per parent; GET /api/parent-login-link?parent_id=... returns full URL; teacher can copy link and send to parent. Parent session sees only their own data (parent-profiles filtered by parent_id; save/mark-payment restricted to session parent). Client receives sessionParentId and skips parent name picker when set.

### Phase 3 — AI-Powered Features
- [x] Natural language queries about music and recordings
  - [x] Floating AI chat button (bottom-right)
  - [x] Chat panel with conversation history
  - [x] Gemini-powered answers with music library context
  - [x] Suggested starter questions
  - [x] Markdown formatting in responses
  - [x] Multi-model fallback (gemini-2.0-flash → gemini-2.5-flash)
  - [x] Graceful handling when API unavailable
- [x] Link to public resources (YouTube, Spotify, educational content)
  - [x] YouTube, Spotify, Wikipedia links on every raga header in music library
  - [x] Resource links auto-added to AI chat responses when ragas are mentioned

### Phase 3 — Tenant-scoped data
- [x] **Data layer:** `tenant_data.py` — all load/save take `teacher_id` and return or write only that tenant’s data.
- [x] **JSON format:** Existing files kept; structure extended to `{ "teacher_id": data, ... }` so one file holds all tenants. Legacy single-tenant content treated as teacher_id 1 on first read.
- [x] **Entities scoped:** Attendance, practice log, assignments, scheduled events, people, audio categories, parent profiles. Dashboard and all relevant API endpoints use `session['teacher_id']` and tenant_data.
- [x] **Auth:** Teacher-only API endpoints require session with `teacher_id`; unauthenticated requests get 401. Student PIN login: session may have role=student with teacher_id and student_id; GET / served for both teacher and student sessions.
- [x] **Phase 6 — Enforce & document:** All sensitive routes and APIs check session via `require_session()`; missing session yields 401 (API) or redirect to /login (pages). Auth methods: teacher password, student PIN, parent magic link. TDD §6 and requirements updated.
- [x] **Startup check:** Server refuses to bind to non-localhost (e.g. HOST=0.0.0.0) when SESSION_SECRET is the dev default; set SESSION_SECRET in .env for network access or use HOST=localhost for local dev.
- [x] **Tenant-scoped media:** Audio files under `media/audio/{teacher_id}/`, event media under `media/events/{teacher_id}/`, photo uploads under `media/photos/{teacher_id}/`. Frontend uses `mediaAudioBase` (e.g. `/media/audio/1/`) for playback and download.
- [x] **School name:** Per-tenant from `people.teacher.school_name` (editable in Teacher settings); shown in header; default `{teacher.name}'s Music School`. API: `POST /api/teacher/update-venmo` accepts optional `school_name`.
- [ ] Smart tagging suggestions for uncategorized content
- [ ] Practice recommendations

### Phase 4 — Student PIN auth (done)
- [x] **Student PIN auth:** verify_student_pin(teacher_id, pin) and resolve_student_by_pin(pin) in auth.py; PINs in tenant_data (student_pins.json). GET/POST /login/student; POST /api/student/set-pin; teacher dashboard "Student login PINs" section; client sessionRole/sessionStudentId for student view.

### Phase 5 — Parent magic link (done)
- [x] **5a Tokens:** create_parent_token(teacher_id, parent_id) and consume_parent_token(token) in auth.py; parent_login_tokens table in db.py; one-time tokens with 7-day expiry.
- [x] **5b Consume link:** GET /login/parent?token=... sets session (role=parent, teacher_id, parent_id), redirect to /; else "Invalid or expired link". GET / allows parent session; build_page passes parent_id; sessionParentId in script; teacher.js sets musicClassParent when role=parent. APIs /api/parent-profiles and parent-profile/save, mark-payment restricted to session parent when role=parent.
- [x] **5c Teacher UI:** GET /api/parent-login-link?parent_id=... (teacher only) returns { url }; build_people_html shows "Generate login link" per parent when role=teacher; teacher.js click handler fetches API and shows Copy link in toast.

### Phase 4 — Tracking & Polish
- [ ] Class calendar view (calendar UI)
- [x] Fee calculation and payment tracking (implemented in parent dashboard)
- [x] Practice streaks (implemented in student dashboard)
- [ ] Practice reminders (push notifications)
- [ ] Push notifications for assignments and class reminders
- [ ] Sharing and export features

---

## Appendix: Hindustani Music Reference

### Raga Reference
| Raga | Time of Day | Mood |
|------|-------------|------|
| Brindavani Sarang | Midday | Devotional, serene |
| Yaman | Evening | Romantic, peaceful |
| Bhairav | Early morning | Serious, meditative |
| Bhimpalasi | Afternoon | Tender, longing |

### Composition Types
| Type | Description |
|------|-------------|
| **Alaap** | Slow, improvised exploration without rhythm. Builds the mood. |
| **Bandish** | Fixed composition with lyrics, set to taal. The main "song." |
| **Taan** | Fast melodic runs and ornamentations. |

### Paltaas (Sargam Exercises)
| Type | Description |
|------|-------------|
| **Basic Paltaa** | Simple ascending/descending patterns |
| **Alankar** | Ornamental patterns for technique |
| **Raga-specific** | Paltaas for a particular raga's notes |

### Taal Reference
| Taal | Beats | Common use |
|------|-------|------------|
| Teentaal | 16 | Most common, versatile |
| Ektaal | 12 | Slower, meditative pieces |
| Jhaptaal | 10 | Medium tempo |
| Rupak | 7 | Lighter compositions |
| Dadra | 6 | Folk-influenced, light classical |

---

## Example AI Queries

**About recordings:**
- "Show me all Brindavani Sarang recordings"
- "Which bandishes have we learned?"
- "Find my paltaa exercises for Yaman"

**About the music:**
- "Explain the structure of Brindavani Sarang"
- "What's the difference between alaap and bandish?"
- "What mood is Bhimpalasi associated with?"

**Finding public resources:**
- "Find YouTube videos of Kishori Amonkar singing this raga"
- "What famous artists have recorded Brindavani Sarang?"

**Practice guidance:**
- "What should I practice before the next class?"
- "Which paltaas help with Yaman?"

---

## Technical Notes

### Data source
WhatsApp exports in format: `[TIME, DATE] SENDER: MESSAGE`

### Detection patterns
| Entity | Pattern |
|--------|---------|
| Raga | Raga names near recordings |
| Composition Type | "alaap", "bandish", "taan" |
| Paltaas | "sargam", "paltaa", "alankar" |
| Taal | "teentaal", "ektaal", etc. |
| Event | "concert", "performance" + location + date |
| Class | "class at", "see you", meeting links |

### Technical approach
- **Phase 1:** Rule-based extraction from chat context
- **Phase 2:** LLM for natural language queries + web search for public resources

### Deployment
- **docs/DEPLOYMENT.md** — HTTPS requirement, pre-deploy checklist, PaaS options (Railway, Render, Fly.io, etc.), and reverse-proxy options (Caddy, nginx, Cloudflare Tunnel) for production.
- **DATA_DIR / MEDIA_DIR:** App and tenant_data read `DATA_DIR` and `MEDIA_DIR` from the environment when set (e.g. on Render with a persistent disk at `/data`); otherwise they use `data/` and `media/` under the project root. Enables persistent storage on PaaS.

### Local setup — first teacher
- Tenant data (students, contacts, attendance, music metadata) is keyed by `teacher_id`; existing JSON uses key `"1"`. To have the first teacher own that data and log in with a fixed email/password, run once: `python scripts/seed_first_teacher.py`. This ensures teacher id=1 exists with email `vaishnavikondapalli@yahoo.com` and password `Vaishnavi`. Media for that teacher should live under `media/events/1/` and `media/audio/1/` (see `scripts/migrate_media_to_tenant_dirs.py` if migrating from legacy paths).
