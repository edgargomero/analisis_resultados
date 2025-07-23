"""
CEAPSI - Configuración e Integración del Sistema de Auditoría
Integra el sistema de auditoría con la aplicación principal Streamlit
"""

import streamlit as st
import logging
from typing import Optional

# Configurar logging
logger = logging.getLogger('CEAPSI_AUDIT_SETUP')

def initialize_audit_system():
    """
    Inicializa el sistema de auditoría en la aplicación Streamlit
    Debe llamarse al inicio de la aplicación principal
    """
    try:
        # Importar dependencias de auditoría
        from audit_manager import initialize_audit_manager
        from supabase_auth import SupabaseAuthManager
        
        # Obtener cliente Supabase existente
        if hasattr(st.session_state, 'supabase_client') and st.session_state.supabase_client:
            supabase_client = st.session_state.supabase_client
        else:
            # Crear cliente Supabase si no existe
            auth_manager = SupabaseAuthManager()
            if auth_manager.is_available():
                supabase_client = auth_manager.supabase
                st.session_state.supabase_client = supabase_client
            else:
                logger.warning("Supabase no disponible - auditoría deshabilitada")
                return False
        
        # Inicializar audit manager
        audit_manager = initialize_audit_manager(supabase_client)
        
        if audit_manager:
            st.session_state.audit_enabled = True
            logger.info("✅ Sistema de auditoría inicializado")
            
            # Registrar inicio de sesión si hay usuario autenticado
            user = audit_manager._get_current_user()
            if user:
                audit_manager.log_user_login("streamlit_session")
            
            return True
        else:
            logger.error("❌ Error inicializando audit manager")
            return False
            
    except ImportError as e:
        logger.warning(f"Dependencias de auditoría no disponibles: {e}")
        st.session_state.audit_enabled = False
        return False
    except Exception as e:
        logger.error(f"Error inicializando sistema de auditoría: {e}")
        st.session_state.audit_enabled = False
        return False

def require_audit_setup(page_name: str):
    """
    Decorador/función para asegurar que la auditoría está configurada
    y registrar visitas a páginas
    """
    # Verificar si auditoría está habilitada
    if not st.session_state.get('audit_enabled', False):
        initialize_audit_system()
    
    # Registrar visita a página si auditoría disponible
    if st.session_state.get('audit_enabled', False) and 'audit_manager' in st.session_state:
        st.session_state.audit_manager.log_page_visit(page_name)

def get_audit_manager():
    """Obtiene el audit manager activo"""
    if st.session_state.get('audit_enabled', False):
        return st.session_state.get('audit_manager')
    return None

def show_audit_status():
    """Muestra el estado del sistema de auditoría en la barra lateral"""
    if st.session_state.get('audit_enabled', False):
        with st.sidebar:
            st.success("🔍 Auditoría: Activa")
            
            audit_manager = get_audit_manager()
            if audit_manager:
                user = audit_manager._get_current_user()
                if user:
                    st.info(f"👤 Usuario: {user.user_metadata.get('name', user.email) if user.user_metadata else user.email}")
    else:
        with st.sidebar:
            st.warning("🔍 Auditoría: Inactiva")

def audit_page_wrapper(page_function, page_name: str):
    """
    Wrapper para páginas que automatiza el registro de auditoría
    
    Uso:
    def mi_pagina():
        # contenido de la página
        pass
    
    audit_page_wrapper(mi_pagina, "dashboard_principal")
    """
    require_audit_setup(page_name)
    
    try:
        # Ejecutar función de página
        result = page_function()
        
        # Registrar éxito de página
        audit_manager = get_audit_manager()
        if audit_manager:
            audit_manager.log_activity(
                activity_type="page_render_success",
                module_name="streamlit_app",
                activity_description=f"Página renderizada exitosamente: {page_name}",
                activity_details={"page_name": page_name}
            )
        
        return result
        
    except Exception as e:
        # Registrar error de página
        audit_manager = get_audit_manager()
        if audit_manager:
            audit_manager.log_activity(
                activity_type="page_render_error",
                module_name="streamlit_app",
                activity_description=f"Error renderizando página: {page_name}",
                activity_details={
                    "page_name": page_name,
                    "error_message": str(e)
                }
            )
        
        # Re-lanzar excepción
        raise

# Funciones de utilidad para módulos específicos

def audit_data_analysis(analysis_type: str, input_data: str, parameters: dict):
    """Inicia el registro de un análisis de datos"""
    audit_manager = get_audit_manager()
    if audit_manager:
        return audit_manager.log_analysis_run(
            analysis_type=analysis_type,
            input_data_source=input_data,
            parameters=parameters,
            execution_status="started"
        )
    return None

def audit_analysis_complete(record_id: str, results: dict, metrics: dict, output_files: list = None, execution_time: float = None):
    """Completa el registro de un análisis de datos"""
    audit_manager = get_audit_manager()
    if audit_manager and record_id:
        return audit_manager.update_analysis_run(
            record_id=record_id,
            execution_status="completed",
            results_summary=results,
            performance_metrics=metrics,
            output_files=output_files,
            execution_time_seconds=execution_time
        )
    return False

def audit_analysis_error(record_id: str, error_message: str, execution_time: float = None):
    """Registra error en análisis de datos"""
    audit_manager = get_audit_manager()
    if audit_manager and record_id:
        return audit_manager.update_analysis_run(
            record_id=record_id,
            execution_status="failed",
            error_details=error_message,
            execution_time_seconds=execution_time
        )
    return False

def audit_file_save(file_path: str, data_type: str, records_count: int, file_size: int):
    """Registra el guardado de archivos"""
    audit_manager = get_audit_manager()
    if audit_manager:
        return audit_manager.log_data_storage(
            storage_type="file",
            data_type=data_type,
            storage_location=file_path,
            data_size_bytes=file_size,
            records_count=records_count,
            metadata={"saved_from": "streamlit_app"}
        )
    return False

# Función para mostrar dashboard de auditoría (solo para admins)
def show_audit_dashboard():
    """Muestra dashboard de auditoría para administradores"""
    audit_manager = get_audit_manager()
    if not audit_manager:
        st.error("Sistema de auditoría no disponible")
        return
    
    user = audit_manager._get_current_user()
    if not user or user.user_metadata.get('role') != 'admin':
        st.error("Acceso denegado. Se requiere rol de administrador.")
        return
    
    st.title("📊 Dashboard de Auditoría")
    
    # Métricas del sistema
    with st.spinner("Cargando métricas del sistema..."):
        metrics = audit_manager.get_system_metrics()
        
        if metrics:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Actividades Hoy", metrics.get("activities_today", 0))
            with col2:
                st.metric("Archivos Subidos (7d)", metrics.get("files_uploaded_week", 0))
            with col3:
                st.metric("Análisis Ejecutados (7d)", metrics.get("analysis_runs_week", 0))
    
    # Actividad reciente
    st.subheader("📋 Actividad Reciente")
    
    try:
        activities = audit_manager.supabase.table("audit_user_activities") \
            .select("*, users:user_id(email)") \
            .order("created_at", desc=True) \
            .limit(50) \
            .execute()
        
        if activities.data:
            import pandas as pd
            df = pd.DataFrame(activities.data)
            
            # Limpiar y formatear datos
            df['created_at'] = pd.to_datetime(df['created_at'])
            df['user_email'] = df.apply(lambda x: x.get('users', {}).get('email', 'Unknown') if x.get('users') else 'Unknown', axis=1)
            
            # Mostrar tabla
            display_columns = ['created_at', 'user_email', 'activity_type', 'module_name', 'activity_description']
            st.dataframe(
                df[display_columns].rename(columns={
                    'created_at': 'Fecha/Hora',
                    'user_email': 'Usuario',
                    'activity_type': 'Tipo',
                    'module_name': 'Módulo',
                    'activity_description': 'Descripción'
                }),
                use_container_width=True
            )
            
            # Opción de exportar
            if st.button("📥 Exportar Actividades"):
                csv = df.to_csv(index=False)
                st.download_button(
                    label="Descargar CSV",
                    data=csv,
                    file_name=f"audit_activities_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
        else:
            st.info("No hay actividades registradas")
            
    except Exception as e:
        st.error(f"Error cargando actividades: {e}")

# Función para mostrar resumen personal de actividad
def show_user_activity_summary(days: int = 30):
    """Muestra resumen de actividad del usuario actual"""
    audit_manager = get_audit_manager()
    if not audit_manager:
        st.warning("Sistema de auditoría no disponible")
        return
    
    user = audit_manager._get_current_user()
    if not user:
        st.warning("Usuario no autenticado")
        return
    
    st.subheader(f"📈 Mi Actividad (últimos {days} días)")
    
    with st.spinner("Cargando resumen de actividad..."):
        df_activity = audit_manager.get_user_activity_summary(days=days)
        
        if not df_activity.empty:
            # Estadísticas generales
            total_activities = len(df_activity)
            activity_types = df_activity['activity_type'].value_counts()
            modules_used = df_activity['module_name'].nunique()
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Actividades", total_activities)
            with col2:
                st.metric("Tipos de Actividad", len(activity_types))
            with col3:
                st.metric("Módulos Utilizados", modules_used)
            
            # Gráfico de actividades por tipo
            if len(activity_types) > 0:
                st.bar_chart(activity_types)
            
            # Tabla de actividades recientes
            with st.expander("Ver Actividades Detalladas"):
                df_display = df_activity[['created_at', 'activity_type', 'module_name', 'activity_description']].copy()
                df_display['created_at'] = pd.to_datetime(df_display['created_at']).dt.strftime('%Y-%m-%d %H:%M')
                
                st.dataframe(
                    df_display.rename(columns={
                        'created_at': 'Fecha/Hora',
                        'activity_type': 'Tipo',
                        'module_name': 'Módulo',
                        'activity_description': 'Descripción'
                    }),
                    use_container_width=True
                )
        else:
            st.info(f"No hay actividades registradas en los últimos {days} días")

# Configuración de cleanup automático (llamar periódicamente)
def setup_audit_cleanup():
    """Configura la limpieza automática de registros de auditoría"""
    try:
        audit_manager = get_audit_manager()
        if audit_manager:
            # Ejecutar función de limpieza
            result = audit_manager.supabase.rpc('cleanup_old_audit_records').execute()
            if result.data:
                logger.info(f"Limpieza de auditoría completada: {result.data} registros eliminados")
            return True
    except Exception as e:
        logger.error(f"Error en limpieza de auditoría: {e}")
        return False