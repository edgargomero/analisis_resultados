# 📁 CEAPSI - Estructura Backend/Frontend Separados

## 🎯 **Nueva Arquitectura Separada**

```
CEAPSI/
├── 📄 app.py                          # ⚠️ LEGACY - App monolítica original
├── 📄 backend_streamlit.py            # 🆕 Backend wrapper para Streamlit Cloud
├── 📄 DEPLOYMENT_GUIDE.md             # 🆕 Guía de despliegue
├── 📄 PROJECT_STRUCTURE_SEPARATED.md  # 🆕 Este archivo
│
├── 🖥️ backend/                        # 🆕 Backend FastAPI
│   ├── 📄 requirements.txt            # Dependencias backend
│   └── 📁 app/                        # Aplicación FastAPI
│       ├── 📄 main.py                 # App principal FastAPI
│       ├── 📁 api/routers/            # Endpoints REST
│       │   ├── analysis.py            # Rutas de análisis
│       │   ├── sessions.py            # Rutas de sesiones
│       │   ├── data.py                # Rutas de datos
│       │   └── models.py              # Rutas de modelos
│       ├── 📁 core/                   # Configuración núcleo
│       │   ├── config.py              # Configuración Pydantic
│       │   └── auth.py                # Autenticación JWT
│       ├── 📁 models/                 # Schemas Pydantic
│       │   └── schemas.py             # Modelos de datos
│       └── 📁 services/               # Lógica de negocio
│
├── 🌐 frontend/                       # 🆕 Frontend Streamlit
│   ├── 📄 app.py                      # App Streamlit principal
│   ├── 📄 api_client.py               # Cliente HTTP para backend
│   └── 📄 backend_adapter.py          # Adaptador backend/local
│
├── 📁 src/                            # 🔄 Código compartido (original)
│   ├── 📁 core/                       # Funcionalidades núcleo
│   │   ├── mcp_session_manager.py     # Gestor sesiones MCP
│   │   └── mcp_init.py                # Inicializador MCP
│   ├── 📁 models/                     # Modelos ML
│   │   └── sistema_multi_modelo.py    # Sistema multi-modelo
│   ├── 📁 services/                   # Servicios procesamiento
│   │   ├── auditoria_datos_llamadas.py
│   │   └── segmentacion_llamadas.py
│   └── 📁 ui/                         # Componentes UI originales
│       └── dashboard_comparacion.py
│
├── 📁 database/                       # Base de datos
│   └── 📁 migrations/                 # Migraciones SQL
│       ├── 001_create_analysis_sessions.sql
│       └── 002_audit_system.sql
│
├── 📁 scripts/                        # Scripts utilidades
│   ├── 📁 development/                # Scripts desarrollo
│   └── 📁 deployment/                 # 🆕 Scripts despliegue
│       └── deploy_backend.py          # Script despliegue backend
│
└── 📁 docs/                           # Documentación
    ├── README.md                      # Documentación principal
    └── CLAUDE.md                      # Guía para Claude Code
```

## 🚀 **Modos de Operación**

### **1. Modo Separado (Producción) 🌐**
```
Frontend Streamlit ──HTTP──> Backend FastAPI ──MCP──> Supabase
     ↓                           ↓
Streamlit Cloud           Streamlit Cloud/Heroku
```

### **2. Modo Híbrido (Desarrollo) 💻**
```
Frontend Streamlit ──API si disponible──> Backend Local
     ↓                                         ↓
Fallback Local ──────────MCP─────────> Supabase
```

### **3. Modo Legacy (Monolítico) ⚠️**
```
app.py ──MCP──> Supabase
  ↓
Streamlit Cloud
```

## 📋 **Opciones de Despliegue**

### **Opción A: Dual Streamlit Cloud**
- **Frontend**: `ceapsi-frontend.streamlit.app` → `frontend/app.py`
- **Backend**: `ceapsi-backend.streamlit.app` → `backend_streamlit.py`
- **Base de datos**: Supabase Cloud (MCP)

### **Opción B: Backend Externo**
- **Frontend**: `ceapsi-app.streamlit.app` → `frontend/app.py`
- **Backend**: Heroku/Railway → `backend/app/main.py`
- **Base de datos**: Supabase Cloud (MCP)

### **Opción C: Monolítico Legacy**
- **App**: `ceapsi-legacy.streamlit.app` → `app.py`
- **Base de datos**: Supabase Cloud (MCP)

## 🔧 **Configuración por Entorno**

### **Backend Secrets:**
```toml
# backend/.streamlit/secrets.toml
SUPABASE_URL = "https://lvouimzndppleeolbbhj.supabase.co"
SUPABASE_KEY = "tu-supabase-key"
SECRET_KEY = "jwt-secret-key"
ALLOWED_ORIGINS = ["https://ceapsi-frontend.streamlit.app"]
```

### **Frontend Secrets:**
```toml
# frontend/.streamlit/secrets.toml  
BACKEND_URL = "https://ceapsi-backend.streamlit.app"
SUPABASE_URL = "https://lvouimzndppleeolbbhj.supabase.co"
SUPABASE_KEY = "tu-supabase-key"
```

## 🔄 **Flujos de Datos**

### **Carga de Archivos:**
```
Usuario → Frontend → Backend API → Supabase MCP → Sesión Creada
```

### **Análisis de Datos:**
```
Frontend → Backend API → Procesamiento ML → Resultados → Supabase MCP
```

### **Visualización:**
```
Frontend → Backend API → Supabase MCP → Datos → Dashboard Streamlit
```

### **Fallback Local:**
```
Frontend → Procesamiento Local → Supabase MCP → Resultados
```

## 🎯 **Beneficios de la Separación**

### ✅ **Escalabilidad:**
- Backend independiente puede manejar múltiples clientes
- Posibilidad de load balancing
- Escalado horizontal del procesamiento ML

### ✅ **Mantenimiento:**
- Despliegues independientes sin downtime
- Actualizaciones de backend sin afectar UI
- Debugging más eficiente

### ✅ **Flexibilidad:**
- Frontend funciona con o sin backend (fallback)
- Posibilidad de múltiples frontends (web, mobile, CLI)
- API reutilizable para integraciones

### ✅ **Desarrollo:**
- Equipos pueden trabajar independientemente
- Testing más granular
- CI/CD pipeline separado

## 🚦 **Estados del Sistema**

### **🟢 Óptimo:**
- Backend API disponible
- Frontend conectado vía HTTP
- Procesamiento distribuido

### **🟡 Fallback:**
- Backend no disponible
- Frontend usa procesamiento local
- Funcionalidad completa mantenida

### **🔴 Error:**
- Frontend no puede cargar
- Supabase MCP no disponible
- Datos no accesibles

## 📊 **Métricas de Performance**

### **Modo Separado:**
- ⚡ Carga inicial: ~2-3s (solo UI)
- 🚀 Procesamiento: Paralelo en backend
- 💾 Memoria: Distribuida

### **Modo Local:**
- ⚡ Carga inicial: ~5-8s (todo el código)
- 🚀 Procesamiento: Local en frontend
- 💾 Memoria: Concentrada

## 🔄 **Migración Gradual**

1. **Fase 1**: Mantener `app.py` como legacy
2. **Fase 2**: Desplegar backend separado
3. **Fase 3**: Migrar frontend a modo API
4. **Fase 4**: Deprecar aplicación monolítica

¡Arquitectura moderna, escalable y mantenible! 🎉