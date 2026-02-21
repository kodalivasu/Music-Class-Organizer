const COMP_TYPES = ['Alaap', 'Bandish', 'Taan', 'Sargam', 'Tarana', 'Unknown'];
const TAALS = ['Teentaal', 'Ektaal', 'Jhaptaal', 'Rupak', 'Dadra', 'Keherwa', 'Adi Tala', 'Unknown'];
for (const info of Object.values(categories)) {
    if (info.composition_type && !COMP_TYPES.includes(info.composition_type)) COMP_TYPES.push(info.composition_type);
    if (info.taal && !TAALS.includes(info.taal)) TAALS.push(info.taal);
}

function esc(s) {
    if (!s) return '';
    const d = document.createElement('div');
    d.textContent = String(s);
    return d.innerHTML.replace(/'/g, '&#39;').replace(/"/g, '&quot;');
}

function buildSelect(options, current, filename, field, cssClass) {
    const jsFn = esc(filename).replace(/'/g, "\\'");
    let html = '<select class="tag-select ' + cssClass + '" onchange="handleSelectChange(\'' + jsFn + '\', \'' + field + '\', this)">';
    const seen = new Set();
    for (const opt of options) {
        if (seen.has(opt)) continue;
        seen.add(opt);
        html += '<option value="' + esc(opt) + '"' + (opt === current ? ' selected' : '') + '>' + esc(opt) + '</option>';
    }
    if (current && !seen.has(current)) html += '<option value="' + esc(current) + '" selected>' + esc(current) + '</option>';
    html += '<option value="__new__">+ New...</option>';
    html += '</select>';
    return html;
}

function handleSelectChange(filename, field, selectEl) {
    if (selectEl.value === '__new__') {
        const label = field === 'composition_type' ? 'Composition Type' : 'Taal';
        const newVal = prompt('Enter new ' + label + ':');
        if (newVal && newVal.trim()) {
            updateField(filename, field, newVal.trim());
            // Add the new option to the select and select it
            const opt = document.createElement('option');
            opt.value = newVal.trim();
            opt.textContent = newVal.trim();
            opt.selected = true;
            selectEl.insertBefore(opt, selectEl.querySelector('option[value="__new__"]'));
        } else {
            // Reset to current value
            const current = categories[filename] ? categories[filename][field] : 'Unknown';
            selectEl.value = current || 'Unknown';
        }
    } else {
        updateField(filename, field, selectEl.value);
    }
}

function buildRagaSelect(currentRaga, filename) {
    const ragas = Object.values(categories).map(c => c.raga).filter(r => r && r !== 'Unknown' && r !== 'Uncategorized');
    const unique = [...new Set(ragas)].sort();
    const jsFn = esc(filename).replace(/'/g, "\\'");
    const isUncat = !currentRaga || currentRaga === 'Unknown' || currentRaga === 'Uncategorized';
    let html = '<select class="tag-select raga-select" onchange="handleRagaChange(\'' + jsFn + '\', this)">';
    html += '<option value="Uncategorized"' + (isUncat ? ' selected' : '') + '>Raga...</option>';
    for (const r of unique) {
        html += '<option value="' + esc(r) + '"' + (r === currentRaga ? ' selected' : '') + '>' + esc(r) + '</option>';
    }
    html += '<option value="__new__">+ New Raga...</option>';
    html += '</select>';
    return html;
}

function handleRagaChange(filename, selectEl) {
    if (selectEl.value === '__new__') {
        const newName = prompt('Enter the new raga name:');
        if (newName && newName.trim()) {
            reassignRaga(filename, newName.trim());
        } else {
            const current = categories[filename] ? categories[filename].raga : 'Uncategorized';
            selectEl.value = (current && current !== 'Unknown') ? current : 'Uncategorized';
        }
    } else {
        reassignRaga(filename, selectEl.value);
    }
}

async function reassignRaga(filename, newRaga) {
    if (!categories[filename]) {
        categories[filename] = { raga: 'Unknown', composition_type: 'Unknown', paltaas: false, taal: 'Unknown', explanation: 'Manually categorized' };
    }
    const oldRaga = categories[filename].raga;
    if (oldRaga === newRaga) return;
    pushUndo('Move ' + filename + ' from ' + oldRaga + ' to ' + newRaga);
    categories[filename].raga = newRaga;
    const resp = await fetch('/api/update-file', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({filename: filename, updates: {raga: newRaga}})
    });
    if (!resp.ok) { showToast('Error saving raga change', true, false); return; }
    // Re-render so the new raga group appears, then re-open the edit panel
    renderMusicLibrary();
    reopenEditPanel(filename);
    showToast('Moved to ' + newRaga, false, true);
}

function reopenEditPanel(filename) {
    const items = document.querySelectorAll('.music-item');
    for (const item of items) {
        if (item.dataset.filename === filename) {
            const editPanel = item.querySelector('.music-item-edit');
            const btn = item.querySelector('.item-edit-toggle');
            if (editPanel) editPanel.classList.remove('collapsed');
            if (btn) btn.classList.add('active');
            // Also expand the parent raga group if collapsed
            const cardBody = item.closest('.card-body');
            if (cardBody && cardBody.classList.contains('collapsed')) {
                cardBody.classList.remove('collapsed');
                const arrow = cardBody.previousElementSibling.querySelector('.collapse-arrow');
                if (arrow) arrow.style.transform = 'rotate(90deg)';
            }
            item.scrollIntoView({ behavior: 'smooth', block: 'center' });
            break;
        }
    }
}

function friendlyName(filename) {
    const parts = filename.replace(/\.[^.]+$/, '').split('_');
    if (parts.length >= 1 && /^\d{4}-\d{2}-\d{2}$/.test(parts[0])) {
        try {
            const d = new Date(parts[0] + 'T12:00:00');
            const dateStr = d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
            const rest = parts.slice(1).join(' ').replace(/-/g, ' ');
            return dateStr + (rest ? ' — ' + rest : '');
        } catch(e) {}
    }
    if (filename.startsWith('Drive_')) return filename.replace(/^Drive_/, '').replace(/\.[^.]+$/, '').replace(/_/g, ' ').replace(/-/g, ' ');
    return filename;
}

function fileDate(fn) {
    const m = fn.match(/^(\d{4}-\d{2}-\d{2})/);
    return m ? m[1] : '';
}

function buildRecentSection() {
    // Combine all audio files, sort newest-first by date in filename
    const allFiles = [...new Set([...Object.keys(categories), ...allAudioFiles])];
    allFiles.sort((a, b) => {
        const da = fileDate(a), db = fileDate(b);
        if (da && db) return db.localeCompare(da);
        if (da) return -1;
        if (db) return 1;
        return b.localeCompare(a);
    });
    const recent = allFiles.slice(0, 10);
    if (recent.length === 0) return '';

    let html = '<div class="card raga-group recent-group">';
    html += '<div class="card-header" onclick="toggleCardBody(this)"><div class="card-header-left">';
    html += '<h3 class="raga-name"><span class="raga-text">Recent Recordings</span></h3></div>';
    html += '<span class="badge">' + recent.length + '</span><span class="collapse-arrow">&#9654;</span></div>';
    html += '<div class="card-body collapsed">';
    for (const fn of recent) {
        html += buildMusicItem(fn, categories[fn] || null);
    }
    html += '</div></div>';
    return html;
}

function renderMusicLibrary() {
    const container = document.getElementById('music-list');
    const byRaga = {};
    for (const [fn, info] of Object.entries(categories)) {
        const raga = (info.raga && info.raga !== 'Unknown') ? info.raga : 'Uncategorized';
        if (!byRaga[raga]) byRaga[raga] = [];
        byRaga[raga].push(fn);
    }
    // Also add files not in categories at all into Uncategorized
    const notInCatalog = allAudioFiles.filter(f => !(f in categories));
    if (notInCatalog.length > 0) {
        if (!byRaga['Uncategorized']) byRaga['Uncategorized'] = [];
        for (const f of notInCatalog) byRaga['Uncategorized'].push(f);
    }
    let html = '';
    // Recent recordings section at top
    html += buildRecentSection();
    // Sort ragas by most recent recording date (newest raga group first), but keep Uncategorized at the bottom
    const ragaKeys = Object.keys(byRaga).filter(r => r !== 'Uncategorized');
    const ragasSorted = ragaKeys.sort((a, b) => {
        const latestA = byRaga[a].sort().reverse()[0] || '';
        const latestB = byRaga[b].sort().reverse()[0] || '';
        return latestB.localeCompare(latestA);
    });
    html += '<h3 class="section-title" style="margin-top:20px; margin-bottom:10px;">Browse by Raga</h3>';
    for (const raga of ragasSorted) html += buildRagaGroup(raga, byRaga[raga]);
    if (byRaga['Uncategorized'] && byRaga['Uncategorized'].length > 0) html += buildUncategorizedGroup(byRaga['Uncategorized']);
    container.innerHTML = html;
    initDragDrop();
    applySearchFilter();
}

function buildRagaGroup(raga, filenames) {
    const safeName = esc(raga);
    const searchTerm = encodeURIComponent('Hindustani classical raga ' + raga);
    let html = '<div class="card raga-group" data-raga="' + safeName + '">';
    html += '<div class="card-header" onclick="toggleCardBody(this)"><div class="card-header-left">';
    html += '<h3 class="raga-name"><span class="raga-text">' + safeName + '</span>';
    html += ' <span class="edit-icon" onclick="event.stopPropagation(); startEditRaga(this, \'' + safeName.replace(/'/g, "\\'") + '\')" title="Rename">&#9998;</span>';
    html += '</h3></div>';
    // Resource links
    if (raga !== 'Unknown' && raga !== 'Uncategorized') {
        html += '<div class="raga-resources" onclick="event.stopPropagation()">';
        html += '<a class="raga-resource-btn yt" href="https://www.youtube.com/results?search_query=' + searchTerm + '" target="_blank" title="YouTube"><svg viewBox="0 0 24 24"><path d="M23.5 6.2c-.3-1-1-1.8-2-2.1C19.8 3.6 12 3.6 12 3.6s-7.8 0-9.5.5c-1 .3-1.8 1-2 2.1C0 7.9 0 12 0 12s0 4.1.5 5.8c.3 1 1 1.8 2 2.1 1.7.5 9.5.5 9.5.5s7.8 0 9.5-.5c1-.3 1.8-1 2-2.1.5-1.7.5-5.8.5-5.8s0-4.1-.5-5.8zM9.5 15.6V8.4l6.3 3.6-6.3 3.6z"/></svg> YouTube</a>';
        html += '<a class="raga-resource-btn sp" href="https://open.spotify.com/search/' + searchTerm + '" target="_blank" title="Spotify"><svg viewBox="0 0 24 24"><path d="M12 0C5.4 0 0 5.4 0 12s5.4 12 12 12 12-5.4 12-12S18.6 0 12 0zm5.5 17.3c-.2.3-.6.4-1 .2-2.7-1.6-6-2-10-1.1-.4.1-.8-.2-.9-.5-.1-.4.2-.8.5-.9 4.3-1 8.1-.6 11.1 1.2.4.2.5.7.3 1.1zm1.5-3.3c-.3.4-.8.5-1.2.3-3-1.9-7.7-2.4-11.3-1.3-.5.1-1-.1-1.1-.6s.1-1 .6-1.1c4.1-1.3 9.2-.7 12.7 1.5.3.2.5.8.3 1.2zm.1-3.4c-3.7-2.2-9.7-2.4-13.2-1.3-.5.2-1.1-.1-1.3-.7-.2-.5.1-1.1.7-1.3 4-1.2 10.6-1 14.8 1.5.5.3.7.9.4 1.4-.3.5-.9.7-1.4.4z"/></svg> Spotify</a>';
        html += '<a class="raga-resource-btn wiki" href="https://en.wikipedia.org/wiki/Special:Search?search=' + searchTerm + '" target="_blank" title="Wikipedia"><svg viewBox="0 0 24 24"><path d="M12.1 2C6.5 2 2 6.5 2 12.1s4.5 10.1 10.1 10.1S22.2 17.6 22.2 12 17.6 2 12.1 2zm5 5.1h-1.8c-.2-.7-.4-1.3-.6-1.9 1 .5 1.8 1.1 2.4 1.9zM12 4c.4.5.9 1.2 1.2 2.1h-2.5c.4-.9.9-1.6 1.3-2.1zM4.3 14c-.1-.6-.2-1.3-.2-2s.1-1.3.2-2h2.2c-.1.7-.1 1.3-.1 2s.1 1.3.1 2H4.3zm.8 2h1.8c.2.7.4 1.3.6 1.9-1-.5-1.8-1.1-2.4-1.9zm1.8-8H5.1c.6-.8 1.4-1.4 2.4-1.9-.2.6-.4 1.2-.6 1.9zM12 20c-.4-.5-.9-1.2-1.2-2.1h2.5c-.4.9-.9 1.6-1.3 2.1zm1.6-4.1H10.4c-.1-.7-.2-1.3-.2-2s.1-1.4.2-2h3.2c.1.6.2 1.3.2 2s-.1 1.3-.2 2zm.3 3.9c.2-.6.4-1.2.6-1.9h1.8c-.6.8-1.4 1.5-2.4 1.9zm.8-3.9c.1-.7.1-1.3.1-2s-.1-1.3-.1-2h2.2c.1.6.2 1.3.2 2s-.1 1.3-.2 2h-2.2z"/></svg> Learn</a>';
        html += '</div>';
    }
    html += '<span class="badge">' + filenames.length + '</span><span class="collapse-arrow">&#9654;</span></div>';
    html += '<div class="card-body collapsed">';
    for (const fn of filenames.sort().reverse()) html += buildMusicItem(fn, categories[fn]);
    html += '</div></div>';
    return html;
}

function buildUncategorizedGroup(filenames) {
    let html = '<div class="card raga-group uncategorized" data-raga="Uncategorized">';
    html += '<div class="card-header" onclick="toggleCardBody(this)"><div class="card-header-left">';
    html += '<h3 class="raga-name"><span class="raga-text">Uncategorized</span></h3></div>';
    html += '<span class="badge muted">' + filenames.length + '</span><span class="collapse-arrow">&#9654;</span></div>';
    html += '<div class="card-body collapsed">';
    for (const fn of filenames.sort()) html += buildMusicItem(fn, null);
    html += '</div></div>';
    return html;
}

function buildMusicItem(filename, info) {
    const comp = info ? (info.composition_type || 'Unknown') : 'Unknown';
    const taal = info ? (info.taal || 'Unknown') : 'Unknown';
    const paltaas = info ? (info.paltaas || false) : false;
    const customTitle = info ? (info.title || '') : '';
    const safeFn = esc(filename);
    const jsFn = safeFn.replace(/'/g, "\\'");
    const friendly = customTitle || friendlyName(filename);
    const mediaUrl = (typeof mediaAudioBase !== 'undefined' ? mediaAudioBase : '/media/audio/') + encodeURIComponent(filename);
    let html = '<div class="music-item" draggable="true" data-filename="' + safeFn + '">';
    // Compact top row: friendly name + action buttons
    html += '<div class="music-item-top">';
    html += '<div class="music-item-info"><span class="music-item-friendly">' + esc(friendly) + '</span></div>';
    html += '<div class="music-item-actions">';
    html += '<button class="item-action-btn" onclick="event.stopPropagation(); downloadRecording(\'' + jsFn + '\')" title="Download"><svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M19 9h-4V3H9v6H5l7 7 7-7zM5 18v2h14v-2H5z"/></svg></button>';
    html += '<button class="item-action-btn" onclick="event.stopPropagation(); shareRecording(\'' + jsFn + '\', \'' + esc(friendly).replace(/'/g, "\\'") + '\')" title="Share"><svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M18 16.08c-.76 0-1.44.3-1.96.77L8.91 12.7c.05-.23.09-.46.09-.7s-.04-.47-.09-.7l7.05-4.11c.54.5 1.25.81 2.04.81 1.66 0 3-1.34 3-3s-1.34-3-3-3-3 1.34-3 3c0 .24.04.47.09.7L8.04 9.81C7.5 9.31 6.79 9 6 9c-1.66 0-3 1.34-3 3s1.34 3 3 3c.79 0 1.5-.31 2.04-.81l7.12 4.16c-.05.21-.08.43-.08.65 0 1.61 1.31 2.92 2.92 2.92 1.61 0 2.92-1.31 2.92-2.92s-1.31-2.92-2.92-2.92z"/></svg></button>';
    html += '<button class="item-edit-toggle" onclick="event.stopPropagation(); toggleItemEdit(this)" title="Edit metadata">&#9998;</button>';
    html += '</div></div>';
    // Audio player (always visible)
    html += '<audio controls preload="none"><source src="' + mediaUrl + '"></audio>';
    // Collapsible edit controls
    html += '<div class="music-item-edit collapsed">';
    html += '<div class="music-item-title-row">';
    html += '<label class="edit-label">Title</label>';
    html += '<input type="text" class="title-edit-input" value="' + esc(friendly) + '" placeholder="' + esc(friendlyName(filename)) + '" onblur="saveTitle(\'' + jsFn + '\', this)" onkeydown="if(event.key===\'Enter\'){this.blur();}">';
    html += '</div>';
    html += '<span class="music-item-name">' + safeFn + '</span>';
    html += '<div class="music-item-tags">';
    html += '<span class="drag-handle" title="Drag to move">&#10495;</span>';
    html += buildRagaSelect(info ? info.raga : 'Uncategorized', filename);
    html += buildSelect(COMP_TYPES, comp, filename, 'composition_type', 'type-select');
    html += buildSelect(TAALS, taal, filename, 'taal', 'taal-select');
    html += '<button class="paltaa-btn' + (paltaas ? ' active' : '') + '" onclick="togglePaltaa(\'' + jsFn + '\', this)">Paltaa</button>';
    html += '<button class="delete-btn" onclick="event.stopPropagation(); deleteRecording(\'' + jsFn + '\')" title="Delete recording">&#128465;</button>';
    html += '</div></div>';
    html += '</div>';
    return html;
}

function saveTitle(filename, inputEl) {
    const newTitle = inputEl.value.trim();
    const defaultTitle = friendlyName(filename);
    const titleToSave = (newTitle && newTitle !== defaultTitle) ? newTitle : '';
    if (!categories[filename]) categories[filename] = { raga: 'Unknown', composition_type: 'Unknown', paltaas: false, taal: 'Unknown', explanation: 'Manually categorized' };
    const oldTitle = categories[filename].title || '';
    if (titleToSave === oldTitle) return;
    pushUndo('title: ' + (oldTitle || defaultTitle) + ' -> ' + (titleToSave || defaultTitle));
    categories[filename].title = titleToSave;
    // Update the friendly name display in the top row
    const item = inputEl.closest('.music-item');
    if (item) {
        const display = item.querySelector('.music-item-friendly');
        if (display) display.textContent = titleToSave || defaultTitle;
    }
    fetch('/api/update-file', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({filename, updates: {title: titleToSave}}) })
    .then(r => r.json()).then(() => showToast('Title saved', false, true)).catch(() => showToast('Error', true, false));
}

function toggleItemEdit(btn) {
    const item = btn.closest('.music-item');
    const editPanel = item.querySelector('.music-item-edit');
    const wasOpen = !editPanel.classList.contains('collapsed');
    editPanel.classList.toggle('collapsed');
    btn.classList.toggle('active');
    if (wasOpen) {
        renderMusicLibrary();
    }
}

function downloadRecording(filename) {
    const a = document.createElement('a');
    a.href = (typeof mediaAudioBase !== 'undefined' ? mediaAudioBase : '/media/audio/') + encodeURIComponent(filename);
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
}

function shareRecording(filename, title) {
    const base = typeof mediaAudioBase !== 'undefined' ? mediaAudioBase : '/media/audio/';
    const url = window.location.origin + base + encodeURIComponent(filename);
    const text = 'Listen to: ' + title;

    // Try native Web Share API first (works great on mobile)
    if (navigator.share) {
        navigator.share({ title: title, text: text, url: url })
        .catch(function() {});
        return;
    }

    // Fallback: show share options modal
    const modal = document.getElementById('share-modal');
    document.getElementById('share-title').textContent = title;
    const waUrl = 'https://wa.me/?text=' + encodeURIComponent(text + ' ' + url);
    const smsUrl = 'sms:?body=' + encodeURIComponent(text + ' ' + url);
    document.getElementById('share-whatsapp-link').href = waUrl;
    document.getElementById('share-sms-link').href = smsUrl;
    document.getElementById('share-copy-url').dataset.url = url;
    modal.style.display = 'flex';
}

function copyShareUrl(btn) {
    const url = btn.dataset.url;
    navigator.clipboard.writeText(url).then(function() {
        showToast('Link copied!', false, false);
    }).catch(function() {
        // Fallback for older browsers
        const input = document.createElement('input');
        input.value = url;
        document.body.appendChild(input);
        input.select();
        document.execCommand('copy');
        document.body.removeChild(input);
        showToast('Link copied!', false, false);
    });
}

async function handleAudioUpload(input) {
    const files = input.files;
    if (!files || files.length === 0) return;
    showToast('Uploading ' + files.length + ' file(s)...', false, false);

    for (const file of files) {
        const reader = new FileReader();
        await new Promise(function(resolve) {
            reader.onload = async function() {
                const base64 = reader.result.split(',')[1];
                const ext = file.name.split('.').pop() || 'mp3';
                const now = new Date();
                const dateStr = now.getFullYear() + '-' + String(now.getMonth()+1).padStart(2,'0') + '-' + String(now.getDate()).padStart(2,'0');
                const name = file.name.replace(/\.[^.]+$/, '').replace(/[^a-zA-Z0-9_-]/g, '_');
                const filename = dateStr + '_' + name + '.' + ext;
                try {
                    const resp = await fetch('/api/upload-audio-file', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({ filename: filename, data: base64 })
                    });
                    const result = await resp.json();
                    if (result.ok) {
                        if (!allAudioFiles.includes(result.filename)) allAudioFiles.push(result.filename);
                    }
                } catch(e) {}
                resolve();
            };
            reader.readAsDataURL(file);
        });
    }
    input.value = '';
    renderMusicLibrary();
    showToast(files.length + ' file(s) uploaded!', false, false);
}

// --- Undo ---
let undoStack = [];
function pushUndo(desc) {
    undoStack.push({ snapshot: JSON.parse(JSON.stringify(categories)), description: desc });
    if (undoStack.length > 30) undoStack.shift();
    updateUndoCount();
}
function undoLastEdit() {
    if (!undoStack.length) return;
    const entry = undoStack.pop();
    categories = entry.snapshot;
    updateUndoCount();
    fetch('/api/restore', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(categories) })
    .then(r => r.json()).then(() => { renderMusicLibrary(); showToast('Undid: ' + entry.description, false, false); })
    .catch(() => showToast('Error undoing', true, false));
}
function updateUndoCount() {
    const btn = document.getElementById('undo-fab');
    if (!btn) return;
    if (undoStack.length > 0) { btn.style.display = 'flex'; btn.querySelector('.undo-count').textContent = undoStack.length; }
    else { btn.style.display = 'none'; }
}

async function deleteRecording(filename) {
    if (!confirm('Delete "' + filename + '"? This will remove the file and its metadata.')) return;
    pushUndo('Delete ' + filename);
    try {
        const resp = await fetch('/api/delete-recording', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ filename: filename })
        });
        const result = await resp.json();
        if (result.ok) {
            delete categories[filename];
            const idx = allAudioFiles.indexOf(filename);
            if (idx > -1) allAudioFiles.splice(idx, 1);
            renderMusicLibrary();
            showToast('Deleted ' + filename, false, true);
        } else {
            showToast('Error: ' + (result.error || 'Delete failed'), true, false);
        }
    } catch(e) {
        showToast('Error deleting recording', true, false);
    }
}

// --- Edit handlers ---
function updateField(filename, field, value) {
    if (!categories[filename]) categories[filename] = { raga: 'Unknown', composition_type: 'Unknown', paltaas: false, taal: 'Unknown', explanation: 'Manually categorized' };
    pushUndo(field + ': ' + categories[filename][field] + ' -> ' + value);
    categories[filename][field] = value;
    fetch('/api/update-file', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({filename, updates: {[field]: value}}) })
    .then(r => r.json()).then(() => showToast('Saved', false, true)).catch(() => showToast('Error', true, false));
}
function togglePaltaa(filename, btn) {
    if (!categories[filename]) categories[filename] = { raga: 'Unknown', composition_type: 'Unknown', paltaas: false, taal: 'Unknown', explanation: 'Manually categorized' };
    pushUndo('paltaas toggle');
    const nv = !categories[filename].paltaas;
    categories[filename].paltaas = nv;
    btn.classList.toggle('active', nv);
    fetch('/api/update-file', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({filename, updates: {paltaas: nv}}) })
    .then(r => r.json()).then(() => showToast('Saved', false, true)).catch(() => showToast('Error', true, false));
}
function startEditRaga(iconEl, oldName) {
    const h3 = iconEl.closest('.raga-name');
    const input = document.createElement('input');
    input.type = 'text'; input.value = oldName; input.className = 'raga-edit-input';
    const orig = h3.innerHTML; h3.innerHTML = ''; h3.appendChild(input); input.focus(); input.select();
    let saved = false;
    function save() {
        if (saved) return; saved = true;
        const nn = input.value.trim();
        if (nn && nn !== oldName) {
            pushUndo('Rename: ' + oldName + ' -> ' + nn);
            fetch('/api/rename-raga', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({old_name: oldName, new_name: nn}) })
            .then(r => r.json()).then(() => { for (const i of Object.values(categories)) { if (i.raga === oldName) i.raga = nn; } renderMusicLibrary(); showToast(oldName + ' -> ' + nn, false, true); })
            .catch(() => { h3.innerHTML = orig; showToast('Error', true, false); });
        } else h3.innerHTML = orig;
    }
    input.addEventListener('blur', save);
    input.addEventListener('keydown', function(e) { if (e.key === 'Enter') { e.preventDefault(); save(); } if (e.key === 'Escape') { saved = true; h3.innerHTML = orig; } });
}

// --- Drag & Drop ---
let draggedFilename = null;
function initDragDrop() {
    document.querySelectorAll('.music-item[draggable]').forEach(function(item) {
        item.addEventListener('dragstart', function(e) { draggedFilename = item.dataset.filename; item.classList.add('dragging'); e.dataTransfer.effectAllowed = 'move'; e.dataTransfer.setData('text/plain', draggedFilename); });
        item.addEventListener('dragend', function() { item.classList.remove('dragging'); document.querySelectorAll('.drag-over').forEach(el => el.classList.remove('drag-over')); draggedFilename = null; });
    });
    document.querySelectorAll('.raga-group').forEach(function(group) {
        group.addEventListener('dragover', function(e) { e.preventDefault(); e.dataTransfer.dropEffect = 'move'; group.classList.add('drag-over'); });
        group.addEventListener('dragleave', function(e) { if (!group.contains(e.relatedTarget)) group.classList.remove('drag-over'); });
        group.addEventListener('drop', function(e) { e.preventDefault(); group.classList.remove('drag-over'); const tr = group.dataset.raga; if (draggedFilename && tr && tr !== 'Uncategorized') { const cr = categories[draggedFilename] ? categories[draggedFilename].raga : null; if (cr !== tr) updateField(draggedFilename, 'raga', tr); } draggedFilename = null; });
    });
}

// --- Search ---
let currentFilter = '';
function filterMusic(q) { currentFilter = q.toLowerCase(); applySearchFilter(); }
function applySearchFilter() {
    if (!currentFilter) { document.querySelectorAll('#music-list .card').forEach(c => c.style.display = ''); return; }
    document.querySelectorAll('#music-list .card').forEach(card => { card.style.display = card.textContent.toLowerCase().includes(currentFilter) ? '' : 'none'; });
}

// --- Toast ---
function showToast(msg, isError, showUndo) {
    const toast = document.getElementById('toast');
    toast.innerHTML = esc(msg);
    if (showUndo && undoStack.length > 0) toast.innerHTML += ' <button class="undo-toast-btn" onclick="event.stopPropagation(); undoLastEdit();">Undo</button>';
    toast.className = 'toast show' + (isError ? ' error' : '');
    clearTimeout(toast._timer);
    toast._timer = setTimeout(() => { toast.className = 'toast'; }, showUndo ? 5000 : 2500);
}

function toggleCardBody(hdr) {
    const body = hdr.nextElementSibling;
    body.classList.toggle('collapsed');
    const arrow = hdr.querySelector('.collapse-arrow');
    if (arrow) arrow.style.transform = body.classList.contains('collapsed') ? '' : 'rotate(90deg)';
}

document.addEventListener('DOMContentLoaded', function() { renderMusicLibrary(); updateUndoCount(); });