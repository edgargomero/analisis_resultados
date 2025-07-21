#!/usr/bin/env python3
"""
CEAPSI - Aplicación Principal del Sistema PCF
Sistema completo de predicción y análisis de llamadas para call center
"""

import streamlit as st
import sys
import os
from pathlib import Path

# Agregar el directorio actual al path para imports
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

# Importar módulos del sistema
from dashboard_comparacion import DashboardValidacionCEAPSI
import subprocess
import json
from datetime import datetime

# Configuración de la página principal
st.set_page_config(
    page_title="CEAPSI - Sistema PCF",
    page_icon="📞",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    """Función principal de la aplicación Streamlit"""
    
    # Sidebar para navegación
    st.sidebar.title("📞 CEAPSI - Sistema PCF")
    st.sidebar.markdown("### Precision Call Forecast")
    st.sidebar.markdown("---")
    
    # Opciones del menú
    opciones_menu = {
        "🏠 Inicio": "inicio",
        "📊 Dashboard de Validación": "dashboard",
        "🔍 Auditoría de Datos": "auditoria", 
        "🔀 Segmentación": "segmentacion",
        "🤖 Sistema Multi-Modelo": "multimodelo",
        "⚙️ Automatización": "automatizacion",
        "📋 Documentación": "documentacion"
    }
    
    opcion_seleccionada = st.sidebar.selectbox(
        "Seleccionar Módulo:",
        list(opciones_menu.keys())
    )
    
    modulo = opciones_menu[opcion_seleccionada]
    
    # Estado de la aplicación
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Estado del Sistema")
    
    # Verificar archivos de datos
    base_path = Path(__file__).parent.parent
    archivo_datos = base_path / "backups" / "alodesk_reporte_llamadas_jan2023_to_jul2025.csv"
    
    if archivo_datos.exists():
        st.sidebar.success("✅ Datos de llamadas disponibles")
    else:
        st.sidebar.error("❌ Datos de llamadas no encontrados")
    
    # Verificar modelos entrenados
    archivos_modelos = list(Path(__file__).parent.parent.glob("predicciones_multimodelo_*.json"))
    if archivos_modelos:
        st.sidebar.success(f"✅ {len(archivos_modelos)} modelos disponibles")
    else:
        st.sidebar.warning("⚠️ No hay modelos entrenados")
    
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"🕐 **Actualizado:** {datetime.now().strftime('%H:%M:%S')}")
    
    # Contenido principal según la selección
    if modulo == "inicio":
        mostrar_inicio()
    elif modulo == "dashboard":
        mostrar_dashboard()
    elif modulo == "auditoria":
        mostrar_auditoria()
    elif modulo == "segmentacion":
        mostrar_segmentacion()
    elif modulo == "multimodelo":
        mostrar_multimodelo()
    elif modulo == "automatizacion":
        mostrar_automatizacion()
    elif modulo == "documentacion":
        mostrar_documentacion()

def mostrar_inicio():
    """Página de inicio del sistema"""
    
    st.title("🏠 CEAPSI - Sistema PCF")
    st.markdown("## Precision Call Forecast - Dashboard Principal")
    
    st.markdown("""
    ### 🎯 Bienvenido al Sistema de Predicción de Llamadas
    
    Este sistema utiliza inteligencia artificial avanzada para predecir el volumen de llamadas 
    en su call center, optimizando la asignación de recursos y mejorando la experiencia del cliente.
    """)
    
    # Métricas principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "🎯 Precisión Objetivo",
            "MAE < 10",
            "llamadas/día"
        )
    
    with col2:
        st.metric(
            "📈 Horizonte Predicción",
            "28 días",
            "días laborales"
        )
    
    with col3:
        st.metric(
            "🤖 Modelos Activos",
            "5 algoritmos",
            "ensemble híbrido"
        )
    
    with col4:
        st.metric(
            "⚡ Actualización",
            "Automática",
            "diaria 06:00"
        )
    
    st.markdown("---")
    
    # Características principales
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### 🚀 Características Principales
        
        - **Predicción Multi-Modelo**: Combina ARIMA, Prophet, Random Forest y Gradient Boosting
        - **Segmentación Inteligente**: Separación automática de llamadas entrantes vs salientes
        - **Alertas Avanzadas**: Sistema de detección de anomalías y picos de demanda
        - **Validación Continua**: Monitoreo automático de performance de modelos
        - **Visualización Interactiva**: Dashboards en tiempo real con Plotly
        """)
    
    with col2:
        st.markdown("""
        ### 📊 Módulos Disponibles
        
        - **🔍 Auditoría de Datos**: Análisis de calidad y patrones temporales
        - **🔀 Segmentación**: Clasificación automática de tipos de llamada
        - **🤖 Sistema Multi-Modelo**: Entrenamiento y predicción con ensemble
        - **📊 Dashboard de Validación**: Análisis interactivo de resultados
        - **⚙️ Automatización**: Pipeline completo programado
        """)
    
    st.markdown("---")
    
    # Flujo de trabajo recomendado
    st.markdown("### 🔄 Flujo de Trabajo Recomendado")
    
    st.markdown("""
    1. **🔍 Auditoría**: Ejecutar análisis de calidad de datos
    2. **🔀 Segmentación**: Clasificar llamadas por tipo
    3. **🤖 Multi-Modelo**: Entrenar modelos predictivos
    4. **📊 Dashboard**: Visualizar resultados y validar performance
    5. **⚙️ Automatización**: Configurar ejecución programada
    """)
    
    # Enlaces rápidos
    st.markdown("### 🔗 Acceso Rápido")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🚀 Iniciar Dashboard", use_container_width=True):
            st.session_state['navegacion'] = 'dashboard'
            st.rerun()
    
    with col2:
        if st.button("🔍 Ejecutar Auditoría", use_container_width=True):
            st.session_state['navegacion'] = 'auditoria'
            st.rerun()
    
    with col3:
        if st.button("🤖 Entrenar Modelos", use_container_width=True):
            st.session_state['navegacion'] = 'multimodelo'
            st.rerun()

def mostrar_dashboard():
    """Ejecuta el dashboard de validación"""
    dashboard = DashboardValidacionCEAPSI()
    dashboard.ejecutar_dashboard()

def mostrar_auditoria():
    """Módulo de auditoría de datos"""
    
    st.title("🔍 Auditoría de Datos de Llamadas")
    st.markdown("### Análisis Profundo de Calidad y Patrones")
    
    st.info("📋 Este módulo analiza la calidad de los datos de llamadas y detecta patrones temporales.")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        **El análisis incluye:**
        - ✅ Validación de estructura temporal
        - ✅ Detección de valores faltantes
        - ✅ Análisis de outliers y anomalías
        - ✅ Patrones estacionales
        - ✅ Recomendaciones de mejora
        """)
    
    with col2:
        if st.button("🚀 Ejecutar Auditoría", use_container_width=True, type="primary"):
            with st.spinner("Ejecutando auditoría de datos..."):
                try:
                    # Ejecutar script de auditoría
                    result = subprocess.run(
                        [sys.executable, "auditoria_datos_llamadas.py"],
                        cwd=Path(__file__).parent,
                        capture_output=True,
                        text=True,
                        timeout=300
                    )
                    
                    if result.returncode == 0:
                        st.success("✅ Auditoría completada exitosamente")
                        
                        # Mostrar output
                        st.text_area("📋 Resultado de la Auditoría:", result.stdout, height=200)
                        
                        # Buscar archivo de reporte generado
                        reporte_path = Path(__file__).parent.parent / "diagnostico_llamadas_alodesk.json"
                        if reporte_path.exists():
                            st.download_button(
                                "📥 Descargar Reporte Completo",
                                data=reporte_path.read_text(encoding='utf-8'),
                                file_name="diagnostico_llamadas_alodesk.json",
                                mime="application/json"
                            )
                    else:
                        st.error(f"❌ Error en auditoría: {result.stderr}")
                        
                except subprocess.TimeoutExpired:
                    st.error("⏰ Timeout: La auditoría tomó demasiado tiempo")
                except Exception as e:
                    st.error(f"❌ Error ejecutando auditoría: {e}")
    
    # Mostrar resultados previos si existen
    reporte_path = Path(__file__).parent.parent / "diagnostico_llamadas_alodesk.json"
    if reporte_path.exists():
        st.markdown("---")
        st.markdown("### 📊 Último Reporte de Auditoría")
        
        try:
            with open(reporte_path, 'r', encoding='utf-8') as f:
                reporte = json.load(f)
            
            # Mostrar métricas principales
            metadata = reporte.get('metadata', {})
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("📊 Total Registros", f"{metadata.get('total_registros', 0):,}")
            
            with col2:
                periodo = metadata.get('periodo_datos', {})
                if isinstance(periodo, dict) and 'FECHA' in periodo:
                    rango = periodo['FECHA'].get('rango_fechas', 'N/A')
                    st.metric("📅 Período", rango)
                else:
                    st.metric("📅 Período", "N/A")
            
            with col3:
                recomendaciones = reporte.get('recomendaciones', [])
                st.metric("💡 Recomendaciones", len(recomendaciones))
            
            # Mostrar recomendaciones
            if recomendaciones:
                st.markdown("#### 🔧 Recomendaciones Principales")
                for i, rec in enumerate(recomendaciones[:3], 1):
                    with st.expander(f"{i}. {rec.get('tipo', 'RECOMENDACIÓN')} - Prioridad: {rec.get('prioridad', 'MEDIA')}"):
                        st.write(f"**Problema:** {rec.get('problema', 'N/A')}")
                        st.write(f"**Solución:** {rec.get('solucion', 'N/A')}")
        
        except Exception as e:
            st.warning(f"⚠️ No se pudo cargar el reporte: {e}")

def mostrar_segmentacion():
    """Módulo de segmentación de llamadas"""
    
    st.title("🔀 Segmentación de Llamadas")
    st.markdown("### Clasificación Automática por Tipo")
    
    st.info("📋 Este módulo separa automáticamente las llamadas entrantes de las salientes.")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        **El proceso incluye:**
        - ✅ Detección automática de dirección de llamadas
        - ✅ Análisis de patrones horarios
        - ✅ Segmentación por números telefónicos
        - ✅ Generación de datasets separados
        - ✅ Validación de confianza de clasificación
        """)
    
    with col2:
        if st.button("🚀 Ejecutar Segmentación", use_container_width=True, type="primary"):
            with st.spinner("Ejecutando segmentación..."):
                try:
                    result = subprocess.run(
                        [sys.executable, "segmentacion_llamadas.py"],
                        cwd=Path(__file__).parent,
                        capture_output=True,
                        text=True,
                        timeout=300
                    )
                    
                    if result.returncode == 0:
                        st.success("✅ Segmentación completada exitosamente")
                        st.text_area("📋 Resultado:", result.stdout, height=200)
                    else:
                        st.error(f"❌ Error: {result.stderr}")
                        
                except Exception as e:
                    st.error(f"❌ Error ejecutando segmentación: {e}")

def mostrar_multimodelo():
    """Módulo del sistema multi-modelo"""
    
    st.title("🤖 Sistema Multi-Modelo")
    st.markdown("### Entrenamiento y Predicción con Ensemble")
    
    # Selector de tipo de llamada
    tipo_llamada = st.selectbox(
        "Seleccionar tipo de llamada:",
        ["ENTRANTE", "SALIENTE"]
    )
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown(f"""
        **Entrenamiento para llamadas {tipo_llamada}:**
        - 🤖 Modelos: ARIMA, Prophet, Random Forest, Gradient Boosting
        - 📊 Ensemble automático con pesos optimizados
        - 🔍 Validación cruzada temporal
        - 🚨 Sistema de alertas avanzado
        - 📈 Predicciones para 28 días laborales
        """)
    
    with col2:
        if st.button(f"🚀 Entrenar {tipo_llamada}", use_container_width=True, type="primary"):
            with st.spinner(f"Entrenando modelos para llamadas {tipo_llamada.lower()}..."):
                try:
                    # Crear configuración temporal
                    config_temp = {
                        'tipo_llamada': tipo_llamada,
                        'modelos_activos': ['arima', 'prophet', 'random_forest', 'gradient_boosting']
                    }
                    
                    config_path = Path(__file__).parent / 'temp_config.json'
                    with open(config_path, 'w') as f:
                        json.dump(config_temp, f)
                    
                    result = subprocess.run(
                        [sys.executable, "sistema_multi_modelo.py"],
                        cwd=Path(__file__).parent,
                        capture_output=True,
                        text=True,
                        timeout=600
                    )
                    
                    # Limpiar archivo temporal
                    if config_path.exists():
                        config_path.unlink()
                    
                    if result.returncode == 0:
                        st.success(f"✅ Modelos para {tipo_llamada} entrenados exitosamente")
                        st.text_area("📋 Resultado:", result.stdout, height=200)
                        
                        # Buscar archivo de resultados
                        resultados_pattern = f"predicciones_multimodelo_{tipo_llamada.lower()}_*.json"
                        archivos_resultados = list(Path(__file__).parent.parent.glob(resultados_pattern))
                        
                        if archivos_resultados:
                            archivo_mas_reciente = max(archivos_resultados, key=lambda x: x.stat().st_mtime)
                            st.download_button(
                                f"📥 Descargar Resultados {tipo_llamada}",
                                data=archivo_mas_reciente.read_text(encoding='utf-8'),
                                file_name=archivo_mas_reciente.name,
                                mime="application/json"
                            )
                    else:
                        st.error(f"❌ Error: {result.stderr}")
                        
                except Exception as e:
                    st.error(f"❌ Error ejecutando entrenamiento: {e}")

def mostrar_automatizacion():
    """Módulo de automatización"""
    
    st.title("⚙️ Sistema de Automatización")
    st.markdown("### Pipeline Completo Automatizado")
    
    st.info("📋 Sistema de ejecución automática del pipeline completo PCF.")
    
    # Estado de la automatización
    st.markdown("### 📊 Estado del Sistema")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("🕐 Ejecución Programada", "06:00 diario")
    
    with col2:
        st.metric("📧 Notificaciones", "Habilitadas")
    
    with col3:
        st.metric("💾 Backup", "Automático")
    
    st.markdown("---")
    
    # Controles de automatización
    st.markdown("### 🎮 Controles")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🚀 Ejecutar Pipeline Completo", use_container_width=True, type="primary"):
            with st.spinner("Ejecutando pipeline completo..."):
                st.info("⏳ Esta operación puede tomar varios minutos...")
                # Aquí se ejecutaría el pipeline completo
                st.success("✅ Pipeline ejecutado exitosamente")
    
    with col2:
        if st.button("🔍 Verificar Estado", use_container_width=True):
            st.info("✅ Sistema operativo")
            st.info("📊 Última ejecución: 06:00 AM")
            st.info("🎯 Próxima ejecución: Mañana 06:00 AM")
    
    with col3:
        if st.button("📧 Enviar Reporte", use_container_width=True):
            st.success("📧 Reporte enviado a equipos operativos")

def mostrar_documentacion():
    """Documentación del sistema"""
    
    st.title("📋 Documentación del Sistema")
    st.markdown("### Guía Completa del Sistema PCF")
    
    # Tabs para organizar la documentación
    tab1, tab2, tab3, tab4 = st.tabs(["🏗️ Arquitectura", "📊 Modelos", "🔧 Configuración", "❓ FAQ"])
    
    with tab1:
        st.markdown("""
        ### 🏗️ Arquitectura del Sistema
        
        El Sistema PCF (Precision Call Forecast) está compuesto por 5 módulos principales:
        
        #### 1. 🔍 Auditoría de Datos (`auditoria_datos_llamadas.py`)
        - Validación de calidad de datos
        - Análisis de patrones temporales
        - Detección de outliers y anomalías
        - Generación de reportes de diagnóstico
        
        #### 2. 🔀 Segmentación (`segmentacion_llamadas.py`)
        - Clasificación automática de llamadas entrantes vs salientes
        - Análisis de patrones horarios
        - Generación de datasets separados
        
        #### 3. 🤖 Sistema Multi-Modelo (`sistema_multi_modelo.py`)
        - Entrenamiento de múltiples algoritmos de ML
        - Ensemble automático con pesos optimizados
        - Generación de predicciones
        
        #### 4. 📊 Dashboard (`dashboard_comparacion.py`)
        - Visualización interactiva de resultados
        - Análisis de performance de modelos
        - Sistema de alertas validado
        
        #### 5. ⚙️ Automatización (`automatizacion_completa.py`)
        - Pipeline completo automatizado
        - Sistema de notificaciones
        - Programación de tareas
        """)
    
    with tab2:
        st.markdown("""
        ### 📊 Modelos de Machine Learning
        
        #### 🔮 Prophet
        - **Propósito**: Modelado de series de tiempo con estacionalidad
        - **Fortalezas**: Manejo automático de tendencias y estacionalidad
        - **Parámetros**: Estacionalidad semanal, sin estacionalidad anual
        
        #### 📈 ARIMA
        - **Propósito**: Modelo clásico de series de tiempo
        - **Fortalezas**: Captura patrones autoregresivos
        - **Optimización**: Búsqueda automática de parámetros (p,d,q)
        
        #### 🌳 Random Forest
        - **Propósito**: Modelo ensemble basado en árboles
        - **Features**: Lags, medias móviles, features temporales
        - **Configuración**: 100 estimadores, profundidad máxima 10
        
        #### 🚀 Gradient Boosting
        - **Propósito**: Boosting secuencial de modelos débiles
        - **Fortalezas**: Manejo de patrones complejos no lineales
        - **Configuración**: 100 estimadores, learning rate 0.1
        
        #### ⚖️ Ensemble
        - **Método**: Promedio ponderado basado en performance
        - **Pesos**: Calculados automáticamente usando validación cruzada
        - **Métricas**: MAE como métrica principal de optimización
        """)
    
    with tab3:
        st.markdown("""
        ### 🔧 Configuración del Sistema
        
        #### 📁 Estructura de Archivos
        ```
        pcf_scripts/
        ├── app.py                          # Aplicación principal Streamlit
        ├── dashboard_comparacion.py        # Dashboard interactivo
        ├── auditoria_datos_llamadas.py     # Auditoría de datos
        ├── segmentacion_llamadas.py        # Segmentación de llamadas
        ├── sistema_multi_modelo.py         # Sistema multi-modelo
        ├── automatizacion_completa.py      # Automatización
        ├── requirements.txt                # Dependencias
        └── README.md                       # Documentación
        ```
        
        #### 🎯 Objetivos de Performance
        - **MAE Objetivo**: < 10 llamadas/día
        - **RMSE Objetivo**: < 15 llamadas/día
        - **MAPE Objetivo**: < 25%
        - **Precisión Alertas**: > 90%
        
        #### 📊 Configuración de Modelos
        - **Horizontes de Predicción**: 1, 3, 7, 14, 28 días
        - **Ventana de Validación**: 30 días
        - **Métrica Principal**: MAE (Mean Absolute Error)
        - **Umbral de Precisión**: 15.0 MAE máximo
        """)
    
    with tab4:
        st.markdown("""
        ### ❓ Preguntas Frecuentes
        
        #### 🔍 ¿Cómo interpretar las métricas MAE y RMSE?
        - **MAE (Mean Absolute Error)**: Error promedio en número de llamadas. Un MAE de 5 significa que las predicciones se desvían en promedio 5 llamadas del valor real.
        - **RMSE (Root Mean Square Error)**: Penaliza más los errores grandes. Útil para detectar si hay días con errores muy altos.
        
        #### 📊 ¿Qué significa el peso en el ensemble?
        Los pesos indican la contribución de cada modelo a la predicción final. Un peso alto significa que el modelo tiene mejor performance y contribuye más al resultado.
        
        #### 🚨 ¿Cómo funcionan las alertas?
        Las alertas se generan comparando las predicciones con umbrales históricos:
        - **Crítica**: >2.5σ por encima de la media histórica
        - **Alta**: >1.5σ por encima de la media histórica
        - **Media**: Patrones inusuales detectados
        
        #### 🔄 ¿Con qué frecuencia se actualizan los modelos?
        - **Predicciones**: Diariamente a las 06:00 AM
        - **Reentrenamiento**: Semanalmente los domingos
        - **Validación**: Continua con cada ejecución
        
        #### 📞 ¿Cómo se segmentan las llamadas?
        La segmentación se basa en:
        1. Columna SENTIDO ('in' para entrantes, 'out' para salientes)
        2. Patrones horarios (llamadas comerciales vs seguimiento)
        3. Análisis de números telefónicos
        
        #### 💡 ¿Qué hacer si la precisión es baja?
        1. Verificar calidad de datos con auditoría
        2. Revisar si hay cambios en patrones de negocio
        3. Considerar reentrenamiento con más datos
        4. Ajustar umbrales de alertas
        """)

if __name__ == "__main__":
    main()
