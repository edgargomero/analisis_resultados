#!/usr/bin/env python3
"""
Script to execute the complete audit system SQL script in Supabase
This script creates all necessary tables, policies, and functions for the audit system
"""

import os
import sys
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_supabase_client():
    """Initialize and return Supabase client"""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    
    if not url or not key:
        print("ERROR: SUPABASE_URL and SUPABASE_KEY must be set in environment variables")
        print("\nPlease create a .env file with:")
        print("SUPABASE_URL=your_supabase_url")
        print("SUPABASE_KEY=your_supabase_service_role_key")
        print("\nFor the audit system to work, you need the SERVICE ROLE key, not the anon key.")
        return None
    
    try:
        supabase = create_client(url, key)
        print("SUCCESS: Supabase client initialized successfully")
        return supabase
    except Exception as e:
        print(f"ERROR: Error initializing Supabase client: {str(e)}")
        return None

def execute_audit_sql():
    """Execute the complete audit system SQL"""
    
    supabase = get_supabase_client()
    if not supabase:
        return False
    
    # SQL commands to execute one by one
    commands = [
        # 1. Create execute_sql function
        """
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
        """,
        
        # 2. Create audit_logs table
        """
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
        """,
        
        # 3. Create audit_user_activities table
        """
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
        """,
        
        # 4. Create audit_file_uploads table
        """
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
        """,
        
        # 5. Create audit_analysis_runs table
        """
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
        """,
        
        # 6. Create audit_api_calls table
        """
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
        """,
        
        # 7. Create audit_data_storage table
        """
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
        """,
    ]
    
    # RLS commands
    rls_commands = [
        "ALTER TABLE public.audit_logs ENABLE ROW LEVEL SECURITY;",
        "ALTER TABLE public.audit_user_activities ENABLE ROW LEVEL SECURITY;",
        "ALTER TABLE public.audit_file_uploads ENABLE ROW LEVEL SECURITY;",
        "ALTER TABLE public.audit_analysis_runs ENABLE ROW LEVEL SECURITY;",
        "ALTER TABLE public.audit_api_calls ENABLE ROW LEVEL SECURITY;",
        "ALTER TABLE public.audit_data_storage ENABLE ROW LEVEL SECURITY;",
    ]
    
    # Policy commands
    policy_commands = [
        """
        CREATE POLICY "Users can view own activities" ON public.audit_user_activities
        FOR SELECT USING (auth.uid() = user_id);
        """,
        """
        CREATE POLICY "Users can insert own activities" ON public.audit_user_activities
        FOR INSERT WITH CHECK (auth.uid() = user_id);
        """,
        """
        CREATE POLICY "Users can view own file uploads" ON public.audit_file_uploads
        FOR SELECT USING (auth.uid() = user_id);
        """,
        """
        CREATE POLICY "Users can insert own file uploads" ON public.audit_file_uploads
        FOR INSERT WITH CHECK (auth.uid() = user_id);
        """,
        """
        CREATE POLICY "Users can view own analysis" ON public.audit_analysis_runs
        FOR SELECT USING (auth.uid() = user_id);
        """,
        """
        CREATE POLICY "Users can manage own analysis" ON public.audit_analysis_runs
        FOR ALL USING (auth.uid() = user_id);
        """,
        """
        CREATE POLICY "Users can view own api calls" ON public.audit_api_calls
        FOR SELECT USING (auth.uid() = user_id);
        """,
        """
        CREATE POLICY "Users can insert own api calls" ON public.audit_api_calls
        FOR INSERT WITH CHECK (auth.uid() = user_id);
        """,
        """
        CREATE POLICY "Users can view own data storage" ON public.audit_data_storage
        FOR SELECT USING (auth.uid() = user_id);
        """,
        """
        CREATE POLICY "Users can insert own data storage" ON public.audit_data_storage
        FOR INSERT WITH CHECK (auth.uid() = user_id);
        """,
        """
        CREATE POLICY "Users can view own logs" ON public.audit_logs
        FOR SELECT USING (auth.uid() = user_id);
        """,
        """
        CREATE POLICY "Service role can insert logs" ON public.audit_logs
        FOR INSERT WITH CHECK (
            auth.jwt() ->> 'role' = 'service_role' OR 
            (auth.uid() IS NOT NULL)
        );
        """,
    ]
    
    # Index commands
    index_commands = [
        "CREATE INDEX IF NOT EXISTS idx_audit_activities_user_time ON public.audit_user_activities(user_id, created_at DESC);",
        "CREATE INDEX IF NOT EXISTS idx_audit_activities_type ON public.audit_user_activities(activity_type);",
        "CREATE INDEX IF NOT EXISTS idx_audit_files_user_time ON public.audit_file_uploads(user_id, created_at DESC);",
        "CREATE INDEX IF NOT EXISTS idx_audit_files_hash ON public.audit_file_uploads(file_hash);",
        "CREATE INDEX IF NOT EXISTS idx_audit_analysis_user_time ON public.audit_analysis_runs(user_id, created_at DESC);",
        "CREATE INDEX IF NOT EXISTS idx_audit_analysis_type ON public.audit_analysis_runs(analysis_type);",
        "CREATE INDEX IF NOT EXISTS idx_audit_api_calls_user_time ON public.audit_api_calls(user_id, created_at DESC);",
        "CREATE INDEX IF NOT EXISTS idx_audit_logs_user_time ON public.audit_logs(user_id, timestamp DESC);",
    ]
    
    # Cleanup function
    cleanup_command = """
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
    """
    
    print("Starting audit system setup...")
    print("=" * 60)
    
    success_count = 0
    total_commands = len(commands) + len(rls_commands) + len(policy_commands) + len(index_commands) + 1
    
    # Execute table creation commands
    print("\nCreating tables...")
    for i, cmd in enumerate(commands, 1):
        try:
            # Use RPC to execute SQL
            result = supabase.rpc('execute_sql', {'sql_text': cmd.strip()}).execute()
            print(f"SUCCESS: Command {i}/{len(commands)}: Table/Function created")
            success_count += 1
        except Exception as e:
            print(f"ERROR: Command {i}/{len(commands)}: {str(e)}")
    
    # Execute RLS commands
    print("\nEnabling Row Level Security...")
    for i, cmd in enumerate(rls_commands, 1):
        try:
            result = supabase.rpc('execute_sql', {'sql_text': cmd.strip()}).execute()
            print(f"SUCCESS: RLS {i}/{len(rls_commands)}: Enabled")
            success_count += 1
        except Exception as e:
            print(f"ERROR: RLS {i}/{len(rls_commands)}: {str(e)}")
    
    # Execute policy commands
    print("\nCreating security policies...")
    for i, cmd in enumerate(policy_commands, 1):
        try:
            result = supabase.rpc('execute_sql', {'sql_text': cmd.strip()}).execute()
            print(f"SUCCESS: Policy {i}/{len(policy_commands)}: Created")
            success_count += 1
        except Exception as e:
            print(f"ERROR: Policy {i}/{len(policy_commands)}: {str(e)}")
    
    # Execute index commands
    print("\nCreating performance indexes...")
    for i, cmd in enumerate(index_commands, 1):
        try:
            result = supabase.rpc('execute_sql', {'sql_text': cmd.strip()}).execute()
            print(f"SUCCESS: Index {i}/{len(index_commands)}: Created")
            success_count += 1
        except Exception as e:
            print(f"ERROR: Index {i}/{len(index_commands)}: {str(e)}")
    
    # Execute cleanup function
    print("\nCreating cleanup function...")
    try:
        result = supabase.rpc('execute_sql', {'sql_text': cleanup_command.strip()}).execute()
        print("SUCCESS: Cleanup function created")
        success_count += 1
    except Exception as e:
        print(f"ERROR: Cleanup function: {str(e)}")
    
    print("\n" + "=" * 60)
    print("EXECUTION SUMMARY")
    print("=" * 60)
    print(f"Total commands: {total_commands}")
    print(f"Successful: {success_count}")
    print(f"Errors: {total_commands - success_count}")
    
    if success_count == total_commands:
        print("\nAUDIT SYSTEM SETUP COMPLETE!")
        print("All tables, policies, and functions have been created successfully.")
    else:
        print(f"\nSetup completed with {total_commands - success_count} errors.")
        print("Some components may not be fully functional.")
    
    # Verify tables
    print("\nVerifying created tables...")
    tables = [
        'audit_logs',
        'audit_user_activities', 
        'audit_file_uploads',
        'audit_analysis_runs',
        'audit_api_calls',
        'audit_data_storage'
    ]
    
    verified_count = 0
    for table in tables:
        try:
            result = supabase.table(table).select("*").limit(1).execute()
            print(f"SUCCESS: Table '{table}' verified")
            verified_count += 1
        except Exception as e:
            print(f"ERROR: Table '{table}' verification failed: {str(e)}")
    
    print(f"\nVerification: {verified_count}/{len(tables)} tables accessible")
    
    return success_count == total_commands

def main():
    """Main execution function"""
    print("CEAPSI Audit System Setup")
    print("=" * 60)
    print("This script will create the complete audit system in your Supabase database.")
    print("It includes tables, security policies, indexes, and utility functions.")
    print()
    
    if execute_audit_sql():
        print("\nSUCCESS: Audit system is ready to use!")
        print("\nNext steps:")
        print("1. Test the system with your application")
        print("2. Configure your application to use the audit tables")
        print("3. Set up regular cleanup using the cleanup_old_audit_records() function")
        return True
    else:
        print("\nSETUP FAILED: Please check the errors above and retry.")
        print("\nTroubleshooting:")
        print("1. Ensure you're using the SERVICE ROLE key, not the anon key")
        print("2. Check that your Supabase project is active")
        print("3. Verify your .env file configuration")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)