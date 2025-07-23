# 🏗️ CEAPSI PCF - Arquitectura del Sistema

## 📋 Resumen Ejecutivo

CEAPSI PCF (Precision Call Forecast) es un sistema de predicción de llamadas para call center construido con arquitectura modular en Python, desplegado en Streamlit Cloud con base de datos Supabase.

## 🌐 Arquitectura General

```
┌─────────────────────────────────────────────────────────────┐
│                    STREAMLIT CLOUD                          │
├─────────────────────────────────────────────────────────────┤
│  Frontend (Streamlit UI)                                   │
│  ├── Dashboard Principal                                    │
│  ├── Monitor Reservo API                                    │
│  └── Interfaces de Usuario                                  │
├─────────────────────────────────────────────────────────────┤
│  Backend (Python Services)                                 │
│  ├── Modelos de IA                                         │
│  ├── Servicios de Datos                                    │
│  └── API Integrations                                      │
├─────────────────────────────────────────────────────────────┤
│  Data Layer                                                │
│  ├── Supabase Cloud (PostgreSQL)                          │
│  ├── Reservo API Integration                               │
│  └── File Storage & Processing                             │
└─────────────────────────────────────────────────────────────┘
```

## 📁 Estructura del Proyecto

```
pcf_scripts/
├── 🚀 run.py                           # Launcher principal
├── 📦 requirements.txt                 # Dependencias
├── 🔧 .env.example                     # Template de configuración
├── 📋 README.md                        # Documentación principal
│
├── 📁 src/                             # Código fuente principal
│   ├── 🏠 app.py                       # Aplicación Streamlit principal
│   │
│   ├── 🎨 ui/                          # Interfaces de usuario
│   │   ├── dashboard_comparacion.py    # Dashboard principal
│   │   └── ux_mejoras.py              # Mejoras UX/UI
│   │
│   ├── 🧠 models/                      # Modelos de IA y ML
│   │   ├── sistema_multi_modelo.py    # Sistema multi-modelo
│   │   └── optimizacion_hiperparametros.py # Optimización
│   │
│   ├── ⚙️ services/                    # Servicios de negocio
│   │   ├── auditoria_datos_llamadas.py # Auditoría de datos
│   │   ├── segmentacion_llamadas.py   # Segmentación
│   │   └── automatizacion_completa.py # Pipeline automático
│   │
│   ├── 🔗 api/                         # Integraciones API
│   │   └── modulo_estado_reservo.py   # Conexión Reservo
│   │
│   ├── 🔐 auth/                        # Autenticación y seguridad
│   │   ├── supabase_auth.py           # Auth Supabase
│   │   └── security_check.py          # Validaciones seguridad
│   │
│   ├── 🗂️ core/                        # Lógica central
│   │   └── preparacion_datos.py       # Procesamiento datos
│   │
│   ├── 🛠️ utils/                       # Utilidades
│   │   └── feriados_chilenos.py       # Gestión feriados
│   │
│   ├── ⚙️ config/                      # Configuración
│   │   ├── setup_supabase.py          # Setup Supabase
│   │   └── *.sql                      # Scripts SQL
│   │
│   └── 📊 audit/                       # Sistema de auditoría
│       ├── audit_manager.py           # Gestor auditoría
│       ├── setup_audit_*.py           # Setup auditoría
│       └── execute_audit_sql.py       # Ejecución SQL
│
├── 📁 assets/                          # Recursos estáticos
│   ├── data/                          # Datos de ejemplo
│   │   ├── ejemplo_datos_llamadas.csv
│   │   └── feriadoschile.csv
│   └── models/                        # Modelos entrenados
│
├── 📁 tests/                           # Testing
│   ├── unit/                          # Tests unitarios
│   ├── integration/                   # Tests integración
│   └── fixtures/                      # Datos de prueba
│
├── 📁 docs/                            # Documentación
│   ├── architecture/                  # Arquitectura
│   └── api/                           # Documentación API
│
├── 📁 logs/                            # Archivos de log
└── 📁 scripts/                         # Scripts utilidad
```

## 🔧 Componentes Principales

### 1. 🏠 Frontend (Streamlit UI)

**Ubicación**: `src/ui/`

- **Dashboard Principal**: Interfaz principal con navegación por pestañas
- **Monitor Reservo**: Estado en tiempo real de la conexión API
- **Componentes UX**: Mejoras de experiencia de usuario

**Características**:
- Interfaz completamente en español
- Dashboard responsivo con Plotly
- Carga de archivos drag & drop
- Monitor de estado API en tiempo real

### 2. 🧠 Modelos de IA/ML

**Ubicación**: `src/models/`

**Algoritmos Implementados**:
- **ARIMA**: Modelos autorregresivos
- **Prophet**: Predicción temporal de Facebook
- **Random Forest**: Ensemble de árboles
- **Gradient Boosting**: Boosting gradiente

**Performance Targets**:
- MAE < 10 llamadas/día
- RMSE < 15 llamadas/día  
- MAPE < 25%

### 3. ⚙️ Servicios de Negocio

**Ubicación**: `src/services/`

- **Auditoría de Datos**: Validación y análisis de calidad
- **Segmentación**: Clasificación automática entrantes/salientes
- **Automatización**: Pipeline completo con progreso visual

### 4. 🔗 Integraciones API

**Ubicación**: `src/api/`

**Reservo API Integration**:
- Sincronización automática cada 15 minutos
- Datos de llamadas en tiempo real
- Estado de agentes y métricas
- Manejo de errores y reconexión automática

### 5. 🔐 Seguridad y Autenticación

**Ubicación**: `src/auth/`

- **Supabase Auth**: Autenticación completa
- **Security Checks**: Validaciones de seguridad
- **Variables de Entorno**: Configuración via Streamlit Secrets

### 6. 🗂️ Procesamiento de Datos

**Ubicación**: `src/core/`

**Capacidades**:
- Carga CSV, Excel, JSON
- Detección automática de encoding
- Validación de columnas requeridas
- Mapeo inteligente de datos

### 7. 📊 Sistema de Auditoría

**Ubicación**: `src/audit/`

- Monitoreo de integridad de datos
- Logs de actividad del sistema
- Métricas de performance
- Alertas automáticas

## 🗄️ Base de Datos (Supabase Cloud)

### Esquema Principal

```sql
-- Tabla principal de llamadas
calls_data (
    id UUID PRIMARY KEY,
    fecha TIMESTAMP,
    telefono VARCHAR,
    sentido VARCHAR,
    atendida BOOLEAN,
    created_at TIMESTAMP,
    metadata JSONB
)

-- Auditoría del sistema
audit_log (
    id UUID PRIMARY KEY,
    evento VARCHAR,
    usuario VARCHAR,
    timestamp TIMESTAMP,
    detalles JSONB
)

-- Configuración del sistema
system_config (
    key VARCHAR PRIMARY KEY,
    value JSONB,
    updated_at TIMESTAMP
)
```

## 🔌 APIs y Integraciones

### Reservo API
- **Endpoint**: `https://api.reservo.cl`
- **Autenticación**: API Key + Client ID
- **Frecuencia**: Sync cada 15 minutos
- **Datos**: Llamadas, agentes, métricas

### Supabase API
- **Endpoint**: Auto-generado por Supabase
- **Autenticación**: Service Role Key
- **Funciones**: CRUD, Real-time, Auth

## 🚀 Flujo de Despliegue

### Streamlit Cloud Deployment

1. **Build Phase**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configuration**: 
   - Variables en `Streamlit Secrets`
   - Configuración automática de Supabase

3. **Runtime**:
   ```bash
   streamlit run src/app.py
   ```

### Variables de Entorno (Streamlit Secrets)

```toml
# Supabase Configuration
SUPABASE_URL = "https://project.supabase.co"
SUPABASE_KEY = "service-role-key"
SUPABASE_ANON_KEY = "anon-key"

# Reservo API
RESERVO_API_URL = "https://api.reservo.cl"
RESERVO_API_KEY = "api-key"
RESERVO_CLIENT_ID = "client-id"

# App Settings
LOG_LEVEL = "INFO"
```

## 📊 Monitoreo y Observabilidad

### Logs del Sistema
- **Ubicación**: `logs/`
- **Formato**: JSON estructurado
- **Niveles**: DEBUG, INFO, WARNING, ERROR, CRITICAL

### Métricas Clave
- Latencia API Reservo
- Precisión de modelos ML
- Tasa de éxito de predicciones
- Uso de recursos del sistema

### Alertas Automáticas
- Conexión API perdida > 30 min
- Precisión modelo < 75%
- Errores críticos en pipeline

## 🔄 Pipeline de Datos

```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│   Reservo   │───▶│  Validation  │───▶│  Supabase   │
│     API     │    │  & Cleaning  │    │  Database   │
└─────────────┘    └──────────────┘    └─────────────┘
                          │
                          ▼
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│  Dashboard  │◄───│   AI Models  │◄───│ Data Prep   │
│   Display   │    │  Prediction  │    │ Processing  │
└─────────────┘    └──────────────┘    └─────────────┘
```

## 🛡️ Seguridad

### Principios de Seguridad
- **Zero Trust**: Validación en cada capa
- **Least Privilege**: Permisos mínimos necesarios
- **Data Encryption**: Cifrado en tránsito y reposo
- **Audit Trail**: Log completo de actividades

### Implementación
- API Keys vía Streamlit Secrets
- Validación de entrada de datos
- Sanitización de SQL queries
- Rate limiting en API calls

## 📈 Escalabilidad

### Horizontal Scaling
- Stateless application design
- Database connection pooling
- Async processing capabilities

### Performance Optimization
- Model caching estratégico
- Lazy loading de componentes
- Batch processing para datos grandes
- Optimización de queries SQL

## 🔮 Roadmap Técnico

### Próximas Mejoras
1. **Microservicios**: Separación de servicios
2. **Containerización**: Docker deployment
3. **CI/CD Pipeline**: Automatización completa
4. **Real-time Analytics**: Streaming data
5. **Mobile Dashboard**: Aplicación móvil

---

**Documentación actualizada**: 2025-01-23  
**Versión del sistema**: 1.0.0  
**Arquitecto**: CEAPSI Team