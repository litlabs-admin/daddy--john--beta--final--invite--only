import os
import time
import requests
import logging
import bcrypt
import jwt
from datetime import datetime, timedelta
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

# Initialize Supabase with environment variables (for database only, not auth)
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")

if not url or not key:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables")

supabase: Client = create_client(url, key)

# JWT Secret Key
JWT_SECRET = os.environ.get("JWT_SECRET_KEY", "your-secret-key-change-this-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# --- Helper Functions ---

def sanitize_input(text: str) -> str:
    """Sanitize user input to prevent injection attacks."""
    if not text or not isinstance(text, str):
        return ""
    
    # Remove potentially dangerous characters and limit length
    text = re.sub(r'[<>"\']', '', text.strip())
    return text[:1000]  # Limit message length

def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash."""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def generate_jwt_token(user_id: str, email: str) -> str:
    """Generate a JWT token for the user."""
    payload = {
        'user_id': user_id,
        'email': email,
        'exp': datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_jwt_token(token: str) -> dict:
    """Verify and decode a JWT token."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def get_user_from_token(auth_header):
    """Validates JWT and retrieves user information."""
    if not auth_header:
        return None, {"error": "Missing Authorization header"}
    
    try:
        if not auth_header.startswith("Bearer "):
            return None, {"error": "Invalid Authorization header format"}
            
        token = auth_header.split(" ")[1]
        if not token:
            return None, {"error": "Missing token"}
            
        payload = verify_jwt_token(token)
        if not payload:
            return None, {"error": "Invalid or expired token"}
            
        # Create a user object similar to Supabase format for compatibility
        user = {
            'id': payload['user_id'],
            'email': payload['email']
        }
        return user, None
    except Exception as e:
        logger.error(f"Token validation error: {str(e)}")
        return None, {"error": "Invalid or expired token"}

def ensure_tables_exist():
    """Ensure required database tables exist."""
    try:
        # Check if messages table exists by trying to select from it
        supabase.table('messages').select('id').limit(1).execute()
        logger.info("Messages table exists")
    except Exception as e:
        logger.warning(f"Messages table might not exist: {str(e)}")
        # Create the table if it doesn't exist
        try:
            supabase.rpc('create_messages_table').execute()
        except:
            logger.error("Could not create messages table automatically")
    
    try:
        # Check if summaries table exists
        supabase.table('summaries').select('id').limit(1).execute()
        logger.info("Summaries table exists")
    except Exception as e:
        logger.warning(f"Summaries table might not exist: {str(e)}")

def safe_database_operation(operation, fallback_value=None):
    """Safely execute database operations with fallback."""
    try:
        result = operation()
        return result, None
    except Exception as e:
        logger.error(f"Database operation failed: {str(e)}")
        return fallback_value, str(e)

def get_persona():
    """Reads the persona from the text file."""
    try:
        persona_path = os.path.join(os.path.dirname(__file__), 'persona.txt')
        with open(persona_path, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except FileNotFoundError:
        logger.warning("persona.txt not found, using fallback")
        return "You are Daddy John, a helpful, caring, and supportive digital dad who gives advice with warmth and humor."
    except Exception as e:
        logger.error(f"Error reading persona: {str(e)}")
        return "You are Daddy John, a helpful, caring, and supportive digital dad who gives advice with warmth and humor."

def make_openrouter_request(messages, timeout=25, max_retries=3):
    """Make a request to OpenRouter API with retry logic."""
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        logger.error("OPENROUTER_API_KEY not found in environment variables")
        return "I'm having trouble connecting to my brain right now, kiddo. Can you try again in a moment?"
    
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
                return "I'm thinking a bit slowly right now. Can you try asking me again?"
        except requests.exceptions.RequestException as e:
            logger.error(f"OpenRouter API error on attempt {attempt + 1}: {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(1)
            else:
                return "I'm having trouble with my thoughts right now. Please try again in a moment."
        except Exception as e:
            logger.error(f"Unexpected error in OpenRouter request: {str(e)}")
            return "Something went wrong in my thinking process. Let me try to help you anyway!"

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

@app.route('/api/login', methods=['POST'])
def login():
    """Custom login endpoint for invited users."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON data"}), 400
            
        email = sanitize_input(data.get("email", "")).lower()
        password = data.get("password", "")
        
        if not email or not password:
            return jsonify({"error": "Email and password are required"}), 400
        
        # Check if user exists in invited_users table
        user_response, error = safe_database_operation(
            lambda: supabase.table('invited_users').select('id, email, password_hash, is_active').eq('email', email).execute()
        )
        
        if error:
            logger.error(f"Database error during login: {error}")
            return jsonify({"error": "Login service temporarily unavailable"}), 503
            
        if not user_response or not user_response.data:
            return jsonify({"error": "Invalid email or password"}), 401
            
        user_data = user_response.data[0]
        
        if not user_data['is_active']:
            return jsonify({"error": "Account is not active"}), 401
            
        # Verify password
        if not verify_password(password, user_data['password_hash']):
            return jsonify({"error": "Invalid email or password"}), 401
            
        # Generate JWT token
        token = generate_jwt_token(user_data['id'], user_data['email'])
        
        return jsonify({
            "token": token,
            "user": {
                "id": user_data['id'],
                "email": user_data['email']
            }
        })
            
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({"error": "An unexpected error occurred"}), 500

@app.route('/api/chat', methods=['POST'])
def chat_handler():
    """Main endpoint to handle chat requests."""
    try:
        # Validate user authentication
        user, error = get_user_from_token(request.headers.get("Authorization"))
        if error:
            return jsonify(error), 401
        
        user_id = user['id']
        
        # Validate and sanitize input
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON data"}), 400
            
        user_message = sanitize_input(data.get("message", ""))
        if not user_message:
            # If empty message, return a friendly response without processing
            return jsonify({"reply": "Hey there! What's on your mind today?"})

        # Try to store user message (non-blocking)
        message_stored = False
        store_result, store_error = safe_database_operation(
            lambda: supabase.table('messages').insert({
                "user_id": user_id,
                "role": "user",
                "content": user_message
            }).execute()
        )
        
        if store_error:
            logger.warning(f"Could not store user message: {store_error}")
        else:
            message_stored = True
        
        # Get chat history (with fallback)
        chat_history = []
        latest_summary = ""
        
        if message_stored:
            history_result, history_error = safe_database_operation(
                lambda: supabase.table('messages').select('role, content').eq('user_id', user_id).order('created_at', desc=True).limit(20).execute()
            )
            
            if history_result and history_result.data:
                chat_history = list(reversed(history_result.data))
            
            summary_result, summary_error = safe_database_operation(
                lambda: supabase.table('summaries').select('summary_text').eq('user_id', user_id).order('created_at', desc=True).limit(1).execute()
            )
            
            if summary_result and summary_result.data:
                latest_summary = summary_result.data[0]['summary_text']

        # Prepare AI prompt
        system_prompt = get_persona()
        context_prompt = f"BACKGROUND CONTEXT (use this for memory but prioritize the user's last message):\n{latest_summary}\n\n---\n\nCURRENT CONVERSATION:" if latest_summary else "CURRENT CONVERSATION:"

        prompt_messages = [
            {"role": "system", "content": system_prompt},
            {"role": "system", "content": context_prompt}
        ]
        
        # Add recent history if available
        if chat_history:
            prompt_messages.extend(chat_history[-10:])  # Last 10 messages
        
        # Add current message
        prompt_messages.append({"role": "user", "content": user_message})
        
        # Get AI response
        ai_response_content = make_openrouter_request(prompt_messages)
        ai_response_content = clean_ai_response(ai_response_content)

        # Try to store AI response (non-blocking)
        if message_stored:
            safe_database_operation(
                lambda: supabase.table('messages').insert({
                    "user_id": user_id,
                    "role": "assistant",
                    "content": ai_response_content
                }).execute()
            )

        # Check if summarization is needed (non-blocking)
        if message_stored and chat_history:
            total_messages = len(chat_history) + 1
            if total_messages > 0 and total_messages % 20 == 0:
                try:
                    summarize_conversation_async(user_id, chat_history)
                except Exception as e:
                    logger.warning(f"Summarization failed: {str(e)}")

        return jsonify({"reply": ai_response_content})
        
    except Exception as e:
        logger.error(f"Unexpected error in chat_handler: {str(e)}")
        return jsonify({"reply": "I'm having a bit of trouble right now, but I'm here for you. Can you try asking me again?"})

def summarize_conversation_async(user_id, history):
    """Generates and stores a summary of the conversation asynchronously."""
    try:
        if not history:
            return
            
        summary_prompt = "Summarize the key points of this conversation in 1-2 sentences. Focus on the user's main concerns, emotional state, and any important context that should be remembered for future conversations."
        messages_for_summary = [{"role": m["role"], "content": m["content"]} for m in history[-10:]]
        messages_for_summary.insert(0, {"role": "system", "content": summary_prompt})

        summary_text = make_openrouter_request(messages_for_summary, timeout=30)
        
        if summary_text and "trouble" not in summary_text.lower():
            safe_database_operation(
                lambda: supabase.table('summaries').insert({
                    "user_id": user_id, 
                    "summary_text": summary_text
                }).execute()
            )
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
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({"error": "Internal server error"}), 500

# Initialize tables on startup
try:
    ensure_tables_exist()
except Exception as e:
    logger.warning(f"Could not verify tables on startup: {str(e)}")

if __name__ == '__main__':
    # Only run in debug mode locally
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=debug_mode)
