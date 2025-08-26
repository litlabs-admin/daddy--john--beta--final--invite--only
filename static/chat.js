import { createClient } from 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js/+esm';

// Get Supabase credentials from environment or window object
const SUPABASE_URL = window.SUPABASE_URL || 'https://bzqorlixwebkvrtuksie.supabase.co';
const SUPABASE_ANON_KEY = window.SUPABASE_ANON_KEY || "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJ6cW9ybGl4d2Via3ZydHVrc2llIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTYwMDU1NDIsImV4cCI6MjA3MTU4MTU0Mn0.y5HN_ewfI2FRYM7ZlGS55nlYsoFMpSIjcTWaGLwzil0";

const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

const chatWindow = document.getElementById('chat-window');
const chatForm = document.getElementById('chat-form');
const messageInput = document.getElementById('message-input');
const logoutButton = document.getElementById('logout-button');

// --- User Authentication and Session Check ---
let authToken = null;
let userData = null;

async function checkSession() {
    try {
        authToken = localStorage.getItem('auth_token');
        const userDataStr = localStorage.getItem('user_data');
        
        if (!authToken || !userDataStr) {
            console.error('No authentication token or user data found');
            window.location.href = '/'; // Redirect to login if not authenticated
            return;
        }
        
        userData = JSON.parse(userDataStr);
        
        // Verify token is still valid by fetching chat history
        await fetchChatHistory();
    } catch (error) {
        console.error('Session check failed:', error);
        localStorage.removeItem('auth_token');
        localStorage.removeItem('user_data');
        window.location.href = '/';
    }
}

// --- UI Helper Functions ---
function addMessage(role, content) {
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message', `${role}-message`);
    
    // Sanitize content to prevent XSS
    const sanitizedContent = content.replace(/[<>]/g, '');
    messageDiv.textContent = sanitizedContent;
    
    chatWindow.appendChild(messageDiv);
    chatWindow.scrollTop = chatWindow.scrollHeight; // Auto-scroll
}

function showTypingIndicator() {
    const typingDiv = document.createElement('div');
    typingDiv.classList.add('typing-indicator');
    typingDiv.id = 'typing-indicator';
    
    for (let i = 0; i < 3; i++) {
        const dot = document.createElement('div');
        dot.classList.add('typing-dot');
        typingDiv.appendChild(dot);
    }
    
    chatWindow.appendChild(typingDiv);
    chatWindow.scrollTop = chatWindow.scrollHeight;
}

function hideTypingIndicator() {
    const typingIndicator = document.getElementById('typing-indicator');
    if (typingIndicator) {
        typingIndicator.remove();
    }
}

async function fetchChatHistory() {
    try {
        // For now, we'll fetch messages through a test API call
        // In a full implementation, you might want a separate endpoint for chat history
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({ message: '' }) // Empty message to just get history
        });

        if (response.status === 401) {
            // Token is invalid
            localStorage.removeItem('auth_token');
            localStorage.removeItem('user_data');
            window.location.href = '/';
            return;
        }

        // For now, just show welcome message
        // In a full implementation, you'd fetch actual chat history from the database
        chatWindow.innerHTML = '';
        addMessage('assistant', 'Hey there! I\'m Daddy John. What\'s on your mind today?');
        
    } catch (error) {
        console.error('Error fetching history:', error);
        addMessage('assistant', 'Sorry, I couldn\'t load our past chats.');
    }
}

// --- Event Listeners ---
chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const message = messageInput.value.trim();
    if (!message) return;

    // Validate message length
    if (message.length > 1000) {
        alert('Message is too long. Please keep it under 1000 characters.');
        return;
    }

    addMessage('user', message);
    messageInput.value = '';
    messageInput.disabled = true;
    
    showTypingIndicator();

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({ message: message })
        });

        hideTypingIndicator();

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.error || `Server responded with status: ${response.status}`);
        }

        const data = await response.json();
        if (data.reply) {
            addMessage('assistant', data.reply);
        } else {
            throw new Error('Invalid response format');
        }

    } catch (error) {
        hideTypingIndicator();
        console.error('Error sending message:', error);
        
        let errorMessage = "Oh, crumbs. Something went wrong on my end, kiddo.";
        if (error.message.includes('401') || error.message.includes('unauthorized')) {
            errorMessage = "Your session has expired. Please log in again.";
            localStorage.removeItem('auth_token');
            localStorage.removeItem('user_data');
            setTimeout(() => window.location.href = '/', 2000);
        } else if (error.message.includes('503') || error.message.includes('unavailable')) {
            errorMessage = "I'm having trouble thinking right now. Give me a moment and try again.";
        }
        
        addMessage('assistant', errorMessage);
    } finally {
        messageInput.disabled = false;
        messageInput.focus();
    }
});

// Handle Enter key for sending messages
messageInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        chatForm.dispatchEvent(new Event('submit'));
    }
});

logoutButton.addEventListener('click', async () => {
    try {
        localStorage.removeItem('auth_token');
        localStorage.removeItem('user_data');
        window.location.href = '/';
    } catch (error) {
        console.error('Logout error:', error);
        // Force redirect even if logout fails
        window.location.href = '/';
    }
});

// --- Initial Load ---
checkSession();