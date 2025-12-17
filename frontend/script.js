// Configuration
const API_BASE_URL = 'http://127.0.0.1:8000/api/v1'; // Use IP to avoid localhost IPv6 issues
let sessionId = generateSessionId();
let messageCount = 0;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
    checkConnection();
});

function initializeApp() {
    // Set session ID
    document.getElementById('sessionId').textContent = sessionId.substring(0, 8);

    // Add welcome message
    addWelcomeMessage();
}

async function checkConnection() {
    const statusDot = document.querySelector('.status-dot');
    const statusText = document.querySelector('.status-indicator span:last-child');

    try {
        const response = await fetch(`${API_BASE_URL.replace('/api/v1', '')}/health`);
        if (response.ok) {
            statusDot.style.backgroundColor = '#10b981'; // Green
            statusText.textContent = 'Connected';
        } else {
            throw new Error('Health check failed');
        }
    } catch (error) {
        console.error('Connection check failed:', error);
        statusDot.style.backgroundColor = '#ef4444'; // Red
        statusText.textContent = 'Disconnected (Check Backend)';
        // Optional: Add a system message about connection
        addMessage('system', '⚠️ Could not connect to the server. Please ensure the backend is running.');
    }
}

function generateSessionId() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
        const r = Math.random() * 16 | 0;
        const v = c === 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}

function addWelcomeMessage() {
    const welcomeMessage = `👋 Welcome to Carrivo Assistant!
I'm here to listen to you, analyze your personality, and recommend the best career path for you.
Then I'll provide you with a clear roadmap and simple explanations to help you start your journey with confidence 🚀.   `;

    addMessage('assistant', welcomeMessage);
}

function addMessage(role, content) {
    const messagesContainer = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message message-${role}`;

    const now = new Date();
    const timeString = now.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit'
    });

    const contentHtml = role === 'system' ? `<em>${content}</em>` : formatMessage(content);

    // Avatar HTML
    const avatarHtml = `
        <div class="avatar">
            <img src="assets/${role === 'user' ? 'user_avatar.png' : 'bot_avatar.png'}" alt="${role}">
        </div>
    `;

    messageDiv.innerHTML = `
        ${role === 'assistant' ? avatarHtml : ''}
        <div class="message-bubble ${role === 'system' ? 'system-bubble' : ''}">
            <div class="message-content">${contentHtml}</div>
            <span class="message-time">${timeString}</span>
        </div>
        ${role === 'user' ? avatarHtml : ''}
    `;

    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;

    if (role !== 'system') {
        messageCount++;
        // updateMessageCount(); // Msg count element removed or hidden in new design
    }
}

function formatMessage(text) {
    if (!text) return "";

    // Auto-link URLs (excluding trailing punctuation)
    const urlRegex = /(https?:\/\/[^\s<]+)/g;
    text = text.replace(urlRegex, function (url) {
        // Remove trailing punctuation like , . ! ? )
        const trailing = url.match(/[.,;!?)]+$/);
        let suffix = '';
        if (trailing) {
            suffix = trailing[0];
            url = url.substring(0, url.length - suffix.length);
        }
        return '<a href="' + url + '" target="_blank" class="chat-link">' + url + '</a>' + suffix;
    });

    // Convert markdown-like formatting
    text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    text = text.replace(/`([^`]+)`/g, '<code>$1</code>');
    text = text.replace(/\n/g, '<br>');

    return text;
}

function updateMessageCount() {
    document.getElementById('messageCount').textContent = messageCount;
}

async function sendMessage(event) {
    event.preventDefault();

    const input = document.getElementById('messageInput');
    const message = input.value.trim();

    if (!message) return;

    // Add user message
    addMessage('user', message);
    input.value = '';

    // Show loading
    showLoading();

    try {
        // Send to API
        console.log("Sending request to:", `${API_BASE_URL}/chat`);
        const response = await fetch(`${API_BASE_URL}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                session_id: sessionId,
                language: "auto" // Auto-detect
            })
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`Server Error: ${response.status} - ${errorText}`);
        }

        const data = await response.json();

        // Add assistant response
        addMessage('assistant', data.response);

    } catch (error) {
        console.error('Error:', error);
        addMessage('assistant', `🚫 Connection Error: ${error.message}. Please check if the backend is running.`);
    } finally {
        hideLoading();
    }
}

function clearChat() {
    const messagesContainer = document.getElementById('chatMessages');
    messagesContainer.innerHTML = '';
    messageCount = 0;
    updateMessageCount();
    addWelcomeMessage();
}

function showLoading() {
    document.getElementById('loadingOverlay').classList.add('active');
    document.getElementById('sendButton').disabled = true;
}

function hideLoading() {
    document.getElementById('loadingOverlay').classList.remove('active');
    document.getElementById('sendButton').disabled = false;
}

// Keyboard shortcuts
document.addEventListener('keydown', (e) => {
    // Ctrl/Cmd + K to focus input
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        document.getElementById('messageInput').focus();
    }
});
