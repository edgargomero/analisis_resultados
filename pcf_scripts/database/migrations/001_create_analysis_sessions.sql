-- Minimal Analysis Sessions Table Creation
-- Execute this in Supabase SQL Editor

-- 1. Create the analysis_sessions table
CREATE TABLE IF NOT EXISTS public.analysis_sessions (
    session_id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id TEXT NOT NULL,
    analysis_type TEXT NOT NULL,
    file_info JSONB DEFAULT '{}',
    status TEXT NOT NULL DEFAULT 'created',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    completed_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE DEFAULT (NOW() + INTERVAL '30 days'),
    analysis_results JSONB DEFAULT '{}',
    results_summary JSONB DEFAULT '{}'
);

-- 2. Create performance indexes
CREATE INDEX IF NOT EXISTS idx_analysis_sessions_user_id ON public.analysis_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_analysis_sessions_status ON public.analysis_sessions(status);
CREATE INDEX IF NOT EXISTS idx_analysis_sessions_analysis_type ON public.analysis_sessions(analysis_type);
CREATE INDEX IF NOT EXISTS idx_analysis_sessions_created_at ON public.analysis_sessions(created_at DESC);

-- 3. Enable Row Level Security
ALTER TABLE public.analysis_sessions ENABLE ROW LEVEL SECURITY;

-- 4. Create RLS policies (permissive for now - can be tightened later)
CREATE POLICY IF NOT EXISTS "Allow service role full access" ON public.analysis_sessions
FOR ALL USING (current_setting('role') = 'service_role');

-- Allow authenticated users full access to their own data
CREATE POLICY IF NOT EXISTS "Users manage own sessions" ON public.analysis_sessions
FOR ALL USING (true);  -- Temporarily allow all access for testing

-- Success indicator
SELECT 'Analysis sessions table created successfully!' as result;