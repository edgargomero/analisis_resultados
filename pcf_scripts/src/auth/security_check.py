#!/usr/bin/env python3
"""
CEAPSI Security Check
Verifica la configuración de seguridad del sistema
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger('SECURITY_CHECK')

def check_environment():
    """Verifica variables de entorno críticas"""
    print("🔍 Verificando configuración de entorno...")
    
    # Cargar variables de entorno
    env_file = Path('.env')
    if not env_file.exists():
        print("❌ CRÍTICO: Archivo .env no encontrado")
        return False
    
    load_dotenv()
    
    # Variables críticas
    critical_vars = [
        'SUPABASE_URL',
        'SUPABASE_KEY', 
        'SUPABASE_PROJECT_REF'
    ]
    
    missing_vars = []
    for var in critical_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ CRÍTICO: Variables faltantes: {missing_vars}")
        return False
    
    print("✅ Variables de entorno configuradas")
    return True

def check_supabase_connection():
    """Verifica conexión con Supabase"""
    print("🔍 Verificando conexión Supabase...")
    
    try:
        from supabase_auth import SupabaseAuthManager
        auth_manager = SupabaseAuthManager()
        
        if not auth_manager.is_available():
            print("❌ CRÍTICO: No se puede conectar con Supabase")
            return False
            
        print("✅ Conexión Supabase establecida")
        return True
        
    except ImportError as e:
        print(f"❌ CRÍTICO: No se puede importar supabase_auth: {e}")
        return False
    except Exception as e:
        print(f"❌ CRÍTICO: Error conexión Supabase: {e}")
        return False

def check_security_files():
    """Verifica archivos de seguridad"""
    print("🔍 Verificando archivos de seguridad...")
    
    # Archivos que NO deben existir en producción
    insecure_files = [
        'config.yaml',
        'auth.py',
        'test_credentials.json'
    ]
    
    found_insecure = []
    for file in insecure_files:
        if Path(file).exists():
            found_insecure.append(file)
    
    if found_insecure:
        print(f"⚠️  ADVERTENCIA: Archivos inseguros encontrados: {found_insecure}")
        print("   Recomendación: Mover a carpeta legacy/")
    
    # Archivos críticos que deben existir
    required_files = [
        'supabase_auth.py',
        '.env',
        '.gitignore'
    ]
    
    missing_files = []
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ CRÍTICO: Archivos requeridos faltantes: {missing_files}")
        return False
    
    print("✅ Archivos de seguridad verificados")
    return True

def check_gitignore():
    """Verifica configuración .gitignore"""
    print("🔍 Verificando .gitignore...")
    
    gitignore_file = Path('.gitignore')
    if not gitignore_file.exists():
        print("❌ CRÍTICO: Archivo .gitignore no encontrado")
        return False
    
    content = gitignore_file.read_text()
    
    # Patrones críticos que deben estar en .gitignore
    critical_patterns = ['.env', '*.toml', '*_credentials.*']
    
    missing_patterns = []
    for pattern in critical_patterns:
        if pattern not in content:
            missing_patterns.append(pattern)
    
    if missing_patterns:
        print(f"⚠️  ADVERTENCIA: Patrones faltantes en .gitignore: {missing_patterns}")
        return False
    
    print("✅ Configuración .gitignore correcta")
    return True

def check_dependencies():
    """Verifica dependencias de seguridad"""
    print("🔍 Verificando dependencias...")
    
    try:
        import supabase
        import dotenv
        print("✅ Dependencias críticas instaladas")
        return True
    except ImportError as e:
        print(f"❌ CRÍTICO: Dependencia faltante: {e}")
        print("   Ejecutar: pip install supabase python-dotenv")
        return False

def check_app_security():
    """Verifica configuración de seguridad en app.py"""
    print("🔍 Verificando configuración app.py...")
    
    app_file = Path('app.py')
    if not app_file.exists():
        print("❌ CRÍTICO: app.py no encontrado")
        return False
    
    content = app_file.read_text()
    
    # Verificar que NO use sistema YAML
    if 'AuthManager()' in content and 'auth.py' in content:
        print("⚠️  ADVERTENCIA: Posible referencia al sistema YAML legacy")
    
    # Verificar que use SOLO Supabase
    if 'SUPABASE_AUTH_AVAILABLE' not in content:
        print("❌ CRÍTICO: Sistema Supabase no implementado correctamente")
        return False
    
    print("✅ Configuración app.py verificada")
    return True

def check_production_readiness():
    """Verifica configuración para producción"""
    print("🔍 Verificando configuración de producción...")
    
    environment = os.getenv('ENVIRONMENT', 'development')
    debug = os.getenv('DEBUG', 'true').lower() == 'true'
    
    if environment == 'development':
        print("⚠️  ADVERTENCIA: Aplicación en modo desarrollo")
        print("   Para producción: ENVIRONMENT=production en .env")
    
    if debug and environment == 'production':
        print("⚠️  ADVERTENCIA: DEBUG activado en producción")
        print("   Para producción: DEBUG=false en .env")
    
    print("✅ Configuración de producción revisada")
    return True

def main():
    """Ejecuta verificación completa de seguridad"""
    print("=" * 60)
    print("🔒 CEAPSI - Verificación de Seguridad")
    print("=" * 60)
    
    checks = [
        check_dependencies,
        check_environment,
        check_supabase_connection,
        check_security_files,
        check_gitignore,
        check_app_security,
        check_production_readiness
    ]
    
    passed = 0
    total = len(checks)
    
    for check in checks:
        try:
            if check():
                passed += 1
            print("-" * 40)
        except Exception as e:
            print(f"❌ ERROR en verificación: {e}")
            print("-" * 40)
    
    print("=" * 60)
    print(f"📊 RESULTADO: {passed}/{total} verificaciones pasadas")
    
    if passed == total:
        print("🎉 SISTEMA SEGURO - Listo para producción")
        return True
    elif passed >= total * 0.8:
        print("⚠️  ADVERTENCIAS ENCONTRADAS - Revisar antes de producción")
        return False
    else:
        print("🚨 PROBLEMAS CRÍTICOS - NO usar en producción")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)