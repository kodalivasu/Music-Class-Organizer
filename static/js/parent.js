let parentProfile = null;
let currentParent = null;
let allAttendance = {};
let allPracticeLog = {};

function initParentDashboard() {
    const saved = localStorage.getItem('musicClassParent');
    if (saved) {
        currentParent = saved;
        loadParentProfile();
    } else {
        renderParentPicker();
    }
}

function renderParentPicker() {
    const container = document.getElementById('parent-name-buttons');
    let html = '';
    for (const name of parentNames) {
        html += '<button class="name-pick-btn" onclick="pickParent(\'' + esc(name).replace(/'/g, "\\'") + '\')">' + esc(name) + '</button>';
    }
    container.innerHTML = html;
    document.getElementById('parent-picker').style.display = '';
    document.getElementById('kid-picker').style.display = 'none';
    document.getElementById('parent-home').style.display = 'none';
}

function pickParent(name) {
    currentParent = name;
    localStorage.setItem('musicClassParent', name);
    loadParentProfile();
}

async function loadParentProfile() {
    try {
        const r = await fetch('/api/parent-profiles');
        const profiles = await r.json();
        parentProfile = profiles[currentParent] || { children: [], payments: [] };
    } catch(e) {
        parentProfile = { children: [], payments: [] };
    }

    if (parentProfile.children.length === 0) {
        // Need to pick children
        showKidPicker();
    } else {
        showParentHome();
    }
}

function showKidPicker() {
    document.getElementById('parent-picker').style.display = 'none';
    document.getElementById('kid-picker').style.display = '';
    document.getElementById('parent-home').style.display = 'none';

    const container = document.getElementById('kid-checkboxes');
    let html = '';
    for (const name of studentNames) {
        const checked = parentProfile.children.includes(name) ? 'checked' : '';
        html += '<label class="att-student" style="max-width:320px; margin:0 auto 6px;"><input type="checkbox" value="' + esc(name) + '" ' + checked + '><span class="att-check"></span><span>' + esc(name) + '</span></label>';
    }
    container.innerHTML = html;
}

async function saveKidSelection() {
    const checkboxes = document.querySelectorAll('#kid-checkboxes input[type=checkbox]');
    const children = [];
    checkboxes.forEach(cb => { if (cb.checked) children.push(cb.value); });
    if (children.length === 0) { showToast('Please select at least one child', true, false); return; }

    parentProfile.children = children;
    await fetch('/api/parent-profile/save', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ parent: currentParent, children: children })
    });
    showParentHome();
}

async function showParentHome() {
    document.getElementById('parent-picker').style.display = 'none';
    document.getElementById('kid-picker').style.display = 'none';
    document.getElementById('parent-home').style.display = '';

    // Set welcome
    const firstName = currentParent.split(' ')[0];
    document.getElementById('parent-welcome-name').textContent = 'Hi, ' + firstName + '!';
    const today = new Date();
    document.getElementById('parent-date-display').textContent = today.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' });

    // Load data
    try {
        const [attR, logR, profR, evR] = await Promise.all([
            fetch('/api/attendance'), fetch('/api/practice-log'),
            fetch('/api/parent-profiles'), fetch('/api/events/scheduled')
        ]);
        allAttendance = await attR.json();
        allPracticeLog = await logR.json();
        const profiles = await profR.json();
        parentProfile = profiles[currentParent] || parentProfile;
        const scheduledEvents = await evR.json();
        renderParentEvents(scheduledEvents);
    } catch(e) {}

    renderChildCards();
    renderFeeSection();
}

// --- Child Practice Cards ---
function renderChildCards() {
    const container = document.getElementById('parent-children-cards');
    let html = '';
    for (const child of parentProfile.children) {
        const dates = (allPracticeLog[child] || []).sort();
        const streak = calcStreakFor(dates);
        const thisWeek = countThisWeek(dates);
        html += '<div class="child-card">';
        html += '<div class="child-card-header">';
        html += '<span class="child-name">' + esc(child) + '</span>';
        html += '<span class="child-streak">&#128293; ' + streak + ' day streak</span>';
        html += '</div>';
        html += renderMiniCal(dates);
        html += '<div class="child-practice-stat">Practiced <strong>' + thisWeek + ' of 7</strong> days this week</div>';
        html += '</div>';
    }
    container.innerHTML = html || '<p class="empty-state">No children selected. <button class="att-action-btn" onclick="showKidPicker()">Select children</button></p>';
}

function calcStreakFor(dates) {
    if (dates.length === 0) return 0;
    const today = new Date(); today.setHours(0,0,0,0);
    const todayStr = pFormatDate(today);
    let check = new Date(today);
    if (!dates.includes(todayStr)) {
        check.setDate(check.getDate() - 1);
        if (!dates.includes(pFormatDate(check))) return 0;
    }
    check = new Date(today);
    if (!dates.includes(todayStr)) check.setDate(check.getDate() - 1);
    let streak = 0;
    while (dates.includes(pFormatDate(check))) { streak++; check.setDate(check.getDate() - 1); }
    return streak;
}

function countThisWeek(dates) {
    const today = new Date(); today.setHours(0,0,0,0);
    const dayOfWeek = today.getDay(); // 0=Sun
    let count = 0;
    for (let i = 0; i <= dayOfWeek; i++) {
        const d = new Date(today); d.setDate(d.getDate() - (dayOfWeek - i));
        if (dates.includes(pFormatDate(d))) count++;
    }
    return count;
}

function pFormatDate(d) {
    return d.getFullYear() + '-' + String(d.getMonth()+1).padStart(2,'0') + '-' + String(d.getDate()).padStart(2,'0');
}

function renderMiniCal(dates) {
    const today = new Date(); today.setHours(0,0,0,0);
    const todayStr = pFormatDate(today);
    const dayNames = ['S','M','T','W','T','F','S'];
    let html = '<div class="child-mini-cal">';
    for (let i = 6; i >= 0; i--) {
        const d = new Date(today); d.setDate(d.getDate() - i);
        const ds = pFormatDate(d);
        const practiced = dates.includes(ds);
        const isToday = ds === todayStr;
        let cls = practiced ? 'practiced' : (isToday ? 'empty' : 'missed');
        html += '<div class="cal-day"><span class="cal-label">' + dayNames[d.getDay()] + '</span>';
        html += '<div class="cal-dot ' + cls + (isToday ? ' today' : '') + '">' + d.getDate() + '</div></div>';
    }
    html += '</div>';
    return html;
}

// --- Fees & Payment ---
function renderFeeSection() {
    const container = document.getElementById('parent-fees-section');
    const payments = parentProfile.payments || [];
    const lastPayment = payments.length > 0 ? payments[payments.length - 1] : null;
    const lastPaymentDate = lastPayment ? lastPayment.date : null;

    // Count classes since last payment
    const classDates = Object.keys(allAttendance).sort();
    let classesSincePayment = 0;
    for (const d of classDates) {
        if (!lastPaymentDate || d > lastPaymentDate) {
            // Check if any of this parent's children attended
            const present = allAttendance[d].students || [];
            for (const child of parentProfile.children) {
                if (present.includes(child)) { classesSincePayment++; break; }
            }
        }
    }

    const venmoHandle = teacherVenmo || '@Teacher';
    const venmoUrl = 'https://venmo.com/' + venmoHandle.replace('@', '');

    let html = '<div class="fee-card">';
    html += '<div class="fee-row"><span class="fee-label">Classes since last payment</span><span class="fee-value highlight">' + classesSincePayment + '</span></div>';
    html += '<div class="fee-row"><span class="fee-label">Last payment</span><span class="fee-value' + (lastPayment ? ' paid' : '') + '">' + (lastPaymentDate || 'No payments yet') + '</span></div>';
    if (lastPayment && lastPayment.amount) {
        html += '<div class="fee-row"><span class="fee-label">Last amount</span><span class="fee-value paid">$' + esc(String(lastPayment.amount)) + '</span></div>';
    }

    // Venmo button
    html += '<a href="' + venmoUrl + '" target="_blank" class="venmo-btn">';
    html += '<svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor"><path d="M19.5 3c.9 1.5 1.3 3 1.3 5 0 5.5-4.7 12.6-8.5 17H5.2L2.8 3.5l6.3-.6 1.3 10.7c1.2-2 2.7-5.2 2.7-7.4 0-1.9-.3-3.1-.8-4.1L19.5 3z"/></svg>';
    html += 'Pay via Venmo (' + esc(venmoHandle) + ')</a>';

    // Mark payment button
    html += '<button class="mark-payment-btn" onclick="togglePaymentForm()">Record a payment</button>';
    html += '<div id="payment-form-area"></div>';

    // Payment history
    if (payments.length > 0) {
        html += '<div class="payment-history"><div class="modal-label" style="margin-top:12px; margin-bottom:6px;">Payment History</div>';
        for (const p of [...payments].reverse()) {
            html += '<div class="payment-entry"><span class="pay-date">' + esc(p.date) + '</span>';
            if (p.amount) html += '<span class="pay-amount">$' + esc(String(p.amount)) + '</span>';
            if (p.note) html += '<span class="pay-note">' + esc(p.note) + '</span>';
            html += '</div>';
        }
        html += '</div>';
    }

    html += '</div>';
    container.innerHTML = html;
}

function togglePaymentForm() {
    const area = document.getElementById('payment-form-area');
    if (area.innerHTML) { area.innerHTML = ''; return; }
    let html = '<div class="payment-form">';
    html += '<div class="modal-row"><label class="modal-label">Amount ($)</label><input type="number" id="pay-amount" class="modal-input" placeholder="e.g. 100"></div>';
    html += '<div class="modal-row"><label class="modal-label">Note (optional)</label><input type="text" id="pay-note" class="modal-input" placeholder="e.g. January + February classes"></div>';
    html += '<button class="save-btn" onclick="submitPayment()">Record Payment</button>';
    html += '</div>';
    area.innerHTML = html;
}

async function submitPayment() {
    const amount = document.getElementById('pay-amount').value.trim();
    const note = document.getElementById('pay-note').value.trim();
    const resp = await fetch('/api/parent-profile/mark-payment', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ parent: currentParent, amount: amount, note: note })
    });
    const result = await resp.json();
    if (result.ok) {
        parentProfile.payments = parentProfile.payments || [];
        parentProfile.payments.push(result.payment);
        renderFeeSection();
        showToast('Payment recorded!', false, false);
    } else {
        showToast('Error recording payment', true, false);
    }
}

// --- Parent Events ---
function renderParentEvents(scheduledEvents) {
    const container = document.getElementById('parent-events-section');
    const todayStr = pFormatDate(new Date());
    const upcoming = (scheduledEvents || []).filter(e => e.date >= todayStr).sort((a,b) => a.date.localeCompare(b.date));

    if (upcoming.length === 0) {
        container.innerHTML = '<div class="parent-event" style="justify-content:center;"><p class="empty-state" style="padding:10px;">No upcoming events</p></div>';
        return;
    }

    let html = '';
    for (const ev of upcoming) {
        const d = new Date(ev.date + 'T12:00:00');
        const month = d.toLocaleDateString('en-US', { month: 'short' });
        const day = d.getDate();
        html += '<div class="parent-event">';
        html += '<div class="parent-event-date"><div class="pe-month">' + month + '</div><div class="pe-day">' + day + '</div></div>';
        html += '<div class="parent-event-info"><div class="parent-event-name">' + esc(ev.name) + '</div>';
        let meta = '';
        if (ev.time) meta += ev.time;
        if (ev.location) meta += (meta ? ' — ' : '') + ev.location;
        if (meta) html += '<div class="parent-event-meta">' + esc(meta) + '</div>';
        if (ev.description) html += '<div class="parent-event-meta" style="margin-top:2px;">' + esc(ev.description) + '</div>';
        html += '</div></div>';
    }
    container.innerHTML = html;
}