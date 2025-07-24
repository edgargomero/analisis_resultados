"""
CEAPSI Backend - Streamlit Wrapper
Wrapper para ejecutar el backend FastAPI dentro de Streamlit Cloud
"""

import streamlit as st
import subprocess
import threading
import time
import requests
import os
import sys
from pathlib import Path

# Add backend to path
current_dir = Path(__file__).parent.absolute()
backend_dir = current_dir / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

st.set_page_config(
    page_title="CEAPSI Backend API",
    page_icon="⚙️",
    layout="wide"
)

def run_backend():
    """Run FastAPI backend in background"""
    try:
        import uvicorn
        from backend.app.main import app
        
        uvicorn.run(
            app, 
            host="0.0.0.0", 
            port=8000,
            log_level="info"
        )
    except Exception as e:
        st.error(f"Error starting backend: {e}")

def check_backend_health():
    """Check if backend is running"""
    try:
        response = requests.get("http://localhost:8000/health", timeout=2)
        return response.status_code == 200, response.json()
    except:
        return False, None

# Initialize session state
if 'backend_started' not in st.session_state:
    st.session_state.backend_started = False

# Main interface
st.title("⚙️ CEAPSI Backend API")
st.markdown("Sistema de análisis de llamadas para call center - API Backend")
st.markdown("---")

# Backend status
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("🚀 Estado del Backend")
    
    if not st.session_state.backend_started:
        st.info("🔄 Backend no iniciado")
        
        if st.button("🚀 Iniciar Backend API", type="primary"):
            with st.spinner("Iniciando backend..."):
                # Start backend in background thread
                backend_thread = threading.Thread(target=run_backend, daemon=True)
                backend_thread.start()
                
                st.session_state.backend_started = True
                time.sleep(3)  # Wait for startup
                st.rerun()
    else:
        # Check health
        is_healthy, health_data = check_backend_health()
        
        if is_healthy:
            st.success("✅ Backend API ejecutándose correctamente")
            
            # Show health data
            if health_data:
                st.json(health_data)
        else:
            st.error("❌ Backend no responde")
            if st.button("🔄 Reiniciar Backend"):
                st.session_state.backend_started = False
                st.rerun()

with col2:
    st.subheader("🔗 Enlaces Rápidos")
    
    if st.session_state.backend_started:
        st.markdown("**API Documentation:**")
        st.markdown("- [📖 Swagger UI](http://localhost:8000/docs)")
        st.markdown("- [📋 ReDoc](http://localhost:8000/redoc)")
        st.markdown("- [❤️ Health Check](http://localhost:8000/health)")
        
        st.markdown("**Base URL:**")
        st.code("http://localhost:8000", language="text")

# API Information
if st.session_state.backend_started:
    st.markdown("---")
    st.subheader("📋 Información de la API")
    
    # Endpoint documentation
    endpoints_data = [
        {
            "method": "GET",
            "endpoint": "/",
            "description": "Información básica de la API"
        },
        {
            "method": "GET", 
            "endpoint": "/health",
            "description": "Estado de salud del sistema"
        },
        {
            "method": "POST",
            "endpoint": "/api/v1/analysis/upload",
            "description": "Subir archivo de datos"
        },
        {
            "method": "POST",
            "endpoint": "/api/v1/analysis/audit",
            "description": "Ejecutar auditoría de datos"
        },
        {
            "method": "POST",
            "endpoint": "/api/v1/analysis/segment",
            "description": "Ejecutar segmentación de llamadas"
        },
        {
            "method": "POST",
            "endpoint": "/api/v1/analysis/predict",
            "description": "Generar predicciones"
        },
        {
            "method": "GET",
            "endpoint": "/api/v1/sessions/",
            "description": "Listar sesiones de usuario"
        },
        {
            "method": "GET",
            "endpoint": "/api/v1/sessions/{id}",
            "description": "Obtener detalles de sesión"
        }
    ]
    
    # Display endpoints in a nice table
    for endpoint in endpoints_data:
        with st.expander(f"{endpoint['method']} {endpoint['endpoint']}"):
            st.write(endpoint['description'])
            
            # Show example curl if backend is running
            if endpoint['method'] == 'GET':
                st.code(f"curl -X GET http://localhost:8000{endpoint['endpoint']}", language="bash")

# Connection instructions
st.markdown("---")
st.subheader("🔧 Conexión desde Frontend")

st.markdown("""
Para conectar el frontend Streamlit con este backend, configura:

**En Streamlit Secrets:**
```toml
BACKEND_URL = "https://tu-backend-app.streamlit.app"
```

**O en archivo .env:**
```env
BACKEND_URL=http://localhost:8000
```
""")

# Environment info
with st.expander("🔍 Información del Entorno"):
    st.write("**Python Version:**", sys.version)
    st.write("**Working Directory:**", os.getcwd())
    st.write("**Available Modules:**")
    
    try:
        import fastapi
        st.write(f"- FastAPI: {fastapi.__version__}")
    except:
        st.write("- FastAPI: ❌ No disponible")
    
    try:
        import uvicorn
        st.write(f"- Uvicorn: {uvicorn.__version__}")  
    except:
        st.write("- Uvicorn: ❌ No disponible")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center;">
    <small>CEAPSI Backend API v2.0 - Sistema de análisis de llamadas</small>
</div>
""", unsafe_allow_html=True)