// ============================================================
// AUDIO RECORDER
// ============================================================
let mediaRecorder = null;
let audioChunks = [];
let recordingStartTime = null;
let recordingTimer = null;

function openRecorder() {
    document.getElementById('recorder-modal').classList.add('active');
    document.getElementById('rec-status').textContent = 'Ready to record';
    document.getElementById('rec-timer').textContent = '0:00';
    document.getElementById('rec-start').style.display = '';
    document.getElementById('rec-stop').style.display = 'none';
    document.getElementById('rec-preview').style.display = 'none';
    document.getElementById('rec-save-section').style.display = 'none';
}

function closeModal(id) {
    document.getElementById(id).classList.remove('active');
    if (id === 'recorder-modal' && mediaRecorder && mediaRecorder.state === 'recording') {
        mediaRecorder.stop();
        mediaRecorder.stream.getTracks().forEach(t => t.stop());
    }
    if (recordingTimer) { clearInterval(recordingTimer); recordingTimer = null; }
}

async function startRecording() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        audioChunks = [];
        // Try webm first, fall back to mp4
        const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus') ? 'audio/webm;codecs=opus'
            : MediaRecorder.isTypeSupported('audio/mp4') ? 'audio/mp4' : '';
        mediaRecorder = mimeType ? new MediaRecorder(stream, { mimeType }) : new MediaRecorder(stream);
        mediaRecorder.ondataavailable = (e) => { if (e.data.size > 0) audioChunks.push(e.data); };
        mediaRecorder.onstop = () => {
            const blob = new Blob(audioChunks, { type: mediaRecorder.mimeType });
            const url = URL.createObjectURL(blob);
            const preview = document.getElementById('rec-preview');
            preview.src = url;
            preview.style.display = 'block';
            document.getElementById('rec-save-section').style.display = 'flex';
            document.getElementById('rec-status').textContent = 'Recording complete — preview below';
            // Store blob for saving
            window._recordedBlob = blob;
        };
        mediaRecorder.start(1000); // collect data every second
        recordingStartTime = Date.now();
        document.getElementById('rec-status').textContent = 'Recording...';
        document.getElementById('rec-start').style.display = 'none';
        document.getElementById('rec-stop').style.display = '';
        // Timer
        recordingTimer = setInterval(() => {
            const elapsed = Math.floor((Date.now() - recordingStartTime) / 1000);
            const mins = Math.floor(elapsed / 60);
            const secs = elapsed % 60;
            document.getElementById('rec-timer').textContent = mins + ':' + String(secs).padStart(2, '0');
        }, 200);
    } catch (err) {
        document.getElementById('rec-status').textContent = 'Microphone access denied. Please allow mic access and try again.';
    }
}

function stopRecording() {
    if (mediaRecorder && mediaRecorder.state === 'recording') {
        mediaRecorder.stop();
        mediaRecorder.stream.getTracks().forEach(t => t.stop());
    }
    if (recordingTimer) { clearInterval(recordingTimer); recordingTimer = null; }
    document.getElementById('rec-start').style.display = '';
    document.getElementById('rec-stop').style.display = 'none';
}

async function saveRecording() {
    const blob = window._recordedBlob;
    if (!blob) return;
    const nameInput = document.getElementById('rec-name');
    const name = nameInput.value.trim() || 'Recording';
    const saveBtn = document.getElementById('rec-save-btn');
    saveBtn.disabled = true;
    saveBtn.textContent = 'Saving...';

    try {
        const reader = new FileReader();
        reader.onloadend = async function() {
            const base64 = reader.result.split(',')[1];
            const ext = blob.type.includes('webm') ? '.webm' : blob.type.includes('mp4') ? '.m4a' : '.webm';
            const resp = await fetch('/api/upload-recording', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ name: name, audio_data: base64, extension: ext })
            });
            const result = await resp.json();
            if (result.ok) {
                showToast('Saved: ' + result.filename, false, false);
                closeModal('recorder-modal');
                // Add to audio files list
                if (!allAudioFiles.includes(result.filename)) allAudioFiles.push(result.filename);
                allAudioFiles.sort();
                renderMusicLibrary();
            } else {
                showToast('Error saving recording', true, false);
            }
            saveBtn.disabled = false;
            saveBtn.textContent = 'Save Recording';
        };
        reader.readAsDataURL(blob);
    } catch (e) {
        showToast('Error: ' + e.message, true, false);
        saveBtn.disabled = false;
        saveBtn.textContent = 'Save Recording';
    }
}

// ============================================================
// ATTENDANCE
// ============================================================
let attendanceData = {};

function openAttendance() {
    const modal = document.getElementById('attendance-modal');
    modal.classList.add('active');
    const dateInput = document.getElementById('att-date');
    dateInput.value = new Date().toISOString().split('T')[0];
    loadAttendanceForDate(dateInput.value);
}

function loadAttendanceForDate(dateStr) {
    fetch('/api/attendance')
    .then(r => r.json())
    .then(data => {
        attendanceData = data;
        renderAttendanceList(dateStr);
    });
}

function renderAttendanceList(dateStr) {
    const container = document.getElementById('att-student-list');
    const existing = attendanceData[dateStr] || {};
    const presentList = existing.students || [];
    const notes = existing.notes || '';
    document.getElementById('att-notes').value = notes;

    let html = '';
    for (const name of studentNames) {
        const checked = presentList.includes(name) ? 'checked' : '';
        const safeName = esc(name);
        html += '<label class="att-student"><input type="checkbox" value="' + safeName + '" ' + checked + '><span class="att-check"></span><span>' + safeName + '</span></label>';
    }
    container.innerHTML = html;
}

function onAttDateChange() {
    const dateStr = document.getElementById('att-date').value;
    renderAttendanceList(dateStr);
}

async function saveAttendance() {
    const dateStr = document.getElementById('att-date').value;
    const checkboxes = document.querySelectorAll('#att-student-list input[type=checkbox]');
    const present = [];
    checkboxes.forEach(cb => { if (cb.checked) present.push(cb.value); });
    const notes = document.getElementById('att-notes').value.trim();

    const resp = await fetch('/api/attendance/save', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ date: dateStr, students: present, notes: notes })
    });
    const result = await resp.json();
    if (result.ok) {
        showToast('Attendance saved for ' + dateStr + ' (' + present.length + ' present)', false, false);
        closeModal('attendance-modal');
    } else {
        showToast('Error saving attendance', true, false);
    }
}

function selectAllStudents() {
    document.querySelectorAll('#att-student-list input[type=checkbox]').forEach(cb => cb.checked = true);
}
function deselectAllStudents() {
    document.querySelectorAll('#att-student-list input[type=checkbox]').forEach(cb => cb.checked = false);
}

// --- Add Student ---
function showAddStudent() {
    const row = document.getElementById('add-student-row');
    row.style.display = row.style.display === 'none' ? 'block' : 'none';
    if (row.style.display !== 'none') document.getElementById('new-student-name').focus();
}

async function addNewStudent() {
    const input = document.getElementById('new-student-name');
    const name = input.value.trim();
    if (!name) return;
    const resp = await fetch('/api/students/add', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ name: name })
    });
    const result = await resp.json();
    if (result.ok) {
        if (!studentNames.includes(name)) studentNames.push(name);
        studentNames.sort();
        input.value = '';
        document.getElementById('add-student-row').style.display = 'none';
        const dateStr = document.getElementById('att-date').value;
        renderAttendanceList(dateStr);
        showToast('Added student: ' + name, false, false);
    } else {
        showToast('Error adding student', true, false);
    }
}

async function addStudentFromSettings() {
    const input = document.getElementById('settings-add-student-name');
    const name = (input && input.value) ? input.value.trim() : '';
    if (!name) { showToast('Enter a student name', true, false); return; }
    try {
        const r = await fetch('/api/students/add', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ name: name }) });
        const data = await r.json();
        if (data.ok) { if (input) input.value = ''; location.reload(); } else { showToast(data.error || 'Error', true, false); }
    } catch (e) { showToast('Error adding student', true, false); }
}

async function setStudentPin(btn) {
    const row = btn.closest('.student-pin-row');
    if (!row) return;
    const studentId = row.dataset.studentName;
    const input = row.querySelector('.pin-input');
    const pin = (input && input.value) ? input.value.trim() : '';
    if (!pin) {
        showToast('Enter a PIN', true, false);
        return;
    }
    const resp = await fetch('/api/student/set-pin', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ student_id: studentId, pin: pin })
    });
    const result = await resp.json();
    if (result.ok) {
        showToast('PIN set for ' + studentId, false, false);
        if (input) input.value = '';
    } else {
        showToast(result.error || 'Failed to set PIN', true, false);
    }
}

// --- Attendance History ---
function openAttendanceHistory() {
    const modal = document.getElementById('history-modal');
    modal.classList.add('active');
    fetch('/api/attendance')
    .then(r => r.json())
    .then(data => {
        const dates = Object.keys(data).sort().reverse();
        let html = '';
        if (dates.length === 0) {
            html = '<p class="empty-state">No attendance records yet.</p>';
        }
        for (const d of dates) {
            const entry = data[d];
            const students = entry.students || [];
            const notes = entry.notes || '';
            html += '<div class="history-entry">';
            html += '<div class="history-date">' + d + '</div>';
            html += '<div class="history-count">' + students.length + ' / ' + studentNames.length + ' present</div>';
            if (students.length > 0) {
                html += '<div class="history-names">' + students.join(', ') + '</div>';
            }
            if (notes) html += '<div class="history-notes">' + esc(notes) + '</div>';
            html += '</div>';
        }
        document.getElementById('history-list').innerHTML = html;
    });
}

// ============================================================
// ASSIGN PRACTICE
// ============================================================
/** Sort filenames by date descending (YYYY-MM-DD prefix); no date = end. */
function sortAudioFilesByDateDesc(files) {
    const parseDate = (fn) => {
        const m = (fn || '').match(/^(\d{4}-\d{2}-\d{2})/);
        return m ? m[1] : '';
    };
    return [...files].sort((a, b) => {
        const da = parseDate(a), db = parseDate(b);
        if (!da && !db) return (a < b ? -1 : a > b ? 1 : 0);
        if (!da) return 1;
        if (!db) return -1;
        return db.localeCompare(da);
    });
}

function openAssignModal(assignment) {
    const modal = document.getElementById('assign-modal');
    modal.classList.add('active');
    const editing = assignment && assignment.id;
    window.editingAssignmentId = editing ? assignment.id : null;
    const modalTitle = document.querySelector('#assign-modal .modal-header h3');
    modalTitle.textContent = editing ? 'Edit assignment' : 'Assign Practice';
    const saveBtn = document.querySelector('#assign-modal .save-btn');
    saveBtn.textContent = editing ? 'Save changes' : 'Assign Practice';
    // Populate recording dropdown (newest first)
    const select = document.getElementById('assign-recording');
    const sortedFiles = sortAudioFilesByDateDesc(allAudioFiles);
    let html = '<option value="">Select a recording...</option>';
    for (const fn of sortedFiles) {
        const info = categories[fn];
        const raga = info ? info.raga : 'Uncategorized';
        html += '<option value="' + esc(fn) + '">' + esc(friendlyName(fn)) + ' (' + esc(raga) + ')</option>';
    }
    select.innerHTML = html;
    // Populate student checkboxes
    const stuList = document.getElementById('assign-students');
    html = '<label class="att-student"><input type="checkbox" value="All" onchange="toggleAssignAll(this)"><span class="att-check"></span><span><strong>All Students</strong></span></label>';
    for (const name of studentNames) {
        html += '<label class="att-student"><input type="checkbox" value="' + esc(name) + '"><span class="att-check"></span><span>' + esc(name) + '</span></label>';
    }
    stuList.innerHTML = html;
    // Pre-fill when editing
    if (editing) {
        document.getElementById('assign-recording').value = assignment.audio_file || '';
        document.getElementById('assign-due').value = assignment.due_date || '';
        document.getElementById('assign-notes').value = assignment.notes || '';
        const to = assignment.assigned_to || [];
        const allChecked = to.length === studentNames.length || (to.length === 1 && to[0] === 'All');
        document.querySelectorAll('#assign-students input[type=checkbox]').forEach(cb => {
            if (cb.value === 'All') cb.checked = allChecked;
            else cb.checked = allChecked || to.includes(cb.value);
        });
    } else {
        document.getElementById('assign-due').value = '';
        document.getElementById('assign-notes').value = '';
    }
}

function toggleAssignAll(cb) {
    const checked = cb.checked;
    document.querySelectorAll('#assign-students input[type=checkbox]').forEach(c => c.checked = checked);
}

async function saveAssignment() {
    const recording = document.getElementById('assign-recording').value;
    if (!recording) { showToast('Please select a recording', true, false); return; }
    const checkboxes = document.querySelectorAll('#assign-students input[type=checkbox]');
    const assignedTo = [];
    checkboxes.forEach(cb => { if (cb.checked && cb.value !== 'All') assignedTo.push(cb.value); });
    if (assignedTo.length === 0) { showToast('Please select at least one student', true, false); return; }
    const notes = document.getElementById('assign-notes').value.trim();
    const dueDate = document.getElementById('assign-due').value;
    const editingId = window.editingAssignmentId;

    const url = editingId ? '/api/assignments/update' : '/api/assignments/create';
    const body = editingId
        ? { id: editingId, audio_file: recording, assigned_to: assignedTo, notes: notes, due_date: dueDate }
        : { audio_file: recording, assigned_to: assignedTo, notes: notes, due_date: dueDate };
    const resp = await fetch(url, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(body)
    });
    const result = await resp.json();
    if (result.ok) {
        showToast(editingId ? 'Assignment updated' : 'Practice assigned to ' + assignedTo.length + ' student(s)', false, false);
        closeModal('assign-modal');
        window.editingAssignmentId = null;
        if (typeof renderAssignmentsList === 'function') {
            const listModal = document.getElementById('assignments-list-modal');
            if (listModal && listModal.classList.contains('active')) refreshAssignmentsListModal();
        }
        updateTeacherAssignmentCount();
    } else {
        showToast(result.error || 'Error saving assignment', true, false);
    }
}

async function updateTeacherAssignmentCount() {
    const el = document.getElementById('teacher-active-assignments-count');
    if (!el) return;
    try {
        const r = await fetch('/api/assignments');
        const assignments = await r.json();
        const n = (assignments || []).filter(a => a.status === 'active').length;
        el.textContent = n + ' assigned';
    } catch (e) {}
}

async function openAssignmentsListModal() {
    const modal = document.getElementById('assignments-list-modal');
    modal.classList.add('active');
    await refreshAssignmentsListModal();
}

async function refreshAssignmentsListModal() {
    const container = document.getElementById('assignments-list');
    if (!container) return;
    container.innerHTML = '<p class="empty-state">Loading...</p>';
    try {
        const r = await fetch('/api/assignments');
        const assignments = await r.json();
        renderAssignmentsList(assignments || [], container);
    } catch (e) {
        container.innerHTML = '<p class="empty-state">Error loading assignments.</p>';
    }
}

function renderAssignmentsList(assignments, container) {
    const active = assignments.filter(a => a.status === 'active');
    if (active.length === 0) {
        container.innerHTML = '<p class="empty-state">No active assignments. Use Assign Practice to add one.</p>';
        return;
    }
    let html = '';
    for (const a of active) {
        const info = categories[a.audio_file] || {};
        const raga = (info.raga && info.raga !== 'Unknown') ? info.raga : 'Uncategorized';
        const friendly = typeof friendlyName === 'function' ? friendlyName(a.audio_file) : a.audio_file;
        const to = a.assigned_to || [];
        const assignLabel = (to.length === 1 && to[0] === 'All') || to.length >= (studentNames || []).length ? 'All' : to.length + ' students';
        html += '<div class="assignment-list-row" data-id="' + esc(a.id) + '">';
        html += '<div class="assignment-list-info">';
        html += '<span class="assignment-list-raga">' + esc(raga) + '</span>';
        html += '<span class="assignment-list-meta">' + esc(friendly) + (a.due_date ? ' · Due ' + esc(a.due_date) : '') + '</span>';
        if (a.notes) html += '<span class="assignment-list-notes">' + esc(a.notes) + '</span>';
        html += '<span class="assignment-list-to">Assigned to: ' + esc(assignLabel) + '</span>';
        html += '</div>';
        html += '<div class="assignment-list-actions">';
        html += '<button type="button" class="btn-link" onclick="editAssignment(\'' + esc(a.id) + '\')">Edit</button>';
        html += '<button type="button" class="btn-link danger" onclick="removeAssignment(\'' + esc(a.id) + '\')">Remove</button>';
        html += '</div></div>';
    }
    container.innerHTML = html;
}

function editAssignment(id) {
    fetch('/api/assignments').then(r => r.json()).then(assignments => {
        const assignment = (assignments || []).find(a => a.id === id);
        if (assignment) {
            closeModal('assignments-list-modal');
            openAssignModal(assignment);
        }
    }).catch(() => {});
}

async function removeAssignment(id) {
    if (!confirm('Remove this assignment? Students will no longer see it.')) return;
    try {
        const resp = await fetch('/api/assignments/remove', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ id: id })
        });
        const result = await resp.json();
        if (result.ok) {
            showToast('Assignment removed', false, false);
            await refreshAssignmentsListModal();
            updateTeacherAssignmentCount();
        } else {
            showToast(result.error || 'Error removing assignment', true, false);
        }
    } catch (e) {
        showToast('Error removing assignment', true, false);
    }
}

// ============================================================
// CREATE EVENT
// ============================================================
function openCreateEvent() {
    const modal = document.getElementById('event-modal');
    modal.classList.add('active');
    document.getElementById('event-name').value = '';
    document.getElementById('event-date').value = '';
    document.getElementById('event-time').value = '';
    document.getElementById('event-location').value = '';
    document.getElementById('event-description').value = '';
}

async function saveEvent() {
    const name = document.getElementById('event-name').value.trim();
    if (!name) { showToast('Please enter an event name', true, false); return; }
    const eventDate = document.getElementById('event-date').value;
    if (!eventDate) { showToast('Please pick a date', true, false); return; }
    const time = document.getElementById('event-time').value;
    const location = document.getElementById('event-location').value.trim();
    const description = document.getElementById('event-description').value.trim();

    const resp = await fetch('/api/events/create', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ name, date: eventDate, time, location, description })
    });
    const result = await resp.json();
    if (result.ok) {
        showToast('Event created: ' + name, false, false);
        closeModal('event-modal');
    } else {
        showToast('Error creating event', true, false);
    }
}

// ============================================================
// UPLOAD PHOTOS
// ============================================================
function openUploadPhotos() {
    document.getElementById('photo-upload-input').click();
}

async function handlePhotoUpload(input) {
    const files = input.files;
    if (!files || files.length === 0) return;
    showToast('Uploading ' + files.length + ' file(s)...', false, false);

    for (const file of files) {
        const reader = new FileReader();
        reader.onloadend = async function() {
            const base64 = reader.result.split(',')[1];
            await fetch('/api/upload-photo', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ name: file.name, data: base64, mime_type: file.type })
            });
        };
        reader.readAsDataURL(file);
    }
    showToast('Upload complete!', false, false);
    input.value = '';
}

// ============================================================
// TEACHER SETTINGS
// ============================================================
function toggleTeacherSettings() {
    const panel = document.getElementById('teacher-settings-panel');
    const main = document.getElementById('teacher-dash-main');
    const isHidden = panel.style.display === 'none';
    panel.style.display = isHidden ? '' : 'none';
    if (main) main.style.display = isHidden ? 'none' : '';
    if (isHidden) {
        setTimeout(function() {
            const input = document.getElementById('venmo-input');
            if (input) { input.focus(); input.setSelectionRange(input.value.length, input.value.length); }
        }, 100);
    }
}

async function saveTeacherSettings() {
    const venmoInput = document.getElementById('venmo-input');
    const schoolInput = document.getElementById('school-name-input');
    const venmo = venmoInput ? venmoInput.value.trim() : '';
    const schoolName = schoolInput ? schoolInput.value.trim() : '';
    if (!venmo) { showToast('Please enter a Venmo handle', true, false); return; }
    try {
        const resp = await fetch('/api/teacher/update-venmo', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ venmo: venmo, school_name: schoolName || undefined })
        });
        const result = await resp.json();
        if (result.ok) {
            if (typeof teacherVenmo !== 'undefined') teacherVenmo = venmo;
            if (schoolName) window.schoolName = schoolName;
            const headerEl = document.getElementById('header-school-name');
            if (headerEl) headerEl.textContent = schoolName || headerEl.textContent || 'Hindustani Classical Music \u2014 Music Class Organizer';
            showToast('Settings saved!', false, false);
            toggleTeacherSettings();
        } else {
            showToast('Error saving', true, false);
        }
    } catch(e) {
        showToast('Error saving settings', true, false);
    }
}

// TEACHER PRACTICE TRACKING
// ============================================================
async function renderTeacherPracticeTracking() {
    const container = document.getElementById('teacher-practice-tracking');
    if (!container) return;

    let log = {};
    try {
        const r = await fetch('/api/practice-log');
        log = await r.json();
    } catch(e) {}

    const studentNames = Object.keys(log).sort();
    if (studentNames.length === 0) {
        container.innerHTML = '<div class="empty-state">No practice data yet. Students will log their practice here.</div>';
        return;
    }

    let html = '';
    for (const name of studentNames) {
        const entries = log[name] || [];
        // Normalize to new format
        const normalized = entries.map(e => typeof e === 'string' ? {date:e, duration:0, items:''} : e);
        const sorted = normalized.sort((a,b) => b.date.localeCompare(a.date));
        const totalDays = sorted.length;
        const totalMinutes = sorted.reduce((sum, e) => sum + (e.duration || 0), 0);

        // Compute current streak
        let streak = 0;
        const today = new Date(); today.setHours(0,0,0,0);
        let check = new Date(today);
        const dates = sorted.map(e => e.date);
        const todayStr = check.getFullYear() + '-' + String(check.getMonth()+1).padStart(2,'0') + '-' + String(check.getDate()).padStart(2,'0');
        if (!dates.includes(todayStr)) {
            check.setDate(check.getDate() - 1);
        }
        while (true) {
            const ds = check.getFullYear() + '-' + String(check.getMonth()+1).padStart(2,'0') + '-' + String(check.getDate()).padStart(2,'0');
            if (dates.includes(ds)) { streak++; check.setDate(check.getDate()-1); }
            else break;
        }

        html += '<div class="practice-tracking-card">';
        html += '<div class="pt-header">';
        html += '<div class="pt-name">' + esc(name) + '</div>';
        html += '<div class="pt-stats">';
        html += '<span class="pt-stat">' + streak + ' day streak</span>';
        html += '<span class="pt-stat">' + totalDays + ' total days</span>';
        html += '<span class="pt-stat">' + totalMinutes + ' min total</span>';
        html += '</div></div>';

        // Show last 7 entries
        const recent = sorted.slice(0, 7);
        if (recent.length > 0) {
            html += '<div class="pt-entries">';
            for (const e of recent) {
                html += '<div class="pt-entry">';
                html += '<span class="pt-date">' + esc(e.date) + '</span>';
                if (e.duration) html += '<span class="pt-dur">' + e.duration + ' min</span>';
                if (e.items) html += '<span class="pt-items">' + esc(e.items) + '</span>';
                html += '</div>';
            }
            if (sorted.length > 7) {
                html += '<div class="pt-more">+ ' + (sorted.length - 7) + ' more entries</div>';
            }
            html += '</div>';
        }
        html += '</div>';
    }
    container.innerHTML = html;
}

// ROLE MANAGEMENT
// ============================================================
function selectRole(role) {
    localStorage.setItem('musicClassRole', role);
    document.getElementById('role-overlay').style.display = 'none';
    document.getElementById('app-container').style.display = '';
    applyRole(role);
}

function switchRole() {
    localStorage.removeItem('musicClassRole');
    localStorage.removeItem('musicClassStudent');
    document.getElementById('role-overlay').style.display = '';
    document.getElementById('app-container').style.display = 'none';
}

function applyRole(role) {
    const teacherDash = document.getElementById('teacher-dash');
    const studentDash = document.getElementById('student-dash');
    const parentDash = document.getElementById('parent-dash');
    const navBtns = document.querySelectorAll('nav button');

    // Hide all dashboards first
    teacherDash.style.display = 'none';
    studentDash.style.display = 'none';
    parentDash.style.display = 'none';
    document.body.classList.remove('student-mode');

    const switchBtn = document.getElementById('global-switch-btn');
    if (switchBtn) switchBtn.style.display = (role === 'teacher') ? '' : 'none';

    if (role === 'student') {
        studentDash.style.display = '';
        navBtns[0].childNodes[navBtns[0].childNodes.length - 1].textContent = 'Practice';
        navBtns[3].childNodes[navBtns[3].childNodes.length - 1].textContent = 'Class contacts';
        document.body.classList.add('student-mode');
        initStudentDashboard();
    } else if (role === 'parent') {
        parentDash.style.display = '';
        navBtns[0].childNodes[navBtns[0].childNodes.length - 1].textContent = 'Home';
        navBtns[3].childNodes[navBtns[3].childNodes.length - 1].textContent = 'Class contacts';
        document.body.classList.add('student-mode');
        initParentDashboard();
    } else {
        teacherDash.style.display = '';
        navBtns[0].childNodes[navBtns[0].childNodes.length - 1].textContent = 'Home';
        navBtns[3].childNodes[navBtns[3].childNodes.length - 1].textContent = 'Class contacts';
        renderTeacherPracticeTracking();
    }
}

// --- Generate parent login link (teacher only) ---
let lastParentLoginUrl = '';
document.body.addEventListener('click', async function(e) {
    const btn = e.target.closest('.btn-generate-parent-link');
    if (!btn) return;
    e.preventDefault();
    const parentName = btn.getAttribute('data-parent');
    if (!parentName) return;
    try {
        const r = await fetch('/api/parent-login-link?parent_id=' + encodeURIComponent(parentName));
        const data = await r.json();
        if (!r.ok) {
            showToast(data.error || 'Error', true, false);
            return;
        }
        lastParentLoginUrl = data.url || '';
        const toast = document.getElementById('toast');
        if (toast) {
            toast.innerHTML = 'Login link ready. <button type="button" class="copy-parent-link-btn save-btn" style="margin-left:6px; padding:4px 8px;">Copy link</button> <button type="button" class="whatsapp-link-btn save-btn" style="margin-left:6px; padding:4px 8px;">Share via WhatsApp</button>';
            toast.className = 'toast show';
            clearTimeout(toast._timer);
            toast._timer = setTimeout(function() { toast.className = 'toast'; }, 10000);
        } else {
            showToast('Link ready – copy from address bar after opening', false, false);
        }
    } catch (err) {
        showToast('Error generating link', true, false);
    }
});
document.body.addEventListener('click', function(e) {
    if (e.target.classList.contains('copy-parent-link-btn')) {
        if (lastParentLoginUrl) {
            navigator.clipboard.writeText(lastParentLoginUrl).then(function() {
                showToast('Copied to clipboard!', false, false);
            }).catch(function() {
                showToast('Copy failed – try selecting the link manually', true, false);
            });
        }
    }
    if (e.target.classList.contains('whatsapp-link-btn') && lastParentLoginUrl) {
        window.open('https://wa.me/?text=' + encodeURIComponent(lastParentLoginUrl), '_blank');
    }
    if (e.target.classList.contains('btn-remove-student')) {
        const btn = e.target.closest('.btn-remove-student');
        const name = btn && btn.dataset.studentName;
        if (name && confirm('Remove student "' + name + '"?')) {
            fetch('/api/students/remove', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ student_id: name }) })
                .then(function(r) { return r.json(); })
                .then(function(data) { if (data.ok) location.reload(); else showToast(data.error || 'Error', true, false); })
                .catch(function() { showToast('Error', true, false); });
        }
    }
    if (e.target.classList.contains('btn-add-contact')) {
        const input = document.getElementById('add-contact-name');
        const name = (input && input.value) ? input.value.trim() : '';
        if (!name) { showToast('Enter a contact name', true, false); return; }
        fetch('/api/families/add', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ parent: name }) })
            .then(function(r) { return r.json(); })
            .then(function(data) { if (data.ok) location.reload(); else showToast(data.error || 'Error', true, false); })
            .catch(function() { showToast('Error', true, false); });
    }
    if (e.target.classList.contains('btn-remove-contact')) {
        const btn = e.target.closest('.btn-remove-contact');
        const name = btn && btn.dataset.parent;
        if (name && confirm('Remove contact "' + name + '"?')) {
            fetch('/api/families/remove', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ parent: name }) })
                .then(function(r) { return r.json(); })
                .then(function(data) { if (data.ok) location.reload(); else showToast(data.error || 'Error', true, false); })
                .catch(function() { showToast('Error', true, false); });
        }
    }
});

// On load: prefer server session role over localStorage
document.addEventListener('DOMContentLoaded', function() {
    let role = null;
    if (typeof sessionRole !== 'undefined' && sessionRole) {
        role = sessionRole;
        localStorage.setItem('musicClassRole', role);
        if (role === 'student' && typeof sessionStudentId !== 'undefined' && sessionStudentId) {
            localStorage.setItem('musicClassStudent', sessionStudentId);
        }
        if (role === 'parent' && typeof sessionParentId !== 'undefined' && sessionParentId) {
            localStorage.setItem('musicClassParent', sessionParentId);
        }
    } else {
        role = localStorage.getItem('musicClassRole');
    }
    if (role) {
        document.getElementById('role-overlay').style.display = 'none';
        document.getElementById('app-container').style.display = '';
        applyRole(role);
    }
});