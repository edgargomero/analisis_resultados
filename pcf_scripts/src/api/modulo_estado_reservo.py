#!/usr/bin/env python3
"""
CEAPSI - Módulo de Estado de Integración con Reservo
Muestra el estado de conexión, configuración y estadísticas de uso de la API de Reservo
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import requests
import os
import time
from typing import Dict, Any, Optional, List
import logging

# Importar dependencias del proyecto
try:
    from preparacion_datos import IntegradorReservo
    from audit_manager import SupabaseAuditManager
    DEPENDENCIES_AVAILABLE = True
except ImportError:
    DEPENDENCIES_AVAILABLE = False

# Configurar logging
logger = logging.getLogger('CEAPSI_ESTADO_RESERVO')

class EstadoIntegracionReservo:
    """Gestor del estado de integración con Reservo"""
    
    def __init__(self):
        self.api_key = None
        self.api_url = "https://reservo.cl/APIpublica/v2"
        self.integrador = None
        self.audit_manager = None
        self._initialize_config()
        self._initialize_audit()
    
    def _initialize_config(self):
        """Inicializa la configuración de Reservo"""
        try:
            # Prioridad 1: Streamlit secrets (formato plano)
            if hasattr(st, 'secrets'):
                # Buscar en formato plano primero
                if 'RESERVO_API_KEY' in st.secrets:
                    self.api_key = st.secrets['RESERVO_API_KEY']
                    self.api_url = st.secrets.get('RESERVO_API_URL', self.api_url)
                # Luego buscar en formato anidado por compatibilidad
                elif 'reservo' in st.secrets:
                    self.api_key = st.secrets["reservo"].get("API_KEY")
                    self.api_url = st.secrets["reservo"].get("API_URL", self.api_url)
            
            # Prioridad 2: Variables de entorno
            if not self.api_key and os.getenv('RESERVO_API_KEY'):
                self.api_key = os.getenv('RESERVO_API_KEY')
                self.api_url = os.getenv('RESERVO_API_URL', self.api_url)
            
            # Crear integrador si hay API key
            if self.api_key and DEPENDENCIES_AVAILABLE:
                self.integrador = IntegradorReservo(self.api_key, self.api_url)
                
        except Exception as e:
            logger.error(f"Error inicializando configuración Reservo: {e}")
    
    def _initialize_audit(self):
        """Inicializa el sistema de auditoría"""
        try:
            if hasattr(st.session_state, 'audit_manager'):
                self.audit_manager = st.session_state.audit_manager
        except Exception as e:
            logger.warning(f"Sistema de auditoría no disponible: {e}")
    
    def check_api_connection(self) -> Dict[str, Any]:
        """Verifica la conexión con la API de Reservo"""
        if not self.integrador:
            return {
                "status": "error",
                "message": "API Key no configurada",
                "details": "Configura RESERVO_API_KEY en secrets o variables de entorno",
                "response_time": 0,
                "timestamp": datetime.now()
            }
        
        try:
            start_time = time.time()
            conectado, mensaje = self.integrador.test_conexion()
            response_time = (time.time() - start_time) * 1000  # ms
            
            # Registrar en auditoría
            if self.audit_manager:
                self.audit_manager.log_api_call(
                    api_provider="reservo",
                    endpoint="/test",
                    method="GET",
                    request_parameters={},
                    response_status=200 if conectado else 500,
                    response_time_ms=int(response_time),
                    success=conectado
                )
            
            return {
                "status": "success" if conectado else "error",
                "message": mensaje,
                "response_time": response_time,
                "timestamp": datetime.now(),
                "api_url": self.api_url
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error de conexión: {str(e)}",
                "response_time": 0,
                "timestamp": datetime.now()
            }
    
    def get_api_usage_stats(self, days: int = 30) -> Dict[str, Any]:
        """Obtiene estadísticas de uso de la API"""
        if not self.audit_manager:
            return {"error": "Sistema de auditoría no disponible"}
        
        try:
            # Calcular fecha límite
            fecha_limite = datetime.now() - timedelta(days=days)
            
            # Consultar llamadas a la API de Reservo
            result = self.audit_manager.supabase.table("audit_api_calls") \
                .select("*") \
                .eq("api_provider", "reservo") \
                .gte("created_at", fecha_limite.isoformat()) \
                .order("created_at", desc=True) \
                .execute()
            
            if not result.data:
                return {
                    "total_calls": 0,
                    "successful_calls": 0,
                    "failed_calls": 0,
                    "avg_response_time": 0,
                    "records_retrieved": 0,
                    "last_call": None,
                    "endpoints_used": [],
                    "daily_usage": {}
                }
            
            df = pd.DataFrame(result.data)
            df['created_at'] = pd.to_datetime(df['created_at'])
            df['date'] = df['created_at'].dt.date
            
            # Calcular métricas
            total_calls = len(df)
            successful_calls = df['success'].sum()
            failed_calls = total_calls - successful_calls
            avg_response_time = df['response_time_ms'].mean()
            records_retrieved = df['records_retrieved'].sum()
            last_call = df['created_at'].max() if not df.empty else None
            
            # Endpoints más usados
            endpoints_used = df['endpoint'].value_counts().head(5).to_dict()
            
            # Uso diario
            daily_usage = df.groupby('date').agg({
                'id': 'count',
                'success': 'sum',
                'response_time_ms': 'mean',
                'records_retrieved': 'sum'
            }).to_dict('index')
            
            return {
                "total_calls": total_calls,
                "successful_calls": int(successful_calls),
                "failed_calls": failed_calls,
                "avg_response_time": avg_response_time,
                "records_retrieved": int(records_retrieved),
                "last_call": last_call,
                "endpoints_used": endpoints_used,
                "daily_usage": daily_usage,
                "success_rate": (successful_calls / total_calls * 100) if total_calls > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas de API: {e}")
            return {"error": str(e)}
    
    def get_recent_api_calls(self, limit: int = 10) -> pd.DataFrame:
        """Obtiene las llamadas más recientes a la API"""
        if not self.audit_manager:
            return pd.DataFrame()
        
        try:
            result = self.audit_manager.supabase.table("audit_api_calls") \
                .select("*") \
                .eq("api_provider", "reservo") \
                .order("created_at", desc=True) \
                .limit(limit) \
                .execute()
            
            if result.data:
                df = pd.DataFrame(result.data)
                df['created_at'] = pd.to_datetime(df['created_at'])
                return df
            else:
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"Error obteniendo llamadas recientes: {e}")
            return pd.DataFrame()
    
    def test_api_endpoints(self) -> Dict[str, Dict[str, Any]]:
        """Prueba diferentes endpoints de la API"""
        if not self.integrador:
            return {"error": "Integrador no disponible"}
        
        endpoints_to_test = [
            {
                "name": "Conexión General",
                "method": "test_conexion",
                "description": "Prueba la conectividad básica"
            },
            {
                "name": "Profesionales", 
                "method": "obtener_profesionales",
                "description": "Lista de profesionales disponibles"
            }
        ]
        
        results = {}
        
        for endpoint in endpoints_to_test:
            try:
                start_time = time.time()
                
                if endpoint["method"] == "test_conexion":
                    conectado, mensaje = self.integrador.test_conexion()
                    success = conectado
                    data_count = 0
                elif endpoint["method"] == "obtener_profesionales":
                    resultado = self.integrador.obtener_profesionales()
                    success = resultado is not None and not resultado.empty
                    data_count = len(resultado) if success else 0
                    mensaje = f"{data_count} profesionales encontrados" if success else "No se pudieron obtener profesionales"
                else:
                    success = False
                    mensaje = "Método no implementado"
                    data_count = 0
                
                response_time = (time.time() - start_time) * 1000
                
                results[endpoint["name"]] = {
                    "success": success,
                    "message": mensaje,
                    "response_time_ms": response_time,
                    "data_count": data_count,
                    "description": endpoint["description"]
                }
                
            except Exception as e:
                results[endpoint["name"]] = {
                    "success": False,
                    "message": f"Error: {str(e)}",
                    "response_time_ms": 0,
                    "data_count": 0,
                    "description": endpoint["description"]
                }
        
        return results


def mostrar_estado_reservo():
    """Función principal para mostrar el estado de integración con Reservo"""
    
    # Configurar página
    st.title("🔗 Estado de Integración con Reservo")
    st.markdown("---")
    
    # Inicializar gestor de estado
    estado = EstadoIntegracionReservo()
    
    # Sidebar con controles
    with st.sidebar:
        st.subheader("⚙️ Controles")
        
        # Botón para refrescar
        if st.button("🔄 Refrescar Estado", type="primary"):
            st.rerun()
        
        # Configuración de días para estadísticas
        days_for_stats = st.selectbox(
            "Período para stats",
            [7, 15, 30, 60, 90],
            index=2
        )
        
        # Información de configuración
        st.subheader("📋 Configuración")
        
        if estado.api_key:
            st.success("✅ API Key configurada")
            st.info(f"🌐 Endpoint: {estado.api_url}")
        else:
            st.error("❌ API Key no configurada")
            st.markdown("""
            **Para configurar:**
            1. Agrega en Streamlit secrets:
            ```toml
            [reservo]
            API_KEY = "tu-api-key"
            API_URL = "https://reservo.cl/APIpublica/v2"
            ```
            """)
    
    # Sección principal: Estado de conexión
    st.subheader("🔗 Estado de Conexión")
    
    with st.spinner("Verificando conexión con Reservo..."):
        connection_status = estado.check_api_connection()
    
    # Mostrar estado en columnas
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if connection_status["status"] == "success":
            st.metric("Estado", "🟢 Conectado")
        else:
            st.metric("Estado", "🔴 Desconectado")
    
    with col2:
        st.metric("Tiempo Respuesta", f"{connection_status['response_time']:.0f} ms")
    
    with col3:
        st.metric("Endpoint", estado.api_url.split('//')[-1])
    
    with col4:
        st.metric("Última Verificación", connection_status["timestamp"].strftime("%H:%M:%S"))
    
    # Mensaje de estado detallado
    if connection_status["status"] == "success":
        st.success(f"✅ {connection_status['message']}")
    else:
        st.error(f"❌ {connection_status['message']}")
        if "details" in connection_status:
            st.info(f"💡 {connection_status['details']}")
    
    st.markdown("---")
    
    # Sección: Prueba de endpoints
    st.subheader("🧪 Prueba de Endpoints")
    
    if estado.integrador:
        if st.button("🔍 Probar Todos los Endpoints"):
            with st.spinner("Probando endpoints..."):
                test_results = estado.test_api_endpoints()
            
            if "error" not in test_results:
                # Mostrar resultados en tabla
                results_data = []
                for name, result in test_results.items():
                    results_data.append({
                        "Endpoint": name,
                        "Estado": "✅ OK" if result["success"] else "❌ Error",
                        "Mensaje": result["message"],
                        "Tiempo (ms)": f"{result['response_time_ms']:.0f}",
                        "Datos": result["data_count"],
                        "Descripción": result["description"]
                    })
                
                df_results = pd.DataFrame(results_data)
                st.dataframe(df_results, use_container_width=True)
            else:
                st.error(f"Error probando endpoints: {test_results['error']}")
    else:
        st.warning("⚠️ Configura la API Key para probar endpoints")
    
    st.markdown("---")
    
    # Sección: Estadísticas de uso
    st.subheader("📊 Estadísticas de Uso")
    
    if estado.audit_manager:
        with st.spinner("Cargando estadísticas..."):
            stats = estado.get_api_usage_stats(days=days_for_stats)
        
        if "error" not in stats:
            # Métricas principales
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Llamadas", stats["total_calls"])
            with col2:
                st.metric("Exitosas", stats["successful_calls"])
            with col3:
                st.metric("Fallidas", stats["failed_calls"])
            with col4:
                st.metric("Tasa Éxito", f"{stats['success_rate']:.1f}%")
            
            # Segunda fila de métricas
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Tiempo Promedio", f"{stats['avg_response_time']:.0f} ms")
            with col2:
                st.metric("Registros Obtenidos", stats["records_retrieved"])
            with col3:
                if stats["last_call"]:
                    last_call_str = stats["last_call"].strftime("%d/%m %H:%M")
                    st.metric("Última Llamada", last_call_str)
                else:
                    st.metric("Última Llamada", "N/A")
            with col4:
                endpoints_count = len(stats["endpoints_used"])
                st.metric("Endpoints Usados", endpoints_count)
            
            # Gráfico de uso diario
            if stats["daily_usage"]:
                st.subheader("📈 Uso Diario")
                
                daily_data = []
                for date, data in stats["daily_usage"].items():
                    daily_data.append({
                        "Fecha": date,
                        "Llamadas": data["id"],
                        "Exitosas": data["success"],
                        "Tiempo Promedio (ms)": data["response_time_ms"],
                        "Registros": data["records_retrieved"]
                    })
                
                df_daily = pd.DataFrame(daily_data)
                df_daily = df_daily.sort_values("Fecha")
                
                # Gráfico de líneas
                fig = go.Figure()
                
                fig.add_trace(go.Scatter(
                    x=df_daily["Fecha"],
                    y=df_daily["Llamadas"],
                    mode='lines+markers',
                    name='Total Llamadas',
                    line=dict(color='blue')
                ))
                
                fig.add_trace(go.Scatter(
                    x=df_daily["Fecha"],
                    y=df_daily["Exitosas"],
                    mode='lines+markers',
                    name='Llamadas Exitosas',
                    line=dict(color='green')
                ))
                
                fig.update_layout(
                    title="Uso Diario de API Reservo",
                    xaxis_title="Fecha",
                    yaxis_title="Número de Llamadas",
                    hovermode='x unified'
                )
                
                st.plotly_chart(fig, use_container_width=True)
            
            # Endpoints más usados
            if stats["endpoints_used"]:
                st.subheader("🎯 Endpoints Más Usados")
                
                endpoints_df = pd.DataFrame(
                    list(stats["endpoints_used"].items()),
                    columns=["Endpoint", "Uso"]
                )
                
                fig_pie = px.pie(
                    endpoints_df,
                    values="Uso",
                    names="Endpoint",
                    title="Distribución de Uso por Endpoint"
                )
                
                st.plotly_chart(fig_pie, use_container_width=True)
        
        else:
            st.error(f"Error cargando estadísticas: {stats['error']}")
    
    else:
        st.warning("⚠️ Sistema de auditoría no disponible. Las estadísticas requieren auditoría activa.")
    
    st.markdown("---")
    
    # Sección: Llamadas recientes
    st.subheader("📋 Llamadas Recientes")
    
    if estado.audit_manager:
        recent_calls = estado.get_recent_api_calls(limit=10)
        
        if not recent_calls.empty:
            # Preparar datos para mostrar
            display_calls = recent_calls[[
                'created_at', 'endpoint', 'method', 'response_status', 
                'response_time_ms', 'records_retrieved', 'success'
            ]].copy()
            
            display_calls['created_at'] = display_calls['created_at'].dt.strftime('%d/%m/%Y %H:%M:%S')
            display_calls['success'] = display_calls['success'].map({True: '✅', False: '❌'})
            
            display_calls = display_calls.rename(columns={
                'created_at': 'Fecha/Hora',
                'endpoint': 'Endpoint',
                'method': 'Método',
                'response_status': 'Status',
                'response_time_ms': 'Tiempo (ms)',
                'records_retrieved': 'Registros',
                'success': 'Éxito'
            })
            
            st.dataframe(display_calls, use_container_width=True)
        else:
            st.info("📝 No hay llamadas recientes registradas")
    else:
        st.info("📝 Habilita auditoría para ver llamadas recientes")
    
    # Footer con información adicional
    st.markdown("---")
    st.markdown("""
    ### 💡 Información Adicional
    
    **Estado de Integración:**
    - 🟢 Verde: Conexión activa y funcional
    - 🔴 Rojo: Problemas de conectividad o configuración
    
    **Métricas Importantes:**
    - **Tiempo de Respuesta**: Debe ser < 2000ms para rendimiento óptimo
    - **Tasa de Éxito**: Debe ser > 95% para operación estable
    - **Registros Obtenidos**: Indica productividad de las llamadas
    
    **Troubleshooting:**
    - Si hay errores de conexión, verifica la API Key
    - Si el tiempo de respuesta es alto, revisa la conectividad de red
    - Si faltan estadísticas, asegúrate que el sistema de auditoría esté activo
    """)


if __name__ == "__main__":
    # Para pruebas locales
    st.set_page_config(
        page_title="Estado Reservo - CEAPSI",
        page_icon="🔗",
        layout="wide"
    )
    
    mostrar_estado_reservo()