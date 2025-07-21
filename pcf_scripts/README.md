# 📞 CEAPSI - Sistema PCF (Precision Call Forecast)

Sistema completo de predicción de llamadas para call center usando inteligencia artificial y análisis avanzado de datos.

## 🎯 Características Principales

- **🤖 Múltiples Modelos de IA**: ARIMA, Prophet, Random Forest, Gradient Boosting
- **📊 Dashboard Interactivo**: Visualización en tiempo real con Streamlit y Plotly
- **🔍 Auditoría de Datos**: Análisis automático de calidad y patrones
- **🔀 Segmentación Inteligente**: Clasificación automática de llamadas entrantes/salientes
- **🚨 Sistema de Alertas**: Detección proactiva de picos de demanda
- **⚙️ Automatización Completa**: Pipeline programado con notificaciones
- **📈 Análisis de Atención**: Métricas históricas de los últimos 15, 30 y 90 días

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

3. **Configurar datos**
   
   Asegúrate de tener el archivo de datos en la ruta correcta:
   ```
   ../backups/alodesk_reporte_llamadas_jan2023_to_jul2025.csv
   ```

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
├── 📊 dashboard_comparacion.py        # Dashboard de validación
├── 🔍 auditoria_datos_llamadas.py     # Auditoría de calidad de datos
├── 🔀 segmentacion_llamadas.py        # Segmentación de llamadas
├── 🤖 sistema_multi_modelo.py         # Sistema multi-modelo
├── ⚙️ automatizacion_completa.py      # Pipeline automatizado
├── 📋 requirements.txt                # Dependencias
├── 📖 README.md                       # Esta documentación
└── .streamlit/
    └── config.toml                    # Configuración de Streamlit
```

## 🎮 Guía de Uso

### 1. 🏠 Página de Inicio
- Resumen del sistema y métricas principales
- Enlaces rápidos a los módulos
- Estado actual del sistema

### 2. 📊 Dashboard de Validación
- **Análisis de Atención**: Gráficas de los últimos 15, 30 y 90 días
- **Comparación de Modelos**: Performance de algoritmos individuales
- **Predicciones Futuras**: Visualización de predicciones con intervalos de confianza
- **Sistema de Alertas**: Alertas validadas con niveles de confianza
- **Métricas de Objetivo**: Progress hacia objetivos del proyecto

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

### 6. ⚙️ Automatización
- Pipeline completo automatizado
- Programación de ejecuciones
- Sistema de notificaciones
- Controles manuales

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
