#!/usr/bin/env python3
"""
CEAPSI PCF - Script de Setup Inicial
Verifica e instala todo lo necesario para el Proyecto PCF
"""

import sys
import subprocess
import os
import platform

def verificar_python():
    """Verifica versión de Python"""
    print("🐍 Verificando Python...")
    version = sys.version_info
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Python {version.major}.{version.minor} detectado")
        print("⚠️ Se requiere Python 3.8 o superior")
        print("💡 Descargar desde: https://www.python.org/downloads/")
        return False
    
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} OK")
    return True

def instalar_dependencias():
    """Instala todas las dependencias necesarias"""
    print("\n📦 Instalando dependencias...")
    
    # Lista de paquetes necesarios para PCF
    paquetes_base = [
        "pandas>=1.5.0",
        "numpy>=1.21.0",
        "scikit-learn>=1.1.0",
        "matplotlib>=3.5.0",
        "plotly>=5.10.0",
        "streamlit>=1.25.0",
        "schedule>=1.2.0"
    ]
    
    # Prophet (instalación especial según OS)
    paquetes_prophet = [
        "prophet>=1.1.4"
    ]
    
    # Estadísticas
    paquetes_stats = [
        "statsmodels>=0.13.0"
    ]
    
    # Utilidades
    paquetes_utils = [
        "openpyxl>=3.0.9",
        "python-dateutil>=2.8.0"
    ]
    
    todos_los_paquetes = paquetes_base + paquetes_prophet + paquetes_stats + paquetes_utils
    
    for paquete in todos_los_paquetes:
        try:
            print(f"   Instalando {paquete}...")
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", paquete
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"   ✅ {paquete} instalado")
            else:
                print(f"   ⚠️ Problema con {paquete}: {result.stderr}")
                
        except Exception as e:
            print(f"   ❌ Error instalando {paquete}: {e}")
    
    print("✅ Instalación de dependencias completada")

def crear_estructura_directorios():
    """Crea la estructura de directorios necesaria"""
    print("\n📁 Creando estructura de directorios...")
    
    # Directorio base del proyecto
    base_dir = "ceapsi_pcf_project"
    
    directorios = [
        base_dir,
        f"{base_dir}/scripts",
        f"{