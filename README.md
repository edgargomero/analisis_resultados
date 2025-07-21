# 🏥 CEAPSI - Análisis 360° y Sistema de Forecasting Predictivo

## Descripción General

Este proyecto implementa una **solución integral de análisis y predicción** para la gestión de recursos humanos en CEAPSI, combinando:
- **Normalización y análisis de datos operacionales** (reservas, llamadas, conversaciones)
- **Visualización avanzada** (mapas de calor, dashboards interactivos)
- **Sistema de forecasting** con Prophet y ARIMA para anticipar necesidades de personal
- **Comparación automática de modelos**
- **Automatización y generación de reportes**

---

## 🚀 **Funcionamiento Actual del Proyecto**

### 1. **Procesamiento y Normalización de Datos**

- **Script principal:** `procesar_datos_ceapsi.py`
- **Fuentes:**  
  - Reservas (sistema Reservo)
  - Llamadas y conversaciones (sistema Alodesk)
- **Salidas:**  
  - Datos normalizados (`datos_normalizados.json`)
  - Métricas de carga laboral (`metricas_carga_laboral.json`)
  - Datos para mapas de calor (`mapa_calor_datos.json`)
  - Resumen ejecutivo (`resumen_ejecutivo.json`)
  - Personal necesario por hora/cargo/semana (`personal_necesario_por_hora.csv` y `.json`)
  - **Todos los archivos se exportan en una carpeta con timestamp** (ej: `resultados_20250718_120355`)

### 2. **Análisis y Visualización**

- **Mapas de calor**: Visualización de la intensidad de transacciones por mes y día de la semana.
- **Dashboards**:  
  - Dashboard actual (React/HTML, no incluido en este repo)
  - Dashboard predictivo (Streamlit, ver sección Forecasting)

### 3. **Sistema de Forecasting Predictivo**

- **Pipeline Prophet y ARIMA**:
  - Preparación de datos (`forecasting/data_preparation.py`):  
    - Filtra domingos y outliers
    - Calcula variable objetivo (horas-persona/día)
    - Genera regresores (volumen de reservas, llamadas, conversaciones, especialidades, etc.)
    - Exporta `datos_prophet.csv` y metadatos
    - Exporta resumen de actividades por cargo y usuario (`actividades_por_cargo_usuario.csv`)
  - Entrenamiento del modelo Prophet (`forecasting/model_training.py`):  
    - Entrena Prophet con regresores
    - Guarda modelo y metadatos
  - **Comparación Prophet vs ARIMA** (`forecasting/compare_arima_prophet.py`):  
    - Entrena ambos modelos sobre los mismos datos
    - Genera predicciones y métricas comparativas (MAE, RMSE)
    - Exporta resultados en la carpeta de resultados más reciente
  - Generación de predicciones (`forecasting/predictions.py`):  
    - Predice necesidades de personal para próximas semanas
    - Detecta alertas y genera recomendaciones de staffing
    - Exporta resultados en JSON, Excel y CSV

### 4. **Automatización**

- **Script:** `forecasting/automation_setup.py`
- Permite ejecutar el pipeline completo de forma programada, enviar alertas por email y generar reportes automáticos.
- Integra la comparación Prophet vs ARIMA en cada ejecución.

---

## 📂 **Estructura de Carpetas y Archivos**

```
analisis_resultados/
├── resultados_YYYYMMDD_HHMMSS/         # Carpeta de resultados por ejecución
│   ├── datos_normalizados.json
│   ├── metricas_carga_laboral.json
│   ├── mapa_calor_datos.json
│   ├── resumen_ejecutivo.json
│   ├── personal_necesario_por_hora.csv
│   ├── personal_necesario_por_hora.json
│   ├── datos_prophet.csv
│   ├── metadatos_prophet.json
│   ├── modelo_prophet.pkl
│   ├── metadatos_modelo.json
│   ├── predicciones_ceapsi_*.json
│   ├── predicciones_arima_*.json
│   └── ...otros archivos
├── forecasting/
│   ├── data_preparation.py
│   ├── model_training.py
│   ├── predictions.py
│   ├── compare_arima_prophet.py
│   ├── automation_setup.py
│   ├── visualization_dashboard.py
│   └── ...otros archivos
├── README.md
├── requirements.txt
└── ...
```

---

## 🛠️ **Cómo Usar el Proyecto**

### **Procesamiento de datos**

```bash
python procesar_datos_ceapsi.py
```
- Genera todos los archivos de análisis y normalización en una carpeta de resultados con timestamp.

### **Preparación y entrenamiento del modelo Prophet**

```bash
cd forecasting
python data_preparation.py
python model_training.py
```

### **Comparación Prophet vs ARIMA**

```bash
python compare_arima_prophet.py
```
- Guarda las predicciones y métricas de ambos modelos en la última carpeta de resultados.

### **Generación de predicciones**

```bash
python predictions.py
```

### **Dashboard predictivo**

```bash
python -m streamlit run forecasting/visualization_dashboard.py
```
- El dashboard muestra la comparación Prophet vs ARIMA, métricas y gráficos.

### **Automatización**

```bash
python forecasting/automation_setup.py --run-once
```
- Ejecuta el pipeline completo, incluyendo la comparación de modelos.

---

## 📊 **Principales Métricas y Funcionalidades**

- **Carga laboral por cargo y usuario** (análisis 360°)
- **Mapas de calor** de actividad por mes y día
- **Predicción de necesidades de personal** (horas-persona/día)
- **Comparación Prophet vs ARIMA** (métricas y gráficos)
- **Alertas automáticas** y recomendaciones de staffing
- **Exportación de resultados** en múltiples formatos
- **Historial de ejecuciones** gracias a carpetas con timestamp

---

## 📈 **Beneficios y Resultados**

- **Optimización de recursos humanos**: reducción de sobre-staffing y mejora en la planificación.
- **Visualización clara** de patrones de demanda y carga laboral.
- **Predicción robusta** con Prophet y ARIMA.
- **Automatización y reportes** para toma de decisiones ágil.
- **Comparación objetiva de modelos** para elegir el mejor enfoque.

---

## 📋 **Requisitos**

- Python 3.8+
- Ver dependencias en `requirements.txt`
- Archivos de datos fuente (CSV de Reservo y Alodesk) en las rutas esperadas.

---

## 📞 **Soporte y Contacto**

- Para dudas técnicas, revisar los scripts y la documentación inline.
- Para soporte, contactar al equipo de desarrollo CEAPSI.

---

**Desarrollado para CEAPSI - Optimización de recursos humanos en salud mental**  
**Estado:** 100% funcional y listo para producción  
**Última actualización:** Julio 2025
