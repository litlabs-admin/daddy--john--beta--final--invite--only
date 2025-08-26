import { createClient } from 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js/+esm';

// Get Supabase credentials from environment or window object
const SUPABASE_URL = window.SUPABASE_URL || 'https://bzqorlixwebkvrtuksie.supabase.co';
const SUPABASE_ANON_KEY = window.SUPABASE_ANON_KEY || "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJ6cW9ybGl4d2Via3ZydHVrc2llIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTYwMDU1NDIsImV4cCI6MjA3MTU4MTU0Mn0.y5HN_ewfI2FRYM7ZlGS55nlYsoFMpSIjcTWaGLwzil0";

const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

const loginForm = document.getElementById('login-form');
const errorMessage = document.getElementById('error-message');

// Clear any previous error messages
function clearError() {
    if (errorMessage) {
        errorMessage.textContent = '';
    }
}

// Show error message
function showError(message) {
    if (errorMessage) {
        errorMessage.textContent = message;
    }
}

// Check if user is already logged in
(async () => {
    try {
        const token = localStorage.getItem('auth_token');
        if (token) {
            // Verify token is still valid by making a test request
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ message: 'test' })
            });
            
            if (response.status !== 401) {
                window.location.href = '/chat';
            } else {
                // Token is invalid, remove it
                localStorage.removeItem('auth_token');
                localStorage.removeItem('user_data');
            }
        }
    } catch (error) {
        console.error('Session check error:', error);
        localStorage.removeItem('auth_token');
        localStorage.removeItem('user_data');
    }
})();

// Validate email format
function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    clearError();
    
    const email = document.getElementById('login-email').value.trim();
    const password = document.getElementById('login-password').value;
    
    // Client-side validation
    if (!isValidEmail(email)) {
        showError('Please enter a valid email address.');
        return;
    }
    
    if (!password) {
        showError('Password is required.');
        return;
    }
    
    try {
        const response = await fetch('/api/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email, password })
        });

        const data = await response.json();

        if (!response.ok) {
            showError(data.error || 'Login failed. Please try again.');
        } else {
            // Store token and user data
            localStorage.setItem('auth_token', data.token);
            localStorage.setItem('user_data', JSON.stringify(data.user));
            window.location.href = '/chat';
        }
    } catch (error) {
        console.error('Login error:', error);
        showError('An unexpected error occurred. Please try again.');
    }
});