#!/usr/bin/env python3
"""
CEAPSI - Script de Verificación Rápida
Verifica que todo esté listo para el despliegue
"""

import sys
import os
from pathlib import Path
import importlib.util

def check_python_version():
    """Verificar versión de Python"""
    version = sys.version_info
    print(f"🐍 Python {version.major}.{version.minor}.{version.micro}")
    
    if version < (3, 8):
        print("   ❌ Requiere Python 3.8+")
        return False
    else:
        print("   ✅ Versión compatible")
        return True

def check_dependencies():
    """Verificar dependencias críticas"""
    print("\n📦 Verificando dependencias...")
    
    required_packages = [
        'streamlit', 'pandas', 'numpy', 'plotly', 
        'sklearn', 'prophet', 'statsmodels', 'openpyxl'
    ]
    
    missing = []
    for package in required_packages:
        try:
            if package == 'sklearn':
                __import__('sklearn')
            else:
                __import__(package)
            print(f"   ✅ {package}")
        except ImportError:
            missing.append(package)
            print(f"   ❌ {package}")
    
    if missing:
        print(f"\n⚠️  Instalar paquetes faltantes:")
        print(f"pip install {' '.join(missing)}")
        return False
    
    return True

def check_files():
    """Verificar archivos principales"""
    print("\n📁 Verificando archivos...")
    
    required_files = [
        'app.py', 'dashboard_comparacion.py', 'sistema_multi_modelo.py',
        'requirements.txt', 'start_ceapsi.py'
    ]
    
    missing = []
    for file in required_files:
        if Path(file).exists():
            print(f"   ✅ {file}")
        else:
            missing.append(file)
            print(f"   ❌ {file}")
    
    if missing:
        print(f"\n⚠️  Archivos faltantes: {', '.join(missing)}")
        return False
    
    return True

def test_streamlit_import():
    """Probar importación de Streamlit"""
    print("\n🚀 Probando Streamlit...")
    
    try:
        import streamlit as st
        print(f"   ✅ Streamlit {st.__version__} importado correctamente")
        return True
    except Exception as e:
        print(f"   ❌ Error con Streamlit: {e}")
        return False

def test_app_syntax():
    """Verificar sintaxis del archivo principal"""
    print("\n🔍 Verificando sintaxis de app.py...")
    
    try:
        with open('app.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Compilar para verificar sintaxis
        compile(content, 'app.py', 'exec')
        print("   ✅ Sintaxis correcta")
        return True
    
    except SyntaxError as e:
        print(f"   ❌ Error de sintaxis: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def main():
    """Ejecutar verificación completa"""
    print("🔍 CEAPSI - Verificación Rápida del Sistema")
    print("=" * 50)
    
    checks = [
        check_python_version(),
        check_dependencies(),
        check_files(),
        test_streamlit_import(),
        test_app_syntax()
    ]
    
    print("\n" + "=" * 50)
    print("📋 RESULTADO DE LA VERIFICACIÓN")
    print("=" * 50)
    
    if all(checks):
        print("🎉 ¡TODO LISTO! El sistema está preparado para ejecutarse")
        print("\n🚀 COMANDOS PARA INICIAR:")
        print("   python start_ceapsi.py")
        print("   # O alternativamente:")
        print("   streamlit run app.py")
        print("\n🌐 URL: http://localhost:8501")
    else:
        print("⚠️  Se requieren correcciones antes del despliegue")
        print("\n🔧 PASOS SUGERIDOS:")
        print("1. pip install -r requirements.txt")
        print("2. python fix_ceapsi.py")
        print("3. python verify_ceapsi.py")
    
    return all(checks)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
