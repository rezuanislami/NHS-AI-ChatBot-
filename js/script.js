document.getElementById('current-year').textContent = new Date().getFullYear();

document.addEventListener('DOMContentLoaded', () => {
    // Backend base URL. The page is served from http-server (port 5500),
    // the API runs under uvicorn (port 8000).
    const API_BASE = 'http://localhost:8000';

    const chatToggle = document.getElementById('chat-toggle');
    const chatWindow = document.getElementById('chat-window');
    const chatClose = document.getElementById('chat-close');
    const userInput = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');
    const chatMessages = document.getElementById('chat-messages');
    const questionChips = document.querySelectorAll('.question-chip');
    const submitTicketBtn = document.getElementById('submit-ticket-btn');
    const ticketModal = document.getElementById('ticket-modal');
    const ticketModalClose = document.getElementById('ticket-modal-close');
    const ticketForm = document.getElementById('ticket-form');
    const ticketStatus = document.getElementById('ticket-status');
    const ticketSubmitButton = ticketForm.querySelector('.modal-submit-btn');

    let chatOpen = false;

    // Server-issued conversation id, kept only in memory for this tab so the
    // backend can stitch follow-up turns together.
    let conversationId = null;

    function announceStatus(message) {
        const announcer = document.getElementById('aria-announcer') || document.createElement('div');
        announcer.id = 'aria-announcer';
        announcer.setAttribute('aria-live', 'polite');
        announcer.setAttribute('aria-atomic', 'true');
        announcer.className = 'visually-hidden';
        announcer.textContent = message;
        document.body.appendChild(announcer);
        setTimeout(() => {
            announcer.textContent = '';
        }, 1000);
    }

    function toggleChat() {
        chatOpen = !chatOpen;
        chatToggle.setAttribute('aria-expanded', String(chatOpen));

        if (chatOpen) {
            chatWindow.classList.add('visible');
            userInput.focus();
            announceStatus('Chat assistant is open.');
        } else {
            chatWindow.classList.remove('visible');
            chatToggle.focus();
            announceStatus('Chat assistant is closed.');
        }
    }

    function closeChat() {
        if (!chatOpen) return;
        chatOpen = false;
        chatToggle.setAttribute('aria-expanded', 'false');
        chatWindow.classList.remove('visible');
        chatToggle.focus();
        announceStatus('Chat assistant is closed.');
    }

    function formatTime() {
        const now = new Date();
        return now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }

    // ---------- Safe DOM rendering ----------
    // Builds the message bubble using textContent / createElement so anything
    // the user types (or the model echoes back) cannot inject HTML.

    function appendBubble(row, paragraphs, sources) {
        const bubble = document.createElement('div');
        bubble.className = row.classList.contains('user-row') ? 'message user-message' : 'message bot-message';

        paragraphs.forEach(text => {
            const p = document.createElement('p');
            p.textContent = text;
            bubble.appendChild(p);
        });

        if (sources && sources.length) {
            const srcWrap = document.createElement('div');
            srcWrap.className = 'message-sources';

            const label = document.createElement('span');
            label.textContent = 'Sources: ';
            srcWrap.appendChild(label);

            sources.forEach((src, idx) => {
                const a = document.createElement('a');
                a.href = src.url || '#';
                a.target = '_blank';
                a.rel = 'noopener noreferrer';
                a.className = 'chat-link';
                a.textContent = src.title || 'NHS Scotland';
                srcWrap.appendChild(a);
                if (idx < sources.length - 1) {
                    srcWrap.appendChild(document.createTextNode(', '));
                }
            });

            bubble.appendChild(srcWrap);
        }

        const time = document.createElement('div');
        time.className = 'message-time';
        time.textContent = formatTime();
        bubble.appendChild(time);

        row.appendChild(bubble);
    }

    function addUserMessage(text) {
        const row = document.createElement('div');
        row.className = 'message-row user-row new-message';
        appendBubble(row, [text], null);
        chatMessages.appendChild(row);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        setTimeout(() => row.classList.remove('new-message'), 300);
    }

    function addBotMessage(text, sources = []) {
        const row = document.createElement('div');
        row.className = 'message-row bot-row new-message';

        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.setAttribute('aria-hidden', 'true');
        const avatarSpan = document.createElement('span');
        avatarSpan.textContent = 'NHS';
        avatar.appendChild(avatarSpan);
        row.appendChild(avatar);

        // Split the model output into paragraphs on blank lines so longer
        // structured answers stay readable.
        const paragraphs = String(text)
            .split(/\n{2,}/)
            .map(p => p.replace(/\n+/g, ' ').trim())
            .filter(Boolean);

        appendBubble(row, paragraphs.length ? paragraphs : [String(text)], sources);

        chatMessages.appendChild(row);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        setTimeout(() => row.classList.remove('new-message'), 300);
    }

    function showTypingIndicator() {
        const row = document.createElement('div');
        row.className = 'message-row bot-row loading-message';
        row.id = 'typing-indicator';

        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.setAttribute('aria-hidden', 'true');
        const avatarSpan = document.createElement('span');
        avatarSpan.textContent = 'NHS';
        avatar.appendChild(avatarSpan);

        const bubble = document.createElement('div');
        bubble.className = 'message bot-message';
        bubble.innerHTML = `
            <div class="typing-dots" aria-label="Assistant is typing">
                <span></span><span></span><span></span>
            </div>
        `;

        row.appendChild(avatar);
        row.appendChild(bubble);
        chatMessages.appendChild(row);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        return row;
    }

    // ---------- Backend call ----------

    async function sendToBackend(message) {
        const body = { message };
        if (conversationId) body.conversation_id = conversationId;

        const response = await fetch(`${API_BASE}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
        });

        if (!response.ok) {
            const detail = await response.text().catch(() => '');
            throw new Error(`Server returned ${response.status}: ${detail}`);
        }

        return response.json();
    }

    async function handleSend(prefilledText = '') {
        const text = (prefilledText || userInput.value).trim();
        if (!text) return;

        addUserMessage(text);
        userInput.value = '';
        sendBtn.disabled = true;

        const typingIndicator = showTypingIndicator();

        try {
            const data = await sendToBackend(text);
            if (data && data.conversation_id) {
                conversationId = data.conversation_id;
            }
            typingIndicator.remove();
            addBotMessage(data.reply || 'No reply received.', data.sources || []);
        } catch (err) {
            console.error('[chat] backend error:', err);
            typingIndicator.remove();
            addBotMessage(
                "I'm having trouble reaching the assistant right now. Please make sure the backend is running on port 8000 and try again.",
                []
            );
        } finally {
            sendBtn.disabled = false;
            userInput.focus();
        }
    }

    // ---------- Ticket modal (still simulated, JIRA wiring TBD) ----------

    function openModal() {
        ticketModal.classList.add('visible');
        ticketModal.setAttribute('aria-hidden', 'false');
        document.getElementById('ticket-name').focus();
    }

    function closeModal() {
        ticketModal.classList.remove('visible');
        ticketModal.setAttribute('aria-hidden', 'true');
        submitTicketBtn.focus();
    }

    chatToggle.addEventListener('click', toggleChat);
    chatClose.addEventListener('click', closeChat);
    sendBtn.addEventListener('click', () => handleSend());
    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handleSend();
    });

    questionChips.forEach(chip => {
        chip.addEventListener('click', () => {
            if (!chatOpen) {
                chatOpen = true;
                chatToggle.setAttribute('aria-expanded', 'true');
                chatWindow.classList.add('visible');
            }
            handleSend(chip.textContent);
        });
    });

    submitTicketBtn.addEventListener('click', openModal);
    ticketModalClose.addEventListener('click', closeModal);

    ticketForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const name = document.getElementById('ticket-name').value.trim();
        const email = document.getElementById('ticket-email').value.trim();
        const issueType = document.getElementById('ticket-issue-type').value;
        const priority = document.getElementById('ticket-priority').value;
        const subject = document.getElementById('ticket-subject').value.trim();
        const description = document.getElementById('ticket-details').value.trim();
        const consent = document.getElementById('ticket-consent').checked;
        const attachmentInput = document.getElementById('ticket-attachment');
        const attachment = attachmentInput.files[0] || null;

        ticketStatus.className = 'ticket-status';
        ticketStatus.textContent = '';

        const emailValid = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);

        if (!name || !email || !issueType || !subject || !description) {
            ticketStatus.textContent = 'Please complete all required fields.';
            return;
        }

        if (!emailValid) {
            ticketStatus.textContent = 'Please enter a valid email address.';
            return;
        }

        if (description.length < 10) {
            ticketStatus.textContent = 'Please add a little more detail to your request.';
            return;
        }

        if (!consent) {
            ticketStatus.textContent = 'Please confirm the details before submitting.';
            return;
        }

        const payload = {
            name,
            email,
            issueType,
            priority,
            subject,
            description,
            source: 'NHS Careers Chatbot Frontend',
            attachment: attachment ? {
                filename: attachment.name,
                size: attachment.size,
                type: attachment.type || 'application/octet-stream'
            } : null
        };

        ticketSubmitButton.disabled = true;
        ticketStatus.className = 'ticket-status loading';
        ticketStatus.textContent = 'Submitting ticket...';

        try {
            const response = await fetch(`${API_BASE}/api/jira-ticket`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });

            // Backend returns either { success, ticketKey, url, message }
            // on 200, or { detail: "..." } on 4xx/5xx.
            const result = await response.json().catch(() => ({}));

            if (!response.ok || !result.success) {
                const reason = result.detail || result.message || `Server returned ${response.status}`;
                throw new Error(reason);
            }

            const refLink = result.url
                ? `<a href="${result.url}" target="_blank" rel="noopener noreferrer">${result.ticketKey}</a>`
                : result.ticketKey;

            ticketStatus.className = 'ticket-status success';
            ticketStatus.innerHTML = `Ticket submitted successfully. Reference: ${refLink}`;

            setTimeout(() => {
                closeModal();
                if (!chatOpen) {
                    chatOpen = true;
                    chatToggle.setAttribute('aria-expanded', 'true');
                    chatWindow.classList.add('visible');
                }
                addBotMessage(
                    `Your support ticket has been submitted successfully. Reference: ${result.ticketKey}. A member of the team will review your details shortly.`
                );
                ticketForm.reset();
                ticketStatus.className = 'ticket-status';
                ticketStatus.textContent = '';
            }, 1200);
        } catch (error) {
            ticketStatus.className = 'ticket-status';
            ticketStatus.textContent = `Unable to submit the ticket: ${error.message}`;
            console.error('[ticket]', error, payload);
        } finally {
            ticketSubmitButton.disabled = false;
        }
    });

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            if (ticketModal.classList.contains('visible')) {
                closeModal();
            } else if (chatOpen) {
                closeChat();
            }
        }
    });

    document.addEventListener('click', (e) => {
        if (chatOpen && !chatWindow.contains(e.target) && !chatToggle.contains(e.target) && !ticketModal.contains(e.target)) {
            closeChat();
        }

        if (e.target === ticketModal) {
            closeModal();
        }
    });

    setTimeout(() => {
        announceStatus('Page loaded. Use the chat button to open the assistant.');
    }, 1000);
});
