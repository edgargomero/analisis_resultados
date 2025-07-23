"""
CEAPSI - Sistema de Auditoría y Logging
Integración completa con Supabase Authentication y Context7 MCP
"""

import streamlit as st
import pandas as pd
import json
import hashlib
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
import logging
from pathlib import Path
import os

# Configurar logging
logger = logging.getLogger('CEAPSI_AUDIT')

class SupabaseAuditManager:
    """
    Gestor de auditoría integrado con Supabase Authentication
    """
    
    def __init__(self, supabase_client):
        self.supabase = supabase_client
        self.session_id = self._generate_session_id()
        
    def _generate_session_id(self) -> str:
        """Genera un ID único de sesión"""
        timestamp = str(time.time())
        return hashlib.md5(timestamp.encode()).hexdigest()[:16]
    
    def _get_current_user(self) -> Optional[Dict]:
        """Obtiene el usuario actual usando Supabase auth"""
        try:
            # Primero intentar obtener desde session_state
            if 'user' in st.session_state and st.session_state['user']:
                return st.session_state['user']
            
            # Si no hay usuario en session, intentar obtener desde Supabase
            user = self.supabase.auth.get_user()
            if user and user.user:
                return user.user
                
        except Exception as e:
            logger.warning(f"No se pudo obtener usuario actual: {e}")
            
        return None
    
    def _get_user_metadata(self) -> Dict[str, Any]:
        """Obtiene metadata del usuario y sesión"""
        user = self._get_current_user()
        
        metadata = {
            "session_id": self.session_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "streamlit_session": st.session_state.get('session_state', 'unknown')
        }
        
        if user:
            metadata.update({
                "user_email": user.email,
                "user_role": user.user_metadata.get('role', 'user') if user.user_metadata else 'user',
                "user_name": user.user_metadata.get('name', 'Unknown') if user.user_metadata else 'Unknown'
            })
        
        return metadata
    
    def log_activity(
        self, 
        activity_type: str,
        module_name: str,
        activity_description: str,
        activity_details: Optional[Dict] = None
    ) -> bool:
        """
        Registra una actividad del usuario
        
        Args:
            activity_type: Tipo de actividad ('login', 'file_upload', 'analysis', etc.)
            module_name: Módulo donde ocurre la actividad
            activity_description: Descripción de la actividad
            activity_details: Detalles adicionales en formato JSON
        """
        try:
            user = self._get_current_user()
            if not user:
                logger.warning("Intento de log sin usuario autenticado")
                return False
            
            metadata = self._get_user_metadata()
            
            audit_record = {
                "user_id": user.id,
                "session_id": self.session_id,
                "activity_type": activity_type,
                "module_name": module_name,
                "activity_description": activity_description,
                "activity_details": activity_details or {},
                "ip_address": metadata.get("ip_address"),
                "user_agent": metadata.get("user_agent"),
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            
            result = self.supabase.table("audit_user_activities").insert(audit_record).execute()
            
            if result.data:
                logger.info(f"Actividad registrada: {activity_type} - {module_name}")
                return True
            else:
                logger.error("Error insertando registro de actividad")
                return False
                
        except Exception as e:
            logger.error(f"Error en log_activity: {e}")
            return False
    
    def log_file_upload(
        self,
        file_name: str,
        file_type: str,
        file_size_bytes: int,
        data_type: str,
        records_count: int,
        columns_detected: List[str],
        validation_status: str,
        validation_details: Dict,
        storage_path: str = None
    ) -> bool:
        """Registra la subida de un archivo"""
        try:
            user = self._get_current_user()
            if not user:
                return False
            
            # Generar hash del archivo para detectar duplicados
            file_hash = hashlib.md5(f"{file_name}{file_size_bytes}{time.time()}".encode()).hexdigest()
            
            upload_record = {
                "user_id": user.id,
                "session_id": self.session_id,
                "file_name": file_name,
                "file_type": file_type,
                "file_size_bytes": file_size_bytes,
                "data_type": data_type,
                "records_count": records_count,
                "columns_detected": columns_detected,
                "validation_status": validation_status,
                "validation_details": validation_details,
                "file_hash": file_hash,
                "storage_path": storage_path,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            
            result = self.supabase.table("audit_file_uploads").insert(upload_record).execute()
            
            # También registrar como actividad general
            self.log_activity(
                activity_type="file_upload",
                module_name="preparacion_datos",
                activity_description=f"Archivo subido: {file_name}",
                activity_details={
                    "file_type": file_type,
                    "records_count": records_count,
                    "validation_status": validation_status
                }
            )
            
            return bool(result.data)
            
        except Exception as e:
            logger.error(f"Error en log_file_upload: {e}")
            return False
    
    def log_analysis_run(
        self,
        analysis_type: str,
        input_data_source: str,
        parameters: Dict,
        execution_status: str = "started",
        results_summary: Dict = None,
        performance_metrics: Dict = None,
        output_files: List[str] = None,
        execution_time_seconds: float = None,
        error_details: str = None
    ) -> str:
        """
        Registra la ejecución de un análisis
        Retorna el ID del registro para actualizaciones posteriores
        """
        try:
            user = self._get_current_user()
            if not user:
                return None
            
            analysis_record = {
                "user_id": user.id,
                "session_id": self.session_id,
                "analysis_type": analysis_type,
                "input_data_source": input_data_source,
                "parameters": parameters,
                "execution_status": execution_status,
                "results_summary": results_summary,
                "performance_metrics": performance_metrics,
                "output_files": output_files or [],
                "execution_time_seconds": execution_time_seconds,
                "error_details": error_details,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "completed_at": datetime.now(timezone.utc).isoformat() if execution_status in ["completed", "failed"] else None
            }
            
            result = self.supabase.table("audit_analysis_runs").insert(analysis_record).execute()
            
            if result.data:
                record_id = result.data[0]["id"]
                
                # Registrar actividad general
                self.log_activity(
                    activity_type="analysis",
                    module_name=analysis_type,
                    activity_description=f"Análisis {execution_status}: {analysis_type}",
                    activity_details=parameters
                )
                
                return record_id
            
            return None
            
        except Exception as e:
            logger.error(f"Error en log_analysis_run: {e}")
            return None
    
    def update_analysis_run(
        self,
        record_id: str,
        execution_status: str,
        results_summary: Dict = None,
        performance_metrics: Dict = None,
        output_files: List[str] = None,
        execution_time_seconds: float = None,
        error_details: str = None
    ) -> bool:
        """Actualiza un registro de análisis existente"""
        try:
            update_data = {
                "execution_status": execution_status,
                "completed_at": datetime.now(timezone.utc).isoformat()
            }
            
            if results_summary:
                update_data["results_summary"] = results_summary
            if performance_metrics:
                update_data["performance_metrics"] = performance_metrics
            if output_files:
                update_data["output_files"] = output_files
            if execution_time_seconds:
                update_data["execution_time_seconds"] = execution_time_seconds
            if error_details:
                update_data["error_details"] = error_details
            
            result = self.supabase.table("audit_analysis_runs").update(update_data).eq("id", record_id).execute()
            
            return bool(result.data)
            
        except Exception as e:
            logger.error(f"Error en update_analysis_run: {e}")
            return False
    
    def log_api_call(
        self,
        api_provider: str,
        endpoint: str,
        method: str,
        request_parameters: Dict,
        response_status: int,
        response_time_ms: int,
        records_retrieved: int = 0,
        success: bool = True,
        error_message: str = None
    ) -> bool:
        """Registra una llamada a API externa"""
        try:
            user = self._get_current_user()
            if not user:
                return False
            
            api_record = {
                "user_id": user.id,
                "session_id": self.session_id,
                "api_provider": api_provider,
                "endpoint": endpoint,
                "method": method,
                "request_parameters": request_parameters,
                "response_status": response_status,
                "response_time_ms": response_time_ms,
                "records_retrieved": records_retrieved,
                "success": success,
                "error_message": error_message,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            
            result = self.supabase.table("audit_api_calls").insert(api_record).execute()
            
            # Registrar actividad general
            self.log_activity(
                activity_type="api_call",
                module_name="preparacion_datos",
                activity_description=f"API call a {api_provider}: {endpoint}",
                activity_details={
                    "method": method,
                    "success": success,
                    "records_retrieved": records_retrieved
                }
            )
            
            return bool(result.data)
            
        except Exception as e:
            logger.error(f"Error en log_api_call: {e}")
            return False
    
    def log_data_storage(
        self,
        storage_type: str,
        data_type: str,
        storage_location: str,
        data_size_bytes: int,
        records_count: int,
        metadata: Dict = None,
        retention_days: int = 90
    ) -> bool:
        """Registra el almacenamiento de datos procesados"""
        try:
            user = self._get_current_user()
            if not user:
                return False
            
            expires_at = None
            if retention_days:
                expires_at = (datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0) + 
                             pd.Timedelta(days=retention_days)).isoformat()
            
            storage_record = {
                "user_id": user.id,
                "session_id": self.session_id,
                "storage_type": storage_type,
                "data_type": data_type,
                "storage_location": storage_location,
                "data_size_bytes": data_size_bytes,
                "records_count": records_count,
                "metadata": metadata or {},
                "retention_days": retention_days,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "expires_at": expires_at
            }
            
            result = self.supabase.table("audit_data_storage").insert(storage_record).execute()
            
            return bool(result.data)
            
        except Exception as e:
            logger.error(f"Error en log_data_storage: {e}")
            return False
    
    def log_page_visit(self, page_name: str, page_params: Dict = None):
        """Registra la visita a una página"""
        self.log_activity(
            activity_type="page_visit",
            module_name="streamlit_app",
            activity_description=f"Visita a página: {page_name}",
            activity_details=page_params or {}
        )
    
    def log_user_login(self, login_method: str = "email"):
        """Registra el login del usuario"""
        self.log_activity(
            activity_type="login",
            module_name="supabase_auth",
            activity_description=f"Usuario autenticado via {login_method}",
            activity_details={"login_method": login_method}
        )
    
    def log_user_logout(self):
        """Registra el logout del usuario"""
        self.log_activity(
            activity_type="logout",
            module_name="supabase_auth",
            activity_description="Usuario cerró sesión",
            activity_details={}
        )
    
    def get_user_activity_summary(self, days: int = 30) -> pd.DataFrame:
        """Obtiene un resumen de actividad del usuario actual"""
        try:
            user = self._get_current_user()
            if not user:
                return pd.DataFrame()
            
            # Calcular fecha límite
            fecha_limite = (datetime.now(timezone.utc) - pd.Timedelta(days=days)).isoformat()
            
            # Consultar actividades del usuario
            result = self.supabase.table("audit_user_activities") \
                .select("*") \
                .eq("user_id", user.id) \
                .gte("created_at", fecha_limite) \
                .order("created_at", desc=True) \
                .execute()
            
            if result.data:
                return pd.DataFrame(result.data)
            else:
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"Error obteniendo resumen de actividad: {e}")
            return pd.DataFrame()
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Obtiene métricas del sistema (solo para administradores)"""
        try:
            user = self._get_current_user()
            if not user or user.user_metadata.get('role') != 'admin':
                return {}
            
            # Consultar métricas generales del sistema
            today = datetime.now(timezone.utc).date().isoformat()
            week_ago = (datetime.now(timezone.utc) - pd.Timedelta(days=7)).date().isoformat()
            
            # Actividades de hoy
            activities_today = self.supabase.table("audit_user_activities") \
                .select("*", count="exact") \
                .gte("created_at", today) \
                .execute()
            
            # Archivos subidos esta semana
            files_week = self.supabase.table("audit_file_uploads") \
                .select("*", count="exact") \
                .gte("created_at", week_ago) \
                .execute()
            
            # Análisis ejecutados esta semana
            analysis_week = self.supabase.table("audit_analysis_runs") \
                .select("*", count="exact") \
                .gte("created_at", week_ago) \
                .execute()
            
            return {
                "activities_today": activities_today.count,
                "files_uploaded_week": files_week.count,
                "analysis_runs_week": analysis_week.count,
                "generated_at": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo métricas del sistema: {e}")
            return {}


# Decorador para audit automático de funciones
def audit_function(activity_type: str, module_name: str):
    """Decorador para auditar automáticamente funciones"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Obtener audit manager desde session_state
            audit_manager = st.session_state.get('audit_manager')
            
            if audit_manager:
                # Registrar inicio de función
                start_time = time.time()
                
                audit_manager.log_activity(
                    activity_type=activity_type,
                    module_name=module_name,
                    activity_description=f"Ejecutando función: {func.__name__}",
                    activity_details={"function": func.__name__, "args_count": len(args), "kwargs_count": len(kwargs)}
                )
                
                try:
                    # Ejecutar función
                    result = func(*args, **kwargs)
                    
                    # Registrar éxito
                    execution_time = time.time() - start_time
                    audit_manager.log_activity(
                        activity_type=f"{activity_type}_completed",
                        module_name=module_name,
                        activity_description=f"Función completada: {func.__name__}",
                        activity_details={
                            "function": func.__name__,
                            "execution_time_seconds": execution_time,
                            "success": True
                        }
                    )
                    
                    return result
                    
                except Exception as e:
                    # Registrar error
                    execution_time = time.time() - start_time
                    audit_manager.log_activity(
                        activity_type=f"{activity_type}_failed",
                        module_name=module_name,
                        activity_description=f"Error en función: {func.__name__}",
                        activity_details={
                            "function": func.__name__,
                            "execution_time_seconds": execution_time,
                            "success": False,
                            "error": str(e)
                        }
                    )
                    raise
            else:
                # Si no hay audit manager, ejecutar función normalmente
                return func(*args, **kwargs)
                
        return wrapper
    return decorator


# Función para inicializar el audit manager en la aplicación
def initialize_audit_manager(supabase_client) -> SupabaseAuditManager:
    """Inicializa y configura el audit manager"""
    audit_manager = SupabaseAuditManager(supabase_client)
    
    # Guardar en session_state para uso global
    st.session_state['audit_manager'] = audit_manager
    
    return audit_manager