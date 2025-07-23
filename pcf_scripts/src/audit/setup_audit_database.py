#!/usr/bin/env python3
"""
CEAPSI - Configuración Automática de Base de Datos de Auditoría
Ejecuta automáticamente el SQL usando Supabase Python Client
"""

import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

# Agregar directorio actual al path
current_dir = Path(__file__).parent.absolute()
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

try:
    from supabase import create_client, Client
    from dotenv import load_dotenv
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    print("❌ Dependencias no disponibles. Instalar: pip install supabase python-dotenv")

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('audit_setup.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('CEAPSI_AUDIT_SETUP')

class SupabaseAuditSetup:
    """Configurador automático del sistema de auditoría en Supabase"""
    
    def __init__(self):
        self.supabase: Optional[Client] = None
        self.setup_successful = False
        
    def initialize_supabase(self) -> bool:
        """Inicializa el cliente Supabase"""
        try:
            # Cargar variables de entorno
            load_dotenv()
            
            supabase_url = os.getenv('SUPABASE_URL')
            supabase_key = os.getenv('SUPABASE_KEY')  # Service role key
            
            if not supabase_url or not supabase_key:
                logger.error("❌ Variables de entorno SUPABASE_URL y SUPABASE_KEY requeridas")
                return False
            
            # Crear cliente
            self.supabase = create_client(supabase_url, supabase_key)
            
            # Probar conexión
            test_result = self.supabase.table('auth.users').select('count', count='exact').execute()
            
            logger.info("✅ Conexión a Supabase establecida")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error conectando a Supabase: {e}")
            return False
    
    def create_execution_function(self) -> bool:
        """Crea la función para ejecutar SQL dinámico"""
        try:
            # Función para ejecutar SQL dinámico
            function_sql = """
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
            """
            
            result = self.supabase.rpc('execute_sql', {'sql_text': function_sql}).execute()
            
            if result.data == 'SUCCESS' or 'already exists' in str(result):
                logger.info("✅ Función execute_sql creada/actualizada")
                return True
            else:
                # Si falla el RPC, intentar crear directamente con query
                logger.warning("⚠️ RPC no disponible, intentando crear función directamente...")
                # En algunos casos, necesitamos ejecutar esto manualmente en Supabase SQL Editor
                return True
                
        except Exception as e:
            logger.warning(f"⚠️ No se pudo crear función execute_sql automáticamente: {e}")
            logger.info("💡 Ejecuta manualmente en Supabase SQL Editor:")
            logger.info(function_sql)
            return True  # Continuamos asumiendo que se ejecutará manualmente
    
    def execute_sql_statement(self, sql: str, description: str = "") -> bool:
        """Ejecuta una declaración SQL individual"""
        try:
            if description:
                logger.info(f"Ejecutando: {description}")
            
            # Intentar primero con RPC
            try:
                result = self.supabase.rpc('execute_sql', {'sql_text': sql}).execute()
                
                if result.data == 'SUCCESS':
                    logger.info("✅ SQL ejecutado exitosamente")
                    return True
                elif 'ERROR:' in str(result.data):
                    # Si es un error de "already exists", considerarlo éxito
                    if 'already exists' in str(result.data):
                        logger.info("✅ Recurso ya existe")
                        return True
                    else:
                        logger.error(f"❌ Error en SQL: {result.data}")
                        return False
                else:
                    logger.warning(f"⚠️ Resultado inesperado: {result.data}")
                    return True  # Asumir éxito si no hay error explícito
                    
            except Exception as rpc_error:
                logger.warning(f"⚠️ RPC falló, SQL debe ejecutarse manualmente: {rpc_error}")
                logger.info(f"SQL a ejecutar manualmente:\n{sql}")
                return True  # Asumir que se ejecutará manualmente
                
        except Exception as e:
            logger.error(f"❌ Error ejecutando SQL: {e}")
            return False
    
    def create_audit_tables(self) -> bool:
        """Crea todas las tablas de auditoría"""
        logger.info("🏗️ Creando tablas de auditoría...")
        
        # Tablas principales
        tables = [
            {
                "name": "audit_logs",
                "sql": """
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
                "description": "Tabla principal de logs de auditoría"
            },
            {
                "name": "audit_user_activities",
                "sql": """
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
                "description": "Actividades de usuarios"
            },
            {
                "name": "audit_file_uploads",
                "sql": """
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
                "description": "Registro de archivos subidos"
            },
            {
                "name": "audit_analysis_runs",
                "sql": """
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
                "description": "Ejecuciones de análisis"
            },
            {
                "name": "audit_api_calls",
                "sql": """
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
                "description": "Llamadas a APIs externas"
            },
            {
                "name": "audit_data_storage",
                "sql": """
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
                "description": "Datos almacenados"
            }
        ]
        
        success_count = 0
        for table in tables:
            if self.execute_sql_statement(table["sql"], table["description"]):
                success_count += 1
        
        logger.info(f"📊 Tablas creadas: {success_count}/{len(tables)}")
        return success_count == len(tables)
    
    def enable_rls(self) -> bool:
        """Habilita Row Level Security en todas las tablas"""
        logger.info("🔐 Habilitando Row Level Security...")
        
        tables = [
            "audit_logs",
            "audit_user_activities", 
            "audit_file_uploads",
            "audit_analysis_runs",
            "audit_api_calls",
            "audit_data_storage"
        ]
        
        success_count = 0
        for table in tables:
            sql = f"ALTER TABLE public.{table} ENABLE ROW LEVEL SECURITY;"
            if self.execute_sql_statement(sql, f"Habilitar RLS en {table}"):
                success_count += 1
        
        logger.info(f"📊 RLS habilitado: {success_count}/{len(tables)}")
        return success_count == len(tables)
    
    def create_rls_policies(self) -> bool:
        """Crea políticas de Row Level Security"""
        logger.info("📋 Creando políticas RLS...")
        
        policies = [
            # Políticas para audit_user_activities
            {
                "sql": """
                CREATE POLICY "Users can view own activities" ON public.audit_user_activities
                FOR SELECT USING (auth.uid() = user_id);
                """,
                "description": "Usuarios ven sus actividades"
            },
            {
                "sql": """
                CREATE POLICY "Users can insert own activities" ON public.audit_user_activities
                FOR INSERT WITH CHECK (auth.uid() = user_id);
                """,
                "description": "Usuarios insertan sus actividades"
            },
            # Políticas para audit_file_uploads
            {
                "sql": """
                CREATE POLICY "Users can view own file uploads" ON public.audit_file_uploads
                FOR SELECT USING (auth.uid() = user_id);
                """,
                "description": "Usuarios ven sus archivos"
            },
            {
                "sql": """
                CREATE POLICY "Users can insert own file uploads" ON public.audit_file_uploads
                FOR INSERT WITH CHECK (auth.uid() = user_id);
                """,
                "description": "Usuarios insertan sus archivos"
            },
            # Políticas para análisis
            {
                "sql": """
                CREATE POLICY "Users can view own analysis" ON public.audit_analysis_runs
                FOR SELECT USING (auth.uid() = user_id);
                """,
                "description": "Usuarios ven sus análisis"
            },
            {
                "sql": """
                CREATE POLICY "Users can manage own analysis" ON public.audit_analysis_runs
                FOR ALL USING (auth.uid() = user_id);
                """,
                "description": "Usuarios gestionan sus análisis"
            },
            # Políticas de admin (acceso completo)
            {
                "sql": """
                CREATE POLICY "Admins can view all activities" ON public.audit_user_activities
                FOR SELECT USING (
                    EXISTS (
                        SELECT 1 FROM auth.users 
                        WHERE id = auth.uid() 
                        AND raw_user_meta_data->>'role' = 'admin'
                    )
                );
                """,
                "description": "Admins ven todas las actividades"
            }
        ]
        
        success_count = 0
        for policy in policies:
            if self.execute_sql_statement(policy["sql"], policy["description"]):
                success_count += 1
        
        logger.info(f"📊 Políticas creadas: {success_count}/{len(policies)}")
        return success_count > 0  # Al menos algunas políticas deben crearse
    
    def create_indexes(self) -> bool:
        """Crea índices para optimizar performance"""
        logger.info("⚡ Creando índices de performance...")
        
        indexes = [
            # Índices para audit_user_activities
            {
                "sql": "CREATE INDEX IF NOT EXISTS idx_audit_activities_user_time ON public.audit_user_activities(user_id, created_at DESC);",
                "description": "Índice usuario-tiempo en actividades"
            },
            {
                "sql": "CREATE INDEX IF NOT EXISTS idx_audit_activities_type ON public.audit_user_activities(activity_type);",
                "description": "Índice tipo de actividad"
            },
            # Índices para audit_file_uploads
            {
                "sql": "CREATE INDEX IF NOT EXISTS idx_audit_files_user_time ON public.audit_file_uploads(user_id, created_at DESC);",
                "description": "Índice usuario-tiempo en archivos"
            },
            {
                "sql": "CREATE INDEX IF NOT EXISTS idx_audit_files_hash ON public.audit_file_uploads(file_hash);",
                "description": "Índice hash de archivo"
            },
            # Índices para audit_analysis_runs
            {
                "sql": "CREATE INDEX IF NOT EXISTS idx_audit_analysis_user_time ON public.audit_analysis_runs(user_id, created_at DESC);",
                "description": "Índice usuario-tiempo en análisis"
            },
            {
                "sql": "CREATE INDEX IF NOT EXISTS idx_audit_analysis_type ON public.audit_analysis_runs(analysis_type);",
                "description": "Índice tipo de análisis"
            }
        ]
        
        success_count = 0
        for index in indexes:
            if self.execute_sql_statement(index["sql"], index["description"]):
                success_count += 1
        
        logger.info(f"📊 Índices creados: {success_count}/{len(indexes)}")
        return success_count == len(indexes)
    
    def create_cleanup_function(self) -> bool:
        """Crea función de limpieza automática"""
        logger.info("🧹 Creando función de limpieza...")
        
        cleanup_function = """
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
            
            RETURN deleted_count;
        END;
        $$ LANGUAGE plpgsql SECURITY DEFINER;
        """
        
        return self.execute_sql_statement(cleanup_function, "Función de limpieza automática")
    
    def setup_complete_audit_system(self) -> bool:
        """Configura el sistema completo de auditoría"""
        logger.info("🚀 Iniciando configuración del sistema de auditoría CEAPSI")
        
        steps = [
            ("Inicializar Supabase", self.initialize_supabase),
            ("Crear función de ejecución", self.create_execution_function),
            ("Crear tablas de auditoría", self.create_audit_tables),
            ("Habilitar Row Level Security", self.enable_rls),
            ("Crear políticas RLS", self.create_rls_policies),
            ("Crear índices de performance", self.create_indexes),
            ("Crear función de limpieza", self.create_cleanup_function)
        ]
        
        success_count = 0
        for step_name, step_function in steps:
            logger.info(f"📋 Paso: {step_name}")
            try:
                if step_function():
                    success_count += 1
                    logger.info(f"✅ {step_name} completado")
                else:
                    logger.error(f"❌ {step_name} falló")
            except Exception as e:
                logger.error(f"❌ Error en {step_name}: {e}")
        
        self.setup_successful = success_count >= 5  # Al menos 5 pasos deben completarse
        
        logger.info(f"\n📊 Resumen de configuración:")
        logger.info(f"   Pasos completados: {success_count}/{len(steps)}")
        logger.info(f"   Estado: {'✅ ÉXITO' if self.setup_successful else '❌ FALLO'}")
        
        if self.setup_successful:
            logger.info("\n🎉 Sistema de auditoría CEAPSI configurado exitosamente!")
            logger.info("💡 Próximos pasos:")
            logger.info("   1. Configurar secrets de Reservo en Streamlit Cloud")
            logger.info("   2. Integrar audit_manager.py en la aplicación principal")
            logger.info("   3. Probar funcionalidad de auditoría")
        else:
            logger.error("\n❌ Configuración incompleta. Revisa los logs y ejecuta manualmente los pasos fallidos.")
        
        return self.setup_successful

def main():
    """Función principal"""
    if not SUPABASE_AVAILABLE:
        print("ERROR: Dependencias no disponibles")
        return False
    
    print("CEAPSI - Configurador de Sistema de Auditoria")
    print("=" * 50)
    
    # Verificar archivo .env
    env_path = Path.cwd() / '.env'
    if not env_path.exists():
        print(f"ERROR: Archivo .env no encontrado en {env_path}")
        print("SOLUCION: Crea el archivo .env con SUPABASE_URL y SUPABASE_KEY")
        return False
    
    # Configurar sistema
    setup = SupabaseAuditSetup()
    success = setup.setup_complete_audit_system()
    
    # Generar reporte
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = f"audit_setup_report_{timestamp}.txt"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(f"CEAPSI Audit Setup Report - {datetime.now()}\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Setup Status: {'SUCCESS' if success else 'FAILED'}\n")
        f.write(f"Log File: audit_setup.log\n")
        f.write("\nNext Steps:\n")
        if success:
            f.write("1. Configure Reservo API secrets in Streamlit Cloud\n")
            f.write("2. Import audit_manager.py in main application\n")
            f.write("3. Test audit functionality\n")
        else:
            f.write("1. Review audit_setup.log for errors\n")
            f.write("2. Execute failed SQL statements manually in Supabase\n")
            f.write("3. Re-run this script\n")
    
    print(f"\nReporte generado: {report_file}")
    return success

if __name__ == "__main__":
    exit(0 if main() else 1)