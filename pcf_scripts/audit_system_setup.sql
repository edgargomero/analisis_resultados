-- CEAPSI Audit System - Complete Setup Script
-- Execute this script in your Supabase SQL Editor
-- This creates all tables, policies, indexes, and functions for the audit system

-- 1. Create execute_sql function (for future use)
CREATE OR REPLACE FUNCTION execute_sql(sql_text TEXT)
RETURNS TEXT
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    EXECUTE sql_text;
    RETURN 'SUCCESS';
EXCEPTION
    WHEN OTHERS THEN
        RETURN 'ERROR: ' || SQLERRM;
END;
$$;

-- 2. Create audit tables
CREATE TABLE IF NOT EXISTS public.audit_logs (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    action TEXT NOT NULL,
    table_name TEXT NOT NULL,
    record_id TEXT,
    old_data JSONB,
    new_data JSONB,
    metadata JSONB DEFAULT '{}',
    ip_address INET,
    user_agent TEXT,
    session_id TEXT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.audit_user_activities (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    session_id TEXT,
    activity_type TEXT NOT NULL,
    module_name TEXT NOT NULL,
    activity_description TEXT,
    activity_details JSONB DEFAULT '{}',
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.audit_file_uploads (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    session_id TEXT,
    file_name TEXT NOT NULL,
    file_type TEXT,
    file_size_bytes BIGINT,
    data_type TEXT,
    records_count INTEGER,
    columns_detected TEXT[],
    validation_status TEXT,
    validation_details JSONB,
    file_hash TEXT,
    storage_path TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.audit_analysis_runs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    session_id TEXT,
    analysis_type TEXT NOT NULL,
    input_data_source TEXT,
    parameters JSONB,
    execution_status TEXT,
    execution_time_seconds NUMERIC,
    results_summary JSONB,
    output_files TEXT[],
    performance_metrics JSONB,
    error_details TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

CREATE TABLE IF NOT EXISTS public.audit_api_calls (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    session_id TEXT,
    api_provider TEXT NOT NULL,
    endpoint TEXT NOT NULL,
    method TEXT NOT NULL,
    request_parameters JSONB,
    response_status INTEGER,
    response_time_ms INTEGER,
    records_retrieved INTEGER,
    success BOOLEAN,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.audit_data_storage (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    session_id TEXT,
    storage_type TEXT NOT NULL,
    data_type TEXT,
    storage_location TEXT,
    data_size_bytes BIGINT,
    records_count INTEGER,
    metadata JSONB,
    retention_days INTEGER DEFAULT 90,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE
);

-- 3. Enable Row Level Security
ALTER TABLE public.audit_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.audit_user_activities ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.audit_file_uploads ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.audit_analysis_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.audit_api_calls ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.audit_data_storage ENABLE ROW LEVEL SECURITY;

-- 4. Create RLS Policies
CREATE POLICY "Users can view own activities" ON public.audit_user_activities
FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own activities" ON public.audit_user_activities
FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can view own file uploads" ON public.audit_file_uploads
FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own file uploads" ON public.audit_file_uploads
FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can view own analysis" ON public.audit_analysis_runs
FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can manage own analysis" ON public.audit_analysis_runs
FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can view own api calls" ON public.audit_api_calls
FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own api calls" ON public.audit_api_calls
FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can view own data storage" ON public.audit_data_storage
FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own data storage" ON public.audit_data_storage
FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can view own logs" ON public.audit_logs
FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Service role can insert logs" ON public.audit_logs
FOR INSERT WITH CHECK (
    auth.jwt() ->> 'role' = 'service_role' OR 
    (auth.uid() IS NOT NULL)
);

-- Admin policies (optional - uncomment if you have admin users)
CREATE POLICY "Admins can view all activities" ON public.audit_user_activities
FOR SELECT USING (
    EXISTS (
        SELECT 1 FROM auth.users 
        WHERE id = auth.uid() 
        AND raw_user_meta_data->>'role' = 'admin'
    )
);

CREATE POLICY "Admins can view all file uploads" ON public.audit_file_uploads
FOR SELECT USING (
    EXISTS (
        SELECT 1 FROM auth.users 
        WHERE id = auth.uid() 
        AND raw_user_meta_data->>'role' = 'admin'
    )
);

-- 5. Create Performance Indexes
CREATE INDEX IF NOT EXISTS idx_audit_activities_user_time ON public.audit_user_activities(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_activities_type ON public.audit_user_activities(activity_type);
CREATE INDEX IF NOT EXISTS idx_audit_files_user_time ON public.audit_file_uploads(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_files_hash ON public.audit_file_uploads(file_hash);
CREATE INDEX IF NOT EXISTS idx_audit_analysis_user_time ON public.audit_analysis_runs(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_analysis_type ON public.audit_analysis_runs(analysis_type);
CREATE INDEX IF NOT EXISTS idx_audit_api_calls_user_time ON public.audit_api_calls(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_time ON public.audit_logs(user_id, timestamp DESC);

-- 6. Create Cleanup Function
CREATE OR REPLACE FUNCTION cleanup_old_audit_records()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER := 0;
BEGIN
    DELETE FROM public.audit_user_activities 
    WHERE created_at < NOW() - INTERVAL '1 year';
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    DELETE FROM public.audit_data_storage 
    WHERE expires_at IS NOT NULL AND expires_at < NOW();
    
    DELETE FROM public.audit_analysis_runs 
    WHERE created_at < NOW() - INTERVAL '6 months' 
    AND execution_status IN ('completed', 'failed');
    
    DELETE FROM public.audit_api_calls 
    WHERE created_at < NOW() - INTERVAL '3 months';
    
    DELETE FROM public.audit_logs 
    WHERE timestamp < NOW() - INTERVAL '1 year';
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 7. Create audit manager helper functions
CREATE OR REPLACE FUNCTION log_user_activity(
    p_user_id UUID,
    p_session_id TEXT,
    p_activity_type TEXT,
    p_module_name TEXT,
    p_activity_description TEXT,
    p_activity_details JSONB DEFAULT '{}',
    p_ip_address INET DEFAULT NULL,
    p_user_agent TEXT DEFAULT NULL
)
RETURNS UUID AS $$
DECLARE
    activity_id UUID;
BEGIN
    INSERT INTO public.audit_user_activities (
        user_id, session_id, activity_type, module_name,
        activity_description, activity_details, ip_address, user_agent
    ) VALUES (
        p_user_id, p_session_id, p_activity_type, p_module_name,
        p_activity_description, p_activity_details, p_ip_address, p_user_agent
    ) RETURNING id INTO activity_id;
    
    RETURN activity_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE OR REPLACE FUNCTION log_file_upload(
    p_user_id UUID,
    p_session_id TEXT,
    p_file_name TEXT,
    p_file_type TEXT,
    p_file_size_bytes BIGINT,
    p_data_type TEXT,
    p_records_count INTEGER DEFAULT NULL,
    p_columns_detected TEXT[] DEFAULT NULL,
    p_validation_status TEXT DEFAULT 'pending',
    p_validation_details JSONB DEFAULT '{}',
    p_file_hash TEXT DEFAULT NULL,
    p_storage_path TEXT DEFAULT NULL
)
RETURNS UUID AS $$
DECLARE
    upload_id UUID;
BEGIN
    INSERT INTO public.audit_file_uploads (
        user_id, session_id, file_name, file_type, file_size_bytes,
        data_type, records_count, columns_detected, validation_status,
        validation_details, file_hash, storage_path
    ) VALUES (
        p_user_id, p_session_id, p_file_name, p_file_type, p_file_size_bytes,
        p_data_type, p_records_count, p_columns_detected, p_validation_status,
        p_validation_details, p_file_hash, p_storage_path
    ) RETURNING id INTO upload_id;
    
    RETURN upload_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE OR REPLACE FUNCTION log_analysis_run(
    p_user_id UUID,
    p_session_id TEXT,
    p_analysis_type TEXT,
    p_input_data_source TEXT,
    p_parameters JSONB DEFAULT '{}',
    p_execution_status TEXT DEFAULT 'started'
)
RETURNS UUID AS $$
DECLARE
    run_id UUID;
BEGIN
    INSERT INTO public.audit_analysis_runs (
        user_id, session_id, analysis_type, input_data_source,
        parameters, execution_status
    ) VALUES (
        p_user_id, p_session_id, p_analysis_type, p_input_data_source,
        p_parameters, p_execution_status
    ) RETURNING id INTO run_id;
    
    RETURN run_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Confirmation message
SELECT 'CEAPSI Audit System setup complete! All tables, policies, indexes, and functions have been created.' as message;