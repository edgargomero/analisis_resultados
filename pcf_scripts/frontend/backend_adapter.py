"""
CEAPSI Frontend - Backend Adapter
Adaptador que permite al frontend trabajar con API o localmente
"""

import streamlit as st
import logging
from typing import Dict, Any, Optional
from api_client import get_api_client, LocalFallback

logger = logging.getLogger('CEAPSI_ADAPTER')

class BackendAdapter:
    """Adaptador que maneja la comunicación con backend o fallback local"""
    
    def __init__(self):
        self.api_client = None
        self.use_api = self._should_use_api()
        
        if self.use_api:
            self.api_client = get_api_client()
    
    def _should_use_api(self) -> bool:
        """Determine if we should use API or local processing"""
        # Check if backend URL is configured
        backend_url = st.secrets.get("BACKEND_URL") or st.session_state.get("backend_url")
        
        if not backend_url:
            return False
        
        # Test backend health
        try:
            client = get_api_client()
            health = client.health_check()
            return health.get("status") == "healthy"
        except Exception as e:
            logger.warning(f"Backend not available, using local mode: {e}")
            return False
    
    def upload_and_process_file(self, uploaded_file, analysis_type: str = "audit") -> Dict[str, Any]:
        """Upload and process file using API or local fallback"""
        
        if self.use_api and self.api_client:
            st.info("🌐 Procesando con backend API...")
            
            # Upload file
            upload_result = self.api_client.upload_data(uploaded_file)
            
            if upload_result.get("success"):
                session_id = upload_result.get("session_id")
                
                # Start analysis
                analysis_result = self.api_client.start_analysis(session_id, analysis_type)
                
                if analysis_result.get("success"):
                    # Store session ID for tracking
                    st.session_state.current_session_id = session_id
                    
                    return {
                        "success": True,
                        "session_id": session_id,
                        "message": "Análisis iniciado exitosamente",
                        "file_info": upload_result.get("file_info")
                    }
                else:
                    return analysis_result
            else:
                return upload_result
        
        else:
            st.info("💻 Procesando localmente...")
            
            # Use local fallback
            return LocalFallback.process_locally(uploaded_file, analysis_type)
    
    def get_analysis_status(self, session_id: str) -> Dict[str, Any]:
        """Get analysis status"""
        
        if self.use_api and self.api_client:
            return self.api_client.get_analysis_status(session_id)
        else:
            # For local processing, check session state
            return st.session_state.get(f"status_{session_id}", {"status": "unknown"})
    
    def get_session_results(self, session_id: str) -> Dict[str, Any]:
        """Get session results"""
        
        if self.use_api and self.api_client:
            return self.api_client.get_session_results(session_id)
        else:
            # For local processing, get from session state
            return st.session_state.get(f"results_{session_id}", {})
    
    def list_sessions(self, page: int = 1, page_size: int = 50) -> Dict[str, Any]:
        """List user sessions"""
        
        if self.use_api and self.api_client:
            return self.api_client.list_sessions(page, page_size)
        else:
            # For local mode, get from MCP session manager
            try:
                from core.mcp_session_manager import get_mcp_session_manager
                session_manager = get_mcp_session_manager()
                user_id = st.session_state.get('user_id', 'anonymous_user')
                sessions = session_manager.list_user_sessions(user_id, page_size)
                
                return {
                    "sessions": sessions,
                    "total_count": len(sessions),
                    "page": page,
                    "page_size": page_size
                }
            except Exception as e:
                logger.error(f"Error listing local sessions: {e}")
                return {"sessions": [], "error": str(e)}
    
    def delete_session(self, session_id: str) -> Dict[str, Any]:
        """Delete a session"""
        
        if self.use_api and self.api_client:
            return self.api_client.delete_session(session_id)
        else:
            # For local mode, use MCP session manager
            try:
                from core.mcp_session_manager import get_mcp_session_manager
                session_manager = get_mcp_session_manager()
                success = session_manager.delete_session(session_id)
                
                if success:
                    return {"message": "Sesión eliminada exitosamente"}
                else:
                    return {"error": "Error eliminando sesión"}
            except Exception as e:
                logger.error(f"Error deleting local session: {e}")
                return {"error": str(e)}
    
    def show_connection_status(self):
        """Show connection status in sidebar"""
        with st.sidebar:
            st.markdown("---")
            st.subheader("🔗 Estado de Conexión")
            
            if self.use_api:
                st.success("🌐 Modo API Backend")
                
                # Test connection
                if self.api_client:
                    health = self.api_client.health_check()
                    if health.get("status") == "healthy":
                        st.success("✅ Backend disponible")
                    else:
                        st.error("❌ Backend no responde")
                        st.error(health.get("error", "Error desconocido"))
            else:
                st.info("💻 Modo Local")
                st.caption("Procesamiento local activo")

def get_backend_adapter() -> BackendAdapter:
    """Get backend adapter instance"""
    if 'backend_adapter' not in st.session_state:
        st.session_state.backend_adapter = BackendAdapter()
    
    return st.session_state.backend_adapter