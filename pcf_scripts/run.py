#!/usr/bin/env python3
"""
CEAPSI PCF System - Main Launcher
Punto de entrada principal para la aplicación Streamlit
"""

import sys
import subprocess
from pathlib import Path

def main():
    """Lanzar la aplicación CEAPSI PCF"""
    
    # Obtener la ruta del archivo app.py
    project_root = Path(__file__).parent
    app_path = project_root / "src" / "app.py"
    
    if not app_path.exists():
        print("❌ Error: No se encontró src/app.py")
        sys.exit(1)
    
    # Lanzar Streamlit
    try:
        print("🚀 Iniciando CEAPSI PCF System...")
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            str(app_path),
            "--server.address", "localhost",
            "--server.port", "8501"
        ], check=True)
    except KeyboardInterrupt:
        print("\n✋ Aplicación detenida por el usuario")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error al iniciar la aplicación: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()