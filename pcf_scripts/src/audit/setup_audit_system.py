import os
import sys
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Supabase client
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

if not url or not key:
    print("ERROR: SUPABASE_URL and SUPABASE_KEY must be set in environment variables")
    print("\nPlease create a .env file with:")
    print("SUPABASE_URL=your_supabase_url")
    print("SUPABASE_KEY=your_supabase_service_role_key")
    print("\nFor the audit system to work, you need the SERVICE ROLE key, not the anon key.")
    sys.exit(1)

try:
    supabase: Client = create_client(url, key)
    print("✅ Supabase client initialized successfully")
except Exception as e:
    print(f"❌ Error initializing Supabase client: {str(e)}")
    sys.exit(1)

# Complete SQL script for audit system
sql_script = """
-- 1. CREAR FUNCIÓN DE EJECUCIÓN SQL
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

-- 2. CREAR TABLAS DE AUDITORÍA

-- Tabla principal de logs de auditoría
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

-- Actividades de usuarios
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

-- Registro de archivos subidos
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

-- Ejecuciones de análisis
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

-- Llamadas a APIs externas
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

-- Datos almacenados
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

-- 3. HABILITAR ROW LEVEL SECURITY
ALTER TABLE public.audit_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.audit_user_activities ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.audit_file_uploads ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.audit_analysis_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.audit_api_calls ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.audit_data_storage ENABLE ROW LEVEL SECURITY;

-- 4. CREAR POLÍTICAS RLS
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

-- Políticas de administrador
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

-- 5. CREAR ÍNDICES PARA PERFORMANCE
CREATE INDEX IF NOT EXISTS idx_audit_activities_user_time ON public.audit_user_activities(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_activities_type ON public.audit_user_activities(activity_type);
CREATE INDEX IF NOT EXISTS idx_audit_files_user_time ON public.audit_file_uploads(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_files_hash ON public.audit_file_uploads(file_hash);
CREATE INDEX IF NOT EXISTS idx_audit_analysis_user_time ON public.audit_analysis_runs(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_analysis_type ON public.audit_analysis_runs(analysis_type);
CREATE INDEX IF NOT EXISTS idx_audit_api_calls_user_time ON public.audit_api_calls(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_time ON public.audit_logs(user_id, timestamp DESC);

-- 6. FUNCIÓN DE LIMPIEZA AUTOMÁTICA
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

def execute_sql_commands(sql_text):
    """Execute SQL commands directly using Supabase"""
    try:
        # Split the script into logical sections (functions, tables, policies, etc.)
        sections = []
        current_section = ""
        lines = sql_text.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('--'):
                if line.startswith('--') and current_section:
                    # New section started
                    if current_section.strip():
                        sections.append(current_section.strip())
                    current_section = ""
                continue
            
            current_section += line + "\n"
            
            # End of statement
            if line.endswith(';'):
                if current_section.strip():
                    sections.append(current_section.strip())
                current_section = ""
        
        # Add any remaining content
        if current_section.strip():
            sections.append(current_section.strip())
        
        results = []
        success_count = 0
        
        for i, statement in enumerate(sections, 1):
            if statement and not statement.startswith('--'):
                try:
                    # Clean up the statement
                    clean_statement = statement.strip()
                    if not clean_statement.endswith(';'):
                        clean_statement += ';'
                    
                    # Execute using supabase client
                    result = supabase.postgrest.session.post(
                        f"{supabase.postgrest.url}/rpc/execute_sql",
                        json={"sql_text": clean_statement},
                        headers=supabase.postgrest.session.headers
                    )
                    
                    if result.status_code == 200:
                        print(f"✅ Statement {i}: SUCCESS")
                        results.append(f"Statement {i}: SUCCESS")
                        success_count += 1
                    else:
                        error_msg = result.text if hasattr(result, 'text') else str(result)
                        print(f"❌ Statement {i}: ERROR - {error_msg}")
                        results.append(f"Statement {i}: ERROR - {error_msg}")
                        
                except Exception as e:
                    print(f"❌ Statement {i}: ERROR - {str(e)}")
                    results.append(f"Statement {i}: ERROR - {str(e)}")
        
        print(f"\n📊 Execution Summary: {success_count}/{len(sections)} statements successful")
        return results
        
    except Exception as e:
        print(f"❌ Error executing SQL: {str(e)}")
        return [f"Error: {str(e)}"]

def main():
    print("Setting up CEAPSI Audit System in Supabase...")
    print("=" * 60)
    
    # Execute the SQL script
    results = execute_sql_commands(sql_script)
    
    print("\n" + "=" * 60)
    print("Execution Summary:")
    print("=" * 60)
    
    success_count = sum(1 for r in results if "SUCCESS" in r)
    error_count = sum(1 for r in results if "ERROR" in r)
    
    print(f"Total statements: {len(results)}")
    print(f"Successful: {success_count}")
    print(f"Errors: {error_count}")
    
    if error_count > 0:
        print("\nErrors encountered:")
        for result in results:
            if "ERROR" in result:
                print(f"  - {result}")
    
    print("\n" + "=" * 60)
    print("Audit system setup complete!")
    
    # Verify tables were created
    try:
        print("\nVerifying created tables...")
        tables = [
            'audit_logs',
            'audit_user_activities', 
            'audit_file_uploads',
            'audit_analysis_runs',
            'audit_api_calls',
            'audit_data_storage'
        ]
        
        for table in tables:
            try:
                # Try to select from the table
                result = supabase.table(table).select("*").limit(1).execute()
                print(f"✓ Table '{table}' verified")
            except Exception as e:
                print(f"✗ Table '{table}' verification failed: {str(e)}")
    except Exception as e:
        print(f"Error verifying tables: {str(e)}")

if __name__ == "__main__":
    main()