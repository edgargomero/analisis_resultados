# 🏥 CEAPSI - Sistema Integral de Análisis y Predicción

## 📋 Descripción General

Sistema completo de análisis de datos y predicción para la gestión de recursos humanos en CEAPSI, que integra:

- **📊 Análisis 360°** de datos operacionales (reservas, llamadas, conversaciones)
- **🤖 Sistema PCF** (Precision Call Forecast) con múltiples modelos de IA
- **☁️ Deployment en Streamlit Cloud** con base de datos Supabase
- **🔗 Integración con API Reservo** para datos en tiempo real
- **📈 Dashboards interactivos** con visualizaciones avanzadas

---

## 🚀 Acceso Rápido

### 🌐 **Aplicación en Producción**
- **URL**: [Disponible en Streamlit Cloud]
- **Acceso**: Requiere autenticación Supabase

### 💻 **Desarrollo Local**
```bash
# Clonar repositorio
git clone https://github.com/edgargomero/analisis_resultados.git
cd analisis_resultados

# Sistema PCF (Streamlit)
cd pcf_scripts
pip install -r requirements.txt
python run.py
```

---

## 🏗️ Arquitectura del Proyecto

```
analisis_resultados/
├── 📁 pcf_scripts/                    # Sistema PCF (Call Forecast)
│   ├── 🚀 app.py                      # Aplicación principal Streamlit
│   ├── 📦 requirements.txt            # Dependencias Python
│   ├── 🏃 run.py                      # Launcher simplificado
│   │
│   ├── 📁 src/                        # Código fuente modular
│   │   ├── api/                       # Integración Reservo API
│   │   ├── auth/                      # Autenticación Supabase
│   │   ├── core/                      # Procesamiento de datos
│   │   ├── models/                    # Modelos de IA (ARIMA, Prophet, RF, GB)
│   │   ├── services/                  # Lógica de negocio
│   │   ├── ui/                        # Componentes UI
│   │   └── utils/                     # Utilidades
│   │
│   ├── 📁 assets/                     # Recursos estáticos
│   ├── 📁 docs/                       # Documentación completa
│   └── 📁 .streamlit/                 # Configuración Streamlit
│
├── 📁 resultados_YYYYMMDD/            # Resultados históricos
├── 📁 forecasting/                    # Sistema de predicción legacy
└── 📁 scripts/                        # Scripts de análisis
```

---

## 🎯 Características Principales

### 1. **Sistema PCF (Precision Call Forecast)**
- **4 Modelos de IA**: ARIMA, Prophet, Random Forest, Gradient Boosting
- **Ensemble Learning**: Combinación optimizada de modelos
- **Predicción a 28 días**: Proyección de llamadas entrantes/salientes
- **Precisión objetivo**: MAE < 10, RMSE < 15, MAPE < 25%

### 2. **Integración en Tiempo Real**
- **🔗 Reservo API**: Sincronización cada 15 minutos
- **🗄️ Supabase**: Base de datos en la nube
- **📊 Dashboard en vivo**: Métricas actualizadas automáticamente

### 3. **Análisis Avanzado**
- **🇨🇱 Feriados Chilenos**: Análisis de impacto en volumen
- **📈 Segmentación**: Clasificación automática de llamadas
- **🔍 Auditoría**: Validación de calidad de datos
- **👥 Análisis por Usuario**: Performance por cargo/agente

### 4. **Automatización y Alertas**
- **Pipeline automatizado**: Ejecución programada
- **Sistema de alertas**: Detección de anomalías
- **Reportes automáticos**: Generación de informes

---

## 🛠️ Instalación y Configuración

### Requisitos
- Python 3.8 o superior
- Cuenta en Streamlit Cloud (para deployment)
- Credenciales de Supabase
- API Key de Reservo

### Instalación Local

1. **Clonar el repositorio**
```bash
git clone https://github.com/edgargomero/analisis_resultados.git
cd analisis_resultados/pcf_scripts
```

2. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

3. **Configurar variables de entorno**
```bash
# Copiar template
cp .env.example .env

# Editar con tus credenciales
# SUPABASE_URL=https://xxxxx.supabase.co
# SUPABASE_KEY=your-service-role-key
# RESERVO_API_KEY=your-api-key
```

4. **Ejecutar aplicación**
```bash
python run.py
# O directamente: streamlit run app.py
```

---

## 📊 Uso del Sistema

### 1. **Carga de Datos**
- Subir archivo CSV/Excel con datos de llamadas
- Formatos soportados: CSV (;), Excel (.xlsx, .xls)
- Columnas requeridas: FECHA, TELEFONO, SENTIDO, ATENDIDA

### 2. **Pipeline de Procesamiento**
1. **Auditoría**: Validación de calidad (~15s)
2. **Segmentación**: Clasificación de llamadas (~20s)
3. **Entrenamiento**: 4 modelos de IA (~45s)
4. **Predicción**: Proyección a 28 días (~25s)

### 3. **Dashboard Interactivo**
- Visualización de predicciones
- Comparación de modelos
- Análisis por hora/día/semana
- Impacto de feriados chilenos

### 4. **Exportación de Resultados**
- JSON con predicciones detalladas
- Excel con resumen ejecutivo
- CSV para análisis adicional

---

## 🚀 Deployment en Streamlit Cloud

### Configuración
1. Fork el repositorio en GitHub
2. Conectar con Streamlit Cloud
3. Configurar:
   - **Main file path**: `pcf_scripts/app.py`
   - **Python version**: 3.9

### Secrets Configuration
En Streamlit Cloud dashboard → Settings → Secrets:
```toml
SUPABASE_URL = "https://your-project.supabase.co"
SUPABASE_KEY = "your-service-role-key"
SUPABASE_ANON_KEY = "your-anon-key"
RESERVO_API_URL = "https://api.reservo.cl"
RESERVO_API_KEY = "your-api-key"
```

---

## 📈 Métricas y Performance

| Métrica | Objetivo | Estado Actual |
|---------|----------|---------------|
| MAE | < 10 llamadas/día | ✅ Cumplido |
| RMSE | < 15 llamadas/día | ✅ Cumplido |
| MAPE | < 25% | ✅ Cumplido |
| Uptime | > 99% | ✅ En monitoreo |

---

## 📚 Documentación

- [📖 Guía de Usuario](pcf_scripts/docs/README.md)
- [🏗️ Arquitectura del Sistema](pcf_scripts/docs/architecture/ARCHITECTURE.md)
- [🚀 Deployment Guide](pcf_scripts/docs/STREAMLIT_DEPLOYMENT.md)
- [📚 Referencias Técnicas](pcf_scripts/docs/REFERENCES.md)
- [🔐 Configuración de Seguridad](pcf_scripts/docs/SECURITY_SETUP.md)

---

## 🤝 Contribuir

1. Fork el proyecto
2. Crear feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit cambios (`git commit -m 'Add AmazingFeature'`)
4. Push al branch (`git push origin feature/AmazingFeature`)
5. Abrir Pull Request

---

## 📞 Soporte

- **Email**: soporte@ceapsi.cl
- **Issues**: [GitHub Issues](https://github.com/edgargomero/analisis_resultados/issues)
- **Documentación**: Ver carpeta `docs/`

---

## 📄 Licencia

Proyecto privado de CEAPSI. Todos los derechos reservados.

---

**Desarrollado para CEAPSI** - Sistema integral de predicción y análisis  
**Estado**: ✅ En producción  
**Última actualización**: Enero 2025  
**Versión**: 2.0.0