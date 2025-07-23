#!/usr/bin/env python3
"""
Script de configuración inicial para Supabase
Ejecutar una sola vez después de crear el proyecto Supabase
"""

import os
from dotenv import load_dotenv
from supabase_auth import SupabaseAuthManager

def setup_supabase():
    """Configura Supabase para CEAPSI"""
    print("🚀 Configurando Supabase para CEAPSI...")
    
    # Cargar variables de entorno
    load_dotenv()
    
    # Verificar variables de entorno
    required_vars = ['SUPABASE_URL', 'SUPABASE_KEY']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Variables de entorno faltantes: {missing_vars}")
        print("\n📝 Crea un archivo .env basado en .env.example con:")
        print("SUPABASE_URL=https://tu-proyecto.supabase.co")
        print("SUPABASE_KEY=tu-anon-key-aqui")
        return False
    
    # Inicializar auth manager
    auth_manager = SupabaseAuthManager()
    
    if not auth_manager.is_available():
        print("❌ No se pudo conectar con Supabase")
        return False
    
    print("✅ Conexión Supabase establecida")
    
    # Crear tabla de usuarios
    print("\n📊 Creando tabla ceapsi_users...")
    if auth_manager.create_users_table():
        print("✅ Tabla ceapsi_users creada/verificada")
    else:
        print("❌ Error creando tabla")
        return False
    
    # Crear usuarios por defecto
    print("\n👥 Creando usuarios por defecto...")
    
    default_users = [
        {
            'username': 'admin',
            'email': 'admin@ceapsi.cl',
            'name': 'Administrador CEAPSI',
            'password': 'admin123',
            'role': 'admin'
        },
        {
            'username': 'analista1',
            'email': 'analista1@ceapsi.cl',
            'name': 'María González',
            'password': 'analista123',
            'role': 'analista'
        },
        {
            'username': 'analista2',
            'email': 'analista2@ceapsi.cl',
            'name': 'Carlos Rodríguez',
            'password': 'analista123',
            'role': 'analista'
        },
        {
            'username': 'viewer',
            'email': 'viewer@ceapsi.cl',
            'name': 'Usuario Visualización',
            'password': 'viewer123',
            'role': 'viewer'
        }
    ]
    
    for user_data in default_users:
        if auth_manager.create_user(**user_data):
            print(f"✅ Usuario creado: {user_data['username']} ({user_data['role']})")
        else:
            print(f"⚠️ Usuario existe/Error: {user_data['username']}")
    
    print("\n🎉 Configuración Supabase completada!")
    print("\n📋 Credenciales por defecto:")
    print("  Admin:     admin / admin123")
    print("  Analista:  analista1 / analista123")
    print("  Analista:  analista2 / analista123") 
    print("  Viewer:    viewer / viewer123")
    
    print("\n🔐 Recuerda cambiar las contraseñas en producción")
    return True

def test_authentication():
    """Prueba el sistema de autenticación"""
    print("\n🧪 Probando autenticación...")
    
    auth_manager = SupabaseAuthManager()
    
    if not auth_manager.is_available():
        print("❌ Supabase no disponible para pruebas")
        return
    
    # Probar login con admin
    user = auth_manager.authenticate_user('admin', 'admin123')
    if user:
        print(f"✅ Login exitoso: {user['name']} ({user['role']})")
    else:
        print("❌ Error en login de prueba")

if __name__ == "__main__":
    if setup_supabase():
        test_authentication()
        print("\n🚀 Sistema listo para usar!")
        print("   Ejecuta: streamlit run app.py")
    else:
        print("\n❌ Error en configuración")