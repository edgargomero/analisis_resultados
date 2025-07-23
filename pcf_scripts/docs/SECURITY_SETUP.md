# 🔒 CEAPSI - Configuración de Seguridad

**Sistema de autenticación EXCLUSIVAMENTE Supabase para máxima seguridad**

## 🚨 Características de Seguridad

### ✅ Implementado
- **Autenticación Supabase nativa**: Sistema robusto con PostgreSQL
- **Sin fallbacks inseguros**: Eliminado sistema YAML legacy
- **Creación manual de admin**: Sin usuarios automáticos
- **Gestión de roles**: admin/analista/viewer
- **Sesiones seguras**: Tokens JWT con expiración
- **Validación de email**: Confirmación obligatoria
- **Variables de entorno**: Credenciales separadas del código

### ❌ Eliminado por Seguridad
- Sistema YAML con contraseñas locales
- Usuarios por defecto automáticos
- Fallbacks de autenticación
- Credenciales hardcodeadas

## 🔧 Configuración Requerida

### 1. Configurar Supabase Dashboard

**Email Confirmation (Recomendado):**
1. Ir a **Authentication > Settings**
2. **IMPORTANTE**: Mantener "Enable email confirmations" ✅
3. Configurar SMTP para envío de emails
4. Personalizar templates de verificación

**Users Management:**
1. Ir a **Authentication > Users**
2. Crear usuario admin manualmente:
   - Email: admin@ceapsi.cl
   - Password: [CONTRASEÑA SEGURA]
   - User Metadata:
     ```json
     {
       "name": "Administrador CEAPSI",
       "role": "admin"
     }
     ```

### 2. Variables de Entorno (.env)

```bash
# OBLIGATORIO: Configuración Supabase
SUPABASE_URL=https://lvouimzndppleeolbbhj.supabase.co
SUPABASE_KEY=[SERVICE_ROLE_KEY]
SUPABASE_PROJECT_REF=lvouimzndppleeolbbhj

# Claude Code MCP
SUPABASE_ACCESS_TOKEN=[PERSONAL_ACCESS_TOKEN]

# Configuración aplicación
ENVIRONMENT=production
DEBUG=false
```

### 3. Dependencias de Seguridad

```bash
pip install supabase==2.8.0 python-dotenv==1.0.1
```

## 👤 Gestión de Usuarios

### Roles Disponibles
- **admin**: Acceso completo + gestión usuarios
- **analista**: Análisis, predicciones, dashboards  
- **viewer**: Solo visualización de resultados

### Proceso de Creación de Usuarios

1. **Admin crea usuarios** en Supabase Dashboard
2. **Usuario confirma email** (obligatorio)
3. **Login** con credenciales validadas
4. **Acceso basado en roles**

### Autoregistro (Opcional)
- Disponible en interfaz de login
- Requiere confirmación de email
- Rol por defecto: "viewer"
- Revisión admin recomendada

## 🛡️ Políticas de Seguridad

### Contraseñas
- **Mínimo**: 6 caracteres
- **Recomendado**: 12+ caracteres con símbolos
- **Gestión**: Supabase auth nativo
- **Reseteo**: Via email de recuperación

### Sesiones
- **Tokens JWT**: Firmados por Supabase
- **Expiración**: Configurable en Supabase
- **Logout**: Invalida tokens inmediatamente
- **Session State**: Limpiado en logout

### Red y Acceso
- **HTTPS**: Obligatorio en producción
- **CORS**: Configurado en Supabase
- **Rate Limiting**: Supabase por defecto
- **IP Whitelisting**: Disponible en plan Pro

## 🚀 Despliegue Seguro

### Streamlit Cloud
```toml
# .streamlit/secrets.toml
[supabase]
SUPABASE_URL = "https://lvouimzndppleeolbbhj.supabase.co"
SUPABASE_KEY = "[SERVICE_ROLE_KEY]"
SUPABASE_PROJECT_REF = "lvouimzndppleeolbbhj"
ENVIRONMENT = "production"
```

### Docker (Opcional)
```dockerfile
# Variables de entorno en container
ENV SUPABASE_URL=https://lvouimzndppleeolbbhj.supabase.co
ENV SUPABASE_KEY=[SERVICE_ROLE_KEY]
ENV ENVIRONMENT=production
```

## 📋 Checklist de Seguridad

### Pre-Despliegue
- [ ] Admin creado manualmente en Supabase
- [ ] Email confirmation habilitado
- [ ] Variables .env configuradas
- [ ] Credenciales no commiteadas
- [ ] Dependencias actualizadas
- [ ] HTTPS configurado

### Post-Despliegue
- [ ] Login admin funcional
- [ ] Confirmación email funcional
- [ ] Roles correctamente aplicados
- [ ] Logout invalida sesiones
- [ ] Logs sin credenciales expuestas
- [ ] Backup de configuración Supabase

## 🔍 Monitoreo y Auditoría

### Logs de Supabase
- **Authentication**: Intentos login, registros
- **API Usage**: Llamadas autenticadas
- **Errors**: Fallos de autenticación

### Logs Aplicación
```python
# Solo logs seguros - SIN credenciales
logger.info(f"Login exitoso: {user['email']}")
logger.warning(f"Intento login fallido: {email}")
logger.error("Error autenticación - revisar configuración")
```

## 🆘 Troubleshooting

### Error: "Sistema de seguridad no disponible"
- Verificar variables SUPABASE_URL y SUPABASE_KEY
- Verificar dependencias instaladas
- Revisar logs de conexión

### Error: "Email not confirmed"
- Usuario debe confirmar email antes del login
- Revisar configuración SMTP en Supabase
- Confirmar manualmente en dashboard si necesario

### Error: "Access token expired"
- Normal - renovación automática
- Revisar configuración de expiración
- Logout/login para forzar renovación

## 📞 Contacto Soporte

**Email**: soporte@ceapsi.cl  
**Administrador**: admin@ceapsi.cl

---

> ⚠️ **IMPORTANTE**: Este sistema maneja datos sensibles de call center.  
> Mantener siempre las mejores prácticas de seguridad.