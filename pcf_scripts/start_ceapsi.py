#!/usr/bin/env python3
"""
CEAPSI - Script de Inicio
"""

import sys
import os
from pathlib import Path

# Configurar paths
project_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_dir))

def main():
    print("🚀 Iniciando CEAPSI - Sistema PCF")
    print(f"📁 Directorio del proyecto: {project_dir}")
    
    # Verificar archivo principal
    app_file = project_dir / "app.py"
    if not app_file.exists():
        print("❌ app.py no encontrado")
        return False
    
    print("✅ Archivos verificados")
    
    # Ejecutar aplicación
    try:
        os.system(f"streamlit run {app_file}")
    except Exception as e:
        print(f"❌ Error ejecutando Streamlit: {e}")
        return False

if __name__ == "__main__":
    main()
