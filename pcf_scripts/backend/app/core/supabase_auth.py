"""
CEAPSI Backend - Supabase Authentication
Sistema de autenticación usando Supabase nativo para el backend FastAPI
"""

import os
import logging
from typing import Optional, Dict, Any
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import create_client, Client
import jwt
from datetime import datetime

logger = logging.getLogger('CEAPSI_BACKEND_AUTH')

class SupabaseAuthBackend:
    """Gestor de autenticación Supabase para backend FastAPI"""
    
    def __init__(self):
        # Configuración desde variables de entorno o Streamlit secrets
        self.supabase_url = os.getenv('SUPABASE_URL')
        # Backend debe usar SERVICE_ROLE_KEY para operaciones administrativas
        self.supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY') or os.getenv('SUPABASE_KEY')
        
        if not self.supabase_url:
            raise ValueError("SUPABASE_URL es requerida")
        if not self.supabase_key:
            raise ValueError("SUPABASE_SERVICE_ROLE_KEY es requerida para el backend")
        
        # Validar que la key es service role (debe ser más larga que anon key)
        if len(self.supabase_key) < 100:
            logger.warning("La key parece ser anon key, backend necesita service role key")
        
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        logger.info("Cliente Supabase Backend inicializado con service role")
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verifica token JWT de Supabase"""
        try:
            # Verificar token con Supabase
            response = self.supabase.auth.get_user(token)
            
            if response.user:
                return {
                    'user_id': response.user.id,
                    'email': response.user.email,
                    'user_metadata': response.user.user_metadata,
                    'role': response.user.user_metadata.get('role', 'viewer')
                }
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token inválido",
                    headers={"WWW-Authenticate": "Bearer"}
                )
                
        except Exception as e:
            logger.error(f"Error verificando token: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Error de autenticación",
                headers={"WWW-Authenticate": "Bearer"}
            )
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene información del usuario por ID"""
        try:
            # En Supabase, podemos obtener el usuario desde la tabla auth.users
            # Pero necesitamos usar el admin client para eso
            # Por ahora, retornamos información básica
            return {
                'user_id': user_id,
                'active': True
            }
        except Exception as e:
            logger.error(f"Error obteniendo usuario {user_id}: {e}")
            return None
    
    def require_role(self, required_roles: list = None):
        """Decorator para requerir roles específicos"""
        def role_checker(user_info: dict = Depends(lambda: None)):
            if not user_info:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Autenticación requerida"
                )
            
            if required_roles:
                user_role = user_info.get('role', 'viewer')
                if user_role not in required_roles:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Rol requerido: {required_roles}. Tu rol: {user_role}"
                    )
            
            return user_info
        
        return role_checker

# Instancia global
supabase_auth = SupabaseAuthBackend()

# Security scheme
security = HTTPBearer(auto_error=False)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Obtiene el usuario actual desde el token"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autorización requerido",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return supabase_auth.verify_token(credentials.credentials)

async def get_current_user_optional(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Optional[Dict[str, Any]]:
    """Obtiene el usuario actual (opcional)"""
    if not credentials:
        return None
    
    try:
        return supabase_auth.verify_token(credentials.credentials)
    except HTTPException:
        return None

def require_admin(user: Dict[str, Any] = Depends(get_current_user)):
    """Requiere rol de administrador"""
    if user.get('role') != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso solo para administradores"
        )
    return user

def require_analyst(user: Dict[str, Any] = Depends(get_current_user)):
    """Requiere rol de analista o superior"""
    role = user.get('role', 'viewer')
    if role not in ['admin', 'analista']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso solo para analistas o administradores"
        )
    return user

# Helper functions para compatibilidad
def create_session_token(user_data: dict) -> str:
    """Crea un token de sesión simple para tracking interno"""
    import uuid
    return str(uuid.uuid4())

def get_supabase_client() -> Client:
    """Retorna cliente Supabase para uso directo"""
    return supabase_auth.supabase