# Agent instructions

You are a development partner helping me build the Music Class Organizer app.

## About this project

An app to organize my kids' music class by extracting and structuring data from WhatsApp group chat exports.

**Core features:**
1. Parse WhatsApp chat exports and organize media (audio, video, photos)
2. Categorize music recordings by Raga, Composition Type, Paltaas, Taal (AI + manual editing)
3. Organize event photos/videos by event name and date
4. Mobile-responsive web UI to browse music library, events, and people
5. Track attendance and calculate fees owed (planned)

## Technical context

- I am non-technical but learning to build with AI assistance
- Prefer simple solutions over complex ones
- Start with scripts/prototypes before building full UI
- Python is a good starting language for parsing and data work
- **Auth:** Session in signed cookie; `require_session(api=True|False)` for protected routes. Unauthenticated: 401 for API, 302 to /login for pages. Three methods: teacher password, student PIN, parent magic link.
- **Roles:** teacher, student, parent. UI and API filter by role (e.g. teacher-only actions, parent sees only own data).

## How I like to work

- Explain concepts with examples
- Show me the code, but also explain what it does
- Break tasks into small, testable steps
- Celebrate small wins along the way
- When adding or changing a feature, always update requirements.md and PRD.md to match and include comment on the change or add

## How we build (principles)

- **Plan before coding:** Prefer a short plan or checklist (or reference TDD/requirements) before making edits. One focused phase per session when possible.
- **Minimum context:** Prefer grep/targeted reads to find exact lines; edit only what's needed (one route, one helper, one section of docs). Avoid "read the whole file and refactor."
- **Token efficiency:** Use small, scoped prompts. Batch repetitive edits in one instruction. Handle docs (TDD, requirements) in a separate step when it makes sense.
- **Efficiency:** Prefer targeted edits and grep over full-file reads. Prefer one clear instruction for batch edits (e.g. "add require_session to all /api/* handlers") rather than many small prompts.
- **One concern per unit:** Backend: one route or helper per action (e.g. `/api/students/remove`, `require_session`). Frontend: small handlers that call APIs and refresh. Reuse patterns (e.g. Add/Remove) across similar features.
- **Layers stay separate:** Python = routes + logic + building HTML. JSON = data shape and storage. CSS = layout and style. JS = events and API calls. Don't put business logic in JS or styling in Python.
- **Document as we go:** When adding or changing behavior, update requirements.md and PRD.md (and TDD.md for security/APIs) and note what changed. Keep AGENTS.md updated with how we work.

(Full summary of these learnings: [learnings/Building-With-AI-Copilot-Summary.md](learnings/Building-With-AI-Copilot-Summary.md).)

## Key data

- WhatsApp exports are in `data/whatsapp-export/WhatsApp Chat - Kiddo Music Group`
- Message format: `[TIME, DATE] SENDER: MESSAGE`
- Teacher: Vaishnavi Kondapalli
- Practice recordings shared via Google Drive links

## Current priorities

- [x] Build a parser for the WhatsApp export format
- [x] Extract class dates and attendance signals
- [x] Organize media files (audio, video, photos)
- [x] Categorize recordings by Hindustani taxonomy (raga, alaap/bandish/sargam)
- [x] Organize event photos/videos by event name and date
- [x] Simple web UI with music library, events gallery, people directory
- [x] Editable categorization (drag-drop, rename ragas, edit tags, undo)
- [x] Build web UI with three user roles (Teacher, Student, Parent)
- [x] Auth: teacher password, student PIN, parent magic link; session enforcement (401/302)
- [x] Teacher settings (music class name, Venmo, student PINs, add/remove students)
- [x] Class contacts (parents): add/remove contacts, generate login link, Share via WhatsApp
- [x] Logout; role-based UI (Switch for teacher only, Class contacts tab)
- [x] In-app recording feature for Teacher
- [x] Add AI-powered queries about the music (explain raga, find famous recordings)
