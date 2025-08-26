import { createClient } from 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js/+esm';

// Get Supabase credentials from environment or window object
const SUPABASE_URL = window.SUPABASE_URL || 'https://bzqorlixwebkvrtuksie.supabase.co';
const SUPABASE_ANON_KEY = window.SUPABASE_ANON_KEY || "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJ6cW9ybGl4d2Via3ZydHVrc2llIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTYwMDU1NDIsImV4cCI6MjA3MTU4MTU0Mn0.y5HN_ewfI2FRYM7ZlGS55nlYsoFMpSIjcTWaGLwzil0";

const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

const chatWindow = document.getElementById('chat-window');
const chatForm = document.getElementById('chat-form');
const messageInput = document.getElementById('message-input');
const logoutButton = document.getElementById('logout-button');
const emojiButton = document.getElementById('emoji-button');
const emojiPicker = document.getElementById('emoji-picker');

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
        addMessage('assistant', 'Hey there! I\'m Daddy John. Can you introduce and tell about yourself first?');
        
    } catch (error) {
        console.error('Error fetching history:', error);
        addMessage('assistant', 'Sorry, I couldn\'t load our past chats.');
    }
}

// --- Emoji Picker Setup ---
const EMOJIS = [
  '😀','😁','😂','🤣','😊','😍','😘','😎','🤩','🥳',
  '🤔','🙃','🙂','😉','🤗','😇','🤝','👍','👎','🙏',
  '🔥','✨','💯','🎉','🥰','😌','🤤','🤠','😴','🤒',
  '😢','😭','😤','😡','🤬','🤯','😱','🙌','👏','🤝'
];

// Recent emojis helpers
const RECENT_KEY = 'dj_recent_emojis_v1';
function getRecentEmojis() {
  try {
    const raw = localStorage.getItem(RECENT_KEY);
    const arr = raw ? JSON.parse(raw) : [];
    return Array.isArray(arr) ? arr.slice(0, 8) : [];
  } catch { return []; }
}
function saveRecentEmojis(arr) {
  try { localStorage.setItem(RECENT_KEY, JSON.stringify(arr.slice(0, 8))); } catch {}
}
function addToRecentEmojis(e) {
  const curr = getRecentEmojis();
  const filtered = [e, ...curr.filter(x => x !== e)].slice(0, 8);
  saveRecentEmojis(filtered);
}

function buildEmojiPicker() {
  if (!emojiPicker) return;
  if (emojiPicker.dataset.built === 'true') return;
  emojiPicker.dataset.built = 'true';
  emojiPicker.setAttribute('role', 'listbox');
  emojiPicker.setAttribute('aria-label', 'Emoji picker');
  emojiPicker.style.position = 'absolute';
  emojiPicker.style.background = '#fff';
  emojiPicker.style.border = '1px solid #ddd';
  emojiPicker.style.borderRadius = '8px';
  emojiPicker.style.padding = '8px';
  emojiPicker.style.boxShadow = '0 6px 18px rgba(0,0,0,0.12)';
  emojiPicker.style.maxWidth = '280px';
  emojiPicker.style.display = 'none';
  emojiPicker.style.zIndex = '1000';
  emojiPicker.style.userSelect = 'none';
  emojiPicker.style.maxHeight = '220px';
  emojiPicker.style.overflowY = 'auto';

  // Recent row
  const recentWrap = document.createElement('div');
  recentWrap.style.display = 'flex';
  recentWrap.style.flexWrap = 'wrap';
  recentWrap.style.gap = '8px';
  recentWrap.style.marginBottom = '6px';
  recentWrap.setAttribute('data-recent', 'true');
  emojiPicker.appendChild(recentWrap);

  const hr = document.createElement('div');
  hr.style.height = '1px';
  hr.style.background = '#eee';
  hr.style.margin = '6px 0';
  emojiPicker.appendChild(hr);

  const grid = document.createElement('div');
  grid.style.display = 'grid';
  grid.style.gridTemplateColumns = 'repeat(12, 28px)';
  grid.style.gridAutoRows = '28px';
  grid.style.gap = '6px';

  EMOJIS.forEach((e) => {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.textContent = e;
    btn.setAttribute('aria-label', `Insert ${e}`);
    btn.style.fontSize = '18px';
    btn.style.lineHeight = '1';
    btn.style.padding = '0';
    btn.style.width = '28px';
    btn.style.height = '28px';
    btn.style.display = 'inline-flex';
    btn.style.alignItems = 'center';
    btn.style.justifyContent = 'center';
    btn.style.cursor = 'pointer';
    btn.style.border = '1px solid transparent';
    btn.style.background = 'transparent';
    btn.style.borderRadius = '6px';
    btn.addEventListener('click', () => {
      insertAtCursor(messageInput, e);
      messageInput.focus();
      addToRecentEmojis(e);
      renderRecentEmojis();
    });
    grid.appendChild(btn);
  });

  emojiPicker.appendChild(grid);
  renderRecentEmojis();
}

function toggleEmojiPicker() {
  if (!emojiPicker || !emojiButton) return;
  buildEmojiPicker();
  const isHidden = emojiPicker.style.display === 'none' || !emojiPicker.style.display;
  if (isHidden) {
    // Show to measure exact size
    emojiPicker.style.visibility = 'hidden';
    emojiPicker.style.display = 'block';
    // Ensure picker width fits 12 columns
    // Let content define width; we'll clamp horizontally
    const container = emojiButton.offsetParent || document.body;
    const containerWidth = container.clientWidth || window.innerWidth;
    const pickerW = emojiPicker.offsetWidth;
    const pickerH = emojiPicker.offsetHeight;

    // Always open upward: bottom edge aligns with button top
    const desiredTop = emojiButton.offsetTop - pickerH - 8;
    let left = emojiButton.offsetLeft; // default left aligned to button
    // Clamp horizontally within container
    if (left + pickerW > containerWidth - 8) {
      left = Math.max(8, containerWidth - pickerW - 8);
    }
    if (left < 8) left = 8;

    emojiPicker.style.top = `${Math.max(0, desiredTop)}px`;
    emojiPicker.style.left = `${left}px`;
    emojiPicker.style.visibility = '';
    emojiPicker.style.display = 'block';
    emojiPicker.setAttribute('aria-hidden', 'false');
  } else {
    emojiPicker.style.display = 'none';
    emojiPicker.setAttribute('aria-hidden', 'true');
  }
}

function insertAtCursor(input, text) {
  if (!input) return;
  const start = input.selectionStart ?? input.value.length;
  const end = input.selectionEnd ?? input.value.length;
  const before = input.value.slice(0, start);
  const after = input.value.slice(end);
  // Enforce maxlength without changing existing validation logic
  const maxLen = parseInt(input.getAttribute('maxlength') || '1000', 10);
  const currentLen = (before + after).length;
  const remaining = maxLen - currentLen;
  const toInsert = text.slice(0, Math.max(0, remaining));
  input.value = before + toInsert + after;
  const pos = start + toInsert.length;
  input.setSelectionRange(pos, pos);
}

function renderRecentEmojis() {
  if (!emojiPicker) return;
  const recentWrap = emojiPicker.querySelector('[data-recent="true"]');
  if (!recentWrap) return;
  recentWrap.innerHTML = '';
  const recents = getRecentEmojis();
  if (!recents.length) return;
  recents.forEach((e) => {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.textContent = e;
    btn.style.fontSize = '18px';
    btn.style.padding = '0';
    btn.style.width = '28px';
    btn.style.height = '28px';
    btn.style.display = 'inline-flex';
    btn.style.alignItems = 'center';
    btn.style.justifyContent = 'center';
    btn.style.border = '1px solid transparent';
    btn.style.background = 'transparent';
    btn.style.borderRadius = '6px';
    btn.addEventListener('click', () => {
      insertAtCursor(messageInput, e);
      messageInput.focus();
      addToRecentEmojis(e);
      renderRecentEmojis();
    });
    recentWrap.appendChild(btn);
  });
}

// Toggle picker
if (emojiButton) {
  emojiButton.addEventListener('click', (e) => {
    e.preventDefault();
    e.stopPropagation();
    toggleEmojiPicker();
  });
}

// Hide picker when clicking outside
document.addEventListener('click', (e) => {
  if (!emojiPicker || emojiPicker.style.display === 'none') return;
  if (e.target === emojiPicker || emojiPicker.contains(e.target)) return;
  if (e.target === emojiButton) return;
  emojiPicker.style.display = 'none';
  emojiPicker.setAttribute('aria-hidden', 'true');
});

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
        if (emojiPicker) {
            emojiPicker.style.display = 'none';
            emojiPicker.setAttribute('aria-hidden', 'true');
        }
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