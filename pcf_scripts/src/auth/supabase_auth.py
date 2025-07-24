"""
Módulo de Autenticación Supabase para CEAPSI
Usa el sistema de autenticación nativo de Supabase
"""

import streamlit as st
import os
from supabase import create_client, Client
import time
from datetime import datetime, timedelta
import logging
import json

logger = logging.getLogger('CEAPSI_SUPABASE_AUTH')

class SupabaseAuthManager:
    """Gestor de autenticación usando el sistema auth nativo de Supabase"""
    
    def __init__(self):
        """
        Inicializa el cliente Supabase
        """
        # Intentar obtener de Streamlit secrets primero, luego de env vars
        if hasattr(st, 'secrets') and 'SUPABASE_URL' in st.secrets:
            self.supabase_url = st.secrets['SUPABASE_URL']
            # Frontend debe usar ANON KEY, no service role key
            self.supabase_key = st.secrets.get('SUPABASE_ANON_KEY') or st.secrets.get('SUPABASE_KEY')
        else:
            self.supabase_url = os.getenv('SUPABASE_URL')
            # Prioritizar anon key para frontend
            self.supabase_key = os.getenv('SUPABASE_ANON_KEY') or os.getenv('SUPABASE_KEY')
        
        # Validar que no estamos usando service role key en frontend
        if self.supabase_key and len(self.supabase_key) > 200:
            logger.warning("⚠️ PELIGRO: Frontend está usando service role key, debería usar anon key")
        elif self.supabase_key and "anon" not in self.supabase_key:
            logger.info("Usando key de Supabase para frontend")
        
        self.supabase: Client = None
        
        if self.supabase_url and self.supabase_key:
            try:
                self.supabase = create_client(self.supabase_url, self.supabase_key)
                logger.info("Cliente Supabase inicializado correctamente")
            except Exception as e:
                logger.error(f"Error inicializando cliente Supabase: {e}")
                if not st._is_running_with_streamlit:
                    print(f"Error conectando con Supabase: {e}")
        else:
            logger.warning("Variables de entorno Supabase no configuradas")
    
    def is_available(self) -> bool:
        """Verifica si Supabase está disponible"""
        return self.supabase is not None
    
    def sign_up(self, email: str, password: str, user_metadata: dict = None) -> dict:
        """
        Registra un nuevo usuario usando Supabase Auth
        
        Args:
            email: Email del usuario
            password: Contraseña
            user_metadata: Metadata adicional (nombre, rol, etc.)
            
        Returns:
            dict: Información del usuario registrado o None si error
        """
        if not self.supabase:
            return None
            
        try:
            response = self.supabase.auth.sign_up({
                "email": email,
                "password": password,
                "options": {
                    "data": user_metadata or {}
                }
            })
            
            if response.user:
                logger.info(f"Usuario registrado: {email}")
                return {
                    'id': response.user.id,
                    'email': response.user.email,
                    'user_metadata': response.user.user_metadata
                }
            return None
            
        except Exception as e:
            logger.error(f"Error registrando usuario {email}: {e}")
            return None
    
    def sign_in(self, email: str, password: str) -> dict:
        """
        Autentica un usuario usando Supabase Auth
        
        Args:
            email: Email del usuario
            password: Contraseña
            
        Returns:
            dict: Información del usuario autenticado o None si error
        """
        if not self.supabase:
            return None
            
        try:
            response = self.supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            if response.user:
                logger.info(f"Login exitoso: {email}")
                return {
                    'id': response.user.id,
                    'email': response.user.email,
                    'user_metadata': response.user.user_metadata,
                    'access_token': response.session.access_token if response.session else None
                }
            return None
            
        except Exception as e:
            logger.error(f"Error autenticando usuario {email}: {e}")
            return None
    
    def sign_out(self) -> bool:
        """
        Cierra sesión del usuario actual
        
        Returns:
            bool: True si logout exitoso
        """
        if not self.supabase:
            return False
            
        try:
            response = self.supabase.auth.sign_out()
            logger.info("Logout exitoso")
            return True
        except Exception as e:
            logger.error(f"Error en logout: {e}")
            return False
    
    def get_current_user(self) -> dict:
        """
        Obtiene el usuario actualmente autenticado
        
        Returns:
            dict: Información del usuario actual o None
        """
        if not self.supabase:
            return None
            
        try:
            user = self.supabase.auth.get_user()
            if user and user.user:
                return {
                    'id': user.user.id,
                    'email': user.user.email,
                    'user_metadata': user.user.user_metadata
                }
            return None
        except Exception as e:
            logger.error(f"Error obteniendo usuario actual: {e}")
            return None
    
    def update_user_password(self, new_password: str) -> bool:
        """
        Actualiza contraseña del usuario actual
        
        Args:
            new_password: Nueva contraseña
            
        Returns:
            bool: True si se actualizó correctamente
        """
        if not self.supabase:
            return False
            
        try:
            response = self.supabase.auth.update_user({
                "password": new_password
            })
            
            if response.user:
                logger.info("Contraseña actualizada exitosamente")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error actualizando contraseña: {e}")
            return False
    
    def login_form(self) -> dict:
        """
        Muestra formulario de login y gestiona autenticación
        
        Returns:
            dict: Información del usuario autenticado o None
        """
        if not self.supabase:
            st.error("⚠️ Sistema de autenticación no disponible")
            st.info("Configurar variables SUPABASE_URL y SUPABASE_KEY")
            return None
        
        # CSS para el formulario de login
        st.markdown("""
        <style>
        .login-container {
            max-width: 400px;
            margin: auto;
            padding: 2rem;
            border-radius: 15px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        .login-header {
            text-align: center;
            margin-bottom: 2rem;
        }
        .login-form {
            background: white;
            padding: 1rem;
            border-radius: 10px;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Header centrado
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("""
            <div class="login-header">
                <h1>📞 CEAPSI</h1>
                <p style="color: #666;">Sistema de Predicción de Llamadas</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Tabs para login y registro
        login_tab, register_tab = st.tabs(["🔐 Iniciar Sesión", "📝 Registrarse"])
        
        with login_tab:
            with st.form("login_form", clear_on_submit=False):
                st.markdown("### Iniciar Sesión")
                
                email = st.text_input("📧 Email", placeholder="usuario@ceapsi.cl")
                password = st.text_input("🔒 Contraseña", type="password", placeholder="Ingrese su contraseña")
                
                col1, col2 = st.columns(2)
                with col1:
                    login_button = st.form_submit_button("🚀 Ingresar", use_container_width=True, type="primary")
                with col2:
                    st.form_submit_button("❌ Limpiar", use_container_width=True)
            
            if login_button and email and password:
                with st.spinner("Verificando credenciales..."):
                    user = self.sign_in(email, password)
                    
                    if user:
                        st.success(f"✅ Bienvenido!")
                        time.sleep(1)
                        return user
                    else:
                        st.error("❌ Credenciales incorrectas")
        
        with register_tab:
            with st.form("register_form", clear_on_submit=False):
                st.markdown("### Crear Cuenta Nueva")
                
                reg_email = st.text_input("📧 Email", placeholder="nuevo@ceapsi.cl", key="reg_email")
                reg_name = st.text_input("👤 Nombre Completo", placeholder="Juan Pérez", key="reg_name")
                reg_role = st.selectbox("🎭 Rol", ["viewer", "analista"], key="reg_role")
                reg_password = st.text_input("🔒 Contraseña", type="password", placeholder="Mínimo 6 caracteres", key="reg_password")
                reg_confirm = st.text_input("🔒 Confirmar Contraseña", type="password", placeholder="Repita la contraseña", key="reg_confirm")
                
                register_button = st.form_submit_button("📝 Registrarse", use_container_width=True, type="primary")
            
            if register_button and all([reg_email, reg_name, reg_password, reg_confirm]):
                if reg_password != reg_confirm:
                    st.error("❌ Las contraseñas no coinciden")
                elif len(reg_password) < 6:
                    st.error("❌ La contraseña debe tener al menos 6 caracteres")
                else:
                    with st.spinner("Creando cuenta..."):
                        user = self.sign_up(reg_email, reg_password, {
                            'name': reg_name,
                            'role': reg_role
                        })
                        
                        if user:
                            st.success("✅ Cuenta creada exitosamente! Verifica tu email.")
                        else:
                            st.error("❌ Error creando cuenta")
        
        # Información de ayuda
        with st.expander("ℹ️ ¿Necesita ayuda?"):
            st.info("""
            **Sistema de Autenticación CEAPSI**
            
            **Para obtener acceso:**
            - Contacte al administrador del sistema
            - Solo usuarios autorizados pueden acceder
            - Email: soporte@ceapsi.cl
            
            **Registro de nuevos usuarios:**
            - Solo con autorización del administrador
            - Use la pestaña "Registrarse" si tiene permisos
            - Verificación de email requerida
            
            **Política de Seguridad:**
            - Contraseñas mínimo 6 caracteres
            - Sesiones seguras con Supabase Auth
            - Acceso basado en roles
            """)
        
        return None
    
    def require_auth(self) -> bool:
        """
        Requiere autenticación - muestra login si no autenticado
        
        Returns:
            bool: True si autenticado, False si no
        """
        # Verificar si ya está autenticado
        if st.session_state.get('authenticated') and st.session_state.get('supabase_user'):
            return True
        
        # Mostrar formulario de login
        user = self.login_form()
        
        if user:
            st.session_state.authenticated = True
            st.session_state.supabase_user = user
            st.rerun()
            return True
        
        return False
    
    def logout(self):
        """Cerrar sesión"""
        # Cerrar sesión en Supabase
        self.sign_out()
        
        # Limpiar session state
        if 'authenticated' in st.session_state:
            del st.session_state.authenticated
        if 'supabase_user' in st.session_state:
            del st.session_state.supabase_user
        st.rerun()
    
    def get_session_user(self) -> dict:
        """
        Obtiene el usuario actual de la sesión
        
        Returns:
            dict: Datos del usuario actual o None
        """
        return st.session_state.get('supabase_user')
    
    def is_admin(self) -> bool:
        """Verifica si el usuario actual es admin"""
        user = self.get_session_user()
        if user and user.get('user_metadata'):
            return user['user_metadata'].get('role') == 'admin'
        return False
    
    def is_analyst(self) -> bool:
        """Verifica si el usuario actual es analista o admin"""
        user = self.get_session_user()
        if user and user.get('user_metadata'):
            role = user['user_metadata'].get('role', '')
            return role in ['admin', 'analista']
        return False
    
    def sidebar_user_info(self):
        """Muestra información del usuario en sidebar"""
        user = self.get_session_user()
        if user:
            user_metadata = user.get('user_metadata', {})
            name = user_metadata.get('name', user.get('email', 'Usuario'))
            role = user_metadata.get('role', 'viewer')
            
            with st.sidebar:
                st.markdown("---")
                st.markdown("### 👤 Sesión Activa")
                st.markdown(f"**{name}**")
                st.caption(f"{user['email']} • {role.title()}")
                
                if st.button("🚪 Cerrar Sesión", key="supabase_logout", use_container_width=True):
                    self.logout()


# Función helper para uso rápido
def require_supabase_auth():
    """
    Función helper para requerir autenticación Supabase
    
    Usage:
        auth_manager = require_supabase_auth()
        if not auth_manager:
            st.stop()
    """
    auth_manager = SupabaseAuthManager()
    if not auth_manager.is_available():
        st.error("⚠️ Sistema de autenticación no disponible")
        return None
    
    if not auth_manager.require_auth():
        st.stop()
    
    return auth_manager


# Script de inicialización (ejecutar una sola vez)
def initialize_supabase_users():
    """
    Script para inicializar usuarios por defecto en Supabase
    Ejecutar una sola vez después de crear la tabla
    """
    auth_manager = SupabaseAuthManager()
    
    if not auth_manager.is_available():
        print("Error: Supabase no disponible")
        return
    
    # Crear tabla
    if auth_manager.create_users_table():
        print("✅ Tabla ceapsi_users creada/verificada")
    
    # Crear usuarios por defecto
    default_users = [
        {
            'username': 'admin',
            'email': 'admin@ceapsi.cl',
            'name': 'Administrador CEAPSI',
            'password': 'admin123',
            'role': 'admin'
        },
        {
            'username': 'analista1',
            'email': 'analista1@ceapsi.cl',
            'name': 'María González',
            'password': 'analista123',
            'role': 'analista'
        },
        {
            'username': 'analista2',
            'email': 'analista2@ceapsi.cl',
            'name': 'Carlos Rodríguez',
            'password': 'analista123',
            'role': 'analista'
        },
        {
            'username': 'viewer',
            'email': 'viewer@ceapsi.cl',
            'name': 'Usuario Visualización',
            'password': 'viewer123',
            'role': 'viewer'
        }
    ]
    
    for user_data in default_users:
        if auth_manager.create_user(**user_data):
            print(f"✅ Usuario creado: {user_data['username']}")
        else:
            print(f"⚠️ Error/Usuario existe: {user_data['username']}")

if __name__ == "__main__":
    initialize_supabase_users()