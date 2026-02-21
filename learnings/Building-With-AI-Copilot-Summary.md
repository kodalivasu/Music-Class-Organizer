# Summary: Main Concepts Learned Building With an AI Copilot

Learned while building the Music Class Organizer app with no prior programming or AI-copilot experience.

---

## 1. Not one big blob of code

- Split the app into **Python (backend)**, **HTML/CSS (layout and style)**, and **JavaScript (behavior)** so each part has a clear job.
- Keep **auth**, **tenant data**, **parsing**, and **HTTP handling** in separate modules instead of one giant file.

## 2. Planning before building

- Write a **plan** (or TDD/requirements) before coding so the agent and you agree on scope.
- Do **phased work** (e.g. "Phase 6: Enforce & document") so changes are small and reviewable.

## 3. Editing with minimum context

- Use **grep** to find exact spots (`parsed.path ==`, route names) instead of reading whole files.
- Make **local, targeted edits** (e.g. one handler at a time) so the agent doesn't need the full codebase in context.
- Keep **prompts scoped** ("add require_session to all /api/* handlers") so the agent does one kind of change per turn.

## 4. Token efficiency

- Prefer **small, precise prompts** and **targeted reads** over "read everything and refactor."
- Do **repetitive edits in batches** with one clear instruction instead of many back-and-forth steps.
- **Document in a separate step** (e.g. "update TDD section 6 and requirements") so doc updates don't bloat the same turn as code.

## 5. Authorization and role-based access

- **Session** = who is logged in (teacher / student / parent), stored in a signed cookie.
- **One helper** (`require_session(api=True/False)`) for "must be logged in" so every route doesn't repeat the same logic.
- **401** for API calls without a session, **302 redirect to login** for page requests.
- **Three auth methods**: teacher password, student PIN, parent magic link—each sets the right role and IDs in the session.

## 6. Building in small functions

- **Backend**: one route or one helper per concern (e.g. `remove_student`, `add_student`, `/api/families/add`).
- **Frontend**: small handlers (e.g. `addStudentFromSettings`, delegated click handlers) that call the API and then reload or update UI.
- **Reuse**: e.g. same "Add / Remove" pattern for students (settings) and contacts (people tab).

## 7. CSS, JS, Python, JSON as separate "layers"

- **Python**: routes, business logic, building HTML strings, reading/writing JSON.
- **JSON**: data shape (people, categories, attendance) and how it's stored per tenant.
- **CSS**: layout, colors, responsiveness; one place to change look (e.g. `.header-logout`, `#global-switch-btn`).
- **JS**: event handlers, fetch, DOM updates; no business logic that belongs in Python.

## 8. Documenting as you go

- **TDD.md** = technical design (security, APIs, data flow).
- **requirements.md** = what's done and what's next; update when you add a feature.
- **AGENTS.md** = how you and the agent work together.
- Keeping docs in sync so the next session (or agent) doesn't rely on stale assumptions.

## 9. UX and "who sees what"

- **Role-based UI**: e.g. Switch and settings only for teacher; Class contacts same tab, different actions by role.
- **One place for admin**: e.g. gear opens only "admin" content (name school, Venmo, students/PINs) so the main dashboard stays simple.

## 10. Working with an AI copilot

- Be **explicit** about scope ("class contacts = parents") to avoid wrong interpretations.
- **Plan → implement → verify** (e.g. "log out and hit GET /api/categories, expect 401") instead of "do everything and hope it works."
- **Ask mode** for questions and design; **Agent mode** when you want edits applied.
