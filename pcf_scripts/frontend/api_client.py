"""
CEAPSI Frontend - API Client with Supabase Auth
Cliente para comunicación con el backend FastAPI usando autenticación Supabase
"""

import requests
import streamlit as st
from typing import Dict, Any, List, Optional
import logging
import json
from pathlib import Path
import tempfile
import os
import io

logger = logging.getLogger('CEAPSI_API_CLIENT')

class CEAPSIAPIClient:
    """Cliente para comunicación con la API de CEAPSI"""
    
    def __init__(self, base_url: str = None):
        self.base_url = base_url or self._get_backend_url()
        self.session = requests.Session()
        self.session.timeout = 30
        
        # Headers básicos
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'CEAPSI-Frontend/2.0'
        })
        
        logger.info(f"API Client inicializado para: {self.base_url}")
    
    def _get_backend_url(self) -> str:
        """Get backend URL from environment or Streamlit secrets"""
        # Detectar URL del backend desde secrets o variables de entorno
        if hasattr(st, 'secrets') and 'BACKEND_URL' in st.secrets:
            return st.secrets['BACKEND_URL'].rstrip('/')
        elif os.getenv('BACKEND_URL'):
            return os.getenv('BACKEND_URL').rstrip('/')
        else:
            return "http://localhost:8000"
    
    def _get_auth_headers(self) -> Dict[str, str]:
        """Obtener headers de autenticación desde sesión Supabase"""
        headers = {}
        
        # Obtener token de autenticación de la sesión
        if hasattr(st.session_state, 'supabase_user'):
            user = st.session_state.supabase_user
            if user and user.get('access_token'):
                headers['Authorization'] = f"Bearer {user['access_token']}"
        
        return headers
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Realizar request HTTP con manejo de errores y auth"""
        url = f"{self.base_url}{endpoint}"
        
        # Agregar headers de autenticación
        auth_headers = self._get_auth_headers()
        if 'headers' in kwargs:
            kwargs['headers'].update(auth_headers)
        else:
            kwargs['headers'] = auth_headers
        
        try:
            response = self.session.request(method, url, **kwargs)
            
            if response.status_code == 401:
                return {
                    "success": False,
                    "error": "No autorizado - verifique su sesión",
                    "status_code": 401,
                    "requires_auth": True
                }
            elif response.status_code == 403:
                return {
                    "success": False,
                    "error": "Acceso denegado - permisos insuficientes",
                    "status_code": 403
                }
            elif response.status_code >= 400:
                error_detail = response.text
                try:
                    error_json = response.json()
                    error_detail = error_json.get('detail', error_detail)
                except:
                    pass
                
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {error_detail}",
                    "status_code": response.status_code
                }
            
            try:
                data = response.json()
                return {"success": True, "data": data}
            except json.JSONDecodeError:
                return {"success": True, "data": response.text}
            
        except requests.exceptions.ConnectionError:
            return {
                "success": False,
                "error": "No se puede conectar con el backend",
                "details": f"URL: {url}",
                "fallback_available": True
            }
        except requests.exceptions.Timeout:
            return {
                "success": False,
                "error": "Timeout conectando con backend",
                "details": "El servidor tardó demasiado en responder",
                "fallback_available": True
            }
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": f"Error de conexión: {str(e)}",
                "fallback_available": True
            }
    
    def health_check(self) -> Dict[str, Any]:
        """Check backend health"""
        result = self._make_request('GET', '/health')
        
        if result.get("success"):
            return result["data"]
        else:
            return {"status": "unhealthy", "error": result.get("error")}
    
    def upload_data(self, uploaded_file) -> Dict[str, Any]:
        """Upload data file to backend"""
        try:
            # Verificar autenticación
            if not self._get_auth_headers():
                return {
                    "success": False,
                    "error": "Sesión requerida para subir archivos",
                    "requires_auth": True
                }
            
            # Preparar archivo para upload
            files = {
                'file': (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)
            }
            
            # Headers con autenticación, sin Content-Type para multipart
            headers = self._get_auth_headers()
            
            response = requests.post(
                f"{self.base_url}/api/v1/data/upload",
                files=files,
                headers=headers,
                timeout=60
            )
            
            if response.status_code == 200:
                return {"success": True, **response.json()}
            elif response.status_code == 401:
                return {
                    "success": False,
                    "error": "Sesión expirada - inicie sesión nuevamente",
                    "requires_auth": True
                }
            else:
                return {
                    "success": False,
                    "error": f"Error subiendo archivo: {response.status_code}",
                    "fallback_available": True
                }
                
        except Exception as e:
            logger.error(f"Error en upload: {e}")
            return {
                "success": False,
                "error": f"Error procesando archivo: {str(e)}",
                "fallback_available": True
            }
    
    def start_analysis(self, session_id: str, analysis_type: str = "audit") -> Dict[str, Any]:
        """Start analysis for a session"""
        data = {
            "session_id": session_id,
            "analysis_type": analysis_type
        }
        
        return self._make_request('POST', '/api/v1/analysis/start', json=data)
    
    def get_analysis_status(self, session_id: str) -> Dict[str, Any]:
        """Get analysis status for a session"""
        return self._make_request('GET', f'/api/v1/analysis/status/{session_id}')
    
    def list_sessions(self, page: int = 1, page_size: int = 50) -> Dict[str, Any]:
        """List user sessions"""
        params = {"page": page, "page_size": page_size}
        return self._make_request('GET', '/api/v1/sessions/', params=params)
    
    def get_session(self, session_id: str) -> Dict[str, Any]:
        """Get session details"""
        return self._make_request('GET', f'/api/v1/sessions/{session_id}')
    
    def get_session_results(self, session_id: str) -> Dict[str, Any]:
        """Get session analysis results"""
        return self._make_request('GET', f'/api/v1/sessions/{session_id}/results')
    
    def delete_session(self, session_id: str) -> Dict[str, Any]:
        """Delete a session"""
        return self._make_request('DELETE', f'/api/v1/sessions/{session_id}')
    
    def restore_session(self, session_id: str) -> Dict[str, Any]:
        """Restore session to current context"""
        return self._make_request('POST', f'/api/v1/sessions/{session_id}/restore')
    
    # ---- Nuevos métodos para Reservo API ----
    
    def get_reservo_status(self) -> Dict[str, Any]:
        """Obtener estado de integración con Reservo"""
        return self._make_request('GET', '/api/v1/reservo/status')
    
    def test_reservo_connection(self) -> Dict[str, Any]:
        """Probar conexión con Reservo API"""
        return self._make_request('GET', '/api/v1/reservo/test-connection')
    
    def get_reservo_professionals(self) -> Dict[str, Any]:
        """Obtener profesionales desde Reservo"""
        return self._make_request('GET', '/api/v1/reservo/professionals')
    
    def get_reservo_appointments(self, start_date: str = None, end_date: str = None) -> Dict[str, Any]:
        """Obtener citas desde Reservo"""
        params = {}
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date
            
        return self._make_request('GET', '/api/v1/reservo/appointments', params=params)
    
    def get_reservo_statistics(self, days: int = 30) -> Dict[str, Any]:
        """Obtener estadísticas de uso de Reservo"""
        params = {'days': days}
        return self._make_request('GET', '/api/v1/reservo/statistics', params=params)
    
    def sync_reservo_data(self, sync_professionals: bool = True, sync_appointments: bool = True, days_back: int = 30) -> Dict[str, Any]:
        """Sincronizar datos desde Reservo"""
        data = {
            "sync_professionals": sync_professionals,
            "sync_appointments": sync_appointments,
            "days_back": days_back
        }
        return self._make_request('POST', '/api/v1/reservo/sync-data', json=data)

def get_api_client() -> CEAPSIAPIClient:
    """Get API client instance"""
    if 'api_client' not in st.session_state:
        st.session_state.api_client = CEAPSIAPIClient()
    
    return st.session_state.api_client

# Fallback functions for when backend is not available
class LocalFallback:
    """Fallback to local processing when backend is unavailable"""
    
    @staticmethod
    def process_locally(uploaded_file, analysis_type: str = "audit") -> Dict[str, Any]:
        """Process data locally using existing modules"""
        try:
            logger.info("Procesando archivo localmente (fallback)")
            
            # Import local modules
            import tempfile
            import pandas as pd
            from datetime import datetime
            import uuid
            
            # Guardar archivo temporal
            with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as tmp_file:
                if uploaded_file.type == "text/csv" or uploaded_file.name.endswith('.csv'):
                    # Manejar CSV
                    bytes_data = uploaded_file.read()
                    content = bytes_data.decode('utf-8')
                    df = pd.read_csv(io.StringIO(content), sep=';')
                else:
                    # Manejar Excel
                    df = pd.read_excel(uploaded_file)
                
                # Guardar como CSV
                df.to_csv(tmp_file, sep=';', index=False)
                temp_path = tmp_file.name
            
            # Crear sesión local
            session_id = str(uuid.uuid4())
            
            # Guardar en session state para tracking local
            st.session_state[f"local_session_{session_id}"] = {
                "file_path": temp_path,
                "created_at": datetime.now(),
                "status": "created",
                "records_count": len(df)
            }
            
            return {
                "success": True,
                "session_id": session_id,
                "message": "Archivo procesado localmente",
                "file_info": {
                    "filename": uploaded_file.name,
                    "records_count": len(df),
                    "columns": list(df.columns)
                },
                "mode": "local_fallback"
            }
            
        except Exception as e:
            logger.error(f"Error en procesamiento local: {e}")
            return {
                "success": False,
                "error": f"Error procesamiento local: {str(e)}"
            }