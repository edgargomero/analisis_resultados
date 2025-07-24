"""
CEAPSI - Inicializador MCP Supabase
Configura la conexión MCP Supabase para la aplicación
"""

import streamlit as st
import os
import logging

logger = logging.getLogger(__name__)

def init_mcp_connection():
    """
    Inicializa la conexión MCP Supabase usando st.connection
    """
    try:
        # Verificar si MCP está configurado
        if not hasattr(st, 'connection'):
            logger.warning("st.connection no disponible - usando fallback local")
            return False
        
        # Configurar conexión usando las variables del .mcp.json
        # Estas deberían estar disponibles como variables de entorno
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_KEY')
        
        # También revisar secrets de Streamlit
        if not supabase_url and hasattr(st, 'secrets'):
            supabase_url = st.secrets.get('SUPABASE_URL')
            supabase_key = st.secrets.get('SUPABASE_KEY')
        
        # Si aún no hay credenciales, usar las del .mcp.json (proyecto específico)
        if not supabase_url:
            # Proyecto CEAPSI específico desde .mcp.json
            supabase_url = "https://lvouimzndppleeolbbhj.supabase.co"
            logger.info("Usando URL de proyecto CEAPSI desde configuración MCP")
        
        if not supabase_key:
            logger.warning("SUPABASE_KEY no encontrada - conexión limitada")
        
        # Crear conexión SQL usando MCP
        try:
            # Configurar connection parameters para MCP Supabase
            connection_params = {
                'url': supabase_url,
                'key': supabase_key
            }
            
            # Intentar crear conexión
            conn = st.connection('supabase', type='sql', **connection_params)
            
            # Test de conexión simple
            test_query = "SELECT 1 as test"
            result = conn.query(test_query)
            
            if not result.empty:
                logger.info("✅ Conexión MCP Supabase establecida correctamente")
                st.session_state.mcp_available = True
                return True
            else:
                logger.warning("Conexión MCP establecida pero sin resultados")
                return False
                
        except Exception as e:
            logger.error(f"Error en conexión MCP específica: {e}")
            # Fallback: marcar MCP como no disponible pero continuar
            st.session_state.mcp_available = False
            return False
            
    except Exception as e:
        logger.error(f"Error inicializando MCP: {e}")
        st.session_state.mcp_available = False
        return False

def get_mcp_connection():
    """
    Obtiene la conexión MCP activa
    """
    try:
        if hasattr(st, 'connection') and st.session_state.get('mcp_available', False):
            return st.connection('supabase', type='sql')
        return None
    except Exception as e:
        logger.error(f"Error obteniendo conexión MCP: {e}")
        return None

def test_mcp_connection():
    """
    Prueba la conexión MCP y retorna información de estado
    """
    status = {
        'available': False,
        'connection_type': 'none',
        'error': None,
        'project_id': None
    }
    
    try:
        # Verificar si st.connection está disponible
        if not hasattr(st, 'connection'):
            status['error'] = "st.connection no disponible"
            return status
        
        # Verificar inicialización
        if not st.session_state.get('mcp_available', False):
            # Intentar inicializar
            if not init_mcp_connection():
                status['error'] = "No se pudo inicializar conexión MCP"
                return status
        
        # Obtener conexión
        conn = get_mcp_connection()
        if not conn:
            status['error'] = "No se pudo obtener conexión MCP"
            return status
        
        # Test avanzado de conexión
        try:
            # Verificar tablas existentes
            tables_query = """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'analysis_sessions'
            """
            
            result = conn.query(tables_query)
            
            if not result.empty:
                status['available'] = True
                status['connection_type'] = 'mcp_supabase'
                status['tables_ready'] = True
            else:
                status['available'] = True
                status['connection_type'] = 'mcp_supabase'
                status['tables_ready'] = False
                status['error'] = "Tabla analysis_sessions no existe - ejecutar setup SQL"
                
        except Exception as e:
            status['available'] = True
            status['connection_type'] = 'mcp_supabase'
            status['tables_ready'] = False
            status['error'] = f"Error verificando tablas: {e}"
        
        # Intentar obtener project info
        try:
            # Esto podría no funcionar en todos los casos, pero intentamos
            project_query = "SELECT current_database() as project"
            result = conn.query(project_query)
            if not result.empty:
                status['project_id'] = result.iloc[0]['project']
        except:
            status['project_id'] = "lvouimzndppleeolbbhj"  # Conocido desde .mcp.json
        
    except Exception as e:
        status['error'] = f"Error en test de conexión: {e}"
    
    return status

def show_mcp_status():
    """
    Muestra el estado de la conexión MCP en la interfaz
    """
    status = test_mcp_connection()
    
    st.subheader("🔌 Estado de Conexión MCP Supabase")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if status['available']:
            st.success("✅ MCP Disponible")
        else:
            st.error("❌ MCP No Disponible")
    
    with col2:
        st.info(f"**Tipo:** {status['connection_type']}")
    
    with col3:
        if status.get('project_id'):
            st.info(f"**Proyecto:** {status['project_id'][:8]}...")
    
    # Mostrar detalles
    if status['available']:
        if status.get('tables_ready'):
            st.success("✅ Base de datos configurada correctamente")
        else:
            st.warning("⚠️ Tablas de base de datos no configuradas")
            st.info("💡 Ve a Supabase Dashboard y ejecuta el SQL de setup")
    
    if status['error']:
        st.error(f"**Error:** {status['error']}")
    
    # Información técnica en expander
    with st.expander("🔧 Información Técnica"):
        st.json(status)
    
    return status