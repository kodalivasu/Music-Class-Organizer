# CSS Location Map – Music Class Organizer

Use this map to find which part of `static/css/main.css` controls which part of the app. **Jump to line** in your editor (Ctrl+G or Cmd+G) to go straight to a section.

---

## Quick reference table

| Section | Start line | Where in app | Who sees it |
|--------|------------|--------------|-------------|
| [Music Items](#music-items) | 5 | Music Library tab – recording cards | Teacher, Student |
| [Editable Controls](#editable-controls) | 218 | Music Library – edit panel (dropdowns, buttons) | Teacher only |
| [Raga Group Header](#raga-group-header-editing) | 311 | Music Library – raga name, collapse arrow | Teacher only |
| [Base Styles](#base-styles) | 383 | Entire app (body, reset) | All |
| [Role Overlay](#role-overlay) | 410 | First screen – “Choose your role” | Before role selected |
| [Header](#header) | 528 | Top bar – “Music Class Organizer” | All |
| [Nav](#nav) | 561 | Bottom tab bar (Home, Music, Events, People) | All |
| [Main](#main) | 622 | Content area, tab panels, h2 titles | All |
| [Teacher Welcome](#teacher-welcome) | 661 | Teacher Home – welcome, date, Switch, Settings | Teacher |
| [Action Cards](#action-cards) | 846 | Teacher Home – Music / Attendance / Events cards | Teacher |
| [Modals](#modals) | 1027 | Pop-ups (Record, Add Event, Mark attendance) | When opened |
| [Recorder](#recorder) | 1100 | Record modal – timer, record button, save form | Teacher |
| [Attendance](#attendance) | 1245 | Mark attendance modal – date, student list | Teacher |
| [History](#history) | 1343 | Attendance modal – past sessions list | Teacher |
| [Scheduled Events](#scheduled-events) | 1390 | Events tab, Upcoming Events card | Teacher, Parent |
| [Recent Recordings](#recent-recordings) | 1445 | Music Library – “Recent Recordings” section | Teacher, Student |
| [Cards](#cards) | 1509 | Collapsible groups (raga groups, etc.) | Music, Events |
| [Gallery](#gallery) | 1568 | Events tab – media grid | Teacher |
| [People](#people) | 1599 | People tab – teacher + students | All |
| [Lightbox](#lightbox) | 1703 | Full-screen image (click gallery image) | When opened |
| [Search](#search) | 1730 | Music Library – search bar, Upload button | Teacher, Student |
| [Toast](#toast) | 1845 | Floating message above nav (“Saved!”, etc.) | All |
| [Student Dashboard](#student-dashboard) | 1895 | Student Home, assignments, practice calendar | Student |
| [Undo FAB](#undo-fab) | 2251 | Floating Undo button (Music Library) | Teacher |
| [Student Mode](#student-mode) | 2287 | Hides edit controls when Student selected | Student view |
| [Parent Dashboard](#parent-dashboard) | 2325 | Parent Home – kids, fees, Venmo, events | Parent |
| [AI Chat Panel](#ai-chat-panel) | 2576 | Chat FAB + chat window | All |
| [Desktop](#desktop) | 2880 | Overrides for screen width ≥ 768px | All (large screens) |

---

## Section details

### Music Items
- **File:** `static/css/main.css` around **line 6**
- **Where:** Music Library tab. Each recording is a card (title, play, download, share, edit).
- **Common edits:** Card background (`.music-item` `background`), title color (`.music-item-friendly` `color`), button colors (`.item-action-btn`).

### Editable Controls
- **File:** around **line 218**
- **Where:** Music Library – when you open the edit panel on a recording (Raga, Type, Taal dropdowns, Paltaa, Delete).
- **Common edits:** Dropdown border/color (`.tag-select`), delete button (`.delete-btn`), paltaa toggle (`.paltaa-btn`).

### Raga Group Header Editing
- **File:** around **line 311**
- **Where:** Music Library – the raga group title you can click to rename, plus badge count and collapse arrow.
- **Common edits:** Raga name input (`.raga-edit-input`), edit icon, badge (`.badge`).

### Base Styles
- **File:** around **line 383**
- **Where:** Whole app (page background, default text color, font).
- **Common edits:** `body` `background`, `body` `color`, `font-family`.

### Role Overlay
- **File:** around **line 410**
- **Where:** First screen – “Choose your role” with Teacher / Student / Parent cards.
- **Common edits:** Background (`.role-overlay`), card style (`.role-card`), title (`.role-title`).

### Header
- **File:** around **line 528**
- **Where:** Top bar with “Music Class Organizer” and subtitle.
- **Common edits:** `header` background, `header h1` font-size/color, accent (`.header h1 span` color).

### Nav
- **File:** around **line 561**
- **Where:** Bottom tab bar (Home, Music, Events, People).
- **Common edits:** `nav` background, `nav button.active` color (active tab), icon size.

### Main
- **File:** around **line 622**
- **Where:** Main content area and tab content.
- **Common edits:** `main` padding, `.tab.active` animation, `h2` size/color.

### Teacher Welcome
- **File:** around **line 661**
- **Where:** Teacher Home – welcome text, date, “Switch role”, Settings, practice tracking cards.
- **Common edits:** `.teacher-welcome`, `.role-switch-btn`, `.settings-btn`, `.practice-tracking-card`.

### Action Cards
- **File:** around **line 846**
- **Where:** Teacher Home – Music, Attendance, Events big cards with buttons.
- **Common edits:** `.action-card` border/background, `.action-btn.primary` (primary button color), card top stripe (`.music-action-card::before` etc.).

### Modals
- **File:** around **line 1027**
- **Where:** Any pop-up from bottom (Record, Add Event, Mark attendance, Share, etc.).
- **Common edits:** `.modal` overlay, `.modal-content` background/radius, `.modal-header`, `.modal-close`.

### Recorder
- **File:** around **line 1100**
- **Where:** Record modal – timer, record/stop button, preview, save form.
- **Common edits:** `#rec-timer` font-size, `.rec-btn` size/color, `.save-btn`, `.modal-input`.

### Attendance
- **File:** around **line 1245**
- **Where:** Mark attendance modal – date picker, list of students with checkboxes.
- **Common edits:** `.att-student`, `.att-check` (checkbox style), `.add-student-btn`.

### History
- **File:** around **line 1343**
- **Where:** Inside attendance modal – list of past sessions (date, count, names).
- **Common edits:** `.history-entry`, `.history-date` color, `.history-names`.

### Scheduled Events
- **File:** around **line 1390**
- **Where:** Events tab and “Upcoming Events” on Teacher Home – event rows with date badge.
- **Common edits:** `.scheduled-event`, `.se-date` (date badge), `.se-name`, `.se-meta`.

### Recent Recordings
- **File:** around **line 1445**
- **Where:** Music Library – “Recent Recordings” collapsible section at top.
- **Common edits:** `.recent-section`, `.recent-item` (same as music items if using same component).

### Cards
- **File:** around **line 1509**
- **Where:** Any collapsible card (raga groups, Recent Recordings, etc.) – header + body.
- **Common edits:** `.card` border/shadow, `.card-header` padding, `.collapse-arrow`.

### Gallery
- **File:** around **line 1568**
- **Where:** Events tab – grid of images/videos for an event.
- **Common edits:** `.gallery` grid gap, `.gallery img` border-radius/size.

### People
- **File:** around **line 1599**
- **Where:** People tab – teacher card, student list, avatars, role badges.
- **Common edits:** `.people-grid`, `.person`, `.teacher-avatar`, `.student-avatar`, `.role-badge`.

### Lightbox
- **File:** around **line 1703**
- **Where:** Full-screen image when you click a gallery image.
- **Common edits:** `#lightbox` background, `#lightbox img` max-size.

### Search
- **File:** around **line 1730**
- **Where:** Music Library – search bar and Upload button.
- **Common edits:** `.search-bar` padding/border, `.upload-audio-btn` color/size, `.share-option-btn`.

### Toast
- **File:** around **line 1845**
- **Where:** Small floating message above the nav (e.g. “Saved!”, “Link copied!”).
- **Common edits:** `.toast` position/background/font-size, `.toast.error` (error color).

### Student Dashboard
- **File:** around **line 1895**
- **Where:** Student Home (name picker, welcome, streak, calendar, assignments, “I practiced!”), Student Music browse.
- **Common edits:** `.picker-card`, `.name-pick-btn`, `.streak-pill`, `.practice-calendar`, `.assignment-card`, `.practice-btn`, `.browse-raga`.

### Undo FAB
- **File:** around **line 2251**
- **Where:** Floating “Undo” button bottom-right in Music Library (teacher only).
- **Common edits:** `#undo-fab` background/position/size.

### Student Mode
- **File:** around **line 2287**
- **Where:** Rules that hide edit controls when role is Student (drag handle, edit icon, dropdowns, undo FAB).
- **Common edits:** Only if you want to show/hide different things in student view.

### Parent Dashboard
- **File:** around **line 2325**
- **Where:** Parent Home – child cards, practice summary, fee card, Venmo button, mark payment, events.
- **Common edits:** `.child-card`, `.child-streak`, `.fee-card`, `.fee-value.highlight`, `.venmo-btn`, `.parent-event`.

### AI Chat Panel
- **File:** around **line 2576**
- **Where:** Orange chat button bottom-right and the chat panel (messages, input, send).
- **Common edits:** `#ai-fab` size/color, `#ai-chat-panel`, `.ai-msg-content`, `.ai-send-btn`, `.ai-suggestion`.

### Desktop
- **File:** around **line 2880**
- **Where:** Overrides when screen width ≥ 768px (nav at top, larger layout, centered modals).
- **Common edits:** Everything inside `@media (min-width: 768px)` – header padding, nav layout, modal position, etc.

---

## How to use this map

1. **Find the UI** you want to change (e.g. “music card background”).
2. **Find the section** in the table (e.g. Music Items → line 6).
3. **Jump to line** in `static/css/main.css` (Ctrl+G / Cmd+G, type the line number).
4. **Edit** the property (e.g. `background`). Use inline comments in the CSS for hints (e.g. `/* Card background */`).
5. **Save and refresh** the app to see the change.

---

## Notes

- Line numbers may shift slightly if you add or remove lines in `main.css`. Use the **section headers** (the `===== SECTION NAME (Lines x-y) =====` blocks) to find the right place.
- In the CSS file, each section has a block comment at the top with **Location**, **Visible**, and **Elements** to match this map.
- Common colors used: `#F5EDE4` cream, `#d4913b` gold, `#2C1810` dark brown, `#E0D5C8` border, `#7A6A5A` muted text.
