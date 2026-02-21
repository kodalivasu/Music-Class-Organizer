let aiChatOpen = false;

function toggleAiChat() {
    aiChatOpen = !aiChatOpen;
    document.getElementById('ai-chat-panel').style.display = aiChatOpen ? 'flex' : 'none';
    document.getElementById('ai-fab').style.display = aiChatOpen ? 'none' : 'flex';
    if (aiChatOpen) {
        document.getElementById('ai-chat-input').focus();
    }
}

function askAiSuggestion(el) {
    document.getElementById('ai-chat-input').value = el.textContent;
    sendAiMessage();
}

async function sendAiMessage() {
    const input = document.getElementById('ai-chat-input');
    const query = input.value.trim();
    if (!query) return;
    input.value = '';

    const messages = document.getElementById('ai-chat-messages');

    // Add user message
    const userDiv = document.createElement('div');
    userDiv.className = 'ai-msg ai-user';
    userDiv.innerHTML = '<div class="ai-msg-content">' + esc(query) + '</div>';
    messages.appendChild(userDiv);

    // Add typing indicator
    const typingDiv = document.createElement('div');
    typingDiv.className = 'ai-msg ai-bot';
    typingDiv.innerHTML = '<div class="ai-msg-content"><div class="ai-typing"><span></span><span></span><span></span></div></div>';
    messages.appendChild(typingDiv);
    messages.scrollTop = messages.scrollHeight;

    // Disable send
    document.querySelector('.ai-send-btn').disabled = true;

    try {
        const resp = await fetch('/api/ai-query', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ query: query })
        });
        const data = await resp.json();

        // Remove typing indicator
        typingDiv.remove();

        // Add bot response
        const botDiv = document.createElement('div');
        botDiv.className = 'ai-msg ai-bot';
        let answer = data.answer || 'Sorry, I could not process that.';

        // Simple markdown → HTML conversion
        answer = formatAiResponse(answer);

        // Add resource links if ragas mentioned
        let resourceHtml = '';
        if (data.mentioned_ragas && data.mentioned_ragas.length > 0) {
            resourceHtml = '<div style="margin-top:10px; display:flex; flex-wrap:wrap; gap:4px;">';
            for (const raga of data.mentioned_ragas) {
                const q = encodeURIComponent('Hindustani classical raga ' + raga);
                resourceHtml += '<a class="raga-resource-btn yt" href="https://www.youtube.com/results?search_query=' + q + '" target="_blank"><svg viewBox="0 0 24 24" width="12" height="12"><path d="M23.5 6.2c-.3-1-1-1.8-2-2.1C19.8 3.6 12 3.6 12 3.6s-7.8 0-9.5.5c-1 .3-1.8 1-2 2.1C0 7.9 0 12 0 12s0 4.1.5 5.8c.3 1 1 1.8 2 2.1 1.7.5 9.5.5 9.5.5s7.8 0 9.5-.5c1-.3 1.8-1 2-2.1.5-1.7.5-5.8.5-5.8s0-4.1-.5-5.8zM9.5 15.6V8.4l6.3 3.6-6.3 3.6z"/></svg> ' + esc(raga) + ' on YouTube</a>';
                resourceHtml += '<a class="raga-resource-btn sp" href="https://open.spotify.com/search/' + q + '" target="_blank"><svg viewBox="0 0 24 24" width="12" height="12"><path d="M12 0C5.4 0 0 5.4 0 12s5.4 12 12 12 12-5.4 12-12S18.6 0 12 0zm5.5 17.3c-.2.3-.6.4-1 .2-2.7-1.6-6-2-10-1.1-.4.1-.8-.2-.9-.5-.1-.4.2-.8.5-.9 4.3-1 8.1-.6 11.1 1.2.4.2.5.7.3 1.1zm1.5-3.3c-.3.4-.8.5-1.2.3-3-1.9-7.7-2.4-11.3-1.3-.5.1-1-.1-1.1-.6s.1-1 .6-1.1c4.1-1.3 9.2-.7 12.7 1.5.3.2.5.8.3 1.2z"/></svg> Spotify</a>';
            }
            resourceHtml += '</div>';
        }

        botDiv.innerHTML = '<div class="ai-msg-content">' + answer + resourceHtml + '</div>';
        messages.appendChild(botDiv);

    } catch(e) {
        typingDiv.remove();
        const errDiv = document.createElement('div');
        errDiv.className = 'ai-msg ai-bot';
        errDiv.innerHTML = '<div class="ai-msg-content" style="color:#ff6666;">Sorry, something went wrong. Please try again.</div>';
        messages.appendChild(errDiv);
    }

    document.querySelector('.ai-send-btn').disabled = false;
    messages.scrollTop = messages.scrollHeight;
    input.focus();
}

function formatAiResponse(text) {
    // Convert markdown-style formatting to HTML
    // Bold
    text = text.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    // Italic
    text = text.replace(/\*(.+?)\*/g, '<em>$1</em>');
    // Inline code
    text = text.replace(/`([^`]+)`/g, '<code>$1</code>');
    // Links
    text = text.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank">$1</a>');
    // Headers (## → bold)
    text = text.replace(/^#{1,3}\s+(.+)$/gm, '<strong>$1</strong>');
    // Lists
    text = text.replace(/^[-*]\s+(.+)$/gm, '&bull; $1');
    // Numbered lists
    text = text.replace(/^(\d+)\.\s+(.+)$/gm, '$1. $2');
    // Paragraphs (double newline)
    text = text.replace(/\n\n/g, '<br><br>');
    // Single newline
    text = text.replace(/\n/g, '<br>');
    return text;
}