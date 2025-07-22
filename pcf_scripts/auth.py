"""
Módulo de Autenticación para CEAPSI
Gestiona login, logout y control de acceso
"""

import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
import bcrypt
from pathlib import Path
import logging

logger = logging.getLogger('CEAPSI_AUTH')

class AuthManager:
    """Gestor de autenticación para la aplicación CEAPSI"""
    
    def __init__(self, config_file='config.yaml'):
        """
        Inicializa el gestor de autenticación
        
        Args:
            config_file: Ruta al archivo de configuración YAML
        """
        self.config_file = Path(config_file)
        self.config = self._load_config()
        self.authenticator = self._setup_authenticator()
        
    def _load_config(self):
        """Carga la configuración desde el archivo YAML"""
        try:
            if not self.config_file.exists():
                # Crear configuración por defecto si no existe
                return self._create_default_config()
                
            with open(self.config_file, 'r', encoding='utf-8') as file:
                config = yaml.load(file, Loader=SafeLoader)
            return config
        except Exception as e:
            logger.error(f"Error cargando configuración: {e}")
            st.error(f"Error cargando configuración de autenticación: {e}")
            return self._create_default_config()
    
    def _create_default_config(self):
        """Crea una configuración por defecto"""
        # Generar hashes para contraseñas por defecto
        admin_hash = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        default_config = {
            'credentials': {
                'usernames': {
                    'admin': {
                        'email': 'admin@ceapsi.cl',
                        'name': 'Administrador',
                        'password': admin_hash
                    }
                }
            },
            'cookie': {
                'expiry_days': 30,
                'key': 'ceapsi_signature_key_default',
                'name': 'ceapsi_auth_cookie'
            },
            'preauthorized': {
                'emails': ['admin@ceapsi.cl']
            }
        }
        
        # Guardar configuración por defecto
        try:
            with open(self.config_file, 'w', encoding='utf-8') as file:
                yaml.dump(default_config, file, default_flow_style=False, allow_unicode=True)
            logger.info("Configuración por defecto creada")
        except Exception as e:
            logger.error(f"Error guardando configuración por defecto: {e}")
            
        return default_config
    
    def _setup_authenticator(self):
        """Configura el autenticador de Streamlit"""
        try:
            authenticator = stauth.Authenticate(
                self.config['credentials'],
                self.config['cookie']['name'],
                self.config['cookie']['key'],
                self.config['cookie']['expiry_days'],
                self.config.get('preauthorized', {})
            )
            return authenticator
        except Exception as e:
            logger.error(f"Error configurando autenticador: {e}")
            st.error(f"Error en configuración de autenticación: {e}")
            return None
    
    def login(self):
        """
        Muestra el formulario de login y gestiona la autenticación
        
        Returns:
            tuple: (name, authentication_status, username)
        """
        if not self.authenticator:
            st.error("Sistema de autenticación no disponible")
            return None, False, None
            
        # Formulario de login
        name, authentication_status, username = self.authenticator.login(
            'Login CEAPSI', 
            'main'
        )
        
        return name, authentication_status, username
    
    def logout(self):
        """Gestiona el logout del usuario"""
        if self.authenticator:
            self.authenticator.logout('Cerrar Sesión', 'sidebar')
    
    def require_auth(self):
        """
        Decorator/función para requerir autenticación
        Muestra el login si no está autenticado
        
        Returns:
            bool: True si autenticado, False si no
        """
        if 'authentication_status' not in st.session_state:
            st.session_state.authentication_status = None
            
        if st.session_state.authentication_status != True:
            # Mostrar página de login
            self._show_login_page()
            return False
        return True
    
    def _show_login_page(self):
        """Muestra la página de login personalizada"""
        # Estilo CSS para la página de login
        st.markdown("""
        <style>
        .login-container {
            max-width: 400px;
            margin: auto;
            padding: 2rem;
        }
        .login-header {
            text-align: center;
            margin-bottom: 2rem;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Header
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("""
            <div class="login-header">
                <h1>📞 CEAPSI</h1>
                <p>Sistema de Predicción de Llamadas</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Login form
        name, authentication_status, username = self.login()
        
        if authentication_status == False:
            st.error('Usuario/contraseña incorrectos')
        elif authentication_status == None:
            st.warning('Por favor ingrese sus credenciales')
            
            # Información de ayuda
            with st.expander("ℹ️ ¿Necesita ayuda?"):
                st.info("""
                **Credenciales de ejemplo:**
                - Usuario: `admin` / Contraseña: `admin123`
                - Usuario: `analista1` / Contraseña: `temp_analista123`
                
                Para solicitar acceso contacte a: soporte@ceapsi.cl
                """)
    
    def get_user_info(self):
        """
        Obtiene información del usuario actual
        
        Returns:
            dict: Información del usuario (name, username, email)
        """
        if st.session_state.get('authentication_status'):
            username = st.session_state.get('username')
            if username and username in self.config['credentials']['usernames']:
                user_data = self.config['credentials']['usernames'][username]
                return {
                    'username': username,
                    'name': user_data.get('name', username),
                    'email': user_data.get('email', '')
                }
        return None
    
    def hash_password(self, password):
        """
        Genera hash bcrypt para una contraseña
        
        Args:
            password: Contraseña en texto plano
            
        Returns:
            str: Hash de la contraseña
        """
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def update_password(self, username, new_password):
        """
        Actualiza la contraseña de un usuario
        
        Args:
            username: Nombre de usuario
            new_password: Nueva contraseña
            
        Returns:
            bool: True si se actualizó correctamente
        """
        try:
            if username in self.config['credentials']['usernames']:
                hashed_password = self.hash_password(new_password)
                self.config['credentials']['usernames'][username]['password'] = hashed_password
                
                # Guardar configuración actualizada
                with open(self.config_file, 'w', encoding='utf-8') as file:
                    yaml.dump(self.config, file, default_flow_style=False, allow_unicode=True)
                
                logger.info(f"Contraseña actualizada para usuario: {username}")
                return True
        except Exception as e:
            logger.error(f"Error actualizando contraseña: {e}")
        return False
    
    def add_user(self, username, name, email, password):
        """
        Agrega un nuevo usuario
        
        Args:
            username: Nombre de usuario
            name: Nombre completo
            email: Email
            password: Contraseña
            
        Returns:
            bool: True si se agregó correctamente
        """
        try:
            if username not in self.config['credentials']['usernames']:
                hashed_password = self.hash_password(password)
                self.config['credentials']['usernames'][username] = {
                    'email': email,
                    'name': name,
                    'password': hashed_password
                }
                
                # Guardar configuración actualizada
                with open(self.config_file, 'w', encoding='utf-8') as file:
                    yaml.dump(self.config, file, default_flow_style=False, allow_unicode=True)
                
                logger.info(f"Usuario agregado: {username}")
                return True
            else:
                logger.warning(f"Usuario ya existe: {username}")
        except Exception as e:
            logger.error(f"Error agregando usuario: {e}")
        return False


# Función helper para uso rápido
def require_authentication():
    """
    Función helper para requerir autenticación en la app
    
    Usage:
        if not require_authentication():
            st.stop()
    """
    auth_manager = AuthManager()
    return auth_manager.require_auth()