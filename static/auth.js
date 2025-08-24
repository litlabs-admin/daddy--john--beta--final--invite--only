import { createClient } from 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js/+esm';

// Get Supabase credentials from environment or window object
const SUPABASE_URL = window.SUPABASE_URL || 'https://bzqorlixwebkvrtuksie.supabase.co';
const SUPABASE_ANON_KEY = window.SUPABASE_ANON_KEY || "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJ6cW9ybGl4d2Via3ZydHVrc2llIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTYwMDU1NDIsImV4cCI6MjA3MTU4MTU0Mn0.y5HN_ewfI2FRYM7ZlGS55nlYsoFMpSIjcTWaGLwzil0";

const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

const loginForm = document.getElementById('login-form');
const signupForm = document.getElementById('signup-form');
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

// Redirect if user is already logged in
(async () => {
    try {
        const { data: { session } } = await supabase.auth.getSession();
        if (session) {
            window.location.href = '/chat';
        }
    } catch (error) {
        console.error('Session check error:', error);
    }
})();

// Validate email format
function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

// Validate password strength
function isValidPassword(password) {
    return password && password.length >= 6;
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
        const { error } = await supabase.auth.signInWithPassword({ email, password });

        if (error) {
            showError(error.message);
        } else {
            window.location.href = '/chat';
        }
    } catch (error) {
        console.error('Login error:', error);
        showError('An unexpected error occurred. Please try again.');
    }
});

signupForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    clearError();
    
    const email = document.getElementById('signup-email').value.trim();
    const password = document.getElementById('signup-password').value;

    // Client-side validation
    if (!isValidEmail(email)) {
        showError('Please enter a valid email address.');
        return;
    }
    
    if (!isValidPassword(password)) {
        showError('Password must be at least 6 characters long.');
        return;
    }

    try {
        const { error } = await supabase.auth.signUp({ email, password });

        if (error) {
            showError(error.message);
        } else {
            alert('Signup successful! Please check your email to verify your account.');
            // Clear the form
            signupForm.reset();
        }
    } catch (error) {
        console.error('Signup error:', error);
        showError('An unexpected error occurred. Please try again.');
    }
});