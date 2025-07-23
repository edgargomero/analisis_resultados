# 🔗 Módulo de Estado de Integración con Reservo

## 📋 Descripción

Módulo completo para monitorear y gestionar la integración con la API de Reservo en tiempo real. Proporciona visibilidad completa del estado de conexión, uso y rendimiento de la API.

## ✨ Características Principales

### 🔍 **Monitoreo de Conexión**
- ✅ Estado de conexión en tiempo real
- ⏱️ Tiempo de respuesta de la API
- 🔗 Verificación de endpoints
- 📊 Métricas de conectividad

### 📊 **Estadísticas de Uso**
- 📈 Llamadas totales por período
- ✅ Tasa de éxito/error
- ⏱️ Tiempo promedio de respuesta
- 📁 Registros obtenidos
- 🎯 Endpoints más utilizados

### 🧪 **Pruebas de Endpoints**
- 🔍 Test de conectividad general
- 👥 Verificación de profesionales
- 📅 Prueba de obtención de citas
- ⚡ Medición de performance

### 📋 **Registro de Actividad**
- 📝 Llamadas recientes a la API
- 🕐 Historial temporal
- ❌ Registro de errores
- 📊 Análisis de tendencias

## 🚀 Instalación y Uso

### 1. **Configuración de Secrets**

En Streamlit Cloud, agregar en secrets:

```toml
[reservo]
API_KEY = "TU_API_KEY_DE_RESERVO"
API_URL = "https://reservo.cl/APIpublica/v2"
```

### 2. **Integración en la App**

El módulo ya está integrado en `app.py` como:
- 📱 **Página**: "🔗 Estado Reservo" en el menú principal
- 🔄 **Auto-refresh**: Actualización automática de estado
- 📊 **Dashboard**: Visualización completa de métricas

### 3. **Funcionalidades Disponibles**

#### **Vista Principal**
- Estado de conexión con indicadores visuales
- Métricas de performance en tiempo real
- Configuración y troubleshooting

#### **Pruebas de Endpoints**
- Test automático de todos los endpoints
- Resultados tabulados con métricas
- Identificación de problemas específicos

#### **Estadísticas Históricas**
- Gráficos de uso diario
- Distribución por endpoint
- Análisis de tendencias

#### **Actividad Reciente**
- Lista de llamadas más recientes
- Estado de cada llamada
- Detalles de errores

## 📊 Pantallas del Módulo

### **🏠 Pantalla Principal**
```
🔗 Estado de Integración con Reservo
=====================================

🔗 Estado de Conexión
┌─────────────┬──────────────┬─────────────┬──────────────┐
│ Estado      │ Tiempo Resp. │ Endpoint    │ Verificación │
├─────────────┼──────────────┼─────────────┼──────────────┤
│ 🟢 Conectado│ 245 ms      │ reservo.cl  │ 14:32:15     │
└─────────────┴──────────────┴─────────────┴──────────────┘

✅ Conexión establecida correctamente

🧪 Prueba de Endpoints
┌──────────────┬────────┬─────────────────┬────────┬──────┐
│ Endpoint     │ Estado │ Mensaje         │ Tiempo │ Datos│
├──────────────┼────────┼─────────────────┼────────┼──────┤
│ Conexión     │ ✅ OK  │ Conectado       │ 245ms  │ 0    │
│ Profesionales│ ✅ OK  │ 15 encontrados  │ 532ms  │ 15   │
└──────────────┴────────┴─────────────────┴────────┴──────┘
```

### **📊 Sección de Estadísticas**
```
📊 Estadísticas de Uso (últimos 30 días)
=======================================

┌─────────────┬─────────┬─────────┬──────────┐
│ Total       │ Exitosas│ Fallidas│ Tasa     │
├─────────────┼─────────┼─────────┼──────────┤
│ 1,247       │ 1,198   │ 49      │ 96.1%    │
└─────────────┴─────────┴─────────┴──────────┘

┌─────────────┬─────────────┬─────────────┬──────────────┐
│ Tiempo Prom.│ Registros   │ Última      │ Endpoints    │
├─────────────┼─────────────┼─────────────┼──────────────┤
│ 387 ms      │ 18,456      │ 23/07 14:30 │ 4            │
└─────────────┴─────────────┴─────────────┴──────────────┘

📈 Uso Diario
[Gráfico de líneas mostrando tendencia]

🎯 Endpoints Más Usados
[Gráfico de torta con distribución]
```

### **📋 Llamadas Recientes**
```
📋 Llamadas Recientes
==================

┌─────────────────┬───────────┬────────┬────────┬────────┬──────┐
│ Fecha/Hora      │ Endpoint  │ Método │ Status │ Tiempo │ Éxito│
├─────────────────┼───────────┼────────┼────────┼────────┼──────┤
│ 23/07/25 14:32  │ /citas    │ GET    │ 200    │ 456ms  │ ✅   │
│ 23/07/25 14:28  │ /prof     │ GET    │ 200    │ 234ms  │ ✅   │
│ 23/07/25 14:25  │ /citas    │ GET    │ 404    │ 123ms  │ ❌   │
└─────────────────┴───────────┴────────┴────────┴────────┴──────┘
```

## 🔧 Troubleshooting

### **🔴 Problemas Comunes**

#### **Estado: 🔴 Desconectado**
```
❌ API Key inválida o expirada
💡 Verifica la configuración en secrets
```

**Solución:**
1. Revisar API Key en secrets de Streamlit
2. Verificar que no haya espacios extra
3. Confirmar que la key no haya expirado

#### **⚠️ Tiempo de Respuesta Alto**
```
⚠️ Tiempo de respuesta: 3,245 ms
💡 Revisar conectividad de red
```

**Solución:**
1. Verificar conexión a internet
2. Revisar si el servidor de Reservo está lento
3. Considerar implementar timeout mayor

#### **❌ Errores Frecuentes**
```
❌ Tasa de éxito: 78.5%
💡 Revisar logs de errores específicos
```

**Solución:**
1. Revisar llamadas recientes para patrones
2. Verificar endpoints que fallan más
3. Ajustar parámetros de las llamadas

## 📈 Métricas de Performance

### **🎯 Objetivos Recomendados**
- **Tiempo de Respuesta**: < 2,000ms
- **Tasa de Éxito**: > 95%
- **Disponibilidad**: > 99%
- **Registros por Llamada**: > 0 (para endpoints de datos)

### **🚨 Alertas Automáticas**
El sistema registra automáticamente:
- Llamadas que tardan > 5 segundos
- Errores HTTP 4xx y 5xx
- Patrones de fallo repetitivos
- Tiempos de inactividad prolongados

## 🔄 Actualización y Mantenimiento

### **Refrescar Datos**
- Botón "🔄 Refrescar Estado" actualiza todo
- Las estadísticas se actualizan cada vez que se carga la página
- El estado de conexión se verifica en tiempo real

### **Configuración de Períodos**
- Selector para 7, 15, 30, 60, 90 días
- Las estadísticas se recalculan automáticamente
- Historial completo disponible via auditoría

### **Limpieza Automática**
- Los registros antiguos se limpian automáticamente
- Política de retención: 90 días por defecto
- Función `cleanup_old_audit_records()` disponible

## 📞 Información de Contacto

- **Sistema**: CEAPSI PCF
- **Módulo**: Estado de Integración Reservo
- **Versión**: 1.0
- **Última Actualización**: Enero 2025

---

### 💡 **Próximas Mejoras**
- 🔔 Notificaciones push para errores críticos
- 📊 Dashboard ejecutivo con KPIs
- 🤖 Predicción de fallos basada en patrones
- 📧 Reportes automáticos por email