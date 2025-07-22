# 📞 CEAPSI - Sistema PCF (Precision Call Forecast)

Sistema completo de predicción de llamadas para call center usando inteligencia artificial y análisis avanzado de datos.

📁 **¡Sube tu propio archivo de datos de llamadas y comienza el análisis inmediatamente!**

## 🎯 Características Principales

- **🤖 Múltiples Modelos de IA**: ARIMA, Prophet, Random Forest, Gradient Boosting
- **📊 Dashboard Simplificado**: Interfaz intuitiva siguiendo mejores prácticas UX/UI
- **🇨🇱 Análisis de Feriados**: Integración completa de feriados chilenos 2023-2025
- **📈 Análisis Comparativo**: Comparación por hora, día de semana y patrones estacionales
- **🔍 Auditoría de Datos**: Análisis automático de calidad y patrones
- **🔀 Segmentación Inteligente**: Clasificación automática de llamadas entrantes/salientes
- **🚨 Sistema de Alertas**: Detección proactiva de picos de demanda
- **⚙️ Pipeline con Progreso**: Seguimiento visual del estado de ejecución
- **🌐 Interfaz en Español**: Totalmente localizada con semanas iniciando en lunes

## 🚀 Instalación y Configuración

### Prerrequisitos

- Python 3.8 o superior
- pip (gestor de paquetes de Python)

### Instalación

1. **Clonar o descargar el proyecto**
   ```bash
   # Si tienes git instalado
   git clone <repository-url>
   cd pcf_scripts
   ```

2. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   ```

3. **¡Listo para usar!**
   
   La aplicación permite subir archivos manualmente. No necesitas configurar rutas específicas.
   
   **Formatos soportados:**
   - CSV (con separador punto y coma)
   - Excel (.xlsx, .xls)
   
   **Archivo de ejemplo incluido:** `ejemplo_datos_llamadas.csv`

### Ejecución

**Modo Dashboard Interactivo (Recomendado)**
```bash
streamlit run app.py
```

**Módulos Individuales**
```bash
# Auditoría de datos
python auditoria_datos_llamadas.py

# Segmentación de llamadas  
python segmentacion_llamadas.py

# Sistema multi-modelo
python sistema_multi_modelo.py

# Automatización completa
python automatizacion_completa.py
```

## 📊 Estructura del Proyecto

```
pcf_scripts/
├── 📱 app.py                          # Aplicación principal Streamlit
├── 📊 dashboard_comparacion.py        # Dashboard simplificado UX/UI
├── 🇨🇱 feriados_chilenos.py           # Sistema de feriados chilenos integrado
├── 🔍 auditoria_datos_llamadas.py     # Auditoría de calidad de datos
├── 📊 preparacion_datos.py            # Módulo de preparación de datos
├── 🔀 segmentacion_llamadas.py        # Segmentación de llamadas
├── 🤖 sistema_multi_modelo.py         # Sistema multi-modelo
├── ⚙️ automatizacion_completa.py      # Pipeline automatizado con progreso
├── 🎨 ux_mejoras.py                   # Mejoras de experiencia de usuario
├── 📋 requirements.txt                # Dependencias
├── 📖 README.md                       # Esta documentación
├── 📝 ejemplo_datos_llamadas.csv      # Datos de ejemplo
├── 🎄 feriadoschile.csv               # Base de datos de feriados
└── .streamlit/
    └── config.toml                    # Configuración de Streamlit
```

## 📁 Formato de Datos Esperado

### Columnas Requeridas

| Columna | Descripción | Ejemplo |
|---------|-------------|----------|
| **FECHA** | Fecha y hora de la llamada | 02-01-2023 08:08:07 |
| **TELEFONO** | Número de teléfono | +56912345678 |
| **SENTIDO** | Tipo de llamada | 'in' (entrante) o 'out' (saliente) |
| **ATENDIDA** | Estado de atención | 'Si' o 'No' |

### Formato del Archivo

- **Separador**: Punto y coma (;)
- **Encoding**: UTF-8, Latin-1, o CP1252
- **Formato de fecha**: DD-MM-YYYY HH:MM:SS
- **Extensiones**: .csv, .xlsx, .xls

### Ejemplo de Archivo CSV

```csv
FECHA;TELEFONO;SENTIDO;ATENDIDA;STATUS
02-01-2023 08:08:07;+56912345678;in;Si;ANSWERED
02-01-2023 08:15:23;+56987654321;out;No;NO_ANSWER
02-01-2023 08:22:45;+56923456789;in;Si;ANSWERED
```

📎 **Descarga el archivo `ejemplo_datos_llamadas.csv` desde la aplicación para ver el formato completo.**

## 🎮 Guía de Uso

### 1. 🏠 Página de Inicio
- Resumen del sistema y métricas principales
- Enlaces rápidos a los módulos
- Estado actual del sistema
- **📁 Sección de carga de archivos en el sidebar**

### 2. 📊 Dashboard Simplificado (Nuevas Funcionalidades)
- **📈 Análisis Comparativo**: Pestañas organizadas para mejor navegación
- **⏰ Análisis por Horas**: Patrones detallados por hora del día
- **📅 Análisis Semanal**: Comparación por días de la semana (Lunes a Domingo)
- **🇨🇱 Impacto de Feriados**: Análisis específico de feriados chilenos
- **📊 Métricas Clave**: KPIs principales en formato visual intuitivo
- **🌐 Interfaz en Español**: Gráficos, etiquetas y navegación completamente en español

### 3. 🔍 Auditoría de Datos
- Análisis automático de calidad de datos
- Detección de patrones temporales
- Identificación de outliers y anomalías
- Generación de reportes de diagnóstico

### 4. 🔀 Segmentación de Llamadas
- Clasificación automática por tipo (entrante/saliente)
- Análisis de patrones horarios
- Validación de confianza de clasificación
- Generación de datasets separados

### 5. 🤖 Sistema Multi-Modelo
- Entrenamiento de múltiples algoritmos
- Ensemble automático con pesos optimizados
- Validación cruzada temporal
- Generación de predicciones para 28 días

### 6. 🇨🇱 Análisis de Feriados Chilenos (NUEVO)
- **Base de datos integrada**: 53 feriados chilenos (2023-2025)
- **Análisis de impacto**: Comparación de llamadas en días feriados vs normales
- **Categorización**: Feriados religiosos, cívicos, electorales y culturales
- **Predicción mejorada**: Los modelos consideran el impacto de feriados automáticamente

### 7. 📊 Preparación de Datos (NUEVO)
- **Carga flexible**: CSV, Excel y JSON
- **Validación automática**: Verificación de columnas requeridas
- **Mapeo inteligente**: Detección automática de formatos de datos
- **Integración API**: Conectividad con Reservo y otras fuentes

### 8. ⚙️ Automatización con Progreso
- Pipeline completo automatizado con **indicadores visuales de progreso**
- **Barra de estado**: Seguimiento en tiempo real del proceso
- **Estimación de tiempo**: Tiempo restante para completar
- Programación de ejecuciones
- Sistema de notificaciones

## 📈 Métricas y Objetivos

| Métrica | Objetivo | Descripción |
|---------|----------|-------------|
| **MAE** | < 10 llamadas/día | Error absoluto promedio |
| **RMSE** | < 15 llamadas/día | Error cuadrático medio |
| **MAPE** | < 25% | Error porcentual absoluto |
| **Precisión Alertas** | > 90% | Precisión del sistema de alertas |

## 🔧 Configuración Avanzada

### Personalizar Objetivos de Performance

Editar los valores en `sistema_multi_modelo.py`:

```python
config_default = {
    'objetivos_performance': {
        'mae_objetivo': 10.0,        # Cambiar según necesidad
        'rmse_objetivo': 15.0,       # Cambiar según necesidad
        'mape_objetivo': 25.0        # Cambiar según necesidad
    }
}
```

### Configurar Automatización

Editar `automatizacion_completa.py` para:
- Horarios de ejecución
- Destinatarios de notificaciones
- Configuración de email
- Umbrales de alertas

### Personalizar Dashboard

El dashboard es completamente personalizable editando `dashboard_comparacion.py`:
- Agregar nuevos tipos de gráficas
- Modificar métricas mostradas
- Cambiar colores y temas
- Agregar nuevos análisis

## 🚨 Solución de Problemas

### Error: "No se pudieron cargar los datos"
- Verificar que el archivo de datos existe en la ruta correcta
- Comprobar permisos de lectura del archivo
- Validar formato del archivo CSV

### Error: "Modelos no encontrados"
- Ejecutar primero la segmentación de llamadas
- Luego entrenar los modelos multi-modelo
- Verificar que se generaron los archivos JSON de resultados

### Error de dependencias
```bash
# Reinstalar dependencias
pip install --upgrade -r requirements.txt

# Si hay conflictos, usar entorno virtual
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Performance lenta
- Reducir el período de datos para análisis
- Usar menos modelos en el ensemble
- Optimizar configuración de Streamlit

## 📞 Soporte

Para soporte técnico o preguntas sobre el sistema:

- **Email**: soporte@ceapsi.cl
- **Documentación**: Usar el módulo "📋 Documentación" en la aplicación
- **Logs**: Revisar archivos de log generados automáticamente

## 🔄 Actualizaciones

### Versión 1.0 - Actual
- ✅ Sistema multi-modelo completo
- ✅ Dashboard interactivo
- ✅ Análisis de atención histórica
- ✅ Automatización programada
- ✅ Sistema de alertas avanzado

### Próximas Versiones
- 🔄 Integración con API de Alodesk en tiempo real
- 🔄 Modelos de deep learning (LSTM, Transformer)
- 🔄 Predicción por agente individual
- 🔄 Optimización automática de turnos

## 📄 Licencia

Este proyecto es propiedad de CEAPSI y está destinado para uso interno.

---

**📞 CEAPSI - Precision Call Forecast** | Desarrollado con ❤️ para optimizar la experiencia del call center
