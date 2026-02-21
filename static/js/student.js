let practiceLog = {};  // { studentName: ["2026-02-09", ...] }
let currentStudent = null;

function initStudentDashboard() {
    const saved = localStorage.getItem('musicClassStudent');
    if (saved && studentNames.includes(saved)) {
        currentStudent = saved;
        document.getElementById('student-picker').style.display = 'none';
        document.getElementById('student-home').style.display = '';
        loadStudentData();
    } else {
        renderStudentPicker();
    }
}

function renderStudentPicker() {
    const container = document.getElementById('student-name-buttons');
    let html = '';
    for (const name of studentNames) {
        html += '<button class="name-pick-btn" onclick="pickStudent(\'' + esc(name).replace(/'/g, "\\'") + '\')">' + esc(name) + '</button>';
    }
    container.innerHTML = html;
}

function pickStudent(name) {
    currentStudent = name;
    localStorage.setItem('musicClassStudent', name);
    document.getElementById('student-picker').style.display = 'none';
    document.getElementById('student-home').style.display = '';
    loadStudentData();
}

async function loadStudentData() {
    document.getElementById('student-display-name').textContent = currentStudent.split(' ')[0];
    const today = new Date();
    document.getElementById('student-date-display').textContent = today.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' });

    // Load practice log
    try {
        const r = await fetch('/api/practice-log');
        practiceLog = await r.json();
    } catch(e) { practiceLog = {}; }

    renderStreak();
    renderPracticeCalendar();
    renderStudentAssignments();
    renderStudentBrowse();
}

// --- Streak ---
function getStudentDates() {
    const entries = practiceLog[currentStudent] || [];
    // Handle both old format (string[]) and new format (object[])
    return entries.map(e => typeof e === 'string' ? e : e.date).sort();
}

function hasLoggedToday() {
    return getStudentDates().includes(formatDate(new Date()));
}

function calcStreak() {
    const dates = getStudentDates();
    if (dates.length === 0) return 0;
    const today = new Date();
    today.setHours(0,0,0,0);
    let streak = 0;
    // Start from today or yesterday
    let check = new Date(today);
    // If practiced today, start counting from today
    const todayStr = formatDate(today);
    if (!dates.includes(todayStr)) {
        // Check if practiced yesterday — if not, streak is 0
        check.setDate(check.getDate() - 1);
        if (!dates.includes(formatDate(check))) return 0;
    }
    // Count consecutive days backwards
    check = new Date(today);
    if (!dates.includes(todayStr)) check.setDate(check.getDate() - 1);
    while (dates.includes(formatDate(check))) {
        streak++;
        check.setDate(check.getDate() - 1);
    }
    return streak;
}

function formatDate(d) {
    return d.getFullYear() + '-' + String(d.getMonth()+1).padStart(2,'0') + '-' + String(d.getDate()).padStart(2,'0');
}

function renderStreak() {
    const streak = calcStreak();
    document.getElementById('streak-count').textContent = streak;
    const pill = document.getElementById('streak-pill');
    if (streak >= 7) pill.style.background = 'linear-gradient(135deg, #3a2010, #5a3010)';
    else if (streak >= 3) pill.style.background = 'linear-gradient(135deg, #3a2010, #4a3010)';
}

// --- Practice Calendar (14 days) ---
function renderPracticeCalendar() {
    const container = document.getElementById('practice-calendar');
    const dates = getStudentDates();
    const today = new Date();
    today.setHours(0,0,0,0);
    const todayStr = formatDate(today);
    const dayNames = ['S','M','T','W','T','F','S'];

    let html = '';
    for (let i = 13; i >= 0; i--) {
        const d = new Date(today);
        d.setDate(d.getDate() - i);
        const ds = formatDate(d);
        const isToday = ds === todayStr;
        const practiced = dates.includes(ds);
        // For future: only mark as missed if it's a past day and there were active assignments
        let cls = 'empty';
        if (practiced) cls = 'practiced';
        else if (!isToday && i > 0) cls = 'missed';

        html += '<div class="cal-day">';
        html += '<span class="cal-label">' + dayNames[d.getDay()] + '</span>';
        html += '<div class="cal-dot ' + cls + (isToday ? ' today' : '') + '">' + d.getDate() + '</div>';
        html += '</div>';
    }
    container.innerHTML = html;
}

// --- Today's Assignments ---
async function renderStudentAssignments() {
    const container = document.getElementById('student-assignments');
    let assignments = [];
    try {
        const r = await fetch('/api/assignments');
        assignments = await r.json();
    } catch(e) {}

    // Filter active assignments for this student
    const mine = assignments.filter(a => {
        if (a.status !== 'active') return false;
        if (a.assigned_to.includes(currentStudent)) return true;
        if (a.assigned_to.includes('All')) return true;
        return false;
    });

    if (mine.length === 0) {
        container.innerHTML = '<div class="assignment-card"><p style="color:#5a5a7a; text-align:center; padding:20px;">No assignments right now. Enjoy your break!</p></div>';
        return;
    }

    const todayStr = formatDate(new Date());
    const practiced = getStudentDates().includes(todayStr);

    let html = '';
    for (const a of mine) {
        const info = categories[a.audio_file] || {};
        const raga = (info.raga && info.raga !== 'Unknown') ? info.raga : 'Uncategorized';
        const comp = info.composition_type || '';
        const taal = info.taal || '';
        const friendly = typeof friendlyName === 'function' ? friendlyName(a.audio_file) : a.audio_file;

        html += '<div class="assignment-card">';
        html += '<div class="assignment-header">';
        html += '<div><div class="assignment-raga">' + esc(raga) + '</div>';
        html += '<div class="assignment-meta">' + esc(comp) + (taal && taal !== 'Unknown' ? ' · ' + esc(taal) : '') + '</div></div>';
        if (a.due_date) html += '<span class="badge" style="font-size:10px;">Due ' + esc(a.due_date) + '</span>';
        html += '</div>';
        if (a.notes) html += '<div class="assignment-notes">' + esc(a.notes) + '</div>';
        html += '<div class="assignment-meta" style="margin-bottom:8px;">' + esc(friendly) + '</div>';
        html += '<audio controls preload="none" style="width:100%; height:40px; margin-bottom:10px;"><source src="' + (typeof mediaAudioBase !== 'undefined' ? mediaAudioBase : '/media/audio/') + encodeURIComponent(a.audio_file) + '"></audio>';

        if (practiced) {
            html += '<div class="practice-done-row">';
            html += '<span class="practice-done-label">&#10003; Practiced today</span>';
            html += '<button class="practice-undo-btn" onclick="unmarkPractice(this)">Undo</button>';
            html += '</div>';
        } else {
            html += '<div class="practice-form">';
            html += '<div style="display:flex; gap:8px; margin-bottom:8px;">';
            html += '<div style="flex:1;"><label class="modal-label" style="font-size:10px;">Minutes</label>';
            html += '<input type="number" class="modal-input pf-duration" placeholder="30" min="1" style="padding:8px; font-size:13px;"></div>';
            html += '<div style="flex:2;"><label class="modal-label" style="font-size:10px;">What did you practice?</label>';
            html += '<input type="text" class="modal-input pf-items" placeholder="e.g. Bhupali Bandish" style="padding:8px; font-size:13px;"></div>';
            html += '</div>';
            html += '<button class="practice-btn not-done" onclick="markPractice(this)">';
            html += '<svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor"><path d="M12 3v10.55c-.59-.34-1.27-.55-2-.55C7.79 13 6 14.79 6 17s1.79 4 4 4 4-1.79 4-4V7h4V3h-6z"/></svg>';
            html += 'I practiced today!</button>';
            html += '</div>';
        }
        html += '</div>';
    }
    container.innerHTML = html;
}

async function markPractice(btn) {
    const todayStr = formatDate(new Date());
    const card = btn.closest('.assignment-card') || btn.closest('.practice-form');
    const durInput = card ? card.querySelector('.pf-duration') : null;
    const itemsInput = card ? card.querySelector('.pf-items') : null;
    const duration = durInput ? parseInt(durInput.value) || 0 : 0;
    const items = itemsInput ? itemsInput.value.trim() : '';

    btn.disabled = true;
    btn.textContent = 'Saving...';
    try {
        await fetch('/api/practice-log/mark', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ student: currentStudent, date: todayStr, duration: duration, items: items })
        });
        if (!practiceLog[currentStudent]) practiceLog[currentStudent] = [];
        const existingDates = practiceLog[currentStudent].map(e => typeof e === 'string' ? e : e.date);
        if (!existingDates.includes(todayStr)) {
            practiceLog[currentStudent].push({date: todayStr, duration: duration, items: items});
        }
        renderStreak();
        renderPracticeCalendar();
        renderStudentAssignments();
        showToast('Great job practicing today!', false, false);
    } catch(e) {
        showToast('Error saving practice', true, false);
        btn.disabled = false;
    }
}

async function unmarkPractice(btn) {
    const todayStr = formatDate(new Date());
    try {
        await fetch('/api/practice-log/unmark', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ student: currentStudent, date: todayStr })
        });
        if (practiceLog[currentStudent]) {
            practiceLog[currentStudent] = practiceLog[currentStudent].filter(d => d !== todayStr);
        }
        renderStreak();
        renderPracticeCalendar();
        renderStudentAssignments();
    } catch(e) {}
}

// --- Student Browse (read-only raga groups) ---
function renderStudentBrowse() {
    const container = document.getElementById('student-music-browse');
    const byRaga = {};
    for (const [fn, info] of Object.entries(categories)) {
        const raga = (info.raga && info.raga !== 'Unknown') ? info.raga : 'Uncategorized';
        if (!byRaga[raga]) byRaga[raga] = [];
        byRaga[raga].push({ filename: fn, info: info });
    }

    let html = '';
    const ragas = Object.keys(byRaga).sort();
    for (const raga of ragas) {
        const items = byRaga[raga];
        html += '<div class="browse-raga">';
        html += '<div class="browse-raga-header" onclick="this.nextElementSibling.classList.toggle(\'collapsed\')">';
        html += '<h4>' + esc(raga) + '</h4>';
        html += '<span class="badge">' + items.length + '</span>';
        html += '</div>';
        html += '<div class="browse-raga-body collapsed">';
        for (const item of items) {
            const i = item.info;
            html += '<div class="browse-item">';
            html += '<div class="browse-item-name">' + esc(typeof friendlyName === 'function' ? friendlyName(item.filename) : item.filename) + '</div>';
            html += '<div class="browse-item-tags">';
            if (i.composition_type && i.composition_type !== 'Unknown') html += '<span class="browse-tag type">' + esc(i.composition_type) + '</span>';
            if (i.taal && i.taal !== 'Unknown') html += '<span class="browse-tag taal">' + esc(i.taal) + '</span>';
            if (i.paltaas) html += '<span class="browse-tag paltaa">Paltaa</span>';
            html += '</div>';
            html += '<audio controls preload="none"><source src="' + (typeof mediaAudioBase !== 'undefined' ? mediaAudioBase : '/media/audio/') + encodeURIComponent(item.filename) + '"></audio>';
            html += '</div>';
        }
        html += '</div></div>';
    }
    container.innerHTML = html || '<p class="empty-state">No recordings yet.</p>';
}