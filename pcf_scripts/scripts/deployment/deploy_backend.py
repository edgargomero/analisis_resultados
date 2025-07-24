"""
CEAPSI Backend Deployment Script
Script para desplegar el backend en diferentes plataformas
"""

import os
import subprocess
import sys
from pathlib import Path

def deploy_to_streamlit_cloud():
    """Deploy backend as a separate Streamlit app"""
    
    print("🚀 Preparando despliegue de backend en Streamlit Cloud...")
    
    # Create a streamlit wrapper for the FastAPI app
    backend_streamlit_app = """
import streamlit as st
import subprocess
import threading
import time
import requests
from backend.app.main import app
import uvicorn

st.set_page_config(
    page_title="CEAPSI Backend API",
    page_icon="⚙️",
    layout="wide"
)

def run_backend():
    \"\"\"Run FastAPI backend\"\"\"
    uvicorn.run(app, host="0.0.0.0", port=8000)

if 'backend_started' not in st.session_state:
    st.session_state.backend_started = False

st.title("⚙️ CEAPSI Backend API")
st.markdown("---")

if not st.session_state.backend_started:
    if st.button("🚀 Iniciar Backend API"):
        # Start backend in thread
        backend_thread = threading.Thread(target=run_backend, daemon=True)
        backend_thread.start()
        st.session_state.backend_started = True
        st.success("Backend iniciado!")
        time.sleep(2)
        st.rerun()

if st.session_state.backend_started:
    st.success("✅ Backend API está ejecutándose")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📋 Información de la API")
        st.write("**URL Base:** http://localhost:8000")
        st.write("**Documentación:** [/docs](http://localhost:8000/docs)")
        st.write("**Health Check:** [/health](http://localhost:8000/health)")
        
    with col2:
        st.subheader("🔧 Estado del Servicio")
        
        try:
            response = requests.get("http://localhost:8000/health", timeout=5)
            if response.status_code == 200:
                health_data = response.json()
                st.success("🟢 Servicio Saludable")
                st.json(health_data)
            else:
                st.error("🔴 Servicio con Problemas")
        except:
            st.warning("🟡 Verificando estado...")
            
    st.markdown("---")
    st.subheader("📖 Documentación de Endpoints")
    
    endpoints = [
        {"method": "GET", "path": "/", "description": "Información de la API"},
        {"method": "GET", "path": "/health", "description": "Estado de salud"},
        {"method": "POST", "path": "/api/v1/analysis/upload", "description": "Subir archivo"},
        {"method": "POST", "path": "/api/v1/analysis/audit", "description": "Auditoría de datos"},
        {"method": "GET", "path": "/api/v1/sessions/", "description": "Listar sesiones"},
    ]
    
    for endpoint in endpoints:
        st.write(f"**{endpoint['method']}** `{endpoint['path']}` - {endpoint['description']}")
"""
    
    # Write the streamlit backend app
    with open("backend_streamlit.py", "w", encoding="utf-8") as f:
        f.write(backend_streamlit_app)
    
    print("✅ Archivo backend_streamlit.py creado")
    print("📋 Para desplegar:")
    print("   1. Subir todo el repositorio a GitHub")
    print("   2. Crear nueva app en Streamlit Cloud apuntando a backend_streamlit.py")
    print("   3. Configurar variables de entorno en Streamlit Secrets")

def deploy_to_heroku():
    """Deploy backend to Heroku"""
    
    print("🚀 Preparando despliegue en Heroku...")
    
    # Create Procfile
    procfile_content = "web: cd backend && uvicorn app.main:app --host=0.0.0.0 --port=${PORT:-8000}"
    
    with open("Procfile", "w") as f:
        f.write(procfile_content)
    
    # Create runtime.txt
    with open("runtime.txt", "w") as f:
        f.write("python-3.10.12")
    
    print("✅ Archivos de despliegue Heroku creados")
    print("📋 Para desplegar:")
    print("   1. heroku create ceapsi-backend")
    print("   2. git push heroku main")

def deploy_to_railway():
    """Deploy backend to Railway"""
    
    print("🚀 Preparando despliegue en Railway...")
    
    # Create railway.json
    railway_config = {
        "build": {
            "builder": "NIXPACKS"
        },
        "deploy": {
            "startCommand": "cd backend && uvicorn app.main:app --host=0.0.0.0 --port=$PORT",
            "healthcheckPath": "/health"
        }
    }
    
    import json
    with open("railway.json", "w") as f:
        json.dump(railway_config, f, indent=2)
    
    print("✅ Configuración Railway creada")
    print("📋 Para desplegar:")
    print("   1. Conectar repositorio en railway.app")
    print("   2. Configurar variables de entorno")

if __name__ == "__main__":
    print("🏗️  CEAPSI Backend Deployment")
    print("=" * 40)
    
    choice = input("""
Seleccionar plataforma de despliegue:
1. Streamlit Cloud (Recomendado)
2. Heroku
3. Railway
4. Todas las opciones

Ingresa tu elección (1-4): """)
    
    if choice == "1":
        deploy_to_streamlit_cloud()
    elif choice == "2":
        deploy_to_heroku()
    elif choice == "3":
        deploy_to_railway()
    elif choice == "4":
        deploy_to_streamlit_cloud()
        deploy_to_heroku()
        deploy_to_railway()
    else:
        print("❌ Opción no válida")
        sys.exit(1)
    
    print("\n✅ Preparación de despliegue completada!")