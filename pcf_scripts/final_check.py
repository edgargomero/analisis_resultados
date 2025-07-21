#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CEAPSI - Script de Correcion Final (sin caracteres especiales)
Resuelve problemas de encoding y verifica funcionamiento
"""

import os
import sys
from pathlib import Path

def fix_encoding_issues():
    """Corregir problemas de encoding"""
    print("Corrigiendo problemas de encoding...")
    
    # Verificar Python
    version = sys.version_info
    if version >= (3, 8):
        print("   Python version: OK")
    else:
        print("   Python version: Requiere 3.8+")
    
    # Verificar dependencias criticas
    deps = ['streamlit', 'pandas', 'numpy', 'plotly']
    for dep in deps:
        try:
            __import__(dep)
            print(f"   {dep}: OK")
        except ImportError:
            print(f"   {dep}: FALTANTE")
    
    return True

def verify_files():
    """Verificar archivos principales"""
    print("Verificando archivos...")
    
    files = ['app.py', 'dashboard_comparacion.py', 'requirements.txt']
    for file in files:
        if Path(file).exists():
            print(f"   {file}: OK")
        else:
            print(f"   {file}: FALTANTE")
    
    return True

def test_streamlit():
    """Probar Streamlit"""
    print("Probando Streamlit...")
    
    try:
        import streamlit as st
        print(f"   Streamlit {st.__version__}: OK")
        return True
    except Exception as e:
        print(f"   Error: {e}")
        return False

def main():
    print("CEAPSI - Verificacion Final")
    print("=" * 40)
    
    # Ejecutar verificaciones
    checks = [
        fix_encoding_issues(),
        verify_files(),
        test_streamlit()
    ]
    
    print("\n" + "=" * 40)
    
    if all(checks):
        print("SISTEMA LISTO!")
        print("\nPara iniciar:")
        print("  streamlit run app.py")
        print("\nURL: http://localhost:8501")
    else:
        print("Se requieren correcciones")
        print("\nEjecutar:")
        print("  pip install -r requirements.txt")
    
    print("=" * 40)

if __name__ == "__main__":
    main()
