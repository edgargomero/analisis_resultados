# 📁 CEAPSI - Estructura del Proyecto

## 🎯 **Estructura Reorganizada y Optimizada**

```
CEAPSI/
├── 📄 app.py                          # Aplicación principal Streamlit
├── 📄 requirements.txt                # Dependencias Python
├── 📄 .env.example                    # Variables de entorno ejemplo
├── 📄 PROJECT_STRUCTURE.md            # Este archivo
│
├── 📁 src/                            # Código fuente principal
│   ├── 📁 api/                        # Integraciones externas
│   │   └── modulo_estado_reservo.py   # API Reservo
│   ├── 📁 auth/                       # Sistema de autenticación
│   │   ├── supabase_auth.py           # Auth Supabase
│   │   └── security_check.py          # Verificaciones seguridad
│   ├── 📁 core/                       # Funcionalidades núcleo
│   │   ├── mcp_session_manager.py     # Gestor sesiones MCP
│   │   ├── mcp_init.py                # Inicializador MCP
│   │   └── preparacion_datos.py       # Preparación datos
│   ├── 📁 models/                     # Modelos ML
│   │   ├── sistema_multi_modelo.py    # Sistema multi-modelo
│   │   └── optimizacion_hiperparametros.py
│   ├── 📁 services/                   # Servicios procesamiento
│   │   ├── auditoria_datos_llamadas.py
│   │   ├── segmentacion_llamadas.py
│   │   └── automatizacion_completa.py
│   ├── 📁 ui/                         # Interfaz usuario
│   │   ├── dashboard_comparacion.py   # Dashboard principal
│   │   ├── historial_sesiones.py     # Historial análisis
│   │   └── ux_mejoras.py             # Mejoras UX
│   └── 📁 utils/                      # Utilidades
│       └── feriados_chilenos.py       # Gestión feriados
│
├── 📁 database/                       # Base de datos
│   └── 📁 migrations/                 # Migraciones SQL
│       ├── 001_create_analysis_sessions.sql
│       └── 002_audit_system.sql
│
├── 📁 assets/                         # Recursos estáticos
│   ├── 📁 data/                       # Datos ejemplo
│   │   ├── ejemplo_datos_llamadas.csv
│   │   ├── datos_prophet_entrante.csv
│   │   ├── datos_prophet_saliente.csv
│   │   └── feriadoschile.csv
│   └── 📁 models/                     # Modelos entrenados
│
├── 📁 config/                         # Configuración
│   └── streamlit_config.toml          # Config Streamlit
│
├── 📁 docs/                           # Documentación
│   ├── README.md                      # Documentación principal
│   ├── CLAUDE.md                      # Guía para Claude Code
│   ├── ARCHITECTURE.md               # Arquitectura sistema
│   ├── SUPABASE_SETUP.md             # Setup Supabase
│   └── STREAMLIT_DEPLOYMENT.md       # Despliegue Streamlit
│
├── 📁 scripts/                        # Scripts desarrollo
│   ├── 📁 development/                # Scripts desarrollo
│   │   └── run.py                     # Script ejecución
│   └── 📁 deployment/                 # Scripts despliegue
│
├── 📁 logs/                           # Logs aplicación
│   ├── ceapsi_app.log                # Log principal
│   └── 📁 archive/                    # Logs archivados
│
├── 📁 legacy/                         # Código legacy
│   └── auth.py                        # Sistema auth antiguo
│
└── 📁 .streamlit/                     # Configuración Streamlit
    ├── config.toml                    # Configuración UI
    └── secrets.toml.example           # Ejemplo secrets
```

## 🧹 **Archivos Eliminados en la Limpieza**

### ❌ **Scripts de Testing/Debug (8 archivos):**
- `explore_database.py`
- `test_analysis_sessions.py`
- `simple_test.py`
- `check_table.py`
- `create_table_direct.py`
- `manual_table_creation.py`
- `final_table_creation.py`
- `complete_test_suite.py`

### ❌ **Archivos SQL Duplicados (5 archivos):**
- `setup_ceapsi_database.sql`
- `setup_analysis_sessions.sql`
- `src/config/audit_tables.sql`
- `src/config/audit_system_setup.sql`
- `src/config/supabase_setup.sql`

### ❌ **Código Duplicado (4 archivos):**
- `src/core/session_manager.py` (mantenido MCP)
- `src/audit/audit_manager.py`
- `src/audit/setup_audit_integration.py`
- `src/config/setup_supabase.py`

### ❌ **Archivos Temporales:**
- `bash.exe.stackdump`
- `audit_setup.log`

## 🎯 **Beneficios de la Nueva Estructura**

### ✅ **Organización Clara:**
- Separación lógica por funcionalidad
- Directorios estándar de la industria
- Estructura escalable y mantenible

### ✅ **Código Optimizado:**
- 20+ archivos menos en el proyecto
- Sin duplicación de funcionalidades
- Sistema de sesiones unificado (MCP)
- Logging consolidado

### ✅ **Seguridad Mejorada:**
- Variables de entorno documentadas
- Gitignore actualizado
- Estructura de directorios segura

### ✅ **Desarrollo Simplificado:**
- Imports más claros
- Documentación centralizada
- Scripts de desarrollo organizados
- Base de datos estructurada

## 🚀 **Para Desarrolladores**

### **Ejecutar la Aplicación:**
```bash
streamlit run app.py
```

### **Estructura de Base de Datos:**
```bash
# 1. Ejecutar migraciones en Supabase Dashboard:
database/migrations/001_create_analysis_sessions.sql
database/migrations/002_audit_system.sql
```

### **Configurar Entorno:**
```bash
# 1. Copiar variables de entorno
cp .env.example .env

# 2. Completar credenciales en .env
# 3. O configurar en Streamlit Cloud secrets
```

### **Estructura MCP Supabase:**
- Configuración en `.mcp.json`
- Gestor en `src/core/mcp_session_manager.py`
- Inicializador en `src/core/mcp_init.py`
- Estado en página "🔌 Estado MCP"

¡Proyecto limpio, organizado y listo para producción! 🎉