# Configuración Supabase para CEAPSI

Esta guía te ayudará a integrar Streamlit con Supabase para autenticación robusta en el sistema CEAPSI.

## 🚀 Configuración Inicial

### 1. Crear Proyecto Supabase

1. Ve a [supabase.com](https://supabase.com) y crea una cuenta
2. Crea un nuevo proyecto
3. Espera a que se complete la configuración

### 2. Obtener Credenciales

En tu dashboard de Supabase:
1. Ve a **Settings > API**
2. Copia:
   - **Project URL** (ej: https://abc123.supabase.co)
   - **Anon key** (ej: eyJ0eXAiOiJKV1QiLCJhbGci...)
   - **Service role key** (para operaciones admin)

### 3. Configurar Variables de Entorno

1. Copia el archivo de ejemplo:
   ```bash
   cp .env.example .env
   ```

2. Edita el archivo `.env` con tus credenciales:
   ```bash
   SUPABASE_URL=https://tu-proyecto.supabase.co
   SUPABASE_KEY=tu-anon-key-aqui
   SUPABASE_SERVICE_ROLE_KEY=tu-service-role-key-aqui
   ```

### 4. Instalar Dependencias

```bash
pip install supabase python-dotenv bcrypt
```

O usar requirements.txt:
```bash
pip install -r requirements.txt
```

## 🏗️ Configuración de Base de Datos

### Opción 1: Automática (Recomendada)

Ejecuta el script de configuración:
```bash
python setup_supabase.py
```

Este script:
- ✅ Verifica la conexión con Supabase
- 📊 Crea la tabla `ceapsi_users`  
- 👥 Crea usuarios por defecto
- 🧪 Prueba la autenticación

### Opción 2: Manual

1. **Crear Tabla de Usuarios** en el SQL Editor de Supabase:

```sql
CREATE TABLE ceapsi_users (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    role VARCHAR(20) DEFAULT 'viewer',
    password_hash TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP,
    login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP
);

-- Crear índices
CREATE INDEX idx_ceapsi_users_username ON ceapsi_users(username);
CREATE INDEX idx_ceapsi_users_email ON ceapsi_users(email);
```

2. **Crear Usuarios** ejecutando `setup_supabase.py` o usando Python:

```python
from supabase_auth import SupabaseAuthManager

auth = SupabaseAuthManager()
auth.create_user(
    username='admin',
    email='admin@ceapsi.cl', 
    name='Administrador',
    password='admin123',
    role='admin'
)
```

## 👥 Usuarios Por Defecto

El sistema crea estos usuarios automáticamente:

| Usuario | Contraseña | Rol | Descripción |
|---------|------------|-----|-------------|
| `admin` | `admin123` | admin | Administrador completo |
| `analista1` | `analista123` | analista | María González |
| `analista2` | `analista123` | analista | Carlos Rodríguez |
| `viewer` | `viewer123` | viewer | Solo visualización |

> ⚠️ **Importante**: Cambiar contraseñas en producción

## 🔗 Configurar MCP para Claude Code

Para usar las herramientas de Supabase en Claude Code:

1. **Obtener Personal Access Token**:
   - Ve a Supabase Dashboard > Account > Access tokens
   - Crea un nuevo token

2. **Actualizar .mcp.json**:
   ```json
   {
     "mcpServers": {
       "supabase": {
         "env": {
           "SUPABASE_ACCESS_TOKEN": "tu-personal-access-token",
           "SUPABASE_PROJECT_REF": "tu-project-ref"
         }
       }
     }
   }
   ```

3. **Reiniciar Claude Code** para aplicar cambios

## 🚀 Ejecutar la Aplicación

```bash
streamlit run app.py
```

El sistema detectará automáticamente si Supabase está configurado y lo usará como método de autenticación principal.

## 🔐 Características de Seguridad

### Protección de Contraseñas
- Hashing bcrypt con salt aleatorio
- Nunca se almacenan contraseñas en texto plano

### Bloqueo de Cuentas
- Máximo 5 intentos de login fallidos
- Bloqueo automático por 15 minutos
- Reset automático tras login exitoso

### Gestión de Sesiones
- Tokens seguros en session state
- Logout automático por inactividad
- Validación de permisos por rol

### Roles de Usuario
- **Admin**: Acceso completo, gestión de usuarios
- **Analista**: Análisis, predicciones, dashboards
- **Viewer**: Solo visualización de resultados

## 🛠️ Troubleshooting

### Error: "Sistema de autenticación no disponible"
- Verificar que `.env` existe con credenciales correctas
- Verificar que las dependencias están instaladas
- Verificar conectividad con Supabase

### Error: "No se pudo conectar con Supabase"
- Verificar SUPABASE_URL y SUPABASE_KEY en `.env`
- Verificar que el proyecto Supabase está activo
- Verificar permisos de la API key

### Error en creación de tabla
- Usar Service Role Key en lugar de Anon Key
- Verificar permisos en Supabase RLS (Row Level Security)
- Ejecutar SQL manualmente en Supabase

### Login no funciona
- Verificar que la tabla `ceapsi_users` existe
- Verificar que los usuarios fueron creados
- Revisar logs para errores específicos

## 📚 Recursos Adicionales

- [Documentación Supabase](https://supabase.com/docs)
- [Streamlit + Supabase Guide](https://docs.streamlit.io/develop/tutorials/databases/supabase)
- [MCP Supabase Server](https://github.com/supabase-community/supabase-mcp)

## 🔄 Migración desde Sistema YAML

El sistema mantiene compatibilidad con el sistema YAML anterior. Si Supabase no está disponible, automáticamente usará el sistema `config.yaml`.

Para migrar usuarios:
1. Configurar Supabase siguiendo esta guía
2. Los usuarios del sistema YAML seguirán funcionando
3. Gradualmente crear usuarios en Supabase
4. Opcional: deshabilitar sistema YAML eliminando `config.yaml`