-- Daddy John Chatbot Database Setup
-- Run this script in your Supabase SQL Editor

-- 1. Create invited_users table for authentication
CREATE TABLE IF NOT EXISTS invited_users (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. Create messages table for chat history
CREATE TABLE IF NOT EXISTS messages (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. Create summaries table for conversation summaries
CREATE TABLE IF NOT EXISTS summaries (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL,
    summary_text TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_invited_users_email ON invited_users(email);
CREATE INDEX IF NOT EXISTS idx_messages_user_id ON messages(user_id);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at);
CREATE INDEX IF NOT EXISTS idx_summaries_user_id ON summaries(user_id);
CREATE INDEX IF NOT EXISTS idx_summaries_created_at ON summaries(created_at);

-- 5. Add foreign key constraints (optional but recommended)
-- Note: Only add these if you want strict referential integrity
-- ALTER TABLE messages ADD CONSTRAINT fk_messages_user_id 
--     FOREIGN KEY (user_id) REFERENCES invited_users(id) ON DELETE CASCADE;
-- ALTER TABLE summaries ADD CONSTRAINT fk_summaries_user_id 
--     FOREIGN KEY (user_id) REFERENCES invited_users(id) ON DELETE CASCADE;

-- 6. Insert test user (password: testpass123)
INSERT INTO invited_users (email, password_hash) VALUES 
('test@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBdXfs2Sk4u2.2')
ON CONFLICT (email) DO NOTHING;

-- 7. Insert additional test users (optional)
INSERT INTO invited_users (email, password_hash) VALUES 
('admin@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBdXfs2Sk4u2.2'),
('beta@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBdXfs2Sk4u2.2')
ON CONFLICT (email) DO NOTHING;

-- 8. Enable Row Level Security (RLS) for better security
ALTER TABLE invited_users ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE summaries ENABLE ROW LEVEL SECURITY;

-- 9. Create RLS policies (adjust as needed for your security requirements)
-- Allow users to read their own data
CREATE POLICY "Users can view own messages" ON messages
    FOR SELECT USING (true); -- Adjust based on your auth system

CREATE POLICY "Users can insert own messages" ON messages
    FOR INSERT WITH CHECK (true); -- Adjust based on your auth system

CREATE POLICY "Users can view own summaries" ON summaries
    FOR SELECT USING (true); -- Adjust based on your auth system

CREATE POLICY "Users can insert own summaries" ON summaries
    FOR INSERT WITH CHECK (true); -- Adjust based on your auth system

-- 10. Grant necessary permissions (if using service role)
-- GRANT ALL ON invited_users TO service_role;
-- GRANT ALL ON messages TO service_role;
-- GRANT ALL ON summaries TO service_role;

-- Verification queries (run these to check if everything is set up correctly)
-- SELECT 'invited_users' as table_name, count(*) as row_count FROM invited_users
-- UNION ALL
-- SELECT 'messages' as table_name, count(*) as row_count FROM messages
-- UNION ALL
-- SELECT 'summaries' as table_name, count(*) as row_count FROM summaries;
