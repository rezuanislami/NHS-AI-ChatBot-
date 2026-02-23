// Set current year in footer
document.getElementById('current-year').textContent = new Date().getFullYear();

document.addEventListener('DOMContentLoaded', () => {

    const API_URL = "http://localhost:8000/chat"; // Change when deployed

    const chatToggle = document.getElementById('chat-toggle');
    const chatWindow = document.getElementById('chat-window');
    const chatClose = document.getElementById('chat-close');
    const userInput = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');
    const chatMessages = document.getElementById('chat-messages');

    let chatOpen = false;

    // --------------------------
    // OPEN / CLOSE CHAT
    // --------------------------

    function toggleChat() {
        chatOpen = !chatOpen;
        chatToggle.setAttribute('aria-expanded', chatOpen);

        if (chatOpen) {
            chatWindow.classList.add('visible');
            userInput.focus();
            announceStatus('Chat assistant is now open.');
        } else {
            chatWindow.classList.remove('visible');
            chatToggle.focus();
            announceStatus('Chat assistant is now closed.');
        }
    }

    function closeChat() {
        if (!chatOpen) return;
        chatOpen = false;
        chatToggle.setAttribute('aria-expanded', 'false');
        chatWindow.classList.remove('visible');
        chatToggle.focus();
        announceStatus('Chat assistant is now closed.');
    }

    // --------------------------
    // MESSAGE RENDERING
    // --------------------------

    function addMessage(text, isUser = false) {
        const now = new Date();
        const timeString =
            now.getHours() + ':' + now.getMinutes().toString().padStart(2, '0');

        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${isUser ? 'user-message' : 'bot-message'}`;

        messageDiv.innerHTML = `
            <p>${text}</p>
            <div class="message-time">${timeString}</div>
        `;

        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function showTypingIndicator() {
        const typingDiv = document.createElement('div');
        typingDiv.className = 'message bot-message';
        typingDiv.id = 'typing-indicator';
        typingDiv.innerHTML = `<p>Typing...</p>`;
        chatMessages.appendChild(typingDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function removeTypingIndicator() {
        const typingDiv = document.getElementById('typing-indicator');
        if (typingDiv) typingDiv.remove();
    }

    // --------------------------
    // API CALL
    // --------------------------

    async function sendToAPI(message) {
        try {
            const response = await fetch(API_URL, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ message })
            });

            if (!response.ok) {
                throw new Error("API error");
            }

            const data = await response.json();
            return data.reply;

        } catch (error) {
            console.error("API Error:", error);
            return "Sorry, something went wrong. Please try again later.";
        }
    }

    // --------------------------
    // SEND HANDLER
    // --------------------------

    async function handleSend() {
        const text = userInput.value.trim();
        if (!text) return;

        addMessage(text, true);
        userInput.value = '';

        showTypingIndicator();

        const reply = await sendToAPI(text);

        removeTypingIndicator();
        addMessage(reply, false);
    }

    // --------------------------
    // ACCESSIBILITY
    // --------------------------

    function announceStatus(message) {
        const announcer = document.getElementById('aria-announcer') || document.createElement('div');
        announcer.id = 'aria-announcer';
        announcer.setAttribute('aria-live', 'polite');
        announcer.setAttribute('aria-atomic', 'true');
        announcer.className = 'visually-hidden';
        announcer.textContent = message;
        document.body.appendChild(announcer);

        setTimeout(() => { announcer.textContent = ''; }, 1000);
    }

    // --------------------------
    // EVENT LISTENERS
    // --------------------------

    chatToggle.addEventListener('click', toggleChat);
    chatClose.addEventListener('click', closeChat);
    sendBtn.addEventListener('click', handleSend);

    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handleSend();
    });

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && chatOpen) closeChat();
    });

    document.addEventListener('click', (e) => {
        if (chatOpen && !chatWindow.contains(e.target) && !chatToggle.contains(e.target)) {
            closeChat();
        }
    });

});