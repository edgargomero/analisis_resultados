"""
CEAPSI - Historial de Sesiones de Análisis
Interfaz para ver y gestionar sesiones previas de análisis
"""

import streamlit as st
import pandas as pd
import json
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Optional

def mostrar_historial_sesiones():
    """Muestra el historial completo de sesiones de análisis"""
    
    st.title("📚 Historial de Sesiones de Análisis")
    st.markdown("---")
    
    try:
        from core.mcp_session_manager import get_mcp_session_manager
        session_manager = get_mcp_session_manager()
        
        # Obtener ID de usuario (por defecto anonymous_user)
        user_id = st.session_state.get('user_id', 'anonymous_user')
        
        # Controles de filtrado
        col1, col2, col3 = st.columns(3)
        
        with col1:
            limit = st.selectbox("Mostrar últimas:", [10, 25, 50, 100], index=1)
            
        with col2:
            status_filter = st.selectbox("Estado:", ["Todas", "completed", "created", "failed"])
            
        with col3:
            if st.button("🔄 Actualizar", use_container_width=True):
                st.rerun()
        
        # Cargar sesiones
        sessions = session_manager.list_user_sessions(user_id, limit)
        
        if not sessions:
            st.info("📝 No hay sesiones de análisis registradas")
            st.markdown("""
            ### ¿Cómo crear una sesión?
            1. Ve a la página principal (**🏠 Inicio**)
            2. Sube un archivo CSV o Excel con datos de llamadas
            3. Ejecuta el pipeline completo
            4. Los resultados se guardarán automáticamente aquí
            """)
            return
        
        # Filtrar por estado si se especifica
        if status_filter != "Todas":
            sessions = [s for s in sessions if s.get('status') == status_filter]
        
        # Estadísticas generales
        st.subheader("📊 Estadísticas Generales")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Sesiones", len(sessions))
            
        with col2:
            completed_sessions = len([s for s in sessions if s.get('status') == 'completed'])
            st.metric("Completadas", completed_sessions)
            
        with col3:
            if sessions:
                avg_files_size = sum(s.get('file_info', {}).get('records_count', 0) for s in sessions) / len(sessions)
                st.metric("Promedio Registros", f"{avg_files_size:.0f}")
            else:
                st.metric("Promedio Registros", "0")
                
        with col4:
            recent_sessions = len([s for s in sessions if datetime.fromisoformat(s['created_at'].replace('Z', '+00:00')) > datetime.now().replace(tzinfo=None) - timedelta(days=7)])
            st.metric("Última Semana", recent_sessions)
        
        # Gráfico de sesiones por tiempo
        if sessions:
            st.subheader("📈 Actividad de Análisis")
            
            # Preparar datos para gráfico
            session_dates = []
            for session in sessions:
                try:
                    date_str = session['created_at'].replace('Z', '+00:00')
                    date = datetime.fromisoformat(date_str)
                    session_dates.append(date.date())
                except:
                    continue
            
            if session_dates:
                df_dates = pd.DataFrame({'fecha': session_dates})
                df_dates_count = df_dates.groupby('fecha').size().reset_index(name='sesiones')
                
                fig = px.bar(
                    df_dates_count, 
                    x='fecha', 
                    y='sesiones',
                    title="Sesiones de Análisis por Día",
                    color='sesiones',
                    color_continuous_scale='Blues'
                )
                st.plotly_chart(fig, use_container_width=True)
        
        # Lista detallada de sesiones
        st.subheader("📋 Sesiones Detalladas")
        
        for i, session in enumerate(sessions):
            with st.expander(f"🔍 Sesión {i+1}: {session.get('file_info', {}).get('filename', 'Sin nombre')} - {session.get('status', 'unknown').upper()}", expanded=i==0):
                
                # Información básica
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Información Básica:**")
                    st.write(f"• **ID Sesión:** `{session['session_id'][:8]}...`")
                    st.write(f"• **Estado:** {session.get('status', 'unknown').upper()}")
                    st.write(f"• **Tipo:** {session.get('analysis_type', 'N/A')}")
                    
                    try:
                        created_date = datetime.fromisoformat(session['created_at'].replace('Z', '+00:00'))
                        st.write(f"• **Creada:** {created_date.strftime('%Y-%m-%d %H:%M:%S')}")
                    except:
                        st.write(f"• **Creada:** {session.get('created_at', 'N/A')}")
                
                with col2:
                    st.write("**Archivo Procesado:**")
                    file_info = session.get('file_info', {})
                    if file_info:
                        st.write(f"• **Nombre:** {file_info.get('filename', 'N/A')}")
                        st.write(f"• **Registros:** {file_info.get('records_count', 'N/A'):,}")
                        st.write(f"• **Columnas:** {len(file_info.get('columns', []))}")
                        if file_info.get('size'):
                            size_kb = file_info['size'] / 1024
                            st.write(f"• **Tamaño:** {size_kb:.1f} KB")
                
                # Mostrar resumen de resultados si está disponible
                if session.get('results_summary'):
                    st.write("**Resumen de Resultados:**")
                    summary = session['results_summary']
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if summary.get('has_predictions'):
                            st.success("✅ Predicciones generadas")
                        else:
                            st.info("ℹ️ Sin predicciones")
                    
                    with col2:
                        if summary.get('has_models'):
                            st.success("✅ Modelos entrenados")
                        else:
                            st.info("ℹ️ Sin modelos")
                    
                    with col3:
                        total_keys = summary.get('total_keys', 0)
                        st.info(f"📊 {total_keys} elementos")
                    
                    # Período de predicción
                    if summary.get('prediction_period'):
                        period = summary['prediction_period']
                        st.write(f"**Período de Predicción:** {period.get('start', 'N/A')} → {period.get('end', 'N/A')} ({period.get('days', 0)} días)")
                    
                    # Métricas de modelos
                    if summary.get('model_metrics'):
                        st.write("**Métricas de Modelos:**")
                        metrics = summary['model_metrics']
                        cols = st.columns(min(len(metrics), 4))
                        for j, (metric, value) in enumerate(metrics.items()):
                            if j < len(cols):
                                cols[j].metric(metric.upper(), f"{value:.2f}")
                
                # Botones de acción
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button(f"🔍 Ver Detalles", key=f"details_{session['session_id']}", use_container_width=True):
                        mostrar_detalles_sesion(session)
                
                with col2:
                    if st.button(f"📊 Cargar en Dashboard", key=f"load_{session['session_id']}", use_container_width=True):
                        cargar_sesion_en_dashboard(session['session_id'])
                
                with col3:
                    if st.button(f"🗑️ Eliminar", key=f"delete_{session['session_id']}", use_container_width=True, type="secondary"):
                        if st.session_state.get(f"confirm_delete_{session['session_id']}", False):
                            eliminar_sesion(session['session_id'])
                        else:
                            st.session_state[f"confirm_delete_{session['session_id']}"] = True
                            st.warning("⚠️ Haz clic de nuevo para confirmar eliminación")
                            st.rerun()
        
    except Exception as e:
        st.error(f"Error cargando historial: {e}")
        st.info("💡 Asegúrate de que la base de datos esté configurada correctamente")

def mostrar_detalles_sesion(session: Dict):
    """Muestra detalles completos de una sesión"""
    
    st.subheader(f"🔍 Detalles de Sesión: {session.get('file_info', {}).get('filename', 'Sin nombre')}")
    
    # Mostrar JSON completo de la sesión (excepto datos binarios)
    session_display = session.copy()
    if 'analysis_results' in session_display:
        session_display['analysis_results'] = "(...datos binarios ocultos...)"
    
    st.json(session_display)

def cargar_sesion_en_dashboard(session_id: str):
    """Carga una sesión específica en el dashboard"""
    
    try:
        from core.mcp_session_manager import get_mcp_session_manager
        session_manager = get_mcp_session_manager()
        
        # Cargar datos de la sesión
        session_data = session_manager.load_analysis_session(session_id)
        
        if session_data and session_data.get('analysis_results'):
            # Cargar resultados en session_state
            st.session_state.resultados_pipeline = session_data['analysis_results']
            st.session_state.pipeline_completado = True
            st.session_state.current_session_id = session_id
            
            st.success("✅ Sesión cargada en el dashboard")
            st.info("💡 Ve a la página **📊 Dashboard** para ver los resultados")
        else:
            st.error("❌ No se encontraron resultados para esta sesión")
            
    except Exception as e:
        st.error(f"Error cargando sesión: {e}")

def eliminar_sesion(session_id: str):
    """Elimina una sesión específica"""
    
    try:
        from core.mcp_session_manager import get_mcp_session_manager
        session_manager = get_mcp_session_manager()
        
        success = session_manager.delete_session(session_id)
        
        if success:
            st.success("✅ Sesión eliminada correctamente")
            # Limpiar estado de confirmación
            if f"confirm_delete_{session_id}" in st.session_state:
                del st.session_state[f"confirm_delete_{session_id}"]
            st.rerun()
        else:
            st.error("❌ Error eliminando sesión")
            
    except Exception as e:
        st.error(f"Error eliminando sesión: {e}")

# Función principal para integrar en la app
def main():
    """Función principal del módulo"""
    mostrar_historial_sesiones()