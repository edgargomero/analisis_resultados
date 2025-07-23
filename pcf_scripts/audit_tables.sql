-- CEAPSI PCF - Tablas de Auditoría y Registro de Actividades
-- Ejecutar en Supabase SQL Editor

-- Usar el sistema de autenticación nativo de Supabase (auth.users)
-- Las tablas de auditoría se relacionan directamente con auth.users

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

-- Tabla de registro de actividades de usuarios
CREATE TABLE IF NOT EXISTS public.audit_user_activities (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    session_id TEXT,
    activity_type TEXT NOT NULL, -- 'login', 'logout', 'file_upload', 'analysis', 'api_call', 'model_training', 'dashboard_view'
    module_name TEXT NOT NULL, -- 'preparacion_datos', 'sistema_multi_modelo', 'dashboard_comparacion', etc.
    activity_description TEXT,
    activity_details JSONB, -- Detalles específicos de la actividad
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabla de registro de archivos subidos
CREATE TABLE IF NOT EXISTS public.audit_file_uploads (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    session_id TEXT,
    file_name TEXT NOT NULL,
    file_type TEXT, -- 'csv', 'xlsx', 'json'
    file_size_bytes BIGINT,
    data_type TEXT, -- 'llamadas', 'citas', 'usuarios_mapping', etc.
    records_count INTEGER,
    columns_detected TEXT[], -- Array de nombres de columnas
    validation_status TEXT, -- 'valid', 'invalid', 'warning'
    validation_details JSONB,
    file_hash TEXT, -- Hash del archivo para detectar duplicados
    storage_path TEXT, -- Ruta donde se guardó el archivo
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabla de registro de análisis y predicciones
CREATE TABLE IF NOT EXISTS audit_analysis_runs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    user_email TEXT,
    session_id TEXT,
    analysis_type TEXT NOT NULL, -- 'auditoria_datos', 'segmentacion', 'multi_modelo', 'prediccion'
    input_data_source TEXT, -- Referencia al archivo o fuente de datos
    parameters JSONB, -- Parámetros utilizados en el análisis
    execution_status TEXT, -- 'started', 'completed', 'failed', 'cancelled'
    execution_time_seconds NUMERIC,
    results_summary JSONB, -- Resumen de resultados
    output_files TEXT[], -- Archivos generados
    performance_metrics JSONB, -- MAE, RMSE, etc.
    error_details TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Tabla de registro de integraciones API (Reservo, etc.)
CREATE TABLE IF NOT EXISTS audit_api_calls (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    user_email TEXT,
    session_id TEXT,
    api_provider TEXT NOT NULL, -- 'reservo', 'alodesk', etc.
    endpoint TEXT NOT NULL,
    method TEXT NOT NULL, -- 'GET', 'POST', etc.
    request_parameters JSONB,
    response_status INTEGER,
    response_time_ms INTEGER,
    records_retrieved INTEGER,
    success BOOLEAN,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabla de registro de datos procesados y guardados
CREATE TABLE IF NOT EXISTS audit_data_storage (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    user_email TEXT,
    session_id TEXT,
    storage_type TEXT NOT NULL, -- 'file', 'database', 'cache'
    data_type TEXT, -- 'llamadas_preparadas', 'citas_reservo', 'resultados_modelo'
    storage_location TEXT,
    data_size_bytes BIGINT,
    records_count INTEGER,
    metadata JSONB,
    retention_days INTEGER DEFAULT 90,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE
);

-- Índices para optimizar consultas
CREATE INDEX IF NOT EXISTS idx_audit_activities_user_time ON audit_user_activities(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_activities_type_time ON audit_user_activities(activity_type, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_files_user_time ON audit_file_uploads(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_analysis_user_time ON audit_analysis_runs(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_analysis_type_time ON audit_analysis_runs(analysis_type, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_api_provider_time ON audit_api_calls(api_provider, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_storage_type_time ON audit_data_storage(data_type, created_at DESC);

-- RLS (Row Level Security) para asegurar que usuarios solo vean sus datos
ALTER TABLE audit_user_activities ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_file_uploads ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_analysis_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_api_calls ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_data_storage ENABLE ROW LEVEL SECURITY;

-- Políticas RLS usando Supabase auth nativo
-- Usuarios pueden ver solo sus propios registros
CREATE POLICY "Users can view own audit logs" ON public.audit_logs
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can view own activities" ON public.audit_user_activities
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can view own file uploads" ON public.audit_file_uploads
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can view own analysis runs" ON public.audit_analysis_runs
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can view own API calls" ON public.audit_api_calls
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can view own data storage" ON public.audit_data_storage
    FOR SELECT USING (auth.uid() = user_id);

-- Políticas para inserción usando service_role o usuarios autenticados
CREATE POLICY "Service role can insert audit logs" ON public.audit_logs
    FOR INSERT WITH CHECK (
        auth.jwt() ->> 'role' = 'service_role' OR 
        (auth.uid() IS NOT NULL)
    );

CREATE POLICY "Authenticated users can insert activities" ON public.audit_user_activities
    FOR INSERT WITH CHECK (auth.uid() IS NOT NULL);

CREATE POLICY "Authenticated users can insert file uploads" ON public.audit_file_uploads
    FOR INSERT WITH CHECK (auth.uid() IS NOT NULL);

CREATE POLICY "Authenticated users can insert analysis runs" ON public.audit_analysis_runs
    FOR INSERT WITH CHECK (auth.uid() IS NOT NULL);

CREATE POLICY "Authenticated users can insert API calls" ON public.audit_api_calls
    FOR INSERT WITH CHECK (auth.uid() IS NOT NULL);

CREATE POLICY "Authenticated users can insert data storage" ON public.audit_data_storage
    FOR INSERT WITH CHECK (auth.uid() IS NOT NULL);

-- Políticas especiales para administradores (pueden ver todo)
CREATE POLICY "Admins can view all activities" ON audit_user_activities
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM auth.users 
            WHERE id = auth.uid() 
            AND raw_user_meta_data->>'role' = 'admin'
        )
    );

CREATE POLICY "Admins can view all file uploads" ON audit_file_uploads
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM auth.users 
            WHERE id = auth.uid() 
            AND raw_user_meta_data->>'role' = 'admin'
        )
    );

CREATE POLICY "Admins can view all analysis runs" ON audit_analysis_runs
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM auth.users 
            WHERE id = auth.uid() 
            AND raw_user_meta_data->>'role' = 'admin'
        )
    );

CREATE POLICY "Admins can view all API calls" ON audit_api_calls
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM auth.users 
            WHERE id = auth.uid() 
            AND raw_user_meta_data->>'role' = 'admin'
        )
    );

CREATE POLICY "Admins can view all data storage" ON audit_data_storage
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM auth.users 
            WHERE id = auth.uid() 
            AND raw_user_meta_data->>'role' = 'admin'
        )
    );

-- Función para limpiar registros antiguos (ejecutar periódicamente)
CREATE OR REPLACE FUNCTION cleanup_old_audit_records()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER := 0;
BEGIN
    -- Limpiar actividades más antiguas de 1 año
    DELETE FROM audit_user_activities 
    WHERE created_at < NOW() - INTERVAL '1 year';
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    -- Limpiar archivos expirados
    DELETE FROM audit_data_storage 
    WHERE expires_at IS NOT NULL AND expires_at < NOW();
    
    -- Limpiar análisis más antiguos de 6 meses
    DELETE FROM audit_analysis_runs 
    WHERE created_at < NOW() - INTERVAL '6 months' 
    AND execution_status IN ('completed', 'failed');
    
    -- Limpiar llamadas API más antiguas de 3 meses
    DELETE FROM audit_api_calls 
    WHERE created_at < NOW() - INTERVAL '3 months';
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Comentarios para documentación
COMMENT ON TABLE audit_user_activities IS 'Registro de todas las actividades de usuarios en el sistema';
COMMENT ON TABLE audit_file_uploads IS 'Registro de todos los archivos subidos por usuarios';
COMMENT ON TABLE audit_analysis_runs IS 'Registro de todos los análisis y predicciones ejecutados';
COMMENT ON TABLE audit_api_calls IS 'Registro de todas las llamadas a APIs externas';
COMMENT ON TABLE audit_data_storage IS 'Registro de datos procesados y almacenados en el sistema';