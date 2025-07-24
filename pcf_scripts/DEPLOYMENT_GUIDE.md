# 🚀 CEAPSI - Guía de Despliegue Backend/Frontend

## 📋 **Arquitectura Separada**

El proyecto CEAPSI ahora está separado en dos componentes principales:

```
CEAPSI/
├── 🖥️ Backend (FastAPI)          # Procesamiento y API
│   └── URL: ceapsi-backend.streamlit.app
├── 🌐 Frontend (Streamlit)       # Interfaz de usuario  
│   └── URL: ceapsi-app.streamlit.app
└── 🗄️ Database (Supabase)        # Almacenamiento
    └── MCP Connection
```

## 🎯 **Opciones de Despliegue**

### **Opción 1: Despliegue Dual en Streamlit Cloud (Recomendado)**

#### **Backend API:**
1. **Crear app separada**: `ceapsi-backend`
2. **Archivo principal**: `backend_streamlit.py` 
3. **Puerto**: 8000 (FastAPI dentro de Streamlit)

#### **Frontend App:**
1. **App principal**: `ceapsi-frontend`
2. **Archivo principal**: `frontend/app.py`
3. **Conexión**: API calls al backend

### **Opción 2: Backend Externo + Frontend Streamlit**

#### **Backend en Heroku/Railway:**
1. **Plataforma**: Heroku, Railway, o DigitalOcean
2. **Exposición**: API REST pública
3. **URL**: `https://ceapsi-api.herokuapp.com`

#### **Frontend en Streamlit Cloud:**
1. **Conexión**: Via BACKEND_URL en secrets
2. **Fallback**: Procesamiento local si backend no disponible

## ⚙️ **Configuración de Variables**

### **Backend Secrets (.env o Streamlit Secrets):**
```toml
[secrets]
# Supabase Configuration
SUPABASE_URL = "https://your-project.supabase.co"
SUPABASE_KEY = "your-service-role-key-here"
SUPABASE_PROJECT_REF = "your-project-ref"
SUPABASE_ACCESS_TOKEN = "your-access-token-here"

# Reservo API Configuration
API_KEY = "Token your-reservo-api-key-here"
API_URL = "https://reservo.cl/APIpublica/v2"

# App Configuration
ENVIRONMENT = "production"
DEBUG = "false"
SECRET_KEY = "your-jwt-secret-key-here"
```

### **Frontend Secrets:**
```toml
[secrets]
# Backend Connection
BACKEND_URL = "https://your-backend-app.streamlit.app"

# Supabase Configuration (IMPORTANT: Use ANON KEY, not service role)
SUPABASE_URL = "https://your-project.supabase.co"
SUPABASE_KEY = "your-anon-key-here"
SUPABASE_PROJECT_REF = "your-project-ref"

# App Configuration
ENVIRONMENT = "production"
DEBUG = "false"
```

### **🚨 IMPORTANTE - Configuración de Claves**
- **Backend**: Usa `SUPABASE_SERVICE_ROLE_KEY` para operaciones administrativas
- **Frontend**: Usa `SUPABASE_ANON_KEY` para autenticación de usuarios
- **NUNCA** expongas service role keys en el frontend
- **ROTAR** todas las claves antes del deployment si han sido comprometidas

## 🔧 **Scripts de Despliegue**

### **1. Preparar Backend:**
```bash
python scripts/deployment/deploy_backend.py
```

### **2. Configurar Frontend:**
```bash
# El frontend automáticamente detecta si usar API o modo local
# Basado en disponibilidad del BACKEND_URL
```

## 🏗️ **Estructura de Archivos**

### **Backend (FastAPI):**
```
backend/
├── app/
│   ├── main.py              # FastAPI app principal
│   ├── api/routers/         # Endpoints REST
│   ├── core/               # Configuración y auth
│   ├── models/             # Pydantic schemas
│   └── services/           # Lógica de negocio
├── requirements.txt        # Dependencias backend
└── backend_streamlit.py    # Wrapper para Streamlit Cloud
```

### **Frontend (Streamlit):**
```
frontend/
├── app.py                  # App Streamlit principal
├── api_client.py          # Cliente para comunicación API
├── backend_adapter.py     # Adaptador backend/local
└── requirements.txt       # Dependencias frontend
```

## 🚦 **Flujo de Comunicación**

### **Modo API (Producción):**
```
Usuario → Frontend Streamlit → Backend API → Supabase → Resultados
```

### **Modo Local (Fallback):**
```
Usuario → Frontend Streamlit → Procesamiento Local → Supabase → Resultados
```

## 📊 **Beneficios de la Separación**

### ✅ **Escalabilidad:**
- Backend independiente puede manejar múltiples frontends
- Posibilidad de balanceador de carga
- Escalado horizontal del procesamiento

### ✅ **Mantenimiento:**
- Despliegues independientes
- Actualizaciones sin afectar interfaz
- Debugging más fácil

### ✅ **Flexibilidad:**
- Frontend funciona con o sin backend
- Múltiples interfaces posibles (web, mobile, API)
- Fallback automático a procesamiento local

## 🔄 **Proceso de Despliegue**

### **Paso 1: Preparar Repositorio**
```bash
git add .
git commit -m "Configuración completa Backend/Frontend con Supabase Auth + Reservo API"
git push origin main
```

### **Paso 2: Desplegar Backend API**
1. **Crear nueva app en Streamlit Cloud**:
   - App name: `ceapsi-backend`
   - Repository: Tu repositorio GitHub
   - Branch: `main`
   - Main file path: `backend_streamlit.py`

2. **Configurar Secrets del Backend**:
   Copiar y pegar las variables del Backend Secrets mostradas arriba

3. **Verificar deployment**:
   - URL resultante: `https://ceapsi-backend.streamlit.app`
   - Verificar que `/health` responda correctamente
   - Probar endpoint `/docs` para documentación API

### **Paso 3: Desplegar Frontend App**
1. **Crear/Actualizar app frontend**:
   - App name: `ceapsi-app` o `ceapsi-frontend`
   - Repository: Tu repositorio GitHub
   - Branch: `main`
   - Main file path: `frontend/app.py`

2. **Configurar Secrets del Frontend**:
   Copiar y pegar las variables del Frontend Secrets, **asegurando**:
   ```toml
   BACKEND_URL = "https://ceapsi-backend.streamlit.app"
   ```

3. **Verificar integración**:
   - Login con Supabase Auth funcional
   - Sidebar muestra: "🌐 Modo API Backend"
   - Conexión con Reservo API a través del backend

### **Paso 4: Testing End-to-End**
1. **Autenticación**:
   - Login/register con Supabase Auth
   - Verificar roles (admin, analista, viewer)
   - Session persistence entre reloads

2. **Comunicación Frontend-Backend**:
   - Upload de archivos funcional
   - API calls con token Bearer
   - Fallback automático si backend no disponible

3. **Integración Reservo**:
   - Estado de conexión visible
   - Test de endpoints desde interfaz
   - Estadísticas y monitoreo

### **Paso 5: Monitoreo y Validación**
1. **Health Checks**:
   - Backend: `https://ceapsi-backend.streamlit.app/health`
   - Frontend: Sidebar connection status

2. **Logs y Debugging**:
   - Streamlit Cloud logs para errores
   - Browser DevTools para frontend issues
   - API response debugging en Swagger UI

## 🛠️ **Desarrollo Local**

### **Backend:**
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### **Frontend:**
```bash
# Configurar BACKEND_URL=http://localhost:8000 en .env
streamlit run frontend/app.py
```

## 📝 **Notas Importantes**

### **🔒 Autenticación y Seguridad**
1. **Supabase Auth**: Sistema nativo de autenticación con tokens JWT
2. **CORS**: Backend configurado para Streamlit Cloud específicamente
3. **Role-based Access**: Administradores, analistas y viewers con permisos diferenciados
4. **Token Persistence**: Sesiones se mantienen entre reloads del frontend

### **🔄 Integración y Fallback**
5. **API Communication**: Frontend detecta automáticamente backend availability
6. **Graceful Degradation**: Procesamiento local si backend no disponible
7. **Reservo API**: Centralizada en backend para mayor seguridad
8. **MCP Database**: Ambos componentes comparten Supabase con Model Context Protocol

### **📊 Monitoreo y Mantenimiento**
9. **Health Endpoints**: Monitoreo automatizado de servicios
10. **Comprehensive Logging**: Logs separados por componente
11. **Error Handling**: Manejo robusto de errores con feedback al usuario
12. **Performance**: Timeout y retry logic configurados

### **🚀 Ventajas de la Arquitectura**
- **Escalabilidad**: Backend independiente maneja múltiples sesiones
- **Flexibilidad**: Deployment independiente de componentes
- **Mantenibilidad**: Updates sin downtime
- **Seguridad**: API keys protegidas en backend
- **User Experience**: Fallback transparente garantiza disponibilidad

¡Sistema empresarial listo para producción con alta disponibilidad y seguridad! 🎉

---

## 🆘 **Troubleshooting**

### **Backend no responde:**
1. Verificar logs en Streamlit Cloud dashboard
2. Comprobar variables de entorno/secrets
3. Revisar CORS configuration
4. Testear health endpoint directamente

### **Autenticación falla:**
1. Verificar Supabase credentials
2. Comprobar token validity
3. Revisar user roles en Supabase dashboard
4. Validar session state en frontend

### **Reservo API errors:**
1. Verificar API_KEY en backend secrets
2. Comprobar connectivity desde health endpoint
3. Revisar rate limits de Reservo
4. Validar endpoint URLs

**Soporte**: Revisar logs detallados en ambos componentes y Supabase dashboard para debugging avanzado.