-- =====================================================
-- CEAPSI PCF - Sistema Completo de Auditoría
-- Ejecutar en Supabase SQL Editor
-- Generado automáticamente por setup_audit_database.py
-- =====================================================

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

-- =====================================================
-- 2. CREAR TABLAS DE AUDITORÍA
-- =====================================================

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

-- =====================================================
-- 3. HABILITAR ROW LEVEL SECURITY
-- =====================================================

ALTER TABLE public.audit_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.audit_user_activities ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.audit_file_uploads ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.audit_analysis_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.audit_api_calls ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.audit_data_storage ENABLE ROW LEVEL SECURITY;

-- =====================================================
-- 4. CREAR POLÍTICAS RLS
-- =====================================================

-- Políticas para audit_user_activities
CREATE POLICY "Users can view own activities" ON public.audit_user_activities
FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own activities" ON public.audit_user_activities
FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Políticas para audit_file_uploads
CREATE POLICY "Users can view own file uploads" ON public.audit_file_uploads
FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own file uploads" ON public.audit_file_uploads
FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Políticas para audit_analysis_runs
CREATE POLICY "Users can view own analysis" ON public.audit_analysis_runs
FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can manage own analysis" ON public.audit_analysis_runs
FOR ALL USING (auth.uid() = user_id);

-- Políticas para audit_api_calls
CREATE POLICY "Users can view own api calls" ON public.audit_api_calls
FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own api calls" ON public.audit_api_calls
FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Políticas para audit_data_storage
CREATE POLICY "Users can view own data storage" ON public.audit_data_storage
FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own data storage" ON public.audit_data_storage
FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Políticas para audit_logs
CREATE POLICY "Users can view own logs" ON public.audit_logs
FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Service role can insert logs" ON public.audit_logs
FOR INSERT WITH CHECK (
    auth.jwt() ->> 'role' = 'service_role' OR 
    (auth.uid() IS NOT NULL)
);

-- Políticas de administrador (acceso completo)
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

CREATE POLICY "Admins can view all analysis runs" ON public.audit_analysis_runs
FOR SELECT USING (
    EXISTS (
        SELECT 1 FROM auth.users 
        WHERE id = auth.uid() 
        AND raw_user_meta_data->>'role' = 'admin'
    )
);

CREATE POLICY "Admins can view all api calls" ON public.audit_api_calls
FOR SELECT USING (
    EXISTS (
        SELECT 1 FROM auth.users 
        WHERE id = auth.uid() 
        AND raw_user_meta_data->>'role' = 'admin'
    )
);

CREATE POLICY "Admins can view all data storage" ON public.audit_data_storage
FOR SELECT USING (
    EXISTS (
        SELECT 1 FROM auth.users 
        WHERE id = auth.uid() 
        AND raw_user_meta_data->>'role' = 'admin'
    )
);

CREATE POLICY "Admins can view all logs" ON public.audit_logs
FOR SELECT USING (
    EXISTS (
        SELECT 1 FROM auth.users 
        WHERE id = auth.uid() 
        AND raw_user_meta_data->>'role' = 'admin'
    )
);

-- =====================================================
-- 5. CREAR ÍNDICES PARA PERFORMANCE
-- =====================================================

-- Índices para audit_user_activities
CREATE INDEX IF NOT EXISTS idx_audit_activities_user_time ON public.audit_user_activities(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_activities_type ON public.audit_user_activities(activity_type);

-- Índices para audit_file_uploads
CREATE INDEX IF NOT EXISTS idx_audit_files_user_time ON public.audit_file_uploads(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_files_hash ON public.audit_file_uploads(file_hash);

-- Índices para audit_analysis_runs
CREATE INDEX IF NOT EXISTS idx_audit_analysis_user_time ON public.audit_analysis_runs(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_analysis_type ON public.audit_analysis_runs(analysis_type);

-- Índices para audit_api_calls
CREATE INDEX IF NOT EXISTS idx_audit_api_calls_user_time ON public.audit_api_calls(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_api_calls_provider ON public.audit_api_calls(api_provider);

-- Índices para audit_data_storage
CREATE INDEX IF NOT EXISTS idx_audit_storage_user_time ON public.audit_data_storage(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_storage_type ON public.audit_data_storage(data_type);
CREATE INDEX IF NOT EXISTS idx_audit_storage_expires ON public.audit_data_storage(expires_at) WHERE expires_at IS NOT NULL;

-- Índices para audit_logs
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_time ON public.audit_logs(user_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_audit_logs_table_action ON public.audit_logs(table_name, action);

-- =====================================================
-- 6. FUNCIÓN DE LIMPIEZA AUTOMÁTICA
-- =====================================================

CREATE OR REPLACE FUNCTION cleanup_old_audit_records()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER := 0;
BEGIN
    -- Limpiar actividades más antiguas de 1 año
    DELETE FROM public.audit_user_activities 
    WHERE created_at < NOW() - INTERVAL '1 year';
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    -- Limpiar archivos expirados
    DELETE FROM public.audit_data_storage 
    WHERE expires_at IS NOT NULL AND expires_at < NOW();
    
    -- Limpiar análisis más antiguos de 6 meses
    DELETE FROM public.audit_analysis_runs 
    WHERE created_at < NOW() - INTERVAL '6 months' 
    AND execution_status IN ('completed', 'failed');
    
    -- Limpiar llamadas API más antiguas de 3 meses
    DELETE FROM public.audit_api_calls 
    WHERE created_at < NOW() - INTERVAL '3 months';
    
    -- Limpiar logs más antiguos de 1 año
    DELETE FROM public.audit_logs 
    WHERE timestamp < NOW() - INTERVAL '1 year';
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =====================================================
-- 7. COMENTARIOS PARA DOCUMENTACIÓN
-- =====================================================

COMMENT ON TABLE public.audit_logs IS 'Registro general de todas las operaciones del sistema';
COMMENT ON TABLE public.audit_user_activities IS 'Registro de actividades específicas de usuarios';
COMMENT ON TABLE public.audit_file_uploads IS 'Registro de todos los archivos subidos por usuarios';
COMMENT ON TABLE public.audit_analysis_runs IS 'Registro de todos los análisis y predicciones ejecutados';
COMMENT ON TABLE public.audit_api_calls IS 'Registro de llamadas a APIs externas (Reservo, etc.)';
COMMENT ON TABLE public.audit_data_storage IS 'Registro de datos procesados y almacenados';

COMMENT ON FUNCTION cleanup_old_audit_records() IS 'Función para limpiar registros de auditoría antiguos - ejecutar periódicamente';
COMMENT ON FUNCTION execute_sql(TEXT) IS 'Función para ejecutar SQL dinámico - usar con precaución';

-- =====================================================
-- 8. VERIFICACIÓN FINAL
-- =====================================================

-- Verificar que todas las tablas fueron creadas
SELECT 
    schemaname, 
    tablename, 
    tableowner,
    rowsecurity as "RLS Enabled"
FROM pg_tables 
WHERE schemaname = 'public' 
AND tablename LIKE 'audit_%'
ORDER BY tablename;

-- Verificar políticas RLS
SELECT 
    schemaname,
    tablename,
    policyname,
    permissive,
    roles,
    cmd,
    qual
FROM pg_policies 
WHERE schemaname = 'public' 
AND tablename LIKE 'audit_%'
ORDER BY tablename, policyname;

-- Verificar índices
SELECT 
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes 
WHERE schemaname = 'public' 
AND tablename LIKE 'audit_%'
ORDER BY tablename, indexname;

-- =====================================================
-- SETUP COMPLETADO EXITOSAMENTE
-- =====================================================

-- ✅ Tablas de auditoría creadas con RLS habilitado
-- ✅ Políticas de seguridad configuradas
-- ✅ Índices de performance optimizados  
-- ✅ Función de limpieza automática disponible
-- ✅ Sistema listo para integración con aplicación

-- PRÓXIMOS PASOS:
-- 1. Ejecutar este SQL en Supabase SQL Editor
-- 2. Configurar secrets de Reservo en Streamlit Cloud:
--    [reservo]
--    API_KEY = "TU_API_KEY_AQUI"
--    API_URL = "https://reservo.cl/APIpublica/v2"
-- 3. Integrar audit_manager.py en la aplicación principal
-- 4. Probar funcionalidad de auditoría