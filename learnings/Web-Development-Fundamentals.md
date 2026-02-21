# Web Development Fundamentals

A growing collection of patterns, best practices, and decision frameworks learned while building the Music Class Organizer app.

---

## Table of Contents

1. [When to Use Each Language (Python vs CSS vs JavaScript)](#when-to-use-each-language)
2. [The Request-Response Flow](#the-request-response-flow)
3. [Real Examples from the Music App](#real-examples-from-the-music-app)
4. [Common Mistakes to Avoid](#common-mistakes-to-avoid)
5. [Decision Checklist](#decision-checklist)

---

## When to Use Each Language

This is the most important thing to learn. Here's how to decide where code belongs:

### Use PYTHON When You Need To:

#### 1. Access the file system or databases

```python
# Reading/writing data files
categories = json.load(open('data/audio_categories.json'))
filepath.write_bytes(audio_data)

# Loading user data, attendance records, etc.
```

**Why Python?** JavaScript in the browser can't access your computer's files for security reasons. Only Python (running on the server) can.

#### 2. Keep secrets secure

```python
# API keys, passwords, sensitive data
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
```

**Why Python?** If you put API keys in JavaScript, anyone can see them by viewing the page source. Python code stays on the server.

#### 3. Process data before sending to browser

```python
# Complex calculations, AI categorization
result = genai.GenerativeModel.generate_content(...)
# Organizing data structures
ragas = sorted(set(v.get("raga") for v in categories.values()))
```

**Why Python?** Heavy processing should happen on the server, not the user's phone/laptop.

#### 4. Decide what HTML to send

```python
# Different content for different users
if role == 'student':
    return student_dashboard_html
elif role == 'teacher':
    return teacher_dashboard_html
```

**Why Python?** The server controls what each user sees based on their role, data, etc.

---

### Use CSS When You Need To:

#### 1. Control visual appearance

```css
/* Colors, sizes, fonts */
.button {
  background: #d4913b;
  padding: 12px 18px;
  border-radius: 10px;
  font-size: 15px;
}
```

**Why CSS?** It's specifically designed for styling. Browser optimizes it. Works offline once cached.

#### 2. Responsive design (mobile vs desktop)

```css
/* Different layouts for different screen sizes */
@media (max-width: 768px) {
  .music-item {
    padding: 8px;  /* Smaller padding on phone */
  }
}
```

**Why CSS?** CSS media queries are the standard way to do responsive design. Works without JavaScript.

#### 3. Animations and transitions

```css
.button:hover {
  transform: scale(1.05);
  transition: all 0.2s;
}
```

**Why CSS?** CSS animations are hardware-accelerated (faster) and work even if JavaScript is disabled.

#### 4. Consistent styling across the app

```css
/* One place to define colors */
:root {
  --primary-color: #d4913b;
  --text-color: #2C1810;
}
```

**Why CSS?** Change one variable, update the entire app. CSS cascades (that's what the C stands for).

---

### Use JAVASCRIPT When You Need To:

#### 1. React to user actions

```javascript
// Click, type, drag, scroll
button.addEventListener('click', function() {
  showModal();
});
```

**Why JavaScript?** Only JS can listen for and respond to user interactions in the browser.

#### 2. Modify the page without reloading

```javascript
// Update content dynamically
document.getElementById('music-list').innerHTML = newHtml;
// Change CSS on the fly
element.classList.add('active');
```

**Why JavaScript?** Creates smooth, app-like experiences without page refreshes.

#### 3. Communicate with the server

```javascript
// Fetch data from Python API
const resp = await fetch('/api/update-file', {
  method: 'POST',
  body: JSON.stringify(data)
});
```

**Why JavaScript?** Sends data to Python backend without leaving the page (AJAX).

#### 4. Client-side validation and logic

```javascript
// Check input before sending to server
if (titleInput.value.trim() === '') {
  showToast('Title cannot be empty');
  return;
}
```

**Why JavaScript?** Instant feedback (no server round-trip needed). Reduces unnecessary API calls.

---

## The Request-Response Flow

Understanding this flow is key to knowing where code belongs:

```
User opens app
  ↓
Browser sends: GET / (request HTML page)
  ↓
Python loads data/audio_categories.json from disk
  ↓
Python builds HTML with that data
  ↓
Python sends back: HTML + links to CSS/JS files
  ↓
Browser parses HTML
  ↓
Browser requests: GET /static/css/main.css
  ↓
Python reads CSS file from disk and sends it
  ↓
Browser requests: GET /static/js/app.js
  ↓
Python reads JS file from disk and sends it
  ↓
Page renders, JavaScript starts running
  ↓
--- User interaction phase ---
  ↓
User clicks "Save" button
  ↓
JavaScript validates the input
  ↓
JavaScript sends: POST /api/update-file (with data)
  ↓
Python writes to audio_categories.json
  ↓
Python sends back: {"ok": true}
  ↓
JavaScript updates the UI, shows success toast
```

**Key insight:**
- Python runs ONCE per page load (generates HTML)
- CSS/JS download ONCE, then stay in browser
- API calls let JavaScript talk to Python when needed

---

## Real Examples from the Music App

Let's look at actual features and why each piece is where it is:

### Example 1: Downloading a Recording

**Problem:** User clicks "Download" button on a music card.

**The flow:**

1. **HTML** (Python-generated): Creates the button
   ```python
   html += '<button onclick="downloadRecording(\\'' + filename + '\\')">'
   ```

2. **CSS** (static file): Styles the button
   ```css
   .item-action-btn {
     border: 1px solid #E0D5C8;
     border-radius: 6px;
     width: 34px;
     height: 34px;
   }
   ```

3. **JavaScript** (static file): Handles the click
   ```javascript
   function downloadRecording(filename) {
     const a = document.createElement('a');
     a.href = '/media/audio/' + filename;
     a.download = filename;
     a.click();
   }
   ```

4. **Python** (server): Serves the audio file
   ```python
   if parsed.path.startswith("/media/audio/"):
       # Read audio file, send to browser
   ```

**Why this division?**
- Python creates the HTML once (knows which files exist)
- CSS makes ALL buttons look consistent (no repeating style code)
- JavaScript adds behavior (only runs when button clicked)
- Python serves the actual file (only server can access disk)

---

### Example 2: Changing Raga Dropdown

**Problem:** User changes a recording's raga from "Bhupali" to "Yaman".

**The flow:**

1. **Python** (initial page): Injects current categories data
   ```python
   page += "let categories = " + json.dumps(categories) + ";\n"
   ```

2. **JavaScript** (static file): Detects change, updates data
   ```javascript
   async function reassignRaga(filename, newRaga) {
     categories[filename].raga = newRaga;  // Update local copy
     await fetch('/api/update-file', {     // Tell server
       method: 'POST',
       body: JSON.stringify({filename, updates: {raga: newRaga}})
     });
   }
   ```

3. **Python** (API endpoint): Saves to disk
   ```python
   elif parsed.path == "/api/update-file":
       categories[filename].update(updates)
       save_audio_categories(categories)  # Write JSON file
   ```

**Why this division?**
- Python knows the current state (loads from JSON)
- JavaScript lets user interact smoothly (no page reload)
- Python persists changes (only server can write files)

---

### Example 3: Responsive Mobile Layout

**Problem:** App should work on phone and desktop.

**Solution:** Pure CSS (no Python or JavaScript needed)

```css
/* Desktop: Two columns */
.action-cards {
  display: flex;
  flex-direction: row;
  gap: 16px;
}

/* Mobile: One column */
@media (max-width: 768px) {
  .action-cards {
    flex-direction: column;
  }
}
```

**Why CSS only?**
- Browser automatically picks which rules to apply
- Works instantly as you resize window
- No server round-trip needed
- No JavaScript checking screen size

---

### Example 4: Teacher vs Student View

**Problem:** Teachers see edit buttons, students don't.

**Solution:** Python decides HTML, CSS hides elements

**Python** (generates different HTML):
```python
if role == 'student':
    document.body.classList.add('student-mode')
```

**CSS** (hides edit controls):
```css
.student-mode .item-edit-toggle {
  display: none;
}
```

**Why this division?**
- Python knows the user's role (from session/login)
- CSS provides clean on/off switch (one class controls everything)
- Could also do this in JavaScript, but CSS is simpler

---

## Common Mistakes to Avoid

### Mistake 1: Putting Styles in JavaScript

**Bad:**
```javascript
button.style.backgroundColor = '#d4913b';
button.style.padding = '12px 18px';
button.style.borderRadius = '10px';
```

**Good:**
```css
/* In CSS file */
.primary-button {
  background: #d4913b;
  padding: 12px 18px;
  border-radius: 10px;
}
```
```javascript
// In JavaScript
button.classList.add('primary-button');
```

**Why?** CSS can style hundreds of buttons with one rule. JavaScript has to style each one individually.

---

### Mistake 2: Doing Complex Math in CSS

**Bad:**
```css
.card {
  width: calc(100% / 3 - 20px);  /* Complex calculation */
}
```

**Better (if the number changes):**
```python
# In Python - calculate once
card_width = (100 / num_columns) - gap_size
html += f'<div class="card" style="width: {card_width}%">'
```

**Why?** If it's truly dynamic (changes per page load), Python should calculate it. CSS is for static styling.

---

### Mistake 3: Loading Data in JavaScript

**Bad:**
```javascript
// Trying to read file in browser
const data = require('./data/categories.json');  // Won't work!
```

**Good:**
```python
# Python loads data, injects into page
categories = load_audio_categories()
page += f"const categories = {json.dumps(categories)};\n"
```

**Why?** Browser JavaScript can't read local files (security). Python loads it, sends it to browser.

---

## Decision Checklist

When adding a new feature, ask yourself:

1. **Does it need to access files or secrets?** → Python
2. **Does it need to be saved permanently?** → Python (save to JSON)
3. **Is it just visual (color, size, layout)?** → CSS
4. **Does it respond to user clicks/typing?** → JavaScript
5. **Does it need to work differently per user?** → Python (generate different HTML)
6. **Does it need to work on mobile?** → CSS (@media queries)
7. **Does it update the page without reloading?** → JavaScript

### Example: "Add a button to delete a recording"

- Button HTML: **Python** (knows which recordings exist)
- Button style: **CSS** (consistent look with other buttons)
- Click handler: **JavaScript** (calls delete API)
- Actual deletion: **Python** (removes file from disk)
- Update UI: **JavaScript** (removes card from page)

All four languages working together!

---

## Summary: The Golden Rules

### Use Python For:
- File system access (read/write data)
- Secrets and API keys
- User authentication and roles
- Database operations
- Heavy processing (AI, image manipulation)
- Generating initial HTML

### Use CSS For:
- All visual styling (colors, fonts, spacing)
- Layout and positioning
- Responsive design (mobile vs desktop)
- Animations and transitions
- Consistent design system

### Use JavaScript For:
- Responding to user actions (clicks, typing)
- Updating page without reload
- Form validation
- Calling Python APIs
- Client-side state management

### Use HTML (via Python) For:
- Page structure
- Initial content
- Dynamic content that varies per user

---

## Notes Section

*Add your own learnings and observations here as you continue building...*
