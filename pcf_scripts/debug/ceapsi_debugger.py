#!/usr/bin/env python3
"""
CEAPSI - Script de Debugging y Diagnóstico
Identifica y soluciona problemas comunes en el despliegue
"""

import sys
import os
import subprocess
import importlib.util
from pathlib import Path
import json

class CEAPSIDebugger:
    def __init__(self):
        self.project_dir = Path(__file__).parent.parent
        self.issues = []
        self.fixes_applied = []
        
    def check_python_version(self):
        """Verificar versión de Python"""
        print("🐍 Verificando versión de Python...")
        version = sys.version_info
        print(f"   Python {version.major}.{version.minor}.{version.micro}")
        
        if version < (3, 8):
            self.issues.append("Python version < 3.8")
            print("   ❌ Requiere Python 3.8 o superior")
            return False
        else:
            print("   ✅ Versión de Python compatible")
            return True
    
    def check_dependencies(self):
        """Verificar dependencias instaladas"""
        print("\n📦 Verificando dependencias...")
        
        requirements_file = self.project_dir / "requirements.txt"
        if not requirements_file.exists():
            print("   ❌ Archivo requirements.txt no encontrado")
            return False
        
        try:
            with open(requirements_file, 'r') as f:
                requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            
            missing_packages = []
            
            for req in requirements:
                package_name = req.split('==')[0].split('>=')[0].split('<=')[0]
                try:
                    __import__(package_name)
                    print(f"   ✅ {package_name}")
                except ImportError:
                    missing_packages.append(req)
                    print(f"   ❌ {package_name} - NO INSTALADO")
            
            if missing_packages:
                self.issues.append(f"Paquetes faltantes: {', '.join(missing_packages)}")
                return False
            else:
                print("   ✅ Todas las dependencias están instaladas")
                return True
                
        except Exception as e:
            print(f"   ❌ Error verificando dependencias: {e}")
            return False
    
    def check_file_structure(self):
        """Verificar estructura de archivos"""
        print("\n📁 Verificando estructura de archivos...")
        
        required_files = [
            "app.py",
            "dashboard_comparacion.py", 
            "sistema_multi_modelo.py",
            "segmentacion_llamadas.py",
            "auditoria_datos_llamadas.py",
            "automatizacion_completa.py",
            "requirements.txt"
        ]
        
        missing_files = []
        for file in required_files:
            file_path = self.project_dir / file
            if file_path.exists():
                print(f"   ✅ {file}")
            else:
                missing_files.append(file)
                print(f"   ❌ {file} - NO ENCONTRADO")
        
        if missing_files:
            self.issues.append(f"Archivos faltantes: {', '.join(missing_files)}")
            return False
        else:
            print("   ✅ Todos los archivos principales están presentes")
            return True
    
    def check_imports(self):
        """Verificar imports en archivos principales"""
        print("\n🔍 Verificando imports...")
        
        files_to_check = ["app.py", "dashboard_comparacion.py", "sistema_multi_modelo.py"]
        
        for file in files_to_check:
            file_path = self.project_dir / file
            if not file_path.exists():
                continue
                
            print(f"   Verificando {file}...")
            
            try:
                # Leer archivo y buscar imports problemáticos
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Verificar imports locales
                if 'from dashboard_comparacion import' in content:
                    dashboard_path = self.project_dir / "dashboard_comparacion.py"
                    if not dashboard_path.exists():
                        self.issues.append(f"{file}: dashboard_comparacion.py no encontrado")
                
                if 'from sistema_multi_modelo import' in content:
                    sistema_path = self.project_dir / "sistema_multi_modelo.py"
                    if not sistema_path.exists():
                        self.issues.append(f"{file}: sistema_multi_modelo.py no encontrado")
                
                print(f"   ✅ {file} - imports verificados")
                
            except Exception as e:
                print(f"   ❌ {file} - Error: {e}")
                self.issues.append(f"Error en {file}: {str(e)}")
    
    def fix_import_paths(self):
        """Corregir problemas de imports"""
        print("\n🔧 Corrigiendo problemas de imports...")
        
        app_file = self.project_dir / "app.py"
        if app_file.exists():
            try:
                with open(app_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Agregar path fix al inicio si no existe
                path_fix = """
# Fix para imports locales
import sys
from pathlib import Path
current_dir = Path(__file__).parent.absolute()
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))
"""
                
                if "sys.path.insert(0, str(current_dir))" not in content:
                    # Buscar donde insertar el fix
                    lines = content.split('\n')
                    insert_index = 0
                    
                    # Buscar después de imports básicos
                    for i, line in enumerate(lines):
                        if line.strip().startswith('import streamlit') or line.strip().startswith('import sys'):
                            insert_index = i + 1
                            break
                    
                    lines.insert(insert_index, path_fix)
                    
                    # Escribir archivo corregido
                    with open(app_file, 'w', encoding='utf-8') as f:
                        f.write('\n'.join(lines))
                    
                    self.fixes_applied.append("Path fix agregado a app.py")
                    print("   ✅ Path fix aplicado a app.py")
                
            except Exception as e:
                print(f"   ❌ Error corrigiendo app.py: {e}")
    
    def test_streamlit_compatibility(self):
        """Probar compatibilidad con Streamlit"""
        print("\n🚀 Probando compatibilidad con Streamlit...")
        
        try:
            import streamlit as st
            print("   ✅ Streamlit importado correctamente")
            
            # Verificar versión de Streamlit
            st_version = st.__version__
            print(f"   📋 Versión de Streamlit: {st_version}")
            
            # Verificar que no hay conflictos de sesión
            app_file = self.project_dir / "app.py"
            if app_file.exists():
                with open(app_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if 'st.session_state' in content:
                    print("   ✅ Uso de session_state detectado")
                else:
                    print("   ⚠️  No se detectó uso de session_state")
            
            return True
            
        except Exception as e:
            print(f"   ❌ Error con Streamlit: {e}")
            self.issues.append(f"Problema con Streamlit: {str(e)}")
            return False
    
    def create_startup_script(self):
        """Crear script de inicio mejorado"""
        print("\n📝 Creando script de inicio...")
        
        startup_script = f"""#!/usr/bin/env python3
\"\"\"
CEAPSI - Script de Inicio con Debugging
\"\"\"

import sys
import os
from pathlib import Path

# Configurar paths
project_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_dir))

# Configurar variables de entorno
os.environ['STREAMLIT_SERVER_HEADLESS'] = 'true'
os.environ['STREAMLIT_SERVER_PORT'] = '8501'
os.environ['STREAMLIT_THEME_BASE'] = 'light'

def main():
    print("🚀 Iniciando CEAPSI - Sistema PCF")
    print(f"📁 Directorio del proyecto: {{project_dir}}")
    
    # Verificar archivos críticos
    critical_files = ["app.py", "dashboard_comparacion.py", "sistema_multi_modelo.py"]
    
    for file in critical_files:
        if (project_dir / file).exists():
            print(f"✅ {{file}} encontrado")
        else:
            print(f"❌ {{file}} NO encontrado")
            return False
    
    # Ejecutar aplicación
    try:
        import streamlit.web.cli as stcli
        sys.argv = ["streamlit", "run", str(project_dir / "app.py")]
        stcli.main()
    except Exception as e:
        print(f"❌ Error ejecutando Streamlit: {{e}}")
        return False

if __name__ == "__main__":
    main()
"""
        
        startup_file = self.project_dir / "start_ceapsi.py"
        with open(startup_file, 'w', encoding='utf-8') as f:
            f.write(startup_script)
        
        self.fixes_applied.append("Script de inicio creado: start_ceapsi.py")
        print("   ✅ Script de inicio creado: start_ceapsi.py")
    
    def create_config_file(self):
        """Crear archivo de configuración para Streamlit"""
        print("\n⚙️ Creando configuración de Streamlit...")
        
        config_dir = self.project_dir / ".streamlit"
        config_dir.mkdir(exist_ok=True)
        
        config_content = """[global]
developmentMode = false
showWarningOnDirectExecution = false

[server]
headless = true
port = 8501
enableCORS = false
enableXsrfProtection = false

[browser]
gatherUsageStats = false

[theme]
base = "light"
primaryColor = "#FF6B6B"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"

[logger]
level = "info"
"""
        
        config_file = config_dir / "config.toml"
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write(config_content)
        
        self.fixes_applied.append("Configuración de Streamlit creada")
        print("   ✅ Configuración de Streamlit creada")
    
    def run_full_diagnosis(self):
        """Ejecutar diagnóstico completo"""
        print("🔍 CEAPSI - Diagnóstico Completo del Sistema")
        print("=" * 50)
        
        # Ejecutar todas las verificaciones
        checks = [
            self.check_python_version(),
            self.check_dependencies(),
            self.check_file_structure(),
            self.check_imports(),
            self.test_streamlit_compatibility()
        ]
        
        # Aplicar correcciones
        self.fix_import_paths()
        self.create_startup_script()
        self.create_config_file()
        
        # Resumen
        print("\n" + "=" * 50)
        print("📋 RESUMEN DEL DIAGNÓSTICO")
        print("=" * 50)
        
        if all(checks):
            print("✅ Todos los checks pasaron exitosamente")
        else:
            print("❌ Se encontraron problemas:")
            for issue in self.issues:
                print(f"   • {issue}")
        
        if self.fixes_applied:
            print("\n🔧 Correcciones aplicadas:")
            for fix in self.fixes_applied:
                print(f"   • {fix}")
        
        print("\n🚀 INSTRUCCIONES DE INICIO:")
        print("1. Ejecutar: python start_ceapsi.py")
        print("2. O alternativamente: streamlit run app.py")
        print("3. La aplicación estará disponible en: http://localhost:8501")
        
        return len(self.issues) == 0

if __name__ == "__main__":
    debugger = CEAPSIDebugger()
    success = debugger.run_full_diagnosis()
    
    if success:
        print("\n🎉 Sistema listo para despliegue!")
    else:
        print("\n⚠️  Se requieren correcciones antes del despliegue")
