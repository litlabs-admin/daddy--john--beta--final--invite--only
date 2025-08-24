import os
import time
import requests
import logging
from dotenv import load_dotenv
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from supabase import create_client, Client
import re

# --- Initialization ---
load_dotenv()

app = Flask(__name__, static_folder='static', template_folder='templates')

# Configure CORS for production
CORS(app, origins=["*"], methods=["GET", "POST"], allow_headers=["Content-Type", "Authorization"])

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Supabase with environment variables
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")

if not url or not key:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables")

supabase: Client = create_client(url, key)

# --- Helper Functions ---

def sanitize_input(text: str) -> str:
    """Sanitize user input to prevent injection attacks."""
    if not text or not isinstance(text, str):
        return ""
    
    # Remove potentially dangerous characters and limit length
    text = re.sub(r'[<>"\']', '', text.strip())
    return text[:1000]  # Limit message length

def get_user_from_token(auth_header):
    """Validates JWT and retrieves user from Supabase."""
    if not auth_header:
        return None, {"error": "Missing Authorization header"}
    
    try:
        if not auth_header.startswith("Bearer "):
            return None, {"error": "Invalid Authorization header format"}
            
        token = auth_header.split(" ")[1]
        if not token:
            return None, {"error": "Missing token"}
            
        user_response = supabase.auth.get_user(token)
        if not user_response.user:
            return None, {"error": "Invalid token"}
            
        return user_response.user, None
    except Exception as e:
        logger.error(f"Token validation error: {str(e)}")
        return None, {"error": "Invalid or expired token"}

def get_persona():
    """Reads the persona from the text file."""
    try:
        persona_path = os.path.join(os.path.dirname(__file__), 'persona.txt')
        with open(persona_path, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except FileNotFoundError:
        logger.warning("persona.txt not found, using fallback")
        return "You are a helpful assistant."
    except Exception as e:
        logger.error(f"Error reading persona: {str(e)}")
        return "You are a helpful assistant."

def make_openrouter_request(messages, timeout=25, max_retries=3):
    """Make a request to OpenRouter API with retry logic."""
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY not found in environment variables")
    
    for attempt in range(max_retries):
        try:
            response = requests.post(
                url="https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": os.environ.get("VERCEL_URL", "http://localhost:5000"),
                    "X-Title": "Daddy John Chatbot"
                },
                json={
                    "model": "mistralai/mistral-7b-instruct",
                    "messages": messages,
                    "max_tokens": 500,
                    "temperature": 0.7
                },
                timeout=timeout
            )
            response.raise_for_status()
            
            result = response.json()
            if 'choices' not in result or not result['choices']:
                raise ValueError("Invalid API response format")
                
            return result['choices'][0]['message']['content']
            
        except requests.exceptions.Timeout:
            logger.warning(f"OpenRouter API timeout on attempt {attempt + 1}")
            if attempt < max_retries - 1:
                time.sleep(1)
            else:
                raise
        except requests.exceptions.RequestException as e:
            logger.error(f"OpenRouter API error on attempt {attempt + 1}: {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(1)
            else:
                raise

def clean_ai_response(response_content):
    """Clean AI response to remove unwanted prefixes."""
    if not response_content:
        return "I'm sorry, I couldn't generate a response right now."
    
    # Remove common prefixes
    if ":" in response_content:
        parts = response_content.split(':', 1)
        if len(parts[0]) < 20 and "daddy john" in parts[0].lower():
            response_content = parts[1].strip()
    
    if response_content.startswith(':'):
        response_content = response_content[1:].strip()
    
    return response_content

# --- API Routes ---

@app.route('/api/chat', methods=['POST'])
def chat_handler():
    """Main endpoint to handle chat requests."""
    try:
        # Validate user authentication
        user, error = get_user_from_token(request.headers.get("Authorization"))
        if error:
            return jsonify(error), 401
        
        user_id = user.id
        
        # Validate and sanitize input
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON data"}), 400
            
        user_message = sanitize_input(data.get("message", ""))
        if not user_message:
            return jsonify({"error": "Message is required and cannot be empty"}), 400

        # Store user message
        try:
            supabase.table('messages').insert({
                "user_id": user_id,
                "role": "user",
                "content": user_message
            }).execute()
        except Exception as e:
            logger.error(f"Database error storing user message: {str(e)}")
            return jsonify({"error": "Failed to store message"}), 500
        
        # Get chat history and summary
        try:
            messages_res = supabase.table('messages').select('role, content').eq('user_id', user_id).order('created_at', desc=True).limit(20).execute()
            chat_history = list(reversed(messages_res.data))
            
            summary_res = supabase.table('summaries').select('summary_text').eq('user_id', user_id).order('created_at', desc=True).limit(1).execute()
            latest_summary = summary_res.data[0]['summary_text'] if summary_res.data else ""
        except Exception as e:
            logger.error(f"Database error fetching history: {str(e)}")
            return jsonify({"error": "Failed to fetch chat history"}), 500

        # Prepare AI prompt
        system_prompt = get_persona()
        context_prompt = f"BACKGROUND CONTEXT (use this for memory but prioritize the user's last message):\n{latest_summary}\n\n---\n\nCURRENT CONVERSATION:" if latest_summary else "CURRENT CONVERSATION:"

        prompt_messages = [
            {"role": "system", "content": system_prompt},
            {"role": "system", "content": context_prompt}
        ]
        prompt_messages.extend(chat_history)
        
        # Get AI response
        try:
            ai_response_content = make_openrouter_request(prompt_messages)
            ai_response_content = clean_ai_response(ai_response_content)
        except Exception as e:
            logger.error(f"AI API error: {str(e)}")
            return jsonify({"error": "AI service is currently unavailable. Please try again later."}), 503

        # Store AI response
        try:
            supabase.table('messages').insert({
                "user_id": user_id,
                "role": "assistant",
                "content": ai_response_content
            }).execute()
        except Exception as e:
            logger.error(f"Database error storing AI response: {str(e)}")
            # Still return the response even if storage fails
            pass

        # Check if summarization is needed (simplified without threading)
        try:
            total_messages = len(chat_history) + 1  # +1 for the new message
            if total_messages > 0 and total_messages % 20 == 0:
                logger.info(f"Triggering summarization for user {user_id}")
                summarize_conversation_sync(user_id, chat_history)
        except Exception as e:
            logger.error(f"Summarization error: {str(e)}")
            # Don't fail the main request if summarization fails

        return jsonify({"reply": ai_response_content})
        
    except Exception as e:
        logger.error(f"Unexpected error in chat_handler: {str(e)}")
        return jsonify({"error": "An unexpected error occurred"}), 500

def summarize_conversation_sync(user_id, history):
    """Generates and stores a summary of the conversation synchronously."""
    try:
        if not history:
            return
            
        summary_prompt = "Summarize the key points of this conversation in 1-2 sentences. Focus on the user's main concerns, emotional state, and any important context that should be remembered for future conversations."
        messages_for_summary = [{"role": m["role"], "content": m["content"]} for m in history[-10:]]  # Use last 10 messages
        messages_for_summary.insert(0, {"role": "system", "content": summary_prompt})

        summary_text = make_openrouter_request(messages_for_summary, timeout=30)
        
        if summary_text:
            supabase.table('summaries').insert({
                "user_id": user_id, 
                "summary_text": summary_text
            }).execute()
            logger.info(f"Successfully stored summary for user {user_id}")

    except Exception as e:
        logger.error(f"Summary generation error: {str(e)}")

# --- Frontend Routes ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat')
def chat():
    return render_template('chat.html')

@app.route('/health')
def health_check():
    """Health check endpoint for monitoring."""
    return jsonify({"status": "healthy", "timestamp": time.time()})

# --- Error Handlers ---
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    # Only run in debug mode locally
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=debug_mode)