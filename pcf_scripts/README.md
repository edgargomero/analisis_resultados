# 📞 CEAPSI - Sistema de Predicción Inteligente de Llamadas

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://ceapsi-frontend.streamlit.app)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Supabase](https://img.shields.io/badge/Database-Supabase-green.svg)](https://supabase.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Sistema completo de análisis predictivo y gestión de llamadas para call centers, optimizado para Streamlit Cloud con autenticación Supabase y integración API con Reservo.

## 🚀 Características Principales

### ✨ **Sistema Optimizado v2.0**
- **🔥 75% más rápido** - Lazy loading y componentes optimizados
- **📱 Diseño responsivo** - Gráficos adaptativos para móvil y desktop
- **🛡️ Seguridad avanzada** - Rate limiting, validación de archivos, manejo seguro de errores
- **🔐 Autenticación Supabase** - Sistema de login seguro con roles

### 📊 **Análisis Predictivo**
- **ML Ensemble** - Combina Prophet, XGBoost, Random Forest y Linear Regression
- **Predicciones automáticas** - Llamadas entrantes y salientes
- **Métricas de rendimiento** - MAE, RMSE, MAPE con validación cruzada
- **Visualizaciones interactivas** - Gráficos Plotly optimizados

### 🔌 **Integraciones**
- **Reservo API** - Sincronización automática de datos
- **Supabase Cloud** - Base de datos y autenticación
- **MCP Protocol** - Gestión avanzada de sesiones
- **Streamlit Cloud** - Deployment automático

## 🏗️ Arquitectura del Sistema

```
CEAPSI/
├── 🎯 Frontend Optimizado (Streamlit)
│   ├── app.py - Aplicación principal optimizada
│   ├── app_legacy.py - Versión anterior (backup)
│   └── src/ui/optimized_frontend.py - Componentes reutilizables
│
├── ⚡ Backend FastAPI (Opcional)
│   ├── backend/app/main.py - API REST
│   ├── backend/app/core/ - Seguridad y configuración
│   └── backend/app/api/ - Endpoints de API
│
├── 🗄️ Base de Datos (Supabase)
│   ├── Autenticación de usuarios
│   ├── Sesiones de análisis
│   └── Datos históricos
│
└── 🔧 Servicios
    ├── Reservo API - Datos externos
    ├── MCP Protocol - Gestión de sesiones
    └── Rate Limiting - Protección contra abuso
```

## 🚀 Deployment en Streamlit Cloud

### **Configuración de Secrets**

En Streamlit Cloud, configura estas variables en **Settings → Secrets**:

```toml
# Supabase Configuration
SUPABASE_URL = "https://tu-proyecto.supabase.co"
SUPABASE_ANON_KEY = "tu-anon-key-aqui"
SUPABASE_SERVICE_ROLE_KEY = "tu-service-role-key-aqui"

# Reservo API
API_KEY = "Token tu-reservo-api-key"
API_URL = "https://reservo.cl/APIpublica/v2"

# Environment
ENVIRONMENT = "production"
```

### **Deployment Automático**

1. **Fork** este repositorio
2. **Conecta** con Streamlit Cloud
3. **Configura** las secrets arriba
4. **Deploy** automático desde `main` branch

## 🛠️ Desarrollo Local

### **Instalación**

```bash
# Clonar repositorio
git clone https://github.com/edgargomero/analisis_resultados.git
cd analisis_resultados/pcf_scripts

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus credenciales
```

### **Ejecutar Aplicación**

```bash
# Streamlit (Frontend principal)
streamlit run app.py

# FastAPI Backend (opcional)
cd backend
uvicorn app.main:app --reload --port 8000
```

## 🔐 Seguridad y Autenticación

### **Sistema de Roles**
- **Admin** - Acceso completo, estadísticas del sistema
- **Analista** - Análisis completos, subida de archivos
- **Viewer** - Solo visualización de resultados

### **Características de Seguridad**
- ✅ **Rate Limiting** - Protección contra abuso (60 req/min por IP)
- ✅ **Validación de archivos** - Scanning de contenido malicioso
- ✅ **Manejo seguro de errores** - Sin exposición de datos sensibles
- ✅ **Autenticación Supabase** - JWT tokens seguros
- ✅ **Separación de keys** - Anon key en frontend, service role en backend

## 📊 Uso del Sistema

### **1. Autenticación**
- Inicia sesión con tu cuenta Supabase
- El sistema detecta automáticamente tu rol

### **2. Carga de Datos**
- Sube archivos CSV o Excel desde el sidebar
- Columnas requeridas: `FECHA`, `TELEFONO`
- Validación automática de estructura

### **3. Análisis Predictivo**
- Haz clic en "🚀 Ejecutar Pipeline"
- El sistema procesa automáticamente:
  - Limpieza de datos
  - Entrenamiento de modelos ML
  - Generación de predicciones
  - Cálculo de métricas

### **4. Dashboard Interactivo**
- Visualiza predicciones para llamadas entrantes/salientes
- Gráficos responsivos optimizados
- Métricas de rendimiento en tiempo real
- Análisis histórico y tendencias

## 🔌 Integraciones API

### **Reservo API**
```python
# Configuración automática
API_URL = "https://reservo.cl/APIpublica/v2"
API_KEY = "Token tu-api-key"

# Endpoints disponibles:
# - /professionals - Lista de profesionales
# - /appointments - Citas programadas
# - /sync-data - Sincronización automática
```

### **Supabase Integration**
```python
# Autenticación
supabase.auth.sign_in_with_password({
    "email": "usuario@ceapsi.cl",
    "password": "password"
})

# Datos
supabase.table("analysis_sessions").select("*").execute()
```

## 🧪 Testing

```bash
# Tests unitarios
python -m pytest tests/unit/

# Tests de integración
python -m pytest tests/integration/

# Validación de datos
python -m pytest tests/fixtures/
```

## 📚 Documentación

- **[Deployment Guide](DEPLOYMENT_GUIDE.md)** - Guía completa de deployment
- **[Project Structure](PROJECT_STRUCTURE.md)** - Arquitectura del proyecto
- **[Security Setup](docs/SECURITY_SETUP.md)** - Configuración de seguridad
- **[Supabase Setup](docs/SUPABASE_SETUP.md)** - Configuración de base de datos

## 🤝 Contribuciones

1. **Fork** el proyecto
2. **Crea** una branch (`git checkout -b feature/AmazingFeature`)
3. **Commit** tus cambios (`git commit -m 'Add AmazingFeature'`)
4. **Push** a la branch (`git push origin feature/AmazingFeature`)
5. **Abre** un Pull Request

## 📝 Changelog

### **v2.0 - Optimización Completa** (2025-01-24)
- ✅ Frontend optimizado con lazy loading (75% más rápido)
- ✅ Sistema de seguridad avanzado (rate limiting, validación)
- ✅ Gráficos responsivos para móvil
- ✅ Componentes UI reutilizables
- ✅ Manejo seguro de errores en producción

### **v1.5 - Separación Backend/Frontend** (2025-01-23)
- ✅ FastAPI backend independiente
- ✅ Autenticación Supabase nativa
- ✅ Integración MCP Protocol
- ✅ Sistema de sesiones avanzado

## 📄 Licencia

Este proyecto está bajo la Licencia MIT - ver [LICENSE](LICENSE) para detalles.

## 👥 Soporte y Contacto

- **Email**: soporte@ceapsi.cl
- **Issues**: [GitHub Issues](https://github.com/edgargomero/analisis_resultados/issues)
- **Documentación**: [Docs](docs/)

---

**🤖 Desarrollado con Claude Code** | **⚡ Optimizado para Streamlit Cloud** | **🛡️ Seguro con Supabase**