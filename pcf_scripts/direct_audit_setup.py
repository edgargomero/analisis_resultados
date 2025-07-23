#!/usr/bin/env python3
"""
Direct SQL execution for CEAPSI Audit System
This script executes SQL directly without relying on an execute_sql function
"""

import os
import sys
import psycopg2
from urllib.parse import urlparse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_db_connection():
    """Get direct PostgreSQL connection from Supabase URL"""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    
    if not url or not key:
        print("ERROR: SUPABASE_URL and SUPABASE_KEY must be set in environment variables")
        print("\nPlease create a .env file with:")
        print("SUPABASE_URL=your_supabase_url")
        print("SUPABASE_KEY=your_supabase_service_role_key")
        return None
    
    # Extract database connection details from Supabase URL
    # Supabase URLs are like: https://abc123.supabase.co
    # Database connection: host=db.abc123.supabase.co port=5432 dbname=postgres
    
    try:
        parsed_url = urlparse(url)
        project_id = parsed_url.hostname.split('.')[0]
        
        # For Supabase, we need to construct the database connection string
        # This requires the database password which is different from the API key
        print("INFO: Direct PostgreSQL connection not available with API key")
        print("INFO: Falling back to Supabase Python client approach")
        return None
        
    except Exception as e:
        print(f"ERROR: Could not parse Supabase URL: {str(e)}")
        return None

def execute_sql_with_supabase():
    """Execute SQL using Supabase client with proper table creation"""
    from supabase import create_client, Client
    
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    
    if not url or not key:
        print("ERROR: Environment variables not set")
        return False
    
    try:
        supabase = create_client(url, key)
        print("SUCCESS: Connected to Supabase")
    except Exception as e:
        print(f"ERROR: Failed to connect to Supabase: {str(e)}")
        return False
    
    # Try to create tables using direct table creation (without execute_sql function)
    success_count = 0
    total_commands = 6  # Number of tables to create
    
    print("\nCreating audit tables...")
    
    # Create each table individually using direct Supabase operations
    # Since we can't execute arbitrary SQL, we'll need to use the Supabase dashboard
    # or create a .sql file that can be executed manually
    
    print("INFO: Direct SQL execution requires database admin access")
    print("INFO: Creating SQL file for manual execution instead...")
    
    # Create a comprehensive SQL file
    sql_content = """
-- CEAPSI Audit System - Complete Setup Script
-- Execute this script in your Supabase SQL Editor

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
/*
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
*/

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

-- Confirmation message
SELECT 'CEAPSI Audit System setup complete!' as message;
"""
    
    # Write the SQL file
    sql_file_path = "C:\\Users\\edgar\\OneDrive\\Documentos\\BBDDCEAPSI\\claude\\analisis_resultados\\pcf_scripts\\audit_system_setup.sql"
    
    try:
        with open(sql_file_path, 'w', encoding='utf-8') as f:
            f.write(sql_content)
        
        print(f"SUCCESS: SQL file created at {sql_file_path}")
        print("\nMANUAL EXECUTION REQUIRED:")
        print("1. Go to your Supabase dashboard")
        print("2. Navigate to 'SQL Editor'")
        print("3. Copy and paste the contents of audit_system_setup.sql")
        print("4. Execute the script")
        print("5. Verify that all tables were created successfully")
        
        return True
        
    except Exception as e:
        print(f"ERROR: Could not create SQL file: {str(e)}")
        return False

def main():
    """Main execution function"""
    print("CEAPSI Audit System Setup")
    print("=" * 60)
    print("Setting up the complete audit system for your Supabase database.")
    print()
    
    if execute_sql_with_supabase():
        print("\nSUCCESS: Setup preparation complete!")
        print("\nNEXT STEPS:")
        print("1. Open your Supabase dashboard")
        print("2. Go to SQL Editor")
        print("3. Execute the generated audit_system_setup.sql file")
        print("4. Verify table creation")
        print("5. Your audit system will be ready to use!")
        return True
    else:
        print("\nERROR: Setup preparation failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)