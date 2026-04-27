document.getElementById('current-year').textContent = new Date().getFullYear();

document.addEventListener('DOMContentLoaded', () => {
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

    const replies = [
        {
            match: ['nursing', 'nurse'],
            html: 'To apply for nursing roles, you would usually need relevant qualifications, registration requirements and an application through NHS Scotland Jobs. <a href="#" class="chat-link" target="_blank" rel="noopener noreferrer">More information</a>'
        },
        {
            match: ['qualification', 'qualifications', 'requirements'],
            html: 'Entry requirements vary by role, but many healthcare careers ask for specific qualifications, relevant experience and right-to-work checks. <a href="#" class="chat-link" target="_blank" rel="noopener noreferrer">View entry requirements</a>'
        },
        {
            match: ['salary', 'band 5', 'pay'],
            html: 'Band 5 roles are commonly used for newly qualified professional posts. Salary depends on the role and current pay banding. <a href="#" class="chat-link" target="_blank" rel="noopener noreferrer">See salary information</a>'
        },
        {
            match: ['apprenticeship', 'apprenticeships'],
            html: 'Apprenticeships can be a good route into NHS Scotland careers. They combine practical work with structured learning and may be available in clinical, business and support roles. <a href="#" class="chat-link" target="_blank" rel="noopener noreferrer">Explore apprenticeships</a>'
        }
    ];

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

    function addMessage(content, isUser = false, isHtml = false) {
        const row = document.createElement('div');
        row.className = `message-row ${isUser ? 'user-row' : 'bot-row'} new-message`;

        if (!isUser) {
            const avatar = document.createElement('div');
            avatar.className = 'message-avatar';
            avatar.setAttribute('aria-hidden', 'true');
            avatar.innerHTML = '<span>NHS</span>';
            row.appendChild(avatar);
        }

        const bubble = document.createElement('div');
        bubble.className = `message ${isUser ? 'user-message' : 'bot-message'}`;
        if (isHtml) {
            bubble.innerHTML = `<p>${content}</p><div class="message-time">${formatTime()}</div>`;
        } else {
            bubble.innerHTML = `<p>${content}</p><div class="message-time">${formatTime()}</div>`;
        }
        row.appendChild(bubble);

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
        avatar.innerHTML = '<span>NHS</span>';

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

    function getReply(text) {
        const lowerText = text.toLowerCase();
        const found = replies.find(reply => reply.match.some(keyword => lowerText.includes(keyword)));

        if (found) return found.html;

        return 'Thank you for your question. I can help with NHS Scotland careers, applications, qualifications, salaries and training pathways. <a href="#" class="chat-link" target="_blank" rel="noopener noreferrer">More information</a>';
    }

    function handleSend(prefilledText = '') {
        const text = (prefilledText || userInput.value).trim();
        if (!text) return;

        addMessage(text, true);
        userInput.value = '';

        const typingIndicator = showTypingIndicator();

        setTimeout(() => {
            typingIndicator.remove();
            addMessage(getReply(text), false, true);
        }, 1100);
    }

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
            // Replace this endpoint when backend is ready.
            // const response = await fetch('/api/jira-ticket', {
            //     method: 'POST',
            //     headers: { 'Content-Type': 'application/json' },
            //     body: JSON.stringify(payload)
            // });
            // const result = await response.json();

            await new Promise(resolve => setTimeout(resolve, 900));
            const result = { success: true, ticketKey: 'NHS-123' };

            if (!result.success) {
                throw new Error('Ticket submission failed');
            }

            ticketStatus.className = 'ticket-status success';
            ticketStatus.textContent = `Ticket submitted successfully. Reference: ${result.ticketKey}`;

            setTimeout(() => {
                closeModal();
                if (!chatOpen) {
                    chatOpen = true;
                    chatToggle.setAttribute('aria-expanded', 'true');
                    chatWindow.classList.add('visible');
                }
                addMessage(`Your support ticket has been submitted successfully. Reference: ${result.ticketKey}. A member of the team will review your details shortly.`, false);
                ticketForm.reset();
                ticketStatus.className = 'ticket-status';
                ticketStatus.textContent = '';
            }, 800);
        } catch (error) {
            ticketStatus.className = 'ticket-status';
            ticketStatus.textContent = 'Unable to submit the ticket right now. Please try again.';
            console.error(error, payload);
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
