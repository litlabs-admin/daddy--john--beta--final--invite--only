# Daddy John Chatbot

A minimal chatbot SaaS web application featuring the "Daddy John" persona, built with HTML, CSS, JavaScript, and Python Flask.

## Features

- **Persona-based AI Chat**: Chatbot speaks as "Daddy John" character defined in `persona.txt`
- **User Authentication**: Secure login/signup with Supabase
- **Chat History**: Persistent conversation storage per user
- **Context Management**: Automatic conversation summarization every 20 messages
- **Modern Dark UI**: Responsive design with smooth animations
- **Production Ready**: Optimized for Vercel deployment

## Tech Stack

- **Frontend**: HTML, CSS, Vanilla JavaScript
- **Backend**: Python Flask with Flask-CORS
- **Database**: Supabase (PostgreSQL)
- **AI**: OpenRouter API with Mistral 7B model
- **Deployment**: Vercel

## Local Development

### Prerequisites

- Python 3.8+
- Supabase account
- OpenRouter API key

### Setup

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd daddyjohnbetafinal
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Variables**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` with your credentials:
   ```
   SUPABASE_URL=your_supabase_project_url
   SUPABASE_KEY=your_supabase_service_role_key
   OPENROUTER_API_KEY=your_openrouter_api_key
   FLASK_ENV=development
   ```

5. **Database Setup**
   
   Create these tables in your Supabase database:
   
   ```sql
   -- Messages table
   CREATE TABLE messages (
     id BIGSERIAL PRIMARY KEY,
     user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
     role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
     content TEXT NOT NULL,
     created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
   );
   
   -- Summaries table
   CREATE TABLE summaries (
     id BIGSERIAL PRIMARY KEY,
     user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
     summary_text TEXT NOT NULL,
     created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
   );
   
   -- Enable Row Level Security
   ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
   ALTER TABLE summaries ENABLE ROW LEVEL SECURITY;
   
   -- RLS Policies
   CREATE POLICY "Users can view own messages" ON messages
     FOR SELECT USING (auth.uid() = user_id);
   
   CREATE POLICY "Users can insert own messages" ON messages
     FOR INSERT WITH CHECK (auth.uid() = user_id);
   
   CREATE POLICY "Users can view own summaries" ON summaries
     FOR SELECT USING (auth.uid() = user_id);
   
   CREATE POLICY "Users can insert own summaries" ON summaries
     FOR INSERT WITH CHECK (auth.uid() = user_id);
   ```

6. **Run locally**
   ```bash
   python app.py
   ```
   
   Visit `http://localhost:5000`

## Deployment to Vercel

### Prerequisites

- Vercel account
- GitHub repository

### Steps

1. **Push to GitHub**
   ```bash
   git add .
   git commit -m "Initial commit"
   git push origin main
   ```

2. **Connect to Vercel**
   - Go to [vercel.com](https://vercel.com)
   - Import your GitHub repository
   - Vercel will auto-detect the Python project

3. **Environment Variables**
   
   In Vercel dashboard, add these environment variables:
   ```
   SUPABASE_URL=your_supabase_project_url
   SUPABASE_KEY=your_supabase_service_role_key
   OPENROUTER_API_KEY=your_openrouter_api_key
   FLASK_ENV=production
   ```

4. **Deploy**
   - Vercel will automatically deploy using `vercel.json` configuration
   - Your app will be available at `https://your-app.vercel.app`

## Security Features

- Input sanitization and validation
- JWT token authentication
- CORS protection
- Rate limiting ready
- XSS prevention
- Environment variable protection

## Architecture

```
├── app.py              # Main Flask application
├── requirements.txt    # Python dependencies
├── vercel.json        # Vercel deployment config
├── persona.txt        # AI character definition
├── .env.example       # Environment variables template
├── static/
│   ├── styles.css     # Dark theme styling
│   ├── auth.js        # Authentication logic
│   └── chat.js        # Chat interface logic
└── templates/
    ├── index.html     # Login/signup page
    └── chat.html      # Chat interface
```

## API Endpoints

- `GET /` - Login page
- `GET /chat` - Chat interface (authenticated)
- `POST /api/chat` - Send message to AI
- `GET /health` - Health check

## Customization

### Changing the AI Persona

Edit `persona.txt` to modify the chatbot's personality and behavior.

### Styling

Modify `static/styles.css` to customize the dark theme and UI components.

### AI Model

Change the model in `app.py`:
```python
"model": "mistralai/mistral-7b-instruct"  # Change to your preferred model
```

## Troubleshooting

### Common Issues

1. **Environment Variables Not Loading**
   - Ensure `.env` file exists and has correct format
   - Check Vercel environment variables are set

2. **Database Connection Issues**
   - Verify Supabase URL and service role key
   - Check database tables exist with correct schema

3. **AI API Errors**
   - Confirm OpenRouter API key is valid
   - Check API quota and billing

### Logs

Check Vercel function logs in the dashboard for detailed error information.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License.
